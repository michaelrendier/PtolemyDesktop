#!/usr/bin/env python3
"""
acquire.py — HyperWebster word acquisition pipeline
=====================================================
Queries: Free Dictionary API → Datamuse → Wiktionary → Wikipedia (optional)
Output:  one JSON file per word into alphabetically sharded dirs (words_a/ … words_z/)
Resume:  on by default — skips existing complete files
Flags:   __incomplete__:field,field written to resonance.learning_source for gaps
Aule:    stream_event() shim wired in — zero-coupling, silent if Aule absent
lxml:    used over BeautifulSoup for performance
No Claude API gap-fill in first pass — flags only.

Author: Ptolemy Project / HyperWebster architecture
"""

# ── Aule shim (zero coupling — silent no-op if Aule not running) ─────────────
try:
    from Aule.aule import stream_event as _emit
except ImportError:
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from Aule.aule import stream_event as _emit
    except ImportError:
        def _emit(channel, event_type, payload=None, **kwargs): pass

# ── Standard imports ──────────────────────────────────────────────────────────
import os
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from lxml import etree, html as lxml_html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    logging.warning("lxml not available — Wiktionary parsing will be degraded")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("acquire")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
OUTPUT_ROOT  = SCRIPT_DIR / "hyperwebster_data"

# ── Rate limiting ─────────────────────────────────────────────────────────────
REQUEST_DELAY = 0.5   # seconds between API calls
WIKIPEDIA_DELAY = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# SHARD DIRECTORY
# ─────────────────────────────────────────────────────────────────────────────

def shard_dir(word: str) -> Path:
    first = word[0].lower() if word and word[0].isalpha() else "_"
    d = OUTPUT_ROOT / f"words_{first}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def word_path(word: str) -> Path:
    return shard_dir(word) / f"{word.lower()}.json"


def is_complete(word: str) -> bool:
    p = word_path(word)
    if not p.exists():
        return False
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        src = data.get("resonance", {}).get("learning_source", "")
        return not str(src).startswith("__incomplete__")
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# INCOMPLETE FLAG HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def flag_incomplete(result: Dict, *fields: str) -> None:
    """Write __incomplete__:field,field into resonance.learning_source."""
    existing = result.get("resonance", {}).get("learning_source", "")
    # Collect already-flagged fields
    flagged = set()
    if existing.startswith("__incomplete__:"):
        flagged = set(existing[len("__incomplete__:"):].split(","))
    flagged.update(fields)
    result.setdefault("resonance", {})["learning_source"] = (
        "__incomplete__:" + ",".join(sorted(flagged))
    )


def clear_incomplete(result: Dict) -> None:
    result.setdefault("resonance", {}).pop("learning_source", None)


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 1 — Free Dictionary API
# ─────────────────────────────────────────────────────────────────────────────

def fetch_free_dictionary(word: str) -> Dict:
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    _emit("api", "api_call", {"source": "free_dictionary", "word": word})
    try:
        r = requests.get(url, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code != 200:
            _emit("api", "api_miss", {"source": "free_dictionary", "word": word, "status": r.status_code})
            return {}
        data = r.json()
        if not isinstance(data, list) or not data:
            return {}
        entry = data[0]
        result = {
            "word": word,
            "phonetics": [],
            "definitions": [],
            "etymology": "",
        }
        # Phonetics
        for ph in entry.get("phonetics", []):
            if ph.get("text"):
                result["phonetics"].append(ph["text"])
        # Meanings → definitions
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "unknown")
            for defn in meaning.get("definitions", []):
                result["definitions"].append({
                    "pos": pos,
                    "definition": defn.get("definition", ""),
                    "example": defn.get("example", ""),
                    "synonyms": defn.get("synonyms", []),
                    "antonyms": defn.get("antonyms", []),
                })
        # Etymology (sometimes in entry)
        if entry.get("origin"):
            result["etymology"] = entry["origin"]
        _emit("api", "api_hit", {"source": "free_dictionary", "word": word,
                                  "definitions": len(result["definitions"])})
        return result
    except Exception as e:
        _emit("api", "api_error", {"source": "free_dictionary", "word": word, "error": str(e)})
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 2 — Datamuse
# ─────────────────────────────────────────────────────────────────────────────

