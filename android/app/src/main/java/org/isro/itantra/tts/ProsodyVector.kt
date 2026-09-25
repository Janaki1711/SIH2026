package org.isro.itantra.tts

import java.nio.ByteBuffer
import java.nio.ByteOrder

data class ProsodyVector(
    val f0PitchMean: Float = 140.0f,
    val f0PitchVariance: Float = 15.0f,
    val cadenceRate: Float = 1.0f,
    val rmsEnergy: Float = 0.5f,
    val urgencyLevel: Byte = 0
) {
    fun toByteArray(): ByteArray {
        val buffer = ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN)
        buffer.putFloat(f0PitchMean)
        buffer.putFloat(f0PitchVariance)
        buffer.putFloat(cadenceRate)
        buffer.putFloat(rmsEnergy)
        return buffer.array()
    }

    companion object {
        fun fromByteArray(bytes: ByteArray): ProsodyVector {
            if (bytes.size < 16) {
                return ProsodyVector()
            }
            val buffer = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)
            val pitch = buffer.float
            val variance = buffer.float
            val cadence = buffer.float
            val energy = buffer.float
            return ProsodyVector(
                f0PitchMean = pitch,
                f0PitchVariance = variance,
                cadenceRate = cadence,
                rmsEnergy = energy,
                urgencyLevel = 0
            )
        }
    }
}
