#!/usr/bin/env python3
"""
Callimachus v0.9 — Secondary Core
===================================
All data I/O in Ptolemy routes through Callimachus.
No Face touches storage directly.

Public API:
  Callimachus(db_path, output_root)
    .index(text)           → IndexRecord
    .label_of(text)        → str (SHA-256 hex label)
    .get(label)            → LSH_Datatype | None
    .put(record, lsh)      → None
    .exists(label)         → bool
    .acquire(word, ...)    → LSH_Datatype
    .acquire_batch(words)  → dict (stats)
    .gallery(spec)         → HyperGallery
    .master_index          → HyperIndex
    .charset_info()        → str
    .db_stats()            → dict

Unicode Standard : 15.1
Wire Encoding    : UTF-8
Charset Order    : Unicode codepoint (public) | permutation-supplied (private/Kryptos)
Database         : SQLite via HyperDatabase (Database.py retired)
"""

from .core.charset      import describe_charset, validate_text
from .core.hyperwebster import HyperWebster, IndexRecord
from .core.lsh_datatype import LSH_Datatype
from .database.hyperdatabase import HyperDatabase
from .gallery.hypergallery   import HyperGallery, HyperIndex, ImageSpec, PixelMode
from .acquire.acquire        import acquire_word, acquire_wordlist

import os
from pathlib import Path
from typing  import Optional


class Callimachus:
    """
    Secondary Core. Single entry point for all Ptolemy data I/O.

    Parameters
    ----------
    db_path     : path to SQLite file (created on first open)
    output_root : root directory for JSON word shards
    charset     : None = PUBLIC_CHARSET (Unicode 15.1 codepoint order)
                  list  = private/cryptographic charset from Kryptos
    """

    VERSION = "0.9"

    def __init__(
        self,
        db_path:     str,
        output_root: str,
        charset:     Optional[list] = None,
    ):
        self._hw          = HyperWebster(charset)
        self._db          = HyperDatabase(db_path)
        self._output_root = Path(output_root)
        self._master_idx  = HyperIndex()
        self._output_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Addressing
    # ------------------------------------------------------------------

    def index(self, text: str) -> IndexRecord:
        """Index a string. Returns IndexRecord(label, payload, length, timestamp)."""
        return self._hw.index(text)

    def label_of(self, text: str) -> str:
        """Return SHA-256 label (primary key) for a string."""
        return self._hw.label_of(text)

    def validate(self, text: str) -> list:
        """Return list of out-of-charset characters. Empty = addressable."""
        return validate_text(text)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def exists(self, label: str) -> bool:
        return self._db.exists(label)

    def get(self, label: str) -> Optional[LSH_Datatype]:
        """Retrieve LSH_Datatype by label. None if not found."""
        return self._db.get(label)

    def put(self, record: IndexRecord, lsh: LSH_Datatype) -> None:
        """Store an LSH_Datatype record."""
        self._db.put(record, lsh)

    # ------------------------------------------------------------------
    # Acquisition
    # ------------------------------------------------------------------

    def acquire(
        self,
        word:      str,
        wikipedia: bool = False,
        force:     bool = False,
    ) -> LSH_Datatype:
        """Acquire a single word from all sources. Resume-by-default."""
        return acquire_word(
            word, self._hw, self._db,
            self._output_root, wikipedia, force
        )

    def acquire_batch(
        self,
        words:     list,
        wikipedia: bool = False,
        force:     bool = False,
    ) -> dict:
        """
        Acquire a list of words. Returns stats dict.
        Uses this instance's db and output_root.
        """
        import time
        stats = {"total": len(words), "complete": 0,
                 "incomplete": 0, "errors": 0}
        for word in words:
            try:
                lsh        = self.acquire(word, wikipedia, force)
                incomplete = any(lsh.get_layer(i) is None for i in range(6))
                stats["incomplete" if incomplete else "complete"] += 1
            except Exception as e:
                import logging
                logging.getLogger("callimachus").error(f"{word!r}: {e}")
                stats["errors"] += 1
        return stats

    # ------------------------------------------------------------------
    # Gallery
    # ------------------------------------------------------------------

    def gallery(self, spec: ImageSpec) -> HyperGallery:
        """Return a HyperGallery for the given ImageSpec."""
        return HyperGallery(spec)

    @property
    def master_index(self) -> HyperIndex:
        """The self-referential master HyperIndex for this Callimachus instance."""
        return self._master_idx

    # ------------------------------------------------------------------
    # Info
    # ------------------------------------------------------------------

    def charset_info(self) -> str:
        return describe_charset()

    def db_stats(self) -> dict:
        return {
            "total":      self._db.count(),
            "incomplete": self._db.count_incomplete(),
            "db_path":    str(self._db._path),
            "version":    self.VERSION,
        }

    def close(self) -> None:
        self._db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __repr__(self):
        return (f"Callimachus(v{self.VERSION}, "
                f"db={self._db._path}, "
                f"words={self._db.count()})")
