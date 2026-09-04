#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
enigma_dialog.py — the ported Pycrypt `Enigma` Toplevel (was a bare `pass`).

Configures the machine (rotor order / ring settings / start positions /
reflector / plugboard), encrypts or decrypts the working text through
`Ciphers.Enigma.Enigma`, and opens the signal-path visualiser
(`enigma_view.EnigmaVisualiser`) for the current settings + text.

Also shows "the strength of Enigma" — the key-space counts the CD-ROM lesson
asks pupils to work out (`analysis.enigma_keyspace`).
"""

from Pharos.PGui import (PHBoxLayout, PVBoxLayout, PLabel, PLineEdit, PComboBox,
                         PButton, PGroupBox)
from PyQt6.QtGui import QFont

from .base import CipherDialog
from Kryptos.Ciphers.common import CipherResult
from Kryptos.Ciphers.Enigma import Enigma
from Kryptos import analysis

_ROTOR_SETS = ['I-II-III', 'I-II-IV', 'II-III-IV', 'III-IV-V', 'I-III-V', 'II-IV-V']


class EnigmaDialog(CipherDialog):
    title = 'Enigma'
    narrative = ('A keyboard, a lampboard, and a scrambler that steps after '
                 'every letter — so AAAAA does not give AAAAA.  The strength is '
                 'the *setting*, not the machine: ~1.6×10²⁰ keys.')

    def body(self, layout):
        r1 = PHBoxLayout()
        self.rotors = PComboBox(); self.rotors.addItems(_ROTOR_SETS)
        self.refl = PComboBox(); self.refl.addItems(['B', 'C'])
        self.pos = PLineEdit('AAA'); self.pos.setMaxLength(3); self.pos.setFixedWidth(60)
        self.ring = PLineEdit('AAA'); self.ring.setMaxLength(3); self.ring.setFixedWidth(60)
        for lab, w in (('Rotors', self.rotors), ('Reflector', self.refl),
                       ('Start', self.pos), ('Ring', self.ring)):
            r1.addWidget(PLabel(lab)); r1.addWidget(w)
        layout.addLayout(r1)

        r2 = PHBoxLayout()
        self.plug = PLineEdit(''); self.plug.setPlaceholderText('plugboard: AB CD EF …')
        self.dirn = PComboBox(); self.dirn.addItems(['Encrypt', 'Decrypt'])
        r2.addWidget(PLabel('Plugboard')); r2.addWidget(self.plug, 1)
        r2.addWidget(self.dirn)
        layout.addLayout(r2)

        for w in (self.rotors, self.refl, self.dirn):
            w.currentIndexChanged.connect(self.recompute)
        for w in (self.pos, self.ring, self.plug):
            w.textChanged.connect(self.recompute)

        r3 = PHBoxLayout()
        viz = PButton('▶  Open signal-path visualiser')
        viz.clicked.connect(self._open_viz)
        strg = PButton('Strength of Enigma …')
        strg.clicked.connect(self._show_strength)
        r3.addWidget(viz); r3.addWidget(strg)
        layout.addLayout(r3)

        self._strength = PLabel('')
        self._strength.setWordWrap(True)
        self._strength.setFont(QFont('Ubuntu Mono', 8))
        self._strength.setStyleSheet('color:#5c8;')
        layout.addWidget(self._strength)

    def _machine(self):
        return Enigma(rotors=self.rotors.currentText().split('-'),
                      positions=(self.pos.text().upper() + 'AAA')[:3],
                      rings=(self.ring.text().upper() + 'AAA')[:3],
                      reflector=self.refl.currentText(),
                      plugboard=self.plug.text().upper())

    def recompute(self):
        try:
            out = self._machine().encrypt(self.working_text)
        except (KeyError, ValueError) as e:
            self.preview = CipherResult(text='', note=f'⚠ {e}')
            self._sync(); return
        grouped = ' '.join(out[i:i + 5] for i in range(0, len(out), 5))
        d = self.dirn.currentText().lower()
        self.preview = CipherResult(text=grouped,
            note=(f'Enigma {d}: rotors {self.rotors.currentText()}, '
                  f'reflector {self.refl.currentText()}, start {self.pos.text().upper()}, '
                  f'ring {self.ring.text().upper()} — reciprocal, so the same '
                  f'settings {d} this back.'))
        self._sync()

    def _show_strength(self):
        ks = analysis.enigma_keyspace()
        self._strength.setText(
            f"rotor order (3 of 5): {ks['rotor_order']}     "
            f"start positions: 26³ = {ks['rotor_positions']}\n"
            f"plugboard (10 leads): {ks['plugboard']:,}\n"
            f"total: {ks['total']:.3e}     optimum leads: {ks['optimum_leads']}\n"
            f"{ks['note']}")

    def _open_viz(self):
        from Kryptos.enigma_view import EnigmaWindow
        self._viz = EnigmaWindow()          # its own top-level window
        self._viz.rotors.setCurrentText(self.rotors.currentText())
        self._viz.refl.setCurrentText(self.refl.currentText())
        self._viz.pos.setText(self.pos.text().upper())
        self._viz.ring.setText(self.ring.text().upper())
        self._viz.plug.setText(self.plug.text().upper())
        self._viz.msg.setText(self.working_text[:120] or 'AAAAA')
        self._viz._load()
        self._viz.show()
        self._viz.raise_()
