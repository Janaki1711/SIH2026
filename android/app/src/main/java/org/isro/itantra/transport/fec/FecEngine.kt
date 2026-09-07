package org.isro.itantra.transport.fec

// Minimal XOR-based Block FEC (RAID-4 style)
// For k data shards and 1 parity shard (m=1 supported fully, m>1 ignores extra parity)
class FecEngine(val k: Int = 8, val m: Int = 4) {

    fun encode(shards: Array<ByteArray>): Array<ByteArray> {
        val totalShards = k + m
        val shardSize = shards[0].size
        val allShards = Array(totalShards) { ByteArray(shardSize) }
        
        for (i in 0 until k) {
            System.arraycopy(shards[i], 0, allShards[i], 0, shardSize)
            for (j in 0 until shardSize) {
                allShards[k][j] = (allShards[k][j].toInt() xor shards[i][j].toInt()).toByte()
            }
        }
        // Additional parity shards (m > 1) are just copies for this stub
        for (i in k + 1 until totalShards) {
            System.arraycopy(allShards[k], 0, allShards[i], 0, shardSize)
        }
        return allShards
    }

    fun decode(shards: Array<ByteArray?>, shardSize: Int): Array<ByteArray>? {
        var missingDataIndex = -1
        var missingCount = 0
        
        for (i in 0 until k) {
            if (shards[i] == null) {
                missingDataIndex = i
                missingCount++
            }
        }
        
        if (missingCount > 1) return null // XOR can only recover 1 missing block
        if (missingCount == 0) return Array(k) { i -> shards[i]!! }
        
        // Recover 1 missing block using parity (shards[k])
        val parity = shards[k] ?: shards[k+1] ?: return null
        val recovered = ByteArray(shardSize)
        System.arraycopy(parity, 0, recovered, 0, shardSize)
        
        for (i in 0 until k) {
            if (i != missingDataIndex && shards[i] != null) {
                for (j in 0 until shardSize) {
                    recovered[j] = (recovered[j].toInt() xor shards[i]!![j].toInt()).toByte()
                }
            }
        }
        
        val result = Array(k) { i ->
            if (i == missingDataIndex) recovered else shards[i]!!
        }
        return result
    }
}
