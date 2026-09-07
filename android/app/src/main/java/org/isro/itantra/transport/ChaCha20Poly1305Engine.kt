package org.isro.itantra.transport

import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * ChaCha20-Poly1305 Authenticated Encryption (AEAD) Engine for Android.
 * 100% Bit-for-Bit Compatible with Python cryptography.hazmat.primitives.ciphers.aead.ChaCha20Poly1305.
 *
 * Wire Format:
 * [ 12-Byte Nonce ] [ Ciphertext ] [ 16-Byte Poly1305 Tag ]
 */
class ChaCha20Poly1305Engine(private val keyBytes: ByteArray) {

    companion object {
        const val NONCE_SIZE = 12
        const val TAG_SIZE = 16
        const val KEY_SIZE = 32
        private const val ALGORITHM = "ChaCha20-Poly1305"
        private const val TRANSFORMATION = "ChaCha20-Poly1305/None/NoPadding"
    }

    init {
        require(keyBytes.size == KEY_SIZE) { "Key must be exactly $KEY_SIZE bytes (got ${keyBytes.size})" }
    }

    private val secretKey = SecretKeySpec(keyBytes, ALGORITHM)
    private val random = SecureRandom()

    fun encrypt(plaintext: ByteArray, associatedData: ByteArray? = null, customNonce: ByteArray? = null): ByteArray {
        val nonce = customNonce ?: ByteArray(NONCE_SIZE).also { random.nextBytes(it) }
        require(nonce.size == NONCE_SIZE) { "Nonce must be exactly $NONCE_SIZE bytes" }

        val cipher = Cipher.getInstance(TRANSFORMATION)
        val ivSpec = IvParameterSpec(nonce)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, ivSpec)

        associatedData?.let {
            if (it.isNotEmpty()) cipher.updateAAD(it)
        }

        val ciphertextWithTag = cipher.doFinal(plaintext)
        val wirePacket = ByteArray(NONCE_SIZE + ciphertextWithTag.size)
        System.arraycopy(nonce, 0, wirePacket, 0, NONCE_SIZE)
        System.arraycopy(ciphertextWithTag, 0, wirePacket, NONCE_SIZE, ciphertextWithTag.size)

        return wirePacket
    }

    fun decrypt(wirePacket: ByteArray, associatedData: ByteArray? = null): ByteArray {
        require(wirePacket.size >= (NONCE_SIZE + TAG_SIZE)) {
            "Packet too short (min ${NONCE_SIZE + TAG_SIZE} bytes)"
        }

        val nonce = ByteArray(NONCE_SIZE)
        val ciphertextLen = wirePacket.size - NONCE_SIZE
        val ciphertextWithTag = ByteArray(ciphertextLen)

        System.arraycopy(wirePacket, 0, nonce, 0, NONCE_SIZE)
        System.arraycopy(wirePacket, NONCE_SIZE, ciphertextWithTag, 0, ciphertextLen)

        val cipher = Cipher.getInstance(TRANSFORMATION)
        val ivSpec = IvParameterSpec(nonce)
        cipher.init(Cipher.DECRYPT_MODE, secretKey, ivSpec)

        associatedData?.let {
            if (it.isNotEmpty()) cipher.updateAAD(it)
        }

        return cipher.doFinal(ciphertextWithTag)
    }
}
