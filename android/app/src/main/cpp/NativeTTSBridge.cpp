#include "NativeTTSBridge.hpp"
#include "IndicTTSEngine.hpp"
#include "OboeAudioPlayer.hpp"
#include "VoiceToneCloner.hpp"
#include <memory>

struct NativeContext {
    std::unique_ptr<IndicTTSEngine> ttsEngine;
    std::unique_ptr<OboeAudioPlayer> audioPlayer;
    std::unique_ptr<VoiceToneCloner> toneCloner;

    NativeContext()
        : ttsEngine(std::make_unique<IndicTTSEngine>()),
          audioPlayer(std::make_unique<OboeAudioPlayer>()),
          toneCloner(std::make_unique<VoiceToneCloner>()) {}
};

extern "C" {

JNIEXPORT jlong JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeCreateEngine(JNIEnv* /*env*/, jobject /*thiz*/) {
    auto* ctx = new NativeContext();
    return reinterpret_cast<jlong>(ctx);
}

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeDestroyEngine(JNIEnv* /*env*/, jobject /*thiz*/, jlong engineHandle) {
    if (engineHandle != 0) {
        auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);
        delete ctx;
    }
}

JNIEXPORT jfloatArray JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeSynthesize(
    JNIEnv *env, jobject /*thiz*/, jlong engineHandle, jstring text, jstring langCode, jbyteArray prosodyBytes) {

    if (engineHandle == 0 || text == nullptr || langCode == nullptr) {
        return env->NewFloatArray(0);
    }

    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);

    const char* nativeText = env->GetStringUTFChars(text, nullptr);
    const char* nativeLang = env->GetStringUTFChars(langCode, nullptr);

    ProsodyVector prosody{};
    if (prosodyBytes != nullptr) {
        jsize len = env->GetArrayLength(prosodyBytes);
        jbyte* b = env->GetByteArrayElements(prosodyBytes, nullptr);
        prosody = ctx->toneCloner->deserializeVector(reinterpret_cast<uint8_t*>(b), len);
        env->ReleaseByteArrayElements(prosodyBytes, b, JNI_ABORT);
    }

    std::vector<float> audioPCM;
    ctx->ttsEngine->synthesize(nativeText, nativeLang, prosody, audioPCM, 16000);

    env->ReleaseStringUTFChars(text, nativeText);
    env->ReleaseStringUTFChars(langCode, nativeLang);

    jfloatArray result = env->NewFloatArray(audioPCM.size());
    if (!audioPCM.empty()) {
        env->SetFloatArrayRegion(result, 0, audioPCM.size(), audioPCM.data());
    }
    return result;
}

JNIEXPORT jfloatArray JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeGenerateSiren(
    JNIEnv *env, jobject /*thiz*/, jlong engineHandle, jfloat durationSec) {

    if (engineHandle == 0) return env->NewFloatArray(0);
    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);

    std::vector<float> siren = ctx->toneCloner->generateEmergencySiren(durationSec, 16000);

    jfloatArray result = env->NewFloatArray(siren.size());
    if (!siren.empty()) {
        env->SetFloatArrayRegion(result, 0, siren.size(), siren.data());
    }
    return result;
}

JNIEXPORT jboolean JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeStartPlayer(
    JNIEnv* /*env*/, jobject /*thiz*/, jlong engineHandle, jint sampleRate) {

    if (engineHandle == 0) return JNI_FALSE;
    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);
    return ctx->audioPlayer->start(sampleRate, 1) ? JNI_TRUE : JNI_FALSE;
}

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeStopPlayer(
    JNIEnv* /*env*/, jobject /*thiz*/, jlong engineHandle) {

    if (engineHandle == 0) return;
    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);
    ctx->audioPlayer->stop();
}

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeEnqueueAudio(
    JNIEnv *env, jobject /*thiz*/, jlong engineHandle, jfloatArray audioData) {

    if (engineHandle == 0 || audioData == nullptr) return;
    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);

    jsize len = env->GetArrayLength(audioData);
    jfloat* pcm = env->GetFloatArrayElements(audioData, nullptr);

    ctx->audioPlayer->enqueueAudio(pcm, len);

    env->ReleaseFloatArrayElements(audioData, pcm, JNI_ABORT);
}

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeSetVolume(
    JNIEnv* /*env*/, jobject /*thiz*/, jlong engineHandle, jfloat volume) {

    if (engineHandle == 0) return;
    auto* ctx = reinterpret_cast<NativeContext*>(engineHandle);
    ctx->audioPlayer->setVolume(volume);
}

}
