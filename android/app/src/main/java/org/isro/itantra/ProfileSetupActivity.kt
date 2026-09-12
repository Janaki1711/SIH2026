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

class ProfileSetupActivity : AppCompatActivity() {

    private val languages = listOf(
        "en" to "English", "hi" to "हिंदी", "kn" to "ಕನ್ನಡ",
        "te" to "తెలుగు", "mr" to "मराठी", "ta" to "தமிழ்",
        "bn" to "বাংলা", "gu" to "ગુજરાતી", "or" to "ଓଡ଼ିଆ", "ml" to "മലയാളം"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile_setup)

        val serverUrl = intent.getStringExtra("server_url") ?: LoginActivity.DEFAULT_SERVER
        val prefs = getSharedPreferences(LoginActivity.PREF_FILE, Context.MODE_PRIVATE)
        val token = prefs.getString(LoginActivity.PREF_TOKEN, "") ?: ""

        val nameInput = findViewById<EditText>(R.id.profileNameInput)
        val langSpinnerSetup = findViewById<Spinner>(R.id.profileLangSpinner)
        val saveBtn = findViewById<Button>(R.id.profileSaveBtn)
        val progressBar = findViewById<ProgressBar>(R.id.profileProgress)
        val errorText = findViewById<TextView>(R.id.profileError)

        // Setup language spinner
        val langNames = languages.map { it.second }
        langSpinnerSetup.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, langNames)

        saveBtn.setOnClickListener {
            val name = nameInput.text.toString().trim()
            if (name.isEmpty()) {
                errorText.text = "Please enter your display name"
                errorText.visibility = View.VISIBLE
                return@setOnClickListener
            }

            val selectedLang = languages[langSpinnerSetup.selectedItemPosition].first
            errorText.visibility = View.GONE
            progressBar.visibility = View.VISIBLE
            saveBtn.isEnabled = false

            Thread {
                try {
                    val url = URL("$serverUrl/api/auth/setup-profile")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "POST"
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.doOutput = true
                    conn.connectTimeout = 4000

                    val body = JSONObject().apply {
                        put("token", token)
                        put("display_name", name)
                        put("preferred_language", selectedLang)
                    }.toString()
                    conn.outputStream.use { it.write(body.toByteArray()) }
                    val code = conn.responseCode
                } catch (e: Exception) {
                    // Offline / local fallback — proceed with local storage
                }

                runOnUiThread {
                    progressBar.visibility = View.GONE
                    saveBtn.isEnabled = true
                    // Save profile locally in SharedPreferences
                    prefs.edit()
                        .putString(LoginActivity.PREF_DISPLAY_NAME, name)
                        .putString(LoginActivity.PREF_LANGUAGE, selectedLang)
                        .apply()
                    startActivity(Intent(this, MainActivity::class.java))
                    finish()
                }
            }.start()
        }
    }

}
