package org.isro.itantra.tts

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.speech.tts.TextToSpeech
import android.util.Log
import java.util.Locale

class IndicTTSManager(private val context: Context) : TextToSpeech.OnInitListener {

    private val nativeBridge = NativeTTSBridge()
    private val alarmRouter = AlarmAudioRouter(context)
    private var androidTts: TextToSpeech? = null
    private var isTtsReady = false
    private var audioTrack: AudioTrack? = null

    companion object {
        private const val TAG = "iTantra_TTSManager"
        private const val SAMPLE_RATE = 16000
    }

    init {
        nativeBridge.startPlayer(SAMPLE_RATE)
        initAudioTrack(isAlarm = false)
        androidTts = TextToSpeech(context, this)
    }

    private fun initAudioTrack(isAlarm: Boolean) {
        try {
            audioTrack?.release()
            val usage = if (isAlarm) AudioAttributes.USAGE_ALARM else AudioAttributes.USAGE_MEDIA
            val contentType = if (isAlarm) AudioAttributes.CONTENT_TYPE_SONIFICATION else AudioAttributes.CONTENT_TYPE_SPEECH

            val audioAttributes = AudioAttributes.Builder()
                .setUsage(usage)
                .setContentType(contentType)
                .build()

            val audioFormat = AudioFormat.Builder()
                .setSampleRate(SAMPLE_RATE)
                .setEncoding(AudioFormat.ENCODING_PCM_FLOAT)
                .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                .build()

            val minBufferSize = AudioTrack.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_FLOAT
            )

            audioTrack = AudioTrack.Builder()
                .setAudioAttributes(audioAttributes)
                .setAudioFormat(audioFormat)
                .setBufferSizeInBytes(Math.max(minBufferSize, 32768))
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()

            audioTrack?.play()
        } catch (e: Exception) {
            Log.e(TAG, "AudioTrack init failed", e)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.language = Locale.ENGLISH
            Log.i(TAG, "Android TTS fallback initialized successfully.")
        }
    }

    fun speak(text: String, langCode: String, prosody: ProsodyVector = ProsodyVector()) {
        Log.i(TAG, "Synthesizing and playing speech: text='$text', lang='$langCode'")

        // 1. Synthesize via C++20 Native Engine
        val pcm = nativeBridge.synthesize(text, langCode, prosody)
        if (pcm.isNotEmpty()) {
            nativeBridge.enqueueAudio(pcm)
            playPcmViaAudioTrack(pcm)
        }

        // 2. Play through Android TextToSpeech engine
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

    private fun playPcmViaAudioTrack(pcm: FloatArray) {
        try {
            if (audioTrack == null || audioTrack?.state != AudioTrack.STATE_INITIALIZED) {
                initAudioTrack(isAlarm = false)
            }
            if (audioTrack?.playState != AudioTrack.PLAYSTATE_PLAYING) {
                audioTrack?.play()
            }
            audioTrack?.write(pcm, 0, pcm.size, AudioTrack.WRITE_BLOCKING)
        } catch (e: Exception) {
            Log.e(TAG, "Error writing to AudioTrack", e)
        }
    }

    fun playEmergencyAlert(text: String, langCode: String) {
        alarmRouter.enforceEmergencyAudioRoute()
        nativeBridge.setVolume(2.0f)
        initAudioTrack(isAlarm = true)

        // 1. Generate & play emergency siren
        val sirenPcm = nativeBridge.generateSiren(1.5f)
        if (sirenPcm.isNotEmpty()) {
            nativeBridge.enqueueAudio(sirenPcm)
            playPcmViaAudioTrack(sirenPcm)
        }

        // 2. Play spoken emergency text
        val emergencyProsody = ProsodyVector(
            f0PitchMean = 220.0f,
            f0PitchVariance = 30.0f,
            cadenceRate = 1.3f,
            rmsEnergy = 1.0f,
            urgencyLevel = 2
        )
        speak(text, langCode, emergencyProsody)
    }

    fun stop() {
        nativeBridge.stopPlayer()
        androidTts?.stop()
        audioTrack?.pause()
        audioTrack?.flush()
        alarmRouter.restoreAudioRoute()
    }

    fun shutdown() {
        stop()
        audioTrack?.release()
        audioTrack = null
        nativeBridge.release()
        androidTts?.shutdown()
    }
}
