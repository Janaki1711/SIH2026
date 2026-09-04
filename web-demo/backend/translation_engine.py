"""
translation_engine.py — Offline Indic Translation & Semantic Realization Bridge
Supports all 10 official Indian Languages required by the ISRO Problem Statement:
  - English (en)
  - Hindi (hi)
  - Gujarati (gu)
  - Marathi (mr)
  - Kannada (kn)
  - Malayalam (ml)
  - Tamil (ta)
  - Telugu (te)
  - Odia (or)
  - Bengali (bn)
"""

from typing import Dict, Any, Optional

SUPPORTED_LANGUAGES = ["en", "hi", "gu", "mr", "kn", "ml", "ta", "te", "or", "bn"]
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
    "mr": "Marathi",
    "kn": "Kannada",
    "ml": "Malayalam",
    "ta": "Tamil",
    "te": "Telugu",
    "or": "Odia",
    "bn": "Bengali",
}

def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code.lower(), code)

def _extract_field_val(field_obj: Any) -> str:
    """Safely extracts the semantic value string from SemanticField, Enum, or string."""
    if field_obj is None:
        return ""
    if hasattr(field_obj, 'canonical_name'):
        return str(field_obj.canonical_name).upper()
    if hasattr(field_obj, 'value') and hasattr(field_obj, 'code'):
        return str(field_obj.value).upper()
    if hasattr(field_obj, 'name'):
        return str(field_obj.name).upper()
    if hasattr(field_obj, 'value'):
        return str(field_obj.value).upper()
    return str(field_obj).upper()

def realize(msg_or_result: Any, target_language: str) -> str:
    """
    Main entry point: Realizes a semantic object into the target language.
    Accepts either a SemanticMessage (v1/v2) or SemanticResult (v3).
    """
    lang = target_language.lower()
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"

    is_fallback = getattr(msg_or_result, 'is_fallback', False)
    tier = getattr(msg_or_result, 'compression_tier', None)
    if tier and hasattr(tier, 'name') and 'FALLBACK' in tier.name:
        is_fallback = True

    if is_fallback:
        orig = getattr(msg_or_result, 'original_text', '') or getattr(msg_or_result, 'fallback_text', '')
        if orig:
            return orig

    # Extract semantic values cleanly
    action = _extract_field_val(getattr(msg_or_result, 'action', ''))
    entity = _extract_field_val(getattr(msg_or_result, 'entity', ''))
    
    # Target / Location extraction
    target = _extract_field_val(getattr(msg_or_result, 'target', ''))
    loc_obj = getattr(msg_or_result, 'location', None)
    loc_text = ""
    if loc_obj:
        if hasattr(loc_obj, 'canonical_name'):
            if not target or target == "UNKNOWN":
                target = loc_obj.canonical_name.upper()
            loc_text = loc_obj.canonical_name
        elif isinstance(loc_obj, str) and not loc_obj.startswith("LocationEntity"):
            loc_text = loc_obj
            if not target: target = loc_obj.upper()

    hazard_text = getattr(msg_or_result, 'hazard', '') or getattr(msg_or_result, 'hazard_text', '')
    if hasattr(hazard_text, 'name'): hazard_text = hazard_text.name
    hazard_str = str(hazard_text).replace("_", " ").lower() if hazard_text else ""

    qty = getattr(msg_or_result, 'person_count', 0) or getattr(msg_or_result, 'quantity', 0)
    if hasattr(qty, 'value'): qty = qty.value
    qty_str = str(qty) if qty and int(qty) > 0 else ""

    # Dispatch to language-specific realizer
    realizers = {
        "en": _realize_en, "hi": _realize_hi, "gu": _realize_gu,
        "mr": _realize_mr, "kn": _realize_kn, "ml": _realize_ml,
        "ta": _realize_ta, "te": _realize_te, "or": _realize_or,
        "bn": _realize_bn
    }
    return realizers[lang](action, entity, target, loc_text, hazard_str, qty_str)


