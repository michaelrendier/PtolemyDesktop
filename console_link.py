#!/usr/bin/env python3
"""
console_link.py — the STANDARDIZED connection to PtolemyDesktop Core.

One protocol, two transports.  Anything (the Qt/PGui desktop, another face, a
test) attaches the same way; the console never learns who is on the other end.

TRANSPORT
    stdio   the console reads stdin / writes stdout as newline-JSON frames
    pty     pty.openpty(); the Qt side attaches a QSocketNotifier to the slave,
            the console runs its loop on the master

FRAMES  (newline-delimited JSON, {"t": <type>, ...})
    in  -> console : say | cmd | attach | update | ping
    out <- console : chat | radio | status | derive | update.result | pong | error

THE UPDATE SESSION
    frame {"t":"update","kind":"pyqt6","path":".../Face.py"} runs UpdateSession:
      1. AST-parse the file (never executed -- safe on Qt imports)
      2. extract_module_menu(path)  -> Pharos/menus/<name>.menu
      3. reconcile against PGui's P-class shim:
           pgui_ready   widget names already covered by a P-class
           pgui_added   widget names with no P-alias -> appended to PGui (idempotent)
           qt5_only     names gone in Qt6 (QtWebKit, QDesktopWidget, ...) -> manual
      4. suggested import line (PyQt5.* -> Pharos.PGui P-classes)
      5. register the face's menu-derived API with the active harness
    returns an  update.result  frame naming everything that changed.
"""
from __future__ import annotations

import ast
import io
import json
import os
import pty
import re
import select
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_PGUI = os.path.join(_HERE, "Pharos", "PGui.py")
_MENUS = os.path.join(_HERE, "Pharos", "menus")

# Qt widget symbols known to have a P-class shim in PGui (kept in sync with the
# passthrough-alias block).
_PGUI_BASE = {
    "QMainWindow": "PMainWindow", "QWidget": "PWidget", "QPushButton": "PButton",
    "QLineEdit": "PLineEdit", "QLabel": "PLabel", "QComboBox": "PComboBox",
    "QTabWidget": "PTabWidget", "QDockWidget": "PDockWidget",
    "QTextEdit": "PTextEdit", "QListWidget": "PListWidget",
    "QTableWidget": "PTableWidget",
}
# QtWidgets classes an update session MAY safely alias into PGui (all real
# widgets/layouts -- the shim's job).  QtCore / QtGui types (QUrl, QColor,
# QIcon, QFont, QEvent, ...) are NOT PGui's concern: they're stable across
# Qt5->Qt6 and a face imports them straight from PyQt6.
_PGUI_ALIASABLE = {
    "QVBoxLayout", "QHBoxLayout", "QGridLayout", "QFormLayout", "QStackedLayout",
    "QScrollArea", "QSplitter", "QGroupBox", "QCheckBox", "QRadioButton",
    "QSlider", "QDial", "QProgressBar", "QSpinBox", "QDoubleSpinBox",
    "QPlainTextEdit", "QTreeWidget", "QTreeView", "QListView", "QTableView",
    "QMenuBar", "QMenu", "QToolBar", "QStatusBar", "QDialog", "QFrame",
    "QStackedWidget", "QToolButton", "QSizePolicy", "QSpacerItem",
    "QGraphicsView", "QGraphicsScene", "QGraphicsProxyWidget",
    "QFileDialog", "QMessageBox", "QInputDialog", "QColorDialog", "QAbstractItemView",
}
# gone in Qt6 -- an update session can't fix these automatically
_QT5_ONLY = {"QtWebKit", "QtWebKitWidgets", "QDesktopWidget", "QRegExp",
             "QGLWidget", "QWebView", "QWebPage", "QAction", "QShortcut"}
# ^ QAction/QShortcut moved QtWidgets->QtGui in Qt6 (import fix, not a widget)


