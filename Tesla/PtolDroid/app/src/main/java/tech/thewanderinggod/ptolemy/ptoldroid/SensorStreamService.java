package tech.thewanderinggod.ptolemy.ptoldroid;

import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.BatteryManager;
import android.os.Bundle;
import android.os.IBinder;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * SensorStreamService — Background service that streams all available
 * device sensors to a Ptolemy/Tesla SensorStream receiver over UDP.
 *
 * Packet format: JSON, max ~1400 bytes (MTU safe)
 * {
 *   "t":  1713600000.123,
 *   "id": "ptoldroid_<device_id>",
 *   "s":  { sensor_key: value, ... }
 * }
 *
 * Start from MainActivity:
 *   Intent i = new Intent(this, SensorStreamService.class);
 *   i.putExtra("host", "192.168.1.100");
 *   i.putExtra("port", 5556);
 *   startService(i);
 *
 * Sensor keys match Tesla/SensorStream.py dispatch table:
 *   acc, gyr, mag, grv, lin, rot, bar, lux, prx, tmp, hum,
 *   gps, step, mic, bat
 */
public class SensorStreamService extends Service
        implements SensorEventListener, LocationListener {

    private static final String TAG     = "PtolSensorStream";
    private static final String DEV_ID  = "ptoldroid_01";

    // Sensor sample rates
    private static final int MOTION_RATE_US = 50000;   // 20 Hz
    private static final int ENV_RATE_US    = 200000;  // 5 Hz

    private SensorManager   mSensorManager;
    private LocationManager mLocationManager;
    private DatagramSocket  mSocket;
    private InetAddress     mHost;
    private int             mPort;

    // Sensor cache — keyed by sensor key string
    private final Map<String, float[]> mSensorCache = new HashMap<>();

    // GPS cache
    private double mLat = 0, mLon = 0, mAlt = 0;
    private float  mBearing = 0, mSpeed = 0, mAccuracy = 0;

    // Mic
    private AudioRecord mAudioRecord;
    private AtomicBoolean mMicRunning = new AtomicBoolean(false);
    private float mMicRms = 0f;

    // Send thread
    private Thread mSendThread;
    private AtomicBoolean mRunning = new AtomicBoolean(false);

    // Send rate (packets/sec for the main loop)
    private static final long SEND_INTERVAL_MS = 50;   // 20 Hz main loop

    // ── Service lifecycle ────────────────────────────────────────────────────

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String host = intent.getStringExtra("host");
        mPort = intent.getIntExtra("port", 5556);

        try {
            mHost   = InetAddress.getByName(host);
            mSocket = new DatagramSocket();
            mSocket.setSoTimeout(1000);
        } catch (Exception e) {
            Log.e(TAG, "Socket init failed: " + e.getMessage());
            stopSelf();
            return START_NOT_STICKY;
        }

        registerSensors();
        startGPS();
        startMic();
        startSendLoop();

        Log.i(TAG, "SensorStreamService started → " + host + ":" + mPort);
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        mRunning.set(false);
        mMicRunning.set(false);
        unregisterSensors();
        stopGPS();
        if (mSocket != null && !mSocket.isClosed()) mSocket.close();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    // ── Sensor registration ───────────────────────────────────────────────────

    private void registerSensors() {
        mSensorManager = (SensorManager) getSystemService(Context.SENSOR_SERVICE);
        if (mSensorManager == null) return;

        int[][] sensors = {
            // { sensor_type, rate_us }
            { Sensor.TYPE_ACCELEROMETER,           MOTION_RATE_US },
            { Sensor.TYPE_GYROSCOPE,               MOTION_RATE_US },
            { Sensor.TYPE_MAGNETIC_FIELD,          MOTION_RATE_US },
            { Sensor.TYPE_GRAVITY,                 MOTION_RATE_US },
            { Sensor.TYPE_LINEAR_ACCELERATION,     MOTION_RATE_US },
            { Sensor.TYPE_ROTATION_VECTOR,         MOTION_RATE_US },
            { Sensor.TYPE_PRESSURE,                ENV_RATE_US    },
            { Sensor.TYPE_LIGHT,                   ENV_RATE_US    },
            { Sensor.TYPE_PROXIMITY,               ENV_RATE_US    },
            { Sensor.TYPE_AMBIENT_TEMPERATURE,     ENV_RATE_US    },
            { Sensor.TYPE_RELATIVE_HUMIDITY,       ENV_RATE_US    },
            { Sensor.TYPE_STEP_COUNTER,            ENV_RATE_US    },
        };

        for (int[] s : sensors) {
            Sensor sensor = mSensorManager.getDefaultSensor(s[0]);
            if (sensor != null) {
                mSensorManager.registerListener(this, sensor, s[1]);
            }
        }
    }

    private void unregisterSensors() {
        if (mSensorManager != null) mSensorManager.unregisterListener(this);
    }

    // ── SensorEventListener ───────────────────────────────────────────────────

    @Override
    public void onSensorChanged(SensorEvent event) {
        String key = sensorKey(event.sensor.getType());
        if (key == null) return;

        float[] copy = new float[event.values.length];
        System.arraycopy(event.values, 0, copy, 0, copy.length);
        synchronized (mSensorCache) {
            mSensorCache.put(key, copy);
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {}

    private String sensorKey(int type) {
        switch (type) {
            case Sensor.TYPE_ACCELEROMETER:         return "acc";
            case Sensor.TYPE_GYROSCOPE:             return "gyr";
            case Sensor.TYPE_MAGNETIC_FIELD:        return "mag";
            case Sensor.TYPE_GRAVITY:               return "grv";
            case Sensor.TYPE_LINEAR_ACCELERATION:   return "lin";
            case Sensor.TYPE_ROTATION_VECTOR:       return "rot";
            case Sensor.TYPE_PRESSURE:              return "bar";
            case Sensor.TYPE_LIGHT:                 return "lux";
            case Sensor.TYPE_PROXIMITY:             return "prx";
            case Sensor.TYPE_AMBIENT_TEMPERATURE:   return "tmp";
            case Sensor.TYPE_RELATIVE_HUMIDITY:     return "hum";
            case Sensor.TYPE_STEP_COUNTER:          return "step";
            default:                                return null;
        }
    }

    // ── GPS ───────────────────────────────────────────────────────────────────

    private void startGPS() {
        mLocationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        if (mLocationManager == null) return;
        try {
            mLocationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER, 1000, 0, this);
            mLocationManager.requestLocationUpdates(
                LocationManager.NETWORK_PROVIDER, 1000, 0, this);
        } catch (SecurityException e) {
            Log.w(TAG, "Location permission not granted");
        }
    }

    private void stopGPS() {
        if (mLocationManager != null) mLocationManager.removeUpdates(this);
    }

    @Override
    public void onLocationChanged(Location location) {
        mLat      = location.getLatitude();
        mLon      = location.getLongitude();
        mAlt      = location.getAltitude();
        mBearing  = location.getBearing();
        mSpeed    = location.getSpeed();
        mAccuracy = location.getAccuracy();
    }

    @Override public void onStatusChanged(String p, int s, Bundle b) {}
    @Override public void onProviderEnabled(String p) {}
    @Override public void onProviderDisabled(String p) {}

    // ── Microphone RMS ───────────────────────────────────────────────────────

    private void startMic() {
        int sampleRate  = 8000;
        int bufferSize  = AudioRecord.getMinBufferSize(
            sampleRate,
            AudioFormat.CHANNEL_IN_MONO,
            AudioFormat.ENCODING_PCM_16BIT);

        try {
            mAudioRecord = new AudioRecord(
                MediaRecorder.AudioSource.MIC,
                sampleRate,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                bufferSize);
            mAudioRecord.startRecording();
            mMicRunning.set(true);

            Thread micThread = new Thread(() -> {
                short[] buf = new short[bufferSize];
                while (mMicRunning.get()) {
                    int read = mAudioRecord.read(buf, 0, bufferSize);
                    if (read > 0) {
                        long sum = 0;
                        for (int i = 0; i < read; i++) sum += (long) buf[i] * buf[i];
                        double rms = Math.sqrt((double) sum / read);
                        mMicRms = (float) Math.min(1.0, rms / 32768.0);
                    }
                }
                mAudioRecord.stop();
                mAudioRecord.release();
            });
            micThread.setDaemon(true);
            micThread.start();
        } catch (Exception e) {
            Log.w(TAG, "Mic init failed: " + e.getMessage());
        }
    }

    // ── Battery ───────────────────────────────────────────────────────────────

    private int getBattery() {
        BatteryManager bm = (BatteryManager) getSystemService(BATTERY_SERVICE);
        if (bm == null) return -1;
        return bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
    }

    // ── Send loop ─────────────────────────────────────────────────────────────

    private void startSendLoop() {
        mRunning.set(true);
        mSendThread = new Thread(() -> {
            while (mRunning.get()) {
                try {
                    JSONObject packet = buildPacket();
                    byte[] data = packet.toString().getBytes("UTF-8");
                    // Split if over MTU (shouldn't happen with typical sensor counts)
                    if (data.length <= 1400) {
                        DatagramPacket dp = new DatagramPacket(
                            data, data.length, mHost, mPort);
                        mSocket.send(dp);
                    } else {
                        // Send sensors in two halves
                        sendSplit(packet);
                    }
                    Thread.sleep(SEND_INTERVAL_MS);
                } catch (InterruptedException e) {
                    break;
                } catch (Exception e) {
                    Log.e(TAG, "Send error: " + e.getMessage());
                }
            }
        });
        mSendThread.setDaemon(true);
        mSendThread.start();
    }

    private JSONObject buildPacket() throws Exception {
        JSONObject packet = new JSONObject();
        packet.put("t",  System.currentTimeMillis() / 1000.0);
        packet.put("id", DEV_ID);

        JSONObject s = new JSONObject();

        synchronized (mSensorCache) {
            for (Map.Entry<String, float[]> entry : mSensorCache.entrySet()) {
                String key = entry.getKey();
                float[] v  = entry.getValue();

                if (key.equals("bar") || key.equals("lux") ||
                    key.equals("prx") || key.equals("tmp") ||
                    key.equals("hum")) {
                    s.put(key, v[0]);
                } else if (key.equals("step")) {
                    s.put(key, (int) v[0]);
                } else {
                    JSONArray arr = new JSONArray();
                    for (float f : v) arr.put(f);
                    s.put(key, arr);
                }
            }
        }

        // GPS
        if (mLat != 0 || mLon != 0) {
            JSONArray gps = new JSONArray();
            gps.put(mLat); gps.put(mLon); gps.put(mAlt);
            gps.put(mBearing); gps.put(mSpeed); gps.put(mAccuracy);
            s.put("gps", gps);
        }

        // Mic
        s.put("mic", mMicRms);

        // Battery
        int bat = getBattery();
        if (bat >= 0) s.put("bat", bat);

        packet.put("s", s);
        return packet;
    }

    private void sendSplit(JSONObject packet) throws Exception {
        // Split into motion-only and environment-only packets
        // Rarely needed but handles edge cases with many sensors populated
        JSONObject s       = packet.getJSONObject("s");
        String[]   motionKeys = {"acc","gyr","mag","grv","lin","rot"};
        String[]   envKeys    = {"bar","lux","prx","tmp","hum","gps","step","mic","bat"};

        for (String[] keys : new String[][]{motionKeys, envKeys}) {
            JSONObject sub = new JSONObject();
            for (String k : keys) {
                if (s.has(k)) sub.put(k, s.get(k));
            }
            JSONObject p = new JSONObject();
            p.put("t",  packet.getDouble("t"));
            p.put("id", packet.getString("id"));
            p.put("s",  sub);
            byte[] data = p.toString().getBytes("UTF-8");
            mSocket.send(new DatagramPacket(data, data.length, mHost, mPort));
        }
    }
}
