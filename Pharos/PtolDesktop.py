#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
PtolDesktop.py — Ptolemy Desktop Architecture
===============================================
Pharos Face

Three systems:

1. ProcessGraph — JACK-style node graph on QGraphicsScene
   - Ptolemy Center node (pannable, not fixed)
   - Face nodes orbit Ptolemy Center
   - Minimized PWindows become graph nodes, auto-connect to their Face
   - Stream connections draggable (sensors, data pipes → projects)
   - Graph pans and transmutes freely

2. SidebarPanel — auto-hiding sidebar
   - 23px activation strip at left edge of screen
   - Hover over strip → unhide sidebar (slides in)
   - Auto-hides after 45 seconds of no interaction
   - Covers other objects (z-order above scene)
   - Fixed — does NOT move with graph

3. TooltipShortcut — enhanced tooltips with keyboard shortcut display
   - Every interactive element: tooltip + shortcut key
   - Shortcut scheme: system tray owns shortcut assignments
   - Format: "Label  [CTRL+K]"

4. DualTrayMenu — system tray with two distinct menus
   - Left click  → User Input Menu  (conversation, commands, quick launch)
   - Right click → System Menu      (sensors, settings, Face status, exit)
   - Stub: Ptolemy's own tray (future)
   - Icon: ptol_button.svg / ptolemysymbol.svg

Usage
-----
    from Pharos.PtolDesktop import ProcessGraph, SidebarPanel, DualTrayMenu

    graph   = ProcessGraph(scene, ptolemy)
    sidebar = SidebarPanel(scene, ptolemy, left_panel_widget)
    tray    = DualTrayMenu(icon, ptolemy)
