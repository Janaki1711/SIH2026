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


# ==============================================================================
#  SENTINEL GUARD + LANGUAGE-NEUTRAL (ENGLISH-PIVOT) LEXICONS
# ==============================================================================
# Internal enum placeholders that must NEVER surface in user-visible output.
_SENTINELS = {"UNKNOWN", "UNDEFINED", "NONE", "NULL", "N/A", "PROPER_LOCATION"}

# Source-language hazard keyword → language-neutral key (the English pivot).
_HAZARD_CANON: Dict[str, str] = {
    # English
    "fire": "fire", "flood": "flood", "earthquake": "earthquake",
    "landslide": "landslide", "explosion": "explosion", "gas leak": "gas leak",
    "chemical spill": "chemical spill", "tsunami": "tsunami",
    "cyclone": "cyclone", "collapse": "collapse",
    "building collapsed": "collapse", "structure failed": "collapse",
    "roof fallen": "collapse",
    # Hindi / Marathi (shared Devanagari)
    "आग": "fire", "अग्निकांड": "fire", "बाढ़": "flood", "भूकंप": "earthquake",
    "भूस्खलन": "landslide", "विस्फोट": "explosion", "गैस रिसाव": "gas leak",
    "सुनामी": "tsunami", "चक्रवात": "cyclone",
    # Gujarati
    "આગ": "fire", "પૂર": "flood", "ભૂકંપ": "earthquake",
    "વિસ્ફોટ": "explosion",
    # Tamil
    "தீ": "fire", "வெள்ளம்": "flood", "விபத்து": "collapse",
    # Telugu
    "అగ్ని": "fire", "వరదలు": "flood",
    # Kannada
    "ಬೆಂಕಿ": "fire", "ಪ್ರವಾಹ": "flood",
    # Malayalam
    "തീപിടിത്തം": "fire", "പ്രളയം": "flood", "ഭൂകമ്പം": "earthquake",
    "ഉരുൾപൊട്ടൽ": "landslide", "വിസ്ഫോടനം": "explosion",
    "സുനാമി": "tsunami",
    # Odia
    "ଅଗ୍ନିକାଣ୍ଡ": "fire", "ବନ୍ୟା": "flood", "ଭୂକମ୍ପ": "earthquake",
    "ଭୂସ୍ଖଳନ": "landslide", "ବିସ୍ଫୋରଣ": "explosion", "ବାତ୍ୟା": "cyclone",
    # Bengali
    "অগ্নিকাণ্ড": "fire", "বন্যা": "flood", "ভূমিকম্প": "earthquake",
    "ভূস্খলন": "landslide", "বিস্ফোরণ": "explosion", "ঘূর্ণিঝড়": "cyclone",
}


def _canonical_hazard(hazard_str: str) -> str:
    """Map a source-language hazard keyword to its language-neutral key."""
    if not hazard_str:
        return ""
    for part in str(hazard_str).split(","):
        key = _HAZARD_CANON.get(part.strip().lower())
        if key:
            return key
    return ""


