# Pharos

**Historical figure:** The Pharos of Alexandria — the great lighthouse, guiding force and signal tower  
**Responsibility:** Core functions, main shell UI, PtolBus, LuthSpell, desktop, settings

---

## Overview

Pharos is the root Face of Ptolemy. It owns the main desktop environment, the PtolBus message bus, LuthSpell (the bus controller), the PtolShell command interface, all UI infrastructure, and the settings system. Every other Face connects to the system through Pharos.

---

## Module Tree

```
Pharos/
├── PtolBus.py            ← Message bus — rotary semaphore, T0/T1 queue, QThread dispatcher
├── luthspell.py          ← BUS controller — HaltingMonitor, ErrorHandler, GarbageCollector
├── luthspell_error_handler.py  ← 27 typed errors across 8 subsystems
├── PtolShell.py          ← Command shell — face/faces/bus/help commands
├── PtolDesktop.py        ← QGraphicsScene desktop — JACK-style process graph
├── Interface.py          ← Window manager, tooltips, keyboard shortcuts
├── PGui.py               ← Window drag (scenePos throughout), window lifecycle
├── PtolFace.py           ← Base class for all Face windows
├── FaceIdentity.py       ← Face identification and registration
├── PtolDmesg.py          ← System message log — Aule is sole writer, Faces submit
├── TuningDisplay.py      ← Live PtolBus stream monitor widget
├── SystemTrayIcon.py     ← Dual tray menus: left=user, right=system
├── ptolemy_settings.py   ← Settings integration engine — scans for settings.json
├── settings_window.py    ← Settings UI — PtolemySettingsWindow / SettingsWindow alias
├── PtolColor.py          ← Ptolemy colour palette
├── Menu.py               ← Menu builder
├── Indicators.py         ← Status indicators (threading, active state)
├── DropWindow.py         ← Drag-and-drop window
├── Dialogs.py            ← Common dialog boxes
├── UtilityFunctions.py   ← Shared utilities
└── menus/                ← .menu files — one per Face module
```

---

## PtolBus

Ptolemy's internal message bus. All inter-Face communication goes through PtolBus.

```python
from Pharos.PtolBus import PtolBus

bus = PtolBus()
bus.start()

# Publish
bus.publish("CH_SENSOR", {"gps": {"lat": 51.5, "lon": -0.1}})

# Subscribe
bus.subscribe("CH_ARCHIMEDES", my_callback)
```

**Architecture:**
- Rotary semaphore queue (traffic circle — not binary gate)
- T0 priority (system/critical) always before T1 (user/normal)
- FIFO within each tier — ordering: `(priority, timestamp)`
- QThread dispatcher — non-blocking relative to UI

**Channels:** `CH_SENSOR`, `CH_LUTHSPELL`, `CH_ARCHIMEDES`, `CH_ACQUIRE`, `CH_FORGE`, `CH_DESKTOP`

---

## LuthSpell

BUS controller. Lives above all Faces — not a Face itself.

| Component | Role |
|---|---|
| `LuthSpell` | T0/T1 arbitration, rotary semaphore |
| `HaltingMonitor` | Watches inference coordinates for halt conditions |
| `ErrorHandler` | Catches, classifies, routes all Ptolemy errors |
| `GarbageCollector` | Triggered on `gc_trigger` errors |

### Error Catalog

| Range | Subsystem |
|---|---|
| PTL_1xx | BUS |
| PTL_2xx | LuthSpell / Halting |
| PTL_3xx | Cyclic Context Buffer |
| PTL_4xx | Blockchain |
| PTL_5xx | Acquisition / HyperWebster |
| PTL_6xx | LSH Model |
| PTL_7xx | Module / Settings |
| PTL_9xx | System / Root |

`PTL_504 RabiesViolation` — FATAL, no GC. `first_encountered` immutability breach. Audit only.

---

## Desktop (PtolDesktop)

QGraphicsScene-based desktop. All windows are moveable scene items.

| Feature | Description |
|---|---|
| Process Graph | JACK-style node layout — Ptolemy Center + Faces as nodes |
| Sidebar | 23px activation strip, auto-hides after 45 seconds |
| Window drag | `scenePos()` throughout PGui.py |
| Minimized windows | Become nodes, auto-connect to their Face node |
| Stream connections | User drags connections manually (skills/tools model) |
| System tray | Left click = user menu, right click = system menu |

---

## Settings System

`ptolemy_settings.py` scans all of `PTOL_ROOT` for `settings.json` files conforming to the standard stack schema. All discovered modules appear in `PtolemySettingsWindow`.

**Standard stack schema** (every `settings.json` must conform):
```json
{
  "module":   "module_id",
  "face":     "FaceName",
  "display":  "Human Label",
  "version":  "1.0",
  "settings": {
    "key": {
      "value":   <current_value>,
      "type":    "str|int|float|bool|enum",
      "label":   "Human label",
      "stub":    false
    }
  }
}
```

Currently 18 modules registered across all Faces.

`select_section(name)` — navigates settings window by module_id, display name, or Face name.

---

## PtolShell Commands

| Command | Action |
|---|---|
| `face <name>` | Open a Face window |
| `faces` | List all registered Faces |
| `bus` | Show PtolBus status |
| `/math` | Open Archimedes SymPy shell |
| `help` | Command reference |

---

## TuningDisplay

Live monitor widget subscribing to all PtolBus channels. Shows real-time event stream: `CH_SENSOR`, `CH_LUTHSPELL`, `CH_ACQUIRE`, etc. Launched from Ptolemy3.py desktop.

---

## Dependencies

- PyQt5 (all UI)
- Pharos/PtolBus (self-owned)
- All Faces (registers them on startup via FaceIdentity)
