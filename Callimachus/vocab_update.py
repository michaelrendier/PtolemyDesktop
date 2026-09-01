#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Callimachus/vocab_update.py — the LIVE vocabulary path.

wordnet_init.py + checkpoint_export.py is the COLD path: JSON checkpoint →
monad_wordnet.bin → the C `ptolemy` binary reads it once at startup.

This is the HOT path. It streams words / text straight into the RUNNING
daemon over its OBSERVE FIFO (spool fallback), where `monad3c_fold_inplace`
folds it in with no restart — and it ties that intake into **The Forge**
(the Aulë Face): every fold is published as an Aulë stream event, so the
Forge can drive it (`aule forge vocab_update.py --wordnet 5000`), replay a
captured stream into it, and audit every write.

TWO HARNESSES, kept apart:
  • the Monad Harness  — VAPMIP/harness.py, the API between the Monad and the
    repos' engines. This file does NOT route through it.
  • the System Process harness — the Tolkien-named Faces (Aulë, Mandos,
    Manwë, Pharos …), independent of the Monad Harness, with the Aulë Face
    (The Forge) as its entry point. `vocab_update` lives here: daemon-direct
    for the write (borrowing only monad_bus's OBSERVE framing), Aulë for
    registration, live view, replay, and audit.

  Callimachus  = the librarian — what vocabulary goes in.
  Aulë / Forge = the craftsman's forge — running it, watching it, auditing it.
  the daemon   = the anvil — the in-place fold.

Usage (direct or under `python Aule/aule.py forge Callimachus/vocab_update.py …`):
    python3 Callimachus/vocab_update.py --wordnet 5000
    python3 Callimachus/vocab_update.py --file some/notes.md
    python3 Callimachus/vocab_update.py --url https://example.com/
    python3 Callimachus/vocab_update.py --text "hiraeth saudade sehnsucht"
    cat corpus.txt | python3 Callimachus/vocab_update.py --stdin
    python3 Callimachus/vocab_update.py --status

Never raises on a missing connection: no daemon → spool; no Aulë → skip the
stream event; no nltk → skip --wordnet; no monad_bus → a local FIFO writer.
Warnings, not faults; the run continues.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, Iterable, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))          # …/PtolemyDesktop/Callimachus
_PDESK = os.path.dirname(_HERE)                             # …/PtolemyDesktop
_THEPLACE = os.path.dirname(_PDESK)                         # …/ThePlace
_VAPMIP = os.path.join(_THEPLACE, 'VAPMIP')
for _p in (_PDESK, _VAPMIP):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_PTOL = os.path.expanduser('~/.ptolemy')
FIFO = os.path.join(_PTOL, 'monad.observe.fifo')
SOCK = os.path.join(_PTOL, 'ptolemy.sock')
SPOOL = os.path.join(_PTOL, 'observe.spool')

# ── Forge (Aulë) settings hook — mirrors Aule/forge_queue.py's pattern ────
VOCAB_UPDATE_SETTINGS = {
    "default_class":   "document",   # INGEST_POLICY class for plain vocab
    "web_class":       "web",        # class for --url pushes
    "chunk_words":     200,          # words per framed OBSERVE message
    "forge_events":    True,         # publish every fold to Aulë's stream
    "forge_channel":   "vocab_update",
}


# ── The Forge tie-in ─────────────────────────────────────────────────────
def _forge(event: str, payload: Dict[str, Any]) -> None:
    """Publish to Aulë's stream. No-op (warn once) if the Face is absent."""
    if not VOCAB_UPDATE_SETTINGS["forge_events"]:
        return
    fn = getattr(_forge, "_impl", "unset")
    if fn == "unset":
        try:
            from Aule.aule import stream_event as fn
        except Exception as e:                              # noqa: BLE001
            sys.stderr.write(f"[vocab_update] Forge (Aulë) unavailable "
                             f"({e}); stream events disabled\n")
            fn = None
        _forge._impl = fn
    if fn is not None:
        try:
            fn(VOCAB_UPDATE_SETTINGS["forge_channel"], event, payload,
               source="Callimachus.vocab_update")
        except Exception:                                   # noqa: BLE001
            pass


