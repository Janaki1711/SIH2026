#pragma once

// WhisperSTTEngine — on-device speech-to-text via whisper.cpp.
//
// Ships parambharat/whisper-tiny-south-indic (41 MB int8, ggml q8_0) and is
// used ONLY for te/ta/kn/ml — the languages where the AI4Bharat conformer
// encoder produces poor CER (benchmark: /tmp/opencode/sttlab/RESULTS.md).
// The remaining app languages (hi/mr/bn/pa/gu/or) keep the conformer path.
//
// Decode config is the exact combination that passed the CER gate
// (avg CER 0.169 vs conformer's 0.368 across 8 samples, deterministic):
//   beam search 5, temperature_inc = 0 (NO temperature fallback — the
//   fallback caused Tamil-script flips and hallucinated truncations),
//   no timestamps, target-language initial prompt.
//
// A collapse guard rejects empty/low-density/wrong-script output and
// returns "" so the caller falls back to the conformer transcript.

#include <string>
#include <vector>
#include <cstddef>

struct whisper_context;

class WhisperSTTEngine {
public:
    WhisperSTTEngine() = default;
    ~WhisperSTTEngine();

    WhisperSTTEngine(const WhisperSTTEngine&) = delete;
    WhisperSTTEngine& operator=(const WhisperSTTEngine&) = delete;

    // Load ggml model from disk. Returns false on any failure (the caller
    // then keeps using the conformer path only).
    bool init(const std::string& modelPath);

    bool isReady() const { return m_ctx != nullptr; }

    // Transcribe 16 kHz mono float PCM in the given ISO language code
    // ("te","ta","kn","ml"). Returns native-script transcript, or "" if
    // decoding failed or the collapse guard rejected the output.
    std::string transcribe(const std::vector<float>& pcm, const std::string& lang);

private:
    whisper_context* m_ctx = nullptr;
};
