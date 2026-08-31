# semantic_compressor.py
"""
iTantra M3 Semantic Compressor
Encodes SemanticMessage into an ultra-compact byte sequence.

BIT LAYOUT (preserved, 4 bytes total):
  Byte 0: Action (4 bits), Urgency (3 bits), IsFallback (1 bit)
  Byte 1: Entity (4 bits), Target (4 bits)
  Byte 2: Quantity (8 bits)
  Byte 3: Condition (4 bits), Emotion (4 bits)

EXTENDED LAYOUT (for PROPER_LOCATION / partial messages):
  When target code == Target.PROPER_LOCATION (15), an additional
  zlib-compressed UTF-8 suffix carries the proper noun text.
  The receiver can reconstruct the LOCATION field from this.

  Byte 0:  header — 0x02 = semantic-with-location-suffix
  Bytes 1–4: the 4 core semantic bytes (as above, target nibble = 0x0F)
  Bytes 5+:  zlib-compressed location_text UTF-8
"""

import struct
import zlib
import json
from semantic_schema import SemanticMessage, Action, Urgency, Entity, Target, Condition, Emotion, SemanticField

_HEADER_FALLBACK         = 0x01   # original: full text fallback
_HEADER_SEMANTIC         = 0x00   # original: clean 4-byte semantic (encoded in MSB of b0)
_HEADER_SEMANTIC_WITH_LOC = 0x02  # new: 4-byte semantic + location suffix


def compress(msg: SemanticMessage) -> bytes:
    if msg.is_fallback:
        header = 0x01
        text_bytes = msg.fallback_text.encode('utf-8')
        compressed_text = zlib.compress(text_bytes, level=9)
        return struct.pack("!B", header) + compressed_text

    # Calculate core 4 bytes
    b0 = ((msg.action.code & 0x0F) << 4) | ((msg.urgency.code & 0x07) << 1) | 0x00
    b1 = ((msg.entity.code & 0x0F) << 4) | (msg.target.code & 0x0F)
    b2 = min(msg.quantity.code, 255) & 0xFF
    b3 = ((msg.condition.code & 0x0F) << 4) | (msg.emotion.code & 0x0F)

    # Store encoded hex representations back onto the msg object for UI inspection
    msg.action.encoded_hex    = f"0x{b0 & 0xF0:02X}"
    msg.urgency.encoded_hex   = f"0x{b0 & 0x0E:02X}"
    msg.entity.encoded_hex    = f"0x{b1 & 0xF0:02X}"
    msg.target.encoded_hex    = f"0x{b1 & 0x0F:02X}"
    msg.quantity.encoded_hex  = f"0x{b2:02X}"
    msg.condition.encoded_hex = f"0x{b3 & 0xF0:02X}"
    msg.emotion.encoded_hex   = f"0x{b3 & 0x0F:02X}"

    # If extended fields are present, append them as a compressed JSON suffix
    extensions = {}
    if msg.location_text and msg.target.code == Target.PROPER_LOCATION.value:
        extensions["loc"] = msg.location_text
    if msg.hazard_text:
        extensions["haz"] = msg.hazard_text
    if msg.resource_text:
        extensions["res"] = msg.resource_text
    if msg.status_text:
        extensions["sts"] = msg.status_text
    if msg.extra_fields:
        extensions["ext"] = [(f.name, str(f.value), f.source_phrase) for f in msg.extra_fields]

    if extensions:
        ext_bytes = json.dumps(extensions).encode('utf-8')
        compressed_ext = zlib.compress(ext_bytes, level=9)
        # Use a special 1-byte header so the receiver knows there's a JSON extension suffix
        header_byte = struct.pack("!B", _HEADER_SEMANTIC_WITH_LOC)
        return header_byte + struct.pack("!BBBB", b0, b1, b2, b3) + compressed_ext

    return struct.pack("!BBBB", b0, b1, b2, b3)


