#pragma once

#include <onnxruntime_cxx_api.h>
#include <vector>
#include <string>
#include <memory>
#include <unordered_map>
#include "MelSpectrogram.hpp"

/**
 * @brief Quantized IndicConformer STT Engine (C++ ONNX Runtime Mobile).
 * Ingests active speech float PCM buffer and decodes phonemes / text offline
 * for Indian languages (Hindi, Tamil, Marathi, etc.).
 */
class IndicSTTEngine {
public:
    IndicSTTEngine(const std::string& encoderPath, const std::string& ctcDecoderPath, const std::string& vocabJsonPath);
    ~IndicSTTEngine() = default;

    /**
     * @brief Transcribes accumulated speech PCM buffer to text.
     * @param pcmBuffer Vector of 16kHz Mono float PCM samples.
     * @param langCode ISO language code (e.g., "hi", "ta", "mr").
     * @return Decoded transcript string.
     */
    std::string transcribeBuffer(const std::vector<float>& pcmBuffer, const std::string& langCode);

private:
    Ort::Env m_env;
    Ort::SessionOptions m_sessionOptions;
    std::unique_ptr<Ort::Session> m_encoderSession;
    std::unique_ptr<Ort::Session> m_ctcSession;
    Ort::MemoryInfo m_memoryInfo;

    // Language vocabulary mappings
    std::unordered_map<std::string, std::vector<std::string>> m_vocabularies;

    void loadVocabulary(const std::string& vocabJsonPath);
    std::string ctcGreedyDecode(const std::vector<int64_t>& tokenIds, const std::string& langCode);
    MelSpectrogramExtractor m_melExtractor;
    std::string m_initError;
};
