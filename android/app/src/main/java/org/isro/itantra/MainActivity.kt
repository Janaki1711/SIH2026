package org.isro.itantra

import android.Manifest
import android.content.Context
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
import android.widget.EditText
import android.widget.Spinner
import android.widget.TextView
import android.graphics.Color
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import org.isro.itantra.audio.NativeSTTBridge
import java.util.Locale

class MainActivity : AppCompatActivity() {
    private val myCallsign: String by lazy {
        val model = android.os.Build.MODEL.filter { it.isLetterOrDigit() }
        "NODE_" + if (model.isNotEmpty()) model.takeLast(6) else "${(1000..9999).random()}"
    }
    private var multicastLock: android.net.wifi.WifiManager.MulticastLock? = null
    private var wifiLock: android.net.wifi.WifiManager.WifiLock? = null
    private lateinit var stateMachine: org.isro.itantra.runtime.PTTStateMachine
    private lateinit var pttAudioAdapter: org.isro.itantra.runtime.PttAudioAdapter
    private var transport: org.isro.itantra.transport.wfbng.WfbngManager? = null

    private fun initPTTFoundation() {
        val database = org.isro.itantra.database.MessageDatabase.getDatabase(this)
        val logger = org.isro.itantra.runtime.CompositeTransitionLogger(
            listOf(
                org.isro.itantra.runtime.LogcatTransitionLogger(),
                org.isro.itantra.database.DatabaseTransitionLogger(database)
            )
        )
        stateMachine = org.isro.itantra.runtime.PTTStateMachine(logger = logger)
        org.isro.itantra.input.PttInputController(
            stateMachine = stateMachine,
            inputProvider = org.isro.itantra.input.ForegroundVolumePttProvider
        )
        pttAudioAdapter = org.isro.itantra.runtime.PttAudioAdapter(stateMachine)
        pttAudioAdapter.onTranscriptionResult = { text ->
            runOnUiThread { statusText.text = text }
        }
        
        val serviceIntent = Intent(this, org.isro.itantra.service.RadioDaemonService::class.java)
        startForegroundService(serviceIntent)
    }

    override fun dispatchKeyEvent(event: android.view.KeyEvent?): Boolean {
        if (org.isro.itantra.input.ForegroundVolumePttProvider.onDispatchKeyEvent(event)) {
            return true
        }
        return super.dispatchKeyEvent(event)
    }

    companion object {
        private const val TAG = "iTantra_MainActivity"
        private const val PERMISSION_REQUEST_CODE = 100
        private const val VAD_SILENCE_TIMEOUT_MS = 10000L // 10-second VAD silence threshold
    }

    private lateinit var netStatusText: android.widget.LinearLayout
    private lateinit var peerIpInput: EditText
    private lateinit var btnConnectPeer: Button
    private lateinit var statusText: TextView
    private lateinit var langSpinner: Spinner
    private lateinit var testButton: Button
    private lateinit var startButton: android.widget.LinearLayout
    private lateinit var stopButton: Button
    private lateinit var btnModeWalkieTalkie: Button
    private lateinit var btnModePhone: Button
    private lateinit var btnSosAmbulance: Button
    private lateinit var btnSosFlood: Button
    private lateinit var btnSosFire: Button
    private lateinit var btnSosUrgent: Button
    private lateinit var customMsgInput: EditText
    private lateinit var btnSendCustom: Button

    private var speechRecognizer: SpeechRecognizer? = null
    private var indicTTSManager: org.isro.itantra.tts.IndicTTSManager? = null
    private var lastRecognizedText: String = ""
    @Volatile private var isRecording = false
    @Volatile private var isTransmitted = false
    @Volatile private var isWalkieTalkieMode = true
    @Volatile private var connectedPeer: String = ""  // deduplicate connection events
    private var spellCorrector: org.isro.itantra.audio.SpellCorrector? = null

    // Prosody capture — collects PCM floats during recording for pitch/energy extraction
    // These are sent in the packet so the receiver can match the speaker's voice character
    private val prosodyPcmBuffer = java.util.concurrent.CopyOnWriteArrayList<Float>()
    private val prosodyMaxSamples = 16000 * 3  // capture up to 3 seconds for prosody analysis

    private val silenceHandler = Handler(Looper.getMainLooper())
    private val silenceRunnable = Runnable {
        if (isRecording) {
            Log.i(TAG, "10-second VAD silence threshold reached. Auto-stopping recording.")
            statusText.text = "⏱️ 10s Silence Timeout: Auto-stopping recording..."
            stopRecordingAndTranscribe()
        }
    }

    private val languageMap = mapOf(
        "English (India)" to "en-IN",
        "Hindi (हिंदी)" to "hi-IN",
        "English (US)" to "en-US",
        "Tamil (தமிழ்)" to "ta-IN",
        "Telugu (తెలుగు)" to "te-IN",
        "Marathi (मराठी)" to "mr-IN",
        "Bengali (বাংলা)" to "bn-IN",
        "Kannada (ಕನ್ನಡ)" to "kn-IN",
        "Malayalam (മലയാളം)" to "ml-IN",
        "Gujarati (ગુજરાતી)" to "gu-IN",
        "Odia (ଓଡ଼ିଆ)" to "or-IN",
        "Punjabi (ਪੰਜਾਬੀ)" to "pa-IN"
    )

    // Mission Domain Dictionary & Identifiers
    private val autoCorrectMap = mapOf(
        // ISRO / SIH specific mission terms
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
        "pragya" to "Pragyan",
        "pragyan" to "Pragyan",

        // Team Call-signs & Identifiers
        "janakee" to "Janaki",
        "janaka" to "Janaki",
        "janaky" to "Janaki",
        "janaki" to "Janaki",
        "chhavi" to "Chhavi",
        "chhavi 2" to "Chhavi_2",
        "parth" to "Parth",
        "nupur" to "Nupur",
        "vaibhav" to "Vaibhav",
        "namastey" to "namaste"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        initPTTFoundation()

        // Acquire Wi-Fi MulticastLock and High-Performance WifiLock for reliable P2P mesh
        try {
            val wifi = applicationContext.getSystemService(Context.WIFI_SERVICE) as? android.net.wifi.WifiManager
            multicastLock = wifi?.createMulticastLock("iTantraMulticastLock")?.apply {
                setReferenceCounted(false)
                acquire()
            }
            wifiLock = wifi?.createWifiLock(
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
                    android.net.wifi.WifiManager.WIFI_MODE_FULL_LOW_LATENCY
                } else {
                    android.net.wifi.WifiManager.WIFI_MODE_FULL_HIGH_PERF
                },
                "iTantraWifiLock"
            )?.apply {
                setReferenceCounted(false)
                acquire()
            }
            Log.i(TAG, "Acquired Wi-Fi MulticastLock and WifiLock (Low Latency / High Perf)")
        } catch (e: Throwable) {
            Log.w(TAG, "WifiLock/MulticastLock notice: ${e.message}")
        }

        // Initialize Indic TTS Engine (Member 2 with 10 Indic languages + Alert Siren)
        try {
            indicTTSManager = org.isro.itantra.tts.IndicTTSManager(this) { statusMsg ->
                runOnUiThread { Log.i(TAG, "TTS: $statusMsg") }
            }
        } catch (e: Throwable) {
            Log.w(TAG, "IndicTTSManager init notice: ${e.message}")
        }

        // Init WFB-ng Transport & Receiver Pipeline with applicationContext
        try {
            val key = ByteArray(32) { 0x42 } // 32-byte shared AES-256 key
            transport = org.isro.itantra.transport.wfbng.WfbngManager(myCallsign, key, "255.255.255.255", 8988, applicationContext)
            transport?.onVoicePayloadDelivered = handler@{ origin, language, priority, payload ->

                // ── PIPELINE LOG ─────────────────────────────────────────────
                Log.i(TAG, "━━ INCOMING_MSG    from=$origin  srcLang=$language  bytes=${payload.size}")

                // Skip self-echo from broadcast
                if (origin == myCallsign) {
                    Log.d(TAG, "Skipping self-echo from $origin")
                    return@handler
                }

                // Receiver's selected target language (from spinner on THIS phone)
                val targetLang = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                    languageMap[langSpinner.selectedItem.toString()]?.substringBefore("-") ?: "en"
                } else "en"

                // Source language carried in the packet header (sender's selected language)
                val sourceLang = if (language.isNotEmpty()) language else "en"

                Log.i(TAG, "━━ TARGET_LANGUAGE  targetLang=$targetLang  sourceLang=$sourceLang")

                // Decode the actual UTF-8 transcript that was transmitted
                val rawText = try {
                    String(payload, Charsets.UTF_8).trim()
                } catch (e: Throwable) {
                    Log.w(TAG, "Payload decode error: ${e.message}")
                    ""
                }

                if (rawText.isBlank()) {
                    Log.w(TAG, "Empty payload from $origin — ignoring")
                    return@handler
                }

                // Filter connection probes — not real messages
                if (rawText.startsWith("ITANTRA_") || rawText.startsWith("PING") || rawText.startsWith("CONNECT_PING")) {
                    runOnUiThread {
                        // netStatusText.text (handled by statusDotText)
                        // netStatusText color update
                    }
                    return@handler
                }

                Log.i(TAG, "━━ RAW_TRANSCRIPT   text='$rawText'")

                // Alert detection on the raw text (works for any language)
                val isAlert = priority.toInt() >= 1 ||
                    rawText.contains("SOS", ignoreCase = true) ||
                    rawText.contains("urgent", ignoreCase = true) ||
                    rawText.contains("emergency", ignoreCase = true) ||
                    rawText.contains("ambulance", ignoreCase = true) ||
                    rawText.contains("flood", ignoreCase = true) ||
                    rawText.contains("fire", ignoreCase = true) ||
                    rawText.contains("तत्काल") || rawText.contains("आपात") ||
                    rawText.contains("ತುರ್ತು") || rawText.contains("అత్యవసరం") ||
                    rawText.contains("அவசரம்") || rawText.contains("জরুরি")

                // Vibrate on incoming message
                try {
                    val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? android.os.Vibrator
                    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                        vibrator?.vibrate(android.os.VibrationEffect.createOneShot(200, android.os.VibrationEffect.DEFAULT_AMPLITUDE))
                    } else {
                        @Suppress("DEPRECATION") vibrator?.vibrate(200)
                    }
                } catch (e: Throwable) {}

