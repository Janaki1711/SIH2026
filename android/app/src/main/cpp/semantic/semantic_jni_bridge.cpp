/**
 * native_bridge.cpp — Android JNI Native Bridge for Member 3 (iTantra Core)
 *
 * Exposes Member3Engine to Nupur's Android Kotlin App:
 * package org.isro.itantra.semantic
 * object SemanticBridge {
 *     external fun compressTranscript(transcript: String, srcLang: String, targetLang: String, callsign: String, seq: Int): ByteArray
 *     external fun decompressAndTranslate(wireBytes: ByteArray, targetLang: String): String
 *     external fun translateText(text: String, srcLang: String, tgtLang: String): String
 * }
 */

#include <jni.h>
#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include "Member3Integration.hpp"

// Serializes all engine use across JNI callers: TX on the main thread, RX on
// the mesh transport thread, and translation on UI / ML Kit callback threads.
static std::mutex g_engineMutex;

static itantra::integration::Member3Engine& getEngine() {
    // Function-local static: thread-safe initialization (C++11).
    static itantra::integration::Member3Engine engine;
    return engine;
}

extern "C" {

JNIEXPORT jbyteArray JNICALL
Java_org_isro_itantra_semantic_SemanticBridge_compressTranscript(
    JNIEnv* env,
    jobject /* thiz */,
    jstring jTranscript,
    jstring jSrcLang,
    jstring jTargetLang,
    jstring jCallsign,
    jint jSeq
) {
    if (!jTranscript) return nullptr;
    std::lock_guard<std::mutex> engineLock(g_engineMutex);

    const char* transcriptC = env->GetStringUTFChars(jTranscript, nullptr);
    const char* srcLangC = jSrcLang ? env->GetStringUTFChars(jSrcLang, nullptr) : "en";
    const char* targetLangC = jTargetLang ? env->GetStringUTFChars(jTargetLang, nullptr) : "en";
    const char* callsignC = jCallsign ? env->GetStringUTFChars(jCallsign, nullptr) : "RESCUE_01";

    std::string transcript(transcriptC);
    std::string srcLang(srcLangC);
    std::string targetLang(targetLangC);
    std::string callsign(callsignC);

    env->ReleaseStringUTFChars(jTranscript, transcriptC);
    if (jSrcLang) env->ReleaseStringUTFChars(jSrcLang, srcLangC);
    if (jTargetLang) env->ReleaseStringUTFChars(jTargetLang, targetLangC);
    if (jCallsign) env->ReleaseStringUTFChars(jCallsign, callsignC);

    auto packet = getEngine().processTranscript(
        transcript, srcLang, targetLang, {}, callsign, static_cast<uint32_t>(jSeq)
    );

    jbyteArray result = env->NewByteArray(static_cast<jsize>(packet.serializedBytes.size()));
    env->SetByteArrayRegion(
        result, 0, static_cast<jsize>(packet.serializedBytes.size()),
        reinterpret_cast<const jbyte*>(packet.serializedBytes.data())
    );
    return result;
}

JNIEXPORT jstring JNICALL
Java_org_isro_itantra_semantic_SemanticBridge_decompressAndTranslate(
    JNIEnv* env,
    jobject /* thiz */,
    jbyteArray jWireBytes,
    jstring jTargetLang
) {
    if (!jWireBytes) return env->NewStringUTF("");
    std::lock_guard<std::mutex> engineLock(g_engineMutex);

    jsize len = env->GetArrayLength(jWireBytes);
    std::vector<uint8_t> wireBytes(len);
    env->GetByteArrayRegion(jWireBytes, 0, len, reinterpret_cast<jbyte*>(wireBytes.data()));

    const char* targetLangC = jTargetLang ? env->GetStringUTFChars(jTargetLang, nullptr) : "en";
    std::string targetLang(targetLangC);
    if (jTargetLang) env->ReleaseStringUTFChars(jTargetLang, targetLangC);

    auto decoded = getEngine().decodePacket(wireBytes, targetLang);
    return env->NewStringUTF(decoded.decodedText.c_str());
}

/**
 * translateText — direct text→semantic-IR→target-text translation WITHOUT
 * going through the ≤36-byte wire format (Tier 3 would truncate free-form
 * text at 33 bytes, so the wire roundtrip must never be used for UI
 * translation).
 *
 * Contract with the Kotlin caller:
 *   - Structured / disaster content  → realized target-language sentence
 *     (all 10 mission languages, including ml/or/pa which ML Kit lacks).
 *     Only parses that recognized a CONCRETE INTENT qualify: a canonical
 *     sentence may replace the speaker's words only when the engine knows
 *     what action was requested.
 *   - Entity-only matches (location/hazard keyword with intent==UNKNOWN)
 *     → input returned UNCHANGED. Realizing those used to fabricate
 *     "Location: Home." for a fire report — the matched location replaced
 *     the whole sentence and the hazard was dropped. The caller now falls
 *     through to its ML Kit cascade, so everything spoken is preserved.
 *   - Free-form content (isFallback) → input returned UNCHANGED, so the
 *     caller falls through to its ML Kit cascade and never mistakes the
 *     passthrough for a translation.
 *   - Any error / empty realization  → input returned UNCHANGED (same
 *     honest-passthrough contract).
 */
JNIEXPORT jstring JNICALL
Java_org_isro_itantra_semantic_SemanticBridge_translateText(
    JNIEnv* env,
    jobject /* thiz */,
    jstring jText,
    jstring jSrcLang,
    jstring jTgtLang
) {
    if (!jText) return env->NewStringUTF("");

    const char* textC = env->GetStringUTFChars(jText, nullptr);
    std::string text(textC ? textC : "");
    if (textC) env->ReleaseStringUTFChars(jText, textC);

    const char* srcC = jSrcLang ? env->GetStringUTFChars(jSrcLang, nullptr) : nullptr;
    const char* tgtC = jTgtLang ? env->GetStringUTFChars(jTgtLang, nullptr) : nullptr;
    std::string srcLang(srcC ? srcC : "en");
    std::string tgtLang(tgtC ? tgtC : "en");
    if (srcC) env->ReleaseStringUTFChars(jSrcLang, srcC);
    if (tgtC) env->ReleaseStringUTFChars(jTgtLang, tgtC);

    if (text.empty() || srcLang == tgtLang) return env->NewStringUTF(text.c_str());

    std::string out;
    {
        std::lock_guard<std::mutex> engineLock(g_engineMutex);
        try {
            auto& engine = getEngine();
            auto res = engine.getTinyMLAgent().analyze(text, srcLang, {});
            // Realize only when a concrete intent was recognized. An
            // entity-only parse (location or hazard keyword matched, but
            // intent==UNKNOWN) must NOT substitute a canonical sentence for
            // what the speaker actually said — returning the input unchanged
            // lets the caller translate the literal text instead.
            if (!res.isFallback &&
                res.intent != itantra::semantic::ActionCode::UNKNOWN) {
                out = engine.getTranslationBridge().realize(res, tgtLang);
            }
        } catch (...) {
            out.clear();
        }
    }

    if (out.empty() || out == text) return env->NewStringUTF(text.c_str());
    return env->NewStringUTF(out.c_str());
}

} // extern "C"