# ══════════════════════════════════════════════════════════════════════════════
#  transport
# ══════════════════════════════════════════════════════════════════════════════
class ConsolePort:
    """Framed-JSON transport over a pair of file objects."""

    def __init__(self, rfile, wfile) -> None:
        self._r = rfile
        self._w = wfile
        self._buf = ""

    @classmethod
    def stdio(cls) -> "ConsolePort":
        return cls(sys.stdin, sys.stdout)

    def send(self, frame: Dict[str, Any]) -> None:
        self._w.write(json.dumps(frame, default=str) + "\n")
        self._w.flush()

    def recv(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        try:
            fd = self._r.fileno()
        except (AttributeError, OSError):
            fd = None
        if fd is not None and timeout is not None:
            if not select.select([fd], [], [], timeout)[0]:
                return None
        line = self._r.readline()
        if not line:
            return None
        line = line.strip()
        if not line:
            return {"t": "noop"}
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return {"t": "chat", "who": "console", "text": line}


# ══════════════════════════════════════════════════════════════════════════════
#  client side  (PtolemyDesktop imports this)
# ══════════════════════════════════════════════════════════════════════════════
class ConsoleClient:
    """Spawn `ptolemy_console.py --port` over a pty and talk to it in frames.

    A background reader pulls every frame into a queue.  say/command/feed_pyqt6
    send, then wait for their own terminal frame; radio/status/derive frames
    stay in the queue for `.events()`."""

    def __init__(self, python: Optional[str] = None) -> None:
        import queue as _q
        self.python = python or sys.executable
        self._proc: Optional[subprocess.Popen] = None
        self._port: Optional[ConsolePort] = None
        self._q: "_q.Queue[Dict[str, Any]]" = _q.Queue()
        self._reader: Optional[threading.Thread] = None
        self._run = False

    def attach(self) -> "ConsoleClient":
        import termios
        import tty
        master, slave = pty.openpty()
        tty.setraw(slave)
        attrs = termios.tcgetattr(slave)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, attrs)
        self._proc = subprocess.Popen(
            [self.python, os.path.join(_HERE, "ptolemy_console.py"), "--port"],
            stdin=slave, stdout=slave, stderr=subprocess.DEVNULL,
            close_fds=True, cwd=_HERE)
        os.close(slave)
        m = io.TextIOWrapper(io.FileIO(master, "r+"), write_through=True,
                             newline="\n")
        self._port = ConsolePort(m, m)
        self._run = True
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self.send({"t": "attach", "who": "console_client"})
        return self

    def _read_loop(self) -> None:
        while self._run and self._port:
            try:
                f = self._port.recv(timeout=0.5)
            except (OSError, ValueError):        # fd closed under us on shutdown
                break
            if f and f.get("t") != "noop":
                self._q.put(f)

    def send(self, frame: Dict[str, Any]) -> None:
        assert self._port
        self._port.send(frame)

    def _await(self, kind: str, timeout: float = 15.0) -> Optional[Dict[str, Any]]:
        """Wait for a frame of type `kind` (or `error`).  Frames that arrive
        while waiting but don't match — radio / status / derive — are put back
        on the queue for `.events()`, so diagnostics are never swallowed by an
        RPC."""
        deadline = time.time() + timeout
        held: List[Dict[str, Any]] = []
        hit: Optional[Dict[str, Any]] = None
        while time.time() < deadline:
            try:
                f = self._q.get(timeout=max(0.0, deadline - time.time()))
            except Exception:                                    # noqa: BLE001
                break
            if f.get("t") in (kind, "error"):
                hit = f
                break
            held.append(f)
        for f in held:
            self._q.put(f)
        return hit

    def events(self) -> List[Dict[str, Any]]:
        """Drain queued radio / status / derive frames (non-blocking)."""
        out: List[Dict[str, Any]] = []
        while True:
            try:
                out.append(self._q.get_nowait())
            except Exception:                                    # noqa: BLE001
                return out

    def say(self, text: str) -> str:
        self.send({"t": "say", "text": text})
        f = self._await("chat")
        return (f or {}).get("text", "(no reply)")

    def command(self, line: str) -> str:
        self.send({"t": "cmd", "line": line})
        f = self._await("chat")
        return (f or {}).get("text", "(no reply)")

    def feed_pyqt6(self, path: str) -> Dict[str, Any]:
        """Hand a PyQt5/PyQt6 face to the console's update session."""
        self.send({"t": "update", "kind": "pyqt6", "path": os.path.abspath(path)})
        return self._await("update.result") or {
            "t": "update.result", "ok": False, "error": "no result frame"}

    def close(self) -> None:
        self._run = False
        try:
            self.send({"t": "quit"})
        except Exception:                                        # noqa: BLE001
            pass
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except Exception:                                    # noqa: BLE001
                self._proc.kill()
        # unblock the reader's readline() by closing the pty master, then join
        if self._port is not None:
            try:
                self._port._r.close()
            except Exception:                                    # noqa: BLE001
                pass
        if self._reader is not None:
            self._reader.join(timeout=1.0)
        self._port = None


