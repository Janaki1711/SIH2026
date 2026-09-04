#include "GeoResolver.hpp"
#include <cctype>
#include <algorithm>
#include <sstream>
#include <cmath>

namespace itantra::semantic {

GeoResolver::GeoResolver() {
    initializeDefaultLandmarks();
}

void GeoResolver::initializeDefaultLandmarks() {
    registerLandmark("Tolankere", GeoID::TOLANKERE, {
        "tolankere", "tholankere", "tolan care", "tolankere lake", "tolankere tank",
        "तोलनकेरे", "தோலன்கெரே", "తోలంకెరె", "ತೊಳನಕೆರೆ", "tolankere"
    });

    registerLandmark("Hubbli", GeoID::HUBBLI, {
        "hubbli", "hubli", "hübli", "hubballi", "hubly",
        "हब्बली", "हुबली", "ஹூப்ளி", "ஹுப்பள்ளி", "హుబ్లి", "ಹುಬ್ಬಳ್ಳಿ"
    });

    registerLandmark("Base Camp", GeoID::BASE, {
        "base camp", "base", "hq", "headquarters", "command base",
        "बेस", "आधार", "मुख्यालय"
    });

    registerLandmark("Sector 1", GeoID::SECTOR_1, {
        "sector 1", "sector one", "सेक्टर 1", "सेक्टर एक", "zone 1"
    });

    registerLandmark("Sector 2", GeoID::SECTOR_2, {
        "sector 2", "sector two", "सेक्टर 2", "सेक्टर दो", "zone 2"
    });

    registerLandmark("Sector 3", GeoID::SECTOR_3, {
        "sector 3", "sector three", "सेक्टर 3", "सेक्टर तीन", "zone 3"
    });

    registerLandmark("Sector 4", GeoID::SECTOR_4, {
        "sector 4", "sector four", "सेक्टर 4", "सेक्टर चार",
        "सیکٹر 4", "ಸೆಕ್ಟರ್ 4", "zone 4"
    });

    registerLandmark("Sector 5", GeoID::SECTOR_5, {
        "sector 5", "sector five", "सेक्टर 5", "सेक्टर पांच", "zone 5"
    });

    registerLandmark("Bridge", GeoID::BRIDGE, {
        "old bridge", "bridge", "railway bridge", "river bridge",
        "पुल", "सेतु", "பாலம்", "వంతెన", "ಸೇತುವೆ"
    });

    registerLandmark("Hospital", GeoID::HOSPITAL, {
        "hospital", "clinic", "district hospital", "general hospital",
        "अस्पताल", "हॉस्पिटल", "மருத்துவமனை", "ఆసుపత్రి", "ಆಸ್ಪತ್ರೆ"
    });

    registerLandmark("School", GeoID::SCHOOL, {
        "school", "college", "campus",
        "स्कूल", "विद्यालय", "பள்ளி", "పాఠశాల", "ಶಾಲೆ"
    });
}

void GeoResolver::registerLandmark(const std::string& canonicalName, uint16_t geoId,
                                   const std::vector<std::string>& aliases) {
    LandmarkEntry entry;
    entry.canonicalName = canonicalName;
    entry.geoId = geoId;
    entry.aliases.push_back(normalize(canonicalName));

    for (const auto& alias : aliases) {
        std::string norm = normalize(alias);
        if (!norm.empty()) {
            entry.aliases.push_back(norm);
            std::string snd = computeSoundex(norm);
            if (!snd.empty()) {
                entry.phoneticAliases.push_back(snd);
            }
        }
    }
    landmarks_.push_back(entry);
}

std::string GeoResolver::normalize(const std::string& input) {
    std::string result;
    result.reserve(input.size());
    for (char c : input) {
        if (std::isalnum(static_cast<unsigned char>(c)) || static_cast<unsigned char>(c) >= 128 || std::isspace(static_cast<unsigned char>(c))) {
            result.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        } else {
            result.push_back(' ');
        }
    }
    // Collapse whitespace
    std::string collapsed;
    bool inSpace = false;
    for (char c : result) {
        if (std::isspace(static_cast<unsigned char>(c))) {
            if (!inSpace && !collapsed.empty()) {
                collapsed.push_back(' ');
                inSpace = true;
            }
        } else {
            collapsed.push_back(c);
            inSpace = false;
        }
    }
    if (!collapsed.empty() && collapsed.back() == ' ') collapsed.pop_back();
    return collapsed;
}

std::string GeoResolver::computeSoundex(const std::string& word) {
    if (word.empty()) return "";
    std::string clean;
    for (char c : word) {
        if (std::isalpha(static_cast<unsigned char>(c))) {
            clean.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
        }
    }
    if (clean.empty()) return "";

    char first = clean[0];
    auto getCode = [](char c) -> char {
        switch (c) {
            case 'B': case 'F': case 'P': case 'V': return '1';
            case 'C': case 'G': case 'J': case 'K': case 'Q': case 'S': case 'X': case 'Z': return '2';
            case 'D': case 'T': return '3';
            case 'L': return '4';
            case 'M': case 'N': return '5';
            case 'R': return '6';
            default: return '0';
        }
    };

    std::string code;
    code.push_back(first);
    char prev = getCode(first);

    for (size_t i = 1; i < clean.size() && code.size() < 4; ++i) {
        char curr = getCode(clean[i]);
        if (curr != '0' && curr != prev) {
            code.push_back(curr);
        }
        prev = curr;
    }
    while (code.size() < 4) {
        code.push_back('0');
    }
    return code;
}

int GeoResolver::levenshteinDistance(const std::string& s1, const std::string& s2) {
    size_t m = s1.size();
    size_t n = s2.size();
    std::vector<std::vector<int>> dp(m + 1, std::vector<int>(n + 1, 0));

    for (size_t i = 0; i <= m; ++i) dp[i][0] = static_cast<int>(i);
    for (size_t j = 0; j <= n; ++j) dp[0][j] = static_cast<int>(j);

    for (size_t i = 1; i <= m; ++i) {
        for (size_t j = 1; j <= n; ++j) {
            if (s1[i - 1] == s2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + std::min({dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]});
            }
        }
    }
    return dp[m][n];
}

