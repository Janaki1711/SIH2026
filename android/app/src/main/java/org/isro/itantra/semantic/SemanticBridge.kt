package org.isro.itantra.semantic

import android.util.Log

/**
 * SemanticBridge — Android Kotlin Native Interface for Member 3 (iTantra Core).
 *
 * Compresses recognized speech transcripts into 4-38 byte packets and
 * decodes incoming packets into the destination Indic language.
 */
object SemanticBridge {

    private const val TAG = "SemanticBridge"

    var isLibraryLoaded: Boolean = false
        private set

    init {
        try {
            System.loadLibrary("itantra_core")
            isLibraryLoaded = true
            Log.i(TAG, "libitantra_core.so loaded successfully.")
        } catch (e: Throwable) {
            isLibraryLoaded = false
            Log.w(TAG, "Semantic core library not loaded (expected in standalone STT builds): ${e.message}")
        }
    }

    /**
     * Compresses a text transcript into an ultra-low bitrate binary packet (4-38 bytes).
     */
    external fun compressTranscript(
        transcript: String,
        srcLang: String,
        targetLang: String,
        callsign: String,
        seq: Int
    ): ByteArray

    /**
     * Decompress an incoming binary packet and realizes it into targetLang.
     */
    external fun decompressAndTranslate(
        wireBytes: ByteArray,
        targetLang: String
    ): String

    /**
     * Translate [text] from [srcLang] into [tgtLang] using the on-device M3
     * semantic engine (parse → semantic IR → realize) across all 10 mission
     * languages — including ml/or/pa, for which ML Kit has no model.
     *
     * Free-form text is returned unchanged (honest passthrough) so callers
     * can fall through to their ML Kit cascade without mistaking the
     * passthrough for a translation.
     */
    external fun translateText(
        text: String,
        srcLang: String,
        tgtLang: String
    ): String
}
