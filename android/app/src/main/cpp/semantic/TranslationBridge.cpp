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
            case semantic::GeoID::KOLHAPUR:  return "कोल्हापुर";
            case semantic::GeoID::BENGALURU: return "बेंगलुरु";
            case semantic::GeoID::BASE:      return "बेस कैंप";
            case semantic::GeoID::SECTOR_1:  return "सेक्टर 1";
            case semantic::GeoID::SECTOR_2:  return "सेक्टर 2";
            case semantic::GeoID::SECTOR_3:  return "सेक्टर 3";
            case semantic::GeoID::SECTOR_4:  return "सेक्टर 4";
            case semantic::GeoID::SECTOR_5:  return "सेक्टर 5";
            case semantic::GeoID::BRIDGE:    return "पुल";
            case semantic::GeoID::HOSPITAL:  return "अस्पताल";
            case semantic::GeoID::SCHOOL:    return "स्कूल";
            // FIX 3: New location types in Hindi
            case semantic::GeoID::RAILWAY_STATION: return "रेलवे स्टेशन";
            case semantic::GeoID::BUS_STAND:       return "बस स्टैंड";
            case semantic::GeoID::AIRPORT:         return "हवाई अड्डा";
            case semantic::GeoID::POLICE_STATION:  return "पुलिस स्टेशन";
            case semantic::GeoID::FIRE_STATION:    return "दमकल केंद्र";
            case semantic::GeoID::MARKET:          return "बाजार";
            case semantic::GeoID::TEMPLE:          return "मंदिर";
            case semantic::GeoID::MOSQUE:          return "मस्जिद";
            case semantic::GeoID::CHURCH:          return "चर्च";
            case semantic::GeoID::HOME:            return "घर";
            case semantic::GeoID::VILLAGE:         return "गांव";
            default: return "स्थान";
        }
    } else if (lang == "gu") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "તોલનકેરે";
            case semantic::GeoID::HUBBLI:    return "હુબલી";
            case semantic::GeoID::KOLHAPUR:  return "કોલ્હાપુર";
            case semantic::GeoID::BENGALURU: return "બેંગલુરુ";
            case semantic::GeoID::BASE:      return "બેઝ કેમ્પ";
            case semantic::GeoID::SECTOR_4:  return "સેક્ટર 4";
            case semantic::GeoID::BRIDGE:    return "પુલ";
            case semantic::GeoID::HOSPITAL:  return "હોસ્પિટલ";
            case semantic::GeoID::SCHOOL:    return "શાળા";
            // FIX 3: New location types in Gujarati
            case semantic::GeoID::RAILWAY_STATION: return "રેલ્વે સ્ટેશન";
            case semantic::GeoID::BUS_STAND:       return "બસ સ્ટૅન્ડ";
            case semantic::GeoID::AIRPORT:         return "એરપોર્ટ";
            case semantic::GeoID::POLICE_STATION:  return "પોલીસ સ્ટેશન";
            case semantic::GeoID::FIRE_STATION:    return "ફાયર સ્ટેશન";
            case semantic::GeoID::MARKET:          return "બજાર";
            case semantic::GeoID::TEMPLE:          return "મંદિર";
            case semantic::GeoID::HOME:            return "ઘર";
            case semantic::GeoID::VILLAGE:         return "ગામ";
            default: return "સ્થળ";
        }
    } else if (lang == "ta") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "தோலன்கெரே";
            case semantic::GeoID::HUBBLI:    return "ஹூப்ளி";
            case semantic::GeoID::KOLHAPUR:  return "கோல்ஹாப்பூர்";
            case semantic::GeoID::BENGALURU: return "பெங்களூர்";
            case semantic::GeoID::BASE:      return "முகாம்";
            case semantic::GeoID::SECTOR_4:  return "செக்டர் 4";
            case semantic::GeoID::BRIDGE:    return "பாலம்";
            case semantic::GeoID::HOSPITAL:  return "மருத்துவமனை";
            case semantic::GeoID::SCHOOL:    return "பள்ளி";
            // FIX 3: New location types in Tamil
            case semantic::GeoID::RAILWAY_STATION: return "இரயில் நிலையம்";
            case semantic::GeoID::BUS_STAND:       return "பஸ் நிலையம்";
            case semantic::GeoID::AIRPORT:         return "விமான நிலையம்";
            case semantic::GeoID::POLICE_STATION:  return "காவல் நிலையம்";
            case semantic::GeoID::FIRE_STATION:    return "தீயணைப்பு நிலையம்";
            case semantic::GeoID::MARKET:          return "சந்தை";
            case semantic::GeoID::TEMPLE:          return "கோயில்";
            case semantic::GeoID::MOSQUE:          return "மசூதி";
            case semantic::GeoID::HOME:            return "வீடு";
            case semantic::GeoID::VILLAGE:         return "கிராமம்";
            default: return "இடம்";
        }
    } else if (lang == "kn") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "ತೊಳನಕೆರೆ";
            case semantic::GeoID::HUBBLI:    return "ಹುಬ್ಬಳ್ಳಿ";
            case semantic::GeoID::KOLHAPUR:  return "ಕೊಲ್ಹಾಪುರ";
            case semantic::GeoID::BENGALURU: return "ಬೆಂಗಳೂರು";
            case semantic::GeoID::BASE:      return "ಬೇಸ್ ಕ್ಯಾಂಪ್";
            case semantic::GeoID::SECTOR_4:  return "ಸೆಕ್ಟರ್ 4";
            case semantic::GeoID::BRIDGE:    return "ಸೇತುವೆ";
            case semantic::GeoID::HOSPITAL:  return "ಆಸ್ಪತ್ರೆ";
            case semantic::GeoID::SCHOOL:    return "ಶಾಲೆ";
            // FIX 3: New location types in Kannada
            case semantic::GeoID::RAILWAY_STATION: return "ರೈಲ್ವೆ ನಿಲ್ದಾಣ";
            case semantic::GeoID::BUS_STAND:       return "ಬಸ್ ನಿಲ್ದಾಣ";
            case semantic::GeoID::AIRPORT:         return "ವಿಮಾನ ನಿಲ್ದಾಣ";
            case semantic::GeoID::POLICE_STATION:  return "ಪೊಲೀಸ್ ಠಾಣೆ";
            case semantic::GeoID::FIRE_STATION:    return "ಅಗ್ನಿಶಾಮಕ ಠಾಣೆ";
            case semantic::GeoID::MARKET:          return "ಮಾರ್ಕೆಟ್";
            case semantic::GeoID::TEMPLE:          return "ದೇವಾಲಯ";
            case semantic::GeoID::HOME:            return "ಮನೆ";
            case semantic::GeoID::VILLAGE:         return "ಗ್ರಾಮ";
            default: return "ಸ್ಥಳ";
        }
    } else if (lang == "te") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "తోలంకెరె";
            case semantic::GeoID::HUBBLI:    return "హుబ్లి";
            case semantic::GeoID::KOLHAPUR:  return "కోల్హాపూర్";
            case semantic::GeoID::BENGALURU: return "బెంగళూరు";
            case semantic::GeoID::BASE:      return "బేస్ క్యాంప్";
            case semantic::GeoID::SECTOR_4:  return "సెక్టర్ 4";
            case semantic::GeoID::BRIDGE:    return "వంతెన";
            case semantic::GeoID::HOSPITAL:  return "ఆసుపత్రి";
            case semantic::GeoID::SCHOOL:    return "పాఠశాల";
            // FIX 3: New location types in Telugu
            case semantic::GeoID::RAILWAY_STATION: return "రైల్వే స్టేషన్";
            case semantic::GeoID::BUS_STAND:       return "బస్ స్టాండ్";
            case semantic::GeoID::AIRPORT:         return "విమానాశ్రయం";
            case semantic::GeoID::POLICE_STATION:  return "పోలీస్ స్టేషన్";
            case semantic::GeoID::FIRE_STATION:    return "అగ్నిమాపక కేంద్రం";
            case semantic::GeoID::MARKET:          return "మార్కెట్";
            case semantic::GeoID::TEMPLE:          return "మందిరం";
            case semantic::GeoID::HOME:            return "ఇల్లు";
            case semantic::GeoID::VILLAGE:         return "గ్రామం";
            default: return "ప్రాంతం";
        }
    } else if (lang == "ml") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "തോലൻകെരെ";
            case semantic::GeoID::HUBBLI:    return "ഹുബ്ലി";
            case semantic::GeoID::KOLHAPUR:  return "കോളാപ്പൂർ";
            case semantic::GeoID::BENGALURU: return "ബംഗളൂരു";
            case semantic::GeoID::BASE:      return "ബേസ് ക്യാമ്പ്";
            case semantic::GeoID::SECTOR_4:  return "സെക്ടർ 4";
            case semantic::GeoID::BRIDGE:    return "പാലം";
            case semantic::GeoID::HOSPITAL:  return "ആശുപത്രി";
            case semantic::GeoID::SCHOOL:    return "സ്കൂൾ";
            // FIX 3: New location types in Malayalam
            case semantic::GeoID::RAILWAY_STATION: return "റെയിൽവേ സ്റ്റേഷൻ";
            case semantic::GeoID::BUS_STAND:       return "ബസ് സ്റ്റോപ്പ്";
            case semantic::GeoID::AIRPORT:         return "വിമാനത്താവളം";
            case semantic::GeoID::POLICE_STATION:  return "പോലീസ് സ്റ്റേഷൻ";
            case semantic::GeoID::FIRE_STATION:    return "അഗ്നിശമന സേന";
            case semantic::GeoID::MARKET:          return "ചന്ത";
            case semantic::GeoID::TEMPLE:          return "ക്ഷേത്രം";
            case semantic::GeoID::MOSQUE:          return "മസ്ജിദ്";
            case semantic::GeoID::HOME:            return "വീട്";
            case semantic::GeoID::VILLAGE:         return "ഗ്രാമം";
            default: return "സ്ഥലം";
        }
    } else if (lang == "or") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "ତୋଲନକେରେ";
            case semantic::GeoID::HUBBLI:    return "ହୁବଳି";
            case semantic::GeoID::KOLHAPUR:  return "କୋଲ୍ହାପୁର";
            case semantic::GeoID::BENGALURU: return "ବେଙ୍ଗାଲୁରୁ";
            case semantic::GeoID::BASE:      return "ବେସ୍ କ୍ୟାମ୍ପ";
            case semantic::GeoID::SECTOR_4:  return "ସେକ୍ଟର 4";
            case semantic::GeoID::BRIDGE:    return "ପୋଲ";
            case semantic::GeoID::HOSPITAL:  return "ଡାକ୍ତରଖାନା";
            case semantic::GeoID::SCHOOL:    return "ବିଦ୍ୟାଳୟ";
            // FIX 3: New location types in Odia
            case semantic::GeoID::RAILWAY_STATION: return "ରେଳ ଷ୍ଟେସନ";
            case semantic::GeoID::BUS_STAND:       return "ବସ ଷ୍ଟାଣ୍ଡ";
            case semantic::GeoID::AIRPORT:         return "ବିମାନ ବନ୍ଦର";
            case semantic::GeoID::POLICE_STATION:  return "ପୋଲିସ ଷ୍ଟେସନ";
            case semantic::GeoID::MARKET:          return "ବଜାର";
            case semantic::GeoID::TEMPLE:          return "ମନ୍ଦିର";
            case semantic::GeoID::HOME:            return "ଘର";
            case semantic::GeoID::VILLAGE:         return "ଗ୍ରାମ";
            default: return "ସ୍ଥାନ";
        }
    } else if (lang == "bn") {
        switch (geoId) {
            case semantic::GeoID::TOLANKERE: return "তোলনকেরে";
            case semantic::GeoID::HUBBLI:    return "হুব্বলি";
            case semantic::GeoID::KOLHAPUR:  return "কোল্হাপুর";
            case semantic::GeoID::BENGALURU: return "বেঙ্গালুরু";
            case semantic::GeoID::BASE:      return "বেস ক্যাম্প";
            case semantic::GeoID::SECTOR_4:  return "সেক্টর 4";
            case semantic::GeoID::BRIDGE:    return "ব্রিজ";
            case semantic::GeoID::HOSPITAL:  return "হাসপাতাল";
            case semantic::GeoID::SCHOOL:    return "বিদ্যালয়";
            // FIX 3: New location types in Bengali
            case semantic::GeoID::RAILWAY_STATION: return "রেলস্টেশন";
            case semantic::GeoID::BUS_STAND:       return "বাস স্ট্যান্ড";
            case semantic::GeoID::AIRPORT:         return "বিমানবন্দর";
            case semantic::GeoID::POLICE_STATION:  return "পুলিশ স্টেশন";
            case semantic::GeoID::FIRE_STATION:    return "ফায়ার স্টেশন";
            case semantic::GeoID::MARKET:          return "বাজার";
            case semantic::GeoID::TEMPLE:          return "মন্দির";
            case semantic::GeoID::MOSQUE:          return "মসজিদ";
            case semantic::GeoID::HOME:            return "বাড়ি";
            case semantic::GeoID::VILLAGE:         return "গ্রাম";
            default: return "স্থান";
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

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            oss << "Do NOT evacuate";
            if (!loc.empty()) oss << " " << loc;
            oss << ".";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            oss << "Medical assistance / ambulance NOT required";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            oss << "Rescue assistance NOT required";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::SUPPLIES) {
            oss << "Supplies / water NOT required";
            if (!loc.empty()) oss << " at " << loc;
            oss << ".";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::SEND_TEAM) {
            oss << "Do NOT send team";
            if (!loc.empty()) oss << " to " << loc;
            oss << ".";
            return oss.str();
        }
        oss << "Negative / No action required";
        if (!loc.empty()) oss << " at " << loc;
        oss << ".";
        return oss.str();
    }

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
            oss << ". Send rescue team immediately.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "Help, there is a fire";
            if (!loc.empty()) oss << " at " << loc;
            oss << ". Send rescue team immediately.";
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
        if (res.personCount > 0) {
            oss << " for " << res.personCount << " casualties/ambulances";
        }
        if (!loc.empty()) oss << " at " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        oss << "Water and emergency supplies requested";
        if (!loc.empty()) oss << " at " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        oss << "Our team is ready and advancing";
        if (!loc.empty()) oss << " towards " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "Fire alert!";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "Flood alert!";
        } else {
            oss << "Tactical alert issued";
        }
        if (!loc.empty()) oss << " at " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEARCH) {
        oss << "Search and rescue operation underway";
        if (!loc.empty()) oss << " near " << loc;
        oss << ".";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::REPORT) {
        oss << "Situation report update";
        if (!loc.empty()) oss << " from " << loc;
        oss << ".";
        return oss.str();
    }

    // FIX 3: Handle LOCATION_REPORT intent ("I am at X", "meet me at X")
    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) {
            oss << "Location report: at " << loc << ".";
        } else {
            oss << "Location update received.";
        }
        return oss.str();
    }

    // FIX 3: Handle GO_TO navigation intent properly
    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) {
            oss << "Proceed to " << loc << ".";
        } else {
            oss << "Navigate to destination.";
        }
        return oss.str();
    }

    if (!loc.empty()) {
        // FIX 3: For UNKNOWN intent with a known location, produce a meaningful message
        oss << "Location: " << loc << ".";
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

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " को खाली मत करो।";
            else oss << "क्षेत्र को खाली मत करो।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " में चिकित्सा सहायता / एम्बुलेंस की आवश्यकता नहीं है।";
            else oss << "चिकित्सा सहायता की आवश्यकता नहीं है।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " में बचाव सहायता की आवश्यकता नहीं है।";
            else oss << "बचाव सहायता की आवश्यकता नहीं है।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::SUPPLIES) {
            if (!loc.empty()) oss << loc << " में पानी / राशन की आवश्यकता नहीं है।";
            else oss << "पानी और राशन की आवश्यकता नहीं है।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::SEND_TEAM) {
            if (!loc.empty()) oss << loc << " में टीम मत भेजो।";
            else oss << "टीम भेजने की आवश्यकता नहीं है।";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " में किसी सहायता की आवश्यकता नहीं है।";
        else oss << "सहायता की आवश्यकता नहीं है।";
        return oss.str();
    }

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
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " में " << res.personCount << " एम्बुलेंस/चिकित्सा सहायता तुरंत भेजो।";
        } else if (!loc.empty()) {
            oss << loc << " में चिकित्सा दल की आवश्यकता है।";
        } else {
            oss << "तुरंत चिकित्सा सहायता भेजो।";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " में पानी और राशन की सहायता चाहिए।";
        else oss << "पानी और राशन की सहायता चाहिए।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "हमारी टीम तैयार है और " << loc << " की ओर रवाना हो रही है।";
        else oss << "हमारी टीम तैयार है।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "आग की चेतावनी! तुरंत सतर्क रहें।";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "बाढ़ की चेतावनी! तुरंत सतर्क रहें।";
        else oss << "चेतावनी जारी!";
        return oss.str();
    }

    // FIX 3: Handle LOCATION_REPORT intent in Hindi
    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "स्थान की सूचना: " << loc << " में हूं।";
        else oss << "स्थान की जानकारी मिली।";
        return oss.str();
    }

    // FIX 3: Handle GO_TO navigation intent in Hindi
    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " पर जाएं।";
        else oss << "गंतव्य पर जाएं।";
        return oss.str();
    }

    // FIX 3: For UNKNOWN intent with a known location, produce a meaningful Hindi message
    if (!loc.empty()) {
        oss << "स्थान: " << loc << "।";
        return oss.str();
    }

    return res.originalText.empty() ? "[आपातकालीन संदेश]" : res.originalText;
}

