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
        const val DEFAULT_SERVER = "http://10.163.175.227:8000"
    }

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
        val serverInput = findViewById<EditText>(R.id.loginServerInput)
        val continueBtn = findViewById<Button>(R.id.loginContinueBtn)
        val progressBar = findViewById<ProgressBar>(R.id.loginProgress)
        val errorText = findViewById<TextView>(R.id.loginError)

        // Show current server URL
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

            // Send OTP in background thread
            Thread {
                try {
                    val url = URL("$serverUrl/api/auth/send-otp")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "POST"
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.doOutput = true
                    conn.connectTimeout = 10000
                    conn.readTimeout = 10000

                    val body = JSONObject().apply {
                        put("phone", phone)
                        put("captcha_token", "dev_bypass")
                    }.toString()

                    conn.outputStream.use { it.write(body.toByteArray()) }

                    val responseCode = conn.responseCode
                    val responseBody = if (responseCode == 200) {
                        conn.inputStream.bufferedReader().readText()
                    } else {
                        conn.errorStream?.bufferedReader()?.readText() ?: ""
                    }

                    runOnUiThread {
                        progressBar.visibility = View.GONE
                        continueBtn.isEnabled = true

                        if (responseCode == 200) {
                            val json = JSONObject(responseBody)
                            val otpForDemo = json.optString("otp_for_demo", "")
                            // Navigate to OTP screen
                            val intent = Intent(this, OtpActivity::class.java).apply {
                                putExtra("phone", phone)
                                putExtra("server_url", serverUrl)
                                putExtra("otp_hint", otpForDemo) // shown in DEV MODE only
                            }
                            startActivity(intent)
                        } else {
                            val msg = try {
                                JSONObject(responseBody).optString("detail", "Failed to send OTP")
                            } catch (e: Exception) { "Failed to send OTP. Check server URL." }
                            errorText.text = msg
                            errorText.visibility = View.VISIBLE
                        }
                    }
                } catch (e: Exception) {
                    runOnUiThread {
                        progressBar.visibility = View.GONE
                        continueBtn.isEnabled = true
                        errorText.text = "Cannot reach server: ${e.message}\nCheck the server URL above."
                        errorText.visibility = View.VISIBLE
                    }
                }
            }.start()
        }
    }

    private fun startMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
