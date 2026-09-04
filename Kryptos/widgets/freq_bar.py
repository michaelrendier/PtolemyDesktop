#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
freq_bar.py — the frequency bar chart.

The Code Book teachers' notes lean on bar charts hard: "build students'
abilities to interpret information from bar-charts" (y9-fatn.doc), and the
CD-ROM's frequency-analysis tool "help[s] pupils to crack codes by plotting
frequency charts".  This is that chart, as a PGui widget.

Shows the 26 letters A-Z, a bar per letter for the working text, and (optional)
a faint overlay of the English reference distribution so the "fingerprint"
comparison al-Kindi described is visible at a glance.
"""

from Pharos.PGui import PWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont

from Kryptos.Ciphers.common import ALPHABET, ENGLISH_FREQ

_BG      = QColor('#050d0d')
_BAR     = QColor('#00d0d0')
_BAR_TOP = QColor('#00ffff')
_REF     = QColor(255, 170, 0, 90)
_AXIS    = QColor(0, 255, 255, 60)
_TEXT    = QColor('#8fdede')


class FreqBar(PWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {ch: 0.0 for ch in ALPHABET}
        self._ref = None
        self.setMinimumHeight(150)
        self._title = 'Letter frequency (%)'

    def set_data(self, freqs: dict, title: str = None):
        """freqs: {letter: percent}."""
        self._data = {ch: float(freqs.get(ch, 0.0)) for ch in ALPHABET}
        if title:
            self._title = title
        self.update()

    def show_english_reference(self, on: bool = True):
        self._ref = ENGLISH_FREQ if on else None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _BG)

        pad_l, pad_b, pad_t = 8, 18, 20
        plot_h = h - pad_b - pad_t
        plot_w = w - pad_l * 2
        cell = plot_w / len(ALPHABET)

        peak = max(list(self._data.values()) +
                   (list(self._ref.values()) if self._ref else [0]) + [1.0])

        p.setPen(QPen(_TEXT))
        p.setFont(QFont('Ubuntu Mono', 8))
        p.drawText(pad_l, 12, self._title)

        p.setPen(QPen(_AXIS))
        p.drawLine(pad_l, h - pad_b, w - pad_l, h - pad_b)

        for i, ch in enumerate(ALPHABET):
            x = pad_l + i * cell
            val = self._data[ch]
            bar_h = plot_h * (val / peak)
            r = QRectF(x + cell * 0.18, h - pad_b - bar_h, cell * 0.64, bar_h)
            g = QBrush(_BAR)
            p.fillRect(r, g)
            p.setPen(QPen(_BAR_TOP))
            p.drawLine(int(r.left()), int(r.top()), int(r.right()), int(r.top()))

            if self._ref:
                ref_h = plot_h * (self._ref[ch] / peak)
                p.setPen(QPen(_REF, 2))
                y = h - pad_b - ref_h
                p.drawLine(int(x + cell * 0.08), int(y),
                           int(x + cell * 0.92), int(y))

            p.setPen(QPen(_TEXT))
            p.drawText(QRectF(x, h - pad_b + 2, cell, pad_b - 2),
                       Qt.AlignmentFlag.AlignHCenter, ch)
        p.end()
