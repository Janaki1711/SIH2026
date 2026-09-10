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
        "तोलनकेरे", "தோலன்கெரே", "తోలంకెరె", "ತೊಳನಕೆರೆ", "તોલનકેરે", "തോളങ്കരെ", "ତୋଲାଙ୍କେରେ", "তোলনকেরে"
    });

    registerLandmark("Hubbli", GeoID::HUBBLI, {
        "hubbli", "hubli", "hübli", "hubballi", "hubly",
        "हब्बली", "हुबली", "ஹூப்ளி", "ஹுப்பள்ளி", "హుబ్లి", "హుబ్బళ్ళి", "ಹುಬ್ಬಳ್ಳಿ",
        "હબ્બલી", "ഹുബ്ലി", "ହୁବ୍ଲି", "হুবলি"
    });

    registerLandmark("Base Camp", GeoID::BASE, {
        "base camp", "base", "hq", "headquarters", "command base",
        "बेस", "आधार", "मुख्यालय", "બેઝ", "முகாம்", "బేస్", "ಬೇಸ್", "ബേസ്", "ବେସ୍", "বেস"
    });

    registerLandmark("Sector 1", GeoID::SECTOR_1, {
        "sector 1", "sector one", "सेक्टर 1", "सेक्टर एक", "સેક્ટર 1", "செக்டர் 1",
        "సెక్టార్ 1", "సెక్టర్ 1", "ಸೆಕ್ಟರ್ 1", "സെക്ടർ 1", "ସେକ୍ଟର 1", "সেক্টর 1", "zone 1"
    });

    registerLandmark("Sector 2", GeoID::SECTOR_2, {
        "sector 2", "sector two", "सेक्टर 2", "सेक्टर दो", "સેક્ટર 2", "செக்டர் 2",
        "సెక్టార్ 2", "సెక్టర్ 2", "ಸೆಕ್ಟರ್ 2", "സെക്ടർ 2", "ସେକ୍ଟର 2", "সেক্টর 2", "zone 2"
    });

    registerLandmark("Sector 3", GeoID::SECTOR_3, {
        "sector 3", "sector three", "सेक्टर 3", "सेक्टर तीन", "સેક્ટર 3", "செக்டர் 3",
        "సెక్టార్ 3", "సెక్టర్ 3", "ಸೆಕ್ಟರ್ 3", "സെക്ടർ 3", "ସେକ୍ଟର 3", "সেক্টর 3", "zone 3"
    });

    registerLandmark("Sector 4", GeoID::SECTOR_4, {
        "sector 4", "sector four", "सेक्टर 4", "सेक्टर चार", "સેક્ટર 4", "செக்டர் 4",
        "సెక్టార్ 4", "సెక్టర్ 4", "ಸೆಕ್ಟರ್ 4", "സെക്ടർ 4", "ସେକ୍ଟର 4", "সেক্টর 4", "zone 4"
    });

    registerLandmark("Sector 5", GeoID::SECTOR_5, {
        "sector 5", "sector five", "सेक्टर 5", "सेक्टर पांच", "સેક્ટર 5", "செக்டர் 5",
        "సెక్టార్ 5", "సెక్టర్ 5", "ಸೆಕ್ಟರ್ 5", "സെക്ടർ 5", "ସେକ୍ଟର 5", "সেক্টর 5", "zone 5"
    });

    registerLandmark("Bridge", GeoID::BRIDGE, {
        "old bridge", "bridge", "railway bridge", "river bridge",
        "पुल", "सेतु", "पूल", "પુલ", "பாலம்", "వంతెన", "ಸೇತುವೆ", "പാലം", "ପୋଲ", "পোল", "সেতু"
    });

    registerLandmark("Hospital", GeoID::HOSPITAL, {
        "hospital", "clinic", "district hospital", "general hospital",
        "अस्पताल", "हॉस्पिटल", "रुग्णालय", "હોસ્પિટલ", "દવાખાનું", "மருத்துவமனை",
        "ஆஸ்பத்திரி", "ఆసుపత్రి", "ದವಾಖಾನೆ", "ಆಸ್ಪತ್ರೆ", "ആശുപത്രി", "ଡାକ୍ତରଖାନା", "হাসপাতাল"
    });

    registerLandmark("School", GeoID::SCHOOL, {
        "school", "college", "campus", "university", "institute", "institution",
        "स्कूल", "विद्यालय", "शाळा", "શાળા", "பள்ளி", "பாடசாலை", "పాఠశాల", "ಶಾಲೆ", "സ്കൂൾ", "ବିଦ୍ୟାଳୟ", "স্কুল"
    });

    // FIX 3: Register missing common location types in English + all 10 Indic languages

    registerLandmark("Railway Station", GeoID::RAILWAY_STATION, {
        "railway station", "train station", "rail station", "station", "rly station",
        "रेलवे स्टेशन", "रेल्वे स्थानक", "रेलवे स्थानक", "ट्रेन स्टेशन",
        "રેલ્વે સ્ટેશન", "ট্রেন স্টেশন", "রেলস্টেশন",
        "இரயில் நிலையம்", "ரயில் நிலையம்",
        "రైల్వే స్టేషన్", "రైలు స్టేషన్",
        "ರೈಲ್ವೆ ನಿಲ್ದಾಣ", "ರೈಲ್ನಿಲ್ದಾಣ",
        "റെയിൽവേ സ്റ്റേഷൻ", "ട്രെയിൻ സ്റ്റേഷൻ",
        "ରେଳ ଷ୍ଟେସନ", "ରେଲ ଷ୍ଟେଶନ"
    });

    registerLandmark("Bus Stand", GeoID::BUS_STAND, {
        "bus stand", "bus stop", "bus station", "bus depot", "bustand",
        "बस स्टैंड", "बस स्टॉप", "बस स्थानक", "बसस्थानक",
        "બસ સ્ટૅન્ડ", "বাস স্ট্যান্ড", "বাস স্টপ",
        "பஸ் நிலையம்", "பஸ் நிறுத்தம்",
        "బస్ స్టాండ్", "బస్ స్టాప్",
        "ಬಸ್ ನಿಲ್ದಾಣ", "ಬಸ್ ಸ್ಟಾಪ್",
        "ബസ് സ്റ്റോപ്പ്", "ബസ് സ്റ്റാൻഡ്",
        "ବସ ଷ୍ଟାଣ୍ଡ", "ବସ ଷ୍ଟପ"
    });

    registerLandmark("Airport", GeoID::AIRPORT, {
        "airport", "airfield", "aerodrome",
        "हवाई अड्डा", "विमानतळ", "हवाई अड्डे",
        "એરપોર્ટ", "বিমানবন্দর",
        "விமான நிலையம்", "ஏர்போர்ட்",
        "విమానాశ్రయం", "ఎయిర్పోర్ట్",
        "ವಿಮಾನ ನಿಲ್ದಾಣ", "ಏರ್ಪೋರ್ಟ್",
        "വിമാനത്താവളം", "ഏർപ്പോർട്ട്",
        "ବିମାନ ବନ୍ଦର", "ଏୟାରପୋର୍ଟ"
    });

    registerLandmark("Police Station", GeoID::POLICE_STATION, {
        "police station", "police post", "thana", "chowki", "thane",
        "पुलिस स्टेशन", "पोलीस स्टेशन", "थाना", "चौकी",
        "પોલીસ સ્ટેશન", "থানা", "পুলিশ স্টেশন",
        "காவல் நிலையம்", "போலீஸ் நிலையம்",
        "పోలీస్ స్టేషన్", "ఠాణా",
        "ಪೊಲೀಸ್ ಠಾಣೆ", "ಪೋಲೀಸ್ ಸ್ಟೇಷನ್",
        "പോലീസ് സ്റ്റേഷൻ", "ഠാണ",
        "ପୋଲିସ ଷ୍ଟେସନ", "ଥାନା"
    });

    registerLandmark("Fire Station", GeoID::FIRE_STATION, {
        "fire station", "fire brigade", "fire house",
        "अग्नि केंद्र", "दमकल केंद्र", "अग्निशमन केंद्र",
        "ફાયર સ્ટેશન", "ফায়ার স্টেশন",
        "தீயணைப்பு நிலையம்",
        "అగ్నిమాపక కేంద్రం",
        "ಅಗ್ನಿಶಾಮಕ ಠಾಣೆ",
        "അഗ്നിശമന സേന", "ഫയർ സ്റ്റേഷൻ",
        "ଅଗ୍ନି ଷ୍ଟେସନ"
    });

    registerLandmark("Market", GeoID::MARKET, {
        "market", "bazaar", "bazar", "marketplace", "sabzi mandi", "mandi",
        "बाजार", "मार्केट", "मंडी",
        "બજાર", "বাজার",
        "சந்தை", "பஜார்",
        "మార్కెట్", "బజార్",
        "ಮಾರ್ಕೆಟ್", "ಬಜಾರ್",
        "ചന്ത", "മാർക്കറ്റ്",
        "ବଜାର", "ମାର୍କେଟ"
    });

    registerLandmark("Temple", GeoID::TEMPLE, {
        "temple", "mandir", "devalaya", "kovil",
        "मंदिर", "देवालय", "मंदिर",
        "મંદિર", "মন্দির",
        "கோயில்", "கோவில்",
        "మందిరం", "దేవాలయం",
        "ದೇವಾಲಯ", "ಮಂದಿರ",
        "ക്ഷേത്രം", "ദേവാലയം",
        "ମନ୍ଦିର", "ଦେବଳ"
    });

    registerLandmark("Mosque", GeoID::MOSQUE, {
        "mosque", "masjid", "dargah",
        "मस्जिद", "दरगाह",
        "મસ્જિદ", "মসজিদ",
        "மசூதி", "மஸ்ஜித்",
        "మసీదు",
        "ಮಸೀದಿ",
        "പള്ളി", "മസ്ജിദ്",
        "ମସଜିଦ"
    });

    registerLandmark("Home", GeoID::HOME, {
        "home", "house", "residence", "ghar",
        "घर", "निवास",
        "ઘર", "বাড়ি", "ঘর",
        "வீடு", "இல்லம்",
        "ఇల్లు", "నివాసం",
        "ಮನೆ", "ನಿವಾಸ",
        "വീട്", "ഭവനം",
        "ଘର", "ନିବାସ"
    });

    registerLandmark("Village", GeoID::VILLAGE, {
        "village", "gaon", "gram", "pind",
        "गांव", "ग्राम", "पिंड",
        "ગામ", "গ্রাম", "গাঁও",
        "கிராமம்", "ஊர்",
        "గ్రామం", "పల్లె",
        "ಗ್ರಾಮ", "ಹಳ್ಳಿ",
        "ഗ്രാമം", "നാട്",
        "ଗ୍ରାମ", "ଗାଁ"
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
