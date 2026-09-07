package org.isro.itantra.native

import java.nio.ByteBuffer

object NativeBridge {

    init {
        System.loadLibrary("audio_stt_core")
    }

    /**
     * Passes a DirectByteBuffer to C++.
     * Returns a checksum of the buffer, or a negative error code.
     * The C++ layer will also modify the first byte to 42 as a test.
     */
    external fun processBuffer(buffer: ByteBuffer, size: Int): Int
    
    external fun startOboeRecording(): Boolean
    
    external fun stopOboeRecording()
}


