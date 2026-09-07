package org.isro.itantra.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

@Database(
    entities = [MessageAuditLog::class],
    version = 2,
    exportSchema = false
)
abstract class MessageDatabase : RoomDatabase() {

    abstract fun messageAuditLogDao(): MessageAuditLogDao

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

        @Volatile
        private var INSTANCE: MessageDatabase? = null

        fun getDatabase(context: Context): MessageDatabase {

            return INSTANCE ?: synchronized(this) {

                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    MessageDatabase::class.java,
                    "itantra_database"
                )
                    .addMigrations(MIGRATION_1_2)
                    .build()

                INSTANCE = instance

                instance
            }
        }
    }
}
