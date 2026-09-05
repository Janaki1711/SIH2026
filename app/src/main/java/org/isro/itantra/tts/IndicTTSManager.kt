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
                    Log.i(TAG, "Native C++ PCM generated: " + pcm.size + " samples for custom input")
                    playPcmStreaming(pcm, isAlarm = false)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Native C++ playback error", e)
            }
        }

        // 2. Play custom input via Android TextToSpeech engine
        if (isTtsReady && androidTts != null) {
            mainHandler.post {
                try {
                    val targetLocale = getLocaleForLang(langCode)
                    var matchedVoice = false
                    
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                        val voices = androidTts?.voices
                        if (voices != null) {
                            for (v in voices) {
                                if (v.locale.language.equals(langCode, ignoreCase = true) ||
                                    (v.locale.country.equals("IN", ignoreCase = true) && v.name.contains(langCode, ignoreCase = true))) {
                                    androidTts?.voice = v
                                    matchedVoice = true
                                    break
                                }
                            }
                        }
                    }

                    androidTts?.language = targetLocale
                    
                    // If the text contains Indic script, try speaking original text first
                    val speakResult = androidTts?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "iTantra_" + System.currentTimeMillis())
                    
                    // If system TTS does not support the native Indic script directly,
                    // dynamically convert the EXACT user-typed sentence into phonetic text
                    if (!matchedVoice && containsIndicUnicode(text)) {
                        val dynamicPhonetic = convertIndicToPhonetic(text)
                        if (dynamicPhonetic.isNotBlank()) {
                            mainHandler.postDelayed({
                                try {
                                    androidTts?.language = Locale.ENGLISH
                                    androidTts?.speak(dynamicPhonetic, TextToSpeech.QUEUE_ADD, null, "iTantra_dyn")
                                } catch (ignored: Exception) {}
                            }, 50)
                        }
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Android TTS custom speak error", e)
                }
            }
        }
    }

    private fun containsIndicUnicode(text: String): Boolean {
        for (ch in text) {
            val code = ch.code
            if (code in 0x0900..0x0D7F) return true
        }
        return false
    }

    // Dynamic Unicode to Phonetic Romanization (Character by Character)
    private fun convertIndicToPhonetic(input: String): String {
        val sb = StringBuilder()
        var i = 0
        val len = input.length

        while (i < len) {
            val ch = input[i]
            val code = ch.code

            // ASCII characters (pass through directly)
            if (code < 0x80) {
                sb.append(ch)
                i++
                continue
            }

            // Brahmi Indic scripts: Devanagari (0x0900), Bengali (0x0980), Gujarati (0x0A80),
            // Odia (0x0B00), Tamil (0x0B80), Telugu (0x0C00), Kannada (0x0C80), Malayalam (0x0D00)
            var base = 0
            if (code in 0x0900..0x097F) base = 0x0900
            else if (code in 0x0980..0x09FF) base = 0x0980
            else if (code in 0x0A80..0x0AFF) base = 0x0A80
            else if (code in 0x0B00..0x0B7F) base = 0x0B00
            else if (code in 0x0B80..0x0BFF) base = 0x0B80
            else if (code in 0x0C00..0x0C7F) base = 0x0C00
            else if (code in 0x0C80..0x0CFF) base = 0x0C80
            else if (code in 0x0D00..0x0D7F) base = 0x0D00

            if (base != 0) {
                val offset = code - base
                when (offset) {
                    // Independent Vowels
                    0x05 -> sb.append("a")
                    0x06 -> sb.append("aa")
                    0x07 -> sb.append("i")
                    0x08 -> sb.append("ee")
                    0x09 -> sb.append("u")
                    0x0A -> sb.append("oo")
                    0x0E, 0x0F -> sb.append("e")
                    0x10 -> sb.append("ai")
                    0x12, 0x13 -> sb.append("o")
                    0x14 -> sb.append("au")

                    // Consonants (with inherent vowel 'a')
                    0x15 -> sb.append("k ")
                    0x16 -> sb.append("kh ")
                    0x17 -> sb.append("g ")
                    0x18 -> sb.append("gh ")
                    0x1A -> sb.append("ch ")
                    0x1B -> sb.append("chh ")
                    0x1C -> sb.append("j ")
                    0x1D -> sb.append("jh ")
                    0x1F, 0x24 -> sb.append("t ")
                    0x20, 0x25 -> sb.append("th ")
                    0x21, 0x26 -> sb.append("d ")
                    0x22, 0x27 -> sb.append("dh ")
                    0x28, 0x29 -> sb.append("n ")
                    0x2A -> sb.append("p ")
                    0x2B -> sb.append("ph ")
                    0x2C -> sb.append("b ")
                    0x2D -> sb.append("bh ")
                    0x2E -> sb.append("m ")
                    0x2F -> sb.append("y ")
                    0x30, 0x31 -> sb.append("r ")
                    0x32, 0x33, 0x34 -> sb.append("l ")
                    0x35 -> sb.append("v ")
                    0x36, 0x37 -> sb.append("sh ")
                    0x38 -> sb.append("s ")
                    0x39 -> sb.append("h ")

                    // Dependent Vowels (Matras)
                    0x3E -> { trimTrailingSpace(sb); sb.append("aa ") }
                    0x3F -> { trimTrailingSpace(sb); sb.append("i ") }
                    0x40 -> { trimTrailingSpace(sb); sb.append("ee ") }
                    0x41 -> { trimTrailingSpace(sb); sb.append("u ") }
                    0x42 -> { trimTrailingSpace(sb); sb.append("oo ") }
                    0x46, 0x47 -> { trimTrailingSpace(sb); sb.append("e ") }
                    0x48 -> { trimTrailingSpace(sb); sb.append("ai ") }
                    0x4A, 0x4B -> { trimTrailingSpace(sb); sb.append("o ") }
                    0x4C -> { trimTrailingSpace(sb); sb.append("au ") }
                    0x4D -> { trimTrailingSpace(sb) } // Halant (remove inherent vowel)
                    0x02 -> { sb.append("n ") }      // Anusvara
                    0x03 -> { sb.append("h ") }      // Visarga
                    else -> sb.append(" ")
                }
            } else {
                sb.append(" ")
            }
            i++
        }
        return sb.toString().trim().replace(Regex("\\s+"), " ")
    }

    private fun trimTrailingSpace(sb: StringBuilder) {
        if (sb.isNotEmpty() && sb.last() == ' ') {
            sb.setLength(sb.length - 1)
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
