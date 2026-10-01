#pragma once

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <memory>
#include <string>

/**
 * @brief C++ ONNX Runtime Wrapper for Silero VAD v5.
 * Evaluates 512-sample float PCM chunks (32ms at 16kHz) and maintains
 * an internal state vector [2, 1, 128] across calls.
 */
class SileroVAD {
public:
    explicit SileroVAD(const std::string& modelPath);
    ~SileroVAD() = default;

    /**
     * @brief Processes a single 512-sample float audio chunk.
     * @param chunk_512 Pointer to array of 512 float PCM samples [-1.0, 1.0].
     * @return Speech probability between 0.0 (Silence) and 1.0 (Active Speech).
     */
    float processChunk(const float* chunk_512);

    /**
     * @brief Resets the internal LSTM state vector to all zeros.
     */
    void resetState();

private:
    Ort::Env m_env;
    Ort::SessionOptions m_sessionOptions;
    std::unique_ptr<Ort::Session> m_session;
    Ort::MemoryInfo m_memoryInfo;

    // State vector [2, 1, 128]
    std::vector<float> m_state;
    // Sample rate tensor [1] containing value 16000
    std::vector<int64_t> m_sr;

    // Tensor shape constants
    static constexpr int64_t kChunkSize = 512;
    const std::vector<int64_t> m_inputShape{1, kChunkSize};
    const std::vector<int64_t> m_stateShape{2, 1, 128};
    const std::vector<int64_t> m_srShape{1};

    // Node names
    const char* m_inputNames[3] = {"input", "sr", "state"};
    const char* m_outputNames[2] = {"output", "stateN"};
};
