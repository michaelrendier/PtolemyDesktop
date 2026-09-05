#!/usr/bin/env python3
"""
ptolemy_console.py — PtolemyDesktop Core.

The Curses Chat Window + the Derivation UI + the harness, in one console app.
The Monad runs it all from inside the harness.  This is the tty side; the Qt /
PGui side connects over a pty and imports it.

    Ptolemy = the combined identity of two harnesses that talk through this
    console:

        ACTIVE  (Alexandrian)  — VAPMIP/harness.py.  Tool calls, renders,
                                 collaboration.  The Monad attaches here.
        SUPPORT (Tolkien)      — the Diagnostic Support Harness = AULE, and Aule
                                 has THE FORGE.  Face process monitorings write
                                 radio-check lines into the console when a
                                 process drifts far enough to fault, and make
                                 the necessary adjustment.

    The MONAD is the STITCHBOARD OPERATOR.  It connects to both harnesses and
    routes between them.  One object holds information (monad), display
    (console sink) and diagnostics (support) — one monolithic calculation.

Tabs (standalone curses):
    THE CHAT TAB       — this window: Ptolemy + the faces + the monad.
    THE VALAQUENTA TAB — the DerivationBrowser, loaded directly. Its own tab,
                         not routed through any face.
    GENERATIONAL LINEAGE — placeholder until the engine is wired.
    THE ARCHIMEDES TAB — the maths-catalogue browser. Only present when the
                         console is EMBEDDED in PtolemyDesktop
                         (PtolemyConsole(..., embedded=True), or the
                         PTOLEMY_DESKTOP env var on a spawned subprocess).
                         Standalone, Archimedes is only the Monad's local
                         maths worker (answer_established / act), no tab.

Installed in PtolemyDesktop the console can also run HIBERNATED — `--port`
mode, no curses — with the desktop rendering the tabs and driving the console
over the pty.

Run:
    python3 ptolemy_console.py            # standalone curses app
    python3 ptolemy_console.py --port     # hibernated: frame protocol, no curses
    python3 ptolemy_console.py --selftest # headless: route a few turns, print

Runs under PtolemyDesktop/.venv (layered on ValaQuenta/.venv).  All cross-repo
imports are warn-not-fault: a missing Monad -> a stand-in; a missing engine
registry -> the chat still runs.
"""
from __future__ import annotations

import argparse
import curses
import difflib
import fnmatch
import os
import pathlib
import queue
import sys
import textwrap
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

NAME = "ptolemy"


# ══════════════════════════════════════════════════════════════════════════════
#  Faces — chat-room identities (Cody, 2026-09-01)
# ──────────────────────────────────────────────────────────────────────────────
#  The faces are NOT processes.  They are identities in the Chat Tab: they post
#  passive reportings and warnings, and Ptolemy (the Monad as stitchboard
#  operator) weighs their opinions and routes any action through his harness.
#  Only Archimedes takes direct action.
#
#      monad  >  harness  >  chat window  <  passive reportings & warnings
#                                          <  hardening guided by intrusion type
#
#  The Face API is the layer of separation — a face never touches the monad or
#  the harness directly.
# ══════════════════════════════════════════════════════════════════════════════
FACE_ROLES = {
    "Aule":       "The Forge — process & backlog monitor (passive)",
    "Mandos":     "The Watchdog — heartbeat & supervisor priority (passive)",
    # Demetrius of Phaleron advised Ptolemy I and organised the Library of
    # Alexandria — its first Librarian.  Phaleron advises Ptolemy the same way.
    "Phaleron":   "The Librarian — Tool Master, catalogue & user-interaction portal (passive, advises)",
    "Archimedes": "The Encyclopedia — reference; the one face that acts",
}


@dataclass
class FacePost:
    who: str
    level: str = "info"          # info | warn | hardening
    text: str = ""
    intrusion: str = ""          # drift | backlog | heartbeat | tool | probe | ...
    weight: float = 0.0
    stamp: str = field(default_factory=lambda: time.strftime("%H:%M:%S"))

    def line(self) -> str:
        mark = {"info": "", "warn": " ⚠", "hardening": " ⚠ HARDENING"}[self.level]
        tag = f" [{self.intrusion}]" if self.intrusion and self.level != "info" else ""
        return f"« {self.who} »{mark}{tag} {self.text}"


# ── Ptolemy's judgement on a support-harness report ──────────────────────────
#  Every un-acked warn / hardening post from the support room gets a judgement:
#  Ptolemy weighs the post's drift, its level, and the other faces' opinions,
#  reaches one decision from a fixed vocabulary, and posts a structured line
#  back into the Chat Tab.  That line follows JUDGEMENT_GRAMMAR verbatim so the
#  SUPPORT HARNESS can ingest Ptolemy's response in turn (a later build).
JUDGEMENT_GRAMMAR = ("« Ptolemy » judgement [<face>/<intrusion>]: <reason> "
                     "-> decision: <DECISION>  action: <action>")
DECISIONS = ("HOLD", "THROTTLE", "HARDEN", "ESCALATE", "DEFER")


@dataclass
class Judgement:
    face: str
    intrusion: str
    decision: str            # one of DECISIONS
    action: str
    reason: str
    stamp: str = field(default_factory=lambda: time.strftime("%H:%M:%S"))

    def line(self) -> str:
        return (f"« {NAME.capitalize()} » judgement [{self.face}/{self.intrusion}]: "
                f"{self.reason} -> decision: {self.decision}  action: {self.action}")


class Face:
    """A chat-room identity.  `probe()` -> drift in [0,1]; past the harness
    threshold the face posts a HARDENING line whose adjustment is classified by
    intrusion type.  `opinion(topic)` -> (stance, weight) for Ptolemy to weigh.
    Only an `active` face (Archimedes) exposes `act()`."""

    def __init__(self, name: str, role: str = "",
                 probe: Optional[Callable[[], float]] = None,
                 adjust: Optional[Callable[[], str]] = None,
                 intrusion_of: Optional[Callable[[float], str]] = None,
                 opinion: Optional[Callable[[str], Tuple[str, float]]] = None,
                 act: Optional[Callable[[str], str]] = None,
                 tab: Optional[Callable[[Any], None]] = None,
                 active: bool = False) -> None:
        self.name = name
        self.role = role or FACE_ROLES.get(name, "(registered)")
        self._probe = probe or (lambda: 0.0)
        self._adjust = adjust or (lambda: "logged; no automatic action")
        self._intrusion_of = intrusion_of or (lambda d: "drift")
        self._opinion = opinion
        self._act = act
        self._tab = tab                    # this face runs a full-screen tab
        self.active = active
        self.last_drift = 0.0

    @property
    def runs_tab(self) -> bool:
        return self._tab is not None

    def run_tab(self, scr: Any) -> None:
        if self._tab is None:
            raise RuntimeError(f"{self.name} has no tab")
        self._tab(scr)

    def report(self, threshold: float) -> FacePost:
        try:
            d = float(self._probe())
        except Exception as e:                                    # noqa: BLE001
            return FacePost(self.name, "warn", f"probe error — {e}", "probe")
        self.last_drift = d
        if d > threshold:
            return FacePost(self.name, "hardening", self._adjust(),
                            self._intrusion_of(d), weight=d)
        return FacePost(self.name, "info", f"nominal (drift {d:.2f})", weight=d)

    def opinion(self, topic: str) -> Tuple[str, float]:
        if self._opinion:
            try:
                return self._opinion(topic)
            except Exception:                                     # noqa: BLE001
                pass
        # no topical view: a weak voice, weaker still if the face is drifting,
        # so a face with a real stance on the topic leads the poll
        return ("no strong view", round(0.2 * max(0.0, 1.0 - self.last_drift), 2))

    def act(self, request: str) -> Optional[str]:
        if self.active and self._act:
            try:
                return self._act(request)
            except Exception as e:                                # noqa: BLE001
                return f"({self.name} error: {e})"
        return None

    # ── Face API: code access (read anytime; writes are Ptolemy-gated) ──────
    def read_code(self, gate: "CodeGate", path: str) -> str:
        return gate.read(path)

    def propose(self, gate: "CodeGate", path: str, new_text: str,
                reason: str) -> "Proposal":
        """Request a code write.  Returns a PENDING Proposal — nothing lands on
        disk until Ptolemy approves it (`StitchBoard` `/approve`)."""
        return gate.propose(self.name, path, new_text, reason)


# ══════════════════════════════════════════════════════════════════════════════
#  CodeGate — faces may read repo code and PROPOSE writes; Ptolemy approves
# ──────────────────────────────────────────────────────────────────────────────
#  "faces get code writing privileges ... but it's locked behind Ptol's
#  control" (Cody, 2026-09-01).  A face can read any permitted file and queue a
#  full-file replacement with a reason; the diff sits pending until Ptolemy
#  approves it, and only then is it written — original backed up first.
#  .py only; never .git / .venv / __pycache__ / *.bin / *_token* / *_secret*.
# ══════════════════════════════════════════════════════════════════════════════
@dataclass
class Proposal:
    pid: int
    face: str
    path: str                    # gate-relative
    reason: str
    new_text: str
    diff: str
    stamp: str = field(default_factory=lambda: time.strftime("%H:%M:%S"))
    status: str = "pending"      # pending | applied | rejected
    note: str = ""

    def stat(self) -> Tuple[int, int]:
        adds = sum(1 for l in self.diff.splitlines()
                   if l.startswith("+") and not l.startswith("+++"))
        dels = sum(1 for l in self.diff.splitlines()
                   if l.startswith("-") and not l.startswith("---"))
        return adds, dels


