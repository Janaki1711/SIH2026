package org.isro.itantra.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.Looper
import android.util.Log
import androidx.core.content.ContextCompat
import kotlin.math.*

/**
 * OfflineGpsFix — strictly GPS_PROVIDER (no network, no cell tower).
 * Provides:
 *   - Periodic satellite fixes cached in [lastFix]
 *   - Haversine distance + bearing to any target coordinate
 *   - SensorManager compass that rotates a bearing relative to phone heading
 *
 * Usage:
 *   val gps = OfflineGpsFix(context)
 *   gps.start { fix -> beaconLat = fix.lat; beaconLon = fix.lon }
 *   gps.stop()
 */
class OfflineGpsFix(private val context: Context) {

    companion object {
        private const val TAG = "OfflineGpsFix"
        private const val MIN_INTERVAL_MS = 20_000L   // request every 20s to save battery
        private const val MIN_DIST_METERS = 5f         // minimum movement before callback

        const val GPS_UNAVAIL = "GPS_UNAVAIL"

        // ── Haversine formula ────────────────────────────────────────────────
        /**
         * Returns Pair(distanceMeters, bearingDegrees 0–360).
         * Pure Kotlin, no Maps dependency.
         */
        fun calculateDistanceAndBearing(
            myLat: Double, myLon: Double,
            targetLat: Double, targetLon: Double
        ): Pair<Double, Double> {
            val R = 6_371_000.0  // Earth radius in metres
            val φ1 = Math.toRadians(myLat)
            val φ2 = Math.toRadians(targetLat)
            val Δφ = Math.toRadians(targetLat - myLat)
            val Δλ = Math.toRadians(targetLon - myLon)

            val a = sin(Δφ / 2).pow(2) + cos(φ1) * cos(φ2) * sin(Δλ / 2).pow(2)
            val c = 2 * atan2(sqrt(a), sqrt(1 - a))
            val distance = R * c

            val y = sin(Δλ) * cos(φ2)
            val x = cos(φ1) * sin(φ2) - sin(φ1) * cos(φ2) * cos(Δλ)
            val bearing = (Math.toDegrees(atan2(y, x)) + 360) % 360

            return Pair(distance, bearing)
        }
    }

    data class GpsFix(
        val lat: Double,
        val lon: Double,
        val accuracyM: Float,      // metres
        val timestampMs: Long = System.currentTimeMillis()
    ) {
        val ageSeconds: Long get() = (System.currentTimeMillis() - timestampMs) / 1000

        /** Compact string for beacon: "12.9716,77.5946,8m,5s" */
        fun toBeaconString(): String = "%.6f,%.6f,%.0fm".format(lat, lon, accuracyM)
    }

    @Volatile var lastFix: GpsFix? = null
        private set

    private var locationManager: LocationManager? = null
    private var onFixCallback: ((GpsFix) -> Unit)? = null

