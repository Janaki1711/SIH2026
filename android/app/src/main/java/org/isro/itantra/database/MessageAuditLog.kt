package org.isro.itantra.database

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "message_audit_log")
data class MessageAuditLog(

    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val timestamp: Long,

    val messageId: String,

    val senderId: String,

    val receiverId: String,

    val messageType: String,

    val previousState: String,

    val nextState: String,

    val status: String
)