class CodeGate:
    ALLOW_EXT = {".py"}
    DENY_PARTS = {".git", ".venv", "__pycache__", "secrets", "node_modules"}
    DENY_GLOBS = ("*_token*", "*_secret*", "*_key*", "*_credential*", "*.bin")

    def __init__(self, root: str) -> None:
        self.root = pathlib.Path(root).resolve()
        self._q: Dict[int, Proposal] = {}
        self._n = 0

    def _resolve(self, path: str) -> pathlib.Path:
        p = (self.root / path).resolve()
        if p != self.root and self.root not in p.parents:
            raise ValueError(f"outside scope: {path}")
        if any(part in self.DENY_PARTS for part in p.parts):
            raise ValueError(f"denied path: {path}")
        if any(fnmatch.fnmatch(p.name, g) for g in self.DENY_GLOBS):
            raise ValueError(f"denied name: {p.name}")
        if p.suffix not in self.ALLOW_EXT:
            raise ValueError(f"file type not permitted: {p.suffix or '(none)'}")
        return p

    def rel(self, p: pathlib.Path) -> str:
        return str(p.relative_to(self.root))

    def read(self, path: str) -> str:
        return self._resolve(path).read_text()

    def propose(self, face: str, path: str, new_text: str,
                reason: str) -> Proposal:
        p = self._resolve(path)
        old = p.read_text() if p.exists() else ""
        diff = "".join(difflib.unified_diff(
            old.splitlines(True), new_text.splitlines(True),
            fromfile=f"a/{self.rel(p)}", tofile=f"b/{self.rel(p)}"))
        if not diff:
            raise ValueError("no change")
        self._n += 1
        pr = Proposal(self._n, face, self.rel(p), reason, new_text, diff)
        self._q[pr.pid] = pr
        return pr

    def pending(self) -> List[Proposal]:
        return [pr for pr in self._q.values() if pr.status == "pending"]

    def get(self, pid: int) -> Optional[Proposal]:
        return self._q.get(pid)

    def approve(self, pid: int, by: str = NAME) -> str:
        pr = self._q.get(pid)
        if not pr or pr.status != "pending":
            return f"(no pending proposal #{pid})"
        p = self._resolve(pr.path)
        if p.exists():
            bak = p.with_suffix(p.suffix + f".bak.{int(time.time())}")
            bak.write_text(p.read_text())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(pr.new_text)
        pr.status, pr.note = "applied", f"by {by}"
        a, d = pr.stat()
        return f"applied #{pid} «{pr.face}» {pr.path}  (+{a} -{d})"

    def reject(self, pid: int, why: str = "") -> str:
        pr = self._q.get(pid)
        if not pr or pr.status != "pending":
            return f"(no pending proposal #{pid})"
        pr.status, pr.note = "rejected", why or "rejected"
        return f"rejected #{pid} «{pr.face}» {pr.path}"


def _int(s: str, default: int = -1) -> int:
    try:
        return int(str(s).strip())
    except (TypeError, ValueError):
        return default


def _coerce_reply(gen: Any) -> str:
    """Best-effort text out of whatever Engine.generate returns."""
    if gen is None:
        return ""
    if isinstance(gen, str):
        return gen.strip()
    if isinstance(gen, dict):
        for k in ("text", "reply", "response", "output", "utterance", "say"):
            if gen.get(k):
                return str(gen[k]).strip()
        return ""
    if isinstance(gen, (list, tuple)):
        parts = [_coerce_reply(x) for x in gen]
        return " ".join(p for p in parts if p).strip() or (
            " ".join(str(x) for x in gen)[:200])
    return str(gen).strip()


# ══════════════════════════════════════════════════════════════════════════════
#  The Monad
# ══════════════════════════════════════════════════════════════════════════════
class MonadLink:
    """The speaking kernel.  Real VAPMIP Engine if importable, else a stand-in
    (PtolemyDesktop gets stand-in monad basic functionality)."""

    def __init__(self) -> None:
        self.kind = "stand-in"
        self._engine = None
        self.enabled = True
        try:
            from VAPMIP.monad import Engine                       # noqa: PLC0415
            self._engine = Engine()
            self.kind = f"VAPMIP.Engine v{getattr(self._engine, 'version', '?')}"
        except Exception as e:                                    # noqa: BLE001
            self._why = f"{type(e).__name__}: {e}"

    def say(self, text: str) -> Tuple[str, Dict[str, Any]]:
        if not self.enabled:
            return ("(monad detached — harness only)", {"via": "detached"})
        if self._engine is not None:
            try:
                gen = self._engine.generate(text)
                reply = _coerce_reply(gen)
                if not reply:
                    reply = f"(monad returned {type(gen).__name__}: {str(gen)[:200]})"
                return reply, {"via": "generate"}
            except Exception as e:                                # noqa: BLE001
                return f"(monad error: {type(e).__name__}: {e})", {"via": "error"}
        # stand-in: acknowledge + reflect structure, no fabrication of content
        toks = text.split()
        return (f"[stand-in monad] heard {len(toks)} tokens; "
                f"lead='{toks[0] if toks else ''}'. Attach VAPMIP for a real reply.",
                {"via": "stand-in"})

    def status(self) -> str:
        return self.kind


class BoxKiteMonad:
    """The speaking construction the user calls "nearly flawless" —
    VAPMIP/rotary_rerun_boxkite_monad.py's RotaryBoxKiteMonad. Heavy import
    (WordNet + the combined store), so it loads lazily on the first say() and
    stays resident. Falls back to `nxt` (HarnessMonad / MonadLink) on failure."""

    def __init__(self, nxt: Any) -> None:
        self._nxt = nxt
        self._monad = None
        self._tried = False
        self.enabled = True
        self.kind = "rotary_rerun_boxkite (loading on first turn)"

    def _load(self) -> None:
        if self._tried:
            return
        self._tried = True
        try:
            import contextlib
            import io
            # rotary_rerun_boxkite_monad.py imports its siblings top-level
            # ("import ptolemy_monad", "from harness import Harness"), so VAPMIP
            # itself must be on the path and it imports as a top-level module.
            vp = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "VAPMIP")
            if vp not in sys.path:
                sys.path.insert(0, vp)
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                from rotary_rerun_boxkite_monad import RotaryBoxKiteMonad
                from harness import Harness
                self._monad = RotaryBoxKiteMonad(harness=Harness())
            sig = getattr(getattr(self._monad, "box_kite", None), "signature", "?")
            self.kind = f"rotary_rerun_boxkite (box-kite sig {sig})"
        except Exception as e:                                    # noqa: BLE001
            self.kind = f"rotary_rerun_boxkite unavailable ({type(e).__name__}) → {self._nxt.status()}"

    def say(self, text: str) -> Tuple[str, Dict[str, Any]]:
        if not self.enabled:
            return ("(monad detached — harness only)", {"via": "detached"})
        self._load()
        if self._monad is not None:
            try:
                # Harness.present() falls back to a plain print() when no
                # 'viewport' Face is registered (none is, here) — under
                # curses raw mode that print lands straight on the terminal
                # at wherever the cursor sits (the input line), corrupting
                # the screen. Swallow it; enc.response is the real answer.
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()), \
                     contextlib.redirect_stderr(io.StringIO()):
                    enc = self._monad.process_input(text, user_id="cody")
                reply = enc.response or "(box-kite returned no words)"
                # the templated sentence is one of 13 fixed shapes
                # (direction -> "this is a kind of {}." etc); the actual
                # selected vocabulary is enc.words_out — show both, so a
                # repeated template shape doesn't read as a repeated answer.
                if enc.words_out:
                    reply += f"   [{enc.direction} · words: {', '.join(enc.words_out)}]"
                return reply, {"via": "boxkite", "direction": enc.direction,
                               "words_out": enc.words_out}
            except Exception as e:                                # noqa: BLE001
                return (f"(box-kite error: {type(e).__name__}: {e})", {"via": "error"})
        return self._nxt.say(text)

    def status(self) -> str:
        return self.kind


