package org.isro.itantra.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class PTTStateMachineTest {

    private class FakeLogger : PTTTransitionLogger {
        var lastTransition: PTTTransition? = null
        override fun logTransition(transition: PTTTransition) {
            lastTransition = transition
        }
    }

    @Test
    fun testIdleListening_PttDown_PttCapturing() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PTT_DOWN)
        assertEquals(PTTState.PTT_CAPTURING, machine.state.value)
    }

    @Test
    fun testPttCapturing_PttUp_Transmitting() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PTT_DOWN) // Move to PTT_CAPTURING
        
        machine.handleEvent(PTTEvent.PTT_UP)
        assertEquals(PTTState.TRANSMITTING, machine.state.value)
    }

    @Test
    fun testTransmitting_TransmissionComplete_IdleListening() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PTT_DOWN) // Move to PTT_CAPTURING
        machine.handleEvent(PTTEvent.PTT_UP) // Move to TRANSMITTING
        
        machine.handleEvent(PTTEvent.TRANSMISSION_COMPLETE)
        assertEquals(PTTState.IDLE_LISTENING, machine.state.value)
    }

    @Test
    fun testIdleListening_PacketReceived_Receiving() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PACKET_RECEIVED)
        assertEquals(PTTState.RECEIVING, machine.state.value)
    }

    @Test
    fun testReceiving_SosTriggered_AlarmActive() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PACKET_RECEIVED) // Move to RECEIVING
        
        machine.handleEvent(PTTEvent.SOS_TRIGGERED)
        assertEquals(PTTState.ALARM_ACTIVE, machine.state.value)
    }

    @Test
    fun testAlarmActive_AlarmFinished_IdleListening() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.SOS_TRIGGERED) // IDLE_LISTENING -> ALARM_ACTIVE
        
        machine.handleEvent(PTTEvent.ALARM_FINISHED)
        assertEquals(PTTState.IDLE_LISTENING, machine.state.value)
    }

    @Test
    fun testInvalid_IdleListening_PttUp_IdleListening() {
        val machine = PTTStateMachine()
        machine.handleEvent(PTTEvent.PTT_UP)
        assertEquals(PTTState.IDLE_LISTENING, machine.state.value)
    }

    @Test
    fun testLoggerInvokedWithCorrectStates() {
        val logger = FakeLogger()
        val machine = PTTStateMachine(logger)
        
        machine.handleEvent(PTTEvent.PTT_DOWN)
        
        val transition = logger.lastTransition
        assertNotNull(transition)
        assertEquals(PTTState.IDLE_LISTENING, transition?.previousState)
        assertEquals(PTTEvent.PTT_DOWN, transition?.event)
        assertEquals(PTTState.PTT_CAPTURING, transition?.nextState)
    }
}

