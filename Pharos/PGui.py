#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
PGui.py — Pharos Window Manager Shim
=====================================
Ptolemy's WINE-style UI layer.

Every Face module imports from here instead of PyQt directly:

    from Pharos.PGui import PMainWindow, PWidget, PButton, PLineEdit ...

PHAROS_MODE = 1  →  Faces render as PWindow items inside the Pharos
                     QGraphicsScene. Full Ptolemy desktop integration.

PHAROS_MODE = 0  →  All P-classes are transparent aliases to real Qt.
                     Any Face runs standalone, completely unmodified.

PWindow — the chrome unit:
  ┌─[PTOL]──[title]────────────[_][□][✕]─┐  ← title bar (draggable)
  │  gradient bracket decorations         │  ← glyph-square corners
  │                                       │
  │   face QWidget (QGraphicsProxyWidget) │
  │                                       │
  └───────────────────────────────────────┘

Thread lifecycle:
  minimize  → thread.quit() + thread.wait() / timer.stop()
              face proxy hidden — zero CPU when not visible
  restore   → thread.start() / timer.start()
              face proxy shown
  close     → thread.quit() + thread.wait()
              proxy and PWindow removed from scene

Menu system:
  All menus are plain-text files under Pharos/menus/.
  PMenuBar and PContextMenu auto-parse them on load.
  Any Python module's public API can be auto-extracted
  with extract_module_menu(module) → writes a menu file.

