package org.isro.itantra.transport.udp

import kotlinx.coroutines.*
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException

class UdpTransceiver(
    private val port: Int = 8988,
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO
) {
    private var socket: DatagramSocket? = null
    private var receiveJob: Job? = null
    private val scope = CoroutineScope(dispatcher + SupervisorJob())
    
    var onPacketReceived: ((ByteArray) -> Unit)? = null

    fun start() {
        if (socket != null && !socket!!.isClosed) return
        
        socket = DatagramSocket(port)
        socket?.soTimeout = 1000
        socket?.broadcast = true
        
        receiveJob = scope.launch {
            val buffer = ByteArray(2048)
            while (isActive) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket?.receive(packet)
                    if (packet.length > 0) {
                        val data = packet.data.copyOfRange(0, packet.length)
                        onPacketReceived?.invoke(data)
                    }
                } catch (e: SocketTimeoutException) {
                    // Normal, just loops to check isActive
                } catch (e: Exception) {
                    if (!isActive) break
                }
            }
        }
    }

    fun stop() {
        receiveJob?.cancel()
        receiveJob = null
        socket?.close()
        socket = null
    }

    fun sendPacket(data: ByteArray, targetIp: String = "255.255.255.255", targetPort: Int = port) {
        scope.launch {
            try {
                val address = InetAddress.getByName(targetIp)
                val packet = DatagramPacket(data, data.size, address, targetPort)
                val s = socket ?: DatagramSocket().apply { broadcast = true }
                s.send(packet)
                if (socket == null) s.close()
            } catch (e: Exception) {
                // Ignore send errors in transceiver for now
            }
        }
    }
}