std::string TranslationBridge::realizeGujarati(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[કટોકટી સંદેશ]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "gu");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " ખાલી કરશો નહીં.";
            else oss << "વિસ્તાર ખાલી કરશો નહીં.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " માં એમ્બ્યુલન્સ / તબીબી સહાયની જરૂર નથી.";
            else oss << "તબીબી સહાયની જરૂર નથી.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " માં બચાવ સહાયની જરૂર નથી.";
            else oss << "બચાવ સહાયની જરૂર નથી.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " માં મદદની જરૂર નથી.";
        else oss << "કોઈ મદદની જરૂર નથી.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " નજીક " << res.personCount << " લોકો ફસાયા છે. તાત્કાલિક બચાવ ટીમ મોકલો.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "મદદ, પૂર આવ્યું છે";
            if (!loc.empty()) oss << " " << loc << " માં";
            oss << ". તાત્કાલિક બચાવ ટીમ મોકલો.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "આગ લાગી છે";
            if (!loc.empty()) oss << " " << loc << " માં";
            oss << ". તાત્કાલિક ફાયર બ્રિગેડ મોકલો.";
        } else {
            if (!loc.empty()) oss << loc << " માં તાત્કાલિક બચાવ સહાય મોકલો.";
            else oss << "તાત્કાલિક બચાવ સહાય મોકલો.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " તાત્કાલિક ખાલી કરો.";
        else oss << "વિસ્તાર તાત્કાલિક ખાલી કરો.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " માં તબીબી સહાય / એમ્બ્યુલન્સ મોકલો.";
        else oss << "તાત્કાલિક તબીબી સહાય મોકલો.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " માં પાણી અને ખોરાકની મદદ મોકલો.";
        else oss << "પાણી અને ખોરાકની મદદ મોકલો.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "અમારી ટીમ તૈયાર છે અને " << loc << " તરફ આગળ વધી રહી છે.";
        else oss << "અમારી ટીમ તૈયાર છે.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "આગની ચેતવણી!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "પૂરની ચેતવણી!";
        else oss << "ચેતવણી જારી!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "સ્થાનની જાણકારી: " << loc << ".";
        else oss << "સ્થાનની જાણકારી મળી.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " તરફ જાઓ.";
        else oss << "મુકામ તરફ જાઓ.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "સ્થાન: " << loc << ".";
        return oss.str();
    }

    return realizeHindi(res);
}

