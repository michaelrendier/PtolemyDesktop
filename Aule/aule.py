"""
aule.py — Aulë Face, Ptolemy Project
=====================================
The craftsman's forge.  Sandbox diagnostic area for Ptolemy.

Four capabilities:
  1. StreamMonitor   — live tap on any Ptolemy input stream (acquire.py, API calls, etc.)
  2. Forge           — run experimental code against live/captured data without touching production
  3. ReplayEngine    — capture → persist → inspect → replay diagnostic streams
  4. Probe           — interactive REPL into live Ptolemy state

Output:
  • TUI via curses  (live view)
  • JSON log files  (persistence, replay)

Directory layout created under ptolemy root:
  aule/
    streams/          raw captured stream JSON (one file per session)
    forge/            experimental scripts dropped here; Aulë runs them in isolation
    replays/          named replay sessions
    probe_history/    REPL command history per session
    aule.log          structured JSON event log

Usage:
  python aule.py monitor                  # live stream TUI
  python aule.py forge <script.py>        # run experimental script in sandbox
  python aule.py replay <session_name>    # replay a captured stream
  python aule.py probe                    # interactive REPL
  python aule.py status                   # summary of all captured sessions

Ptolemy integration:
  Any module can publish to Aulë's stream by importing and calling:
    from aule import stream_event
    stream_event("acquire", "word_fetched", {"word": "hiraeth", "sources": ["wiktionary"]})

Author: Ptolemy Project / Aulë Face
"""

import os
import sys
import json
import time
import curses
import signal
import socket
import hashlib
import inspect
import textwrap
import argparse
from Aule.aule_wiring import init_aule_wiring, aule_beat
import threading
import traceback
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from collections import deque
from typing import Any, Callable, Optional

# ── Directory bootstrap ───────────────────────────────────────────────────────

def _find_ptolemy_root() -> Path:
    """Walk up from aule.py to find the Ptolemy root (contains pharos/ or ptolemy_core.py)."""
    here = Path(__file__).resolve().parent
    for candidate in [here, here.parent, here.parent.parent]:
        if (candidate / "ptolemy_core.py").exists() or (candidate / "pharos").is_dir():
            return candidate
    return here  # fallback: run in place

PTOLEMY_ROOT = _find_ptolemy_root()
AULE_ROOT    = PTOLEMY_ROOT / "aule"

