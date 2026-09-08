#include "IndicSTTEngine.hpp"
#include <android/log.h>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <map>
#include <cmath>

#define LOG_TAG "IndicSTTEngine"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

// Unicode script classification for token masking
enum class UScript {
    SPECIAL,    // <unk>, <blk>, ▁ (space), etc.
    DEVANAGARI, // U+0900-U+097F (Hindi, Marathi, Sanskrit, Nepali, Dogri, Konkani, Maithili, Bodo)
    BENGALI,    // U+0980-U+09FF (Bengali, Assamese)
    GURMUKHI,   // U+0A00-U+0A7F (Punjabi)
    GUJARATI,   // U+0A80-U+0AFF
    ORIYA,      // U+0B00-U+0B7F
    TAMIL,      // U+0B80-U+0BFF
    TELUGU,     // U+0C00-U+0C7F
    KANNADA,    // U+0C80-U+0CFF
    MALAYALAM,  // U+0D00-U+0D7F
    ARABIC,     // U+0600-U+06FF (Urdu, Kashmiri, Sindhi)
    OL_CHIKI,   // U+1C50-U+1C7F (Santali)
    MEETEI,     // U+ABC0-U+ABFF (Manipuri/Meetei Mayek)
    OTHER
};

static UScript classifyChar(uint32_t cp) {
    if (cp >= 0x0900 && cp <= 0x097F) return UScript::DEVANAGARI;
    if (cp >= 0x0980 && cp <= 0x09FF) return UScript::BENGALI;
    if (cp >= 0x0A00 && cp <= 0x0A7F) return UScript::GURMUKHI;
    if (cp >= 0x0A80 && cp <= 0x0AFF) return UScript::GUJARATI;
    if (cp >= 0x0B00 && cp <= 0x0B7F) return UScript::ORIYA;
    if (cp >= 0x0B80 && cp <= 0x0BFF) return UScript::TAMIL;
    if (cp >= 0x0C00 && cp <= 0x0C7F) return UScript::TELUGU;
    if (cp >= 0x0C80 && cp <= 0x0CFF) return UScript::KANNADA;
    if (cp >= 0x0D00 && cp <= 0x0D7F) return UScript::MALAYALAM;
    if (cp >= 0x0600 && cp <= 0x06FF) return UScript::ARABIC;
    if (cp >= 0x1C50 && cp <= 0x1C7F) return UScript::OL_CHIKI;
    if (cp >= 0xABC0 && cp <= 0xABFF) return UScript::MEETEI;
    return UScript::OTHER;
}

// Classify a token string by its dominant Unicode script
static UScript classifyToken(const std::string& token) {
    if (token.empty() || token == "<unk>" || token == "<blk>" || token == "|") {
        return UScript::SPECIAL;
    }
    // Decode first non-▁ UTF-8 character
    const unsigned char* p = reinterpret_cast<const unsigned char*>(token.c_str());
    size_t len = token.size();
    size_t i = 0;
    while (i < len) {
        uint32_t cp = 0;
        int bytes = 0;
        if (p[i] < 0x80) { cp = p[i]; bytes = 1; }
        else if ((p[i] & 0xE0) == 0xC0) { cp = p[i] & 0x1F; bytes = 2; }
        else if ((p[i] & 0xF0) == 0xE0) { cp = p[i] & 0x0F; bytes = 3; }
        else if ((p[i] & 0xF8) == 0xF0) { cp = p[i] & 0x07; bytes = 4; }
        else { i++; continue; }
        for (int b = 1; b < bytes && (i + b) < len; ++b)
            cp = (cp << 6) | (p[i + b] & 0x3F);
        i += bytes;
        // Skip SentencePiece space marker ▁ (U+2581) and ASCII
        if (cp == 0x2581 || cp < 0x80) continue;
        return classifyChar(cp);
    }
    return UScript::SPECIAL; // Token is only ▁ or ASCII
}

