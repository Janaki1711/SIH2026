#include "IndicTTSEngine.hpp"
#include <cmath>
#include <algorithm>
#include <sstream>
#include <vector>
#include <cstdint>

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
    // Vowels (F1, F2, F3, BW1, BW2, BW3)
    phonemeFormants_["a"]   = {800.0f, 1200.0f, 2500.0f, 80.0f, 90.0f, 120.0f};  // अ
    phonemeFormants_["aa"]  = {750.0f, 1100.0f, 2400.0f, 80.0f, 90.0f, 120.0f};  // आ
    phonemeFormants_["i"]   = {300.0f, 2200.0f, 3000.0f, 60.0f, 100.0f, 150.0f}; // इ, ि
    phonemeFormants_["ee"]  = {280.0f, 2300.0f, 3100.0f, 60.0f, 100.0f, 150.0f}; // ई, ी
    phonemeFormants_["u"]   = {350.0f, 800.0f,  2250.0f, 70.0f, 80.0f,  100.0f}; // उ, ु
    phonemeFormants_["oo"]  = {320.0f, 750.0f,  2200.0f, 70.0f, 80.0f,  100.0f}; // ऊ, ू
    phonemeFormants_["e"]   = {500.0f, 1800.0f, 2600.0f, 70.0f, 90.0f, 130.0f}; // ए, े
    phonemeFormants_["ai"]  = {600.0f, 1950.0f, 2700.0f, 75.0f, 95.0f, 135.0f}; // ऐ, ै
    phonemeFormants_["o"]   = {500.0f, 950.0f,  2400.0f, 70.0f, 85.0f, 120.0f}; // ओ, ो
    phonemeFormants_["au"]  = {600.0f, 1000.0f, 2450.0f, 75.0f, 90.0f, 125.0f}; // औ, ौ

    // Consonants
    phonemeFormants_["k"]   = {300.0f, 1500.0f, 2500.0f, 150.0f, 150.0f, 200.0f}; // क, க, క, ಕ
    phonemeFormants_["kh"]  = {320.0f, 1550.0f, 2550.0f, 160.0f, 150.0f, 200.0f}; // ख
    phonemeFormants_["g"]   = {350.0f, 1400.0f, 2400.0f, 140.0f, 140.0f, 190.0f}; // ग, గ, ಗ, ഗ
    phonemeFormants_["gh"]  = {360.0f, 1420.0f, 2420.0f, 150.0f, 140.0f, 190.0f}; // घ
    phonemeFormants_["ch"]  = {400.0f, 1800.0f, 2800.0f, 160.0f, 160.0f, 210.0f}; // च, ச, చ, ಚ
    phonemeFormants_["j"]   = {380.0f, 1750.0f, 2700.0f, 150.0f, 150.0f, 200.0f}; // ज, జ, ಜ, ജ
    phonemeFormants_["t"]   = {350.0f, 1700.0f, 2700.0f, 120.0f, 120.0f, 180.0f}; // त, த, త, ತ, ത
    phonemeFormants_["th"]  = {360.0f, 1720.0f, 2720.0f, 130.0f, 120.0f, 180.0f}; // थ
    phonemeFormants_["d"]   = {380.0f, 1600.0f, 2600.0f, 130.0f, 130.0f, 190.0f}; // द, ద, ದ, ദ
    phonemeFormants_["dh"]  = {390.0f, 1620.0f, 2620.0f, 140.0f, 130.0f, 190.0f}; // ध
    phonemeFormants_["n"]   = {280.0f, 1500.0f, 2400.0f, 50.0f,  100.0f, 150.0f}; // न, ந, న, ನ, ന
    phonemeFormants_["p"]   = {300.0f, 900.0f,  2200.0f, 140.0f, 140.0f, 190.0f}; // प, ப, ప, ಪ, പ
    phonemeFormants_["ph"]  = {310.0f, 920.0f,  2220.0f, 150.0f, 140.0f, 190.0f}; // फ
    phonemeFormants_["b"]   = {320.0f, 1000.0f, 2300.0f, 130.0f, 130.0f, 180.0f}; // ब, బ, ಬ, ബ
    phonemeFormants_["bh"]  = {330.0f, 1020.0f, 2320.0f, 140.0f, 130.0f, 180.0f}; // भ
    phonemeFormants_["m"]   = {250.0f, 1000.0f, 2200.0f, 50.0f,  100.0f, 150.0f}; // म, ம, మ, ಮ, മ
    phonemeFormants_["y"]   = {300.0f, 2000.0f, 2800.0f, 70.0f,  100.0f, 140.0f}; // य, ய, య, ಯ, യ
    phonemeFormants_["r"]   = {400.0f, 1300.0f, 1700.0f, 80.0f,  100.0f, 120.0f}; // र, ர, ర, ರ, ര
    phonemeFormants_["l"]   = {380.0f, 1200.0f, 2600.0f, 70.0f,  100.0f, 140.0f}; // ल, ல, ల, ಲ, ല
    phonemeFormants_["v"]   = {320.0f, 1100.0f, 2400.0f, 80.0f,  100.0f, 150.0f}; // व, வ, వ, ವ, വ
    phonemeFormants_["s"]   = {400.0f, 1600.0f, 4000.0f, 200.0f, 200.0f, 300.0f}; // स, ஸ, స, ಸ, സ
    phonemeFormants_["sh"]  = {380.0f, 1900.0f, 3500.0f, 180.0f, 180.0f, 250.0f}; // श, ஷ, శ, ಶ, ശ
    phonemeFormants_["h"]   = {450.0f, 1400.0f, 2400.0f, 150.0f, 150.0f, 200.0f}; // ह, ஹ, హ, ಹ, ഹ

    phonemeFormants_["sil"] = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
}

