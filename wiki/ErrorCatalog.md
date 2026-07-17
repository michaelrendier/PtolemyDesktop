# Ptolemy Error Catalog

**Source:** `Pharos/luthspell_error_handler.py`  
**Handler:** `ErrorHandler` class — all errors route through `handler.handle(error)`  
**GC:** `GarbageCollector` — triggered automatically when `error.gc_trigger = True`  
**Log:** `PtolDmesg` — ErrorHandler writes via `dmesg.error()` / `dmesg.fatal()`

---

## Error Handler Requirements and Expectations

### Wiring Requirement

Every Face **must** wire the ErrorHandler on spawn:

```python
from Pharos.luthspell_error_handler import ErrorHandler, GarbageCollector
from Pharos.PtolDmesg import dmesg

gc      = GarbageCollector()
handler = ErrorHandler(gc=gc, on_error=lambda e: dmesg.error(FACE_NAME, str(e)))
```

All registered objects must call `gc.register(self)` on init and `gc.release(self)` on clean teardown.

### Severity Levels

| Level | Value | Meaning |
|---|---|---|
| `INFO` | 0 | Nominal — logged only |
| `WARN` | 1 | Degraded, continuing |
| `ERROR` | 2 | Failure, recovery attempted |
| `FATAL` | 3 | Unrecoverable — halt or GC |

### GC Trigger Rules

- `gc_trigger = True` → `GarbageCollector.collect()` runs immediately after logging
- `gc_trigger = False` on FATAL → logical/integrity violation, GC would not help
- `PTL_504 RabiesViolation` is FATAL with `gc_trigger = False` — it is a **code error**, not a memory leak

### Expectations Per Face

Every Face must handle these error classes at minimum:

| Face | Required handling |
|---|---|
| **Pharos** | All PTL_1xx (bus), PTL_7xx (module), PTL_9xx (system) |
| **Callimachus** | PTL_4xx (blockchain), PTL_5xx (acquisition), PTL_3xx (buffer) |
| **Philadelphos** | PTL_2xx (LuthSpell), PTL_6xx (LSH), PTL_5xx (acquisition) |
| **Aule** | All — Aule receives escalations from all Faces |
| **Kryptos** | PTL_5xx (acquisition), PTL_6xx (LSH) |
| **All Faces** | PTL_701 ModuleNotWired, PTL_702 SettingsKeyMissing |

### Escalation Path

```
Face catches exception
  → wraps in PtolemyError subclass
  → handler.handle(error)
    → logs to PtolDmesg
    → GC if gc_trigger
    → on_error callback → Ptolemy root / Aule
      → Aule writes to PtolDmesg (sole writer)
      → Pharos/LuthSpell decides halt or redirect
```

---

## Error Catalog

### PTL_1xx — Bus

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_101 | `BusChannelNotFound` | WARN | ✗ | Message targets channel with no subscribers |
| PTL_102 | `BusMessageMalformed` | ERROR | ✗ | BusMessage missing fields or invalid payload |
| PTL_103 | `BusOverflow` | FATAL | ✓ | Queue full, T1 eviction failed |
| PTL_104 | `BusPriorityViolation` | ERROR | ✗ | Priority value outside T0/T1 range |
| PTL_105 | `BusDeadlock` | FATAL | ✓ | Circular wait in dispatch thread |

**Wiring requirement:** `PtolBus` publishes PTL_1xx to `CH_LOG` automatically. Faces do not catch bus errors directly — they arrive via `CH_LOG` subscription.

---

### PTL_2xx — LuthSpell

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_201 | `BoundaryNotSet` | WARN | ✗ | check() called before set_boundary() |
| PTL_202 | `HaltPassFailed` | FATAL | ✓ | halt_pass() could not write to blockchain |
| PTL_203 | `BoundaryCorrupted` | FATAL | ✓ | Boundary hash mismatch |
| PTL_204 | `InfiniteHaltLoop` | FATAL | ✓ | halt_pass() triggered from halt handler |
| PTL_205 | `RedirectFailed` | FATAL | ✓ | Ptolemy cannot redirect after halt |

