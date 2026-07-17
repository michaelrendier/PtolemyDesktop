#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Tesla/SensorStream.py — Mobile Sensor Stream Receiver
======================================================
Receives real-time sensor data from Android (PtolDroid) or iOS (PtolSense)
devices over UDP. Works on LAN or over a punched hole (Tesla.HolePunch).

Sensor coverage:
    Motion:      accelerometer, gyroscope, gravity, linear_acceleration,
                 rotation_vector, game_rotation_vector, step_counter
    Environment: magnetometer, barometer, ambient_light, temperature,
                 humidity, proximity
    Position:    gps (lat/lon/alt/bearing/speed/accuracy)
    Audio:       mic_level (RMS amplitude, not raw audio)
    Camera:      orientation hint only (not video — use TreasureHunt VNC for that)

Packet format (JSON over UDP, max 1400 bytes to stay under MTU):
    {
        "t":  1713600000.123,      // unix timestamp float
        "id": "ptoldroid_01",      // device identifier
        "s": {                     // sensor dict — only present sensors
            "acc":  [x, y, z],     // accelerometer m/s²
            "gyr":  [x, y, z],     // gyroscope rad/s
            "mag":  [x, y, z],     // magnetometer µT
            "grv":  [x, y, z],     // gravity m/s²
            "lin":  [x, y, z],     // linear acceleration m/s²
            "rot":  [x, y, z, w],  // rotation vector (quaternion)
            "bar":  p,             // barometer hPa
            "lux":  l,             // ambient light lux
            "prx":  d,             // proximity cm (or 0/1 near/far)
            "tmp":  t,             // temperature °C
            "hum":  h,             // humidity %
            "gps":  [lat, lon, alt, bearing, speed, accuracy],
            "step": n,             // step count since reboot
            "mic":  rms,           // microphone RMS level 0.0–1.0
            "bat":  pct            // battery % 0–100
        }
    }

Device sends at configurable rate (default 20Hz motion, 1Hz environment/GPS).
Receiver de-multiplexes by sensor key, emits typed Qt signals.

Usage (Ptolemy integration):
    stream = SensorStream(parent=ptolemy)
    stream.accelerometer.connect(lambda x, y, z: ...)
    stream.gps.connect(lambda lat, lon, alt, bearing, speed, acc: ...)
    stream.listen()                              # LAN, port 5556
    # or over punched hole:
    stream.listen(sock=ptolemy.hole_punch.sock)

Standalone:
    python3 -m Tesla.SensorStream --port 5556 --print
