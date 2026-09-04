#include "IndicTTSEngine.hpp"
#include <cmath>
#include <algorithm>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

IndicTTSEngine::IndicTTSEngine()
    : toneCloner_(std::make_unique<VoiceToneCloner>()) {
    initFormantTable();
}

bool IndicTTSEngine::initialize(const std::string& /*modelAssetsDir*/) {
    return true;
}

std::vector<std::string> IndicTTSEngine::getSupportedLanguages() const {
    return {"hi", "gu", "mr", "kn", "ml", "ta", "te", "or", "bn", "en"};
}

void IndicTTSEngine::initFormantTable() {
    phonemeFormants_["a"] = {800.0f, 1200.0f, 2500.0f, 80.0f, 90.0f, 120.0f};
    phonemeFormants_["aa"] = {750.0f, 1100.0f, 2400.0f, 80.0f, 90.0f, 120.0f};
    phonemeFormants_["i"] = {300.0f, 2200.0f, 3000.0f, 60.0f, 100.0f, 150.0f};
    phonemeFormants_["ee"] = {280.0f, 2300.0f, 3100.0f, 60.0f, 100.0f, 150.0f};
    phonemeFormants_["u"] = {350.0f, 800.0f, 2250.0f, 70.0f, 80.0f, 100.0f};
    phonemeFormants_["oo"] = {320.0f, 750.0f, 2200.0f, 70.0f, 80.0f, 100.0f};
    phonemeFormants_["e"] = {500.0f, 1800.0f, 2600.0f, 70.0f, 90.0f, 130.0f};
    phonemeFormants_["ai"] = {600.0f, 1950.0f, 2700.0f, 75.0f, 95.0f, 135.0f};
    phonemeFormants_["o"] = {500.0f, 950.0f, 2400.0f, 70.0f, 85.0f, 120.0f};
    phonemeFormants_["au"] = {600.0f, 1000.0f, 2450.0f, 75.0f, 90.0f, 125.0f};

    phonemeFormants_["k"] = {300.0f, 1500.0f, 2500.0f, 150.0f, 150.0f, 200.0f};
    phonemeFormants_["t"] = {350.0f, 1700.0f, 2700.0f, 120.0f, 120.0f, 180.0f};
    phonemeFormants_["p"] = {300.0f, 900.0f, 2200.0f, 140.0f, 140.0f, 190.0f};
    phonemeFormants_["s"] = {400.0f, 1600.0f, 4000.0f, 200.0f, 200.0f, 300.0f};
    phonemeFormants_["m"] = {250.0f, 1000.0f, 2200.0f, 50.0f, 100.0f, 150.0f};
    phonemeFormants_["n"] = {280.0f, 1500.0f, 2400.0f, 50.0f, 100.0f, 150.0f};
    phonemeFormants_["r"] = {400.0f, 1300.0f, 1700.0f, 80.0f, 100.0f, 120.0f};
    phonemeFormants_["l"] = {380.0f, 1200.0f, 2600.0f, 70.0f, 100.0f, 140.0f};
    phonemeFormants_["sil"] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
}

std::vector<std::string> IndicTTSEngine::textToPhonemes(const std::string& text, const std::string& /*langCode*/) {
    std::vector<std::string> phonemes;
    if (text.empty()) return phonemes;

    for (size_t i = 0; i < text.length(); ++i) {
        char c = text[i];
        if (c == ' ' || c == ',' || c == '.' || c == '!') {
            phonemes.push_back("sil");
        } else if (c == 'a' || c == 'A') {
            phonemes.push_back("a");
        } else if (c == 'i' || c == 'I') {
            phonemes.push_back("i");
        } else if (c == 'u' || c == 'U') {
            phonemes.push_back("u");
        } else if (c == 'e' || c == 'E') {
            phonemes.push_back("e");
        } else if (c == 'o' || c == 'O') {
            phonemes.push_back("o");
        } else if (c == 'm' || c == 'M') {
            phonemes.push_back("m");
        } else if (c == 'n' || c == 'N') {
            phonemes.push_back("n");
        } else if (c == 's' || c == 'S') {
            phonemes.push_back("s");
        } else if (c == 'r' || c == 'R') {
            phonemes.push_back("r");
        } else if (c == 't' || c == 'T') {
            phonemes.push_back("t");
        } else if (c == 'k' || c == 'K') {
            phonemes.push_back("k");
        } else {
            if ((static_cast<unsigned char>(c) & 0xC0) != 0x80) {
                phonemes.push_back("a");
            }
        }
    }
    return phonemes;
}

