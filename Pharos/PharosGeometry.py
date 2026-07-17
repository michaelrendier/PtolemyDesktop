#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
PharosGeometry.py — Pharos Interface Display Geometries
========================================================
Pure geometry layer: widget construction, layout positions, drawing primitives.
No menu dispatch, no bus calls, no callbacks.

Classes:
    _PaintOverlay(QWidget)  — transparent overlay; paints arcs/text on the seal
    PharosLayout(QWidget)   — geometry base class; subclassed by User

Interface.py imports PharosLayout and adds all behavior via User(PharosLayout).
"""

from PyQt6.QtCore    import Qt, QRectF, QRect, QTimer, QPointF
from PyQt6.QtGui     import QPixmap, QPolygonF, QPainter
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsProxyWidget, QWidget, QGridLayout, QLabel)

from math      import pi, cos, sin, ceil, sqrt
from random    import randrange
from subprocess import Popen, PIPE

import os
import psutil


# ══════════════════════════════════════════════════════════════════════════════
#  _PaintOverlay — transparent QWidget overlay; draws arcs and text on seal
# ══════════════════════════════════════════════════════════════════════════════

class _PaintOverlay(QWidget):
    """
    Transparent child widget of PharosLayout.
    Paints curved text, title banners, and proc-monitor rings over the seal SVG.
    WA_TransparentForMouseEvents passes all clicks to underlying buttons.
    Center is derived from display.geometry() so all circular elements share
    the same exact center as the seal.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.User    = parent
        self.Ptolemy = parent.Ptolemy

        self.x = 0
        self.y = 0
        self.w = parent.w
        self.h = parent.h

        self.MONITOR  = False
        self.MINI     = False
        self.identity = 'Pharos'
        self.color    = 'darkcyan'
        self.cwd      = ''
        self.name = self.user = self.platform = self.nodename = ''
        self.time = self.date = ''

        self.centerx = parent.w // 2
        self.centery = parent.h // 2

        self.colors = [(r, g, b) for r in (0, 1) for g in (0, 1) for b in (0, 1)]
        self.colordict = {
            (0,0,0):'black', (0,0,1):'blue',    (0,1,0):'green',
            (0,1,1):'cyan',  (1,0,0):'red',     (1,0,1):'yellow',
            (1,1,0):'magenta',(1,1,1):'white',
        }

        self.screensaver = QTimer(self)
        self.screensaver.timeout.connect(self._switch_monitor)
        self.screensaver.setSingleShot(True)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # Size to the seal widget width — wider than parent.w (225) because the
        # seal SVG is fixed at btnSize*13=299px.  Arc text at radius ~130 from
        # center ~149 reaches x≈279 which clips if the overlay is only 225px.
        seal_w = parent.display.width() if parent.display.width() > parent.w else parent.w
        self.w = seal_w
        self.setGeometry(0, 0, seal_w, parent.h)

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(1000)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start()

    # ── display state ──────────────────────────────────────────────────────────

    def set_mini(self, mini: bool):
        self.MINI = mini
        if mini:
            self.MONITOR = True
            if self.screensaver.isActive():
                self.screensaver.stop()
        else:
            self.MONITOR = False
            self.screensaver.start(10000)
        self.update()

    def changeIdentity(self, identity: str):
        self.identity = identity
        self.update()

    def _switch_monitor(self):
        self.MONITOR = True
        self.update()

    def refresh(self):
        self.name     = str(self.Ptolemy.name)
        self.user     = str(self.Ptolemy.user)[2:-1]
        self.platform = str(self.Ptolemy.platform)[2:-1]
        self.nodename = str(self.Ptolemy.nodename)[2:-1]
        self.time     = self.Ptolemy.sysTime()
        self.date     = self.Ptolemy.sysDate()

        self.color = {
            'Pharos':      'darkcyan',
            'Alexandria':  'magenta',
            'Anaximander': 'orange',
            'Archimedes':  'darkblue',
            'Callimachus': 'darkgreen',
            'Kryptos':     'purple',
            'Phaleron':    'grey',
            'Mouseion':    'white',
            'Tesla':       'darkred',
        }.get(self.identity, 'darkcyan')

        geo = self.User.display.geometry()
        self.centerx = geo.x() + geo.width()  // 2
        self.centery = geo.y() + geo.height() // 2
        self.cwd = '*'.join(self.Ptolemy.cwd()[1:].split('/')[-3:])
        self.update()

    # ── Qt paint protocol ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(self.Ptolemy.pen(self.color))
        painter.setBrush(self.Ptolemy.brush('black'))
        painter.setFont(self.Ptolemy.font(12))
        self._title(painter, self.name, 0, 15)
        self._title(painter, self.user, 1, 28)
        if self.MONITOR:
            self._procMonitor(painter)
        self._archtype(painter, self.identity)
        painter.end()

    # ── drawing primitives ─────────────────────────────────────────────────────

    def _archtype(self, painter, persona=None):
        radius      = int(self.User.display.height() / 2.3)
        sweep_angle = 160
        start_angle = 190
        self.cwd    = '*'.join(self.Ptolemy.cwd()[1:].split('/')[-3:])

        painter.setPen(self.Ptolemy.pen('blue'))
        self._labelcur(painter, self.centerx - 3, self.centery + 5,
                       radius, start_angle, sweep_angle, self.cwd)
        painter.setPen(self.Ptolemy.pen('white'))
        self._labelcur(painter, self.centerx - 4, self.centery + 6,
                       radius, start_angle, sweep_angle, self.cwd)

        if persona:
            painter.setPen(self.Ptolemy.pen('darkgreen', 2))
            painter.setFont(self.Ptolemy.font(18))
            radius      = int(self.User.display.height() / 2.25)
            sweep_angle = -110
            start_angle = 145
            self._labelcur(painter, self.centerx - 3, self.centery + 5,
                           radius, start_angle, sweep_angle, persona)
            painter.setPen(self.Ptolemy.pen('orange'))
            self._labelcur(painter, self.centerx - 4, self.centery + 6,
                           radius, start_angle, sweep_angle, persona)

    def _title(self, painter, title, x, y):
        titlex = self.x + x
        titley = self.y + y
        painter.setPen(self.Ptolemy.pen(self.color))
        painter.setBrush(self.Ptolemy.brush(self.color))
        painter.setFont(self.Ptolemy.font(18))
        upper = QPolygonF([
            QPointF(titlex + 3,                titley - 5),
            QPointF(titlex + 8,                titley - 10),
            QPointF(titlex + (self.w / 3) * 2, titley - 10),
            QPointF(titlex + (self.w / 3) * 2 - 5, titley - 5),
        ])
        painter.drawPolygon(upper)
        lower = QPolygonF([
            QPointF(titlex + 3,          titley),
            QPointF(titlex + 8,          titley - 5),
            QPointF(titlex + self.w - 5, titley - 5),
            QPointF(titlex + self.w - 10,titley),
        ])
        painter.drawPolygon(lower)
        painter.setPen(self.Ptolemy.pen('red'))
        painter.drawLine(titlex + 3, titley - 4, titlex + self.w - 5, titley - 4)
        painter.setPen(self.Ptolemy.pen('black'))
        painter.drawText(titlex + 10, titley - 2, title)
        painter.setPen(self.Ptolemy.pen('white'))
        painter.drawText(titlex + 8,  titley,     title)

    def _labelcur(self, painter, cx, cy, radius, start_angle, sweep_angle, label):
        try:
            theta = 2.0 / (360.0 / sweep_angle) * pi / (len(label) - 1)
        except ZeroDivisionError:
            theta = pi / 180
        c = cos(theta)
        s = sin(theta)
        x = radius * cos(start_angle * (pi / 180.))
        y = radius * sin(start_angle * (pi / 180.))
        for i in label:
            painter.drawText(int(x + cx), int(y + cy), i)
            t = x
            x = c * x - s * y
            y = s * t + c * y

    def _arc(self, painter, x, y, radius, start_angle, sweep_angle):
        arcRect = QRectF(x - radius, y - radius, 2 * radius + 1, 2 * radius + 1)
        painter.drawArc(arcRect, int(start_angle * 16), int(sweep_angle * 16))

    # ── proc monitor ───────────────────────────────────────────────────────────

    def _procMonitor(self, painter):
        cpuCount   = psutil.cpu_count()
        cpuPercent = psutil.cpu_percent(None, True)
        cpuAngle   = 360.0 / cpuCount

        psMem      = psutil.virtual_memory()
        memAngle   = 360.0 * (psMem[2] / 100.)

        psSwap     = psutil.swap_memory()
        swapAngle  = 360 * (psSwap[3] / 100.0)

        netIF      = self._cmdline('ls /sys/class/net/').decode().split('\n')[:-1]
        netCount   = len(netIF)
        netAngle   = 360.0 / max(netCount, 1)

        proc       = psutil.process_iter()
        procList   = list(proc)
        procNum    = len(procList)
        procAngle  = 360.0 / max(procNum, 1)

        kwidth = int(self.w * 0.08)
        if kwidth % 2 != 0:
            kwidth += 2
        centerAdjust = (kwidth + 1) / 2
        painter.setBrush(self.Ptolemy.brush('white'))
        painter.drawEllipse(
            int(self.centerx - centerAdjust), int(self.centery - centerAdjust),
            kwidth, kwidth
        )

        for i in range(cpuCount):
            color = self.colordict[self.colors[i + 3]]
            painter.setPen(self.Ptolemy.pen(color, 5))
            self._arc(painter, self.centerx, self.centery, 30,
                      i * cpuAngle, cpuAngle * (cpuPercent[i] / 100.))

        painter.setPen(self.Ptolemy.pen('cyan', 5))
        self._arc(painter, self.centerx, self.centery, 40, 0, memAngle)
        self._arc(painter, self.centerx, self.centery, 50, 0, swapAngle)
        self._arc(painter, self.centerx, self.centery, 60, 0, 360)

        for i in range(len(netIF)):
            color = self.colordict[self.colors[i + 1]]
            painter.setPen(self.Ptolemy.pen(color, 5))
            if self._netstat(netIF[i]):
                self._arc(painter, self.centerx, self.centery, 70,
                          i * netAngle, netAngle)

        painter.setPen(self.Ptolemy.pen('cyan', 23))
        for i in range(procNum):
            try:
                procPercent = procList[i].cpu_percent()
            except psutil.NoSuchProcess:
                pass
            else:
                if procPercent > 0:
                    self._arc(painter, self.centerx, self.centery, 80,
                              i * procAngle, procAngle)

    def _cmdline(self, command):
        process = Popen(args=command, stdout=PIPE, stderr=PIPE, shell=True)
        return process.communicate()[0]

    def _netstat(self, interface):
        s1 = psutil.net_io_counters(True)
        s2 = psutil.net_io_counters(True)
        return (int(s2[interface][0]) - int(s1[interface][0]) +
                int(s2[interface][1]) - int(s1[interface][1])) > 0