# ==============================================================================
# 1. ENGLISH (en)
# ==============================================================================
def _realize_en(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "Hubbli", "TOLANKERE": "Tolankere", "BASE": "Base HQ", "SECTOR_4": "Sector 4", "HOSPITAL": "the hospital"}
    ENTITIES = {"RESCUE": "rescue team", "RESCUE_REQUEST": "rescue team", "MEDICAL": "medical team", "AMBULANCE": "ambulance", "FIRE": "fire brigade", "FIRE_TEAM": "firefighters"}
    l_str = LOCS.get(target, loc_text or (target.replace("_", " ").title() if target else ""))
    e_str = ENTITIES.get(entity, entity.replace("_", " ").lower() if entity else "team")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f" to {l_str}" if l_str else ""
        return f"Send {q}{e_str}{t} immediately."
    elif "HELP" in action or "REQUEST" in action:
        return f"Urgent {e_str} assistance requested at {l_str}." if l_str else "Assistance requested immediately."
    elif "EVACUATE" in action:
        return f"Evacuate {l_str or 'the area'} immediately."
    elif "ALERT" in action:
        return f"ALERT: {hazard or 'Emergency'} reported at {l_str}."
    return f"Status update for {l_str or 'current location'}."


# ==============================================================================
# 2. HINDI (hi)
# ==============================================================================
def _realize_hi(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "हब्बली", "TOLANKERE": "तोलनकेरे", "BASE": "बेस", "SECTOR_4": "सेक्टर 4", "HOSPITAL": "अस्पताल"}
    ENTITIES = {"RESCUE": "बचाव दल", "RESCUE_REQUEST": "बचाव दल", "MEDICAL": "चिकित्सा दल", "AMBULANCE": "एम्बुलेंस", "FIRE": "दमकल", "FIRE_TEAM": "अग्निशमन दल"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "दल")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} में " if l_str else ""
        return f"तुरंत {t}{q}{e_str} भेजो।"
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} पर तुरंत सहायता की आवश्यकता है।" if l_str else "तुरंत सहायता की आवश्यकता है।"
    elif "EVACUATE" in action:
        return f"{l_str or 'इलाके'} को तुरंत खाली कराएं।"
    elif "ALERT" in action:
        return f"चेतावनी: {l_str} में {hazard or 'खतरा'}।"
    return f"{l_str or 'क्षेत्र'} की स्थिति रिपोर्ट।"


# ==============================================================================
# 3. GUJARATI (gu)
# ==============================================================================
def _realize_gu(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "હબ્બલી", "TOLANKERE": "તોલનકેરે", "BASE": "બેઝ", "SECTOR_4": "સેક્ટર 4", "HOSPITAL": "હોસ્પિટલ"}
    ENTITIES = {"RESCUE": "બચાવ ટીમ", "RESCUE_REQUEST": "બચાવ ટીમ", "MEDICAL": "તબીબી ટીમ", "AMBULANCE": "એમ્બ્યુલન્સ", "FIRE": "ફાયર બ્રિગેડ", "FIRE_TEAM": "અગ્નિશામક દળ"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "ટીમ")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} ખાતે " if l_str else ""
        return f"તરત જ {t}{q}{e_str} મોકલો."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} ખાતે તાત્કાલિક મદદની જરૂર છે." if l_str else "તાત્કાલિક મદદની જરૂર છે."
    elif "EVACUATE" in action:
        return f"{l_str or 'વિસ્તાર'} તાત્કાલિક ખાલી કરો."
    elif "ALERT" in action:
        return f"ચેતવણી: {l_str} ખાતે {hazard or 'જોખમ'}."
    return f"{l_str or 'વિસ્તાર'}નો સ્થિતિ અહેવાલ."


