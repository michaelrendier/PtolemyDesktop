# Mandos

**Face:** Mandos — Keeper of the Dead  
**Domain:** Dormant state management, checkpoint store, supervisor resurrection, world_break  
**Priority:** Secondary supervisor — gains authority if Aule fails  
**Source:** `Mandos/`

---

## Role

Mandos holds Face state between death and resurrection.

When any Face hits a FATAL error, its state is checkpointed to Mandos before the GarbageCollector runs. Aule decides when to call for resurrection. If Aule itself dies, Mandos gains supervisor authority and attempts Aule's resurrection from checkpoint. If Mandos fails — `world_break()`.

Mandos does not repair. Mandos does not restart. Mandos holds and waits.

---

## Priority Model

```
Normal operation:    Aule has supervisor authority
Aule FATAL:          Mandos watchdog detects missed heartbeats
                     Mandos gains authority
                     Mandos attempts Aule resurrection
Aule unrestorable:   Ptolemy runs in safe mode (Pharos + Mandos only)
Mandos FATAL:        world_break() -- the world is broken
```

---

## Components

| File | Purpose |
|---|---|
| `mandos.py` | Main Face: `accept_dead()`, `release()`, `world_break()` |
| `mandos_store.py` | Atomic JSON checkpoint store, keyed by Face + ISO timestamp |
| `mandos_watchdog.py` | Daemon thread watching Aule heartbeat (5s interval, 3 misses = dead) |
| `mandos_resurrect.py` | Pulls checkpoint, calls Face init, SMNNIP conservation check |
| `smnnip_engine_mandos.py` | SMNNIP stub — domain: system state integrity |

---

## Wiring

Mandos is started by Aule at boot via `Aule/aule_wiring.py`:

```python
from Mandos.mandos import start as mandos_start, register_aule_init
mandos_start()
register_aule_init(lambda state: _aule_cold_init(state))
```

All other Faces wire to Mandos implicitly — `ErrorHandler._mandos_intercept()` calls `Mandos.accept_dead()` automatically on every FATAL before GC runs. No Face needs to call Mandos directly.

---

## Error Codes

| Code | Class | Condition |
|---|---|---|
| PTL_906 | `MandosRestoreFailed` | Checkpoint found, deserialization failed |
| PTL_907 | `SupervisorRestartBudgetExceeded` | Aule N/T restart ceiling hit |
| PTL_908 | `MandosStoreWriteFailed` | Could not write checkpoint before GC |
| PTL_909 | `AuleWatchdogTimeout` | Aule declared dead, Mandos gains priority |
| PTL_910 | `WorldBreak` | Mandos FATAL — kernel panic, sys.exit(1) |

---

## PTL_910 Kernel Panic Message

> *Great is the Fall of Gondolin: love not too well the work of thy hands and the devices of thy heart; and remember that the true hope of the Noldor lieth in the West and cometh from the Sea.*

---

## Related

- [Aule](Aule) — supervisor, repair authority, hands dead Faces to Mandos
- [Pharos](Pharos) — system bus, last Face standing in safe mode
- [docs/ErrorCatalog.md](../docs/ErrorCatalog.md) — PTL_906–910
