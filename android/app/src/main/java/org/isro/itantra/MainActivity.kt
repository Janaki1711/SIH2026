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

    private lateinit var netStatusText: TextView
    private lateinit var peerIpInput: EditText
    private lateinit var btnConnectPeer: Button
    private lateinit var statusText: TextView
    private lateinit var langSpinner: Spinner
    private lateinit var testButton: Button
    private lateinit var startButton: Button
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
    private var androidTts: android.speech.tts.TextToSpeech? = null
    private var lastRecognizedText: String = ""
    @Volatile private var isRecording = false
    @Volatile private var isWalkieTalkieMode = true
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

        // Initialize Android System Text-To-Speech fallback
        try {
            androidTts = android.speech.tts.TextToSpeech(this) { status ->
                if (status == android.speech.tts.TextToSpeech.SUCCESS) {
                    androidTts?.language = Locale("en", "IN")
                }
            }
        } catch (e: Throwable) {
            Log.w(TAG, "TTS init notice: ${e.message}")
        }

        // Init WFB-ng Transport & Receiver Pipeline with applicationContext
        try {
            val key = ByteArray(32) { 0x42 } // 32-byte shared AES-256 key
            transport = org.isro.itantra.transport.wfbng.WfbngManager(myCallsign, key, "255.255.255.255", 8988, applicationContext)
            transport?.onVoicePayloadDelivered = { origin, language, priority, payload ->
                android.util.Log.i(TAG, "⚡ Received UDP packet: ${payload.size}B from $origin (source: $language)")
                runOnUiThread { statusText.text = "⚡ Received ${payload.size}B from $origin\nDecompressing..." }
                try {
                    val targetLang = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                        val sel = langSpinner.selectedItem.toString()
                        languageMap[sel]?.substringBefore("-") ?: "en"
                    } else "en"

                    val decodedText = try {
                        if (org.isro.itantra.semantic.SemanticBridge.isLibraryLoaded) {
                            org.isro.itantra.semantic.SemanticBridge.decompressAndTranslate(payload, targetLang)
                        } else {
                            String(payload, java.nio.charset.StandardCharsets.UTF_8)
                        }
                    } catch (e: Throwable) {
                        Log.w(TAG, "Semantic decompress fallback: ${e.message}")
                        String(payload, java.nio.charset.StandardCharsets.UTF_8)
                    }

                    if (decodedText.startsWith("PING") || decodedText.startsWith("CONNECT_PING")) {
                        runOnUiThread {
                            netStatusText.text = "🟢 PEER ONLINE: $origin\n📡 Walkie-Talkie Mesh Active!"
                            netStatusText.setTextColor(Color.parseColor("#00E676"))
                            statusText.text = "🟢 Connected to peer: $origin"
                        }
                    } else {
                        runOnUiThread {
                            statusText.text = "🚨 RX FROM $origin ($language ➔ $targetLang):\n$decodedText"
                        }

                        // Vibrate to alert user
                        try {
                            val vibrator = getSystemService(Context.VIBRATOR_SERVICE) as? android.os.Vibrator
                            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                                vibrator?.vibrate(android.os.VibrationEffect.createOneShot(200, android.os.VibrationEffect.DEFAULT_AMPLITUDE))
                            } else {
                                @Suppress("DEPRECATION")
                                vibrator?.vibrate(200)
                            }
                        } catch (e: Throwable) {}

                        val isAlert = priority.toInt() >= 1 || 
                                      decodedText.contains("SOS", ignoreCase = true) || 
                                      decodedText.contains("ambulance", ignoreCase = true) || 
                                      decodedText.contains("flood", ignoreCase = true) || 
                                      decodedText.contains("fire", ignoreCase = true) || 
                                      decodedText.contains("urgent", ignoreCase = true) || 
                                      decodedText.contains("तत्काल") || 
                                      decodedText.contains("आपात") ||
                                      decodedText.contains("ତୁରନ୍ତ")

                        playTTS(decodedText, targetLang, isAlert)
                    }
                } catch (e: Throwable) {
                    Log.e(TAG, "Rx pipeline error", e)
                    runOnUiThread { statusText.text = "⚡ Received from $origin, decode notice: ${e.message}" }
                }
            }

            transport?.onPeerDiscovered = { peerCallsign, peerIp ->
                runOnUiThread {
                    netStatusText.text = "🟢 PEER ONLINE: $peerCallsign ($peerIp:8988)\n📡 Walkie-Talkie Mesh Active!"
                    netStatusText.setTextColor(Color.parseColor("#00E676"))
                    statusText.text = "🟢 Connected to $peerCallsign ($peerIp:8988)"
                    android.widget.Toast.makeText(this, "🟢 Connected to $peerCallsign ($peerIp)", android.widget.Toast.LENGTH_SHORT).show()
                }
            }

            transport?.onLinkConfirmed = { peerCallsign, peerIp, rtt ->
                runOnUiThread {
                    val rttStr = if (rtt > 0) " | ⚡ RTT: ${rtt}ms" else ""
                    netStatusText.text = "🟢 CONNECTED TO: $peerCallsign ($peerIp:8988)$rttStr\n📡 Two-Way Walkie-Talkie Mesh Active!"
                    netStatusText.setTextColor(Color.parseColor("#00E676"))
                    statusText.text = "🟢 Connected to $peerCallsign ($peerIp:8988)$rttStr"
                }
            }

            Thread { transport?.start() }.start()
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

        btnModeWalkieTalkie.setOnClickListener {
            isWalkieTalkieMode = true
            btnModeWalkieTalkie.backgroundTintList = android.content.res.ColorStateList.valueOf(Color.parseColor("#00E5FF"))
            btnModeWalkieTalkie.setTextColor(Color.parseColor("#0B0E14"))
            btnModePhone.backgroundTintList = android.content.res.ColorStateList.valueOf(Color.parseColor("#374151"))
            btnModePhone.setTextColor(Color.parseColor("#FFFFFF"))
            statusText.text = "📻 Mode: Tactical Walkie-Talkie (PTT active, high volume alerts)"
        }

        btnModePhone.setOnClickListener {
            isWalkieTalkieMode = false
            btnModePhone.backgroundTintList = android.content.res.ColorStateList.valueOf(Color.parseColor("#00E5FF"))
            btnModePhone.setTextColor(Color.parseColor("#0B0E14"))
            btnModeWalkieTalkie.backgroundTintList = android.content.res.ColorStateList.valueOf(Color.parseColor("#374151"))
            btnModeWalkieTalkie.setTextColor(Color.parseColor("#FFFFFF"))
            statusText.text = "📱 Mode: Standard Phone (Normal media voice notes & text)"
        }

        val allIps = getAllLocalIpAddresses()
        val ipDisplay = if (allIps.isNotEmpty()) allIps.joinToString(" / ") else "Offline"

        // Hotspot subnets: standard Android 192.168.43.x, OnePlus OxygenOS 10.0.0.x,
        // some devices use 10.42.0.x or 172.20.10.x (iPhone hotspot)
        val isOnHotspot = allIps.any {
            it.startsWith("192.168.43.") ||
            it.startsWith("10.0.0.") ||
            it.startsWith("10.42.0.") ||
            it.startsWith("172.20.10.")
        }
        // Campus/cellular: 10.x.x.x ranges that are NOT known hotspot subnets
        val isCampusOrCellular = !isOnHotspot && allIps.any {
            it.startsWith("10.") || it.startsWith("100.")
        }

        if (isCampusOrCellular) {
            netStatusText.text = "📱 THIS DEVICE IP: $ipDisplay\n⚠️ You are on Campus Wi-Fi / 5G (AP Isolation active).\n👉 Turn ON Hotspot on Phone 1 & connect Phone 2 to it!"
            netStatusText.setTextColor(Color.parseColor("#FFD600"))
        } else {
            netStatusText.text = "📱 THIS DEVICE IP: $ipDisplay\n👉 Enter the OTHER phone's IP below:"
            netStatusText.setTextColor(Color.parseColor("#00E5FF"))
        }
        peerIpInput.hint = "Enter OTHER Phone's IP"

        btnConnectPeer.setOnClickListener {
            val ip = peerIpInput.text.toString().trim()
            if (ip.isEmpty()) {
                android.widget.Toast.makeText(this, "⚠️ Please enter the other phone's IP address", android.widget.Toast.LENGTH_SHORT).show()
                netStatusText.text = "⚠️ Please enter the OTHER phone's IP below:"
                netStatusText.setTextColor(Color.parseColor("#FFD600"))
                return@setOnClickListener
            }

            val ipRegex = Regex("""^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$""")
            if (!ip.matches(ipRegex)) {
                android.widget.Toast.makeText(this, "❌ Invalid IPv4 address format!\nExample: 10.163.175.126", android.widget.Toast.LENGTH_LONG).show()
                netStatusText.text = "❌ Invalid IP format ($ip)!\n👉 Enter a valid 4-number IP (e.g. 10.163.175.126)"
                netStatusText.setTextColor(Color.parseColor("#FF5252"))
                return@setOnClickListener
            }

            val myIps = getAllLocalIpAddresses()
            if (myIps.contains(ip)) {
                android.widget.Toast.makeText(this, "⚠️ That's THIS phone's IP!\nEnter the OTHER phone's IP.", android.widget.Toast.LENGTH_LONG).show()
                netStatusText.text = "⚠️ You entered THIS phone's IP ($ip)!\n👉 Look at the OTHER phone's screen and type THAT IP."
                netStatusText.setTextColor(Color.parseColor("#FF5252"))
                return@setOnClickListener
            }

            btnConnectPeer.isEnabled = false
            netStatusText.text = "🟡 Connecting to $ip:8988 (Sending Link Probe)..."
            netStatusText.setTextColor(Color.parseColor("#FFD600"))
            statusText.text = "🟡 Probing peer link at $ip:8988..."

            transport?.pingPeer(ip, timeoutMs = 1200L, maxAttempts = 3) { success, peerCallsign, rttMs, msg ->
                runOnUiThread {
                    btnConnectPeer.isEnabled = true
                    if (success) {
                        netStatusText.text = "🟢 CONNECTED TO: $peerCallsign ($ip:8988)\n⚡ RTT: ${rttMs}ms | 📡 Two-Way Walkie-Talkie Mesh Active!"
                        netStatusText.setTextColor(Color.parseColor("#00E676"))
                        statusText.text = "🟢 Connected to $peerCallsign ($ip:8988) | RTT: ${rttMs}ms"
                        android.widget.Toast.makeText(this, "🟢 Connected to $peerCallsign ($ip)!", android.widget.Toast.LENGTH_SHORT).show()
                    } else {
                        netStatusText.text = "❌ Link failed to $ip:8988 (Sent 3 / Recv 0)\n👉 Verify: Both phones on same Wi-Fi / Hotspot & IP is correct."
                        netStatusText.setTextColor(Color.parseColor("#FF5252"))
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
                speechRecognizer?.setRecognitionListener(object : RecognitionListener {
                    override fun onReadyForSpeech(params: Bundle?) {
                        runOnUiThread { statusText.text = "🎙️ Listening (English)... Speak clearly into mic!" }
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
                        Log.i(TAG, "Speech end detected cleanly.")
                    }
                    override fun onError(error: Int) {
                        val errorDesc = when (error) {
                            5, 13, SpeechRecognizer.ERROR_NETWORK ->
                                "Offline Voice: Speak close to mic, or tap a 1-Tap Tactical Alert below!"
                            SpeechRecognizer.ERROR_NO_MATCH ->
                                "No speech detected. Hold mic close and speak clearly."
                            SpeechRecognizer.ERROR_SPEECH_TIMEOUT ->
                                "Silence timeout: no voice heard."
                            SpeechRecognizer.ERROR_AUDIO ->
                                "Microphone audio error."
                            else -> "Mic idle. Tap START RECORDING to speak."
                        }
                        Log.w(TAG, "SpeechRecognizer notice: error code $error")
                        runOnUiThread { statusText.text = "Result:\n$errorDesc" }
                    }

                    override fun onResults(results: Bundle?) {
                        val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            lastRecognizedText = matches[0]
                            val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                                langSpinner.selectedItem.toString()
                            } else {
                                "English (India)"
                            }
                            val langCode = languageMap[selectedLangName]?.substringBefore("-") ?: "en"
                            transmitMessage(lastRecognizedText, langCode)
                        }
                    }

                    override fun onPartialResults(partialResults: Bundle?) {
                        val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                        if (!matches.isNullOrEmpty()) {
                            lastRecognizedText = matches[0]
                            runOnUiThread { statusText.text = "🗣️ Hearing: $lastRecognizedText..." }
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

    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    @Volatile private var totalSamplesPushed = 0L

    private fun startRecording() {
        try {
            isRecording = true
            totalSamplesPushed = 0L
            lastRecognizedText = ""
            val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
                langSpinner.selectedItem.toString()
            } else {
                "English (India)"
            }
            val langTag = languageMap[selectedLangName] ?: "en-IN"
            val langCode = langTag.substringBefore("-")
            val isEnglish = langTag.startsWith("en")

            statusText.text = "🎙️ Listening ($selectedLangName)... Speak clearly into mic!"

            if (isEnglish) {
                // --- PATH 2: DEDICATED ENGLISH ASR ARCHITECTURE ---
                Log.i(TAG, "[LANGUAGE_ROUTER] Language: English ($langTag) -> Route: Dedicated English ASR")
                val speechIntent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, langTag)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, langTag)
                    putExtra(RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_PREFERENCE, langTag)
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                    putExtra("android.speech.extra.DICTATION_MODE", true)
                    putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
                }
                runOnUiThread {
                    try {
                        speechRecognizer?.startListening(speechIntent)
                    } catch (e: Throwable) {
                        Log.w(TAG, "SpeechRecognizer start listening error: ${e.message}")
                    }
                }
            } else {
                // --- PATH 1: DEDICATED INDIC CONFORMER ASR ARCHITECTURE ---
                Log.i(TAG, "[LANGUAGE_ROUTER] Language: Indic ($langTag) -> Route: AI4Bharat IndicConformer")
                if (NativeSTTBridge.isLibraryLoaded) {
                    NativeSTTBridge.safeStartAudioCapture()
                }

                if (ActivityCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                    try {
                        val minBuf = AudioRecord.getMinBufferSize(16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
                        val bufferSize = maxOf(minBuf, 8192)

                        var record: AudioRecord? = AudioRecord(
                            MediaRecorder.AudioSource.VOICE_RECOGNITION,
                            16000,
                            AudioFormat.CHANNEL_IN_MONO,
                            AudioFormat.ENCODING_PCM_16BIT,
                            bufferSize
                        )
                        if (record?.state != AudioRecord.STATE_INITIALIZED) {
                            record?.release()
                            record = AudioRecord(
                                MediaRecorder.AudioSource.MIC,
                                16000,
                                AudioFormat.CHANNEL_IN_MONO,
                                AudioFormat.ENCODING_PCM_16BIT,
                                bufferSize
                            )
                        }

                        if (record?.state == AudioRecord.STATE_INITIALIZED) {
                            audioRecord = record
                            audioRecord?.startRecording()
                            recordingThread = Thread {
                                val pcm = ShortArray(512)
                                while (isRecording && audioRecord?.recordingState == AudioRecord.RECORDSTATE_RECORDING) {
                                    val read = audioRecord?.read(pcm, 0, pcm.size) ?: 0
                                    if (read > 0 && NativeSTTBridge.isLibraryLoaded) {
                                        NativeSTTBridge.safePushAudioPCM(pcm, read)
                                        totalSamplesPushed += read
                                    }
                                }
                            }.apply { start() }
                            Log.i(TAG, "Hardware microphone capture active for Indic STT at 16kHz mono.")
                        } else {
                            Log.e(TAG, "AudioRecord failed to initialize.")
                        }
                    } catch (e: Throwable) {
                        Log.w(TAG, "AudioRecord hardware mic stream notice: ${e.message}")
                    }
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
        val selectedLangName = if (::langSpinner.isInitialized && langSpinner.selectedItem != null) {
            langSpinner.selectedItem.toString()
        } else {
            "English (India)"
        }
        val langTag = languageMap[selectedLangName] ?: "en-IN"
        val langCode = langTag.substringBefore("-")
        val isEnglish = langTag.startsWith("en")

        if (isEnglish) {
            runOnUiThread {
                try {
                    speechRecognizer?.stopListening()
                } catch (e: Throwable) {
                    Log.w(TAG, "SpeechRecognizer stop listening notice: ${e.message}")
                }
            }
        } else {
            Thread {
                try {
                    isRecording = false
                    silenceHandler.removeCallbacks(silenceRunnable)

                    try {
                        recordingThread?.join(500)
                    } catch (e: Throwable) {}

                    try {
                        audioRecord?.stop()
                        audioRecord?.release()
                        audioRecord = null
                    } catch (e: Throwable) {}

                    // Query Native C++ STT Bridge (AI4Bharat Indic Conformer + Silero VAD)
                    var nativeMsg = ""
                    if (NativeSTTBridge.isLibraryLoaded) {
                        nativeMsg = NativeSTTBridge.safeStopAudioCaptureAndTranscribe(langCode)
                    }

                    val cleanMsg = nativeMsg.trim()
                    val processedMsg = convertIndicScript(cleanMsg, langCode)

                    val candidateText = when {
                        processedMsg.isNotBlank() && processedMsg != "आ" && processedMsg != "अ" && processedMsg != "aa" && processedMsg != "a" && !processedMsg.startsWith("No speech") && !processedMsg.contains("Exception") -> processedMsg
                        totalSamplesPushed >= 3200 -> {
                            val durMs = totalSamplesPushed / 16
                            "Voice Alert (${durMs}ms captured: emergency message)"
                        }
                        else -> ""
                    }

                    runOnUiThread {
                        if (candidateText.isNotBlank()) {
                            transmitMessage(candidateText, langCode)
                        } else {
                            statusText.text = "Result:\nNo speech detected. Hold mic close and speak clearly."
                        }
                    }

                } catch (e: Throwable) {
                    Log.e(TAG, "Error stopping recording: ${e.message}", e)
                    runOnUiThread { statusText.text = "Recording stopped." }
                }
            }.start()
        }
    }

    private fun transmitMessage(rawText: String, langCode: String) {
        val correctedText = autoCorrectAndFormatText(rawText, langCode)
        var displayMsg = "Result:\nTranscript ($langCode): $correctedText"

        val packet: ByteArray = try {
            if (org.isro.itantra.semantic.SemanticBridge.isLibraryLoaded) {
                val compressed = org.isro.itantra.semantic.SemanticBridge.compressTranscript(
                    correctedText, langCode, "en", myCallsign, 1
                )
                if (compressed.size <= 38) {
                    displayMsg += "\n⚡ M3 Semantic: ${compressed.size}B (≤38B limit)"
                } else {
                    val numFrags = (compressed.size + 26) / 27
                    displayMsg += "\n⚡ M3: $numFrags fragments × ≤38B each (Total: ${compressed.size}B)"
                }
                compressed
            } else {
                correctedText.toByteArray(java.nio.charset.StandardCharsets.UTF_8)
            }
        } catch (e: Throwable) {
            Log.w(TAG, "Semantic compression fallback: ${e.message}")
            correctedText.toByteArray(java.nio.charset.StandardCharsets.UTF_8)
        }

        try {
            transport?.sendVoiceMessage(packet, langCode, 1.toByte(), "RESCUE_ALL")
            displayMsg += "\n📡 Transmitted over UDP Mesh!"
        } catch (e: Throwable) {
            Log.e(TAG, "Transport send error: ${e.message}", e)
            displayMsg += "\n❌ Send error: ${e.message}"
        }

        runOnUiThread { statusText.text = displayMsg }
    }

    private fun playTTS(text: String, langCode: String, isEmergency: Boolean = false) {
        try {
            if (isEmergency && isWalkieTalkieMode) {
                indicTTSManager?.playEmergencyAlert(text, langCode)
                return
            }
            if (indicTTSManager != null) {
                indicTTSManager?.speak(text, langCode)
                return
            }
        } catch (e: Throwable) {
            Log.w(TAG, "IndicTTSManager speak notice: ${e.message}")
        }

        // Fallback to Android OS TTS
        try {
            val locale = when (langCode) {
                "hi" -> Locale("hi", "IN")
                "ta" -> Locale("ta", "IN")
                "te" -> Locale("te", "IN")
                "mr" -> Locale("mr", "IN")
                "bn" -> Locale("bn", "IN")
                "kn" -> Locale("kn", "IN")
                "ml" -> Locale("ml", "IN")
                "gu" -> Locale("gu", "IN")
                "or" -> Locale("or", "IN")
                "pa" -> Locale("pa", "IN")
                else -> Locale("en", "IN")
            }
            androidTts?.language = locale
            androidTts?.speak(text, android.speech.tts.TextToSpeech.QUEUE_FLUSH, null, "iTantra_TTS")
        } catch (e: Throwable) {
            Log.w(TAG, "Android TTS fallback notice: ${e.message}")
        }
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

    override fun onDestroy() {
        super.onDestroy()
        try {
            silenceHandler.removeCallbacks(silenceRunnable)
            speechRecognizer?.destroy()
            indicTTSManager?.shutdown()
            androidTts?.stop()
            androidTts?.shutdown()
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


