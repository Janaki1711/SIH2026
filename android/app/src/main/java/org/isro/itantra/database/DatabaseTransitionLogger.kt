package org.isro.itantra.database

import org.isro.itantra.runtime.PTTTransition
import org.isro.itantra.runtime.PTTTransitionLogger
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class DatabaseTransitionLogger(
    private val database: MessageDatabase
) : PTTTransitionLogger {

    private val scope = CoroutineScope(
        SupervisorJob() + Dispatchers.IO
    )

    override fun logTransition(transition: PTTTransition) {

        scope.launch {

            val log = MessageAuditLog(
                timestamp = transition.timestamp,
                messageId = "RUNTIME_${transition.timestamp}",
                senderId = "LOCAL",
                receiverId = "LOCAL",
                messageType = transition.event.toString(),
                previousState = transition.previousState.name,
                nextState = transition.nextState.name,
                status = "STATE_TRANSITION"
            )

            database.messageAuditLogDao().insert(log)
        }
    }
}
