#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
simple.py — the ported Pycrypt cipher dialogs (everything except Enigma, which
gets its own window).  Each is a thin CipherDialog: controls in body(), the
maths in recompute() calling the Ciphers/ engines.  Encrypt/decrypt and the
"break it" buttons live side by side, matching the old Toplevels.
"""

import string

from Pharos.PGui import (PVBoxLayout, PHBoxLayout, PGridLayout, PGroupBox,
                         PLabel, PLineEdit, PCheckBox, PRadioButton, PButtonGroup,
                         PSlider, PSpinBox, PComboBox, PButton, PPlainTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .base import CipherDialog
from Kryptos.Ciphers.common import CipherResult, clean
from Kryptos.Ciphers import Caesar, Transposition, Substitution, Playfair, Vigenere
from Kryptos import analysis


# ══════════════════════════════════════════════════════════════════════════
class ReplaceDialog(CipherDialog):
    title = 'Strip Characters'
    narrative = ('Before frequency analysis the message is reduced to a clean '
                 'letter stream — "the tabula recta has no entry for [spaces, '
                 'punctuation]".')

    _OPTS = [('Spaces', ' '), ('Line feeds', '\n'), ('Carriage returns', '\r'),
             ('Tabs', '\t'), ('Punctuation', string.punctuation),
             ('Digits', string.digits)]

    def body(self, layout):
        box = PGroupBox('Strip which characters?')
        g = PGridLayout(box)
        self._checks = []
        for i, (label, _chars) in enumerate(self._OPTS):
            cb = PCheckBox(label)
            cb.stateChanged.connect(self.recompute)
            g.addWidget(cb, i // 2, i % 2)
            self._checks.append(cb)
        layout.addWidget(box)

    def recompute(self):
        text = self.working_text
        removed = []
        for cb, (label, chars) in zip(self._checks, self._OPTS):
            if cb.isChecked():
                for ch in chars:
                    text = text.replace(ch, '')
                removed.append(label.lower())
        note = f"stripped: {', '.join(removed)}" if removed else 'nothing stripped'
        self.preview = CipherResult(text=text, note=note)
        self._sync()


# ══════════════════════════════════════════════════════════════════════════
class CaesarDialog(CipherDialog):
    title = 'Caesar / Affine'
    narrative = ('c = (p + k) mod 26.  Affine: c = (a·p + b) mod 26, a coprime '
                 'to 26.  25 Caesar keys, 12·26 affine keys — brute force is '
                 'instant.')

    def body(self, layout):
        from Kryptos.widgets.alphabet_strip import AlphabetStrip
        self.strip = AlphabetStrip()
        layout.addWidget(self.strip)

        row = PHBoxLayout()
        self.mode = PComboBox()
        self.mode.addItems(['Caesar encrypt', 'Caesar decrypt',
                            'Caesar brute force', 'Affine encrypt',
                            'Affine decrypt', 'Affine break'])
        self.mode.currentIndexChanged.connect(self._mode_changed)
        row.addWidget(PLabel('Mode')); row.addWidget(self.mode, 1)
        layout.addLayout(row)

        self.krow = PHBoxLayout()
        self.slider = PSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 25); self.slider.setValue(3)
        self.slider.valueChanged.connect(self.recompute)
        self.klabel = PLabel('shift k = 3')
        self.krow.addWidget(self.klabel); self.krow.addWidget(self.slider, 1)
        layout.addLayout(self.krow)

        self.arow = PHBoxLayout()
        self.a = PSpinBox(); self.a.setRange(1, 25); self.a.setValue(5)
        self.b = PSpinBox(); self.b.setRange(0, 25); self.b.setValue(8)
        self.a.valueChanged.connect(self.recompute)
        self.b.valueChanged.connect(self.recompute)
        self.arow.addWidget(PLabel('a')); self.arow.addWidget(self.a)
        self.arow.addWidget(PLabel('b')); self.arow.addWidget(self.b)
        layout.addLayout(self.arow)
        self._mode_changed()

    def _mode_changed(self):
        m = self.mode.currentText()
        is_affine = m.startswith('Affine')
        self.a.setEnabled(is_affine and 'break' not in m)
        self.b.setEnabled(is_affine and 'break' not in m)
        self.slider.setEnabled(m.startswith('Caesar') and 'brute' not in m)
        self.recompute()

    def recompute(self):
        m = self.mode.currentText()
        k = self.slider.value()
        self.klabel.setText(f'shift k = {k}')
        a, b = self.a.value(), self.b.value()
        try:
            if m == 'Caesar encrypt':
                out = Caesar.shift(self.working_text, k)
                self.strip.set_cipher_alphabet(Caesar.shift(string.ascii_uppercase, k))
                note = f'Caesar +{k}'
            elif m == 'Caesar decrypt':
                out = Caesar.unshift(self.working_text, k)
                self.strip.set_cipher_alphabet(Caesar.unshift(string.ascii_uppercase, k))
                note = f'Caesar −{k}'
            elif m == 'Caesar brute force':
                lines = [f'{kk:2d}: {pt[:70]}' for kk, pt in Caesar.brute_force(self.working_text)]
                bk, _, _ = Caesar.best_shift(self.working_text)
                out = '\n'.join(lines)
                note = f'25 shifts — best fit to English is k = {bk}'
            elif m == 'Affine encrypt':
                out = Caesar.affine(self.working_text, a, b)
                note = f'affine a={a} b={b}'
            elif m == 'Affine decrypt':
                out = Caesar.affine_decrypt(self.working_text, a, b)
                note = f'affine⁻¹ a={a} b={b}'
            else:  # Affine break
                cands = Caesar.affine_break(self.working_text, top=5)
                out = '\n'.join(f'a={aa:2d} b={bb:2d}  {pt[:64]}' for aa, bb, pt, _ in cands)
                note = f'best: a={cands[0][0]} b={cands[0][1]} (χ² {cands[0][3]:.1f})'
        except ValueError as e:
            out, note = '', f'⚠ {e}'
        self.preview = CipherResult(text=out, note=note)
        self._sync()


# ══════════════════════════════════════════════════════════════════════════
class TranspositionDialog(CipherDialog):
    title = 'Rail Fence / Scytale'
    narrative = ('Transposition moves the letters around instead of replacing '
                 'them — the rail fence zig-zags; the scytale reads a strip '
                 'wound on a rod.')

    def body(self, layout):
        row = PHBoxLayout()
        self.kind = PComboBox(); self.kind.addItems(['Rail fence', 'Scytale'])
        self.kind.currentIndexChanged.connect(self.recompute)
        self.dirn = PComboBox(); self.dirn.addItems(['Encrypt', 'Decrypt'])
        self.dirn.currentIndexChanged.connect(self.recompute)
        self.n = PSpinBox(); self.n.setRange(2, 12); self.n.setValue(3)
        self.n.valueChanged.connect(self.recompute)
        row.addWidget(self.kind); row.addWidget(self.dirn)
        row.addWidget(PLabel('rails / diameter')); row.addWidget(self.n)
        layout.addLayout(row)

    def recompute(self):
        n = self.n.value()
        rail = self.kind.currentText() == 'Rail fence'
        enc = self.dirn.currentText() == 'Encrypt'
        fn = {(True, True): Transposition.railfence_encrypt,
              (True, False): Transposition.railfence_decrypt,
              (False, True): Transposition.scytale_encrypt,
              (False, False): Transposition.scytale_decrypt}[(rail, enc)]
        out = fn(self.working_text, n)
        note = f"{self.kind.currentText()} {self.dirn.currentText().lower()}, n={n}"
        self.preview = CipherResult(text=out, note=note)
        self._sync()


# ══════════════════════════════════════════════════════════════════════════
class SubstitutionDialog(CipherDialog):
    title = 'Monoalphabetic Substitution'
    narrative = ('26! ≈ 4×10²⁶ keys — but every letter keeps its frequency '
                 '"fingerprint" (al-Kindi).  "Map by frequency" lines the '
                 'cipher letters up against English E T A O I N …')

    def body(self, layout):
        from Kryptos.widgets.alphabet_strip import AlphabetStrip
        self.strip = AlphabetStrip()
        layout.addWidget(self.strip)

        row = PHBoxLayout()
        self.key = PLineEdit(); self.key.setPlaceholderText('keyword alphabet, e.g. PHANTOM')
        self.key.textChanged.connect(self.recompute)
        self.dirn = PComboBox(); self.dirn.addItems(['Encrypt', 'Decrypt'])
        self.dirn.currentIndexChanged.connect(self.recompute)
        row.addWidget(PLabel('Keyword')); row.addWidget(self.key, 1); row.addWidget(self.dirn)
        layout.addLayout(row)

        brow = PHBoxLayout()
        b1 = PButton('Break: map by frequency'); b1.clicked.connect(self._by_freq)
        b2 = PButton('Break: word-pattern dictionary'); b2.clicked.connect(self._by_dict)
        brow.addWidget(b1); brow.addWidget(b2)
        layout.addLayout(brow)
        self._forced = None

    def _by_freq(self):
        self._forced = ('freq', Substitution.solve_by_frequency(self.working_text))
        self.recompute()

    def _by_dict(self):
        self._forced = ('dict', analysis.dictionary_attack(self.working_text))
        self.recompute()

    def recompute(self):
        if self._forced and self._forced[0] == 'freq':
            key = self._forced[1]
            out = key.decrypt(self.working_text)
            self.strip.set_cipher_alphabet(key.mapping)
            self.preview = CipherResult(text=out, key=key,
                note='first guess by frequency order — refine by hand')
            self._sync(); return
        if self._forced and self._forced[0] == 'dict':
            crib = self._forced[1]
            lines = [f'{cw:<12} → {", ".join(cands[:6])}' for cw, cands in
                     sorted(crib.items(), key=lambda kv: -len(kv[0]))[:25]]
            self.preview = CipherResult(text='\n'.join(lines) or '(no pattern matches)',
                note=f'{len(crib)} cipher words have dictionary matches by pattern')
            self._sync(); return

        kw = clean(self.key.text())
        key = Substitution.keyword_alphabet(kw) if kw else Substitution.SubstitutionKey()
        self.strip.set_cipher_alphabet(key.mapping)
        if self.dirn.currentText() == 'Encrypt':
            out = key.encrypt(self.working_text)
        else:
            out = key.decrypt(self.working_text)
        self.preview = CipherResult(text=out, key=key,
            note=f'keyword {kw!r} → cipher alphabet {key.mapping}' if kw else 'identity')
        self._sync()

    def body_reset(self):
        self._forced = None


# ══════════════════════════════════════════════════════════════════════════
class PlayfairDialog(CipherDialog):
    title = 'Playfair'
    narrative = ('Wheatstone 1854 — the first cipher on letter *pairs*.  '
                 'A 5×5 keyed square, I/J share a cell; row → right, '
                 'column → down, rectangle → swap columns.')

    def body(self, layout):
        row = PHBoxLayout()
        self.key = PLineEdit(); self.key.setPlaceholderText('keyword, e.g. PLAYFAIR EXAMPLE')
        self.key.textChanged.connect(self.recompute)
        self.dirn = PComboBox(); self.dirn.addItems(['Encrypt', 'Decrypt'])
        self.dirn.currentIndexChanged.connect(self.recompute)
        row.addWidget(PLabel('Keyword')); row.addWidget(self.key, 1); row.addWidget(self.dirn)
        layout.addLayout(row)

        self.square = PLabel()
        self.square.setFont(QFont('Ubuntu Mono', 13))
        self.square.setStyleSheet('color:#0ff; background:#0d2020; padding:6px;')
        layout.addWidget(self.square)

    def recompute(self):
        kw = self.key.text() or 'MONARCHY'
        sq = Playfair.build_square(kw)
        self.square.setText('\n'.join('  '.join(r) for r in sq))
        fn = Playfair.encrypt if self.dirn.currentText() == 'Encrypt' else Playfair.decrypt
        out = fn(self.working_text, kw)
        # readable in 5-groups
        grouped = ' '.join(out[i:i + 5] for i in range(0, len(out), 5))
        self.preview = CipherResult(text=grouped,
            note=f'Playfair {self.dirn.currentText().lower()}, key {clean(kw)!r}')
        self._sync()


# ══════════════════════════════════════════════════════════════════════════
class PigpenDialog(CipherDialog):
    title = 'Pigpen'
    narrative = ('A monoalphabetic substitution that swaps letters for grid '
                 'fragments — cryptographically a Caesar with no shift, but a '
                 'classic classroom cipher.  Rendered here in a pigpen font.')

    def body(self, layout):
        self.view = PLabel()
        self.view.setWordWrap(True)
        self.view.setStyleSheet('color:#cfe; background:#0d2020; padding:8px;')
        try:
            from PyQt6.QtGui import QFontDatabase
            import os
            fp = os.path.join(os.path.dirname(__file__), '..', 'TheCodeBook',
                              'fonts', 'pigpen-mono.ttf')
            fid = QFontDatabase.addApplicationFont(fp)
            fam = QFontDatabase.applicationFontFamilies(fid)
            self.view.setFont(QFont(fam[0] if fam else 'monospace', 20))
        except Exception:
            self.view.setFont(QFont('monospace', 20))
        layout.addWidget(self.view)

    def recompute(self):
        s = clean(self.working_text)
        self.view.setText(s)
        self.preview = CipherResult(text=s, note='pigpen — a symbol per letter (font substitution)')
        self._sync()


# ══════════════════════════════════════════════════════════════════════════
class VigenereDialog(CipherDialog):
    title = 'Vigenère'
    narrative = ('A repeating-key Caesar — "le chiffre indéchiffrable" for 300 '
                 'years until Babbage & Kasiski: repeated strings in the '
                 'ciphertext leak the key length.')

    def body(self, layout):
        row = PHBoxLayout()
        self.key = PLineEdit(); self.key.setPlaceholderText('keyword, e.g. LEMON')
        self.key.textChanged.connect(self.recompute)
        self.dirn = PComboBox(); self.dirn.addItems(['Encrypt', 'Decrypt'])
        self.dirn.currentIndexChanged.connect(self.recompute)
        row.addWidget(PLabel('Keyword')); row.addWidget(self.key, 1); row.addWidget(self.dirn)
        layout.addLayout(row)

        b = PButton('Break: Kasiski + Index of Coincidence')
        b.clicked.connect(self._break)
        layout.addWidget(b)
        self._broke = None

    def _break(self):
        self._broke = analysis.break_vigenere(self.working_text)
        self.recompute()

    def recompute(self):
        if self._broke:
            r = self._broke
            self.preview = CipherResult(
                text=r['plaintext'],
                note=(f"Kasiski period {r['period']}, recovered key {r['key']!r}, "
                      f"column IoC {r['ioc']:.3f} (English ≈ 0.067)"))
            self._sync(); return
        kw = clean(self.key.text())
        if not kw:
            self.preview = CipherResult(text='', note='enter a keyword')
            self._sync(); return
        fn = Vigenere.encrypt if self.dirn.currentText() == 'Encrypt' else Vigenere.decrypt
        out = fn(self.working_text, kw)
        self.preview = CipherResult(text=out,
            note=f'Vigenère {self.dirn.currentText().lower()}, key {kw!r}')
        self._sync()
