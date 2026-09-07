package org.isro.itantra.audio

import android.util.Log

object NativeSTTBridge {

    private const val TAG = "NativeSTTBridge"

    var isLibraryLoaded: Boolean = false
        private set

    init {
        try {
            // Load dependent ONNX Runtime shared library first
            try {
                System.loadLibrary("onnxruntime")
                Log.i(TAG, "libonnxruntime.so loaded successfully.")
            } catch (e: Throwable) {
                Log.w(TAG, "libonnxruntime.so load notice: ${e.message}")
            }

            // Load main STT C++ core library
            System.loadLibrary("audio_stt_core")
            isLibraryLoaded = true
            Log.i(TAG, "Native library libaudio_stt_core.so loaded successfully.")
        } catch (e: Throwable) {
            isLibraryLoaded = false
            Log.w(TAG, "Native library load notice (expected on 16KB preview emulators): ${e.message}")
        }
    }

    fun safeInit(vadModelPath: String, sttEncoderPath: String, sttDecoderPath: String, vocabJsonPath: String): Boolean {
        if (!isLibraryLoaded) return false
        return try {
            initNativeEngine(vadModelPath, sttEncoderPath, sttDecoderPath, vocabJsonPath)
        } catch (e: Throwable) {
            false
        }
    }

    fun safeStartAudioCapture(): Boolean {
        if (!isLibraryLoaded) return false
        return try {
            startAudioCapture()
        } catch (e: Throwable) {
            false
        }
    }

    fun safePushAudioPCM(pcmData: ShortArray, length: Int) {
        if (!isLibraryLoaded) return
        try {
            pushAudioPCM(pcmData, length)
        } catch (e: Throwable) {
            Log.w(TAG, "safePushAudioPCM notice: ${e.message}")
        }
    }

    fun safePumpRingBuffer() {
        if (!isLibraryLoaded) return
        try {
            pumpRingBuffer()
        } catch (e: Throwable) {
            Log.w(TAG, "pumpRingBuffer notice: ${e.message}")
        }
    }

    fun safeStopAudioCaptureAndTranscribe(langCode: String): String {
        if (!isLibraryLoaded) return ""
        return try {
            stopAudioCaptureAndTranscribe(langCode)
        } catch (e: Throwable) {
            ""
        }
    }

    @JvmStatic
    external fun initNativeEngine(
        vadModelPath: String,
        sttEncoderPath: String,
        sttDecoderPath: String,
        vocabJsonPath: String
    ): Boolean

    @JvmStatic
    external fun startAudioCapture(): Boolean

    @JvmStatic
    external fun pushAudioPCM(pcmData: ShortArray, length: Int)

    @JvmStatic
    external fun pumpRingBuffer()

    @JvmStatic
    external fun stopAudioCaptureAndTranscribe(langCode: String): String

    @JvmStatic
    external fun releaseNativeEngine()
}

