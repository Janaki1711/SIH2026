# semantic_schema.py
"""
iTantra M3 Semantic Schema Codebook
Defines the deterministic mappings for tactical semantic concepts.
"""

from enum import IntEnum
from typing import Dict, Any, List, Optional

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
    ALERT = 13
    SECURE = 14
    RESPOND = 15

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
    AMBULANCE = 8
    HELICOPTER = 9
    ENGINEER = 10
    FIRE_TEAM = 11
    DISASTER = 12

class Target(IntEnum):
    UNKNOWN = 0
    HUBBLI = 1
    TOLANKERE = 2
    BASE = 3
    SECTOR_1 = 4
    SECTOR_2 = 5
    SECTOR_3 = 6
    SECTOR_4 = 7
    SECTOR_5 = 8
    BRIDGE = 9
    HOSPITAL = 10
    SCHOOL = 11
    # PROPER_LOCATION = 15 means a proper noun location preserved as text (code 15)
    PROPER_LOCATION = 15

class Condition(IntEnum):
    UNKNOWN = 0
    TRAPPED = 1
    INJURED = 2
    SAFE = 3
    MISSING = 4
    UNCONSCIOUS = 5
    CRITICAL = 6
    STABLE = 7
    DECEASED = 8
    EVACUATED = 9
    EXPOSED = 10

class Emotion(IntEnum):
    UNKNOWN = 0
    DISTRESS = 1
    CALM = 2
    PANIC = 3
    FEAR = 4
    ANGER = 5
    CONFUSION = 6
    RELIEF = 7

class SemanticField:
    def __init__(self, name: str, value: Any, code: int, source_phrase: str = "", encoded_hex: str = "", confidence: float = 1.0, source_type: str = "RULE"):
        self.name = name
        self.value = value
        self.code = code
        self.source_phrase = source_phrase
        self.encoded_hex = encoded_hex
        self.confidence = confidence  # 0.0–1.0; <0.7 = low confidence, preserved as text
        self.source_type = source_type  # "RULE", "TINYML", "HYBRID"

    def to_dict(self):
        d = {
            "field": self.name,
            "value": self.value,
            "code": self.code,
            "source_phrase": self.source_phrase,
            "encoded_value": self.encoded_hex,
            "source": self.source_type,
        }
        if self.confidence < 1.0:
            d["confidence"] = round(self.confidence, 2)
        return d

class SemanticMessage:
    def __init__(self, fallback_text: str = "", fallback_reason: str = "", matched_fields: List[str] = None, failed_fields: List[str] = None):
        self.action    = SemanticField("ACTION",    "UNKNOWN", 0)
        self.urgency   = SemanticField("URGENCY",   "ROUTINE", 0)
        self.entity    = SemanticField("ENTITY",    "UNKNOWN", 0)
        self.target    = SemanticField("TARGET",    "UNKNOWN", 0)
        self.condition = SemanticField("CONDITION", "UNKNOWN", 0)
        self.emotion   = SemanticField("EMOTION",   "UNKNOWN", 0)
        self.quantity  = SemanticField("QUANTITY",  0, 0)

        # Extended fields (stored as plain text, not encoded in the 4-byte packet)
        self.location_text: Optional[str] = None   # proper noun location not in Target enum
        self.hazard_text:   Optional[str] = None   # detected hazard/threat description
        self.resource_text: Optional[str] = None   # resource required/available
        self.status_text:   Optional[str] = None   # detected communication/event status
        self.extra_fields:  List[SemanticField] = []  # additional recognized semantic fields

        self.location_source: str = "RULE"
        self.hazard_source: str = "RULE"
        self.resource_source: str = "RULE"
        self.status_source: str = "RULE"

        self.fallback_text   = fallback_text
        self.is_fallback     = bool(fallback_text)
        self.fallback_reason = fallback_reason
        self.matched_fields  = matched_fields or []
        self.failed_fields   = failed_fields or []

    def fields_list(self):
        base = [self.action, self.entity, self.quantity, self.target, self.urgency, self.condition, self.emotion]
        # Inject extra recognised text fields as SemanticField-like objects for UI display
        extras = list(self.extra_fields)
        if self.location_text and self.target.code in (0, Target.PROPER_LOCATION):
            extras.append(SemanticField("LOCATION", self.location_text, Target.PROPER_LOCATION, self.location_text, "PROPER_NOUN", 0.95, self.location_source))
        if self.hazard_text:
            extras.append(SemanticField("HAZARD", self.hazard_text, 0, self.hazard_text, "TEXT", 0.90, self.hazard_source))
        if self.resource_text:
            extras.append(SemanticField("RESOURCE", self.resource_text, 0, self.resource_text, "TEXT", 0.90, self.resource_source))
        if self.status_text:
            extras.append(SemanticField("STATUS", self.status_text, 0, self.status_text, "TEXT", 0.90, self.status_source))
        return base + extras

    def to_dict(self) -> Dict[str, Any]:
        # Filter out UNKNOWN/zero fields but always include extra text fields
        base_active = [f.to_dict() for f in [self.action, self.entity, self.quantity, self.target, self.urgency, self.condition, self.emotion]
                       if f.value != "UNKNOWN" and f.value != 0]
        extra_active = [f.to_dict() for f in self.extra_fields]
        # Proper-noun location
        if self.location_text and self.target.code in (0, Target.PROPER_LOCATION):
            extra_active.append(SemanticField("LOCATION", self.location_text, Target.PROPER_LOCATION, self.location_text, "PROPER_NOUN", 0.95, self.location_source).to_dict())
        if self.hazard_text:
            extra_active.append(SemanticField("HAZARD", self.hazard_text, 0, self.hazard_text, "TEXT", 0.90, self.hazard_source).to_dict())
        if self.resource_text:
            extra_active.append(SemanticField("RESOURCE", self.resource_text, 0, self.resource_text, "TEXT", 0.90, self.resource_source).to_dict())
        if self.status_text:
            extra_active.append(SemanticField("STATUS", self.status_text, 0, self.status_text, "TEXT", 0.90, self.status_source).to_dict())

        return {
            "fields": base_active + extra_active,
            "is_fallback": self.is_fallback,
            "fallback_text": self.fallback_text,
            "fallback_reason": self.fallback_reason,
            "matched_fields": self.matched_fields,
            "failed_fields": self.failed_fields,
        }

def get_codebook() -> Dict[str, Any]:
    """Returns the codebook dictionaries for the frontend."""
    return {
        "ACTION":    {e.name: e.value for e in Action},
        "URGENCY":   {e.name: e.value for e in Urgency},
        "ENTITY":    {e.name: e.value for e in Entity},
        "TARGET":    {e.name: e.value for e in Target},
        "CONDITION": {e.name: e.value for e in Condition},
        "EMOTION":   {e.name: e.value for e in Emotion},
    }
