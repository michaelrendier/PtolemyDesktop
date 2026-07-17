# Callimachus v09 — HyperWebster, HyperDatabase, LSH_Datatype

`Callimachus/v09/`

---

## Overview

Callimachus v09 is the canonical Callimachus implementation. It replaces `Database.py` (MySQL stub — retired). Three primary systems: HyperWebster (bijective addressing), HyperDatabase (SQLite), and LSH_Datatype (12-layer word record). Named for Callimachus of Cyrene, who created the Pinakes — the first library catalogue.

---

## Module Structure

```
Callimachus/v09/
├── core/
│   ├── charset.py           ← PUBLIC_CHARSET — Unicode 15.1, 97-char Basic Latin
│   ├── hyperwebster.py      ← Horner bijection addressing engine
│   └── lsh_datatype.py      ← LSH_Datatype — 12-layer spectral word record
├── acquire/
│   └── acquire.py           ← Batch acquisition pipeline
├── database/
│   └── hyperdatabase.py     ← SQLite wrapper — label as PRIMARY KEY
├── gallery/
│   └── hypergallery.py      ← HyperGallery — image addressing via HW
└── __init__.py              ← Callimachus(db_path, hw_root) — top-level API
```

---

## Public API

```python
from Callimachus.v09 import Callimachus

db_path = '/path/to/ptolemy.db'
hw_root = '/path/to/hyperwebster/'

cal = Callimachus(db_path, hw_root)

# Index a word → HyperWebster record
hw_record = cal.index("ptolemy")

# Get the HW label of a word
label = cal.label_of("ptolemy")      # 64-char SHA-256 hex

# Retrieve by word surface
record = cal.get("ptolemy")          # → LSH_Datatype or None

# Store a record
cal.put("ptolemy", lsh_datatype_obj)

# Full acquisition pipeline (one word)
record = cal.acquire("ptolemy")

# Gallery (image addressing)
gallery = cal.gallery("ptolemy")
```

---

## HyperWebster Addressing

Bijective base-N addressing via Horner's method. Every string over the PUBLIC_CHARSET has exactly one integer address. No collisions. No hash truncation.

```
string  →  Horner accumulation  →  integer  →  SHA-256  →  label (64 hex chars)
```

The **label** is the PRIMARY KEY everywhere. The **payload** (base-N encoded integer) is stored for coordinate-space regeneration only.

```python
from Callimachus.v09.core.hyperwebster import HyperWebster

hw = HyperWebster()
record = hw.index("ptolemy")

record.label    # 64-char SHA-256 hex — stable PRIMARY KEY
record.payload  # base-N coordinate string — regeneration only
record.length   # character count
```

**Permutation = cryptographic key:**
- `PUBLIC_CHARSET` (Unicode codepoint order) → public addressing
- Any other codepoint order → private addressing (Kryptos manages permutations)

---

## PUBLIC_CHARSET

97-character Unicode 15.1 Basic Latin subset. Defined in `core/charset.py`.

The charset order determines the Horner base and all address computations. It is frozen — changing it would invalidate the entire database. Kryptos KCF-1 derives private charsets (permutations of PUBLIC_CHARSET) for encrypted addressing.

---

## HyperDatabase

SQLite wrapper. Three reads maximum to any word. No ORM, no MySQL, no joins.

```python
from Callimachus.v09.database.hyperdatabase import HyperDatabase

with HyperDatabase("ptolemy.db") as db:
    # Write
    db.put(hw_record, lsh_datatype_obj)   # INSERT OR REPLACE

    # Read
    exists = db.exists(label)             # SELECT COUNT — one read
    record = db.get(label)                # SELECT — one read, JSON deserialize

    # Iterate
    for label, record in db.iter_all():   # full scan
        ...
```

Primary key: HyperWebster label (64-char SHA-256 hex). No foreign keys. Schema is in `LSH_Datatype` — see `docs/architecture/LSH_Datatype.md`.

---

## Acquisition Pipeline

`Callimachus/v09/acquire/acquire.py` — batch pipeline. Sources in priority order:

1. Free Dictionary API
2. Datamuse
3. Wiktionary (lxml — performance locked)
4. Wikipedia (optional, `--wikipedia` flag)

Flags:
- `--resume` (default on): skips words with complete records
- `--wikipedia`: enable Wikipedia source
- `--incomplete`: retry only `__incomplete__` records

**Incomplete flagging:** Any layer returning `None` is noted in `resonance.learning_source` as `__incomplete__:field1,field2`. No LLM gap-fill in first pass.

For inline (per-inference) acquisition: `Philadelphos/LSH_Datatype_parser/acquire_inline.py`.

---

## HyperGallery

Image addressing via HyperWebster. Associates image files with their HW label:

```python
from Callimachus.v09.gallery.hypergallery import HyperGallery

gallery = HyperGallery(hw_root)
gallery.store("ptolemy", image_path)
entry = gallery.get("ptolemy")
```

Images are indexed by the HW label of their filename (or associated word). Used by Mouseion face for visual word associations.

---

## Migration from Database.py

`Database.py` is retired. In `Ptolemy3.py`:

```python
# OLD (retired):
from Callimachus.Database import Database
self.db = Database(parent=self)

# NEW (v09):
from Callimachus.v09 import Callimachus as _CallimachusV09
_db_path = os.path.join(self.homeDir, 'Callimachus', 'data', 'ptolemy.db')
_hw_root = os.path.join(self.homeDir, 'Callimachus', 'data', 'hyperwebster')
self.db = _CallimachusV09(_db_path, _hw_root)
```

`self.db` attribute name is preserved for backward compatibility with `DBControlPanel` and any Face that accesses `Ptolemy.db`.

---

## Settings

`Callimachus/settings/settings.json`

| Key | Default | Description |
|---|---|---|
| `db_backend` | `hyperdatabase` | `hyperdatabase` / `sqlite` / `postgres` |
| `audit_chain_port` | `5010` | PtolChain node port |
| `hyperwebster_shard_dir` | `data/hyperwebster/` | Word shard root |
| `blockchain_enabled` | `true` | PtolChain active flag |

---

## Dependencies

- `sqlite3` (stdlib)
- `lxml` (Wiktionary parsing)
- `requests` (Free Dictionary API, Datamuse)
- `hashlib` (Horner SHA-256)
- `Pharos.PtolBus` (acquire event publishing)
- `Aule` (stream_event shim — zero coupling)
