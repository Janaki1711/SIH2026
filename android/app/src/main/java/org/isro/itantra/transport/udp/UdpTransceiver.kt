package org.isro.itantra.transport.udp

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.util.Log
import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.NetworkInterface
import java.net.SocketTimeoutException
import java.nio.charset.StandardCharsets
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

class UdpTransceiver(
    private val port: Int = 8988,
    private val localCallsign: String = "NODE",
    private val context: Context? = null,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    companion object {
        private const val TAG = "iTantraNet"
    }

    private var socket: DatagramSocket? = null
    private var receiveJob: Job? = null
    private var beaconJob: Job? = null
    private var networkCallback: ConnectivityManager.NetworkCallback? = null
    private var activeWifiNetwork: Network? = null
    private val scope = CoroutineScope(dispatcher + SupervisorJob())

    /** Updated by MainActivity with current GPS string e.g. "12.9716,77.5946,8m" or "GPS_UNAVAIL" */
    @Volatile var beaconGpsPayload: String = "GPS_UNAVAIL"
    /** Updated by MainActivity with sender's selected language code e.g. "hi", "en", "kn" */
    @Volatile var beaconLang: String = "en"

    val discoveredPeers = ConcurrentHashMap<String, InetAddress>()
    private val pendingHandshakes = ConcurrentHashMap<String, CompletableDeferred<Pair<String, Long>>>()
    private val seqGenerator = AtomicInteger(100)

    var onPacketReceived: ((ByteArray) -> Unit)? = null
    var onPeerDiscovered: ((String, String) -> Unit)? = null
    var onLinkConfirmed: ((String, String, Long) -> Unit)? = null

    val txCount = AtomicInteger(0)
    val rxCount = AtomicInteger(0)

    fun isBound(): Boolean = socket?.isBound == true && socket?.isClosed == false

    fun getDiagnosticInfo(): Map<String, String> {
        val info = mutableMapOf<String, String>()
        info["callsign"] = localCallsign
        info["port"] = port.toString()
        info["bound"] = (socket?.isBound == true).toString()
        info["closed"] = (socket?.isClosed == true).toString()
        info["localPort"] = (socket?.localPort ?: -1).toString()
        info["localIps"] = getLocalIpList().joinToString(", ")
        info["interfaces"] = getActiveInterfacesSummary().joinToString(" | ")
        info["txCount"] = txCount.get().toString()
        info["rxCount"] = rxCount.get().toString()
        info["discoveredPeers"] = discoveredPeers.keys.joinToString(", ")
        info["wifiNetwork"] = (activeWifiNetwork != null).toString()
        return info
    }

    fun getLocalIpList(): List<String> {
        val wifiIps = mutableListOf<String>()
        val otherIps = mutableListOf<String>()
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                val isWifi = iface.name.startsWith("wlan", ignoreCase = true) ||
                             iface.name.startsWith("ap", ignoreCase = true) ||
                             iface.name.startsWith("softap", ignoreCase = true) ||
                             iface.name.startsWith("p2p", ignoreCase = true) ||
                             iface.name.startsWith("eth", ignoreCase = true)
                for (addr in iface.inetAddresses) {
                    if (addr is Inet4Address && !addr.isLoopbackAddress) {
                        addr.hostAddress?.let { ip ->
                            if (isWifi) wifiIps.add(ip) else otherIps.add(ip)
                        }
                    }
                }
            }
        } catch (e: Throwable) {
            Log.w(TAG, "Error enumerating local IPs: ${e.message}")
        }
        return wifiIps + otherIps
    }

    fun getActiveInterfacesSummary(): List<String> {
        val summaries = mutableListOf<String>()
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                val ips = iface.inetAddresses.toList().filterIsInstance<Inet4Address>().map { it.hostAddress }
                summaries.add("${iface.name}: $ips")
            }
        } catch (e: Throwable) {}
        return summaries
    }

    private fun registerNetworkCallbackOnly() {
        if (context == null) return
        try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager ?: return
            val request = NetworkRequest.Builder()
                .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
                .removeCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
                .build()
            networkCallback = object : ConnectivityManager.NetworkCallback() {
                override fun onAvailable(network: Network) {
                    activeWifiNetwork = network
                    Log.i(TAG, "NET_INTERFACE Wi-Fi network available: $network")
                }
                override fun onLost(network: Network) {
                    if (activeWifiNetwork == network) activeWifiNetwork = null
                }
            }
            cm.registerNetworkCallback(request, networkCallback!!)
        } catch (e: Throwable) {
            Log.w(TAG, "NetworkCallback register notice: ${e.message}")
        }
    }

    private fun bindToWifiNetworkIfAvailable() {
        // Legacy — replaced by registerNetworkCallbackOnly() + no bindProcessToNetwork
        registerNetworkCallbackOnly()
    }

    fun start() {
        if (socket != null && !socket!!.isClosed) {
            Log.i(TAG, "UDP_RECEIVER_READY already running on port $port")
            return
        }

        try {
            // Unbind process from any previously bound network so we get the default routing table
            if (context != null) {
                try {
                    val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
                    cm?.bindProcessToNetwork(null)
                } catch (e: Throwable) {}
            }

            // Bind socket to all interfaces on port 8988
            socket = DatagramSocket(null).apply {
                reuseAddress = true
                broadcast = true
                soTimeout = 1000
                bind(InetSocketAddress(8988))
            }

            Log.i(TAG, "UDP_BIND local=0.0.0.0:$port bound=${socket?.isBound}")
            Log.i(TAG, "UDP_RECEIVER_READY port=$port")
            Log.i(TAG, "NET_INTERFACE active interfaces: ${getActiveInterfacesSummary().joinToString(" | ")}")

            // Register network callback only — do NOT call bindProcessToNetwork or bindSocket
            // as both interfere with the socket's routing after it's already bound
            registerNetworkCallbackOnly()
        } catch (e: Throwable) {
            Log.e(TAG, "UDP_ERROR failed to bind UDP socket on port $port: ${e.message}", e)
            return
        }

        // Packet Receiver Loop
        receiveJob = scope.launch {
            val buffer = ByteArray(2048)
            Log.i(TAG, "UDP_RECEIVER_READY loop started on port $port")
            while (isActive) {
                try {
                    val s = socket ?: break
                    val packet = DatagramPacket(buffer, buffer.size)
                    s.receive(packet)
                    if (packet.length > 0) {
                        rxCount.incrementAndGet()
                        val data = packet.data.copyOfRange(0, packet.length)
                        val senderHost = packet.address.hostAddress ?: ""
                        val text = try { String(data, StandardCharsets.UTF_8) } catch (e: Throwable) { "" }

                        Log.i(TAG, "UDP_RX src=$senderHost:${packet.port} bytes=${packet.length} data=${text.take(40)}")

                        when {
                            // 1. 3-Way Handshake: HELLO
                            text.startsWith("ITANTRA_HELLO:") -> {
                                val parts = text.split(":")
                                val peerCallsign = if (parts.size > 1) parts[1].trim() else "PEER"
                                val seq = if (parts.size > 2) parts[2].trim() else "0"
                                val sentTs = if (parts.size > 3) parts[3].toLongOrNull() ?: 0L else 0L

                                if (peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    onPeerDiscovered?.invoke(peerCallsign, senderHost)

                                    // Reply with HELLO_ACK directly to sender's IP and port
                                    val ackMsg = "ITANTRA_ACK:$localCallsign:$seq:$sentTs"
                                    sendRawDirect(packet.address, packet.port, ackMsg.toByteArray(StandardCharsets.UTF_8))
                                    Log.i(TAG, "HANDSHAKE [HELLO -> ACK] Replying ACK to $senderHost:${packet.port} peer=$peerCallsign seq=$seq")
                                }
                            }

                            // 2. 3-Way Handshake: HELLO_ACK
                            text.startsWith("ITANTRA_ACK:") -> {
                                val parts = text.split(":")
                                val peerCallsign = if (parts.size > 1) parts[1].trim() else "PEER"
                                val seq = if (parts.size > 2) parts[2].trim() else ""
                                val origTs = if (parts.size > 3) parts[3].toLongOrNull() ?: 0L else 0L
                                val rtt = if (origTs > 0) System.currentTimeMillis() - origTs else 0L

                                if (peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    onPeerDiscovered?.invoke(peerCallsign, senderHost)

                                    Log.i(TAG, "HANDSHAKE [ACK -> CONFIRM] ACK received from $senderHost:${packet.port} peer=$peerCallsign rtt=${rtt}ms seq=$seq")

                                    // Complete pending handshake deferred
                                    pendingHandshakes[senderHost]?.complete(Pair(peerCallsign, rtt))
                                    pendingHandshakes[peerCallsign]?.complete(Pair(peerCallsign, rtt))
                                    if (seq.isNotEmpty()) {
                                        pendingHandshakes[seq]?.complete(Pair(peerCallsign, rtt))
                                    }

                                    // Send LINK_CONFIRM to finalize 3-way handshake on other side
                                    val confirmMsg = "ITANTRA_LINK_CONFIRM:$localCallsign:$seq"
                                    sendRawDirect(packet.address, packet.port, confirmMsg.toByteArray(StandardCharsets.UTF_8))
                                    Log.i(TAG, "HANDSHAKE LINK_CONFIRM sent to $senderHost:${packet.port}")
                                }
                            }

                            // 3. 3-Way Handshake: LINK_CONFIRM
                            text.startsWith("ITANTRA_LINK_CONFIRM:") -> {
                                val parts = text.split(":")
                                val peerCallsign = if (parts.size > 1) parts[1].trim() else "PEER"
                                if (peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    onPeerDiscovered?.invoke(peerCallsign, senderHost)
                                    onLinkConfirmed?.invoke(peerCallsign, senderHost, 0L)
                                    Log.i(TAG, "HANDSHAKE [LINK_CONFIRM -> CONNECTED] Established link with $peerCallsign at $senderHost")
                                }
                            }

                            // 4. Discovery Beacons: BCN
                            // Format: ITANTRA_BCN:{nodeId}:{lang}:{lat,lon,acc | GPS_UNAVAIL}:{ts}
                            text.startsWith("ITANTRA_BCN:") -> {
                                val parts = text.removePrefix("ITANTRA_BCN:").split(":")
                                val peerCallsign = parts.getOrElse(0) { "" }.trim()
                                val peerLang = parts.getOrElse(1) { "en" }.trim()
                                // GPS may contain comma: "12.97,77.59,8m" — take up to ts (last part)
                                val peerGps = if (parts.size > 3) parts.dropLast(1).drop(2).joinToString(":") else "GPS_UNAVAIL"
                                if (peerCallsign.isNotEmpty() && peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    // Pass lang+gps as extended info in the ip field (format: "ip|lang|gps")
                                    onPeerDiscovered?.invoke(peerCallsign, "$senderHost|$peerLang|$peerGps")
                                    val ackMsg = "ITANTRA_ACK:$localCallsign:BCN:${System.currentTimeMillis()}"
                                    sendRawDirect(packet.address, packet.port, ackMsg.toByteArray(StandardCharsets.UTF_8))
                                }
                            }

                            // 5. Legacy PING / PONG
                            text.startsWith("ITANTRA_PING:") -> {
                                val peerCallsign = text.substringAfter("ITANTRA_PING:").substringBefore(":").trim()
                                if (peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    onPeerDiscovered?.invoke(peerCallsign, senderHost)
                                    val pongMsg = "ITANTRA_PONG:$localCallsign:${System.currentTimeMillis()}"
                                    sendRawDirect(packet.address, packet.port, pongMsg.toByteArray(StandardCharsets.UTF_8))
                                }
                            }
                            text.startsWith("ITANTRA_PONG:") -> {
                                val peerCallsign = text.substringAfter("ITANTRA_PONG:").substringBefore(":").trim()
                                if (peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                    discoveredPeers[peerCallsign] = packet.address
                                    if (senderHost.isNotEmpty()) discoveredPeers["PEER_$senderHost"] = packet.address
                                    onPeerDiscovered?.invoke(peerCallsign, senderHost)
                                    pendingHandshakes[senderHost]?.complete(Pair(peerCallsign, 10L))
                                    pendingHandshakes[peerCallsign]?.complete(Pair(peerCallsign, 10L))
                                }
                            }

                            // 6. Production Voice / Tactical / M3 Payload
                            else -> {
                                // FIX 1: BIDIRECTIONAL - skip packets we sent ourselves (self-echo from broadcast)
                                if (isLocalAddress(packet.address)) {
                                    Log.d(TAG, "DATA_PAYLOAD_RX ignoring self-echo from $senderHost")
                                } else {
                                    if (senderHost.isNotEmpty()) {
                                        discoveredPeers["NODE_${senderHost.replace('.', '_')}"] = packet.address
                                        onPeerDiscovered?.invoke("PEER", senderHost)
                                    }
                                    Log.i(TAG, "DATA_PAYLOAD_RX src=$senderHost:${packet.port} bytes=${packet.length}")
                                    try {
                                        onPacketReceived?.invoke(data)
                                    } catch (t: Throwable) {
                                        Log.e(TAG, "UDP_ERROR handling incoming packet: ${t.message}", t)
                                    }
                                }
                            }
                        }
                    }
                } catch (e: SocketTimeoutException) {
                    // Normal timeout
                } catch (e: Exception) {
                    if (!isActive) break
                    Log.w(TAG, "UDP_ERROR receive exception: ${e.message}")
                }
            }
            Log.i(TAG, "UDP_RECEIVER loop exited.")
        }

        // Periodic Peer Discovery Beacon (every 3s)
        beaconJob = scope.launch {
            while (isActive) {
                try {
                    // Beacon format: ITANTRA_BCN:{nodeId}:{lang}:{lat}:{lon}:{ts}
                    // GPS fields are populated by MainActivity via beaconGps/beaconLang vars
                    val gps = beaconGpsPayload    // "lat,lon" or "GPS_UNAVAIL"
                    val lang = beaconLang         // e.g. "hi", "en", "kn"
                    val bcnMsg = "ITANTRA_BCN:$localCallsign:$lang:$gps:${System.currentTimeMillis()}".toByteArray(StandardCharsets.UTF_8)
                    sendBroadcastDatagram(bcnMsg)
                } catch (e: Throwable) {}
                delay(15000)  // 15s — enough for discovery, reduces UI flicker from rapid callbacks
            }
        }
    }

    private fun isLocalAddress(addr: InetAddress): Boolean {
        if (addr.isLoopbackAddress) return true
        val host = addr.hostAddress ?: return false
        val localList = getLocalIpList()
        return localList.contains(host)
    }

    fun sendRawDirect(target: InetAddress, targetPort: Int = port, data: ByteArray) {
        try {
            val s = socket ?: return
            if (s.isClosed) return
            val packet = DatagramPacket(data, data.size, target, targetPort)
            s.send(packet)
            txCount.incrementAndGet()
            Log.i(TAG, "UDP_TX dst=$target:$targetPort bytes=${data.size}")
        } catch (e: Throwable) {
            Log.w(TAG, "UDP_ERROR sendRawDirect failed to $target:$targetPort: ${e.message}")
        }
    }

    fun addPeerIp(ipStr: String) {
        scope.launch {
            try {
                val addr = InetAddress.getByName(ipStr.trim())
                discoveredPeers["PEER_${ipStr.trim()}"] = addr
                val seq = seqGenerator.incrementAndGet().toString()
                val helloMsg = "ITANTRA_HELLO:$localCallsign:$seq:${System.currentTimeMillis()}".toByteArray(StandardCharsets.UTF_8)
                sendRawDirect(addr, port, helloMsg)
                Log.i(TAG, "HANDSHAKE [HELLO] sent dst=$ipStr:$port seq=$seq (manual peer)")
            } catch (e: Throwable) {
                Log.w(TAG, "UDP_ERROR addPeerIp failed for $ipStr: ${e.message}")
            }
        }
    }

    fun pingPeer(
        targetIp: String,
        timeoutMs: Long = 1200L,
        maxAttempts: Int = 3,
        onResult: (success: Boolean, peerCallsign: String, rttMs: Long, message: String) -> Unit
    ) {
        scope.launch {
            val cleanIp = targetIp.trim()
            val targetAddr = try {
                InetAddress.getByName(cleanIp)
            } catch (e: Throwable) {
                onResult(false, "", 0L, "Invalid IP address: $cleanIp")
                return@launch
            }

            var respondedCallsign: String? = null
            var measuredRtt = 0L

            for (attempt in 1..maxAttempts) {
                val seq = "${System.currentTimeMillis()}_${seqGenerator.incrementAndGet()}"
                val deferred = CompletableDeferred<Pair<String, Long>>()
                pendingHandshakes[cleanIp] = deferred
                pendingHandshakes[seq] = deferred

                val helloMsg = "ITANTRA_HELLO:$localCallsign:$seq:${System.currentTimeMillis()}".toByteArray(StandardCharsets.UTF_8)
                
                // Direct unicast to target
                sendRawDirect(targetAddr, port, helloMsg)
                Log.i(TAG, "HANDSHAKE [HELLO] dst=$cleanIp:$port attempt=$attempt/$maxAttempts seq=$seq")

                // If attempt >= 2, also send broadcast fallback probes on local subnets
                if (attempt >= 2) {
                    try {
                        sendBroadcastDatagram(helloMsg)
                        Log.i(TAG, "HANDSHAKE [HELLO_BROADCAST_FALLBACK] sent across subnets seq=$seq")
                    } catch (e: Throwable) {}
                }

                try {
                    withTimeout(timeoutMs) {
                        val result = deferred.await()
                        respondedCallsign = result.first
                        measuredRtt = result.second
                    }
                    if (respondedCallsign != null) {
                        break
                    }
                } catch (e: TimeoutCancellationException) {
                    Log.w(TAG, "HANDSHAKE Timeout attempt $attempt/$maxAttempts for $cleanIp")
                } finally {
                    pendingHandshakes.remove(cleanIp)
                    pendingHandshakes.remove(seq)
                }
            }

            if (respondedCallsign != null) {
                discoveredPeers[respondedCallsign!!] = targetAddr
                discoveredPeers["PEER_$cleanIp"] = targetAddr
                onPeerDiscovered?.invoke(respondedCallsign!!, cleanIp)
                onLinkConfirmed?.invoke(respondedCallsign!!, cleanIp, measuredRtt)
                Log.i(TAG, "HANDSHAKE LINK_STATE CONNECTED with $respondedCallsign at $cleanIp:$port (${measuredRtt}ms)")
                onResult(true, respondedCallsign!!, measuredRtt, "Connected to $respondedCallsign at $cleanIp:$port (${measuredRtt}ms)")
            } else {
                Log.w(TAG, "HANDSHAKE LINK_STATE FAILED for $cleanIp:$port (Sent $maxAttempts / Recv 0)")
                onResult(false, "", 0L, "No response from $cleanIp:$port after $maxAttempts attempts (Sent $maxAttempts / Recv 0)")
            }
        }
    }

    private fun sendBroadcastDatagram(data: ByteArray) {
        val targets = mutableSetOf<InetAddress>()
        targets.addAll(discoveredPeers.values)

        // 1. Limited broadcast
        try { targets.add(InetAddress.getByName("255.255.255.255")) } catch (e: Throwable) {}

        // 2. Subnet broadcast on all active network interfaces
        val localIps = getLocalIpList()
        try {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (iface.isLoopback || !iface.isUp) continue
                for (ifaceAddr in iface.interfaceAddresses) {
                    ifaceAddr.broadcast?.let { targets.add(it) }
                }
            }
        } catch (e: Throwable) {}

        // 3. Dynamic subnet targeting based on local IP (e.g. 192.168.43.x or 10.x.x.x)
        for (localIp in localIps) {
            val lastDot = localIp.lastIndexOf('.')
            if (lastDot > 0) {
                val prefix = localIp.substring(0, lastDot + 1)
                try {
                    targets.add(InetAddress.getByName("${prefix}1"))   // Hotspot host / gateway
                    targets.add(InetAddress.getByName("${prefix}255")) // Subnet broadcast
                } catch (e: Throwable) {}

                // Zero-config sweep: if no peers discovered yet, probe first 15 client addresses
                if (discoveredPeers.isEmpty()) {
                    for (hostId in 2..15) {
                        val candidateIp = "$prefix$hostId"
                        if (candidateIp != localIp) {
                            try { targets.add(InetAddress.getByName(candidateIp)) } catch (e: Throwable) {}
                        }
                    }
                }
            }
        }

        // 4. Default hotspot fallback addresses (all known Android hotspot subnets)
        // Standard Android: 192.168.43.x, OnePlus OxygenOS: 10.0.0.x / 10.1.x.x, some ROMs: 10.42.0.x
        val hotspotFallbacks = listOf(
            "192.168.43.1", "192.168.43.255",
            "10.0.0.1", "10.0.0.255",
            "10.1.0.1", "10.1.255.255",
            "10.42.0.1", "10.42.0.255"
        )
        for (addr in hotspotFallbacks) {
            try { targets.add(InetAddress.getByName(addr)) } catch (e: Throwable) {}
        }

        for (target in targets) {
            sendRawDirect(target, port, data)
        }
    }

    fun sendPacket(data: ByteArray, targetIp: String = "255.255.255.255", targetPort: Int = port) {
        scope.launch {
            val targets = mutableSetOf<InetAddress>()

            // 0. Include registered peers
            targets.addAll(discoveredPeers.values)

            // 1. Explicit target IP
            val cleanTarget = targetIp.trim()
            if (cleanTarget.isNotEmpty()) {
                try {
                    targets.add(InetAddress.getByName(cleanTarget))
                } catch (e: Throwable) {}
            }

            // 2. Subnet broadcasts on all active network interfaces
            val localIps = getLocalIpList()
            try {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val iface = interfaces.nextElement()
                    if (iface.isLoopback || !iface.isUp) continue
                    for (ifaceAddr in iface.interfaceAddresses) {
                        ifaceAddr.broadcast?.let { targets.add(it) }
                    }
                }
            } catch (e: Throwable) {}

            // 3. Dynamic subnet targeting based on local IP
            for (localIp in localIps) {
                val lastDot = localIp.lastIndexOf('.')
                if (lastDot > 0) {
                    val prefix = localIp.substring(0, lastDot + 1)
                    try {
                        targets.add(InetAddress.getByName("${prefix}1"))
                        targets.add(InetAddress.getByName("${prefix}255"))
                    } catch (e: Throwable) {}
                }
            }

            // 4. Common Hotspot fallbacks (all known Android hotspot subnets)
            val hotspotFallbacks = listOf(
                "255.255.255.255",
                "192.168.43.1", "192.168.43.255",
                "10.0.0.1", "10.0.0.255",
                "10.1.0.1", "10.1.255.255",
                "10.42.0.1", "10.42.0.255"
            )
            for (addr in hotspotFallbacks) {
                try { targets.add(InetAddress.getByName(addr)) } catch (e: Throwable) {}
            }

            // FIX 3: BIDIRECTIONAL — always use the main bound socket, never create a new one.
            // Creating a new DatagramSocket() here uses a random ephemeral port and may use
            // the wrong network interface (e.g., cellular instead of Wi-Fi hotspot), causing
            // ENETUNREACH. The main socket is already correctly bound to 0.0.0.0:8988.
            val mainSocket = socket
            if (mainSocket == null || mainSocket.isClosed) {
                Log.w(TAG, "DATA_ERROR sendPacket — main socket not ready, dropping packet")
                return@launch
            }
            for (targetAddress in targets) {
                try {
                    val packet = DatagramPacket(data, data.size, targetAddress, targetPort)
                    mainSocket.send(packet)
                    txCount.incrementAndGet()
                    Log.i(TAG, "DATA_TX dst=$targetAddress:$targetPort bytes=${data.size}")
                } catch (e: Throwable) {
                    Log.w(TAG, "DATA_ERROR send failed to $targetAddress:$targetPort: ${e.message}")
                }
            }
        }
    }

    fun stop() {
        if (networkCallback != null && context != null) {
            try {
                val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
                cm?.unregisterNetworkCallback(networkCallback!!)
            } catch (e: Throwable) {}
            networkCallback = null
        }
        beaconJob?.cancel()
        beaconJob = null
        receiveJob?.cancel()
        receiveJob = null
        socket?.close()
        socket = null
        Log.i(TAG, "UDP_RECEIVER transceiver stopped.")
    }
}


