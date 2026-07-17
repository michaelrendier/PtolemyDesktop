#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
VastRepository  --  Callimachus Address-Space Query Model
=========================================================

Primary knowledge store for Ptolemy.  Every ingested entry lives here,
addressed by its HyperWebster coordinate.  Tables are NLP-derived
category labels; entries are individual subjects within a category.

Storage hierarchy on disk:
    VastRepository/
        VastRepository.json          ← top-level index
        <category>/
            <entry_id>.json          ← full entry (dataclass serialised)

Three reads maximum to retrieve any content:
    1. VastRepository.json  → find table, find entry path
    2. <category>/<id>.json → full entry

Query model:
    lookup()       direct address resolution by entry_id
    search()       NLP-field search (category, subject, tags, text)
    chunk_match()  find entries sharing a HyperGallery chunk address
    proximity()    entries nearest in HyperWebster address space
"""

import json
import os
import hashlib
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# ---------------------------------------------------------------------------
# Entry dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ImageRef:
    """
    HyperGallery image reference.
    chunks     -- ordered list of 32x32 RGB chunk addresses (bare hex strings,
                  no 0x prefix).  Index 0 = top-left, row-major scan order.
    chunk_size -- tile dimension in pixels (default 32)
    width      -- original image width in pixels
    height     -- original image height in pixels
    alt        -- img alt text
    context    -- ±120 chars of surrounding page text
    source_url -- original remote URL (provenance only, never used for fetch)
    """
    chunks:     list        = field(default_factory=list)
    chunk_size: int         = 32
    width:      int         = 0
    height:     int         = 0
    alt:        str         = ""
    context:    str         = ""
    source_url: str         = ""


@dataclass
class Entry:
    """
    Standard VastRepository entry.  Books on a shelf.
    """
    id:         str                         # sha256 of normalised url
    url:        str
    fetcher:    str                         # "requests" | "lynx"
    timestamp:  str                         # ISO8601
    title:      str
    text:       str
    category:   str                         # NLP-assigned
    subject:    str                         # NLP-assigned
    tags:       list        = field(default_factory=list)
    images:     list        = field(default_factory=list)  # list of ImageRef dicts

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict):
        images = [ImageRef(**img) for img in d.pop("images", [])]
        # ResearchEntry fields present → build correct subclass
        research_keys = {"authors", "published", "venue", "doi",
                         "abstract", "sigma", "p_value",
                         "sample_size", "confidence_source"}
        if research_keys & d.keys():
            obj = ResearchEntry(**d)
        else:
            obj = cls(**d)
        obj.images = images
        return obj


@dataclass
class ResearchEntry(Entry):
    """
    Entry for a research paper.  Adds paper metadata extracted from the
    document itself; confidence values come from the paper's own reported
    statistics, not from NLP.
    """
    authors:           list         = field(default_factory=list)
    published:         Optional[str] = None     # ISO8601 date
    venue:             Optional[str] = None     # journal / conference
    doi:               Optional[str] = None
    abstract:          Optional[str] = None
    sigma:             Optional[float] = None
    p_value:           Optional[float] = None
    sample_size:       Optional[int]   = None
    confidence_source: Optional[str]   = None   # "abstract"|"results"|"figure_N"


# ---------------------------------------------------------------------------
# VastRepository index helpers
# ---------------------------------------------------------------------------

def _entry_id(url: str) -> str:
    """Normalise URL then sha256 → hex entry id."""
    import re
    # strip tracking params
    url = re.sub(r'[?&](utm_\w+|fbclid|gclid|ref)=[^&]*', '', url)
    url = url.rstrip('/')
    return hashlib.sha256(url.encode()).hexdigest()


def _index_path(root: str) -> str:
    return os.path.join(root, "VastRepository.json")


def _entry_path(root: str, category: str, entry_id: str) -> str:
    return os.path.join(root, category, f"{entry_id}.json")


# ---------------------------------------------------------------------------
# VastRepository
# ---------------------------------------------------------------------------

class VastRepository:
    """
    Address-space query interface for Callimachus.

    Parameters
    ----------
    root : str
        Path to the VastRepository directory on disk.
        Created on first write if absent.
    """

    def __init__(self, root: str):
        self.root = root
        self._index: dict = {}
        self._load_index()

    # ------------------------------------------------------------------
    # Index I/O
    # ------------------------------------------------------------------

    def _load_index(self):
        path = _index_path(self.root)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                self._index = json.load(f)
        else:
            self._index = {}

    def _save_index(self):
        os.makedirs(self.root, exist_ok=True)
        path = _index_path(self.root)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(self, entry: Entry) -> str:
        """
        Persist entry to disk and update the top-level index.
        Returns the entry id.
        """
        category = entry.category
        eid      = entry.id

        # ensure category directory
        cat_dir = os.path.join(self.root, category)
        os.makedirs(cat_dir, exist_ok=True)

        # write entry JSON
        entry_file = _entry_path(self.root, category, eid)
        with open(entry_file, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2, ensure_ascii=False)

        # update index
        if category not in self._index:
            self._index[category] = {
                "label":       category,
                "entry_count": 0,
                "entries":     {}
            }
        self._index[category]["entries"][eid] = {
            "subject":   entry.subject,
            "url":       entry.url,
            "timestamp": entry.timestamp,
            "path":      os.path.join(category, f"{eid}.json")
        }
        self._index[category]["entry_count"] = \
            len(self._index[category]["entries"])

        self._save_index()
        return eid

    # ------------------------------------------------------------------
    # Query: lookup
    # ------------------------------------------------------------------

    def lookup(self, entry_id: str) -> Optional[Entry]:
        """
        Direct address resolution.  Three reads maximum.
        Returns Entry / ResearchEntry or None if not found.
        """
        for category, table in self._index.items():
            if entry_id in table["entries"]:
                rel_path   = table["entries"][entry_id]["path"]
                entry_file = os.path.join(self.root, rel_path)
                if os.path.isfile(entry_file):
                    with open(entry_file, "r", encoding="utf-8") as f:
                        return Entry.from_dict(json.load(f))
        return None

    def lookup_by_url(self, url: str) -> Optional[Entry]:
        """Convenience wrapper: resolve url → id → entry."""
        return self.lookup(_entry_id(url))

    # ------------------------------------------------------------------
    # Query: search
    # ------------------------------------------------------------------

    def search(self,
               term:     Optional[str]       = None,
               category: Optional[str]       = None,
               subject:  Optional[str]       = None,
               tags:     Optional[list]      = None,
               limit:    int                 = 50) -> list:
        """
        NLP-field search against the index and entry content.

        Parameters
        ----------
        term     : free-text match against title + text (case-insensitive)
        category : exact category match
        subject  : substring match against subject field
        tags     : list of tags; entry must contain ALL supplied tags
        limit    : maximum results returned

        Returns list of Entry objects, most recently ingested first.
        """
        results = []

        for cat_name, table in self._index.items():

            # category filter — skip entire table fast
            if category and cat_name != category:
                continue

            for eid, meta in table["entries"].items():

                # subject filter on index metadata (no file read needed)
                if subject and subject.lower() not in meta["subject"].lower():
                    continue

                # load entry for deeper field checks
                entry = self._load_entry(cat_name, eid)
                if entry is None:
                    continue

                # tag filter
                if tags:
                    if not all(t in entry.tags for t in tags):
                        continue

                # free-text filter
                if term:
                    haystack = (entry.title + " " + entry.text).lower()
                    if term.lower() not in haystack:
                        continue

                results.append(entry)
                if len(results) >= limit:
                    return _sort_by_timestamp(results)

        return _sort_by_timestamp(results)

    # ------------------------------------------------------------------
    # Query: chunk_match
    # ------------------------------------------------------------------

    def chunk_match(self, chunk_address: str) -> list:
        """
        Find all entries whose ImageRef list contains chunk_address.
        chunk_address is a bare hex string (no 0x prefix).

        Used by Phaleron to discover entries sharing a visual tile,
        and by the appraisal network for visual similarity queries.
        """
        results = []
        for cat_name, table in self._index.items():
            for eid in table["entries"]:
                entry = self._load_entry(cat_name, eid)
                if entry is None:
                    continue
                for img in entry.images:
                    if isinstance(img, ImageRef):
                        chunks = img.chunks
                    elif isinstance(img, dict):
                        chunks = img.get("chunks", [])
                    else:
                        continue
                    if chunk_address in chunks:
                        results.append(entry)
                        break
        return results

    # ------------------------------------------------------------------
    # Query: proximity
    # ------------------------------------------------------------------

    def proximity(self, entry_id: str, n: int = 10) -> list:
        """
        Return up to n entries whose HyperWebster addresses are nearest
        to the address of entry_id in the address space.

        Proximity is computed as |address(A) - address(B)| on the
        integer addresses of the entry ids (sha256 hex → int).
        This is a first-order approximation; full octonion-address
        proximity lives in the HyperWebster manifold layer.
        """
        target_int = int(entry_id, 16)
        scored     = []

        for cat_name, table in self._index.items():
            for eid in table["entries"]:
                if eid == entry_id:
                    continue
                try:
                    dist = abs(int(eid, 16) - target_int)
                except ValueError:
                    continue
                scored.append((dist, cat_name, eid))

        scored.sort(key=lambda x: x[0])

        results = []
        for _, cat_name, eid in scored[:n]:
            entry = self._load_entry(cat_name, eid)
            if entry:
                results.append(entry)
        return results

    # ------------------------------------------------------------------
    # Query: list categories / list entries
    # ------------------------------------------------------------------

    def categories(self) -> list:
        """Return all category names in the index."""
        return list(self._index.keys())

    def list_entries(self, category: str) -> list:
        """Return lightweight index metadata for all entries in a category."""
        table = self._index.get(category, {})
        return list(table.get("entries", {}).values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_entry(self, category: str, entry_id: str) -> Optional[Entry]:
        rel_path   = self._index[category]["entries"][entry_id]["path"]
        entry_file = os.path.join(self.root, rel_path)
        if not os.path.isfile(entry_file):
            return None
        with open(entry_file, "r", encoding="utf-8") as f:
            return Entry.from_dict(json.load(f))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sort_by_timestamp(entries: list) -> list:
    """Most recently ingested first."""
    def _key(e):
        return e.timestamp if hasattr(e, "timestamp") else ""
    return sorted(entries, key=_key, reverse=True)