float GeoResolver::similarityRatio(const std::string& s1, const std::string& s2) {
    if (s1.empty() && s2.empty()) return 1.0f;
    if (s1.empty() || s2.empty()) return 0.0f;
    int dist = levenshteinDistance(s1, s2);
    int maxLen = static_cast<int>(std::max(s1.size(), s2.size()));
    return 1.0f - (static_cast<float>(dist) / static_cast<float>(maxLen));
}

LocationEntity GeoResolver::resolveLocation(const std::string& text) const {
    LocationEntity bestMatch;
    bestMatch.geoId = GeoID::UNKNOWN;
    bestMatch.confidence = 0.0f;

    if (text.empty()) return bestMatch;

    std::string normText = normalize(text);

    // 1. Direct substring match (Exact or multi-word)
    for (const auto& landmark : landmarks_) {
        for (const auto& alias : landmark.aliases) {
            if (alias.empty()) continue;
            // Check if whole word alias exists in normText
            if (normText.find(alias) != std::string::npos) {
                float conf = 0.98f;
                if (conf > bestMatch.confidence) {
                    bestMatch.canonicalName = landmark.canonicalName;
                    bestMatch.geoId = landmark.geoId;
                    bestMatch.confidence = conf;
                    bestMatch.matchedToken = alias;
                }
            }
        }
    }

    if (bestMatch.confidence >= 0.95f) {
        return bestMatch;
    }

    // 2. Sliding window n-gram extraction for phonetic and approximate matching
    std::istringstream iss(normText);
    std::vector<std::string> tokens;
    std::string word;
    while (iss >> word) {
        tokens.push_back(word);
    }

    size_t numTokens = tokens.size();
    for (size_t len = 1; len <= std::min<size_t>(3, numTokens); ++len) {
        for (size_t start = 0; start + len <= numTokens; ++start) {
            std::string span;
            for (size_t i = 0; i < len; ++i) {
                if (i > 0) span += " ";
                span += tokens[start + i];
            }

            std::string spanSoundex = computeSoundex(span);

            for (const auto& landmark : landmarks_) {
                for (size_t aIdx = 0; aIdx < landmark.aliases.size(); ++aIdx) {
                    const auto& alias = landmark.aliases[aIdx];
                    
                    // Approximate string distance
                    float sim = similarityRatio(span, alias);
                    if (sim >= 0.75f && sim > bestMatch.confidence) {
                        bestMatch.canonicalName = landmark.canonicalName;
                        bestMatch.geoId = landmark.geoId;
                        bestMatch.confidence = sim * 0.95f;
                        bestMatch.matchedToken = span;
                    }

                    // Phonetic matching via Soundex
                    if (aIdx < landmark.phoneticAliases.size() && !spanSoundex.empty()) {
                        if (spanSoundex == landmark.phoneticAliases[aIdx]) {
                            float phonConf = 0.88f;
                            if (phonConf > bestMatch.confidence) {
                                bestMatch.canonicalName = landmark.canonicalName;
                                bestMatch.geoId = landmark.geoId;
                                bestMatch.confidence = phonConf;
                                bestMatch.matchedToken = span;
                            }
                        }
                    }
                }
            }
        }
    }

    return bestMatch;
}

} // namespace itantra::semantic
