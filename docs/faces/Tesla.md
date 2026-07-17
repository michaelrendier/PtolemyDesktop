# Tesla

**Historical figure:** Nikola Tesla — inventor, electrical engineer, master of remote transmission  
**Responsibility:** Device interfacing — sensors, GPS, networking, robot I/O, Android bridge

---

## Overview

Tesla is Ptolemy's device interface Face. It handles all hardware sensor streams, network hole-punching, KVM control, GPS, Android device bridging, and robot I/O. All physical-world data enters Ptolemy through Tesla.

---

## Module Tree

```
Tesla/
├── SensorStream.py           ← PtolBus integration — attach_bus() → CH_SENSOR publish
├── HolePunch.py              ← NAT hole-punching for peer-to-peer connectivity
├── HolePunchClient.py        ← Hole punch client side
├── HolePunchServer.py        ← Hole punch server side
├── GpsHolePunch.py           ← GPS-aware hole-punch (location-tagged connections)
├── GpsHolePunchServer.py     ← GPS hole-punch server
├── KVM.py                    ← Keyboard/Video/Mouse remote control
├── IPZSP.py                  ← IP Zero-State Protocol
├── Sockets.py                ← Raw socket utilities
├── SurfaceP4Touchpad.py      ← Microsoft Surface Pro 4 touchpad driver
├── Zork_Sentence_Parser.py   ← Natural language command parser (robot I/O)
├── PtolDroid/                ← Android application (Java)
│   ├── SensorStreamService.java  ← Background sensor streaming service
│   └── MainActivity.java         ← Main Android entry point
└── CurseOfGemini/            ← Curses-based terminal interface experiment
```

---

## SensorStream + PtolBus

Primary data flow — Tesla publishes all sensor data to PtolBus `CH_SENSOR` channel.

```python
from Tesla.SensorStream import SensorStream
from Pharos.PtolBus import PtolBus

bus  = PtolBus()
stream = SensorStream()
stream.attach_bus(bus)   # wires Qt signals → CH_SENSOR publish

stream.start()
# All sensor events now flow through PtolBus to subscribers
# (Anaximander subscribes to GPS, Archimedes to accelerometer, etc.)
```

---

## Sensor Registry

| Sensor | Channel | Status |
|---|---|---|
| GPS | `CH_SENSOR/gps` | Stub — Android bridge pending |
| Accelerometer | `CH_SENSOR/accelerometer` | Stub |
| Gyroscope | `CH_SENSOR/gyroscope` | Stub |
| Microphone | `CH_SENSOR/microphone` | Routed to Philadelphos ears |
| Camera | `CH_SENSOR/camera` | Stub |
| KVM | `CH_SENSOR/kvm` | Active |

Sensor active/inactive state managed by `Pharos/ptolemy_settings.py` → `Tesla/sensor_inputs.json`.

---

## Hole Punching

NAT traversal for peer-to-peer Ptolemy instances. Enables direct device-to-device communication without central relay.

```python
from Tesla.HolePunch import HolePunch
punch = HolePunch(server="relay.thewanderinggod.tech")
punch.connect(peer_id="ptolemy_remote")
```

---

## PtolDroid (Android)

Android application providing sensor stream from mobile device to Ptolemy desktop.

`SensorStreamService.java` — background service that continuously streams:
- GPS location
- Accelerometer
- Gyroscope
- Proximity
- Light sensor

Data transmitted via HolePunch connection to Tesla/SensorStream on the desktop.

---

## Zork Sentence Parser

Natural language command parser for robot I/O. Parses freeform text into structured commands using Zork-style verb/noun/object decomposition. Used as the command model for Tesla device control.

---

## Settings

`Tesla/settings/settings.json`

| Key | Description |
|---|---|
| `sensor_stream_enabled` | Master sensor stream switch |
| `gps_enabled` | GPS sensor active |
| `hole_punch_server` | Relay server address |
| `kvm_enabled` | KVM control active |
| `droid_port` | PtolDroid connection port |

---

## Dependencies

- PyQt5 (Qt signals for sensor events)
- socket (stdlib — raw networking)
- Pharos/PtolBus (CH_SENSOR publisher)
- Android SDK (PtolDroid build)
