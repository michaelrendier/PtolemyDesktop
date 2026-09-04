#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
alphabet_strip.py — a plain-alphabet / cipher-alphabet pair, drawn as two
aligned monospace rows.

"Cryptographers deal in terms of the original or plain alphabet and the cipher
 alphabet.  When they are placed next to each other, then the shift becomes
 apparent."   — The Code Book, CD-ROM Overview

Used by the Caesar dialog (top = plain, bottom = shifted, live) and the
monoalphabetic dialog (bottom = the substitution being built).  Ported from the
coloured ABC.../ABC... labels in the old Pycrypt Caesar and Scrabble dialogs
(blue = original, red = encoded).
"""

from Pharos.PGui import PWidget
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

from Kryptos.Ciphers.common import ALPHABET

_BG      = QColor('#050d0d')
_PLAIN   = QColor('#4aa3ff')   # blue — the old build's "original" colour
_CIPHER  = QColor('#ff5533')   # red  — the old build's "encoded" colour
_DIM     = QColor('#2b3a3a')


class AlphabetStrip(PWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cipher = ALPHABET
        self._highlight = set()          # indices to ring
        self.setMinimumHeight(46)
        self.setMaximumHeight(60)

    def set_cipher_alphabet(self, cipher: str):
        self._cipher = (cipher.upper() + '.' * 26)[:26]
        self.update()

    def set_highlight(self, indices):
        self._highlight = set(indices)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, _BG)
        cell = w / 26
        f = QFont('Ubuntu Mono', 10)
        f.setBold(True)
        p.setFont(f)

        for i in range(26):
            x = i * cell
            if i in self._highlight:
                p.setPen(QPen(QColor('#00ffff'), 1))
                p.drawRect(QRectF(x + 1, 1, cell - 2, h - 2))
            p.setPen(QPen(_PLAIN))
            p.drawText(QRectF(x, 2, cell, h / 2 - 2),
                       Qt.AlignmentFlag.AlignCenter, ALPHABET[i])
            p.setPen(QPen(_CIPHER if self._cipher[i] != '.' else _DIM))
            p.drawText(QRectF(x, h / 2, cell, h / 2 - 2),
                       Qt.AlignmentFlag.AlignCenter, self._cipher[i])
        p.end()
