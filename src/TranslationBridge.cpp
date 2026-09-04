#include "TranslationBridge.hpp"
#include <sstream>

namespace itantra::translation {

TranslationBridge::TranslationBridge() : model_(nullptr) {}

TranslationBridge::TranslationBridge(std::shared_ptr<ITranslationModel> model) : model_(model) {}

void TranslationBridge::setModel(std::shared_ptr<ITranslationModel> model) {
    model_ = model;
}

std::string TranslationBridge::getTargetLocationName(uint16_t geoId, const std::string& lang) {
    if (geoId == semantic::GeoID::UNKNOWN) return "";

    if (lang == "hi" || lang == "mr") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "तोलनकेरे";
            case semantic::GeoID::HUBBLI:    return "हब्बली";
            case semantic::GeoID::BASE:      return "बेस कैंप";
            case semantic::GeoID::SECTOR_1:  return "सेक्टर 1";
            case semantic::GeoID::SECTOR_2:  return "सेक्टर 2";
            case semantic::GeoID::SECTOR_3:  return "सेक्टर 3";
            case semantic::GeoID::SECTOR_4:  return "सेक्टर 4";
            case semantic::GeoID::SECTOR_5:  return "सेक्टर 5";
            case semantic::GeoID::BRIDGE:    return "पुल";
            case semantic::GeoID::HOSPITAL:  return "अस्पताल";
            case semantic::GeoID::SCHOOL:    return "स्कूल";
            default: return "स्थान";
        }
    } else if (lang == "ta") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "தோலன்கெரே";
            case semantic::GeoID::HUBBLI:    return "ஹூப்ளி";
            case semantic::GeoID::BASE:      return "முகாம்";
            case semantic::GeoID::SECTOR_4:  return "செக்டர் 4";
            case semantic::GeoID::BRIDGE:    return "பாலம்";
            case semantic::GeoID::HOSPITAL:  return "மருத்துவமனை";
            case semantic::GeoID::SCHOOL:    return "பள்ளி";
            default: return "இடம்";
        }
    } else if (lang == "kn") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "ತೊಳನಕೆರೆ";
            case semantic::GeoID::HUBBLI:    return "ಹುಬ್ಬಳ್ಳಿ";
            case semantic::GeoID::BASE:      return "ಬೇಸ್ ಕ್ಯಾಂಪ್";
            case semantic::GeoID::SECTOR_4:  return "ಸೆಕ್ಟರ್ 4";
            case semantic::GeoID::BRIDGE:    return "ಸೇತುವೆ";
            case semantic::GeoID::HOSPITAL:  return "ಆಸ್ಪತ್ರೆ";
            case semantic::GeoID::SCHOOL:    return "ಶಾಲೆ";
            default: return "ಸ್ಥಳ";
        }
    } else if (lang == "te") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "తోలంకెరె";
            case semantic::GeoID::HUBBLI:    return "హుబ్లి";
            case semantic::GeoID::BASE:      return "బేస్ క్యాంప్";
            case semantic::GeoID::SECTOR_4:  return "సెక్టర్ 4";
            case semantic::GeoID::BRIDGE:    return "వంతెన";
            case semantic::GeoID::HOSPITAL:  return "ఆసుపత్రి";
            case semantic::GeoID::SCHOOL:    return "పాఠశాల";
            default: return "ప్రాంతం";
        }
    }

    return semantic::geoIdToString(geoId);
}

std::string TranslationBridge::realizeEnglish(const semantic::SemanticResult& res) {
    if (res.isFallback) {
        return res.originalText.empty() ? "[Fallback message]" : res.originalText;
    }

    std::ostringstream oss;
    std::string loc = res.location.canonicalName.empty() ? "" : res.location.canonicalName;

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << res.personCount << " people trapped near " << loc;
            if (res.hazard == semantic::HazardCode::FLOOD) oss << " due to flood. Send rescue team immediately.";
            else if (res.hazard == semantic::HazardCode::FIRE) oss << " due to fire. Send rescue team immediately.";
            else oss << ". Send rescue team immediately.";
        } else if (res.personCount > 0) {
            oss << res.personCount << " people trapped. Requesting rescue assistance.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "Help, there is a flood";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "Help, there is a fire";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
        } else {
            oss << "Rescue assistance requested";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        oss << "Evacuate immediately";
        if (!loc.empty()) oss << " from " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        oss << "Medical assistance required";
        if (!loc.empty()) oss << " at " << loc;
        oss << ".";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << semantic::actionToString(res.action) << " at " << loc << ".";
        return oss.str();
    }

    return res.originalText.empty() ? "Emergency message received." : res.originalText;
}

