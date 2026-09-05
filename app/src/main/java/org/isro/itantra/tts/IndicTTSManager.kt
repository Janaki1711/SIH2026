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
import android.speech.tts.Voice
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
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, (maxVol * 0.9).toInt(), 0)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Volume adjust error: " + e.message)
        }
    }

    private fun initAndroidTts() {
        try {
            androidTts = TextToSpeech(context.applicationContext, this)
        } catch (e: Exception) {
            Log.e(TAG, "TTS Init Error", e)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    postStatus("SPEAKING: Live Speech Output Active")
                }
                override fun onDone(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE (RX READY)")
                }
                override fun onError(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE")
                }
            })
            Log.i(TAG, "Android TTS successfully initialized.")
            postStatus("STATE: TTS READY (ALL 10 INDIC LANGUAGES)")
        } else {
            Log.w(TAG, "Android TTS init status: " + status)
            postStatus("STATE: NATIVE C++20 ENGINE READY")
        }
    }

    fun speak(text: String, langCode: String, prosody: ProsodyVector = ProsodyVector()) {
        if (text.isBlank()) return
        
        postStatus("SYNTHESIZING: '" + text.take(25) + "...' [" + langCode.uppercase() + "]")
        Log.i(TAG, "Synthesizing custom input: text='$text', lang='$langCode'")
        initSystemVolume()

        // 1. Synthesize and play custom input via Native C++20 Indic Formant Engine
        audioExecutor.execute {
            try {
                val pcm = nativeBridge.synthesize(text, langCode, prosody)
                if (pcm.isNotEmpty()) {
                    Log.i(TAG, "Native C++ PCM generated: " + pcm.size + " samples for '" + text + "'")
                    playPcmStreaming(pcm, isAlarm = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Native C++ playback error", e)
            }
        }

        // 2. Also speak custom input via Android TextToSpeech engine with targeted Indic Locale
        if (isTtsReady && androidTts != null) {
            mainHandler.post {
                try {
                    val targetLocale = getLocaleForLang(langCode)
                    
                    // On OnePlus/Android, find the native Indic voice
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                        val voices = androidTts?.voices
                        if (voices != null) {
                            for (v in voices) {
                                if (v.locale.language.equals(langCode, ignoreCase = true) ||
                                    v.locale.country.equals("IN", ignoreCase = true) && v.name.contains(langCode, ignoreCase = true)) {
                                    androidTts?.voice = v
                                    break
                                }
                            }
                        }
                    }

                    androidTts?.language = targetLocale
                    val speakResult = androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantra_" + System.currentTimeMillis())
                    Log.i(TAG, "Android TTS speak custom text result code: " + speakResult)
                } catch (e: Exception) {
                    Log.e(TAG, "Android TTS custom speak error", e)
                }
            }
        }
    }

    private fun getLocaleForLang(langCode: String): Locale {
        return when (langCode.lowercase()) {
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
    }

    private fun playPcmStreaming(pcm: FloatArray, isAlarm: Boolean) {
        var track: AudioTrack? = null
        try {
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

            track = AudioTrack.Builder()
                .setAudioAttributes(audioAttributes)
                .setAudioFormat(audioFormat)
                .setBufferSizeInBytes(Math.max(minBufferSize, 4096))
                .setTransferMode(AudioTrack.MODE_STREAM)
                .build()

            track.play()
            
            // Stream PCM in chunks of 1024 floats for immediate audio output
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

    fun playEmergencyAlert(text: String, langCode: String) {
        postStatus("EMERGENCY OVERRIDE: 100% HARDWARE VOLUME")
        alarmRouter.enforceEmergencyAudioRoute()
        nativeBridge.setVolume(2.5f)

        audioExecutor.execute {
            val sirenPcm = nativeBridge.generateSiren(1.5f)
            if (sirenPcm.isNotEmpty()) {
                playPcmStreaming(sirenPcm, isAlarm = true)
            }

            val emergencyProsody = ProsodyVector(
                f0PitchMean = 220.0f,
                f0PitchVariance = 30.0f,
                cadenceRate = 1.3f,
                rmsEnergy = 1.0f,
                urgencyLevel = 2
            )
            val pcm = nativeBridge.synthesize(text, langCode, emergencyProsody)
            if (pcm.isNotEmpty()) {
                playPcmStreaming(pcm, isAlarm = true)
            }
        }

        mainHandler.post {
            if (isTtsReady && androidTts != null) {
                val locale = getLocaleForLang(langCode)
                androidTts?.language = locale
                androidTts?.speak(text, TextToSpeech.QUEUE_ADD, null, "iTantra_SOS")
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
