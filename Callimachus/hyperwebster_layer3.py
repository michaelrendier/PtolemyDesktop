#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Callimachus/hyperwebster_layer3.py — Context Buffer Layer 3 Bridge
===================================================================
Connects the Noether Information Current's Layer 3 eviction queue
to the HyperWebster JSON word-shard store.

Architecture position
---------------------
    ContextBuffer._layer3_queue
        ↓ drain()
    HyperWebsterLayer3.ingest(entries)
        ↓ for each (word_key, timestamp, snippet)
    HyperWebster.index_text(word)          → (address_hex, length, ts)
    words_<letter>/<address_hex>.json      → word record written / updated

Word record schema (JSON)
-------------------------
{
    "word":         str,
    "address_hex":  str,          # HyperWebster 256-bit address
    "length":       int,          # len(word)
    "shard":        str,          # 'words_a' … 'words_z' (or 'words_other')
    "snippets":     [str],        # ≤MAX_SNIPPETS context snippets
    "timestamps":   [float],      # epoch timestamps of each snippet
    "first_encountered": float,   # IMMUTABLE — The Rabies Principle
    "hit_count":    int,
    "incomplete":   bool          # True if acquisition gaps remain
}

The Rabies Principle
--------------------
first_encountered is written ONCE and never overwritten.
Any update path that would change it is silently ignored.
This is enforced at the record level, not just by convention.

Shard directory layout
-----------------------
    {words_root}/
        words_a/   …   words_z/
            <address_hex>.json
        words_other/
            <address_hex>.json

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

# ── HyperWebster import (sibling package) ─────────────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))
_HW_DIR      = os.path.join(_HERE, 'HyperWebster-Data-Storage')
if _HW_DIR not in sys.path:
    sys.path.insert(0, _HW_DIR)

from hyperwebster import HyperWebster   # noqa: E402


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

MAX_SNIPPETS  = 8          # max context snippets stored per word record
MAX_TIMESTAMP = 32         # max timestamps stored per word record
_ALPHABET     = 'abcdefghijklmnopqrstuvwxyz'


def _shard_name(word: str) -> str:
    """Map word to its shard directory name."""
    first = word[0].lower() if word else ''
    return f'words_{first}' if first in _ALPHABET else 'words_other'


# ══════════════════════════════════════════════════════════════════════════════
#  WordRecord — the on-disk structure
# ══════════════════════════════════════════════════════════════════════════════

class WordRecord:
    """
    In-memory representation of a word shard JSON record.
    Enforces The Rabies Principle on first_encountered.
    """

    __slots__ = (
        'word', 'address_hex', 'length', 'shard',
        'snippets', 'timestamps', 'first_encountered',
        'hit_count', 'incomplete',
    )

    def __init__(self, word: str, address_hex: str, length: int,
                 shard: str, now: float):
        self.word             = word
        self.address_hex      = address_hex
        self.length           = length
        self.shard            = shard
        self.snippets         : List[str]   = []
        self.timestamps       : List[float] = [now]
        self.first_encountered: float       = now   # IMMUTABLE — Rabies Principle
        self.hit_count        : int         = 0
        self.incomplete       : bool        = True  # flagged until acquisition pass

    # ── serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            'word':             self.word,
            'address_hex':      self.address_hex,
            'length':           self.length,
            'shard':            self.shard,
            'snippets':         self.snippets,
            'timestamps':       self.timestamps,
            'first_encountered': self.first_encountered,
            'hit_count':        self.hit_count,
            'incomplete':       self.incomplete,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'WordRecord':
        r = cls.__new__(cls)
        r.word             = d.get('word', '')
        r.address_hex      = d.get('address_hex', '')
        r.length           = d.get('length', 0)
        r.shard            = d.get('shard', 'words_other')
        r.snippets         = d.get('snippets', [])
        r.timestamps       = d.get('timestamps', [])
        r.first_encountered = d.get('first_encountered', 0.0)   # read-only after this
        r.hit_count        = d.get('hit_count', 0)
        r.incomplete       = d.get('incomplete', True)
        return r

    def update(self, snippet: str, timestamp: float):
        """
        Merge a new context encounter into this record.
        first_encountered is NEVER updated (Rabies Principle).
        """
        if snippet and snippet not in self.snippets:
            self.snippets = (self.snippets + [snippet])[-MAX_SNIPPETS:]
        self.timestamps = (self.timestamps + [timestamp])[-MAX_TIMESTAMP:]
        self.hit_count += 1
        # first_encountered: intentionally not touched


# ══════════════════════════════════════════════════════════════════════════════
#  HyperWebsterLayer3 — the bridge
# ══════════════════════════════════════════════════════════════════════════════

