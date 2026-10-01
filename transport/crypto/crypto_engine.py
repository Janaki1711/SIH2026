"""
crypto_engine.py — Tactical Authenticated Encryption Layer

Authenticated encryption for transport packets.

Wire format:
    [ Nonce: 12 bytes ]
    [ Authentication Tag: 16 bytes ]
    [ Ciphertext: N bytes ]

NOTE:
This implementation uses only the Python standard library and therefore
does NOT implement ChaCha20-Poly1305. Do not label it as ChaCha20-Poly1305
or "military-grade" in project documentation.

For production deployment, replace this implementation with a vetted AEAD
implementation such as ChaCha20-Poly1305 from an established crypto library.
"""

import hashlib
import hmac
import os
import struct
from typing import Optional


# ------------------------------------------------------------------
# Default development key
#
# IMPORTANT:
# This is suitable only for local development/testing.
# Do not hard-code a real production mission key in source code.
# ------------------------------------------------------------------

DEFAULT_MISSION_KEY = hashlib.sha256(
    b"ITANTRA_TACTICAL_MISSION_KEY_DEVELOPMENT"
).digest()


class TacticalCrypto:
    """
    Lightweight authenticated encryption interface.

    API compatibility:

        encrypted = crypto.encrypt(
            plaintext,
            sequence_num=sequence
        )

        plaintext = crypto.decrypt(
            encrypted
        )
    """

    NONCE_SIZE = 12
    TAG_SIZE = 16
    BLOCK_SIZE = 32

    def __init__(
        self,
        key: bytes = DEFAULT_MISSION_KEY,
    ):

        if len(key) != 32:

            raise ValueError(
                "Tactical mission key must be exactly "
                "32 bytes (256 bits)"
            )

        self.key = bytes(key)

        # Random per-instance prefix reduces nonce collision risk
        # between different instances using the same sequence numbers.
        self.instance_id = (
            int.from_bytes(
                os.urandom(4),
                "big",
            )
        )

        self.nonce_counter = 0

    # ------------------------------------------------------------------
    # Encryption
    # ------------------------------------------------------------------

    def encrypt(
        self,
        plaintext: bytes,
        sequence_num: int,
    ) -> bytes:
        """
        Encrypt and authenticate plaintext.

        Wire format:

            nonce (12 bytes)
            +
            authentication tag (16 bytes)
            +
            ciphertext
        """

        if not isinstance(
            plaintext,
            (
                bytes,
                bytearray,
            ),
        ):

            raise TypeError(
                "plaintext must be bytes"
            )

        if not (
            0 <= sequence_num <= 0xFFFFFFFF
        ):

            raise ValueError(
                "sequence_num must fit in uint32"
            )

        self.nonce_counter = (
            self.nonce_counter + 1
        ) & 0xFFFFFFFF

        # ----------------------------------------------------------
        # 12-byte nonce:
        #
        # [ sequence number: 4 bytes ]
        # [ instance ID:      4 bytes ]
        # [ local counter:    4 bytes ]
        # ----------------------------------------------------------

        nonce = struct.pack(
            "!III",
            sequence_num,
            self.instance_id,
            self.nonce_counter,
        )

        keystream = (
            self._generate_keystream(
                key=self.key,
                nonce=nonce,
                length=len(plaintext),
            )
        )

        ciphertext = bytes(
            plain_byte ^ stream_byte
            for plain_byte,
            stream_byte in zip(
                plaintext,
                keystream,
            )
        )

        auth_tag = (
            self._calculate_tag(
                key=self.key,
                nonce=nonce,
                ciphertext=ciphertext,
            )[:self.TAG_SIZE]
        )

        return (
            nonce
            + auth_tag
            + ciphertext
        )

    # ------------------------------------------------------------------
    # Decryption
    # ------------------------------------------------------------------

    def decrypt(
        self,
        wire_payload: bytes,
    ) -> Optional[bytes]:
        """
        Authenticate and decrypt a wire payload.

        Returns:
            plaintext on success
            None if authentication fails or payload is malformed
        """

        minimum_size = (
            self.NONCE_SIZE
            + self.TAG_SIZE
        )

        if len(wire_payload) < minimum_size:

            return None

        nonce = (
            wire_payload[
                :self.NONCE_SIZE
            ]
        )

        received_tag = (
            wire_payload[
                self.NONCE_SIZE:
                self.NONCE_SIZE
                + self.TAG_SIZE
            ]
        )

        ciphertext = (
            wire_payload[
                self.NONCE_SIZE
                + self.TAG_SIZE:
            ]
        )

        expected_tag = (
            self._calculate_tag(
                key=self.key,
                nonce=nonce,
                ciphertext=ciphertext,
            )[:self.TAG_SIZE]
        )

        # Constant-time comparison
        if not hmac.compare_digest(
            received_tag,
            expected_tag,
        ):

            return None

        keystream = (
            self._generate_keystream(
                key=self.key,
                nonce=nonce,
                length=len(ciphertext),
            )
        )

        plaintext = bytes(
            cipher_byte ^ stream_byte
            for cipher_byte,
            stream_byte in zip(
                ciphertext,
                keystream,
            )
        )

        return plaintext

    # ------------------------------------------------------------------
    # Internal keystream generator
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_keystream(
        key: bytes,
        nonce: bytes,
        length: int,
    ) -> bytes:
        """
        Generate a deterministic XOR keystream.

        This is a project-development construction and is NOT a
        replacement for a standardized AEAD cipher.
        """

        output = bytearray()

        counter = 0

        while len(output) < length:

            counter_bytes = (
                struct.pack(
                    "!I",
                    counter,
                )
            )

            block = (
                hashlib.sha256(
                    key
                    + nonce
                    + counter_bytes
                ).digest()
            )

            output.extend(
                block
            )

            counter += 1

        return bytes(
            output[:length]
        )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_tag(
        key: bytes,
        nonce: bytes,
        ciphertext: bytes,
    ) -> bytes:
        """
        Calculate HMAC-SHA256 authentication tag.
        """

        return hmac.new(
            key,
            nonce + ciphertext,
            hashlib.sha256,
        ).digest()
