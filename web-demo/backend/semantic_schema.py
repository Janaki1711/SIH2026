# semantic_schema.py
"""
iTantra M3 Semantic Schema Codebook
Defines the deterministic mappings for tactical semantic concepts.
"""

from enum import IntEnum
from typing import Dict, Any, List

class Action(IntEnum):
    UNKNOWN = 0
    SEND_TEAM = 1
    REQUEST_HELP = 2
    EVACUATE = 3
    REPORT = 4
    CANCEL = 5
    MOVE = 6
    HOLD = 7
    SEARCH = 8
    RESCUE = 9
    MEDICAL = 10
    FIRE = 11
    SUPPLY = 12

class Urgency(IntEnum):
    ROUTINE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Entity(IntEnum):
    UNKNOWN = 0
    RESCUE = 1
    MEDICAL = 2
    POLICE = 3
    FIRE = 4
    SUPPLY = 5
    TROOP = 6
    PERSONNEL = 7

class Target(IntEnum):
    UNKNOWN = 0
    HUBBLI = 1
    TOLANKERE = 2
    BASE = 3
    SECTOR_1 = 4
    SECTOR_2 = 5
    SECTOR_3 = 6
    SECTOR_4 = 7

class Condition(IntEnum):
    UNKNOWN = 0
    TRAPPED = 1
    INJURED = 2
    SAFE = 3
    MISSING = 4

class Emotion(IntEnum):
    UNKNOWN = 0
    DISTRESS = 1
    CALM = 2
    PANIC = 3

class SemanticField:
    def __init__(self, name: str, value: Any, code: int, source_phrase: str = "", encoded_hex: str = ""):
        self.name = name
        self.value = value
        self.code = code
        self.source_phrase = source_phrase
        self.encoded_hex = encoded_hex

    def to_dict(self):
        return {
            "field": self.name,
            "value": self.value,
            "code": self.code,
            "source_phrase": self.source_phrase,
            "encoded_value": self.encoded_hex
        }

class SemanticMessage:
    def __init__(self, fallback_text: str = "", fallback_reason: str = "", matched_fields: List[str] = None, failed_fields: List[str] = None):
        self.action = SemanticField("ACTION", "UNKNOWN", 0)
        self.urgency = SemanticField("URGENCY", "ROUTINE", 0)
        self.entity = SemanticField("ENTITY", "UNKNOWN", 0)
        self.target = SemanticField("TARGET", "UNKNOWN", 0)
        self.condition = SemanticField("CONDITION", "UNKNOWN", 0)
        self.emotion = SemanticField("EMOTION", "UNKNOWN", 0)
        self.quantity = SemanticField("QUANTITY", 0, 0)
        
        self.fallback_text = fallback_text
        self.is_fallback = bool(fallback_text)
        self.fallback_reason = fallback_reason
        self.matched_fields = matched_fields or []
        self.failed_fields = failed_fields or []

    def fields_list(self):
        return [self.action, self.entity, self.quantity, self.target, self.urgency, self.condition, self.emotion]

    def to_dict(self) -> Dict[str, Any]:
        # Filter out UNKNOWN fields dynamically for the UI visualization
        active_fields = [f.to_dict() for f in self.fields_list() if f.value != "UNKNOWN" and f.value != 0]
        
        # If action is SEND_TEAM but quantity is 0, we still want to show action, but maybe drop quantity? 
        # For simplicity, if quantity is 0 we drop it unless we want it shown. Let's just drop 0.
        
        return {
            "fields": active_fields,
            "is_fallback": self.is_fallback,
            "fallback_text": self.fallback_text,
            "fallback_reason": self.fallback_reason,
            "matched_fields": self.matched_fields,
            "failed_fields": self.failed_fields
        }

def get_codebook() -> Dict[str, Any]:
    """Returns the codebook dictionaries for the frontend."""
    return {
        "ACTION": {e.name: e.value for e in Action},
        "URGENCY": {e.name: e.value for e in Urgency},
        "ENTITY": {e.name: e.value for e in Entity},
        "TARGET": {e.name: e.value for e in Target},
        "CONDITION": {e.name: e.value for e in Condition},
        "EMOTION": {e.name: e.value for e in Emotion},
    }
