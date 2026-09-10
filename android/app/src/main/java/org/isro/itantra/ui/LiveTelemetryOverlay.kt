package org.isro.itantra.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val ColorBackground    = Color(0xFF0B0E14)
private val ColorSurface       = Color(0xFF1A2332)
private val ColorCyan          = Color(0xFF00E5FF)
private val ColorGreen         = Color(0xFF00E676)
private val ColorYellow        = Color(0xFFFFD600)
private val ColorTextSecondary = Color(0xFF8BA3B8)

/**
 * TelemetryState — data class holding all live RF + processing metrics
 * displayed in the LiveTelemetryOverlay HUD card.
 */
data class TelemetryState(
    val payloadBytes: Int = 0,          // e.g. 38
    val airtimeMs: Int = 0,             // e.g. 18
    val bandwidthSavedPct: Float = 0f,  // e.g. 99.8
    val fecParityBlocks: Int = 4,       // Reed-Solomon parity count
    val carrier: String = "Wi-Fi",      // "Wi-Fi Direct", "Wi-Fi Hotspot", "BT", "BLE"
    val txCount: Int = 0,
    val rxCount: Int = 0,
    val rssiDbm: Int = 0,               // Link quality in dBm
    val compressionTier: Int = 3        // 1=Macro(6B), 2=Structured(22B), 3=Phoneme(38B)
)

/**
 * LiveTelemetryOverlay — Member 6 (Vaibhav Jr.) deliverable.
 *
 * Real-time diagnostic HUD card per README spec displaying:
 *  - Payload size (6–38 Bytes)
 *  - Airtime latency (ms)
 *  - Bandwidth saved (%)
 *  - WFB-ng FEC parity blocks
 *  - Carrier (Wi-Fi Direct / BT)
 *  - TX / RX packet counts
 */
@Composable
fun LiveTelemetryOverlay(
    telemetry: TelemetryState,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = ColorSurface),
        shape = RoundedCornerShape(10.dp)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {

            // Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "⚡ LIVE TELEMETRY",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp,
                    color = ColorCyan
                )
                Spacer(Modifier.weight(1f))
                CarrierBadge(telemetry.carrier)
            }

            Spacer(Modifier.height(8.dp))

            // Metrics grid — two columns
            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    MetricItem(
                        label = "PAYLOAD",
                        value = if (telemetry.payloadBytes > 0) "${telemetry.payloadBytes} B" else "– B",
                        valueColor = when {
                            telemetry.payloadBytes in 1..8   -> ColorGreen
                            telemetry.payloadBytes in 9..22  -> ColorCyan
                            telemetry.payloadBytes in 23..38 -> ColorYellow
                            else -> ColorTextSecondary
                        }
                    )
                    MetricItem(
                        label = "AIRTIME",
                        value = if (telemetry.airtimeMs > 0) "${telemetry.airtimeMs} ms" else "– ms",
                        valueColor = if (telemetry.airtimeMs in 1..30) ColorGreen else ColorYellow
                    )
                    MetricItem(
                        label = "BW SAVED",
                        value = if (telemetry.bandwidthSavedPct > 0) "%.1f%%".format(telemetry.bandwidthSavedPct) else "–",
                        valueColor = ColorGreen
                    )
                }
                Spacer(Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    MetricItem(
                        label = "FEC PARITY",
                        value = "${telemetry.fecParityBlocks} blocks",
                        valueColor = ColorCyan
                    )
                    MetricItem(
                        label = "TX / RX",
                        value = "${telemetry.txCount} / ${telemetry.rxCount}",
                        valueColor = ColorTextSecondary
                    )
                    MetricItem(
                        label = "TIER",
                        value = when (telemetry.compressionTier) {
                            1 -> "T1 Macro"
                            2 -> "T2 Struct"
                            else -> "T3 Phoneme"
                        },
                        valueColor = when (telemetry.compressionTier) {
                            1 -> ColorGreen
                            2 -> ColorCyan
                            else -> ColorYellow
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun MetricItem(label: String, value: String, valueColor: Color) {
    Column {
        Text(
            text = label,
            fontSize = 9.sp,
            color = ColorTextSecondary,
            letterSpacing = 1.sp
        )
        Text(
            text = value,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            fontFamily = FontFamily.Monospace,
            color = valueColor
        )
    }
}

@Composable
private fun CarrierBadge(carrier: String) {
    val (bg, label) = when {
        carrier.contains("Direct", ignoreCase = true) -> Pair(ColorGreen.copy(alpha = 0.2f), "Wi-Fi Direct")
        carrier.contains("BLE", ignoreCase = true)    -> Pair(Color(0xFF7C4DFF).copy(alpha = 0.3f), "BLE")
        carrier.contains("BT", ignoreCase = true)     -> Pair(Color(0xFF536DFE).copy(alpha = 0.3f), "Bluetooth")
        else -> Pair(ColorCyan.copy(alpha = 0.15f), carrier)
    }
    Box(
        modifier = Modifier
            .background(bg, shape = RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(label, fontSize = 9.sp, color = ColorCyan, fontWeight = FontWeight.SemiBold)
    }
}
