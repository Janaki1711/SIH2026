"""
m3_adapter.py — iTantra M3 Protocol Adapter for Web Demo
Updated for Semantic Communication pipeline.
"""

import os
import sys
import time

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_M3_ROOT  = os.path.abspath(os.path.join(_THIS_DIR, '..', '..'))
_M3_BUILD = os.path.join(_M3_ROOT, 'build')

_pb2 = None
ADAPTER_MODE = "REAL_PROTOBUF"
try:
    if _M3_BUILD not in sys.path:
        sys.path.insert(0, _M3_BUILD)
    import packet_schema_pb2 as mod
    _pb2 = mod
except ImportError:
    try:
        import packet_schema_pb2 as mod
        _pb2 = mod
    except ImportError:
        ADAPTER_MODE = "FALLBACK"

MAGIC_HEADER = 0x41475931  # "AGY1"
PRIORITY_NAMES = {0: "ROUTINE", 1: "TACTICAL", 2: "LIFE_SAFETY_ALERT"}

def _manual_encode(payload: bytes, language: str, callsign: str, sequence: int, priority: int, timestamp_ms: int) -> bytes:
    def _encode_varint(value: int) -> bytes:
        result = []
        while True:
            bits = value & 0x7F
            value >>= 7
            if value:
                result.append(bits | 0x80)
            else:
                result.append(bits)
                break
        return bytes(result)

    def _encode_field_varint(field_num: int, value: int) -> bytes:
        tag = (field_num << 3) | 0
        return _encode_varint(tag) + _encode_varint(value)

    def _encode_field_bytes(field_num: int, value: bytes) -> bytes:
        tag = (field_num << 3) | 2
        return _encode_varint(tag) + _encode_varint(len(value)) + value

    out = b''
    out += _encode_field_varint(1, MAGIC_HEADER)
    out += _encode_field_varint(2, sequence)
    out += _encode_field_varint(3, timestamp_ms)
    if priority != 0:
        out += _encode_field_varint(4, priority)
    out += _encode_field_bytes(5, callsign.encode('utf-8'))
    out += _encode_field_bytes(6, language.encode('utf-8'))
    out += _encode_field_bytes(7, payload)
    return out

def _decode_varint(data: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if pos >= len(data): raise ValueError("EOF varint")
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): break
        shift += 7
    return result, pos

def _manual_decode(data: bytes) -> dict:
    packet = {'magic_header': 0, 'sequence_number': 0, 'timestamp_ms': 0, 'priority': 0, 
              'source_callsign': '', 'source_language': '', 'compressed_payload': b''}
    pos = 0
    while pos < len(data):
        tag_value, pos = _decode_varint(data, pos)
        field_num = tag_value >> 3
        wire_type = tag_value & 0x07
        if wire_type == 0:
            value, pos = _decode_varint(data, pos)
            if field_num == 1: packet['magic_header'] = value
            elif field_num == 2: packet['sequence_number'] = value
            elif field_num == 3: packet['timestamp_ms'] = value
            elif field_num == 4: packet['priority'] = value
        elif wire_type == 2:
            length, pos = _decode_varint(data, pos)
            value_bytes = data[pos:pos + length]
            pos += length
            if field_num == 5: packet['source_callsign'] = value_bytes.decode('utf-8', errors='replace')
            elif field_num == 6: packet['source_language'] = value_bytes.decode('utf-8', errors='replace')
            elif field_num == 7: packet['compressed_payload'] = value_bytes
        else:
            break
    return packet

def encode_packet(payload: bytes, language: str, callsign: str, sequence: int, priority: int) -> tuple[bytes, dict]:
    ts_ms = int(time.time() * 1000)
    fields = {
        'magic_header': f'0x{MAGIC_HEADER:08X} (AGY1)',
        'sequence_number': sequence,
        'timestamp_ms': ts_ms,
        'priority': PRIORITY_NAMES.get(priority, 'UNKNOWN'),
        'source_callsign': callsign,
        'source_language': language,
        'compressed_payload_size': len(payload),
    }

    if _pb2 is not None:
        packet = _pb2.VoicePacket()
        packet.magic_header = MAGIC_HEADER
        packet.sequence_number = sequence
        packet.timestamp_ms = ts_ms
        packet.priority = priority
        packet.source_callsign = callsign
        packet.source_language = language
        packet.compressed_payload = payload
        wire_bytes = packet.SerializeToString()
    else:
        wire_bytes = _manual_encode(payload, language, callsign, sequence, priority, ts_ms)

    return wire_bytes, fields

def decode_packet(data: bytes) -> dict:
    if _pb2 is not None:
        packet = _pb2.VoicePacket()
        packet.ParseFromString(data)
        return {
            'magic_header': packet.magic_header,
            'sequence_number': packet.sequence_number,
            'timestamp_ms': packet.timestamp_ms,
            'priority': packet.priority,
            'source_callsign': packet.source_callsign,
            'source_language': packet.source_language,
            'compressed_payload': packet.compressed_payload,
        }
    else:
        return _manual_decode(data)

def adapter_info() -> dict:
    return {'mode': ADAPTER_MODE, 'has_real_protobuf': _pb2 is not None}