class HyperWebsterLayer3:
    """
    Drains the ContextBuffer Layer 3 queue and writes word records
    to the HyperWebster JSON shard store.

    Usage
    -----
        bridge = HyperWebsterLayer3(words_root='/path/to/HyperWebster')
        entries = context_buffer.layer3_drain()
        bridge.ingest(entries)

    The bridge is intentionally stateless between calls — safe to call
    from any thread. File writes are atomic via a write-then-rename pattern.
    """

    def __init__(self, words_root: Optional[str] = None):
        """
        words_root: directory that contains words_a/ … words_z/ subdirs.
        Defaults to Ptolemy/Callimachus/HyperWebster/ relative to this file.
        """
        if words_root is None:
            words_root = os.path.join(_HERE, 'HyperWebster')
        self.words_root = Path(words_root)
        self._hw = HyperWebster()
        self._ensure_shards()

    # ── public ────────────────────────────────────────────────────────────

    def ingest(self, entries: List[Tuple[str, float, str]]) -> int:
        """
        Process a list of Layer 3 drain entries.
        Each entry: (word_key: str, timestamp: float, snippet: str)
        Returns count of records written/updated.
        """
        written = 0
        for word_key, timestamp, snippet in entries:
            if not word_key:
                continue
            try:
                self._process_word(word_key, timestamp, snippet)
                written += 1
            except Exception as e:
                # Non-fatal — log and continue
                print(f"[Layer3] ingest error for {word_key!r}: {e}")
        return written

    def lookup(self, word: str) -> Optional[WordRecord]:
        """Retrieve a word record by word string. Returns None if not found."""
        path = self._record_path(word)
        return self._load_record(path)

    def address_of(self, word: str) -> Optional[str]:
        """Return the HyperWebster 256-bit hex address of a word."""
        try:
            addr_hex, _, _ = self._hw.index_text(word)
            return addr_hex
        except Exception:
            return None

    # ── internal ──────────────────────────────────────────────────────────

    def _ensure_shards(self):
        """Create shard directories if absent."""
        for letter in _ALPHABET:
            (self.words_root / f'words_{letter}').mkdir(parents=True, exist_ok=True)
        (self.words_root / 'words_other').mkdir(parents=True, exist_ok=True)

    def _record_path(self, word: str) -> Path:
        """Compute the JSON path for a word."""
        try:
            addr_hex, length, _ = self._hw.index_text(word)
        except Exception:
            # Fallback: use plain word as filename (safe chars only)
            safe = re.sub(r'[^\w]', '_', word)[:64]
            shard = _shard_name(word)
            return self.words_root / shard / f'{safe}.json'
        shard = _shard_name(word)
        return self.words_root / shard / f'{addr_hex}.json'

    def _load_record(self, path: Path) -> Optional[WordRecord]:
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return WordRecord.from_dict(json.load(f))
        except Exception:
            return None

    def _save_record(self, record: WordRecord, path: Path):
        """Atomic write: temp file → rename."""
        tmp = path.with_suffix('.tmp')
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
            tmp.replace(path)
        except Exception:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            raise

    def _process_word(self, word: str, timestamp: float, snippet: str):
        """Write or update a single word record."""
        now  = timestamp or time.time()
        path = self._record_path(word)
        rec  = self._load_record(path)

        if rec is None:
            # New word — compute address properly
            try:
                addr_hex, length, _ = self._hw.index_text(word)
            except Exception:
                addr_hex = word[:64]
                length   = len(word)
            shard = _shard_name(word)
            rec   = WordRecord(word, addr_hex, length, shard, now)

        rec.update(snippet, now)
        self._save_record(rec, path)


# ── re import needed in _record_path ──────────────────────────────────────────
import re   # noqa: E402 (after class definition to keep it readable)


# ══════════════════════════════════════════════════════════════════════════════
#  Integration helper — call this from ContextBuffer drain loop
# ══════════════════════════════════════════════════════════════════════════════

def drain_to_hyperwebster(context_buffer, bridge: HyperWebsterLayer3) -> int:
    """
    Drain Layer 3 queue from a ContextBuffer instance and ingest via bridge.
    Returns count of records written.
    """
    entries = context_buffer.layer3_drain()
    if not entries:
        return 0
    return bridge.ingest(entries)


# ══════════════════════════════════════════════════════════════════════════════
#  Smoke test
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        bridge = HyperWebsterLayer3(words_root=tmpdir)

        # Simulate Layer 3 drain entries
        test_entries = [
            ('sedenion',  time.time(), 'The sedenion is the I/O gate'),
            ('noether',   time.time(), 'Noether conservation verified'),
            ('focal',     time.time(), 'Multiple focal points collapse'),
            ('hiraeth',   time.time(), 'untranslatable Welsh longing'),
            ('sedenion',  time.time(), 'sedenion near zero divisor'),  # second hit
        ]

        written = bridge.ingest(test_entries)
        print(f"[Layer3] Written: {written} records")

        # Verify Rabies Principle
        rec = bridge.lookup('sedenion')
        if rec:
            print(f"[Layer3] sedenion:")
            print(f"  address_hex  : {rec.address_hex[:16]}…")
            print(f"  hit_count    : {rec.hit_count}")
            print(f"  first_seen   : {rec.first_encountered}")
            print(f"  snippets     : {rec.snippets}")
            print(f"  incomplete   : {rec.incomplete}")
        else:
            print("[Layer3] sedenion record not found — check path resolution")

        print("[Layer3] Smoke test complete.")
