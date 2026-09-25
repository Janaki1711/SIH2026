package org.isro.itantra.database

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface EmergencyCodebookDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertCode(code: EmergencyCodebook)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(codes: List<EmergencyCodebook>)

    @Query("SELECT * FROM emergency_codebook WHERE codeId = :codeId LIMIT 1")
    suspend fun getByCodeId(codeId: String): EmergencyCodebook?

    @Query("SELECT * FROM emergency_codebook WHERE priority = 'CRITICAL'")
    suspend fun getCriticalCodes(): List<EmergencyCodebook>

    @Query("SELECT * FROM emergency_codebook ORDER BY codeId ASC")
    suspend fun getAllCodes(): List<EmergencyCodebook>
}
