package org.isro.itantra.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [
        MessageAuditLog::class,
        MeshPeerRegistry::class,
        EmergencyCodebook::class
    ],
    version = 3,
    exportSchema = false
)
abstract class MessageDatabase : RoomDatabase() {

    abstract fun messageAuditLogDao(): MessageAuditLogDao
    abstract fun meshPeerRegistryDao(): MeshPeerRegistryDao
    abstract fun emergencyCodebookDao(): EmergencyCodebookDao

    companion object {

        private val MIGRATION_1_2 = object : Migration(1, 2) {

            override fun migrate(db: SupportSQLiteDatabase) {
                // Create the new table
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS `message_audit_log_new` (
                        `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
                        `timestamp` INTEGER NOT NULL, 
                        `messageId` TEXT NOT NULL, 
                        `senderId` TEXT NOT NULL, 
                        `receiverId` TEXT NOT NULL, 
                        `messageType` TEXT NOT NULL, 
                        `previousState` TEXT NOT NULL, 
                        `nextState` TEXT NOT NULL, 
                        `status` TEXT NOT NULL
                    )
                    """.trimIndent()
                )

                // Copy the data from the old table to the new table
                // Mapping the old 'state' column to 'nextState' (or previousState) as appropriate.
                db.execSQL(
                    """
                    INSERT INTO message_audit_log_new (id, timestamp, messageId, senderId, receiverId, messageType, previousState, nextState, status)
                    SELECT id, timestamp, messageId, senderId, receiverId, messageType, '', state, status FROM message_audit_log
                    """.trimIndent()
                )

                // Remove the old table
                db.execSQL("DROP TABLE message_audit_log")

                // Rename the new table to the original table name
                db.execSQL("ALTER TABLE message_audit_log_new RENAME TO message_audit_log")
            }
        }

        private val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Table 2: MeshPeerRegistry
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS `mesh_peer_registry` (
                        `nodeCallsign` TEXT NOT NULL PRIMARY KEY,
                        `macOrP2pIp` TEXT NOT NULL DEFAULT '',
                        `transportType` TEXT NOT NULL DEFAULT 'WiFi',
                        `lastSeenTimestampMs` INTEGER NOT NULL DEFAULT 0,
                        `linkQualityRssi` INTEGER NOT NULL DEFAULT 0,
                        `batteryLevelPct` INTEGER NOT NULL DEFAULT -1,
                        `hopCount` INTEGER NOT NULL DEFAULT 1
                    )
                    """.trimIndent()
                )
                // Table 3: EmergencyCodebook
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS `emergency_codebook` (
                        `codeId` TEXT NOT NULL PRIMARY KEY,
                        `shortMacro` TEXT NOT NULL DEFAULT '',
                        `expandedTextHi` TEXT NOT NULL DEFAULT '',
                        `expandedTextTa` TEXT NOT NULL DEFAULT '',
                        `expandedTextTe` TEXT NOT NULL DEFAULT '',
                        `expandedTextMr` TEXT NOT NULL DEFAULT '',
                        `expandedTextBn` TEXT NOT NULL DEFAULT '',
                        `expandedTextKn` TEXT NOT NULL DEFAULT '',
                        `expandedTextMl` TEXT NOT NULL DEFAULT '',
                        `expandedTextGu` TEXT NOT NULL DEFAULT '',
                        `expandedTextOr` TEXT NOT NULL DEFAULT '',
                        `expandedTextEn` TEXT NOT NULL DEFAULT '',
                        `priority` TEXT NOT NULL DEFAULT 'CRITICAL'
                    )
                    """.trimIndent()
                )
            }
        }

        @Volatile
        private var INSTANCE: MessageDatabase? = null

        fun getDatabase(context: Context): MessageDatabase {

            return INSTANCE ?: synchronized(this) {

                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    MessageDatabase::class.java,
                    "itantra_database"
                )
                    .addMigrations(MIGRATION_1_2, MIGRATION_2_3)
                    .build()

                INSTANCE = instance

                instance
            }
        }
    }
}