void IndicTTSEngine::synthesizePhoneme(
    const FormantParams& fp,
    float durationSec,
    float pitchHz,
    float energy,
    std::vector<float>& outPcm,
    int sampleRate
) {
    size_t sampleCount = static_cast<size_t>(durationSec * sampleRate);
    if (sampleCount == 0) return;

    if (fp.f1 == 0.0f) {
        outPcm.insert(outPcm.end(), sampleCount, 0.0f);
        return;
    }

    auto getFilterCoeffs = [sampleRate](float freq, float bw, float& a1, float& a2, float& b0) {
        float r = std::exp(-M_PI * bw / sampleRate);
        float omega = 2.0f * M_PI * freq / sampleRate;
        a1 = -2.0f * r * std::cos(omega);
        a2 = r * r;
        b0 = 1.0f - r;
    };

    float a1_1, a2_1, b0_1;
    float a1_2, a2_2, b0_2;
    float a1_3, a2_3, b0_3;

    getFilterCoeffs(fp.f1, fp.bw1, a1_1, a2_1, b0_1);
    getFilterCoeffs(fp.f2, fp.bw2, a1_2, a2_2, b0_2);
    getFilterCoeffs(fp.f3, fp.bw3, a1_3, a2_3, b0_3);

    float y1_1 = 0.0f, y2_1 = 0.0f;
    float y1_2 = 0.0f, y2_2 = 0.0f;
    float y1_3 = 0.0f, y2_3 = 0.0f;

    double glottalPhase = 0.0;
    double glottalInc = 2.0 * M_PI * pitchHz / sampleRate;

    for (size_t i = 0; i < sampleCount; ++i) {
        float excitation = 0.0f;
        float normPhase = static_cast<float>(glottalPhase / (2.0 * M_PI));
        if (normPhase < 0.6f) {
            excitation = 3.0f * std::pow(normPhase / 0.6f, 2.0f) - 2.0f * std::pow(normPhase / 0.6f, 3.0f);
        } else {
            excitation = 1.0f - (normPhase - 0.6f) / 0.4f;
        }

        glottalPhase += glottalInc;
        if (glottalPhase >= 2.0 * M_PI) glottalPhase -= 2.0 * M_PI;

        float out1 = b0_1 * excitation - a1_1 * y1_1 - a2_1 * y2_1;
        y2_1 = y1_1;
        y1_1 = out1;

        float out2 = b0_2 * excitation - a1_2 * y1_2 - a2_2 * y2_2;
        y2_2 = y1_2;
        y1_2 = out2;

        float out3 = b0_3 * excitation - a1_3 * y1_3 - a2_3 * y2_3;
        y2_3 = y1_3;
        y1_3 = out3;

        float mixed = (out1 * 0.5f + out2 * 0.3f + out3 * 0.2f) * energy;
        outPcm.push_back(std::clamp(mixed, -1.0f, 1.0f));
    }
}

void IndicTTSEngine::synthesize(
    const std::string& text,
    const std::string& langCode,
    const ProsodyVector& prosody,
    std::vector<float>& outAudioPCM,
    int sampleRate
) {
    outAudioPCM.clear();
    std::vector<std::string> phonemes = textToPhonemes(text, langCode);

    float pitch = (prosody.f0_pitch_mean > 50.0f) ? prosody.f0_pitch_mean : 140.0f;
    float cadence = (prosody.cadence_rate > 0.1f) ? prosody.cadence_rate : 1.0f;
    float energy = (prosody.rms_energy > 0.0f) ? prosody.rms_energy : 0.6f;

    float baseDur = 0.08f / cadence;

    for (const auto& ph : phonemes) {
        auto it = phonemeFormants_.find(ph);
        if (it != phonemeFormants_.end()) {
            synthesizePhoneme(it->second, baseDur, pitch, energy, outAudioPCM, sampleRate);
        } else {
            synthesizePhoneme(phonemeFormants_["a"], baseDur, pitch, energy, outAudioPCM, sampleRate);
        }
    }
}
