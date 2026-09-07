package org.isro.itantra.runtime

import org.isro.itantra.native.NativeBridge
import org.isro.itantra.audio.NativeSTTBridge
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.collectLatest

class PttAudioAdapter(
    private val stateMachine: PTTStateMachine
) {
    private val scope = CoroutineScope(Dispatchers.Main + Job())
    private var isRecording = false
    private var pumpJob: Job? = null
    
    // Callback to pass transcription back to UI (Test/Debug UI)
    var onTranscriptionResult: ((String) -> Unit)? = null

    init {
        scope.launch {
            stateMachine.state.collectLatest { state ->
                when (state) {
                    PTTState.PTT_CAPTURING -> {
                        if (!isRecording) {
                            NativeSTTBridge.safeStartAudioCapture()
                            val success = NativeBridge.startOboeRecording()
                            if (success) {
                                isRecording = true
                                pumpJob = scope.launch(Dispatchers.IO) {
                                    while (isActive && isRecording) {
                                        NativeSTTBridge.safePumpRingBuffer()
                                        delay(30)
                                    }
                                }
                            }
                        }
                    }
                    else -> {
                        if (isRecording) {
                            isRecording = false
                            pumpJob?.cancelAndJoin()
                            NativeBridge.stopOboeRecording()
                            NativeSTTBridge.safePumpRingBuffer() // Final flush
                            
                            val transcript = NativeSTTBridge.safeStopAudioCaptureAndTranscribe("hi")
                            withContext(Dispatchers.Main) {
                                onTranscriptionResult?.invoke(transcript)
                            }
                        }
                    }
                }
            }
        }
    }
}