# ==============================================================================
# 4. MARATHI (mr)
# ==============================================================================
def _realize_mr(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "हब्बली", "TOLANKERE": "तोलनकेरे", "BASE": "तळ", "SECTOR_4": "सेक्टर 4", "HOSPITAL": "रुग्णालय"}
    ENTITIES = {"RESCUE": "बचाव पथक", "RESCUE_REQUEST": "बचाव पथक", "MEDICAL": "वैद्यकीय पथक", "AMBULANCE": "रुग्णवाहिका", "FIRE": "अग्निशामक दल", "FIRE_TEAM": "अग्निशामक पथक"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "पथक")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} येथे " if l_str else ""
        return f"तातडीने {t}{q}{e_str} पाठवा."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} येथे तातडीच्या मदतीची आवश्यकता आहे." if l_str else "तातडीच्या मदतीची गरज आहे."
    elif "EVACUATE" in action:
        return f"{l_str or 'परिसर'} त्वरित रिकामे करा."
    elif "ALERT" in action:
        return f"इशारा: {l_str} येथे {hazard or 'धोका'}."
    return f"{l_str or 'भागाची'} परिस्थिती माहिती."


# ==============================================================================
# 5. KANNADA (kn)
# ==============================================================================
def _realize_kn(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "ಹುಬ್ಬಳ್ಳಿಗೆ", "TOLANKERE": "ತೋಲನಕೆರೆಗೆ", "BASE": "ನೆಲೆಗೆ", "SECTOR_4": "ಸೆಕ್ಟರ್ 4 ಕ್ಕೆ", "HOSPITAL": "ಆಸ್ಪತ್ರೆಗೆ"}
    ENTITIES = {"RESCUE": "ರಕ್ಷಣಾ ತಂಡ", "RESCUE_REQUEST": "ರಕ್ಷಣಾ ತಂಡ", "MEDICAL": "ವೈದ್ಯಕೀಯ ತಂಡ", "AMBULANCE": "ಆಂಬ್ಯುಲೆನ್ಸ್", "FIRE": "ಅಗ್ನಿಶಾಮಕ ದಳ", "FIRE_TEAM": "ಅಗ್ನಿಶಾಮಕ ಸಿಬ್ಬಂದಿ"}
    l_str = LOCS.get(target, (loc_text + "ಗೆ") if loc_text else (target + "ಗೆ" if target else ""))
    e_str = ENTITIES.get(entity, "ತಂಡ")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"ತಕ್ಷಣ {t}{q}{e_str} ಕಳುಹಿಸಿ."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} ತಕ್ಷಣದ ಸಹಾಯ ಬೇಕಾಗಿದೆ." if l_str else "ತುರ್ತು ಸಹಾಯ ಬೇಕಾಗಿದೆ."
    elif "EVACUATE" in action:
        return f"{l_str or 'ಪ್ರದೇಶವನ್ನು'} ತಕ್ಷಣ ಖಾಲಿ ಮಾಡಿ."
    elif "ALERT" in action:
        return f"ಎಚ್ಚರಿಕೆ: {l_str} {hazard or 'ಅಪಾಯ'}."
    return f"{l_str or 'ಪ್ರದೇಶದ'} ಪರಿಸ್ಥಿತಿ ವರದಿ."