# ══════════════════════════════════════════════════════════════════════════════
#  Harness link — the frame seam to a resident C monad (`ptol -w`)
# ──────────────────────────────────────────────────────────────────────────────
#  ptol.c forks this console onto the tty and keeps the other end of a
#  socketpair, answering `say` frames with the sedenion word shadow through
#  PtolC/monad_harness.c.  Newline-delimited JSON, matching console_link.py.
# ══════════════════════════════════════════════════════════════════════════════
class HarnessLink:
    def __init__(self, fd: int) -> None:
        import socket                                            # noqa: PLC0415
        # the fd is one end of ptol.c's AF_UNIX socketpair — not seekable, so
        # wrap it as a socket and take a read/write text stream off it.
        self._sock = socket.socket(fileno=fd)
        self._f = self._sock.makefile("rw", encoding="utf-8", newline="\n")
        self._id = 0
        self._lock = threading.Lock()

    def send(self, frame: Dict[str, Any]) -> None:
        import json                                              # noqa: PLC0415
        with self._lock:
            self._f.write(json.dumps(frame, default=str) + "\n")
            self._f.flush()

    def rpc(self, frame: Dict[str, Any], want: str = "chat",
            timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        import json                                              # noqa: PLC0415
        self._id += 1
        rid = self._id
        self.send({**frame, "id": rid})
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._f.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                f = json.loads(line)
            except ValueError:
                continue
            if f.get("t") in (want, "error") and f.get("id") in (None, rid):
                return f
        return None


class HarnessMonad:
    """MonadLink-shaped: routes say() to the resident C monad, falls back to
    the in-process `local` MonadLink if the link is silent."""

    def __init__(self, link: HarnessLink, local: "MonadLink") -> None:
        self._link = link
        self._local = local
        self.enabled = True
        self.kind = "ptol -w (resident C monad)"
        self.last_geom: Dict[str, Any] = {}

    def say(self, text: str) -> Tuple[str, Dict[str, Any]]:
        if not self.enabled:
            return ("(monad detached — harness only)", {"via": "detached"})
        try:
            f = self._link.rpc({"t": "say", "text": text}, want="chat")
        except Exception:                                        # noqa: BLE001
            f = None
        if f and f.get("t") == "chat":
            g = {k: f[k] for k in ("sigma", "gamma", "primes", "mode") if k in f}
            self.last_geom = g
            tail = ""
            if g.get("primes"):
                tail = (f"   [σ={float(g.get('sigma', 0)):.3f} "
                        f"Γ={float(g.get('gamma', 0)):+.3f} · primes {g['primes']}]")
            return (str(f.get("text", "")).strip() + tail, {"via": "harness", "geom": g})
        return self._local.say(text)

    def status(self) -> str:
        return self.kind


# ══════════════════════════════════════════════════════════════════════════════
#  SUPPORT harness  (Tolkien / Diagnostic Support)
# ══════════════════════════════════════════════════════════════════════════════
class SupportHarness:
    """The faces' room.  A slow periodic poll (PERIOD) checks each face; it only
    posts to `sink` (the Chat Tab) when a face is DRIFTING or errored — a
    nominal check-in says nothing.  `latest` still records every check so
    Ptolemy can review and `/radio` can print the full roster on demand.
    Nothing here acts — Ptolemy routes any action through the active harness,
    and only Archimedes has an `act()` of its own.  (Cody, 2026-09-04: their
    job is to report when drift starts, not to update the chat every few
    seconds.)"""

    THRESHOLD = 0.25
    PERIOD = 3 * 60 * 60      # 3 hours — a drift watch, not a heartbeat

    def __init__(self, sink: "queue.Queue[str]",
                 registry_getter: Optional[Callable[[], Any]] = None) -> None:
        self._sink = sink
        self._get_reg = registry_getter or (lambda: None)
        self.faces: Dict[str, Face] = {}
        self.latest: Dict[str, FacePost] = {}
        self._run = False
        self._thr: Optional[threading.Thread] = None
        # some Aule/Mandos modules print on import; keep the screen clean.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            self._wire_faces()

    # ── build the four faces ────────────────────────────────────────────────
    def _wire_faces(self) -> None:
        self.add_face(Face("Aule", probe=self._aule_probe,
                           adjust=lambda: "the Forge is throttling intake until backlog clears",
                           intrusion_of=lambda d: "backlog" if d < 0.6 else "flood"))
        self.add_face(Face("Mandos", probe=self._mandos_probe,
                           adjust=lambda: "raised supervisor priority over Aule",
                           intrusion_of=lambda d: "heartbeat"))
        # Phaleron — the Librarian: passive, fed tool/portal signals by the
        # console via `note_portal()`; advises when asked.
        self._portal_load = 0.0
        self.add_face(Face("Phaleron", probe=lambda: self._portal_load,
                           adjust=lambda: "narrowed the tool surface to the vetted catalogue",
                           intrusion_of=lambda d: "tool",
                           opinion=self._phaleron_opinion))
        # Archimedes — the Encyclopedia: the one active face; RUNS the
        # ValaQuenta Tab (guided tour / mathematical encyclopedia /
        # supercalculator).  Standalone -> run_tab draws the DerivationBrowser;
        # hibernated (console installed in the desktop) -> act() answers the
        # same three modes as text/frames and the desktop renders the tab.
        self.add_face(Face("Archimedes", probe=lambda: 0.0,
                           opinion=self._archimedes_opinion,
                           act=self._archimedes_act,
                           tab=self._archimedes_tab, active=True))

    def _aule_probe(self) -> float:
        d = 0.0
        try:
            from Aule import forge_queue                          # noqa: PLC0415
            fq = forge_queue.ForgeQueue()
            cap = forge_queue.FORGE_SETTINGS.get("max_queue_depth", 64)
            d = max(d, min(1.0, fq.depth() / max(1, cap)))
        except Exception:                                         # noqa: BLE001
            pass
        try:
            import contextlib
            import io
            from Aule import aule as _aule                        # noqa: PLC0415
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                s = _aule.status_summary()
            if isinstance(s, dict):
                d = max(d, float(s.get("drift", s.get("worst", 0.0)) or 0.0))
        except Exception:                                         # noqa: BLE001
            pass
        return d

    @staticmethod
    def _mandos_probe() -> float:
        try:
            from Mandos import mandos_watchdog                    # noqa: PLC0415
            gb = getattr(mandos_watchdog, "_last_beat", None)
            if not gb:
                return 0.0
            age = time.monotonic() - gb
            return min(1.0, age / (mandos_watchdog.HEARTBEAT_INTERVAL
                                   * mandos_watchdog.MISSED_BEATS))
        except Exception:                                         # noqa: BLE001
            return 0.0

    def _phaleron_opinion(self, topic: str) -> Tuple[str, float]:
        t = topic.lower()
        if any(w in t for w in ("tool", "run", "open", "file", "user", "ui")):
            return ("in my catalogue — proceed via the portal", 0.9)
        return ("outside the catalogue — defer to Archimedes", 0.4)

    def _archimedes_opinion(self, topic: str) -> Tuple[str, float]:
        t = topic.lower()
        if any(w in t for w in ("math", "maths", "physics", "prove", "derive",
                                "equation", "why", "theorem", "engine", "proof")):
            return ("this is reference — I can speak to it", 0.9)
        return ("not a reference question", 0.3)

    # ── Archimedes runs the ValaQuenta Tab ─────────────────────────────────
    def _archimedes_find(self, reg, ql: str):
        """(engine, equation | None) referenced in the query, or (None, None)."""
        for name in reg.list_modules():
            if name in ql or name.replace("_", " ") in ql:
                for full in reg.list_equations(name):
                    en = full.split(".", 1)[1]
                    if en in ql:
                        return name, en
                return name, None
        return None, None

    def _archimedes_act(self, request: str) -> str:
        """Text form of the ValaQuenta Tab — three modes:
        supercalculator (run/compute), guided tour (prove/derive/how),
        encyclopedia (default).  Used standalone for `/enc` and by the desktop
        when the console is hibernated."""
        reg = self._get_reg()
        if reg is None:
            return "Archimedes: no ValaQuenta registry loaded."
        q = request.strip()
        ql = q.lower()
        engine, eq = self._archimedes_find(reg, ql)
        mode = ("calc" if any(w in ql for w in ("run ", "compute", "calc", "="))
                else "tour" if any(w in ql for w in ("prove", "derive", "tour",
                                                     "guide", " how ", "steps",
                                                     "proof"))
                else "enc")

        if engine is None:
            hits = [n for n in reg.list_modules()
                    if any(w and w in n for w in ql.split())]
            if hits:
                return "Archimedes: which engine — " + ", ".join(hits[:12])
            return (f"Archimedes catalogues {len(reg.list_modules())} engines; "
                    f"none matched '{q[:50]}'. Name one, or Tab into the "
                    f"ValaQuenta Tab.")

        mod = reg.get_module(engine)

        if mode == "calc":
            if eq is None:
                eqs = [e.split(".", 1)[1] for e in reg.list_equations(engine)]
                return (f"Archimedes ▸ {mod.display_name}: name the equation — "
                        + ", ".join(eqs[:14]))
            try:
                r = reg.run(f"{engine}.{eq}", {})
                val = r.get("result", r) if isinstance(r, dict) else r
                return (f"Archimedes ▸ supercalculator  {engine}.{eq} =\n"
                        f"  {str(val)[:600]}")
            except Exception as e:                                # noqa: BLE001
                return (f"Archimedes ▸ {engine}.{eq}: needs parameters / did "
                        f"not run — {type(e).__name__}: {e}")

        if mode == "tour":
            try:
                from ValaQuenta.engine.proof_locale import (          # noqa: PLC0415
                    render_guided, proof_catalog)
                if proof_catalog(engine):
                    return "Archimedes ▸ guided tour\n" + render_guided(engine, eq)
            except Exception:                                     # noqa: BLE001
                pass
            return (f"Archimedes ▸ {mod.display_name}: no proof_locale catalog "
                    f"yet — Tab into the ValaQuenta Tab, key p, for the "
                    f"declaration of {eq or 'any equation'}.")

        # encyclopedia
        out = [f"Archimedes ▸ {mod.display_name}  v{mod.version}",
               f"  {mod.process_description}"]
        try:
            from ValaQuenta.engine import manifest as _mf              # noqa: PLC0415
            man = _mf.load(engine) or _mf.scaffold(engine, mod)
            p = man.get("provenance", {})
            if p.get("status_label"):
                out.append(f"  status : {p['status_label']}")
            if p.get("origin"):
                out.append(f"  origin : {p['origin'][:220]}")
            w = p.get("wiki", {})
            if w.get("valaquenta"):
                out.append(f"  wiki   : {w['valaquenta']}")
            cs = man.get("environment", {}).get("constants", [])
            if cs:
                out.append("  consts : "
                           + ", ".join(c.get("symbol", "?") for c in cs))
        except Exception:                                         # noqa: BLE001
            pass
        out.append(f"  {len(reg.list_equations(engine))} equations — "
                   f"'/enc run {engine}.<eq>' to compute, '/enc tour {engine}' "
                   f"for the walk, or Tab for the full tab.")
        return "\n".join(out)

    def _archimedes_tab(self, scr: Any) -> None:
        """Standalone (curses) form of the ValaQuenta Tab — the DerivationBrowser."""
        reg = self._get_reg()
        if reg is None:
            raise RuntimeError("no ValaQuenta registry")
        from ValaQuenta.engine.console_curses import DerivationBrowser  # noqa: PLC0415
        DerivationBrowser(scr, reg).run()

    # ── registry ───────────────────────────────────────────────────────────
    def add_face(self, face: Face) -> None:
        self.faces[face.name] = face

    def register(self, name: str, probe: Callable[[], float],
                 adjust: Optional[Callable[[], str]] = None) -> None:
        """Back-compat: register a bare probe/adjust as a passive face."""
        self.add_face(Face(name, role="(registered)", probe=probe, adjust=adjust))

    def note_portal(self, load: float) -> None:
        """Console feeds Phaleron the current tool/user-portal load in [0,1]."""
        self._portal_load = max(0.0, min(1.0, float(load)))

    # ── the poll ───────────────────────────────────────────────────────────
    def radio_check(self, quiet: bool = False) -> List[str]:
        """Check every face. `quiet=True` (the periodic poll) returns only the
        faces that are DRIFTING or errored; `/radio` calls it plain and gets
        the full nominal roster."""
        lines: List[str] = []
        for name, face in self.faces.items():
            post = face.report(self.THRESHOLD)
            self.latest[name] = post
            if quiet and post.level == "info":       # nominal check-in — silent
                continue
            lines.append(f"[{post.stamp}] {post.line()}")
        if not self.faces and not quiet:
            lines.append(f"[{time.strftime('%H:%M:%S')}] no faces — support room empty")
        return lines

    def opinions(self, topic: str) -> List[Tuple[str, str, float]]:
        out = []
        for name, face in self.faces.items():
            stance, weight = face.opinion(topic)
            out.append((name, stance, float(weight)))
        return sorted(out, key=lambda r: -r[2])

    def _loop(self) -> None:
        while self._run:
            for ln in self.radio_check(quiet=True):   # drift / errors only
                self._sink.put(ln)
            for _ in range(int(self.PERIOD * 4)):
                if not self._run:
                    break
                time.sleep(0.25)

    def start(self) -> None:
        if self._thr:
            return
        self._run = True
        self._thr = threading.Thread(target=self._loop, daemon=True)
        self._thr.start()

    def stop(self) -> None:
        self._run = False

    def status(self) -> str:
        if not self.latest:
            return f"{len(self.faces)} faces, no poll yet"
        worst = max(p.weight for p in self.latest.values())
        warns = sum(1 for p in self.latest.values() if p.level != "info")
        return (f"{len(self.faces)} faces, worst drift {worst:.2f}"
                + (f", {warns} warning(s)" if warns else ""))


# ══════════════════════════════════════════════════════════════════════════════
#  ACTIVE harness  (Alexandrian)
# ══════════════════════════════════════════════════════════════════════════════
class ActiveHarness:
    """VAPMIP/harness.py if importable, with the Monad attached; else a stub."""

    def __init__(self, monad: MonadLink) -> None:
        self.kind = "stub"
        self._h = None
        try:
            from VAPMIP.harness import Harness                    # noqa: PLC0415
            self._h = Harness()
            if monad._engine is not None:
                try:
                    self._h.attach_monad(monad._engine)
                except Exception:                                 # noqa: BLE001
                    pass
            self.kind = "VAPMIP.Harness" + (
                " +monad" if getattr(self._h, "monad_attached", False) else "")
        except Exception:                                         # noqa: BLE001
            pass

    def present(self, content: Any, kind: str = "text") -> str:
        if self._h is not None:
            try:
                r = self._h.present(content, kind=kind)
                return str(getattr(r, "data", r))
            except Exception as e:                                # noqa: BLE001
                return f"(active harness error: {e})"
        return f"(stub present [{kind}]) {str(content)[:120]}"

    def status(self) -> str:
        return self.kind


# ══════════════════════════════════════════════════════════════════════════════
#  THE STITCHBOARD  —  the Monad as operator, routing between both harnesses
# ══════════════════════════════════════════════════════════════════════════════
class StitchBoard:
    def __init__(self) -> None:
        self.sink: "queue.Queue[str]" = queue.Queue()
        self.monad = MonadLink()
        self._registry = None
        self._registry_loaded = False
        # Archimedes (in the support room) runs the ValaQuenta Tab, so the
        # support harness gets a lazy handle to the registry.
        self.support = SupportHarness(self.sink, self._get_registry)
        self.active = ActiveHarness(self.monad)
        self._mode = "sentence"      # sentence construction (default) | paragraph
        self.harness: Optional["HarnessLink"] = None  # set in --harness mode
        self._acked: set = set()          # (face, stamp, level) already routed
        self._judgements: List[Judgement] = []   # Ptolemy's decisions, in order
        # faces may read/propose code within this root; writes are Ptolemy-gated
        _root = os.environ.get(
            "PTOLEMY_CODE_ROOT",
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.gate = CodeGate(_root)

    def _get_registry(self):
        if not self._registry_loaded:
            # ValaQuenta's registry prints on register(); in --port mode stdout
            # IS the frame pipe, so keep it quiet.
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                self._registry = _load_registry()
            self._registry_loaded = True
        return self._registry

    @property
    def registry(self):
        return self._get_registry()

    # -- routing --------------------------------------------------------------
    def route(self, msg: str) -> str:
        """The one seam.  Classify the turn and route it; drain support events."""
        self._drain_support()
        m = msg.strip()
        if not m:
            return ""
        if m.startswith("/radio"):
            for ln in self.support.radio_check():
                self.sink.put(ln)
            return "(radio-check queued)"
        if m.startswith("/paragraph"):
            self._mode = "paragraph"
            self._send_mode()
            return ("(mode: paragraph — a prompt of >1 sentence gets its "
                    "paragraph grammar; /sentence returns to the default)")
        if m.startswith("/sentence"):
            self._mode = "sentence"
            self._send_mode()
            return "(mode: sentence construction — the default)"
        if m.startswith("/mode"):
            return f"(construction mode: {self._mode})"
        if m.startswith("/tool "):
            return self.active.present(m[6:], kind="tool-request")
        if m.startswith("/diag"):
            return f"support: {self.support.status()}   active: {self.active.status()}"
        if m.startswith("/faces"):
            rows = []
            for name, face in self.support.faces.items():
                p = self.support.latest.get(name)
                tail = f"  ({p.level}, drift {p.weight:.2f})" if p else ""
                star = " *acts*" if face.active else ""
                rows.append(f"  {name}{star} — {face.role}{tail}")
            return "faces:\n" + "\n".join(rows)
        if m.startswith("/poll ") or m.startswith("/ask "):
            topic = m.split(" ", 1)[1]
            return self.poll_opinions(topic)
        if m.startswith("/enc ") or m.startswith("/archimedes "):
            q = m.split(" ", 1)[1]
            arch = self.support.faces.get("Archimedes")
            out = arch.act(q) if arch else None
            return out or "(Archimedes unavailable)"
        if m.startswith("/proposals"):
            pend = self.gate.pending()
            if not pend:
                return "no pending code proposals"
            return "pending code proposals:\n" + "\n".join(
                f"  #{pr.pid} «{pr.face}» {pr.path}  (+{pr.stat()[0]} -{pr.stat()[1]})"
                f"  — {pr.reason}" for pr in pend)
        if m.startswith("/diff "):
            pr = self.gate.get(_int(m.split(None, 1)[1]))
            return pr.diff if pr else "(no such proposal)"
        if m.startswith("/approve "):
            return self.gate.approve(_int(m.split(None, 1)[1]))
        if m.startswith("/reject "):
            parts = m.split(None, 2)
            return self.gate.reject(_int(parts[1]),
                                    parts[2] if len(parts) > 2 else "")
        if m.startswith("/monad"):
            arg = m[6:].strip().lower()
            if arg in ("off", "detach", "0"):
                self.monad.enabled = False
                return "(monad detached — harness + stitchboard stay live)"
            if arg in ("on", "attach", "1"):
                self.monad.enabled = True
                return "(monad attached)"
            return f"(monad {'attached' if self.monad.enabled else 'detached'})"
        # Archimedes the Professor: established maths/physics, no framework maths.
        # He answers as a chat bot; Ptolemy relays; no support-harness post.
        prof = self.answer_established(m)
        if prof is not None:
            return prof
        reply, meta = self.monad.say(m)
        if self._mode == "paragraph":
            reply = self._with_paragraph_grammar(m, reply)
        return reply

    def _send_mode(self) -> None:
        if self.harness is not None:
            try:
                self.harness.send({"t": "mode", "mode": self._mode})
            except Exception:                                    # noqa: BLE001
                pass

    def _with_paragraph_grammar(self, prompt: str, reply: str) -> str:
        """Layer semantic_paragraph.py's paragraph read onto a monad reply —
        the higher-order prime semantic hash over the prompt's sentence
        structure (VAPMIP/semantic_paragraph.py)."""
        try:
            vp = os.path.join(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))), "VAPMIP")
            if vp not in sys.path:
                sys.path.insert(0, vp)
            import semantic_paragraph as sp                      # noqa: PLC0415
            if not sp.is_paragraph(prompt):
                return reply
            try:
                h = sp.paragraph_hash(prompt)
                arc = " → ".join(h["grammar"])
                sup = ", ".join(h["support"][:8])
                return (f"{reply}\n"
                        f"  ¶ {h['n_sentences']} sentences   arc: {arc}\n"
                        f"  ¶ support: {sup}")
            except Exception:                                    # noqa: BLE001
                n = len(sp.split_sentences(prompt))
                return (f"{reply}\n  ¶ {n} sentences "
                        f"(prime hash unavailable — WordNet not loaded)")
        except Exception as e:                                   # noqa: BLE001
            return f"{reply}\n  ¶ (paragraph mode: {type(e).__name__})"

    _archimedes_face = None

    def answer_established(self, question: str) -> Optional[str]:
        """Route an established-maths question to the Archimedes Face. Returns
        its literal answer, or None if it needs framework maths / is not maths
        (Ptolemy keeps it)."""
        try:
            if self._archimedes_face is None:
                from Archimedes.face import ArchimedesFace       # noqa: PLC0415
                type(self)._archimedes_face = ArchimedesFace()
            return self._archimedes_face.answer(question)
        except Exception:                                        # noqa: BLE001
            return None

    def _drain_support(self) -> List[str]:
        out: List[str] = []
        while True:
            try:
                out.append(self.sink.get_nowait())
            except queue.Empty:
                break
        return out

    def drain(self) -> List[str]:
        return self._drain_support()

    # -- Ptolemy reviewing / polling the support room -----------------------
    def _decide(self, post: FacePost,
                opinions: List[Tuple[str, str, float]]) -> Tuple[str, str, str]:
        """Deterministic: (decision, action, reason) from the post's level, its
        drift weight, its intrusion kind, and the strongest concurring opinion
        from the OTHER faces."""
        lvl, w, intr = post.level, float(post.weight), (post.intrusion or "")
        others = [(n, s, wt) for (n, s, wt) in opinions if n != post.who]
        concur = max((wt for _, _, wt in others), default=0.0)
        cname = next((n for n, _, wt in others if wt == concur), "")

        if intr == "heartbeat" and lvl == "hardening":
            return ("ESCALATE", "raise supervisor priority",
                    f"heartbeat hardening from {post.who} — supervisor priority "
                    f"regardless of drift {w:.2f}")
        if intr == "tool" or any(k in post.text.lower() for k in
                                 ("maths", "derive", "proof", "equation", "theorem")):
            return ("DEFER", "route to Archimedes (reference)",
                    f"{intr or 'reference'} question — Archimedes' jurisdiction")
        if lvl == "hardening":
            if w >= 0.60:
                tail = f"; {cname} concurs {concur:.2f}" if concur >= 0.50 else ""
                return ("HARDEN", "apply the proposed adjustment",
                        f"drift {w:.2f} >= 0.60, hardening from {post.who}{tail}")
            return ("THROTTLE", "route the adjustment as a request, not applied",
                    f"drift {w:.2f} < 0.60 — throttle, do not auto-apply")
        if lvl == "warn":
            if w >= 0.40 and concur >= 0.50:
                return ("THROTTLE", "route the adjustment as a request",
                        f"warn drift {w:.2f}; {cname} concurs {concur:.2f}")
            if w >= 0.40:
                return ("ESCALATE", "cross-check on the next poll",
                        f"warn drift {w:.2f}, no concurrence ({concur:.2f}) — watch")
            return ("HOLD", "note only", f"warn drift {w:.2f} < 0.40 — hold")
        return ("HOLD", "note only", "info-level — nothing to decide")

    def judge_support(self) -> List[str]:
        """Ptolemy's judgement pass over the support room.  For each un-acked
        warn / hardening post: weigh it, poll the other faces, decide, act, and
        emit one JUDGEMENT_GRAMMAR line (which the support harness ingests, a
        later build).  Passive posts are left for the Chat Tab."""
        lines: List[str] = []
        for name, post in list(self.support.latest.items()):
            if post.level == "info":
                continue
            key = (name, post.stamp, post.level)
            if key in self._acked:
                continue
            self._acked.add(key)
            opinions = self.support.opinions(post.intrusion or post.text)
            decision, action, reason = self._decide(post, opinions)
            if decision == "HARDEN":
                self.active.present(f"{name}: {post.text}", kind="face-hardening")
            elif decision == "THROTTLE":
                self.active.present(f"{name}: {post.text}",
                                    kind="face-throttle-request")
            elif decision == "DEFER":
                arch = self.support.faces.get("Archimedes")
                if arch is not None:
                    try:
                        arch.act(post.text)
                    except Exception:                            # noqa: BLE001
                        pass
            j = Judgement(face=name, intrusion=post.intrusion or post.level,
                          decision=decision, action=action, reason=reason,
                          stamp=post.stamp)
            self._judgements.append(j)
            lines.append(j.line())
        return lines

    # kept name — the console / --port loop call this
    review_faces = judge_support

    def poll_opinions(self, topic: str) -> str:
        rows = self.support.opinions(topic)
        if not rows:
            return "(no faces to poll)"
        body = "\n".join(f"  {n:<10} {w:.2f}  {s}" for n, s, w in rows)
        lead, lstance, lw = rows[0]
        direct = (f"{NAME} directs: follow {lead} ({lstance})" if lw >= 0.5
                  else f"{NAME} directs: no strong opinion — hold")
        return f"weighted opinions on '{topic}':\n{body}\n{direct}"

    def status_line(self) -> str:
        return (f"monad:{self.monad.status()}  "
                f"active:{self.active.status()}  "
                f"support:{self.support.status()}")


