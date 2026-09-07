package org.isro.itantra.transport.wfbng

import org.isro.itantra.transport.crypto.CryptoEngine
import org.isro.itantra.transport.fec.FecEngine
import org.isro.itantra.transport.mesh.MeshRouter
import org.isro.itantra.transport.udp.UdpTransceiver
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.concurrent.atomic.AtomicInteger

class WfbngManager(
    val callsign: String,
    cryptoKey: ByteArray
) {
    val crypto = CryptoEngine(cryptoKey)
    val fec = FecEngine(8, 4)
    val mesh = MeshRouter(callsign)
    val udp = UdpTransceiver()

    private val sequenceCounter = AtomicInteger(0)
    var onVoicePayloadDelivered: ((String, String, Byte, ByteArray) -> Unit)? = null

    init {
        mesh.onUdpBroadcast = { packetBytes ->
            udp.sendPacket(packetBytes)
        }

        mesh.onLocalDeliver = { origin, encryptedPayload ->
            val plaintext = crypto.decrypt(encryptedPayload)
            if (plaintext != null && plaintext.size >= 3) {
                val langBytes = plaintext.copyOfRange(0, 2)
                val language = String(langBytes, StandardCharsets.UTF_8).trimEnd('\u0000')
                val priority = plaintext[2]
                val voicePayload = plaintext.copyOfRange(3, plaintext.size)
                
                onVoicePayloadDelivered?.invoke(origin, language, priority, voicePayload)
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
        val encrypted = crypto.encrypt(taggedPayload)
        
        mesh.sendNewPacket(targetCallsign, sequence, encrypted)
    }
}