# Language-neutral hazard key → target-language word (per supported language).
_HAZARD_OUT: Dict[str, Dict[str, str]] = {
    "en": {"fire": "fire", "flood": "flood", "earthquake": "earthquake",
           "landslide": "landslide", "explosion": "explosion",
           "gas leak": "gas leak", "chemical spill": "chemical spill",
           "tsunami": "tsunami", "cyclone": "cyclone",
           "collapse": "building collapse"},
    "hi": {"fire": "आग", "flood": "बाढ़", "earthquake": "भूकंप",
           "landslide": "भूस्खलन", "explosion": "विस्फोट",
           "gas leak": "गैस रिसाव", "chemical spill": "रासायनिक रिसाव",
           "tsunami": "सुनामी", "cyclone": "चक्रवात",
           "collapse": "इमारत गिरना"},
    "gu": {"fire": "આગ", "flood": "પૂર", "earthquake": "ભૂકંપ",
           "landslide": "ભૂસ્ખલન", "explosion": "વિસ્ફોટ",
           "gas leak": "ગેસ ચુસ્કી", "chemical spill": "રાસાયણિક ચુસ્કી",
           "tsunami": "સુનામી", "cyclone": "વાવાઝોડું",
           "collapse": "ઇમારત ધરાશાયી"},
    "mr": {"fire": "आग", "flood": "पूर", "earthquake": "भूकंप",
           "landslide": "भूस्खलन", "explosion": "विस्फोट",
           "gas leak": "गॅस गळती", "chemical spill": "रासायनिक गळती",
           "tsunami": "सुनामी", "cyclone": "चक्रीवादळ",
           "collapse": "इमारत पडणे"},
    "kn": {"fire": "ಬೆಂಕಿ", "flood": "ಪ್ರವಾಹ", "earthquake": "ಭೂಕಂಪ",
           "landslide": "ಭೂಕುಸಿತ", "explosion": "ಸ್ಫೋಟ",
           "gas leak": "ಅನಿಲ ಸೋರಿಕೆ", "chemical spill": "ರಾಸಾಯನಿಕ ಸೋರಿಕೆ",
           "tsunami": "ಸುನಾಮಿ", "cyclone": "ಚಂಡಮಾರುತ",
           "collapse": "ಕಟ್ಟಡ ಕುಸಿತ"},
    "ml": {"fire": "തീപിടിത്തം", "flood": "പ്രളയം", "earthquake": "ഭൂകമ്പം",
           "landslide": "ഉരുൾപൊട്ടൽ", "explosion": "വിസ്ഫോടനം",
           "gas leak": "വാതകചോർച്ച", "chemical spill": "രാസവസ്തു ചോർച്ച",
           "tsunami": "സുനാമി", "cyclone": "ചുഴലിക്കാറ്റ്",
           "collapse": "കെട്ടിടം തകർന്നു"},
    "ta": {"fire": "தீ", "flood": "வெள்ளம்", "earthquake": "நிலநடுக்கம்",
           "landslide": "நிலச்சரிவு", "explosion": "குண்டுவெடிப்பு",
           "gas leak": "எரிவாயு கசிவு", "chemical spill": "ரசாயனக் கசிவு",
           "tsunami": "சுனாமி", "cyclone": "புயல்",
           "collapse": "கட்டிடம் இடிந்தது"},
    "te": {"fire": "అగ్ని", "flood": "వరద", "earthquake": "భూకంపం",
           "landslide": "భూస్ఖలనం", "explosion": "పేలుడు",
           "gas leak": "వాయు లీక్", "chemical spill": "రసాయన లీక్",
           "tsunami": "సునామి", "cyclone": "తుఫాను",
           "collapse": "భవనం కుప్పకూలింది"},
    "or": {"fire": "ଅଗ୍ନିକାଣ୍ଡ", "flood": "ବନ୍ୟା", "earthquake": "ଭୂକମ୍ପ",
           "landslide": "ଭୂସ୍ଖଳନ", "explosion": "ବିସ୍ଫୋରଣ",
           "gas leak": "ଗ୍ୟାସ ଚୋରା", "chemical spill": "ରାସାୟନିକ ଚୋରା",
           "tsunami": "ସୁନାମୀ", "cyclone": "ବାତ୍ୟା",
           "collapse": "ଘର ଭାଙ୍ଗିଛି"},
    "bn": {"fire": "আগ", "flood": "বন্যা", "earthquake": "ভূমিকম্প",
           "landslide": "ভূস্খলন", "explosion": "বিস্ফোরণ",
           "gas leak": "গ্যাস লিক", "chemical spill": "রাসায়নিক লিক",
           "tsunami": "সুনামি", "cyclone": "ঘূর্ণিঝড়",
           "collapse": "ভবন ভেঙে পড়েছে"},
}