# ══════════════════════════════════════════════════════════════════════════════
#  the curses app
# ══════════════════════════════════════════════════════════════════════════════
def _load_registry():
    try:
        from ValaQuenta.__main__ import _register_all             # noqa: PLC0415
        return _register_all()
    except Exception:                                             # noqa: BLE001
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  The Ptolemy Manager — one pcmanfm-style frame, folder tabs raise a Pane
# ──────────────────────────────────────────────────────────────────────────────
#  Constant chrome: [folder tabs][path/crumb][ nav box │ main view ][status][input]
#  A `Pane` supplies the contents of each box for its tab; switching tabs just
#  raises a different Pane. The boxes are independent — nav / view / keypad /
#  input — layered into the same structure the ValaQuenta browser uses.
# ══════════════════════════════════════════════════════════════════════════════
class Pane:
    name = "?"
    enabled = True
    takes_input = False
    input_hint = ""
    keypad: List[str] = []

    def __init__(self, console: "PtolemyConsole") -> None:
        self.c = console
        self.sel = 0
        self.vscroll = 0

    # contents of each box (override as needed)
    def crumb(self) -> str:
        return f" ⌂ / {self.name}"

    def nav_title(self) -> str:
        return self.name.upper()

    def nav_items(self) -> List[str]:
        return []

    def view_title(self) -> str:
        return ""

    def view_lines(self, w: int) -> List[str]:
        return []

    # events
    def on_activate(self, item: str) -> None:    # Enter / → on a nav row
        pass

    def on_back(self) -> None:                   # ←
        pass

    def on_submit(self, text: str) -> None:      # Enter on the input line
        pass

    def on_show(self) -> None:                   # this pane raised to the top
        pass

    # presentation — raw nav_items() stay the logical/lookup keys; display()
    # is what's actually drawn (e.g. humanized titles). Default: identity.
    def display(self, item: str) -> str:
        return item

    def is_header(self, item: str) -> bool:
        """Non-selectable separator row — a blank, a "— label —" (ChatPane),
        or a "── Label ──" group header (ValaQuenta-style, ArchimedesPane)."""
        return (not item) or item.startswith("—")

    # helper
    def _clamp_sel(self) -> None:
        items = self.nav_items()
        n = len(items)
        self.sel = 0 if n == 0 else max(0, min(self.sel, n - 1))
        if items and self.is_header(items[self.sel]):
            for j, it in enumerate(items):
                if not self.is_header(it):
                    self.sel = j
                    break


