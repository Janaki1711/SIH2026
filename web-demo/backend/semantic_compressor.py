"""
semantic_compressor.py — 3-Tier Semantic Compressor & Decompressor

Implements:
- Tier 1: Semantic Macro (6–8 bytes)
- Tier 2: Structured Frame (18–22 bytes)
- Tier 3: Fallback Payload (35–38 bytes)
"""

import struct
from typing import Union
from semantic_codebook import ActionCode, UrgencyCode, HazardCode, GeoID, CompressionTier
from tinyml_agent import SemanticResult, LocationEntity

def compress_tier1(res: SemanticResult) -> bytes:
    """Tier 1: 6 bytes payload."""
    b0 = int(CompressionTier.TIER_1_MACRO.value) | (0x80 if res.is_negated else 0x00)
    b1 = ((int(res.intent.value) & 0x0F) << 4) | (int(res.urgency.value) & 0x0F)
    b2 = ((int(res.action.value) & 0x0F) << 4) | (int(res.hazard.value) & 0x0F)
    b3 = min(res.person_count, 255) & 0xFF
    gid = int(res.location.geo_id)
    b4 = (gid >> 8) & 0xFF
    b5 = gid & 0xFF
    return struct.pack("!BBBBBB", b0, b1, b2, b3, b4, b5)

def decompress_tier1(data: bytes) -> SemanticResult:
    if len(data) < 6:
        raise ValueError("Tier 1 payload must be at least 6 bytes")
    b0, b1, b2, b3, b4, b5 = struct.unpack("!BBBBBB", data[:6])
    is_negated = (b0 & 0x80) != 0
    intent = ActionCode((b1 >> 4) & 0x0F)
    urgency = UrgencyCode(b1 & 0x0F)
    action = ActionCode((b2 >> 4) & 0x0F)
    hazard = HazardCode(b2 & 0x0F)
    person_count = b3
    gid = (b4 << 8) | b5

    from semantic_codebook import GEOID_TO_CANONICAL
    canonical = GEOID_TO_CANONICAL.get(gid, "Unknown Location")

    return SemanticResult(
        original_text="",
        intent=intent,
        action=action,
        hazard=hazard,
        person_count=person_count,
        urgency=urgency,
        location=LocationEntity(canonical, gid, 0.95),
        compression_tier=CompressionTier.TIER_1_MACRO,
        confidence=0.95,
        is_negated=is_negated
    )

def compress_tier2(res: SemanticResult) -> bytes:
    """Tier 2: 18 bytes payload."""
    b0 = int(CompressionTier.TIER_2_STRUCTURED.value) | (0x80 if res.is_negated else 0x00)
    b1 = int(res.intent.value) & 0xFF
    b2 = int(res.action.value) & 0xFF
    b3 = int(res.hazard.value) & 0xFF
    b4 = int(res.urgency.value) & 0xFF
    count16 = min(res.person_count, 65535)
    gid = int(res.location.geo_id)
    conf_byte = min(max(int(res.confidence * 100), 0), 100)

    lang = res.detected_language or "en"
    l0 = ord(lang[0]) if len(lang) > 0 else ord('e')
    l1 = ord(lang[1]) if len(lang) > 1 else ord('n')

    sub_flags = (1 if res.is_negated else 0) | ((len(res.extracted_entities) & 0x7FFF) << 1)
    ctx_flags = 0

    return struct.pack("!BBBBBHHBBBHI", b0, b1, b2, b3, b4, count16, gid, conf_byte, l0, l1, sub_flags, ctx_flags)

def decompress_tier2(data: bytes) -> SemanticResult:
    if len(data) < 18:
        raise ValueError("Tier 2 payload must be at least 18 bytes")
    b0, b1, b2, b3, b4, count16, gid, conf_byte, l0, l1, sub_flags, ctx_flags = struct.unpack("!BBBBBHHBBBHI", data[:18])
    is_negated = ((b0 & 0x80) != 0) or ((sub_flags & 0x01) != 0)

    intent = ActionCode(b1) if b1 in ActionCode._value2member_map_ else ActionCode.UNKNOWN
    action = ActionCode(b2) if b2 in ActionCode._value2member_map_ else ActionCode.UNKNOWN
    hazard = HazardCode(b3) if b3 in HazardCode._value2member_map_ else HazardCode.NONE
    urgency = UrgencyCode(b4) if b4 in UrgencyCode._value2member_map_ else UrgencyCode.ROUTINE

    lang = chr(l0) + chr(l1)
    from semantic_codebook import GEOID_TO_CANONICAL
    canonical = GEOID_TO_CANONICAL.get(gid, "Unknown Location")

    return SemanticResult(
        original_text="",
        detected_language=lang,
        intent=intent,
        action=action,
        hazard=hazard,
        person_count=count16,
        urgency=urgency,
        location=LocationEntity(canonical, gid, 0.95),
        compression_tier=CompressionTier.TIER_2_STRUCTURED,
        confidence=conf_byte / 100.0,
        is_negated=is_negated
    )

def compress_tier3(res: SemanticResult) -> bytes:
    """Tier 3: Dynamic bounded payload (3 + len <= 27 bytes)."""
    b0 = int(CompressionTier.TIER_3_FALLBACK.value)
    text_bytes = res.original_text.encode('utf-8')
    payload_cap = 24
    payload = text_bytes[:payload_cap]
    raw_len = len(payload)
    mode = 0x01
    return struct.pack("!BBB", b0, raw_len, mode) + payload

def decompress_tier3(data: bytes) -> SemanticResult:
    if len(data) < 3:
        raise ValueError("Tier 3 payload must be at least 3 bytes")
    b0, raw_len, mode = struct.unpack("!BBB", data[:3])
    actual_len = min(raw_len, len(data) - 3)
    text = data[3:3 + actual_len].decode('utf-8', errors='replace')
    return SemanticResult(
        original_text=text,
        is_fallback=True,
        fallback_reason="Decoded from Tier 3 fallback payload",
        compression_tier=CompressionTier.TIER_3_FALLBACK,
        confidence=0.50
    )

def compress(res: SemanticResult) -> bytes:
    if res.compression_tier == CompressionTier.TIER_1_MACRO:
        return compress_tier1(res)
    elif res.compression_tier == CompressionTier.TIER_2_STRUCTURED:
        return compress_tier2(res)
    else:
        return compress_tier3(res)

def decompress(data: bytes) -> SemanticResult:
    if not data:
        raise ValueError("Cannot decompress empty byte sequence")
    header = data[0]
    if header == int(CompressionTier.TIER_1_MACRO.value):
        return decompress_tier1(data)
    elif header == int(CompressionTier.TIER_2_STRUCTURED.value):
        return decompress_tier2(data)
    elif header == int(CompressionTier.TIER_3_FALLBACK.value):
        return decompress_tier3(data)
    else:
        return decompress_tier3(data)