# Parsed Condition enum → short target-language phrase (same pivot idea).
_COND_PHRASES: Dict[str, Dict[str, str]] = {
    "en": {"TRAPPED": "people are trapped", "INJURED": "people are injured",
           "UNCONSCIOUS": "people are unconscious", "MISSING": "people are missing",
           "CRITICAL": "the condition is critical", "SAFE": "people are safe",
           "EVACUATED": "the area has been evacuated",
           "EXPOSED": "people are exposed to the weather"},
    "hi": {"TRAPPED": "लोग फंसे हुए हैं", "INJURED": "लोग घायल हैं",
           "UNCONSCIOUS": "लोग बेहोश हैं", "MISSING": "लोग लापता हैं",
           "CRITICAL": "स्थिति गंभीर है", "SAFE": "लोग सुरक्षित हैं",
           "EVACUATED": "इलाका खाली कर दिया गया है",
           "EXPOSED": "लोग खुले में हैं"},
    "gu": {"TRAPPED": "લોકો ફસાયેલા છે", "INJURED": "લોકો ઘાયલ છે",
           "UNCONSCIOUS": "લોકો બેહોશ છે", "MISSING": "લોકો ગુમ થયા છે",
           "CRITICAL": "સ્થિતિ ગંભીર છે", "SAFE": "લોકો સુરક્ષિત છે",
           "EVACUATED": "વિસ્તાર ખાલી કરવામાં આવ્યો છે",
           "EXPOSED": "લોકો ખુલ્લામાં છે"},
    "mr": {"TRAPPED": "लोक अडकले आहेत", "INJURED": "लोक जखमी आहेत",
           "UNCONSCIOUS": "लोक बेशुद्ध आहेत", "MISSING": "लोक गायब आहेत",
           "CRITICAL": "स्थिती गंभीर आहे", "SAFE": "लोक सुरक्षित आहेत",
           "EVACUATED": "परिसर रिकामा केला आहे",
           "EXPOSED": "लोक उघड्यावर आहेत"},
    "kn": {"TRAPPED": "ಜನರು ಸಿಕ್ಕಿಹಿಡಿದಿದ್ದಾರೆ", "INJURED": "ಜನರು ಗಾಯಗೊಂಡಿದ್ದಾರೆ",
           "UNCONSCIOUS": "ಜನರು ಪ್ರಜ್ಞೆ ತಪ್ಪಿದ್ದಾರೆ", "MISSING": "ಜನರು ಕಾಣೆಯಾಗಿದ್ದಾರೆ",
           "CRITICAL": "ಸ್ಥಿತಿ ಗಂಭೀರವಾಗಿದೆ", "SAFE": "ಜನರು ಸುರಕ್ಷಿತರಾಗಿದ್ದಾರೆ",
           "EVACUATED": "ಪ್ರದೇಶವನ್ನು ಖಾಲಿ ಮಾಡಲಾಗಿದೆ",
           "EXPOSED": "ಜನರು ಮುಕ್ತ ಸ್ಥಳದಲ್ಲಿದ್ದಾರೆ"},
    "ml": {"TRAPPED": "ആളുകൾ കുടുങ്ങിയിട്ടുണ്ട്", "INJURED": "ആളുകൾക്ക് പരിക്പറ്റിയിട്ടുണ്ട്",
           "UNCONSCIOUS": "ആളുകൾ ബോധരഹിതരാണ്", "MISSING": "ആളുകൾ കാണാതായി",
           "CRITICAL": "അവസ്ഥ ഗുരുതരമാണ്", "SAFE": "ആളുകൾ സുരക്ഷിതരാണ്",
           "EVACUATED": "പ്രദേശം ഒഴിപ്പിച്ചു",
           "EXPOSED": "ആളുകൾക്ക് അഭയമില്ല"},
    "ta": {"TRAPPED": "மக்கள் சிக்கியுள்ளனர்", "INJURED": "மக்கள் காயமடைந்துள்ளனர்",
           "UNCONSCIOUS": "மக்கள் மயக்கத்தில் உள்ளனர்", "MISSING": "மக்கள் காணாமல் போயுள்ளனர்",
           "CRITICAL": "நிலைமை மிகவும் கவலைக்கிடமாக உள்ளது", "SAFE": "மக்கள் பாதுகாப்பாக உள்ளனர்",
           "EVACUATED": "பகுதி காலியாக்கப்பட்டது",
           "EXPOSED": "மக்கள் திறந்த வெளியில் உள்ளனர்"},
    "te": {"TRAPPED": "ప్రజలు చిక్కుకున్నారు", "INJURED": "ప్రజలు గాయపడ్డారు",
           "UNCONSCIOUS": "ప్రజలు స్పృహ లేనివారు", "MISSING": "ప్రజలు తప్పిపోయారు",
           "CRITICAL": "పరిస్థితి విషమం", "SAFE": "ప్రజలు సురక్షితంగా ఉన్నారు",
           "EVACUATED": "ప్రాంతాన్ని ఖాళీ చేశారు",
           "EXPOSED": "ప్రజలు బయట ఉన్నారు"},
    "or": {"TRAPPED": "ଲୋକେ ଫସିଯାଇଛନ୍ତି", "INJURED": "ଲୋକେ ଆହତ ହୋଇଛନ୍ତି",
           "UNCONSCIOUS": "ଲୋକେ ବେହୋସ ଅଛନ୍ତି", "MISSING": "ଲୋକେ ହଜିଯାଇଛନ୍ତି",
           "CRITICAL": "ସ୍ଥିତି ଗୁରୁତର", "SAFE": "ଲୋକେ ସୁରକ୍ଷିତ ଅଛନ୍ତି",
           "EVACUATED": "ଅଞ୍ଚଳ ଖାଲି ହୋଇଛି",
           "EXPOSED": "ଲୋକେ ଖୋଲା ସ୍ଥାନରେ ଅଛନ୍ତି"},
    "bn": {"TRAPPED": "মানুষ আটকে পড়েছে", "INJURED": "মানুষ আহত",
           "UNCONSCIOUS": "মানুষ অচেতন", "MISSING": "মানুষ নিখোঁজ",
           "CRITICAL": "অবস্থা গুরুতর", "SAFE": "মানুষ নিরাপদ",
           "EVACUATED": "এলাকা খালি করা হয়েছে",
           "EXPOSED": "মানুষ খোলায় আছে"},
}

