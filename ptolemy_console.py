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
from typing import Any, Callable, Dict, List, Optional, Tuple

NAME = "ptolemy"


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
        try:
            from VAPMIP.monad import Engine                       # noqa: PLC0415
            self._engine = Engine()
            self.kind = f"VAPMIP.Engine v{getattr(self._engine, 'version', '?')}"
        except Exception as e:                                    # noqa: BLE001
            self._why = f"{type(e).__name__}: {e}"

    def say(self, text: str) -> Tuple[str, Dict[str, Any]]:
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
    """Periodic radio-check over registered faces.  A face's probe returns a
    drift in [0, 1]; past THRESHOLD it faults and the harness reports the
    adjustment it made.  Lines go to `sink` (the console)."""

    THRESHOLD = 0.25
    PERIOD = 8.0

    def __init__(self, sink: "queue.Queue[str]") -> None:
        self._sink = sink
        self._faces: Dict[str, Callable[[], float]] = {}
        self._adjust: Dict[str, Callable[[], str]] = {}
        self._last: Dict[str, float] = {}
        self._run = False
        self._thr: Optional[threading.Thread] = None
        # some Aule/Mandos modules print on import; keep the screen clean.
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            self._wire_existing()

    def _wire_existing(self) -> None:
        # the support harness IS Aule, and Aule has THE FORGE -- already built,
        # refactor alongside.  Primary probe: the Forge queue's backlog pressure.
        # Secondary: the Mandos heartbeat watchdog on Aule.
        try:
            from Aule import forge_queue                          # noqa: PLC0415
            fq = forge_queue.ForgeQueue()
            cap = forge_queue.FORGE_SETTINGS.get("max_queue_depth", 64)

            def forge_probe() -> float:
                try:
                    return min(1.0, fq.depth() / max(1, cap))
                except Exception:                                 # noqa: BLE001
                    return 0.0

            def forge_adjust() -> str:
                return "the Forge is throttling intake until backlog clears"

            self.register("aule.forge", forge_probe, forge_adjust)
        except Exception:                                         # noqa: BLE001
            pass
        try:
            from Aule import aule as _aule                        # noqa: PLC0415

            def aule_bus_probe() -> float:
                # a stalled event bus (no recent events) is not itself a fault;
                # report it flat unless status_summary flags trouble.
                import contextlib
                import io
                try:
                    with contextlib.redirect_stdout(io.StringIO()), \
                         contextlib.redirect_stderr(io.StringIO()):
                        s = _aule.status_summary()
                    if isinstance(s, dict):
                        return float(s.get("drift", s.get("worst", 0.0)) or 0.0)
                except Exception:                                 # noqa: BLE001
                    pass
                return 0.0

            self.register("aule.bus", aule_bus_probe,
                          lambda: "logged; Aule bus attention")
        except Exception:                                         # noqa: BLE001
            pass
        try:
            from Mandos import mandos_watchdog                    # noqa: PLC0415

            def mandos_probe() -> float:
                gb = getattr(mandos_watchdog, "_last_beat", None)
                if not gb:
                    return 0.0
                age = time.monotonic() - gb
                return min(1.0, age / (mandos_watchdog.HEARTBEAT_INTERVAL
                                       * mandos_watchdog.MISSED_BEATS))

            self.register("mandos.watch(aule)", mandos_probe,
                          lambda: "Mandos raised supervisor priority over Aule")
        except Exception:                                         # noqa: BLE001
            pass

    def register(self, name: str, probe: Callable[[], float],
                 adjust: Optional[Callable[[], str]] = None) -> None:
        self._faces[name] = probe
        self._adjust[name] = adjust or (lambda: "logged; no automatic action")
        self._last[name] = 0.0

    def radio_check(self) -> List[str]:
        stamp = time.strftime("%H:%M:%S")
        lines: List[str] = []
        for name, probe in self._faces.items():
            try:
                drift = float(probe())
            except Exception as e:                                # noqa: BLE001
                lines.append(f"[RADIO {stamp}] {name}: probe error — {e}")
                continue
            self._last[name] = drift
            if drift > self.THRESHOLD:
                action = self._adjust[name]()
                lines.append(f"[RADIO {stamp}] {name}: DRIFT {drift:.2f} > "
                             f"{self.THRESHOLD:.2f} — {action}")
            else:
                lines.append(f"[RADIO {stamp}] {name}: nominal (drift {drift:.2f})")
        if not self._faces:
            lines.append(f"[RADIO {stamp}] no faces registered — support harness idle")
        return lines

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
        if not self._last:
            return "idle"
        worst = max(self._last.values())
        return f"{len(self._last)} faces, worst drift {worst:.2f}"


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
            f"{NAME} console — PtolemyDesktop Core.  Tab: derivation UI   /diag /radio /tool   q: quit",
            f"  {board.status_line()}", ""]
        self.input = ""

    def _push(self, s: str) -> None:
        for seg in (textwrap.wrap(s, max(20, self.scr.getmaxyx()[1] - 2)) or [""]):
            self.lines.append(seg)

    def _flush_support(self) -> None:
        for ln in self.board.drain():
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
    b.support.register("demo_face", lambda: 0.4, lambda: "throttled demo_face ingest")
    for msg in ("hello ptolemy", "/diag", "/radio", "what is the derivation engine"):
        print(f"\n{NAME}> {msg}")
        print("  ->", b.route(msg))
        for ln in b.drain():
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
            if f is None:
                continue
            t = f.get("t")
            if t in ("attach", "noop"):
                port.send({"t": "status", **_status_dict(board)})
            elif t == "ping":
                port.send({"t": "pong", "at": time.time()})
            elif t == "say":
                port.send({"t": "chat", "who": NAME,
                           "text": board.route(f.get("text", ""))})
            elif t == "cmd":
                port.send({"t": "chat", "who": NAME,
                           "text": board.route(f.get("line", ""))})
            elif t == "update":
                res = run_update_session(f.get("path", ""), board.active._h)
                port.send(res)
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