# ==============================================================================
# 6. MALAYALAM (ml)
# ==============================================================================
def _realize_ml(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "ഹുബ്ലിയിലേക്ക്", "TOLANKERE": "തോളങ്കരെയിലേക്ക്", "BASE": "ബേസിലേക്ക്", "SECTOR_4": "സെക്ടർ 4 ലേക്ക്", "HOSPITAL": "ആശുപത്രിയിലേക്ക്"}
    ENTITIES = {"RESCUE": "രക്ഷാപ്രവർത്തക സംഘത്തെ", "RESCUE_REQUEST": "രക്ഷാപ്രവർത്തക സംഘത്തെ", "MEDICAL": "മെഡിക്കൽ സംഘത്തെ", "AMBULANCE": "ആംബുലൻസ്", "FIRE": "ഫയർ ഫോഴ്സിനെ", "FIRE_TEAM": "അഗ്നിശമന സേനയെ"}
    l_str = LOCS.get(target, (loc_text + "ലേക്ക്") if loc_text else (target + "ലേക്ക്" if target else ""))
    e_str = ENTITIES.get(entity, "സംഘത്തെ")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"ഉടൻ തന്നെ {t}{q}{e_str} അയക്കുക."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} അടിയന്തര സഹായം ആവശ്യമാണ്." if l_str else "അടിയന്തര സഹായം ആവശ്യമാണ്."
    elif "EVACUATE" in action:
        return f"{l_str or 'പ്രദേശം'} ഉടൻ ഒഴിപ്പിക്കുക."
    elif "ALERT" in action:
        return f"മുന്നറിയിപ്പ്: {l_str} {hazard or 'അപകടം'}."
    return f"{l_str or 'സ്ഥലത്തെ'} വിവരങ്ങൾ."


# ==============================================================================
# 7. TAMIL (ta)
# ==============================================================================
def _realize_ta(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "ஹூப்ளிக்கு", "TOLANKERE": "தோலன்கெரேவுக்கு", "BASE": "முகாமிற்கு", "SECTOR_4": "பகுதி 4-க்கு", "HOSPITAL": "மருத்துவமனைக்கு"}
    ENTITIES = {"RESCUE": "மீட்புக் குழுவை", "RESCUE_REQUEST": "மீட்புக் குழுவை", "MEDICAL": "மருத்துவக் குழுவை", "AMBULANCE": "ஆம்புலன்ஸை", "FIRE": "தீயணைப்புப் படையை", "FIRE_TEAM": "தீயணைப்புக் குழுவை"}
    l_str = LOCS.get(target, (loc_text + "க்கு") if loc_text else (target + "க்கு" if target else ""))
    e_str = ENTITIES.get(entity, "குழுவை")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"உடனடியாக {t}{q}{e_str} அனுப்பவும்."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} அவசர உதவி தேவைப்படுகிறது." if l_str else "உடனடி உதவி தேவைப்படுகிறது."
    elif "EVACUATE" in action:
        return f"{l_str or 'பகுதியை'} உடனடியாக வெளியேற்றவும்."
    elif "ALERT" in action:
        return f"எச்சரிக்கை: {l_str} {hazard or 'ஆபத்து'}."
    return f"{l_str or 'பகுதியின்'} நிலை அறிக்கை."


# ==============================================================================
# 8. TELUGU (te)
# ==============================================================================
def _realize_te(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "హుబ్లీకి", "TOLANKERE": "తోలన్కెరెకు", "BASE": "బేస్‌కు", "SECTOR_4": "సెక్టార్ 4 కు", "HOSPITAL": "ఆసుపత్రికి"}
    ENTITIES = {"RESCUE": "రక్షణ బృందాన్ని", "RESCUE_REQUEST": "రక్షణ బృందాన్ని", "MEDICAL": "వైద్య బృందాన్ని", "AMBULANCE": "అంబులెన్స్", "FIRE": "అగ్నిమాపక దళాన్ని", "FIRE_TEAM": "అగ్నిమాపక సిబ్బందిని"}
    l_str = LOCS.get(target, (loc_text + "కు") if loc_text else (target + "కు" if target else ""))
    e_str = ENTITIES.get(entity, "బృందాన్ని")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"వెంటనే {t}{q}{e_str} పంపండి."
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} వద్ద తక్షణ సహాయం అవసరం." if l_str else "తక్షణ సహాయం అవసరం."
    elif "EVACUATE" in action:
        return f"{l_str or 'ప్రాంతాన్ని'} వెంటనే ఖాళీ చేయించండి."
    elif "ALERT" in action:
        return f"హెచ్చరిక: {l_str} {hazard or 'ప్రమాదం'}."
    return f"{l_str or 'ప్రాంతపు'} నివేదిక."


