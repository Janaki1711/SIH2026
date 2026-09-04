"""
translation_engine.py — Offline Indic Translation & Semantic Realization Bridge

Supports multilingual realization across Hindi, Tamil, Kannada, Marathi, Telugu, English.
"""

from typing import Dict, Any, Optional
from semantic_codebook import ActionCode, UrgencyCode, HazardCode, GeoID
from tinyml_agent import SemanticResult

SUPPORTED_LANGUAGES = ["hi", "en", "mr", "ta", "te", "kn"]
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "en": "English",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
}

def get_target_location_name(geo_id: int, lang: str) -> str:
    if geo_id == GeoID.UNKNOWN:
        return ""
    if lang in ("hi", "mr"):
        mapping = {
            GeoID.TOLANKERE: "तोलनकेरे",
            GeoID.HUBBLI: "हब्बली",
            GeoID.BASE: "बेस कैंप",
            GeoID.SECTOR_1: "सेक्टर 1",
            GeoID.SECTOR_2: "सेक्टर 2",
            GeoID.SECTOR_3: "सेक्टर 3",
            GeoID.SECTOR_4: "सेक्टर 4",
            GeoID.SECTOR_5: "सेक्टर 5",
            GeoID.BRIDGE: "पुल",
            GeoID.HOSPITAL: "अस्पताल",
            GeoID.SCHOOL: "स्कूल",
        }
    elif lang == "ta":
        mapping = {
            GeoID.TOLANKERE: "தோலன்கெரே",
            GeoID.HUBBLI: "ஹூப்ளி",
            GeoID.BASE: "முகாம்",
            GeoID.SECTOR_4: "செக்டர் 4",
            GeoID.BRIDGE: "பாலம்",
            GeoID.HOSPITAL: "மருத்துவமனை",
            GeoID.SCHOOL: "பள்ளி",
        }
    elif lang == "kn":
        mapping = {
            GeoID.TOLANKERE: "ತೊಳನಕೆರೆ",
            GeoID.HUBBLI: "ಹುಬ್ಬಳ್ಳಿ",
            GeoID.BASE: "ಬೇಸ್ ಕ್ಯಾಂಪ್",
            GeoID.SECTOR_4: "ಸೆಕ್ಟರ್ 4",
            GeoID.BRIDGE: "ಸೇತುವೆ",
            GeoID.HOSPITAL: "ಆಸ್ಪತ್ರೆ",
            GeoID.SCHOOL: "ಶಾಲೆ",
        }
    elif lang == "te":
        mapping = {
            GeoID.TOLANKERE: "తోలంకెరె",
            GeoID.HUBBLI: "హుబ్లి",
            GeoID.BASE: "బేస్ క్యాంప్",
            GeoID.SECTOR_4: "సెక్టర్ 4",
            GeoID.BRIDGE: "వంతెన",
            GeoID.HOSPITAL: "ఆసుపత్రి",
            GeoID.SCHOOL: "పాఠశాల",
        }
    else:
        mapping = {
            GeoID.TOLANKERE: "Tolankere",
            GeoID.HUBBLI: "Hubbli",
            GeoID.BASE: "Base Camp",
            GeoID.SECTOR_1: "Sector 1",
            GeoID.SECTOR_2: "Sector 2",
            GeoID.SECTOR_3: "Sector 3",
            GeoID.SECTOR_4: "Sector 4",
            GeoID.SECTOR_5: "Sector 5",
            GeoID.BRIDGE: "Bridge",
            GeoID.HOSPITAL: "Hospital",
            GeoID.SCHOOL: "School",
        }
    return mapping.get(geo_id, "Location")


