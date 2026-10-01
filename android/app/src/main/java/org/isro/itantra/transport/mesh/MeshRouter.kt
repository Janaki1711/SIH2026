package org.isro.itantra.transport.mesh

import org.isro.itantra.transport.WfbngPacket
import java.util.Collections
import java.util.LinkedHashMap

class MeshRouter(private val myCallsign: String) {
    // LRU Cache for duplicate detection (Sequence + Origin + ShardIndex)
    private val maxCacheSize = 2000
    private val seenPackets = Collections.synchronizedMap(
        object : LinkedHashMap<String, Long>(maxCacheSize, 0.75f, true) {
            override fun removeEldestEntry(eldest: Map.Entry<String, Long>): Boolean {
                return size > maxCacheSize
            }
        }
    )

    // Callbacks
    var onUdpBroadcast: ((ByteArray) -> Unit)? = null
    var onLocalDeliver: ((WfbngPacket) -> Unit)? = null

    fun sendNewPacket(packet: WfbngPacket) {
        val cacheKey = "${packet.sequence}-${packet.originCallsign}-${packet.shardIndex}"
        seenPackets[cacheKey] = System.currentTimeMillis()
        
        onUdpBroadcast?.invoke(packet.toBytes())
    }

    fun sendNewPacket(targetCallsign: String, seq: Short, payload: ByteArray) {
        val packet = WfbngPacket(
            sequence = seq,
            originCallsign = myCallsign,
            targetCallsign = targetCallsign,
            payload = payload
        )
        sendNewPacket(packet)
    }

    fun routeIncoming(rawBytes: ByteArray) {
        val packet = WfbngPacket.fromBytes(rawBytes) ?: return
        
        val cacheKey = "${packet.sequence}-${packet.originCallsign}-${packet.shardIndex}"
        if (seenPackets.containsKey(cacheKey)) {
            return // Duplicate
        }
        seenPackets[cacheKey] = System.currentTimeMillis()

        // Ignore echo loopback of our own broadcasts
        if (packet.originCallsign == myCallsign) {
            return
        }

        // Local delivery?
        if (packet.targetCallsign == myCallsign || packet.targetCallsign == "ALL" || packet.targetCallsign.endsWith("_ALL")) {
            onLocalDeliver?.invoke(packet)
        }

        // Rebroadcast?
        if (packet.ttl > 1 && packet.targetCallsign != myCallsign) {
            packet.ttl = (packet.ttl - 1).toByte()
            onUdpBroadcast?.invoke(packet.toBytes())
        }
    }
}
