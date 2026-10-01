package org.isro.itantra.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query

@Dao
interface MessageAuditLogDao {

    @Insert
    suspend fun insert(log: MessageAuditLog)

    @Query("SELECT * FROM message_audit_log ORDER BY timestamp DESC")
    suspend fun getAllLogs(): List<MessageAuditLog>

    @Query("DELETE FROM message_audit_log")
    suspend fun deleteAll()
}
