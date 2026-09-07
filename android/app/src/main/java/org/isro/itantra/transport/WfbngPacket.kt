package org.isro.itantra.transport

import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets

data class WfbngPacket(
    var magic: Byte = 0x42,
    var ttl: Byte = 7,
    var sequence: Short = 0,
    var originCallsign: String = "",
    var targetCallsign: String = "",
    var payload: ByteArray = ByteArray(0) // Crypto payload
) {
    fun toBytes(): ByteArray {
        val originBytes = originCallsign.toByteArray(StandardCharsets.UTF_8).copyOf(16)
        val targetBytes = targetCallsign.toByteArray(StandardCharsets.UTF_8).copyOf(16)
        
        val bb = ByteBuffer.allocate(1 + 1 + 2 + 16 + 16 + payload.size)
        bb.put(magic)
        bb.put(ttl)
        bb.putShort(sequence)
        bb.put(originBytes)
        bb.put(targetBytes)
        bb.put(payload)
        return bb.array()
    }

    companion object {
        fun fromBytes(bytes: ByteArray): WfbngPacket? {
            if (bytes.size < 36) return null
            val bb = ByteBuffer.wrap(bytes)
            val magic = bb.get()
            if (magic != 0x42.toByte()) return null
            val ttl = bb.get()
            val sequence = bb.short
            val originBytes = ByteArray(16)
            bb.get(originBytes)
            val targetBytes = ByteArray(16)
            bb.get(targetBytes)
            val payload = ByteArray(bb.remaining())
            bb.get(payload)
            
            return WfbngPacket(
                magic, ttl, sequence,
                String(originBytes, StandardCharsets.UTF_8).trimEnd('\u0000'),
                String(targetBytes, StandardCharsets.UTF_8).trimEnd('\u0000'),
                payload
            )
        }
    }
}
