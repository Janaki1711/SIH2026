package org.isro.itantra.runtime

data class PTTTransition(
    val timestamp: Long,
    val previousState: PTTState,
    val event: PTTEvent,
    val nextState: PTTState
)