**Wiring requirement:** LuthSpell must be wired before any inference. `LuthSpellNotWired` (PTL_903) fires if inference starts unwired.

---

### PTL_3xx — Buffer

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_301 | `BufferEvictionFailed` | ERROR | ✗ | CyclicContextBuffer could not free slot |
| PTL_302 | `BufferIntegrityViolation` | FATAL | ✓ | Context window checksum mismatch |
| PTL_303 | `BufferOverCapacity` | ERROR | ✗ | Write exceeds capacity, eviction disabled |
| PTL_304 | `CompressionFailed` | ERROR | ✗ | HyperWebster payload encoding failed |
| PTL_305 | `HyperindexFailed` | ERROR | ✗ | Horner bijection charset mismatch |

---

### PTL_4xx — Blockchain

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_401 | `BlockchainCommitFailed` | FATAL | ✓ | Block write failed |
| PTL_402 | `ChainIntegrityViolation` | FATAL | ✓ | Hash chain broken |
| PTL_403 | `GenesisBlockMissing` | FATAL | ✓ | Chain opened without genesis block |
| PTL_404 | `BranchOrphan` | ERROR | ✗ | Branch references unknown parent |

**Wiring requirement:** Callimachus initialises PtolChain on boot. PTL_403 on init = unrecoverable without manual repair.

---

### PTL_5xx — Acquisition

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_501 | `WordAcquisitionFailed` | WARN | ✗ | All sources returned empty |
| PTL_502 | `AcquisitionAPITimeout` | WARN | ✗ | API request timed out |
| PTL_503 | `WordRecordCorrupted` | ERROR | ✗ | JSON shard validation failed |
| PTL_504 | `RabiesViolation` | FATAL | ✗ | `first_encountered` write attempted — **code error** |
| PTL_505 | `SemanticWordBridgeFailed` | ERROR | ✗ | Cross-language bridge failed |

**PTL_504 special rule:** `first_encountered` is permanently immutable (Rabies Principle). Any write attempt after construction is a **programming error** — fix the code, do not catch and continue.

---

### PTL_6xx — LSH

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_601 | `MonadIsolationViolation` | FATAL | ✓ | WordMonad written from outside owning layer |
| PTL_602 | `InferenceCoordInvalid` | ERROR | ✗ | Octonion coordinate out of bounds |
| PTL_603 | `LSHModelNotInitialized` | FATAL | ✗ | Inference before model weights loaded |
| PTL_604 | `GrammarNeuronFailed` | WARN | ✗ | Parser failed for this language |
| PTL_605 | `SelfAdjointViolation` | ERROR | ✗ | Hermitian/self-adjoint check failed |

---

### PTL_7xx — Module

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_701 | `ModuleNotWired` | ERROR | ✗ | Face called before wiring complete |
| PTL_702 | `SettingsKeyMissing` | ERROR | ✗ | Required key absent from settings.json |
| PTL_703 | `ModuleSwapFailed` | FATAL | ✓ | Hot-swap failed mid-operation |
| PTL_704 | `SettingsIntegrityViolation` | FATAL | ✗ | settings.json tampered after load |

---

### PTL_9xx — System

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_901 | `PtolemyNotInitialized` | FATAL | ✗ | Face called before Ptolemy root init |
| PTL_902 | `FaceNotFound` | ERROR | ✗ | import_face() cannot locate module |
| PTL_903 | `LuthSpellNotWired` | FATAL | ✗ | System op before LuthSpell.wire() |
| PTL_999 | `UnknownError` | FATAL | ✓ | Unclassified exception — wraps any non-PtolemyError |

---

## Adding New Error Codes

1. Subclass `PtolemyError` in `luthspell_error_handler.py`
2. Assign next sequential code in the correct range
3. Set `severity` and `gc_trigger` explicitly
4. Add docstring describing the condition
5. Add to this catalog
6. Add to `docs/ErrorCatalog.md` Wiki page

**Never reuse a code.** Retired codes must remain as comments.