def fetch_datamuse(word: str) -> Dict:
    result = {}
    base = "https://api.datamuse.com/words"
    _emit("api", "api_call", {"source": "datamuse", "word": word})
    try:
        # Synonyms (means like)
        r = requests.get(base, params={"ml": word, "max": 20}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["synonyms_datamuse"] = [w["word"] for w in r.json()]
        # Rhymes
        r = requests.get(base, params={"rel_rhy": word, "max": 10}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["rhymes"] = [w["word"] for w in r.json()]
        # Homophones
        r = requests.get(base, params={"rel_hom": word, "max": 10}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["homophones"] = [w["word"] for w in r.json()]
        # Triggers (associated words)
        r = requests.get(base, params={"rel_trg": word, "max": 20}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["triggers"] = [w["word"] for w in r.json()]
        # Follows (right collocates)
        r = requests.get(base, params={"lc": word, "max": 10}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["right_collocates"] = [w["word"] for w in r.json()]
        # Preceded by (left collocates)
        r = requests.get(base, params={"rc": word, "max": 10}, timeout=10)
        time.sleep(REQUEST_DELAY)
        if r.status_code == 200:
            result["left_collocates"] = [w["word"] for w in r.json()]
        _emit("api", "api_hit", {"source": "datamuse", "word": word})
    except Exception as e:
        _emit("api", "api_error", {"source": "datamuse", "word": word, "error": str(e)})
    return result


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 3 — Wiktionary (lxml)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_wiktionary(word: str) -> Dict:
    url = f"https://en.wiktionary.org/wiki/{word}"
    _emit("api", "api_call", {"source": "wiktionary", "word": word})
    try:
        r = requests.get(url, timeout=10,
                         headers={"User-Agent": "Ptolemy-HyperWebster/1.0"})
        time.sleep(REQUEST_DELAY)
        if r.status_code != 200:
            _emit("api", "api_miss", {"source": "wiktionary", "word": word})
            return {}

        result = {
            "pronunciation_ipa": [],
            "etymology_wikt": "",
            "definitions_wikt": [],
            "translations": {},
        }

        if LXML_AVAILABLE:
            tree = lxml_html.fromstring(r.content)

            # IPA
            for span in tree.cssselect("span.IPA"):
                txt = span.text_content().strip()
                if txt and txt not in result["pronunciation_ipa"]:
                    result["pronunciation_ipa"].append(txt)

            # Etymology — iterate elements; grab first <p> after Etymology heading
            in_etym = False
            for elem in tree.iter():
                tag = getattr(elem, "tag", "")
                if not isinstance(tag, str):
                    continue
                if tag in ("h2", "h3", "h4"):
                    in_etym = "etymology" in (elem.text_content() or "").lower()
                    continue
                if in_etym and tag == "p":
                    txt = (elem.text_content() or "").strip()
                    if len(txt) > 20:
                        result["etymology_wikt"] = txt
                        break

            # Definitions — li items in mw-parser-output
            for li in tree.cssselect(".mw-parser-output > ol > li"):
                txt = li.text_content().strip()
                if txt and len(txt) > 5:
                    result["definitions_wikt"].append(txt[:400])
                    if len(result["definitions_wikt"]) >= 10:
                        break

        _emit("api", "api_hit", {"source": "wiktionary", "word": word,
                                  "ipa_count": len(result["pronunciation_ipa"])})
        return result
    except Exception as e:
        _emit("api", "api_error", {"source": "wiktionary", "word": word, "error": str(e)})
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE 4 — Wikipedia (optional)
# ─────────────────────────────────────────────────────────────────────────────

def fetch_wikipedia(word: str) -> Dict:
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + word
    _emit("api", "api_call", {"source": "wikipedia", "word": word})
    try:
        r = requests.get(url, timeout=10,
                         headers={"User-Agent": "Ptolemy-HyperWebster/1.0"})
        time.sleep(WIKIPEDIA_DELAY)
        if r.status_code != 200:
            _emit("api", "api_miss", {"source": "wikipedia", "word": word})
            return {}
        data = r.json()
        if data.get("type") == "disambiguation":
            return {"wikipedia_disambiguation": True}
        extract = data.get("extract", "")
        if not extract:
            return {}
        _emit("api", "api_hit", {"source": "wikipedia", "word": word})
        return {
            "wikipedia_summary": extract[:800],
            "wikipedia_title": data.get("title", ""),
            "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
    except Exception as e:
        _emit("api", "api_error", {"source": "wikipedia", "word": word, "error": str(e)})
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLER — merge all sources into SemanticWord-shaped JSON
# ─────────────────────────────────────────────────────────────────────────────

def assemble(word: str,
             fd: Dict,
             dm: Dict,
             wk: Dict,
             wp: Dict) -> Dict:
    """
    Assemble a SemanticWord-compatible JSON from all source dicts.
    Fields that cannot be filled are flagged __incomplete__.
    first_encountered is set once and NEVER modified (The Rabies Principle).
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # Phonetics: prefer Wiktionary IPA, fallback to Free Dict
    ipa = wk.get("pronunciation_ipa", [])
    if not ipa and fd.get("phonetics"):
        ipa = fd["phonetics"]
    phonetics_raw = fd.get("phonetics", [])

    # Definitions: merge Free Dict (structured) + Wiktionary (raw text)
    definitions = fd.get("definitions", [])
    definitions_wikt = wk.get("definitions_wikt", [])

    # Etymology: prefer Free Dict (usually better English prose), fallback Wiktionary
    etymology = fd.get("etymology", "") or wk.get("etymology_wikt", "")

    # Synonyms/antonyms from Free Dict definitions
    synonyms, antonyms = [], []
    for defn in definitions:
        synonyms.extend(defn.get("synonyms", []))
        antonyms.extend(defn.get("antonyms", []))
    synonyms = list(dict.fromkeys(synonyms))   # deduplicate, preserve order
    antonyms = list(dict.fromkeys(antonyms))

    # POS — primary from first definition
    primary_pos = definitions[0]["pos"] if definitions else "unknown"

    # ── Build the output record ───────────────────────────────────────────────
    record = {
        "word": word,
        "token_glyphed": None,        # set by HyperWebster layer
        "hyperwebster_address": None, # set by Callimachus / Horner layer

        "semantic": {
            "denotation": definitions[0]["definition"] if definitions else "",
            "connotations": [],
            "synonyms": synonyms,
            "antonyms": antonyms,
            "sense_inventory": [
                {"pos": d["pos"], "definition": d["definition"],
                 "example": d.get("example", "")}
                for d in definitions
            ],
            "raw_wiktionary": definitions_wikt[:5],
        },

        "etymology": {
            "prose": etymology,
            "root_language": "",
            "first_attested": "",
        },

        "phonology": {
            "ipa": ipa,
            "phonetics_raw": phonetics_raw,
            "syllable_count": 0,        # computed later
        },

        "morphology": {
            "primary_pos": primary_pos,
        },

        "associative": {
            "synonyms_datamuse": dm.get("synonyms_datamuse", []),
            "rhymes": dm.get("rhymes", []),
            "homophones": dm.get("homophones", []),
            "triggers": dm.get("triggers", []),
            "left_collocates": dm.get("left_collocates", []),
            "right_collocates": dm.get("right_collocates", []),
        },

        "encyclopedic": {
            "summary": wp.get("wikipedia_summary", ""),
            "title": wp.get("wikipedia_title", ""),
            "url": wp.get("wikipedia_url", ""),
            "disambiguation": wp.get("wikipedia_disambiguation", False),
        },

        "translations": wk.get("translations", {}),

        # ── PersonalResonance / Rabies Principle ──────────────────────────────
        "resonance": {
            "first_encountered": now_iso,   # IMMUTABLE after first write
            "learning_source": "acquisition_pipeline_v1",
            "confidence": 0.0,              # set by training
        },

        "meta": {
            "acquired_at": now_iso,
            "sources_hit": [],
            "version": "1.0",
        },
    }

    # Track which sources actually returned data
    if fd:  record["meta"]["sources_hit"].append("free_dictionary")
    if dm:  record["meta"]["sources_hit"].append("datamuse")
    if wk:  record["meta"]["sources_hit"].append("wiktionary")
    if wp:  record["meta"]["sources_hit"].append("wikipedia")

    # ── Incomplete flagging ───────────────────────────────────────────────────
    missing = []
    if not record["semantic"]["denotation"]:
        missing.append("denotation")
    if not record["phonology"]["ipa"]:
        missing.append("ipa")
    if not record["etymology"]["prose"]:
        missing.append("etymology")
    if not definitions:
        missing.append("definitions")

    if missing:
        flag_incomplete(record, *missing)
    else:
        clear_incomplete(record)

    return record


# ─────────────────────────────────────────────────────────────────────────────
# ACQUIRE — single word
# ─────────────────────────────────────────────────────────────────────────────

def acquire_word(word: str, use_wikipedia: bool = False, force: bool = False) -> Dict:
    word = word.strip().lower()
    if not word:
        return {}

    out_path = word_path(word)

    # Resume: skip if already complete
    if not force and is_complete(word):
        _emit("acquire", "word_skip", {"word": word, "reason": "already_complete"})
        log.info(f"  SKIP  {word}  (complete)")
        return {}

    # If file exists but incomplete — preserve first_encountered (Rabies Principle)
    existing_first_encountered = None
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_first_encountered = existing.get("resonance", {}).get("first_encountered")
        except Exception:
            pass

    _emit("acquire", "word_start", {"word": word})
    log.info(f"  FETCH {word}")
    t0 = time.time()

    fd = fetch_free_dictionary(word)
    dm = fetch_datamuse(word)
    wk = fetch_wiktionary(word)
    wp = fetch_wikipedia(word) if use_wikipedia else {}

    record = assemble(word, fd, dm, wk, wp)

    # Restore first_encountered if this is a re-acquisition (Rabies Principle)
    if existing_first_encountered:
        record["resonance"]["first_encountered"] = existing_first_encountered

    # Write JSON
    out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    elapsed = time.time() - t0
    incomplete = record["resonance"].get("learning_source", "").startswith("__incomplete__")
    status = "word_incomplete" if incomplete else "word_complete"

    _emit("acquire", status, {
        "word": word,
        "elapsed_ms": round(elapsed * 1000),
        "sources": record["meta"]["sources_hit"],
        "flags": record["resonance"].get("learning_source", ""),
    })

    flag_str = f"  [INCOMPLETE: {record['resonance']['learning_source']}]" if incomplete else ""
    log.info(f"  {'INCOMPLETE' if incomplete else 'OK':10}  {word}  "
             f"({len(record['meta']['sources_hit'])} sources, {elapsed:.1f}s){flag_str}")

    return record


# ─────────────────────────────────────────────────────────────────────────────
# BATCH ACQUIRE — list of words
# ─────────────────────────────────────────────────────────────────────────────

def acquire_batch(words: List[str],
                  use_wikipedia: bool = False,
                  force: bool = False) -> None:
    _emit("acquire", "session_start", {"word_count": len(words), "wikipedia": use_wikipedia})
    t0 = time.time()
    ok, incomplete, skipped, errors = 0, 0, 0, 0

    for i, word in enumerate(words, 1):
        log.info(f"[{i}/{len(words)}] {word}")
        try:
            record = acquire_word(word, use_wikipedia=use_wikipedia, force=force)
            if not record:
                skipped += 1
            elif record.get("resonance", {}).get("learning_source", "").startswith("__incomplete__"):
                incomplete += 1
            else:
                ok += 1
        except Exception as e:
            errors += 1
            _emit("acquire", "error", {"word": word, "error": str(e)})
            log.error(f"  ERROR  {word}  {e}")

    elapsed = time.time() - t0
    _emit("acquire", "session_end", {
        "ok": ok, "incomplete": incomplete, "skipped": skipped,
        "errors": errors, "elapsed_s": round(elapsed, 1)
    })
    log.info(f"\nDone: {ok} ok, {incomplete} incomplete, {skipped} skipped, "
             f"{errors} errors — {elapsed:.1f}s total")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

TEST_23 = [
    "the", "run", "water", "red", "abandon",
    "ephemeral", "melancholy", "serendipity", "threshold", "petrichor",
    "sonder", "lacuna", "ineffable", "qualia", "palimpsest",
    "liminal", "apophenia", "hiraeth", "redwood", "synchronicity",
    "bread", "void", "numinous",
]

def main():
    parser = argparse.ArgumentParser(description="HyperWebster acquisition pipeline")
    parser.add_argument("words", nargs="*",
                        help="Words to acquire. If none, runs 23-word test set.")
    parser.add_argument("--file", "-f", metavar="WORDLIST",
                        help="Path to newline-delimited word list file")
    parser.add_argument("--wikipedia", "-w", action="store_true",
                        help="Also query Wikipedia (slower — off by default)")
    parser.add_argument("--force", action="store_true",
                        help="Re-acquire even if already complete")
    parser.add_argument("--output", "-o", metavar="DIR",
                        help="Override output root directory")
    args = parser.parse_args()

    global OUTPUT_ROOT
    if args.output:
        OUTPUT_ROOT = Path(args.output)

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    log.info(f"Output root: {OUTPUT_ROOT}")

    if args.file:
        p = Path(args.file)
        if not p.exists():
            log.error(f"Word list not found: {p}")
            sys.exit(1)
        words = [w.strip() for w in p.read_text().splitlines() if w.strip()]
    elif args.words:
        words = args.words
    else:
        log.info(f"No words specified — running 23-word test set")
        words = TEST_23

    acquire_batch(words, use_wikipedia=args.wikipedia, force=args.force)


if __name__ == "__main__":
    main()