def decompress(data: bytes) -> SemanticMessage:
    if not data:
        return SemanticMessage()

    b0 = data[0]

    # --- Check for new extended header byte ---
    if b0 == _HEADER_SEMANTIC_WITH_LOC:
        # 1 header byte + 4 semantic bytes + compressed location
        if len(data) < 5:
            return SemanticMessage(fallback_text="[TRUNCATED EXTENDED PACKET]")
        real_b0 = data[1]
        b1 = data[2]
        b2 = data[3]
        b3 = data[4]
        location_suffix = data[5:]
        extensions = {}
        if location_suffix:
            try:
                ext_str = zlib.decompress(location_suffix).decode('utf-8')
                if ext_str.startswith('{'):
                    extensions = json.loads(ext_str)
                else:
                    extensions["loc"] = ext_str  # backward compatibility
            except Exception:
                pass
        return _decode_semantic_bytes(real_b0, b1, b2, b3, extensions)

    # --- Original fallback packet ---
    is_fallback = (b0 & 0x01) == 0x01
    if is_fallback:
        compressed_text = data[1:]
        try:
            text = zlib.decompress(compressed_text).decode('utf-8')
        except Exception:
            text = "[CORRUPTED DECOMPRESSION]"
        return SemanticMessage(fallback_text=text)

    # --- Original 4-byte semantic packet ---
    if len(data) < 4:
        return SemanticMessage(fallback_text="[TRUNCATED PACKET]")

    b1 = data[1]
    b2 = data[2]
    b3 = data[3]
    return _decode_semantic_bytes(b0, b1, b2, b3, None)


def _decode_semantic_bytes(b0: int, b1: int, b2: int, b3: int, extensions: dict = None) -> SemanticMessage:
    a_val  = (b0 >> 4) & 0x0F
    u_val  = (b0 >> 1) & 0x07
    e_val  = (b1 >> 4) & 0x0F
    t_val  = b1 & 0x0F
    q_val  = b2
    c_val  = (b3 >> 4) & 0x0F
    em_val = b3 & 0x0F

    try:
        msg = SemanticMessage()
        msg.action    = SemanticField("ACTION",    Action(a_val).name,    a_val)
        msg.urgency   = SemanticField("URGENCY",   Urgency(u_val).name,   u_val)
        msg.entity    = SemanticField("ENTITY",    Entity(e_val).name,    e_val)
        msg.target    = SemanticField("TARGET",    Target(t_val).name,    t_val)
        msg.quantity  = SemanticField("QUANTITY",  q_val,                  q_val)
        msg.condition = SemanticField("CONDITION", Condition(c_val).name,  c_val)
        msg.emotion   = SemanticField("EMOTION",   Emotion(em_val).name,   em_val)

        # Populate encoded_hex
        msg.action.encoded_hex    = f"0x{b0 & 0xF0:02X}"
        msg.urgency.encoded_hex   = f"0x{b0 & 0x0E:02X}"
        msg.entity.encoded_hex    = f"0x{b1 & 0xF0:02X}"
        msg.target.encoded_hex    = f"0x{b1 & 0x0F:02X}"
        msg.quantity.encoded_hex  = f"0x{b2:02X}"
        msg.condition.encoded_hex = f"0x{b3 & 0xF0:02X}"
        msg.emotion.encoded_hex   = f"0x{b3 & 0x0F:02X}"

        # Restore extended fields
        if extensions:
            if "loc" in extensions:
                msg.location_text = extensions["loc"]
            if "haz" in extensions:
                msg.hazard_text = extensions["haz"]
            if "res" in extensions:
                msg.resource_text = extensions["res"]
            if "sts" in extensions:
                msg.status_text = extensions["sts"]
            if "ext" in extensions:
                for item in extensions["ext"]:
                    if len(item) == 3:
                        name, val, src = item
                        msg.extra_fields.append(SemanticField(name, val, 0, src, "TEXT", 0.9))

        return msg
    except ValueError:
        return SemanticMessage(fallback_text="[INVALID SEMANTIC CODE]")
