"""
protocol.py — iTantra M3 Web Demo Protocol Primitives

HONESTY NOTE:
  crc16()      → MEASURED. Python implementation of CRC16/CCITT-FALSE.
                 Phase 1 M3 C++ does NOT include CRC yet (planned Phase 3).
                 This demonstrates the Phase 3 capability.
  xor_encrypt() → DEMO MODE. XOR cipher for demo only.
                  Phase 3 will use AES-GCM.
  compress()    → MEASURED. Real zlib compression.
                  Phase 1 M3 C++ stores raw UTF-8 (no compression).
                  Phase 2 will use arithmetic coding + SentencePiece.
"""

import zlib
import struct
import time


# ── CRC16/CCITT-FALSE ────────────────────────────────────────────────────────

def crc16(data: bytes) -> int:
    """
    CRC16/CCITT-FALSE implementation.
    MEASURED — pure Python. Phase 3 will move this to C++ with hardware CRC
    on the radio module.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
        crc &= 0xFFFF
    return crc


def crc16_append(data: bytes) -> bytes:
    """Append 2-byte big-endian CRC16 to data."""
    return data + struct.pack('>H', crc16(data))


def crc16_verify(data_with_crc: bytes) -> tuple[bool, bytes, int, int]:
    """
    Verify CRC16 suffix.
    Returns: (is_valid, payload_bytes, received_crc, computed_crc)
    """
    if len(data_with_crc) < 2:
        return False, b'', 0, 0
    payload = data_with_crc[:-2]
    received_crc = struct.unpack('>H', data_with_crc[-2:])[0]
    computed_crc = crc16(payload)
    return (received_crc == computed_crc), payload, received_crc, computed_crc


# ── XOR Encryption (DEMO MODE) ───────────────────────────────────────────────

_DEMO_KEY = b'ITANTRA_DEMO_KEY'  # 16-byte XOR key — DEMO only


def xor_encrypt(data: bytes, key: bytes = _DEMO_KEY) -> bytes:
    """
    XOR encryption.
    DEMO MODE — AES-GCM with proper key exchange planned for Phase 3.
    """
    result = bytearray(len(data))
    klen = len(key)
    for i, byte in enumerate(data):
        result[i] = byte ^ key[i % klen]
    return bytes(result)


def xor_decrypt(data: bytes, key: bytes = _DEMO_KEY) -> bytes:
    """XOR decryption — identical to encryption for XOR cipher. DEMO MODE."""
    return xor_encrypt(data, key)


def corrupt_bytes(data: bytes, corrupt_positions: int = 3) -> bytes:
    """Introduce bit-flips at deterministic positions to test CRC detection."""
    import random as _random
    result = bytearray(data)
    positions = _random.sample(range(len(result)), min(corrupt_positions, len(result)))
    for pos in positions:
        result[pos] ^= 0xFF  # Flip all bits at that byte
    return bytes(result)


# ── zlib Compression (MEASURED) ──────────────────────────────────────────────

def compress(data: bytes, level: int = 6) -> tuple[bytes, float]:
    """
    Compress using zlib.
    MEASURED — actual bytes and timing.
    NOTE: zlib has ~10 byte header overhead; very short strings often EXPAND.
    Phase 2 M3 will use arithmetic coding + SentencePiece tokenization.
    """
    t0 = time.perf_counter()
    compressed = zlib.compress(data, level=level)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return compressed, elapsed_ms


def decompress(data: bytes) -> tuple[bytes, float]:
    """
    Decompress zlib data.
    MEASURED — actual bytes and timing.
    """
    t0 = time.perf_counter()
    decompressed = zlib.decompress(data)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return decompressed, elapsed_ms


# ── Packet Loss Simulation ────────────────────────────────────────────────────

import random as _random

def should_drop_packet(loss_rate: float) -> bool:
    """Return True if this packet should be dropped at the given loss rate."""
    if loss_rate <= 0.0:
        return False
    return _random.random() < loss_rate


# ── Hex formatting ────────────────────────────────────────────────────────────

def hex_dump(data: bytes, bytes_per_line: int = 16) -> str:
    """
    Format bytes as a hex dump string.
    """
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        addr = f'{i:04x}'
        lines.append(f'{addr}  {hex_part:<{bytes_per_line * 3}}  {ascii_part}')
    return '\n'.join(lines)


def hex_flat(data: bytes) -> str:
    """Return flat hex string: '0d 0a 41 ...'"""
    return ' '.join(f'{b:02x}' for b in data)
