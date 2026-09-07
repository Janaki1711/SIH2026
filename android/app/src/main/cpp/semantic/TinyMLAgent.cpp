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
    // Simple Unicode range inspection for Indic scripts
    for (size_t i = 0; i < text.size(); ++i) {
        unsigned char c = static_cast<unsigned char>(text[i]);
        if (c == 0xE0) {
            if (i + 2 < text.size()) {
                unsigned char c1 = static_cast<unsigned char>(text[i + 1]);
                if (c1 == 0xA4 || c1 == 0xA5) return "hi"; // Devanagari (Hindi / Marathi)
                if (c1 == 0xAE || c1 == 0xAF) return "ta"; // Tamil
                if (c1 == 0xB0 || c1 == 0xB1) return "te"; // Telugu
                if (c1 == 0xB2 || c1 == 0xB3) return "kn"; // Kannada
            }
        }
    }
    return "en";
}

uint32_t TinyMLAgent::extractPersonCount(const std::string& text) {
    // Check number words
    static const std::unordered_map<std::string, uint32_t> words = {
        {"one", 1}, {"two", 2}, {"three", 3}, {"four", 4}, {"five", 5},
        {"six", 6}, {"seven", 7}, {"eight", 8}, {"nine", 9}, {"ten", 10},
        {"एक", 1}, {"दो", 2}, {"दोन", 2}, {"तीन", 3}, {"चार", 4}, {"पांच", 5},
        {"पाँच", 5}, {"पाच", 5}, {"छह", 6}, {"सात", 7}, {"आठ", 8}, {"नौ", 9}, {"दस", 10},
        {"ஒன்று", 1}, {"இரண்டு", 2}, {"மூன்று", 3}, {"நான்கு", 4}, {"ஐந்து", 5},
        {"ఒకటి", 1}, {"రెండు", 2}, {"మూడు", 3}, {"నాలుగు", 4}, {"ఐదు", 5},
        {"ಒಂದು", 1}, {"ಎರಡು", 2}, {"ಮೂರು", 3}, {"ನಾಲ್ಕು", 4}, {"ಐದು", 5}
    };

    // 1. Direct word search
    for (const auto& [word, count] : words) {
        if (text.find(word) != std::string::npos) {
            return count;
        }
    }

    // 2. Regular expression for digits preceding people/victim words
    std::regex countRegex(R"(\b(\d+)\s*(people|persons|trapped|victims|casualties|men|women|children|जवान|लोग|व्यक्तियों)?\b)", std::regex::icase);
    std::smatch match;
    if (std::regex_search(text, match, countRegex)) {
        try {
            return static_cast<uint32_t>(std::stoul(match[1].str()));
        } catch (...) {}
    }

    return 0;
}

HazardCode TinyMLAgent::extractHazard(const std::string& text) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    if (lower.find("flood") != std::string::npos || lower.find("flooding") != std::string::npos ||
        lower.find("बाढ़") != std::string::npos || lower.find("पाणी") != std::string::npos ||
        lower.find("വെള്ളപ്പൊക്കം") != std::string::npos || lower.find("வெள்ளம்") != std::string::npos ||
        lower.find("వరదలు") != std::string::npos || lower.find("ಪ್ರವಾಹ") != std::string::npos) {
        return HazardCode::FLOOD;
    }
    if (lower.find("fire") != std::string::npos || lower.find("blaze") != std::string::npos ||
        lower.find("आग") != std::string::npos || lower.find("தீ") != std::string::npos ||
        lower.find("ಬೆಂಕಿ") != std::string::npos) {
        return HazardCode::FIRE;
    }
    if (lower.find("earthquake") != std::string::npos || lower.find("भूकंप") != std::string::npos) {
        return HazardCode::EARTHQUAKE;
    }
    if (lower.find("landslide") != std::string::npos || lower.find("भूस्खलन") != std::string::npos) {
        return HazardCode::LANDSLIDE;
    }
    if (lower.find("collapse") != std::string::npos || lower.find("collapsed") != std::string::npos ||
        lower.find("गिर गया") != std::string::npos) {
        return HazardCode::BUILDING_COLLAPSE;
    }
    if (lower.find("explosion") != std::string::npos || lower.find("blast") != std::string::npos ||
        lower.find("धमाका") != std::string::npos || lower.find("विस्फोट") != std::string::npos) {
        return HazardCode::EXPLOSION;
    }
    if (lower.find("gas leak") != std::string::npos || lower.find("toxic") != std::string::npos) {
        return HazardCode::GAS_LEAK;
    }
    return HazardCode::NONE;
}

