#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Pycrypt.py — the Kryptos face: Cody's Code Book cryptography workbench, ported
from the original Tkinter build (Ptolemy2/Kryptos/TheCodeBook/Pycrypt.py) to
PyQt6 / Pharos.PGui.

Faithful to the old layout:

    ┌─ Working Text ─┐┌─ Change Text ─┐┌─ Text Statistics ─┐
    │  the message   ││  cipher out /  ││  frequency bars +  │
    │  you work on   ││  break results ││  al-Kindi analysis │
    └────────────────┘└────────────────┘└────────────────────┘
    [⏻] │ Strip │ RailFence Scytale │ Caesar Pigpen Mono │
        │ Playfair Vigenère Enigma │ Freq Digraph VowelTrowel

Power on → tool buttons enable (old `startwork`).  A tool opens its dialog on
the Working Text; OK drops the result into Change Text; **Commit** promotes
Change → Working and re-runs the statistics.  Power off → revert to the
original text (old `stopwork`).

Standalone:  PTOLEMY_PHAROS=0 python Kryptos/Pycrypt.py
"""

import os
import sys

from Pharos.PGui import (PMainWindow, PWidget, PVBoxLayout, PHBoxLayout,
                         PSplitter, PPlainTextEdit, PLabel, PToolBar, PButton,
                         PStatusBar, PFileDialog, PMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QAction, QFontDatabase

try:
    from Pharos.PtolFace import PtolFace
except Exception:                                   # standalone without Pharos tree
    class PtolFace:
        def ptol_init(self): self._ptol_timers = []

from Kryptos import analysis
from Kryptos.Ciphers.common import clean
from Kryptos.widgets.freq_bar import FreqBar
from Kryptos.dialogs.simple import (ReplaceDialog, CaesarDialog,
                                    TranspositionDialog, SubstitutionDialog,
                                    PlayfairDialog, PigpenDialog, VigenereDialog)
from Kryptos.dialogs.enigma_dialog import EnigmaDialog

_HERE = os.path.dirname(os.path.abspath(__file__))
_IMG  = os.path.join(_HERE, 'TheCodeBook', 'images')
_FONTS = os.path.join(_HERE, 'TheCodeBook', 'fonts')

_STYLE = (
    "QMainWindow,QWidget { background:#050d0d; color:#cfe; }"
    "QPlainTextEdit { background:#0d2020; color:#cfe; border:1px solid #0a6b7a; }"
    "QToolBar { background:#0a1414; border-bottom:1px solid #0a6b7a; spacing:2px; }"
    "QToolButton { background:#0a1414; border:1px solid #0a6b7a; padding:2px; }"
    "QToolButton:hover { border-color:#0ff; }"
    "QToolButton:disabled { border-color:#233; }"
    "QToolButton:checked { background:#062; border-color:#0f8; }"
    "QStatusBar { background:#0a1414; color:#8fdede; }"
    "QLabel { color:#8fdede; }"
    "QMenuBar { background:#0a1414; color:#cfe; }"
    "QMenuBar::item:selected { background:#062; }"
    "QMenu { background:#0a1414; color:#cfe; }"
)


def _icon(name):
    p = os.path.join(_IMG, name)
    return QIcon(p) if os.path.isfile(p) else QIcon()


class Pycrypt(PMainWindow, PtolFace):

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            PtolFace.ptol_init(self)
        except Exception:
            pass
        self.Ptolemy = parent
        self.original_text = ''
        self._powered = False

        for fn in ('pigpen-mono.ttf', 'rendier-glyph-mono.ttf', 'rendier-script-mono.ttf'):
            fp = os.path.join(_FONTS, fn)
            if os.path.isfile(fp):
                QFontDatabase.addApplicationFont(fp)

        self.setWindowTitle('Ptolemy · Kryptos · The Code Book')
        self.setStyleSheet(_STYLE)
        self.resize(1180, 720)
        self._build_menu()
        self._build_body()
        self._build_toolbar()
        self.status = PStatusBar(); self.setStatusBar(self.status)
        self.status.showMessage('Load or type a message, then press ⏻ to power on.')
        self._set_tools_enabled(False)

    # ── layout ─────────────────────────────────────────────────────────────
    def _build_body(self):
        central = PWidget(); root = PVBoxLayout(central)
        split = PSplitter(Qt.Orientation.Horizontal)

        self.working = self._pane('Working Text', '#cfe')
        self.change = self._pane('Change Text', '#9f9', read_only=True)

        stats_wrap = PWidget(); sv = PVBoxLayout(stats_wrap)
        sv.setContentsMargins(0, 0, 0, 0)
        sv.addWidget(PLabel('Text Statistics'))
        self.freqbar = FreqBar()
        sv.addWidget(self.freqbar, 1)
        self.stats = PPlainTextEdit(); self.stats.setReadOnly(True)
        self.stats.setFont(QFont('Ubuntu Mono', 9))
        sv.addWidget(self.stats, 2)

        for w in (self._wrap('Working Text', self.working),
                  self._wrap('Change Text', self.change), stats_wrap):
            split.addWidget(w)
        split.setSizes([420, 420, 340])
        root.addWidget(split)
        self.setCentralWidget(central)
        self.working.textChanged.connect(self._on_working_changed)

    def _pane(self, _title, colour, read_only=False):
        te = PPlainTextEdit()
        te.setReadOnly(read_only)
        te.setFont(QFont('Ubuntu Mono', 10))
        te.setStyleSheet(f'color:{colour};')
        return te

    def _wrap(self, title, widget):
        w = PWidget(); v = PVBoxLayout(w); v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(PLabel(title)); v.addWidget(widget)
        return w

    # ── menu ───────────────────────────────────────────────────────────────
    def _build_menu(self):
        m = self.menuBar().addMenu('File')
        for label, slot, key in (('New', self._new, 'Ctrl+N'),
                                 ('Open…', self._open, 'Ctrl+O'),
                                 ('Save…', self._save, 'Ctrl+S'),
                                 (None, None, None),
                                 ('Close', self.close, 'Ctrl+W')):
            if label is None:
                m.addSeparator(); continue
            a = QAction(label, self); a.setShortcut(key)
            a.triggered.connect(slot); m.addAction(a)

        t = self.menuBar().addMenu('Analysis')
        for label, slot in (('Refresh statistics', self.collectstats),
                            ('Frequency-analysis hints', self._hints),
                            ('Vowel Trowel (find vowels)', self._vowel_trowel),
                            ('Toggle English reference bars', self._toggle_ref)):
            a = QAction(label, self); a.triggered.connect(slot); t.addAction(a)

    # ── toolbar (the drawer of button groups — Cody's first engineered
    #    button code, kept structurally) ─────────────────────────────────────
    def _build_toolbar(self):
        tb = PToolBar('tools'); tb.setMovable(False)
        self.addToolBar(tb)

        self.power = QAction(_icon('start.png'), 'Power', self)
        self.power.setCheckable(True)
        self.power.toggled.connect(self._toggle_power)
        tb.addAction(self.power)
        tb.addSeparator()

        self._tool_actions = []

        def add(icon, text, handler):
            a = QAction(_icon(icon), text, self)
            a.setToolTip(text)
            a.triggered.connect(handler)
            tb.addAction(a)
            self._tool_actions.append(a)
            return a

        add('replace.png', 'Strip characters', lambda: self._run(ReplaceDialog))
        tb.addSeparator()
        add('railfence.png', 'Rail fence / Scytale', lambda: self._run(TranspositionDialog))
        add('scytale.png', 'Scytale (rod diameter)', lambda: self._run(TranspositionDialog))
        tb.addSeparator()
        add('caesar.png', 'Caesar / Affine shift', lambda: self._run(CaesarDialog))
        add('pigpen.png', 'Pigpen', lambda: self._run(PigpenDialog))
        add('monoalpha.png', 'Monoalphabetic substitution', lambda: self._run(SubstitutionDialog))
        tb.addSeparator()
        add('playfair.png', 'Playfair', lambda: self._run(PlayfairDialog))
        add('vigener.png', 'Vigenère', lambda: self._run(VigenereDialog))
        add('enigma.png', 'Enigma', lambda: self._run(EnigmaDialog))
        tb.addSeparator()
        add('freqletters.png', 'Frequency analysis', self.collectstats)
        add('freqdouble.png', 'Digraph frequency', self._digraphs)
        add('voweltrowel.png', 'Vowel Trowel', self._vowel_trowel)

        tb.addSeparator()
        commit = QAction('Commit ▸ Working', self)
        commit.triggered.connect(self._commit)
        tb.addAction(commit)
        self._tool_actions.append(commit)

    # ── power / tools ──────────────────────────────────────────────────────
    def _toggle_power(self, on):
        self._powered = on
        self.power.setIcon(_icon('stop.png' if on else 'start.png'))
        if on:
            self.original_text = self.working.toPlainText()
            self.collectstats()
            self.status.showMessage('Powered on — pick a cipher.')
        else:
            if self.original_text:
                self.working.setPlainText(self.original_text)
            self.change.clear()
            self.status.showMessage('Powered off — reverted to original text.')
        self._set_tools_enabled(on)

    def _set_tools_enabled(self, on):
        for a in getattr(self, '_tool_actions', []):
            a.setEnabled(on)

    @property
    def working_text(self):
        return self.working.toPlainText()

    def _run(self, dialog_cls):
        dlg = dialog_cls(self.working_text, self)
        if dlg.exec():
            self.change.setPlainText(dlg.result_text)
            if dlg.note:
                self.status.showMessage(dlg.note)

    def _commit(self):
        txt = self.change.toPlainText()
        if not txt:
            return
        self.working.setPlainText(txt)
        self.change.clear()
        self.collectstats()
        self.status.showMessage('Change Text committed to Working Text.')

    # ── statistics (old collectstats, split from the UI) ───────────────────
    def _on_working_changed(self):
        if self._powered:
            self.collectstats()

    def collectstats(self):
        text = self.working_text
        s = clean(text)
        self.freqbar.set_data(analysis.letter_frequencies(text))
        out = []
        out.append(f'characters (letters): {len(s)}')
        out.append(f'words: {len(text.split())}')
        out.append(f'index of coincidence: {analysis.index_of_coincidence(text):.4f}'
                   f'   (English ≈ 0.067, random ≈ 0.038)')
        out.append('')
        counts = analysis.letter_counts(text)
        by_n = sorted(counts.items(), key=lambda kv: -kv[1])
        out.append('frequency, most → least:')
        out.append('  ' + '  '.join(f'{k}:{v}' for k, v in by_n[:13]))
        out.append('  ' + '  '.join(f'{k}:{v}' for k, v in by_n[13:]))
        out.append('')
        dg = analysis.digraph_frequencies(text, 12)
        if dg:
            out.append('top digraphs: ' + ', '.join(f'{d}×{n}' for d, n in dg))
        doubles = analysis.repeated_pairs(text)
        if doubles:
            from collections import Counter
            dc = Counter(p for _, p in doubles)
            out.append('doubled letters: ' + ', '.join(f'{p}×{n}' for p, n in dc.most_common()))
        self.stats.setPlainText('\n'.join(out))

    def _digraphs(self):
        dg = analysis.ngram_counts(self.working_text, 2).most_common(30)
        self.stats.setPlainText('Digraph frequency (top 30):\n' +
            '\n'.join(f'  {d}  {n}' for d, n in dg) +
            '\n\nEnglish: ' + ' '.join(analysis.COMMON_DIGRAPHS))
        self.status.showMessage('Digraph frequency — Playfair leaves these visible.')

    def _hints(self):
        h = analysis.hints(self.working_text)
        self.stats.setPlainText('Frequency-analysis hints (Code Book hint sheet):\n\n'
                                + '\n\n'.join(f'• {x}' for x in h))
        self.status.showMessage(f'{len(h)} hints from the working text.')

    def _vowel_trowel(self):
        v, c = analysis.vowel_trowel(self.working_text)
        self.stats.setPlainText(
            "Vowel Trowel (Sukhotin's algorithm — no frequency table needed):\n\n"
            f"probable vowels     : {' '.join(v)}\n"
            f"probable consonants : {' '.join(c)}\n\n"
            "Vowels sit next to consonants, not each other — the letter with the\n"
            "highest neighbour-count is picked as a vowel, then its neighbours are\n"
            "made less likely, and so on.")
        self.status.showMessage('Vowel Trowel: ' + ' '.join(v[:6]))

    def _toggle_ref(self):
        self.freqbar._ref = None if self.freqbar._ref else analysis.ENGLISH_FREQ
        self.freqbar.update()

    # ── file menu ──────────────────────────────────────────────────────────
    def _new(self):
        self.working.clear(); self.change.clear(); self.original_text = ''

    def _open(self):
        fn, _ = PFileDialog.getOpenFileName(self, 'Open text', _HERE,
            'Text (*.txt);;All files (*)')
        if fn:
            with open(fn, 'r', errors='replace') as f:
                self.working.setPlainText(f.read())

    def _save(self):
        fn, _ = PFileDialog.getSaveFileName(self, 'Save Change Text', _HERE,
            'Text (*.txt)')
        if fn:
            with open(fn, 'w') as f:
                f.write(self.change.toPlainText() or self.working_text)
            self.status.showMessage(f'saved {fn}')


if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = Pycrypt()
    w.working.setPlainText(
        'The Code Book on CD-ROM largely follows the structure of The Code Book, '
        'with chapters that focus on the birth of cryptography, Victorian ciphers, '
        'World Wars I and II, the Information Age and Quantum Cryptography.')
    w.show()
    sys.exit(app.exec())
