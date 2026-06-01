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

---

### PTL_1xx additions

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_106 | `BusQueueFull` | ERROR | ✓ | `queue.Full` during bus put — subscriber not consuming |
| PTL_107 | `BusDispatchFailed` | ERROR | ✗ | Unhandled exception during dispatch to subscriber |

---

### PTL_2xx additions

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_206 | `PrioritySchemeNotWired` | ERROR | ✗ | PRIORITY_SCHEME value has no implementation in luthspell.py |

---

### PTL_3xx additions

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_306 | `CompressionModelNotWired` | ERROR | ✗ | Compression model name not implemented |
| PTL_307 | `HyperindexMethodNotWired` | ERROR | ✗ | Hyperindex method name not implemented |
| PTL_308 | `BufferCommitOutOfOrder` | ERROR | ✗ | commit() before compress()/hyperindex() — sequencing violation |

---

### PTL_5xx additions

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_506 | `AcquisitionSourceParseError` | WARN | ✗ | Per-source parse failure during acquisition |

---

### PTL_7xx additions

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_705 | `SettingsValidationError` | ERROR | ✗ | Settings value failed validation — wrong type or out of range |

---

### PTL_8xx — I/O and System Resources *(new range)*

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_801 | `DmesgWriteFailed` | WARN | ✗ | PtolDmesg OSError/PermissionError on log write |
| PTL_802 | `FaceImportFailed` | ERROR | ✗ | Face found but failed to import — syntax or dependency error |
| PTL_803 | `ContextPersistFailed` | ERROR | ✗ | context_manager FileNotFoundError or JSONDecodeError |
| PTL_804 | `ForgeJobFailed` | ERROR | ✓ | forge_queue subprocess failed or timed out |
| PTL_805 | `ShellCommandFailed` | WARN | ✗ | PtolShell command raised unhandled exception |

---

### PTL_9xx additions — Mandos supervisor codes

| Code | Class | Sev | GC | Description |
|---|---|---|---|---|
| PTL_906 | `MandosRestoreFailed` | FATAL | ✗ | Checkpoint found, deserialization failed — cold boot required |
| PTL_907 | `SupervisorRestartBudgetExceeded` | FATAL | ✗ | Aule N/T restart ceiling hit — Face enters Mandos |
| PTL_908 | `MandosStoreWriteFailed` | FATAL | ✗ | Could not serialize checkpoint before GC — state lost |
| PTL_909 | `AuleWatchdogTimeout` | FATAL | ✗ | Mandos declares Aule dead — gains supervisor priority |
| PTL_910 | `WorldBreak` | FATAL | ✗ | Mandos FATAL — final PtolChain write, kernel panic, sys.exit(1) |

**PTL_910 kernel panic message is fixed and verbatim. See `Mandos/mandos.py:world_break()`.**

---

## Wiring Template (all Faces)

```python
from Pharos.luthspell_error_handler import ErrorHandler, GarbageCollector
from Pharos.PtolDmesg import dmesg

gc      = GarbageCollector()
handler = ErrorHandler(
    gc=gc,
    face_name=FACE_NAME,
    on_error=lambda e: dmesg.error(FACE_NAME, str(e)),
    get_state_fn=lambda: self.get_checkpoint_state(),  # optional but recommended
)
gc.register(self)
```

`get_state_fn` is called automatically before GC on any FATAL — result is checkpointed to Mandos.
If omitted, Mandos receives an empty state dict plus the fatal error record.

---

## Total: 55 typed PTL errors across 9 ranges (PTL_904, PTL_905 reserved)