"""

import os
import math
from PyQt6.QtCore  import (Qt, QRectF, QPointF, QTimer, QPropertyAnimation,
                            QEasingCurve, pyqtSignal, QObject)
from PyQt6.QtGui   import (QPainter, QColor, QPen, QBrush, QFont,
                            QFontMetrics, QCursor, QIcon, QAction)
from PyQt6.QtSvg   import QSvgRenderer
from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsScene, QGraphicsObject,
                              QSystemTrayIcon, QMenu, QWidget,
                              QGraphicsProxyWidget, QApplication,
                              QGraphicsLineItem)

try:
    from Pharos.PtolColor import FaceColor
    _COLORS = {
        'ptolemy':     '#00ccff',
        'pharos':      FaceColor.PHAROS,
        'callimachus': FaceColor.CALLIMACHUS,
        'archimedes':  FaceColor.ARCHIMEDES,
        'alexandria':  FaceColor.ALEXANDRIA,
        'anaximander': FaceColor.ANAXIMANDER,
        'kryptos':     FaceColor.KRYPTOS,
        'phaleron':    FaceColor.PHALERON,
        'tesla':       FaceColor.TESLA,
        'mouseion':    getattr(FaceColor, 'MOUSEION', '#e67e22'),
        'philadelphos':getattr(FaceColor, 'PHILADELPHOS', '#16a085'),
        'aule':        '#ffcc00',
    }
except ImportError:
    _COLORS = {k: '#00ccff' for k in
               ['ptolemy','pharos','callimachus','archimedes','alexandria',
                'anaximander','kryptos','phaleron','tesla','mouseion',
                'philadelphos','aule']}

_IMAGES = os.path.join(os.path.dirname(__file__), '..', 'images', 'Pharos')

# ── Keyboard shortcut registry ────────────────────────────────────────────────
# Owned by the system tray. Referenced by tooltips.

SHORTCUTS = {
    'exit':         'CTRL+Q',
    'archimedes':   'CTRL+A',
    'callimachus':  'CTRL+L',
    'alexandria':   'CTRL+V',
    'anaximander':  'CTRL+N',
    'kryptos':      'CTRL+K',
    'mouseion':     'CTRL+M',
    'phaleron':     'CTRL+P',
    'pharos':       'CTRL+H',
    'tesla':        'CTRL+T',
    'search':       'CTRL+F',
    'navigation':   'CTRL+G',
    'settings':     'CTRL+,',
    'shell':        'CTRL+`',
    'wifi':         'CTRL+I',
    'clock':        'CTRL+D',
    'sidebar':      'CTRL+B',
    'new_window':   'CTRL+W',
}

def tooltip_with_shortcut(label: str, key: str = None) -> str:
    """Format tooltip with optional keyboard shortcut."""
    if key and key in SHORTCUTS:
        return f'{label}  [{SHORTCUTS[key]}]'
    return label


# ═══════════════════════════════════════════════════════════════════════════════
# §1  PROCESS GRAPH — JACK-style node layout
# ═══════════════════════════════════════════════════════════════════════════════

_NODE_R    = 36   # face node radius
_CENTER_R  = 54   # Ptolemy center radius
_ORBIT_R   = 180  # default orbit radius
_CONN_W    = 1.5  # connection line width


class GraphNode(QGraphicsObject):
    """
    A single node in the process graph.
    Ptolemy Center or a Face node.
    Draggable. Emits position_changed for connection redraw.
    """

    position_changed = pyqtSignal()
    node_clicked     = pyqtSignal(str)   # emits face_id

    def __init__(self, face_id: str, label: str, color: str,
                 radius: float = _NODE_R, is_center: bool = False,
                 parent=None):
        super().__init__(parent)
        self.face_id   = face_id
        self.label     = label
        self.color     = QColor(color)
        self.radius    = radius
        self.is_center = is_center

        self._drag      = False
        self._drag_off  = QPointF()
        self._hover     = False
        self._minimized_window = None   # PWindow if this is a minimized win node
        self._svg_renderer = None

        # load face SVG if available
        svg_path = os.path.join(_IMAGES, f'{face_id}symbol.svg')
        if os.path.exists(svg_path):
            self._svg_renderer = QSvgRenderer(svg_path)

        self._port_hover    = False
        self._port_dragging = False
        self._drag_line     = None
        self._graph_ref     = None   # set by ProcessGraph after construction

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)   # we handle drag
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)
        self.setZValue(5)

        # tooltip
        tip = tooltip_with_shortcut(label, face_id)
        self.setToolTip(tip)

    def boundingRect(self):
        r = self.radius + 6
        return QRectF(-r, -r, r * 2, r * 2)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.radius
        hover_boost = 8 if self._hover else 0

        # glow ring
        glow = QColor(self.color)
        glow.setAlpha(60 + hover_boost * 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPointF(0, 0), r + 6 + hover_boost, r + 6 + hover_boost)

        # body
        body = QColor(self.color)
        body.setAlpha(30 if not self._hover else 50)
        painter.setBrush(QBrush(body))
        pen = QPen(self.color, 1.5 if not self._hover else 2.5)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(0, 0), r, r)

        # Port dot (right edge — JACK-style output port)
        port_color = QColor('#00ffcc') if self._port_hover else QColor('#004444')
        painter.setPen(QPen(QColor('#00ffcc'), 1))
        painter.setBrush(QBrush(port_color))
        painter.drawEllipse(self._port_rect())

        # SVG icon or text
        if self._svg_renderer and self._svg_renderer.isValid():
            svg_r = r * 0.65
            svg_rect = QRectF(-svg_r, -svg_r, svg_r * 2, svg_r * 2)
            self._svg_renderer.render(painter, svg_rect)
        else:
            painter.setPen(QPen(self.color))
            painter.setFont(QFont('Ubuntu Mono', 7 if self.is_center else 6))
            fm = QFontMetrics(painter.font())
            text = self.label[:8]
            tw = fm.horizontalAdvance(text)
            painter.drawText(int(-tw / 2), int(fm.ascent() / 2), text)

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()

    def hoverMoveEvent(self, event):
        was = self._port_hover
        self._port_hover = self._in_port(event.pos())
        if was != self._port_hover:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor if self._port_hover
                                   else Qt.CursorShape.ArrowCursor))
            self.update()

    def hoverLeaveEvent(self, event):
        self._hover = False
        self._port_hover = False
        self.update()

    def _port_rect(self) -> QRectF:
        """Small port circle on right edge of node for JACK-drag."""
        r = self.radius
        return QRectF(r - 5, -5, 10, 10)

    def _in_port(self, pos: QPointF) -> bool:
        return self._port_rect().contains(pos)

    def contextMenuEvent(self, event):
        """Right-click: Connect to... menu."""
        from PyQt6.QtGui import QAction; from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background:#080d1a; border:1px solid #1a2a3a;
                    color:#aac8d8; font-family:'Ubuntu Mono'; font-size:11px; }
            QMenu::item:selected { background:#0d1830; color:#00ccff; }
        """)

        # find graph to get sibling nodes
        graph = getattr(self, '_graph_ref', None)
        if graph:
            connect_menu = menu.addMenu('Connect to...')
            for fid, node in graph._nodes.items():
                if node is self:
                    continue
                a = QAction(node.label, connect_menu)
                a.setData(fid)
                a.triggered.connect(
                    lambda checked, s=self.face_id, d=fid: graph.add_stream_connection(s, d, 'stream')
                )
                connect_menu.addAction(a)
            menu.addSeparator()

        disconnect_a = menu.addAction('Disconnect all streams')
        disconnect_a.triggered.connect(lambda: self._disconnect_streams(graph))
        menu.addSeparator()
        info_a = menu.addAction(f'Face: {self.label}')
        info_a.setEnabled(False)

        menu.exec(event.screenPos().toPoint())
        event.accept()

    def _disconnect_streams(self, graph):
        if not graph:
            return
        to_remove = [c for c in graph._conns
                     if (c.src is self or c.dst is self)
                     and c.stype == 'stream']
        for c in to_remove:
            graph._scene.removeItem(c)
            graph._conns.remove(c)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._in_port(event.pos()):
                # JACK-style port drag — start drawing a connection line
                self._port_dragging = True
                sp = self.scenePos() + QPointF(self.radius, 0)
                self._drag_line = PortDragLine(sp)
                self.scene().addItem(self._drag_line)
                self.setCursor(QCursor(Qt.CursorShape.CrossCursor))
            else:
                self._drag = True
                self._drag_off = event.pos()
                self.setCursor(QCursor(Qt.CursorShape.SizeAllCursor))
                self.setZValue(20)
        event.accept()

    def mouseMoveEvent(self, event):
        if getattr(self, '_port_dragging', False) and self._drag_line:
            self._drag_line.set_dst(event.scenePos())
            self._drag_line.update()
        elif self._drag:
            delta = event.scenePos() - self.scenePos() - self._drag_off
            self.setPos(self.pos() + delta)
            self.position_changed.emit()
        event.accept()

    def mouseReleaseEvent(self, event):
        if getattr(self, '_port_dragging', False):
            self._port_dragging = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            # find node under release point
            if self._drag_line:
                self.scene().removeItem(self._drag_line)
                self._drag_line = None
            target = self._find_node_at(event.scenePos())
            if target and target is not self:
                graph = getattr(self, '_graph_ref', None)
                if graph:
                    graph.add_stream_connection(
                        self.face_id, target.face_id, 'stream'
                    )
        elif self._drag:
            self._drag = False
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            self.setZValue(5)
            self.position_changed.emit()
        event.accept()

    def _find_node_at(self, scene_pos: QPointF):
        """Return GraphNode under scene_pos, or None."""
        items = self.scene().items(scene_pos)
        for item in items:
            if isinstance(item, GraphNode) and item is not self:
                return item
        return None

    def mouseDoubleClickEvent(self, event):
        self.node_clicked.emit(self.face_id)
        event.accept()