// Convert Unicode string (across 10 Indic scripts) to sequence of phonetic formants
std::vector<std::string> IndicTTSEngine::textToPhonemes(const std::string& text, const std::string& /*langCode*/) {
    std::vector<std::string> phonemes;
    if (text.empty()) return phonemes;

    size_t i = 0;
    while (i < text.length()) {
        uint32_t codepoint = 0;
        unsigned char c = static_cast<unsigned char>(text[i]);

        if (c < 0x80) {
            // 1-byte ASCII
            codepoint = c;
            i += 1;
        } else if ((c & 0xE0) == 0xC0 && i + 1 < text.length()) {
            // 2-byte UTF-8
            codepoint = ((c & 0x1F) << 6) | (static_cast<unsigned char>(text[i + 1]) & 0x3F);
            i += 2;
        } else if ((c & 0xF0) == 0xE0 && i + 2 < text.length()) {
            // 3-byte UTF-8 (Devanagari, Bengali, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam)
            codepoint = ((c & 0x0F) << 12) |
                        ((static_cast<unsigned char>(text[i + 1]) & 0x3F) << 6) |
                        (static_cast<unsigned char>(text[i + 2]) & 0x3F);
            i += 3;
        } else if ((c & 0xF8) == 0xF0 && i + 3 < text.length()) {
            // 4-byte UTF-8
            codepoint = ((c & 0x07) << 18) |
                        ((static_cast<unsigned char>(text[i + 1]) & 0x3F) << 12) |
                        ((static_cast<unsigned char>(text[i + 2]) & 0x3F) << 6) |
                        (static_cast<unsigned char>(text[i + 3]) & 0x3F);
            i += 4;
        } else {
            i += 1;
            continue;
        }

        // 1. Punctuation / Whitespace
        if (codepoint == ' ' || codepoint == ',' || codepoint == '.' ||
            codepoint == '!' || codepoint == '?' || codepoint == 0x0964 || codepoint == 0x0965) {
            phonemes.push_back("sil");
            continue;
        }

        // 2. ASCII Latin characters (English)
        if (codepoint < 0x80) {
            char asciiChar = static_cast<char>(std::tolower(static_cast<int>(codepoint)));
            switch (asciiChar) {
                case 'a': phonemes.push_back("a"); break;
                case 'b': phonemes.push_back("b"); phonemes.push_back("a"); break;
                case 'c': phonemes.push_back("s"); break;
                case 'd': phonemes.push_back("d"); phonemes.push_back("a"); break;
                case 'e': phonemes.push_back("e"); break;
                case 'f': phonemes.push_back("ph"); phonemes.push_back("a"); break;
                case 'g': phonemes.push_back("g"); phonemes.push_back("a"); break;
                case 'h': phonemes.push_back("h"); break;
                case 'i': phonemes.push_back("i"); break;
                case 'j': phonemes.push_back("j"); phonemes.push_back("a"); break;
                case 'k': phonemes.push_back("k"); phonemes.push_back("a"); break;
                case 'l': phonemes.push_back("l"); phonemes.push_back("a"); break;
                case 'm': phonemes.push_back("m"); break;
                case 'n': phonemes.push_back("n"); break;
                case 'o': phonemes.push_back("o"); break;
                case 'p': phonemes.push_back("p"); phonemes.push_back("a"); break;
                case 'q': phonemes.push_back("k"); break;
                case 'r': phonemes.push_back("r"); phonemes.push_back("a"); break;
                case 's': phonemes.push_back("s"); break;
                case 't': phonemes.push_back("t"); phonemes.push_back("a"); break;
                case 'u': phonemes.push_back("u"); break;
                case 'v': phonemes.push_back("v"); phonemes.push_back("a"); break;
                case 'w': phonemes.push_back("v"); phonemes.push_back("a"); break;
                case 'x': phonemes.push_back("k"); phonemes.push_back("s"); break;
                case 'y': phonemes.push_back("y"); phonemes.push_back("a"); break;
                case 'z': phonemes.push_back("s"); break;
                default: break;
            }
            continue;
        }

        // 3. Indic Brahmi Scripts:
        // Hindi/Marathi (0x0900), Bengali (0x0980), Gujarati (0x0A80), Odia (0x0B00),
        // Tamil (0x0B80), Telugu (0x0C00), Kannada (0x0C80), Malayalam (0x0D00)
        uint32_t blockBase = 0;
        if (codepoint >= 0x0900 && codepoint <= 0x097F) blockBase = 0x0900;      // Devanagari (Hindi, Marathi)
        else if (codepoint >= 0x0980 && codepoint <= 0x09FF) blockBase = 0x0980; // Bengali
        else if (codepoint >= 0x0A80 && codepoint <= 0x0AFF) blockBase = 0x0A80; // Gujarati
        else if (codepoint >= 0x0B00 && codepoint <= 0x0B7F) blockBase = 0x0B00; // Odia
        else if (codepoint >= 0x0B80 && codepoint <= 0x0BFF) blockBase = 0x0B80; // Tamil
        else if (codepoint >= 0x0C00 && codepoint <= 0x0C7F) blockBase = 0x0C00; // Telugu
        else if (codepoint >= 0x0C80 && codepoint <= 0x0CFF) blockBase = 0x0C80; // Kannada
        else if (codepoint >= 0x0D00 && codepoint <= 0x0D7F) blockBase = 0x0D00; // Malayalam

        if (blockBase != 0) {
            uint32_t offset = codepoint - blockBase;

            // Independent Vowels
            if (offset == 0x05) { phonemes.push_back("a"); }
            else if (offset == 0x06) { phonemes.push_back("aa"); }
            else if (offset == 0x07) { phonemes.push_back("i"); }
            else if (offset == 0x08) { phonemes.push_back("ee"); }
            else if (offset == 0x09) { phonemes.push_back("u"); }
            else if (offset == 0x0A) { phonemes.push_back("oo"); }
            else if (offset == 0x0E || offset == 0x0F) { phonemes.push_back("e"); }
            else if (offset == 0x10) { phonemes.push_back("ai"); }
            else if (offset == 0x12 || offset == 0x13) { phonemes.push_back("o"); }
            else if (offset == 0x14) { phonemes.push_back("au"); }

            // Consonants (inherent vowel 'a')
            else if (offset == 0x15) { phonemes.push_back("k");  phonemes.push_back("a"); }
            else if (offset == 0x16) { phonemes.push_back("kh"); phonemes.push_back("a"); }
            else if (offset == 0x17) { phonemes.push_back("g");  phonemes.push_back("a"); }
            else if (offset == 0x18) { phonemes.push_back("gh"); phonemes.push_back("a"); }
            else if (offset == 0x1A) { phonemes.push_back("ch"); phonemes.push_back("a"); }
            else if (offset == 0x1C) { phonemes.push_back("j");  phonemes.push_back("a"); }
            else if (offset == 0x1F || offset == 0x24) { phonemes.push_back("t");  phonemes.push_back("a"); }
            else if (offset == 0x20 || offset == 0x25) { phonemes.push_back("th"); phonemes.push_back("a"); }
            else if (offset == 0x21 || offset == 0x26) { phonemes.push_back("d");  phonemes.push_back("a"); }
            else if (offset == 0x22 || offset == 0x27) { phonemes.push_back("dh"); phonemes.push_back("a"); }
            else if (offset == 0x28 || offset == 0x29) { phonemes.push_back("n");  phonemes.push_back("a"); }
            else if (offset == 0x2A) { phonemes.push_back("p");  phonemes.push_back("a"); }
            else if (offset == 0x2B) { phonemes.push_back("ph"); phonemes.push_back("a"); }
            else if (offset == 0x2C) { phonemes.push_back("b");  phonemes.push_back("a"); }
            else if (offset == 0x2D) { phonemes.push_back("bh"); phonemes.push_back("a"); }
            else if (offset == 0x2E) { phonemes.push_back("m");  phonemes.push_back("a"); }
            else if (offset == 0x2F) { phonemes.push_back("y");  phonemes.push_back("a"); }
            else if (offset == 0x30 || offset == 0x31) { phonemes.push_back("r");  phonemes.push_back("a"); }
            else if (offset == 0x32 || offset == 0x33 || offset == 0x34) { phonemes.push_back("l");  phonemes.push_back("a"); }
            else if (offset == 0x35) { phonemes.push_back("v");  phonemes.push_back("a"); }
            else if (offset == 0x36 || offset == 0x37) { phonemes.push_back("sh"); phonemes.push_back("a"); }
            else if (offset == 0x38) { phonemes.push_back("s");  phonemes.push_back("a"); }
            else if (offset == 0x39) { phonemes.push_back("h");  phonemes.push_back("a"); }

            // Dependent Vowel Signs (Matras) - replace previous inherent 'a' if present
            else if (offset == 0x3E) { // ा, ா, ా, ಾ, ാ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("aa");
            }
            else if (offset == 0x3F) { // ि, ி, ి, ಿ, ി
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("i");
            }
            else if (offset == 0x40) { // ी, ீ, ీ, ೀ, ീ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("ee");
            }
            else if (offset == 0x41) { // ु, ு, ు, ು, ു
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("u");
            }
            else if (offset == 0x42) { // ू, ூ, ూ, ೂ, ൂ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("oo");
            }
            else if (offset == 0x46 || offset == 0x47) { // े, ெ, ே, ె, ే, ೆ, ೇ, െ, േ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("e");
            }
            else if (offset == 0x48) { // ै, ை, ై, ೈ, ൈ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("ai");
            }
            else if (offset == 0x4A || offset == 0x4B) { // ो, ொ, ோ, ొ, ో, ೊ, ೋ, ൊ, ോ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("o");
            }
            else if (offset == 0x4C) { // ौ, ௌ, ౌ, ೌ, ൌ
                if (!phonemes.empty() && phonemes.back() == "a") phonemes.pop_back();
                phonemes.push_back("au");
            }
            else if (offset == 0x4D) { // Virama / Halant ् (cancels inherent vowel)
                if (!phonemes.empty() && phonemes.back() == "a") {
                    phonemes.pop_back();
                }
            }
            else if (offset == 0x02) { // Anusvara ं
                phonemes.push_back("m");
            }
            else if (offset == 0x03) { // Visarga ः
                phonemes.push_back("h");
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
        b0 = (1.0f - r) * 4.5f;
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

        float mixed = (out1 * 0.5f + out2 * 0.35f + out3 * 0.25f) * energy;
        outPcm.push_back(std::clamp(mixed, -0.95f, 0.95f));
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

    float pitch = (prosody.f0_pitch_mean > 50.0f) ? prosody.f0_pitch_mean : 145.0f;
    float cadence = (prosody.cadence_rate > 0.1f) ? prosody.cadence_rate : 1.0f;
    float energy = (prosody.rms_energy > 0.0f) ? prosody.rms_energy : 0.9f;

    float baseDur = 0.09f / cadence;

    for (const auto& ph : phonemes) {
        auto it = phonemeFormants_.find(ph);
        if (it != phonemeFormants_.end()) {
            synthesizePhoneme(it->second, baseDur, pitch, energy, outAudioPCM, sampleRate);
        } else {
            synthesizePhoneme(phonemeFormants_["a"], baseDur, pitch, energy, outAudioPCM, sampleRate);
        }
    }

    float maxAmp = 0.0f;
    for (float sample : outAudioPCM) {
        maxAmp = std::max(maxAmp, std::abs(sample));
    }
    if (maxAmp > 0.01f && maxAmp < 0.75f) {
        float gain = 0.85f / maxAmp;
        for (float& sample : outAudioPCM) {
            sample *= gain;
        }
    }
}
