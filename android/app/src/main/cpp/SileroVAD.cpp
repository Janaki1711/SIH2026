#include "SileroVAD.hpp"
#include <android/log.h>
#include <algorithm>
#include <cstdio>

#define LOG_TAG "SileroVAD"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

SileroVAD::SileroVAD(const std::string& modelPath)
    : m_env(ORT_LOGGING_LEVEL_WARNING, "SileroVAD"),
      m_memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault)),
      m_state(2 * 1 * 128, 0.0f),
      m_sr({16000}) {

    m_sessionOptions.SetIntraOpNumThreads(1);
    m_sessionOptions.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

    if (!modelPath.empty()) {
        FILE* f = fopen(modelPath.c_str(), "rb");
        if (f) {
            fseek(f, 0, SEEK_END);
            long sz = ftell(f);
            fclose(f);

            if (sz > 1000) { // Valid model file check (> 1 KB)
                try {
                    m_session = std::make_unique<Ort::Session>(m_env, modelPath.c_str(), m_sessionOptions);
                    LOGI("Silero VAD session created successfully (%ld bytes)", sz);
                } catch (const std::exception& e) {
                    LOGE("Failed to create Silero VAD ONNX Session: %s", e.what());
                    m_session.reset();
                } catch (...) {
                    LOGE("Unknown error creating Silero VAD session");
                    m_session.reset();
                }
            } else {
                LOGE("Silero VAD model file invalid or too small (%ld bytes)", sz);
            }
        } else {
            LOGE("Cannot open Silero VAD model file at %s", modelPath.c_str());
        }
    }
}

void SileroVAD::resetState() {
    std::fill(m_state.begin(), m_state.end(), 0.0f);
}

float SileroVAD::processChunk(const float* chunk_512) {
    if (!m_session || !chunk_512) return 0.8f; // Safe speech detection fallback if session not active

    Ort::Value inputTensor = Ort::Value::CreateTensor<float>(
        m_memoryInfo, const_cast<float*>(chunk_512), kChunkSize, m_inputShape.data(), m_inputShape.size()
    );

    Ort::Value srTensor = Ort::Value::CreateTensor<int64_t>(
        m_memoryInfo, m_sr.data(), m_sr.size(), m_srShape.data(), m_srShape.size()
    );

    Ort::Value stateTensor = Ort::Value::CreateTensor<float>(
        m_memoryInfo, m_state.data(), m_state.size(), m_stateShape.data(), m_stateShape.size()
    );

    std::vector<Ort::Value> inputs;
    inputs.push_back(std::move(inputTensor));
    inputs.push_back(std::move(srTensor));
    inputs.push_back(std::move(stateTensor));

    try {
        auto outputs = m_session->Run(
            Ort::RunOptions{nullptr},
            m_inputNames,
            inputs.data(),
            inputs.size(),
            m_outputNames,
            2
        );

        float speechProb = outputs[0].GetTensorData<float>()[0];

        const float* newStateData = outputs[1].GetTensorData<float>();
        std::copy(newStateData, newStateData + m_state.size(), m_state.begin());

        return speechProb;

    } catch (const std::exception& e) {
        LOGE("Error during Silero VAD inference: %s", e.what());
        return 0.8f;
    } catch (...) {
        LOGE("Unknown error during Silero VAD inference");
        return 0.8f;
    }
}
