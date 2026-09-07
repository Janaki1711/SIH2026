package org.isro.itantra.transport.mesh

import org.isro.itantra.transport.WfbngPacket
import java.util.Collections
import java.util.LinkedHashMap

class MeshRouter(private val myCallsign: String) {
    // LRU Cache for duplicate detection (Sequence + Origin)
    private val maxCacheSize = 1000
    private val seenPackets = Collections.synchronizedMap(
        object : LinkedHashMap<String, Long>(maxCacheSize, 0.75f, true) {
            override fun removeEldestEntry(eldest: Map.Entry<String, Long>): Boolean {
                return size > maxCacheSize
            }
        }
    )

    // Callbacks
    var onUdpBroadcast: ((ByteArray) -> Unit)? = null
    var onLocalDeliver: ((String, ByteArray) -> Unit)? = null

    fun sendNewPacket(targetCallsign: String, seq: Short, payload: ByteArray) {
        val packet = WfbngPacket(
            sequence = seq,
            originCallsign = myCallsign,
            targetCallsign = targetCallsign,
            payload = payload
        )
        // Cache our own sent packet so we don't rebroadcast it if we hear it echoed
        val cacheKey = "$seq-$myCallsign"
        seenPackets[cacheKey] = System.currentTimeMillis()
        
        onUdpBroadcast?.invoke(packet.toBytes())
    }

    fun routeIncoming(rawBytes: ByteArray) {
        val packet = WfbngPacket.fromBytes(rawBytes) ?: return
        
        val cacheKey = "${packet.sequence}-${packet.originCallsign}"
        if (seenPackets.containsKey(cacheKey)) {
            return // Duplicate
        }
        seenPackets[cacheKey] = System.currentTimeMillis()

        // Local delivery?
        if (packet.targetCallsign == myCallsign || packet.targetCallsign == "ALL") {
            onLocalDeliver?.invoke(packet.originCallsign, packet.payload)
        }

        // Rebroadcast?
        if (packet.ttl > 1 && packet.targetCallsign != myCallsign) {
            packet.ttl--
            onUdpBroadcast?.invoke(packet.toBytes())
        }
    }
}
