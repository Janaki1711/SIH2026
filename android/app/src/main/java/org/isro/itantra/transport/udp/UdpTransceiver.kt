package org.isro.itantra.transport.udp

import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException

class UdpTransceiver(
    private val port: Int = 8988,
    private val localCallsign: String = "NODE",
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    private var socket: DatagramSocket? = null
    private var receiveJob: Job? = null
    private var beaconJob: Job? = null
    private val scope = CoroutineScope(dispatcher + SupervisorJob())

    val discoveredPeers = java.util.concurrent.ConcurrentHashMap<String, InetAddress>()
    var onPacketReceived: ((ByteArray) -> Unit)? = null
    var onPeerDiscovered: ((String, String) -> Unit)? = null

    fun start() {
        if (socket != null && !socket!!.isClosed) return

        try {
            socket = DatagramSocket(null).apply {
                reuseAddress = true
                broadcast = true
                soTimeout = 1000
                bind(java.net.InetSocketAddress(port))
            }
            android.util.Log.i("UdpTransceiver", "UDP Transceiver bound to port $port with broadcast=true")
        } catch (e: Throwable) {
            android.util.Log.e("UdpTransceiver", "Failed to bind UDP socket: ${e.message}", e)
            return
        }

        // 1. Packet Receiver Loop
        receiveJob = scope.launch {
            val buffer = ByteArray(2048)
            while (isActive) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket?.receive(packet)
                    if (packet.length > 0) {
                        val data = packet.data.copyOfRange(0, packet.length)
                        val text = String(data, java.nio.charset.StandardCharsets.UTF_8)

                        // Check for discovery beacon: BCN:<callsign>
                        if (text.startsWith("ITANTRA_BCN:")) {
                            val peerCallsign = text.substringAfter("ITANTRA_BCN:").trim()
                            if (peerCallsign.isNotEmpty() && peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                discoveredPeers[peerCallsign] = packet.address
                                onPeerDiscovered?.invoke(peerCallsign, packet.address.hostAddress ?: "")
                                // Auto-reply with ACK directly to sender
                                sendRaw(packet.address, "ITANTRA_ACK:$localCallsign".toByteArray())
                            }
                        } else if (text.startsWith("ITANTRA_ACK:")) {
                            val peerCallsign = text.substringAfter("ITANTRA_ACK:").trim()
                            if (peerCallsign.isNotEmpty() && peerCallsign != localCallsign && !isLocalAddress(packet.address)) {
                                discoveredPeers[peerCallsign] = packet.address
                                onPeerDiscovered?.invoke(peerCallsign, packet.address.hostAddress ?: "")
                            }
                        } else {
                            if (!isLocalAddress(packet.address)) {
                                val remoteIp = packet.address.hostAddress ?: ""
                                if (remoteIp.isNotEmpty()) {
                                    discoveredPeers["NODE_${remoteIp.replace('.', '_')}"] = packet.address
                                    onPeerDiscovered?.invoke("PEER", remoteIp)
                                }
                            }
                            android.util.Log.i("UdpTransceiver", "Received UDP packet: ${packet.length} bytes from ${packet.address}:${packet.port}")
                            try {
                                onPacketReceived?.invoke(data)
                            } catch (t: Throwable) {
                                android.util.Log.e("UdpTransceiver", "Callback error handling packet: ${t.message}", t)
                            }
                        }
                    }
                } catch (e: SocketTimeoutException) {
                    // Normal timeout, loop to check isActive
                } catch (e: Exception) {
                    if (!isActive) break
                }
            }
        }

        // 2. Periodic Peer Discovery Beacon (every 2.5s)
        beaconJob = scope.launch {
            val bcnMsg = "ITANTRA_BCN:$localCallsign".toByteArray()
            while (isActive) {
                try {
                    sendDirect(InetAddress.getByName("255.255.255.255"), bcnMsg)
                    sendDirect(InetAddress.getByName("192.168.43.255"), bcnMsg)
                    sendDirect(InetAddress.getByName("192.168.43.1"), bcnMsg)

                    val interfaces = java.net.NetworkInterface.getNetworkInterfaces()
                    while (interfaces.hasMoreElements()) {
                        val iface = interfaces.nextElement()
                        if (iface.isLoopback || !iface.isUp) continue
                        for (ifaceAddr in iface.interfaceAddresses) {
                            ifaceAddr.broadcast?.let { sendDirect(it, bcnMsg) }
                        }
                    }

                    for (peerAddr in discoveredPeers.values) {
                        sendDirect(peerAddr, bcnMsg)
                    }
                } catch (e: Throwable) {}
                delay(2500)
            }
        }
    }

    private fun isLocalAddress(addr: InetAddress): Boolean {
        if (addr.isLoopbackAddress) return true
        try {
            val interfaces = java.net.NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                for (a in iface.inetAddresses) {
                    if (a.hostAddress == addr.hostAddress) return true
                }
            }
        } catch (e: Throwable) {}
        return false
    }

    private fun sendDirect(target: InetAddress, data: ByteArray) {
        try {
            val packet = DatagramPacket(data, data.size, target, port)
            val s = socket ?: DatagramSocket().apply { broadcast = true }
            s.send(packet)
        } catch (e: Throwable) {}
    }

    private fun sendRaw(targetAddress: InetAddress, data: ByteArray) {
        scope.launch {
            sendDirect(targetAddress, data)
        }
    }

    fun addPeerIp(ipStr: String) {
        scope.launch {
            try {
                val addr = InetAddress.getByName(ipStr.trim())
                discoveredPeers["PEER_${ipStr.trim()}"] = addr
                val bcnMsg = "ITANTRA_BCN:$localCallsign".toByteArray()
                sendRaw(addr, bcnMsg)
                android.util.Log.i("UdpTransceiver", "Added manual peer IP: $ipStr and sent beacon")
            } catch (e: Throwable) {
                android.util.Log.w("UdpTransceiver", "addPeerIp failed: ${e.message}")
            }
        }
    }

    fun stop() {
        beaconJob?.cancel()
        beaconJob = null
        receiveJob?.cancel()
        receiveJob = null
        socket?.close()
        socket = null
    }

    fun sendPacket(data: ByteArray, targetIp: String = "255.255.255.255", targetPort: Int = port) {
        scope.launch {
            val targets = mutableSetOf<InetAddress>()

            // 0. Include all registered / discovered peers
            targets.addAll(discoveredPeers.values)

            // 1. Target IP (e.g. 255.255.255.255)
            try {
                targets.add(InetAddress.getByName(targetIp))
            } catch (e: Throwable) {}

            // 2. Discover local interface broadcasts
            try {
                val interfaces = java.net.NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val iface = interfaces.nextElement()
                    if (iface.isLoopback || !iface.isUp) continue
                    for (ifaceAddr in iface.interfaceAddresses) {
                        ifaceAddr.broadcast?.let { targets.add(it) }
                    }
                }
            } catch (e: Throwable) {
                android.util.Log.w("UdpTransceiver", "Interface discovery error: ${e.message}")
            }

            // 3. Always include standard Android Hotspot gateway and broadcast
            try {
                targets.add(InetAddress.getByName("192.168.43.1"))
                targets.add(InetAddress.getByName("192.168.43.255"))
            } catch (e: Throwable) {}

            // 4. Send packet to fast target set (no blocking 254-loop)
            for (targetAddress in targets) {
                try {
                    val packet = DatagramPacket(data, data.size, targetAddress, targetPort)
                    val s = socket ?: DatagramSocket().apply { broadcast = true }
                    s.send(packet)
                    android.util.Log.d("UdpTransceiver", "Sent UDP packet (${data.size}B) to $targetAddress:$targetPort")
                } catch (e: Throwable) {
                    android.util.Log.w("UdpTransceiver", "Send failed to $targetAddress:$targetPort: ${e.message}")
                }
            }
        }
    }
}
