package org.isro.itantra.runtime


import android.util.Log

class LogcatTransitionLogger : PTTTransitionLogger {

    companion object {
        private const val TAG = "iTantra-PTT"
    }

    override fun logTransition(transition: PTTTransition) {

        Log.d(
            TAG,
            "Transition: " +
                    "${transition.previousState} " +
                    "--(${transition.event})--> " +
                    "${transition.nextState}"
        )
    }
}