# kept for import compatibility — PharosLayout now uses _PaintOverlay
UserDisplay = _PaintOverlay


# ══════════════════════════════════════════════════════════════════════════════
#  PharosLayout — geometry base class for User
# ══════════════════════════════════════════════════════════════════════════════

class PharosLayout(QWidget):
    """
    Geometry-only base. Constructs all widgets, defines layout positions.
    Assigns no callbacks — User subclass wires those via _wire_callbacks().
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.Ptolemy = parent
        self.styles  = self.Ptolemy.stylesheet

        self.x = int(self.Ptolemy.scene.width()  / 2) - 76
        self.y = int(self.Ptolemy.scene.height() / 2) - 175
        self.w = 225
        self.h = 350

        self.setGeometry(self.x, self.y, self.w, self.h)
        self.setStyleSheet('QWidget { background-color: transparent; }')

        phila         = self.Ptolemy.Philadelphos
        self.output   = phila.setOutput if phila and hasattr(phila, 'setOutput') else None
        self.interfaceImg = self.Ptolemy.pharosImg
        self.mediaDir     = self.Ptolemy.mediaDir
        self.scene        = self.Ptolemy.scene

        self.identity = 'Pharos'
        self.setToolTip(self.identity + ' Interface')

        self.sysTrayList = [
            'display', 'power', 'alexandria', 'archimedes', 'anaximander',
            'callimachus', 'kryptos', 'mouseion', 'phaleron', 'pharos', 'tesla',
            'treasureHunt', 'navigation', 'core', 'earth', 'graph', 'fractal',
            'stanDev', 'dbCPanel', 'library', 'wikiGroup', 'clock',
        ]

        self.FS      = 44100
        self.CHUNKSZ = 1024

        self.initUi()

    # ── construction ───────────────────────────────────────────────────────────

    def initUi(self):
        self.btnSize = 23

        self.display = QSvgWidget(self.interfaceImg + 'nav-seal.svg', parent=self)
        self.display.setFixedSize(self.btnSize * 13, self.btnSize * 13)
        self.frame       = self.frameGeometry()
        self.displayRect = QRect(
            self.frameGeometry().x(), self.frameGeometry().y(),
            self.display.rect().width(), self.display.rect().height(),
        )

        self._overlay = _PaintOverlay(self)

        self.buildButtons()

        self.clock = QLabel(str(self.Ptolemy.timeStamp()))
        self.clock.setFixedHeight(self.btnSize)
        self.clock.setToolTip('Clock')
        self.clock.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout = QGridLayout(self)
        self.originalLayout()
        self.setLayout(self.layout)
        self._overlay.raise_()   # keep overlay above layout widgets

        self.clockTimer = QTimer(self)
        self.clockTimer.setInterval(1000)
        self.clockTimer.timeout.connect(self.clockAnimate)
        self.clockTimer.start()

        self.spectro = None
        self.mic     = None
        try:
            from Archimedes.SpectroSecurity import LiveSpectrogram as LS
            self.spectro = LS.SpectrogramWidget(self)
            self.spectro.read_collected.connect(self.spectro.update)
            self.spectro.setFixedSize(50, 50)
            self.spectro.setWindowFlags(Qt.WindowType.CustomizeWindowHint)
            self.spectro.setStyleSheet(self.styles)
            self._sp_proxy = QGraphicsProxyWidget()
            self._sp_proxy.setWidget(self.spectro)
            self._sp_proxy.setZValue(0)
            # _sp_proxy added to interface group by Ptolemy3._init_ui() after group creation
            self.mic = LS.MicrophoneRecorder(self.spectro.read_collected)
            t = QTimer(self)
            t.timeout.connect(self.mic.read)
            t.start(int(1000 / (self.FS / self.CHUNKSZ)))
        except ImportError:
            pass

        self.indicator = QLabel()
        self.indicatorIcon = QPixmap(self.interfaceImg + 'indicator-ball.gif')
        self.indicator.setPixmap(self.indicatorIcon)
        self.indicator.resize(75, 75)
        self._ind_proxy = QGraphicsProxyWidget()
        self._ind_proxy.setWidget(self.indicator)
        self.indicator.show()
        self.indicator.setVisible(True)

    def _make_btn(self, name: str, svg: str, tip: str):
        btn = QSvgWidget(self.interfaceImg + svg)
        btn.setFixedSize(self.btnSize, self.btnSize)
        btn.setToolTip(tip)
        setattr(self, name + 'Btn', btn)

    def buildButtons(self):
        """Construct all button widgets with sizes and tooltips. No callbacks."""
        self.clockBtn = QLabel(str(self.Ptolemy.timeStamp()))
        self.clockBtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clockBtn.setFixedHeight(self.btnSize)
        self.clockBtn.setToolTip('Clock  [CTRL+D]')

        self.blankBtn = QSvgWidget(self.interfaceImg + 'blank.svg')
        self.blankBtn.setFixedSize(self.btnSize, self.btnSize)

        self._make_btn('power',        'power.svg',            'Exit Program  [CTRL+Q]')
        self._make_btn('alexandria',   'alexandriasymbol.svg', 'Alexandria  [CTRL+V]')
        self._make_btn('archimedes',   'archimedessymbol.svg', 'Archimedes Menu  [CTRL+A]')
        self._make_btn('anaximander',  'anaximandersymbol.svg','Anaximander Menu  [CTRL+N]')
        self._make_btn('callimachus',  'callimachussymbol.svg','Callimachus Menu  [CTRL+L]')
        self._make_btn('kryptos',      'kryptossymbol.svg',    'Kryptos Menu  [CTRL+K]')
        self._make_btn('mouseion',     'mouseionsymbol.svg',   'Mouseion Menu  [CTRL+M]')
        self._make_btn('phaleron',     'phaleronsymbol.svg',   'Phaleron Menu  [CTRL+P]')
        self._make_btn('pharos',       'pharossymbol.svg',     'Pharos Menu  [CTRL+H]')
        self._make_btn('tesla',        'teslasymbol.svg',      'Tesla Menu  [CTRL+T]')
        self._make_btn('treasureHunt', 'treasurehunt.svg',     'Treasure Hunt  [CTRL+F]')
        self._make_btn('navigation',   'navigation.svg',       'Navigation Assistant')
        self._make_btn('core',         'procmonitor.svg',      'Core')
        self._make_btn('earth',        'earth.svg',            'Earth')
        self._make_btn('graph',        'graphplot.svg',        'GraphPlot')
        self._make_btn('fractal',      'fractal.svg',          'Fractal Viewer')
        self._make_btn('stanDev',      'standarddeviation.svg','Standard Deviation')
        self._make_btn('dbCPanel',     'databasecpanel.svg',   'Database Control Panel')
        self._make_btn('library',      'library.svg',          'Read Library Books')
        self._make_btn('wikiGroup',    'wikigroup.svg',        'Read Wikipedia Books')

    def originalLayout(self):
        self.layout.addWidget(self.display,       0,  0, 10, 10)
        self.layout.addWidget(self.powerBtn,      11, 0,  1,  1)
        self.layout.addWidget(self.alexandriaBtn, 11, 1,  1,  1)
        self.layout.addWidget(self.archimedesBtn, 11, 2,  1,  1)
        self.layout.addWidget(self.anaximanderBtn,11, 3,  1,  1)
        self.layout.addWidget(self.callimachusBtn,11, 4,  1,  1)
        self.layout.addWidget(self.kryptosBtn,    11, 5,  1,  1)
        self.layout.addWidget(self.mouseionBtn,   11, 6,  1,  1)
        self.layout.addWidget(self.phaleronBtn,   11, 7,  1,  1)
        self.layout.addWidget(self.pharosBtn,     11, 8,  1,  1)
        self.layout.addWidget(self.teslaBtn,      11, 9,  1,  1)
        self.layout.addWidget(self.clock,         12, 0,  1, 10)

    def clearLayout(self):
        for name in self.sysTrayList[2:-1]:
            btn = getattr(self, name + 'Btn', None)
            if btn:
                btn.deleteLater()
        self.buildButtons()
        self.layout.addWidget(self.pharosBtn, 11, 1, 1, 1)

    # ── display updates ────────────────────────────────────────────────────────

    def clockAnimate(self):
        self.layout.removeWidget(self.clock)
        self.clock.setText(str(self.Ptolemy.timeStamp()))
        del self.clockBtn
        self.clockBtn = QLabel(str(self.Ptolemy.timeStamp()))
        self.clockBtn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clockBtn.setFixedHeight(self.btnSize)
        self.clockBtn.setToolTip('Clock  [CTRL+D]')
        self.layout.addWidget(self.clockBtn, 12, 0, 1, 10)

    def displayEnter(self):
        self.display.load(self.interfaceImg + 'nav-seal-over.svg')
        if not self._overlay.MINI:
            self._overlay.MONITOR = False
            if self._overlay.screensaver.isActive():
                self._overlay.screensaver.stop()

    def displayLeave(self):
        self.display.load(self.interfaceImg + 'nav-seal.svg')
        if not self._overlay.MINI:
            self._overlay.screensaver.start(10000)
