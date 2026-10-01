#pragma once
#include <jni.h>

#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT jlong JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeCreateEngine(JNIEnv *env, jobject thiz);

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeDestroyEngine(JNIEnv *env, jobject thiz, jlong engineHandle);

JNIEXPORT jfloatArray JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeSynthesize(
    JNIEnv *env, jobject thiz, jlong engineHandle, jstring text, jstring langCode, jbyteArray prosodyBytes);

JNIEXPORT jfloatArray JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeGenerateSiren(
    JNIEnv *env, jobject thiz, jlong engineHandle, jfloat durationSec);

JNIEXPORT jboolean JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeStartPlayer(
    JNIEnv *env, jobject thiz, jlong engineHandle, jint sampleRate);

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeStopPlayer(
    JNIEnv *env, jobject thiz, jlong engineHandle);

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeEnqueueAudio(
    JNIEnv *env, jobject thiz, jlong engineHandle, jfloatArray audioData);

JNIEXPORT void JNICALL
Java_org_isro_itantra_tts_NativeTTSBridge_nativeSetVolume(
    JNIEnv *env, jobject thiz, jlong engineHandle, jfloat volume);

#ifdef __cplusplus
}
#endif