    private val locationListener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            if (location.provider != LocationManager.GPS_PROVIDER) return  // strict GPS only
            val fix = GpsFix(
                lat = location.latitude,
                lon = location.longitude,
                accuracyM = location.accuracy
            )
            lastFix = fix
            Log.i(TAG, "GPS fix: ${fix.lat},${fix.lon} acc=${fix.accuracyM}m")
            onFixCallback?.invoke(fix)
        }

        @Deprecated("Deprecated in Java")
        override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
        override fun onProviderEnabled(provider: String) {}
        override fun onProviderDisabled(provider: String) {
            Log.w(TAG, "GPS provider disabled: $provider")
        }
    }

    /**
     * Start requesting GPS fixes.
     * @param onFix called on the main thread when a new fix arrives.
     */
    fun start(onFix: (GpsFix) -> Unit) {
        onFixCallback = onFix
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            Log.w(TAG, "ACCESS_FINE_LOCATION not granted — GPS unavailable")
            return
        }
        try {
            locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            val mgr = locationManager ?: return

            // Use GPS_PROVIDER strictly (not network, not fused)
            if (!mgr.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                Log.w(TAG, "GPS provider not enabled on device")
                return
            }

            mgr.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                MIN_INTERVAL_MS,
                MIN_DIST_METERS,
                locationListener,
                Looper.getMainLooper()
            )

            // Return last known fix immediately if available (avoids wait on cold start)
            mgr.getLastKnownLocation(LocationManager.GPS_PROVIDER)?.let { loc ->
                val fix = GpsFix(loc.latitude, loc.longitude, loc.accuracy)
                lastFix = fix
                onFix(fix)
                Log.i(TAG, "Last known GPS: ${fix.lat},${fix.lon}")
            }

            Log.i(TAG, "GPS location updates started (GPS_PROVIDER, interval=${MIN_INTERVAL_MS}ms)")
        } catch (e: Throwable) {
            Log.e(TAG, "GPS start error: ${e.message}")
        }
    }

    fun stop() {
        try {
            locationManager?.removeUpdates(locationListener)
        } catch (e: Throwable) {}
        locationManager = null
        onFixCallback = null
        Log.i(TAG, "GPS stopped")
    }

    /** Current lat,lon as a compact beacon string, or GPS_UNAVAIL */
    fun beaconGpsString(): String = lastFix?.toBeaconString() ?: GPS_UNAVAIL
}

/**
 * TacticalCompass — uses TYPE_ROTATION_VECTOR sensor to continuously
 * rotate a bearing so it always points at a target GPS coordinate,
 * regardless of which way the user is facing.
 *
 * Usage:
 *   val compass = TacticalCompass(context, targetLat, targetLon)
 *   compass.start { arrowRotationDeg -> compassArrowView.rotation = arrowRotationDeg }
 *   compass.stop()
 */
class TacticalCompass(
    private val context: Context,
    private var targetLat: Double = 0.0,
    private var targetLon: Double = 0.0
) : SensorEventListener {

    private var sensorManager: SensorManager? = null
    private var rotationSensor: Sensor? = null
    private var onBearing: ((Float) -> Unit)? = null
    private var myLat = 0.0
    private var myLon = 0.0
    private val rotMatrix = FloatArray(9)
    private val orientation = FloatArray(3)

    fun updateMyLocation(lat: Double, lon: Double) { myLat = lat; myLon = lon }
    fun updateTarget(lat: Double, lon: Double) { targetLat = lat; targetLon = lon }

    fun start(onArrowRotation: (Float) -> Unit) {
        onBearing = onArrowRotation
        sensorManager = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager
        rotationSensor = sensorManager?.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)
            ?: sensorManager?.getDefaultSensor(Sensor.TYPE_ORIENTATION)
        if (rotationSensor == null) {
            android.util.Log.w("TacticalCompass", "No rotation sensor available")
            return
        }
        sensorManager?.registerListener(this, rotationSensor, SensorManager.SENSOR_DELAY_UI)
    }

    fun stop() {
        sensorManager?.unregisterListener(this)
        sensorManager = null
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (event.sensor.type == Sensor.TYPE_ROTATION_VECTOR) {
            SensorManager.getRotationMatrixFromVector(rotMatrix, event.values)
            SensorManager.getOrientation(rotMatrix, orientation)
            val azimuthDeg = Math.toDegrees(orientation[0].toDouble()).toFloat()
            val phoneFacing = (azimuthDeg + 360) % 360

            if (myLat != 0.0 && targetLat != 0.0) {
                val (_, bearing) = OfflineGpsFix.calculateDistanceAndBearing(
                    myLat, myLon, targetLat, targetLon
                )
                // Arrow rotation = target bearing minus phone facing direction
                val arrowRotation = ((bearing - phoneFacing + 360) % 360).toFloat()
                onBearing?.invoke(arrowRotation)
            }
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
}