# ── the daemon handle ────────────────────────────────────────────────────
class _LocalDaemonWriter:
    """Minimal fallback if monad_bus is not importable — the same OBSERVE
    framing the harness/hooks use: `<class>\\n<line>…\\n.\\n`."""
    name = "c:ptolemy-daemon(local)"

    def __init__(self, fifo: str, sock: str, spool: str) -> None:
        self.fifo, self.sock, self.spool = fifo, sock, spool

    def alive(self) -> bool:
        try:
            fd = os.open(self.fifo, os.O_WRONLY | os.O_NONBLOCK)
            os.close(fd)
            return True
        except OSError:
            return False

    def learn(self, text: str, w_sem: float = 1.0,
              w_ctx: Optional[float] = None, cls: str = "document") -> int:
        sents = [ln.strip() for ln in text.replace("\r", " ").split("\n")
                 if ln.strip()] or [text.strip()]
        msg = (f"{cls}\n" + "\n".join(sents) + "\n.\n").encode("utf-8", "replace")
        try:
            fd = os.open(self.fifo, os.O_WRONLY | os.O_NONBLOCK)
            try:
                os.write(fd, msg)
            finally:
                os.close(fd)
            return len(text.split())
        except OSError:
            try:
                os.makedirs(os.path.dirname(self.spool), exist_ok=True)
                with open(self.spool, "a", encoding="utf-8") as f:
                    f.write(msg.decode("utf-8", "replace"))
                return len(text.split())
            except OSError:
                return 0


def _daemon(fifo: str = FIFO, sock: str = SOCK, spool: str = SPOOL):
    try:
        from monad_bus import CMonadBackend
        return CMonadBackend(fifo, sock, spool)
    except Exception as e:                                  # noqa: BLE001
        sys.stderr.write(f"[vocab_update] monad_bus unavailable ({e}); "
                         "using the local FIFO writer\n")
        return _LocalDaemonWriter(fifo, sock, spool)


# ── the update object ────────────────────────────────────────────────────
class VocabUpdate:
    """Streams vocabulary into the running daemon and reports to The Forge."""

    def __init__(self, cls: Optional[str] = None,
                 fifo: str = FIFO, sock: str = SOCK, spool: str = SPOOL) -> None:
        self.cls = cls or VOCAB_UPDATE_SETTINGS["default_class"]
        self.dae = _daemon(fifo, sock, spool)
        self.calls = 0
        self.words = 0
        self._t0 = time.time()

    # -- core -------------------------------------------------------------
    def alive(self) -> bool:
        return bool(self.dae.alive())

    def push_text(self, text: str, cls: Optional[str] = None) -> int:
        text = (text or "").strip()
        if not text:
            return 0
        c = cls or self.cls
        n = self.dae.learn(text, 1.0, 1.0, cls=c)
        self.calls += 1
        self.words += n
        _forge("fold", {"words": n, "bytes": len(text.encode("utf-8")),
                        "class": c, "via": self.dae.name,
                        "spooled": not self.alive()})
        return n

    def push_words(self, words: Iterable[str], cls: Optional[str] = None,
                   chunk: Optional[int] = None) -> int:
        chunk = chunk or VOCAB_UPDATE_SETTINGS["chunk_words"]
        buf, total = [], 0
        for w in words:
            w = str(w).strip().replace("_", " ")
            if not w:
                continue
            buf.append(w)
            if len(buf) >= chunk:
                total += self.push_text(" ".join(buf), cls)
                buf = []
        if buf:
            total += self.push_text(" ".join(buf), cls)
        return total

    # -- sources -------------------------------------------------------------
    def push_file(self, path: str, cls: Optional[str] = None) -> int:
        try:
            with open(path, "rb") as f:
                body = f.read()
        except OSError as e:
            sys.stderr.write(f"[vocab_update] --file {path}: {e}\n")
            return 0
        text = body.decode("utf-8", "replace")
        if path.lower().endswith((".htm", ".html")) or "<html" in text[:2048].lower():
            try:
                from monad_browse import strip_html
                text = strip_html(body, "text/html", path)
            except Exception:                              # noqa: BLE001
                pass
        return self.push_text(text, cls or VOCAB_UPDATE_SETTINGS["default_class"])

    def push_url(self, url: str) -> int:
        try:
            from monad_browse import fetch, strip_html
        except Exception as e:                             # noqa: BLE001
            sys.stderr.write(f"[vocab_update] --url needs monad_browse ({e})\n")
            return 0
        f = fetch(url)
        if f.status == 0 or f.status >= 400:
            sys.stderr.write(f"[vocab_update] --url {url}: fetch {f.status} "
                             f"{f.error}\n")
            return 0
        prose = strip_html(f.body, f.content_type, f.url_final)
        return self.push_text(prose, VOCAB_UPDATE_SETTINGS["web_class"])

    def push_wordnet_lemmas(self, limit: Optional[int] = None,
                            cls: Optional[str] = None) -> int:
        """The live analogue of wordnet_init.py pass 1 — stream surface
        forms into the running daemon instead of a cold checkpoint."""
        wn = None
        try:
            from nltk.corpus import wordnet as wn
            _ = wn.all_synsets  # touch → triggers LookupError here if corpus missing
        except Exception as e:                             # noqa: BLE001
            sys.stderr.write(f"[vocab_update] --wordnet needs nltk + the "
                             f"wordnet corpus ({e})\n")
            return 0

        def _lemmas():
            seen = set()
            for i, syn in enumerate(wn.all_synsets()):
                if limit is not None and i >= limit:
                    return
                for name in syn.lemma_names():
                    w = name.replace("_", " ")
                    if w not in seen:
                        seen.add(w)
                        yield w

        _forge("wordnet_begin", {"limit": limit})
        n = self.push_words(_lemmas(), cls or VOCAB_UPDATE_SETTINGS["default_class"])
        _forge("wordnet_end", {"words": n})
        return n

    def push_stdin(self, cls: Optional[str] = None) -> int:
        return self.push_text(sys.stdin.read(),
                              cls or VOCAB_UPDATE_SETTINGS["default_class"])

    # -- status / Forge registration ---------------------------------------
    def status(self) -> Dict[str, Any]:
        try:
            spool_bytes = os.path.getsize(SPOOL)
        except OSError:
            spool_bytes = 0
        return {
            "daemon_alive": self.alive(),
            "daemon_via": self.dae.name,
            "fifo": FIFO, "spool_bytes": spool_bytes,
            "forge_available": getattr(_forge, "_impl", None) not in (None, "unset"),
            "pushed_calls": self.calls, "pushed_words": self.words,
            "uptime_s": round(time.time() - self._t0, 1),
        }

    def register_with_forge(self) -> None:
        """Announce this live vocab sink to The Forge so `aule probe` /
        `aule replay` can target it by name."""
        _forge("register", {"sink": "Callimachus.vocab_update.VocabUpdate",
                            "daemon_via": self.dae.name,
                            "daemon_alive": self.alive(),
                            "settings": VOCAB_UPDATE_SETTINGS})

    @classmethod
    def forge_sink(cls, event_type: str, payload: Dict[str, Any]) -> int:
        """Callback for the Forge / a stream tap: hand it any text-producing
        event from an `Aule/forge/` run and it goes into the live Monad,
        audited. `payload` must carry 'text' (or 'words')."""
        vu = cls()
        if "text" in payload:
            return vu.push_text(str(payload["text"]),
                                payload.get("class"))
        if "words" in payload:
            return vu.push_words(payload["words"], payload.get("class"))
        return 0