# Sentence templates for the condition / hazard appendices.
_COND_FMT: Dict[str, str] = {
    "en": "Status: {c}.", "hi": "स्थिति: {c}।", "gu": "સ્થિતિ: {c}.",
    "mr": "स्थिती: {c}.", "kn": "ಸ್ಥಿತಿ: {c}.", "ml": "അവസ്ഥ: {c}.",
    "ta": "நிலை: {c}.", "te": "పరిస్థితి: {c}.", "or": "ସ୍ଥିତି: {c}.",
    "bn": "অবস্থা: {c}।",
}

_DANGER_FMT: Dict[str, str] = {
    "en": "Danger: {h}.", "hi": "खतरा: {h}।", "gu": "જોખમ: {h}.",
    "mr": "धोका: {h}.", "kn": "ಅಪಾಯ: {h}.", "ml": "അപകടം: {h}.",
    "ta": "ஆபத்து: {h}.", "te": "ప్రమాదం: {h}.", "or": "ବିପଦ: {h}.",
    "bn": "বিপদ: {h}।",
}


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

    # Primary: use location_text (SemanticMessage proper-noun field)
    loc_text = getattr(msg_or_result, 'location_text', '') or ""

    # Secondary: try legacy 'location' attribute (geo_resolver style objects)
    loc_obj = getattr(msg_or_result, 'location', None)
    if loc_obj:
        if hasattr(loc_obj, 'canonical_name'):
            if not target or target == "UNKNOWN":
                target = loc_obj.canonical_name.upper()
            if not loc_text:
                loc_text = loc_obj.canonical_name
        elif isinstance(loc_obj, str) and not loc_obj.startswith("LocationEntity"):
            if not loc_text:
                loc_text = loc_obj
            if not target: target = loc_obj.upper()

    # If target is PROPER_LOCATION sentinel, replace with the actual text
    if target == "PROPER_LOCATION" and loc_text:
        target = loc_text.upper()

    hazard_text = getattr(msg_or_result, 'hazard', '') or getattr(msg_or_result, 'hazard_text', '')
    if hasattr(hazard_text, 'name'): hazard_text = hazard_text.name
    hazard_str = str(hazard_text).replace("_", " ").lower() if hazard_text else ""

    qty = getattr(msg_or_result, 'person_count', 0) or getattr(msg_or_result, 'quantity', 0)
    if hasattr(qty, 'value'): qty = qty.value
    qty_str = str(qty) if qty and int(qty) > 0 else ""

    is_negated = getattr(msg_or_result, 'is_negated', False)

    # Condition is carried through so status-only messages keep their meaning.
    condition = _extract_field_val(getattr(msg_or_result, 'condition', ''))

    # ── NEVER emit internal sentinels (UNKNOWN / PROPER_LOCATION / …) ───────
    def _scrub(v: Any) -> str:
        if not v:
            return ""
        s = str(v).strip()
        return "" if s.upper() in _SENTINELS else s

    action = _scrub(action)
    entity = _scrub(entity)
    target = _scrub(target)
    loc_text = _scrub(loc_text)
    condition = _scrub(condition)
    hazard_str = _scrub(hazard_str)

    # Hazard: source-language keyword → language-neutral key → target word.
    hazard_key = _canonical_hazard(hazard_str)
    hazard_out = _HAZARD_OUT.get(lang, {}).get(hazard_key, "") if hazard_key else ""

    # Dispatch to language-specific realizer
    realizers = {
        "en": _realize_en, "hi": _realize_hi, "gu": _realize_gu,
        "mr": _realize_mr, "kn": _realize_kn, "ml": _realize_ml,
        "ta": _realize_ta, "te": _realize_te, "or": _realize_or,
        "bn": _realize_bn
    }
    base = realizers[lang](action, entity, target, loc_text, hazard_out, qty_str, is_negated)

    # ── Append semantics the fixed sentence templates don't carry ───────────
    extras = []
    if condition:
        phrase = _COND_PHRASES.get(lang, {}).get(condition)
        if phrase:
            extras.append(_COND_FMT[lang].format(c=phrase))
    if hazard_out and "ALERT" not in action:
        extras.append(_DANGER_FMT[lang].format(h=hazard_out))
    if extras:
        return f"{base} {' '.join(extras)}"
    return base