DIRS = {
    "streams":       AULE_ROOT / "streams",
    "forge":         AULE_ROOT / "forge",
    "replays":       AULE_ROOT / "replays",
    "probe_history": AULE_ROOT / "probe_history",
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

LOG_FILE = AULE_ROOT / "aule.log"

# ── Event bus (in-process pub/sub) ───────────────────────────────────────────

class _EventBus:
    """Lightweight in-process pub/sub.  Thread-safe."""

    def __init__(self):
        self._lock       = threading.Lock()
        self._listeners  : dict[str, list[Callable]] = {}
        self._ring       : deque = deque(maxlen=2000)   # last 2000 events in memory

    def subscribe(self, channel: str, fn: Callable):
        with self._lock:
            self._listeners.setdefault(channel, []).append(fn)

    def unsubscribe(self, channel: str, fn: Callable):
        with self._lock:
            if channel in self._listeners:
                self._listeners[channel] = [f for f in self._listeners[channel] if f is not fn]

    def publish(self, event: dict):
        with self._lock:
            self._ring.append(event)
            targets = list(self._listeners.get(event.get("channel", "*"), []))
            targets += list(self._listeners.get("*", []))
        for fn in targets:
            try:
                fn(event)
            except Exception:
                pass  # never let a subscriber crash the publisher

    def recent(self, n: int = 100, channel: Optional[str] = None) -> list:
        with self._lock:
            events = list(self._ring)
        if channel:
            events = [e for e in events if e.get("channel") == channel]
        return events[-n:]

BUS = _EventBus()

# ── Public API: stream_event ──────────────────────────────────────────────────

def stream_event(channel: str, event_type: str, payload: dict = None, *, source: str = None):
    """
    Publish a diagnostic event to Aulë's bus.

    Any Ptolemy module can call this.  It is a no-op if Aulë is not running —
    the event is still logged to the ring buffer and JSON log, but no TUI is required.

    Args:
        channel:    e.g. "acquire", "api", "kryptos", "hyperwebster"
        event_type: e.g. "word_fetched", "api_call_start", "index_computed"
        payload:    arbitrary dict of event data
        source:     auto-detected from call stack if not provided
    """
    if source is None:
        frame = inspect.stack()[1]
        source = f"{Path(frame.filename).name}:{frame.lineno}"

    event = {
        "ts":         datetime.now(timezone.utc).isoformat(),
        "ts_mono":    time.monotonic(),
        "channel":    channel,
        "type":       event_type,
        "source":     source,
        "payload":    payload or {},
        "session":    _SESSION_ID,
    }

    BUS.publish(event)
    _append_log(event)


# ── Session management ────────────────────────────────────────────────────────

_SESSION_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "_" + \
              hashlib.md5(socket.gethostname().encode()).hexdigest()[:6]

_current_stream_file : Optional[Path] = None
_stream_buffer       : list = []
_stream_lock         = threading.Lock()

def _append_log(event: dict):
    """Append event to the persistent JSON log (one JSON object per line)."""
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass

def _stream_writer_thread(path: Path, stop_event: threading.Event):
    """Background thread: flush stream buffer to JSON file every 2s."""
    while not stop_event.is_set():
        aule_beat()
        time.sleep(2)
        with _stream_lock:
            if _stream_buffer:
                with open(path, "a") as f:
                    for ev in _stream_buffer:
                        f.write(json.dumps(ev) + "\n")
                _stream_buffer.clear()
    # Final flush
    with _stream_lock:
        if _stream_buffer:
            with open(path, "a") as f:
                for ev in _stream_buffer:
                    f.write(json.dumps(ev) + "\n")
            _stream_buffer.clear()


# ── StreamMonitor (curses TUI) ────────────────────────────────────────────────

CHANNEL_COLORS = {
    "acquire":      2,   # green
    "api":          3,   # yellow
    "kryptos":      5,   # magenta
    "hyperwebster": 6,   # cyan
    "forge":        4,   # blue
    "probe":        3,   # yellow
    "error":        1,   # red
    "*":            7,   # white
}

def _channel_color(ch: str) -> int:
    return CHANNEL_COLORS.get(ch, 7)

class StreamMonitor:
    """
    Curses-based live stream TUI.

    Layout:
    ┌─────────────────────────────────────────────────┐
    │  Aulë Monitor  [session]  [time]                │  header
    ├─────────────────────────────────────────────────┤
    │  CHANNEL FILTER: [all]  events: 1234            │  status bar
    ├─────────────────────────────────────────────────┤
    │                                                 │
    │  [12:34:01] acquire  word_fetched  hiraeth      │  scrolling event pane
    │  [12:34:01] api      call_start    anthropic    │
    │  ...                                            │
    ├─────────────────────────────────────────────────┤
    │  [detail pane — selected event JSON]            │  detail
    ├─────────────────────────────────────────────────┤
    │  q:quit  f:filter  c:clear  p:pause  s:save     │  help bar
    └─────────────────────────────────────────────────┘
    """

    def __init__(self):
        self.events        : deque = deque(maxlen=5000)
        self.paused        = False
        self.channel_filter: Optional[str] = None
        self.selected_idx  = 0
        self.scroll_offset = 0
        self.lock          = threading.Lock()
        self._saved        = False

    def _on_event(self, event: dict):
        if not self.paused:
            with self.lock:
                self.events.append(event)

    def _filtered(self) -> list:
        with self.lock:
            evs = list(self.events)
        if self.channel_filter:
            evs = [e for e in evs if e.get("channel") == self.channel_filter]
        return evs

    def _save_session(self):
        name = f"monitor_{_SESSION_ID}.json"
        path = DIRS["streams"] / name
        evs = self._filtered()
        with open(path, "w") as f:
            json.dump({"session": _SESSION_ID, "events": evs}, f, indent=2)
        self._saved = True
        return path

    def run(self):
        BUS.subscribe("*", self._on_event)
        # Seed with recent events already in ring
        for ev in BUS.recent(200):
            self.events.append(ev)
        try:
            curses.wrapper(self._main)
        finally:
            BUS.unsubscribe("*", self._on_event)

    def _main(self, stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED,     -1)
        curses.init_pair(2, curses.COLOR_GREEN,   -1)
        curses.init_pair(3, curses.COLOR_YELLOW,  -1)
        curses.init_pair(4, curses.COLOR_BLUE,    -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_CYAN,    -1)
        curses.init_pair(7, curses.COLOR_WHITE,   -1)
        curses.init_pair(8, curses.COLOR_BLACK,   curses.COLOR_WHITE)  # highlight

        stdscr.nodelay(True)
        stdscr.timeout(100)

        detail_height = 6
        help_height   = 1
        status_height = 1
        header_height = 1

        while True:
            try:
                max_y, max_x = stdscr.getmaxyx()
                list_height  = max_y - header_height - status_height - detail_height - help_height - 2

                stdscr.erase()

                # ── Header ────────────────────────────────────────────
                header = f"  ⚒  Aulë Monitor  │  session: {_SESSION_ID}  │  {datetime.now().strftime('%H:%M:%S')}"
                stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
                stdscr.addstr(0, 0, header[:max_x-1].ljust(max_x-1))
                stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)

                # ── Status bar ────────────────────────────────────────
                evs    = self._filtered()
                filt   = self.channel_filter or "all"
                paused = "  ⏸ PAUSED" if self.paused else ""
                saved  = "  ✓ saved" if self._saved else ""
                status = f"  filter: [{filt}]  events: {len(evs)}{paused}{saved}"
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(1, 0, status[:max_x-1].ljust(max_x-1))
                stdscr.attroff(curses.color_pair(3))

                # ── Divider ───────────────────────────────────────────
                stdscr.addstr(2, 0, "─" * (max_x-1))

                # ── Event list ────────────────────────────────────────
                if evs:
                    visible_start = max(0, len(evs) - list_height - self.scroll_offset)
                    visible       = evs[visible_start: visible_start + list_height]
                    sel_in_view   = self.selected_idx - visible_start

                    for row_i, ev in enumerate(visible):
                        y = 3 + row_i
                        if y >= 3 + list_height:
                            break

                        ts      = ev.get("ts","")[-15:-4] if ev.get("ts") else "??:??:??"  # HH:MM:SS.mmm
                        chan    = (ev.get("channel") or "?")[:12].ljust(12)
                        etype  = (ev.get("type") or "?")[:20].ljust(20)
                        src    = (ev.get("source") or "")[:20]
                        # Show first payload value as hint
                        pload  = ev.get("payload", {})
                        hint   = ""
                        if pload:
                            k, v = next(iter(pload.items()))
                            hint = f"  {k}={str(v)[:30]}"

                        line   = f"  [{ts}]  {chan}  {etype}  {src}{hint}"
                        color  = curses.color_pair(_channel_color(ev.get("channel","*")))

                        abs_idx = visible_start + row_i
                        if abs_idx == self.selected_idx:
                            stdscr.attron(curses.color_pair(8) | curses.A_BOLD)
                            stdscr.addstr(y, 0, line[:max_x-1].ljust(max_x-1))
                            stdscr.attroff(curses.color_pair(8) | curses.A_BOLD)
                        else:
                            stdscr.attron(color)
                            stdscr.addstr(y, 0, line[:max_x-1])
                            stdscr.attroff(color)
                else:
                    stdscr.attron(curses.color_pair(3))
                    stdscr.addstr(3 + list_height//2, max_x//2 - 15,
                                  "  waiting for stream events...  ")
                    stdscr.attroff(curses.color_pair(3))

                # ── Detail pane ───────────────────────────────────────
                detail_y = 3 + list_height
                stdscr.addstr(detail_y, 0, "─" * (max_x-1))
                if evs and 0 <= self.selected_idx < len(evs):
                    ev   = evs[self.selected_idx]
                    blob = json.dumps(ev, indent=2)
                    lines = blob.split("\n")
                    for i, line in enumerate(lines[:detail_height]):
                        if detail_y + 1 + i < max_y - 1:
                            stdscr.attron(curses.color_pair(7))
                            stdscr.addstr(detail_y + 1 + i, 2, line[:max_x-4])
                            stdscr.attroff(curses.color_pair(7))

                # ── Help bar ──────────────────────────────────────────
                help_y = max_y - 1
                help_txt = "  q:quit  ↑↓:select  f:filter  c:clear  p:pause/resume  s:save  r:replay"
                stdscr.attron(curses.color_pair(8))
                stdscr.addstr(help_y, 0, help_txt[:max_x-1].ljust(max_x-1))
                stdscr.attroff(curses.color_pair(8))

                stdscr.refresh()

                # ── Input ─────────────────────────────────────────────
                k = stdscr.getch()
                if k == ord('q'):
                    break
                elif k == ord('p'):
                    self.paused = not self.paused
                    self._saved = False
                elif k == ord('c'):
                    with self.lock:
                        self.events.clear()
                    self.selected_idx = 0
                    self._saved = False
                elif k == ord('s'):
                    path = self._save_session()
                    self._saved = True
                elif k == ord('f'):
                    # Simple channel filter cycle
                    channels = list({e.get("channel","?") for e in self.events}) + [None]
                    try:
                        idx = channels.index(self.channel_filter)
                        self.channel_filter = channels[(idx+1) % len(channels)]
                    except ValueError:
                        self.channel_filter = channels[0] if channels else None
                elif k == ord('r'):
                    path = self._save_session()
                    # Signal replay
                    break
                elif k == curses.KEY_UP:
                    self.selected_idx = max(0, self.selected_idx - 1)
                elif k == curses.KEY_DOWN:
                    evs2 = self._filtered()
                    self.selected_idx = min(len(evs2)-1, self.selected_idx + 1)

            except curses.error:
                pass