class ChatPane(Pane):
    name = "Chat"
    takes_input = True

    _CMDS = ["› sentence mode", "› paragraph mode", "/faces", "/diag",
             "/radio", "/proposals", "/monad"]

    @property
    def input_hint(self) -> str:
        return f"{NAME}[{self.c.board._mode[:4]}]> "

    def crumb(self) -> str:
        return f" ⌂ / Chat · {self.c.board._mode}"

    def nav_title(self) -> str:
        return "COMMANDS · FACES"

    def nav_items(self) -> List[str]:
        rows = list(self._CMDS) + ["", "— faces —"]
        for nm, face in self.c.board.support.faces.items():
            p = self.c.board.support.latest.get(nm)
            tail = f"  {p.weight:.2f}" if p else ""
            rows.append(f"  {nm}{tail}")
        return rows

    def view_title(self) -> str:
        return "TRANSCRIPT"

    def view_lines(self, w: int) -> List[str]:
        return self.c.lines[-400:]

    def on_activate(self, item: str) -> None:
        it = item.strip("› ").strip()
        if it == "sentence mode":
            self.c._route("/sentence")
        elif it == "paragraph mode":
            self.c._route("/paragraph")
        elif it.startswith("/"):
            self.c._route(it)
        elif it and not it.startswith("—") and it in self.c.board.support.faces:
            self.c._route(f"/poll {it}")

    def on_submit(self, text: str) -> None:
        self.c._push(f"{NAME}> {text}")
        if text.strip() != "q":
            self.c._route(text)


