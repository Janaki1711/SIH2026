# translation_engine.py
"""
iTantra M3 Translation Engine (Target Language Realization)
Converts a SemanticMessage back into human-readable text.

v2 fixes:
 - Never emit the literal word "UNKNOWN" in output
 - Use source_phrase as fallback when value is UNKNOWN
 - Graceful sentence construction for partial messages
 - Proper-noun location passthrough in all languages
"""

from semantic_schema import SemanticMessage

SUPPORTED_LANGUAGES = ["hi", "en", "mr", "ta", "te", "kn"]
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "en": "English",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
}

def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)

def _resolve_location(msg: SemanticMessage, target_map: dict) -> str:
    """Return the best location string — never 'UNKNOWN'."""
    if msg.target.value == "PROPER_LOCATION" and msg.location_text:
        return msg.location_text
    if msg.target.code == 0:
        # Target is UNKNOWN — use source_phrase if available, else empty string
        return msg.target.source_phrase or ""
    return target_map.get(str(msg.target.value), str(msg.target.value).replace("_", " "))

def _resolve_entity(msg: SemanticMessage, entity_map: dict) -> str:
    """Return the best entity string — never 'UNKNOWN'."""
    if msg.entity.code == 0:
        if msg.resource_text:
            return msg.resource_text
        return msg.entity.source_phrase or ""
    val = str(msg.entity.value)
    return entity_map.get(val, val.replace("_", " "))

def realize(msg: SemanticMessage, target_language: str) -> str:
    if msg.is_fallback:
        return f"[FALLBACK_TEXT]: {msg.fallback_text}"

    qty = msg.quantity.value if msg.quantity.value > 0 else ""

    if target_language == "hi":
        return _realize_hindi(msg, qty)
    elif target_language == "en":
        return _realize_english(msg, qty)
    elif target_language == "mr":
        return _realize_hindi(msg, qty) + " (MR)"
    elif target_language == "ta":
        return _realize_tamil(msg, qty)
    else:
        return _realize_english(msg, qty)


