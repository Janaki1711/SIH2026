"""
semantic_codebook.py — Centralized Semantic Codebook for iTantra M3

Defines exact numeric codes for intents, actions, hazards, urgencies,
and predefined landmark GeoIDs across the entire system.
"""

from enum import IntEnum
from typing import Dict, Any

class ActionCode(IntEnum):
    UNKNOWN          = 0x00
    RESCUE_REQUEST   = 0x01
    EVACUATE         = 0x02
    MEDICAL          = 0x03
    SUPPLIES         = 0x04
    SEARCH           = 0x05
    REPORT           = 0x06
    FLOOD            = 0x07
    BOAT             = 0x08
    FIRE             = 0x09
    SOS              = 0x0A
    PERSON_MISSING   = 0x0B
    LOCATION_REPORT  = 0x0C
    ALERT            = 0x0D
    SECURE           = 0x0E
    MOVE             = 0x0F
    SEND_TEAM        = 0x10
    REQUEST_HELP     = 0x11
    CANCEL           = 0x12
    HOLD             = 0x13
    RESPOND          = 0x14

class UrgencyCode(IntEnum):
    ROUTINE      = 0x00
    TACTICAL     = 0x01
    CRITICAL_SOS = 0x03

class PriorityLevel(IntEnum):
    ROUTINE           = 0
    TACTICAL          = 1
    LIFE_SAFETY_ALERT = 2

class HazardCode(IntEnum):
    NONE              = 0x00
    FLOOD             = 0x01
    FIRE              = 0x02
    EARTHQUAKE        = 0x03
    LANDSLIDE         = 0x04
    BUILDING_COLLAPSE = 0x05
    EXPLOSION         = 0x06
    GAS_LEAK          = 0x07
    STORM             = 0x08
    GENERAL_DANGER    = 0x09

class GeoID(IntEnum):
    UNKNOWN                 = 0x0000
    TOLANKERE               = 0x4F2A
    HUBBLI                  = 0x4F2B
    BASE                    = 0x4F01
    SECTOR_1                = 0x4E01
    SECTOR_2                = 0x4E02
    SECTOR_3                = 0x4E03
    SECTOR_4                = 0x4E04
    SECTOR_5                = 0x4E05
    BRIDGE                  = 0x4E10
    HOSPITAL                = 0x4E11
    SCHOOL                  = 0x4E12
    PROPER_LOCATION_DYNAMIC = 0x4FFF

class CompressionTier(IntEnum):
    TIER_1_MACRO      = 1  # 6–8 bytes
    TIER_2_STRUCTURED = 2  # 18–22 bytes
    TIER_3_FALLBACK   = 3  # 35–38 bytes

GEOID_TO_CANONICAL = {
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

def get_codebook_dict() -> Dict[str, Any]:
    return {
        "ACTION": {e.name: int(e.value) for e in ActionCode},
        "URGENCY": {e.name: int(e.value) for e in UrgencyCode},
        "HAZARD": {e.name: int(e.value) for e in HazardCode},
        "GEOID": {e.name: f"0x{int(e.value):04X}" for e in GeoID},
        "TIER": {e.name: int(e.value) for e in CompressionTier},
    }
