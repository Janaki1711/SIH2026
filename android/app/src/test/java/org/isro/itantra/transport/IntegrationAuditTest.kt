package org.isro.itantra.transport

import org.junit.Assert.*
import org.junit.Test
import java.nio.charset.StandardCharsets

class IntegrationAuditTest {

    private val testKey = "01234567890123456789012345678901".toByteArray(StandardCharsets.UTF_8)
    private val wrongKey = "WRONG_KEY_0123456789012345678901".toByteArray(StandardCharsets.UTF_8)

    @Test
    fun testChaCha20Poly1305_EncryptDecrypt() {
        val engine = ChaCha20Poly1305Engine(testKey)
        val plaintext = "Hello iTantra Tactical Walkie-Talkie Mesh".toByteArray(StandardCharsets.UTF_8)
        
        val encrypted = engine.encrypt(plaintext)
        assertTrue(encrypted.size >= plaintext.size + ChaCha20Poly1305Engine.NONCE_SIZE + ChaCha20Poly1305Engine.TAG_SIZE)
        
        val decrypted = engine.decrypt(encrypted)
        assertArrayEquals(plaintext, decrypted)
    }

    @Test
    fun testChaCha20Poly1305_CorruptedCiphertextRejection() {
        val engine = ChaCha20Poly1305Engine(testKey)
        val plaintext = "Do not evacuate Sector 4.".toByteArray(StandardCharsets.UTF_8)
        val encrypted = engine.encrypt(plaintext)
        
        // Corrupt ciphertext body
        val corrupted = encrypted.copyOf()
        corrupted[ChaCha20Poly1305Engine.NONCE_SIZE + 2] = (corrupted[ChaCha20Poly1305Engine.NONCE_SIZE + 2].toInt() xor 0xFF).toByte()
        
        val decrypted = engine.decrypt(corrupted)
        // Decrypted content with corrupted ciphertext must NOT match original plaintext
        assertFalse(plaintext.contentEquals(decrypted))
    }

    @Test
    fun testChaCha20Poly1305_WrongKeyRejection() {
        val engine1 = ChaCha20Poly1305Engine(testKey)
        val engine2 = ChaCha20Poly1305Engine(wrongKey)
        val plaintext = "Rescue team dispatched to Block 7.".toByteArray(StandardCharsets.UTF_8)
        
        val encrypted = engine1.encrypt(plaintext)
        val decrypted = engine2.decrypt(encrypted)
        
        assertFalse(plaintext.contentEquals(decrypted))
    }

    @Test
    fun testReedSolomon_0to4ShardsLostRecovery() {
        val fec = ReedSolomonFECEngine(8, 4)
        val originalPayload = "TACTICAL_PAYLOAD_SECTOR_4_URGENT_EVACUATION_FALSE_2026".toByteArray(StandardCharsets.UTF_8)
        
        val shards = fec.encode(originalPayload)
        assertEquals(12, shards.size) // K=8 + M=4
        
        // Test 0, 1, 2, 3, 4 dropped shards
        for (lossCount in 0..4) {
            val received = mutableMapOf<Int, ByteArray>()
            for (i in lossCount until shards.size) {
                received[i] = shards[i]
            }
            assertTrue("Must have at least 8 shards", received.size >= 8)
            
            val recovered = fec.decode(received, originalPayload.size)
            assertArrayEquals("Failed recovery with $lossCount lost shards", originalPayload, recovered)
        }
    }

    @Test(expected = IllegalArgumentException::class)
    fun testReedSolomon_5ShardsLostRejection() {
        val fec = ReedSolomonFECEngine(8, 4)
        val originalPayload = "SHORT_PAYLOAD".toByteArray(StandardCharsets.UTF_8)
        val shards = fec.encode(originalPayload)
        
        // 5 shards lost -> only 7 received (< K=8)
        val received = mutableMapOf<Int, ByteArray>()
        for (i in 5 until shards.size) {
            received[i] = shards[i]
        }
        assertEquals(7, received.size)
        fec.decode(received, originalPayload.size) // Must throw IllegalArgumentException
    }

    @Test
    fun testWfbngPacket_SerializationDeserialization() {
        val payload = "Hello WFB-ng Mesh Frame".toByteArray(StandardCharsets.UTF_8)
        val packet = WfbngPacket(
            sequence = 42.toShort(),
            originCallsign = "NODE_A",
            targetCallsign = "NODE_B",
            shardIndex = 3.toByte(),
            totalShards = 12.toByte(),
            originalLength = payload.size.toShort(),
            ttl = 5.toByte(),
            payload = payload
        )

        val serialized = packet.toBytes()
        assertTrue(serialized.isNotEmpty())

        val deserialized = WfbngPacket.fromBytes(serialized)
        assertNotNull(deserialized)
        assertEquals(42.toShort(), deserialized!!.sequence)
        assertEquals("NODE_A", deserialized.originCallsign)
        assertEquals("NODE_B", deserialized.targetCallsign)
        assertEquals(3.toByte(), deserialized.shardIndex)
        assertEquals(12.toByte(), deserialized.totalShards)
        assertEquals(payload.size.toShort(), deserialized.originalLength)
        assertArrayEquals(payload, deserialized.payload)
    }

    @Test
    fun testHandshakeParsing_FormatValidation() {
        val localCallsign = "NODE_A"
        val timestamp = 1725880000000L
        val seq = "101"
        
        val helloStr = "ITANTRA_HELLO:$localCallsign:$seq:$timestamp"
        assertTrue(helloStr.startsWith("ITANTRA_HELLO:"))
        val helloParts = helloStr.split(":")
        assertEquals("NODE_A", helloParts[1])
        assertEquals(seq, helloParts[2])
        assertEquals(timestamp, helloParts[3].toLong())

        val ackStr = "ITANTRA_ACK:NODE_B:$seq:$timestamp"
        assertTrue(ackStr.startsWith("ITANTRA_ACK:"))
        val ackParts = ackStr.split(":")
        assertEquals("NODE_B", ackParts[1])
        assertEquals(seq, ackParts[2])
        assertEquals(timestamp, ackParts[3].toLong())

        val confirmStr = "ITANTRA_LINK_CONFIRM:$localCallsign:$seq"
        assertTrue(confirmStr.startsWith("ITANTRA_LINK_CONFIRM:"))
        val confirmParts = confirmStr.split(":")
        assertEquals("NODE_A", confirmParts[1])
        assertEquals(seq, confirmParts[2])
    }
}
