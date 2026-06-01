#!/usr/bin/env python3
"""
acquire_inline.py — LSH two-pass inline acquisition
======================================================
Philadelphos / LSH_Datatype_parser

Two callables for inline use in the LSH inference pipeline:

    acquire_pre(words)   — called BEFORE LSH inference (on command words)
    acquire_post(words)  — called AFTER LSH inference (on output words)

Both return a dict keyed by word. Non-blocking relative to inference:
the caller decides whether to await or fire-and-forget.

Pass 1 (pre):  enriches command words before LSH sees them.
               Result injected into inference context.
Pass 2 (post): enriches output words after LSH determines response.
               Result stored/logged. Does NOT alter output text.

Design rules:
  - No argparse. No logging noise. No batch loop.
  - Returns dict synchronously. Caller owns threading/async if needed.
  - Wiktionary etymology XPath fixed (iter-based, not cssselect).
  - Rabies Principle preserved: first_encountered never overwritten.
  - Aule shim: zero-coupling, silent if Aule absent.
  - lxml over BeautifulSoup (locked).
  - No Claude/LLM API gap-fill. Flags only.
"""

# ── Aule shim ─────────────────────────────────────────────────────────────────
try:
    from Aule.aule import stream_event as _emit
except ImportError:
    def _emit(channel, event_type, payload=None, **kwargs): pass

import json
import time
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from lxml import html as lxml_html
    _LXML = True
except ImportError:
    _LXML = False

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE        = Path(__file__).resolve().parent
_OUTPUT_ROOT = _HERE / "hyperwebster_data"

_DELAY   = 0.4   # between API calls within one word
_TIMEOUT = 7


# ─────────────────────────────────────────────────────────────────────────────
# Internal: fetchers (flat, no logging, return {} on any failure)
# ─────────────────────────────────────────────────────────────────────────────

def _free_dict(word: str) -> dict:
    try:
        r = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}",
            timeout=_TIMEOUT)
        time.sleep(_DELAY)
        if r.status_code != 200 or not isinstance(r.json(), list):
            return {}
        entry    = r.json()[0]
        meanings = entry.get("meanings", [])
        defs     = []
        syns, ants = [], []
        for m in meanings:
            pos = m.get("partOfSpeech", "unknown")
            for d in m.get("definitions", []):
                defs.append({"pos": pos,
                             "definition": d.get("definition", ""),
                             "example":    d.get("example", "")})
                syns.extend(d.get("synonyms", []))
                ants.extend(d.get("antonyms", []))
        phonetics = [p["text"] for p in entry.get("phonetics", []) if p.get("text")]
        etymology = entry.get("origin", "")
        return {"defs": defs, "phonetics": phonetics,
                "etymology": etymology, "synonyms": syns, "antonyms": ants}
    except Exception:
        return {}


def _datamuse(word: str) -> dict:
    base = "https://api.datamuse.com/words"
    out  = {}
    try:
        for key, params in [
            ("synonyms",       {"ml": word,       "max": 20}),
            ("rhymes",         {"rel_rhy": word,   "max": 10}),
            ("homophones",     {"rel_hom": word,   "max": 10}),
            ("triggers",       {"rel_trg": word,   "max": 20}),
            ("right_collocates",{"lc": word,        "max": 10}),
            ("left_collocates", {"rc": word,        "max": 10}),
        ]:
            r = requests.get(base, params=params, timeout=_TIMEOUT)
            time.sleep(_DELAY)
            if r.status_code == 200:
                out[key] = [w["word"] for w in r.json()]
    except Exception:
        pass
    return out