// Map language code to expected script
static UScript langToScript(const std::string& langCode) {
    if (langCode == "hi" || langCode == "mr" || langCode == "sa" || langCode == "ne" ||
        langCode == "doi" || langCode == "kok" || langCode == "mai" || langCode == "brx") return UScript::DEVANAGARI;
    if (langCode == "bn" || langCode == "as") return UScript::BENGALI;
    if (langCode == "pa") return UScript::GURMUKHI;
    if (langCode == "gu") return UScript::GUJARATI;
    if (langCode == "or") return UScript::ORIYA;
    if (langCode == "ta") return UScript::TAMIL;
    if (langCode == "te") return UScript::TELUGU;
    if (langCode == "kn") return UScript::KANNADA;
    if (langCode == "ml") return UScript::MALAYALAM;
    if (langCode == "ur" || langCode == "ks" || langCode == "sd") return UScript::ARABIC;
    if (langCode == "sat") return UScript::OL_CHIKI;
    if (langCode == "mni") return UScript::MEETEI;
    // English and unknown → Devanagari (will be transliterated in Kotlin)
    return UScript::DEVANAGARI;
}

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
        LOGE("Failed to open vocabulary file at %s", vocabJsonPath.c_str());
        return;
    }

    std::string firstLine;
    if (std::getline(file, firstLine)) {
        if (!firstLine.empty() && firstLine[0] != '{') {
            // Unified tokens.txt format: "<token> <id>"
            std::vector<std::string> tokens;
            auto parseLine = [&](const std::string& line) {
                if (line.empty()) return;
                size_t lastSpace = line.rfind(' ');
                if (lastSpace != std::string::npos) {
                    std::string tok = line.substr(0, lastSpace);
                    try {
                        size_t id = static_cast<size_t>(std::stoul(line.substr(lastSpace + 1)));
                        if (id >= tokens.size()) {
                            tokens.resize(id + 1);
                        }
                        tokens[id] = tok;
                    } catch (...) {}
                }
            };
            parseLine(firstLine);
            std::string line;
            while (std::getline(file, line)) {
                parseLine(line);
            }
            m_unifiedTokens = std::move(tokens);
            LOGI("Loaded %zu unified CTC tokens from %s", m_unifiedTokens.size(), vocabJsonPath.c_str());

            // Pre-compute script classification for each token
            m_tokenScripts.resize(m_unifiedTokens.size());
            std::map<int, int> scriptCounts;
            for (size_t idx = 0; idx < m_unifiedTokens.size(); ++idx) {
                UScript s = classifyToken(m_unifiedTokens[idx]);
                m_tokenScripts[idx] = static_cast<int>(s);
                scriptCounts[static_cast<int>(s)]++;
            }
            LOGI("Token script distribution: Devanagari=%d Bengali=%d Tamil=%d Telugu=%d Kannada=%d Malayalam=%d Gujarati=%d Gurmukhi=%d Special=%d",
                 scriptCounts[static_cast<int>(UScript::DEVANAGARI)],
                 scriptCounts[static_cast<int>(UScript::BENGALI)],
                 scriptCounts[static_cast<int>(UScript::TAMIL)],
                 scriptCounts[static_cast<int>(UScript::TELUGU)],
                 scriptCounts[static_cast<int>(UScript::KANNADA)],
                 scriptCounts[static_cast<int>(UScript::MALAYALAM)],
                 scriptCounts[static_cast<int>(UScript::GUJARATI)],
                 scriptCounts[static_cast<int>(UScript::GURMUKHI)],
                 scriptCounts[static_cast<int>(UScript::SPECIAL)]);
            return;
        }
    }

    // JSON vocab format
    file.clear();
    file.seekg(0, std::ios::beg);
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

    // 1. Use unified vocabulary from tokens.txt if loaded
    if (!m_unifiedTokens.empty()) {
        int64_t blankId = static_cast<int64_t>(m_unifiedTokens.size()) - 1; // 5632 for <blk>
        for (int64_t id : tokenIds) {
            if (id == blankId || id == 0) { // Skip blank and unk
                prev = id;
                continue;
            }
            if (id != prev) {
                if (id >= 0 && id < static_cast<int64_t>(m_unifiedTokens.size())) {
                    const std::string& tok = m_unifiedTokens[id];
                    if (tok != "<unk>" && tok != "<blk>" && tok != "|") {
                        result += tok;
                    }
                }
            }
            prev = id;
        }

        // Replace SentencePiece space character \u2581 (0xE2, 0x96, 0x81) with ' '
        std::string spSpace = "\xE2\x96\x81";
        size_t spPos = 0;
        while ((spPos = result.find(spSpace, spPos)) != std::string::npos) {
            result.replace(spPos, spSpace.length(), " ");
            spPos += 1;
        }

        // Clean leading/trailing spaces
        size_t start = result.find_first_not_of(" \t\n\r");
        if (start == std::string::npos) return "";
        size_t end = result.find_last_not_of(" \t\n\r");
        return result.substr(start, end - start + 1);
    }

    // 2. Fallback to per-language vocabulary from vocab.json
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
        size_t durationMs = pcmBuffer.size() / 16;
        LOGW("Indic STT Engine init notice: %s. Using VAD voice fallback.", m_initError.c_str());
        return "Voice Alert (" + std::to_string(durationMs) + " ms) [Init Error: " + m_initError + "]";
    }

    if (!m_encoderSession) {
        size_t durationMs = pcmBuffer.size() / 16;
        return "Voice Alert (" + std::to_string(durationMs) + " ms) [Session null: enc=NULL]";
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

        // Dynamically query encoder input names to support both "processed_signal" and "audio_signal"
        Ort::AllocatorWithDefaultOptions allocator;
        size_t encInputCount = m_encoderSession->GetInputCount();
        std::vector<std::string> encInputNameStrs(encInputCount);
        std::vector<const char*> encInputNames(encInputCount);
        std::vector<Ort::Value> encInputTensors;

        for (size_t i = 0; i < encInputCount; ++i) {
            auto nameAlloc = m_encoderSession->GetInputNameAllocated(i, allocator);
            encInputNameStrs[i] = nameAlloc.get();
            encInputNames[i] = encInputNameStrs[i].c_str();

            if (encInputNameStrs[i] == "processed_signal" || encInputNameStrs[i] == "audio_signal" || i == 0) {
                std::vector<int64_t> inputShape = {1, 80, numFrames};
                encInputTensors.push_back(Ort::Value::CreateTensor<float>(
                    m_memoryInfo, melFeatures.data(), melFeatures.size(), inputShape.data(), inputShape.size()
                ));
            } else if (encInputNameStrs[i] == "processed_signal_length" || encInputNameStrs[i] == "length" || i == 1) {
                int64_t lengthVal = numFrames;
                std::vector<int64_t> lengthShape = {1};
                encInputTensors.push_back(Ort::Value::CreateTensor<int64_t>(
                    m_memoryInfo, &lengthVal, 1, lengthShape.data(), lengthShape.size()
                ));
            }
        }

        // Dynamically query encoder output names
        size_t encOutputCount = m_encoderSession->GetOutputCount();
        std::vector<std::string> encOutputNameStrs(encOutputCount);
        std::vector<const char*> encOutputNames(encOutputCount);
        for (size_t i = 0; i < encOutputCount; ++i) {
            auto nameAlloc = m_encoderSession->GetOutputNameAllocated(i, allocator);
            encOutputNameStrs[i] = nameAlloc.get();
            encOutputNames[i] = encOutputNameStrs[i].c_str();
        }

        auto encOutputs = m_encoderSession->Run(
            Ort::RunOptions{nullptr},
            encInputNames.data(),
            encInputTensors.data(),
            encInputTensors.size(),
            encOutputNames.data(),
            encOutputNames.size()
        );

        const float* logitsData = nullptr;
        int64_t timeSteps = 0;
        int64_t vocabSize = 0;

        auto encShape = encOutputs[0].GetTensorTypeAndShapeInfo().GetShape();
        if (encShape.size() == 3 && encShape[2] > 1024) {
            // Direct CTC output from end-to-end conformer (shape: [batch, time, 5633])
            timeSteps = encShape[1];
            vocabSize = encShape[2];
            logitsData = encOutputs[0].GetTensorData<float>();
            LOGI("Direct CTC log_probs from Conformer: timeSteps=%lld, vocabSize=%lld", (long long)timeSteps, (long long)vocabSize);
        } else if (m_ctcSession) {
            // Fallback for split architecture
            size_t ctcInputCount = m_ctcSession->GetInputCount();
            std::vector<const char*> ctcInputNames;
            std::vector<Ort::Value> ctcInputTensors;

            ctcInputNames.push_back("encoder_output");
            ctcInputTensors.push_back(std::move(encOutputs[0]));

            int64_t targetId = 6;
            static const std::map<std::string, int64_t> langIdMap = {
                {"as", 0}, {"bn", 1}, {"brx", 2}, {"doi", 3}, {"kok", 4},
                {"gu", 5}, {"hi", 6}, {"kn", 7}, {"ks", 8}, {"mai", 9},
                {"ml", 10}, {"mni", 11}, {"mr", 12}, {"ne", 13}, {"or", 14},
                {"pa", 15}, {"sa", 16}, {"sat", 17}, {"sd", 18}, {"ta", 19},
                {"te", 20}, {"ur", 21}, {"en", 6}
            };
            auto it = langIdMap.find(langCode);
            if (it != langIdMap.end()) targetId = it->second;

            std::vector<int64_t> langShape = {1};
            Ort::Value langTensor = Ort::Value::CreateTensor<int64_t>(
                m_memoryInfo, &targetId, 1, langShape.data(), langShape.size()
            );

            if (ctcInputCount > 1) {
                ctcInputNames.push_back("language_ids");
                ctcInputTensors.push_back(std::move(langTensor));
            }

            const char* ctcOutputNames[] = {"logprobs"};
            auto ctcOutputs = m_ctcSession->Run(
                Ort::RunOptions{nullptr},
                ctcInputNames.data(),
                ctcInputTensors.data(),
                ctcInputTensors.size(),
                ctcOutputNames,
                1
            );

            auto ctcShape = ctcOutputs[0].GetTensorTypeAndShapeInfo().GetShape();
            timeSteps = ctcShape[1];
            vocabSize = ctcShape[2];
            logitsData = ctcOutputs[0].GetTensorData<float>();
        } else {
            return "Error: Conformer output is hidden representation but no CTC decoder session loaded.";
        }

        // Language-conditioned CTC greedy argmax:
        // Only consider tokens matching the selected language's script
        UScript targetScript = langToScript(langCode);
        int targetScriptInt = static_cast<int>(targetScript);
        int specialScriptInt = static_cast<int>(UScript::SPECIAL);
        bool hasScriptMask = !m_tokenScripts.empty() && m_tokenScripts.size() == static_cast<size_t>(vocabSize);

        LOGI("Language-conditioned decode: langCode=%s targetScript=%d hasMask=%d", langCode.c_str(), targetScriptInt, hasScriptMask ? 1 : 0);

        std::vector<int64_t> tokenIds;
        for (int64_t t = 0; t < timeSteps; ++t) {
            const float* frameLogits = logitsData + (t * vocabSize);
            int64_t maxIdx = vocabSize - 1; // Default to blank token (last token = <blk>)
            float maxVal = -1e30f;

            for (int64_t v = 0; v < vocabSize; ++v) {
                // Skip tokens from wrong script (allow SPECIAL tokens always)
                if (hasScriptMask) {
                    int tokenScript = m_tokenScripts[v];
                    if (tokenScript != targetScriptInt && tokenScript != specialScriptInt) {
                        continue; // Mask out this token
                    }
                }
                if (frameLogits[v] > maxVal) {
                    maxVal = frameLogits[v];
                    maxIdx = v;
                }
            }
            tokenIds.push_back(maxIdx);
        }

        std::string decoded = ctcGreedyDecode(tokenIds, langCode);
        if (decoded.empty()) {
            size_t durationMs = pcmBuffer.size() / 16;
            return "Voice Transmission (" + std::to_string(durationMs) + " ms speech captured in [" + langCode + "])";
        }
        return decoded;

    } catch (const std::exception& e) {
        LOGE("Error during Indic STT inference: %s", e.what());
        return "Inference Error: " + std::string(e.what());
    }
}
