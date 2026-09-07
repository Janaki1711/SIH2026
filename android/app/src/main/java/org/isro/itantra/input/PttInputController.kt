package org.isro.itantra.input

import org.isro.itantra.runtime.PTTEvent
import org.isro.itantra.runtime.PTTStateMachine

class PttInputController(
    private val stateMachine: PTTStateMachine,
    private val inputProvider: PttInputProvider
) : PttKeyListener {

    init {
        inputProvider.setPttKeyListener(this)
    }

    override fun onPttPressed() {
        stateMachine.handleEvent(PTTEvent.PTT_DOWN)
    }

    override fun onPttReleased() {
        stateMachine.handleEvent(PTTEvent.PTT_UP)
    }

    fun release() {
        inputProvider.setPttKeyListener(null)
    }
}

