#pragma once

#include <vector>
#include <cstdint>
#include <string>

#pragma pack(push, 1)
struct ProsodyVector {
    float f0_pitch_mean;     // Fundamental frequency mean (Hz)
    float f0_pitch_variance; // Pitch deviation (Hz)
    float cadence_rate;      // Speaking rate factor (0.5 to 2.0)
    float rms_energy;        // Root Mean Square energy (0.0 to 1.0)
    uint8_t urgency_level;   // 0 = Normal, 1 = Priority, 2 = Emergency SOS
    uint8_t reserved[3];     // Padding
};
#pragma pack(pop)

class VoiceToneCloner {
public:
    VoiceToneCloner();
    ~VoiceToneCloner() = default;

    ProsodyVector extractFeatures(const float* audioPCM, size_t sampleCount, int sampleRate = 16000);

    void applyProsody(
        const std::vector<float>& inputAudio,
        const ProsodyVector& prosody,
        std::vector<float>& outputAudio,
        int sampleRate = 16000
    );

    std::vector<float> generateEmergencySiren(float durationSeconds = 1.0f, int sampleRate = 16000);

    std::vector<uint8_t> serializeVector(const ProsodyVector& vec);
    ProsodyVector deserializeVector(const uint8_t* data, size_t length);
};