std::string TranslationBridge::realizeMarathi(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[तातडीचा संदेश]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "mr");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " परिसर रिकामा करू नका.";
            else oss << "परिसर रिकामा करू नका.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " मध्ये रुग्णवाहिका / वैद्यकीय मदतीची गरज नाही.";
            else oss << "वैद्यकीय मदतीची गरज नाही.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " मध्ये बचाव पथकाची गरज नाही.";
            else oss << "मदतीची गरज नाही.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " मध्ये मदतीची गरज नाही.";
        else oss << "मदतीची गरज नाही.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " जवळ " << res.personCount << " लोक अडकले आहेत. तातडीने बचाव पथक पाठवा.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "मदत करा, पूर आला आहे";
            if (!loc.empty()) oss << " " << loc << " मध्ये";
            oss << ". तातडीने मदत पाठवा.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "आग लागली आहे";
            if (!loc.empty()) oss << " " << loc << " मध्ये";
            oss << ". तातडीने मदत पाठवा.";
        } else {
            if (!loc.empty()) oss << loc << " मध्ये तातडीने मदत पाठवा.";
            else oss << "तातडीने मदत पाठवा.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " तातडीने रिकामे करा.";
        else oss << "परिसर तातडीने रिकामा करा.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " मध्ये पाणी आणि अन्न पुरवा.";
        else oss << "पाणी आणि अन्न पुरवा.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " मध्ये वैद्यकीय मदत / रुग्णवाहिका पाठवा.";
        else oss << "वैद्यकीय मदत पाठवा.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "आमचे पथक तयार आहे आणि " << loc << " कडे रवाना होत आहे.";
        else oss << "आमचे पथक तयार आहे.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "आगीचा इशारा!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "पुराचा इशारा!";
        else oss << "इशारा जारी!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "ठिकाणाची माहिती: " << loc << ".";
        else oss << "ठिकाणाची माहिती मिळाली.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " वर जा.";
        else oss << "ध्येयस्थानावर जा.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "ठिकाण: " << loc << ".";
        return oss.str();
    }

    return realizeHindi(res);
}

