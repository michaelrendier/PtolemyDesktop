"""
aule/forge/example_acquire_probe.py
=====================================
Example forge script demonstrating how to run a diagnostic
pass of the acquire pipeline and emit events to Aulë's stream.

Drop any experimental script in aule/forge/ and run:
    python aule.py forge aule/forge/example_acquire_probe.py

This script will NOT be included in the public open-source release
of Ptolemy — it is a sandbox artifact.  Production acquire.py remains
untouched.  This script imports production code read-only.

Events emitted to stream:
    channel="acquire"  type="word_start"
    channel="acquire"  type="api_call"
    channel="acquire"  type="word_complete"
    channel="acquire"  type="word_incomplete"
    channel="acquire"  type="summary"
"""

import sys
import json
import time
import os
from pathlib import Path

# ── Resolve Ptolemy root from environment ─────────────────────────
PTOLEMY_ROOT = Path(os.environ.get("PTOLEMY_ROOT", Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(PTOLEMY_ROOT))

# ── Import Aulë stream publisher ──────────────────────────────────
try:
    from aule import stream_event
except ImportError:
    # Fallback: no-op if running outside Aulë
    def stream_event(channel, event_type, payload=None, **kwargs):
        print(json.dumps({"channel": channel, "type": event_type, "payload": payload or {}}))

# ── Test word list (subset of the 23 diagnostic words) ────────────
TEST_WORDS = [
    "hiraeth",      # deliberately incomplete — tests flag system
    "petrichor",    # rare but findable
    "the",          # structural — should be nearly empty
    "river",        # concrete noun
    "synchronicity",# Jungian coinage
]

# ── Simulated acquisition pass (replace with real acquire.py call) ─
def probe_word(word: str) -> dict:
    """
    In a real forge script this would call:
        from callimachus.acquire import fetch_word
    or run acquire.py as a subprocess.

    Here we simulate the stream pattern so you can test Aulë's
    monitoring without a live internet connection.
    """
    stream_event("acquire", "word_start", {"word": word})
    time.sleep(0.05)  # simulate latency

    # Simulate source checks
    sources_tried  = []
    sources_hit    = []
    incomplete     = False

    for source in ["free_dict", "datamuse", "wiktionary"]:
        stream_event("acquire", "api_call", {"word": word, "source": source})
        time.sleep(0.02)

        # Simulate hiraeth missing from free_dict
        if word == "hiraeth" and source == "free_dict":
            stream_event("acquire", "api_miss", {"word": word, "source": source})
            sources_tried.append(source)
            continue

        # Simulate 'the' having minimal data
        if word == "the" and source == "datamuse":
            stream_event("acquire", "api_hit", {"word": word, "source": source, "fields": 2})
            sources_hit.append(source)
            sources_tried.append(source)
            continue

        stream_event("acquire", "api_hit", {"word": word, "source": source, "fields": 8})
        sources_hit.append(source)
        sources_tried.append(source)

    # Flag incomplete if below threshold
    if len(sources_hit) < 2 or word == "hiraeth":
        incomplete = True
        stream_event("acquire", "word_incomplete", {
            "word":    word,
            "reason":  "insufficient sources",
            "sources": sources_hit,
        })
    else:
        stream_event("acquire", "word_complete", {
            "word":    word,
            "sources": sources_hit,
            "fields":  12,
        })

    return {
        "word":       word,
        "complete":   not incomplete,
        "sources":    sources_hit,
        "incomplete": incomplete,
    }

# ── Main run ──────────────────────────────────────────────────────
def main():
    stream_event("acquire", "forge_run_start", {
        "words":    TEST_WORDS,
        "n":        len(TEST_WORDS),
        "mode":     "diagnostic probe",
    })

    results      = []
    complete     = 0
    incomplete_l = []

    for word in TEST_WORDS:
        result = probe_word(word)
        results.append(result)
        if result["complete"]:
            complete += 1
        else:
            incomplete_l.append(word)

    stream_event("acquire", "summary", {
        "total":      len(TEST_WORDS),
        "complete":   complete,
        "incomplete": incomplete_l,
        "rate":       f"{complete/len(TEST_WORDS)*100:.1f}%",
    })

    # Print summary to stdout (also captured by Forge)
    print(f"\nAulë Forge — acquire probe complete")
    print(f"  Words:      {len(TEST_WORDS)}")
    print(f"  Complete:   {complete}")
    print(f"  Incomplete: {incomplete_l}")

if __name__ == "__main__":
    main()