# ==============================================================================
# 9. ODIA (or)
# ==============================================================================
def _realize_or(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "ହୁବ୍ଲିକୁ", "TOLANKERE": "ତୋଲାଙ୍କେରେକୁ", "BASE": "ବେସକୁ", "SECTOR_4": "ସେକ୍ଟର 4 କୁ", "HOSPITAL": "ଡାକ୍ତରଖାନାକୁ"}
    ENTITIES = {"RESCUE": "ଉଦ୍ଧାରକାରୀ ଦଳ", "RESCUE_REQUEST": "ଉଦ୍ଧାରକାରୀ ଦଳ", "MEDICAL": "ଡାକ୍ତରୀ ଦଳ", "AMBULANCE": "ଆମ୍ବୁଲାନ୍ସ", "FIRE": "ଅଗ୍ନିଶମ ବାହିନୀ", "FIRE_TEAM": "ଅଗ୍ନିଶମ କର୍ମଚାରୀ"}
    l_str = LOCS.get(target, (loc_text + "କୁ") if loc_text else (target + "କୁ" if target else ""))
    e_str = ENTITIES.get(entity, "ଦଳ")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"ତୁରନ୍ତ {t}{q}{e_str} ପଠାନ୍ତୁ।"
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} ଠାରେ ତୁରନ୍ତ ସାହାଯ୍ୟ ଆବଶ୍ୟକ।" if l_str else "ତୁରନ୍ତ ସାହାଯ୍ୟ ଆବଶ୍ୟକ।"
    elif "EVACUATE" in action:
        return f"{l_str or 'ଏହି ଅଞ୍ଚଳକୁ'} ତୁରନ୍ତ ଖାଲି କରନ୍ତୁ।"
    elif "ALERT" in action:
        return f"ଚେତାବନୀ: {l_str} {hazard or 'ବିପଦ'}।"
    return f"{l_str or 'ଅଞ୍ଚଳର'} ସ୍ଥିତି ବିବରଣୀ।"


# ==============================================================================
# 10. BENGALI (bn)
# ==============================================================================
def _realize_bn(action, entity, target, loc_text, hazard, qty):
    LOCS = {"HUBBLI": "হুবলিতে", "TOLANKERE": "তোলনকেরেতে", "BASE": "ঘাঁটিতে", "SECTOR_4": "সেক্টর ৪-এ", "HOSPITAL": "হাসপাতালে"}
    ENTITIES = {"RESCUE": "উদ্ধারকারী দল", "RESCUE_REQUEST": "উদ্ধারকারী দল", "MEDICAL": "চিকিৎসা দল", "AMBULANCE": "অ্যাম্বুলেন্স", "FIRE": "দমকল বাহিনী", "FIRE_TEAM": "দমকল কর্মী"}
    l_str = LOCS.get(target, (loc_text + "-তে") if loc_text else (target + "-তে" if target else ""))
    e_str = ENTITIES.get(entity, "দল")

    if "SEND" in action or "RESCUE" in action:
        q = f"{qty} " if qty else ""
        t = f"{l_str} " if l_str else ""
        return f"অবিলম্বে {t}{q}{e_str} পাঠান।"
    elif "HELP" in action or "REQUEST" in action:
        return f"{l_str} অবিলম্বে সাহায্যের প্রয়োজন।" if l_str else "অবিলম্বে সাহায্যের প্রয়োজন।"
    elif "EVACUATE" in action:
        return f"{l_str or 'এলাকাটি'} অবিলম্বে খালি করুন।"
    elif "ALERT" in action:
        return f"সতর্কতা: {l_str} {hazard or 'বিপদ'}।"
    return f"{l_str or 'এলাকার'} পরিস্থিতি رپورٹ।"
