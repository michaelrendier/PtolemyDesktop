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

Run:
    python3 ptolemy_console.py            # the curses app
    python3 ptolemy_console.py --selftest # headless: route a few turns, print

Runs under PtolemyDesktop/.venv (layered on ValaQuenta/.venv).  All cross-repo
imports are warn-not-fault: a missing Monad -> a stand-in; a missing engine
registry -> the chat still runs.
"""
from __future__ import annotations

import argparse
import curses
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
                 active: bool = False) -> None:
        self.name = name
        self.role = role or FACE_ROLES.get(name, "(registered)")
        self._probe = probe or (lambda: 0.0)
        self._adjust = adjust or (lambda: "logged; no automatic action")
        self._intrusion_of = intrusion_of or (lambda d: "drift")
        self._opinion = opinion
        self._act = act
        self.active = active
        self.last_drift = 0.0

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
#  SUPPORT harness  (Tolkien / Diagnostic Support)
# ══════════════════════════════════════════════════════════════════════════════
class SupportHarness:
    """The faces' room.  A periodic poll asks each face for a passive post; the
    posts go to `sink` (the Chat Tab), attributed to the face.  `latest` keeps
    the last post per face so Ptolemy can review and poll opinions.  Nothing
    here acts — Ptolemy routes any action through the active harness, and only
    Archimedes has an `act()` of its own."""

    THRESHOLD = 0.25
    PERIOD = 8.0

    def __init__(self, sink: "queue.Queue[str]") -> None:
        self._sink = sink
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
        # Archimedes — the Encyclopedia: the one active face.
        self.add_face(Face("Archimedes", probe=lambda: 0.0,
                           opinion=self._archimedes_opinion,
                           act=self._archimedes_act, active=True))

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
                                "equation", "why", "theorem")):
            return ("this is reference — I can speak to it", 0.9)
        return ("not a reference question", 0.3)

    @staticmethod
    def _archimedes_act(request: str) -> str:
        return (f"Archimedes: (maths/physics .bin not loaded) — noted '{request[:80]}'. "
                f"Load the domain corpus for a real answer.")

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
    def radio_check(self) -> List[str]:
        lines: List[str] = []
        for name, face in self.faces.items():
            post = face.report(self.THRESHOLD)
            self.latest[name] = post
            lines.append(f"[{post.stamp}] {post.line()}")
        if not self.faces:
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
            for ln in self.radio_check():
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
        self.support = SupportHarness(self.sink)
        self.active = ActiveHarness(self.monad)
        self._acked: set = set()          # (face, stamp, level) already routed

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
        if m.startswith("/monad"):
            arg = m[6:].strip().lower()
            if arg in ("off", "detach", "0"):
                self.monad.enabled = False
                return "(monad detached — harness + stitchboard stay live)"
            if arg in ("on", "attach", "1"):
                self.monad.enabled = True
                return "(monad attached)"
            return f"(monad {'attached' if self.monad.enabled else 'detached'})"
        reply, meta = self.monad.say(m)
        return reply

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
    def review_faces(self) -> List[str]:
        """Ptolemy looks at the latest face posts; for a warn / hardening post
        not yet acknowledged he routes it through the active harness and
        records a one-line ack.  Passive posts he leaves for the Chat Tab."""
        acks: List[str] = []
        for name, post in list(self.support.latest.items()):
            if post.level == "info":
                continue
            key = (name, post.stamp, post.level)
            if key in self._acked:
                continue
            self._acked.add(key)
            routed = self.active.present(
                f"{name}: {post.text}", kind=f"face-{post.level}")
            acks.append(f"{NAME}: ack «{name}» [{post.intrusion or post.level}] "
                        f"→ {str(routed)[:80]}")
        return acks

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
            f"{NAME} console — PtolemyDesktop Core.  Tab: ValaQuenta   "
            f"/faces /poll /enc /radio /diag /tool   q: quit",
            f"  {board.status_line()}", ""]
        self.input = ""

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
                    self._derivation_subloop()
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

    def _derivation_subloop(self) -> None:
        if self.registry is None:
            self._push("(no ValaQuenta registry — derivation UI unavailable)")
            return
        try:
            from ValaQuenta.engine.console_curses import DerivationBrowser  # noqa: PLC0415
            self.scr.nodelay(False)
            curses.curs_set(0)
            DerivationBrowser(self.scr, self.registry).run()
        except Exception as e:                                    # noqa: BLE001
            self._push(f"(derivation UI error: {type(e).__name__}: {e})")
        finally:
            self.scr.nodelay(True)
            curses.curs_set(1)
            self._push("(back from derivation UI)")

    def _draw(self) -> None:
        self.scr.erase()
        h, w = self.scr.getmaxyx()
        body = self.lines[-(h - 2):]
        for i, ln in enumerate(body):
            try:
                self.scr.addstr(i, 0, ln[:w - 1])
            except curses.error:
                pass
        try:
            self.scr.addstr(h - 2, 0, self.board.status_line()[:w - 1], curses.A_DIM)
            self.scr.addstr(h - 1, 0, f"{NAME}> {self.input}"[:w - 1])
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
                "/enc why is sigma one half", "/diag"):
        print(f"\n{NAME}> {msg}")
        print("  ->", b.route(msg))
        for ln in b.drain():
            print("    ", ln)
        for ln in b.review_faces():
            print("    ", ln)
    reg = _load_registry()
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
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.port:
        return run_port()
    board = StitchBoard()
    registry = _load_registry()
    curses.wrapper(lambda scr: PtolemyConsole(scr, board, registry).run())
    return 0


if __name__ == "__main__":
    sys.exit(main())
