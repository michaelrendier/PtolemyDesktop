#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
base.py — the shape every Pycrypt cipher dialog shares.

In the Tk build each cipher was a `Toplevel` with a live preview into the
Change Text box and an OK/Cancel pair; OK promoted the preview, Cancel restored
the working text.  `CipherDialog` is that contract as one PGui `PDialog`:

    dlg = CaesarDialog(working_text, parent)
    if dlg.exec():
        change_text, note = dlg.result_text, dlg.note

Subclasses fill `body()` with their controls and implement `recompute()` to set
`self.preview` (a CipherResult).  `on_preview_changed` is called so the dialog
can echo the result into its own read-only preview pane.
"""

from Pharos.PGui import (PDialog, PVBoxLayout, PPlainTextEdit, PDialogButtonBox,
                         PLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from Kryptos.Ciphers.common import CipherResult

_STYLE = (
    "QDialog { background:#050d0d; color:#cfe; }"
    "QLabel { color:#8fdede; }"
    "QPlainTextEdit,QLineEdit,QTextEdit { background:#0d2020; color:#cfe;"
    "  border:1px solid #0a6b7a; selection-background-color:#0aa; }"
    "QPushButton { background:#0a1414; color:#cfe; border:1px solid #0aa;"
    "  padding:4px 10px; } QPushButton:hover { border-color:#0ff; }"
    "QGroupBox { border:1px solid #0a6b7a; margin-top:8px; }"
    "QGroupBox::title { color:#8fdede; subcontrol-origin:margin; left:8px; }"
    "QComboBox,QSpinBox { background:#0d2020; color:#cfe; border:1px solid #0aa; }"
    "QRadioButton,QCheckBox { color:#cfe; }"
    "QSlider::groove:horizontal { background:#0a6b7a; height:4px; }"
    "QSlider::handle:horizontal { background:#0ff; width:12px; margin:-6px 0; }"
)


class CipherDialog(PDialog):
    title = 'Cipher'
    # a short passage from The Code Book this tool mechanises — shown at top
    narrative = ''

    def __init__(self, working_text: str, parent=None):
        super().__init__(parent)
        self.working_text = working_text or ''
        self.preview = CipherResult(text=self.working_text)
        self.setWindowTitle(f'Pycrypt — {self.title}')
        self.setStyleSheet(_STYLE)
        self.setMinimumWidth(560)

        self._root = PVBoxLayout(self)
        if self.narrative:
            lab = PLabel(self.narrative)
            lab.setWordWrap(True)
            lab.setFont(QFont('Ubuntu Mono', 8))
            lab.setStyleSheet("color:#5c8; font-style:italic;")
            self._root.addWidget(lab)

        self.body(self._root)

        self._preview_pane = PPlainTextEdit()
        self._preview_pane.setReadOnly(True)
        self._preview_pane.setFont(QFont('Ubuntu Mono', 10))
        self._preview_pane.setMaximumHeight(150)
        self._root.addWidget(PLabel('Result → Change Text'))
        self._root.addWidget(self._preview_pane)

        self._note = PLabel('')
        self._note.setWordWrap(True)
        self._root.addWidget(self._note)

        bb = PDialogButtonBox(
            PDialogButtonBox.StandardButton.Ok | PDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        self._root.addWidget(bb)

        self.recompute()

    # ── override points ──────────────────────────────────────────────────────
    def body(self, layout):
        """Add controls; connect their signals to self.recompute."""

    def recompute(self):
        """Set self.preview (a CipherResult) from the current controls."""
        self.preview = CipherResult(text=self.working_text)
        self._sync()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _sync(self):
        # body() may call recompute() before the preview pane exists — skip
        # until __init__ has finished wiring it up (it calls recompute() again).
        if not hasattr(self, '_preview_pane'):
            return
        self._preview_pane.setPlainText(self.preview.text)
        self._note.setText(self.preview.note or '')

    @property
    def result_text(self) -> str:
        return self.preview.text

    @property
    def note(self) -> str:
        return self.preview.note

    @property
    def result(self) -> CipherResult:
        return self.preview
