package org.isro.itantra.transport.wfbng

import org.isro.itantra.transport.ChaCha20Poly1305Engine
import org.isro.itantra.transport.ReedSolomonFECEngine
import org.isro.itantra.transport.mesh.MeshRouter
import org.isro.itantra.transport.udp.UdpTransceiver
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.concurrent.atomic.AtomicInteger

class WfbngManager(
    val callsign: String,
    cryptoKey: ByteArray,
    val targetIp: String = "255.255.255.255",
    val port: Int = 8988
) {
    val crypto = ChaCha20Poly1305Engine(cryptoKey)
    val fec = ReedSolomonFECEngine(8, 4)
    val mesh = MeshRouter(callsign)
    val udp = UdpTransceiver(port, callsign)

    private val sequenceCounter = AtomicInteger(0)
    var onVoicePayloadDelivered: ((String, String, Byte, ByteArray) -> Unit)? = null
    var onPeerDiscovered: ((String, String) -> Unit)? = null

    init {
        udp.onPeerDiscovered = { peerCallsign, peerIp ->
            onPeerDiscovered?.invoke(peerCallsign, peerIp)
        }
        mesh.onUdpBroadcast = { packetBytes ->
            udp.sendPacket(packetBytes, targetIp, port)
        }

        mesh.onLocalDeliver = { origin, encryptedPayload ->
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
                // If unencrypted or raw payload delivered
                onVoicePayloadDelivered?.invoke(origin, "en", 0.toByte(), encryptedPayload)
            }
        }

        udp.onPacketReceived = { rawBytes ->
            mesh.routeIncoming(rawBytes)
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
        
        mesh.sendNewPacket(targetCallsign, sequence, encrypted)
    }
}


