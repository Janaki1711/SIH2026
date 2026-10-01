#include "WhisperSTTEngine.hpp"

#include "whisper.h"
#include <android/log.h>
#include <chrono>

#define LOG_TAG "WhisperSTTEngine"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGW(...) __android_log_print(ANDROID_LOG_WARN, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

WhisperSTTEngine::~WhisperSTTEngine() {
    if (m_ctx) {
        whisper_free(m_ctx);
        m_ctx = nullptr;
    }
}

// Target-language initial prompt — the collapse guard proven in the CER gate
// (without it, short Telugu utterances collapsed to "." or flipped scripts).
static const char* promptFor(const std::string& lang) {
    if (lang == "te") return "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41.";  // తెలుగు.
    if (lang == "ta") return "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd.";          // தமிழ்.
    if (lang == "kn") return "\u0c95\u0ca8\u0ccd\u0ca8\u0cad.";         // ಕನ್ನಡ.
    if (lang == "ml") return "\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02.";   // മലയാളം.
    return nullptr;
}

// Native-script Unicode block for the gated languages.
static bool scriptRangeFor(const std::string& lang, uint32_t& lo, uint32_t& hi) {
    if (lang == "ta") { lo = 0x0B80; hi = 0x0BFF; return true; }
    if (lang == "te") { lo = 0x0C00; hi = 0x0C7F; return true; }
    if (lang == "kn") { lo = 0x0C80; hi = 0x0CFF; return true; }
    if (lang == "ml") { lo = 0x0D00; hi = 0x0D7F; return true; }
    return false;
}

// Decode UTF-8 and count (a) all letters we care about (Latin + Indic
// U+0900..U+0D7F) and (b) letters inside the expected native-script block.
static void scanOutput(const std::string& text, uint32_t lo, uint32_t hi,
                       size_t& letters, size_t& targetLetters) {
    letters = targetLetters = 0;
    size_t i = 0;
    const size_t n = text.size();
    while (i < n) {
        const unsigned char c = static_cast<unsigned char>(text[i]);
        uint32_t cp = 0;
        size_t len = 1;
        if (c < 0x80) { cp = c; }
        else if ((c >> 5) == 6) { cp = c & 0x1F; len = 2; }
        else if ((c >> 4) == 14) { cp = c & 0x0F; len = 3; }
        else if ((c >> 3) == 30) { cp = c & 0x07; len = 4; }
        else { i++; continue; }
        if (i + len > n) break;
        bool ok = true;
        for (size_t k = 1; k < len; k++) {
            const unsigned char cc = static_cast<unsigned char>(text[i + k]);
            if ((cc & 0xC0) != 0x80) { ok = false; break; }
            cp = (cp << 6) | (cc & 0x3F);
        }
        i += len;
        if (!ok) continue;

        const bool isLetter =
            (cp >= 'A' && cp <= 'Z') || (cp >= 'a' && cp <= 'z') ||
            (cp >= 0x0900 && cp <= 0x0D7F);
        if (isLetter) {
            letters++;
            if (cp >= lo && cp <= hi) targetLetters++;
        }
    }
}

bool WhisperSTTEngine::init(const std::string& modelPath) {
    if (modelPath.empty()) {
        LOGE("init: empty model path");
        return false;
    }
    whisper_context_params cparams = whisper_context_default_params();
    cparams.use_gpu = false;   // Android build is CPU-only ggml
    m_ctx = whisper_init_from_file_with_params(modelPath.c_str(), cparams);
    if (!m_ctx) {
        LOGE("init: failed to load model from %s", modelPath.c_str());
        return false;
    }
    LOGI("model loaded: %s", modelPath.c_str());
    return true;
}

std::string WhisperSTTEngine::transcribe(const std::vector<float>& pcm,
                                         const std::string& lang) {
    if (!m_ctx || pcm.empty()) return "";

    uint32_t lo = 0, hi = 0;
    if (!scriptRangeFor(lang, lo, hi)) {
        LOGW("transcribe: language '%s' not in whisper gate (te/ta/kn/ml) — refusing", lang.c_str());
        return "";
    }
    const char* prompt = promptFor(lang);
    if (!prompt) return "";

    // Exact configuration that passed the CER gate (avg 0.169 vs conformer
    // 0.368; greedy+best_of1 == beam5 quality at ~40% less decode time):
    //   greedy, best_of=1, temperature_inc=0 (NO fallback — the fallback
    //   caused Tamil-script flips and hallucinated truncations),
    //   no_timestamps, target-language initial_prompt, language forced.
    // no_context=true because the gate ran each sample in a fresh process;
    // on-device the context is reused across utterances, so past text must
    // not leak into the next decode.
    whisper_full_params wparams = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    wparams.strategy = WHISPER_SAMPLING_GREEDY;
    wparams.greedy.best_of = 1;
    wparams.temperature = 0.0f;
    wparams.temperature_inc = 0.0f;   // -nf: disable temperature fallback
    wparams.no_timestamps = true;     // -nt
    wparams.no_context = true;
    wparams.print_progress = false;
    wparams.print_realtime = false;
    wparams.print_special = false;
    wparams.translate = false;
    wparams.detect_language = false;
    wparams.language = lang.c_str();
    wparams.initial_prompt = prompt;
    wparams.carry_initial_prompt = false;
    wparams.n_threads = 4;

    const auto t0 = std::chrono::steady_clock::now();
    if (whisper_full(m_ctx, wparams, pcm.data(), static_cast<int>(pcm.size())) != 0) {
        LOGW("transcribe: whisper_full failed for lang=%s", lang.c_str());
        return "";
    }

    std::string out;
    const int nSeg = whisper_full_n_segments(m_ctx);
    for (int i = 0; i < nSeg; i++) {
        const char* seg = whisper_full_get_segment_text(m_ctx, i);
        if (seg) out += seg;
    }
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - t0).count();

    // Trim leading/trailing whitespace.
    const auto first = out.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) out.clear();
    else {
        const auto last = out.find_last_not_of(" \t\r\n");
        out = out.substr(first, last - first + 1);
    }

    // ---- Collapse guard (contract: return "" → caller falls back) ----
    size_t letters = 0, targetLetters = 0;
    scanOutput(out, lo, hi, letters, targetLetters);
    const double durSec = static_cast<double>(pcm.size()) / 16000.0;
    const size_t minLetters = static_cast<size_t>(
        durSec * 0.5 > 3.0 ? durSec * 0.5 : 3.0);
    const size_t maxLetters = static_cast<size_t>(durSec * 30.0) + 15;

    bool reject = false;
    const char* why = "";
    if (out.empty() || letters < minLetters) {
        reject = true; why = "too short / empty (collapse)";
    } else if (letters > maxLetters) {
        reject = true; why = "runaway output (hallucination)";
    } else if (targetLetters < 2 || targetLetters * 3 < letters) {
        // Wrong-script flip (e.g. Tamil under te) or Latin-heavy garbage.
        reject = true; why = "wrong-script / script mismatch";
    }

    if (reject) {
        LOGW("collapse guard REJECTED [%s] (%s): letters=%zu target=%zu dur=%.1fs out='%s'",
             lang.c_str(), why, letters, targetLetters, durSec, out.c_str());
        return "";
    }

    LOGI("whisper[%s] %.1fs audio -> %zu letters in %lld ms: %s",
         lang.c_str(), durSec, letters, static_cast<long long>(ms), out.c_str());
    return out;
}
