# crypto.py
"""
iTantra M3 Cryptography & Integrity
Provides CRC16-CCITT and ChaCha20-Poly1305 authenticated encryption.
"""

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import os
import struct

# Hardcoded demo key for ChaCha20-Poly1305 (32 bytes)
_DEMO_KEY = b"ITANTRA_SIH_2026_M3_CHACHA20_KEY" 

def encrypt(plaintext: bytes) -> bytes:
    """
    Encrypts the plaintext using ChaCha20-Poly1305.
    Returns: nonce (12 bytes) + ciphertext (includes 16 byte MAC)
    """
    chacha = ChaCha20Poly1305(_DEMO_KEY)
    nonce = os.urandom(12)
    ciphertext = chacha.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext

def decrypt(data: bytes) -> bytes:
    """
    Decrypts the ChaCha20-Poly1305 data.
    Raises exception if authentication fails.
    """
    if len(data) < 28:
        raise ValueError("Payload too small for ChaCha20-Poly1305")
        
    nonce = data[:12]
    ciphertext = data[12:]
    
    chacha = ChaCha20Poly1305(_DEMO_KEY)
    return chacha.decrypt(nonce, ciphertext, associated_data=None)

# ─────────────────────────────────────────────────────────────────────────────
# CRC16-CCITT-FALSE
# Poly: 0x1021, Init: 0xFFFF
# ─────────────────────────────────────────────────────────────────────────────

def calculate_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def append_crc16(data: bytes) -> bytes:
    crc = calculate_crc16(data)
    return data + struct.pack(">H", crc)

def verify_crc16(data: bytes) -> tuple[bool, bytes, int, int]:
    """
    Verifies the CRC16 attached at the end of data.
    Returns (is_valid, original_data, received_crc, computed_crc)
    """
    if len(data) < 2:
        return False, b"", 0, 0
    
    original_data = data[:-2]
    received_crc = struct.unpack(">H", data[-2:])[0]
    computed_crc = calculate_crc16(original_data)
    
    return received_crc == computed_crc, original_data, received_crc, computed_crc