# ==============================================================================
# 1. ENGLISH (en)
# ==============================================================================
def _realize_en(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "Hubbli", "TOLANKERE": "Tolankere", "BASE": "Base HQ", "SECTOR_4": "Sector 4", "HOSPITAL": "the hospital"}
    ENTITIES = {"RESCUE": "rescue team", "RESCUE_REQUEST": "rescue team", "MEDICAL": "medical team", "AMBULANCE": "ambulance", "FIRE": "fire brigade", "FIRE_TEAM": "firefighters"}
    l_str = LOCS.get(target, loc_text or (target.replace("_", " ").title() if target else ""))
    e_str = ENTITIES.get(entity, entity.replace("_", " ").lower() if entity else "team")

    if is_negated:
        if "EVACUATE" in action:
            return f"Do NOT evacuate {l_str or 'the area'}."
        if "MEDICAL" in action or "AMBULANCE" in entity or "MEDICAL" in entity:
            return f"Medical assistance / ambulance NOT required at {l_str}." if l_str else "Medical assistance / ambulance NOT required."
        if "SEND" in action or "RESCUE" in action or "HELP" in action or "REQUEST" in action:
            return f"Rescue assistance NOT required at {l_str}." if l_str else "Rescue assistance NOT required."
        if "SUPPLIES" in action:
            return f"Supplies / water NOT required at {l_str}." if l_str else "Supplies / water NOT required."
        return f"Negative update: no action required for {l_str or 'current location'}."

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
def _realize_hi(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "हब्बली", "TOLANKERE": "तोलनकेरे", "BASE": "बेस", "SECTOR_4": "सेक्टर 4", "HOSPITAL": "अस्पताल"}
    ENTITIES = {"RESCUE": "बचाव दल", "RESCUE_REQUEST": "बचाव दल", "MEDICAL": "चिकित्सा दल", "AMBULANCE": "एम्बुलेंस", "FIRE": "दमकल", "FIRE_TEAM": "अग्निशमन दल"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "दल")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'क्षेत्र'} को खाली मत करो।"
        if "MEDICAL" in action or "AMBULANCE" in entity:
            return f"{l_str} में चिकित्सा सहायता / एम्बुलेंस की आवश्यकता नहीं है।" if l_str else "चिकित्सा सहायता की आवश्यकता नहीं है।"
        if "SEND" in action or "RESCUE" in action:
            return f"{l_str} में बचाव सहायता की आवश्यकता नहीं है।" if l_str else "सहायता की आवश्यकता नहीं है।"
        return f"{l_str or 'क्षेत्र'} में किसी सहायता की आवश्यकता नहीं है।"

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
def _realize_gu(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "હબ્બલી", "TOLANKERE": "તોલનકેરે", "BASE": "બેઝ", "SECTOR_4": "સેક્ટર 4", "HOSPITAL": "હોસ્પિટલ"}
    ENTITIES = {"RESCUE": "બચાવ ટીમ", "RESCUE_REQUEST": "બચાવ ટીમ", "MEDICAL": "તબીબી ટીમ", "AMBULANCE": "એમ્બ્યુલન્સ", "FIRE": "ફાયર બ્રિગેડ", "FIRE_TEAM": "અગ્નિશામક દળ"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "ટીમ")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'વિસ્તાર'} ખાલી કરશો નહીં."
        return f"{l_str or 'વિસ્તાર'}માં મદદની જરૂર નથી."

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
def _realize_mr(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "हब्बली", "TOLANKERE": "तोलनकेरे", "BASE": "तळ", "SECTOR_4": "सेक्टर 4", "HOSPITAL": "रुग्णालय"}
    ENTITIES = {"RESCUE": "बचाव पथक", "RESCUE_REQUEST": "बचाव पथक", "MEDICAL": "वैद्यकीय पथक", "AMBULANCE": "रुग्णवाहिका", "FIRE": "अग्निशामक दल", "FIRE_TEAM": "अग्निशामक पथक"}
    l_str = LOCS.get(target, loc_text or target)
    e_str = ENTITIES.get(entity, "पथक")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'परिसर'} रिकामा करू नका."
        return f"{l_str or 'परिसर'}मध्ये मदतीची गरज नाही."

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
def _realize_kn(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "ಹುಬ್ಬಳ್ಳಿಗೆ", "TOLANKERE": "ತೊಳನಕೆರೆಗೆ", "BASE": "ನೆಲೆಗೆ", "SECTOR_4": "ಸೆಕ್ಟರ್ 4 ಕ್ಕೆ", "HOSPITAL": "ಆಸ್ಪತ್ರೆಗೆ"}
    ENTITIES = {"RESCUE": "ರಕ್ಷಣಾ ತಂಡ", "RESCUE_REQUEST": "ರಕ್ಷಣಾ ತಂಡ", "MEDICAL": "ವೈದ್ಯಕೀಯ ತಂಡ", "AMBULANCE": "ಆಂಬ್ಯುಲೆನ್ಸ್", "FIRE": "ಅಗ್ನಿಶಾಮಕ ದಳ", "FIRE_TEAM": "ಅಗ್ನಿಶಾಮಕ ಸಿಬ್ಬಂದಿ"}
    l_str = LOCS.get(target, (loc_text + "ಗೆ") if loc_text else (target + "ಗೆ" if target else ""))
    e_str = ENTITIES.get(entity, "ತಂಡ")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'ಪ್ರದೇಶವನ್ನು'} ಖಾಲಿ ಮಾಡಬೇಡಿ."
        return f"{l_str or 'ಪ್ರದೇಶಕ್ಕೆ'} ಯಾವುದೇ ಸಹಾಯ ಅಗತ್ಯವಿಲ್ಲ."

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
def _realize_ml(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "ഹുബ്ലിയിലേക്ക്", "TOLANKERE": "തോളങ്കരെയിലേക്ക്", "BASE": "ബേസിലേക്ക്", "SECTOR_4": "സെക്ടർ 4 ലേക്ക്", "HOSPITAL": "ആശുപത്രിയിലേക്ക്"}
    ENTITIES = {"RESCUE": "രക്ഷാപ്രവർത്തക സംഘത്തെ", "RESCUE_REQUEST": "രക്ഷാപ്രവർത്തക സംഘത്തെ", "MEDICAL": "മെഡിക്കൽ സംഘത്തെ", "AMBULANCE": "ആംബുലൻസ്", "FIRE": "ഫയർ ഫോഴ്സിനെ", "FIRE_TEAM": "അഗ്നിശമന സേനയെ"}
    l_str = LOCS.get(target, (loc_text + "ലേക്ക്") if loc_text else (target + "ലേക്ക്" if target else ""))
    e_str = ENTITIES.get(entity, "സംഘത്തെ")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'പ്രദേശം'} ഒഴിപ്പിക്കരുത്."
        return f"{l_str or 'സ്ഥലത്ത്'} സഹായം ആവശ്യമില്ല."

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
def _realize_ta(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "ஹூப்ளிக்கு", "TOLANKERE": "தோலன்கெரேவுக்கு", "BASE": "முகாமிற்கு", "SECTOR_4": "பகுதி 4-க்கு", "HOSPITAL": "மருத்துவமனைக்கு"}
    ENTITIES = {"RESCUE": "மீட்புக் குழுவை", "RESCUE_REQUEST": "மீட்புக் குழுவை", "MEDICAL": "மருத்துவக் குழுவை", "AMBULANCE": "ஆம்புலன்ஸை", "FIRE": "தீயணைப்புப் படையை", "FIRE_TEAM": "தீயணைப்புக் குழுவை"}
    l_str = LOCS.get(target, (loc_text + "க்கு") if loc_text else (target + "க்கு" if target else ""))
    e_str = ENTITIES.get(entity, "குழுவை")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'பகுதியை'} வெளியேற்ற வேண்டாம்."
        return f"{l_str or 'பகுதிக்கு'} உதவி தேவையில்லை."

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
def _realize_te(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "హుబ్లీకి", "TOLANKERE": "తోలంకెరెకు", "BASE": "బేస్‌కు", "SECTOR_4": "సెక్టార్ 4 కు", "HOSPITAL": "ఆసుపత్రికి"}
    ENTITIES = {"RESCUE": "రక్షణ బృందాన్ని", "RESCUE_REQUEST": "రక్షణ బృందాన్ని", "MEDICAL": "వైద్య బృందాన్ని", "AMBULANCE": "అంబులెన్స్", "FIRE": "అగ్నిమాపక దళాన్ని", "FIRE_TEAM": "అగ్నిమాపక సిబ్బందిని"}
    l_str = LOCS.get(target, (loc_text + "కు") if loc_text else (target + "కు" if target else ""))
    e_str = ENTITIES.get(entity, "బృందాన్ని")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'ప్రాంతాన్ని'} ఖాళీ చేయవద్దు."
        return f"{l_str or 'ప్రాంతానికి'} సహాయం అవసరం లేదు."

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
def _realize_or(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "ହୁବ୍ଲିକୁ", "TOLANKERE": "ତୋଲାଙ୍କେରେକୁ", "BASE": "ବେସକୁ", "SECTOR_4": "ସେକ୍ଟର 4 କୁ", "HOSPITAL": "ଡାକ୍ତରଖାନାକୁ"}
    ENTITIES = {"RESCUE": "ଉଦ୍ଧାରକାରୀ ଦଳ", "RESCUE_REQUEST": "ଉଦ୍ଧାରକାରୀ ଦଳ", "MEDICAL": "ଡାକ୍ତରୀ ଦଳ", "AMBULANCE": "ଆମ୍ବୁଲାନ୍ସ", "FIRE": "ଅଗ୍ନିଶମ ବାହିନୀ", "FIRE_TEAM": "ଅଗ୍ନିଶମ କର୍ମଚାରୀ"}
    l_str = LOCS.get(target, (loc_text + "କୁ") if loc_text else (target + "କୁ" if target else ""))
    e_str = ENTITIES.get(entity, "ଦଳ")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'ଅଞ୍ଚଳ'} ଖାଲି କରନ୍ତୁ ନାହିଁ।"
        return f"{l_str or 'ଅଞ୍ଚଳ'} ପାଇଁ ସହାୟତା ଆବଶ୍ୟକ ନାହିଁ।"

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
def _realize_bn(action, entity, target, loc_text, hazard, qty, is_negated=False):
    LOCS = {"HUBBLI": "হুবলিতে", "TOLANKERE": "তোলনকেরেতে", "BASE": "ঘাঁটিতে", "SECTOR_4": "সেক্টর ৪-এ", "HOSPITAL": "হাসপাতালে"}
    ENTITIES = {"RESCUE": "উদ্ধারকারী দল", "RESCUE_REQUEST": "উদ্ধারকারী দল", "MEDICAL": "চিকিৎসা দল", "AMBULANCE": "অ্যাম্বুলেন্স", "FIRE": "দমকল বাহিনী", "FIRE_TEAM": "দমকল কর্মী"}
    l_str = LOCS.get(target, (loc_text + "-তে") if loc_text else (target + "-তে" if target else ""))
    e_str = ENTITIES.get(entity, "দল")

    if is_negated:
        if "EVACUATE" in action:
            return f"{l_str or 'এলাকা'} খালি করবেন না।"
        return f"{l_str or 'এলাকা'}তে সাহায্যের প্রয়োজন নেই।"

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
    return f"{l_str or 'এলাকারের'}পরিস্থিতির প্রতিবেদন।"


