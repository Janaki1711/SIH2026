package org.isro.itantra.ui

import android.app.Activity
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PorterDuff
import android.graphics.PorterDuffXfermode
import android.graphics.RectF
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import org.isro.itantra.R

/** A small, replayable first-run guide that spotlights the real controls. */
object OnboardingGuide {
    private const val PREFS = "itantra_onboarding"
    private const val COMPLETED = "main_guide_completed"

    private data class Step(val targetId: Int, val title: String, val body: String)

    private val steps = listOf(
        Step(
            R.id.netStatusText,
            "Start on the same hotspot",
            "Turn on a Wi-Fi hotspot on one phone and connect every iTantra phone to it. Internet is not needed to exchange messages. Download any required translation models before going offline. Tap this status for connection diagnostics."
        ),
        Step(
            R.id.langSpinner,
            "Choose your speaking language",
            "Select the language you will speak. Other phones can choose their own language for translated playback."
        ),
        Step(
            R.id.rosterText,
            "Check who is on the mesh",
            "Nearby iTantra phones on the same hotspot appear here. Wait for a peer before starting your communication demo."
        ),
        Step(
            R.id.startButton,
            "Talk, then tap to send",
            "Tap once to start recording. Speak clearly, then tap again to stop and send. The button shows when it is listening or processing."
        ),
        Step(
            R.id.customMsgInput,
            "Send a typed message",
            "Type a message in your selected language and tap Send. Incoming and outgoing messages appear in the conversation area."
        )
    )

