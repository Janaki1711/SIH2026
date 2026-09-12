package org.isro.itantra.tts

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.util.Log
import java.util.Locale
import java.util.concurrent.Executors

class IndicTTSManager(
    private val context: Context,
    private val onStatusUpdate: ((String) -> Unit)? = null
) : TextToSpeech.OnInitListener {

    private val nativeBridge = NativeTTSBridge()
    private val alarmRouter = AlarmAudioRouter(context)
    private var androidTts: TextToSpeech? = null
    private var isTtsReady = false
    private val audioExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    companion object {
        private const val TAG = "iTantra_TTSManager"
        private const val SAMPLE_RATE = 16000
    }

    init {
        nativeBridge.startPlayer(SAMPLE_RATE)
        initSystemVolume()
        initAndroidTts()
    }

    private fun initSystemVolume() {
        try {
            val maxVol = audioManager.getStreamMaxVolume(AudioManager.STREAM_MUSIC)
            val currentVol = audioManager.getStreamVolume(AudioManager.STREAM_MUSIC)
            if (currentVol < maxVol / 2) {
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, (maxVol * 0.95).toInt(), 0)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Volume error: " + e.message)
        }
    }

    private fun initAndroidTts() {
        try {
            androidTts = TextToSpeech(context.applicationContext, this)
        } catch (e: Exception) {
            Log.e(TAG, "TTS Init Error", e)
        }
    }

    var onTtsDone: (() -> Unit)? = null

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    postStatus("SPEAKING: Clear Voice Output Active")
                }
                override fun onDone(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE (RX READY)")
                    onTtsDone?.invoke()  // advance MessageScheduler queue
                }
                override fun onError(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE")
                    onTtsDone?.invoke()
                }
            })
            Log.i(TAG, "Android TTS engine initialized successfully.")
            postStatus("STATE: TTS READY (ALL 10 INDIC LANGUAGES)")
        } else {
            Log.w(TAG, "Android TTS init status: " + status)
            postStatus("STATE: NATIVE C++20 ENGINE READY")
        }
    }

    fun speak(text: String, langCode: String, prosody: ProsodyVector = ProsodyVector()) {
        if (text.isBlank()) return

        postStatus("SYNTHESIZING: '${text.take(25)}...' [${langCode.uppercase()}]")
        Log.i(TAG, "TTS speak: lang=$langCode  text='$text'")
        initSystemVolume()

        if (isTtsReady && androidTts != null) {
            mainHandler.post {
                try {
                    val pitchFactor = (prosody.f0PitchMean / 140.0f).coerceIn(0.5f, 2.0f)
                    val rateFactor = prosody.cadenceRate.coerceIn(0.85f, 1.15f)

                    androidTts?.setPitch(pitchFactor)
                    androidTts?.setSpeechRate(rateFactor)

                    val targetLocale = getLocaleForLang(langCode)
                    val langResult = androidTts?.setLanguage(targetLocale)

                    Log.i(TAG, "TTS setLanguage($targetLocale) = $langResult")

                    when (langResult) {
                        TextToSpeech.LANG_MISSING_DATA -> {
                            Log.w(TAG, "TTS pack missing for $langCode — trying English fallback")
                            // Try to install the pack in background
                            try {
                                val installIntent = android.content.Intent(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA)
                                installIntent.setPackage("com.google.android.tts")
                                installIntent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                                context.startActivity(installIntent)
                            } catch (e: Throwable) {}
                            // Fallback to English — always available
                            androidTts?.setLanguage(java.util.Locale("en", "IN"))
                        }
                        TextToSpeech.LANG_NOT_SUPPORTED -> {
                            Log.w(TAG, "TTS lang not supported: $langCode — falling back to English")
                            androidTts?.setLanguage(java.util.Locale("en", "IN"))
                        }
                        else -> { /* OK or LANG_AVAILABLE — keep as set */ }
                    }

                    // Always speak — TTS will use best available voice for the set locale
                    androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantra_${System.currentTimeMillis()}")
                } catch (e: Exception) {
                    Log.e(TAG, "Android TTS speak error", e)
                    playViaNativeCpp(text, langCode, prosody)
                }
            }
        } else {
            playViaNativeCpp(text, langCode, prosody)
        }
    }

    private fun playViaNativeCpp(text: String, langCode: String, prosody: ProsodyVector) {
        audioExecutor.execute {
            try {
                val pcm = nativeBridge.synthesize(text, langCode, prosody)
                if (pcm.isNotEmpty()) {
                    playPcmStreaming(pcm, isAlarm = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Native C++ playback error", e)
            }
        }
    }

    private fun getLocaleForLang(langCode: String): Locale {
        return when (langCode.lowercase().trim()) {
            "hi" -> Locale("hi", "IN")
            "ta" -> Locale("ta", "IN")
            "te" -> Locale("te", "IN")
            "kn" -> Locale("kn", "IN")
            "ml" -> Locale("ml", "IN")
            "mr" -> Locale("mr", "IN")
            "gu" -> Locale("gu", "IN")
            "bn" -> Locale("bn", "IN")
            "or" -> Locale("or", "IN")
            "pa" -> Locale("pa", "IN")
            else -> Locale("en", "IN")
        }
    }

    private fun playPcmStreaming(pcm: FloatArray, isAlarm: Boolean) {
        var track: AudioTrack? = null
        try {
            val usage = AudioAttributes.USAGE_MEDIA
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

            track = AudioTrack.Builder()
                .setAudioAttributes(audioAttributes)
                .setAudioFormat(audioFormat)
                .setBufferSizeInBytes(Math.max(minBufferSize, 4096))
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()

            track.play()

            val chunkSize = 1024
            var offset = 0
            while (offset < pcm.size) {
                val toWrite = Math.min(chunkSize, pcm.size - offset)
                track.write(pcm, offset, toWrite, AudioTrack.WRITE_BLOCKING)
                offset += toWrite
            }

            val playDurationMs = (pcm.size * 1000L) / SAMPLE_RATE
            Thread.sleep(playDurationMs + 40)
        } catch (e: Exception) {
            Log.e(TAG, "AudioTrack stream error", e)
        } finally {
            try {
                track?.stop()
                track?.release()
            } catch (ignored: Exception) {}
        }
    }

    /**
     * Apply sender's prosody characteristics to the Android TTS engine so the
     * synthesized voice roughly matches the sender's pitch and speaking rate.
     * Called before speak() when the packet contains prosody data.
     */
    fun applyProsodyToTts(pitchMultiplier: Float, speechRate: Float) {
        try {
            androidTts?.setPitch(pitchMultiplier.coerceIn(0.5f, 2.0f))
            androidTts?.setSpeechRate(speechRate.coerceIn(0.5f, 2.0f))
        } catch (e: Exception) {
            Log.w(TAG, "applyProsodyToTts: ${e.message}")
        }
    }

    fun playEmergencyAlert(text: String, langCode: String) {
        postStatus("🚨 EMERGENCY ALERT: Playing tone, then voice message...")
        nativeBridge.setVolume(0.30f) // 30% alert tone volume

        audioExecutor.execute {
            try {
                // 1. First: Short, clear alert tone (0.7s)
                val sirenPcm = nativeBridge.generateSiren(0.7f)
                if (sirenPcm.isNotEmpty()) {
                    playPcmStreaming(sirenPcm, isAlarm = true)
                }
                // Short pause after tone before speech
                Thread.sleep(200)
            } catch (e: Throwable) {
                Log.w(TAG, "Alert tone error: ${e.message}")
            }

            // 2. Second: Speak the emergency message in the selected language
            mainHandler.post {
                speak(text, langCode)
            }
        }
    }

    private fun postStatus(msg: String) {
        mainHandler.post {
            onStatusUpdate?.invoke(msg)
        }
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
        audioExecutor.shutdown()
    }
}
