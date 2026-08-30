# translation_engine.py
"""
iTantra M3 Translation Engine (Target Language Realization)
Converts a SemanticMessage back into human-readable text.
"""

from semantic_schema import SemanticMessage

SUPPORTED_LANGUAGES = ["hi", "en", "mr", "ta", "te", "kn"]
LANGUAGE_NAMES = {
    "hi": "Hindi",
    "en": "English",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada"
}

def get_language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)

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

def _realize_english(msg: SemanticMessage, qty: int) -> str:
    action_str = str(msg.action.value).replace("_", " ")
    entity_str = str(msg.entity.value)
    target_str = str(msg.target.value).replace("_", " ")
    
    if msg.action.value == "SEND_TEAM":
        return f"Send {qty} {entity_str} team to {target_str} immediately."
    elif msg.action.value == "REQUEST_HELP":
        return f"{target_str} requesting {entity_str} support."
    elif msg.action.value == "EVACUATE":
        return f"Evacuate {target_str} immediately."
        
    return f"{action_str} {qty} {entity_str} at {target_str}."

def _realize_hindi(msg: SemanticMessage, qty: int) -> str:
    entity_map = {
        "RESCUE": "बचाव दल",
        "MEDICAL": "चिकित्सा दल",
        "POLICE": "पुलिस",
        "FIRE": "फायर ब्रिगेड",
        "SUPPLY": "आपूर्ति",
    }
    target_map = {
        "HUBBLI": "हब्बली",
        "TOLANKERE": "तोलनकेरे",
        "SECTOR_4": "सेक्टर चार",
    }
    
    ent = entity_map.get(msg.entity.value, msg.entity.value)
    tgt = target_map.get(msg.target.value, msg.target.value)
    
    if msg.action.value == "SEND_TEAM":
        return f"तुरंत {tgt} में {qty} {ent} भेजो।"
    elif msg.action.value == "REQUEST_HELP":
        return f"{tgt} को {ent} की सहायता चाहिए।"
    elif msg.action.value == "EVACUATE":
        return f"{tgt} को तुरंत खाली करें।"
        
    return f"{msg.action.value} {qty} {ent} at {tgt}."

def _realize_tamil(msg: SemanticMessage, qty: int) -> str:
    entity_map = {
        "RESCUE": "மீட்புக் குழுவை",
        "MEDICAL": "மருத்துவக் குழுவை",
    }
    target_map = {
        "HUBBLI": "ஹூப்ளிக்கு",
        "TOLANKERE": "தோலன்கெரேவுக்கு",
    }
    
    ent = entity_map.get(msg.entity.value, msg.entity.value)
    tgt = target_map.get(msg.target.value, msg.target.value)
    
    if msg.action.value == "SEND_TEAM":
        return f"உடனடியாக {qty} {ent} {tgt} அனுப்பவும்."
        
    return _realize_english(msg, qty) + " (TA)"