std::string TranslationBridge::realizeKannada(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[ತುರ್ತು ಸಂದೇಶ]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "kn");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " ಪ್ರದೇಶವನ್ನು ಖಾಲಿ ಮಾಡಬೇಡಿ.";
            else oss << "ಪ್ರದೇಶವನ್ನು ಖಾಲಿ ಮಾಡಬೇಡಿ.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " ಗೆ ಆಂಬ್ಯುಲೆನ್ಸ್ / ವೈದ್ಯಕೀಯ ನೆರವು ಅಗತ್ಯವಿಲ್ಲ.";
            else oss << "ವೈದ್ಯಕೀಯ ನೆರವು ಅಗತ್ಯವಿಲ್ಲ.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " ಗೆ ರಕ್ಷಣಾ ಸಹಾಯ ಅಗತ್ಯವಿಲ್ಲ.";
            else oss << "ರಕ್ಷಣಾ ಸಹಾಯ ಅಗತ್ಯವಿಲ್ಲ.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " ಗೆ ಯಾವುದೇ ಸಹಾಯ ಅಗತ್ಯವಿಲ್ಲ.";
        else oss << "ಯಾವುದೇ ಸಹಾಯ ಅಗತ್ಯವಿಲ್ಲ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " ಹತ್ತಿರ " << res.personCount << " ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ. ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "ಸಹಾಯ ಮಾಡಿ, ಪ್ರವಾಹ ಬಂದಿದೆ";
            if (!loc.empty()) oss << " " << loc << " ನಲ್ಲಿ";
            oss << ". ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "ಬೆಂಕಿ ಅವಘಡ ಸಂಭವಿಸಿದೆ";
            if (!loc.empty()) oss << " " << loc << " ನಲ್ಲಿ";
            oss << ". ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ.";
        } else {
            if (!loc.empty()) oss << loc << " ನಲ್ಲಿ ತಕ್ಷಣ ರಕ್ಷಣಾ ಸಹಾಯ ಕಳುಹಿಸಿ.";
            else oss << "ತಕ್ಷಣ ರಕ್ಷಣಾ ಸಹಾಯ ಕಳುಹಿಸಿ.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " ತಕ್ಷಣ ಖಾಲಿ ಮಾಡಿ.";
        else oss << "ಪ್ರದೇಶವನ್ನು ತಕ್ಷಣ ಖಾಲಿ ಮಾಡಿ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " ಗೆ ನೀರು ಮತ್ತು ಆಹಾರ ಸಹಾಯ ಕಳುಹಿಸಿ.";
        else oss << "ನೀರು ಮತ್ತು ಆಹಾರ ಸರಬರಾಜು ಕಳುಹಿಸಿ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " ಗೆ ವೈದ್ಯಕೀಯ ನೆರವು / ಆಂಬ್ಯುಲೆನ್ಸ್ ಕಳುಹಿಸಿ.";
        else oss << "ವೈದ್ಯಕೀಯ ನೆರವು ಕಳುಹಿಸಿ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "ನಮ್ಮ ತಂಡ ಸಿದ್ಧವಾಗಿದೆ ಮತ್ತು " << loc << " ಕಡೆಗೆ ಸಾಗುತ್ತಿದೆ.";
        else oss << "ನಮ್ಮ ತಂಡ ಸಿದ್ಧವಾಗಿದೆ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "ಬೆಂಕಿ ಎಚ್ಚರಿಕೆ!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ!";
        else oss << "ಎಚ್ಚರಿಕೆ ಸಂದೇಶ!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "ಸ್ಥಳ ವರದಿ: " << loc << ".";
        else oss << "ಸ್ಥಳ ಮಾಹಿತಿ ಬಂದಿದೆ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " ಕಡೆಗೆ ಹೋಗಿ.";
        else oss << "ಗಮ್ಯಸ್ಥಾನಕ್ಕೆ ಹೋಗಿ.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "ಸ್ಥಳ: " << loc << ".";
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeMalayalam(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[അടിയന്തര സന്ദേശം]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "ml");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " പ്രദേശം ഒഴിപ്പിക്കരുത്.";
            else oss << "പ്രദേശം ഒഴിപ്പിക്കരുത്.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " ലേക്ക് ആംബുലൻസ് / മെഡിക്കൽ സഹായം ആവശ്യമില്ല.";
            else oss << "മെഡിക്കൽ സഹായം ആവശ്യമില്ല.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " ലേക്ക് രക്ഷാപ്രവർത്തനം ആവശ്യമില്ല.";
            else oss << "സഹായം ആവശ്യമില്ല.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " ലേക്ക് സഹായം ആവശ്യമില്ല.";
        else oss << "സഹായം ആവശ്യമില്ല.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " സമീപം " << res.personCount << " ആളുകൾ കുടുങ്ങിയിരിക്കുന്നു. ഉടൻ രക്ഷാപ്രവർത്തകരെ അയക്കുക.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "സഹായം, വെള്ളപ്പൊക്കമുണ്ടായി";
            if (!loc.empty()) oss << " " << loc << " ൽ";
            oss << ". ഉടൻ രക്ഷാപ്രവർത്തകരെ അയക്കുക.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "തീപിടുത്തമുണ്ടായി";
            if (!loc.empty()) oss << " " << loc << " ൽ";
            oss << ". ഉടൻ രക്ഷാപ്രവർത്തകരെ അയക്കുക.";
        } else {
            if (!loc.empty()) oss << loc << " ൽ ഉടൻ രക്ഷാസഹായം അയക്കുക.";
            else oss << "ഉടൻ രക്ഷാസഹായം അയക്കുക.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " ഉടനടി ഒഴിപ്പിക്കുക.";
        else oss << "പ്രദേശം ഉടനടി ഒഴിപ്പിക്കുക.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " ലേക്ക് വെള്ളവും ഭക്ഷണവും എത്തിക്കുക.";
        else oss << "വെള്ളവും ഭക്ഷണവും ആവശ്യമുണ്ട്.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " ലേക്ക് അടിയന്തര മെഡിക്കൽ സഹായം / ആംബുലൻസ് അയക്കുക.";
        else oss << "മെഡിക്കൽ സഹായം അയക്കുക.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "ഞങ്ങളുടെ സംഘം സജ്ജമാണ്, " << loc << " ലേക്ക് നീങ്ങുന്നു.";
        else oss << "ഞങ്ങളുടെ സംഘം സജ്ജമാണ്.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "തീപിടുത്ത മുന്നറിയിപ്പ്!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "വെള്ളപ്പൊക്ക മുന്നറിയിപ്പ്!";
        else oss << "ജാഗ്രതാ മുന്നറിയിപ്പ്!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "സ്ഥാന റിപ്പോർട്ട്: " << loc << ".";
        else oss << "സ്ഥാന വിവരം ലഭിച്ചു.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " ലേക്ക് പോകുക.";
        else oss << "ലക്ഷ്യസ്ഥാനത്തേക്ക് പോകുക.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "സ്ഥാനം: " << loc << ".";
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeTamil(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[அவசர செய்தி]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "ta");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " பகுதியிலிருந்து வெளியேற வேண்டாம்.";
            else oss << "வெளியேற வேண்டாம்.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " பகுதிக்கு ஆம்புலன்ஸ் / மருத்துவ உதவி தேவையில்லை.";
            else oss << "மருத்துவ உதவி தேவையில்லை.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " பகுதிக்கு மீட்பு உதவி தேவையில்லை.";
            else oss << "உதவி தேவையில்லை.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " பகுதிக்கு உதவி தேவையில்லை.";
        else oss << "உதவி தேவையில்லை.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " அருகில் " << res.personCount << " பேர் சிக்கியுள்ளனர். உடனடியாக மீட்புக் குழுவை அனுப்பவும்.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "உதவி, வெள்ளம் வந்துள்ளது";
            if (!loc.empty()) oss << " " << loc << " பகுதியில்";
            oss << ". உடனடியாக மீட்புக் குழுவை அனுப்பவும்.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "தீ விபத்து ஏற்பட்டுள்ளது";
            if (!loc.empty()) oss << " " << loc << " பகுதியில்";
            oss << ". உடனடியாக மீட்புக் குழுவை அனுப்பவும்.";
        } else {
            if (!loc.empty()) oss << loc << " பகுதியில் உடனடியாக உதவி தேவை.";
            else oss << "உடனடியாக உதவி தேவை.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " பகுதியிலிருந்து உடனடியாக வெளியேறவும்.";
        else oss << "உடனடியாக வெளியேறவும்.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " பகுதிக்கு குடிநீர் மற்றும் உணவு விநியோகம் அனுப்பவும்.";
        else oss << "குடிநீர் மற்றும் உணவு தேவை.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " பகுதிக்கு மருத்துவ உதவி / ஆம்புலன்ஸ் அனுப்பவும்.";
        else oss << "மருத்துவ உதவி தேவை.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "எங்கள் குழு தயாராக உள்ளது, " << loc << " நோக்கி செல்கிறது.";
        else oss << "எங்கள் குழு தயாராக உள்ளது.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "தீ விபத்து எச்சரிக்கை!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "வெள்ள எச்சரிக்கை!";
        else oss << "எச்சரிக்கை!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "இடத் தகவல்: " << loc << ".";
        else oss << "இடத் தகவல் கிடைத்தது.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " நோக்கி செல்லவும்.";
        else oss << "இலக்கிற்குச் செல்லவும்.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "இடம்: " << loc << ".";
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeTelugu(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[అత్యవసర సందేశం]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "te");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " ప్రాంతాన్ని ఖాళీ చేయవద్దు.";
            else oss << "ఖాళీ చేయవద్దు.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " కు అంబులెన్స్ / వైద్య సహాయం అవసరం లేదు.";
            else oss << "వైద్య సహాయం అవసరం లేదు.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " వద్ద రక్షణ సహాయం అవసరం లేదు.";
            else oss << "సహాయం అవసరం లేదు.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " వద్ద సహాయం అవసరం లేదు.";
        else oss << "సహాయం అవసరం లేదు.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " వద్ద " << res.personCount << " మంది చిక్కుకున్నారు. వెంటనే రక్షణ బృందాన్ని పంపండి.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "సహాయం, వరదలు వచ్చాయి";
            if (!loc.empty()) oss << " " << loc << " వద్ద";
            oss << ". వెంటనే రక్షణ బృందాన్ని పంపండి.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "అగ్ని ప్రమాదం జరిగింది";
            if (!loc.empty()) oss << " " << loc << " వద్ద";
            oss << ". వెంటనే ఫైర్ బ్రిగేడ్ పంపండి.";
        } else {
            if (!loc.empty()) oss << loc << " వద్ద వెంటనే సహాయం పంపండి.";
            else oss << "వెంటనే సహాయం పంపండి.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " ప్రాంతాన్ని వెంటనే ఖాళీ చేయండి.";
        else oss << "వెంటనే ఖాళీ చేయండి.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " కు నీరు మరియు ఆహార సరఫరాలు పంపండి.";
        else oss << "నీరు మరియు ఆహార సహాయం కావాలి.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " కు వైద్య సహాయం / అంబులెన్స్ పంపండి.";
        else oss << "వైద్య సహాయం పంపండి.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "మా బృందం సిద్ధంగా ఉంది మరియు " << loc << " వైపు వెళుతోంది.";
        else oss << "మా బృందం సిద్ధంగా ఉంది.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "అగ్నిప్రమాద హెచ్చరిక!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "వరద హెచ్చరిక!";
        else oss << "హెచ్చరిక!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "స్థాన సమాచారం: " << loc << ".";
        else oss << "స్థాన సమాచారం వచ్చింది.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " వైపు వెళ్లండి.";
        else oss << "గమ్యస్థానానికి వెళ్లండి.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "స్థానం: " << loc << ".";
        return oss.str();
    }

    return realizeEnglish(res);
}

