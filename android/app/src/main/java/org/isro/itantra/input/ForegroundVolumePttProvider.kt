package org.isro.itantra.input

import android.view.KeyEvent

object ForegroundVolumePttProvider : PttInputProvider {

    private var listener: PttKeyListener? = null
    private var isPressed = false

    override fun setPttKeyListener(listener: PttKeyListener?) {
        this.listener = listener
    }

    /**
     * Call this from MainActivity's dispatchKeyEvent.
     * Returns true if the event was consumed.
     */
    fun onDispatchKeyEvent(event: KeyEvent?): Boolean {
        if (event == null) return false

        if (event.keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            when (event.action) {
                KeyEvent.ACTION_DOWN -> {
                    if (!isPressed) {
                        isPressed = true
                        listener?.onPttPressed()
                    }
                    return true // Consume
                }
                KeyEvent.ACTION_UP -> {
                    if (isPressed) {
                        isPressed = false
                        listener?.onPttReleased()
                    }
                    return true // Consume
                }
            }
        }
        return false
    }
}