def _wiktionary(word: str) -> dict:
    if not _LXML:
        return {}
    try:
        r = requests.get(
            f"https://en.wiktionary.org/wiki/{word}",
            timeout=_TIMEOUT,
            headers={"User-Agent": "Ptolemy-HyperWebster/1.0"})
        time.sleep(_DELAY)
        if r.status_code != 200:
            return {}
        tree = lxml_html.fromstring(r.content)

        # IPA — span.IPA elements
        ipa = []
        for span in tree.cssselect("span.IPA"):
            txt = span.text_content().strip()
            if txt and txt not in ipa:
                ipa.append(txt)

        # Etymology — iterate elements; grab first <p> after any Etymology heading.
        # Uses element iteration (not XPath heading selectors) for robustness.
        etymology = ""
        in_etym   = False
        for elem in tree.iter():
            tag = getattr(elem, "tag", "")
            if not isinstance(tag, str):
                continue
            if tag in ("h2", "h3", "h4"):
                heading = (elem.text_content() or "").lower()
                in_etym = "etymology" in heading
                continue
            if in_etym and tag == "p":
                txt = (elem.text_content() or "").strip()
                # Skip navigation/short noise paragraphs
                if len(txt) > 20:
                    etymology = txt
                    break

        # Definitions — first 10 li in mw-parser-output ol
        defs_wikt = []
        for li in tree.cssselect(".mw-parser-output > ol > li"):
            txt = (li.text_content() or "").strip()
            if txt and len(txt) > 5:
                defs_wikt.append(txt[:400])
            if len(defs_wikt) >= 10:
                break

        return {"ipa": ipa, "etymology": etymology, "defs_wikt": defs_wikt}
    except Exception:
        return {}


def _wikipedia(word: str) -> dict:
    try:
        r = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{word}",
            timeout=_TIMEOUT,
            headers={"User-Agent": "Ptolemy-HyperWebster/1.0"})
        time.sleep(_DELAY)
        if r.status_code != 200:
            return {}
        data = r.json()
        if data.get("type") == "disambiguation":
            return {"disambiguation": True}
        extract = data.get("extract", "")
        return {
            "summary": extract[:800],
            "title":   data.get("title", ""),
            "url":     data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        } if extract else {}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# Internal: assemble LSH record from source dicts
# ─────────────────────────────────────────────────────────────────────────────

def _shard_path(word: str) -> Path:
    first = word[0].lower() if word and word[0].isalpha() else "_"
    d = _OUTPUT_ROOT / f"words_{first}"
    d.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in word)
    return d / f"{safe}.json"


def _existing_first_encountered(word: str) -> Optional[str]:
    """Return immutable first_encountered if word already on disk."""
    p = _shard_path(word)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))\
                   .get("resonance", {}).get("first_encountered")
    except Exception:
        return None


def _is_complete(word: str) -> bool:
    p = _shard_path(word)
    if not p.exists():
        return False
    try:
        src = json.loads(p.read_text(encoding="utf-8"))\
                  .get("resonance", {}).get("learning_source", "")
        return not str(src).startswith("__incomplete__")
    except Exception:
        return False


