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

        outFrames = (pcm.size() - kWindowSize) / kHopSize + 1;
        outMel.assign(kNumMels * outFrames, 0.0f);

        std::vector<float> real(kFftSize, 0.0f);
        std::vector<float> imag(kFftSize, 0.0f);
        std::vector<float> power(kFftSize / 2 + 1, 0.0f);

        for (int64_t f = 0; f < outFrames; ++f) {
            size_t offset = f * kHopSize;

            for (int i = 0; i < kWindowSize; ++i) {
                float window = 0.5f * (1.0f - std::cos(2.0f * M_PI * i / (kWindowSize - 1)));
                real[i] = pcm[offset + i] * window;
                imag[i] = 0.0f;
            }
            for (int i = kWindowSize; i < kFftSize; ++i) {
                real[i] = 0.0f;
                imag[i] = 0.0f;
            }

            fftRadix2(real, imag);

            for (int k = 0; k <= kFftSize / 2; ++k) {
                power[k] = real[k] * real[k] + imag[k] * imag[k];
            }

            for (int m = 0; m < kNumMels; ++m) {
                float energy = 0.0f;
                for (const auto& pair : m_filterbanks[m]) {
                    energy += power[pair.first] * pair.second;
                }
                outMel[m * outFrames + f] = std::log(std::max(energy, 1e-5f));
            }
        }
    }

private:
    std::vector<std::vector<std::pair<int, float>>> m_filterbanks;

    static float hzToMel(float hz) {
        return 2595.0f * std::log10(1.0f + hz / 700.0f);
    }

    static float melToHz(float mel) {
        return 700.0f * (std::pow(10.0f, mel / 2595.0f) - 1.0f);
    }

    void initFilterbanks() {
        m_filterbanks.resize(kNumMels);
        float melLow = hzToMel(0.0f);
        float melHigh = hzToMel(kSampleRate / 2.0f);
        float melStep = (melHigh - melLow) / (kNumMels + 1);

        std::vector<int> binPoints(kNumMels + 2);
        for (int i = 0; i < kNumMels + 2; ++i) {
            float hz = melToHz(melLow + i * melStep);
            binPoints[i] = static_cast<int>(std::floor((kFftSize + 1) * hz / kSampleRate));
        }

        for (int m = 0; m < kNumMels; ++m) {
            int left = binPoints[m];
            int center = binPoints[m + 1];
            int right = binPoints[m + 2];

            for (int k = left; k < center; ++k) {
                if (k >= 0 && k <= kFftSize / 2 && center > left) {
                    float weight = static_cast<float>(k - left) / (center - left);
                    m_filterbanks[m].emplace_back(k, weight);
                }
            }
            for (int k = center; k < right; ++k) {
                if (k >= 0 && k <= kFftSize / 2 && right > center) {
                    float weight = static_cast<float>(right - k) / (right - center);
                    m_filterbanks[m].emplace_back(k, weight);
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
