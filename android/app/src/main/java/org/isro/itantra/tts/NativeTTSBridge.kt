package org.isro.itantra.tts

import android.util.Log

class NativeTTSBridge {

    companion object {
        private const val TAG = "iTantra_NativeBridge"
        private var isLoaded = false

        init {
            try {
                System.loadLibrary("audio_tts_core")
                isLoaded = true
                Log.i(TAG, "libaudio_tts_core.so successfully loaded.")
            } catch (e: UnsatisfiedLinkError) {
                Log.e(TAG, "Failed to load libaudio_tts_core.so", e)
                isLoaded = false
            }
        }

        fun isNativeAvailable(): Boolean = isLoaded
    }

    private var engineHandle: Long = 0L

    init {
        if (isLoaded) {
            engineHandle = nativeCreateEngine()
        }
    }

    fun synthesize(text: String, langCode: String, prosody: ProsodyVector): FloatArray {
        if (!isLoaded || engineHandle == 0L) return FloatArray(0)
        return nativeSynthesize(engineHandle, text, langCode, prosody.toByteArray())
    }

    fun generateSiren(durationSec: Float = 1.0f): FloatArray {
        if (!isLoaded || engineHandle == 0L) return FloatArray(0)
        return nativeGenerateSiren(engineHandle, durationSec)
    }

    fun startPlayer(sampleRate: Int = 16000): Boolean {
        if (!isLoaded || engineHandle == 0L) return false
        return nativeStartPlayer(engineHandle, sampleRate)
    }

    fun stopPlayer() {
        if (isLoaded && engineHandle != 0L) {
            nativeStopPlayer(engineHandle)
        }
    }

    fun enqueueAudio(audioData: FloatArray) {
        if (isLoaded && engineHandle != 0L && audioData.isNotEmpty()) {
            nativeEnqueueAudio(engineHandle, audioData)
        }
    }

    fun setVolume(volume: Float) {
        if (isLoaded && engineHandle != 0L) {
            nativeSetVolume(engineHandle, volume)
        }
    }

    fun release() {
        if (isLoaded && engineHandle != 0L) {
            nativeDestroyEngine(engineHandle)
            engineHandle = 0L
        }
    }

    // Native JNI declarations
    private external fun nativeCreateEngine(): Long
    private external fun nativeDestroyEngine(handle: Long)
    private external fun nativeSynthesize(handle: Long, text: String, langCode: String, prosodyBytes: ByteArray): FloatArray
    private external fun nativeGenerateSiren(handle: Long, durationSec: Float): FloatArray
    private external fun nativeStartPlayer(handle: Long, sampleRate: Int): Boolean
    private external fun nativeStopPlayer(handle: Long)
    private external fun nativeEnqueueAudio(handle: Long, audioData: FloatArray)
    private external fun nativeSetVolume(handle: Long, volume: Float)
}
