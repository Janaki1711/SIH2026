#include "IndicSTTEngine.hpp"
#include <android/log.h>
#include <fstream>
#include <sstream>
#include <algorithm>

#define LOG_TAG "IndicSTTEngine"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

IndicSTTEngine::IndicSTTEngine(const std::string& encoderPath, const std::string& ctcDecoderPath, const std::string& vocabJsonPath)
    : m_env(ORT_LOGGING_LEVEL_WARNING, "IndicSTTEngine"),
      m_memoryInfo(Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault)) {

    m_sessionOptions.SetIntraOpNumThreads(2);
    m_sessionOptions.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

    if (encoderPath.empty()) {
        m_initError = "Encoder path is empty.";
        LOGE("%s", m_initError.c_str());
    } else {
        try {
            m_encoderSession = std::make_unique<Ort::Session>(m_env, encoderPath.c_str(), m_sessionOptions);
            LOGI("Encoder model loaded from %s", encoderPath.c_str());
        } catch (const std::exception& e) {
            m_initError = "Encoder load failed: " + std::string(e.what());
            LOGE("%s", m_initError.c_str());
        }
    }

    if (ctcDecoderPath.empty()) {
        if (m_initError.empty()) m_initError = "Decoder path is empty.";
        LOGE("Decoder path empty");
    } else {
        try {
            m_ctcSession = std::make_unique<Ort::Session>(m_env, ctcDecoderPath.c_str(), m_sessionOptions);
            LOGI("CTC Decoder model loaded from %s", ctcDecoderPath.c_str());
        } catch (const std::exception& e) {
            if (m_initError.empty()) m_initError = "Decoder load failed: " + std::string(e.what());
            LOGE("%s", m_initError.c_str());
        }
    }

    if (!vocabJsonPath.empty()) {
        loadVocabulary(vocabJsonPath);
    }
}

