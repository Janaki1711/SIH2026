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

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isTtsReady = true
            androidTts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    postStatus("SPEAKING: Indic Speech Output Active")
                }
                override fun onDone(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE (RX READY)")
                }
                override fun onError(utteranceId: String?) {
                    postStatus("STATE: PLAYBACK COMPLETE")
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

        postStatus("SYNTHESIZING: '" + text.take(25) + "...' [" + langCode.uppercase() + "]")
        Log.i(TAG, "Synthesizing custom input: text='$text', lang='$langCode'")
        initSystemVolume()

        // 1. Synthesize and play via Native C++20 Indic Formant Engine
        audioExecutor.execute {
            try {
                val pcm = nativeBridge.synthesize(text, langCode, prosody)
                if (pcm.isNotEmpty()) {
                    Log.i(TAG, "Native C++ PCM generated: " + pcm.size + " samples for custom input")
                    playPcmStreaming(pcm, isAlarm = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Native C++ playback error", e)
            }
        }

        // 2. Play via Android TextToSpeech engine with fallback
        if (isTtsReady && androidTts != null) {
            mainHandler.post {
                try {
                    val targetLocale = getLocaleForLang(langCode)
                    var matchedNativeVoice = false

                    // Look for an installed voice matching the target Indic language on the phone
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                        val voices = androidTts?.voices
                        if (voices != null) {
                            for (v in voices) {
                                if (v.locale.language.equals(langCode, ignoreCase = true) ||
                                    (v.locale.country.equals("IN", ignoreCase = true) && v.name.contains(langCode, ignoreCase = true))) {
                                    androidTts?.voice = v
                                    matchedNativeVoice = true
                                    break
                                }
                            }
                        }
                    }

                    val langResult = androidTts?.setLanguage(targetLocale)
                    val isLangAvailable = (langResult != TextToSpeech.LANG_MISSING_DATA && langResult != TextToSpeech.LANG_NOT_SUPPORTED)

                    if (matchedNativeVoice || isLangAvailable) {
                        // The phone has native Indic voice data installed (e.g. Hindi, Tamil, Telugu)
                        androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantra_" + System.currentTimeMillis())
                    } else {
                        // The phone does not have the voice pack downloaded (e.g. Kannada, Odia on some ROMs)
                        // Convert to fluent phonetic syllable romanization so Google TTS speaks the exact words
                        val phoneticSpeech = transliterateIndicToSyllables(text)
                        androidTts?.language = Locale.ENGLISH
                        androidTts?.speak(phoneticSpeech, TextToSpeech.QUEUE_FLUSH, null, "iTantra_phonetic")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Android TTS speak error", e)
                }
            }
        }
    }

    // Complete Syllable-Based Transliteration for all 10 Indian Scripts
    private fun transliterateIndicToSyllables(text: String): String {
        val consonants = mapOf(
            0x15 to "k", 0x16 to "kh", 0x17 to "g", 0x18 to "gh", 0x19 to "ng",
            0x1A to "ch", 0x1B to "chh", 0x1C to "j", 0x1D to "jh", 0x1E to "ny",
            0x1F to "t", 0x20 to "th", 0x21 to "d", 0x22 to "dh", 0x23 to "n",
            0x24 to "t", 0x25 to "th", 0x26 to "d", 0x27 to "dh", 0x28 to "n",
            0x2A to "p", 0x2B to "ph", 0x2C to "b", 0x2D to "bh", 0x2E to "m",
            0x2F to "y", 0x30 to "r", 0x31 to "r", 0x32 to "l", 0x33 to "l", 0x34 to "l", 0x35 to "v",
            0x36 to "sh", 0x37 to "sh", 0x38 to "s", 0x39 to "h"
        )
        val vowels = mapOf(
            0x05 to "a", 0x06 to "aa", 0x07 to "i", 0x08 to "ee", 0x09 to "u", 0x0A to "oo",
            0x0E to "e", 0x0F to "e", 0x10 to "ai", 0x12 to "o", 0x13 to "o", 0x14 to "au"
        )
        val matras = mapOf(
            0x3E to "aa", 0x3F to "i", 0x40 to "ee", 0x41 to "u", 0x42 to "oo",
            0x46 to "e", 0x47 to "ay", 0x48 to "ai", 0x4A to "o", 0x4B to "o", 0x4C to "au"
        )

        val sb = StringBuilder()
        var i = 0
        val len = text.length

        while (i < len) {
            val c = text[i].code
            if (c < 128) {
                sb.append(text[i])
                i++
                continue
            }

            var base = 0
            if (c in 0x0900..0x097F) base = 0x0900      // Devanagari (Hindi, Marathi)
            else if (c in 0x0C80..0x0CFF) base = 0x0C80 // Kannada
            else if (c in 0x0B80..0x0BFF) base = 0x0B80 // Tamil
            else if (c in 0x0C00..0x0C7F) base = 0x0C00 // Telugu
            else if (c in 0x0D00..0x0D7F) base = 0x0D00 // Malayalam
            else if (c in 0x0A80..0x0AFF) base = 0x0A80 // Gujarati
            else if (c in 0x0980..0x09FF) base = 0x0980 // Bengali
            else if (c in 0x0B00..0x0B7F) base = 0x0B00 // Odia

            if (base != 0) {
                val off = c - base
                if (vowels.containsKey(off)) {
                    sb.append(vowels[off])
                } else if (consonants.containsKey(off)) {
                    val cons = consonants[off] ?: ""
                    if (i + 1 < len) {
                        val nextOff = text[i + 1].code - base
                        if (matras.containsKey(nextOff)) {
                            sb.append(cons).append(matras[nextOff])
                            i++ // consume matra
                        } else if (nextOff == 0x4D) { // virama / halant
                            sb.append(cons)
                            i++ // consume virama
                        } else {
                            sb.append(cons).append("a")
                        }
                    } else {
                        sb.append(cons).append("a")
                    }
                } else if (off == 0x02) { // Anusvara
                    sb.append("m")
                } else if (off == 0x03) { // Visarga
                    sb.append("h")
                }
            }
            i++
        }
        return sb.toString()
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
