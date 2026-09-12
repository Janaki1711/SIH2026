package org.isro.itantra

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * LoginActivity — Phone number authentication entry point.
 * Sends OTP to the backend server, then navigates to OtpActivity.
 *
 * Backend server URL is configurable via SharedPreferences.
 * Default: http://10.163.175.227:8000 (the server phone's IP).
 */
class LoginActivity : AppCompatActivity() {

    companion object {
        const val PREF_FILE = "itantra_auth"
        const val PREF_TOKEN = "session_token"
        const val PREF_USER_ID = "user_id"
        const val PREF_DISPLAY_NAME = "display_name"
        const val PREF_LANGUAGE = "preferred_language"
        const val PREF_PHONE = "phone"
        const val PREF_SERVER_URL = "server_url"
        const val PREF_NODE_ID = "node_id"  // unique mesh callsign e.g. "R7K2", "A91C"
        const val DEFAULT_SERVER = "http://10.0.2.2:8000"

        /** Generate a short 4-char alphanumeric node ID from a seed string (phone tail, userId, etc.) */
        fun generateNodeId(seed: String): String {
            val chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  // no confusable 0/O/1/I
            val hash = seed.hashCode().toLong().and(0xFFFFFFFFL)
            return buildString {
                var n = hash
                repeat(4) {
                    append(chars[(n % chars.length).toInt()])
                    n /= chars.length
                }
            }
        }
    }

    private var tapCount = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // If already logged in, skip directly to MainActivity
        val prefs = getSharedPreferences(PREF_FILE, Context.MODE_PRIVATE)
        if (prefs.getString(PREF_TOKEN, null) != null) {
            startMain()
            return
        }

        setContentView(R.layout.activity_login)
        setupUI()
    }

    private fun setupUI() {
        val prefs = getSharedPreferences(PREF_FILE, Context.MODE_PRIVATE)
        val phoneInput = findViewById<EditText>(R.id.loginPhoneInput)
        val serverContainer = findViewById<View>(R.id.loginServerContainer)
        val serverInput = findViewById<EditText>(R.id.loginServerInput)
        val continueBtn = findViewById<Button>(R.id.loginContinueBtn)
        val progressBar = findViewById<ProgressBar>(R.id.loginProgress)
        val errorText = findViewById<TextView>(R.id.loginError)

        serverInput.setText(prefs.getString(PREF_SERVER_URL, DEFAULT_SERVER))


        continueBtn.setOnClickListener {
            val rawPhone = phoneInput.text.toString().trim().replace(" ", "").replace("-", "")
            val phone = if (rawPhone.startsWith("+")) rawPhone else "+91$rawPhone"
            val serverUrl = serverInput.text.toString().trim().trimEnd('/')

            if (rawPhone.length < 10) {
                errorText.text = "Enter a valid 10-digit phone number"
                errorText.visibility = View.VISIBLE
                return@setOnClickListener
            }

            // Save server URL
            prefs.edit().putString(PREF_SERVER_URL, serverUrl).apply()

            errorText.visibility = View.GONE
            progressBar.visibility = View.VISIBLE
            continueBtn.isEnabled = false

            // Send OTP in background thread with offline fallback
            Thread {
                var otpForDemo = "123456"
                var isOfflineFallback = false

                try {
                    val url = URL("$serverUrl/api/auth/send-otp")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "POST"
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.doOutput = true
                    conn.connectTimeout = 4000
                    conn.readTimeout = 4000

                    val body = JSONObject().apply {
                        put("phone", phone)
                        put("captcha_token", "dev_bypass")
                    }.toString()

                    conn.outputStream.use { it.write(body.toByteArray()) }

                    val responseCode = conn.responseCode
                    if (responseCode == 200) {
                        val responseBody = conn.inputStream.bufferedReader().readText()
                        val json = JSONObject(responseBody)
                        otpForDemo = json.optString("otp_for_demo", "123456")
                    } else {
                        isOfflineFallback = true
                    }
                } catch (e: Exception) {
                    // Server unreachable — seamlessly fall back to local offline demo mode
                    isOfflineFallback = true
                }

                runOnUiThread {
                    progressBar.visibility = View.GONE
                    continueBtn.isEnabled = true

                    if (isOfflineFallback) {
                        Toast.makeText(this, "Operating in Local Emergency Mode (OTP: 123456)", Toast.LENGTH_LONG).show()
                    }

                    val intent = Intent(this, OtpActivity::class.java).apply {
                        putExtra("phone", phone)
                        putExtra("server_url", serverUrl)
                        putExtra("otp_hint", otpForDemo)
                        putExtra("is_offline_mode", isOfflineFallback)
                    }
                    startActivity(intent)
                }
            }.start()
        }
    }

    private fun startMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}

