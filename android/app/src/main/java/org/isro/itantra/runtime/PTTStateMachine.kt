package org.isro.itantra.runtime

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class PTTStateMachine(
    private val logger: PTTTransitionLogger? = null
) {

    private val _state = MutableStateFlow(PTTState.IDLE_LISTENING)

    val state: StateFlow<PTTState> = _state.asStateFlow()

    fun handleEvent(event: PTTEvent) {

        val currentState = _state.value

        val nextState = when (currentState) {

            PTTState.IDLE_LISTENING -> {
                when (event) {
                    PTTEvent.PTT_DOWN -> PTTState.PTT_CAPTURING
                    PTTEvent.PACKET_RECEIVED -> PTTState.RECEIVING
                    PTTEvent.SOS_TRIGGERED -> PTTState.ALARM_ACTIVE
                    else -> currentState
                }
            }

            PTTState.PTT_CAPTURING -> {
                when (event) {
                    PTTEvent.PTT_UP -> PTTState.TRANSMITTING
                    PTTEvent.SOS_TRIGGERED -> PTTState.ALARM_ACTIVE
                    else -> currentState
                }
            }

            PTTState.TRANSMITTING -> {
                when (event) {
                    PTTEvent.TRANSMISSION_COMPLETE -> PTTState.IDLE_LISTENING
                    PTTEvent.SOS_TRIGGERED -> PTTState.ALARM_ACTIVE
                    else -> currentState
                }
            }

            PTTState.RECEIVING -> {
                when (event) {
                    PTTEvent.TRANSMISSION_COMPLETE -> PTTState.IDLE_LISTENING
                    PTTEvent.SOS_TRIGGERED -> PTTState.ALARM_ACTIVE
                    else -> currentState
                }
            }

            PTTState.ALARM_ACTIVE -> {
                when (event) {
                    PTTEvent.ALARM_FINISHED -> PTTState.IDLE_LISTENING
                    else -> currentState
                }
            }
        }

        _state.value = nextState

        // Record the transition
        logger?.logTransition(
            PTTTransition(
                timestamp = System.currentTimeMillis(),
                previousState = currentState,
                event = event,
                nextState = nextState
            )
        )
    }
}
