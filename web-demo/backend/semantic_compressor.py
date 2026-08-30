# semantic_compressor.py
"""
iTantra M3 Semantic Compressor
Encodes SemanticMessage into an ultra-compact byte sequence.
"""

import struct
import zlib
from semantic_schema import SemanticMessage, Action, Urgency, Entity, Target, Condition, Emotion, SemanticField

# NEW BIT LAYOUT (4 bytes total to accommodate Condition/Emotion)
# Byte 0: Action (4 bits), Urgency (3 bits), IsFallback (1 bit)
# Byte 1: Entity (4 bits), Target (4 bits)
# Byte 2: Quantity (8 bits)
# Byte 3: Condition (4 bits), Emotion (4 bits)

def compress(msg: SemanticMessage) -> bytes:
    if msg.is_fallback:
        header = 0x01
        text_bytes = msg.fallback_text.encode('utf-8')
        compressed_text = zlib.compress(text_bytes, level=9)
        return struct.pack("!B", header) + compressed_text
    
    # Calculate bytes
    b0 = ((msg.action.code & 0x0F) << 4) | ((msg.urgency.code & 0x07) << 1) | 0x00
    b1 = ((msg.entity.code & 0x0F) << 4) | (msg.target.code & 0x0F)
    b2 = msg.quantity.code & 0xFF
    b3 = ((msg.condition.code & 0x0F) << 4) | (msg.emotion.code & 0x0F)
    
    # Store encoded hex representations back onto the msg object for UI inspection
    msg.action.encoded_hex = f"0x{b0 & 0xF0:02X}"
    msg.urgency.encoded_hex = f"0x{b0 & 0x0E:02X}"
    msg.entity.encoded_hex = f"0x{b1 & 0xF0:02X}"
    msg.target.encoded_hex = f"0x{b1 & 0x0F:02X}"
    msg.quantity.encoded_hex = f"0x{b2:02X}"
    msg.condition.encoded_hex = f"0x{b3 & 0xF0:02X}"
    msg.emotion.encoded_hex = f"0x{b3 & 0x0F:02X}"

    return struct.pack("!BBBB", b0, b1, b2, b3)

def decompress(data: bytes) -> SemanticMessage:
    if not data:
        return SemanticMessage()
        
    b0 = data[0]
    is_fallback = (b0 & 0x01) == 0x01
    
    if is_fallback:
        compressed_text = data[1:]
        try:
            text = zlib.decompress(compressed_text).decode('utf-8')
        except Exception:
            text = "[CORRUPTED DECOMPRESSION]"
        return SemanticMessage(fallback_text=text)
        
    if len(data) < 4:
        return SemanticMessage(fallback_text="[TRUNCATED PACKET]")
        
    b1 = data[1]
    b2 = data[2]
    b3 = data[3]
    
    a_val = (b0 >> 4) & 0x0F
    u_val = (b0 >> 1) & 0x07
    e_val = (b1 >> 4) & 0x0F
    t_val = b1 & 0x0F
    q_val = b2
    c_val = (b3 >> 4) & 0x0F
    em_val = b3 & 0x0F
    
    try:
        msg = SemanticMessage()
        msg.action = SemanticField("ACTION", Action(a_val).name, a_val)
        msg.urgency = SemanticField("URGENCY", Urgency(u_val).name, u_val)
        msg.entity = SemanticField("ENTITY", Entity(e_val).name, e_val)
        msg.target = SemanticField("TARGET", Target(t_val).name, t_val)
        msg.quantity = SemanticField("QUANTITY", q_val, q_val)
        msg.condition = SemanticField("CONDITION", Condition(c_val).name, c_val)
        msg.emotion = SemanticField("EMOTION", Emotion(em_val).name, em_val)
        
        # Populate encoded_hex just like on compress
        msg.action.encoded_hex = f"0x{b0 & 0xF0:02X}"
        msg.urgency.encoded_hex = f"0x{b0 & 0x0E:02X}"
        msg.entity.encoded_hex = f"0x{b1 & 0xF0:02X}"
        msg.target.encoded_hex = f"0x{b1 & 0x0F:02X}"
        msg.quantity.encoded_hex = f"0x{b2:02X}"
        msg.condition.encoded_hex = f"0x{b3 & 0xF0:02X}"
        msg.emotion.encoded_hex = f"0x{b3 & 0x0F:02X}"

        return msg
    except ValueError:
        return SemanticMessage(fallback_text="[INVALID SEMANTIC CODE]")
