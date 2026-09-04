"""
packet_framer.py — Protobuf Binary Framer & CRC16-CCITT Engine

Handles:
1. Populating VoicePacket protobuf message
2. Attaching 16-byte prosody vector
3. Computing CRC16-CCITT (polynomial 0x1021, init 0xFFFF)
4. Deserialization & CRC16 corruption rejection
"""

import sys
import os
import time
import struct
from typing import Tuple, Optional

# Ensure build directory is in sys.path for packet_schema_pb2
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_BUILD_DIR = os.path.abspath(os.path.join(_THIS_DIR, '..', '..', 'build'))
if _BUILD_DIR not in sys.path:
    sys.path.insert(0, _BUILD_DIR)

import packet_schema_pb2 as pb

MAGIC_HEADER = 0x41475931  # "AGY1"

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

    packet = pb.VoicePacket()
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

def parse_and_validate_frame(wire_bytes: bytes) -> pb.VoicePacket:
    if not wire_bytes:
        raise ValueError("Received empty wire bytes")

    packet = pb.VoicePacket()
    if not packet.ParseFromString(wire_bytes):
        raise ValueError("Protobuf deserialization failed")

    if packet.magic_header != MAGIC_HEADER:
        raise ValueError(f"Invalid magic header 0x{packet.magic_header:08X} (expected 0x{MAGIC_HEADER:08X})")

    received_crc = packet.crc16_checksum

    # Verify CRC
    verify_packet = pb.VoicePacket()
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
