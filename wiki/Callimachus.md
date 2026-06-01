# Callimachus

**Historical figure:** Callimachus of Cyrene — head of the Library of Alexandria, creator of the *Pinakes* (first library catalogue)  
**Responsibility:** Archival, database, HyperWebster acquisition, blockchain audit trail

---

## Overview

Callimachus is Ptolemy's archival and database Face. It owns the HyperWebster lexical addressing system, the LSH_Datatype word record format, the HyperDatabase (SQLite), and the PtolChain blockchain audit trail. Named for the scholar who catalogued the entire Library of Alexandria.

---

## Module Tree

```
Callimachus/
├── v09/                          ← Current canonical version
│   ├── core/
│   │   ├── charset.py            ← PUBLIC_CHARSET — Unicode 15.1, 97-char Basic Latin
│   │   ├── hyperwebster.py       ← Horner bijection addressing engine
│   │   └── lsh_datatype.py       ← LSH_Datatype — 12-layer spectral word record
│   ├── acquire/
│   │   └── acquire.py            ← Batch acquisition pipeline
│   ├── database/
│   │   └── hyperdatabase.py      ← SQLite wrapper, HW label as PRIMARY KEY
│   └── gallery/
│       └── hypergallery.py       ← HyperGallery — image addressing via HW
├── BlockChain/
│   ├── PtolChain/                ← Canonical blockchain (use this)
│   │   ├── Block.py, Chain.py    ← Core chain
│   │   ├── Node.py               ← Flask node with /audit endpoint
│   │   └── Config.py             ← Settings-driven, Face branch ports
│   └── JackCoin/                 ← Legacy (do not use — superseded by PtolChain)
├── HyperWebster-Data-Storage/    ← Legacy HW experiments (pre-v09)
└── Database.py                   ← DEPRECATED — retire, replace with HyperDatabase
```

---

## HyperWebster Addressing

Every string over the PUBLIC_CHARSET has a unique integer address via Horner's method (bijective base-N).

```
string → Horner accumulation → integer → SHA-256 → label (64 hex chars)
```

The **label** is the PRIMARY KEY used everywhere. The **payload** (base-N encoded integer) is stored for regeneration only.

```python
from Callimachus.v09.core.hyperwebster import HyperWebster

hw = HyperWebster()
record = hw.index("ptolemy")
# record.label   → 64-char SHA-256 hex (stable primary key)
# record.payload → base-N coordinate string (for regeneration)
# record.length  → character count
```

**Permutation = cryptographic key.** `PUBLIC_CHARSET` (Unicode codepoint order) = public addressing. Any other order = private addressing. Kryptos owns permutation management.

---

## LSH_Datatype

12-layer spectral word record. The word datatype for the entire Ptolemy system.

| Layer | Name | Writable |
|---|---|---|
| 0 | `word_surface` | Acquisition only |
| 1 | `canonical_form` | Acquisition only |
| 2 | `pos_primary` | Acquisition only |
| 3 | `pos_secondary` | Acquisition only |
| 4 | `etymology` | Acquisition only |
| 5 | `definition_core` | Acquisition only |
| 6 | `definition_ext` | AI-writable |
| 7 | `semantic_vector` | AI-writable |
| 8 | `relational_graph` | AI-writable |
| 9 | `contextual_usage` | AI-writable |
| 10 | `spectral_tone` | AI-writable (demotic Unicode Tag glyph) |
| 11 | `cross_lang_bridge` | AI-writable |

**Rabies Principle:** `first_encountered` is permanently immutable after first set. Enforced at three levels: Python `__setattr__`, SQLite BEFORE UPDATE trigger, C++ `const` (Ptolemy++).

`RabiesViolation` error code: `PTL_504` — FATAL, no GC.

---

## HyperDatabase

SQLite wrapper. HyperWebster label is PRIMARY KEY. No ORM, no MySQL, no silent failures.

```python
from Callimachus.v09.database.hyperdatabase import HyperDatabase

with HyperDatabase("ptolemy.db") as db:
    db.put(hw_record, lsh_datatype)   # INSERT OR REPLACE
    exists = db.exists(label)          # SELECT COUNT — one read
    record = db.get(label)             # SELECT — one read, deserialize JSON
```

Three reads max to any word. No joins, no foreign keys.

---

## Acquisition Pipeline

`Callimachus/v09/acquire/acquire.py` — batch pipeline.  
`Philadelphos/LSH_Datatype_parser/acquire_inline.py` — inline two-pass pipeline.

Sources in order:
1. Free Dictionary API
2. Datamuse
3. Wiktionary (lxml — performance locked)
4. Wikipedia (optional, `--wikipedia` flag)

Resume on by default — skips complete records. Retries `__incomplete__` records.

**Incomplete flagging:** Any acquisition layer that returns `None` is recorded in `resonance.learning_source` as `__incomplete__:field,field`. No Claude/LLM gap-fill in first pass.

---

## PtolChain (Canonical Blockchain)

All Face audit trails use PtolChain. JackCoin variants are legacy — do not use.

```python
from Callimachus.BlockChain.PtolChain import AuditChain

chain = AuditChain(face="Callimachus")
chain.log({"event": "word_acquired", "word": "ptolemy"})
```

Each Face runs its own branch. Node ports are settings-driven (`Config.py`). `/audit` endpoint on each node for external inspection.

---

## Settings

`Callimachus/settings/settings.json`

| Key | Description |
|---|---|
| `db_backend` | `hyperdatabase` / `sqlite` / `postgres` |
| `audit_chain_port` | PtolChain node port (default 5010) |
| `hyperwebster_shard_dir` | Word shard root directory |
| `blockchain_enabled` | PtolChain active flag |

---

## Dependencies

- sqlite3 (stdlib)
- lxml (Wiktionary parsing)
- requests (API fetchers)
- hashlib (Horner SHA-256)
- Pharos/PtolBus (acquire event publishing)
- Aule (stream_event shim — zero-coupling)