def _realize_english(msg: SemanticMessage, qty) -> str:
    ENTITY_MAP = {
        "RESCUE":     "rescue",
        "MEDICAL":    "medical",
        "POLICE":     "police",
        "FIRE":       "fire brigade",
        "FIRE_TEAM":  "fire",
        "SUPPLY":     "supply",
        "AMBULANCE":  "ambulance",
        "HELICOPTER": "helicopter",
        "DISASTER":   "disaster relief",
        "ENGINEER":   "engineering",
        "TROOP":      "troops",
    }
    TARGET_MAP = {
        "HUBBLI":    "Hubbli",
        "TOLANKERE": "Tolankere",
        "BASE":      "Base",
        "SECTOR_1":  "Sector 1",
        "SECTOR_2":  "Sector 2",
        "SECTOR_3":  "Sector 3",
        "SECTOR_4":  "Sector 4",
        "SECTOR_5":  "Sector 5",
        "BRIDGE":    "the bridge",
        "HOSPITAL":  "the hospital",
        "SCHOOL":    "the school",
    }

    ent = _resolve_entity(msg, ENTITY_MAP)
    tgt = _resolve_location(msg, TARGET_MAP)

    action = msg.action.value if msg.action.code != 0 else ""

    # ── SEND_TEAM ──
    if action == "SEND_TEAM":
        parts = ["Send"]
        if ent and ent.lower() in ("help", "support", "assistance"):
            parts.append(ent)
            if qty:
                parts.append(f"for {qty}")
        else:
            if qty:
                parts.append(str(qty))
            if ent:
                parts.append(f"{ent} team")
                
        cond = msg.condition.value if msg.condition.code != 0 else ""
        if cond:
            parts.append(f"({cond.lower()})")
            
        if tgt:
            parts.append(f"to {tgt}")
        parts.append("immediately.")
        return " ".join(parts)

    # ── REQUEST_HELP ──
    elif action == "REQUEST_HELP":
        resources = []
        if ent:
            resources.append(ent)
        for ef in msg.extra_fields:
            if ef.name == "RESOURCE_REQUIRED":
                val = str(ef.value)
                res = ENTITY_MAP.get(val, val.replace("_", " ").lower())
                if res not in resources: resources.append(res)
                
        ent_str = " and ".join(resources)
        
        if ent_str and tgt:
            return f"Requesting {ent_str} support at {tgt}."
        elif ent_str:
            return f"Requesting {ent_str} support immediately."
        elif tgt:
            return f"Requesting assistance at {tgt}."
        else:
            cond = msg.condition.value if msg.condition.code != 0 else ""
            em = msg.emotion.value if msg.emotion.code != 0 else ""
            details = " — ".join(filter(None, [cond, em]))
            return f"Help requested{(': ' + details) if details else ''}."

    # ── EVACUATE ──
    elif action == "EVACUATE":
        loc = tgt or "area"
        return f"Evacuate {loc} immediately."

    # ── ALERT ──
    elif action == "ALERT":
        hazard = msg.hazard_text or (msg.entity.source_phrase if msg.entity.code != 0 else "")
        loc = tgt or ""
        cond = msg.condition.value if msg.condition.code != 0 else ""
        parts = ["ALERT"]
        if hazard:
            parts.append(f"— {hazard}")
        if loc:
            parts.append(f"at {loc}")
        if cond:
            parts.append(f"({cond})")
        return " ".join(parts) + "."

    # ── MOVE ──
    elif action == "MOVE":
        parts = []
        if ent:
            parts.append(ent.capitalize())
        if msg.quantity.code != 0:
            parts.append(f"({qty})")
        cs_fields = [f for f in msg.extra_fields if f.name == "CALLSIGN"]
        if cs_fields:
            parts.append(cs_fields[0].value)
        parts.append("is moving")

        dir_fields = [f for f in msg.extra_fields if f.name == "DIRECTION"]
        direction = dir_fields[0].value.lower() if dir_fields else ""

        # Deduplicate if target is just the direction name
        if tgt and tgt.lower() in {"north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"}:
            if not direction:
                direction = tgt.lower()
            tgt = ""

        if direction and tgt and tgt.lower() != direction.lower():
            parts.append(f"{direction} towards {tgt}")
        elif direction:
            parts.append(direction)
        elif tgt:
            parts.append(f"towards {tgt}")

        cond = msg.condition.value if msg.condition.code != 0 else ""
        if cond:
            return f"{' '.join(parts)} — {cond}."
        return f"{' '.join(parts)}."

    # ── SEARCH ──
    elif action == "SEARCH":
        loc = tgt or "the area"
        return f"Searching {loc}."

    # ── REPORT / HOLD / SECURE / other ──
    elif action in ("REPORT", "HOLD", "SECURE"):
        loc = tgt or "location"
        return f"{action.replace('_', ' ').capitalize()} at {loc}."

    # ── NO CLEAR ACTION — build summary from available fields ──
    parts = []
    dir_fields = [f for f in msg.extra_fields if f.name == "DIRECTION"]
    direction = dir_fields[0].value if dir_fields else ""
    if msg.emotion.code != 0:
        parts.append(f"Situation: {msg.emotion.value.lower()}")
    if msg.condition.code != 0:
        parts.append(f"Condition: {msg.condition.value.lower()}")
        for ef in msg.extra_fields:
            if ef.name == "CONDITION_DETAIL":
                parts.append(f"also {ef.value.lower()}")
    if qty:
        parts.append(f"Count: {qty}")
    if direction:
        parts.append(f"Direction: {direction}")
    if tgt:
        parts.append(f"Location: {tgt}")
    if msg.hazard_text:
        parts.append(f"Hazard: {msg.hazard_text}")
    if msg.status_text:
        parts.append(f"Status: {msg.status_text}")
    if msg.urgency.code != 0:
        parts.append(f"[{msg.urgency.value}]")
    if parts:
        return ". ".join(parts) + "."
    return "[Partial semantic message received]"


