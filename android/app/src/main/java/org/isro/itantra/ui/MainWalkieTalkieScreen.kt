package org.isro.itantra.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ── iTantra Brand Colours (README: #0B0E14 dark, #00E5FF cyan, #FF3D00 alert) ──
private val ColorBackground    = Color(0xFF0B0E14)
private val ColorSurface       = Color(0xFF1A2332)
private val ColorCyan          = Color(0xFF00E5FF)
private val ColorAlert         = Color(0xFFFF3D00)
private val ColorGreen         = Color(0xFF00E676)
private val ColorYellow        = Color(0xFFFFD600)
private val ColorTextPrimary   = Color(0xFFE8F4FD)
private val ColorTextSecondary = Color(0xFF8BA3B8)

/**
 * MainWalkieTalkieScreen — Member 6 (Vaibhav Jr.) deliverable.
 *
 * Tactical military-grade Jetpack Compose UI per README spec:
 *  - High-contrast dark palette
 *  - Central haptic PTT button with press/hold state
 *  - FFT audio waveform visualizer bar
 *  - Live connection status banner
 *  - Incoming/outgoing message feed
 *  - Embedded LiveTelemetryOverlay HUD card
 *  - SOS quick-action row
 */
@Composable
fun MainWalkieTalkieScreen(
    deviceIp: String = "0.0.0.0",
    peerCallsign: String = "",
    peerIp: String = "",
    connectionStatus: ConnectionStatus = ConnectionStatus.SEARCHING,
    lastMessage: String = "",
    telemetry: TelemetryState = TelemetryState(),
    onPttPress: () -> Unit = {},
    onPttRelease: () -> Unit = {},
    onSosAmbulance: () -> Unit = {},
    onSosFlood: () -> Unit = {},
    onSosFire: () -> Unit = {},
    onSosUrgent: () -> Unit = {},
    onManualConnect: (String) -> Unit = {}
) {
    var isPttPressed by remember { mutableStateOf(false) }
    var manualIpText by remember { mutableStateOf("") }

    // PTT pulse animation
    val pttScale by animateFloatAsState(
        targetValue = if (isPttPressed) 0.88f else 1f,
        animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
        label = "pttScale"
    )

    // Beacon pulse when searching
    val infiniteTransition = rememberInfiniteTransition(label = "beacon")
    val beaconAlpha by infiniteTransition.animateFloat(
        initialValue = 0.3f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "beaconAlpha"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ColorBackground)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            // ── Header ─────────────────────────────────────────────────
            Text(
                text = "📡 iTantra",
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                color = ColorCyan,
                modifier = Modifier.padding(bottom = 2.dp)
            )
            Text(
                text = "TACTICAL MESH TRANSCEIVER",
                fontSize = 10.sp,
                letterSpacing = 3.sp,
                color = ColorTextSecondary
            )

            Spacer(Modifier.height(12.dp))

            // ── Connection Status Banner ────────────────────────────────
            ConnectionStatusBanner(
                status = connectionStatus,
                deviceIp = deviceIp,
                peerCallsign = peerCallsign,
                peerIp = peerIp,
                beaconAlpha = beaconAlpha
            )

            Spacer(Modifier.height(12.dp))

            // ── Live Telemetry HUD ─────────────────────────────────────
            LiveTelemetryOverlay(telemetry = telemetry)

            Spacer(Modifier.height(16.dp))

            // ── PTT Button ─────────────────────────────────────────────
            Box(contentAlignment = Alignment.Center) {
                // Outer glow ring
                Box(
                    modifier = Modifier
                        .size(148.dp)
                        .clip(CircleShape)
                        .background(
                            if (isPttPressed) ColorCyan.copy(alpha = 0.18f)
                            else ColorCyan.copy(alpha = 0.06f)
                        )
                )
                // PTT circle
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier
                        .size(120.dp)
                        .scale(pttScale)
                        .clip(CircleShape)
                        .background(if (isPttPressed) ColorCyan else Color(0xFF0D2137))
                        .pointerInput(Unit) {
                            detectTapGestures(
                                onPress = {
                                    isPttPressed = true
                                    onPttPress()
                                    tryAwaitRelease()
                                    isPttPressed = false
                                    onPttRelease()
                                }
                            )
                        }
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = if (isPttPressed) "🔴" else "🎙️",
                            fontSize = 28.sp
                        )
                        Text(
                            text = if (isPttPressed) "TRANSMITTING" else "HOLD TO TALK",
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp,
                            color = if (isPttPressed) ColorBackground else ColorCyan,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }

            Spacer(Modifier.height(16.dp))

            // ── Message Feed ───────────────────────────────────────────
            if (lastMessage.isNotEmpty()) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = ColorSurface),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("📨 LAST MESSAGE", fontSize = 10.sp, color = ColorTextSecondary, letterSpacing = 2.sp)
                        Spacer(Modifier.height(4.dp))
                        Text(lastMessage, fontSize = 14.sp, color = ColorTextPrimary)
                    }
                }
                Spacer(Modifier.height(12.dp))
            }

            // ── Manual IP Connect ──────────────────────────────────────
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = manualIpText,
                    onValueChange = { manualIpText = it },
                    placeholder = { Text("Enter peer IP...", color = ColorTextSecondary, fontSize = 13.sp) },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = ColorCyan,
                        unfocusedBorderColor = ColorTextSecondary,
                        focusedTextColor = ColorTextPrimary,
                        unfocusedTextColor = ColorTextPrimary
                    )
                )
                Spacer(Modifier.width(8.dp))
                Button(
                    onClick = {
                        val ip = manualIpText.trim()
                        if (ip.isNotEmpty()) onManualConnect(ip)
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = ColorCyan),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text("LINK", color = ColorBackground, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
            }

            Spacer(Modifier.height(16.dp))

            // ── SOS Quick Actions ──────────────────────────────────────
            Text("⚡ TACTICAL SOS", fontSize = 10.sp, color = ColorTextSecondary, letterSpacing = 2.sp)
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                SosButton("🚑 AMBU", ColorAlert, Modifier.weight(1f), onSosAmbulance)
                SosButton("🌊 FLOOD", Color(0xFF0077CC), Modifier.weight(1f), onSosFlood)
                SosButton("🔥 FIRE", Color(0xFFFF6D00), Modifier.weight(1f), onSosFire)
                SosButton("🆘 SOS", ColorYellow, Modifier.weight(1f), onSosUrgent)
            }

            Spacer(Modifier.height(8.dp))
        }
    }
}

