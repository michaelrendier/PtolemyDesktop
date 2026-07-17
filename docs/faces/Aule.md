# Aulë

**Historical figure:** Aulë the Smith *(Ainulindalë / Tolkien)* — craftsman, forge-master, builder of the Dwarves  
**Responsibility:** Diagnostic forge, sandbox runner, stream monitor, code watch, audit trail

---

## Overview

Aulë is Ptolemy's diagnostic and experimental Face. It monitors all system event streams, manages the forge queue (staged code execution), watches the `Aule/forge/` directory for new scripts, and writes all events to the AuditChain. It is the only Face with write access to PtolDmesg. Other Faces submit to Aulë; Aulë writes.

Full specification: `docs/Aule/Aule_Face_Documentation.docx`

---

## Module Tree

```
Aule/
├── aule.py               ← StreamMonitor, stream_event() shim, event router
├── aule_sanitation.py    ← 2FA/3FA gate, Aule-risk gate, trust levels 0–3
├── aule_shim.py          ← Zero-coupling shim — silent no-op if Aule not running
├── forge_queue.py        ← ForgeQueue — watches forge/, stages execution, AuditChain
└── forge/
    └── example_acquire_probe.py  ← Example forge probe script
```

---

## stream_event() Shim

Every Face uses the Aule shim for zero-coupling event emission:

```python
# In any Face:
try:
    from Aule.aule import stream_event as _emit
except ImportError:
    def _emit(channel, event_type, payload=None, **kwargs): pass

_emit("acquire", "word_fetched", {"word": "ptolemy", "sources": ["wiktionary"]})
```

If Aule is not running, `_emit` is a silent no-op. No errors, no dependencies.

---

## ForgeQueue

Watches `Aule/forge/` directory for new `.py` probe scripts. Stages execution through the trust gate, runs, and logs result to AuditChain.

```python
from Aule.forge_queue import ForgeQueue

fq = ForgeQueue(bus=ptol_bus)
fq.start_watch()   # begins watching Aule/forge/
```

Each script run produces an AuditChain entry: script name, result, timestamp, trust level.

---

## Trust Levels

Managed by `aule_sanitation.py`:

| Level | Description |
|---|---|
| 0 | Untrusted — sandboxed, no file I/O |
| 1 | Default — standard Ptolemy module access |
| 2 | Elevated — can write to Callimachus |
| 3 | Root — full system access (requires 3FA) |

2FA/3FA gate enforced before any Level 2+ operation.

---

## PtolDmesg

`Pharos/PtolDmesg.py` — system message log. **Aulë is the sole writer.** Faces submit events; Aulë validates, timestamps, and commits.

```python
# From any Face — submit, don't write directly:
_emit("system", "face_started", {"face": "Archimedes"})
# Aule receives this, validates trust level, writes to PtolDmesg
```

---

## Settings

`Aule/settings/settings.json`

| Key | Description |
|---|---|
| `forge_watch_interval_ms` | Forge directory poll interval |
| `audit_chain_enabled` | AuditChain logging active |
| `trust_level_default` | Default trust level for new scripts (0–3) |
| `fa_enabled` | 2FA/3FA gate active |

---

## Dependencies

- Pharos/PtolBus (event subscriber + publisher)
- Callimachus/BlockChain/PtolChain (AuditChain backend)
- Pharos/PtolDmesg (write target)
- watchdog or polling (forge/ directory watch)
