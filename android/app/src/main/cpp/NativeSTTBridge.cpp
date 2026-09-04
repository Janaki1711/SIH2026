#include "NativeSTTBridge.hpp"
#include "SileroVAD.hpp"
#include "IndicSTTEngine.hpp"
#include <android/log.h>
#include <cstring>
#include <vector>
#include <string>
#include <mutex>
#include <memory>

#define LOG_TAG "NativeSTTBridge"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

static std::vector<float> g_accumulatedSpeechBuffer;
static std::vector<float> g_rawAudioBuffer;
static std::vector<float> g_vadChunkBuffer;
static std::mutex g_audioMutex;

// Global Pointers for the ONNX Engines
static std::unique_ptr<SileroVAD> g_vadEngine;
static std::unique_ptr<IndicSTTEngine> g_sttEngine;

static std::string JStringToString(JNIEnv* env, jstring jstr) {
    if (!jstr) return "";
    const char* utf = env->GetStringUTFChars(jstr, nullptr);
    if (!utf) return "";
    std::string str(utf);
    env->ReleaseStringUTFChars(jstr, utf);
    return str;
}

extern "C" {

JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_initNativeEngine(
    JNIEnv *env,
    jclass clazz,
    jstring vadModelPath,
    jstring sttEncoderPath,
    jstring sttDecoderPath,
    jstring vocabJsonPath
) {
    try {
        LOGI("Initializing Native Audio STT Core Engines...");
        std::string vadStr = JStringToString(env, vadModelPath);
        std::string encStr = JStringToString(env, sttEncoderPath);
        std::string decStr = JStringToString(env, sttDecoderPath);
        std::string vocabStr = JStringToString(env, vocabJsonPath);

        g_vadEngine = std::make_unique<SileroVAD>(vadStr);
        g_sttEngine = std::make_unique<IndicSTTEngine>(encStr, decStr, vocabStr);

        LOGI("Native Engines successfully instantiated.");
        return JNI_TRUE;
    } catch (const std::exception& e) {
        LOGE("Failed to initialize native engines: %s", e.what());
        return JNI_FALSE;
    } catch (...) {
        LOGE("Unknown error during native engine init.");
        return JNI_FALSE;
    }
}

JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_startAudioCapture(
    JNIEnv *env,
    jclass clazz
) {
    try {
        std::lock_guard<std::mutex> lock(g_audioMutex);
        g_accumulatedSpeechBuffer.clear();
        g_rawAudioBuffer.clear();
        g_vadChunkBuffer.clear();
        if (g_vadEngine) {
            g_vadEngine->resetState(); // Reset LSTM cell states for new speech
        }
        LOGI("Native Audio capture session started.");
        return JNI_TRUE;
    } catch (...) {
        return JNI_FALSE;
    }
}

JNIEXPORT void JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_pushAudioPCM(
    JNIEnv *env,
    jclass clazz,
    jshortArray pcmData,
    jint length
) {
    try {
        if (!pcmData || length <= 0) return;

        jshort *samples = env->GetShortArrayElements(pcmData, nullptr);
        if (!samples) return;

        {
            std::lock_guard<std::mutex> lock(g_audioMutex);
            for (int i = 0; i < length; ++i) {
                float floatVal = samples[i] / 32768.0f;
                g_rawAudioBuffer.push_back(floatVal);
                g_vadChunkBuffer.push_back(floatVal);

                if (g_vadChunkBuffer.size() >= 512) {
                    // Pass to Silero VAD for gating
                    float speechProb = 1.0f; 
                    if (g_vadEngine) {
                        speechProb = g_vadEngine->processChunk(g_vadChunkBuffer.data());
                    }

                    // Lower threshold to 0.25f to reliably capture speech across various microphones
                    if (speechProb > 0.25f) {
                        g_accumulatedSpeechBuffer.insert(
                            g_accumulatedSpeechBuffer.end(),
                            g_vadChunkBuffer.begin(),
                            g_vadChunkBuffer.end()
                        );
                    }
                    g_vadChunkBuffer.clear();
                }
            }
        }

        env->ReleaseShortArrayElements(pcmData, samples, JNI_ABORT);
    } catch (...) {
        LOGE("Exception in pushAudioPCM");
    }
}

JNIEXPORT jstring JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_stopAudioCaptureAndTranscribe(
    JNIEnv *env,
    jclass clazz,
    jstring langCode
) {
    try {
        std::vector<float> finalBuffer;
        {
            std::lock_guard<std::mutex> lock(g_audioMutex);
            if (g_accumulatedSpeechBuffer.size() >= 1600) {
                finalBuffer = g_accumulatedSpeechBuffer;
            } else if (g_rawAudioBuffer.size() >= 1600) {
                finalBuffer = g_rawAudioBuffer; // VAD fallback to ensure speech is never dropped
            }
        }

        std::string langStr = JStringToString(env, langCode);
        if (langStr.empty()) langStr = "hi";

        if (finalBuffer.size() < 1600) { // Less than 100ms of audio
            return env->NewStringUTF("No speech detected (Silero VAD idle: silence).");
        }

        std::string resultText = "";
        if (g_sttEngine) {
            // Run the actual ONNX Inference!
            resultText = g_sttEngine->transcribeBuffer(finalBuffer, langStr);
        } else {
            size_t durationMs = finalBuffer.size() / 16;
            resultText = "VAD Active Speech Detected: " + std::to_string(durationMs) + " ms voice audio captured in [" + langStr + "] by C++ Engine";
        }
        
        return env->NewStringUTF(resultText.c_str());
    } catch (const std::exception& e) {
        LOGE("Error during native transcription: %s", e.what());
        return env->NewStringUTF("Inference C++ Exception.");
    } catch (...) {
        return env->NewStringUTF("No speech detected (VAD idle).");
    }
}

JNIEXPORT void JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_releaseNativeEngine(
    JNIEnv *env,
    jclass clazz
) {
    try {
        std::lock_guard<std::mutex> lock(g_audioMutex);
        g_accumulatedSpeechBuffer.clear();
        g_vadChunkBuffer.clear();
        g_vadEngine.reset();
        g_sttEngine.reset();
        LOGI("Native Audio STT Core released.");
    } catch (...) {}
}
}