# ── Forge (experimental sandbox runner) ──────────────────────────────────────

class Forge:
    """
    Run experimental scripts in an isolated subprocess with stream capture.

    The forged script gets:
      - AULE_SESSION env var
      - PTOLEMY_ROOT env var
      - aule module importable (so it can call stream_event)
      - A captured JSON stream of all events it publishes

    The production codebase is never imported or modified.
    """

    def __init__(self):
        self.results : list[dict] = []

    def run(self, script_path: str, args: list[str] = None, live: bool = True):
        script = Path(script_path)
        if not script.exists():
            # Check forge directory
            forge_path = DIRS["forge"] / script_path
            if forge_path.exists():
                script = forge_path
            else:
                print(f"[Aulë Forge] Script not found: {script_path}")
                return None

        session_name = f"forge_{script.stem}_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
        output_path  = DIRS["streams"] / f"{session_name}.json"

        env = os.environ.copy()
        env["AULE_SESSION"]  = _SESSION_ID
        env["AULE_LOG"]      = str(output_path)
        env["PTOLEMY_ROOT"]  = str(PTOLEMY_ROOT)
        env["PYTHONPATH"]    = str(PTOLEMY_ROOT) + os.pathsep + env.get("PYTHONPATH","")

        cmd = [sys.executable, str(script)] + (args or [])

        print(f"\n[Aulë Forge] ⚒  Running: {script.name}")
        print(f"[Aulë Forge]    Session: {session_name}")
        print(f"[Aulë Forge]    Output:  {output_path}")
        print(f"[Aulë Forge] {'─'*50}")

        events    = []
        start_ts  = time.monotonic()
        returncode = None

        try:
            proc = subprocess.Popen(
                cmd, env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_lines = []
            stderr_lines = []

            def read_stream(stream, lines, label, color_code):
                for line in stream:
                    line = line.rstrip()
                    lines.append(line)
                    if live:
                        print(f"\033[{color_code}m[{label}]\033[0m {line}")
                    # Detect structured events in stdout
                    if line.startswith('{"ts"'):
                        try:
                            ev = json.loads(line)
                            events.append(ev)
                            BUS.publish(ev)
                        except Exception:
                            pass

            t_out = threading.Thread(target=read_stream, args=(proc.stdout, stdout_lines, "stdout", "32"))
            t_err = threading.Thread(target=read_stream, args=(proc.stderr, stderr_lines, "stderr", "33"))
            t_out.start(); t_err.start()
            t_out.join();  t_err.join()
            proc.wait()
            returncode = proc.returncode

        except KeyboardInterrupt:
            proc.kill()
            returncode = -1

        elapsed = time.monotonic() - start_ts

        result = {
            "session":    session_name,
            "script":     str(script),
            "args":       args or [],
            "returncode": returncode,
            "elapsed_s":  round(elapsed, 3),
            "events":     events,
            "stdout":     stdout_lines,
            "stderr":     stderr_lines,
            "ts":         datetime.now(timezone.utc).isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)

        self.results.append(result)

        status = "✓ OK" if returncode == 0 else f"✗ exit {returncode}"
        print(f"\n[Aulë Forge] {'─'*50}")
        print(f"[Aulë Forge] {status}  elapsed: {elapsed:.3f}s  events: {len(events)}")
        print(f"[Aulë Forge] Saved: {output_path}")

        return result


# ── ReplayEngine ─────────────────────────────────────────────────────────────

class ReplayEngine:
    """
    Load a captured stream JSON and replay it through the event bus at original
    timing (or accelerated/instant).

    Useful for:
      - Reproducing a specific acquisition run against new processing code
      - Testing diagnostic visualisations against known data
      - Debugging timing-sensitive stream interactions
    """

    def __init__(self):
        self.sessions : dict[str, Path] = self._discover()

    def _discover(self) -> dict[str, Path]:
        out = {}
        for f in sorted(DIRS["streams"].glob("*.json")):
            out[f.stem] = f
        return out

    def list_sessions(self):
        self.sessions = self._discover()
        if not self.sessions:
            print("[Aulë Replay] No captured sessions found.")
            return
        print(f"\n[Aulë Replay] {'─'*60}")
        print(f"  {'Session':<45}  {'Events':>7}  {'Size':>8}")
        print(f"  {'─'*45}  {'─'*7}  {'─'*8}")
        for name, path in sorted(self.sessions.items()):
            size = path.stat().st_size
            try:
                data = json.loads(path.read_text())
                n_events = len(data.get("events", []))
            except Exception:
                # NDJSON fallback
                n_events = sum(1 for _ in open(path))
            print(f"  {name:<45}  {n_events:>7}  {size//1024:>6}KB")
        print()

    def load(self, session_name: str) -> list[dict]:
        self.sessions = self._discover()
        path = self.sessions.get(session_name)
        if not path:
            # Try partial match
            matches = [k for k in self.sessions if session_name in k]
            if len(matches) == 1:
                path = self.sessions[matches[0]]
            elif len(matches) > 1:
                print(f"[Aulë Replay] Ambiguous: {matches}")
                return []
            else:
                print(f"[Aulë Replay] Session not found: {session_name}")
                return []

        try:
            data = json.loads(path.read_text())
            return data.get("events", [])
        except Exception:
            # Try NDJSON
            events = []
            for line in open(path):
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except Exception:
                        pass
            return events

    def replay(self, session_name: str, speed: float = 1.0, channel_filter: str = None):
        """
        Replay events through the bus.
        speed=1.0 → real time, speed=0 → instant, speed=2.0 → 2× faster
        """
        events = self.load(session_name)
        if not events:
            return

        if channel_filter:
            events = [e for e in events if e.get("channel") == channel_filter]

        print(f"\n[Aulë Replay] ▶  {session_name}")
        print(f"[Aulë Replay]    {len(events)} events  speed={speed}×")
        print(f"[Aulë Replay] {'─'*50}")

        if not events:
            print("[Aulë Replay] No events after filter.")
            return

        base_mono = events[0].get("ts_mono", 0)
        replay_start = time.monotonic()

        for ev in events:
            if speed > 0:
                target_offset = (ev.get("ts_mono", 0) - base_mono) / speed
                now_offset    = time.monotonic() - replay_start
                sleep_for     = target_offset - now_offset
                if sleep_for > 0:
                    time.sleep(sleep_for)

            # Tag as replay
            ev_copy = dict(ev)
            ev_copy["replay"]  = True
            ev_copy["session"] = _SESSION_ID

            BUS.publish(ev_copy)

            chan  = ev.get("channel","?")[:10]
            etype = ev.get("type","?")[:20]
            print(f"  ▶ {chan:<10}  {etype}")

        print(f"\n[Aulë Replay] ■  done")


# ── Probe (REPL into Ptolemy state) ──────────────────────────────────────────

class Probe:
    """
    Interactive REPL with Ptolemy context pre-loaded.

    Available in the REPL namespace:
      bus          — the global event bus
      stream_event — publish an event manually
      forge        — Forge instance
      replay       — ReplayEngine instance
      events()     — recent events
      P            — PTOLEMY_ROOT path
      help_aule()  — this help

    History is saved to aule/probe_history/<session>.txt
    """

    BANNER = """
  ╔══════════════════════════════════════════════════════╗
  ║  Aulë Probe  —  Ptolemy Diagnostic REPL             ║
  ║  "He made things for the delight in the craft"      ║
  ╠══════════════════════════════════════════════════════╣
  ║  bus          event bus (subscribe, publish, recent) ║
  ║  stream_event publish a manual event                 ║
  ║  forge        Forge instance (.run, .results)        ║
  ║  replay       ReplayEngine (.list_sessions, .replay) ║
  ║  events(n)    recent n events from ring buffer       ║
  ║  P            PTOLEMY_ROOT path                      ║
  ║  help_aule()  this message                           ║
  ║  Ctrl+D / exit()  quit                               ║
  ╚══════════════════════════════════════════════════════╝
"""

    def __init__(self):
        self._forge  = Forge()
        self._replay = ReplayEngine()
        self._history_file = DIRS["probe_history"] / f"probe_{_SESSION_ID}.txt"

    def _namespace(self) -> dict:
        return {
            "bus":          BUS,
            "stream_event": stream_event,
            "forge":        self._forge,
            "replay":       self._replay,
            "events":       BUS.recent,
            "P":            PTOLEMY_ROOT,
            "help_aule":    lambda: print(self.BANNER),
            "__doc__":      "Aulë Probe — Ptolemy diagnostic REPL",
        }

    def run(self):
        import code
        import readline
        import rlcompleter

        print(self.BANNER)

        ns = self._namespace()
        readline.set_completer(rlcompleter.Completer(ns).complete)
        readline.parse_and_bind("tab: complete")

        # Load history
        if self._history_file.exists():
            try:
                readline.read_history_file(str(self._history_file))
            except Exception:
                pass

        console = code.InteractiveConsole(locals=ns)
        try:
            console.interact(banner="", exitmsg="")
        finally:
            try:
                readline.write_history_file(str(self._history_file))
            except Exception:
                pass


# ── Status summary ────────────────────────────────────────────────────────────

def status_summary():
    """Print a summary of all captured Aulë sessions."""
    re = ReplayEngine()
    print(f"\n  Aulë Face — Ptolemy Diagnostic Forge")
    print(f"  Root:    {AULE_ROOT}")
    print(f"  Session: {_SESSION_ID}")
    re.list_sessions()

    # Log file stats
    if LOG_FILE.exists():
        lines = sum(1 for _ in open(LOG_FILE))
        size  = LOG_FILE.stat().st_size // 1024
        print(f"  aule.log: {lines} events  ({size}KB)")
    else:
        print(f"  aule.log: empty")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    init_aule_wiring()
    parser = argparse.ArgumentParser(
        prog="aule",
        description="Aulë Face — Ptolemy Diagnostic Forge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Commands:
          monitor               Live stream TUI (curses)
          forge <script.py>     Run experimental script in sandbox
          replay <session>      Replay a captured stream
          replay --list         List all captured sessions
          probe                 Interactive REPL into Ptolemy state
          status                Summary of all sessions and log stats

        Examples:
          python aule.py monitor
          python aule.py forge aule/forge/test_acquire.py
          python aule.py replay --list
          python aule.py replay forge_test_acquire_20260418T120000 --speed 2
          python aule.py probe
        """)
    )
    parser.add_argument("command", nargs="?", default="status",
                        choices=["monitor","forge","replay","probe","status"])
    parser.add_argument("target", nargs="?", help="Script path (forge) or session name (replay)")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Replay speed multiplier (0=instant, 1=real-time, 2=2× faster)")
    parser.add_argument("--channel", type=str, default=None,
                        help="Filter by channel name")
    parser.add_argument("--list", action="store_true",
                        help="List available replay sessions")
    parser.add_argument("args", nargs="*", help="Extra args forwarded to forged script")

    opts = parser.parse_args()

    if opts.command == "status" or opts.command is None:
        status_summary()

    elif opts.command == "monitor":
        mon = StreamMonitor()
        # Inject a welcome event so the TUI has something to show immediately
        stream_event("aule", "monitor_start", {"message": "Aulë Monitor started", "root": str(PTOLEMY_ROOT)})
        mon.run()

    elif opts.command == "forge":
        if not opts.target:
            parser.error("forge requires a script path")
        f = Forge()
        f.run(opts.target, args=opts.args)

    elif opts.command == "replay":
        re = ReplayEngine()
        if opts.list or not opts.target:
            re.list_sessions()
        else:
            re.replay(opts.target, speed=opts.speed, channel_filter=opts.channel)

    elif opts.command == "probe":
        p = Probe()
        p.run()


if __name__ == "__main__":
    main()
