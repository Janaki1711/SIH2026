package org.isro.itantra.transport.wfbng

import org.isro.itantra.transport.ChaCha20Poly1305Engine
import org.isro.itantra.transport.ReedSolomonFECEngine
import org.isro.itantra.transport.WfbngPacket
import org.isro.itantra.transport.mesh.MeshRouter
import org.isro.itantra.transport.udp.UdpTransceiver
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.Collections
import java.util.LinkedHashMap
import java.util.concurrent.atomic.AtomicInteger

class WfbngManager(
    val callsign: String,
    cryptoKey: ByteArray,
    val targetIp: String = "255.255.255.255",
    val port: Int = 8988,
    val context: android.content.Context? = null
) {
    val crypto = ChaCha20Poly1305Engine(cryptoKey)
    val fec = ReedSolomonFECEngine(8, 4)
    val mesh = MeshRouter(callsign)
    val udp = UdpTransceiver(port, callsign, context = context)

    private val sequenceCounter = AtomicInteger(0)
    var onVoicePayloadDelivered: ((String, String, Byte, ByteArray) -> Unit)? = null
    var onPeerDiscovered: ((String, String) -> Unit)? = null
    var onLinkConfirmed: ((String, String, Long) -> Unit)? = null

    private data class ShardSession(
        val totalShards: Int,
        val originalLength: Int,
        val receivedShards: MutableMap<Int, ByteArray> = mutableMapOf(),
        val timestamp: Long = System.currentTimeMillis(),
        var isDecoded: Boolean = false
    )

    private val shardSessions = Collections.synchronizedMap(
        object : LinkedHashMap<String, ShardSession>(200, 0.75f, true) {
            override fun removeEldestEntry(eldest: Map.Entry<String, ShardSession>): Boolean {
                return size > 200 || (System.currentTimeMillis() - eldest.value.timestamp > 30000)
            }
        }
    )

    init {
        udp.onPeerDiscovered = { peerCallsign, peerIp ->
            onPeerDiscovered?.invoke(peerCallsign, peerIp)
        }
        udp.onLinkConfirmed = { peerCallsign, peerIp, rtt ->
            onLinkConfirmed?.invoke(peerCallsign, peerIp, rtt)
        }
        mesh.onUdpBroadcast = { packetBytes ->
            udp.sendPacket(packetBytes, targetIp, port)
        }

        mesh.onLocalDeliver = { packet ->
            handleIncomingPacket(packet)
        }

        udp.onPacketReceived = { rawBytes ->
            mesh.routeIncoming(rawBytes)
        }
    }

    private fun handleIncomingPacket(packet: WfbngPacket) {
        val totalShards = packet.totalShards.toInt() and 0xFF
        if (totalShards <= 1) {
            // Unfragmented or single-shard packet
            deliverEncryptedPayload(packet.originCallsign, packet.payload)
            return
        }

        val sessionKey = "${packet.originCallsign}-${packet.sequence}"
        val session = shardSessions.getOrPut(sessionKey) {
            ShardSession(
                totalShards = totalShards,
                originalLength = packet.originalLength.toInt() and 0xFFFF
            )
        }

        var reconstructedBytes: ByteArray? = null
        synchronized(session) {
            if (session.isDecoded) return

            val shardIdx = packet.shardIndex.toInt() and 0xFF
            session.receivedShards[shardIdx] = packet.payload

            if (session.receivedShards.size >= fec.k) {
                session.isDecoded = true
                reconstructedBytes = try {
                    fec.decode(session.receivedShards, session.originalLength)
                } catch (e: Throwable) {
                    android.util.Log.e("WfbngManager", "FEC reconstruction failed: ${e.message}")
                    null
                }
            }
        }

        reconstructedBytes?.let { encryptedData ->
            deliverEncryptedPayload(packet.originCallsign, encryptedData)
        }
    }

    private fun deliverEncryptedPayload(origin: String, encryptedPayload: ByteArray) {
        val plaintext = try {
            crypto.decrypt(encryptedPayload)
        } catch (e: Throwable) {
            android.util.Log.w("WfbngManager", "Decryption failed: ${e.message}")
            null
        }
        if (plaintext != null && plaintext.size >= 3) {
            val langBytes = plaintext.copyOfRange(0, 2)
            val language = String(langBytes, StandardCharsets.UTF_8).trimEnd('\u0000')
            val priority = plaintext[2]
            val voicePayload = plaintext.copyOfRange(3, plaintext.size)
            
            onVoicePayloadDelivered?.invoke(origin, language, priority, voicePayload)
        } else if (encryptedPayload.isNotEmpty()) {
            onVoicePayloadDelivered?.invoke(origin, "en", 0.toByte(), encryptedPayload)
        }
    }

    fun start() {
        udp.start()
    }

    fun stop() {
        udp.stop()
    }

    fun addManualPeer(ipStr: String) {
        udp.addPeerIp(ipStr)
    }

    fun getDiagnosticInfo(): Map<String, String> {
        return udp.getDiagnosticInfo()
    }

    fun pingPeer(
        targetIp: String,
        timeoutMs: Long = 1200L,
        maxAttempts: Int = 3,
        onResult: (Boolean, String, Long, String) -> Unit
    ) {
        udp.pingPeer(targetIp, timeoutMs, maxAttempts, onResult)
    }

    fun sendVoiceMessage(voicePayload: ByteArray, language: String = "hi", priority: Byte = 0, targetCallsign: String = "ALL") {
        val sequence = (sequenceCounter.incrementAndGet() and 0xFFFF).toShort()
        
        val langBytes = language.toByteArray(StandardCharsets.UTF_8)
        val paddedLang = ByteArray(2)
        System.arraycopy(langBytes, 0, paddedLang, 0, minOf(langBytes.size, 2))
        
        val bb = ByteBuffer.allocate(2 + 1 + voicePayload.size)
        bb.put(paddedLang)
        bb.put(priority)
        bb.put(voicePayload)
        
        val taggedPayload = bb.array()
        val encrypted = try {
            crypto.encrypt(taggedPayload)
        } catch (e: Throwable) {
            android.util.Log.e("WfbngManager", "Crypto encrypt error, falling back to raw: ${e.message}")
            taggedPayload
        }
        
        // Split into K=8 data shards + M=4 Cauchy parity shards (N=12 total)
        val shards = fec.encode(encrypted)
        val totalShards = fec.n.toByte()
        val originalLen = encrypted.size.toShort()

        for (shardIdx in shards.indices) {
            val packet = WfbngPacket(
                sequence = sequence,
                originCallsign = callsign,
                targetCallsign = targetCallsign,
                shardIndex = shardIdx.toByte(),
                totalShards = totalShards,
                originalLength = originalLen,
                payload = shards[shardIdx]
            )
            mesh.sendNewPacket(packet)
        }
    }
}


