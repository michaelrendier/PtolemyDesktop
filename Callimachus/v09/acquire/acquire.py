#!/usr/bin/env python3
"""
Callimachus — Acquire
======================
HyperWebster word acquisition pipeline.
Callimachus is the only entry point. No loose scripts.

Sources (in order):
  1. Free Dictionary API
  2. Datamuse
  3. Wiktionary (lxml)
  4. Wikipedia (optional, --wikipedia flag)

Output:
  - One JSON shard per word (words_a/ … words_z/ relative to output_root)
  - LSH_Datatype written to HyperDatabase (label = HyperWebster SHA-256 of word)
  - incomplete flag set if any acquisition layer is None after all sources

Resume:
  Default ON — skips words where HyperDatabase record exists AND incomplete=0.
  Retries incomplete records.

No Claude API gap-fill in first pass. Flags only.
lxml over BeautifulSoup (performance decision — locked).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

try:
    from lxml import html as lxml_html
    _LXML = True
except ImportError:
    _LXML = False
    logging.warning("lxml not available — Wiktionary parsing degraded")

from ..core.hyperwebster import HyperWebster
from ..core.lsh_datatype import LSH_Datatype
from ..core.charset     import validate_text
from ..database.hyperdatabase import HyperDatabase

log = logging.getLogger("callimachus.acquire")

_REQUEST_DELAY   = 0.5
_WIKIPEDIA_DELAY = 1.0
_TIMEOUT         = 8


# ---------------------------------------------------------------------------
# Source fetchers — each returns a dict of fields or {} on failure
# ---------------------------------------------------------------------------

def _fetch_free_dictionary(word: str) -> dict:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, list) or not data:
            return {}
        entry     = data[0]
        meanings  = entry.get("meanings", [])
        pos       = meanings[0].get("partOfSpeech") if meanings else None
        defs      = meanings[0].get("definitions", []) if meanings else []
        defn      = defs[0].get("definition") if defs else None
        phonetics = entry.get("phonetics", [])
        etymology = None
        for p in phonetics:
            if p.get("text"):
                break
        return {"pos_primary": pos, "definition_core": defn}
    except Exception as e:
        log.debug(f"FreeDictionary failed for {word!r}: {e}")
        return {}


def _fetch_datamuse(word: str) -> dict:
    url = f"https://api.datamuse.com/words?sp={word}&md=dp&max=1"
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        data = r.json()
        if not data:
            return {}
        entry = data[0]
        tags  = entry.get("tags", [])
        pos   = None
        for t in tags:
            if t in ("n", "v", "adj", "adv", "u"):
                pos = {"n": "noun", "v": "verb", "adj": "adjective",
                       "adv": "adverb", "u": "unknown"}.get(t, t)
                break
        defs = entry.get("defs", [])
        defn = defs[0].split("\t", 1)[-1] if defs else None
        return {"pos_secondary": pos, "definition_core": defn}
    except Exception as e:
        log.debug(f"Datamuse failed for {word!r}: {e}")
        return {}


def _fetch_wiktionary(word: str) -> dict:
    if not _LXML:
        return {}
    url = f"https://en.wiktionary.org/wiki/{word}"
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        tree = lxml_html.fromstring(r.content)
        # Etymology: first mw-parser-output p after Etymology heading
        etym = None
        for h in tree.xpath("//h3[.//span[@id='Etymology' or starts-with(@id,'Etymology')]]"):
            p = h.getnext()
            if p is not None:
                etym = (p.text_content() or "").strip() or None
            break
        # Definition: first <li> in mw-parser-output ol
        defn = None
        lis  = tree.xpath("//div[@class='mw-parser-output']//ol/li")
        if lis:
            defn = (lis[0].text_content() or "").strip() or None
        return {"etymology": etym, "definition_core": defn}
    except Exception as e:
        log.debug(f"Wiktionary failed for {word!r}: {e}")
        return {}


def _fetch_wikipedia(word: str) -> dict:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{word}"
    try:
        r = requests.get(url, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        data  = r.json()
        defn  = data.get("extract", "").split(".")[0] + "." if data.get("extract") else None
        return {"definition_core": defn}
    except Exception as e:
        log.debug(f"Wikipedia failed for {word!r}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Shard path
# ---------------------------------------------------------------------------

def _shard_path(output_root: Path, word: str) -> Path:
    first = word[0].lower() if word and word[0].isalpha() else "_"
    d     = output_root / f"words_{first}"
    d.mkdir(parents=True, exist_ok=True)
    # sanitize filename
    safe  = "".join(c if c.isalnum() or c in "-_" else "_" for c in word)
    return d / f"{safe}.json"


# ---------------------------------------------------------------------------
# Core acquisition function
# ---------------------------------------------------------------------------

def acquire_word(
    word:        str,
    hw:          HyperWebster,
    db:          HyperDatabase,
    output_root: Path,
    wikipedia:   bool = False,
    force:       bool = False,
) -> LSH_Datatype:
    """
    Acquire a single word. Returns LSH_Datatype.
    Writes JSON shard and HyperDatabase record.
    Resumes by default (skips if complete record exists).
    """
    label = hw.label_of(word)

    # Resume logic — skip complete records
    if not force and db.exists(label):
        row = db.get_record(label)
        if row and row['incomplete'] == 0:
            log.debug(f"Skip (complete): {word!r}")
            existing = db.get(label)
            return existing

    log.info(f"Acquiring: {word!r}")

    # Check charset
    bad_chars = validate_text(word)
    if bad_chars:
        log.warning(f"{word!r} contains out-of-charset chars: {bad_chars}")

    # Gather from sources
    fields = {}
    for fetcher in [_fetch_free_dictionary, _fetch_datamuse, _fetch_wiktionary]:
        result = fetcher(word)
        for k, v in result.items():
            if v and k not in fields:
                fields[k] = v
        time.sleep(_REQUEST_DELAY)

    if wikipedia:
        wiki = _fetch_wikipedia(word)
        for k, v in wiki.items():
            if v and k not in fields:
                fields[k] = v
        time.sleep(_WIKIPEDIA_DELAY)

    # Build LSH_Datatype
    record = hw.index(word)
    lsh    = LSH_Datatype.from_acquisition(
        hw_label      = label,
        word_surface  = word,
        canonical     = word.lower(),
        pos_primary   = fields.get("pos_primary"),
        pos_secondary = fields.get("pos_secondary"),
        etymology     = fields.get("etymology"),
        definition    = fields.get("definition_core"),
    )

    # Write JSON shard
    shard_file = _shard_path(output_root, word)
    shard_data = lsh.to_dict()
    shard_data["hw_record"] = {
        "label":     record.label,
        "payload":   record.payload,
        "length":    record.length,
        "timestamp": record.timestamp,
    }
    with open(shard_file, "w", encoding="utf-8") as f:
        json.dump(shard_data, f, ensure_ascii=False, indent=2)
    log.debug(f"Shard written: {shard_file}")

    # Write HyperDatabase record
    db.put(record, lsh)

    return lsh


# ---------------------------------------------------------------------------
# Batch acquisition
# ---------------------------------------------------------------------------

def acquire_wordlist(
    words:       list[str],
    db_path:     str,
    output_root: str,
    wikipedia:   bool = False,
    force:       bool = False,
) -> dict:
    """
    Acquire a list of words.
    Returns summary dict: {total, complete, incomplete, skipped, errors}.
    """
    hw    = HyperWebster()
    root  = Path(output_root)
    stats = {"total": len(words), "complete": 0,
             "incomplete": 0, "skipped": 0, "errors": 0}

    with HyperDatabase(db_path) as db:
        for word in words:
            try:
                lsh = acquire_word(word, hw, db, root, wikipedia, force)
                incomplete = any(lsh.get_layer(i) is None for i in range(6))
                if incomplete:
                    stats["incomplete"] += 1
                else:
                    stats["complete"] += 1
            except Exception as e:
                log.error(f"Error acquiring {word!r}: {e}")
                stats["errors"] += 1

    log.info(
        f"Acquisition complete — "
        f"{stats['complete']} complete, {stats['incomplete']} incomplete, "
        f"{stats['errors']} errors of {stats['total']} total."
    )
    return stats
