# Blockchain — PtolChain AuditChain

`Callimachus/BlockChain/PtolChain/`

---

## Overview

PtolChain is Ptolemy's canonical blockchain. All Face audit trails use PtolChain. The JackCoin variants (`JackCoin/`, `JackCoin5001/`, `JackCoin5002/`, `JackCoin5003/`) are legacy — do not use.

Each Face runs its own branch. Node ports are settings-driven. Every Face can expose its chain via the `/audit` Flask endpoint.

---

## Module Structure

```
Callimachus/BlockChain/PtolChain/
├── Block.py        ← Block: index, timestamp, data, prev_hash, hash, nonce
├── Chain.py        ← Chain: validity checks, save/load, block lookup
├── Node.py         ← Flask node — /audit endpoint, peer sync
└── Config.py       ← Settings-driven port and Face branch configuration
```

---

## Block

Each block contains:

| Field | Type | Description |
|---|---|---|
| `index` | int | Sequential block number |
| `timestamp` | float | `time.time()` at creation |
| `data` | dict | Arbitrary payload (event dict) |
| `prev_hash` | str | SHA-256 of previous block |
| `hash` | str | SHA-256 of this block (computed) |
| `nonce` | int | Proof-of-work nonce (lightweight) |

Block hash = SHA-256 of `f"{index}{timestamp}{data}{prev_hash}{nonce}"`.

---

## Chain Validity

`Chain.is_valid()` checks three conditions for every block pair:

1. Blocks are indexed consecutively (`prev.index + 1 == cur.index`)
2. Each block's hash is internally valid (`cur.is_valid()`)
3. Each block's `prev_hash` matches the actual hash of the previous block

```python
from Callimachus.BlockChain.PtolChain.Chain import Chain

chain = Chain(blocks)
assert chain.is_valid()
```

---

## AuditChain API

```python
from Callimachus.BlockChain.PtolChain import AuditChain

# One chain per Face branch
chain = AuditChain(face="Callimachus")

# Log an event
chain.log({"event": "word_acquired", "word": "ptolemy", "label": "abc123"})

# Log a halt record (LuthSpell)
chain.log(halt_record.to_dict())

# Log context eviction (CyclicContextBuffer)
chain.log(entry.to_dict())

# Verify chain integrity
assert chain.is_valid()

# Expose via /audit endpoint
chain.serve(port=5010)  # Flask node
```

---

## Face Branch Ports

Each Face has its own PtolChain branch. Default ports:

| Face | Branch | Default Port |
|---|---|---|
| Callimachus | `callimachus` | 5010 |
| LuthSpell | `luthspell` | 5011 |
| Philadelphos | `philadelphos` | 5012 |
| Aule | `aule` | 5013 |
| Kryptos | `kryptos` | 5014 |
| Pharos | `pharos` | 5015 |

All ports are settings-driven (`Config.py`). Override in `Callimachus/settings/settings.json`.

---

## /audit Endpoint

Each node exposes `/audit` (Flask GET):

```
GET http://localhost:5010/audit
→ [
    {"index": 0, "timestamp": ..., "data": {...}, "hash": "...", "prev_hash": ""},
    {"index": 1, ...},
    ...
  ]
```

External audit tools hit this endpoint to verify chain integrity without touching the local filesystem.

---

## Who Writes to the Chain

| Writer | Event type |
|---|---|
| Callimachus acquisition | `word_acquired`, `word_updated`, `word_incomplete` |
| LuthSpell | `boundary_set`, `halt_record`, `redirect_issued` |
| CyclicContextBuffer | `context_evicted` (with octonion hyperindex address) |
| Interface.py | `gui_menu_open` (via `_chain_commit`) |
| KryptosVault | `secret_stored`, `secret_deleted` |
| Aule | `3fa_pass`, `3fa_fail`, `quarantine`, `sanitation_event` |

---

## Chain Persistence

`Chain.self_save()` iterates all blocks and calls `Block.self_save()`. Each block is written to disk as a JSON file in the Face branch directory:

```
Callimachus/BlockChain/PtolChain/data/callimachus/
├── block_000000.json
├── block_000001.json
└── ...
```

On startup, `AuditChain.__init__()` loads all block files in index order and validates the chain.

---

## Why PtolChain (not JackCoin)

JackCoin was the original proof-of-concept. PtolChain adds:
- Per-Face branch separation
- Settings-driven port configuration
- `/audit` Flask endpoint for external inspection
- `AuditChain` wrapper class (high-level API)
- Proper `first_encountered` immutability at chain level (supports Rabies Principle enforcement)

JackCoin variants in `JackCoin/`, `JackCoin5001-5003/` are retained for reference only. Do not add new functionality there.
