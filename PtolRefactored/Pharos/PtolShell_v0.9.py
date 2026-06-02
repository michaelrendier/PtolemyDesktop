#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

# PtolShell — QTermWidget-backed shell with MetaPrompt mode routing
#
# MetaPrompt modes (commit on Enter):
#   (none) → Ptolemy C/O   — BBS-style buffered conversation, /slash commands
#                             Own CyclicContextBuffer. Stateful. Not a pty.
#                             Designed like old ATA BBS chat: /who /say /history etc.
#                             color: ROYAL_BLUE
#   >>>    → Python3 REPL  — python3 pty               — color: GREEN
#   $      → System C/O   — bash pty                  — color: YELLOW
#   #      → Root C/O     — bash pty (root)            — color: RED
#   @Name  → Face C/O     — Face speaks in shell       — color: Face color
#            e.g. @Archimedes: index rebuild complete
#            Face → Face: @Callimachus→@Archimedes: index ready
#
# QTermWidget owns ALL display, pty, ANSI, interactive programs.
# Mode detector intercepts only the input bar — QTermWidget is never replaced.
#
# Faces are shell users. Daemons POST at boot (see FaceIdentity.py).
# Ptolemy buffer is its own conversation space — not piped to QTermWidget.

import os

from PyQt6.QtCore    import Qt, pyqtSignal, QProcess, QThread
from PyQt6.QtGui     import QFont, QColor, QKeyEvent
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLineEdit, QLabel, QSizePolicy)

try:
    import QTermWidget
    _HAS_QTERM = True
except ImportError:
    _HAS_QTERM = False

try:
    from Pharos.FaceIdentity import get_face, ShellPrompt, DaemonIdentity
    from Pharos.PtolColor import PtolColor, ShellModeColor
    _HAS_FACE_IDENTITY = True
except ImportError:
    _HAS_FACE_IDENTITY = False

# ── Mode definitions ──────────────────────────────────────────────────────────
# prefix : (label_text, label_color, pty_program, pty_args)
# '@' is the Face mode prefix — resolved dynamically per Face name.
_MODES = {
    ''   : ('Ptolemy', '#1a2a6c', None,        None),
    '>>>': ('Python3', '#00ff66', 'python3',  ['-i']),
    '$'  : ('Shell',   '#ffcc00', '/bin/bash', []),
    '#'  : ('Root',    '#ff4444', '/bin/bash', ['--login']),
}
_DEFAULT_MODE = ''
_FACE_PREFIX  = '@'   # @Archimedes: message  or  @Callimachus→@Archimedes: msg


class _AinurThread(QThread):
    """Run Ainur.stream() off the UI thread. Emits chunk by chunk."""
    chunk   = pyqtSignal(str)
    done    = pyqtSignal()
    error   = pyqtSignal(str)

    def __init__(self, ainur, message, parent=None):
        super().__init__(parent)
        self._ainur   = ainur
        self._message = message

    def run(self):
        try:
            for chunk in self._ainur.stream(self._message):
                self.chunk.emit(chunk)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.done.emit()


class _GeminiThread(QThread):
    """Run Gemini streaming generation off the UI thread."""
    chunk = pyqtSignal(str)
    done  = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, prompt, api_key, parent=None):
        super().__init__(parent)
        self._prompt  = prompt
        self._api_key = api_key

    def run(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            model    = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(self._prompt, stream=True)
            for chunk in response:
                text = getattr(chunk, 'text', None)
                if text:
                    self.chunk.emit(text)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.done.emit()


class _SMNNIPThread(QThread):
    """Run SMNNIP L3 autoregressive generation off the UI thread."""
    chunk = pyqtSignal(str)
    done  = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, brain, command, parent=None):
        super().__init__(parent)
        self._brain   = brain
        self._command = command

    def run(self):
        try:
            for ch in self._brain.generate(self._command):
                self.chunk.emit(ch)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.done.emit()