# category slugs whose plain .replace('_',' ').title() reads wrong
# (acronyms, ampersands) — everything else humanizes generically.
_TITLE_OVERRIDES = {
    "rf_microwave": "RF & Microwave",
    "qft": "Quantum Field Theory",
}
_TIER_ORDER = ("foundations", "physics", "engineering")


def _humanize(slug: str) -> str:
    return _TITLE_OVERRIDES.get(slug, slug.replace("_", " ").title())


class ArchimedesPane(Pane):
    name = "Archimedes"
    takes_input = True
    input_hint = "ask Archimedes> "
    keypad = ["Integral( )", "Derivative( )", "Sum( )", "sqrt( )", "pi",
              "^", "*", "==", "solve … for x"]

    def __init__(self, console: "PtolemyConsole") -> None:
        super().__init__(console)
        self.level = 0            # 0 = categories, 1 = equations of self.cat
        self.cat = ""
        self.detail: List[str] = []
        self._by_cat: Dict[str, list] = {}
        self._pages: Dict[str, dict] = {}
        self._tier_of: Dict[str, str] = {}     # category slug -> foundations/physics/engineering
        self._face = None
        self._err = ""

    def _load(self) -> None:
        if self._by_cat or self._err:
            return
        try:
            import sys as _sys
            here = os.path.dirname(os.path.abspath(__file__))
            if here not in _sys.path:
                _sys.path.insert(0, here)
            from Archimedes.Maths.researcher import by_category, pages  # noqa: PLC0415
            from Archimedes.face import ArchimedesFace                  # noqa: PLC0415
            self._by_cat = by_category()
            self._pages = pages()
            self._face = ArchimedesFace()
            for key in self._pages:                # "foundations.algebra" -> tier
                tier, _, cat = key.partition(".")
                if cat:
                    self._tier_of[cat] = tier
        except Exception as e:                                          # noqa: BLE001
            self._err = f"{type(e).__name__}: {e}"

    def on_show(self) -> None:
        self._load()

    def crumb(self) -> str:
        p = " ⌂ / Archimedes"
        if self.level >= 1 and self.cat:
            p += f" / {_humanize(self.cat)}"
        return p

    def nav_title(self) -> str:
        return "CATEGORIES" if self.level == 0 else _humanize(self.cat).upper()

    def display(self, item: str) -> str:
        if self.level == 0 and not self.is_header(item) and item != "..":
            return _humanize(item)
        return item                     # headers/".."/equation names are already words

    def is_header(self, item: str) -> bool:
        return super().is_header(item) or item.startswith("── ")

    def nav_items(self) -> List[str]:
        self._load()
        if self._err:
            return ["(formulary unavailable)"]
        if self.level == 0:
            rows: List[str] = []
            seen: set = set()
            for tier in _TIER_ORDER:
                cats = sorted(c for c in self._by_cat if self._tier_of.get(c) == tier)
                if not cats:
                    continue
                rows.append(f"── {_humanize(tier)} ──")
                rows.extend(cats)
                seen.update(cats)
            leftover = sorted(c for c in self._by_cat if c not in seen)
            if leftover:
                rows.append("── Other ──")
                rows.extend(leftover)
            return rows
        rows = [".."]
        rows += [md.name for md in self._by_cat.get(self.cat, [])]
        return rows

    def view_title(self) -> str:
        return "DETAIL"

    def view_lines(self, w: int) -> List[str]:
        if self._err:
            return ["The Archimedes formulary did not load:", "  " + self._err,
                    "", "Run  python -m Archimedes.Maths.researcher  to check."]
        if self.detail:
            return self.detail
        items = self.nav_items()
        if not items:
            return []
        cur = items[min(self.sel, len(items) - 1)]
        if self.is_header(cur):
            return ["(select a category below)"]
        if self.level == 0:
            pg = next((v for k, v in self._pages.items() if k.endswith(cur)), {})
            defs = self._by_cat.get(cur, [])
            out = [pg.get("title") or _humanize(cur), ""]
            if pg.get("blurb"):
                out += textwrap.wrap(pg["blurb"], max(20, w - 2)) + [""]
            out.append(f"{len(defs)} formulae — → to open the list")
            return out
        return ["→ open this formula for its expression and every",
                "  rearranged form (each variable across the =)."]

    def _show_formula(self, name: str) -> None:
        defs = self._by_cat.get(self.cat, [])
        md = next((d for d in defs if d.name == name), None)
        if md is None:
            self.detail = [f"(no formula '{name}')"]
            return
        out = [md.name, "=" * min(len(md.name), 60), f"  {md.expr}"]
        jur = getattr(md, "jurisdiction", "") or ""
        if jur:
            out.append(f"  jurisdiction: {jur}")
        sibs = [d for d in defs
                if d.id.rsplit("__", 1)[0] == md.id.rsplit("__", 1)[0]
                and d.id != md.id]
        if sibs:
            out += ["", "rearranged forms:"]
            out += [f"  {d.name.split('— ')[-1]:<16} {d.expr}" for d in sibs]
        self.detail = out

    def on_activate(self, item: str) -> None:
        if self.is_header(item):
            return
        self.detail = []
        if self._err:
            return
        if self.level == 0:
            self.cat = item.strip()
            self.level = 1
            self.sel = 0
        else:
            if item.strip() == "..":
                self.on_back()
            else:
                self._show_formula(item.strip())

    def on_back(self) -> None:
        self.detail = []
        if self.level == 1:
            self.level = 0
            self.sel = 0

    def on_submit(self, text: str) -> None:
        self._load()
        if self._face is None:
            self.detail = ["(Archimedes face unavailable)"]
            return
        try:
            ans = self._face.answer(text)
        except Exception as e:                                         # noqa: BLE001
            ans = f"(error: {type(e).__name__}: {e})"
        self.detail = [f"ask> {text}", "", ans or
                       "(not established maths I can state — Ptolemy would keep it)"]


class LineagePane(Pane):
    name = "Generational Lineage"
    enabled = False

    def nav_items(self) -> List[str]:
        return ["(engine not wired into the console yet)"]

    def view_title(self) -> str:
        return "GREYED"

    def view_lines(self, w: int) -> List[str]:
        return ["The Generational Lineage engine (GenerationalLineage/) is not",
                "tied into the Ptolemy manager yet. This tab is a placeholder —",
                "the frame is here; the contents are the next build."]


class ValaQuentaPane(Pane):
    name = "ValaQuenta"

    def nav_items(self) -> List[str]:
        return ["Open the Derivation Browser  →"]

    def view_title(self) -> str:
        return "DERIVATION BROWSER"

    def view_lines(self, w: int) -> List[str]:
        return ["The ValaQuenta engine encyclopedia — the full-screen",
                "Derivation Browser (its own nav / view / proof panels).",
                "", "→ or Enter to raise it; q inside returns here."]

    def on_activate(self, item: str) -> None:
        self.c._run_derivation_subloop()


