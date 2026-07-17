#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Tesla/PtolSense.py — iOS Sensor Stream Bridge
==============================================
iOS does not allow raw UDP from native apps without entitlements,
but Pythonista (iOS Python environment) does.

This script runs IN Pythonista on the iPhone/iPad and streams
all available CoreMotion and CoreLocation sensors to Tesla/SensorStream.py.

Requires: Pythonista 3 on iOS (https://omz-software.com/pythonista/)
          Run from Pythonista app — no Xcode required.

Sensor availability on iOS vs Android:
    iOS via Pythonista/motion module:
        ✓ Accelerometer (user + gravity separated)
        ✓ Gyroscope
        ✓ Magnetometer
        ✓ Gravity
        ✓ Attitude (rotation as Euler angles, not quaternion)
        ✓ Barometer (iPhone 6+ / iPad Air 2+)
        ~ GPS (via location module, requires permission each run)
        ✗ Step counter (HealthKit, not accessible from Pythonista)
        ✗ Proximity sensor (private API)
        ✗ Ambient light (private API)
        ~ Microphone (not available from Pythonista)
        ✓ Battery level (via objc_util)

Usage on device:
    1. Install Pythonista from App Store
    2. Copy this script to Pythonista
    3. Edit HOST and PORT below
    4. Run — sensors stream immediately

Or over SSH via StaSh (Pythonista shell):
    python PtolSense.py --host 192.168.1.100 --port 5556 --hz 20
"""

import sys
import time
import json
import socket
import struct

# ── Configuration ─────────────────────────────────────────────────────────────
HOST       = '192.168.1.100'    # Ptolemy machine IP — change this
# TODO:SETTINGS — hardcoded port → Tesla/settings tab
PORT       = 5556
DEVICE_ID  = 'ptolsense_ios_01'
MOTION_HZ  = 20                 # samples/sec for IMU
ENV_HZ     = 1                  # samples/sec for GPS/baro
# ─────────────────────────────────────────────────────────────────────────────

def is_pythonista():
    try:
        import motion
        return True
    except ImportError:
        return False


# ── Pythonista (on-device) implementation ────────────────────────────────────

def run_pythonista(host, port, device_id, motion_hz, env_hz):
    import motion
    try:
        import location
        has_location = True
    except ImportError:
        has_location = False

    motion.start_updates()
    if has_location:
        location.start_updates()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    motion_interval = 1.0 / motion_hz
    env_interval    = 1.0 / env_hz
    last_env        = 0.0
    frame           = 0

    print(f'[PtolSense] Streaming to {host}:{port} at {motion_hz}Hz')

    try:
        while True:
            t_start = time.time()
            now     = t_start

            sensors = {}

            # ── IMU ──────────────────────────────────────────────────────────
            try:
                g = motion.get_gravity()
                sensors['grv'] = [g[0], g[1], g[2]]

                a = motion.get_user_acceleration()
                sensors['lin'] = [a[0], a[1], a[2]]

                # Total = gravity + user acceleration
                sensors['acc'] = [g[0]+a[0], g[1]+a[1], g[2]+a[2]]
            except Exception:
                pass

            try:
                gy = motion.get_rotation_rate()
                sensors['gyr'] = [gy[0], gy[1], gy[2]]
            except Exception:
                pass

            try:
                m = motion.get_magnetic_field()
                # Pythonista returns (x, y, z, accuracy)
                sensors['mag'] = [m[0], m[1], m[2]]
            except Exception:
                pass

            try:
                # Attitude as Euler angles (pitch, roll, yaw) in radians
                att = motion.get_attitude()
                # Encode as rotation vector [pitch, roll, yaw, 0] — no quaternion API
                sensors['rot'] = [att[0], att[1], att[2], 0.0]
            except Exception:
                pass

            # ── Environment (slower rate) ──────────────────────────────────
            if now - last_env >= env_interval:
                last_env = now

                # Barometer
                try:
                    bar = motion.get_pressure()   # kPa on iOS
                    if bar is not None:
                        sensors['bar'] = bar * 10.0   # kPa → hPa
                except Exception:
                    pass

                # GPS
                if has_location:
                    try:
                        loc = location.get_location()
                        if loc:
                            sensors['gps'] = [
                                loc.get('latitude',  0.0),
                                loc.get('longitude', 0.0),
                                loc.get('altitude',  0.0),
                                loc.get('course',    0.0),
                                loc.get('speed',     0.0),
                                loc.get('horizontal_accuracy', 0.0),
                            ]
                    except Exception:
                        pass

                # Battery
                try:
                    import objc_util
                    dev = objc_util.ObjCClass('UIDevice').currentDevice()
                    dev.setBatteryMonitoringEnabled_(True)
                    bat_level = dev.batteryLevel()
                    if bat_level >= 0:
                        sensors['bat'] = int(bat_level * 100)
                except Exception:
                    pass

            # ── Build and send packet ────────────────────────────────────────
            if sensors:
                packet = {
                    't':  now,
                    'id': device_id,
                    's':  sensors,
                }
                payload = json.dumps(packet).encode('utf-8')
                if len(payload) <= 1400:
                    sock.sendto(payload, (host, port))

            frame += 1
            elapsed = time.time() - t_start
            sleep   = max(0, motion_interval - elapsed)
            time.sleep(sleep)

    except KeyboardInterrupt:
        print('\n[PtolSense] Stopped')
    finally:
        motion.stop_updates()
        if has_location:
            location.stop_updates()
        sock.close()


# ── Desktop test stub (for development without a device) ─────────────────────

def run_desktop_stub(host, port, device_id, motion_hz):
    """
    Generates synthetic sensor data for testing SensorStream.py
    without a physical device. Runs on the desktop.
    python3 Tesla/PtolSense.py --stub --host 127.0.0.1
    """
    import math
    import random

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    interval = 1.0 / motion_hz
    t0       = time.time()
    frame    = 0

    print(f'[PtolSense-STUB] Synthetic sensor data → {host}:{port}')

    try:
        while True:
            t   = time.time()
            age = t - t0
            sensors = {
                'acc': [
                    0.05 * math.sin(age * 2.1),
                    0.05 * math.cos(age * 1.7),
                    9.81 + 0.02 * math.sin(age * 0.3),
                ],
                'gyr': [
                    0.01 * math.sin(age * 3.0),
                    0.01 * math.cos(age * 2.5),
                    0.005 * math.sin(age * 1.1),
                ],
                'mag': [25.0 + random.gauss(0, 0.5),
                        -10.0 + random.gauss(0, 0.5),
                        40.0 + random.gauss(0, 0.5)],
                'grv': [0.0, 0.0, 9.81],
                'bar': 1013.25 + 0.1 * math.sin(age * 0.05),
                'lux': 300.0 + 50 * math.sin(age * 0.1),
                'gps': [49.2827 + age * 0.000001,
                        -123.1207 + age * 0.000001,
                        50.0, 45.0, 1.2, 5.0],
                'bat': max(0, 100 - int(age / 36)),
                'mic': abs(0.1 * math.sin(age * 10.0)),
            }
            packet = {'t': t, 'id': device_id, 's': sensors}
            payload = json.dumps(packet).encode()
            sock.sendto(payload, (host, port))
            frame += 1
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f'\n[Stub] Sent {frame} packets')
    finally:
        sock.close()


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    host      = HOST
    port      = PORT
    device_id = DEVICE_ID
    hz        = MOTION_HZ
    stub      = False

    i = 0
    while i < len(args):
        if args[i] == '--host'     and i+1 < len(args): host      = args[i+1]; i+=2
        elif args[i] == '--port'   and i+1 < len(args): port      = int(args[i+1]); i+=2
        elif args[i] == '--id'     and i+1 < len(args): device_id = args[i+1]; i+=2
        elif args[i] == '--hz'     and i+1 < len(args): hz        = int(args[i+1]); i+=2
        elif args[i] == '--stub':  stub = True; i+=1
        else: i+=1

    if stub:
        run_desktop_stub(host, port, device_id, hz)
    elif is_pythonista():
        run_pythonista(host, port, device_id, hz, ENV_HZ)
    else:
        print('Not running in Pythonista. Use --stub for desktop testing.')
        print('On iOS: copy this script to Pythonista and run it there.')
        sys.exit(1)


if __name__ == '__main__':
    main()
