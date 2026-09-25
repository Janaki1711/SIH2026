package org.isro.itantra.tts

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Build
import android.util.Log

class AlarmAudioRouter(private val context: Context) {

    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager
    private var originalVolume: Int = -1
    private var focusRequest: AudioFocusRequest? = null

    companion object {
        private const val TAG = "iTantra_AlarmRouter"
    }

    fun enforceEmergencyAudioRoute() {
        try {
            originalVolume = audioManager.getStreamVolume(AudioManager.STREAM_ALARM)
            val maxVolume = audioManager.getStreamMaxVolume(AudioManager.STREAM_ALARM)
            audioManager.setStreamVolume(AudioManager.STREAM_ALARM, maxVolume, AudioManager.FLAG_SHOW_UI)

            val audioAttributes = AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                .setFlags(AudioAttributes.FLAG_AUDIBILITY_ENFORCED)
                .build()

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                focusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE)
                    .setAudioAttributes(audioAttributes)
                    .setOnAudioFocusChangeListener { /* maintain priority */ }
                    .build()
                focusRequest?.let { audioManager.requestAudioFocus(it) }
            } else {
                @Suppress("DEPRECATION")
                audioManager.requestAudioFocus(
                    null,
                    AudioManager.STREAM_ALARM,
                    AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_EXCLUSIVE
                )
            }
            Log.i(TAG, "Emergency Audio Route enforced: STREAM_ALARM max volume.")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to enforce emergency audio route", e)
        }
    }

    fun restoreAudioRoute() {
        try {
            if (originalVolume >= 0) {
                audioManager.setStreamVolume(AudioManager.STREAM_ALARM, originalVolume, 0)
                originalVolume = -1
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                focusRequest?.let { audioManager.abandonAudioFocusRequest(it) }
            } else {
                @Suppress("DEPRECATION")
                audioManager.abandonAudioFocus(null)
            }
            Log.i(TAG, "Normal audio route restored.")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to restore audio route", e)
        }
    }
}
