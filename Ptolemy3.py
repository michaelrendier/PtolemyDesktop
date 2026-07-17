#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Ptolemy3.py — Integration Kernel v3.0
======================================
Architecture:
    Ptolemy   — QMainWindow shell, singletons, scene substrate
    PtolBus   — Face registry, thread lifecycle, suspend/resume
    PGui      — PWindow chrome, QGraphicsProxyWidget management (Pharos/PGui.py)
    PtolVispy — VisPy GL canvas helper (defined below)

    All networking and device interfacing lives in Tesla:
        Tesla.HolePunch  — UDP NAT traversal, rendezvous relay, GPS data channel
        Tesla.KVM        — Fake KVM: mouse/kb structs over punched UDP socket
        Tesla.Sockets    — Base UDP/TCP layer
        Tesla.KVMServer  — Remote receiver (python-xlib / uinput application)

Render strategy:
    QGraphicsScene   — primary desktop, all PWindows live here (~10^3 items)
    VisPy/OpenGL     — injected as QGraphicsProxyWidget for data-dense faces
                       (Alexandria, Archimedes spectrograph, Noether plots)
                       GPU-side VBO rendering: 10^6+ primitives at 60fps
                       QGraphicsScene handles chrome only; VisPy handles pixels

Threading contract:
    Each Face launched through PtolBus gets:
        face._ptol_thread  — QThread driving the face's work loop
        face._ptol_timers  — list of QTimers owned by the face
    PtolBus.suspend(id)  → thread.quit() + timer.stop() for each
    PtolBus.resume(id)   → thread.start() + timer.start() for each
    PtolBus.terminate(id)→ suspend + thread.wait() + del
    Faces not visible are NOT processing. No exceptions.