def _realize_hindi(msg: SemanticMessage, qty) -> str:
    ENTITY_MAP = {
        "RESCUE":     "बचाव दल",
        "MEDICAL":    "चिकित्सा दल",
        "POLICE":     "पुलिस",
        "FIRE":       "फायर ब्रिगेड",
        "FIRE_TEAM":  "फायर दल",
        "SUPPLY":     "आपूर्ति",
        "AMBULANCE":  "एम्बुलेंस",
        "HELICOPTER": "हेलिकॉप्टर",
        "DISASTER":   "आपदा राहत दल",
        "ENGINEER":   "इंजीनियर दल",
        "TROOP":      "सेना दल",
    }
    TARGET_MAP = {
        "HUBBLI":    "हब्बली",
        "TOLANKERE": "तोलनकेरे",
        "BASE":      "बेस",
        "SECTOR_1":  "सेक्टर एक",
        "SECTOR_2":  "सेक्टर दो",
        "SECTOR_3":  "सेक्टर तीन",
        "SECTOR_4":  "सेक्टर चार",
        "SECTOR_5":  "सेक्टर पांच",
        "BRIDGE":    "पुल",
        "HOSPITAL":  "अस्पताल",
        "SCHOOL":    "स्कूल",
    }

    ent = _resolve_entity(msg, ENTITY_MAP)
    tgt = _resolve_location(msg, TARGET_MAP)
    action = msg.action.value if msg.action.code != 0 else ""

    if action == "SEND_TEAM":
        parts = ["तुरंत"]
        if tgt:
            parts.append(f"{tgt} में")
        if qty:
            parts.append(str(qty))
            
        cond = msg.condition.value if msg.condition.code != 0 else ""
        if cond:
            cond_str = msg.condition.source_phrase or cond
            parts.append(f"({cond_str})")
            
        if ent:
            parts.append(ent)
        parts.append("भेजो।")
        return " ".join(parts)

    elif action == "REQUEST_HELP":
        if tgt and ent:
            return f"{tgt} को {ent} की सहायता चाहिए।"
        elif ent:
            return f"तुरंत {ent} की सहायता चाहिए।"
        else:
            return "मदद की जरूरत है।"

    elif action == "EVACUATE":
        loc = tgt or "क्षेत्र"
        return f"{loc} को तुरंत खाली करें।"

    elif action == "ALERT":
        hazard = msg.hazard_text or ""
        loc = tgt or ""
        return f"चेतावनी: {hazard}{' — ' + loc if loc else ''}।"

    elif action == "MOVE":
        parts = []
        if ent:
            parts.append(ent)
        if qty:
            parts.append(f"({qty})")
        cs_fields = [f for f in msg.extra_fields if f.name == "CALLSIGN"]
        if cs_fields:
            parts.append(cs_fields[0].value)
        dir_fields = [f for f in msg.extra_fields if f.name == "DIRECTION"]
        direction = dir_fields[0].value if dir_fields else ""
        DIR_MAP_HI = {
            "NORTH": "उत्तर", "SOUTH": "दक्षिण", "EAST": "पूर्व", "WEST": "पश्चिम",
            "NORTHEAST": "उत्तर-पूर्व", "NORTHWEST": "उत्तर-पश्चिम",
            "SOUTHEAST": "दक्षिण-पूर्व", "SOUTHWEST": "दक्षिण-पश्चिम"
        }
        dir_hi = DIR_MAP_HI.get(direction.upper(), direction.lower())
        if dir_hi and tgt:
            parts.append(f"{tgt} की ओर {dir_hi} दिशा में आगे बढ़ रहा है।")
        elif dir_hi:
            parts.append(f"{dir_hi} दिशा में आगे बढ़ रहा है।")
        elif tgt:
            parts.append(f"{tgt} की ओर बढ़ रहा है।")
        else:
            parts.append("आगे बढ़ रहा है।")
        return " ".join(parts)

    # Partial / no action
    parts = []
    if msg.emotion.code != 0:
        parts.append(f"स्थिति: {msg.emotion.source_phrase or msg.emotion.value}")
    if msg.condition.code != 0:
        parts.append(f"हालत: {msg.condition.source_phrase or msg.condition.value}")
    if qty:
        parts.append(f"संख्या: {qty}")
    if tgt:
        parts.append(f"स्थान: {tgt}")
    if msg.hazard_text:
        parts.append(f"खतरा: {msg.hazard_text}")
    if msg.status_text:
        parts.append(f"स्थिति विवरण: {msg.status_text}")
    if msg.urgency.code != 0:
        parts.append(f"[{msg.urgency.value}]")
    if parts:
        return "। ".join(parts) + "।"
    return "[आंशिक संदेश]"


def _realize_tamil(msg: SemanticMessage, qty) -> str:
    ENTITY_MAP = {
        "RESCUE":     "மீட்புக் குழுவை",
        "MEDICAL":    "மருத்துவக் குழுவை",
        "AMBULANCE":  "ஆம்புலன்ஸ்",
        "FIRE_TEAM":  "தீயணைப்புக் குழுவை",
        "POLICE":     "காவல்துறையை",
    }
    TARGET_MAP = {
        "HUBBLI":    "ஹூப்ளிக்கு",
        "TOLANKERE": "தோலன்கெரேவுக்கு",
        "BRIDGE":    "பாலத்திற்கு",
        "HOSPITAL":  "மருத்துவமனைக்கு",
        "SCHOOL":    "பள்ளிக்கு",
        "SECTOR_4":  "நான்காம் பகுதிக்கு",
    }

    ent = _resolve_entity(msg, ENTITY_MAP)
    if msg.target.value == "PROPER_LOCATION" and msg.location_text:
        tgt = msg.location_text + "க்கு"
    else:
        tgt_raw = str(msg.target.value) if msg.target.code != 0 else ""
        tgt = TARGET_MAP.get(tgt_raw, tgt_raw.replace("_", " "))

    action = msg.action.value if msg.action.code != 0 else ""

    if action == "SEND_TEAM":
        parts = ["உடனடியாக"]
        if qty:
            parts.append(str(qty))
        if ent:
            parts.append(ent)
        if tgt:
            parts.append(tgt)
        parts.append("அனுப்பவும்.")
        return " ".join(parts)

    return _realize_english(msg, qty) + " (TA)"
