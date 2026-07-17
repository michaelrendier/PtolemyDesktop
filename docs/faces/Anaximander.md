# Anaximander

**Historical figure:** Anaximander of Miletus — first to produce a map of the known world  
**Responsibility:** Navigation and travel — geographic routing, GPS, location services

---

## Overview

Anaximander is Ptolemy's navigation Face. It handles all geographic data, routing logic, GPS interfacing, and location-aware queries. Named for the pre-Socratic philosopher who drew the first known world map.

---

## Modules

| Module | Description |
|---|---|
| `Navigation.py` | Core navigation logic — routing, waypoints, destination management |

---

## Planned Capabilities

| Capability | Status |
|---|---|
| GPS integration | Stub — wired via Tesla SensorStream |
| Offline map cache | Stub — settings flag exists |
| Route calculation | Partial |
| Location-aware search | Planned — Phaleron integration |
| Map provider abstraction | Stub — OSM / Google / Bing enum |

---

## GPS Data Flow

```
Tesla/SensorStream → CH_SENSOR (PtolBus) → Anaximander subscriber
```

GPS sensor data arrives on the PtolBus `CH_SENSOR` channel. Anaximander subscribes and maintains current location state.

---

## Settings

`Anaximander/settings/settings.json`

| Key | Default | Description |
|---|---|---|
| `default_map_provider` | `osm` | Map tile source: osm / google / bing |
| `gps_update_interval_s` | `5` | GPS poll interval in seconds |
| `offline_maps_enabled` | `false` | Cache map tiles locally |

All settings currently stubbed — wiring pending Tesla GPS activation.

---

## Dependencies

- Tesla/SensorStream (GPS source)
- Pharos/PtolBus (sensor channel subscriber)
- Mouseion (map display target, planned)