std::string TranslationBridge::realizeOdia(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[ଜରୁରୀକାଳୀନ ସନ୍ଦେଶ]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "or");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " ଖାଲି କରନ୍ତୁ ନାହିଁ।";
            else oss << "ସ୍ଥାନ ଖାଲି କରନ୍ତୁ ନାହିଁ।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " ପାଇଁ ଆମ୍ବୁଲାନ୍ସ / ଡାକ୍ତରୀ ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
            else oss << "ଡାକ୍ତରୀ ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " ପାଇଁ ଉଦ୍ଧାର ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
            else oss << "ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " ପାଇଁ କୌଣସି ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
        else oss << "ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " ପାଖରେ " << res.personCount << " ଲୋକ ଫସି ରହିଛନ୍ତି। ତୁରନ୍ତ ଉଦ୍ଧାରକାରୀ ଦଳ ପଠାନ୍ତୁ।";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "ସାହାଯ୍ୟ କରନ୍ତୁ, ବନ୍ୟା ଆସିଛି";
            if (!loc.empty()) oss << " " << loc << " ରେ";
            oss << "। ତୁରନ୍ତ ଉଦ୍ଧାରକାରୀ ଦଳ ପଠାନ୍ତୁ।";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "ନିଆଁ ଲାଗିଛି";
            if (!loc.empty()) oss << " " << loc << " ରେ";
            oss << "। ତୁରନ୍ତ ସହାୟତା ପଠାନ୍ତୁ।";
        } else {
            if (!loc.empty()) oss << loc << " ରେ ତୁରନ୍ତ ଉଦ୍ଧାର ସହାୟତା ପଠାନ୍ତୁ।";
            else oss << "ତୁରନ୍ତ ଉଦ୍ଧାର ସହାୟତା ପଠାନ୍ତୁ।";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " କୁ ତୁରନ୍ତ ଖାଲି କରନ୍ତୁ।";
        else oss << "ସ୍ଥାନକୁ ତୁରନ୍ତ ଖାଲି କରନ୍ତୁ।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " କୁ ଜଳ ଏବଂ ଖାଦ୍ୟ ସାହାଯ୍ୟ ପଠାନ୍ତୁ।";
        else oss << "ଜଳ ଏବଂ ଖାଦ୍ୟ ସାହାଯ୍ୟ ଆବଶ୍ୟକ।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " କୁ ଡାକ୍ତରୀ ସହାୟତା / ଆମ୍ବୁଲାନ୍ସ ପଠାନ୍ତୁ।";
        else oss << "ଡାକ୍ତରୀ ସହାୟତା ପଠାନ୍ତୁ।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "ଆମର ଦଳ ପ୍ରସ୍ତୁତ ଅଛି ଏବଂ " << loc << " ଆଡକୁ ଯାଉଛି।";
        else oss << "ଆମର ଦଳ ପ୍ରସ୍ତୁତ ଅଛି।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "ଅଗ୍ନି ବିପଦ ଚେତାବନୀ!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "ବନ୍ୟା ବିପଦ ଚେତାବନୀ!";
        else oss << "ଚେତାବନୀ!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "ସ୍ଥାନ ସୂଚନା: " << loc << ".";
        else oss << "ସ୍ଥାନ ସୂଚନା ମିଳିଛି।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " କୁ ଯାଆନ୍ତୁ।";
        else oss << "ଲକ୍ଷ୍ୟସ୍ଥାନକୁ ଯାଆନ୍ତୁ।";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "ସ୍ଥାନ: " << loc << ".";
        return oss.str();
    }

    return realizeHindi(res);
}