"""

# ── Standard library ──────────────────────────────────────────────────────────
import sys
import os
import time
import inspect
import importlib
import struct
from subprocess import Popen, PIPE

# ── PyQt6 ─────────────────────────────────────────────────────────────────────
from PyQt6.QtCore    import Qt, QTimer, QThread, pyqtSignal, QObject, QRect, QRectF, QPointF, QEvent
from PyQt6.QtGui     import QBrush, QColor, QPen, QFont, QIcon, QPixmap
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGraphicsScene,
                              QGraphicsView, QGraphicsProxyWidget, QGraphicsItemGroup,
                              QGraphicsItem, QGraphicsRectItem,
                              QFrame, QGridLayout)

# ── Ptolemy core modules ───────────────────────────────────────────────────────
from Pharos.PtolBus            import (PtolBus as _PharosPtolBus, BusMessage, Priority,
                                        CH_PROMPT, CH_LOG, CH_BLOCKCHAIN)
from Pharos.PtolRegistry       import FaceRegistry
from urllib.request            import build_opener

try:
    from Pharos.PtolShell      import PtolShell
except Exception as _e:
    PtolShell = None
    print(f'[Pharos] PtolShell: {_e}')

try:
    from Pharos.PGui           import PWindow
except Exception as _e:
    PWindow = None
    print(f'[Pharos] PGui/PWindow: {_e}')

try:
    from Philadelphos.monad    import Monad as _Monad
except Exception as _e:
    _Monad = None
    print(f'[Philadelphos] Monad: {_e}')

# DEFERRED — may fail, reported to shell, never kills desktop
try:
    from Callimachus.v09 import Callimachus as _CallimachusV09
except Exception as _e:
    _CallimachusV09 = None
    print(f'[Callimachus] v09: {_e}')

try:
    from Pharos.Dialogs        import Dialogs
except Exception as _e:
    Dialogs = None
    print(f'[Pharos] Dialogs: {_e}')

try:
    from Pharos.SystemTrayIcon import SystemTrayIcon
except Exception as _e:
    SystemTrayIcon = None
    print(f'[Pharos] SystemTrayIcon: {_e}')

try:
    from Pharos.UtilityFunctions import cmdline
except Exception as _e:
    cmdline = None
    print(f'[Pharos] UtilityFunctions: {_e}')

try:
    from Pharos.Menu           import Menu
except Exception as _e:
    Menu = None
    print(f'[Pharos] Menu: {_e}')

try:
    from Pharos.Interface      import User   # NOTE: pulls OpenGL.GLUT
except Exception as _e:
    User = None
    print(f'[Pharos] Interface (OpenGL): {_e}')

# ── Tesla — all interfacing ────────────────────────────────────────────────────
try:
    from Tesla.HolePunch       import HolePunch
except Exception as _e:
    HolePunch = None
    print(f'[Tesla] HolePunch: {_e}')

try:
    from Tesla.KVM             import KVMClient
except Exception as _e:
    KVMClient = None
    print(f'[Tesla] KVM: {_e}')



# ══════════════════════════════════════════════════════════════════════════════
#  MonadLearner — serialised background β-field writer
# ══════════════════════════════════════════════════════════════════════════════

import queue as _queue
import threading as _threading

class _MonadLearner(_threading.Thread):
    """
    Single persistent daemon thread. Serialises all monad.learn() calls so
    the β field never sees concurrent writes from the Qt UI thread and the
    CH_LEARN subscriber simultaneously.

    β saturation cache: zeros whose |β| > _BETA_SAT skip β deepening on
    subsequent learn() calls — avoids redundant computation while still
    updating A-connections.  O(1) set lookup.

    Usage:
        learner = _MonadLearner(monad)
        learner.start()
        learner.enqueue("some text")
        learner.shutdown()   # sends None sentinel
    """
    _BETA_SAT = 7.552   # abs(L_GROUND)*4 ≈ 1.888*4

    def __init__(self, monad):
        """
        :param monad: The shared :class:`Philadelphos.monad.Monad` instance.
        """
        super().__init__(daemon=True, name='MonadLearner')
        self._monad      = monad
        self._queue      = _queue.Queue()
        self._saturated  = set()

    def enqueue(self, text: str):
        """Queue *text* for background learning; ignores blank strings.

        :param text: Raw text to pass to :meth:`Monad.learn`.
        :type text: str
        """
        if text and text.strip():
            self._queue.put(text)

    def shutdown(self):
        """Signal the thread to exit cleanly by enqueuing the ``None`` sentinel."""
        self._queue.put(None)

    def run(self):
        """Drain the queue, calling ``monad.learn(text)`` for each item."""
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                self._monad.learn(text)
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  PtolVispy — VisPy GL canvas integration helper
# ══════════════════════════════════════════════════════════════════════════════

class PtolVispy:
    """
    Mixin/helper for faces that use VisPy for GPU-accelerated rendering.

    Why VisPy for data-dense faces:
        QGraphicsScene handles ~10^3 items before frame rate degrades.
        VisPy renders directly to OpenGL via VBO — 10^6+ primitives at 60fps.
        Working proof: working/vispy-test-2.py renders 320,000 vertices
        (16×20 signals × 1000 samples) in real time with GLSL clipping.

    Architecture:
        VisPy canvas → renders data/geometry to OpenGL surface
        canvas.native → the underlying Qt widget
        QGraphicsProxyWidget(canvas.native) → sits on QGraphicsScene
        PWindow wraps the proxy → chrome, suspend, close

    Faces that benefit: Alexandria (Earth/Core), Archimedes (spectrograph,
    Noether current plots), Mouseion (GLViewer), any future graph-dense UI.

    Usage in a Face:
        class AlexandriaGl(QWidget, PtolVispy):
            def __init__(self, parent):
                super().__init__(parent)
                self.canvas = self.make_vispy_canvas(size=(800, 600))
                layout = QVBoxLayout(self)
                layout.addWidget(self.canvas.native)
                # Implement on_draw, on_resize on self.canvas

    Or full-GL face launched via bus:
        pwin = ptolemy.bus.launch(AlexandriaGl, use_vispy=True)
        # bus.launch with use_vispy=True proxies canvas.native directly
    """

    @staticmethod
    def make_vispy_canvas(size=(800, 600), title='', keys='interactive'):
        """Return a VisPy canvas configured for Qt5 backend embedding."""
        try:
            import vispy
            vispy.use('PyQt6')
            from vispy import app
            canvas = app.Canvas(size=size, title=title, keys=keys, show=False)
            return canvas
        except ImportError:
            raise RuntimeError(
                'VisPy not installed. '
                'pip install vispy --break-system-packages')

    @staticmethod
    def add_vispy_to_scene(scene, canvas, x=0, y=0):
        """
        Embed a VisPy canvas.native into a QGraphicsScene as a proxy widget.
        Returns the QGraphicsProxyWidget.
        """
        proxy = scene.addWidget(canvas.native)
        proxy.setPos(x, y)
        return proxy


# ══════════════════════════════════════════════════════════════════════════════
#  Desktop helper items — sidebar, magic strip, drag overlays
# ══════════════════════════════════════════════════════════════════════════════

class _PanelTimerFilter(QObject):
    """Resets a single-shot hide-timer whenever the panel sees mouse activity."""

    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self._timer = timer

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.MouseMove,
                             QEvent.Type.MouseButtonPress,
                             QEvent.Type.HoverMove,
                             QEvent.Type.Enter):
            self._timer.start()
        return False


class _MagicStrip(QGraphicsRectItem):
    """5 px invisible vertical strip anchored to the left edge of the scene.
    Hovering or pressing it calls show_fn to reveal the sidebar."""

    def __init__(self, scene_h, show_fn):
        super().__init__(0, 0, 5, scene_h)
        self._show_fn = show_fn
        self.setBrush(QBrush(QColor(0, 0, 0, 1)))
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setAcceptHoverEvents(True)
        self.setZValue(200)

    def hoverEnterEvent(self, event):
        self._show_fn()
        super().hoverEnterEvent(event)

    def mousePressEvent(self, event):
        self._show_fn()
        super().mousePressEvent(event)


class _DragOverlay(QGraphicsItem):
    """Transparent grab-strip that moves a target QGraphicsItem when dragged.

    Positioned over the top edge of the target; the target and overlay move
    together.  The overlay is NOT a child of the target so it can have a
    Z-value above the proxy widget that would otherwise eat mouse events.
    """

    def __init__(self, target, w, h=24):
        super().__init__()
        self._target      = target
        self._w           = float(w)
        self._h           = float(h)
        self._dragging    = False
        self._press_scene = QPointF()
        self._press_pos   = QPointF()
        self.setAcceptHoverEvents(True)
        self.setZValue(2)

    def boundingRect(self):
        return QRectF(0, 0, self._w, self._h)

    def paint(self, painter, option, widget=None):
        pass

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging    = True
            self._press_scene = event.scenePos()
            self._press_pos   = self._target.pos()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            delta   = event.scenePos() - self._press_scene
            new_pos = self._press_pos + delta
            self._target.setPos(new_pos)
            self.setPos(new_pos)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


# ══════════════════════════════════════════════════════════════════════════════
#  Ptolemy — Main window shell (v3.0)
# ══════════════════════════════════════════════════════════════════════════════

class Ptolemy(QMainWindow):
    """
    Integration kernel. Owns the scene, singletons, and the bus.
    Does not own faces — the bus does.
    Does not drive face logic — faces drive themselves.

    Faces launch via:
        self.bus.launch(FaceClass)             # inline, integrated
        self.bus.launch_subprocess(path)       # legacy subprocess
        self.bus.import_face(module, cls)      # dynamic import then launch
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Paths ─────────────────────────────────────────────────────────────
        # TODO:SETTINGS — hardcoded path, use PTOL_ROOT
        # PTOL_ROOT — derived from kernel location, not hardcoded
        self.homeDir   = os.path.dirname(os.path.abspath(__file__)) + os.sep
        self.mediaDir  = os.path.join(self.homeDir, 'media', '')
        self.imgDir    = os.path.join(self.homeDir, 'images', '')
        self.pharosImg = os.path.join(self.imgDir, 'Pharos', '')
        self.screen    = QApplication.primaryScreen().geometry()

        # ── Scene / View ──────────────────────────────────────────────────────
        self._setup_scene()

        # ── Identity ──────────────────────────────────────────────────────────
        self.name     = 'Πτολεμαῖος Φιλάδελφος'
        self.user     = Popen('whoami',  stdout=PIPE, shell=True).communicate()[0][:-1]
        self.platform = Popen('uname -o',stdout=PIPE, shell=True).communicate()[0][:-1]
        self.nodename = Popen('uname -n',stdout=PIPE, shell=True).communicate()[0][:-1]

        # ── Stylesheet ────────────────────────────────────────────────────────
        self.stylesheet = self._build_stylesheet()

        # ── Core singletons ───────────────────────────────────────────────────
        if _CallimachusV09:
            _db_path = os.path.join(self.homeDir, 'Callimachus', 'data', 'ptolemy.db')
            _hw_root = os.path.join(self.homeDir, 'Callimachus', 'data', 'hyperwebster')
            try:
                self.db = _CallimachusV09(_db_path, _hw_root)
            except Exception as _e:
                self.db = None
                print(f'[Callimachus] init: {_e}')
        else:
            self.db = None
        self.dialogs = Dialogs(parent=self)  if Dialogs  else None
        self.opener   = build_opener()
        self.opener.addheaders = [
            ('User-agent',           'Mozilla/5.0 (X11; Linux x86_64)'),
            ('Accept',               'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language',      'en-US,en;q=0.9'),
            ('Upgrade-Insecure-Requests', '1'),
        ]

        # ── Integration bus ───────────────────────────────────────────────────
        # self.bus       = FaceRegistry (launch/suspend/terminate faces)
        # self.msg_bus   = PtolBus message bus (pub/sub channels, T0/T1 priority)
        self.bus = FaceRegistry(self)
        self.msg_bus = _PharosPtolBus(ptolemy=self, parent=self)
        self.msg_bus.start()
        # Wire luthspell to message bus
        try:
            from Pharos.luthspell import LuthSpell
            self.luthspell = LuthSpell(bus=self.msg_bus)
            self.luthspell.wire()
        except Exception as e:
            self.luthspell = None
            print(f"[PtolBus] LuthSpell wire failed: {e}")
        # Tuning Display (output stream monitor)
        try:
            from Pharos.TuningDisplay import TuningDisplay
            self.tuning_display = TuningDisplay(bus=self.msg_bus, parent=None)
            # Don't show on startup — launch via tray or shortcut
        except Exception as e:
            self.tuning_display = None
            print(f"[TuningDisplay] init failed: {e}")
        # Aule forge queue
        try:
            from Aule.forge_queue import ForgeQueue
            self.forge_queue = ForgeQueue()
            self.forge_queue.set_bus(self.msg_bus)
            self.forge_queue.start()
        except Exception as e:
            self.forge_queue = None
            print(f"[Aule] ForgeQueue start failed: {e}")
        # Tesla sensor stream → message bus
        try:
            from Tesla.SensorStream import SensorStream
            self.sensor_stream = SensorStream(parent=self)
            self.sensor_stream.attach_bus(self.msg_bus)
        except Exception as e:
            self.sensor_stream = None
            print(f"[Tesla] SensorStream init: {e}")

        # ── Network layer ─────────────────────────────────────────────────────
        self.hole_punch = HolePunch(self)   if HolePunch  else None
        self.kvm        = KVMClient(self)   if KVMClient  else None

        # ── System tray ───────────────────────────────────────────────────────
        self.sysTrayIcon = SystemTrayIcon(
            QIcon(self.imgDir + 'Pharos/indicator-ball.gif'), parent=self) if SystemTrayIcon else None
        if self.sysTrayIcon:
            self.sysTrayIcon.show()

        # ── Command history ───────────────────────────────────────────────────
        self.cmdhistory = []

        # ── UI ────────────────────────────────────────────────────────────────
        self.Philadelphos = None   # pre-set so Menu/Interface don't crash before _launch_philadelphos()
        self._init_ui()

        # ── dmesg boot header ─────────────────────────────────────────────────
        try:
            from Pharos.PtolDmesg import dmesg
            dmesg.boot()
            dmesg.write('pharos', 'boot initiated')
        except Exception as _e:
            print(f'[dmesg] {_e}')

        # ── Blockchain — resurrection check + bus subscription ────────────────
        self._chain = None
        try:
            from Pharos.ptol_blockchain import chain as _chain, SafeMode
            mode, ctx = _chain.resurrection_mode()
            if mode != SafeMode.CLEAN:
                try:
                    from Pharos.PtolDmesg import dmesg
                    dmesg.warn('pharos', f'resurrection mode: {mode.name}')
                except Exception:
                    pass
                print(f'[blockchain] resurrection: {mode.name} — {ctx}')
            self.msg_bus.subscribe(CH_BLOCKCHAIN, _chain.bus_handler)
            self._chain = _chain
        except Exception as _e:
            print(f'[blockchain] {_e}')

        # ── CyclicContextBuffer — kernel-owned, shared via CH_CONTEXT ─────────
        self.ccb = None
        try:
            from Philadelphos.cyclic_context_buffer import CyclicContextBuffer
            def _ccb_evict(entry):
                try:
                    self.msg_bus.broadcast_context_update({
                        'compressed': entry._compressed,
                        'address':    entry._hyperindex_address,
                        'hash':       entry._block_hash,
                    })
                except Exception:
                    pass
            self.ccb = CyclicContextBuffer(on_evict=_ccb_evict)
        except Exception as _e:
            print(f'[CCB] {_e}')

        # ── Lich — undead emergency manager ──────────────────────────────────
        try:
            from Lich import LichKing
            self.lich = LichKing(self)
        except Exception as _e:
            self.lich = None
            print(f'[Lich] {_e}')

    # ── Scene setup ───────────────────────────────────────────────────────────

    def _setup_scene(self):
        w, h = self.screen.width(), self.screen.height()

        self._form = QWidget(self)
        self._form.setContentsMargins(0, 0, 0, 0)
        layout = QGridLayout(self._form)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(0, 0, w, h)
        self.view  = QGraphicsView(self._form)
        self.view.setScene(self.scene)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setBackgroundBrush(QBrush(QColor('black')))
        self.view.setInteractive(True)
        self.view.setContentsMargins(0, 0, 0, 0)
        self.view.setGeometry(self.screen)

        self._form.setGeometry(self.screen)
        self.setCentralWidget(self._form)
        self.setGeometry(self.screen)
        self.setWindowTitle('Πτολεμαῖος Φιλάδελφος')
        self.setWindowIcon(QIcon(self.imgDir + 'ptol.svg'))

    # ── UI init ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.setStyleSheet(self.stylesheet)

        if Menu:
            self.Menu = Menu(parent=self)
            self.Menu.setParent(None)       # detach from QMainWindow so addWidget can embed it
            self._menu_proxy = self.scene.addWidget(self.Menu)
        else:
            self.Menu = None
            self._menu_proxy = None

        if User:
            self.Interface = User(self)
            self.Interface.setParent(None)  # detach from QMainWindow so PWindow can embed it
            if PWindow:
                self._pharos_win = PWindow(
                    self.scene, self.Interface,
                    title='', thread=None, timers=[],
                    x=self.Interface.x, y=self.Interface.y,
                    w=self.Interface.w, h=self.Interface.h,
                    undecorated=True,
                )
                self._pharos_proxy = self._pharos_win._proxy
            else:
                self._pharos_proxy = self.scene.addWidget(self.Interface)
                self._pharos_proxy.setPos(self.Interface.x, self.Interface.y)
                self._pharos_win = None
            self._interface_group = None
            # Spectro and indicator as PWindow children — move automatically on drag
            if hasattr(self.Interface, '_sp_proxy') and self.Interface._sp_proxy is not None:
                self.Interface._sp_proxy.setParentItem(self._pharos_win)
                self.Interface._sp_proxy.setPos(self.Interface.w + 10,
                                                 self.Interface.h - 85)
                self.Interface._sp_proxy.setZValue(0)
            if hasattr(self.Interface, '_ind_proxy') and self.Interface._ind_proxy is not None:
                self.Interface._ind_proxy.setParentItem(self._pharos_win)
                self.Interface._ind_proxy.setPos(10, 35)
        else:
            self.Interface = None
            self._pharos_proxy = None
            self._pharos_win   = None
            self._interface_group = None
            print('[Pharos] Interface (OpenGL) disabled — skipped')

        # ── Monad singleton — shared by shell pty and CH_LEARN subscriber ────────
        self.monad = None
        self.monad_learner = None
        if _Monad is not None:
            try:
                self.monad = _Monad(N=25000)
                _ck = os.path.join(os.path.dirname(__file__),
                                   'Callimachus', 'data', 'monad_wordnet.json')
                if os.path.exists(_ck):
                    self.monad.load(_ck)
                    print('[Monad] loaded from checkpoint')
                self.monad_learner = _MonadLearner(self.monad)
                self.monad_learner.start()
                # subscribe to CH_LEARN for passive text ingestion
                from Pharos.PtolBus import CH_LEARN
                self.msg_bus.subscribe(
                    CH_LEARN,
                    lambda msg: self.monad_learner.enqueue(
                        msg.payload if isinstance(msg.payload, str)
                        else str(msg.payload)))
                print('[Monad] learner thread started, CH_LEARN subscribed')
            except Exception as _e:
                print(f'[Monad] init error: {_e}')

        # ── PtolShell — permanent PGui window, 80×25 terminal ─────────────────
        _SW, _SH = 660, 415
        try:
            if PtolShell and PWindow:
                self._ptol_shell = PtolShell(parent=None)
                self._ptol_shell.Ptolemy = self
                self._ptol_shell.resize(_SW, _SH)
                self._shell_win = PWindow(
                    self.scene, self._ptol_shell,
                    title='Ptolemy',
                    thread=None, timers=[],
                    x=60, y=60, w=_SW, h=_SH)
            else:
                self._ptol_shell = None
                self._shell_win  = None
        except Exception as _e:
            self._ptol_shell = None
            self._shell_win  = None
            print(f'[PtolShell] init failed: {_e}')

        self._launch_philadelphos()   # after shell block — checks self._ptol_shell

        # ── LeftPanel (fixed sidebar, 30 s autohide) ──────────────────────────
        self._panel_proxy     = None
        self._panel_hide_timer = None
        self._magic_strip     = None
        try:
            from Pharos.LeftPanel import LeftPanel as _LP
            self.LeftPanel = _LP(parent=None)
            self.LeftPanel.resize(260, self.screen.height())
            self._panel_proxy = self.scene.addWidget(self.LeftPanel)
            self._panel_proxy.setPos(0, 0)
            self._panel_proxy.setZValue(5)
            self._panel_proxy.hide()                 # hidden until magic strip

            self._panel_hide_timer = QTimer(self)
            self._panel_hide_timer.setSingleShot(True)
            self._panel_hide_timer.setInterval(30000)
            self._panel_hide_timer.timeout.connect(self._hide_left_panel)

            self._panel_ef = _PanelTimerFilter(self._panel_hide_timer)
            self.LeftPanel.installEventFilter(self._panel_ef)

            self._magic_strip = _MagicStrip(self.screen.height(), self._show_left_panel)
            self._magic_strip.setPos(0, 0)
            self.scene.addItem(self._magic_strip)
        except Exception as _lp_e:
            self.LeftPanel = None
            print(f'[LeftPanel] {_lp_e}')

        # wire menu drag overlay after first event loop (widget sized by then)
        self._menu_drag = None
        QTimer.singleShot(0, self._wire_drag_overlays)

    def raise_ptolemy(self):
        self.raise_()
        self.activateWindow()
        if self._pharos_win is not None and self.Interface:
            self._pharos_win.setPos(self.Interface.x, self.Interface.y)

    def _show_left_panel(self):
        if self._panel_proxy:
            self._panel_proxy.show()
            if self._panel_hide_timer:
                self._panel_hide_timer.start()

    def _hide_left_panel(self):
        if self._panel_proxy:
            self._panel_proxy.hide()

    def _wire_drag_overlays(self):
        """Add transparent drag-grab strip over the menu (Interface uses PWindow drag)."""
        if self._menu_proxy and self.Menu:
            mp = self._menu_proxy
            w  = self.Menu.width()  or 200
            h  = self.Menu.height() or 30
            if w > 0:
                self._menu_drag = _DragOverlay(mp, w, h)
                self._menu_drag.setPos(mp.pos())
                self.scene.addItem(self._menu_drag)

    def _launch_philadelphos(self):
        """
        Philadelphos is the AI/command layer.
        If PtolShell is present it owns the visible input/output — Phila is
        API-only (setOutput calls). Only add Phila to scene when no shell exists.
        """
        try:
            from Philadelphos.Phila import Phila
            self.Philadelphos = Phila(None)
            if not self._ptol_shell:
                self.scene.addWidget(self.Philadelphos)
        except ImportError:
            self.Philadelphos = None

    # ── Face launchers (bus delegates) ────────────────────────────────────────

    def open_face(self, module_path, class_name, *args, **kwargs):
        """
        Universal face launcher. Dynamically imports and launches any face.
        Example: self.open_face('Phaleron.TreasureHunt.TreasureHunt', 'TreasureHunt')
        """
        face_cls = self.bus.import_face(module_path, class_name)
        return self.bus.launch(face_cls, *args, **kwargs)

    def openTuningDisplay(self, event=None):
        """Launch the Tuning Display stream monitor."""
        try:
            if self.tuning_display is None:
                from Pharos.TuningDisplay import TuningDisplay
                self.tuning_display = TuningDisplay(bus=self.bus, parent=self)
            self.tuning_display.show()
            self.tuning_display.raise_()
        except Exception as e:
            print(f'[TuningDisplay] {e}')

    def openSettings(self, section=None, event=None):
        try:
            from Pharos.settings_window import SettingsWindow
            if not hasattr(self, '_settings_win') or self._settings_win is None:
                self._settings_win = SettingsWindow(parent=self)
            self._settings_win.show()
            self._settings_win.raise_()
            if section:
                self._settings_win.select_section(section)
        except Exception as e:
            print(f'[Settings] failed to open: {e}')

    def openSearch(self, event=None):
        return self.open_face(
            'Phaleron.TreasureHunt.TreasureHunt', 'TreasureHunt')

    def openNavigation(self, event=None):
        return self.open_face('Anaximander.Navigation', 'Navigation')

    def openCore(self, event=None):
        from Mouseion.GLViewer import Viewer
        from Alexandria.Core   import Core
        return self.bus.launch(Viewer, Core, self)

    def openEarth(self, event=None):
        from Mouseion.GLViewer import Viewer
        from Alexandria.Earth  import Earth
        return self.bus.launch(Viewer, Earth, rotate=True)

    def openWikiGroup(self, event=None):
        return self.open_face('Mouseion.WikiGroup', 'WikiGroup')

    def openLibrary(self, event=None):
        return self.open_face('Mouseion.Library', 'Library')

    def openNotepad(self, event=None):
        return self.open_face('Phaleron.Notepad', 'Notepad')

    def openDbCPanel(self, event=None):
        return self.open_face('Callimachus.DBControlPanel', 'DBControlPanel')

    def openGraphPlot(self, event=None):
        from Archimedes.Maths.GraphPlot import GraphPlot
        return self.bus.launch(GraphPlot)

    def openFractal(self, event=None):
        try:
            from Alexandria.FractalRenderer import FractalView
            return self.bus.launch(FractalView)
        except Exception as e:
            print(f'[Fractal] {e}')

    def openStanDev(self, event=None):
        # Stub: StandardDeviation face not yet implemented.
        # Replace with: return self.open_face('Archimedes.Maths.StandardDeviation', 'StandardDeviation')
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, 'Standard Deviation',
                'StandardDeviation face is not implemented yet.')
        except Exception as e:
            print(f'[openStanDev stub] {e}')
        return None

    # ── Network launchers ─────────────────────────────────────────────────────

    def punch_to(self, peer_id, relay_host=None, relay_port=None):
        """Initiate hole punch. Connect kvm on success."""
        self.hole_punch.punch_ready.connect(self._on_punch_ready)
        self.hole_punch.punch_failed.connect(self._on_punch_failed)
        self.hole_punch.punch(peer_id, relay_host, relay_port)

    def _on_punch_ready(self, ip, port):
        self.kvm.connect(ip, port, sock=self.hole_punch.sock)
        # TreasureHunt VNC fallback URL (configure per deployment)
        self.kvm.vnc_url = None   # e.g. 'http://host:6080/vnc.html'

    def _on_punch_failed(self, reason):
        print(f'[Tesla/KVM] Hole punch failed: {reason}')
        vnc_url = self.kvm.open_vnc_fallback()
        if vnc_url:
            self._open_vnc_in_browser(vnc_url)

    def _open_vnc_in_browser(self, url):
        """Route VNC fallback URL to TreasureHunt tab via bus."""
        for rec in self.bus._registry.values():
            if rec['cls'] == 'TreasureHunt' and rec['state'] == 'running':
                face = rec.get('face')
                if face and hasattr(face, 'add_new_tab'):
                    face.add_new_tab(url, 'VNC Fallback')
                    return

    # ── Qt primitives ─────────────────────────────────────────────────────────

    def pen(self, color, width=1):
        p = QPen(QColor(color))
        p.setWidth(width)
        p.setCapStyle(Qt.PenCapStyle.FlatCap)
        return p

    def brush(self, color):
        return QBrush(QColor(color))

    def font(self, size=10):
        return QFont('Ubuntu Mono', size)

    def cwd(self):
        return os.getcwd()

    def sysTime(self):
        t = time.localtime()
        return f'{t[3]:02d}:{t[4]:02d}:{t[5]:02d}'

    def sysDate(self):
        t = time.localtime()
        return f'{t[2]:02d}.{t[1]:02d}.{str(t[0])[2:]}'

    def timeStamp(self):
        return [self.sysDate(), self.sysTime()]

    def cronJob(self, interval_ms, job):
        cron = QTimer(self)
        # Accept seconds (float) or milliseconds (int) — normalize to int ms
        ms = int(interval_ms * 1000) if interval_ms < 1 else int(interval_ms)
        cron.setInterval(ms)
        try:
            cron.timeout.connect(job)
        except TypeError:
            pass
        cron.start()
        return cron

    # ── Stylesheet ────────────────────────────────────────────────────────────

    def _build_stylesheet(self):
        return (
            "QMainWindow { background-color: black; color: white } "
            "QWidget { background-color: black; color: white } "
            "QMenuBar { border: 1px solid white; background-color: black; color: white } "
            "QMenuBar::item { background-color: black; color: white } "
            "QToolBar { border: 1px solid white; background-color: black; color: white } "
            "QStatusBar { border: 1px solid white; background-color: black; color: white } "
            "QTabWidget { border: 1px solid white; background-color: black; color: white } "
            "QTabBar::tab { border: 1px solid white; background-color: black; color: white } "
            "QComboBox { border: 1px solid white; background-color: #333; color: white } "
            "QPushButton { border: 1px solid #00ffff; background-color: black; color: #00ffff } "
            "QPushButton:hover { border: 1px solid #0055ff; color: #0055ff } "
            "QLineEdit { border: 1px solid white; background-color: #111; color: white } "
            "QDockWidget { border: 1px solid white; background-color: black; color: white } "
            "QTableWidget { background-color: black; color: white } "
            "QTableWidget::item:focus { border: 1px solid white; background-color: #003 } "
            "QHeaderView::section { background-color: #001a33; color: white } "
            "QTextBrowser { border: 1px solid black; background-color: white; color: black } "
            "QListWidget { background-color: #111; color: white } "
            "QLabel { border: 0px } "
        )

    # ── Events ────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        for fid in list(self.bus._registry.keys()):
            self.bus.terminate(fid)
        if self.msg_bus:
            self.msg_bus.stop()
        if self.kvm:
            self.kvm.disconnect()
        if self.hole_punch:
            self.hole_punch.close()
        event.accept()

    def keyPressEvent(self, event):
        key  = event.key()
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier:
            _map = {
                Qt.Key.Key_Q:         self.close,
                Qt.Key.Key_A:         self.openGraphPlot,       # Archimedes
                Qt.Key.Key_L:         self.openDbCPanel,        # Callimachus
                Qt.Key.Key_V:         self.openCore,            # Alexandria
                Qt.Key.Key_N:         self.openNavigation,      # Anaximander
                Qt.Key.Key_K:         self.openKryptos,
                Qt.Key.Key_M:         self.openLibrary,         # Mouseion
                Qt.Key.Key_P:         self.openSearch,          # Phaleron
                Qt.Key.Key_H:         self.raise_ptolemy,       # Pharos — raise interface
                Qt.Key.Key_T:         self.openTesla,
                Qt.Key.Key_F:         self.openSearch,
                Qt.Key.Key_Comma:     self.openSettings,
                Qt.Key.Key_QuoteLeft: self.openShell,           # CTRL+`
            }
            fn = _map.get(key)
            if fn:
                fn()

    def openShell(self, event=None):
        """Raise the Ptolemy shell window (always present, never hidden)."""
        if self._shell_win is not None:
            self._shell_win.show()
            if self._ptol_shell is not None:
                self._ptol_shell.setFocus()

    def openFace(self, face_id: str):
        """Dispatcher: open a Face by id string (used by DualTrayMenu, graph nodes)."""
        _dispatch = {
            'pharos':       self.raise_ptolemy,
            'archimedes':   self.openGraphPlot,
            'callimachus':  self.openDbCPanel,
            'alexandria':   self.openCore,
            'anaximander':  self.openNavigation,
            'kryptos':      self.openKryptos,
            'mouseion':     self.openLibrary,
            'phaleron':     self.openSearch,
            'tesla':        self.openTesla,
            'settings':     self.openSettings,
        }
        fn = _dispatch.get(face_id.lower())
        if fn:
            fn()

    def openKryptos(self, event=None):
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, 'Kryptos', 'Kryptos face not yet implemented.')
        except Exception:
            pass

    def openTesla(self, event=None):
        try:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, 'Tesla', 'Tesla face not yet implemented.')
        except Exception:
            pass

    def mousePressEvent(self, event):
        item = self.view.itemAt(int(event.position().x()), int(event.position().y()))
        if self.Philadelphos and hasattr(self.Philadelphos, 'setOutput'):
            self.Philadelphos.setOutput(str(item), speak=False)
        self._aniclick(event)

    def _aniclick(self, event):
        pen = self.pen('white', 2)
        brush = self.brush('black')
        x, y = int(event.position().x()), int(event.position().y())
        c1 = self.scene.addEllipse(x-10, y-10, 20,  20,  pen, brush)
        c2 = self.scene.addEllipse(x-20, y-20, 40,  40,  pen, brush)
        c3 = self.scene.addEllipse(x-30, y-30, 60,  60,  pen, brush)
        self.scene.removeItem(c1)
        self.scene.removeItem(c2)
        QTimer.singleShot(150, lambda: self._safe_remove(c3))

    def _safe_remove(self, item):
        if item.scene():
            self.scene.removeItem(item)

    def log(self, msg, color=None):
        """Post a log message to the message bus (CH_LOG channel)."""
        try:
            meta = {'color': color} if color else {}
            self.msg_bus.publish(BusMessage(CH_LOG, str(msg), Priority.T2,
                                            sender='Ptolemy', meta=meta))
        except Exception:
            print(f'[Ptolemy.log] {msg}')

    def hideShow(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()


# ══════════════════════════════════════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Ptolemy III')

    ptol = Ptolemy()
    ptol.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
