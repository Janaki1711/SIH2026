package org.isro.itantra.tts

import android.content.Context
import android.util.Log

class PTTTransceiverController(
    private val context: Context,
    private val ttsManager: IndicTTSManager
) {
    enum class TransceiverMode {
        WALKIE_TALKIE_HALF_DUPLEX,
        PHONE_FULL_DUPLEX
    }

    private var currentMode = TransceiverMode.WALKIE_TALKIE_HALF_DUPLEX
    private var isTransmitting = false

    companion object {
        private const val TAG = "iTantra_PTTController"
    }

    fun setMode(mode: TransceiverMode) {
        currentMode = mode
        Log.i(TAG, "Switched transceiver mode to: $mode")
    }

    fun getMode(): TransceiverMode = currentMode

    fun onPttPressed(text: String, langCode: String) {
        isTransmitting = true
        Log.i(TAG, "PTT Pressed. Transmitting voice synthesis: $text in $langCode")
        ttsManager.speak(text, langCode)
    }

    fun onPttReleased() {
        isTransmitting = false
        Log.i(TAG, "PTT Released. Standby for RX.")
    }

    fun triggerEmergencySos(emergencyText: String, langCode: String) {
        Log.w(TAG, "TRIGGERING EMERGENCY SOS OVERRIDE")
        ttsManager.playEmergencyAlert(emergencyText, langCode)
    }

    fun shutdown() {
        ttsManager.shutdown()
    }
}
