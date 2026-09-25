package org.isro.itantra.runtime


sealed class PTTEvent {

    data object PTT_DOWN : PTTEvent()

    data object PTT_UP : PTTEvent()

    data object TRANSMISSION_STARTED : PTTEvent()

    data object TRANSMISSION_COMPLETE : PTTEvent()

    data object PACKET_RECEIVED : PTTEvent()

    /** Fired by MessageScheduler when all queued inbound items have been played. */
    data object QUEUE_DRAIN : PTTEvent()

    data object SOS_TRIGGERED : PTTEvent()

    data object ALARM_FINISHED : PTTEvent()

    data class ERROR(val message: String) : PTTEvent()
}
