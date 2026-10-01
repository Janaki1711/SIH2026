package org.isro.itantra.database

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * EmergencyCodebook — Table 3 as per iTantra README Database Architecture.
 * Offline macro lookup table: short codes expand to full Indic-language emergency messages.
 */
@Entity(tableName = "emergency_codebook")
data class EmergencyCodebook(
    @PrimaryKey
    val codeId: String,                     // e.g. "SOS_FIRE", "SOS_FLOOD", "SOS_AMBULANCE"
    val shortMacro: String = "",            // e.g. "FIRE"
    val expandedTextHi: String = "",        // Hindi
    val expandedTextTa: String = "",        // Tamil
    val expandedTextTe: String = "",        // Telugu
    val expandedTextMr: String = "",        // Marathi
    val expandedTextBn: String = "",        // Bengali
    val expandedTextKn: String = "",        // Kannada
    val expandedTextMl: String = "",        // Malayalam
    val expandedTextGu: String = "",        // Gujarati
    val expandedTextOr: String = "",        // Odia
    val expandedTextEn: String = "",        // English fallback
    val priority: String = "CRITICAL"       // "ROUTINE", "TACTICAL", "CRITICAL"
)