class PtolShell(QWidget):
    """
    In-scene Ptolemy shell.
    Input bar at bottom detects MetaPrompt prefix on Enter.
    QTermWidget above handles all pty I/O and display.
    Falls back to QProcess widget if QTermWidget not installed.
    """

    mode_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 360)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet('background: #050510;')
        self._mode = _DEFAULT_MODE

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Terminal area ─────────────────────────────────────────────────────
        if _HAS_QTERM:
            self._term = QTermWidget.QTermWidget()
            self._term.setColorScheme('Linux')
            self._term.setScrollBarPosition(QTermWidget.QTermWidget.ScrollBarRight)
            self._term.setTerminalFont(QFont('Monospace', 10))
            self._term.startShellProgram()
            self._term.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            layout.addWidget(self._term)
        else:
            self._term = _FallbackTerm(self)
            layout.addWidget(self._term)

        # ── Mode indicator + input bar ────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setContentsMargins(2, 2, 2, 2)
        bar.setSpacing(4)

        self._mode_label = QLabel('Ptolemy')
        self._mode_label.setFixedWidth(62)
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mode_label.setFont(QFont('Monospace', 9))

        self._input = _ModeInput(self)
        self._input.setFont(QFont('Monospace', 10))
        self._input.setPlaceholderText('MetaPrompt  >>>  $  #  @FaceName')
        self._input.mode_commit.connect(self._on_commit)

        bar.addWidget(self._mode_label)
        bar.addWidget(self._input)

        bar_widget = QWidget()
        bar_widget.setLayout(bar)
        bar_widget.setStyleSheet('background: #0a0a12;')
        bar_widget.setFixedHeight(32)
        layout.addWidget(bar_widget)

        self._apply_mode_color(_DEFAULT_MODE)

    def showEvent(self, event):
        super().showEvent(event)
        self._input.setFocus()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._input.setFocus()

    # ── Mode commit ───────────────────────────────────────────────────────────

    def _on_commit(self, text: str):
        stripped = text.strip()

        # ── Face mode: @FaceName: message  or  @Sender→@Recipient: message ──
        if stripped.startswith(_FACE_PREFIX) and _HAS_FACE_IDENTITY:
            self._dispatch_face_message(stripped)
            self._input.clear()
            return

        new_mode = _DEFAULT_MODE
        command  = stripped
        for prefix in ('>>>', '$', '#'):
            if stripped.startswith(prefix):
                new_mode = prefix
                command  = stripped[len(prefix):].strip()
                break
        if new_mode != self._mode:
            self._mode = new_mode
            self._apply_mode_color(new_mode)
            self.mode_changed.emit(new_mode)
            if new_mode != _DEFAULT_MODE:
                self._start_pty(new_mode)
            if not command:
                self._input.clear()
                return
        self._dispatch(new_mode, command)
        self._input.clear()

    def _dispatch_face_message(self, text: str):
        """
        Parse and emit a Face shell message.
        Formats:
          @Archimedes: index rebuild complete
          @Callimachus→@Archimedes: index ready
        """
        body = text[1:]  # strip leading @
        # Face → Face?
        if '→' in body or '->' in body:
            sep = '→' if '→' in body else '->'
            parts = body.split(sep, 1)
            sender_raw   = parts[0].strip().lstrip('@')
            rest         = parts[1].strip().lstrip('@') if len(parts) > 1 else ''
            colon_idx    = rest.find(':')
            recipient_raw = rest[:colon_idx].strip() if colon_idx >= 0 else rest.strip()
            message       = rest[colon_idx+1:].strip() if colon_idx >= 0 else ''
            out = ShellPrompt.face_to_face(sender_raw, recipient_raw, message)
            # color mode label with sender's color
            face = get_face(sender_raw)
            label_color = face.color if face else '#c9a227'
            self._set_transient_label(face.display if face else sender_raw, label_color)
        else:
            colon_idx  = body.find(':')
            face_name  = body[:colon_idx].strip().lstrip('@') if colon_idx >= 0 else body.strip().lstrip('@')
            message    = body[colon_idx+1:].strip() if colon_idx >= 0 else ''
            out        = ShellPrompt.face_say(face_name, message)
            face = get_face(face_name)
            label_color = face.color if face else '#c9a227'
            self._set_transient_label(face.display if face else face_name, label_color)

        if _HAS_QTERM:
            self._term.sendText(out + '\n')
        else:
            self._term.write(out + '\n')

    def _set_transient_label(self, name: str, color: str):
        """Briefly show Face name as mode label (does not persist)."""
        self._mode_label.setText(name[:10])
        self._mode_label.setStyleSheet(
            f'color: {color}; font-weight: bold; background: #0a0a12; border: 1px solid {color};')

    def _handle_input(self):
        """Process input bar submission — route to mode dispatch or ptolemy command."""
        stripped = self._input.text().strip()
        if not stripped:
            return
        new_mode = _DEFAULT_MODE
        command  = stripped
        for prefix in _MODES:
            if stripped.startswith(prefix + ' ') or stripped == prefix:
                new_mode = prefix
                command  = stripped[len(prefix):].strip()
                break
        if new_mode != self._mode:
            self._mode = new_mode
            self._apply_mode_color(new_mode)
            self.mode_changed.emit(new_mode)
            if new_mode != _DEFAULT_MODE:
                self._start_pty(new_mode)
            if not command:
                self._input.clear()
                return
        self._dispatch(new_mode, command)
        self._input.clear()

    def _dispatch(self, mode: str, command: str):
        if not command:
            return
        if mode == _DEFAULT_MODE:
            self._ptolemy_command(command)
        else:
            if _HAS_QTERM:
                self._term.sendText(command + '\n')
            else:
                self._term.send(command)

    def _start_pty(self, mode: str):
        if not _HAS_QTERM:
            return
        _, _, program, args = _MODES[mode]
        if program:
            self._term.setShellProgram(program)
            self._term.setArgs(args or [])
            self._term.startShellProgram()

    def _ptolemy_command(self, command: str):
        """
        Dispatch Ptolemy-mode commands.
        Supported:
            face <name>            — switch prompt identity / open face subshell
            face <name> <message>  — send message to face
            bus                    — show PtolBus queue/channel status
            faces                  — list registered faces
            help                   — list commands
        """
        parts   = command.strip().split(None, 2)
        cmd     = parts[0].lower() if parts else ''
        ptol    = getattr(self, 'Ptolemy', None) or (
                      self.parent() if hasattr(self, 'parent') else None)

        def _write(text, color='#00ccff'):
            if _HAS_QTERM:
                self._term.sendText(f'# {text}\n')
            else:
                self._term.write(text + '\n', color)

        if cmd == 'face':
            if len(parts) < 2:
                _write('Usage: face <name> [message]', '#ff9900')
                return
            face_name = parts[1].lower()
            message   = parts[2] if len(parts) > 2 else None
            # Try to get face identity
            try:
                from Pharos.FaceIdentity import get_face
                face_obj = get_face(face_name)
                color = face_obj.color if face_obj else '#c9a227'
                label = face_obj.display if face_obj else face_name.title()
            except Exception:
                color, label = '#c9a227', face_name.title()
            if message:
                # Face-to-face message via PtolShell dispatch
                self._dispatch_face_message(f'{face_name}:{message}')
            else:
                # Switch prompt to face subshell identity
                self._set_transient_label(label, color)
                _write(f'Entering {label} subshell. Type "exit" to return.', color)
                # If face is archimedes, launch math shell
                if face_name == 'archimedes':
                    try:
                        from Archimedes.Maths.ArchimedesShell import ArchimedesShell
                        bus = getattr(ptol, 'bus', None) if ptol else None
                        arch_shell = ArchimedesShell(output_fn=_write, bus=bus)
                        _write(arch_shell._ns['help_math'](), '#aaaaaa')
                        # Store on self for ongoing math eval
                        self._arch_shell = arch_shell
                    except Exception as ex:
                        _write(f'Archimedes: {ex}', '#ff5555')
                # Emit on bus if available
                if ptol and hasattr(ptol, 'msg_bus'):
                    try:
                        from Pharos.PtolBus import BusMessage, CH_FACE_EVENT, Priority
                        ptol.msg_bus.publish(BusMessage(
                            CH_FACE_EVENT,
                            {'action': 'subshell', 'face': face_name},
                            Priority.T1, sender='PtolShell'))
                    except Exception:
                        pass

        elif cmd in ('/math', 'math'):
            # Enter Archimedes SymPy subshell
            expr = ' '.join(parts[1:]) if len(parts) > 1 else None
            try:
                from Archimedes.Maths.ArchimedesShell import ArchimedesShell
                bus = getattr(ptol, 'bus', None) if ptol else None
                arch = ArchimedesShell(output_fn=_write, bus=bus)
                if expr:
                    arch.eval(expr)
                else:
                    _write('Archimedes /math mode. Type /math <expr> or face archimedes <expr>', '#00ccff')
                    _write(arch._ns['help_math'](), '#aaaaaa')
            except Exception as ex:
                _write(f'Archimedes shell error: {ex}', '#ff5555')

        elif cmd == 'faces':
            if ptol and hasattr(ptol, 'bus') and hasattr(ptol.bus, '_registry'):
                reg = ptol.bus._registry
                if reg:
                    for fid, rec in reg.items():
                        _write(f'  {fid:30s} [{rec["state"]}]', '#aaffcc')
                else:
                    _write('No faces registered.', '#888888')
            else:
                _write('Bus not available.', '#ff5555')

        elif cmd == 'bus':
            b = getattr(ptol, 'msg_bus', None)
            if b:
                try:
                    _write(f'PtolBus  channels={len(b.channels())}  queue={b.queue_depth()}', '#00ccff')
                    for ch in b.channels():
                        _write(f'  {ch:30s}  subscribers={b.subscriber_count(ch)}', '#aaaaaa')
                except Exception as ex:
                    _write(f'Bus status error: {ex}', '#ff5555')
            else:
                _write('msg_bus not available.', '#ff5555')

        elif cmd == '/claude':
            prompt = command[len('/claude'):].strip()
            if not prompt:
                _write('Usage: /claude <prompt>', '#ff9900')
                return
            self._ainur_respond(prompt, _write)

        elif cmd == '/gemini':
            prompt = command[len('/gemini'):].strip()
            if not prompt:
                _write('Usage: /gemini <prompt>', '#ff9900')
                return
            self._gemini_respond(prompt, _write)

        elif cmd in ('/datainput', 'datainput'):
            # Extract path from command if present, else prompt via dialog
            tail_parts = [p for p in parts[1:] if not p.startswith('-')]
            corpus_path = ' '.join(tail_parts) if tail_parts else None
            if not corpus_path:
                try:
                    from PyQt6.QtWidgets import QFileDialog
                    corpus_path = QFileDialog.getExistingDirectory(
                        self, 'Select Corpus Directory',
                        os.path.expanduser('~'))
                    if not corpus_path:
                        _write('[DataInput] cancelled.', '#888888')
                        return
                except Exception:
                    _write('[DataInput] Usage: /DataInput /path/to/corpus', '#ff9900')
                    return
            _write(f'[DataInput] ingesting: {corpus_path}', '#9988ff')
            try:
                from Philadelphos.data_input import handle_data_input
                import threading
                flags = [p for p in (parts[1:] if len(parts) > 1 else [])
                         if p.startswith('-')]
                dm = '--dm' in [f.lower() for f in flags]

                def _run():
                    handle_data_input(corpus_path=corpus_path,
                                      diagnostic_mode=dm,
                                      ainur_instance=getattr(self, '_ainur', None))

                t = threading.Thread(target=_run, daemon=True)
                t.start()
                _write('[DataInput] tower running in background…', '#9988ff')
                _write('When complete: weights saved to Philadelphos/weights/', '#888888')
            except Exception as ex:
                _write(f'[DataInput] error: {ex}', '#ff5555')

        elif cmd in ('/outputtuning', 'outputtuning'):
            _write('[OutputTuning] starting shell…', '#9988ff')
            try:
                from Philadelphos.output_tuner import parse_and_run as ot_run
                ot_run(command)
            except Exception as ex:
                _write(f'[OutputTuning] error: {ex}', '#ff5555')

        elif cmd == 'help' or cmd == '?':
            _write('Ptolemy commands:', '#00ccff')
            _write('  face <name> [message]  — open face subshell / send message')
            _write('  faces                  — list active faces')
            _write('  bus                    — bus channel status')
            _write('  /DataInput [--DM]      — ingest corpus, train SMNNIP tower')
            _write('  /OutputTuning [flags]  — diagnostic output tuner shell')
            _write('  /claude <prompt>       — [user] ask Claude directly')
            _write('  /gemini <prompt>       — [user] ask Gemini directly')
            _write('  help                   — this list')
            _write('  (anything else)        — Ptolemy responds via SMNNIP 𝕆 layer')

        else:
            # Primary: Ptolemy responds via SMNNIP tower (backward to Reals)
            self._ptolemy_respond(command, _write)

    def _ptolemy_respond(self, command: str, write_fn):
        """
        Ptolemy's primary response path.
        Loads SMNNIP weights, runs L3 autoregressive generation (𝕆 layer),
        annotates with Noether current, filters through PtolemyTongue.
        Falls back with instructions if weights not yet trained.
        """
        # Lazy init SMNNIP brain
        if not hasattr(self, '_brain') or self._brain is None:
            try:
                from Pharos.PtolBrain import PtolBrain
                self._brain = PtolBrain()
                write_fn(self._brain.status(), '#00ccff')
            except FileNotFoundError as exc:
                write_fn(str(exc), '#ff9900')
                write_fn('Run /DataInput to train the tower first.', '#ff9900')
                return
            except Exception as exc:
                write_fn(f'[Ptolemy] brain error: {exc}', '#ff5555')
                self._brain = None
                return

        # Lazy PtolemyTongue
        if not hasattr(self, '_tongue') or self._tongue is None:
            try:
                from Philadelphos.ptolemy_tongue import PtolemyTongue
                self._tongue = PtolemyTongue()
            except Exception:
                self._tongue = None

        write_fn('Ptolemy ›', '#00ccff')
        self._ptol_buf = []

        def _flush(text: str):
            t = text.strip()
            if not t:
                return
            if self._tongue is not None:
                t = self._tongue.filter(t)
            write_fn(t, '#aaffcc')

        def on_chunk(ch):
            self._ptol_buf.append(ch)
            joined = ''.join(self._ptol_buf)
            if any(joined.endswith(p) for p in ('.', '!', '?', '\n')) or len(joined) > 120:
                _flush(joined)
                self._ptol_buf = []

        def on_done():
            _flush(''.join(self._ptol_buf))
            self._ptol_buf = []
            self._ptol_thread = None

        def on_error(msg):
            write_fn(f'[Ptolemy] {msg}', '#ff5555')
            self._ptol_thread = None

        thread = _SMNNIPThread(self._brain, command, parent=self)
        thread.chunk.connect(on_chunk, Qt.ConnectionType.QueuedConnection)
        thread.done.connect(on_done,   Qt.ConnectionType.QueuedConnection)
        thread.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        self._ptol_thread = thread
        thread.start()

    def _ainur_respond(self, command: str, write_fn):
        """
        Send a free-form command to Ainur (Claude API).
        Runs stream() in a QThread; chunks are filtered through PtolemyTongue
        and written to the terminal as they arrive.
        Lazy-initialises self._ainur and self._tongue on first call.
        """
        if not hasattr(self, '_ainur') or self._ainur is None:
            try:
                from Philadelphos.Ainur.ainur import Ainur
                self._ainur = Ainur()
                if not self._ainur.status.ready:
                    write_fn(f'[Ainur] not ready: {self._ainur.status.error}', '#ff5555')
                    return
                write_fn(self._ainur.status.header(), '#9988ff')
            except Exception as exc:
                write_fn(f'[Ainur] init error: {exc}', '#ff5555')
                self._ainur = None
                return

        # Lazy PtolemyTongue init — last filter before display
        if not hasattr(self, '_tongue') or self._tongue is None:
            try:
                from Philadelphos.ptolemy_tongue import PtolemyTongue
                self._tongue = PtolemyTongue()
            except Exception:
                self._tongue = None

        write_fn('Ainur ›', '#9988ff')

        # Running buffer — flush at sentence boundary or 120 chars
        self._ainur_buf = []

        def _flush(text: str):
            t = text.strip()
            if not t:
                return
            if self._tongue is not None:
                t = self._tongue.filter(t)
            write_fn(t, '#ccbbff')

        def on_chunk(chunk):
            self._ainur_buf.append(chunk)
            joined = ''.join(self._ainur_buf)
            if any(joined.endswith(p) for p in ('.', '!', '?', '\n')) or len(joined) > 120:
                _flush(joined)
                self._ainur_buf = []

        def on_done():
            _flush(''.join(self._ainur_buf))
            self._ainur_buf = []
            self._ainur_thread = None

        def on_error(msg):
            write_fn(f'[Ainur] stream error: {msg}', '#ff5555')
            self._ainur_thread = None

        thread = _AinurThread(self._ainur, command, parent=self)
        thread.chunk.connect(on_chunk, Qt.ConnectionType.QueuedConnection)
        thread.done.connect(on_done,   Qt.ConnectionType.QueuedConnection)
        thread.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        self._ainur_thread = thread   # keep alive until done
        thread.start()

    def _gemini_respond(self, prompt: str, write_fn):
        """
        Send prompt to Gemini (user-level command).
        Requires GEMINI_API_KEY in environment.
        Chunks filtered through PtolemyTongue before display.
        """
        import os
        key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if not key:
            write_fn('[Gemini] GEMINI_API_KEY not set — Gemini offline.', '#ff5555')
            write_fn('[Gemini] Set env var GEMINI_API_KEY to enable.', '#ff9900')
            return

        try:
            import google.generativeai
        except ImportError:
            write_fn('[Gemini] google-generativeai not installed.', '#ff5555')
            write_fn('[Gemini] Run: pip3 install google-generativeai', '#ff9900')
            return

        if not hasattr(self, '_tongue') or self._tongue is None:
            try:
                from Philadelphos.ptolemy_tongue import PtolemyTongue
                self._tongue = PtolemyTongue()
            except Exception:
                self._tongue = None

        write_fn('Gemini ›', '#4db8ff')
        self._gemini_buf = []

        def _flush(text: str):
            t = text.strip()
            if not t:
                return
            if self._tongue is not None:
                t = self._tongue.filter(t)
            write_fn(t, '#aaddff')

        def on_chunk(chunk):
            self._gemini_buf.append(chunk)
            joined = ''.join(self._gemini_buf)
            if any(joined.endswith(p) for p in ('.', '!', '?', '\n')) or len(joined) > 120:
                _flush(joined)
                self._gemini_buf = []

        def on_done():
            _flush(''.join(self._gemini_buf))
            self._gemini_buf = []
            self._gemini_thread = None

        def on_error(msg):
            write_fn(f'[Gemini] error: {msg}', '#ff5555')
            self._gemini_thread = None

        thread = _GeminiThread(prompt, key, parent=self)
        thread.chunk.connect(on_chunk, Qt.ConnectionType.QueuedConnection)
        thread.done.connect(on_done,   Qt.ConnectionType.QueuedConnection)
        thread.error.connect(on_error, Qt.ConnectionType.QueuedConnection)
        self._gemini_thread = thread
        thread.start()

    def _apply_mode_color(self, mode: str):
        label, color, _, _ = _MODES.get(mode, _MODES[_DEFAULT_MODE])
        self._mode_label.setText(label)
        self._mode_label.setStyleSheet(
            f'color: {color}; font-weight: bold; background: #0a0a12; border: 1px solid {color};')
        self._input.setStyleSheet(
            f'background: #050510; color: {color}; border: 1px solid #333;')

    def set_focused(self, focused: bool):
        self.setWindowOpacity(1.0 if focused else 0.30)


