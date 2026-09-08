#pragma once

#include <vector>
#include <cmath>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

class MelSpectrogramExtractor {
public:
    static constexpr int kSampleRate = 16000;
    static constexpr int kWindowSize = 400; // 25ms
    static constexpr int kHopSize = 160;    // 10ms
    static constexpr int kFftSize = 512;
    static constexpr int kNumMels = 80;

    MelSpectrogramExtractor() {
        initFilterbanks();
    }

    void extract(const std::vector<float>& pcm, std::vector<float>& outMel, int64_t& outFrames) {
        if (pcm.size() < kWindowSize) {
            outFrames = 0;
            outMel.clear();
            return;
        }

        // Apply pre-emphasis filter (0.97) to enhance speech formants
        std::vector<float> audio = pcm;
        for (int i = static_cast<int>(audio.size()) - 1; i > 0; --i) {
            audio[i] -= 0.97f * audio[i - 1];
        }
        audio[0] *= (1.0f - 0.97f);

        outFrames = (audio.size() - kWindowSize) / kHopSize + 1;
        outMel.assign(kNumMels * outFrames, 0.0f);

        std::vector<float> real(kFftSize, 0.0f);
        std::vector<float> imag(kFftSize, 0.0f);

        for (int64_t f = 0; f < outFrames; ++f) {
            size_t offset = f * kHopSize;

            for (int i = 0; i < kWindowSize; ++i) {
                // Periodic Hann window matching NeMo / Torchaudio
                float window = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / kWindowSize));
                real[i] = audio[offset + i] * window;
                imag[i] = 0.0f;
            }
            for (int i = kWindowSize; i < kFftSize; ++i) {
                real[i] = 0.0f;
                imag[i] = 0.0f;
            }

            fftRadix2(real, imag);

            for (int m = 0; m < kNumMels; ++m) {
                float energy = 0.0f;
                for (const auto& pair : m_filterbanks[m]) {
                    float power = real[pair.first] * real[pair.first] + imag[pair.first] * imag[pair.first];
                    energy += power * pair.second;
                }
                outMel[m * outFrames + f] = std::log(std::max(energy, 1e-5f));
            }
        }

        // Apply per-feature normalization (mean=0, std=1 per mel bin) matching NeMo preprocessor
        if (outFrames > 1) {
            for (int m = 0; m < kNumMels; ++m) {
                float sum = 0.0f;
                for (int64_t f = 0; f < outFrames; ++f) {
                    sum += outMel[m * outFrames + f];
                }
                float mean = sum / static_cast<float>(outFrames);
                float sqSum = 0.0f;
                for (int64_t f = 0; f < outFrames; ++f) {
                    float diff = outMel[m * outFrames + f] - mean;
                    sqSum += diff * diff;
                }
                float stdDev = std::sqrt(sqSum / static_cast<float>(outFrames) + 1e-5f);
                for (int64_t f = 0; f < outFrames; ++f) {
                    outMel[m * outFrames + f] = (outMel[m * outFrames + f] - mean) / stdDev;
                }
            }
        }
    }

private:
    std::vector<std::vector<std::pair<int, float>>> m_filterbanks;

    static float hzToMelSlaney(float hz) {
        float f_sp = 200.0f / 3.0f;
        float min_log_hz = 1000.0f;
        float min_log_mel = min_log_hz / f_sp;
        float logstep = std::log(6.4f) / 27.0f;
        if (hz >= min_log_hz) {
            return min_log_mel + std::log(hz / min_log_hz) / logstep;
        }
        return hz / f_sp;
    }

    static float melToHzSlaney(float mel) {
        float f_sp = 200.0f / 3.0f;
        float min_log_hz = 1000.0f;
        float min_log_mel = min_log_hz / f_sp;
        float logstep = std::log(6.4f) / 27.0f;
        if (mel >= min_log_mel) {
            return min_log_hz * std::exp(logstep * (mel - min_log_mel));
        }
        return f_sp * mel;
    }

    void initFilterbanks() {
        m_filterbanks.resize(kNumMels);
        int n_freqs = kFftSize / 2 + 1; // 257

        float melLow = hzToMelSlaney(0.0f);
        float melHigh = hzToMelSlaney(kSampleRate / 2.0f);

        std::vector<float> hzPoints(kNumMels + 2);
        for (int i = 0; i < kNumMels + 2; ++i) {
            float m = melLow + static_cast<float>(i) * (melHigh - melLow) / static_cast<float>(kNumMels + 1);
            hzPoints[i] = melToHzSlaney(m);
        }

        for (int m = 0; m < kNumMels; ++m) {
            float left = hzPoints[m];
            float center = hzPoints[m + 1];
            float right = hzPoints[m + 2];
            // Slaney triangular area normalization
            float norm = 2.0f / (right - left);

            for (int k = 0; k < n_freqs; ++k) {
                float f = static_cast<float>(k) * kSampleRate / static_cast<float>(kFftSize);
                if (f > left && f <= center) {
                    m_filterbanks[m].emplace_back(k, ((f - left) / (center - left)) * norm);
                } else if (f > center && f < right) {
                    m_filterbanks[m].emplace_back(k, ((right - f) / (right - center)) * norm);
                }
            }
        }
    }

    static void fftRadix2(std::vector<float>& real, std::vector<float>& imag) {
        const int n = kFftSize;
        for (int i = 1, j = 0; i < n; ++i) {
            int bit = n >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) {
                std::swap(real[i], real[j]);
                std::swap(imag[i], imag[j]);
            }
        }
        for (int len = 2; len <= n; len <<= 1) {
            float angle = -2.0f * M_PI / len;
            float wlen_r = std::cos(angle);
            float wlen_i = std::sin(angle);
            for (int i = 0; i < n; i += len) {
                float w_r = 1.0f;
                float w_i = 0.0f;
                for (int j = 0; j < len / 2; ++j) {
                    float u_r = real[i + j];
                    float u_i = imag[i + j];
                    float v_r = real[i + j + len / 2] * w_r - imag[i + j + len / 2] * w_i;
                    float v_i = real[i + j + len / 2] * w_i + imag[i + j + len / 2] * w_r;
                    real[i + j] = u_r + v_r;
                    imag[i + j] = u_i + v_i;
                    real[i + j + len / 2] = u_r - v_r;
                    imag[i + j + len / 2] = u_i - v_i;
                    float next_w_r = w_r * wlen_r - w_i * wlen_i;
                    w_i = w_r * wlen_i + w_i * wlen_r;
                    w_r = next_w_r;
                }
            }
        }
    }
};
