"""
packet_framer.py — Protobuf Binary Framer & CRC16-CCITT Engine
Zero-dependency resilient implementation:
Uses Google Protobuf when available, with automatic binary varint fallback.
"""

import sys
import os
import time
import struct
from typing import Tuple, Optional

# Ensure build and current directories are in sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.abspath(os.path.join(_THIS_DIR, '..', '..', 'build'))
for p in [_THIS_DIR, _BUILD_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

MAGIC_HEADER = 0x41475931  # "AGY1"

# Check if real google.protobuf is importable
_USE_REAL_PROTO = False
try:
    import google.protobuf
    import packet_schema_pb2 as pb
    _USE_REAL_PROTO = True
except Exception:
    _USE_REAL_PROTO = False


def calculate_crc16(data: bytes) -> int:
    """CRC16-CCITT (poly 0x1021, init 0xFFFF)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


# ─────────────────────────────────────────────────────────────────────────────
# Resilient VoicePacket Class (used if google.protobuf is not installed)
# ─────────────────────────────────────────────────────────────────────────────
class FallbackVoicePacket:
    def __init__(self):
        self.magic_header = MAGIC_HEADER
        self.sequence_number = 0
        self.timestamp_ms = 0
        self.priority = 0
        self.source_callsign = ""
        self.source_language = ""
        self.compressed_payload = b""
        self.prosody_vector = b""
        self.crc16_checksum = 0

    def CopyFrom(self, other):
        self.magic_header = other.magic_header
        self.sequence_number = other.sequence_number
        self.timestamp_ms = other.timestamp_ms
        self.priority = other.priority
        self.source_callsign = other.source_callsign
        self.source_language = other.source_language
        self.compressed_payload = other.compressed_payload
        self.prosody_vector = other.prosody_vector
        self.crc16_checksum = other.crc16_checksum

    def SerializeToString(self) -> bytes:
        def _encode_varint(v: int) -> bytes:
            res = []
            while True:
                bits = v & 0x7F
                v >>= 7
                if v: res.append(bits | 0x80)
                else: res.append(bits); break
            return bytes(res)

        def _field_varint(num: int, val: int) -> bytes:
            return _encode_varint((num << 3) | 0) + _encode_varint(val)

        def _field_bytes(num: int, b_val: bytes) -> bytes:
            return _encode_varint((num << 3) | 2) + _encode_varint(len(b_val)) + b_val

        out = b""
        out += _field_varint(1, self.magic_header)
        out += _field_varint(2, self.sequence_number)
        out += _field_varint(3, self.timestamp_ms)
        out += _field_varint(4, self.priority)
        if self.source_callsign:
            out += _field_bytes(5, self.source_callsign.encode("utf-8"))
        if self.source_language:
            out += _field_bytes(6, self.source_language.encode("utf-8"))
        if self.compressed_payload:
            out += _field_bytes(7, self.compressed_payload)
        if self.prosody_vector:
            out += _field_bytes(8, self.prosody_vector)
        out += _field_varint(9, self.crc16_checksum)
        return out

    def ParseFromString(self, data: bytes) -> bool:
        def _decode_varint(b: bytes, pos: int):
            res = 0; shift = 0
            while True:
                if pos >= len(b): raise ValueError("EOF")
                byte = b[pos]; pos += 1
                res |= (byte & 0x7F) << shift
                if not (byte & 0x80): break
                shift += 7
            return res, pos

        pos = 0
        try:
            while pos < len(data):
                tag, pos = _decode_varint(data, pos)
                field_num = tag >> 3
                wire_type = tag & 0x07
                if wire_type == 0:
                    val, pos = _decode_varint(data, pos)
                    if field_num == 1: self.magic_header = val
                    elif field_num == 2: self.sequence_number = val
                    elif field_num == 3: self.timestamp_ms = val
                    elif field_num == 4: self.priority = val
                    elif field_num == 9: self.crc16_checksum = val
                elif wire_type == 2:
                    length, pos = _decode_varint(data, pos)
                    chunk = data[pos:pos+length]
                    pos += length
                    if field_num == 5: self.source_callsign = chunk.decode("utf-8", errors="replace")
                    elif field_num == 6: self.source_language = chunk.decode("utf-8", errors="replace")
                    elif field_num == 7: self.compressed_payload = chunk
                    elif field_num == 8: self.prosody_vector = chunk
                else:
                    break
            return True
        except Exception:
            return False


COMPACT_MAGIC = 0x53  # 'S'

LANG_TO_CODE = {
    "en": 0, "hi": 1, "ta": 2, "kn": 3, "mr": 4,
    "te": 5, "gu": 6, "ml": 7, "or": 8, "bn": 9
}
CODE_TO_LANG = {v: k for k, v in LANG_TO_CODE.items()}

MAX_FRAME_SIZE = 38
UNFRAGMENTED_MAX_SIZE = 64
MAX_FRAGMENT_PAYLOAD = 27
FLAG_FRAGMENTED = 0x80

def callsign_to_id(callsign: str) -> int:
    h = 0x5A5A
    for c in callsign:
        h = ((h * 31) + ord(c)) & 0xFFFF
    return h

def id_to_callsign(cid: int) -> str:
    if cid == callsign_to_id("RESCUE_01"): return "RESCUE_01"
    if cid == callsign_to_id("CMD_ALPHA"): return "CMD_ALPHA"
    if cid == callsign_to_id("BASE_CAMP"): return "BASE_CAMP"
    return f"STATION_{cid}"


def _create_packet():
    if _USE_REAL_PROTO:
        return pb.VoicePacket()
    return FallbackVoicePacket()


def frame_payload(
    payload: bytes,
    source_language: str = "en",
    callsign: str = "CMD_ALPHA",
    sequence: int = 1,
    priority: int = 0,
    prosody_vector: Optional[bytes] = None
) -> List[bytes]:
    if not payload:
        raise ValueError("payload cannot be empty")

    has_prosody = bool(prosody_vector and any(b != 0 for b in prosody_vector))
    lang_code = LANG_TO_CODE.get(source_language.lower(), 15)
    prio = min(priority, 2) & 0x03
    seq16 = sequence & 0xFFFF
    cid16 = callsign_to_id(callsign)

    prosody_len = 16 if (has_prosody and prosody_vector) else 0
    unfragmented_total = 1 + 1 + 2 + 2 + 1 + len(payload) + prosody_len + 2

    # Case 1: Unfragmented single frame
    if unfragmented_total <= UNFRAGMENTED_MAX_SIZE:
        flags = (prio << 5) | (0x10 if has_prosody else 0x00) | (lang_code & 0x0F)
        payload_len = min(len(payload), 255)
        header = struct.pack("!BBHHB", COMPACT_MAGIC, flags, seq16, cid16, payload_len)
        body = header + payload[:payload_len]
        if has_prosody:
            body += prosody_vector[:16].ljust(16, b'\x00')
        crc = calculate_crc16(body)
        frame = body + struct.pack("!H", crc)
        return [frame]

    # Case 2: Fragmented into multiple <=38B frames (chunk <= 27B)
    total_bytes = len(payload)
    num_fragments = (total_bytes + MAX_FRAGMENT_PAYLOAD - 1) // MAX_FRAGMENT_PAYLOAD
    if num_fragments > 255:
        raise ValueError("Payload exceeds 255 fragments")

    frames = []
    flags = FLAG_FRAGMENTED | (prio << 5) | (lang_code & 0x0F)

    for i in range(num_fragments):
        start = i * MAX_FRAGMENT_PAYLOAD
        chunk = payload[start:start + MAX_FRAGMENT_PAYLOAD]
        chunk_len = len(chunk)

        # Header: Magic(1) + Flags(1) + Seq(2) + Cid(2) + FragIdx(1) + TotalFrags(1) + ChunkLen(1) = 9 bytes
        header = struct.pack("!BBHHBBB", COMPACT_MAGIC, flags, seq16, cid16, i, num_fragments, chunk_len)
        body = header + chunk
        crc = calculate_crc16(body)
        frame = body + struct.pack("!H", crc)
        assert len(frame) <= MAX_FRAME_SIZE, f"Fragment frame size {len(frame)} exceeds 38B!"
        frames.append(frame)

    return frames


def frame_packet(
    compressed_payload: bytes,
    source_language: str = "en",
    callsign: str = "CMD_ALPHA",
    sequence: int = 1,
    priority: int = 0,
    prosody_vector: Optional[bytes] = None
) -> bytes:
    frames = frame_payload(compressed_payload, source_language, callsign, sequence, priority, prosody_vector)
    return frames[0] if frames else b""


def parse_and_validate_frame(wire_bytes: bytes):
    if not wire_bytes:
        raise ValueError("Received empty wire bytes")

    # Mode 1: Compact Binary Frame (0x53)
    if wire_bytes[0] == COMPACT_MAGIC and len(wire_bytes) >= 9:
        n = len(wire_bytes)
        received_crc = (wire_bytes[-2] << 8) | wire_bytes[-1]
        expected_crc = calculate_crc16(wire_bytes[:-2])

        if received_crc != expected_crc:
            raise ValueError(f"CRC16 mismatch: received 0x{received_crc:04X}, calculated 0x{expected_crc:04X}")

        flags = wire_bytes[1]
        is_fragmented = bool(flags & FLAG_FRAGMENTED)
        prio = (flags >> 5) & 0x03
        has_prosody = not is_fragmented and bool(flags & 0x10)
        lang_code = flags & 0x0F

        seq, cid = struct.unpack("!HH", wire_bytes[2:6])

        packet = _create_packet()
        packet.magic_header = MAGIC_HEADER
        packet.sequence_number = seq
        packet.priority = prio
        packet.source_language = CODE_TO_LANG.get(lang_code, "en")
        packet.source_callsign = id_to_callsign(cid)
        packet.crc16_checksum = received_crc

        if is_fragmented:
            if n < 11:
                raise ValueError("Fragmented frame too short")
            frag_idx, total_frags, payload_len = struct.unpack("!BBB", wire_bytes[6:9])
            if 9 + payload_len > n - 2:
                raise ValueError("Invalid fragment payload length")
            payload = wire_bytes[9:9 + payload_len]
            packet.compressed_payload = payload
        else:
            payload_len = wire_bytes[6]
            if 7 + payload_len > n - 2:
                raise ValueError("Invalid payload length in compact frame")
            payload = wire_bytes[7:7 + payload_len]
            prosody = b""
            if has_prosody and (n - 2 > 7 + payload_len):
                prosody = wire_bytes[7 + payload_len:n - 2]
            packet.compressed_payload = payload
            packet.prosody_vector = prosody

        return packet

    # Mode 2: Protobuf Fallback
    packet = _create_packet()
    if not packet.ParseFromString(wire_bytes):
        raise ValueError("Protobuf deserialization failed")

    if packet.magic_header != MAGIC_HEADER:
        raise ValueError(f"Invalid magic header 0x{packet.magic_header:08X} (expected 0x{MAGIC_HEADER:08X})")

    received_crc = packet.crc16_checksum
    verify_packet = _create_packet()
    verify_packet.CopyFrom(packet)
    verify_packet.crc16_checksum = 0
    verify_bytes = verify_packet.SerializeToString()
    expected_crc = calculate_crc16(verify_bytes)

    if received_crc != expected_crc:
        raise ValueError(f"CRC16 mismatch: received 0x{received_crc:04X}, calculated 0x{expected_crc:04X}")

    return packet


def validate_frame(wire_bytes: bytes) -> bool:
    try:
        parse_and_validate_frame(wire_bytes)
        return True
    except Exception:
        return False


class MessageReassembler:
    def __init__(self):
        self.sessions = {}

    def process_frame(self, frame_bytes: bytes):
        if not frame_bytes:
            return {"is_complete": False}

        try:
            pkt = parse_and_validate_frame(frame_bytes)
        except Exception:
            return {"is_complete": False}

        if frame_bytes[0] == COMPACT_MAGIC and (frame_bytes[1] & FLAG_FRAGMENTED):
            if len(frame_bytes) < 11:
                return {"is_complete": False}

            seq, cid = struct.unpack("!HH", frame_bytes[2:6])
            frag_idx, total_frags, payload_len = struct.unpack("!BBB", frame_bytes[6:9])
            chunk = frame_bytes[9:9 + payload_len]

            session_key = f"{seq}-{cid}"
            if session_key not in self.sessions:
                self.sessions[session_key] = {
                    "seq": seq,
                    "cid": cid,
                    "flags": frame_bytes[1],
                    "total_frags": total_frags,
                    "fragments": {},
                    "last_update": time.time()
                }

            session = self.sessions[session_key]
            session["fragments"][frag_idx] = chunk
            session["last_update"] = time.time()

            if len(session["fragments"]) == total_frags:
                full_payload = bytearray()
                for i in range(total_frags):
                    if i not in session["fragments"]:
                        return {"is_complete": False}
                    full_payload.extend(session["fragments"][i])

                pkt.compressed_payload = bytes(full_payload)
                del self.sessions[session_key]
                return {
                    "is_complete": True,
                    "packet": pkt,
                    "received_fragments": total_frags,
                    "total_fragments": total_frags
                }

            return {
                "is_complete": False,
                "received_fragments": len(session["fragments"]),
                "total_fragments": total_frags
            }

        return {
            "is_complete": True,
            "packet": pkt,
            "received_fragments": 1,
            "total_fragments": 1
        }

