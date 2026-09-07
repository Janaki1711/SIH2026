package org.isro.itantra.transport

import org.isro.itantra.transport.ChaCha20Poly1305Engine
import org.isro.itantra.transport.ReedSolomonReedSolomonFECEngine
import org.isro.itantra.transport.mesh.MeshRouter
import org.isro.itantra.transport.udp.UdpTransceiver
import org.isro.itantra.transport.wfbng.WfbngManager
import org.junit.Assert.*
import org.junit.Test
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.delay

class WfbngTransportTest {

    @Test
    fun testPacketEncodeDecode() {
        val payload = "Hello ITantra".toByteArray()
        val packet = WfbngPacket(
            magic = 0x42,
            ttl = 7,
            sequence = 1234,
            originCallsign = "NODE_A",
            targetCallsign = "NODE_B",
            payload = payload
        )
        
        val bytes = packet.toBytes()
        val decoded = WfbngPacket.fromBytes(bytes)
        
        assertNotNull(decoded)
        assertEquals(0x42.toByte(), decoded!!.magic)
        assertEquals(7.toByte(), decoded.ttl)
        assertEquals(1234.toShort(), decoded.sequence)
        assertEquals("NODE_A", decoded.originCallsign)
        assertEquals("NODE_B", decoded.targetCallsign)
        assertArrayEquals(payload, decoded.payload)
    }

    @Test
    fun testEncryptionDecryption() {
        val key = ByteArray(32) { it.toByte() }
        val crypto = ChaCha20Poly1305Engine(key)
        
        val plaintext = "TopSecretMessage".toByteArray()
        val ciphertext = crypto.encrypt(plaintext)
        
        // Nonce(12) + Tag(16) + Ciphertext(16) = 44 bytes
        assertTrue(ciphertext.size >= 28) 
        
        val decrypted = crypto.decrypt(ciphertext)
        assertNotNull(decrypted)
        assertArrayEquals(plaintext, decrypted!!)
    }

    @Test
    fun testFecEncodeRecovery() {
        val fec = ReedSolomonFECEngine(k = 4, m = 2)
        val shardSize = 10
        val dataShards = Array(4) { i -> ByteArray(shardSize) { (i + 1).toByte() } }
        
        val encoded = fec.encode(dataShards)
        assertEquals(6, encoded.size)
        
        // Simulate missing shards (drop indices 0 and 2)
        val received = arrayOfNulls<ByteArray>(6)
        received[0] = encoded[0]
        received[1] = encoded[1]
        received[3] = encoded[3]
        received[4] = encoded[4]
        received[5] = encoded[5]
        
        val decoded = fec.decode(received, shardSize)
        assertNotNull(decoded)
        assertEquals(4, decoded!!.size)
        assertArrayEquals(dataShards[0], decoded[0])
        assertArrayEquals(dataShards[2], decoded[2])
    }

    @Test
    fun testMeshTtlAndDuplicates() {
        val router = MeshRouter("NODE_B")
        var broadcastCount = 0
        var localDeliverCount = 0
        
        router.onUdpBroadcast = { broadcastCount++ }
        router.onLocalDeliver = { _, _ -> localDeliverCount++ }
        
        val packet = WfbngPacket(
            magic = 0x42,
            ttl = 3,
            sequence = 100,
            originCallsign = "NODE_A",
            targetCallsign = "NODE_C", // Not me, should route
            payload = ByteArray(0)
        )
        
        // 1. New packet, should rebroadcast, TTL decremented
        router.routeIncoming(packet.toBytes())
        assertEquals(1, broadcastCount)
        assertEquals(0, localDeliverCount)
        
        // 2. Exact same packet again, should be dropped
        router.routeIncoming(packet.toBytes())
        assertEquals(1, broadcastCount) // Still 1
        
        // 3. Packet destined for me
        val myPacket = WfbngPacket(
            magic = 0x42,
            ttl = 3,
            sequence = 101,
            originCallsign = "NODE_A",
            targetCallsign = "NODE_B",
            payload = ByteArray(0)
        )
        router.routeIncoming(myPacket.toBytes())
        assertEquals(1, broadcastCount) // Does not rebroadcast since it reached destination
        assertEquals(1, localDeliverCount) // Delivered
    }

    @Test
    fun testUdpSendReceive() = runTest {
        val port = 18988
        val rx = UdpTransceiver(port = port)
        var received = false
        
        rx.onPacketReceived = { data ->
            val str = String(data)
            if (str == "UDP_TEST") received = true
        }
        rx.start()
        
        val tx = UdpTransceiver(port = port + 1)
        tx.sendPacket("UDP_TEST".toByteArray(), "127.0.0.1", port)
        
        delay(500)
        
        tx.stop()
        rx.stop()
        
        assertTrue(received)
    }
}



