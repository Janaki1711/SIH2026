/**
 * native_bridge.cpp — Android JNI Native Bridge for Member 3 (iTantra Core)
 *
 * Exposes Member3Engine to Nupur's Android Kotlin App:
 * package org.isro.itantra.semantic
 * object SemanticBridge {
 *     external fun compressTranscript(transcript: String, srcLang: String, targetLang: String, callsign: String, seq: Int): ByteArray
 *     external fun decompressAndTranslate(wireBytes: ByteArray, targetLang: String): String
 * }
 */

#include <jni.h>
#include <string>
#include <vector>
#include <memory>
#include "Member3Integration.hpp"

static std::unique_ptr<itantra::integration::Member3Engine> g_engine = nullptr;

static itantra::integration::Member3Engine& getEngine() {
    if (!g_engine) {
        g_engine = std::make_unique<itantra::integration::Member3Engine>();
    }
    return *g_engine;
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

    jsize len = env->GetArrayLength(jWireBytes);
    std::vector<uint8_t> wireBytes(len);
    env->GetByteArrayRegion(jWireBytes, 0, len, reinterpret_cast<jbyte*>(wireBytes.data()));

    const char* targetLangC = jTargetLang ? env->GetStringUTFChars(jTargetLang, nullptr) : "en";
    std::string targetLang(targetLangC);
    if (jTargetLang) env->ReleaseStringUTFChars(jTargetLang, targetLangC);

    auto decoded = getEngine().decodePacket(wireBytes, targetLang);
    return env->NewStringUTF(decoded.decodedText.c_str());
}

} // extern "C"
