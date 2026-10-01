package org.isro.itantra.runtime

import android.os.Handler
import android.os.Looper
import android.util.Log
import java.util.concurrent.LinkedBlockingDeque

/**
 * MessageScheduler — serializes inbound voice playback so victims don't overlap.
 *
 * Contract:
 *  - Inbound voice packets are enqueued via [enqueue].
 *  - One TTS plays at a time; others wait in FIFO order.
 *  - SOS / life-safety packets jump the queue (LIFO front insert).
 *  - PTT is blocked while any item is playing; caller checks [isChannelBusy].
 *  - When the queue drains, [onQueueEmpty] fires so the UI resets to IDLE.
 *
 * Wire in MainActivity:
 *   scheduler = MessageScheduler(stateMachine)
 *   scheduler.onPlayItem = { item -> playTTS(item.text, item.lang) }
 *   scheduler.onQueueStatus = { count -> updateBanner(count) }
 *   scheduler.onQueueEmpty = { resetPttButton() }
 *   // on inbound packet:
 *   scheduler.enqueue(MessageScheduler.Item(origin, lang, translatedText, gps, isSos))
 */
class MessageScheduler(
    private val stateMachine: PTTStateMachine
) {

    companion object {
        private const val TAG = "MessageScheduler"
        /** Fallback timeout — if TTS onDone never fires, advance queue after this */
        private const val FALLBACK_PLAYBACK_MS = 8_000L
    }

    data class Item(
        val nodeId: String,
        val lang: String,
        val text: String,
        val gps: String = "",            // "lat,lon,acc" or GPS_UNAVAIL
        val isSos: Boolean = false,
        val priority: Int = if (isSos) 10 else 0
    )

    // Callbacks — set by MainActivity
    var onPlayItem: ((Item) -> Unit)? = null
    var onQueueStatus: ((queued: Int, currentNodeId: String) -> Unit)? = null
    var onQueueEmpty: (() -> Unit)? = null
    var onPttBlocked: (() -> Unit)? = null   // fires when user tries PTT while busy

    private val queue = LinkedBlockingDeque<Item>()
    private val handler = Handler(Looper.getMainLooper())
    @Volatile private var isPlaying = false
    @Volatile private var playbackTimeoutRunnable: Runnable? = null

    /** True only while a TTS item is actively playing — PTT is blocked during this time only. */
    val isChannelBusy: Boolean get() = isPlaying

    /**
     * Add an item to the queue.
     * SOS items jump to the front (after any currently-playing item).
     */
    fun enqueue(item: Item) {
        if (item.isSos) {
            queue.addFirst(item)
            Log.i(TAG, "SOS ENQUEUE FRONT: ${item.nodeId} — queue size: ${queue.size}")
        } else {
            queue.addLast(item)
            Log.i(TAG, "ENQUEUE: ${item.nodeId} [${item.lang}] — queue size: ${queue.size}")
        }
        stateMachine.handleEvent(PTTEvent.PACKET_RECEIVED)
        notifyStatus()
        if (!isPlaying) drainNext()
    }

    /**
     * Call this when TTS playback of the current item finishes.
     * Triggers the next item automatically.
     */
    fun onPlaybackDone() {
        handler.post {
            playbackTimeoutRunnable?.let { handler.removeCallbacks(it) }
            playbackTimeoutRunnable = null
            isPlaying = false
            Log.i(TAG, "Playback done — queue remaining: ${queue.size}")
            drainNext()
        }
    }

    /**
     * Check if PTT is allowed. If not, fire [onPttBlocked] and return false.
     */
    fun checkPttAllowed(): Boolean {
        return if (isChannelBusy) {
            Log.i(TAG, "PTT blocked — channel busy (${queue.size} queued)")
            onPttBlocked?.invoke()
            false
        } else {
            true
        }
    }

    /** Clear everything (e.g. on activity destroy). */
    fun clear() {
        queue.clear()
        handler.post {
            playbackTimeoutRunnable?.let { handler.removeCallbacks(it) }
            isPlaying = false
        }
    }

    private fun drainNext() {
        val item = queue.poll()
        if (item == null) {
            // Queue empty
            isPlaying = false
            stateMachine.handleEvent(PTTEvent.TRANSMISSION_COMPLETE)  // back to IDLE
            onQueueEmpty?.invoke()
            Log.i(TAG, "Queue drained → IDLE_LISTENING")
            return
        }

        isPlaying = true
        Log.i(TAG, "PLAY: ${item.nodeId} [${item.lang}] isSos=${item.isSos}")
        notifyStatus(item.nodeId)
        onPlayItem?.invoke(item)

        // Fallback auto-advance if TTS done callback is never called
        val timeout = Runnable {
            Log.w(TAG, "Playback timeout fallback — advancing queue")
            onPlaybackDone()
        }
        playbackTimeoutRunnable = timeout
        handler.postDelayed(timeout, FALLBACK_PLAYBACK_MS)
    }

    private fun notifyStatus(currentNodeId: String = "") {
        onQueueStatus?.invoke(queue.size, currentNodeId)
    }
}
