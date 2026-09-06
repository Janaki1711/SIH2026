#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <memory>
#include "VoiceToneCloner.hpp"

struct FormantParams {
    float f1;
    float f2;
    float f3;
    float bw1;
    float bw2;
    float bw3;
};

class IndicTTSEngine {
public:
    IndicTTSEngine();
    ~IndicTTSEngine() = default;

    bool initialize(const std::string& modelAssetsDir = "");

    void synthesize(
        const std::string& text,
        const std::string& langCode,
        const ProsodyVector& prosody,
        std::vector<float>& outAudioPCM,
        int sampleRate = 16000
    );

    std::vector<std::string> getSupportedLanguages() const;

private:
    void initFormantTable();
    std::vector<std::string> textToPhonemes(const std::string& text, const std::string& langCode);
    void synthesizePhoneme(
        const FormantParams& fp,
        float durationSec,
        float pitchHz,
        float energy,
        std::vector<float>& outPcm,
        int sampleRate = 16000
    );

    std::unordered_map<std::string, FormantParams> phonemeFormants_;
    std::unique_ptr<VoiceToneCloner> toneCloner_;
};
