package org.isro.itantra.transport

/**
 * Reed-Solomon GF(2^8) Cauchy Erasure Coding Engine for Android.
 * 100% Cross-Language Compatible with Python fec_engine.py.
 *
 * Parameters:
 * - K (Data Shards) = 8
 * - M (Parity Shards) = 4
 * - Primitive Polynomial = 0x11D (285)
 * - Generator Matrix: Cauchy Matrix C[i][j] = 1 / ((i + K) ^ j)
 */
class ReedSolomonFECEngine(val k: Int = 8, val m: Int = 4) {

    val n: Int = k + m

    private object GF256 {
        const val POLYNOMIAL = 0x11D
        val exp = IntArray(512)
        val log = IntArray(256)

        init {
            var x = 1
            for (i in 0 until 255) {
                exp[i] = x
                exp[i + 255] = x
                log[x] = i
                x = x shl 1
                if ((x and 0x100) != 0) {
                    x = x xor POLYNOMIAL
                }
            }
            log[0] = 0
        }

        fun mul(a: Int, b: Int): Int {
            if (a == 0 || b == 0) return 0
            return exp[log[a] + log[b]]
        }

        fun inv(a: Int): Int {
            require(a != 0) { "Zero has no inverse in GF(2^8)" }
            return exp[255 - log[a]]
        }
    }

    private val matrix: Array<IntArray> = Array(m) { i ->
        IntArray(k) { j ->
            val xi = i + k
            val yj = j
            GF256.inv(xi xor yj)
        }
    }

    fun encode(payload: ByteArray): Array<ByteArray> {
        val shardSize = (payload.size + k - 1) / k
        val paddedLen = shardSize * k
        val padded = ByteArray(paddedLen)
        System.arraycopy(payload, 0, padded, 0, payload.size)

        val shards = Array(n) { ByteArray(shardSize) }

        // 1. Data Shards (0..K-1)
        for (i in 0 until k) {
            System.arraycopy(padded, i * shardSize, shards[i], 0, shardSize)
        }

        // 2. Cauchy Parity Shards (K..K+M-1)
        for (i in 0 until m) {
            val parity = ByteArray(shardSize)
            for (j in 0 until k) {
                val coeff = matrix[i][j]
                val dShard = shards[j]
                for (b in 0 until shardSize) {
                    val pVal = parity[b].toInt() and 0xFF
                    val dVal = dShard[b].toInt() and 0xFF
                    parity[b] = (pVal xor GF256.mul(coeff, dVal)).toByte()
                }
            }
            shards[k + i] = parity
        }

        return shards
    }

    fun decode(receivedShards: Map<Int, ByteArray>, originalPayloadLen: Int): ByteArray {
        require(receivedShards.size >= k) {
            "Insufficient shards: need $k, got ${receivedShards.size}"
        }

        // Fast path: All K data shards received intact
        var hasAllData = true
        for (i in 0 until k) {
            if (!receivedShards.containsKey(i)) {
                hasAllData = false
                break
            }
        }
        if (hasAllData) {
            val recovered = ByteArray(k * receivedShards[0]!!.size)
            for (i in 0 until k) {
                System.arraycopy(receivedShards[i]!!, 0, recovered, i * receivedShards[0]!!.size, receivedShards[0]!!.size)
            }
            val result = ByteArray(originalPayloadLen)
            System.arraycopy(recovered, 0, result, 0, originalPayloadLen)
            return result
        }

        val selectedIndices = receivedShards.keys.sorted().take(k)
        val shardSize = receivedShards[selectedIndices[0]]!!.size

        // Build K x K submatrix
        val submatrix = Array(k) { r ->
            val idx = selectedIndices[r]
            if (idx < k) {
                IntArray(k) { c -> if (c == idx) 1 else 0 }
            } else {
                matrix[idx - k].clone()
            }
        }

        val invMatrix = invertMatrix(submatrix)

        // Reconstruct K data shards
        val recoveredData = ByteArray(k * shardSize)
        for (i in 0 until k) {
            val reconstructed = ByteArray(shardSize)
            for (j in 0 until k) {
                val coeff = invMatrix[i][j]
                val rShard = receivedShards[selectedIndices[j]]!!
                for (b in 0 until shardSize) {
                    val rVal = rShard[b].toInt() and 0xFF
                    val curVal = reconstructed[b].toInt() and 0xFF
                    reconstructed[b] = (curVal xor GF256.mul(coeff, rVal)).toByte()
                }
            }
            System.arraycopy(reconstructed, 0, recoveredData, i * shardSize, shardSize)
        }

        val result = ByteArray(originalPayloadLen)
        System.arraycopy(recoveredData, 0, result, 0, originalPayloadLen)
        return result
    }

    private fun invertMatrix(mat: Array<IntArray>): Array<IntArray> {
        val dim = mat.size
        val A = Array(dim) { r -> mat[r].clone() }
        val I = Array(dim) { r -> IntArray(dim) { c -> if (r == c) 1 else 0 } }

        for (col in 0 until dim) {
            var pivotRow = -1
            for (row in col until dim) {
                if (A[row][col] != 0) {
                    pivotRow = row
                    break
                }
            }
            require(pivotRow != -1) { "Singular matrix in RS decoding" }

            val tempA = A[col]; A[col] = A[pivotRow]; A[pivotRow] = tempA
            val tempI = I[col]; I[col] = I[pivotRow]; I[pivotRow] = tempI

            val pivotInv = GF256.inv(A[col][col])
            for (j in 0 until dim) {
                A[col][j] = GF256.mul(A[col][j], pivotInv)
                I[col][j] = GF256.mul(I[col][j], pivotInv)
            }

            for (row in 0 until dim) {
                if (row != col && A[row][col] != 0) {
                    val factor = A[row][col]
                    for (j in 0 until dim) {
                        A[row][j] = A[row][j] xor GF256.mul(factor, A[col][j])
                        I[row][j] = I[row][j] xor GF256.mul(factor, I[col][j])
                    }
                }
            }
        }
        return I
    }
}
