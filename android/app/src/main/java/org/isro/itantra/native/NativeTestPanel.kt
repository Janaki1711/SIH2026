package org.isro.itantra.native

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import java.nio.ByteBuffer

@Composable
fun NativeTestPanel() {
    var testResult by remember { mutableStateOf("No result yet") }

    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
        Text(
            text = "JNI Native Bridge Test",
            style = MaterialTheme.typography.titleMedium
        )
        Spacer(modifier = Modifier.height(8.dp))
        Button(
            onClick = {
                try {
                    // Create a 10-byte DirectByteBuffer
                    val buffer = ByteBuffer.allocateDirect(10)
                    for (i in 0 until 10) {
                        buffer.put(i, (i + 1).toByte()) // 1, 2, 3... 10
                    }
                    
                    val checksum = NativeBridge.processBuffer(buffer, 10)
                    
                    val modifiedFirstByte = buffer.get(0)
                    
                    testResult = "Checksum: $checksum\nFirst Byte changed to: $modifiedFirstByte"
                } catch (e: Exception) {
                    testResult = "Error: ${e.message}"
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Run Native Buffer Test")
        }
        Spacer(modifier = Modifier.height(8.dp))
        Text(text = testResult)
    }
}