"""

import json
import socket
import time
from collections import deque

from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal


# ── Sensor signal definitions ─────────────────────────────────────────────────

class SensorSignals(QObject):
    """All sensor signals in one place for clean connection."""

    # Motion
    accelerometer       = pyqtSignal(float, float, float)          # x y z m/s²
    gyroscope           = pyqtSignal(float, float, float)          # x y z rad/s
    gravity             = pyqtSignal(float, float, float)          # x y z m/s²
    linear_acceleration = pyqtSignal(float, float, float)          # x y z m/s²
    rotation_vector     = pyqtSignal(float, float, float, float)   # x y z w
    magnetometer        = pyqtSignal(float, float, float)          # x y z µT

    # Environment
    barometer           = pyqtSignal(float)                        # hPa
    ambient_light       = pyqtSignal(float)                        # lux
    proximity           = pyqtSignal(float)                        # cm or 0/1
    temperature         = pyqtSignal(float)                        # °C
    humidity            = pyqtSignal(float)                        # %

    # Position
    gps                 = pyqtSignal(float, float, float, float, float, float)
    #                                lat    lon    alt    bearing speed  accuracy

    # Activity
    step_counter        = pyqtSignal(int)                          # steps since reboot
    mic_level           = pyqtSignal(float)                        # RMS 0.0–1.0
    battery             = pyqtSignal(int)                          # % 0–100

    # Meta
    device_connected    = pyqtSignal(str, str)     # device_id, addr
    device_lost         = pyqtSignal(str)          # device_id
    raw_packet          = pyqtSignal(dict)         # full packet for debugging
    packet_received     = pyqtSignal(dict, str)    # packet, device_id — bus publisher
    parse_error         = pyqtSignal(str, bytes)   # error msg, raw data


# ── Per-device state tracker ──────────────────────────────────────────────────

class DeviceState:
    """Tracks last-seen time and packet rate for one device."""
    TIMEOUT_S = 10.0

    def __init__(self, device_id, addr):
        self.device_id  = device_id
        self.addr       = addr
        self.last_seen  = time.monotonic()
        self._timestamps = deque(maxlen=100)

    def ping(self, addr):
        now = time.monotonic()
        self._timestamps.append(now)
        self.last_seen = now
        self.addr = addr

    @property
    def is_alive(self):
        return (time.monotonic() - self.last_seen) < self.TIMEOUT_S

    @property
    def packet_rate_hz(self):
        ts = list(self._timestamps)
        if len(ts) < 2:
            return 0.0
        window = ts[-1] - ts[0]
        return (len(ts) - 1) / window if window > 0 else 0.0


# ── Receive thread ────────────────────────────────────────────────────────────

class SensorReceiveThread(QThread):
    """
    Blocking UDP receive loop. Parses packets and emits raw_packet signal.
    Runs in its own thread — never blocks the Qt event loop.
    """

    raw_packet   = pyqtSignal(dict, str, int)   # packet, addr_ip, addr_port
    recv_error   = pyqtSignal(str, bytes)
    started_ok   = pyqtSignal(str, int)         # bound_ip, port

    def __init__(self, host, port, sock=None, buffer_size=2048):
        super().__init__()
        self.host        = host
        self.port        = port
        self._ext_sock   = sock         # pre-punched socket (optional)
        self.buffer_size = buffer_size
        self._running    = False
        self._sock       = None

    def run(self):
        self._running = True

        if self._ext_sock:
            # Reuse punched socket from HolePunch
            self._sock = self._ext_sock
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(1.0)
            self._sock.bind((self.host, self.port))

        self.started_ok.emit(self.host, self.port)

        while self._running:
            try:
                data, addr = self._sock.recvfrom(self.buffer_size)
                try:
                    packet = json.loads(data.decode('utf-8'))
                    self.raw_packet.emit(packet, addr[0], addr[1])
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    self.recv_error.emit(str(e), data)
            except socket.timeout:
                continue
            except OSError:
                break

        if not self._ext_sock and self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def stop(self):
        self._running = False
        self.quit()
        self.wait(2000)


# ── SensorStream — main interface ─────────────────────────────────────────────

class SensorStream(QObject):
    """
    Main sensor stream receiver for Ptolemy/Tesla.

    Manages device registry, dispatches sensor signals,
    detects device timeouts, supports multiple simultaneous devices.

    Signals are on self.sig (SensorSignals instance).

    Usage:
        stream = SensorStream(parent=ptolemy)
        stream.sig.accelerometer.connect(on_accel)
        stream.sig.gps.connect(on_gps)
        stream.listen()

    Rate control (tell device what to send):
        stream.configure_device(device_id, rates={
            'motion_hz': 20,
            'env_hz':    1,
            'gps_hz':    1,
            'sensors':   ['acc', 'gyr', 'gps', 'bar']
        })
    """

    # Sensor key → signal emitter method name
    _DISPATCH = {
        'acc': '_emit_acc',
        'gyr': '_emit_gyr',
        'mag': '_emit_mag',
        'grv': '_emit_grv',
        'lin': '_emit_lin',
        'rot': '_emit_rot',
        'bar': '_emit_bar',
        'lux': '_emit_lux',
        'prx': '_emit_prx',
        'tmp': '_emit_tmp',
        'hum': '_emit_hum',
        'gps': '_emit_gps',
        'step':'_emit_step',
        'mic': '_emit_mic',
        'bat': '_emit_bat',
    }

    def __init__(self, host='0.0.0.0', port=5556, parent=None, bus=None):
        super().__init__(parent)
        self.host    = host
        self.port    = port
        self.sig     = SensorSignals(self)
        self._bus    = bus   # PtolBus reference — set externally or via attach_bus()

        self._devices  = {}     # device_id → DeviceState
        self._thread   = None
        self._sock     = None   # external punched socket if provided

    def attach_bus(self, bus):
        """
        Attach a PtolBus. After this, every sensor packet is also
        published to CH_SENSOR so TuningDisplay and other subscribers see it.
        """
        self._bus = bus
        # Wire packet signal to bus publisher
        self.sig.packet_received.connect(self._publish_to_bus)

    def _publish_to_bus(self, packet: dict, device_id: str):
        if self._bus is None:
            return
        try:
            from Pharos.PtolBus import BusMessage, CH_SENSOR, Priority
            self._bus.publish(BusMessage(
                CH_SENSOR,
                {'device': device_id, 'packet': packet},
                Priority.T1, sender='Tesla.SensorStream'))
        except Exception:
            pass

        # Device timeout watchdog — checks every 5s
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(5000)
        self._watchdog.timeout.connect(self._check_timeouts)

    # ── Start / stop ──────────────────────────────────────────────────────────

    def listen(self, sock=None):
        """
        Start receiving sensor data.
        sock: pre-opened UDP socket (from HolePunch) — binds to that instead.
        """
        self._sock   = sock
        self._thread = SensorReceiveThread(
            self.host, self.port,
            sock=sock,
            buffer_size=2048)
        self._thread.raw_packet.connect(self._on_packet)
        self._thread.recv_error.connect(
            lambda msg, data: self.sig.parse_error.emit(msg, data))
        self._thread.started_ok.connect(
            lambda h, p: print(f'[SensorStream] Listening on {h}:{p}'))
        self._thread.start()
        self._watchdog.start()

    def stop(self):
        self._watchdog.stop()
        if self._thread:
            self._thread.stop()
            self._thread = None

    # ── Packet dispatch ───────────────────────────────────────────────────────

    def _on_packet(self, packet, addr_ip, addr_port):
        device_id = packet.get('id', addr_ip)
        sensors   = packet.get('s', {})

        # Device registry
        if device_id not in self._devices:
            self._devices[device_id] = DeviceState(device_id, (addr_ip, addr_port))
            self.sig.device_connected.emit(device_id, addr_ip)
        self._devices[device_id].ping((addr_ip, addr_port))

        self.sig.raw_packet.emit(packet)

        # Dispatch each sensor key
        for key, emitter_name in self._DISPATCH.items():
            if key in sensors:
                getattr(self, emitter_name)(sensors[key])

    # ── Signal emitters ───────────────────────────────────────────────────────

    def _emit_acc(self, v):
        if len(v) >= 3:
            self.sig.accelerometer.emit(float(v[0]), float(v[1]), float(v[2]))

    def _emit_gyr(self, v):
        if len(v) >= 3:
            self.sig.gyroscope.emit(float(v[0]), float(v[1]), float(v[2]))

    def _emit_mag(self, v):
        if len(v) >= 3:
            self.sig.magnetometer.emit(float(v[0]), float(v[1]), float(v[2]))

    def _emit_grv(self, v):
        if len(v) >= 3:
            self.sig.gravity.emit(float(v[0]), float(v[1]), float(v[2]))

    def _emit_lin(self, v):
        if len(v) >= 3:
            self.sig.linear_acceleration.emit(float(v[0]), float(v[1]), float(v[2]))

    def _emit_rot(self, v):
        if len(v) >= 4:
            self.sig.rotation_vector.emit(
                float(v[0]), float(v[1]), float(v[2]), float(v[3]))

    def _emit_bar(self, v):
        self.sig.barometer.emit(float(v))

    def _emit_lux(self, v):
        self.sig.ambient_light.emit(float(v))

    def _emit_prx(self, v):
        self.sig.proximity.emit(float(v))

    def _emit_tmp(self, v):
        self.sig.temperature.emit(float(v))

    def _emit_hum(self, v):
        self.sig.humidity.emit(float(v))

    def _emit_gps(self, v):
        if len(v) >= 6:
            self.sig.gps.emit(
                float(v[0]), float(v[1]), float(v[2]),
                float(v[3]), float(v[4]), float(v[5]))

    def _emit_step(self, v):
        self.sig.step_counter.emit(int(v))

    def _emit_mic(self, v):
        self.sig.mic_level.emit(float(v))

    def _emit_bat(self, v):
        self.sig.battery.emit(int(v))

    # ── Device management ─────────────────────────────────────────────────────

    def _check_timeouts(self):
        dead = [did for did, ds in self._devices.items() if not ds.is_alive]
        for did in dead:
            del self._devices[did]
            self.sig.device_lost.emit(did)

    def devices(self):
        """Return dict of live device_id → DeviceState."""
        return {k: v for k, v in self._devices.items() if v.is_alive}

    def device_rate(self, device_id):
        """Return current packet rate in Hz for a device."""
        ds = self._devices.get(device_id)
        return ds.packet_rate_hz if ds else 0.0

    def configure_device(self, device_id, rates=None):
        """
        Send configuration packet back to device.
        rates dict example:
            {'motion_hz': 20, 'env_hz': 1, 'gps_hz': 1,
             'sensors': ['acc', 'gyr', 'gps', 'bar', 'mag']}
        Device must implement CONFIG packet handling (see PtolDroid).
        """
        ds = self._devices.get(device_id)
        if not ds or not self._thread or not self._thread._sock:
            return False
        config = {'cmd': 'CONFIG', 'rates': rates or {}}
        try:
            payload = json.dumps(config).encode()
            self._thread._sock.sendto(payload, ds.addr)
            return True
        except Exception:
            return False


# ── Recorder — persist sensor streams to disk ─────────────────────────────────

class SensorRecorder(QObject):
    """
    Optional: attach to a SensorStream to log all raw packets to JSONL.
    One line per packet. Gzip optional.
    Usage:
        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        rec = SensorRecorder(PTOL_ROOT + '/media/sensors/')
        rec.attach(stream)
        rec.start('session_01')
        rec.stop()
    """

    def __init__(self, output_dir, gzip=False, parent=None):
        super().__init__(parent)
        self.output_dir = output_dir
        self.gzip       = gzip
        self._file      = None
        self._stream    = None
        self._session   = None

    def attach(self, sensor_stream):
        self._stream = sensor_stream
        sensor_stream.sig.raw_packet.connect(self._write)

    def start(self, session_name=None):
        import os
        ts = time.strftime('%Y%m%d_%H%M%S')
        name = f'{session_name or ts}.jsonl'
        if self.gzip:
            name += '.gz'
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, name)
        if self.gzip:
            import gzip
            self._file = gzip.open(path, 'wt', encoding='utf-8')
        else:
            self._file = open(path, 'w', encoding='utf-8')
        self._session = session_name
        print(f'[SensorRecorder] Recording to {path}')

    def _write(self, packet):
        if self._file:
            try:
                self._file.write(json.dumps(packet) + '\n')
            except Exception:
                pass

    def stop(self):
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None


# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # TODO:SETTINGS — hardcoded port → Tesla/settings tab
    port = 5556
    if '--port' in sys.argv:
        port = int(sys.argv[sys.argv.index('--port') + 1])

    verbose = '--print' in sys.argv

    stream = SensorStream(port=port)

    if verbose:
        stream.sig.accelerometer.connect(
            lambda x, y, z: print(f'ACC  {x:8.3f} {y:8.3f} {z:8.3f}'))
        stream.sig.gyroscope.connect(
            lambda x, y, z: print(f'GYR  {x:8.3f} {y:8.3f} {z:8.3f}'))
        stream.sig.gps.connect(
            lambda lat, lon, alt, b, sp, ac:
                print(f'GPS  {lat:.6f} {lon:.6f}  alt={alt:.1f}m  spd={sp:.1f}m/s'))
        stream.sig.barometer.connect(
            lambda p: print(f'BAR  {p:.2f} hPa'))
        stream.sig.device_connected.connect(
            lambda did, addr: print(f'[+] Device connected: {did} from {addr}'))
        stream.sig.device_lost.connect(
            lambda did: print(f'[-] Device lost: {did}'))

    stream.listen()
    print(f'[SensorStream] Listening on 0.0.0.0:{port}')
    print('  Waiting for sensor data from PtolDroid or PtolSense...')
    print('  Ctrl+C to stop')

    sys.exit(app.exec())
