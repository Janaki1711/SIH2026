package org.isro.itantra.tts

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
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
                audioManager.setStreamVolume(AudioManager.STREAM_MUSIC, (maxVol * 0.85).toInt(), 0)
            }
        } catch (e: Exception) {
            Log.w(TAG, "Could not adjust system volume: " + e.message)
        }
    }

    private fun initAndroidTts() {
        try {
            androidTts = TextToSpeech(context.applicationContext, this)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to initialize Android TextToSpeech", e)
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.language = Locale.ENGLISH
            androidTts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    postStatus("SPEAKING: Android Voice Active")
                }
                override fun onDone(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE (RX READY)")
                }
                override fun onError(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK DONE")
                }
            })
            Log.i(TAG, "Android TTS successfully initialized.")
            postStatus("STATE: TTS READY (NATIVE + OS ENGINE)")
        } else {
            Log.w(TAG, "Android TTS onInit returned " + status)
            postStatus("STATE: NATIVE C++20 ENGINE READY")
        }
    }

    fun speak(text: String, langCode: String, prosody: ProsodyVector = ProsodyVector()) {
        postStatus("SYNTHESIZING: '" + text + "' [" + langCode + "]")
        Log.i(TAG, "Synthesizing and playing speech: text='" + text + "', lang='" + langCode + "'")

        initSystemVolume()

        audioExecutor.execute {
            try {
                val pcm = nativeBridge.synthesize(text, langCode, prosody)
                if (pcm.isNotEmpty()) {
                    Log.i(TAG, "Native PCM generated: " + pcm.size + " samples.")
                    playPcmViaAudioTrack(pcm, isAlarm = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in native PCM playback", e)
            }
        }

        if (isTtsReady && androidTts != null) {
            mainHandler.post {
                try {
                    val locale = getLocaleForLang(langCode)
                    val langResult = androidTts?.setLanguage(locale)
                    if (langResult == TextToSpeech.LANG_MISSING_DATA || langResult == TextToSpeech.LANG_NOT_SUPPORTED) {
                        androidTts?.language = Locale.ENGLISH
                    }
                    androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantra_" + System.currentTimeMillis())
                } catch (e: Exception) {
                    Log.e(TAG, "Error triggering Android TTS", e)
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

    private fun playPcmViaAudioTrack(pcm: FloatArray, isAlarm: Boolean) {
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

            val bufferSize = Math.max(minBufferSize, pcm.size * 4)

            track = AudioTrack.Builder()
                .setAudioAttributes(audioAttributes)
                .setAudioFormat(audioFormat)
                .setBufferSizeInBytes(bufferSize)
                .setTransferMode(AudioTrack.MODE_STATIC)
                .build()

            track.write(pcm, 0, pcm.size, AudioTrack.WRITE_BLOCKING)
            track.play()

            val playDurationMs = (pcm.size * 1000L) / SAMPLE_RATE
            Thread.sleep(playDurationMs + 50)
        } catch (e: Exception) {
            Log.e(TAG, "Error playing PCM via AudioTrack", e)
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
        nativeBridge.setVolume(2.0f)

        audioExecutor.execute {
            val sirenPcm = nativeBridge.generateSiren(1.5f)
            if (sirenPcm.isNotEmpty()) {
                playPcmViaAudioTrack(sirenPcm, isAlarm = true)
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
                playPcmViaAudioTrack(pcm, isAlarm = true)
            }
        }

        mainHandler.post {
            if (isTtsReady && androidTts != null) {
                androidTts?.language = Locale.ENGLISH
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
