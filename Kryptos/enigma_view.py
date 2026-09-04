#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
enigma_view.py — the Pycrypt showcase: the Enigma signal path made visible.

Cody's design, in nes-viewport terms:

    map      = a subdued black-and-white photo of an open Enigma
               (TheCodeBook/images/enigma_map.png)
    viewport = exactly the same size as the map  →  the SCREEN-LOCKED
               archetype: no panning, no scrollbars, nothing clips
    menu     = the SVG-style Enigma drawn ON TOP, pixel-registered to the
               photo — the interactive layer the arrow keys move a cursor
               through

One function behind it all: `Ciphers.Enigma.Enigma.trace_path(letter)` — the
true, historically accurate traversal `key → plugboard → ETW → III → II → I →
reflector → I → II → III → ETW → plugboard → lamp`.  The overlay draws ONLY
what that returns.

Runs inside the Pycrypt face, or standalone:

    PTOLEMY_PHAROS=0 python Kryptos/enigma_view.py
"""

import os
import sys

from Pharos.PGui import (PWidget, PMainWindow, PVBoxLayout, PHBoxLayout, PLabel,
                         PComboBox, PLineEdit, PButton, PSlider)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (QPainter, QPixmap, QColor, QPen, QBrush, QFont,
                         QPainterPath)

from Kryptos.Ciphers.Enigma import Enigma, ALPHABET

_HERE = os.path.dirname(os.path.abspath(__file__))
_MAP  = os.path.join(_HERE, 'TheCodeBook', 'images', 'enigma_map.png')

# QWERTZ — the German layout the real Enigma lamp/key boards use
QWERTZ = ['QWERTZUIO', 'ASDFGHJK', 'PYXCVBNML']

# colours
C_FWD   = QColor('#00e5ff')      # key → reflector
C_RET   = QColor('#ffb000')      # reflector → lamp
C_NODE  = QColor(0, 229, 255, 70)
C_LADDER = QColor(150, 170, 190, 55)
C_WIRE  = QColor(255, 176, 0, 120)
C_SEL   = QColor('#00ff88')
C_LAMP  = QColor('#ffe14d')
C_HUD   = QColor('#bfe9e9')


class EnigmaVisualiser(PWidget):
    """Screen-locked: widget size == map size, three layers composited in place."""

    # menu elements the arrow keys cycle through
    MENU = ['letter', 'rotorL', 'rotorM', 'rotorR', 'reflector', 'plugboard', 'play']

    def __init__(self, rotors=('I', 'II', 'III'), positions='AAA', rings='AAA',
                 reflector='B', plugboard='', parent=None):
        super().__init__(parent)
        self._pix = QPixmap(_MAP) if os.path.isfile(_MAP) else QPixmap(918, 1062)
        if self._pix.isNull():
            self._pix = QPixmap(918, 1062)
            self._pix.fill(QColor('#20242a'))
        self.W, self.H = self._pix.width(), self._pix.height()
        self.setFixedSize(self.W, self.H)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.cfg = dict(rotors=list(rotors), positions=positions, rings=rings,
                        reflector=reflector, plugboard=plugboard)
        self._machine = None
        self._paths = []          # list[Path] for the text typed so far
        self._idx = -1            # which keypress is showing
        self._marker = 0.0        # 0..1 along the current polyline
        self._sel = 0             # index into MENU
        self._letter = 'A'
        self._build_geometry()
        self._reset_machine()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._playing = False
        self._speed = 60          # ms per marker step

    # ── geometry: map every contact of every component to a screen point ─────
    def _build_geometry(self):
        W, H = self.W, self.H
        self._pts = {}

        def board(rows, y0, dy, x0, dx):
            pos = {}
            for r, row in enumerate(rows):
                y = y0 + r * dy
                indent = (9 - len(row)) * dx / 2
                for c, ch in enumerate(row):
                    pos[ch] = QPointF(x0 + indent + c * dx, y)
            return pos

        self._lamp_xy = board(QWERTZ, H * 0.365, H * 0.052, W * 0.20, W * 0.074)
        self._key_xy  = board(QWERTZ, H * 0.545, H * 0.060, W * 0.20, W * 0.074)

        # rotor / reflector contact ladders — 26 contacts top→bottom
        self._ladder_x = {'reflector': W * 0.20,
                          'III': W * 0.34, 'II': W * 0.47, 'I': W * 0.60,
                          'ETW': W * 0.73}
        self._ladder_y0 = H * 0.045
        self._ladder_dy = (H * 0.28 - self._ladder_y0) / 25.0

        # plugboard sockets along the bottom
        self._plug_x0, self._plug_dx = W * 0.12, (W * 0.78 - W * 0.12) / 25.0
        self._plug_y = H * 0.855

    def _ladder_pt(self, name, contact, leg='forward'):
        # forward leg hugs the left of the ladder, return leg the right, so the
        # two directions don't overprint each other
        dx = -5 if leg == 'forward' else 5
        return QPointF(self._ladder_x[name] + dx,
                       self._ladder_y0 + contact * self._ladder_dy)

    def _plug_pt(self, contact):
        return QPointF(self._plug_x0 + contact * self._plug_dx, self._plug_y)

    def _hop_point(self, hop, which):
        """Screen point for a hop's input ('in') or output ('out') contact."""
        c = hop.contact_in if which == 'in' else hop.contact_out
        comp = hop.component
        if comp == 'keyboard':
            return self._key_xy[ALPHABET[c]]
        if comp == 'lamp':
            return self._lamp_xy[ALPHABET[c]]
        if comp == 'plugboard':
            return self._plug_pt(c)
        if comp == 'ETW':
            return self._ladder_pt('ETW', c, hop.leg)
        if comp == 'reflector':
            return self._ladder_pt('reflector', c, hop.leg)
        if comp == 'rotor':
            return self._ladder_pt(hop.label, c, hop.leg)
        return QPointF(self.W / 2, self.H / 2)

    # ── machine / typing ───────────────────────────────────────────────────
    def _reset_machine(self):
        self._machine = Enigma(rotors=self.cfg['rotors'],
                               positions=self.cfg['positions'],
                               rings=self.cfg['rings'],
                               reflector=self.cfg['reflector'],
                               plugboard=self.cfg['plugboard'])
        self._paths = []
        self._idx = -1
        self._marker = 0.0
        self.update()

    def set_text(self, text: str):
        self._reset_machine()
        self._pending = [c for c in text.upper() if c in ALPHABET]

    def type_next(self):
        if not getattr(self, '_pending', None):
            return False
        ch = self._pending.pop(0)
        self._paths.append(self._machine.trace_path(ch))
        self._idx = len(self._paths) - 1
        self._marker = 0.0
        self.update()
        return True

    def step_one(self, letter=None):
        letter = (letter or self._letter).upper()
        if letter not in ALPHABET:
            return
        self._paths.append(self._machine.trace_path(letter))
        self._idx = len(self._paths) - 1
        self._marker = 0.0
        self.update()

    def play(self):
        self._playing = not self._playing
        if self._playing:
            self._timer.start(self._speed)
        else:
            self._timer.stop()

    def _tick(self):
        self._marker += 0.06
        if self._marker >= 1.0:
            self._marker = 0.0
            if not self.type_next():
                self._playing = False
                self._timer.stop()
        self.update()

    def set_speed(self, ms):
        self._speed = ms
        if self._playing:
            self._timer.start(ms)

    # ── the current polyline (screen points), from trace_path only ──────────
    def _polyline(self):
        if not (0 <= self._idx < len(self._paths)):
            return [], []
        path = self._paths[self._idx]
        pts, legs = [], []
        for h in path.hops:
            pts.append(self._hop_point(h, 'in'))
            legs.append(h.leg)
        pts.append(self._hop_point(path.hops[-1], 'out'))
        legs.append(path.hops[-1].leg)
        return pts, legs

    # ── navigation: arrow keys move the cursor over the menu, not the map ───
    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key.Key_Right, Qt.Key.Key_Down):
            self._sel = (self._sel + 1) % len(self.MENU)
        elif k in (Qt.Key.Key_Left, Qt.Key.Key_Up):
            self._sel = (self._sel - 1) % len(self.MENU)
        elif k in (Qt.Key.Key_Home,):
            self._sel = 0
        elif k in (Qt.Key.Key_End,):
            self._sel = len(self.MENU) - 1
        elif k in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._actuate()
        elif Qt.Key.Key_A <= k <= Qt.Key.Key_Z:
            self._letter = chr(k)
            self.step_one(self._letter)
        else:
            super().keyPressEvent(e)
            return
        self.update()

    def _actuate(self):
        el = self.MENU[self._sel]
        if el == 'letter':
            self.step_one(self._letter)
        elif el in ('rotorL', 'rotorM', 'rotorR'):
            i = {'rotorL': 0, 'rotorM': 1, 'rotorR': 2}[el]
            rot = [self._machine.rotor1, self._machine.rotor2, self._machine.rotor3][i]
            rot.step()
            self.cfg['positions'] = self._machine.windows
        elif el == 'reflector':
            self.cfg['reflector'] = 'C' if self.cfg['reflector'] == 'B' else 'B'
            self._reset_machine()
        elif el == 'play':
            self.play()
        self.update()

    # ── paint: 3 layers ────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # layer 1 — map
        p.drawPixmap(0, 0, self._pix)
        # layer 2 — frame (viewport == map, but be explicit)
        p.setClipRect(0, 0, self.W, self.H)
        # layer 3 — menu / overlay
        self._draw_ladders(p)
        self._draw_boards(p)
        self._draw_path(p)
        self._draw_hud(p)
        p.end()

    def _draw_ladders(self, p):
        p.setPen(QPen(C_LADDER, 1))
        for name in ('reflector', 'III', 'II', 'I', 'ETW'):
            x = self._ladder_x[name]
            p.drawLine(QPointF(x, self._ladder_y0),
                       QPointF(x, self._ladder_y0 + 25 * self._ladder_dy))
            for c in range(26):
                pt = self._ladder_pt(name, c)
                p.setBrush(QBrush(C_NODE))
                p.drawEllipse(pt, 2.2, 2.2)
            p.setPen(QPen(C_HUD))
            p.setFont(QFont('Ubuntu Mono', 8))
            label = {'reflector': 'UKW', 'ETW': 'ETW'}.get(name, name)
            p.drawText(QPointF(x - 12, self._ladder_y0 - 6), label)
            p.setPen(QPen(C_LADDER, 1))
        # rotor window letters
        if self._machine:
            p.setPen(QPen(C_HUD)); p.setFont(QFont('Ubuntu Mono', 11, QFont.Weight.Bold))
            for name, ch in zip(('III', 'II', 'I'), reversed(self._machine.windows)):
                x = self._ladder_x[name]
                p.drawText(QRectF(x - 12, self._ladder_y0 + 26 * self._ladder_dy, 24, 16),
                           Qt.AlignmentFlag.AlignCenter, ch)

    def _draw_boards(self, p):
        p.setFont(QFont('Ubuntu Mono', 8))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for xy in (self._lamp_xy, self._key_xy):
            for ch, pt in xy.items():
                p.setPen(QPen(QColor(0, 229, 255, 55)))
                p.drawEllipse(pt, 7, 7)
        for c in range(26):
            p.setBrush(QBrush(C_NODE)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(self._plug_pt(c), 2.6, 2.6)

    def _draw_path(self, p):
        pts, legs = self._polyline()
        if len(pts) < 2:
            return
        for i in range(len(pts) - 1):
            col = C_FWD if legs[i] == 'forward' else C_RET
            pen = QPen(col, 2.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(pts[i], pts[i + 1])

        # rotor internal wire in use (faint), per rotor hop
        path = self._paths[self._idx]
        p.setPen(QPen(C_WIRE, 1.4))
        for h in path.hops:
            if h.component == 'rotor' and h.internal_in is not None:
                a = self._ladder_pt(h.label, h.internal_in)
                b = self._ladder_pt(h.label, h.internal_out)
                p.drawLine(a, b)

        # marker dot travelling the polyline
        seg = self._marker * (len(pts) - 1)
        i = min(int(seg), len(pts) - 2)
        t = seg - i
        mp = QPointF(pts[i].x() + t * (pts[i + 1].x() - pts[i].x()),
                     pts[i].y() + t * (pts[i + 1].y() - pts[i].y()))
        p.setBrush(QBrush(QColor('#ffffff'))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(mp, 4, 4)

        # lit lamp
        lamp = path.lamp
        if lamp in self._lamp_xy:
            p.setBrush(QBrush(C_LAMP)); p.setPen(QPen(QColor('#fff6c0'), 2))
            p.drawEllipse(self._lamp_xy[lamp], 11, 11)
            p.setPen(QPen(QColor('#1a1400'))); p.setFont(QFont('Ubuntu Mono', 9, QFont.Weight.Bold))
            p.drawText(QRectF(self._lamp_xy[lamp].x() - 8, self._lamp_xy[lamp].y() - 8, 16, 16),
                       Qt.AlignmentFlag.AlignCenter, lamp)

    def _draw_hud(self, p):
        p.setPen(QPen(C_HUD)); p.setFont(QFont('Ubuntu Mono', 9))
        lines = [f"rotors {'-'.join(self.cfg['rotors'])}   reflector {self.cfg['reflector']}",
                 f"windows {self._machine.windows if self._machine else '---'}"
                 f"   ring {self.cfg['rings']}   plug [{self.cfg['plugboard'] or '—'}]"]
        if 0 <= self._idx < len(self._paths):
            pa = self._paths[self._idx]
            chain = ' '.join(h.letter_in for h in pa.hops) + f' → {pa.lamp}'
            stp = '+'.join(pa.stepped) + ('  DOUBLE-STEP' if pa.double_step else '')
            lines += [f"key {pa.letter} → lamp {pa.lamp}   ({self._idx + 1}/{len(self._paths)})",
                      f"stepped: {stp}", chain]
        for i, ln in enumerate(lines):
            p.drawText(10, self.H - 74 + i * 14, ln)
        # selection cursor
        p.setPen(QPen(C_SEL)); p.setFont(QFont('Ubuntu Mono', 9, QFont.Weight.Bold))
        p.drawText(10, 16, f"◄ ► menu: [{self.MENU[self._sel]}]   "
                           f"type a letter to send it   Enter = actuate")


# ── standalone window ──────────────────────────────────────────────────────
class EnigmaWindow(PMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Pycrypt — Enigma signal path')
        w = PWidget(); lay = PVBoxLayout(w)

        cfg = PHBoxLayout()
        self.rotors = PComboBox(); self.rotors.addItems(
            ['I-II-III', 'I-II-IV', 'II-IV-V', 'III-IV-V', 'I-III-V'])
        self.refl = PComboBox(); self.refl.addItems(['B', 'C'])
        self.pos = PLineEdit('AAA'); self.pos.setMaxLength(3); self.pos.setFixedWidth(56)
        self.ring = PLineEdit('AAA'); self.ring.setMaxLength(3); self.ring.setFixedWidth(56)
        self.plug = PLineEdit(''); self.plug.setPlaceholderText('AB CD EF')
        self.msg = PLineEdit('AAAAA')
        for lab, wdg in (('rotors', self.rotors), ('reflector', self.refl),
                         ('pos', self.pos), ('ring', self.ring),
                         ('plug', self.plug), ('text', self.msg)):
            cfg.addWidget(PLabel(lab)); cfg.addWidget(wdg)
        go = PButton('Load'); go.clicked.connect(self._load)
        cfg.addWidget(go)
        lay.addLayout(cfg)

        self.view = EnigmaVisualiser()
        lay.addWidget(self.view)

        ctl = PHBoxLayout()
        b_step = PButton('Type next ▸'); b_step.clicked.connect(self.view.type_next)
        b_play = PButton('Play ⏵'); b_play.clicked.connect(self.view.play)
        b_reset = PButton('Reset ⟲'); b_reset.clicked.connect(self._load)
        sp = PSlider(Qt.Orientation.Horizontal); sp.setRange(15, 200); sp.setValue(60)
        sp.valueChanged.connect(self.view.set_speed)
        for x in (b_step, b_play, b_reset, PLabel('speed'), sp):
            ctl.addWidget(x)
        lay.addLayout(ctl)

        self.setCentralWidget(w)
        self._load()

    def _load(self):
        self.view.cfg.update(
            rotors=self.rotors.currentText().split('-'),
            reflector=self.refl.currentText(),
            positions=(self.pos.text().upper() + 'AAA')[:3],
            rings=(self.ring.text().upper() + 'AAA')[:3],
            plugboard=self.plug.text().upper())
        self.view.set_text(self.msg.text())
        self.view.type_next()
        self.view.setFocus()


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = EnigmaWindow()
    win.show()
    sys.exit(app.exec())
