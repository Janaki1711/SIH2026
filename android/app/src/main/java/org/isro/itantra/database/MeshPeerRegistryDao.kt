package org.isro.itantra.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface MeshPeerRegistryDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertPeer(peer: MeshPeerRegistry)

    @Query("SELECT * FROM mesh_peer_registry ORDER BY lastSeenTimestampMs DESC")
    suspend fun getAllPeers(): List<MeshPeerRegistry>

    @Query("SELECT * FROM mesh_peer_registry WHERE nodeCallsign = :callsign LIMIT 1")
    suspend fun getPeerByCallsign(callsign: String): MeshPeerRegistry?

    @Query("DELETE FROM mesh_peer_registry WHERE lastSeenTimestampMs < :cutoffMs")
    suspend fun pruneStale(cutoffMs: Long)

    @Query("DELETE FROM mesh_peer_registry")
    suspend fun clearAll()
}