# ══════════════════════════════════════════════════════════════════════════════
#  the update session
# ══════════════════════════════════════════════════════════════════════════════
def _pgui_aliases_present() -> Dict[str, str]:
    present = dict(_PGUI_BASE)
    try:
        src = open(_PGUI).read()
        for m in re.finditer(r"^\s*(P[A-Za-z]+)\s*=\s*(Q[A-Za-z]+)\s*(?:#.*)?$",
                             src, re.M):
            present[m.group(2)] = m.group(1)
    except OSError:
        pass
    return present


_AUTO_IMPORT_MARK = "# --- QtWidgets auto-added by update sessions ---"


def _append_pgui_alias(qname: str) -> str:
    """Idempotently make PGui expose  P<Name>  for a QtWidgets class:
    (1) ensure a standalone `from PyQt6.QtWidgets import <qname>` line exists
        (a separate marked line -- never edits the existing import tuple),
    (2) add  P<Name> = Q<Name>  to the passthrough-alias block."""
    pname = "P" + qname[1:]
    src = open(_PGUI).read()
    changed = False

    # (1) the import — one marked line we own, extend it in place
    if _AUTO_IMPORT_MARK not in src:
        anchor = "#  PASSTHROUGH ALIASES"
        src = src.replace(anchor,
                          f"{_AUTO_IMPORT_MARK}\nfrom PyQt6.QtWidgets import "
                          f"{qname}\n\n{anchor}", 1)
        changed = True
    elif not re.search(rf"^from PyQt6\.QtWidgets import .*\b{qname}\b", src, re.M):
        src = re.sub(rf"({re.escape(_AUTO_IMPORT_MARK)}\nfrom PyQt6\.QtWidgets import [^\n]+)",
                     rf"\1, {qname}", src, count=1)
        changed = True

    # (2) the alias  (allow a trailing comment)
    if not re.search(rf"^\s*{pname}\s*=\s*{qname}\b", src, re.M):
        anchor = "PTableWidget = QTableWidget"
        if anchor in src:
            src = src.replace(anchor, anchor + f"\n{pname:<13}= {qname}"
                              f"   # auto-added by an update session", 1)
            changed = True

    if changed:
        open(_PGUI, "w").write(src)
    return pname