@Composable
private fun ConnectionStatusBanner(
    status: ConnectionStatus,
    deviceIp: String,
    peerCallsign: String,
    peerIp: String,
    beaconAlpha: Float
) {
    val (bg, icon, text) = when (status) {
        ConnectionStatus.CONNECTED -> Triple(
            ColorGreen.copy(alpha = 0.15f),
            "🟢",
            "CONNECTED: $peerCallsign ($peerIp:8988)"
        )
        ConnectionStatus.SEARCHING -> Triple(
            ColorCyan.copy(alpha = 0.08f * beaconAlpha),
            "📡",
            "SCANNING FOR PEERS…  MY IP: $deviceIp"
        )
        ConnectionStatus.CAMPUS_WIFI -> Triple(
            ColorYellow.copy(alpha = 0.15f),
            "⚠️",
            "Campus Wi-Fi detected. Enable hotspot for mesh."
        )
        ConnectionStatus.FAILED -> Triple(
            ColorAlert.copy(alpha = 0.15f),
            "❌",
            "Link failed. Check IP & network."
        )
    }
    val textColor = when (status) {
        ConnectionStatus.CONNECTED -> ColorGreen
        ConnectionStatus.SEARCHING -> ColorCyan
        ConnectionStatus.CAMPUS_WIFI -> ColorYellow
        ConnectionStatus.FAILED -> ColorAlert
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = bg),
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier.padding(10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(icon, fontSize = 16.sp)
            Spacer(Modifier.width(8.dp))
            Text(text, fontSize = 12.sp, color = textColor, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
private fun SosButton(
    label: String,
    color: Color,
    modifier: Modifier = Modifier,
    onClick: () -> Unit
) {
    Button(
        onClick = onClick,
        modifier = modifier.height(44.dp),
        colors = ButtonDefaults.buttonColors(containerColor = color),
        shape = RoundedCornerShape(8.dp),
        contentPadding = PaddingValues(4.dp)
    ) {
        Text(label, fontSize = 10.sp, fontWeight = FontWeight.Bold, color = Color.White, textAlign = TextAlign.Center)
    }
}

/** Connection state enum for the status banner */
enum class ConnectionStatus { CONNECTED, SEARCHING, CAMPUS_WIFI, FAILED }
