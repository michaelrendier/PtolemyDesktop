# CyclicContextBuffer — FIFO Sliding Window Context

`Philadelphos/cyclic_context_buffer.py`

---

## Overview

CyclicContextBuffer is Ptolemy's live context memory. It is a FIFO sliding window of conversation entries. When the buffer is full and a new entry arrives, the oldest entry is **evicted** — but eviction is confirmed only after three operations succeed in sequence:

1. **Compress** — L2 octonion projection of the entry
2. **Hyperindex** — octonion Noether-current address
3. **Blockchain commit** — AuditChain write

The entry is not removed from the buffer until all three succeed. No silent drops.

---

## Object Model

```
CyclicContextBuffer
└── EntryObject[]          ← FIFO deque, max BUFFER_SIZE_LINES
    ├── PromptObject        ← user input text + timestamp
    └── ResponseObject      ← Ptolemy output text + timestamp
```

```python
from Philadelphos.cyclic_context_buffer import (
    CyclicContextBuffer, PromptObject, ResponseObject
)

buf = CyclicContextBuffer(size_lines=100)
p = PromptObject("What is octonion multiplication?")
r = ResponseObject("Octonions are a non-associative normed division algebra...")
buf.append(p, r)
```

---

## Eviction Pipeline

On eviction (buffer full, new entry arrives):

```
EntryObject
  → entry.compress(model=COMPRESSION_MODEL)
        ↓ octonion_stub (default)
        → SHA-256 of full exchange
        → derive 8 octonion components (e0-e7)
        → normalise to [0,1) per component
        → JSON: {o: [e0..e7], p: head64, r: head64, t: ts}
  → entry.hyperindex(method=HYPERINDEX_METHOD)
        ↓ octonion → Noether current address
        → stable address for the entry in HyperWebster space
  → entry.blockchain_commit(chain=BLOCKCHAIN_BACKEND)
        ↓ AuditChain.log(entry.to_dict())
        → block hash stored on entry
  → entry removed from deque
```

**Confirmed eviction:** Entry stays in deque until all three steps succeed. If any step fails, the entry remains and is retried on the next cycle.

---

## Compression Model

Default: `octonion_stub`

```python
# octonion_stub compression:
raw = f"{p_text}|||{r_text}|||{timestamp}"
h   = hashlib.sha256(raw.encode()).hexdigest()
# Split into 8 × 8-hex segments → 8 octonion components e0-e7
# Sedenion dims e8-e15 deliberately excluded (volatile, order-dependent)
# Only the stable octonion core (e0-e7) is preserved
```

When Phase 5 SMIP is wired: replace `octonion_stub` with `smip` — the real sedenion→octonion projection via ValaQuenta. The module hook (`COMPRESSION_MODEL` setting) makes this a drop-in swap.

---

## Hyperindex

Default: `octonion` method.

The 8-component octonion vector from compression is used as an address in HyperWebster space. The hyperindex is the SHA-256 of the normalised octonion components — a stable, collision-resistant address for the context entry.

This address is used by PtolBrain to locate related past context during inference.

---

## Shared Context (CH_CONTEXT)

The kernel owns the CCB at `Ptolemy.ccb`. On every `append()`, the kernel calls:

```python
bus.broadcast_context_update(entry)
```

This publishes on `CH_CONTEXT`. All subscribed Faces receive the new context entry in real-time. The CCB itself lives in Ptolemy (kernel scope) — not in any Face.

---

## Settings (Module Hooks)

All settings are module hooks — each becomes a Settings tab entry in `PtolemySettingsWindow`.

| Hook | Default | Swap target |
|---|---|---|
| `BUFFER_SIZE_LINES` | `100` | Any integer |
| `COMPRESSION_MODEL` | `octonion_stub` | `smip` (Phase 5) |
| `HYPERINDEX_METHOD` | `octonion` | Any SMIP layer |
| `BLOCKCHAIN_BACKEND` | `branch` | Any PtolChain variant |

Settings file: `Philadelphos/settings/cyclic_context_buffer/settings.json`

---

## EntryObject Lifecycle

```
append(prompt, response)
    → create EntryObject
    → if len(deque) >= BUFFER_SIZE_LINES:
          oldest = deque[0]
          oldest.compress()        # step 1
          oldest.hyperindex()      # step 2
          oldest.blockchain_commit()  # step 3
          deque.popleft()          # only if all 3 succeed
    → deque.append(new_entry)
```

**No index manipulation during iteration.** The deque is never modified while being read. All reads get a snapshot copy.

---

## Dependencies

- `collections.deque` (stdlib — FIFO)
- `hashlib` (octonion compression)
- `Callimachus.BlockChain.PtolChain.AuditChain` (blockchain backend)
- `Pharos.PtolBus` (`CH_CONTEXT` broadcast)