class PtolemyConsole:
    def __init__(self, stdscr, board: StitchBoard, registry,
                 embedded: bool = False) -> None:
        self.scr = stdscr
        self.board = board
        self.registry = registry
        self.lines: List[str] = []        # the Chat transcript, starts clean
        self.input = ""
        # ValaQuenta is a first-class tab; Archimedes is only the local maths
        # worker for the Monad — its browsing Tab appears only when the console
        # is embedded in PtolemyDesktop.
        self.panes: List[Pane] = [ChatPane(self), ValaQuentaPane(self),
                                  LineagePane(self)]
        if embedded:
            self.panes.append(ArchimedesPane(self))
        self.tab = 0

    @property
    def pane(self) -> Pane:
        return self.panes[self.tab]

    # ── transcript / routing (Chat) ──────────────────────────────────────
    def _push(self, s: str) -> None:
        for seg in (textwrap.wrap(s, max(20, self.scr.getmaxyx()[1] - 2)) or [""]):
            self.lines.append(seg)

    def _route(self, msg: str) -> None:
        reply = self.board.route(msg)
        self._flush_support()
        if reply:
            self._push(f"  {reply}")

    def _flush_support(self) -> None:
        for ln in self.board.drain():
            self._push(ln)
        for ln in self.board.review_faces():
            self._push(ln)

    # ── ValaQuenta full-screen sub-loop (raised to the top) ──────────────
    def _run_derivation_subloop(self) -> None:
        """Load the ValaQuenta Derivation Browser directly — it is its own
        tab, not something routed through the Archimedes face."""
        reg = self.registry or getattr(self.board, "registry", None)
        if reg is None:
            self._push("(ValaQuenta registry not available)")
            return
        try:
            from ValaQuenta.engine.console_curses import DerivationBrowser  # noqa: PLC0415
            self.scr.nodelay(False)
            curses.curs_set(0)
            DerivationBrowser(self.scr, reg).run()
        except Exception as e:                                    # noqa: BLE001
            self._push(f"(Derivation Browser error: {type(e).__name__}: {e})")
        finally:
            self.scr.nodelay(True)
            curses.curs_set(1)

    # ── tab switching ───────────────────────────────────────────────────
    def _select_tab(self, i: int, cycle: bool = False) -> None:
        if not (0 <= i < len(self.panes)):
            return
        if cycle:                       # Tab/BTab skip disabled panes
            for _ in range(len(self.panes)):
                if self.panes[i].enabled:
                    break
                i = (i + 1) % len(self.panes)
        self.tab = i
        self.pane._clamp_sel()
        self.pane.on_show()

    def _step_sel(self, p: Pane, delta: int) -> None:
        """Move p.sel by one row in `delta`'s direction, skipping header
        rows (they're not selectable). Stops at the array edge rather than
        landing on a header there."""
        items = p.nav_items()
        n = len(items)
        if n == 0:
            return
        i = p.sel
        while 0 <= i + delta < n:
            i += delta
            if not p.is_header(items[i]):
                p.sel = i
                return
        if p.is_header(items[p.sel]):          # started on one — snap off it
            for j, it in enumerate(items):
                if not p.is_header(it):
                    p.sel = j
                    return

    # ── main loop ───────────────────────────────────────────────────────
    def run(self) -> None:
        curses.curs_set(1)
        self.scr.nodelay(True)
        self.scr.keypad(True)
        # never let a bottom-right write scroll the whole screen — that was
        # stacking the frame into the scrollback every turn
        self.scr.scrollok(False)
        self.scr.idlok(False)
        self.scr.leaveok(False)
        self.board.support.start()
        self.pane.on_show()
        try:
            while True:
                self._flush_support()
                self._draw()
                try:
                    k = self.scr.getch()
                except curses.error:
                    k = -1
                if k == -1:
                    time.sleep(0.05)
                    continue
                if k == 27:                       # ESC — may be a split CSI seq
                    k = self._resolve_escape()
                    if k is None:
                        continue
                p = self.pane
                if k in (curses.KEY_F1, curses.KEY_F2, curses.KEY_F3, curses.KEY_F4):
                    self._select_tab(k - curses.KEY_F1)
                elif k == ord("\t"):
                    self._select_tab((self.tab + 1) % len(self.panes), cycle=True)
                elif k == curses.KEY_BTAB:
                    self._select_tab((self.tab - 1) % len(self.panes), cycle=True)
                elif k == 4:                                    # Ctrl-D
                    break
                elif k in (curses.KEY_UP,):
                    self._step_sel(p, -1)
                elif k in (curses.KEY_DOWN,):
                    self._step_sel(p, 1)
                elif k in (curses.KEY_LEFT,):
                    p.on_back()
                elif k in (curses.KEY_RIGHT,):
                    items = p.nav_items()
                    if items:
                        p.on_activate(items[min(p.sel, len(items) - 1)])
                elif k in (curses.KEY_ENTER, 10, 13):
                    if p.takes_input and self.input.strip():
                        if self.input.strip() == "q":
                            break
                        txt, self.input = self.input, ""
                        p.on_submit(txt)
                    else:
                        items = p.nav_items()
                        if items:
                            p.on_activate(items[min(p.sel, len(items) - 1)])
                elif k in (curses.KEY_BACKSPACE, 127, 8):
                    if p.takes_input:
                        self.input = self.input[:-1]
                elif 32 <= k < 127 and p.takes_input:
                    self.input += chr(k)
        except KeyboardInterrupt:
            pass                        # Ctrl-C quits like q / Ctrl-D, no traceback
        finally:
            self.board.support.stop()

    def _resolve_escape(self):
        """A lone ESC under nodelay may be a split CSI/SS3 sequence. Drain the
        rest briefly and map it; swallow anything unrecognised (return None)."""
        self.scr.nodelay(False)
        self.scr.timeout(40)
        seq = []
        try:
            while True:
                n = self.scr.getch()
                if n == -1 or len(seq) > 6:
                    break
                seq.append(n)
        except curses.error:
            pass
        finally:
            self.scr.timeout(-1)
            self.scr.nodelay(True)
        s = "".join(chr(c) for c in seq if 0 <= c < 128)
        return {
            "[A": curses.KEY_UP, "OA": curses.KEY_UP,
            "[B": curses.KEY_DOWN, "OB": curses.KEY_DOWN,
            "[C": curses.KEY_RIGHT, "OC": curses.KEY_RIGHT,
            "[D": curses.KEY_LEFT, "OD": curses.KEY_LEFT,
            "[Z": curses.KEY_BTAB,
            "OP": curses.KEY_F1, "OQ": curses.KEY_F2,
            "OR": curses.KEY_F3, "OS": curses.KEY_F4,
            "[11~": curses.KEY_F1, "[12~": curses.KEY_F2,
            "[13~": curses.KEY_F3, "[14~": curses.KEY_F4,
        }.get(s)

    # ── the frame ───────────────────────────────────────────────────────
    def _put(self, y: int, x: int, s: str, attr: int = 0) -> None:
        try:
            h, w = self.scr.getmaxyx()
            if 0 <= y < h and x < w:
                self.scr.addstr(y, x, s[:max(0, w - 1 - x)], attr)
        except curses.error:
            pass

    def _tab_layout(self, w: int):
        """(name, x, inner_width, enabled, active) per tab, laid left→right;
        drops tabs that would overflow the width."""
        out, x = [], 1
        for i, pn in enumerate(self.panes):
            iw = len(pn.name) + 2               # " Name "
            if x + iw + 2 >= w:
                break
            out.append((pn.name, x, iw, pn.enabled, i == self.tab))
            x += iw + 2                          # + the two corner columns
        return out

    def _draw_tabs(self, w: int) -> None:
        """Browser / file-manager folder tabs on rows 0-1: the active tab's
        bottom is open into the body; the others are sealed under the
        baseline (they sit 'behind' the content, out of the way)."""
        self._put(1, 0, "─" * (w - 1), curses.A_DIM)      # the baseline
        for name, x, iw, enabled, active in self._tab_layout(w):
            top_attr = curses.A_BOLD if (active or enabled) else curses.A_DIM
            lbl_attr = (curses.A_REVERSE | curses.A_BOLD) if active else (
                curses.A_BOLD if enabled else curses.A_DIM)
            self._put(0, x, "┌" + "─" * iw + "┐", top_attr)
            self._put(0, x + 1, f" {name} ", lbl_attr)
            if active:
                self._put(1, x, "┘" + " " * iw + "└", curses.A_BOLD)
            else:
                self._put(1, x, "┴" + "─" * iw + "┴", curses.A_DIM)

    def _draw_box(self, y: int, x: int, bh: int, bw: int, title: str,
                  lines: List[str], selrow: int = -1, focus: bool = False,
                  header_rows: Optional[set] = None) -> None:
        """A titled, bordered box. Each logical row in `lines` is word-wrapped
        to fit; a wrapped CONTINUATION line gets one extra space of indent
        (3 vs 2) so it reads as "more of the row above", never confused with
        a logical sub-label's own 2-space indent (that's in the row's text,
        not this rendering offset). `header_rows` marks logical indices that
        are separators — dim, never selection-highlighted, whole row spans."""
        header_rows = header_rows or set()
        tattr = curses.A_BOLD if focus else curses.A_DIM
        self._put(y, x, ("┌─ " + title + " ").ljust(bw - 1, "─") + "┐", tattr)
        for r in range(1, bh - 1):
            self._put(y + r, x, "│", curses.A_DIM)
            self._put(y + r, x + bw - 1, "│", curses.A_DIM)
        self._put(y + bh - 1, x, "└".ljust(bw - 1, "─") + "┘", curses.A_DIM)

        inner_h = bh - 2
        content_w = max(1, bw - 4)
        cont_w = max(1, content_w - 1)

        # logical rows -> physical display rows (word-wrapped)
        phys: List[Tuple[str, int, bool]] = []      # (text, logical_idx, is_continuation)
        for li, ln in enumerate(lines):
            for wi, seg in enumerate(textwrap.wrap(ln, content_w) or [""]):
                phys.append((seg, li, wi > 0))

        # scroll so the selected logical row's FIRST physical line is visible
        sel_phys = next((i for i, ph in enumerate(phys) if ph[1] == selrow), 0)
        top = 0
        if sel_phys >= inner_h:
            top = sel_phys - inner_h + 1

        for r, (seg, li, is_cont) in enumerate(phys[top:top + inner_h]):
            attr = 0
            if li in header_rows:
                attr = curses.A_BOLD | curses.A_DIM
            elif li == selrow:
                attr = curses.A_REVERSE | (curses.A_BOLD if focus else 0)
            indent, width = (3, cont_w) if is_cont else (2, content_w)
            self._put(y + 1 + r, x + indent, seg[:width].ljust(width), attr)

    INPUT_BAND = 7   # 5 content lines + 2 borders — ALWAYS reserved when a pane
                     # takes input, so growing/shrinking never moves anything
                     # else (the NES-viewport rule: the window is fixed, the
                     # text map scrolls inside it).

    def _draw(self) -> None:
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        p = self.pane

        self._draw_tabs(w)                            # rows 0-1
        self._put(2, 0, p.crumb().ljust(w - 1), curses.A_BOLD)   # row 2

        body_y = 3
        has_input = p.takes_input
        has_pad = bool(p.keypad)
        # status + input-band + keypad — fixed sizes regardless of content,
        # so the nav/view boxes never resize as the user types
        foot = 1 + (self.INPUT_BAND if has_input else 0) + (1 if has_pad else 0)
        body_h = max(3, h - body_y - foot)
        nav_w = max(20, min(40, w // 3))

        nav = p.nav_items()
        p._clamp_sel()
        nav_disp = [p.display(it) for it in nav]
        nav_headers = {i for i, it in enumerate(nav) if p.is_header(it)}
        self._draw_box(body_y, 0, body_h, nav_w, p.nav_title(), nav_disp,
                       selrow=p.sel if nav else -1, focus=not has_input or not self.input,
                       header_rows=nav_headers)
        vlines: List[str] = []
        for ln in p.view_lines(w - nav_w - 4):
            vlines.extend(textwrap.wrap(ln, w - nav_w - 6) or [""])
        # a view that is a live log (Chat) sticks to the tail
        if isinstance(p, ChatPane):
            vlines = vlines[-(body_h - 2):]
        self._draw_box(body_y, nav_w, body_h, w - nav_w, p.view_title(), vlines,
                       focus=bool(has_input and self.input))

        y = body_y + body_h
        if has_pad:
            self._put(y, 0, ("  keypad: " + "  ".join(p.keypad)).ljust(w - 1),
                      curses.A_DIM)
            y += 1
        legend = " F1-F4 tab · ↑↓ nav · → open · ← up · ^D quit "
        st = self.board.status_line()
        self._put(y, 0, st.ljust(w - 1), curses.A_DIM)          # clear the row
        self._put(y, max(0, w - 1 - len(legend)), legend, curses.A_REVERSE)
        y += 1
        if has_input:
            self._draw_input_band(y, w, p)
        self.scr.refresh()

    def _draw_input_band(self, y_top: int, w: int, p: Pane) -> None:
        """The growing input box, Claude-Code style: 1 line normally, up to 5
        of wrapped text — a VIEWPORT (past 5 it shows the tail, where the
        cursor is, not the head). Anchored to the bottom of the fixed
        INPUT_BAND, so it only ever grows into blank space already reserved
        above it; nothing else on screen moves."""
        inner_w = max(4, w - 5)
        raw_lines = textwrap.wrap(self.input, inner_w) or [""]
        visible_n = min(5, len(raw_lines))
        view = raw_lines[-visible_n:]                     # the viewport: the tail
        box_h = visible_n + 2
        box_top = y_top + (self.INPUT_BAND - box_h)       # bottom stays fixed
        title = p.input_hint.strip() or "input"
        self._draw_box(box_top, 0, box_h, w - 1, title, view, selrow=-1, focus=True)
        try:
            last = view[-1] if view else ""
            self.scr.move(box_top + box_h - 2, min(w - 3, 2 + len(last)))
        except curses.error:
            pass


# ══════════════════════════════════════════════════════════════════════════════
def selftest() -> int:
    print(f"=== {NAME} console selftest ===")
    b = StitchBoard()
    print("status:", b.status_line())
    print("faces:", ", ".join(b.support.faces))
    b.support.register("demo_face", lambda: 0.4, lambda: "throttled demo_face ingest")
    for msg in ("hello ptolemy", "/faces", "/radio", "/poll open the tool file",
                "/enc emerger", "/enc run emerger.verify",
                "/enc tour emerger", "/diag"):
        print(f"\n{NAME}> {msg}")
        print("  ->", b.route(msg))
        for ln in b.drain():
            print("    ", ln)
        for ln in b.review_faces():
            print("    ", ln)
    # --- CodeGate: a face proposes, Ptolemy approves ---------------------
    import shutil
    import tempfile
    d = tempfile.mkdtemp(prefix="ptol_gate_")
    try:
        src = pathlib.Path(d) / "two_objects.py"
        src.write_text("def a(x):\n    return x + 1\n\n\ndef b(x):\n    return x * 2\n")
        gate = CodeGate(d)
        arch = b.support.faces["Archimedes"]
        print(f"\n{NAME}> (Archimedes reads two_objects.py, proposes a fold)")
        _ = arch.read_code(gate, "two_objects.py")
        pr = arch.propose(gate, "two_objects.py",
                          "def ab(x):\n    return (x + 1) * 2\n",
                          "minimise: fold a,b into one object")
        print(f"     proposal #{pr.pid} «{pr.face}» {pr.path}  (+{pr.stat()[0]} -{pr.stat()[1]})")
        print("    ", gate.reject(999).strip(), "(guard: bad id)")
        print("    ", gate.approve(pr.pid).strip())
        print("     file now:", src.read_text().replace(chr(10), " ⏎ ").strip())
        baks = list(pathlib.Path(d).glob("*.bak.*"))
        print("     backup made:", bool(baks))
        # deny check
        try:
            gate.read("../etc_shadow_token.bin")
        except ValueError as e:
            print("     deny works:", e)
    finally:
        shutil.rmtree(d, ignore_errors=True)

    reg = b.registry            # already loaded once by Archimedes above
    print("\nValaQuenta registry:", (f"{len(reg.list_modules())} engines" if reg else "unavailable"))
    print("\nselftest OK")
    return 0


def run_port() -> int:
    """Frame-protocol mode: drive the StitchBoard behind console_link's
    standardized connection (stdio here; a pty when spawned by ConsoleClient).
    This is how PtolemyDesktop attaches — and how new PyQt6 code is fed in for
    an update session."""
    from console_link import ConsolePort, run_update_session      # noqa: PLC0415
    port = ConsolePort.stdio()
    board = StitchBoard()
    board.support.start()
    port.send({"t": "status", **_status_dict(board)})
    try:
        while True:
            f = port.recv(timeout=1.0)
            for ln in board.drain():
                port.send({"t": "radio", "line": ln})
            for ln in board.review_faces():
                port.send({"t": "radio", "line": ln})
            if f is None:
                continue
            t = f.get("t")
            rid = f.get("id")
            if t in ("attach", "noop"):
                port.send({"t": "status", **_status_dict(board)})
            elif t == "ping":
                port.send({"t": "pong", "at": time.time(), "id": rid})
            elif t == "say":
                port.send({"t": "chat", "who": NAME, "id": rid,
                           "text": board.route(f.get("text", ""))})
            elif t == "cmd":
                port.send({"t": "chat", "who": NAME, "id": rid,
                           "text": board.route(f.get("line", ""))})
            elif t == "update":
                res = run_update_session(f.get("path", ""), board.active._h)
                port.send({**res, "id": rid})
            elif t == "quit":
                break
    finally:
        board.support.stop()
    return 0


def _status_dict(board: "StitchBoard") -> Dict[str, Any]:
    return {"monad": board.monad.status(), "active": board.active.status(),
            "support": board.support.status()}


def main() -> int:
    ap = argparse.ArgumentParser(description="PtolemyDesktop Core — chat + derivation console")
    ap.add_argument("--selftest", action="store_true", help="headless smoke, no curses")
    ap.add_argument("--port", action="store_true",
                    help="frame-protocol mode (console_link) — no curses")
    ap.add_argument("--harness", type=int, metavar="FD", default=None,
                    help="run curses with the speaking monad on a resident C "
                         "process (`ptol -w`) over frame FD")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.port:
        return run_port()          # hibernated: no curses; the desktop renders the tabs

    board = StitchBoard()
    if args.harness is not None:
        try:
            link = HarnessLink(args.harness)
            board.harness = link
            board.monad = HarnessMonad(link, board.monad)
            board.active = ActiveHarness(board.monad)
            link.send({"t": "attach", "who": "ptolemy_console"})
        except Exception:                                        # noqa: BLE001
            board.harness = None       # link failed -> in-process MonadLink stays
    # the speaking construction: rotary_rerun_boxkite first, everything else the
    # fallback chain (harness C console_speak / VAPMIP.Engine / stand-in)
    board.monad = BoxKiteMonad(board.monad)
    board.active = ActiveHarness(board.monad)
    # the Archimedes browsing Tab is a PtolemyDesktop-only affordance; a
    # PtolemyDesktop importer constructs PtolemyConsole(..., embedded=True),
    # or sets PTOLEMY_DESKTOP when it spawns this as a subprocess.
    embedded = bool(os.environ.get("PTOLEMY_DESKTOP"))
    curses.wrapper(
        lambda scr: PtolemyConsole(scr, board, board.registry,
                                   embedded=embedded).run())
    if board.harness is not None:
        try:
            board.harness.send({"t": "quit"})
        except Exception:                                        # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:      # belt-and-suspenders for the tiny window
        sys.exit(130)              # before run()'s own try/except is armed