def _assemble(word: str, fd: dict, dm: dict, wk: dict, wp: dict,
              first_encountered: Optional[str] = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    defs     = fd.get("defs", [])
    ipa      = wk.get("ipa", []) or fd.get("phonetics", [])
    etymology = fd.get("etymology", "") or wk.get("etymology", "")
    syns     = list(dict.fromkeys(fd.get("synonyms", [])))
    ants     = list(dict.fromkeys(fd.get("antonyms", [])))
    primary_pos = defs[0]["pos"] if defs else "unknown"

    sources = ([("free_dictionary", fd)] + [("datamuse", dm)] +
               [("wiktionary", wk)] + [("wikipedia", wp)])
    sources_hit = [name for name, d in sources if d]

    missing = []
    if not defs:             missing.append("definitions")
    if not (defs and defs[0].get("definition")): missing.append("denotation")
    if not ipa:              missing.append("ipa")
    if not etymology:        missing.append("etymology")
    learning_source = ("__incomplete__:" + ",".join(sorted(missing))
                       if missing else "acquisition_pipeline_v1")

    return {
        "word":                  word,
        "token_glyphed":         None,
        "hyperwebster_address":  None,
        "semantic": {
            "denotation":    defs[0]["definition"] if defs else "",
            "connotations":  [],
            "synonyms":      syns,
            "antonyms":      ants,
            "sense_inventory": [
                {"pos": d["pos"], "definition": d["definition"],
                 "example": d.get("example", "")} for d in defs
            ],
            "raw_wiktionary": wk.get("defs_wikt", [])[:5],
        },
        "etymology": {
            "prose":          etymology,
            "root_language":  "",
            "first_attested": "",
        },
        "phonology": {
            "ipa":            ipa,
            "phonetics_raw":  fd.get("phonetics", []),
            "syllable_count": 0,
        },
        "morphology": {"primary_pos": primary_pos},
        "associative": {
            "synonyms_datamuse":  dm.get("synonyms", []),
            "rhymes":             dm.get("rhymes", []),
            "homophones":         dm.get("homophones", []),
            "triggers":           dm.get("triggers", []),
            "left_collocates":    dm.get("left_collocates", []),
            "right_collocates":   dm.get("right_collocates", []),
        },
        "encyclopedic": {
            "summary":        wp.get("summary", ""),
            "title":          wp.get("title", ""),
            "url":            wp.get("url", ""),
            "disambiguation": wp.get("disambiguation", False),
        },
        "translations": {},
        "resonance": {
            "first_encountered": first_encountered or now,  # Rabies Principle
            "learning_source":   learning_source,
            "confidence":        0.0,
        },
        "meta": {
            "acquired_at": now,
            "sources_hit": sources_hit,
            "version":     "1.0",
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core inline acquire — single word, returns LSH record dict
# ─────────────────────────────────────────────────────────────────────────────

def acquire(word: str,
            wikipedia: bool = False,
            force:     bool = False,
            persist:   bool = True) -> dict:
    """
    Acquire one word. Returns LSH record dict.

    Parameters
    ----------
    word       : the word to acquire
    wikipedia  : also query Wikipedia (slower)
    force      : re-acquire even if complete record exists on disk
    persist    : write JSON shard to disk (default True)
                 set False for ephemeral inline enrichment (pass 2 fire-and-forget)

    Returns {} if word is empty or already complete and force=False.
    """
    word = word.strip().lower()
    if not word:
        return {}

    if not force and _is_complete(word):
        # Return cached record without re-fetching
        p = _shard_path(word)
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass

    first_enc = _existing_first_encountered(word)  # preserve Rabies Principle

    _emit("acquire", "word_start", {"word": word})

    fd = _free_dict(word)
    dm = _datamuse(word)
    wk = _wiktionary(word)
    wp = _wikipedia(word) if wikipedia else {}

    record = _assemble(word, fd, dm, wk, wp, first_enc)

    if persist:
        _shard_path(word).write_text(
            json.dumps(record, ensure_ascii=False, indent=2),
            encoding="utf-8")

    incomplete = record["resonance"]["learning_source"].startswith("__incomplete__")
    _emit("acquire", "word_incomplete" if incomplete else "word_complete",
          {"word": word, "flags": record["resonance"]["learning_source"],
           "sources": record["meta"]["sources_hit"]})

    return record


# ─────────────────────────────────────────────────────────────────────────────
# Pass 1 — pre-inference (command words → enrich before LSH sees them)
# ─────────────────────────────────────────────────────────────────────────────

def acquire_pre(words: List[str],
                wikipedia: bool = False) -> Dict[str, dict]:
    """
    Pass 1: acquire words from incoming command BEFORE LSH inference.

    - Persists to disk (these are words entering the system).
    - Returns {word: lsh_record} for all words.
    - Skips words already complete on disk (returns cached record).
    - Caller injects result into inference context as needed.

    Example
    -------
        context["word_data"] = acquire_pre(tokenize(command))
        result = lsh_model.infer(command, context)
    """
    _emit("acquire", "pre_pass_start", {"words": words})
    out = {}
    for word in words:
        w = word.strip().lower()
        if w:
            out[w] = acquire(w, wikipedia=wikipedia, force=False, persist=True)
    _emit("acquire", "pre_pass_end", {"count": len(out)})
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Pass 2 — post-inference (output words → enrich after LSH determines output)
# ─────────────────────────────────────────────────────────────────────────────

def acquire_post(words: List[str],
                 wikipedia: bool = False,
                 persist:   bool = True) -> Dict[str, dict]:
    """
    Pass 2: acquire words from LSH output AFTER inference.

    - Persists by default (output words are now known to the system).
    - Does NOT alter the output text — enrichment is stored/logged only.
    - Returns {word: lsh_record} for all words.

    Example
    -------
        output = lsh_model.infer(command, context)
        word_data = acquire_post(tokenize(output))
        # word_data available for downstream layers (TuningDisplay, AuditChain)
    """
    _emit("acquire", "post_pass_start", {"words": words})
    out = {}
    for word in words:
        w = word.strip().lower()
        if w:
            out[w] = acquire(w, wikipedia=wikipedia, force=False, persist=persist)
    _emit("acquire", "post_pass_end", {"count": len(out)})
    return out