# ==============================================================================
# PUBLIC TRANSLATION HELPER
# ==============================================================================
def translate(arg1: str, arg2: str, arg3: str) -> str:
    """Translate text from source to target language via canonical semantic representation.
    Pipeline: text → parse(source_lang) → SemanticMessage → realize(target_lang)
    Supports both (source_lang, target_lang, text) and (text, source_lang, target_lang) orderings.
    All 100 source×target combinations supported.

    Honest-output rules (English-as-median: the semantic IR is the pivot):
      • src == tgt → identity (never rewrite text into itself)
      • weak/fallback parse → passthrough of the original (never fabricate)
      • nothing translatable (no action/condition/hazard) → passthrough
      • internal sentinels (UNKNOWN…) never reach user-visible output
    """
    arg1_s, arg2_s, arg3_s = str(arg1), str(arg2), str(arg3)
    if arg1_s.lower() in SUPPORTED_LANGUAGES and arg2_s.lower() in SUPPORTED_LANGUAGES:
        source_language, target_language, text = arg1_s.lower(), arg2_s.lower(), arg3_s
    elif arg2_s.lower() in SUPPORTED_LANGUAGES and arg3_s.lower() in SUPPORTED_LANGUAGES:
        text, source_language, target_language = arg1_s, arg2_s.lower(), arg3_s.lower()
    else:
        source_language, target_language, text = arg1_s.lower(), arg2_s.lower(), arg3_s

    # Same language → identity.
    if source_language == target_language:
        return text

    import semantic_parser
    msg = semantic_parser.parse(text, source_language)

    # Weak parse → honest passthrough (never fabricate a "translation").
    if getattr(msg, "is_fallback", False):
        return text

    # Nothing we can faithfully realize (status/emotion/quantity-only) → passthrough.
    has_translatable = (
        getattr(getattr(msg, "action", None), "code", 0) != 0
        or getattr(getattr(msg, "condition", None), "code", 0) != 0
        or bool(getattr(msg, "hazard_text", ""))
    )
    if not has_translatable:
        return text

    out = realize(msg, target_language)

    # Belt-and-braces: never leak an internal sentinel into user-visible text.
    if not out or not out.strip():
        return text
    if "unknown" in out.lower() and "unknown" not in text.lower():
        return text
    return out