Author: Ptolemy Project / Pharos Face
"""

import os
import ast
import importlib
import inspect

from PyQt6.QtCore    import Qt, QRectF, QPointF, QTimer, pyqtSignal, QObject
from PyQt6.QtGui     import (QPainter, QColor, QPen, QBrush, QLinearGradient,
                             QFont, QFontMetrics, QCursor, QAction)
from PyQt6.QtSvg     import QSvgRenderer
from PyQt6.QtWidgets import (QWidget, QMainWindow, QPushButton, QLineEdit,
                             QLabel, QComboBox, QTabWidget, QDockWidget,
                             QTextEdit, QListWidget, QTableWidget,
                             QGraphicsItem, QGraphicsProxyWidget,
                             QGraphicsScene, QMenu, QMenuBar,
                             QApplication)

# ── Mode flag ─────────────────────────────────────────────────────────────────
PHAROS_MODE = int(os.environ.get('PTOLEMY_PHAROS', '1'))

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE      = os.path.dirname(os.path.abspath(__file__))
_PTOL_ROOT = os.path.dirname(_HERE)
_IMG_DIR   = os.path.join(_PTOL_ROOT, 'images', 'Pharos')
_MENU_DIR  = os.path.join(_HERE, 'menus')
_PTOL_SVG  = os.path.join(_IMG_DIR, 'ptolemysymbol.svg')

os.makedirs(_MENU_DIR, exist_ok=True)

# ── Colours ───────────────────────────────────────────────────────────────────
_C_BG        = QColor('#050d0d')
_C_TITLEBAR  = QColor('#0a1414')
_C_RED       = QColor('#cc2200')
_C_CYAN      = QColor('#00ffff')
_C_BLUE      = QColor('#0055ff')
_C_BORDER    = QColor(0, 255, 255, 60)
_C_CONTENT   = QColor('#0d2020')

_TITLE_H     = 28      # px — title bar height
_BTN_W       = 18      # control button width
_BTN_H       = 18      # control button height
_BTN_GAP     = 3       # gap between control buttons
_PTOL_W      = 22      # PTOL cipher button width
_CORNER_LONG = 20      # bracket arm long side
_CORNER_SHORT= 8       # bracket arm inner tick
_STROKE      = 6.0     # title bar gradient accent line


# ══════════════════════════════════════════════════════════════════════════════
#  MENU SYSTEM — plain text file format
# ══════════════════════════════════════════════════════════════════════════════

def extract_module_menu(module_or_path, menu_name=None):
    """
    Auto-extract a menu definition from a Python module.

    Uses AST parsing so the module is never executed — safe on files
    that import Qt, OpenGL, or other heavy dependencies.

    Writes  Pharos/menus/<menu_name>.menu  containing every
    public method of every class in the module, grouped by class.

    Format of the generated file:
        # <ClassName>
        method_name | docstring first line (if available)
        ---
        # <NextClass>
        ...

    Parameters
    ----------
    module_or_path : str path to .py file  OR  module object
    menu_name      : output filename stem (default: derived from path/module)
    """
    if isinstance(module_or_path, str):
        path = module_or_path
        name = menu_name or os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            src = f.read()
        tree = ast.parse(src)
    else:
        mod  = module_or_path
        name = menu_name or getattr(mod, '__name__', 'unknown').split('.')[-1]
        src  = inspect.getsource(mod)
        tree = ast.parse(src)

    outpath = os.path.join(_MENU_DIR, name + '.menu')
    lines   = [f'# Auto-extracted from {name}\n']

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = []
        for item in ast.walk(node):
            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                # grab docstring if present
                doc = ''
                if (item.body and
                        isinstance(item.body[0], ast.Expr) and
                        isinstance(item.body[0].value, ast.Constant)):
                    doc = str(item.body[0].value.value).split('\n')[0][:80]
                methods.append((item.name, doc))
        if not methods:
            continue
        lines.append(f'\n# {node.name}\n')
        for mname, doc in methods:
            lines.append(f'{mname} | {doc}\n')
        lines.append('---\n')

    with open(outpath, 'w') as f:
        f.writelines(lines)

    return outpath


def load_menu_file(menu_name):
    """
    Parse a .menu plain-text file.

    Returns list of sections:
        [ {'header': str, 'items': [{'name': str, 'tip': str}]} ]
    """
    path = os.path.join(_MENU_DIR, menu_name + '.menu')
    if not os.path.exists(path):
        return []

    sections = []
    current  = None

    with open(path) as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith('##'):
                continue
            if line.startswith('#'):
                current = {'header': line[1:].strip(), 'items': []}
                sections.append(current)
            elif line == '---':
                current = None
            elif '|' in line and current is not None:
                parts = line.split('|', 1)
                current['items'].append({
                    'name': parts[0].strip(),
                    'tip':  parts[1].strip() if len(parts) > 1 else ''
                })
    return sections


class PMenuBar(QMenuBar):
    """
    QMenuBar that loads its structure from a .menu plain-text file.
    Falls back to empty if the file doesn't exist.
    Menus can be rebuilt at runtime by calling reload().
    """

    def __init__(self, menu_name, callback=None, parent=None):
        super().__init__(parent)
        self._menu_name = menu_name
        self._callback  = callback   # callable(action_name) or None
        self._build()

    def _build(self):
        self.clear()
        for section in load_menu_file(self._menu_name):
            menu = self.addMenu(section['header'])
            for item in section['items']:
                act = QAction(item['name'], self)
                act.setStatusTip(item['tip'])
                if self._callback:
                    act.triggered.connect(
                        lambda checked, n=item['name']: self._callback(n)
                    )
                menu.addAction(act)

    def reload(self):
        self._build()


class PContextMenu(QMenu):
    """
    QMenu loaded from a .menu plain-text file section.
    menu_name  — file stem
    section    — header name of the section to use (or None = first)
    """

    def __init__(self, menu_name, section=None, callback=None, parent=None):
        super().__init__(parent)
        sections = load_menu_file(menu_name)
        target   = None
        for s in sections:
            if section is None or s['header'] == section:
                target = s
                break
        if target:
            for item in target['items']:
                act = QAction(item['name'], self)
                act.setStatusTip(item['tip'])
                if callback:
                    act.triggered.connect(
                        lambda checked, n=item['name']: callback(n)
                    )
                self.addAction(act)


# ══════════════════════════════════════════════════════════════════════════════
#  PGUI PAINTER HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _grad(x1, y1, x2, y2):
    """Horizontal gradient: red → cyan → blue."""
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0.00, _C_RED)
    g.setColorAt(0.38, _C_CYAN)
    g.setColorAt(1.00, _C_BLUE)
    return g


def _border_grad(x1, y1, x2, y2):
    """Horizontal border gradient with alpha."""
    g = QLinearGradient(x1, y1, x2, y2)
    g.setColorAt(0.00, QColor(204, 34,   0, 150))
    g.setColorAt(0.38, QColor(0,   255, 255, 100))
    g.setColorAt(1.00, QColor(0,   85,  255, 150))
    return g


# ══════════════════════════════════════════════════════════════════════════════
#  PWINDOW — the chrome QGraphicsItem
# ══════════════════════════════════════════════════════════════════════════════

class PWindow(QGraphicsItem):
    """
    The Ptolemy window chrome.

    Usage
    -----
        face_widget = TreasureHunt(parent=None)    # any QWidget
        win = PWindow(
            scene,
            face_widget,
            title  = 'Phaleron — Treasure Hunt',
            thread = face_thread,      # QThread or None
            timers = [face_timer],     # list of QTimers or []
            x=100, y=80
        )

    The face_widget is embedded via QGraphicsProxyWidget.
    Dragging the title bar moves the whole window.
    Minimize suspends thread + timers and hides the proxy.
    Restore resumes thread + timers and shows the proxy.
    Close terminates thread, removes PWindow from scene.
    """

    MINIMIZED = 0
    NORMAL    = 1

    def __init__(self, scene_or_widget, widget=None, title='Ptolemy',
                 thread=None, timers=None,
                 x=60, y=60, w=640, h=480,
                 face_id=None, bus=None, ptolemy=None,
                 undecorated=False):
        """
        Two call signatures are supported:

        Legacy / direct:
            PWindow(scene, widget, title=..., thread=..., timers=..., x, y, w, h)

        PtolBus.launch() style:
            PWindow(face_widget, title=..., face_id=..., bus=..., ptolemy=...)
            — scene is inferred from ptolemy.scene
            — thread/timers are pulled from face_widget._ptol_thread / ._ptol_timers
        """
        # ── resolve overloaded first arg ──────────────────────────────────
        if widget is None:
            # PtolBus call: first arg IS the widget; scene comes from ptolemy
            widget = scene_or_widget
            if ptolemy is not None:
                scene = ptolemy.scene
            else:
                raise ValueError("PWindow: scene or ptolemy required")
        else:
            scene = scene_or_widget

        # pull thread/timers from face if not explicitly supplied
        if thread is None:
            thread = getattr(widget, '_ptol_thread', None)
        if not timers:
            timers = getattr(widget, '_ptol_timers', [])

        self._face_id     = face_id
        self._bus         = bus
        self._ptolemy     = ptolemy
        self._undecorated = undecorated

        super().__init__()

        self._scene   = scene
        self._widget  = widget
        self._title   = title
        self._thread  = thread
        self._timers  = timers or []
        self._state   = self.NORMAL
        # face_id/bus/ptolemy already set above in overload block

        # title bar height — zero when undecorated
        self._title_h = 0 if undecorated else _TITLE_H

        # geometry
        self._x       = x
        self._y       = y
        self._w       = w
        self._h       = h + self._title_h

        # drag state
        self._drag    = False
        self._drag_offset = QPointF()

        # SVG renderer for PTOL cipher button
        self._ptol_renderer = None
        if os.path.exists(_PTOL_SVG):
            self._ptol_renderer = QSvgRenderer(_PTOL_SVG)

        # embed the face widget
        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(widget)
        self._proxy.setPos(0, self._title_h)

        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)   # we handle drag
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

        scene.addItem(self)

    # ── bounding rect ──────────────────────────────────────────────────────

    def boundingRect(self):
        return QRectF(0, 0, self._w, self._h)

    # ── hit rects (title-bar sub-regions) ─────────────────────────────────

    def _ptol_rect(self):
        return QRectF(6, (_TITLE_H - _PTOL_W) / 2, _PTOL_W, _PTOL_W)

    def _close_rect(self):
        x = self._w - 8 - _BTN_W
        y = (_TITLE_H - _BTN_H) / 2
        return QRectF(x, y, _BTN_W, _BTN_H)

    def _max_rect(self):
        x = self._w - 8 - _BTN_W * 2 - _BTN_GAP
        y = (_TITLE_H - _BTN_H) / 2
        return QRectF(x, y, _BTN_W, _BTN_H)

    def _min_rect(self):
        x = self._w - 8 - _BTN_W * 3 - _BTN_GAP * 2
        y = (_TITLE_H - _BTN_H) / 2
        return QRectF(x, y, _BTN_W, _BTN_H)

    def _title_drag_rect(self):
        """Draggable area — title bar minus buttons and PTOL btn."""
        return QRectF(_PTOL_W + 12, 0,
                      self._w - (_PTOL_W + 12) - (_BTN_W * 3 + _BTN_GAP * 2 + 16),
                      _TITLE_H)

    # ── paint ──────────────────────────────────────────────────────────────

    def paint(self, painter, option, widget=None):
        if self._undecorated:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self._w, self._h

        # ── window body ──
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_C_BG))
        painter.drawRect(QRectF(0, 0, w, h))

        # ── border gradient ──
        pen = QPen(QBrush(_border_grad(0, 0, w, 0)), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRectF(0.5, 0.5, w - 1, h - 1))

        # ── title bar bg ──
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_C_TITLEBAR))
        painter.drawRect(QRectF(0, 0, w, _TITLE_H))

        # ── gradient accent line ──
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_grad(0, 0, w, 0)))
        painter.drawRect(QRectF(0, _TITLE_H - 1, w, 1.5))

        # ── corner brackets ──
        self._paint_corners(painter, w, h)

        # ── PTOL cipher button ──
        self._paint_ptol_btn(painter)

        # ── title text ──
        painter.setPen(QPen(QColor('#00dddd')))
        painter.setFont(QFont('Ubuntu Mono', 9))
        fm    = QFontMetrics(painter.font())
        tw    = fm.horizontalAdvance(self._title)
        tx    = (w - tw) / 2
        ty    = _TITLE_H / 2 + fm.ascent() / 2 - 1
        painter.drawText(int(tx), int(ty), self._title)

        # ── control buttons ──
        self._paint_controls(painter, w)

    def _paint_corners(self, painter, w, h):
        g     = QBrush(_grad(0, 0, w, 0))
        short = _CORNER_SHORT
        long_ = _CORNER_LONG

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(g)

        # top-left outer
        painter.setOpacity(0.85)
        painter.drawRect(QRectF(2, 2, 3, long_))
        painter.drawRect(QRectF(2, 2, long_, 3))
        # top-left inner tick
        painter.setOpacity(0.5)
        painter.drawRect(QRectF(9, 9, 2, short))
        painter.drawRect(QRectF(9, 9, short, 2))

        # top-right outer
        painter.setOpacity(0.85)
        painter.drawRect(QRectF(w - 5, 2, 3, long_))
        painter.drawRect(QRectF(w - 2 - long_, 2, long_, 3))
        # top-right inner tick
        painter.setOpacity(0.5)
        painter.drawRect(QRectF(w - 11, 9, 2, short))
        painter.drawRect(QRectF(w - 9 - short, 9, short, 2))

        # bottom-left
        painter.setOpacity(0.4)
        painter.drawRect(QRectF(2, h - 2 - long_, 3, long_))
        painter.drawRect(QRectF(2, h - 5, long_, 3))

        # bottom-right
        painter.drawRect(QRectF(w - 5, h - 2 - long_, 3, long_))
        painter.drawRect(QRectF(w - 2 - long_, h - 5, long_, 3))

        painter.setOpacity(1.0)

    def _paint_ptol_btn(self, painter):
        r    = self._ptol_rect()
        painter.setPen(QPen(QColor('#003333'), 0.5))
        painter.setBrush(QBrush(QColor('#080f0f')))
        painter.drawRoundedRect(r, 3, 3)

        if self._ptol_renderer and self._ptol_renderer.isValid():
            self._ptol_renderer.render(painter, r)
        else:
            # fallback — draw PTOL cipher directly
            cx = r.x() + r.width()  / 2
            cy = r.y() + r.height() / 2
            rad = r.width() * 0.38

            # O — blue circle
            pen = QPen(QColor('#0000FF'), r.width() * 0.11)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), rad, rad)

            # I — red line through and beyond
            pen = QPen(QColor('#FF0000'), r.width() * 0.08)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            top = r.y() + 1
            bot = r.y() + r.height() - 1
            painter.drawLine(QPointF(cx, top), QPointF(cx, bot))

    def _paint_controls(self, painter, w):
        y   = (_TITLE_H - _BTN_H) / 2

        # minimize — underscore
        mr = self._min_rect()
        painter.setPen(QPen(QColor('#003333'), 0.5))
        painter.setBrush(QBrush(QColor('#0d1a1a')))
        painter.drawRoundedRect(mr, 2, 2)
        painter.setPen(QPen(QColor('#005555'), 1.5))
        my = mr.y() + mr.height() * 0.65
        painter.drawLine(
            QPointF(mr.x() + 3, my),
            QPointF(mr.x() + mr.width() - 3, my)
        )

        # maximize — square
        xr = self._max_rect()
        painter.setPen(QPen(QColor('#003333'), 0.5))
        painter.setBrush(QBrush(QColor('#0d1a1a')))
        painter.drawRoundedRect(xr, 2, 2)
        painter.setPen(QPen(QColor('#004466'), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        inner = xr.adjusted(3, 3, -3, -3)
        painter.drawRect(inner)

        # close — X (very dim red)
        cr = self._close_rect()
        painter.setPen(QPen(QColor('#220000'), 0.5))
        painter.setBrush(QBrush(QColor('#0d1010')))
        painter.drawRoundedRect(cr, 2, 2)
        painter.setPen(QPen(QColor('#441111'), 1.2))
        m = 4
        painter.drawLine(
            QPointF(cr.x() + m,              cr.y() + m),
            QPointF(cr.x() + cr.width() - m, cr.y() + cr.height() - m)
        )
        painter.drawLine(
            QPointF(cr.x() + cr.width() - m, cr.y() + m),
            QPointF(cr.x() + m,              cr.y() + cr.height() - m)
        )

    # ── mouse events ───────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if self._undecorated:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag = True
                self._drag_offset = event.scenePos()
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            super().mousePressEvent(event)
            return

        p = event.pos()

        if self._close_rect().contains(p):
            self._close()
            return

        if self._min_rect().contains(p):
            self._toggle_minimize()
            return

        if self._max_rect().contains(p):
            # placeholder — maximize not yet implemented
            return

        if self._title_drag_rect().contains(p):
            self._drag = True
            self._drag_offset = event.scenePos()
            self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag:
            delta = event.scenePos() - self._drag_offset
            self.setPos(self.pos() + delta)
            self._drag_offset = event.scenePos()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag:
            self._drag = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            return
        super().mouseReleaseEvent(event)

    # ── window lifecycle ───────────────────────────────────────────────────

    def _toggle_minimize(self):
        if self._state == self.NORMAL:
            self._minimize()
        else:
            self._restore()

    def _minimize(self):
        """Hide face proxy. Suspend thread + timers. Zero CPU."""
        self._state = self.MINIMIZED
        self._proxy.hide()

        # resize chrome to title bar only
        self._h = self._title_h
        self.prepareGeometryChange()

        # suspend thread
        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()

        # pause timers
        for t in self._timers:
            if t.isActive():
                t.stop()

        self.update()

    def _restore(self):
        """Show face proxy. Resume thread + timers."""
        self._state = self.NORMAL
        self._proxy.show()

        # restore full height
        self._h = self._proxy.widget().height() + self._title_h
        self.prepareGeometryChange()

        # resume thread
        if self._thread is not None:
            if not self._thread.isRunning():
                self._thread.start()

        # resume timers
        for t in self._timers:
            if not t.isActive():
                t.start()

        self.update()

    def _close(self):
        """Terminate thread, remove from scene.
        Delegates to PtolBus.terminate() when available so registry stays clean.
        """
        if self._bus is not None and self._face_id is not None:
            # Bus handles full teardown including scene removal
            self._bus.terminate(self._face_id)
            return

        # standalone path — no bus
        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()

        for t in self._timers:
            t.stop()

        if self._scene.items().__contains__(self) if hasattr(self._scene, 'items') else True:
            self._scene.removeItem(self)

    # ── public API ─────────────────────────────────────────────────────────

    def set_thread(self, thread):
        """Attach a QThread to this window for lifecycle management."""
        self._thread = thread

    def add_timer(self, timer):
        """Register a QTimer for suspend/resume on minimize."""
        self._timers.append(timer)

    def set_title(self, title):
        self._title = title
        self.update()


# ══════════════════════════════════════════════════════════════════════════════
#  PASSTHROUGH ALIASES — standalone mode (PHAROS_MODE = 0)
#  In Pharos mode these are replaced below with P-native classes.
# ══════════════════════════════════════════════════════════════════════════════

PMainWindow  = QMainWindow
PWidget      = QWidget
PButton      = QPushButton
PLineEdit    = QLineEdit
PLabel       = QLabel
PComboBox    = QComboBox
PTabWidget   = QTabWidget
PDockWidget  = QDockWidget
PTextEdit    = QTextEdit
PListWidget  = QListWidget
PTableWidget = QTableWidget


# ══════════════════════════════════════════════════════════════════════════════
#  PHAROS MODE OVERRIDES
#  When PHAROS_MODE=1, PMainWindow wraps itself in a PWindow on show().
# ══════════════════════════════════════════════════════════════════════════════

if PHAROS_MODE:

    class PMainWindow(QMainWindow):
        """
        Drop-in QMainWindow replacement.
        When shown inside Ptolemy, wraps itself in a PWindow chrome item.
        Requires self._ptolemy_scene to be set before show() is called,
        or a parent that exposes .scene.
        """

        _ptolemy_scene  = None   # set by Ptolemy before spawning faces
        _ptolemy_wins   = {}     # window registry  id(widget) → PWindow

        def __init__(self, parent=None):
            super().__init__(parent)
            self._pwindow = None
            self.setWindowFlags(Qt.WindowType.Widget)

        def show(self):
            scene = PMainWindow._ptolemy_scene
            if scene is None:
                # no scene registered — fall back to normal Qt window
                super().show()
                return

            if self._pwindow is None:
                title = self.windowTitle() or self.__class__.__name__
                w     = self.width()  or 640
                h     = self.height() or 480
                self._pwindow = PWindow(
                    scene, self, title=title,
                    w=w, h=h,
                    x=80, y=80
                )
                PMainWindow._ptolemy_wins[id(self)] = self._pwindow
            else:
                self._pwindow.setVisible(True)

        def hide(self):
            if self._pwindow:
                self._pwindow._minimize()
            else:
                super().hide()

        def setWindowTitle(self, title):
            super().setWindowTitle(title)
            if self._pwindow:
                self._pwindow.set_title(title)

        @classmethod
        def register_scene(cls, scene):
            """Call once from Ptolemy.__init__ to wire up the scene."""
            cls._ptolemy_scene = scene


# ══════════════════════════════════════════════════════════════════════════════
#  PGUI CONVENIENCE — spawn a face with full chrome in one call
# ══════════════════════════════════════════════════════════════════════════════

def spawn_face(scene, widget_class, title,
               thread=None, timers=None,
               x=80, y=80, w=640, h=480,
               **kwargs):
    """
    Instantiate a face widget and wrap it in a PWindow in one call.

        win = spawn_face(
            ptolemy.scene,
            TreasureHunt,
            'Phaleron — Treasure Hunt',
            x=100, y=60, w=900, h=600
        )

    Returns the PWindow item (not the widget).
    """
    widget = widget_class(**kwargs)
    widget.resize(w, h)
    return PWindow(scene, widget, title=title,
                   thread=thread, timers=timers,
                   x=x, y=y, w=w, h=h)


# ══════════════════════════════════════════════════════════════════════════════
#  PTOLEMY INTEGRATION HOOK
#  Call this from Ptolemy2.py initUI() to register the scene.
# ══════════════════════════════════════════════════════════════════════════════

def init_pharos(ptolemy_instance):
    """
    Wire PGui into a live Ptolemy instance.
    Call once from Ptolemy.initUI():

        from Pharos.PGui import init_pharos
        init_pharos(self)
    """
    PMainWindow.register_scene(ptolemy_instance.scene)
