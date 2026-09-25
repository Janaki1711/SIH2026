#include "TinyMLAgent.hpp"
#include <algorithm>
#include <cctype>
#include <sstream>
#include <regex>

namespace itantra::semantic {

TinyMLAgent::TinyMLAgent() : mlModel_(nullptr) {}

TinyMLAgent::TinyMLAgent(std::shared_ptr<ITinyMLSemanticModel> mlModel) : mlModel_(mlModel) {}

void TinyMLAgent::setModelBackend(std::shared_ptr<ITinyMLSemanticModel> mlModel) {
    mlModel_ = mlModel;
}

std::string TinyMLAgent::detectLanguage(const std::string& text, const std::string& fallbackLang) {
    if (!fallbackLang.empty() && fallbackLang != "auto") {
        return fallbackLang;
    }
    // Unicode range inspection for 10 official languages
    for (size_t i = 0; i < text.size(); ++i) {
        unsigned char c = static_cast<unsigned char>(text[i]);
        if (c == 0xE0) {
            if (i + 2 < text.size()) {
                unsigned char c1 = static_cast<unsigned char>(text[i + 1]);
                if (c1 == 0xA4 || c1 == 0xA5) return "hi"; // Devanagari (Hindi / Marathi)
                if (c1 == 0xA6 || c1 == 0xA7) return "bn"; // Bengali
                if (c1 == 0xAA || c1 == 0xAB) return "gu"; // Gujarati
                if (c1 == 0xAC || c1 == 0xAD) return "or"; // Odia
                if (c1 == 0xAE || c1 == 0xAF) return "ta"; // Tamil
                if (c1 == 0xB0 || c1 == 0xB1) return "te"; // Telugu
                if (c1 == 0xB2 || c1 == 0xB3) return "kn"; // Kannada
                if (c1 == 0xB4 || c1 == 0xB5) return "ml"; // Malayalam
            }
        }
    }
    return "en";
}

namespace {

// Word-boundary test for keyword matching (UTF-8 safe, byte-level).
// A match at [pos, pos+len) is a whole word only when both sides are a
// delimiter: start/end of string, ASCII whitespace/punctuation, or an
// Indic danda (U+0964/U+0965). Any ASCII letter/digit or any other
// non-ASCII codepoint (Indic letters AND vowel signs) continues a word.
// This stops "ಇಲ್ಲ" matching inside "ಇಲ್ಲಿ", "not" inside "notification",
// "stop" inside "stoppage", and "cancel" inside "cancellation".
bool isMarkerDelimBefore(const std::string& s, size_t pos) {
    if (pos == 0) return true;
    unsigned char c = static_cast<unsigned char>(s[pos - 1]);
    if (c < 0x80) return !std::isalnum(c);
    return false;  // previous char is non-ASCII: part of a longer word
}

bool isMarkerDelimAfter(const std::string& s, size_t end) {
    if (end >= s.size()) return true;
    unsigned char c = static_cast<unsigned char>(s[end]);
    if (c < 0x80) return !std::isalnum(c);
    // Indic danda U+0964 (E0 A5 A4) / U+0965 (E0 A5 A5) ends a sentence.
    if (c == 0xE0 && end + 2 < s.size() + 1 &&
        static_cast<unsigned char>(s[end + 1]) == 0xA5 &&
        end + 2 < s.size() &&
        (static_cast<unsigned char>(s[end + 2]) == 0xA4 ||
         static_cast<unsigned char>(s[end + 2]) == 0xA5)) {
        return true;
    }
    return false;  // vowel sign, letter, etc.: match continues a longer word
}

// Byte-exact marker search with word boundaries. English matching is done
// by the caller on a lowercased copy; Indic markers match byte-exact
// (lowercasing is a no-op on bytes >= 0x80, so one path serves both).
bool hasMarker(const std::string& text, const std::string& marker) {
    if (marker.empty()) return false;
    size_t pos = 0;
    while ((pos = text.find(marker, pos)) != std::string::npos) {
        if (isMarkerDelimBefore(text, pos) &&
            isMarkerDelimAfter(text, pos + marker.size())) {
            return true;
        }
        ++pos;
    }
    return false;
}

std::string asciiLower(std::string s) {
    for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

}  // namespace

bool TinyMLAgent::extractNegation(const std::string& text) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    // All markers below are matched as WHOLE WORDS (hasMarker enforces
    // boundaries on both sides). Trailing spaces from the old substring
    // lists are dropped — the boundary test covers "no," "(no)" etc.

    // English negation markers
    static const char* enNeg[] = {
        "not", "don't", "dont", "do not", "no", "never", "cannot", "can't",
        "cant", "stop", "cancel", "without", "no assistance", "no help",
        "needs no", "need no", "not required", "no rescue", "isn't", "isnt",
        "aren't", "arent", "wasn't", "wasnt", "weren't", "werent",
        "haven't", "havent", "hasn't", "hasnt", "won't", "wont",
    };
    for (const char* m : enNeg) {
        if (hasMarker(lower, m)) return true;
    }

