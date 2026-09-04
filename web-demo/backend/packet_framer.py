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


def _create_packet():
    if _USE_REAL_PROTO:
        return pb.VoicePacket()
    return FallbackVoicePacket()


def frame_packet(
    compressed_payload: bytes,
    source_language: str,
    callsign: str,
    sequence: int,
    priority: int,
    prosody_vector: Optional[bytes] = None
) -> bytes:
    if not compressed_payload:
        raise ValueError("compressed_payload cannot be empty")

    packet = _create_packet()
    packet.magic_header = MAGIC_HEADER
    packet.sequence_number = sequence
    packet.timestamp_ms = int(time.time() * 1000)
    packet.priority = priority if priority in (0, 1, 2) else 0
    packet.source_callsign = callsign or "CMD_ALPHA"
    packet.source_language = source_language or "en"
    packet.compressed_payload = compressed_payload

    if prosody_vector:
        if len(prosody_vector) != 16:
            prosody_vector = prosody_vector[:16].ljust(16, b'\x00')
        packet.prosody_vector = prosody_vector

    # Step 1: Pre-CRC serialization
    packet.crc16_checksum = 0
    pre_crc_bytes = packet.SerializeToString()
    crc = calculate_crc16(pre_crc_bytes)

    # Step 2: Final serialization with computed CRC16 field
    packet.crc16_checksum = crc
    return packet.SerializeToString()


def parse_and_validate_frame(wire_bytes: bytes):
    if not wire_bytes:
        raise ValueError("Received empty wire bytes")

    packet = _create_packet()
    if not packet.ParseFromString(wire_bytes):
        raise ValueError("Protobuf deserialization failed")

    if packet.magic_header != MAGIC_HEADER:
        raise ValueError(f"Invalid magic header 0x{packet.magic_header:08X} (expected 0x{MAGIC_HEADER:08X})")

    received_crc = packet.crc16_checksum

    # Verify CRC
    verify_packet = _create_packet()
    verify_packet.CopyFrom(packet)
    verify_packet.crc16_checksum = 0
    verify_bytes = verify_packet.SerializeToString()
    expected_crc = calculate_crc16(verify_bytes)

    if received_crc != expected_crc:
        raise ValueError(f"CRC16 mismatch: received 0x{received_crc:04X}, calculated 0x{expected_crc:04X} (frame corrupted)")

    return packet


def validate_frame(wire_bytes: bytes) -> bool:
    try:
        parse_and_validate_frame(wire_bytes)
        return True
    except Exception:
        return False
