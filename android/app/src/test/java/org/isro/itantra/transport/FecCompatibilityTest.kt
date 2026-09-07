package org.isro.itantra.transport

import org.isro.itantra.transport.fec.FecEngine
import org.junit.Test
import org.junit.Assert.*

class FecCompatibilityTest {
    @Test
    fun testKotlinParityGeneration() {
        val fec = FecEngine(k = 8, m = 4)
        val data = Array(8) { i -> ByteArray(10) { (i + 1).toByte() } }
        
        val encoded = fec.encode(data)
        
        // Print the first parity block (index 8)
        val parity = encoded[8]
        val hex = parity.joinToString("") { "%02x".format(it) }
        println("Kotlin XOR parity block 0: $hex")
    }
}