void IndicSTTEngine::loadVocabulary(const std::string& vocabJsonPath) {
    std::ifstream file(vocabJsonPath);
    if (!file.is_open()) {
        LOGE("Failed to open vocabulary JSON file at %s", vocabJsonPath.c_str());
        return;
    }
    std::string content((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    size_t pos = 0;
    while (pos < content.size()) {
        size_t keyStart = content.find('"', pos);
        if (keyStart == std::string::npos) break;
        size_t keyEnd = content.find('"', keyStart + 1);
        if (keyEnd == std::string::npos) break;
        std::string lang = content.substr(keyStart + 1, keyEnd - keyStart - 1);

        size_t arrayStart = content.find('[', keyEnd);
        if (arrayStart == std::string::npos) break;
        size_t arrayEnd = content.find(']', arrayStart);
        if (arrayEnd == std::string::npos) break;

        std::vector<std::string> tokens;
        size_t tokPos = arrayStart + 1;
        while (tokPos < arrayEnd) {
            size_t tStart = content.find('"', tokPos);
            if (tStart == std::string::npos || tStart >= arrayEnd) break;

            size_t tEnd = tStart + 1;
            while (tEnd < arrayEnd) {
                if (content[tEnd] == '"' && content[tEnd - 1] != '\\') {
                    break;
                }
                tEnd++;
            }
            if (tEnd >= arrayEnd) break;

            std::string token = content.substr(tStart + 1, tEnd - tStart - 1);
            size_t uPos = 0;
            while ((uPos = token.find("\\u2581", uPos)) != std::string::npos) {
                token.replace(uPos, 6, " ");
                uPos += 1;
            }
            tokens.push_back(token);
            tokPos = tEnd + 1;
        }

        if (!tokens.empty()) {
            m_vocabularies[lang] = std::move(tokens);
        }
        pos = arrayEnd + 1;
    }

    LOGI("Loaded %zu languages into vocabulary from %s", m_vocabularies.size(), vocabJsonPath.c_str());
}

std::string IndicSTTEngine::ctcGreedyDecode(const std::vector<int64_t>& tokenIds, const std::string& langCode) {
    if (tokenIds.empty()) return "";

    std::string result = "";
    int64_t prev = -1;

    auto it = m_vocabularies.find(langCode);
    if (it == m_vocabularies.end()) {
        it = m_vocabularies.find("hi"); // Fallback to Hindi vocabulary
    }

    if (it != m_vocabularies.end()) {
        const auto& vocab = it->second;
        for (int64_t id : tokenIds) {
            if (id != prev && id < static_cast<int64_t>(vocab.size())) {
                if (vocab[id] != "<unk>" && vocab[id] != "|") {
                    result += vocab[id];
                }
            }
            prev = id;
        }
    } else {
        for (int64_t id : tokenIds) {
            if (id != prev) {
                result += std::to_string(id) + " ";
            }
            prev = id;
        }
    }

    return result;
}

std::string IndicSTTEngine::transcribeBuffer(const std::vector<float>& pcmBuffer, const std::string& langCode) {
    if (pcmBuffer.empty()) {
        return "No speech recorded.";
    }

    if (!m_initError.empty()) {
        return "Init Error: " + m_initError;
    }

    if (!m_encoderSession || !m_ctcSession) {
        return "Model Session Null (Encoder/Decoder failed to load)";
    }

    LOGI("Processing STT transcription buffer of size %zu samples for language: %s", pcmBuffer.size(), langCode.c_str());

    try {
        std::vector<float> melFeatures;
        int64_t numFrames = 0;
        m_melExtractor.extract(pcmBuffer, melFeatures, numFrames);

        if (numFrames == 0 || melFeatures.empty()) {
            size_t durationMs = pcmBuffer.size() / 16;
            return "Voice detected (" + std::to_string(durationMs) + " ms speech captured)";
        }

        LOGI("Extracted %lld Mel frames (80 bins) from %zu PCM samples", (long long)numFrames, pcmBuffer.size());

        // Conformer encoder expects rank 3 [batch=1, mels=80, time=numFrames]
        std::vector<int64_t> inputShape = {1, 80, numFrames};
        Ort::Value inputTensor = Ort::Value::CreateTensor<float>(
            m_memoryInfo, melFeatures.data(), melFeatures.size(), inputShape.data(), inputShape.size()
        );

        int64_t lengthVal = numFrames;
        std::vector<int64_t> lengthShape = {1};
        Ort::Value lengthTensor = Ort::Value::CreateTensor<int64_t>(
            m_memoryInfo, &lengthVal, 1, lengthShape.data(), lengthShape.size()
        );

        const char* encInputNames[] = {"audio_signal", "length"};
        Ort::Value encInputTensors[] = {std::move(inputTensor), std::move(lengthTensor)};
        const char* encOutputNames[] = {"outputs"};

        auto encOutputs = m_encoderSession->Run(
            Ort::RunOptions{nullptr}, encInputNames, encInputTensors, 2, encOutputNames, 1
        );

        const char* ctcInputNames[] = {"encoder_output"};
        const char* ctcOutputNames[] = {"logprobs"};

        auto ctcOutputs = m_ctcSession->Run(
            Ort::RunOptions{nullptr}, ctcInputNames, encOutputs.data(), 1, ctcOutputNames, 1
        );

        const float* logitsData = ctcOutputs[0].GetTensorData<float>();
        auto tensorInfo = ctcOutputs[0].GetTensorTypeAndShapeInfo();
        auto shape = tensorInfo.GetShape();

        int64_t timeSteps = shape[1];
        int64_t vocabSize = shape[2];

        std::vector<int64_t> tokenIds;
        for (int64_t t = 0; t < timeSteps; ++t) {
            const float* frameLogits = logitsData + (t * vocabSize);
            int64_t maxIdx = 0;
            float maxVal = frameLogits[0];
            for (int64_t v = 1; v < vocabSize; ++v) {
                if (frameLogits[v] > maxVal) {
                    maxVal = frameLogits[v];
                    maxIdx = v;
                }
            }
            tokenIds.push_back(maxIdx);
        }

        std::string decoded = ctcGreedyDecode(tokenIds, langCode);
        if (decoded.empty()) {
            return "Decoded " + std::to_string(tokenIds.size()) + " frames (Blank)";
        }
        return decoded;

    } catch (const std::exception& e) {
        LOGE("Error during Indic STT inference: %s", e.what());
        return "Inference Error: " + std::string(e.what());
    }
}