class StreamConnection(QGraphicsItem):
    """
    Draggable connection line between two nodes.
    Represents a data stream (sensor feed, pipe, etc.)
    """

    def __init__(self, src_node: GraphNode, dst_node: GraphNode,
                 stream_type: str = 'data', color: str = '#00ccff'):
        super().__init__()
        self.src  = src_node
        self.dst  = dst_node
        self.stype = stream_type
        self.color = QColor(color)
        self.color.setAlpha(140)
        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self._hover = False

    def boundingRect(self):
        sp = self.src.scenePos()
        dp = self.dst.scenePos()
        x = min(sp.x(), dp.x()) - 10
        y = min(sp.y(), dp.y()) - 10
        w = abs(sp.x() - dp.x()) + 20
        h = abs(sp.y() - dp.y()) + 20
        return QRectF(x, y, w, h)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        sp = self.src.scenePos()
        dp = self.dst.scenePos()
        pen = QPen(self.color, 2.0 if self._hover else _CONN_W)
        pen.setStyle(Qt.PenStyle.DashLine if self.stype == 'stream' else Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.drawLine(sp, dp)

        # midpoint label
        if self._hover:
            mid = (sp + dp) / 2
            painter.setPen(QPen(self.color))
            painter.setFont(QFont('Ubuntu Mono', 7))
            painter.drawText(mid.toPoint(), self.stype)

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()

    def hoverMoveEvent(self, event):
        was = self._port_hover
        self._port_hover = self._in_port(event.pos())
        if was != self._port_hover:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor if self._port_hover
                                   else Qt.CursorShape.ArrowCursor))
            self.update()
        self.prepareGeometryChange()

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()
        self.prepareGeometryChange()


