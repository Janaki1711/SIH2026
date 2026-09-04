"""
m3_adapter.py — iTantra M3 Protocol Adapter for Web Demo
Updated for Member 3 3-Tier Semantic Communication & CRC16 validation.
"""

import os
import sys
import time
from typing import Tuple, Dict, Any

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_M3_ROOT  = os.path.abspath(os.path.join(_THIS_DIR, '..', '..'))
_M3_BUILD = os.path.join(_M3_ROOT, 'build')

if _M3_BUILD not in sys.path:
    sys.path.insert(0, _M3_BUILD)

import packet_framer
from packet_framer import MAGIC_HEADER, calculate_crc16, frame_packet as pf_frame_packet, parse_and_validate_frame

ADAPTER_MODE = "REAL_PROTOBUF"
PRIORITY_NAMES = {0: "ROUTINE", 1: "TACTICAL", 2: "LIFE_SAFETY_ALERT"}

def encode_packet(payload: bytes, language: str, callsign: str, sequence: int, priority: int, prosody_vector: bytes = None) -> tuple[bytes, dict]:
    wire_bytes = pf_frame_packet(
        compressed_payload=payload,
        source_language=language,
        callsign=callsign,
        sequence=sequence,
        priority=priority,
        prosody_vector=prosody_vector
    )

    crc = calculate_crc16(wire_bytes)
    ts_ms = int(time.time() * 1000)

    fields = {
        'magic_header': f'0x{MAGIC_HEADER:08X} (AGY1)',
        'sequence_number': sequence,
        'timestamp_ms': ts_ms,
        'priority': PRIORITY_NAMES.get(priority, 'UNKNOWN'),
        'source_callsign': callsign,
        'source_language': language,
        'compressed_payload_size': len(payload),
        'crc16': f'0x{crc:04X}',
    }

    return wire_bytes, fields

def decode_packet(data: bytes) -> dict:
    packet = parse_and_validate_frame(data)
    return {
        'magic_header': packet.magic_header,
        'sequence_number': packet.sequence_number,
        'timestamp_ms': packet.timestamp_ms,
        'priority': packet.priority,
        'source_callsign': packet.source_callsign,
        'source_language': packet.source_language,
        'compressed_payload': packet.compressed_payload,
        'prosody_vector': packet.prosody_vector,
        'crc16_checksum': packet.crc16_checksum,
    }

def adapter_info() -> dict:
    return {'mode': ADAPTER_MODE, 'has_real_protobuf': True, 'crc16_enabled': True}
