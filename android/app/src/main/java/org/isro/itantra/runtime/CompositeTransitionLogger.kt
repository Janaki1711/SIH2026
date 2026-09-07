package org.isro.itantra.runtime

class CompositeTransitionLogger(
    private val loggers: List<PTTTransitionLogger>
) : PTTTransitionLogger {

    override fun logTransition(transition: PTTTransition) {
        loggers.forEach { logger ->
            logger.logTransition(transition)
        }
    }
}
