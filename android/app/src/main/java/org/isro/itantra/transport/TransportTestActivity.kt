package org.isro.itantra.transport

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ScrollView
import android.widget.TextView
import android.widget.LinearLayout
import android.graphics.Color
import org.isro.itantra.transport.wfbng.WfbngManager

class TransportTestActivity : Activity() {

    private var transport: WfbngManager? = null
    private lateinit var logView: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
            setBackgroundColor(Color.parseColor("#121212"))
        }

        val etLocalCallsign = EditText(this).apply { hint = "Local Callsign (NODE_A)"; setText("NODE_A"); setTextColor(Color.WHITE) }
        val etTargetCallsign = EditText(this).apply { hint = "Target Callsign (NODE_B)"; setText("NODE_B"); setTextColor(Color.WHITE) }
        val etTargetIp = EditText(this).apply { hint = "Target IP (10.0.2.17)"; setText("10.0.2.17"); setTextColor(Color.WHITE) }
        val etPort = EditText(this).apply { hint = "UDP Port (8988)"; setText("8988"); setTextColor(Color.WHITE) }
        
        val btnStart = Button(this).apply { text = "START TRANSPORT" }
        val btnSend = Button(this).apply { text = "SEND TEST MESSAGE"; isEnabled = false }
        
        logView = TextView(this).apply { 
            setTextColor(Color.GREEN)
            textSize = 12f
        }
        val scrollView = ScrollView(this).apply { addView(logView) }

        layout.addView(etLocalCallsign)
        layout.addView(etTargetCallsign)
        layout.addView(etTargetIp)
        layout.addView(etPort)
        layout.addView(btnStart)
        layout.addView(btnSend)
        layout.addView(scrollView)
        
        setContentView(layout)

        val fixedKey = ByteArray(32) { 0x42 } // Fixed shared key

        btnStart.setOnClickListener {
            val localCallsign = etLocalCallsign.text.toString().trim()
            val targetIp = etTargetIp.text.toString().trim()
            val port = etPort.text.toString().toIntOrNull() ?: 8988

            transport?.stop()
            transport = WfbngManager(localCallsign, fixedKey, targetIp, port).apply {
                onVoicePayloadDelivered = { origin, language, priority, payload ->
                    runOnUiThread {
                        log("--- PACKET RECEIVED ---")
                        log("Origin: $origin, Lang: $language, Priority: $priority")
                        log("Payload: ${String(payload)}")
                    }
                }
            }
            
            Thread {
                try {
                    transport?.start()
                    runOnUiThread {
                        log("Transport STARTED")
                        log("Local: $localCallsign")
                        log("Target IP: $targetIp:$port")
                        btnSend.isEnabled = true
                    }
                } catch (e: Exception) {
                    runOnUiThread {
                        log("Error starting transport: ${e.message}")
                    }
                }
            }.start()
        }

        btnSend.setOnClickListener {
            val targetCallsign = etTargetCallsign.text.toString().trim()
            val payloadStr = "HELLO_FROM_${etLocalCallsign.text.toString().trim()}"
            
            try {
                transport?.sendVoiceMessage(
                    voicePayload = payloadStr.toByteArray(),
                    language = "en",
                    priority = 1,
                    targetCallsign = targetCallsign
                )
                log("--- PACKET SENT ---")
                log("To: $targetCallsign, Payload: $payloadStr")
            } catch (e: Exception) {
                log("Send Error: ${e.message}")
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        transport?.stop()
    }

    private fun log(msg: String) {
        logView.append("\n$msg")
    }
}
