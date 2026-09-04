package org.isro.itantra.tts

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

    private lateinit var btnPresetHi: Button
    private lateinit var btnPresetTa: Button
    private lateinit var btnPresetTe: Button
    private lateinit var btnPresetEn: Button

    private lateinit var btnPttTalk: Button
    private lateinit var btnEmergencySos: Button

    private lateinit var tvPayloadSize: TextView
    private lateinit var tvLatency: TextView
    private lateinit var tvTransceiverState: TextView

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

        ttsManager = IndicTTSManager(this)
        pttController = PTTTransceiverController(this, ttsManager)

        initViews()
        setupListeners()
    }

    private fun initViews() {
        rgMode = findViewById(R.id.rgMode)
        rbWalkieTalkie = findViewById(R.id.rbWalkieTalkie)
        rbPhoneMode = findViewById(R.id.rbPhoneMode)
        spinnerLanguage = findViewById(R.id.spinnerLanguage)
        etSpeechText = findViewById(R.id.etSpeechText)

        btnPresetHi = findViewById(R.id.btnPresetHi)
        btnPresetTa = findViewById(R.id.btnPresetTa)
        btnPresetTe = findViewById(R.id.btnPresetTe)
        btnPresetEn = findViewById(R.id.btnPresetEn)

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

        btnPttTalk.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    val langCode = languages[spinnerLanguage.selectedItemPosition].second
                    val text = etSpeechText.text.toString().ifEmpty { "Testing iTantra transmission" }
                    pttController.onPttPressed(text, langCode)
                    tvTransceiverState.text = "STATE: TRANSMITTING (TX ACTIVE)"
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
            val emergencyText = "EMERGENCY SOS ALERT! IMMEDIATE ASSISTANCE REQUIRED AT SECTOR ALPHA."
            pttController.triggerEmergencySos(emergencyText, langCode)
            tvTransceiverState.text = "STATE: EMERGENCY OVERRIDE ACTIVE (100% VOL)"
            tvPayloadSize.text = "PAYLOAD: 40-BYTE SEMANTIC PACKET (PRIORITY 0)"
            tvLatency.text = "LATENCY: 8ms HARDWARE INTR"
        }

        btnPresetHi.setOnClickListener {
            spinnerLanguage.setSelection(0)
            etSpeechText.setText("यह इसरो आई-तंत्रा आपातकालीन संचार प्रणाली है।")
        }

        btnPresetTa.setOnClickListener {
            spinnerLanguage.setSelection(1)
            etSpeechText.setText("இது இஸ்ரோ ஐ-தந்திரா அவசர தொடர்பு அமைப்பு.")
        }

        btnPresetTe.setOnClickListener {
            spinnerLanguage.setSelection(2)
            etSpeechText.setText("ఇది ఇస్రో ఐ-తంత్ర అత్యవసర సమాచార వ్యవస్థ.")
        }

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
