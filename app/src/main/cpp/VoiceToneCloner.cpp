#include "VoiceToneCloner.hpp"
#include <cmath>
#include <algorithm>
#include <cstring>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

VoiceToneCloner::VoiceToneCloner() {}

ProsodyVector VoiceToneCloner::extractFeatures(const float* audioPCM, size_t sampleCount, int sampleRate) {
    ProsodyVector vec{};
    vec.f0_pitch_mean = 140.0f;
    vec.f0_pitch_variance = 15.0f;
    vec.cadence_rate = 1.0f;
    vec.rms_energy = 0.5f;
    vec.urgency_level = 0;
    vec.reserved[0] = 0;
    vec.reserved[1] = 0;
    vec.reserved[2] = 0;

    if (sampleCount == 0 || audioPCM == nullptr) {
        return vec;
    }

    double sumSq = 0.0;
    for (size_t i = 0; i < sampleCount; ++i) {
        sumSq += static_cast<double>(audioPCM[i]) * static_cast<double>(audioPCM[i]);
    }
    vec.rms_energy = std::clamp(static_cast<float>(std::sqrt(sumSq / sampleCount)), 0.0f, 1.0f);

    int minLag = sampleRate / 400;
    int maxLag = sampleRate / 60;
    float bestCorr = -1.0f;
    int bestLag = minLag;

    for (int lag = minLag; lag <= maxLag && (static_cast<size_t>(lag) < sampleCount); ++lag) {
        float corr = 0.0f;
        size_t N = std::min(sampleCount - lag, static_cast<size_t>(1024));
        for (size_t i = 0; i < N; ++i) {
            corr += audioPCM[i] * audioPCM[i + lag];
        }
        if (corr > bestCorr) {
            bestCorr = corr;
            bestLag = lag;
        }
    }

    if (bestLag > 0) {
        vec.f0_pitch_mean = static_cast<float>(sampleRate) / static_cast<float>(bestLag);
        vec.f0_pitch_variance = 12.0f;
    }

    return vec;
}

void VoiceToneCloner::applyProsody(
    const std::vector<float>& inputAudio,
    const ProsodyVector& prosody,
    std::vector<float>& outputAudio,
    int /*sampleRate*/
) {
    if (inputAudio.empty()) {
        outputAudio.clear();
        return;
    }

    float energyGain = (prosody.rms_energy > 0.01f) ? (prosody.rms_energy / 0.3f) : 1.0f;
    energyGain = std::clamp(energyGain, 0.5f, 3.0f);

    outputAudio.resize(inputAudio.size());
    for (size_t i = 0; i < inputAudio.size(); ++i) {
        outputAudio[i] = std::clamp(inputAudio[i] * energyGain, -1.0f, 1.0f);
    }
}

std::vector<float> VoiceToneCloner::generateEmergencySiren(float durationSeconds, int sampleRate) {
    size_t totalSamples = static_cast<size_t>(durationSeconds * sampleRate);
    std::vector<float> siren(totalSamples);

    double phase = 0.0;
    for (size_t i = 0; i < totalSamples; ++i) {
        float progress = static_cast<float>(i) / static_cast<float>(totalSamples);
        float currentFreq = 880.0f + 880.0f * (0.5f + 0.5f * std::sin(2.0 * M_PI * 4.0 * progress));
        phase += 2.0 * M_PI * currentFreq / sampleRate;
        if (phase >= 2.0 * M_PI) phase -= 2.0 * M_PI;

        siren[i] = static_cast<float>(std::sin(phase));
    }
    return siren;
}

std::vector<uint8_t> VoiceToneCloner::serializeVector(const ProsodyVector& vec) {
    std::vector<uint8_t> data(sizeof(ProsodyVector));
    std::memcpy(data.data(), &vec, sizeof(ProsodyVector));
    return data;
}

ProsodyVector VoiceToneCloner::deserializeVector(const uint8_t* data, size_t length) {
    ProsodyVector vec{};
    if (data != nullptr && length >= sizeof(ProsodyVector)) {
        std::memcpy(&vec, data, sizeof(ProsodyVector));
    }
    return vec;
}
