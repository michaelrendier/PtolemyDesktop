"""
aule_shim.py — Aulë integration for existing Ptolemy modules
=============================================================
Drop this pattern into any Ptolemy Face to make it stream-aware.
Zero dependency on Aulë being running — if Aulë is absent the
stream_event calls become silent no-ops via the fallback.

Usage in acquire.py, pharos.py, etc.:

    # At top of file — three lines, zero coupling
    try:
        from aule import stream_event as _emit
    except ImportError:
        def _emit(channel, event_type, payload=None, **kwargs): pass

    # Then anywhere in the code:
    _emit("acquire", "word_fetched", {"word": word, "source": "wiktionary"})
    _emit("api",     "call_start",   {"endpoint": url, "method": "GET"})
    _emit("api",     "call_end",     {"status": 200,   "ms": elapsed_ms})

Recommended channel names (consistent across all Faces):
    "acquire"       — HyperWebster acquisition pipeline
    "api"           — outbound API calls (Free Dict, Datamuse, Wiktionary, Wikipedia)
    "kryptos"       — encryption/addressing operations
    "hyperwebster"  — Horner indexing and octonion addressing
    "callimachus"   — archival / database writes
    "pharos"        — core routing and dispatch
    "julius_caesar" — LLM face inference
    "bridge"        — mouseion_console / Bridge API calls
    "error"         — any Face, unhandled exceptions

Recommended event_type names:
    word_start / word_complete / word_incomplete / word_skip
    api_call / api_hit / api_miss / api_error / api_ratelimit
    index_start / index_complete / index_collision
    file_open / file_write / file_close
    session_start / session_end
    error / warning / info

Payload conventions:
    Always include the primary key as the first item.
    Use snake_case.  Timestamps are auto-added by Aulë.
    Keep payloads flat where possible — nested dicts are fine
    but Aulë's TUI only shows the first key=value in the list view.
"""

# This file is documentation / a copy-paste reference.
# It is not imported directly.
