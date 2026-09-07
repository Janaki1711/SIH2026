package org.isro.itantra.database

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun DatabaseTestScreen() {

    val context = androidx.compose.ui.platform.LocalContext.current
    val scope = rememberCoroutineScope()

    var result by remember {
        mutableStateOf("No database operation performed")
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {

        Text(text = result)

        Button(
            onClick = {

                scope.launch {

                    val database =
                        MessageDatabase.getDatabase(context)

                    val record = MessageAuditLog(
                        timestamp = System.currentTimeMillis(),
                        messageId = "TEST001",
                        senderId = "DEVICE_A",
                        receiverId = "DEVICE_B",
                        messageType = "TEST",
                        previousState = "IDLE_LISTENING",
                        nextState = "PTT_CAPTURING",
                        status = "SUCCESS"
                    )

                    database.messageAuditLogDao().insert(record)

                    result = "Record inserted successfully"
                }
            }
        ) {
            Text("INSERT TEST RECORD")
        }

        Button(
            onClick = {

                scope.launch {

                    val database =
                        MessageDatabase.getDatabase(context)

                    val logs =
                        database.messageAuditLogDao().getAllLogs()

                    result = "Records in database: ${logs.size}"
                }
            }
        ) {
            Text("READ DATABASE")
        }

        Button(
            onClick = {

                scope.launch {

                    val database =
                        MessageDatabase.getDatabase(context)

                    database.messageAuditLogDao().deleteAll()

                    result = "Database cleared"
                }
            }
        ) {
            Text("CLEAR DATABASE")
        }
    }
}