std::string TranslationBridge::realizeBengali(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[জরুরি বার্তা]" : res.originalText;

    std::string loc = getTargetLocationName(res.location.geoId, "bn");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " এলাকা খালি করবেন না।";
            else oss << "এলাকা খালি করবেন না।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " এ অ্যাম্বুলেন্স / চিকিৎসা সহায়তার প্রয়োজন নেই।";
            else oss << "চিকিৎসা সহায়তার প্রয়োজন নেই।";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " এ উদ্ধারকারী দলের প্রয়োজন নেই।";
            else oss << "সহায়তার প্রয়োজন নেই।";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " এ কোন সাহায্যের প্রয়োজন নেই।";
        else oss << "সাহায্যের প্রয়োজন নেই।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " এর কাছে " << res.personCount << " জন মানুষ আটকা পড়েছেন। অবিলম্বে উদ্ধারকারী দল পাঠান।";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "সাহায্য করুন, বন্যা হয়েছে";
            if (!loc.empty()) oss << " " << loc << " এ";
            oss << "। অবিলম্বে উদ্ধারকারী দল পাঠান।";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "আগুন লেগেছে";
            if (!loc.empty()) oss << " " << loc << " এ";
            oss << "। অবিলম্বে উদ্ধারকারী দল পাঠান।";
        } else {
            if (!loc.empty()) oss << loc << " এ অবিলম্বে উদ্ধার সহায়তা পাঠান।";
            else oss << "অবিলম্বে উদ্ধার সহায়তা পাঠান।";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " অবিলম্বে খালি করুন।";
        else oss << "এলাকা অবিলম্বে খালি করুন।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " এ জল এবং খাদ্য সরবরাহ পাঠান।";
        else oss << "জল এবং খাদ্য সাহায্য প্রয়োজন।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " এ চিকিৎসা সহায়তা / অ্যাম্বুলেন্স পাঠান।";
        else oss << "চিকিৎসা সহায়তা পাঠান।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "আমাদের দল প্রস্তুত এবং " << loc << " এর দিকে অগ্রসর হচ্ছে।";
        else oss << "আমাদের দল প্রস্তুত।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "অগ্নিকাণ্ডের সতর্কতা!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "বন্যা সতর্কতা!";
        else oss << "সতর্কতা!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "স্থানের খবর: " << loc << ".";
        else oss << "স্থানের তথ্য পেয়েছি।";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " এ যান।";
        else oss << "গন্তব্যে যান।";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "স্থান: " << loc << ".";
        return oss.str();
    }

    return realizeHindi(res);
}

