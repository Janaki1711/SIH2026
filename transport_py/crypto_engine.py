# ==============================================================================
# iTantra WFB-ng Transport - Authenticated Cryptographic Engine
# Standard: IETF RFC 8439 ChaCha20-Poly1305 Authenticated Encryption (AEAD)
# ==============================================================================

import os
from typing import Optional, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
except ImportError:
    raise ImportError(
        "Missing 'cryptography' package. Please install it using: pip install cryptography"
    )

class CryptoEngine:
    """
    Authenticated Encryption with Associated Data (AEAD) using ChaCha20-Poly1305.
    
    Wire Format Specification:
    +-----------------------+--------------------------+----------------------+
    | Nonce (12 Bytes)      | Ciphertext (N Bytes)     | Auth Tag (16 Bytes)  |
    +-----------------------+--------------------------+----------------------+
    Total Wire Overhead = 12 (Nonce) + 16 (Poly1305 Tag) = 28 Bytes.
    """

    NONCE_SIZE = 12   # 96-bit nonce as per RFC 8439
    TAG_SIZE = 16     # 128-bit Poly1305 MAC tag
    KEY_SIZE = 32     # 256-bit symmetric key

    def __init__(self, key_bytes: bytes):
        if len(key_bytes) != self.KEY_SIZE:
            raise ValueError(f"ChaCha20-Poly1305 key must be exactly {self.KEY_SIZE} bytes (got {len(key_bytes)})")
        self._key = key_bytes
        self._aead = ChaCha20Poly1305(self._key)

    def encrypt(self, plaintext: bytes, associated_data: Optional[bytes] = None, custom_nonce: Optional[bytes] = None) -> bytes:
        """
        Encrypts plaintext and produces wire packet: [12B Nonce] [Ciphertext + 16B Tag]
        """
        nonce = custom_nonce if custom_nonce is not None else os.urandom(self.NONCE_SIZE)
        if len(nonce) != self.NONCE_SIZE:
            raise ValueError(f"Nonce must be exactly {self.NONCE_SIZE} bytes")

        aad = associated_data if associated_data is not None else b""
        # ChaCha20Poly1305.encrypt appends the 16-byte Poly1305 tag to the ciphertext
        ciphertext_with_tag = self._aead.encrypt(nonce, plaintext, aad)

        return nonce + ciphertext_with_tag

    def decrypt(self, wire_packet: bytes, associated_data: Optional[bytes] = None) -> bytes:
        """
        Decrypts wire packet: [12B Nonce] [Ciphertext + 16B Tag]
        Raises InvalidTag if tampering or corruption occurs.
        """
        if len(wire_packet) < (self.NONCE_SIZE + self.TAG_SIZE):
            raise ValueError(f"Packet too short to contain Nonce and Poly1305 Tag (min {self.NONCE_SIZE + self.TAG_SIZE} bytes)")

        nonce = wire_packet[:self.NONCE_SIZE]
        ciphertext_with_tag = wire_packet[self.NONCE_SIZE:]
        aad = associated_data if associated_data is not None else b""

        return self._aead.decrypt(nonce, ciphertext_with_tag, aad)

    @classmethod
    def generate_key(cls) -> bytes:
        return ChaCha20Poly1305.generate_key()