                if (sourceLang == targetLang) {
                    // Same language — display and speak directly
                    Log.i(TAG, "━━ TTS_INPUT        lang=$targetLang  text='$rawText'  (same language)")
                    runOnUiThread { statusText.text = "📥 From $origin [$sourceLang]:\n$rawText" }
                    playTTS(rawText, targetLang, isAlert)
                } else {
                    // Different languages — show original immediately, then translate + speak
                    runOnUiThread { statusText.text = "📥 From $origin [$sourceLang→$targetLang]:\n$rawText\n⏳ Translating..." }
                    translateWithMlKit(rawText, sourceLang, targetLang) { translated ->
                        val displayText = if (translated.isNotBlank() && !translated.startsWith("[$sourceLang]"))
                            translated else rawText
                        Log.i(TAG, "━━ TRANSLATION_RESULT  $sourceLang→$targetLang  out='$displayText'")
                        Log.i(TAG, "━━ TTS_INPUT           lang=$targetLang  text='$displayText'")
                        runOnUiThread {
                            statusText.text = "📥 $origin [$sourceLang→$targetLang]:\n$displayText"
                            playTTS(displayText, targetLang, isAlert)
                        }
                    }
                }
            }

            transport?.onPeerDiscovered = { peerCallsign, peerIp ->
                // Deduplicate — only update UI once per unique peer, not on every beacon
                if (connectedPeer != peerCallsign) {
                    connectedPeer = peerCallsign
                    runOnUiThread {
                        findViewById<android.widget.TextView?>(R.id.statusDotText)?.let {
                            it.text = "Mesh Link • $peerCallsign"
                            it.setTextColor(android.graphics.Color.parseColor("#065F46"))
                        }
                        findViewById<android.widget.TextView?>(R.id.statusDot)
                            ?.background = getDrawable(R.drawable.dot_green)
                        findViewById<android.widget.TextView?>(R.id.peerNodeLabel)?.text = peerCallsign
                        statusText.text = "Connected: $peerCallsign"
                        android.widget.Toast.makeText(this@MainActivity, "Connected: $peerCallsign", android.widget.Toast.LENGTH_SHORT).show()
                        Log.i(TAG, "PEER_DISCOVERED: $peerCallsign @ $peerIp")
                    }
                }
            }

            transport?.onLinkConfirmed = { peerCallsign, peerIp, rtt ->
                runOnUiThread {
                    val rttStr = if (rtt > 0) "${rtt}ms" else "—"
                    connectedPeer = peerCallsign
                    // Update status dot and peer label
                    findViewById<android.widget.TextView?>(R.id.statusDotText)?.let {
                        it.text = "Mesh Link • $rttStr"
                        it.setTextColor(android.graphics.Color.parseColor("#065F46"))
                    }
                    findViewById<android.widget.TextView?>(R.id.statusDot)
                        ?.background = getDrawable(R.drawable.dot_green)
                    // Also update header status dot
                    findViewById<android.view.View?>(R.id.statusDotHeader)
                        ?.background = getDrawable(R.drawable.dot_green)
                    findViewById<android.widget.TextView?>(R.id.peerNodeLabel)?.text = peerCallsign
                    // Update RTT display in new UI
                    findViewById<android.widget.TextView?>(R.id.rttValue)?.text = rttStr
                    statusText.text = "Connected: $peerCallsign | $rttStr"
                    Log.i(TAG, "LINK_CONFIRMED: $peerCallsign @ $peerIp (${rttStr})")
                }
            }

            Thread { transport?.start() }.start()
            // Pre-download MLKit translation models for the most common Indian language pairs
            // so cross-language translation is instant when the user first speaks.
            // This runs in background and downloads over ANY network (Wi-Fi or mobile).
            preDownloadTranslationModels()
        } catch (e: Throwable) {
            Log.e(TAG, "Failed to init transport", e)
        }

        netStatusText = findViewById(R.id.netStatusText)
        peerIpInput = findViewById(R.id.peerIpInput)
        btnConnectPeer = findViewById(R.id.btnConnectPeer)
        statusText = findViewById(R.id.statusText)
        langSpinner = findViewById(R.id.langSpinner)
        btnModeWalkieTalkie = findViewById(R.id.btnModeWalkieTalkie)
        btnModePhone = findViewById(R.id.btnModePhone)
        testButton = findViewById(R.id.testButton)
        startButton = findViewById(R.id.startButton)
        stopButton = findViewById(R.id.stopButton)
        btnSosAmbulance = findViewById(R.id.btnSosAmbulance)
        btnSosFlood = findViewById(R.id.btnSosFlood)
        btnSosFire = findViewById(R.id.btnSosFire)
        btnSosUrgent = findViewById(R.id.btnSosUrgent)
        customMsgInput = findViewById(R.id.customMsgInput)
        btnSendCustom = findViewById(R.id.btnSendCustom)

        // ── NEW UI: additional view references ────────────────────────
        val pttLabel      = findViewById<android.widget.TextView?>(R.id.pttLabel)
        val pttStateDot   = findViewById<android.view.View?>(R.id.pttStateDot)
        val pttStateText  = findViewById<android.widget.TextView?>(R.id.pttStateText)
        val txMsgText     = findViewById<android.widget.TextView?>(R.id.txMessageText)
        val rxLangLbl     = findViewById<android.widget.TextView?>(R.id.rxLangLabel)
        val rxTimeLbl     = findViewById<android.widget.TextView?>(R.id.rxTimeLabel)
        val txLangLbl     = findViewById<android.widget.TextView?>(R.id.txLangLabel)
        val txTimeLbl     = findViewById<android.widget.TextView?>(R.id.txTimeLabel)
        val statusDotText = findViewById<android.widget.TextView?>(R.id.statusDotText)
        val peerNodeLabel = findViewById<android.widget.TextView?>(R.id.peerNodeLabel)
        val diagSheet     = findViewById<android.view.View?>(R.id.diagSheet)
        val diagPeerIp    = findViewById<android.widget.EditText?>(R.id.diagPeerIpInput)
        val diagPing      = findViewById<android.widget.Button?>(R.id.btnDiagPing)
        val diagConnect   = findViewById<android.widget.Button?>(R.id.btnDiagConnect)
        val diagCpu       = findViewById<android.widget.TextView?>(R.id.diagCpu)
        val diagRam       = findViewById<android.widget.TextView?>(R.id.diagRam)
        val diagBattery   = findViewById<android.widget.TextView?>(R.id.diagBattery)
        val diagTxRx      = findViewById<android.widget.TextView?>(R.id.diagTxRx)
        val diagPayload   = findViewById<android.widget.TextView?>(R.id.diagPayload)
        val diagAirtime   = findViewById<android.widget.TextView?>(R.id.diagAirtime)
        val diagCarrier   = findViewById<android.widget.TextView?>(R.id.diagCarrier)
        val diagLogText   = findViewById<android.widget.TextView?>(R.id.diagLogText)
        val btnCloseDiag  = findViewById<android.widget.Button?>(R.id.btnCloseDiag)
        val peerChip      = findViewById<android.view.View?>(R.id.peerChip)

        // ── PTT HOLD-TO-TALK on the new circular button ───────────────
        startButton.setOnTouchListener { v, event ->
            when (event.action) {
                android.view.MotionEvent.ACTION_DOWN -> {
                    // Visual: go red/active
                    startButton.background = getDrawable(R.drawable.ptt_btn_bg_active)
                    pttLabel?.text = "TRANSMITTING"
                    pttStateDot?.background = getDrawable(R.drawable.dot_red)
                    pttStateText?.text = "TRANSMITTING"
                    pttStateText?.setTextColor(Color.parseColor("#EF4444"))
                    if (!isRecording) {
                        if (checkAndRequestAudioPermission()) startRecording()
                    }
                    v.performClick()
                }
                android.view.MotionEvent.ACTION_UP, android.view.MotionEvent.ACTION_CANCEL -> {
                    // Visual: restore idle
                    startButton.background = getDrawable(R.drawable.ptt_btn_bg)
                    pttLabel?.text = "HOLD TO SPEAK"
                    pttStateDot?.background = getDrawable(R.drawable.dot_grey)
                    pttStateText?.text = "CARRIER IDLE"
                    pttStateText?.setTextColor(Color.parseColor("#475569"))
                    if (isRecording) {
                        silenceHandler.removeCallbacks(silenceRunnable)
                        isRecording = false
                        stopRecordingAndTranscribe()
                    }
                }
            }
            true
        }

        // ── RECEIVED MESSAGE display helper ─────────────────────────
        // Override transport callback to also update the new card views
        val originalDelivered = transport?.onVoicePayloadDelivered
        transport?.onVoicePayloadDelivered = existingHandler@{ origin, language, priority, payload ->
            originalDelivered?.invoke(origin, language, priority, payload)
            // Update RX card metadata
            val tLang = if (::langSpinner.isInitialized && langSpinner.selectedItem != null)
                languageMap[langSpinner.selectedItem.toString()]?.substringBefore("-") ?: "en"
            else "en"
            val srcDisplay = language.uppercase()
            val tgtDisplay = tLang.uppercase()
            runOnUiThread {
                rxLangLbl?.text = "$srcDisplay → $tgtDisplay"
                rxTimeLbl?.text = "from $origin • just now"
                peerNodeLabel?.text = origin
                // Update TX/RX counters in diagnostics
                val info = transport?.getDiagnosticInfo() ?: emptyMap()
                diagTxRx?.text = "${info["txCount"] ?: 0} / ${info["rxCount"] ?: 0}"
            }
        }

        // ── DIAGNOSTICS SHEET toggle ─────────────────────────────────
        peerChip?.setOnClickListener {
            val allIps = getAllLocalIpAddresses()
            diagPeerIp?.setText(peerIpInput.text.toString().ifEmpty { allIps.firstOrNull() ?: "" })
            diagSheet?.visibility = android.view.View.VISIBLE
            updateDiagnosticsPanel(diagCpu, diagRam, diagBattery, diagTxRx, diagPayload, diagAirtime, diagCarrier, diagLogText)
        }
        btnCloseDiag?.setOnClickListener { diagSheet?.visibility = android.view.View.GONE }

        // PING from diagnostics sheet
        diagPing?.setOnClickListener {
            val ip = diagPeerIp?.text.toString().trim()
            if (ip.isNotEmpty()) {
                diagLogText?.append("\n> PING → $ip:8988")
                transport?.pingPeer(ip, timeoutMs = 1500L, maxAttempts = 3) { success, peer, rtt, msg ->
                    runOnUiThread {
                        if (success) {
                            diagLogText?.append("\n> ACK from $peer  RTT: ${rtt}ms")
                            peerNodeLabel?.text = peer
                        } else {
                            diagLogText?.append("\n> TIMEOUT: no response from $ip")
                        }
                    }
                }
            }
        }

        // CONNECT from diagnostics sheet
        diagConnect?.setOnClickListener {
            val ip = diagPeerIp?.text.toString().trim()
            if (ip.isNotEmpty()) {
                peerIpInput.setText(ip)
                btnConnectPeer.performClick()
                diagSheet?.visibility = android.view.View.GONE
            }
        }

        // Update diagnostics every 3 seconds when sheet is visible
        val diagHandler = android.os.Handler(android.os.Looper.getMainLooper())
        val diagRunnable = object : Runnable {
            override fun run() {
                if (diagSheet?.visibility == android.view.View.VISIBLE) {
                    updateDiagnosticsPanel(diagCpu, diagRam, diagBattery, diagTxRx, diagPayload, diagAirtime, diagCarrier, diagLogText)
                }
                diagHandler.postDelayed(this, 3000)
            }
        }
        diagHandler.postDelayed(diagRunnable, 3000)

        // Update sent card when transmitMessage runs — hook via statusText observer
        // The statusText.text starts with "Sent [lang]:" — parse and push to tx card
        val txWatcher = object : android.text.TextWatcher {
            override fun afterTextChanged(s: android.text.Editable?) {
                val txt = s?.toString() ?: return
                if (txt.startsWith("Sent [")) {
                    val langEnd = txt.indexOf("]:")
                    if (langEnd > 0) {
                        val lang = txt.substring(6, langEnd).uppercase()
                        val msg = txt.substring(langEnd + 2).trim()
                        txMsgText?.text = msg
                        txLangLbl?.text = lang
                        txTimeLbl?.text = "just now"
                    }
                }
            }
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
        }
        statusText.addTextChangedListener(txWatcher)

        // Initial IP display in status dot text
        val allIps = getAllLocalIpAddresses()
        val ipDisplay = if (allIps.isNotEmpty()) allIps.joinToString(" / ") else "Offline"
        statusDotText?.text = "Searching... | $ipDisplay"

        // Update peer node label and status when connection is established
        // (transport callbacks handle this via onPeerDiscovered / onLinkConfirmed)

        // Mode buttons (hidden but keep functional)
        btnModeWalkieTalkie.setOnClickListener { isWalkieTalkieMode = true }
        btnModePhone.setOnClickListener { isWalkieTalkieMode = false }

        btnConnectPeer.setOnClickListener {
            val ip = peerIpInput.text.toString().trim()
            if (ip.isEmpty()) {
                android.widget.Toast.makeText(this, "⚠️ Please enter the other phone's IP address", android.widget.Toast.LENGTH_SHORT).show()
                // netStatusText.text (handled by statusDotText)
                // netStatusText color update
                return@setOnClickListener
            }

            val ipRegex = Regex("""^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$""")
            if (!ip.matches(ipRegex)) {
                android.widget.Toast.makeText(this, "❌ Invalid IPv4 address format!\nExample: 10.163.175.126", android.widget.Toast.LENGTH_LONG).show()
                // netStatusText.text (handled by statusDotText)
                // netStatusText color update
                return@setOnClickListener
            }

            val myIps = getAllLocalIpAddresses()
            if (myIps.contains(ip)) {
                android.widget.Toast.makeText(this, "⚠️ That's THIS phone's IP!\nEnter the OTHER phone's IP.", android.widget.Toast.LENGTH_LONG).show()
                // netStatusText.text (handled by statusDotText)
                // netStatusText color update
                return@setOnClickListener
            }

            btnConnectPeer.isEnabled = false
            // netStatusText.text (handled by statusDotText)
            // netStatusText color update
            statusText.text = "🟡 Probing peer link at $ip:8988..."

            transport?.pingPeer(ip, timeoutMs = 1200L, maxAttempts = 3) { success, peerCallsign, rttMs, msg ->
                runOnUiThread {
                    btnConnectPeer.isEnabled = true
                    if (success) {
                        // netStatusText.text (handled by statusDotText)
                        // netStatusText color update
                        statusText.text = "🟢 Connected to $peerCallsign ($ip:8988) | RTT: ${rttMs}ms"
                        android.widget.Toast.makeText(this, "🟢 Connected to $peerCallsign ($ip)!", android.widget.Toast.LENGTH_SHORT).show()
                    } else {
                        // netStatusText.text (handled by statusDotText)
                        // netStatusText color update
                        statusText.text = "❌ Ping timeout: $ip:8988"
                        android.widget.Toast.makeText(this, "❌ No response from $ip:8988", android.widget.Toast.LENGTH_LONG).show()
                    }
                }
            }
        }

        // Populate Language Selection Dropdown with High-Contrast White Text
        val languagesList = languageMap.keys.toList()
        val adapter = object : ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, languagesList) {
            override fun getView(position: Int, convertView: android.view.View?, parent: android.view.ViewGroup): android.view.View {
                val view = super.getView(position, convertView, parent) as TextView
                view.setTextColor(Color.parseColor("#00E5FF"))
                view.textSize = 14f
                view.setTypeface(null, android.graphics.Typeface.BOLD)
                return view
            }
            override fun getDropDownView(position: Int, convertView: android.view.View?, parent: android.view.ViewGroup): android.view.View {
                val view = super.getDropDownView(position, convertView, parent) as TextView
                view.setBackgroundColor(Color.parseColor("#1E293B"))
                view.setTextColor(Color.parseColor("#FFFFFF"))
                view.setPadding(24, 24, 24, 24)
                return view
            }
        }
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

        // 1-Tap Tactical SOS Quick Alerts
        btnSosAmbulance.setOnClickListener {
            val langCode = getSelectedLangCode()
            val msg = when (langCode) {
                "hi" -> "तत्काल 5 एम्बुलेंस की आवश्यकता है"
                "ta" -> "உடனடியாக 5 ஆம்புலன்ஸ்கள் தேவை"
                "te" -> "వెంటనే 5 అంబులెన్సులు కావాలి"
                "mr" -> "त्वरित ५ रुग्णवाहिकांची आवश्यकता आहे"
                "bn" -> "অবিলম্বে ৫টি অ্যাম্বুলেন্স প্রয়োজন"
                "kn" -> "ತಕ್ಷಣ 5 ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗಳ ಅಗತ್ಯವಿದೆ"
                "ml" -> "ഉടൻ 5 ആംബുലൻസുകൾ ആവശ്യമാണ്"
                "gu" -> "તરત જ 5 એમ્બ્યુલન્સની જરૂર છે"
                "or" -> "ତୁରନ୍ତ ୫ଟି ଆମ୍ବୁଲାନ୍ସ ଆବଶ୍ୟକ"
                else -> "Need 5 ambulances immediately at Sector 4"
            }
            transmitMessage(msg, langCode)
        }

        btnSosFlood.setOnClickListener {
            val langCode = getSelectedLangCode()
            val msg = when (langCode) {
                "hi" -> "बाढ़ की चेतावनी: तुरंत इलाका खाली करें"
                "ta" -> "வெள்ள எச்சரிக்கை: உடனடியாக வெளியேறுங்கள்"
                "te" -> "వరద హెచ్చరిక: వెంటనే ఖాళీ చేయండి"
                "mr" -> "पुराचा इशारा: परिसर त्वरित रिकामे करा"
                "bn" -> "বন্যার সতর্কতা: অবিলম্বে এলাকা খালি করুন"
                "kn" -> "ಪ್ರವಾಹ ಎಚ್ಚರಿಕೆ: ತಕ್ಷಣ ಪ್ರದೇಶವನ್ನು ತೆರವುಗೊಳಿಸಿ"
                "ml" -> "പ്രളയ മുന്നറിയിപ്പ്: ഉടൻ പ്രദേശം ഒഴിയുക"
                "gu" -> "પૂરની ચેતવણી: વિસ્તાર તાત્કાલિક ખાલી કરો"
                "or" -> "ବନ୍ୟା ଚେତାବନୀ: ତୁରନ୍ତ ସ୍ଥାନ ଖାଲି କରନ୍ତୁ"
                else -> "Flood alert: Evacuate sector immediately"
            }
            transmitMessage(msg, langCode)
        }

        btnSosFire.setOnClickListener {
            val langCode = getSelectedLangCode()
            val msg = when (langCode) {
                "hi" -> "आग का खतरा: आपातकालीन दल भेजें"
                "ta" -> "தீ விபத்து: அவசர குழுவை அனுப்பவும்"
                "te" -> "అగ్ని ప్రమాదం: అత్యవసర బృందాన్ని పంపండి"
                "mr" -> "आगीचा धोका: आपत्कालीन पथक पाठवा"
                "bn" -> "অগ্নিকাণ্ড: জরুরি দল পাঠান"
                "kn" -> "ಬೆಂಕಿ ಅವಘಡ: ತುರ್ತು ತಂಡವನ್ನು ಕಳುಹಿಸಿ"
                "ml" -> "തീപിടുത്തം: അടിയന്തര സംഘത്തെ അയക്കുക"
                "gu" -> "આગનો ભય: ઈમરજન્સી ટીમ મોકલો"
                "or" -> "ଅଗ୍ନି ବିପଦ: ଜରୁରୀକାଳୀନ ଦଳ ପଠାନ୍ତୁ"
                else -> "Fire hazard: Deploy emergency units"
            }
            transmitMessage(msg, langCode)
        }

        btnSosUrgent.setOnClickListener {
            val langCode = getSelectedLangCode()
            val msg = when (langCode) {
                "hi" -> "अति आवश्यक सहायता चाहिए"
                "ta" -> "அவசர உதவி தேவை"
                "te" -> "అత్యవసర సహాయం కావాలి"
                "mr" -> "तातडीची मदत हवी आहे"
                "bn" -> "জরুরি সাহায্য প্রয়োজন"
                "kn" -> "ತುರ್ತು ಸಹಾಯ ಬೇಕಾಗಿದೆ"
                "ml" -> "അടിയന്തര സഹായം വേണം"
                "gu" -> "તાત્કાલિક મદદની જરૂર છે"
                "or" -> "ଜରୁରୀ ସାହାଯ୍ୟ ଆବଶ୍ୟକ"
                else -> "Urgent SOS: Need reinforcements immediately"
            }
            transmitMessage(msg, langCode)
        }

        btnSendCustom.setOnClickListener {
            val customText = customMsgInput.text.toString().trim()
            if (customText.isNotEmpty()) {
                val langCode = getSelectedLangCode()
                transmitMessage(customText, langCode)
                customMsgInput.setText("")
            }
        }

        // Show logged-in user info in status dot
        val prefs = getSharedPreferences(LoginActivity.PREF_FILE, android.content.Context.MODE_PRIVATE)
        val displayName = prefs.getString(LoginActivity.PREF_DISPLAY_NAME, null)
        val savedLang = prefs.getString(LoginActivity.PREF_LANGUAGE, null)
        if (displayName != null) {
            findViewById<android.widget.TextView?>(R.id.statusDotText)?.text = displayName
        }
        // Pre-select the saved language in spinner
        if (savedLang != null && ::langSpinner.isInitialized) {
            val langEntries = languageMap.entries.toList()
            val idx = langEntries.indexOfFirst { it.value.substringBefore("-") == savedLang }
            if (idx >= 0) langSpinner.setSelection(idx)
        }

        // Logout when header pill long-pressed
        netStatusText.setOnLongClickListener {
            android.app.AlertDialog.Builder(this)
                .setTitle("Sign Out")
                .setMessage("Sign out from iTantra?")
                .setPositiveButton("Sign Out") { _, _ ->
                    getSharedPreferences(LoginActivity.PREF_FILE, android.content.Context.MODE_PRIVATE)
                        .edit().clear().apply()
                    connectedPeer = ""
                    transport?.stop()
                    startActivity(android.content.Intent(this, LoginActivity::class.java))
                    finish()
                }
                .setNegativeButton("Cancel", null)
                .show()
            true
        }

        // Wire new START AUDIO and TRANSCRIBE buttons (same as PTT hold/release)
        findViewById<android.widget.Button?>(R.id.btnStartAudio)?.setOnClickListener {
            if (!isRecording) {
                if (checkAndRequestAudioPermission()) startRecording()
            }
        }
        findViewById<android.widget.Button?>(R.id.btnStopTranscribe)?.setOnClickListener {
            if (isRecording) {
                silenceHandler.removeCallbacks(silenceRunnable)
                isRecording = false
                stopRecordingAndTranscribe()
            }
        }

        // Wire header status pill → open diagnostics
        netStatusText.setOnClickListener {
            findViewById<android.view.View?>(R.id.diagSheet)?.visibility = android.view.View.VISIBLE
            updateDiagnosticsPanel(
                findViewById(R.id.diagCpu), findViewById(R.id.diagRam),
                findViewById(R.id.diagBattery), findViewById(R.id.diagTxRx),
                findViewById(R.id.diagPayload), findViewById(R.id.diagAirtime),
                findViewById(R.id.diagCarrier), findViewById(R.id.diagLogText)
            )
        }

        // 0. Click SEND TEST ALERT (PTT)
        testButton.setOnClickListener {
            val langCode = getSelectedLangCode()
            val testMsg = when (langCode) {
                "hi" -> "तत्काल 5 एम्बुलेंस की आवश्यकता है"
                "ta" -> "உடனடியாக 5 ஆம்புலன்ஸ்கள் தேவை"
                "te" -> "వెంటనే 5 అంబులెన్సులు కావాలి"
                "mr" -> "त्वरित ५ रुग्णवाहिकांची आवश्यकता आहे"
                "bn" -> "অবিলম্বে ৫টি অ্যাম্বুলেন্স প্রয়োজন"
                "kn" -> "ತಕ್ಷಣ 5 ಆಂಬ್ಯುಲೆನ್ಸ್‌ಗಳ ಅಗತ್ಯವಿದೆ"
                "ml" -> "ഉടൻ 5 ആംബുലൻസുകൾ ആവശ്യമാണ്"
                "gu" -> "તરત જ 5 એમ્બ્યુલન્સની જરૂર છે"
                "or" -> "ତୁରନ୍ତ ୫ଟି ଆମ୍ବୁଲାନ୍ସ ଆବଶ୍ୟକ"
                else -> "Need 5 ambulances immediately at Sector 4"
            }
            transmitMessage(testMsg, langCode)
        }

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
                isRecording = false
                statusText.text = "⚡ Transcribing speech on-device..."
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
                speechRecognizer?.setRecognitionListener(buildRecognitionListener())
            }
        } catch (e: Exception) {
            Log.w(TAG, "SpeechRecognizer setup: ${e.message}")
        }
    }

    private fun buildRecognitionListener(): RecognitionListener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            val lang = if (::langSpinner.isInitialized && langSpinner.selectedItem != null)
                langSpinner.selectedItem.toString() else "Selected language"
            runOnUiThread { statusText.text = "Listening ($lang)... Speak now!" }
            resetSilenceTimer()
        }
        override fun onBeginningOfSpeech() { resetSilenceTimer() }
        override fun onRmsChanged(rmsdB: Float) { if (rmsdB > 0f) resetSilenceTimer() }
        override fun onBufferReceived(buffer: ByteArray?) { resetSilenceTimer() }
        override fun onEndOfSpeech() {}

        override fun onError(error: Int) {
            Log.w(TAG, "SpeechRecognizer error $error")
            when (error) {
                SpeechRecognizer.ERROR_NO_MATCH -> {
                    runOnUiThread { statusText.text = "No speech detected. Speak clearly and try again." }
                }
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> {
                    runOnUiThread { statusText.text = "Speech timeout. Hold PTT and speak." }
                }
                SpeechRecognizer.ERROR_NETWORK, 5, 13 -> {
                    // Network error — Google ASR couldn't connect for this language
                    // This happens when online ASR fails for Indic languages
                    // Set isTransmitted to prevent any competing delay from double-triggering
                    isTransmitted = true
                    runOnUiThread {
                        statusText.text = "Speech recognition unavailable for this language.\nTry text input or select English."
                    }
                }
                SpeechRecognizer.ERROR_AUDIO ->
                    runOnUiThread { statusText.text = "Microphone error. Check permissions." }
                else -> runOnUiThread { statusText.text = "Ready. Hold PTT to speak." }
            }
        }

        override fun onResults(results: Bundle?) {
            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if (!matches.isNullOrEmpty() && matches[0].isNotBlank()) {
                lastRecognizedText = matches[0]
                val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null)
                    langSpinner.selectedItem.toString() else "English (India)"
                val langCode = languageMap[selectedLangName]?.substringBefore("-") ?: "en"
                Log.i(TAG, "STT_RESULT lang=$langCode text=\'${matches[0]}\'")
                if (!isTransmitted) {
                    isTransmitted = true
                    transmitMessage(lastRecognizedText, langCode)
                }
            }
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            if (!matches.isNullOrEmpty()) {
                lastRecognizedText = matches[0]
                runOnUiThread { statusText.text = "Hearing: $lastRecognizedText..." }
                resetSilenceTimer()
            }
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}
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

    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    @Volatile private var totalSamplesPushed = 0L

    private fun startRecording() {
        // Called from setOnTouchListener (UI thread) — do NOT use runOnUiThread() here
        // as it would defer execution and cause a race condition with startListening()
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) {
            statusText.text = "Microphone permission required."
            return
        }

        isRecording = true
        isTransmitted = false
        totalSamplesPushed = 0L
        lastRecognizedText = ""
        prosodyPcmBuffer.clear()

        val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null)
            langSpinner.selectedItem.toString() else "English (India)"
        val langTag = languageMap[selectedLangName] ?: "en-IN"
        val langCode = langTag.substringBefore("-")

        statusText.text = "Listening ($selectedLangName)... Speak now!"
        Log.i(TAG, "[STT] Starting: $selectedLangName  langTag=$langTag")

        // Destroy + recreate + startListening all in sequence on the current (UI) thread
        // No runOnUiThread needed — we ARE on the UI thread already
        try {
            speechRecognizer?.destroy()
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
            speechRecognizer?.setRecognitionListener(buildRecognitionListener())

            val speechIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE, langTag)
                putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, langTag)
                putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
            }

            speechRecognizer?.startListening(speechIntent)
            Log.i(TAG, "[STT] startListening($langTag) called")
        } catch (e: Throwable) {
            Log.e(TAG, "[STT] startListening error: ${e.message}")
            statusText.text = "Microphone error. Try again."
            isRecording = false
            return
        }

        resetSilenceTimer()
    }



    /** Start native Indic ONNX STT audio capture (AI4Bharat IndicConformer) */
    private fun startNativeIndicSTT(langCode: String) {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) return
        try {
            if (NativeSTTBridge.isLibraryLoaded) NativeSTTBridge.safeStartAudioCapture()
            val minBuf = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
            val bufferSize = maxOf(minBuf, 8192)
            var record: AudioRecord? = try {
                AudioRecord(MediaRecorder.AudioSource.VOICE_RECOGNITION, 16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufferSize)
            } catch (e: Throwable) { null }
            if (record?.state != AudioRecord.STATE_INITIALIZED) {
                record?.release()
                record = try {
                    AudioRecord(MediaRecorder.AudioSource.MIC, 16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufferSize)
                } catch (e: Throwable) { null }
            }
            if (record?.state == AudioRecord.STATE_INITIALIZED) {
                audioRecord = record
                audioRecord?.startRecording()
                recordingThread = Thread {
                    val pcm = ShortArray(512)
                    while (isRecording && audioRecord?.recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                        val read = audioRecord?.read(pcm, 0, pcm.size) ?: 0
                        if (read > 0) {
                            if (NativeSTTBridge.isLibraryLoaded) {
                                NativeSTTBridge.safePushAudioPCM(pcm, read)
                            }
                            totalSamplesPushed += read
                            // Capture PCM floats for prosody (pitch + energy) extraction
                            if (prosodyPcmBuffer.size < prosodyMaxSamples) {
                                for (i in 0 until read) {
                                    prosodyPcmBuffer.add(pcm[i].toFloat() / 32768f)
                                }
                            }
                        }
                    }
                }.apply { start() }
                Log.i(TAG, "ONNX native STT capture started for $langCode")
            }
        } catch (e: Throwable) {
            Log.w(TAG, "Native STT start error: ${e.message}")
        }
    }


    private fun stopRecordingAndTranscribe() {
        silenceHandler.removeCallbacks(silenceRunnable)
        isRecording = false

        val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null)
            langSpinner.selectedItem.toString() else "English (India)"
        val langTag = languageMap[selectedLangName] ?: "en-IN"
        val langCode = langTag.substringBefore("-")

        // stopListening() tells ASR to process what was recorded and fire onResults()
        // Do NOT set a competing timeout — onResults() handles transmission
        // onError() handles the failure cases (no match, timeout, network error)
        // The 10-second VAD timer is the only additional fallback
        runOnUiThread {
            try {
                speechRecognizer?.stopListening()
                statusText.text = "Processing..."
            } catch (e: Throwable) {}
        }

        // Stop ONNX audio capture
        Thread {
            try { recordingThread?.join(300) } catch (e: Throwable) {}
            try { audioRecord?.stop(); audioRecord?.release(); audioRecord = null } catch (e: Throwable) {}
        }.start()
    }

    /** Get transcription result from ONNX native STT engine and transmit if not already done */
    private fun tryNativeSTTResult(langCode: String) {
        Thread {
            try {
                var nativeMsg = ""
                if (NativeSTTBridge.isLibraryLoaded) {
                    nativeMsg = NativeSTTBridge.safeStopAudioCaptureAndTranscribe(langCode)
                }
                val cleanMsg = nativeMsg.trim()
                val processedMsg = convertIndicScript(cleanMsg, langCode)
                val candidateText = when {
                    processedMsg.isNotBlank()
                        && processedMsg !in listOf("আ", "अ", "aa", "a", "")
                        && !processedMsg.startsWith("No speech")
                        && !processedMsg.contains("Exception")
                        && !processedMsg.contains("Init Error")
                        && !processedMsg.contains("Encoder load")
                        && !processedMsg.contains("failed")
                        && !processedMsg.contains("Invalid fd") -> processedMsg
                    // Don't transmit ONNX error messages — SpeechRecognizer result should be used instead
                    else -> ""
                }
                runOnUiThread {
                    if (candidateText.isNotBlank() && !isTransmitted) {
                        isTransmitted = true
                        transmitMessage(candidateText, langCode)
                    } else if (!isTransmitted) {
                        statusText.text = "No speech detected. Hold mic close and speak clearly."
                    }
                }
            } catch (e: Throwable) {
                Log.e(TAG, "ONNX STT result error: ${e.message}", e)
            }
        }.start()
    }
    private fun transmitMessage(rawText: String, langCode: String) {
        val correctedText = autoCorrectAndFormatText(rawText, langCode)
        if (correctedText.isBlank()) return

        Log.i(TAG, "━━ STT_TRANSCRIPT  lang=$langCode  text='$correctedText'")

        // Extract prosody from PCM captured during recording (pitch + energy)
        val prosodyBytes = extractProsodyBytes()
        prosodyPcmBuffer.clear()

        // SEND IMMEDIATELY — do not wait for async language detection
        // Language detection runs in parallel for logging only
        val packet: ByteArray = correctedText.toByteArray(Charsets.UTF_8)
        Log.i(TAG, "━━ OUTGOING_MSG    lang=$langCode  bytes=${packet.size}  text='$correctedText'")

        try {
            transport?.sendVoiceMessage(packet, langCode, 1.toByte(), "RESCUE_ALL")
        } catch (e: Throwable) {
            Log.e(TAG, "Transport send error: ${e.message}", e)
            runOnUiThread { statusText.text = "Send error: ${e.message}" }
            return
        }

        runOnUiThread {
            statusText.text = "Sent [$langCode]: $correctedText"
        }

        // Language detection runs async for diagnostics — does NOT block transmission
        detectLanguage(correctedText) { detectedLang ->
            if (detectedLang != null && detectedLang != langCode) {
                Log.i(TAG, "━━ LANG_DETECTION  spinner=$langCode  detected=$detectedLang  (informational only)")
            }
        }
    }

    /**
     * Play TTS with optional sender prosody to approximate their voice character.
     * prosodyBytes: 16-byte array from the packet — [0-3]=pitch_f32, [4-7]=rms_f32
     * If prosodyBytes is empty or null, uses default voice.
     */
    private fun playTTS(
        text: String,
        langCode: String,
        isEmergency: Boolean = false,
        prosodyBytes: ByteArray? = null
    ) {
        try {
            // Build ProsodyVector from the sender's captured pitch/energy
            val prosody = if (prosodyBytes != null && prosodyBytes.size >= 8) {
                val buf = java.nio.ByteBuffer.wrap(prosodyBytes)
                    .order(java.nio.ByteOrder.LITTLE_ENDIAN)
                val pitch = buf.float.coerceIn(60f, 400f)  // bytes 0-3
                val rms   = buf.float.coerceIn(0f, 1f)     // bytes 4-7
                Log.i(TAG, "━━ TTS_PROSODY      pitch=%.1fHz rms=%.3f".format(pitch, rms))
                // Map pitch to Android TTS pitch multiplier: 140Hz (neutral) = 1.0x
                // Lower pitch (male, ~100Hz) → 0.8x, Higher (female, ~220Hz) → 1.3x
                val androidPitch = (pitch / 140f).coerceIn(0.7f, 1.6f)
                // Apply pitch/speed to the Android TTS engine (accessible from MainActivity)
                // Apply pitch/speed to IndicTTSManager's internal Android TTS
                try {
                    indicTTSManager?.applyProsodyToTts(androidPitch, 0.9f + rms * 0.2f)
                } catch (e: Throwable) {}
                org.isro.itantra.tts.ProsodyVector(
                    f0PitchMean = pitch,
                    rmsEnergy = rms
                )
            } else {
                org.isro.itantra.tts.ProsodyVector()
            }

            if (isEmergency && isWalkieTalkieMode) {
                indicTTSManager?.playEmergencyAlert(text, langCode)
            } else {
                indicTTSManager?.speak(text, langCode, prosody)
            }
            Log.i(TAG, "━━ TTS_INPUT        lang=$langCode  text='$text'")
        } catch (e: Throwable) {
            Log.w(TAG, "TTS notice: ${e.message}")
            // Fallback to Android TTS directly
            try { indicTTSManager?.speak(text, langCode) } catch (e2: Throwable) {}
        }
    }

    /**
     * FIX 2: MULTILINGUAL TRANSLATION — Offline text translation between all supported language pairs.
     *
     * Architecture: Since this is an offline emergency app, we use a deterministic phrase-expansion
     * approach combined with Android's built-in TextToSpeech locale detection.
     *
     * For the primary use case (emergency/tactical messages), we map known phrases across languages.
     * For free-form text, we preserve the original meaning by passing it through with a language tag.
     *
     * Pipeline: sourceLang text → normalize → identify known emergency phrases → render in targetLang
     *
     * This function is only called when the C++ SemanticBridge (M3 engine) is NOT loaded.
     * When SemanticBridge IS loaded, translation is handled entirely in C++ by TranslationBridge.cpp.
     */
    /**
     * FIX 2: MULTILINGUAL TRANSLATION — On-device offline translation using Google MLKit.
     *
     * MLKit Translation works fully offline after a one-time model download (~20MB per language).
     * It handles arbitrary sentences including real place names, directions, and conversational
     * speech — not just hardcoded phrases.
     *
     * Language models are downloaded automatically on first use (Wi-Fi only by default).
     * Once downloaded, all translation is done entirely on-device with no internet.
     *
     * Supported: en, hi, ta, te, mr, bn, kn, ml, gu, or, pa — all combinations.
     */
    private val mlkitTranslatorCache = java.util.concurrent.ConcurrentHashMap<String, com.google.mlkit.nl.translate.Translator>()
    private val translationCache = java.util.concurrent.ConcurrentHashMap<String, String>()

    /**
     * Map our 2-letter language codes to MLKit TranslateLanguage constants.
     * MLKit v17.0.3 supports: en, hi, ta, te, mr, bn, kn, gu
     * Malayalam (ml), Odia (or), Punjabi (pa) are NOT in MLKit — we proxy through
     * a closely related language so something useful is shown:
     *   ml (Malayalam) → ta (Tamil, both Dravidian family)
     *   or (Odia)      → hi (Hindi, both Indo-Aryan, closest in script similarity)
     *   pa (Punjabi)   → hi (Hindi, both Indo-Aryan, mutually intelligible)
     * Returns null if the language is not supported and no proxy is available.
     */
    private fun mlkitLanguageCode(lang: String): String? {
        return when (lang) {
            "hi" -> com.google.mlkit.nl.translate.TranslateLanguage.HINDI
            "ta" -> com.google.mlkit.nl.translate.TranslateLanguage.TAMIL
            "te" -> com.google.mlkit.nl.translate.TranslateLanguage.TELUGU
            "mr" -> com.google.mlkit.nl.translate.TranslateLanguage.MARATHI
            "bn" -> com.google.mlkit.nl.translate.TranslateLanguage.BENGALI
            "kn" -> com.google.mlkit.nl.translate.TranslateLanguage.KANNADA
            "gu" -> com.google.mlkit.nl.translate.TranslateLanguage.GUJARATI
            "en" -> com.google.mlkit.nl.translate.TranslateLanguage.ENGLISH
            // Proxied: MLKit doesn't support these directly
            "ml" -> com.google.mlkit.nl.translate.TranslateLanguage.TAMIL    // Dravidian family proxy
            "or" -> com.google.mlkit.nl.translate.TranslateLanguage.HINDI    // Indo-Aryan proxy
            "pa" -> com.google.mlkit.nl.translate.TranslateLanguage.HINDI    // Indo-Aryan proxy
            else -> null
        }
    }

    /**
     * Async translation via MLKit. Invokes onResult on a background thread.
     * Model is downloaded on first use (Wi-Fi only, ~20MB per language pair).
     * All subsequent calls use the on-device model — fully offline.
     */
    private fun translateWithMlKit(
        text: String,
        sourceLang: String,
        targetLang: String,
        onResult: (translated: String) -> Unit
    ) {
        if (text.isBlank() || sourceLang == targetLang) { onResult(text); return }

        val cacheKey = "$sourceLang|$targetLang|$text"
        translationCache[cacheKey]?.let { onResult(it); return }

        val srcCode = mlkitLanguageCode(sourceLang)
        val tgtCode = mlkitLanguageCode(targetLang)
        if (srcCode == null || tgtCode == null) {
            onResult("[$sourceLang] $text")
            return
        }

        val enCode = mlkitLanguageCode("en")!!
        val conditions = com.google.mlkit.common.model.DownloadConditions.Builder().build()

        // MLKit only has direct translation pairs with English.
        // Non-English pairs (hi→kn, kn→te, etc.) MUST go through English as pivot:
        //   Step 1: hi → en
        //   Step 2: en → kn
        // English pairs (en→hi, hi→en) go directly.

        val needsPivot = sourceLang != "en" && targetLang != "en"

        if (!needsPivot) {
            // Direct translation (one of the languages is English)
            val translatorKey = "$sourceLang|$targetLang"
            val translator = mlkitTranslatorCache.getOrPut(translatorKey) {
                val options = com.google.mlkit.nl.translate.TranslatorOptions.Builder()
                    .setSourceLanguage(srcCode).setTargetLanguage(tgtCode).build()
                com.google.mlkit.nl.translate.Translation.getClient(options)
            }
            translator.downloadModelIfNeeded(conditions)
                .addOnSuccessListener {
                    translator.translate(text)
                        .addOnSuccessListener { translated ->
                            translationCache[cacheKey] = translated
                            Log.i(TAG, "MLKit[$sourceLang→$targetLang] direct: '$text' → '$translated'")
                            onResult(translated)
                        }
                        .addOnFailureListener { e ->
                            Log.w(TAG, "MLKit direct translate error: ${e.message}")
                            onResult(text)
                        }
                }
                .addOnFailureListener { e ->
                    Log.w(TAG, "MLKit model download failed: ${e.message}")
                    onResult(text)
                }
        } else {
            // Pivot via English: srcLang → en → targetLang
            val step1Key = "$sourceLang|en"
            val step1 = mlkitTranslatorCache.getOrPut(step1Key) {
                val options = com.google.mlkit.nl.translate.TranslatorOptions.Builder()
                    .setSourceLanguage(srcCode).setTargetLanguage(enCode).build()
                com.google.mlkit.nl.translate.Translation.getClient(options)
            }
            val step2Key = "en|$targetLang"
            val step2 = mlkitTranslatorCache.getOrPut(step2Key) {
                val options = com.google.mlkit.nl.translate.TranslatorOptions.Builder()
                    .setSourceLanguage(enCode).setTargetLanguage(tgtCode).build()
                com.google.mlkit.nl.translate.Translation.getClient(options)
            }

            step1.downloadModelIfNeeded(conditions)
                .addOnSuccessListener {
                    step2.downloadModelIfNeeded(conditions)
                        .addOnSuccessListener {
                            // Step 1: source → English
                            step1.translate(text)
                                .addOnSuccessListener { englishText ->
                                    Log.i(TAG, "MLKit pivot step1 [$sourceLang→en]: '$text' → '$englishText'")
                                    // Step 2: English → target
                                    step2.translate(englishText)
                                        .addOnSuccessListener { finalText ->
                                            translationCache[cacheKey] = finalText
                                            Log.i(TAG, "MLKit pivot step2 [en→$targetLang]: '$englishText' → '$finalText'")
                                            onResult(finalText)
                                        }
                                        .addOnFailureListener { e ->
                                            Log.w(TAG, "MLKit pivot step2 error: ${e.message}")
                                            onResult(englishText) // fallback to English intermediate
                                        }
                                }
                                .addOnFailureListener { e ->
                                    Log.w(TAG, "MLKit pivot step1 error: ${e.message}")
                                    onResult(text)
                                }
                        }
                        .addOnFailureListener { e ->
                            Log.w(TAG, "MLKit en→$targetLang model download failed: ${e.message}")
                            onResult(text)
                        }
                }
                .addOnFailureListener { e ->
                    Log.w(TAG, "MLKit $sourceLang→en model download failed: ${e.message}")
                    onResult(text)
                }
        }
    }

    /**
     * Synchronous translate for the receive pipeline.
     * Returns cached result instantly. If not cached yet, shows the original text
     * with a language tag, then asynchronously fetches translation and updates the UI + TTS.
     * After the first call for a language pair, all subsequent calls are instant.
     */
    private fun translateText(
        text: String,
        sourceLang: String,
        targetLang: String,
        speakAloud: Boolean = false,
        isAlert: Boolean = false
    ): String {
        if (text.isBlank() || sourceLang == targetLang) return text

        val cacheKey = "$sourceLang|$targetLang|$text"
        translationCache[cacheKey]?.let { cached ->
            // Cache hit — play TTS immediately if requested
            if (speakAloud && cached.isNotBlank()) playTTS(cached, targetLang, isAlert)
            return cached
        }

        // Fire async translation — updates the UI and plays TTS when translation arrives
        translateWithMlKit(text, sourceLang, targetLang) { translated ->
            translationCache[cacheKey] = translated
            runOnUiThread {
                // Update status text if it still shows the placeholder
                val current = statusText.text.toString()
                if (current.contains("[$sourceLang]")) {
                    val updated = current
                        .replace("[$sourceLang] $text", translated)
                        .replace("\n[$sourceLang] $text", "\n$translated")
                    statusText.text = updated
                }
                // FIX 2: Play TTS in receiver's target language once translation is ready
                if (speakAloud && translated.isNotBlank() && !translated.startsWith("[$sourceLang]")) {
                    playTTS(translated, targetLang, isAlert)
                }
            }
        }

        // Immediate fallback — replaced by real translation once MLKit model downloads
        return "[$sourceLang] $text"
    }



    /**
     * Pre-download MLKit translation models for the most common Indian language pairs.
     * Called once at startup — downloads in background over ANY network.
     * Once downloaded (~20MB per language), all translation is fully offline forever.
     */
    private fun preDownloadTranslationModels() {
        // Download ALL lang↔en models so every 10×10 language combination works via pivot.
        // Any pair X→Y (both non-English) is handled as X→en→Y automatically.
        // ml proxied via ta, or/pa proxied via hi (same model downloads).
        val allLangs = listOf("hi", "kn", "te", "mr", "ta", "bn", "gu",
                              "ml",  // uses ta model
                              "or",  // uses hi model
                              "pa")  // uses hi model
        val conditions = com.google.mlkit.common.model.DownloadConditions.Builder().build()
        val enCode = mlkitLanguageCode("en") ?: return

        // Deduplicate proxy languages (ml/ta, or/pa/hi share the same model)
        val uniqueCodes = allLangs.mapNotNull { mlkitLanguageCode(it) }.toSet()

        for (langCode in uniqueCodes) {
            // Download lang→en (needed when this language is the sender)
            val optSend = com.google.mlkit.nl.translate.TranslatorOptions.Builder()
                .setSourceLanguage(langCode).setTargetLanguage(enCode).build()
            com.google.mlkit.nl.translate.Translation.getClient(optSend)
                .downloadModelIfNeeded(conditions)
                .addOnSuccessListener { Log.i(TAG, "MLKit ready: $langCode→en") }
                .addOnFailureListener { e -> Log.w(TAG, "MLKit fail $langCode→en: ${e.message}") }

            // Download en→lang (needed when this language is the receiver / pivot target)
            val optRecv = com.google.mlkit.nl.translate.TranslatorOptions.Builder()
                .setSourceLanguage(enCode).setTargetLanguage(langCode).build()
            com.google.mlkit.nl.translate.Translation.getClient(optRecv)
                .downloadModelIfNeeded(conditions)
                .addOnSuccessListener { Log.i(TAG, "MLKit ready: en→$langCode") }
                .addOnFailureListener { e -> Log.w(TAG, "MLKit fail en→$langCode: ${e.message}") }
        }
        Log.i(TAG, "MLKit: pre-downloading ${uniqueCodes.size * 2} models — all ${allLangs.size}×${allLangs.size} combinations covered")
    }

    /**
     * Detect the language of a text string using MLKit Language ID.
     * Returns a 2-letter language code (e.g. "hi", "kn", "en") or null if detection fails.
     * This model is tiny (~1MB) and works fully offline.
     */
    private fun detectLanguage(text: String, onResult: (String?) -> Unit) {
        if (text.isBlank()) { onResult(null); return }
        val identifier = com.google.mlkit.nl.languageid.LanguageIdentification.getClient()
        identifier.identifyLanguage(text)
            .addOnSuccessListener { langCode ->
                val detected = if (langCode == "und" || langCode.isNullOrBlank()) null else langCode
                Log.i(TAG, "MLKit LanguageID: '$text' → $detected")
                onResult(detected)
            }
            .addOnFailureListener {
                onResult(null)
            }
    }

    /**
     * Extract prosody (pitch + energy) from the PCM buffer captured during recording.
     * Returns a 16-byte array suitable for inclusion in the WfbngManager packet.
     * On the receiver side, these values are used to adjust TTS pitch and volume
     * so the synthesized speech roughly matches the sender's voice character.
     */
    private fun extractProsodyBytes(): ByteArray {
        val samples = prosodyPcmBuffer.toFloatArray()
        if (samples.isEmpty()) return ByteArray(16)

        // RMS energy
        var sumSq = 0.0
        for (s in samples) sumSq += s.toDouble() * s.toDouble()
        val rms = Math.sqrt(sumSq / samples.size).toFloat().coerceIn(0f, 1f)

        // Autocorrelation pitch detection (60Hz–400Hz range at 16kHz)
        val sampleRate = 16000
        val minLag = sampleRate / 400
        val maxLag = sampleRate / 60
        var bestCorr = -1f
        var bestLag = minLag
        val n = minOf(samples.size, 1024)
        for (lag in minLag..minOf(maxLag, samples.size - 1)) {
            var corr = 0f
            for (i in 0 until n) {
                if (i + lag < samples.size) corr += samples[i] * samples[i + lag]
            }
            if (corr > bestCorr) { bestCorr = corr; bestLag = lag }
        }
        val pitch = if (bestLag > 0) (sampleRate.toFloat() / bestLag).coerceIn(60f, 400f) else 140f

        // Pack into 16 bytes: [0-3]=pitch_f32, [4-7]=rms_f32, [8-15]=reserved(0)
        val buf = java.nio.ByteBuffer.allocate(16)
        buf.order(java.nio.ByteOrder.LITTLE_ENDIAN)
        buf.putFloat(pitch)   // bytes 0-3
        buf.putFloat(rms)     // bytes 4-7
        buf.putFloat(0f)      // bytes 8-11 reserved
        buf.putFloat(0f)      // bytes 12-15 reserved
        Log.i(TAG, "Prosody extracted: pitch=%.1fHz rms=%.3f".format(pitch, rms))
        return buf.array()
    }

    private fun formatTranscriptForLanguage(cleanMsg: String, langCode: String): String {
        if (cleanMsg.isBlank()) return cleanMsg
        if (langCode.startsWith("en")) {
            val roman = transliterateToRoman(cleanMsg)
            return if (roman.isNotBlank()) roman else cleanMsg
        }
        return convertIndicScript(cleanMsg, langCode)
    }

    private fun convertIndicScript(input: String, targetLang: String): String {
        val targetBase = when (targetLang.lowercase()) {
            "hi", "mr" -> 0x0900
            "bn" -> 0x0980
            "pa" -> 0x0A00
            "gu" -> 0x0A80
            "or" -> 0x0B00
            "ta" -> 0x0B80
            "te" -> 0x0C00
            "kn" -> 0x0C80
            "ml" -> 0x0D00
            else -> return input
        }

        val sb = StringBuilder()
        for (ch in input) {
            val code = ch.code
            // Check if it is an Indic Unicode character (U+0900 to U+0D7F)
            if (code in 0x0900..0x0D7F) {
                var offset = code % 0x80
                
                // Tamil phonetic stop mapping
                if (targetLang == "ta") {
                    offset = when (offset) {
                        0x16, 0x17, 0x18 -> 0x15 // Kha, Ga, Gha -> Ka (க)
                        0x1B, 0x1C, 0x1D -> 0x1A // Chha, Ja, Jha -> Cha (ச)
                        0x20, 0x21, 0x22 -> 0x1F // Tha, Da, Dha -> Ta (ட)
                        0x25, 0x26, 0x27 -> 0x24 // Tha, Da, Dha -> Ta (த)
                        0x2B, 0x2C, 0x2D -> 0x2A // Pha, Ba, Bha -> Pa (ப)
                        0x36 -> 0x37             // Sha -> Sha (ஷ)
                        else -> offset
                    }
                }
                
                val targetCode = targetBase + offset
                sb.append(targetCode.toChar())
            } else {
                sb.append(ch)
            }
        }
        return sb.toString()
    }

    // Auto-Correct and Format Speech Transcript Text
    /**
     * Transliterate Devanagari (and other Indic scripts) to Roman/Latin script.
     * The AI4Bharat IndicConformer model only has Indic tokens in its vocabulary,
     * so when the user speaks English, it outputs phonetic Devanagari approximations.
     * This function converts those back to readable Roman text.
     */
    private fun transliterateToRoman(input: String): String {
        if (input.isBlank()) return input

        // Consonant base forms (without implicit 'a' — we add 'a' only when no matra/halant follows)
        val consonants = mapOf(
            'क' to "k", 'ख' to "kh", 'ग' to "g", 'घ' to "gh", 'ङ' to "ng",
            'च' to "ch", 'छ' to "chh", 'ज' to "j", 'झ' to "jh", 'ञ' to "ny",
            'ट' to "t", 'ठ' to "th", 'ड' to "d", 'ढ' to "dh", 'ण' to "n",
            'त' to "t", 'थ' to "th", 'द' to "d", 'ध' to "dh", 'न' to "n",
            'प' to "p", 'फ' to "ph", 'ब' to "b", 'भ' to "bh", 'म' to "m",
            'य' to "y", 'र' to "r", 'ल' to "l", 'व' to "v", 'श' to "sh",
            'ष' to "sh", 'स' to "s", 'ह' to "h"
        )

        // Independent vowels
        val vowels = mapOf(
            'अ' to "a", 'आ' to "a", 'इ' to "i", 'ई' to "i",
            'उ' to "u", 'ऊ' to "u", 'ऋ' to "ri", 'ॠ' to "ri",
            'ए' to "e", 'ऐ' to "e", 'ओ' to "o", 'औ' to "au"
        )

        // Dependent vowel signs (matras) — replace the implicit 'a'
        val matras = mapOf(
            'ा' to "a", 'ि' to "i", 'ी' to "i", 'ु' to "u", 'ू' to "u",
            'े' to "e", 'ै' to "e", 'ो' to "o", 'ौ' to "au",
            'ृ' to "ri", 'ॄ' to "ri", 'ॅ' to "e", 'ॉ' to "o"
        )

        // Nukta consonants (consonant + ़)
        val nuktaConsonants = mapOf(
            'क' to "q", 'ख' to "kh", 'ग' to "gh", 'ज' to "z",
            'फ' to "f", 'ड' to "r", 'ढ' to "rh"
        )

        val sb = StringBuilder()
        val chars = input.toList()
        var i = 0
        var lastWasConsonant = false  // tracks if we need to add implicit 'a'

        while (i < chars.size) {
            val ch = chars[i]
            val next = if (i + 1 < chars.size) chars[i + 1] else null

            when {
                // Space character (SentencePiece or regular)
                ch == '▁' || ch == ' ' -> {
                    lastWasConsonant = false // Schwa deletion at word boundaries
                    sb.append(" ")
                    i++
                }
                // Halant (virama) — suppresses the implicit 'a' of preceding consonant
                ch == '्' -> {
                    lastWasConsonant = false  // 'a' already NOT added
                    i++
                }
                // Nukta — modifies the preceding consonant
                ch == '़' -> {
                    // Already processed with consonant if applicable
                    i++
                }
                // Anusvara
                ch == 'ं' -> {
                    sb.append("n")
                    lastWasConsonant = false
                    i++
                }
                // Chandrabindu
                ch == 'ँ' -> {
                    sb.append("n")
                    lastWasConsonant = false
                    i++
                }
                // Visarga
                ch == 'ः' -> {
                    sb.append("h")
                    lastWasConsonant = false
                    i++
                }
                // Matras — replace the implicit 'a' with the vowel sound
                matras.containsKey(ch) -> {
                    lastWasConsonant = false  // matra replaces implicit 'a'
                    sb.append(matras[ch])
                    i++
                }
                // English wh digraph (व् + ह)
                ch == 'व' && next == '्' && i + 2 < chars.size && chars[i + 2] == 'ह' -> {
                    if (lastWasConsonant) { sb.append("a") }
                    sb.append("wh")
                    lastWasConsonant = true
                    i += 3
                }
                // Consonants
                consonants.containsKey(ch) -> {
                    if (lastWasConsonant) { sb.append("a") } // Inter-consonant schwa
                    // Check for nukta (consonant + ़)
                    if (next == '़' && nuktaConsonants.containsKey(ch)) {
                        sb.append(nuktaConsonants[ch])
                        i += 2
                    } else {
                        sb.append(consonants[ch])
                        i++
                    }
                    lastWasConsonant = true
                }
                // Independent vowels
                vowels.containsKey(ch) || ch == 'ऑ' || ch == 'ॅ' -> {
                    if (lastWasConsonant) { sb.append("a") }
                    lastWasConsonant = false
                    if (ch == 'ऑ') sb.append("o")
                    else if (ch == 'ॅ') sb.append("a")
                    else sb.append(vowels[ch])
                    i++
                }
                // Devanagari digits
                ch in '०'..'९' -> {
                    lastWasConsonant = false
                    sb.append((ch.code - '०'.code + '0'.code).toChar())
                    i++
                }
                // OM symbol
                ch == 'ॐ' -> {
                    lastWasConsonant = false
                    sb.append("om")
                    i++
                }
                // ASCII characters — pass through
                ch.code < 128 -> {
                    lastWasConsonant = false
                    sb.append(ch)
                    i++
                }
                // Any other Indic/unknown character — skip
                else -> {
                    lastWasConsonant = false
                    i++
                }
            }
        }

        // Modern Indic and English: word-final schwa deletion (no trailing 'a')

        return sb.toString()
            .replace("\\s+".toRegex(), " ")
            .trim()
    }

    private fun autoCorrectAndFormatText(input: String, langCode: String = "en"): String {
        if (input.isBlank()) return input

        var text = input.trim().replace("\\s+".toRegex(), " ")

        // 1. First apply phonetic & domain dictionary replacements
        for ((wrong, correct) in autoCorrectMap) {
            val regex = "(?i)\\b$wrong\\b".toRegex()
            text = text.replace(regex, correct)
        }

        // 2. Offline Spelling Correction (only for Indic languages — do NOT distort English words)
        if (spellCorrector != null && !langCode.startsWith("en")) {
            val words = text.split(" ")
            val correctedWords = words.map { word ->
                spellCorrector!!.correct(word)
            }
            text = correctedWords.joinToString(" ")
        }

        // 3. Re-apply domain dictionary to ensure key terms/names remain accurate
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
            val minSizes = mapOf(
                "ctc_decoder.onnx" to 20_000_000L,
                "encoder.onnx" to 100_000_000L,
                "silero_vad.onnx" to 2_000_000L,
                "tokens.txt" to 50_000L,
                "vocab.json" to 50_000L
            )
            val minRequired = minSizes[assetName] ?: 10L
            if (file.exists() && file.length() >= minRequired) {
                return file.absolutePath
            }
            file.delete()
            assets.open(assetName).use { inputStream ->
                java.io.FileOutputStream(file).use { outputStream ->
                    inputStream.copyTo(outputStream)
                }
            }
            Log.i(TAG, "Copied asset $assetName (${file.length()} bytes) to storage.")
            return file.absolutePath
        } catch (e: Exception) {
            android.util.Log.e("MainActivity", "Failed to copy asset $assetName: ${e.message}")
            return ""
        }
    }

    private fun initNativeAudioEngine() {
        try {
            // Extract the necessary files from the APK to internal storage so C++ can read them
            val vadPath = copyAssetToStorage("silero_vad.onnx")
            val encPath = copyAssetToStorage("encoder.onnx")
            val decPath = copyAssetToStorage("ctc_decoder.onnx")
            val tokensPath = copyAssetToStorage("tokens.txt")
            val vocabPath = if (tokensPath.isNotEmpty()) tokensPath else copyAssetToStorage("vocab.json")
            
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

    private fun getSelectedLangCode(): String {
        val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
            langSpinner.selectedItem.toString()
        } else {
            "English (India)"
        }
        return languageMap[selectedLangName]?.substringBefore("-") ?: "en"
    }

    private fun getAllLocalIpAddresses(): List<String> {
        val wifiIps = mutableListOf<String>()
        val otherIps = mutableListOf<String>()
        try {
            val interfaces = java.net.NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                val isWifi = iface.name.startsWith("wlan", ignoreCase = true) ||
                             iface.name.startsWith("ap", ignoreCase = true) ||
                             iface.name.startsWith("softap", ignoreCase = true) ||
                             iface.name.startsWith("p2p", ignoreCase = true) ||
                             iface.name.startsWith("eth", ignoreCase = true)
                for (addr in iface.inetAddresses) {
                    if (!addr.isLoopbackAddress && addr is java.net.Inet4Address) {
                        val host = addr.hostAddress ?: continue
                        if (!host.startsWith("127.")) {
                            if (isWifi) {
                                if (!wifiIps.contains(host)) wifiIps.add(host)
                            } else {
                                if (!otherIps.contains(host)) otherIps.add(host)
                            }
                        }
                    }
                }
            }
        } catch (e: Throwable) {}
        return wifiIps + otherIps
    }

    private fun getLocalIpAddress(): String {
        return getAllLocalIpAddresses().firstOrNull() ?: "Offline"
    }


    private fun updateDiagnosticsPanel(
        diagCpu: android.widget.TextView?,
        diagRam: android.widget.TextView?,
        diagBattery: android.widget.TextView?,
        diagTxRx: android.widget.TextView?,
        diagPayload: android.widget.TextView?,
        diagAirtime: android.widget.TextView?,
        diagCarrier: android.widget.TextView?,
        diagLog: android.widget.TextView?
    ) {
        try {
            // RAM
            val am = getSystemService(android.content.Context.ACTIVITY_SERVICE) as android.app.ActivityManager
            val mi = android.app.ActivityManager.MemoryInfo()
            am.getMemoryInfo(mi)
            val ramUsed = ((mi.totalMem - mi.availMem) / (1024 * 1024)).toInt()
            diagRam?.text = "$ramUsed MB"
            diagCpu?.text = "—"  // /proc/stat needs root on modern Android

            // Battery
            val battIntent = registerReceiver(null, android.content.IntentFilter(android.content.Intent.ACTION_BATTERY_CHANGED))
            val level = battIntent?.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1) ?: -1
            val scale = battIntent?.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, 100) ?: 100
            val bat = if (level >= 0) "${ level * 100 / scale }%" else "--"
            diagBattery?.text = bat
            if (level * 100 / scale < 20) diagBattery?.setTextColor(android.graphics.Color.parseColor("#EF4444"))
            else if (level * 100 / scale < 50) diagBattery?.setTextColor(android.graphics.Color.parseColor("#F59E0B"))
            else diagBattery?.setTextColor(android.graphics.Color.parseColor("#059669"))

            // Transport counters
            val info = transport?.getDiagnosticInfo() ?: emptyMap()
            val tx = info["txCount"] ?: "0"
            val rx = info["rxCount"] ?: "0"
            diagTxRx?.text = "$tx / $rx"
            diagCarrier?.text = (info["carrier"] ?: "WI-FI").uppercase()
            diagPayload?.text = "—"
            diagAirtime?.text = "—"

            // Append log entry
            val peers = info["discoveredPeers"] ?: ""
            if (peers.isNotEmpty()) {
                val ts = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.US).format(java.util.Date())
                val logEntry = "\n> [$ts] Peers: $peers  TX:$tx RX:$rx"
                val current = diagLog?.text?.toString() ?: ""
                val logLines = current.split("\n")
                val trimmed = if (logLines.size > 8) logLines.takeLast(8).joinToString("\n") else current
                diagLog?.text = trimmed + logEntry
            }
        } catch (e: Throwable) {
            android.util.Log.w(TAG, "Diagnostics update error: ${e.message}")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            silenceHandler.removeCallbacks(silenceRunnable)
            speechRecognizer?.destroy()
            indicTTSManager?.shutdown()
            transport?.stop()
            if (multicastLock?.isHeld == true) {
                multicastLock?.release()
            }
            if (wifiLock?.isHeld == true) {
                wifiLock?.release()
            }
        } catch (e: Exception) {}
    }
}
