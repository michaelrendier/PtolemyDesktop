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

Two tabs:
    THE CHAT TAB       — this window: Ptolemy + the faces + the monad.
    THE VALAQUENTA TAB — the DerivationBrowser.  ARCHIMEDES runs it (guided
                         tour / mathematical encyclopedia / supercalculator).
                         Full stop.

The console runs its OWN tabs when standalone.  Installed in PtolemyDesktop it
is HIBERNATED — `--port` mode, no curses — and the desktop renders the tabs,
driving the console over the pty.  Archimedes' `run_tab(scr)` is the
standalone form; `act()` (three modes) is the hibernated form the desktop
calls.

Run:
    python3 ptolemy_console.py            # standalone curses app (both tabs)
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


class PtolemyConsole:
    def __init__(self, stdscr, board: StitchBoard, registry) -> None:
        self.scr = stdscr
        self.board = board
        self.registry = registry
        self.lines: List[str] = [
            f"{NAME} console — PtolemyDesktop Core.  "
            f"1-4 / ←→: tabs   Tab: ValaQuenta   "
            f"/paragraph /sentence /faces /poll /enc /radio /diag   q: quit",
            f"  {board.status_line()}", ""]
        self.input = ""
        # the tabs discussed — unbuilt ones are greyed and unselectable
        self.tabs: List[List[Any]] = [
            ["Chat", True], ["ValaQuenta", True],
            ["Generational Lineage", False], ["Archimedes", False]]
        self.tab = 0

    def _push(self, s: str) -> None:
        for seg in (textwrap.wrap(s, max(20, self.scr.getmaxyx()[1] - 2)) or [""]):
            self.lines.append(seg)

    def _flush_support(self) -> None:
        for ln in self.board.drain():                 # face posts -> Chat Tab
            self._push(ln)
        for ln in self.board.review_faces():          # Ptolemy's acks
            self._push(ln)

    def run(self) -> None:
        curses.curs_set(1)
        self.scr.nodelay(True)
        self.scr.keypad(True)
        self.board.support.start()
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
                if k in (ord("\t"),):
                    self._select_tab(1)          # Tab -> the ValaQuenta Tab
                elif k in (curses.KEY_F1, curses.KEY_F2, curses.KEY_F3, curses.KEY_F4):
                    self._select_tab(k - curses.KEY_F1)
                elif k in (curses.KEY_LEFT, curses.KEY_RIGHT) and not self.input:
                    self._move_tab(-1 if k == curses.KEY_LEFT else 1)
                elif k in (curses.KEY_ENTER, 10, 13):
                    self._submit()
                elif k in (curses.KEY_BACKSPACE, 127, 8):
                    self.input = self.input[:-1]
                elif k == 4:  # Ctrl-D
                    break
                elif 32 <= k < 127:
                    self.input += chr(k)
                if self.input.strip() == "q" and k in (curses.KEY_ENTER, 10, 13):
                    break
        finally:
            self.board.support.stop()

    def _submit(self) -> None:
        msg = self.input
        self.input = ""
        if not msg.strip():
            return
        self._push(f"{NAME}> {msg}")
        if msg.strip() == "q":
            return
        reply = self.board.route(msg)
        self._flush_support()
        if reply:
            self._push(f"  {reply}")

    def _move_tab(self, d: int) -> None:
        i = self.tab
        for _ in range(len(self.tabs)):
            i = (i + d) % len(self.tabs)
            if self.tabs[i][1]:
                self._select_tab(i)
                return

    def _select_tab(self, i: int) -> None:
        if not (0 <= i < len(self.tabs)):
            return
        name, on = self.tabs[i]
        if not on:
            self._push(f"({name} tab — greyed: not built yet)")
            return
        if name == "ValaQuenta":
            self.tab = i
            self._draw()
            self._derivation_subloop()
            self.tab = 0                 # ValaQuenta is a subloop; land back on Chat
            return
        self.tab = i

    def _derivation_subloop(self) -> None:
        """Tab into the ValaQuenta Tab.  Archimedes runs it."""
        arch = self.board.support.faces.get("Archimedes")
        if arch is None or not arch.runs_tab:
            self._push("(Archimedes has no ValaQuenta Tab)")
            return
        try:
            self.scr.nodelay(False)
            curses.curs_set(0)
            arch.run_tab(self.scr)
        except Exception as e:                                    # noqa: BLE001
            self._push(f"(ValaQuenta Tab error: {type(e).__name__}: {e})")
        finally:
            self.scr.nodelay(True)
            curses.curs_set(1)
            self._push("(back from the ValaQuenta Tab — Archimedes)")

    def _draw_tabbar(self, w: int) -> None:
        x = 0
        for i, (name, on) in enumerate(self.tabs):
            cell = f" {name} "
            if i == self.tab:
                attr = curses.A_REVERSE | curses.A_BOLD
            elif on:
                attr = curses.A_BOLD
            else:
                attr = curses.A_DIM
            try:
                if x < w - 1:
                    self.scr.addstr(0, x, cell[:max(0, w - 1 - x)], attr)
                x += len(cell)
                if x < w - 1:
                    self.scr.addstr(0, x, "│", curses.A_DIM)
                x += 1
            except curses.error:
                pass

    def _draw(self) -> None:
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        self._draw_tabbar(w)
        body = self.lines[-(h - 3):]
        for i, ln in enumerate(body):
            try:
                self.scr.addstr(i + 1, 0, ln[:w - 1])
            except curses.error:
                pass
        try:
            self.scr.addstr(h - 2, 0, self.board.status_line()[:w - 1], curses.A_DIM)
            prompt = f"{NAME}[{self.board._mode[:4]}]> {self.input}"
            self.scr.addstr(h - 1, 0, prompt[:w - 1])
        except curses.error:
            pass
        self.scr.refresh()


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
    curses.wrapper(lambda scr: PtolemyConsole(scr, board, board.registry).run())
    if board.harness is not None:
        try:
            board.harness.send({"t": "quit"})
        except Exception:                                        # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