    // Hindi / Marathi negation
    static const char* hiNeg[] = {
        "नहीं", "नही", "मत", "नाही", "नको", "नये",
        "आवश्यकता नहीं", "गरज नाही", "पाठवू नका", "करू नका",
    };
    for (const char* m : hiNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Gujarati negation
    static const char* guNeg[] = {
        "નથી", "નહીં", "ના", "જરૂર નથી",
        "મોકલશો નહીં", "કરશો નહીં",
    };
    for (const char* m : guNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Tamil negation
    static const char* taNeg[] = {
        "இல்லை", "வேண்டாம்", "கூடாது", "தேவையில்லை",
        "வேண்டா", "அனுப்ப வேண்டாம்",
    };
    for (const char* m : taNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Telugu negation
    static const char* teNeg[] = {
        "లేదు", "వద్దు", "కాదు", "అవసరం లేదు",
        "పంపవద్దు", "చేయవద్దు",
    };
    for (const char* m : teNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Kannada negation ("ಇಲ್ಲ" must not fire inside "ಇಲ್ಲಿ" — boundary test)
    static const char* knNeg[] = {
        "ಇಲ್ಲ", "ಬೇಡ", "ಬಾರದು", "ಅಗತ್ಯವಿಲ್ಲ",
        "ಕಳುಹಿಸಬೇಡಿ", "ಮಾಡಬೇಡಿ",
    };
    for (const char* m : knNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Malayalam negation
    static const char* mlNeg[] = {
        "ഇല്ല", "വേണ്ട", "അരുത്", "പാടില്ല",
        "ആവശ്യമില്ല", "അയക്കരുത്", "ഒഴിപ്പിക്കരുത്",
    };
    for (const char* m : mlNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Odia negation
    static const char* orNeg[] = {
        "ନାହିଁ", "ନୁହେଁ", "ମନା", "ଆବଶ୍ୟକ ନାହିଁ",
        "ପଠାନ୍ତୁ ନାହିଁ", "କରନ୍ତୁ ନାହିଁ",
    };
    for (const char* m : orNeg) {
        if (hasMarker(text, m)) return true;
    }

    // Bengali negation
    static const char* bnNeg[] = {
        "দরকার নেই", "প্রয়োজন নেই", "পাঠাবেন না", "করবেন না",
        "নেই", "না",
    };
    for (const char* m : bnNeg) {
        if (hasMarker(text, m)) return true;
    }

    return false;
}

// Decline/cancel-class negation: the speaker explicitly refuses or stands
// down ("do not need", "వద్దు", "ಬೇಡ"). Only these markers authorize the
// "NOT required" realization. Bare absence ("no water", "నీరు లేదు") means
// the resource is LACKED — i.e. needed — and must realize positive.
bool TinyMLAgent::extractStrongNegation(const std::string& text) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    static const char* enStrong[] = {
        "don't need", "dont need", "do not need", "not needed",
        "not required", "no need", "don't want", "do not want", "dont want",
        "don't send", "do not send", "dont send", "no help", "no assistance",
        "no rescue", "need no", "needs no", "cancel", "stand down",
        "false alarm", "all clear", "all good", "all is well",
        "no emergency", "never mind", "ignore that", "disregard",
        "call off", "called off", "not necessary", "no longer needed",
        "don't come", "do not come", "dont come",
    };
    for (const char* m : enStrong) {
        if (hasMarker(lower, m)) return true;
    }

    static const char* hiStrong[] = {
        "आवश्यकता नहीं", "जरूरत नहीं", "नहीं चाहिए", "मत भेजो", "नको",
        "गरज नाही", "नाही पाहिजे",
    };
    for (const char* m : hiStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* guStrong[] = {
        "જરૂર નથી", "મોકલશો નહીં", "જોઈતું નથી", "નથી જોઈતું",
    };
    for (const char* m : guStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* taStrong[] = {
        "வேண்டாம்", "தேவையில்லை", "அனுப்ப வேண்டாம்", "தேவை இல்லை",
    };
    for (const char* m : taStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* teStrong[] = {
        "అవసరం లేదు", "అక్కర్లేదు", "వద్దు", "పంపవద్దు", "చేయవద్దు",
    };
    for (const char* m : teStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* knStrong[] = {
        "ಬೇಡ", "ಅಗತ್ಯವಿಲ್ಲ", "ಬೇಕಾಗಿಲ್ಲ", "ಕಳುಹಿಸಬೇಡಿ", "ಮಾಡಬೇಡಿ",
    };
    for (const char* m : knStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* mlStrong[] = {
        "വേണ്ട", "ആവശ്യമില്ല", "അയക്കരുത്", "ഒഴിപ്പിക്കരുത്",
    };
    for (const char* m : mlStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* orStrong[] = {
        "ଆବଶ୍ୟକ ନାହିଁ", "ଦରକାର ନାହିଁ", "ପଠାନ୍ତୁ ନାହିଁ",
    };
    for (const char* m : orStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* bnStrong[] = {
        "দরকার নেই", "প্রয়োজন নেই", "লাগবে না", "পাঠাবেন না", "চাই না",
    };
    for (const char* m : bnStrong) {
        if (hasMarker(text, m)) return true;
    }

    static const char* paStrong[] = {
        "ਲੋੜ ਨਹੀਂ", "ਨਾ ਭੇਜੋ", "ਚਾਹੀਦਾ ਨਹੀਂ",
    };
    for (const char* m : paStrong) {
        if (hasMarker(text, m)) return true;
    }

    return false;
}

uint32_t TinyMLAgent::extractPersonCount(const std::string& text) {
    // 1. Scrub landmark/location digit patterns to avoid classifying "Sector 4" or "Block 7" as casualty count
    std::string scrubbed = text;
    // Lowercase before the case-sensitive word search below — otherwise
    // "Five people…" misses {"five", 5} (extractHazard already lowercases).
    // Byte-wise tolower is safe for UTF-8: Indic bytes are >= 0x80 and stay put.
    for (char& c : scrubbed) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    
    // Landmark prefix regexes in English and Indic scripts
    static const std::vector<std::regex> landmarkRegexes = {
        std::regex(R"(\b(sector|block|gate|room|ward|zone|building|nh|highway|lane|door)\s*#?\s*\d+\b)", std::regex::icase),
        std::regex(R"(सेक्टर\s*\d+)", std::regex::icase),
        std::regex(R"(સેક્ટર\s*\d+)", std::regex::icase),
        std::regex(R"(செக்டர்\s*\d+)", std::regex::icase),
        std::regex(R"(సెక్టర్\s*\d+)", std::regex::icase),
        std::regex(R"(ಸೆಕ್ಟರ್\s*\d+)", std::regex::icase),
        std::regex(R"(സെക്ടർ\s*\d+)", std::regex::icase),
        std::regex(R"(ସେକ୍ଟର\s*\d+)", std::regex::icase),
        std::regex(R"(সেক্টর\s*\d+)", std::regex::icase)
    };

    for (const auto& r : landmarkRegexes) {
        scrubbed = std::regex_replace(scrubbed, r, " ");
    }

    // Number words in 10 languages (1 to 10)
    static const std::unordered_map<std::string, uint32_t> words = {
        {"one", 1}, {"two", 2}, {"three", 3}, {"four", 4}, {"five", 5},
        {"six", 6}, {"seven", 7}, {"eight", 8}, {"nine", 9}, {"ten", 10},
        // Hindi / Marathi
        {"एक", 1}, {"दो", 2}, {"दोन", 2}, {"तीन", 3}, {"चार", 4}, {"पांच", 5},
        {"पाँच", 5}, {"पाच", 5}, {"छह", 6}, {"सहा", 6}, {"सात", 7}, {"आठ", 8}, {"नौ", 9}, {"नऊ", 9}, {"दस", 10}, {"दहा", 10},
        // Gujarati
        {"બે", 2}, {"ત્રણ", 3}, {"પાંચ", 5}, {"છ", 6}, {"નવ", 9}, {"દસ", 10},
        // Bengali
        {"দুই", 2}, {"তিন", 3}, {"চার", 4}, {"পাঁচ", 5}, {"ছয়", 6}, {"নয়", 9}, {"দশ", 10},
        // Odia
        {"ଦୁଇ", 2}, {"ତିନି", 3}, {"ଚାରି", 4}, {"ପାଞ୍ଚ", 5}, {"ଛଅ", 6}, {"ସାତ", 7}, {"ଆଠ", 8}, {"ନଅ", 9}, {"ଦଶ", 10},
        // Tamil
        {"ஒன்று", 1}, {"இரண்டு", 2}, {"மூன்று", 3}, {"நான்கு", 4}, {"ஐந்து", 5}, {"ஆறு", 6}, {"ஏழு", 7}, {"எட்டு", 8}, {"ஒன்பது", 9}, {"பத்து", 10},
        // Telugu
        {"ఒకటి", 1}, {"రెండు", 2}, {"మూడు", 3}, {"నాలుగు", 4}, {"ఐదు", 5}, {"ఆరు", 6}, {"ఏడు", 7}, {"ఎనిమిది", 8}, {"తొమ్మిది", 9}, {"పది", 10},
        // Kannada
        {"ಒಂದು", 1}, {"ಎರಡು", 2}, {"ಮೂರು", 3}, {"ನಾಲ್ಕು", 4}, {"ಐದು", 5}, {"ಆರು", 6}, {"ಏಳು", 7}, {"ಎಂಟು", 8}, {"ಒಂಬತ್ತು", 9}, {"ಹತ್ತು", 10},
        // Malayalam
        {"ഒന്ന്", 1}, {"രണ്ട്", 2}, {"മൂന്ന്", 3}, {"നാല്", 4}, {"അഞ്ച്", 5}, {"ആറ്", 6}, {"ഏഴ്", 7}, {"എട്ട്", 8}, {"ഒൻപത്", 9}, {"പത്ത്", 10}
    };

    // 2. Direct word search on scrubbed text
    for (const auto& [word, count] : words) {
        if (scrubbed.find(word) != std::string::npos) {
            return count;
        }
    }

    // 3. Regular expression for digits in scrubbed text explicitly preceding casualty/team keywords
    std::regex countRegex(R"(\b(\d+)\s*(people|persons|trapped|victims|casualties|men|women|children|teams|team|workers|doctors|ambulances|जवान|लोग|व्यक्तियों|डॉक्टर|रुग्णवाहिका|લોકો|লোক|ମଣିଷ|പേർ|பேர்|మంది|ಜನರು|ଜଣ|জন)?\b)", std::regex::icase);
    std::smatch match;
    if (std::regex_search(scrubbed, match, countRegex)) {
        try {
            uint32_t val = static_cast<uint32_t>(std::stoul(match[1].str()));
            if (val > 0 && val <= 1000) return val;
        } catch (...) {}
    }

    return 0;
}

HazardCode TinyMLAgent::extractHazard(const std::string& text) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    // Flood (en, hi, mr, gu, ta, te, kn, ml, or, bn)
    if (lower.find("flood") != std::string::npos || lower.find("flooding") != std::string::npos ||
        lower.find("बाढ़") != std::string::npos || lower.find("पूर") != std::string::npos ||
        lower.find("पाणी") != std::string::npos || lower.find("પૂર") != std::string::npos ||
        lower.find("വെള്ളപ്പൊക്കം") != std::string::npos || lower.find("വെള്ളം") != std::string::npos ||
        lower.find("வெள்ளம்") != std::string::npos || lower.find("வரదలు") != std::string::npos ||
        lower.find("వరద") != std::string::npos || lower.find("ಪ್ರವಾಹ") != std::string::npos ||
        lower.find("ବନ୍ୟା") != std::string::npos || lower.find("বন্যা") != std::string::npos) {
        return HazardCode::FLOOD;
    }
    // Fire
    if (lower.find("fire") != std::string::npos || lower.find("blaze") != std::string::npos ||
        lower.find("आग") != std::string::npos || lower.find("वणवा") != std::string::npos ||
        lower.find("આગ") != std::string::npos || lower.find("தீ") != std::string::npos ||
        lower.find("நெருப்பு") != std::string::npos || lower.find("నిప్పు") != std::string::npos ||
        lower.find("అగ్ని") != std::string::npos || lower.find("ಬೆಂಕಿ") != std::string::npos ||
        lower.find("അഗ്നിബാധ") != std::string::npos || lower.find("തീ") != std::string::npos ||
        lower.find("ନିଆଁ") != std::string::npos || lower.find("আগুন") != std::string::npos) {
        return HazardCode::FIRE;
    }
    // Earthquake
    if (lower.find("earthquake") != std::string::npos || lower.find("quake") != std::string::npos ||
        lower.find("भूकंप") != std::string::npos || lower.find("ધરતીકંપ") != std::string::npos ||
        lower.find("நிலநடுக்கம்") != std::string::npos || lower.find("భూకంపం") != std::string::npos ||
        lower.find("ಭೂಕಂಪ") != std::string::npos || lower.find("ഭൂകമ്പം") != std::string::npos ||
        lower.find("ଭୂମିକମ୍ପ") != std::string::npos || lower.find("ভূমিকম্প") != std::string::npos) {
        return HazardCode::EARTHQUAKE;
    }
    // Landslide
    if (lower.find("landslide") != std::string::npos || lower.find("भूस्खलन") != std::string::npos ||
        lower.find("दरड") != std::string::npos || lower.find("ભૂસ્ખલન") != std::string::npos ||
        lower.find("நிலச்சரிவு") != std::string::npos || lower.find("కొండచరియలు") != std::string::npos ||
        lower.find("ಭೂಕುಸಿತ") != std::string::npos || lower.find("ഉരുൾപൊട്ടൽ") != std::string::npos ||
        lower.find("ଭୂସ୍ଖଳନ") != std::string::npos || lower.find("ভূমিধস") != std::string::npos) {
        return HazardCode::LANDSLIDE;
    }
    // Building Collapse
    if (lower.find("collapse") != std::string::npos || lower.find("collapsed") != std::string::npos ||
        lower.find("गिर गया") != std::string::npos || lower.find("ढह गया") != std::string::npos ||
        lower.find("कोसळले") != std::string::npos || lower.find("તૂટી") != std::string::npos ||
        lower.find("இடிந்து") != std::string::npos || lower.find("కూలిపోయింది") != std::string::npos ||
        lower.find("ಕುಸಿತ") != std::string::npos || lower.find("തകർച്ച") != std::string::npos ||
        lower.find("ଭୁଶୁଡ଼ି") != std::string::npos || lower.find("ভেঙে") != std::string::npos) {
        return HazardCode::BUILDING_COLLAPSE;
    }
    // Explosion
    if (lower.find("explosion") != std::string::npos || lower.find("blast") != std::string::npos ||
        lower.find("धमाका") != std::string::npos || lower.find("विस्फोट") != std::string::npos ||
        lower.find("વિસ્ફોટ") != std::string::npos || lower.find("வெடிப்பு") != std::string::npos ||
        lower.find("పేలుడు") != std::string::npos || lower.find("ಸ್ಫೋಟ") != std::string::npos ||
        lower.find("സ്ഫോടനം") != std::string::npos || lower.find("ବିସ୍ଫୋରଣ") != std::string::npos ||
        lower.find("বিস্ফোরণ") != std::string::npos) {
        return HazardCode::EXPLOSION;
    }
    // Gas Leak
    if (lower.find("gas leak") != std::string::npos || lower.find("toxic") != std::string::npos ||
        lower.find("गैस") != std::string::npos || lower.find("ગૅસ") != std::string::npos ||
        lower.find("વાયુ") != std::string::npos || lower.find("எரிவாயு") != std::string::npos ||
        lower.find("గ్యాస్") != std::string::npos || lower.find("ಅನಿಲ") != std::string::npos ||
        lower.find("വാതക") != std::string::npos || lower.find("ଗ୍ୟାସ") != std::string::npos) {
        return HazardCode::GAS_LEAK;
    }
    return HazardCode::NONE;
}

ActionCode TinyMLAgent::extractActionAndIntent(const std::string& text, ActionCode& outAction) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    outAction = ActionCode::UNKNOWN;

    // 1. Rescue / Help Request / Trapped (en, hi, mr, gu, ta, te, kn, ml, or, bn)
    if (lower.find("rescue") != std::string::npos || lower.find("help") != std::string::npos ||
        lower.find("trapped") != std::string::npos || lower.find("stuck") != std::string::npos ||
        lower.find("struck") != std::string::npos ||
        // Field-demo phrasings that previously fell through as free-form text:
        lower.find("get me out") != std::string::npos ||
        lower.find("take me out") != std::string::npos ||
        lower.find("let me out") != std::string::npos ||
        lower.find("out of here") != std::string::npos ||
        lower.find("मदद") != std::string::npos || lower.find("बचाओ") != std::string::npos ||
        lower.find("फंसे") != std::string::npos || lower.find("मदत") != std::string::npos ||
        lower.find("वाचवा") != std::string::npos || lower.find("अडकले") != std::string::npos ||
        lower.find("મદદ") != std::string::npos || lower.find("બચાવો") != std::string::npos ||
        lower.find("ફસાયા") != std::string::npos || lower.find("ઉદ્ધાર") != std::string::npos ||
        lower.find("உதவி") != std::string::npos || lower.find("காப்பாற்று") != std::string::npos ||
        lower.find("சிக்கியுள்ளனர்") != std::string::npos || lower.find("மீட்பு") != std::string::npos ||
        lower.find("సహాయం") != std::string::npos || lower.find("రక్షించండి") != std::string::npos ||
        lower.find("చిక్కుకున్నారు") != std::string::npos || lower.find("రక్షణ") != std::string::npos ||
        lower.find("ಸಹಾಯ") != std::string::npos || lower.find("ರಕ್ಷಿಸಿ") != std::string::npos ||
        lower.find("ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ") != std::string::npos || lower.find("ರಕ್ಷಣಾ") != std::string::npos ||
        lower.find("രക്ഷിക്കൂ") != std::string::npos || lower.find("സഹായം") != std::string::npos ||
        lower.find("കുടുങ്ങി") != std::string::npos || lower.find("രക്ഷാപ്രവർത്തനം") != std::string::npos ||
        lower.find("ସାହାଯ୍ୟ") != std::string::npos || lower.find("ରକ୍ଷା କର") != std::string::npos ||
        lower.find("ଫସି") != std::string::npos || lower.find("ଉଦ୍ଧାର") != std::string::npos ||
        lower.find("সাহায্য") != std::string::npos || lower.find("বাঁচাও") != std::string::npos ||
        lower.find("আটকে") != std::string::npos || lower.find("উদ্ধার") != std::string::npos ||
        lower.find("send help") != std::string::npos) {
        
        if (lower.find("boat") != std::string::npos || lower.find("नाव") != std::string::npos ||
            lower.find("होडी") != std::string::npos || lower.find("બોટ") != std::string::npos ||
            lower.find("படகு") != std::string::npos || lower.find("పడవ") != std::string::npos ||
            lower.find("ದೋಣಿ") != std::string::npos || lower.find("ബോട്ട്") != std::string::npos ||
            lower.find("ଡଙ୍ଗା") != std::string::npos || lower.find("নৌকা") != std::string::npos) {
            outAction = ActionCode::BOAT;
        } else if (lower.find("team") != std::string::npos || lower.find("दल") != std::string::npos ||
                   lower.find("पथक") != std::string::npos || lower.find("ટીમ") != std::string::npos ||
                   lower.find("குழு") != std::string::npos || lower.find("బృందం") != std::string::npos ||
                   lower.find("ತಂಡ") != std::string::npos || lower.find("സംഘം") != std::string::npos ||
                   lower.find("ଦଳ") != std::string::npos || lower.find("দল") != std::string::npos ||
                   lower.find("भेजो") != std::string::npos || lower.find("पाठवा") != std::string::npos ||
                   lower.find("મોકલો") != std::string::npos || lower.find("அனுப்பு") != std::string::npos ||
                   lower.find("పంపండి") != std::string::npos || lower.find("ಕಳುಹಿಸಿ") != std::string::npos ||
                   lower.find("അയക്കുക") != std::string::npos || lower.find("ପଠାଅ") != std::string::npos ||
                   lower.find("পাঠান") != std::string::npos) {
            outAction = ActionCode::SEND_TEAM;
        } else {
            outAction = ActionCode::RESCUE_REQUEST;
        }
        return ActionCode::RESCUE_REQUEST;
    }

    // 2. Evacuate
    if (lower.find("evacuate") != std::string::npos || lower.find("evacuation") != std::string::npos ||
        lower.find("खाली करो") != std::string::npos || lower.find("निकालो") != std::string::npos ||
        lower.find("रिकामे करा") != std::string::npos || lower.find("બહાર નીકળો") != std::string::npos ||
        lower.find("ખાલી કરો") != std::string::npos || lower.find("வெளியேறு") != std::string::npos ||
        lower.find("வெளியேற்று") != std::string::npos || lower.find("ఖాళీ చేయండి") != std::string::npos ||
        lower.find("తరలించండి") != std::string::npos || lower.find("ಖಾಲಿ ಮಾಡಿ") != std::string::npos ||
        lower.find("ಹೊರಡಿ") != std::string::npos || lower.find("ഒഴിഞ്ഞുപോകുക") != std::string::npos ||
        lower.find("ഒഴിപ്പിക്കുക") != std::string::npos || lower.find("ଖାଲି କର") != std::string::npos ||
        lower.find("ସ୍ଥାନାନ୍ତର") != std::string::npos || lower.find("খালি করুন") != std::string::npos ||
        lower.find("অপসারণ") != std::string::npos) {
        outAction = ActionCode::EVACUATE;
        return ActionCode::EVACUATE;
    }

    // 3. Medical / Doctor / Ambulance
    if (lower.find("medical") != std::string::npos || lower.find("doctor") != std::string::npos ||
        lower.find("ambulance") != std::string::npos || lower.find("ambulances") != std::string::npos ||
        lower.find("injured") != std::string::npos || lower.find("casualties") != std::string::npos ||
        lower.find("चिकित्सा") != std::string::npos || lower.find("डॉक्टर") != std::string::npos ||
        lower.find("घायल") != std::string::npos || lower.find("रुग्णवाहिका") != std::string::npos ||
        lower.find("ઇજાગ્રસ્ત") != std::string::npos || lower.find("જખમી") != std::string::npos ||
        lower.find("એમ્બ્યુલન્સ") != std::string::npos || lower.find("દવા") != std::string::npos ||
        lower.find("மருத்துவம்") != std::string::npos || lower.find("ஆம்புலன்ஸ்") != std::string::npos ||
        lower.find("காயம்") != std::string::npos || lower.find("வைத்தியம்") != std::string::npos ||
        lower.find("వైద్యం") != std::string::npos || lower.find("అంబులెన్స్") != std::string::npos ||
        lower.find("గాయపడిన") != std::string::npos || lower.find("డాక్టర్") != std::string::npos ||
        lower.find("ಚಿಕಿತ್ಸೆ") != std::string::npos || lower.find("ಆಂಬ್ಯುಲೆನ್ಸ್") != std::string::npos ||
        lower.find("ಗಾಯಗೊಂಡ") != std::string::npos || lower.find("ವೈದ್ಯಕೀಯ") != std::string::npos ||
        lower.find("ചികിത്സ") != std::string::npos || lower.find("ആംബുലൻസ്") != std::string::npos ||
        lower.find("പരിക്കേറ്റ") != std::string::npos || lower.find("വൈദ്യം") != std::string::npos ||
        lower.find("ଡାକ୍ତର") != std::string::npos || lower.find("ଆମ୍ବୁଲାନ୍ସ") != std::string::npos ||
        lower.find("ଆହତ") != std::string::npos || lower.find("ଚିକିତ୍ସା") != std::string::npos ||
        lower.find("চিকিৎসা") != std::string::npos || lower.find("অ্যাম্বুলেন্স") != std::string::npos ||
        lower.find("আহত") != std::string::npos || lower.find("ডাক্তার") != std::string::npos) {
        outAction = ActionCode::MEDICAL;
        return ActionCode::MEDICAL;
    }

    // 4. Supplies / Food / Water
    if (lower.find("supplies") != std::string::npos || lower.find("food") != std::string::npos ||
        lower.find("water") != std::string::npos || lower.find("ration") != std::string::npos ||
        lower.find("राशन") != std::string::npos || lower.find("पानी") != std::string::npos ||
        lower.find("भोजन") != std::string::npos || lower.find("अन्न") != std::string::npos ||
        lower.find("ખોરાક") != std::string::npos || lower.find("પાણી") != std::string::npos ||
        lower.find("અનાજ") != std::string::npos || lower.find("உணவு") != std::string::npos ||
        lower.find("தண்ணீர்") != std::string::npos || lower.find("குடிநீர்") != std::string::npos ||
        lower.find("ఆహారం") != std::string::npos || lower.find("నీరు") != std::string::npos ||
        lower.find("సరఫరా") != std::string::npos || lower.find("ಆಹಾರ") != std::string::npos ||
        lower.find("ನೀರು") != std::string::npos || lower.find("ಸರಬರಾಜು") != std::string::npos ||
        lower.find("ഭക്ഷണം") != std::string::npos || lower.find("വെള്ളം") != std::string::npos ||
        lower.find("സാധനങ്ങൾ") != std::string::npos || lower.find("ଖାଦ୍ୟ") != std::string::npos ||
        lower.find("ଜଳ") != std::string::npos || lower.find("ଯୋଗାଣ") != std::string::npos ||
        lower.find("খাদ্য") != std::string::npos || lower.find("জল") != std::string::npos ||
        lower.find("সরবরাহ") != std::string::npos) {
        outAction = ActionCode::SUPPLIES;
        return ActionCode::SUPPLIES;
    }

    // 5. Team Ready / Dispatch
    if (lower.find("team is ready") != std::string::npos || lower.find("team ready") != std::string::npos ||
        lower.find("ready") != std::string::npos || lower.find("dispatch team") != std::string::npos ||
        lower.find("send team") != std::string::npos || lower.find("तैयार") != std::string::npos ||
        lower.find("रवाना") != std::string::npos || lower.find("सज्ज") != std::string::npos ||
        lower.find("તૈયાર") != std::string::npos || lower.find("தயார்") != std::string::npos ||
        lower.find("సిద్ధం") != std::string::npos || lower.find("ಸಿದ್ಧ") != std::string::npos ||
        lower.find("സജ്ജമാണ്") != std::string::npos || lower.find("ପ୍ରସ୍ତୁତ") != std::string::npos ||
        lower.find("প্রস্তুত") != std::string::npos) {
        outAction = ActionCode::SEND_TEAM;
        return ActionCode::SEND_TEAM;
    }

    // 6. Search / Missing
    if (lower.find("search") != std::string::npos || lower.find("missing") != std::string::npos ||
        lower.find("खोजो") != std::string::npos || lower.find("गायब") != std::string::npos ||
        lower.find("शोध") != std::string::npos || lower.find("શોધો") != std::string::npos ||
        lower.find("ગુમ") != std::string::npos || lower.find("தேடு") != std::string::npos ||
        lower.find("காணவில்லை") != std::string::npos || lower.find("వెతకండి") != std::string::npos ||
        lower.find("గల్లంతైన") != std::string::npos || lower.find("ಹುಡುಕಿ") != std::string::npos ||
        lower.find("ಕಾಣೆಯಾದ") != std::string::npos || lower.find("തിരയുക") != std::string::npos ||
        lower.find("കാണാതായ") != std::string::npos || lower.find("ଖୋଜ") != std::string::npos ||
        lower.find("ନିଖୋଜ") != std::string::npos || lower.find("খোঁজো") != std::string::npos ||
        lower.find("নিখোঁজ") != std::string::npos) {
        outAction = ActionCode::SEARCH;
        return ActionCode::SEARCH;
    }

    // 7. Alert / Warning
    if (lower.find("alert") != std::string::npos || lower.find("warning") != std::string::npos ||
        lower.find("चेतावनी") != std::string::npos || lower.find("सावधान") != std::string::npos ||
        lower.find("સાવધાન") != std::string::npos || lower.find("ચેતવણી") != std::string::npos ||
        lower.find("எச்சரிக்கை") != std::string::npos || lower.find("హెచ్చరిక") != std::string::npos ||
        lower.find("ಎಚ್ಚರಿಕೆ") != std::string::npos || lower.find("ജാഗ്രത") != std::string::npos ||
        lower.find("ସତର୍କ") != std::string::npos || lower.find("সতর্কতা") != std::string::npos) {
        outAction = ActionCode::ALERT;
        return ActionCode::ALERT;
    }

    // 8. Move / Advance
    if (lower.find("moving") != std::string::npos || lower.find("advance") != std::string::npos ||
        lower.find("आगे बढ़") != std::string::npos || lower.find("पुढे चला") != std::string::npos ||
        lower.find("આગળ વધો") != std::string::npos || lower.find("முன்னேறு") != std::string::npos ||
        lower.find("ముందుకు కదలండి") != std::string::npos || lower.find("ಮುಂದೆ ಸಾಗಿ") != std::string::npos ||
        lower.find("മുന്നോട്ട് നീങ്ങുക") != std::string::npos || lower.find("ଆଗକୁ ବଢ଼") != std::string::npos ||
        lower.find("এগিয়ে চলুন") != std::string::npos) {
        outAction = ActionCode::MOVE;
        return ActionCode::MOVE;
    }

    // 9. Report / Status
    if (lower.find("report") != std::string::npos || lower.find("status") != std::string::npos ||
        lower.find("सूचना") != std::string::npos || lower.find("अहवाल") != std::string::npos ||
        lower.find("અહેવાલ") != std::string::npos || lower.find("அறிக்கை") != std::string::npos ||
        lower.find("నివేదిక") != std::string::npos || lower.find("ವರದಿ") != std::string::npos ||
        lower.find("റിപ്പോർട്ട്") != std::string::npos || lower.find("ରିପୋର୍ଟ") != std::string::npos ||
        lower.find("ರಿಪೋರ್ಟ") != std::string::npos || lower.find("রিপোর্ট") != std::string::npos) {
        outAction = ActionCode::REPORT;
        return ActionCode::REPORT;
    }

    // FIX 3: 10. LOCATION_REPORT — "I am at X", "meet me at X", "near X", "at X"
    // These phrases report the speaker's location without an explicit movement command
    if (lower.find("i am at") != std::string::npos || lower.find("i am near") != std::string::npos ||
        lower.find("i am in") != std::string::npos || lower.find("i'm in") != std::string::npos ||
        lower.find("im in") != std::string::npos || lower.find("we are in") != std::string::npos ||
        lower.find("meet me at") != std::string::npos || lower.find("meet me near") != std::string::npos ||
        lower.find("we are at") != std::string::npos || lower.find("located at") != std::string::npos ||
        lower.find("standing at") != std::string::npos || lower.find("waiting at") != std::string::npos ||
        // Hindi / Marathi
        lower.find("मैं हूं") != std::string::npos || lower.find("मैं यहाँ हूं") != std::string::npos ||
        lower.find("मी आहे") != std::string::npos || lower.find("इथे आहे") != std::string::npos ||
        // Tamil
        lower.find("நான் இருக்கிறேன்") != std::string::npos ||
        // Telugu
        lower.find("నేను ఉన్నాను") != std::string::npos ||
        // Kannada
        lower.find("ನಾನು ಇದ್ದೇನೆ") != std::string::npos ||
        // Malayalam
        lower.find("ഞാൻ ഇവിടെ ഉണ്ട്") != std::string::npos) {
        outAction = ActionCode::LOCATION_REPORT;
        return ActionCode::LOCATION_REPORT;
    }

    // FIX 3: 11. GO_TO / Navigate / Movement to a location
    // Recognizes "go to", "proceed to", "move to", "head to", "reach", "towards"
    // in English and all 10 Indic languages
    if (lower.find("go to") != std::string::npos || lower.find("proceed to") != std::string::npos ||
        lower.find("move to") != std::string::npos || lower.find("head to") != std::string::npos ||
        lower.find("navigate to") != std::string::npos || lower.find("reach the") != std::string::npos ||
        lower.find("go towards") != std::string::npos || lower.find("heading to") != std::string::npos ||
        lower.find("take me to") != std::string::npos || lower.find("direct to") != std::string::npos ||
        // Hindi / Marathi
        lower.find("जाओ") != std::string::npos || lower.find("जाएं") != std::string::npos ||
        lower.find("चलो") != std::string::npos || lower.find("पहुंचो") != std::string::npos ||
        lower.find("की तरफ जाओ") != std::string::npos || lower.find("को जाना") != std::string::npos ||
        lower.find("पहुंचें") != std::string::npos ||
        // Gujarati
        lower.find("જાઓ") != std::string::npos || lower.find("પહોંચો") != std::string::npos ||
        // Bengali
        lower.find("যাও") != std::string::npos || lower.find("পৌঁছাও") != std::string::npos ||
        // Tamil
        lower.find("போ") != std::string::npos || lower.find("செல்") != std::string::npos ||
        lower.find("சென்றடை") != std::string::npos ||
        // Telugu
        lower.find("వెళ్ళండి") != std::string::npos || lower.find("చేరండి") != std::string::npos ||
        // Kannada
        lower.find("ಹೋಗಿ") != std::string::npos || lower.find("ತಲುಪಿ") != std::string::npos ||
        // Malayalam
        lower.find("പോകൂ") != std::string::npos || lower.find("എത്തൂ") != std::string::npos ||
        // Odia
        lower.find("ଯାଅ") != std::string::npos || lower.find("ପହଞ୍ଚ") != std::string::npos) {
        outAction = ActionCode::GO_TO;
        return ActionCode::GO_TO;
    }

    return ActionCode::UNKNOWN;
}

UrgencyCode TinyMLAgent::classifyUrgency(const std::string& text,
                                         ActionCode intent,
                                         HazardCode hazard,
                                         const std::vector<uint8_t>& acousticProsody) {
    if (acousticProsody.size() >= 16) {
        uint8_t energyByte = acousticProsody[0];
        if (energyByte >= 0xD0) return UrgencyCode::CRITICAL_SOS;
        if (energyByte >= 0x80) return UrgencyCode::TACTICAL;
    }

    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    // Critical Emergency in 10 languages
    if (lower.find("immediately") != std::string::npos || lower.find("immediate") != std::string::npos ||
        lower.find("urgent") != std::string::npos || lower.find("sos") != std::string::npos ||
        lower.find("critical") != std::string::npos || lower.find("right now") != std::string::npos ||
        lower.find("asap") != std::string::npos || lower.find("emergency") != std::string::npos ||
        lower.find("तुरंत") != std::string::npos || lower.find("फौरन") != std::string::npos ||
        lower.find("आपातकाल") != std::string::npos || lower.find("तातडीने") != std::string::npos ||
        lower.find("તાત્કાલિક") != std::string::npos || lower.find("કટોકટી") != std::string::npos ||
        lower.find("உடனடியாக") != std::string::npos || lower.find("அவசரம்") != std::string::npos ||
        lower.find("వెంటనే") != std::string::npos || lower.find("అత్యవసరం") != std::string::npos ||
        lower.find("ತಕ್ಷಣ") != std::string::npos || lower.find("ತುರ್ತು") != std::string::npos ||
        lower.find("ഉടൻ") != std::string::npos || lower.find("അടിയന്തിരം") != std::string::npos ||
        lower.find("ତୁରନ୍ତ") != std::string::npos || lower.find("ଜରୁରୀ") != std::string::npos ||
        lower.find("অবিলম্বে") != std::string::npos || lower.find("জরুরি") != std::string::npos ||
        intent == ActionCode::RESCUE_REQUEST || intent == ActionCode::SOS ||
        hazard == HazardCode::FLOOD || hazard == HazardCode::FIRE || hazard == HazardCode::EXPLOSION) {
        return UrgencyCode::CRITICAL_SOS;
    }

    // Tactical Quick Actions in 10 languages
    if (lower.find("quickly") != std::string::npos || lower.find("fast") != std::string::npos ||
        lower.find("soon") != std::string::npos || lower.find("जल्दी") != std::string::npos ||
        lower.find("लवकर") != std::string::npos || lower.find("ઝડપથી") != std::string::npos ||
        lower.find("விரைவில்") != std::string::npos || lower.find("త్వరగా") != std::string::npos ||
        lower.find("ಬೇಗ") != std::string::npos || lower.find("വേഗത്തിൽ") != std::string::npos ||
        lower.find("ଶୀଘ୍ର") != std::string::npos || lower.find("দ্রুত") != std::string::npos ||
        intent == ActionCode::EVACUATE || intent == ActionCode::MOVE || intent == ActionCode::SEARCH) {
        return UrgencyCode::TACTICAL;
    }

    return UrgencyCode::ROUTINE;
}

SemanticResult TinyMLAgent::runDeterministicFallback(const std::string& text,
                                                     const std::string& sourceLanguage,
                                                     const std::vector<uint8_t>& prosody) {
    SemanticResult res;
    res.originalText = text;
    res.detectedLanguage = detectLanguage(text, sourceLanguage);
    res.modelBackendUsed = "DETERMINISTIC_LOCAL_FALLBACK";

    // Validate prosody vector size
    if (!prosody.empty()) {
        if (prosody.size() == 16) {
            res.prosodyVector = prosody;
        } else {
            // Pad or truncate to 16 bytes
            res.prosodyVector.resize(16, 0);
            for (size_t i = 0; i < std::min<size_t>(16, prosody.size()); ++i) {
                res.prosodyVector[i] = prosody[i];
            }
        }
    }

    // 1. Location Entity Resolution
    res.location = geoResolver_.resolveLocation(text);
    // Only high-confidence direct-alias matches count: fuzzy/soundex
    // candidates (conf <= ~0.95) produced phantom locations such as
    // "School" for "I'm stuck in flood" — in disaster traffic a wrong
    // location is more dangerous than none.
    if (res.location.geoId != GeoID::UNKNOWN && res.location.confidence < 0.95f) {
        res.location.geoId = GeoID::UNKNOWN;
        res.location.canonicalName.clear();
        res.location.matchedToken.clear();
        res.location.confidence = 0.0f;
    }
    if (res.location.geoId != GeoID::UNKNOWN) {
        res.extractedEntities.push_back({"LOCATION", res.location.canonicalName, res.location.confidence});
    }

    // 2. Intent & Action Extraction
    res.intent = extractActionAndIntent(text, res.action);
    if (res.intent != ActionCode::UNKNOWN) {
        res.extractedEntities.push_back({"INTENT", actionToString(res.intent), 0.92f});
    }

    // 3. Hazard Extraction
    res.hazard = extractHazard(text);
    if (res.hazard != HazardCode::NONE) {
        res.extractedEntities.push_back({"HAZARD", hazardToString(res.hazard), 0.95f});
    }

    // 4. Person Count Extraction
    res.personCount = extractPersonCount(text);
    if (res.personCount > 0) {
        res.extractedEntities.push_back({"PERSON_COUNT", std::to_string(res.personCount), 0.98f});
    }

    // 5. Negation Detection
    res.isNegated = extractNegation(text);
    if (res.isNegated) {
        res.extractedEntities.push_back({"MODIFIER", "NEGATION", 1.0f});
        // Decline-class only: bare absence ("no water", "నీరు లేదు") keeps
        // isStrongNegation=false so realize() renders the POSITIVE need.
        res.isStrongNegation = extractStrongNegation(text);
    }

    // 6. Urgency Classification
    res.urgency = classifyUrgency(text, res.intent, res.hazard, res.prosodyVector);

    // 7. Confidence & Tier Selection Logic
    // If no meaningful semantic concept was recognized, or general negated statement with unknown intent
    // A LOCATION_REPORT that yielded NO location, hazard or person count
    // ("I am in trouble") carries no semantics — treat it as free-form
    // instead of emitting a hollow "Location update received."
    bool vacuousLocationReport =
        res.intent == ActionCode::LOCATION_REPORT &&
        res.hazard == HazardCode::NONE &&
        res.location.geoId == GeoID::UNKNOWN &&
        res.personCount == 0;
    if ((res.intent == ActionCode::UNKNOWN || vacuousLocationReport) &&
        res.hazard == HazardCode::NONE && res.location.geoId == GeoID::UNKNOWN) {
        res.isFallback = true;
        res.fallbackReason = "Unrecognized semantic intent / natural conversational statement";
        res.confidence = 0.85f;
        res.compressionTier = CompressionTier::TIER_3_FALLBACK;
    } else if (res.location.geoId != GeoID::UNKNOWN || res.personCount > 0 || res.isNegated) {
        // Rich structured information present -> Tier 2 (includes negation flag)
        res.isFallback = false;
        res.confidence = 0.90f;
        res.compressionTier = CompressionTier::TIER_2_STRUCTURED;
    } else {
        // Clean compact macro -> Tier 1
        res.isFallback = false;
        res.confidence = 0.95f;
        res.compressionTier = CompressionTier::TIER_1_MACRO;
    }

    return res;
}

SemanticResult TinyMLAgent::analyze(const std::string& text,
                                    const std::string& sourceLanguage,
                                    const std::vector<uint8_t>& optionalProsody) {
    if (mlModel_ && mlModel_->isModelLoaded()) {
        SemanticResult res;
        if (mlModel_->runInference(text, sourceLanguage, res)) {
            res.modelBackendUsed = mlModel_->getModelName();
            if (!optionalProsody.empty()) {
                res.prosodyVector = optionalProsody;
                if (res.prosodyVector.size() != 16) res.prosodyVector.resize(16, 0);
            }
            return res;
        }
    }

    // Use deterministic fallback
    return runDeterministicFallback(text, sourceLanguage, optionalProsody);
}

} // namespace itantra::semantic
