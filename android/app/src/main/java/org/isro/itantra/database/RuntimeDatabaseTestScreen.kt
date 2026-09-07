package org.isro.itantra.database

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import org.isro.itantra.runtime.CompositeTransitionLogger
import org.isro.itantra.runtime.LogcatTransitionLogger
import org.isro.itantra.runtime.PTTEvent
import org.isro.itantra.runtime.PTTStateMachine

import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue

@Composable
fun RuntimeDatabaseTestScreen() {

    val context = androidx.compose.ui.platform.LocalContext.current

    val database = remember {
        MessageDatabase.getDatabase(context)
    }

    val stateMachine = remember {

        val logger = CompositeTransitionLogger(
            listOf(
                LogcatTransitionLogger(),
                DatabaseTransitionLogger(database)
            )
        )

        val sm = PTTStateMachine(
            logger = logger
        )
        
        org.isro.itantra.input.PttInputController(
            stateMachine = sm,
            inputProvider = org.isro.itantra.input.ForegroundVolumePttProvider
        )
        
        sm
    }

    val currentState by stateMachine.state.collectAsState()
    var transcriptResult by remember { mutableStateOf("No transcription yet") }
    
    // Permission and Asset Initialization
    androidx.compose.runtime.LaunchedEffect(Unit) {
        // Copy assets to cache
        val cacheDir = context.cacheDir
        kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
            org.isro.itantra.utils.AssetHelper.copyAssetsToCache(context, "", cacheDir)
            
            // Init STT Bridge
            val vadModel = java.io.File(cacheDir, "silero_vad.onnx").absolutePath
            val encModel = java.io.File(cacheDir, "encoder.onnx").absolutePath
            val decModel = java.io.File(cacheDir, "ctc_decoder.onnx").absolutePath
            val vocab = java.io.File(cacheDir, "vocab.json").absolutePath
            
            org.isro.itantra.audio.NativeSTTBridge.safeInit(vadModel, encModel, decModel, vocab)
        }
    }
    
    // Connect audio layer
    remember {
        val adapter = org.isro.itantra.runtime.PttAudioAdapter(stateMachine)
        adapter.onTranscriptionResult = { text ->
            transcriptResult = text
        }
        adapter
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {

        Text(
            text = "iTantra Runtime + Black Box",
            style = MaterialTheme.typography.headlineSmall
        )

        Spacer(modifier = Modifier.height(24.dp))

        Text(text = "Current State")
        Text(
            text = currentState.name,
            style = MaterialTheme.typography.headlineMedium
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(text = "STT Result & Lang ID:")
        Text(
            text = transcriptResult,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(PTTEvent.PTT_DOWN)
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("PTT DOWN")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(PTTEvent.PTT_UP)
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("PTT UP")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(
                    PTTEvent.TRANSMISSION_COMPLETE
                )
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("TRANSMISSION COMPLETE")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(
                    PTTEvent.PACKET_RECEIVED
                )
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("PACKET RECEIVED")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(
                    PTTEvent.SOS_TRIGGERED
                )
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("SOS")
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            onClick = {
                stateMachine.handleEvent(
                    PTTEvent.ALARM_FINISHED
                )
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("ALARM FINISHED")
        }
    }
}
