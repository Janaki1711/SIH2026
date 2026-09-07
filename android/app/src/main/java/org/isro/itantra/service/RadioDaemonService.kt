package org.isro.itantra.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

class RadioDaemonService : Service() {

    companion object {
        const val ACTION_START = "org.isro.itantra.START_RADIO_DAEMON"
        const val ACTION_STOP = "org.isro.itantra.STOP_RADIO_DAEMON"
        private const val CHANNEL_ID = "radio_daemon_channel"
        private const val NOTIFICATION_ID = 1
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startDaemon()
            ACTION_STOP -> stopDaemon()
            else -> startDaemon() // Default fallback
        }
        return START_STICKY
    }

    private fun startDaemon() {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("iTantra Radio Daemon")
            .setContentText("Listening for PTT events...")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(
                NOTIFICATION_ID, 
                notification, 
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    private fun stopDaemon() {
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Radio Daemon Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Background service for iTantra Radio"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }
}

