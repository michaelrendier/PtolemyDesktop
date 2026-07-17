# PtolBus — Ptolemy Message Bus

`Pharos/PtolBus.py`

---

## Overview

PtolBus is Ptolemy's internal message bus. All inter-Face communication passes through it. The bus is not a simple queue — it is the thread pool owner. Ptolemy hands it a `ResourceBudget` at boot; the bus manages all thread allocation internally from that budget.

---

## Architecture Flags

| Flag | Effect |
|---|---|
| `BUS_IS_THREADS` | Bus owns and IS the thread pool. Ptolemy hands a `ResourceBudget` at start. |
| `FACE_POST_BOOT` | No Face exists until POST completes. Bus rejects messages from unregistered Faces (strict mode). |
| `PER_FACE_STDIO` | Each Face gets `CH_FACE_IN/OUT/ERR` triple + 4 thread slots. |
| `THREAD_POOL_DYNAMIC` | Ptolemy reserves 5 kernel slots (K0-K4). Per-Face minimum 4. Aule sizes the rest. |
| `ALL_BUS_EVENTS_TO_DMESG` | Every bus event writes to PtolDmesg. Aule watches dmesg only — never called directly by the bus. |
| `EARLY_SYMPTOM_DETECTION` | HealthMonitor tracks queue backpressure, thread starvation. Symptom level 0.0–1.0 → TuningDisplay gradient. |
| `CYCLIC_CONTEXT_BUFFER_SHARED` | `CH_CONTEXT` channel; Ptolemy kernel calls `broadcast_context_update()`. All Faces read from it. |
| `LICH` | Emergency interface. `engage_emergency(lich)` — Lich takes authority over bus during emergency. Bus inversion of authority. |

---

## Priority Scheme — Rotary Semaphore

Not a binary gate. Traffic circle model: message enters the rotary and yields until its tier clears. Within tier: FIFO by timestamp.

| Priority | Tier | Behaviour |
|---|---|---|
| T0 | system / critical | Always first — right of way, no yield |
| T1 | user / normal | Right of way over T2-T4 |
| T2 | autonomous | Yields in rotary |
| T3 | autonomous | Yields |
| T4 | autonomous | Lowest — always yields |

```python
from Pharos.PtolBus import Priority, BusMessage

msg = BusMessage(channel=CH_PROMPT, payload=data, priority=Priority.T1)
```

---

## Thread Pool

**Kernel slots (permanent — never parked by the bus):**

| Slot | Name | Role |
|---|---|---|
| K0 | BusDispatch | Internal queue drain — always running |
| K1 | UserDirective | User-facing commands |
| K2-K4 | Autonomous | Parked on "Full Attention Please" signal |

**Face slots (allocated on POST):**  
Each Face gets four slots: `{face_id}_stdin`, `{face_id}_stdout`, `{face_id}_stderr`, `{face_id}_work`.

Additional slots: Face requests via `CH_LOG → dmesg → Aule`. Aule grants or denies.

---

## Channels

| Channel | Constant | Purpose |
|---|---|---|
| `PROMPT` | `CH_PROMPT` | User prompt submission |
| `INFERENCE_COORDS` | `CH_INFERENCE` | LSH inference coordinate packets |
| `LUTHSPELL` | `CH_LUTHSPELL` | LuthSpell boundary and halt events |
| `FACE_EVENT` | `CH_FACE_EVENT` | Face lifecycle events (POST, shutdown) |
| `SENSOR` | `CH_SENSOR` | Device/GPS sensor data |
| `LOG` | `CH_LOG` | Face log requests → dmesg |
| `BLOCKCHAIN` | `CH_BLOCKCHAIN` | PtolChain audit events |
| `SETTINGS` | `CH_SETTINGS` | Settings change broadcasts |
| `CONTEXT` | `CH_CONTEXT` | CyclicContextBuffer shared broadcast |
| `DMESG` | `CH_DMESG` | Bus-internal events reflected to dmesg |

---

## ResourceBudget

```python
from Pharos.PtolBus import ResourceBudget

budget = ResourceBudget(
    kernel_threads=5,       # K0-K4, permanent
    max_face_threads=40,    # soft cap — Aule can raise
    dispatch_interval_ms=10
)
bus.handshake(budget)
```

---

## Usage

```python
from Pharos.PtolBus import PtolBus, Priority, BusMessage

bus = PtolBus()
bus.start()

# Publish — T1 (normal)
bus.publish(BusMessage(CH_SENSOR, {"gps": {"lat": 51.5, "lon": -0.1}}, Priority.T1))

# Subscribe
bus.subscribe(CH_ARCHIMEDES, my_callback)

# Broadcast context update (kernel-level only)
bus.broadcast_context_update(context_entry)
```

---

## HealthMonitor

Polls every `health_poll_interval` seconds (default 5). Tracks:
- Queue depth (backpressure)
- Thread slot starvation approach
- Symptom level 0.0–1.0

Emits `symptom_level_changed(float)` signal → `TuningDisplay` renders gradient overlay.

---

## Settings

`Pharos/settings/ptolemy_bus/settings.json`

| Key | Default | Description |
|---|---|---|
| `priority_scheme` | `rotary` | Semaphore model |
| `queue_maxsize` | `1024` | Bus queue depth |
| `dispatch_interval_ms` | `10` | Queue drain interval |
| `strict_post` | `false` | Reject unregistered Face messages |
| `health_poll_interval` | `5` | Seconds between HealthMonitor polls |
| `max_face_threads` | `40` | Soft cap on Face thread slots |
