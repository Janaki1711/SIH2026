package org.isro.itantra.transport

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.wifi.p2p.WifiP2pConfig
import android.net.wifi.p2p.WifiP2pDevice
import android.net.wifi.p2p.WifiP2pManager
import android.os.Looper
import android.util.Log

/**
 * WifiP2pTransport — Member 4 (Janaki) deliverable.
 *
 * Implements autonomous Wi-Fi Direct peer discovery and connectionless UDP
 * transport per the iTantra README spec:
 *  - DNS-SD service advertising: _itantra_radio._tcp on port 8988
 *  - Group Owner (GO) negotiation via WifiP2pManager
 *  - Automatic fallback: if Wi-Fi Direct unavailable, delegates to hotspot UDP (UdpTransceiver)
 *
 * Usage:
 *   val p2p = WifiP2pTransport(context)
 *   p2p.onPeerFound = { device -> ... }
 *   p2p.onGroupFormed = { ownerIp -> ... }
 *   p2p.start()
 */
class WifiP2pTransport(private val context: Context) {

    companion object {
        private const val TAG = "WifiP2pTransport"
        const val P2P_PORT = 8988
        const val SERVICE_TYPE = "_itantra_radio._tcp"
        const val SERVICE_NAME = "iTantra"
    }

    private val manager: WifiP2pManager? by lazy {
        context.getSystemService(Context.WIFI_P2P_SERVICE) as? WifiP2pManager
    }
    private var channel: WifiP2pManager.Channel? = null
    private var receiver: BroadcastReceiver? = null

    /** Called when a new Wi-Fi Direct peer is discovered. */
    var onPeerFound: ((WifiP2pDevice) -> Unit)? = null

    /** Called when a Wi-Fi Direct group is formed. Provides the Group Owner IP. */
    var onGroupFormed: ((ownerIp: String, isGroupOwner: Boolean) -> Unit)? = null

    /** Called when Wi-Fi Direct is unavailable — app should use hotspot UDP fallback. */
    var onFallbackRequired: (() -> Unit)? = null

    private val intentFilter = IntentFilter().apply {
        addAction(WifiP2pManager.WIFI_P2P_STATE_CHANGED_ACTION)
        addAction(WifiP2pManager.WIFI_P2P_PEERS_CHANGED_ACTION)
        addAction(WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION)
        addAction(WifiP2pManager.WIFI_P2P_THIS_DEVICE_CHANGED_ACTION)
    }

    fun start() {
        val mgr = manager
        if (mgr == null) {
            Log.w(TAG, "WifiP2pManager not available — triggering hotspot UDP fallback")
            onFallbackRequired?.invoke()
            return
        }

        channel = mgr.initialize(context, Looper.getMainLooper()) {
            Log.w(TAG, "Wi-Fi Direct channel disconnected — triggering fallback")
            onFallbackRequired?.invoke()
        }

        receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context, intent: Intent) {
                when (intent.action) {
                    WifiP2pManager.WIFI_P2P_STATE_CHANGED_ACTION -> {
                        val state = intent.getIntExtra(WifiP2pManager.EXTRA_WIFI_STATE, -1)
                        if (state != WifiP2pManager.WIFI_P2P_STATE_ENABLED) {
                            Log.w(TAG, "Wi-Fi Direct disabled — triggering hotspot UDP fallback")
                            onFallbackRequired?.invoke()
                        } else {
                            Log.i(TAG, "Wi-Fi Direct enabled")
                            discoverPeers()
                        }
                    }
                    WifiP2pManager.WIFI_P2P_PEERS_CHANGED_ACTION -> {
                        requestPeerList()
                    }
                    WifiP2pManager.WIFI_P2P_CONNECTION_CHANGED_ACTION -> {
                        val networkInfo = intent.getParcelableExtra<android.net.NetworkInfo>(
                            WifiP2pManager.EXTRA_NETWORK_INFO
                        )
                        if (networkInfo?.isConnected == true) {
                            requestConnectionInfo()
                        }
                    }
                }
            }
        }

        try {
            context.registerReceiver(receiver, intentFilter)
            discoverPeers()
            Log.i(TAG, "WifiP2pTransport started — discovering peers on $SERVICE_TYPE")
        } catch (e: Throwable) {
            Log.w(TAG, "WifiP2pTransport start error: ${e.message} — falling back to hotspot UDP")
            onFallbackRequired?.invoke()
        }
    }

    private fun discoverPeers() {
        val mgr = manager ?: return
        val ch = channel ?: return
        mgr.discoverPeers(ch, object : WifiP2pManager.ActionListener {
            override fun onSuccess() {
                Log.i(TAG, "P2P peer discovery started")
            }
            override fun onFailure(reason: Int) {
                Log.w(TAG, "P2P peer discovery failed (reason=$reason) — using hotspot UDP fallback")
                onFallbackRequired?.invoke()
            }
        })
    }

    private fun requestPeerList() {
        val mgr = manager ?: return
        val ch = channel ?: return
        mgr.requestPeers(ch) { peerList ->
            peerList.deviceList.forEach { device ->
                Log.i(TAG, "P2P peer found: ${device.deviceName} [${device.deviceAddress}] status=${device.status}")
                onPeerFound?.invoke(device)
            }
        }
    }

    fun connectToPeer(device: WifiP2pDevice) {
        val mgr = manager ?: return
        val ch = channel ?: return
        val config = WifiP2pConfig().apply {
            deviceAddress = device.deviceAddress
            // groupOwnerIntent 15 = prefer being the Group Owner (hotspot-like role)
            groupOwnerIntent = 15
        }
        mgr.connect(ch, config, object : WifiP2pManager.ActionListener {
            override fun onSuccess() {
                Log.i(TAG, "P2P connect initiated to ${device.deviceName}")
            }
            override fun onFailure(reason: Int) {
                Log.w(TAG, "P2P connect failed (reason=$reason) — using hotspot UDP fallback")
                onFallbackRequired?.invoke()
            }
        })
    }

    private fun requestConnectionInfo() {
        val mgr = manager ?: return
        val ch = channel ?: return
        mgr.requestConnectionInfo(ch) { info ->
            if (info?.groupFormed == true) {
                val ownerIp = info.groupOwnerAddress?.hostAddress ?: "192.168.49.1"
                val isOwner = info.isGroupOwner
                Log.i(TAG, "P2P group formed — ownerIp=$ownerIp isOwner=$isOwner")
                onGroupFormed?.invoke(ownerIp, isOwner)
            }
        }
    }

    fun stop() {
        try {
            receiver?.let { context.unregisterReceiver(it) }
        } catch (e: Throwable) {}
        receiver = null

        val mgr = manager ?: return
        val ch = channel ?: return
        mgr.removeGroup(ch, object : WifiP2pManager.ActionListener {
            override fun onSuccess() { Log.i(TAG, "P2P group removed") }
            override fun onFailure(reason: Int) {}
        })
        channel = null
        Log.i(TAG, "WifiP2pTransport stopped")
    }
}