class ProcessGraph(QObject):
    """
    JACK-style process graph on QGraphicsScene.

    Ptolemy Center at scene center. Face nodes orbit it.
    Graph pans and transmutes freely (no fixed anchor).
    Minimized PWindows auto-add as nodes, connected to their Face.
    Stream connections are draggable by user.
    """

    FACE_IDS = [
        'pharos', 'callimachus', 'archimedes', 'alexandria',
        'anaximander', 'kryptos', 'phaleron', 'tesla',
        'mouseion', 'philadelphos',
    ]
    FACE_LABELS = {
        'pharos':       'Pharos',
        'callimachus':  'Callimachus',
        'archimedes':   'Archimedes',
        'alexandria':   'Alexandria',
        'anaximander':  'Anaximander',
        'kryptos':      'Kryptos',
        'phaleron':     'Phaleron',
        'tesla':        'Tesla',
        'mouseion':     'Mouseion',
        'philadelphos': 'Philadelphos',
    }

    def __init__(self, scene: QGraphicsScene, ptolemy=None):
        super().__init__()
        self._scene   = scene
        self._ptolemy = ptolemy
        self._nodes:  dict[str, GraphNode] = {}
        self._conns:  list[StreamConnection] = []

        self._build()

    def _center(self) -> QPointF:
        return QPointF(
            int(self._scene.width())  // 2,
            int(self._scene.height()) // 2
        )

    def _build(self):
        """Build Ptolemy Center + Face nodes in orbital layout."""
        cx, cy = self._center().x(), self._center().y()

        # Ptolemy Center
        center = GraphNode(
            'ptolemy', 'Ptolemy', _COLORS['ptolemy'],
            radius=_CENTER_R, is_center=True
        )
        center.setPos(cx, cy)
        center.position_changed.connect(self._redraw_connections)
        center.node_clicked.connect(self._on_node_click)
        self._scene.addItem(center)
        self._nodes['ptolemy'] = center

        # Face nodes in orbit
        n = len(self.FACE_IDS)
        for i, fid in enumerate(self.FACE_IDS):
            angle = (2 * math.pi * i / n) - math.pi / 2
            nx = cx + _ORBIT_R * math.cos(angle)
            ny = cy + _ORBIT_R * math.sin(angle)

            color = _COLORS.get(fid, '#00ccff')
            node  = GraphNode(fid, self.FACE_LABELS[fid], color)
            node.setPos(nx, ny)
            node.position_changed.connect(self._redraw_connections)
            node.node_clicked.connect(self._on_node_click)
            self._scene.addItem(node)
            self._nodes[fid] = node

            node._graph_ref = self   # back-reference for context menu

            # connection to center (structural, not a stream)
            conn = StreamConnection(center, node, stream_type='face',
                                    color=color)
            self._scene.addItem(conn)
            self._conns.append(conn)

        # set graph_ref on center too
        center._graph_ref = self

    def _redraw_connections(self):
        for conn in self._conns:
            conn.prepareGeometryChange()
            conn.update()

    def _on_node_click(self, face_id: str):
        """Double-click on a node — open that Face."""
        if self._ptolemy and hasattr(self._ptolemy, 'openFace'):
            self._ptolemy.openFace(face_id)

    def add_minimized_window(self, pwindow, face_id: str):
        """
        When a PWindow is minimized, add it as a node in the graph.
        Auto-connects to its Face node.
        """
        if face_id not in self._nodes:
            return

        face_node = self._nodes[face_id]
        fp        = face_node.scenePos()

        # offset slightly from face node
        win_node = GraphNode(
            f'win_{id(pwindow)}',
            pwindow._title[:10] if hasattr(pwindow, '_title') else 'Window',
            _COLORS.get(face_id, '#445566'),
            radius=18
        )
        win_node.setPos(fp.x() + 60, fp.y() + 40)
        win_node._minimized_window = pwindow
        win_node.node_clicked.connect(lambda _: pwindow._restore())
        win_node.position_changed.connect(self._redraw_connections)
        self._scene.addItem(win_node)
        self._nodes[f'win_{id(pwindow)}'] = win_node

        # auto-connect to face node
        conn = StreamConnection(face_node, win_node, stream_type='window',
                                color=_COLORS.get(face_id, '#445566'))
        self._scene.addItem(conn)
        self._conns.append(conn)

    def add_stream_connection(self, src_id: str, dst_id: str,
                              stream_type: str = 'stream',
                              color: str = '#00ccff'):
        """User-dragged stream connection between any two nodes."""
        src = self._nodes.get(src_id)
        dst = self._nodes.get(dst_id)
        if src and dst:
            conn = StreamConnection(src, dst, stream_type, color)
            self._scene.addItem(conn)
            self._conns.append(conn)


