package org.isro.itantra.database

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * MeshPeerRegistry — Table 2 as per iTantra README Database Architecture.
 * Tracks live mesh neighbor nodes: callsign, IP, transport type, RSSI, battery, hops.
 */
@Entity(tableName = "mesh_peer_registry")
data class MeshPeerRegistry(
    @PrimaryKey
    val nodeCallsign: String,           // e.g. "RESCUE_LEADER_01"
    val macOrP2pIp: String = "",        // MAC address or Wi-Fi Direct / hotspot IP
    val transportType: String = "WiFi", // "WiFi_Direct", "WiFi_Hotspot", "BT", "BLE"
    val lastSeenTimestampMs: Long = 0L, // epoch ms
    val linkQualityRssi: Int = 0,       // dBm, e.g. -65
    val batteryLevelPct: Int = -1,      // 0-100, -1 if unknown
    val hopCount: Int = 1               // 1 = direct, 2+ = relayed
)
