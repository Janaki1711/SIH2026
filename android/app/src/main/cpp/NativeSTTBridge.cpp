#include "NativeSTTBridge.hpp"
#include "SileroVAD.hpp"
#include "IndicSTTEngine.hpp"
#include "WhisperSTTEngine.hpp"
#include <android/log.h>
#include <cstring>
#include <vector>
#include <string>
#include <mutex>
#include <memory>

#define LOG_TAG "NativeSTTBridge"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)

static std::vector<float> g_accumulatedSpeechBuffer;
static std::vector<float> g_rawAudioBuffer;
static std::vector<float> g_vadChunkBuffer;
static std::mutex g_audioMutex;

// Global Pointers for the ONNX Engines
static std::unique_ptr<SileroVAD> g_vadEngine;
static std::unique_ptr<IndicSTTEngine> g_sttEngine;

// Whisper (te/ta/kn/ml) — lazy-initialized on first gated transcription so
// hi/mr/bn/pa/gu/or users never pay the ~43 MB model load or its RAM cost.
static std::mutex g_whisperMutex;          // guards lazy init + transcribe
static std::string g_whisperModelPath;     // set from Kotlin, no load here
static std::unique_ptr<WhisperSTTEngine> g_whisperEngine;
static bool g_whisperInitFailed = false;   // don't retry a failing load every utterance

// Language gate from the CER benchmark: only these four were gated to the
// parambharat model; all other app languages keep the conformer encoder.
static bool useWhisperFor(const std::string& lang) {
    return lang == "te" || lang == "ta" || lang == "kn" || lang == "ml";
}

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

// Called from Kotlin with the ggml model path (copied from assets). Stores the
// path only — the model is actually loaded lazily on the first te/ta/kn/ml
// transcription, so app startup and non-whisper languages stay unaffected.
JNIEXPORT jboolean JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_setWhisperModel(
    JNIEnv *env,
    jclass clazz,
    jstring modelPath
) {
    try {
        std::string path = JStringToString(env, modelPath);
        if (path.empty()) {
            LOGW("setWhisperModel: empty path — whisper disabled, conformer fallback only.");
            return JNI_FALSE;
        }
        {
            std::lock_guard<std::mutex> lock(g_whisperMutex);
            g_whisperModelPath = path;
            g_whisperEngine.reset();       // force reload on next use
            g_whisperInitFailed = false;
        }
        LOGI("setWhisperModel: %s (lazy load on first te/ta/kn/ml utterance)", path.c_str());
        return JNI_TRUE;
    } catch (const std::exception& e) {
        LOGE("setWhisperModel failed: %s", e.what());
        return JNI_FALSE;
    } catch (...) {
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
} // Close extern "C"
#include "AudioRingBuffer.hpp"
std::shared_ptr<AudioRingBuffer> getGlobalRingBuffer();

extern "C" {

JNIEXPORT void JNICALL Java_org_isro_itantra_audio_NativeSTTBridge_pumpRingBuffer(
    JNIEnv *env,
    jclass clazz
) {
    try {
        auto rb = getGlobalRingBuffer();
        if (!rb) return;

        std::lock_guard<std::mutex> lock(g_audioMutex);
        float temp[512];
        while (rb->available() >= 512) {
            if (rb->read(temp, 512)) {
                for (int i = 0; i < 512; ++i) {
                    g_rawAudioBuffer.push_back(temp[i]);
                    g_vadChunkBuffer.push_back(temp[i]);
                }
                
                float speechProb = 1.0f;
                if (g_vadEngine) {
                    speechProb = g_vadEngine->processChunk(g_vadChunkBuffer.data());
                }

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
    } catch (...) {
        LOGE("Exception in pumpRingBuffer");
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
            // Use the full recorded audio buffer in PTT mode so speech is never chopped or dropped by VAD
            if (g_rawAudioBuffer.size() >= 1600) {
                finalBuffer = g_rawAudioBuffer;
            } else if (g_accumulatedSpeechBuffer.size() >= 1600) {
                finalBuffer = g_accumulatedSpeechBuffer;
            }
        }

        // Apply Automatic Gain Control (AGC) so quiet phone microphones reach optimal neural network level
        if (!finalBuffer.empty()) {
            float maxAmp = 0.0f;
            for (float s : finalBuffer) {
                float a = std::abs(s);
                if (a > maxAmp) maxAmp = a;
            }
            if (maxAmp > 0.005f && maxAmp < 0.7f) {
                float gain = 0.7f / maxAmp;
                for (float& s : finalBuffer) {
                    s *= gain;
                }
                LOGI("Applied AGC gain multiplier: %.2f (original peak: %.3f)", gain, maxAmp);
            }
        }

        std::string langStr = JStringToString(env, langCode);
        if (langStr.empty()) langStr = "hi";

        if (finalBuffer.size() < 1600) { // Less than 100ms of audio
            return env->NewStringUTF("No speech detected (Silero VAD idle: silence).");
        }

        std::string resultText = "";
        if (useWhisperFor(langStr) && !g_whisperModelPath.empty()) {
            // Gate-passed whisper path for te/ta/kn/ml. Empty result = collapse
            // guard rejected it (or init failed) → fall back to conformer below.
            std::lock_guard<std::mutex> wlock(g_whisperMutex);
            if (!g_whisperEngine && !g_whisperInitFailed) {
                auto engine = std::make_unique<WhisperSTTEngine>();
                if (engine->init(g_whisperModelPath)) {
                    g_whisperEngine = std::move(engine);
                    LOGI("WhisperSTTEngine loaded lazily for [%s]", langStr.c_str());
                } else {
                    g_whisperInitFailed = true;
                    LOGW("WhisperSTTEngine init failed — conformer fallback for all languages.");
                }
            }
            if (g_whisperEngine) {
                resultText = g_whisperEngine->transcribe(finalBuffer, langStr);
                if (resultText.empty()) {
                    LOGW("whisper output empty/rejected for [%s] — falling back to conformer", langStr.c_str());
                }
            }
        }
        if (resultText.empty()) {
            if (g_sttEngine) {
                // Run the actual ONNX Inference!
                resultText = g_sttEngine->transcribeBuffer(finalBuffer, langStr);
            } else {
                size_t durationMs = finalBuffer.size() / 16;
                resultText = "VAD Active Speech Detected: " + std::to_string(durationMs) + " ms voice audio captured in [" + langStr + "] by C++ Engine";
            }
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
        {
            std::lock_guard<std::mutex> wlock(g_whisperMutex);
            g_whisperEngine.reset();
        }
        LOGI("Native Audio STT Core released.");
    } catch (...) {}
}
}