# ── MetaPrompt input widget ───────────────────────────────────────────────────

class _ModeInput(QLineEdit):
    """Emits mode_commit on Enter. Does not forward keys to QTermWidget."""
    mode_commit = pyqtSignal(str)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.mode_commit.emit(self.text())
        else:
            super().keyPressEvent(event)


# ── Fallback terminal (QTermWidget not installed) ─────────────────────────────

class _FallbackTerm(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QTextEdit
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._out = QTextEdit()
        self._out.setReadOnly(True)
        self._out.setFont(QFont('Monospace', 10))
        self._out.setStyleSheet('background: #050510; color: #aaffcc; border: none;')
        layout.addWidget(self._out)
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self.write('[QTermWidget not found — install SIP build for full pty]\n', '#ff8800')

    def send(self, command: str):
        self._proc.start('/bin/bash', ['-c', command])

    def write(self, text: str, color: str = '#aaffcc'):
        self._out.setTextColor(QColor(color))
        self._out.insertPlainText(text)
        self._out.ensureCursorVisible()

    def _on_stdout(self):
        self.write(bytes(self._proc.readAllStandardOutput()).decode('utf-8', errors='replace'))

    def _on_stderr(self):
        self.write(bytes(self._proc.readAllStandardError()).decode('utf-8', errors='replace'), '#ff5555')