# ═══════════════════════════════════════════════════════════════════════════════
# §2  SIDEBAR PANEL — auto-hiding with 23px activation strip
# ═══════════════════════════════════════════════════════════════════════════════

_SIDEBAR_W    = 260     # full sidebar width
_STRIP_W      = 23      # activation strip width
_AUTO_HIDE_MS = 45000   # 45 seconds


class SidebarActivationStrip(QGraphicsItem):
    """
    The 23px invisible activation strip at the left edge.
    Hover → emit activate signal → sidebar slides in.
    """

    def __init__(self, scene_h: float, on_activate, parent=None):
        super().__init__(parent)
        self._h           = scene_h
        self._on_activate = on_activate
        self._hover       = False
        self.setAcceptHoverEvents(True)
        self.setZValue(100)
        self.setToolTip(tooltip_with_shortcut('Sidebar', 'sidebar'))

    def boundingRect(self):
        return QRectF(0, 0, _STRIP_W, self._h)

    def paint(self, painter, option, widget=None):
        # nearly invisible — just a hint
        color = QColor('#00ccff')
        color.setAlpha(15 if not self._hover else 40)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRect(self.boundingRect())

        # vertical line at edge
        pen = QPen(QColor('#00ccff'), 1)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.drawLine(QPointF(_STRIP_W - 1, 0),
                         QPointF(_STRIP_W - 1, self._h))

    def hoverEnterEvent(self, event):
        self._hover = True
        self.update()

    def hoverMoveEvent(self, event):
        was = self._port_hover
        self._port_hover = self._in_port(event.pos())
        if was != self._port_hover:
            self.setCursor(QCursor(Qt.CursorShape.CrossCursor if self._port_hover
                                   else Qt.CursorShape.ArrowCursor))
            self.update()
        self._on_activate()

    def hoverLeaveEvent(self, event):
        self._hover = False
        self.update()