std::string TranslationBridge::realizeHindi(const semantic::SemanticResult& res) {
    if (res.isFallback) {
        return res.originalText.empty() ? "[आपातकालीन संदेश]" : res.originalText;
    }

    std::ostringstream oss;
    std::string loc = getTargetLocationName(res.location.geoId, "hi");

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " के पास " << res.personCount << " लोग फंसे हुए हैं";
            if (res.hazard == semantic::HazardCode::FLOOD) oss << " बाढ़ के कारण। तुरंत बचाव दल भेजो।";
            else oss << "। तुरंत बचाव दल भेजो।";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "मदद, बाढ़ आ गई है";
            if (!loc.empty()) oss << " " << loc << " में";
            oss << "। तुरंत सहायता भेजो।";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "आग लग गई है";
            if (!loc.empty()) oss << " " << loc << " में";
            oss << "। तुरंत फायर ब्रिगेड भेजो।";
        } else {
            if (!loc.empty()) oss << loc << " में तुरंत मदद भेजो।";
            else oss << "तुरंत बचाव सहायता भेजो।";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " को तुरंत खाली करो।";
        else oss << "क्षेत्र को तुरंत खाली करो।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " में चिकित्सा दल की आवश्यकता है।";
        else oss << "तुरंत चिकित्सा सहायता भेजो।";
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeTamil(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[அவசர செய்தி]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "ta");
    std::ostringstream oss;

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " அருகில் " << res.personCount << " பேர் சிக்கியுள்ளனர். உடனடியாக மீட்புக் குழுவை அனுப்பவும்.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "உதவி, வெள்ளம் வந்துள்ளது. உடனடியாக மீட்புக் குழுவை அனுப்பவும்.";
        } else {
            oss << "உடனடியாக உதவி தேவை.";
        }
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeKannada(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[ತುರ್ತು ಸಂದೇಶ]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "kn");
    std::ostringstream oss;

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " ಹತ್ತಿರ " << res.personCount << " ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ. ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "ಸಹಾಯ ಮಾಡಿ, ಪ್ರವಾಹ ಬಂದಿದೆ. ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ.";
        } else {
            oss << "ತಕ್ಷಣ ರಕ್ಷಣಾ ಸಹಾಯ ಕಳುಹಿಸಿ.";
        }
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeMarathi(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[तातडीचा संदेश]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "mr");
    std::ostringstream oss;

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " जवळ " << res.personCount << " लोक अडकले आहेत. तातडीने बचाव पथक पाठवा.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "मदत करा, पूर आला आहे. तातडीने मदत पाठवा.";
        } else {
            oss << "तातडीने मदत पाठवा.";
        }
        return oss.str();
    }

    return realizeHindi(res);
}

std::string TranslationBridge::realizeTelugu(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[అత్యవసర సందేశం]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "te");
    std::ostringstream oss;

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " వద్ద " << res.personCount << " మంది చిక్కుకున్నారు. వెంటనే రక్షణ బృందాన్ని పంపండి.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "సహాయం, వరదలు వచ్చాయి. వెంటనే రక్షణ బృందాన్ని పంపండి.";
        } else {
            oss << "వెంటనే సహాయం పంపండి.";
        }
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realize(const semantic::SemanticResult& result, const std::string& targetLanguage) {
    if (targetLanguage == "hi") return realizeHindi(result);
    if (targetLanguage == "ta") return realizeTamil(result);
    if (targetLanguage == "kn") return realizeKannada(result);
    if (targetLanguage == "mr") return realizeMarathi(result);
    if (targetLanguage == "te") return realizeTelugu(result);
    return realizeEnglish(result);
}

std::string TranslationBridge::translate(const std::string& text,
                                         const std::string& sourceLanguage,
                                         const std::string& targetLanguage) {
    if (sourceLanguage == targetLanguage) return text;
    if (model_ && model_->isLoaded()) {
        return model_->translate(text, sourceLanguage, targetLanguage);
    }
    // Return original text labeled as fallback
    return text;
}

} // namespace itantra::translation