    fun maybeStart(activity: Activity, root: ViewGroup) {
        val completed = activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE)
            .getBoolean(COMPLETED, false)
        if (!completed) root.post { start(activity, root, 0) }
    }

    fun start(activity: Activity, root: ViewGroup, startAt: Int = 0) {
        if (steps.isEmpty() || activity.isFinishing) return
        (root.findViewWithTag<View>("itantra_onboarding_overlay")?.parent as? ViewGroup)
            ?.removeView(root.findViewWithTag("itantra_onboarding_overlay"))

        val overlay = FrameLayout(activity).apply {
            tag = "itantra_onboarding_overlay"
            isClickable = true
            isFocusable = true
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES
        }
        val spotlight = SpotlightView(activity)
        overlay.addView(spotlight, FrameLayout.LayoutParams(-1, -1))

        val card = LinearLayout(activity).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(activity, 20), dp(activity, 18), dp(activity, 20), dp(activity, 16))
            background = GradientDrawable().apply {
                setColor(Color.WHITE)
                cornerRadius = dp(activity, 18).toFloat()
                setStroke(dp(activity, 1), Color.rgb(216, 224, 231))
            }
            elevation = dp(activity, 8).toFloat()
        }
        val title = TextView(activity).apply {
            textSize = 18f
            setTextColor(Color.rgb(20, 42, 59))
            typeface = android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL)
        }
        val body = TextView(activity).apply {
            textSize = 14f
            setTextColor(Color.rgb(65, 82, 96))
            setLineSpacing(dp(activity, 3).toFloat(), 1f)
        }
        val stepLabel = TextView(activity).apply {
            textSize = 12f
            setTextColor(Color.rgb(83, 101, 117))
        }
        val controls = LinearLayout(activity).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val skip = Button(activity).apply {
            text = "Skip guide"
            textSize = 12f
            setTextColor(Color.rgb(18, 81, 138))
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.rgb(234, 242, 248))
            setOnClickListener { finish(activity, root, overlay) }
        }
        val spacer = View(activity)
        val back = Button(activity).apply {
            text = "Back"
            textSize = 12f
            setTextColor(Color.rgb(18, 81, 138))
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.WHITE)
        }
        val next = Button(activity).apply {
            textSize = 12f
            setTextColor(Color.WHITE)
            backgroundTintList = android.content.res.ColorStateList.valueOf(Color.rgb(23, 105, 170))
        }
        controls.addView(skip)
        controls.addView(spacer, LinearLayout.LayoutParams(0, 1, 1f))
        controls.addView(back)
        controls.addView(next)
        card.addView(title)
        card.addView(body, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(activity, 8) })
        card.addView(stepLabel, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(activity, 12) })
        card.addView(controls, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(activity, 8) })

        overlay.addView(card)
        var index = startAt.coerceIn(0, steps.lastIndex)

        fun showStep() {
            val step = steps[index]
            title.text = step.title
            body.text = step.body
            stepLabel.text = "${index + 1} of ${steps.size}"
            back.isEnabled = index > 0
            back.alpha = if (index > 0) 1f else 0.45f
            next.text = if (index == steps.lastIndex) "Done" else "Next"
            val target = activity.findViewById<View>(step.targetId)
            spotlight.setTarget(target)
            target.post {
                val targetLocation = IntArray(2)
                val rootLocation = IntArray(2)
                target.getLocationOnScreen(targetLocation)
                root.getLocationOnScreen(rootLocation)
                val targetCenterY = targetLocation[1] - rootLocation[1] + target.height / 2
                val placeAtBottom = targetCenterY < root.height * 0.58f
                val params = (card.layoutParams as? FrameLayout.LayoutParams)
                    ?: FrameLayout.LayoutParams(-1, -2)
                params.gravity = if (placeAtBottom) Gravity.BOTTOM else Gravity.TOP
                params.leftMargin = dp(activity, 18)
                params.rightMargin = dp(activity, 18)
                params.topMargin = if (placeAtBottom) 0 else dp(activity, 22)
                params.bottomMargin = if (placeAtBottom) dp(activity, 22) else 0
                card.layoutParams = params
                spotlight.invalidate()
            }
        }

        back.setOnClickListener { if (index > 0) { index--; showStep() } }
        next.setOnClickListener {
            if (index < steps.lastIndex) { index++; showStep() }
            else finish(activity, root, overlay)
        }

        root.addView(overlay, ViewGroup.LayoutParams(-1, -1))
        showStep()
        title.requestFocus()
    }

    private fun finish(activity: Activity, root: ViewGroup, overlay: View) {
        activity.getSharedPreferences(PREFS, Activity.MODE_PRIVATE).edit()
            .putBoolean(COMPLETED, true).apply()
        root.removeView(overlay)
    }

    private fun dp(activity: Activity, value: Int): Int =
        (value * activity.resources.displayMetrics.density).toInt()

    private class SpotlightView(activity: Activity) : View(activity) {
        private val density = activity.resources.displayMetrics.density
        private val scrim = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = 0xB3000000.toInt() }
        private val clear = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            xfermode = PorterDuffXfermode(PorterDuff.Mode.CLEAR)
        }
        private val outline = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = Color.rgb(23, 105, 170)
            style = Paint.Style.STROKE
            strokeWidth = 2.5f * density
        }
        private var target: View? = null
        private val rect = RectF()

        init { setLayerType(View.LAYER_TYPE_SOFTWARE, null) }

        fun setTarget(view: View?) { target = view; invalidate() }

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            canvas.drawRect(0f, 0f, width.toFloat(), height.toFloat(), scrim)
            val view = target?.takeIf { it.isShown } ?: return
            val targetLocation = IntArray(2)
            val rootLocation = IntArray(2)
            view.getLocationOnScreen(targetLocation)
            (parent as? View)?.getLocationOnScreen(rootLocation)
            val pad = 7f * density
            rect.set(
                targetLocation[0] - rootLocation[0] - pad,
                targetLocation[1] - rootLocation[1] - pad,
                targetLocation[0] - rootLocation[0] + view.width + pad,
                targetLocation[1] - rootLocation[1] + view.height + pad
            )
            canvas.drawRoundRect(rect, 14f * density, 14f * density, clear)
            canvas.drawRoundRect(rect, 14f * density, 14f * density, outline)
        }
    }
}