ActionCode TinyMLAgent::extractActionAndIntent(const std::string& text, ActionCode& outAction) {
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    outAction = ActionCode::UNKNOWN;

    // Rescue / Help Request
    if (lower.find("rescue") != std::string::npos || lower.find("help") != std::string::npos ||
        lower.find("trapped") != std::string::npos || lower.find("stuck") != std::string::npos ||
        lower.find("मदद") != std::string::npos || lower.find("बचाओ") != std::string::npos ||
        lower.find("फंसे") != std::string::npos || lower.find("मदत") != std::string::npos ||
        lower.find("உதவி") != std::string::npos || lower.find("காப்பாற்று") != std::string::npos ||
        lower.find("సహాయం") != std::string::npos || lower.find("ಸಹಾಯ") != std::string::npos ||
        lower.find("रಕ್ಷಿಸಿ") != std::string::npos || lower.find("send help") != std::string::npos) {
        
        if (lower.find("boat") != std::string::npos || lower.find("नाव") != std::string::npos || lower.find("படகு") != std::string::npos) {
            outAction = ActionCode::BOAT;
        } else if (lower.find("team") != std::string::npos || lower.find("दल") != std::string::npos || lower.find("भेजो") != std::string::npos) {
            outAction = ActionCode::SEND_TEAM;
        } else {
            outAction = ActionCode::RESCUE_REQUEST;
        }
        return ActionCode::RESCUE_REQUEST;
    }

    // Evacuate
    if (lower.find("evacuate") != std::string::npos || lower.find("evacuation") != std::string::npos ||
        lower.find("खाली करो") != std::string::npos || lower.find("निकालो") != std::string::npos ||
        lower.find("வெளியேற்று") != std::string::npos) {
        outAction = ActionCode::EVACUATE;
        return ActionCode::EVACUATE;
    }

    // Medical
    if (lower.find("medical") != std::string::npos || lower.find("doctor") != std::string::npos ||
        lower.find("ambulance") != std::string::npos || lower.find("injured") != std::string::npos ||
        lower.find("चिकित्सा") != std::string::npos || lower.find("घायल") != std::string::npos ||
        lower.find("மருத்துவம்") != std::string::npos) {
        outAction = ActionCode::MEDICAL;
        return ActionCode::MEDICAL;
    }

    // Supplies
    if (lower.find("supplies") != std::string::npos || lower.find("food") != std::string::npos ||
        lower.find("water") != std::string::npos || lower.find("ration") != std::string::npos ||
        lower.find("राशन") != std::string::npos || lower.find("पानी") != std::string::npos) {
        outAction = ActionCode::SUPPLIES;
        return ActionCode::SUPPLIES;
    }

    // Search
    if (lower.find("search") != std::string::npos || lower.find("missing") != std::string::npos ||
        lower.find("खोजो") != std::string::npos || lower.find("गायब") != std::string::npos ||
        lower.find("தேடு") != std::string::npos) {
        outAction = ActionCode::SEARCH;
        return ActionCode::SEARCH;
    }

    // Alert
    if (lower.find("alert") != std::string::npos || lower.find("warning") != std::string::npos ||
        lower.find("चेतावनी") != std::string::npos || lower.find("எச்சரிக்கை") != std::string::npos) {
        outAction = ActionCode::ALERT;
        return ActionCode::ALERT;
    }

    // Move
    if (lower.find("moving") != std::string::npos || lower.find("advance") != std::string::npos ||
        lower.find("आगे बढ़") != std::string::npos) {
        outAction = ActionCode::MOVE;
        return ActionCode::MOVE;
    }

    // Report
    if (lower.find("report") != std::string::npos || lower.find("status") != std::string::npos ||
        lower.find("सूचना") != std::string::npos) {
        outAction = ActionCode::REPORT;
        return ActionCode::REPORT;
    }

    return ActionCode::UNKNOWN;
}

UrgencyCode TinyMLAgent::classifyUrgency(const std::string& text,
                                         ActionCode intent,
                                         HazardCode hazard,
                                         const std::vector<uint8_t>& acousticProsody) {
    // 1. If acoustic prosody has high energy (e.g. byte 0 indicates stress/pitch > threshold)
    if (acousticProsody.size() >= 16) {
        uint8_t energyByte = acousticProsody[0];
        if (energyByte >= 0xD0) {
            return UrgencyCode::CRITICAL_SOS;
        } else if (energyByte >= 0x80) {
            return UrgencyCode::TACTICAL;
        }
    }

    // 2. Textual triage rules
    std::string lower;
    lower.reserve(text.size());
    for (char c : text) lower.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));

    if (lower.find("immediately") != std::string::npos || lower.find("immediate") != std::string::npos ||
        lower.find("urgent") != std::string::npos || lower.find("sos") != std::string::npos ||
        lower.find("critical") != std::string::npos || lower.find("right now") != std::string::npos ||
        lower.find("asap") != std::string::npos || lower.find("emergency") != std::string::npos ||
        lower.find("तुरंत") != std::string::npos || lower.find("फौरन") != std::string::npos ||
        lower.find("आपातकाल") != std::string::npos || lower.find("உடனடியாக") != std::string::npos ||
        lower.find("వెంటనే") != std::string::npos || lower.find("ತಕ್ಷಣ") != std::string::npos ||
        intent == ActionCode::RESCUE_REQUEST || intent == ActionCode::SOS ||
        hazard == HazardCode::FLOOD || hazard == HazardCode::FIRE || hazard == HazardCode::EXPLOSION) {
        return UrgencyCode::CRITICAL_SOS;
    }

    if (lower.find("quickly") != std::string::npos || lower.find("fast") != std::string::npos ||
        lower.find("soon") != std::string::npos || lower.find("जल्दी") != std::string::npos ||
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

    // 5. Urgency Classification
    res.urgency = classifyUrgency(text, res.intent, res.hazard, res.prosodyVector);

    // 6. Confidence & Tier Selection Logic
    // If no meaningful semantic concept was recognized (intent unknown, hazard none, location unknown)
    if (res.intent == ActionCode::UNKNOWN && res.hazard == HazardCode::NONE && res.location.geoId == GeoID::UNKNOWN) {
        res.isFallback = true;
        res.fallbackReason = "Unrecognized semantic intent / out-of-codebook natural language";
        res.confidence = 0.35f;
        res.compressionTier = CompressionTier::TIER_3_FALLBACK;
    } else if (res.location.geoId != GeoID::UNKNOWN || res.personCount > 0 || res.extractedEntities.size() >= 3) {
        // Rich structured information present -> Tier 2
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
