# LuthSpell — BUS Controller & Halting Monitor

`Pharos/luthspell.py`

---

## Overview

LuthSpell is Ptolemy's BUS controller. It lives above all Faces and is not a Face itself — it belongs to Ptolemy (the kernel), not to Pharos. Its job is T0/T1 priority arbitration, halting monitor, error handling, and garbage collection.

**LuthSpell has no persistent state beyond what the blockchain holds.** The blockchain is the source of truth for boundary and halt records.

---

## Components

| Component | Role |
|---|---|
| `LuthSpell` | BUS controller — T0/T1 arbitration, rotary semaphore |
| `HaltingMonitor` | Internal sensing organ — watches inference coordinates |
| `ErrorHandler` | Catches, classifies, routes all Ptolemy errors |
| `GarbageCollector` | Triggered on `gc_trigger` class errors |

---

## Halting Monitor

The HaltingMonitor is LuthSpell's internal organ. It does not terminate inference — it marks a **boundary**. "YOU SHALL NOT PASS" is a boundary marker, not a kill signal. Ptolemy receives the halt report and issues a redirect.

```python
from Pharos.luthspell import LuthSpell, HaltingMonitor

monitor = HaltingMonitor()

# Set boundary at start of inference
boundary_hash = monitor.set_boundary(inference_coords)

# Check each inference step
halt, reason = monitor.check(current_coords)
if halt:
    # Report to Ptolemy — Ptolemy issues redirect
    ptolemy.redirect(reason, current_coords)
```

**Boundary hash:** SHA-256 of `f"{coords}|{timestamp}"`. Committed to blockchain on creation. Halt records reference the boundary hash.

---

## Priority Arbitration

LuthSpell enforces the T0/T1 rotary scheme:

- **T0** (system/critical): Always first — `CHANNEL_LUTHSPELL`, `CHANNEL_INFERENCE` control messages
- **T1** (user/normal): Prompt submissions, inference packets

LuthSpell subscribes to `CHANNEL_PROMPT` and `CHANNEL_INFERENCE`. On prompt receipt (T1): sets boundary. On inference coordinate receipt: calls `monitor.check()`.

```python
def _on_prompt(self, msg):
    if msg.priority <= Priority.T1:
        h = self._monitor.set_boundary(msg.payload)
        self._publish(f"boundary_set:{h[:16]}", Priority.T0)

def _on_inference_coord(self, msg):
    halt, reason = self._monitor.check(msg.payload)
    if halt:
        self._halt_pass(reason, msg.payload)
```

---

## Error Catalog

27 typed errors across 8 subsystems:

| Range | Subsystem | Example |
|---|---|---|
| PTL_1xx | BUS | PTL_101 QueueOverflow |
| PTL_2xx | LuthSpell / Halting | PTL_201 BoundaryViolation |
| PTL_3xx | CyclicContextBuffer | PTL_301 EvictionFailed |
| PTL_4xx | Blockchain | PTL_401 ChainCorrupt |
| PTL_5xx | Acquisition / HyperWebster | PTL_504 RabiesViolation |
| PTL_6xx | LSH Model | PTL_601 InferenceTimeout |
| PTL_7xx | Module / Settings | PTL_701 ModuleNotFound |
| PTL_9xx | System / Root | PTL_901 BootFailed |

`PTL_504 RabiesViolation` — FATAL, no GC. `first_encountered` immutability breach. Audit trail only — no recovery. Originates from `Callimachus/v09/core/lsh_datatype.py`.

Error classification is in `luthspell_error_handler.py`. Each error class has: code, subsystem, severity, gc_trigger (bool).

---

## GarbageCollector

Triggered only on `gc_trigger=True` error classes. LuthSpell does not run GC on its own schedule. The GC fires when an error-class event is published on `CH_LUTHSPELL` with `gc_trigger: true` in the payload.

GC does not touch Aule-owned state. Aule is sole writer to dmesg and forge. GC only touches: inference coordinate caches, stale context buffer references, orphaned Face thread registrations.

---

## Blockchain Integration

All halt records and boundary sets are committed to the PtolChain blockchain:

```python
from Callimachus.BlockChain.PtolChain import AuditChain

chain = AuditChain(face="LuthSpell")
chain.log(halt_record.to_dict())
```

This is the only persistent state LuthSpell has. On restart, LuthSpell re-reads recent chain entries to recover boundary context.

---

## Wire Protocol

```python
luth = LuthSpell(bus=bus, chain=chain, on_halt=ptolemy.redirect)
luth.wire()  # subscribe to CH_PROMPT and CH_INFERENCE
```

`on_halt` callback receives `(reason, coords)`. It is Ptolemy's redirect handler — LuthSpell never directly manipulates inference; it only reports.

---

## Settings

`Pharos/settings/luthspell/settings.json`

| Key | Default | Description |
|---|---|---|
| `channel_prompt` | `PROMPT` | Prompt channel name |
| `channel_inference` | `INFERENCE_COORDS` | Inference coordinate channel |
| `channel_luthspell` | `LUTHSPELL` | LuthSpell event channel |
| `blockchain_backend` | `branch` | Blockchain backend type |
| `priority_scheme` | `rotary` | Arbitration scheme |