def run_update_session(path: str, active_harness=None) -> Dict[str, Any]:
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        src = open(path).read()
        tree = ast.parse(src)
    except Exception as e:                                       # noqa: BLE001
        return {"t": "update.result", "ok": False, "path": path,
                "error": f"parse: {type(e).__name__}: {e}"}

    # face / widget classes
    face_classes: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
            if any(b.startswith(("Q", "P")) or b.endswith("Face") for b in bases):
                face_classes.append(f"{node.name}({', '.join(bases)})")

    # Qt symbols used
    qt_modules: set = set()
    qt_names: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and \
                node.module.startswith(("PyQt5", "PyQt6")):
            sub = node.module.split(".")
            if len(sub) > 1:
                qt_modules.add(sub[1])
            for a in node.names:
                qt_names.add(a.name)
    # widget-ish names actually referenced
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    widgets = {w for w in (qt_names | used) if re.fullmatch(r"Q[A-Z][A-Za-z]+", w)}

    present = _pgui_aliases_present()
    pgui_ready = sorted(w for w in widgets if w in present)
    qt5_only = sorted((qt_modules | widgets) & _QT5_ONLY)
    # only alias real QtWidgets classes; never QtCore/QtGui types
    to_add = sorted(w for w in widgets
                    if w not in present and w in _PGUI_ALIASABLE)
    core_gui = sorted(w for w in widgets
                      if w not in present and w not in _PGUI_ALIASABLE
                      and w not in _QT5_ONLY)
    pgui_added = [_append_pgui_alias(w) for w in to_add]

    # menu
    menu_path = ""
    try:
        sys.path.insert(0, _HERE)
        from Pharos.PGui import extract_module_menu                # noqa: PLC0415
        menu_path = extract_module_menu(path, menu_name=name)
    except Exception as e:                                        # noqa: BLE001
        menu_path = f"(menu extraction failed: {type(e).__name__}: {e})"

    # suggested import rewrite
    p_map = {**present, **{w: "P" + w[1:] for w in to_add}}
    lines_out = []
    pgui_import = sorted(p_map[w] for w in widgets if w in p_map)
    if pgui_import:
        lines_out.append("from Pharos.PGui import " + ", ".join(pgui_import))
    if core_gui:
        lines_out.append("from PyQt6.QtGui import " + ", ".join(sorted(core_gui))
                         + "   # (QtCore/QtGui types — import direct, not via PGui)")
    if qt5_only:
        lines_out.append("# MANUAL: " + ", ".join(qt5_only)
                         + " — no Qt6 equivalent / moved module")
    suggested = "\n".join(lines_out) or "(no widget imports)"

    # register with the active harness (menu-derived API)
    registered = []
    if active_harness is not None:
        try:
            active_harness.register(name, ["face", "ui"],
                                    lambda cap, act, **p: {"ok": True,
                                                           "face": name, "act": act})
            registered = [name]
        except Exception:                                        # noqa: BLE001
            pass

    return {
        "t": "update.result", "ok": True, "path": path, "module": name,
        "face_classes": face_classes,
        "qt_modules": sorted(qt_modules),
        "pgui_ready": pgui_ready,
        "pgui_added": pgui_added,
        "core_gui": core_gui,
        "qt5_only": qt5_only,
        "suggested_import": suggested,
        "menu": menu_path,
        "harness_registered": registered,
        "note": "PGui aliases auto-added; qt5_only names need a manual Qt6 "
                "equivalent (QtWebKit gone, QDesktopWidget -> primaryScreen); "
                "the face file's own import lines are reported, not rewritten.",
    }


def _roundtrip(python: Optional[str] = None) -> int:
    """Spawn the console over a pty and exercise every frame type once."""
    c = ConsoleClient(python=python or os.path.join(_HERE, ".venv/bin/python3")
                      if os.path.exists(os.path.join(_HERE, ".venv/bin/python3"))
                      else None).attach()
    ok = True
    try:
        time.sleep(1.0)
        boot = [e.get("t") for e in c.events()]
        print(f"  boot frames      : {boot}")
        say = c.say("hello ptolemy")
        print(f"  say -> chat      : {say[:60]!r}")
        ok &= bool(say) and say != "(no reply)"
        print(f"  /radio -> chat   : {c.command('/radio')!r}")
        time.sleep(0.3)
        rad = [e.get("line") for e in c.events() if e.get("t") == "radio"]
        print(f"  radio lines      : {len(rad)}")
        ok &= len(rad) >= 1
        r = c.feed_pyqt6(os.path.join(_HERE, "Phaleron/APISniff/APISniffCL.py"))
        print(f"  feed_pyqt6 -> ok : {r.get('ok')}  module={r.get('module')}  "
              f"pgui_added={r.get('pgui_added')}")
        ok &= bool(r.get("ok")) and "face_classes" in r
    finally:
        c.close()
    print("  ROUNDTRIP:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--roundtrip":
        sys.exit(_roundtrip())
    # console_link.py <face.py>  -> run an update session, print the result
    if len(sys.argv) > 1:
        print(json.dumps(run_update_session(sys.argv[1]), indent=2))
    else:
        print(__doc__)
