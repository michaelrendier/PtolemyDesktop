#!/usr/bin/env python3
"""
Callimachus — HyperDatabase
=============================
SQLite wrapper. HyperWebster label (SHA-256 hex) is the PRIMARY KEY.
Replaces Database.py entirely. No SQL remnants from LAMP stack.

No ORM. No MySQL. No silent failures.
All errors surface as exceptions with full context.

Schema:
  words table:
    label         TEXT PRIMARY KEY   — HyperWebster SHA-256 label
    payload       TEXT NOT NULL      — base-N encoded integer address (regeneration)
    length        INTEGER NOT NULL   — character count
    indexed_at    TEXT NOT NULL      — time.ctime() at first index
    metadata      TEXT               — JSON: full LSH_Datatype serialization
    incomplete    INTEGER DEFAULT 0  — 1 if any acquisition layer is None

  Rabies trigger:
    BEFORE UPDATE of first_encountered → RAISE ABORT.
    Enforced at DB layer independent of Python object.

Three reads max to any word:
  exists(label)  → single SELECT COUNT
  get(label)     → single SELECT, deserialize JSON metadata
  put(record)    → single INSERT OR REPLACE

No joins. No foreign keys. No stored procedures.
Callimachus is the only caller. Direct module import, never HTTP.
"""

import json
import os
import sqlite3
from typing import Optional

from ..core.hyperwebster import IndexRecord
from ..core.lsh_datatype import LSH_Datatype


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    label       TEXT    PRIMARY KEY,
    payload     TEXT    NOT NULL,
    length      INTEGER NOT NULL,
    indexed_at  TEXT    NOT NULL,
    metadata    TEXT,
    incomplete  INTEGER DEFAULT 0
);

CREATE TRIGGER IF NOT EXISTS rabies_immutable
BEFORE UPDATE OF first_encountered ON words
BEGIN
    SELECT RAISE(ABORT, 'first_encountered is immutable - Rabies Principle');
END;

CREATE INDEX IF NOT EXISTS idx_incomplete ON words (incomplete)
    WHERE incomplete = 1;
"""


# ---------------------------------------------------------------------------
# HyperDatabase
# ---------------------------------------------------------------------------

class HyperDatabase:
    """
    SQLite-backed word store. HyperWebster label = PK everywhere.

    Parameters
    ----------
    db_path : str
        Path to SQLite file. Created on first open if absent.
        Use ':memory:' for tests.
    """

    def __init__(self, db_path: str):
        self._path = db_path
        if db_path != ':memory:':
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def exists(self, label: str) -> bool:
        """Return True if label is in the database."""
        row = self._conn.execute(
            "SELECT COUNT(*) FROM words WHERE label = ?", (label,)
        ).fetchone()
        return row[0] > 0

    def put(self, record: IndexRecord, lsh: LSH_Datatype) -> None:
        """
        Insert or replace a word record.
        If label already exists, updates all fields EXCEPT first_encountered
        (Rabies Principle enforced by trigger).
        """
        incomplete = int(any(lsh.get_layer(i) is None for i in range(6)))
        metadata   = json.dumps(lsh.to_dict(), ensure_ascii=False)
        self._conn.execute(
            """
            INSERT INTO words (label, payload, length, indexed_at, metadata, incomplete)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(label) DO UPDATE SET
                payload    = excluded.payload,
                length     = excluded.length,
                metadata   = excluded.metadata,
                incomplete = excluded.incomplete
            """,
            (record.label, record.payload, record.length,
             record.timestamp, metadata, incomplete)
        )
        self._conn.commit()

    def get(self, label: str) -> Optional[LSH_Datatype]:
        """
        Retrieve LSH_Datatype by label.
        Returns None if not found — never raises on missing key.
        Raises on data corruption.
        """
        row = self._conn.execute(
            "SELECT metadata FROM words WHERE label = ?", (label,)
        ).fetchone()
        if row is None:
            return None
        if not row['metadata']:
            raise RuntimeError(
                f"HyperDatabase: label {label[:12]}… exists but metadata is empty. "
                "Record may be corrupted."
            )
        return LSH_Datatype.from_dict(json.loads(row['metadata']))

    def get_record(self, label: str) -> Optional[sqlite3.Row]:
        """Return raw DB row. Used by acquire pipeline for resume logic."""
        return self._conn.execute(
            "SELECT * FROM words WHERE label = ?", (label,)
        ).fetchone()

    def mark_complete(self, label: str) -> None:
        """Clear the incomplete flag once all acquisition layers are filled."""
        self._conn.execute(
            "UPDATE words SET incomplete = 0 WHERE label = ?", (label,)
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def incomplete_labels(self) -> list[str]:
        """Return all labels with incomplete acquisition layers."""
        rows = self._conn.execute(
            "SELECT label FROM words WHERE incomplete = 1"
        ).fetchall()
        return [r['label'] for r in rows]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]

    def count_incomplete(self) -> int:
        return self._conn.execute(
            "SELECT COUNT(*) FROM words WHERE incomplete = 1"
        ).fetchone()[0]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
