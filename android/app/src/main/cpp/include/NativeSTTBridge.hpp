#ifndef NATIVE_STT_BRIDGE_HPP
#define NATIVE_STT_BRIDGE_HPP

#include <jni.h>

extern "C" {
    JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_initNativeEngine(
        JNIEnv *env, jclass clazz, jstring vadModelPath, jstring sttEncoderPath, jstring sttDecoderPath, jstring vocabJsonPath
    );

    JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_setWhisperModel(
        JNIEnv *env, jclass clazz, jstring modelPath
    );

    JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_startAudioCapture(
        JNIEnv *env, jclass clazz
    );

    JNIEXPORT void JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_pushAudioPCM(
        JNIEnv *env, jclass clazz, jshortArray pcmData, jint length
    );

    JNIEXPORT jstring JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_stopAudioCaptureAndTranscribe(
        JNIEnv *env, jclass clazz, jstring langCode
    );

    JNIEXPORT void JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_releaseNativeEngine(
        JNIEnv *env, jclass clazz
    );
}

#endif