class SidebarPanel(QObject):
    """
    Auto-hiding sidebar.
    - 23px activation strip at left edge
    - Slides in on hover, auto-hides after 45 seconds
    - Fixed position — does NOT pan with graph
    - Covers other objects (high z-order)
    - Contains LeftPanel widget
    """

    def __init__(self, scene: QGraphicsScene, ptolemy=None,
                 left_panel_widget: QWidget = None):
        super().__init__()
        self._scene   = scene
        self._ptolemy = ptolemy
        self._widget  = left_panel_widget
        self._visible = False

        # proxy for the sidebar widget
        self._proxy = None
        if left_panel_widget:
            self._proxy = QGraphicsProxyWidget()
            self._proxy.setWidget(left_panel_widget)
            self._proxy.setPos(-_SIDEBAR_W, 0)   # start hidden
            self._proxy.setZValue(99)
            scene.addItem(self._proxy)
            left_panel_widget.setFixedWidth(_SIDEBAR_W)
            left_panel_widget.setFixedHeight(int(scene.height()))

        # activation strip
        self._strip = SidebarActivationStrip(
            int(scene.height()), self._show
        )
        self._strip.setPos(0, 0)
        scene.addItem(self._strip)

        # auto-hide timer
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(_AUTO_HIDE_MS)
        self._timer.timeout.connect(self._hide)

    def _show(self):
        if self._visible:
            self._timer.start()   # reset timer on re-hover
            return
        self._visible = True
        if self._proxy:
            self._proxy.setPos(0, 0)
        self._timer.start()

    def _hide(self):
        if not self._visible:
            return
        self._visible = False
        if self._proxy:
            self._proxy.setPos(-_SIDEBAR_W, 0)

    def reset_timer(self):
        """Call when user interacts with sidebar to reset auto-hide clock."""
        if self._visible:
            self._timer.start()

    def force_show(self):
        self._show()

    def force_hide(self):
        self._timer.stop()
        self._hide()


# ═══════════════════════════════════════════════════════════════════════════════
# §3  DUAL TRAY MENU
# ═══════════════════════════════════════════════════════════════════════════════

