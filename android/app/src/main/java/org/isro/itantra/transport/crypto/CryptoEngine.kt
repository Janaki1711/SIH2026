package org.isro.itantra.transport.crypto

import org.bouncycastle.jce.provider.BouncyCastleProvider
import java.security.SecureRandom
import java.security.Security
import javax.crypto.Cipher
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.SecretKeySpec

class CryptoEngine(key: ByteArray) {
    private val secretKey = SecretKeySpec(key.copyOf(32), "ChaCha20")
    private val secureRandom = SecureRandom()

    init {
        if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
            Security.addProvider(BouncyCastleProvider())
        }
    }

    fun encrypt(plaintext: ByteArray): ByteArray {
        val nonce = ByteArray(12)
        secureRandom.nextBytes(nonce)
        
        val cipher = Cipher.getInstance("ChaCha20-Poly1305", "BC")
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, IvParameterSpec(nonce))
        
        val bcOutput = cipher.doFinal(plaintext)
        val ciphertextLength = bcOutput.size - 16
        val ciphertext = bcOutput.copyOfRange(0, ciphertextLength)
        val tag = bcOutput.copyOfRange(ciphertextLength, bcOutput.size)
        
        // Exact format: [Nonce: 12][Tag: 16][Ciphertext: N]
        return nonce + tag + ciphertext
    }

    fun decrypt(encrypted: ByteArray): ByteArray? {
        if (encrypted.size < 28) return null // 12 nonce + 16 tag minimum
        try {
            val nonce = encrypted.copyOfRange(0, 12)
            val tag = encrypted.copyOfRange(12, 28)
            val ciphertext = encrypted.copyOfRange(28, encrypted.size)
            
            // Reconstruct BouncyCastle expected format: [Ciphertext][Tag]
            val bcInput = ciphertext + tag
            
            val cipher = Cipher.getInstance("ChaCha20-Poly1305", "BC")
            cipher.init(Cipher.DECRYPT_MODE, secretKey, IvParameterSpec(nonce))
            
            return cipher.doFinal(bcInput)
        } catch (e: Exception) {
            return null
        }
    }
}
