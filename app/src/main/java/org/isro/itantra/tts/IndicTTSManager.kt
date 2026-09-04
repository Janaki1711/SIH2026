package org.isro.itantra.tts

import android.content.Context
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

class IndicTTSManager(private val context: Context) : TextToSpeech.OnInitListener {

    private val nativeBridge = NativeTTSBridge()
    private val alarmRouter = AlarmAudioRouter(context)
    private var androidTts: TextToSpeech? = null
    private var isTtsReady = false

    companion object {
        private const val TAG = "iTantra_TTSManager"
    }

    init {
        nativeBridge.startPlayer(16000)
        androidTts = TextToSpeech(context, this)
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.language = Locale("hi", "IN")
            Log.i(TAG, "Android TTS fallback initialized.")
        }
    }

    fun speak(text: String, langCode: String, prosody: ProsodyVector = ProsodyVector()) {
        if (NativeTTSBridge.isNativeAvailable()) {
            val pcm = nativeBridge.synthesize(text, langCode, prosody)
            if (pcm.isNotEmpty()) {
                nativeBridge.enqueueAudio(pcm)
                return
            }
        }

        if (isTtsReady && androidTts != null) {
            val locale = when (langCode.lowercase()) {
                "hi" -> Locale("hi", "IN")
                "ta" -> Locale("ta", "IN")
                "te" -> Locale("te", "IN")
                "kn" -> Locale("kn", "IN")
                "ml" -> Locale("ml", "IN")
                "mr" -> Locale("mr", "IN")
                "gu" -> Locale("gu", "IN")
                "bn" -> Locale("bn", "IN")
                "or" -> Locale("or", "IN")
                else -> Locale.ENGLISH
            }
            androidTts?.language = locale
            androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantraTTS")
        }
    }

    fun playEmergencyAlert(text: String, langCode: String) {
        alarmRouter.enforceEmergencyAudioRoute()
        nativeBridge.setVolume(2.0f)

        val sirenPcm = nativeBridge.generateSiren(1.2f)
        if (sirenPcm.isNotEmpty()) {
            nativeBridge.enqueueAudio(sirenPcm)
        }

        val emergencyProsody = ProsodyVector(
            f0PitchMean = 180.0f,
            f0PitchVariance = 25.0f,
            cadenceRate = 1.25f,
            rmsEnergy = 1.0f,
            urgencyLevel = 2
        )
        speak(text, langCode, emergencyProsody)
    }

    fun stop() {
        nativeBridge.stopPlayer()
        androidTts?.stop()
        alarmRouter.restoreAudioRoute()
    }

    fun shutdown() {
        stop()
        nativeBridge.release()
        androidTts?.shutdown()
    }
}
