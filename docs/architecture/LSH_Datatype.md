# LSH_Datatype — 12-Layer Spectral Word Record

`Callimachus/v09/core/lsh_datatype.py`

---

## Overview

LSH_Datatype is the canonical word record format for the entire Ptolemy system. Every word that passes through Ptolemy — acquired, inferred, or generated — becomes an LSH_Datatype record. It has 12 layers, each representing a different spectral dimension of the word.

"LSH" = Locality-Sensitive Hashing. The datatype carries the hash coordinates used by PtolBrain to resolve word identity without exact string matching.

---

## 12 Layers

| # | Layer | Writable by | Description |
|---|---|---|---|
| 0 | `word_surface` | Acquisition only | The raw string as encountered |
| 1 | `canonical_form` | Acquisition only | Normalised form (lowercase, stripped) |
| 2 | `pos_primary` | Acquisition only | Primary part of speech (noun, verb, …) |
| 3 | `pos_secondary` | Acquisition only | Secondary POS (transitive, modal, …) |
| 4 | `etymology` | Acquisition only | Language family, root, borrowing chain |
| 5 | `definition_core` | Acquisition only | Core dictionary definition |
| 6 | `definition_ext` | AI-writable | Extended definition, usage notes |
| 7 | `semantic_vector` | AI-writable | Semantic embedding (LSH hash coords) |
| 8 | `relational_graph` | AI-writable | Synonyms, antonyms, co-occurrence graph |
| 9 | `contextual_usage` | AI-writable | Usage examples, register, domain |
| 10 | `spectral_tone` | AI-writable | Demotic Unicode Tag glyph (U+E0000 block) |
| 11 | `cross_lang_bridge` | AI-writable | Translation equivalents, calques |

**Acquisition-only** layers (0–5) are set once by the acquisition pipeline and never overwritten. **AI-writable** layers (6–11) are written by Ptolemy during inference and enrichment.

---

## Rabies Principle

`first_encountered` is permanently immutable after first set. This is the Rabies Principle — enforced at three levels:

1. **Python:** `__setattr__` override raises `RabiesViolation` on any write attempt
2. **SQLite:** `BEFORE UPDATE` trigger rejects any row that modifies `first_encountered`
3. **C++:** `const` field in Ptolemy++ (when compiled)

Error code: `PTL_504 RabiesViolation` — FATAL, no GC.

```python
record = LSH_Datatype("ptolemy")
record.first_encountered  # set on first acquisition — immutable forever

# This raises RabiesViolation:
record.first_encountered = "2026-01-01"  # PTL_504
```

---

## HyperWebster Address

Every LSH_Datatype record has a HyperWebster label — the SHA-256 of the Horner bijection address of `word_surface`. This label is the PRIMARY KEY in HyperDatabase.

```python
from Callimachus.v09.core.hyperwebster import HyperWebster
from Callimachus.v09.core.lsh_datatype import LSH_Datatype

hw = HyperWebster()
record = hw.index("ptolemy")
# record.label   → 64-char SHA-256 hex (stable PRIMARY KEY)
# record.payload → base-N coordinate string

datatype = LSH_Datatype(word_surface="ptolemy", label=record.label)
```

---

## Incomplete Flagging

Any acquisition layer that returns `None` is recorded in `resonance.learning_source` as:

```
__incomplete__:field,field,...
```

No Claude/LLM gap-fill in the first acquisition pass. Incomplete records are retried on next acquisition run. The `resume` flag in `acquire.py` skips complete records (default on).

---

## Spectral Tone Layer

Layer 10 (`spectral_tone`) stores a demotic Unicode Tag glyph from the U+E0000 block. This is a single invisible Unicode character encoding the semantic "tone" of the word — used by PtolemyTongue (FoldGeometry) as a weighting signal.

The Tag block characters are invisible in all standard renderers. They survive round-trips through JSON, SQLite, and most APIs.

---

## Storage Schema (SQLite)

```sql
CREATE TABLE words (
    label       TEXT PRIMARY KEY,   -- SHA-256 HW address
    payload     TEXT,               -- base-N coordinate string
    word_surface        TEXT,
    canonical_form      TEXT,
    pos_primary         TEXT,
    pos_secondary       TEXT,
    etymology           TEXT,
    definition_core     TEXT,
    definition_ext      TEXT,
    semantic_vector     TEXT,       -- JSON array
    relational_graph    TEXT,       -- JSON object
    contextual_usage    TEXT,
    spectral_tone       TEXT,       -- single U+E0000 char
    cross_lang_bridge   TEXT,
    first_encountered   TEXT,       -- IMMUTABLE after first set
    learning_source     TEXT        -- acquisition source + __incomplete__ flags
);

CREATE TRIGGER protect_first_encountered
BEFORE UPDATE ON words
WHEN OLD.first_encountered IS NOT NULL
BEGIN
    SELECT RAISE(ABORT, 'PTL_504: RabiesViolation — first_encountered is immutable');
END;
```

---

## Usage

```python
from Callimachus.v09 import Callimachus

cal = Callimachus(db_path, hw_root)

# Store a word
cal.put("ptolemy", lsh_datatype_obj)

# Retrieve by word surface
record = cal.get("ptolemy")

# Check existence
if cal.exists("ptolemy"):
    ...

# Acquire (single word, inline)
record = cal.acquire("ptolemy")
```

---

## Dependencies

- `sqlite3` (stdlib)
- `hashlib` (Horner SHA-256)
- `lxml` (Wiktionary parsing in acquisition)
- `requests` (Free Dictionary API, Datamuse)