class DualTrayMenu(QSystemTrayIcon):
    """
    System tray with two distinct menus.

    Left click  → User Input Menu  (conversation, commands, quick launch)
    Right click → System Menu      (sensors, Face status, settings, exit)

    Icon: ptol_button.svg or ptolemysymbol.svg
    """

    def __init__(self, ptolemy=None, parent=None):
        self._ptolemy = ptolemy

        # resolve icon
        icon = self._load_icon()
        super().__init__(icon, parent)

        self._build_user_menu()
        self._build_system_menu()

        # left click → user menu
        self.activated.connect(self._on_activate)

        # right click → system menu (Qt default for setContextMenu)
        self.setContextMenu(self._system_menu)

        # ── Ptolemy's own tray stub ───────────────────────────────────────
        # TODO: Ptolemy will eventually have his own system tray
        # displaying his active state, current Face, and conversation status.
        # Stub registered here — implementation deferred.
        # self._ptolemy_tray = PtolemyTrayStub()
        # ─────────────────────────────────────────────────────────────────

        self.setToolTip('Ptolemy')
        self.show()

    def _load_icon(self) -> QIcon:
        for name in ('ptol_button.svg', 'ptolemysymbol.svg', 'pharossymbol.svg'):
            path = os.path.join(_IMAGES, name)
            if os.path.exists(path):
                return QIcon(path)
        return QIcon()   # empty fallback

    # ── User Input Menu (left click) ─────────────────────────────────────────

    def _build_user_menu(self):
        m = QMenu()
        m.setStyleSheet(self._menu_style())

        # Conversation / commands
        a = QAction('⬡  Open Ptolemy Shell', m)
        a.setShortcut(SHORTCUTS.get('shell', ''))
        a.triggered.connect(self._open_shell)
        m.addAction(a)

        m.addSeparator()

        # Quick Face launch
        for fid, label in ProcessGraph.FACE_LABELS.items():
            sc = SHORTCUTS.get(fid, '')
            action = QAction(f'    {label}', m)
            if sc:
                action.setShortcut(sc)
            action.setData(fid)
            action.triggered.connect(lambda checked, f=fid: self._open_face(f))
            m.addAction(action)

        m.addSeparator()

        hide_a = QAction('Hide', m)
        hide_a.triggered.connect(self.hide)
        m.addAction(hide_a)

        self._user_menu = m

    # ── System Menu (right click) ─────────────────────────────────────────────

    def _build_system_menu(self):
        m = QMenu()
        m.setStyleSheet(self._menu_style())

        # Settings
        settings_a = QAction('⚙  Settings', m)
        settings_a.setShortcut(SHORTCUTS.get('settings', ''))
        settings_a.triggered.connect(self._open_settings)
        m.addAction(settings_a)

        m.addSeparator()

        # Face status section
        m.addSection('FACES')
        for fid, label in ProcessGraph.FACE_LABELS.items():
            a = QAction(f'○  {label}', m)
            a.setData(fid)
            m.addAction(a)

        m.addSeparator()

        # Sensors section (Tesla)
        m.addSection('SENSORS')
        self._sensor_section = m   # reference for dynamic updates

        m.addSeparator()

        # WiFi shortcut
        wifi_a = QAction(f'📶  WiFi Settings  [{SHORTCUTS.get("wifi","")}]', m)
        wifi_a.triggered.connect(self._open_wifi)
        m.addAction(wifi_a)

        m.addSeparator()

        exit_a = QAction(f'Exit  [{SHORTCUTS.get("exit","")}]', m)
        exit_a.triggered.connect(self._exit)
        m.addAction(exit_a)

        self._system_menu = m

    # ── Event routing ─────────────────────────────────────────────────────────

    def _on_activate(self, reason):
        if reason == QSystemTrayIcon.Trigger:      # left single click
            self._user_menu.popup(QCursor.pos())
        # right click handled by setContextMenu → _system_menu

    # ── Actions ───────────────────────────────────────────────────────────────

    def _open_shell(self):
        if self._ptolemy and hasattr(self._ptolemy, 'openShell'):
            self._ptolemy.openShell()

    def _open_face(self, face_id: str):
        if self._ptolemy and hasattr(self._ptolemy, 'openFace'):
            self._ptolemy.openFace(face_id)

    def _open_settings(self):
        if self._ptolemy and hasattr(self._ptolemy, 'openSettings'):
            self._ptolemy.openSettings()

    def _open_wifi(self):
        if self._ptolemy and hasattr(self._ptolemy, 'openSettings'):
            self._ptolemy.openSettings(section='wifi')

    def _exit(self):
        if self._ptolemy is not None:
            self._ptolemy.close()
        else:
            QApplication.instance().quit()

    def _menu_style(self) -> str:
        return """
            QMenu {
                background: #080d1a;
                border: 1px solid #1a2a3a;
                color: #aac8d8;
                font-family: 'Ubuntu Mono';
                font-size: 11px;
            }
            QMenu::item:selected {
                background: #0d1830;
                color: #00ccff;
            }
            QMenu::separator {
                height: 1px;
                background: #1a2a3a;
                margin: 3px 0;
            }
            QMenu::section {
                color: #445566;
                font-size: 9px;
                letter-spacing: 2px;
                padding: 4px 8px 2px;
            }
        """


# ═══════════════════════════════════════════════════════════════════════════════
# §4  JACK-STYLE PORT DRAG + RIGHT-CLICK CONNECT
# ═══════════════════════════════════════════════════════════════════════════════

class PortDragLine(QGraphicsItem):
    """
    Temporary drag line while user is drawing a stream connection.
    Appears when user drags from a node port. Disappears on release.
    """
    def __init__(self, src_pos: QPointF, parent=None):
        super().__init__(parent)
        self._src = src_pos
        self._dst = src_pos
        self._pen = QPen(QColor('#00ccff'), 1.5, Qt.PenStyle.DashLine)
        self._pen.setDashPattern([6, 4])
        self.setZValue(200)

    def set_dst(self, pos: QPointF):
        self.prepareGeometryChange()
        self._dst = pos

    def boundingRect(self):
        x = min(self._src.x(), self._dst.x()) - 10
        y = min(self._src.y(), self._dst.y()) - 10
        w = abs(self._src.x() - self._dst.x()) + 20
        h = abs(self._src.y() - self._dst.y()) + 20
        return QRectF(x, y, w, h)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self._pen)
        painter.drawLine(self._src, self._dst)
        # destination dot
        dot = QPen(QColor('#00ccff'), 1)
        painter.setPen(dot)
        painter.setBrush(QBrush(QColor('#00ccff')))
        painter.drawEllipse(self._dst, 4, 4)
