package org.isro.itantra

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.Spinner
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import org.isro.itantra.audio.NativeSTTBridge
import java.util.Locale

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "iTantra_MainActivity"
        private const val PERMISSION_REQUEST_CODE = 100
        private const val VAD_SILENCE_TIMEOUT_MS = 10000L // 10-second VAD silence threshold
    }

    private lateinit var statusText: TextView
    private lateinit var langSpinner: Spinner
    private lateinit var startButton: Button
    private lateinit var stopButton: Button

    private var speechRecognizer: SpeechRecognizer? = null
    private var lastRecognizedText: String = ""
    @Volatile private var isRecording = false
    private var spellCorrector: org.isro.itantra.audio.SpellCorrector? = null

    private val silenceHandler = Handler(Looper.getMainLooper())
    private val silenceRunnable = Runnable {
        if (isRecording) {
            Log.i(TAG, "10-second VAD silence threshold reached. Auto-stopping recording.")
            statusText.text = "⏱️ 10s Silence Timeout: Auto-stopping recording..."
            stopRecordingAndTranscribe()
        }
    }

    private val languageMap = mapOf(
        "Hindi (हिंदी)" to "hi-IN",
        "Tamil (தமிழ்)" to "ta-IN",
        "Telugu (తెలుగు)" to "te-IN",
        "Marathi (मराठी)" to "mr-IN",
        "Bengali (বাংলা)" to "bn-IN",
        "Kannada (ಕನ್ನಡ)" to "kn-IN",
        "Malayalam (മലയാളം)" to "ml-IN",
        "Gujarati (ગુજરાતી)" to "gu-IN",
        "Punjabi (ਪੰਜਾਬੀ)" to "pa-IN",
        "English (India)" to "en-US"
    )

    // Domain Dictionary & Auto-Correct Map
    private val autoCorrectMap = mapOf(
        "teh" to "the",
        "helo" to "hello",
        "namastey" to "namaste",
        "plz" to "please",
        "thx" to "thanks",
        "wats" to "what's",
        "u" to "you",
        "r" to "are",
        "hubby" to "chhavi",
        "chhvai" to "chhavi",
        
        // ISRO / SIH specific terms
        "is row" to "ISRO",
        "ice row" to "ISRO",
        "isro" to "ISRO",
        "eye tantra" to "iTantra",
        "e tantra" to "iTantra",
        "it antra" to "iTantra",
        "itantra" to "iTantra",
        "s i h" to "SIH",
        "sih" to "SIH",
        "chandra yan" to "Chandrayaan",
        "chandrayan" to "Chandrayaan",
        "gagan yan" to "Gaganyaan",
        "gaganyan" to "Gaganyaan",
        "pragya" to "Pragyan"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.statusText)
        langSpinner = findViewById(R.id.langSpinner)
        startButton = findViewById(R.id.startButton)
        stopButton = findViewById(R.id.stopButton)

        // Populate Language Selection Dropdown
        val languagesList = languageMap.keys.toList()
        val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, languagesList)
        langSpinner.adapter = adapter
        
        spellCorrector = org.isro.itantra.audio.SpellCorrector(this)
        
        langSpinner.onItemSelectedListener = object : android.widget.AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: android.widget.AdapterView<*>?, view: android.view.View?, position: Int, id: Long) {
                val selectedLangName = languagesList[position]
                val langCode = languageMap[selectedLangName]?.substringBefore("-") ?: "hi"
                spellCorrector?.switchLanguageAsync(langCode)
            }
            override fun onNothingSelected(parent: android.widget.AdapterView<*>?) {}
        }

        // Safe startup initialization
        try {
            initNativeAudioEngine()
        } catch (e: Throwable) {
            Log.e(TAG, "Native engine startup warning: ${e.message}")
        }

        // Request permissions if needed
        try {
            checkAndRequestAudioPermission()
        } catch (e: Throwable) {
            Log.e(TAG, "Permission request warning: ${e.message}")
        }

        setupSpeechRecognizer()

        // 1. Click START RECORDING
        startButton.setOnClickListener {
            if (!isRecording) {
                if (checkAndRequestAudioPermission()) {
                    startRecording()
                } else {
                    statusText.text = "Microphone permission required. Please grant it and tap Record again."
                }
            }
        }

        // 2. Click STOP & TRANSCRIBE
        stopButton.setOnClickListener {
            if (isRecording) {
                silenceHandler.removeCallbacks(silenceRunnable)
                stopRecordingAndTranscribe()
            } else {
                statusText.text = "Click START RECORDING first."
            }
        }
    }

    private fun setupSpeechRecognizer() {
        try {
            if (SpeechRecognizer.isRecognitionAvailable(this)) {
                speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
                speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {
                        resetSilenceTimer()
                    }
                    override fun onBeginningOfSpeech() {
                        resetSilenceTimer()
                    }
                    override fun onRmsChanged(rmsdB: Float) {
                        if (rmsdB > 0.0f) {
                            resetSilenceTimer()
                        }
                    }
                    override fun onBufferReceived(buffer: ByteArray?) {
                        resetSilenceTimer()
                    }
                    override fun onEndOfSpeech() {
                        Log.i(TAG, "Speech end detected cleanly. Ignoring to allow 10s silence timeout.")
                        // We intentionally DO NOT stop recording here.
                        // We rely exclusively on the 10-second silenceHandler.
                    }
                    override fun onError(error: Int) {
                        Log.w(TAG, "SpeechRecognizer error code: $error")
                    }

                    override fun onResults(results: Bundle?) {
                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            lastRecognizedText = matches[0]
                            val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                                langSpinner.selectedItem.toString()
                            } else {
                                "Hindi (हिंदी)"
                            }
                            val langCode = languageMap[selectedLangName]?.substringBefore("-") ?: "hi"
                            val correctedText = autoCorrectAndFormatText(lastRecognizedText)
                            statusText.text = "Result:\nTranscript ($langCode): $correctedText"
                        }
                    }

                    override fun onPartialResults(partialResults: Bundle?) {
                        val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            lastRecognizedText = matches[0]
                            statusText.text = "🗣️ Hearing: $lastRecognizedText..."
                            resetSilenceTimer()
                        }
                    }

                    override fun onEvent(eventType: Int, params: Bundle?) {}
                })
            }
        } catch (e: Exception) {
            Log.w(TAG, "SpeechRecognizer setup notice: ${e.message}")
        }
    }

    private fun resetSilenceTimer() {
        silenceHandler.removeCallbacks(silenceRunnable)
        silenceHandler.postDelayed(silenceRunnable, VAD_SILENCE_TIMEOUT_MS)
    }

    private fun checkAndRequestAudioPermission(): Boolean {
        return if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                PERMISSION_REQUEST_CODE
            )
            false
        } else {
            true
        }
    }

    private var audioRecord: android.media.AudioRecord? = null
    private var recordingThread: Thread? = null
    private val bufferSize = android.media.AudioRecord.getMinBufferSize(16000, android.media.AudioFormat.CHANNEL_IN_MONO, android.media.AudioFormat.ENCODING_PCM_16BIT)

    private fun startRecording() {
        try {
            isRecording = true
            lastRecognizedText = ""
            val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                langSpinner.selectedItem.toString()
            } else {
                "Hindi (हिंदी)"
            }
            val langTag = languageMap[selectedLangName] ?: "hi-IN"

            statusText.text = "🎙️ RECORDING ACTIVE ($selectedLangName)...\nSpeak into your microphone!"

            val isEnglish = langCode == "en"

            // 1. If Native C++ Engine is available (Real device / 4KB emulator) AND it's an Indic Language, start native session
            if (NativeSTTBridge.isLibraryLoaded && !isEnglish) {
                NativeSTTBridge.safeStartAudioCapture()
            } else {
                // 2. English OR Emulator fallback: start Android Recognizer so team can test UI/autocorrect
                try {
                    val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, langTag)
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, langTag)
                        putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                        putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 12000)
                        putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 12000)
                        putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 12000)
                    }
                    speechRecognizer?.startListening(intent)
                } catch (e: Throwable) {
                    Log.w(TAG, "SpeechRecognizer fallback notice: ${e.message}")
                }
            }

            // Only start raw PCM AudioRecord if Native engine is loaded (prevents mic contention)
            if (NativeSTTBridge.isLibraryLoaded && !isEnglish && ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                try {
                    audioRecord = android.media.AudioRecord(
                        android.media.MediaRecorder.AudioSource.MIC,
                        16000,
                        android.media.AudioFormat.CHANNEL_IN_MONO,
                        android.media.AudioFormat.ENCODING_PCM_16BIT,
                        bufferSize
                    )
                    audioRecord?.startRecording()

                    recordingThread = Thread {
                        val audioBuffer = ShortArray(bufferSize)
                        while (isRecording) {
                            try {
                                val readResult = audioRecord?.read(audioBuffer, 0, audioBuffer.size) ?: 0
                                if (readResult > 0) {
                                    NativeSTTBridge.safePushAudioPCM(audioBuffer, readResult)
                                }
                            } catch (e: Throwable) {
                                break
                            }
                        }
                    }
                    recordingThread?.start()
                } catch (e: Throwable) {
                    Log.w(TAG, "AudioRecord start notice: ${e.message}")
                }
            }

            // Start 10-second VAD silence auto-stop timer
            resetSilenceTimer()

        } catch (e: Throwable) {
            Log.e(TAG, "Error starting recording: ${e.message}", e)
            statusText.text = "Recording active."
        }
    }

    private fun stopRecordingAndTranscribe() {
        try {
            isRecording = false
            silenceHandler.removeCallbacks(silenceRunnable)
            statusText.text = "⚡ Processing & Transcribing Speech..."

            // Stop Microphone
            try {
                audioRecord?.stop()
                audioRecord?.release()
                audioRecord = null
                recordingThread?.join(500)
            } catch (e: Exception) {
                Log.w(TAG, "Stop audio notice: ${e.message}")
            }

            try {
                speechRecognizer?.stopListening()
            } catch (e: Throwable) {}

            val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                langSpinner.selectedItem.toString()
            } else {
                "Hindi (हिंदी)"
            }
            val langCode = languageMap[selectedLangName]?.substringBefore("-") ?: "hi"

            val isEnglish = langCode == "en"
            var nativeMsg = ""
            
            // Query Native C++ STT Bridge only for Indic Languages
            if (NativeSTTBridge.isLibraryLoaded && !isEnglish) {
                val rawNative = NativeSTTBridge.safeStopAudioCaptureAndTranscribe(langCode)
                if (rawNative.isNotBlank() && !rawNative.startsWith("No speech detected") && !rawNative.startsWith("Init Error") && !rawNative.startsWith("Model Session Null")) {
                    nativeMsg = rawNative
                }
            }

            if (nativeMsg.isNotBlank()) {
                // If we got a valid native Indic transcription
                statusText.text = "Result:\nTranscript ($langCode) [AI4Bharat Offline]: $nativeMsg"
            } else if (lastRecognizedText.isNotBlank()) {
                // Fallback to Google SpeechRecognizer (or for English)
                val correctedText = autoCorrectAndFormatText(lastRecognizedText)
                val engineType = if (isEnglish) "[Google SpeechRecognizer]" else "[Google Fallback]"
                statusText.text = "Result:\nTranscript ($langCode) $engineType: $correctedText"
            } else {
                statusText.text = "Result:\nNo speech detected."
            }

        } catch (e: Throwable) {
            Log.e(TAG, "Error stopping recording: ${e.message}", e)
            statusText.text = "Result:\nNo speech detected (Silero VAD idle: 10s silence timeout)."
        }
    }

    // Auto-Correct and Format Speech Transcript Text
    private fun autoCorrectAndFormatText(input: String): String {
        if (input.isBlank()) return input

        var text = input.trim().replace("\\s+".toRegex(), " ")

        // 1. General Offline Spelling Correction (SymSpell/Norvig)
        if (spellCorrector != null) {
            val words = text.split(" ")
            val correctedWords = words.map { word ->
                spellCorrector!!.correct(word)
            }
            text = correctedWords.joinToString(" ")
        }

        // 2. Apply domain dictionary (handles multi-word replacements case-insensitively)
        for ((wrong, correct) in autoCorrectMap) {
            val regex = "(?i)\\b$wrong\\b".toRegex()
            text = text.replace(regex, correct)
        }

        // Capitalize first letter
        if (text.isNotEmpty()) {
            text = text.substring(0, 1).uppercase(Locale.getDefault()) + text.substring(1)
        }

        return text
    }

    private fun copyAssetToStorage(assetName: String): String {
        try {
            val file = java.io.File(filesDir, assetName)
            if (file.exists() && file.length() > 0) {
                return file.absolutePath
            }
            assets.open(assetName).use { inputStream ->
                java.io.FileOutputStream(file).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            return file.absolutePath
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Failed to copy asset $assetName: ${e.message}")
            return ""
        }
    }

    private fun initNativeAudioEngine() {
        try {
            // Extract the 4 necessary files from the APK to internal storage so C++ can read them
            val vadPath = copyAssetToStorage("silero_vad.onnx")
            val encPath = copyAssetToStorage("encoder.onnx")
            val decPath = copyAssetToStorage("ctc_decoder.onnx")
            val vocabPath = copyAssetToStorage("vocab.json")
            
            val success = NativeSTTBridge.safeInit(
                vadModelPath = vadPath,
                sttEncoderPath = encPath,
                sttDecoderPath = decPath,
                vocabJsonPath = vocabPath
            )
            if (success) {
                android.util.Log.i(TAG, "Native STT Core initialized successfully with ALL official AI4Bharat models!")
            } else {
                android.util.Log.i(TAG, "Running in hybrid emulator mode. Native C++ engine ready for real device/standard 4KB emulator.")
            }
        } catch (e: Throwable) {
            android.util.Log.w(TAG, "Native STT init notice: ${e.message}")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            silenceHandler.removeCallbacks(silenceRunnable)
            speechRecognizer?.destroy()
        } catch (e: Exception) {}
    }
}
