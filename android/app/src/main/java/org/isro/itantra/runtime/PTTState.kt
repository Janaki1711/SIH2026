package org.isro.itantra.runtime


enum class PTTState {
    IDLE_LISTENING,
    PTT_CAPTURING,
    TRANSMITTING,
    RECEIVING,
    QUEUE_WAITING,   // playing current item, more items in queue
    ALARM_ACTIVE
}