def realize(res: SemanticResult, target_lang: str = "en") -> str:
    if res.is_fallback:
        return res.original_text if res.original_text else "[Fallback message]"

    loc = res.location.canonical_name if res.location else ""
    gid = res.location.geo_id if res.location else GeoID.UNKNOWN

    if target_lang == "hi":
        loc_hi = get_target_location_name(gid, "hi")
        if res.intent == ActionCode.RESCUE_REQUEST:
            if res.person_count > 0 and loc_hi:
                haz_str = " बाढ़ के कारण" if res.hazard == HazardCode.FLOOD else ""
                return f"{loc_hi} के पास {res.person_count} लोग फंसे हुए हैं{haz_str}। तुरंत बचाव दल भेजो।"
            elif res.hazard == HazardCode.FLOOD:
                loc_part = f" {loc_hi} में" if loc_hi else ""
                return f"मदद, बाढ़ आ गई है{loc_part}। तुरंत सहायता भेजो।"
            elif res.hazard == HazardCode.FIRE:
                loc_part = f" {loc_hi} में" if loc_hi else ""
                return f"आग लग गई है{loc_part}। तुरंत फायर ब्रिगेड भेजो।"
            else:
                return f"{loc_hi} में तुरंत मदद भेजो।" if loc_hi else "तुरंत बचाव सहायता भेजो।"
        elif res.intent == ActionCode.EVACUATE:
            return f"{loc_hi} को तुरंत खाली करो।" if loc_hi else "क्षेत्र को तुरंत खाली करो।"
        elif res.intent == ActionCode.MEDICAL:
            return f"{loc_hi} में चिकित्सा दल की आवश्यकता है।" if loc_hi else "तुरंत चिकित्सा सहायता भेजो।"

    elif target_lang == "ta":
        loc_ta = get_target_location_name(gid, "ta")
        if res.intent == ActionCode.RESCUE_REQUEST:
            if res.person_count > 0 and loc_ta:
                return f"{loc_ta} அருகில் {res.person_count} பேர் சிக்கியுள்ளனர். உடனடியாக மீட்புக் குழுவை அனுப்பவும்."
            elif res.hazard == HazardCode.FLOOD:
                return "உதவி, வெள்ளம் வந்துள்ளது. உடனடியாக மீட்புக் குழுவை அனுப்பவும்."
            else:
                return "உடனடியாக உதவி தேவை."

    elif target_lang == "kn":
        loc_kn = get_target_location_name(gid, "kn")
        if res.intent == ActionCode.RESCUE_REQUEST:
            if res.person_count > 0 and loc_kn:
                return f"{loc_kn} ಹತ್ತಿರ {res.person_count} ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದಾರೆ. ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ."
            elif res.hazard == HazardCode.FLOOD:
                return "ಸಹಾಯ ಮಾಡಿ, ಪ್ರವಾಹ ಬಂದಿದೆ. ತಕ್ಷಣ ರಕ್ಷಣಾ ತಂಡವನ್ನು ಕಳುಹಿಸಿ."
            else:
                return "ತಕ್ಷಣ ರಕ್ಷಣಾ ಸಹಾಯ ಕಳುಹಿಸಿ."

    elif target_lang == "mr":
        loc_mr = get_target_location_name(gid, "mr")
        if res.intent == ActionCode.RESCUE_REQUEST:
            if res.person_count > 0 and loc_mr:
                return f"{loc_mr} जवळ {res.person_count} लोक अडकले आहेत. तातडीने बचाव पथक पाठवा."
            elif res.hazard == HazardCode.FLOOD:
                return "मदत करा, पूर आला आहे. तातडीने मदत पाठवा."
            else:
                return "तातडीने मदत पाठवा."

    elif target_lang == "te":
        loc_te = get_target_location_name(gid, "te")
        if res.intent == ActionCode.RESCUE_REQUEST:
            if res.person_count > 0 and loc_te:
                return f"{loc_te} వద్ద {res.person_count} మంది చిక్కుకున్నారు. వెంటనే రక్షణ బృందాన్ని పంపండి."
            elif res.hazard == HazardCode.FLOOD:
                return "సహాయం, వరదలు వచ్చాయి. వెంటనే రక్షణ బృందాన్ని పంపండి."
            else:
                return "వెంటనే సహాయం పంపండి."

    # English realization default
    if res.intent == ActionCode.RESCUE_REQUEST:
        if res.person_count > 0 and loc:
            haz_str = " due to flooding" if res.hazard == HazardCode.FLOOD else (" due to fire" if res.hazard == HazardCode.FIRE else "")
            return f"{res.person_count} people are trapped near {loc}{haz_str}. Send rescue team immediately."
        elif res.person_count > 0:
            return f"{res.person_count} people trapped. Requesting rescue assistance."
        elif res.hazard == HazardCode.FLOOD:
            loc_str = f" at {loc}" if loc else ""
            return f"Help, there is a flood{loc_str}."
        elif res.hazard == HazardCode.FIRE:
            loc_str = f" at {loc}" if loc else ""
            return f"Help, there is a fire{loc_str}."
        else:
            loc_str = f" at {loc}" if loc else ""
            return f"Rescue assistance requested{loc_str}."
    elif res.intent == ActionCode.EVACUATE:
        loc_str = f" from {loc}" if loc else ""
        return f"Evacuate immediately{loc_str}."
    elif res.intent == ActionCode.MEDICAL:
        loc_str = f" at {loc}" if loc else ""
        return f"Medical assistance required{loc_str}."

    if loc:
        return f"{res.action.name} at {loc}."
    return res.original_text if res.original_text else "Emergency message received."


def translate(text: str, source_lang: str, target_lang: str) -> str:
    """Offline translation realization fallback."""
    if source_lang == target_lang:
        return text
    return text