# ── CLI (also the Forge-drop entry point) ────────────────────────────────
def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wordnet", nargs="?", type=int, const=0, default=None,
                    metavar="N", help="stream WordNet lemmas (N synsets, 0=all)")
    ap.add_argument("--file", metavar="PATH", help="stream a file (html stripped)")
    ap.add_argument("--url", metavar="URL", help="fetch + strip + stream a page")
    ap.add_argument("--text", metavar="STR", help="stream a literal string")
    ap.add_argument("--stdin", action="store_true", help="stream stdin")
    ap.add_argument("--cls", metavar="CLASS", default=None,
                    help="INGEST_POLICY class (default: document)")
    ap.add_argument("--status", action="store_true", help="print status and exit")
    a = ap.parse_args(argv)

    vu = VocabUpdate(cls=a.cls)
    vu.register_with_forge()

    if a.status:
        import json
        print(json.dumps(vu.status(), indent=2))
        return 0

    if not vu.alive():
        sys.stderr.write("[vocab_update] daemon not reachable on "
                         f"{FIFO} — writes go to the spool "
                         f"({SPOOL}) for the daemon to drain later\n")

    n = 0
    if a.wordnet is not None:
        n += vu.push_wordnet_lemmas(limit=(a.wordnet or None))
    if a.file:
        n += vu.push_file(a.file)
    if a.url:
        n += vu.push_url(a.url)
    if a.text:
        n += vu.push_text(a.text)
    if a.stdin:
        n += vu.push_stdin()
    if a.wordnet is None and not any((a.file, a.url, a.text, a.stdin)):
        ap.print_help()
        return 2

    st = vu.status()
    sys.stderr.write(f"[vocab_update] {n} words in {vu.calls} folds → "
                     f"{st['daemon_via']} "
                     f"({'live' if st['daemon_alive'] else 'spooled'}); "
                     f"Forge={'on' if st['forge_available'] else 'off'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