std::string TranslationBridge::realizePunjabi(const semantic::SemanticResult& res) {
    if (res.isFallback) return res.originalText.empty() ? "[ਆਪਤਕਾਲੀਨ ਸੰਦੇਸ਼]" : res.originalText;

    // No "pa" branch in getTargetLocationName — proper nouns fall through to
    // geoIdToString (Latin script), which Punjabi readers handle fine.
    std::string loc = getTargetLocationName(res.location.geoId, "pa");
    std::ostringstream oss;

    if (res.isNegated && res.isStrongNegation) {
        if (res.intent == semantic::ActionCode::EVACUATE) {
            if (!loc.empty()) oss << loc << " ਖਾਲੀ ਨਾ ਕਰੋ.";
            else oss << "ਇਲਾਕਾ ਖਾਲੀ ਨਾ ਕਰੋ.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::MEDICAL) {
            if (!loc.empty()) oss << loc << " ਵਿੱਚ ਐਂਬੂਲੈਂਸ / ਮੈਡੀਕਲ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
            else oss << "ਮੈਡੀਕਲ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
            return oss.str();
        }
        if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
            if (!loc.empty()) oss << loc << " ਵਿੱਚ ਬਚਾਅ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
            else oss << "ਬਚਾਅ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
            return oss.str();
        }
        if (!loc.empty()) oss << loc << " ਵਿੱਚ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
        else oss << "ਕਿਸੇ ਮਦਦ ਦੀ ਲੋੜ ਨਹੀਂ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::RESCUE_REQUEST || res.intent == semantic::ActionCode::REQUEST_HELP) {
        if (res.personCount > 0 && !loc.empty()) {
            oss << loc << " ਕੋਲ " << res.personCount << " ਲੋਕ ਫਸੇ ਹਨ. ਤੁਰੰਤ ਬਚਾਅ ਟੀਮ ਭੇਜੋ.";
        } else if (res.hazard == semantic::HazardCode::FLOOD) {
            oss << "ਮਦਦ ਕਰੋ, ਬਾੜੀ ਆ ਗਈ ਹੈ";
            if (!loc.empty()) oss << " " << loc;
            oss << ". ਤੁਰੰਤ ਬਚਾਅ ਟੀਮ ਭੇਜੋ.";
        } else if (res.hazard == semantic::HazardCode::FIRE) {
            oss << "ਅੱਗ ਲੱਗੀ ਹੈ";
            if (!loc.empty()) oss << " " << loc;
            oss << ". ਤੁਰੰਤ ਫਾਇਰ ਬ੍ਰਿਗੇਡ ਭੇਜੋ.";
        } else {
            if (!loc.empty()) oss << loc << " ਵਿੱਚ ਤੁਰੰਤ ਬਚਾਅ ਮਦਦ ਭੇਜੋ.";
            else oss << "ਤੁਰੰਤ ਬਚਾਅ ਮਦਦ ਭੇਜੋ.";
        }
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::EVACUATE) {
        if (!loc.empty()) oss << loc << " ਤੁਰੰਤ ਖਾਲੀ ਕਰੋ.";
        else oss << "ਇਲਾਕਾ ਤੁਰੰਤ ਖਾਲੀ ਕਰੋ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SUPPLIES) {
        if (!loc.empty()) oss << loc << " ਨੂੰ ਪਾਣੀ ਅਤੇ ਰਾਸ਼ਨ ਭੇਜੋ.";
        else oss << "ਪਾਣੀ ਅਤੇ ਰਾਸ਼ਨ ਦੀ ਲੋੜ ਹੈ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::MEDICAL) {
        if (!loc.empty()) oss << loc << " ਲਈ ਡਾਕਟਰੀ ਮਦਦ / ਐਂਬੂਲੈਂਸ ਭੇਜੋ.";
        else oss << "ਡਾਕਟਰੀ ਮਦਦ ਭੇਜੋ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::SEND_TEAM) {
        if (!loc.empty()) oss << "ਸਾਡੀ ਟੀਮ ਤਿਆਰ ਹੈ ਅਤੇ " << loc << " ਵੱਲ ਵਧ ਰਹੀ ਹੈ.";
        else oss << "ਸਾਡੀ ਟੀਮ ਤਿਆਰ ਹੈ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::ALERT) {
        if (res.hazard == semantic::HazardCode::FIRE) oss << "ਅੱਗ ਦੀ ਚੇਤਾਵਨੀ!";
        else if (res.hazard == semantic::HazardCode::FLOOD) oss << "ਬਾੜੀ ਦੀ ਚੇਤਾਵਨੀ!";
        else oss << "ਚੇਤਾਵਨੀ ਜਾਰੀ!";
        if (!loc.empty()) oss << " (" << loc << ")";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::LOCATION_REPORT) {
        if (!loc.empty()) oss << "ਸਥਾਨ ਦੀ ਜਾਣਕਾਰੀ: " << loc << ".";
        else oss << "ਸਥਾਨ ਦੀ ਜਾਣਕਾਰੀ ਮਿਲੀ.";
        return oss.str();
    }

    if (res.intent == semantic::ActionCode::GO_TO) {
        if (!loc.empty()) oss << loc << " ਤੇ ਜਾਓ.";
        else oss << "ਮੰਜ਼ਿਲ ਤੇ ਜਾਓ.";
        return oss.str();
    }

    if (!loc.empty()) {
        oss << "ਸਥਾਨ: " << loc << ".";
        return oss.str();
    }

    return res.originalText.empty() ? "[ਆਪਤਕਾਲੀਨ ਸੰਦੇਸ਼]" : res.originalText;
}

std::string TranslationBridge::realize(const semantic::SemanticResult& result, const std::string& targetLanguage) {
    if (targetLanguage == "hi") return realizeHindi(result);
    if (targetLanguage == "gu") return realizeGujarati(result);
    if (targetLanguage == "mr") return realizeMarathi(result);
    if (targetLanguage == "kn") return realizeKannada(result);
    if (targetLanguage == "ml") return realizeMalayalam(result);
    if (targetLanguage == "ta") return realizeTamil(result);
    if (targetLanguage == "te") return realizeTelugu(result);
    if (targetLanguage == "or") return realizeOdia(result);
    if (targetLanguage == "bn") return realizeBengali(result);
    if (targetLanguage == "pa") return realizePunjabi(result);
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
