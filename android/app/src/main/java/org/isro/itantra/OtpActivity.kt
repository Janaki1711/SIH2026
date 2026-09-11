package org.isro.itantra

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.CountDownTimer
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class OtpActivity : AppCompatActivity() {

    private var phone = ""
    private var serverUrl = ""
    private var resendTimer: CountDownTimer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_otp)

        phone = intent.getStringExtra("phone") ?: ""
        serverUrl = intent.getStringExtra("server_url") ?: LoginActivity.DEFAULT_SERVER
        val otpHint = intent.getStringExtra("otp_hint") ?: ""

        setupUI(otpHint)
    }

    private fun setupUI(otpHint: String) {
        val phoneLabel = findViewById<TextView>(R.id.otpPhoneLabel)
        val otpInput = findViewById<EditText>(R.id.otpInput)
        val verifyBtn = findViewById<Button>(R.id.otpVerifyBtn)
        val resendBtn = findViewById<Button>(R.id.otpResendBtn)
        val progressBar = findViewById<ProgressBar>(R.id.otpProgress)
        val errorText = findViewById<TextView>(R.id.otpError)
        val devHint = findViewById<TextView>(R.id.otpDevHint)

        phoneLabel.text = "OTP sent to $phone"

        // DEV MODE: show OTP hint
        if (otpHint.isNotEmpty()) {
            devHint.text = "DEV MODE — OTP: $otpHint"
            devHint.visibility = View.VISIBLE
        }

        // Start 60s resend cooldown
        startResendTimer(resendBtn)

        verifyBtn.setOnClickListener {
            val otp = otpInput.text.toString().trim()
            if (otp.length != 6) {
                errorText.text = "Enter the 6-digit OTP"
                errorText.visibility = View.VISIBLE
                return@setOnClickListener
            }
            errorText.visibility = View.GONE
            progressBar.visibility = View.VISIBLE
            verifyBtn.isEnabled = false

            verifyOtp(otp, progressBar, verifyBtn, errorText)
        }

        resendBtn.setOnClickListener {
            resendOtp(resendBtn)
        }
    }

    private fun verifyOtp(otp: String, progress: ProgressBar, verifyBtn: Button, errorText: TextView) {
        Thread {
            try {
                val url = URL("$serverUrl/api/auth/verify-otp")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                conn.connectTimeout = 10000
                conn.readTimeout = 10000

                val body = JSONObject().apply {
                    put("phone", phone)
                    put("otp", otp)
                }.toString()
                conn.outputStream.use { it.write(body.toByteArray()) }

                val responseCode = conn.responseCode
                val responseBody = if (responseCode == 200) {
                    conn.inputStream.bufferedReader().readText()
                } else {
                    conn.errorStream?.bufferedReader()?.readText() ?: ""
                }

                runOnUiThread {
                    progress.visibility = View.GONE
                    verifyBtn.isEnabled = true

                    if (responseCode == 200) {
                        val json = JSONObject(responseBody)
                        if (json.optBoolean("success", false)) {
                            val token = json.optString("session_token", "")
                            val userId = json.optString("user_id", "")
                            val needsSetup = json.optBoolean("needs_profile_setup", true)

                            // Save token
                            getSharedPreferences(LoginActivity.PREF_FILE, Context.MODE_PRIVATE)
                                .edit()
                                .putString(LoginActivity.PREF_TOKEN, token)
                                .putString(LoginActivity.PREF_USER_ID, userId)
                                .putString(LoginActivity.PREF_PHONE, phone)
                                .apply()

                            if (needsSetup) {
                                startActivity(Intent(this, ProfileSetupActivity::class.java).apply {
                                    putExtra("server_url", serverUrl)
                                })
                            } else {
                                startActivity(Intent(this, MainActivity::class.java))
                            }
                            finish()
                        } else {
                            errorText.text = json.optString("error", "Verification failed")
                            errorText.visibility = View.VISIBLE
                        }
                    } else {
                        val msg = try {
                            JSONObject(responseBody).optString("detail", "Invalid OTP")
                        } catch (e: Exception) { "Invalid OTP. Please try again." }
                        errorText.text = msg
                        errorText.visibility = View.VISIBLE
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    progress.visibility = View.GONE
                    verifyBtn.isEnabled = true
                    errorText.text = "Network error: ${e.message}"
                    errorText.visibility = View.VISIBLE
                }
            }
        }.start()
    }

    private fun resendOtp(resendBtn: Button) {
        resendBtn.isEnabled = false
        Thread {
            try {
                val url = URL("$serverUrl/api/auth/send-otp")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.doOutput = true
                val body = JSONObject().apply {
                    put("phone", phone)
                    put("captcha_token", "dev_bypass")
                }.toString()
                conn.outputStream.use { it.write(body.toByteArray()) }
                val code = conn.responseCode
                val resp = if (code == 200) conn.inputStream.bufferedReader().readText() else ""

                runOnUiThread {
                    if (code == 200) {
                        val hint = JSONObject(resp).optString("otp_for_demo", "")
                        if (hint.isNotEmpty()) {
                            findViewById<TextView>(R.id.otpDevHint).let {
                                it.text = "DEV MODE — OTP: $hint"
                                it.visibility = View.VISIBLE
                            }
                        }
                        android.widget.Toast.makeText(this, "OTP resent", android.widget.Toast.LENGTH_SHORT).show()
                        startResendTimer(resendBtn)
                    }
                }
            } catch (e: Exception) {
                runOnUiThread { resendBtn.isEnabled = true }
            }
        }.start()
    }

    private fun startResendTimer(resendBtn: Button) {
        resendTimer?.cancel()
        resendBtn.isEnabled = false
        resendTimer = object : CountDownTimer(60000, 1000) {
            override fun onTick(ms: Long) {
                resendBtn.text = "Resend OTP in ${ms / 1000}s"
            }
            override fun onFinish() {
                resendBtn.isEnabled = true
                resendBtn.text = "Resend OTP"
            }
        }.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        resendTimer?.cancel()
    }
}
