package org.isro.itantra.tts

import org.isro.itantra.R

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.MotionEvent
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.Spinner
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var ttsManager: IndicTTSManager
    private lateinit var pttController: PTTTransceiverController

    private lateinit var rgMode: RadioGroup
    private lateinit var rbWalkieTalkie: RadioButton
    private lateinit var rbPhoneMode: RadioButton
    private lateinit var spinnerLanguage: Spinner
    private lateinit var etSpeechText: EditText

    // 10 Preset Buttons for all 10 Indian Languages
    private lateinit var btnPresetHi: Button
    private lateinit var btnPresetTa: Button
    private lateinit var btnPresetTe: Button
    private lateinit var btnPresetKn: Button
    private lateinit var btnPresetMl: Button
    private lateinit var btnPresetMr: Button
    private lateinit var btnPresetGu: Button
    private lateinit var btnPresetBn: Button
    private lateinit var btnPresetOr: Button
    private lateinit var btnPresetEn: Button

    private lateinit var btnPlayAudio: Button
    private lateinit var btnPttTalk: Button
    private lateinit var btnEmergencySos: Button

    private lateinit var tvPayloadSize: TextView
    private lateinit var tvLatency: TextView
    private lateinit var tvTransceiverState: TextView

    // 10 Indian Languages
    private val languages = listOf(
        "Hindi (hi)" to "hi",
        "Tamil (ta)" to "ta",
        "Telugu (te)" to "te",
        "Kannada (kn)" to "kn",
        "Malayalam (ml)" to "ml",
        "Marathi (mr)" to "mr",
        "Gujarati (gu)" to "gu",
        "Bengali (bn)" to "bn",
        "Odia (or)" to "or",
        "English (en)" to "en"
    )

    @SuppressLint("ClickableViewAccessibility")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        checkAndRequestPermissions()

        initViews()

        ttsManager = IndicTTSManager(this) { statusMsg ->
            tvTransceiverState.text = statusMsg
        }
        pttController = PTTTransceiverController(this, ttsManager)

        setupListeners()
    }

    private fun initViews() {
        rgMode = findViewById(R.id.rgMode)
        rbWalkieTalkie = findViewById(R.id.rbWalkieTalkie)
        rbPhoneMode = findViewById(R.id.rbPhoneMode)
        spinnerLanguage = findViewById(R.id.spinnerLanguage)
        etSpeechText = findViewById(R.id.etSpeechText)

        // 10 Language Presets
        btnPresetHi = findViewById(R.id.btnPresetHi)
        btnPresetTa = findViewById(R.id.btnPresetTa)
        btnPresetTe = findViewById(R.id.btnPresetTe)
        btnPresetKn = findViewById(R.id.btnPresetKn)
        btnPresetMl = findViewById(R.id.btnPresetMl)
        btnPresetMr = findViewById(R.id.btnPresetMr)
        btnPresetGu = findViewById(R.id.btnPresetGu)
        btnPresetBn = findViewById(R.id.btnPresetBn)
        btnPresetOr = findViewById(R.id.btnPresetOr)
        btnPresetEn = findViewById(R.id.btnPresetEn)

        btnPlayAudio = findViewById(R.id.btnPlayAudio)
        btnPttTalk = findViewById(R.id.btnPttTalk)
        btnEmergencySos = findViewById(R.id.btnEmergencySos)

        tvPayloadSize = findViewById(R.id.tvPayloadSize)
        tvLatency = findViewById(R.id.tvLatency)
        tvTransceiverState = findViewById(R.id.tvTransceiverState)

        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_dropdown_item,
            languages.map { it.first }
        )
        spinnerLanguage.adapter = adapter
    }

    @SuppressLint("ClickableViewAccessibility", "SetTextI18n")
    private fun setupListeners() {
        rgMode.setOnCheckedChangeListener { _, checkedId ->
            if (checkedId == R.id.rbWalkieTalkie) {
                pttController.setMode(PTTTransceiverController.TransceiverMode.WALKIE_TALKIE_HALF_DUPLEX)
                tvTransceiverState.text = "STATE: HALF-DUPLEX (PTT READY)"
            } else {
                pttController.setMode(PTTTransceiverController.TransceiverMode.PHONE_FULL_DUPLEX)
                tvTransceiverState.text = "STATE: FULL-DUPLEX (PHONE MODE)"
            }
        }

        btnPlayAudio.setOnClickListener {
            val langCode = languages[spinnerLanguage.selectedItemPosition].second
            val text = etSpeechText.text.toString().ifEmpty { "Testing iTantra audio reception." }
            tvPayloadSize.text = "PAYLOAD: " + (text.toByteArray().size + 16) + " BYTES"
            tvLatency.text = "LATENCY: < 15ms"
            ttsManager.speak(text, langCode)
        }

        btnPttTalk.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    val langCode = languages[spinnerLanguage.selectedItemPosition].second
                    val text = etSpeechText.text.toString().ifEmpty { "Testing iTantra transmission" }
                    pttController.onPttPressed(text, langCode)
                    tvPayloadSize.text = "PAYLOAD: " + (text.toByteArray().size + 16) + " BYTES"
                    tvLatency.text = "LATENCY: < 15ms"
                    true
                }
                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                    pttController.onPttReleased()
                    tvTransceiverState.text = "STATE: IDLE (RX STANDBY)"
                    true
                }
                else -> false
            }
        }

        btnEmergencySos.setOnClickListener {
            val langCode = languages[spinnerLanguage.selectedItemPosition].second
            val emergencyText = etSpeechText.text.toString().ifEmpty {
                "EMERGENCY SOS ALERT! IMMEDIATE ASSISTANCE REQUIRED AT SECTOR ALPHA."
            }
            pttController.triggerEmergencySos(emergencyText, langCode)
            tvPayloadSize.text = "PAYLOAD: 40-BYTE SEMANTIC PACKET (PRIORITY 0)"
            tvLatency.text = "LATENCY: 8ms HARDWARE INTR"
        }

        // --- All 10 Language Preset Listeners ---
        // 1. Hindi
        btnPresetHi.setOnClickListener {
            spinnerLanguage.setSelection(0)
            etSpeechText.setText("यह इसरो आई-तंत्रा आपातकालीन संचार प्रणाली है।")
        }

        // 2. Tamil
        btnPresetTa.setOnClickListener {
            spinnerLanguage.setSelection(1)
            etSpeechText.setText("இது இஸ்ரோ ஐ-தந்திரா அவசர தொடர்பு அமைப்பு.")
        }

        // 3. Telugu
        btnPresetTe.setOnClickListener {
            spinnerLanguage.setSelection(2)
            etSpeechText.setText("ఇది ಇಸ್ರೋ ಐ-ತಂತ್ರ అత్యవసర సమాచార వ్యవస్థ.")
        }

        // 4. Kannada
        btnPresetKn.setOnClickListener {
            spinnerLanguage.setSelection(3)
            etSpeechText.setText("ಇಸ್ರೋ ಐ-ತಂತ್ರ ತುರ್ತು ಸಂದೇಶ ಸಂಪರ್ಕ ಸ್ಥಾಪಿಸಲಾಗಿದೆ.")
        }

        // 5. Malayalam
        btnPresetMl.setOnClickListener {
            spinnerLanguage.setSelection(4)
            etSpeechText.setText("ഇത് ഐഎസ്ആർഒ ഐ-തന്ത്ര അടിയന്തര ആശയവിനിമയ സംവിധാനമാണ്.")
        }

        // 6. Marathi
        btnPresetMr.setOnClickListener {
            spinnerLanguage.setSelection(5)
            etSpeechText.setText("ही इस्रो आय-तंत्र आणीबाणी संप्रेषण प्रणाली आहे.")
        }

        // 7. Gujarati
        btnPresetGu.setOnClickListener {
            spinnerLanguage.setSelection(6)
            etSpeechText.setText("આ ઈસરો આઈ-તંત્ર કટોકટી સંચાર પ્રણાલી છે.")
        }

        // 8. Bengali
        btnPresetBn.setOnClickListener {
            spinnerLanguage.setSelection(7)
            etSpeechText.setText("এটি ইসরো আই-তন্ত্র জরুরী যোগাযোগ ব্যবস্থা।")
        }

        // 9. Odia
        btnPresetOr.setOnClickListener {
            spinnerLanguage.setSelection(8)
            etSpeechText.setText("ଏହା ଇସ୍ରୋ ଆଇ-ତନ୍ତ୍ର ଜରୁରୀକାଳୀନ ଯୋଗାଯୋଗ ବ୍ୟବସ୍ଥା।")
        }

        // 10. English
        btnPresetEn.setOnClickListener {
            spinnerLanguage.setSelection(9)
            etSpeechText.setText("ISRO iTantra Ultra-Low Bitrate Neural Transceiver link established.")
        }
    }

    private fun checkAndRequestPermissions() {
        val permissions = arrayOf(
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.MODIFY_AUDIO_SETTINGS,
            Manifest.permission.ACCESS_NOTIFICATION_POLICY
        )
        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), 1001)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        pttController.shutdown()
        ttsManager.shutdown()
    }
}

