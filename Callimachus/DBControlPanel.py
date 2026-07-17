#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
DBControlPanel — Callimachus Face
===================================
Database control panel. Uses Callimachus v09 (SQLite / HyperWebster).
Database.py (MySQL stub) retired.
"""

import os
import sys

from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (QApplication, QWidget, QGridLayout,
                              QLabel, QVBoxLayout)

from Pharos.PtolFace  import PtolFace
from Pharos.PGui      import PMainWindow

_HERE     = os.path.dirname(os.path.abspath(__file__))
_PTOL_ROOT = os.path.dirname(_HERE)

_DEFAULT_IMAGE_DIR = os.path.join(_PTOL_ROOT, 'images', 'Callimachus') + os.sep
_DEFAULT_DB_PATH   = os.path.join(_HERE, 'data', 'ptolemy.db')
_DEFAULT_HW_ROOT   = os.path.join(_HERE, 'data', 'hyperwebster')

_STYLESHEET = (
    'QMainWindow { border: 1px solid white; background: black; color: white } '
    'QWidget { background: black; color: white } '
    'QPushButton { border: 1px solid white; background: black; color: white } '
    'QPushButton:hover { border: 1px solid blue } '
    'QLabel { border: 0px } '
)


class DBControlPanel(PMainWindow, PtolFace):

    def __init__(self, parent=None):
        super().__init__(parent)
        PMainWindow.__init__(self)

        self.setWindowTitle('Callimachus DB CPanel — Ptolemy')

        if parent:
            self.Ptolemy  = parent
            self.imageDir = getattr(parent, 'imgDir', _DEFAULT_IMAGE_DIR) + 'Callimachus/'
            self.styles   = getattr(parent, 'stylesheet', _STYLESHEET)
            self.dialogs  = getattr(parent, 'dialogs', None)
            self.database = getattr(parent, 'db', None)   # Callimachus v09 instance
        else:
            self.Ptolemy  = None
            self.imageDir = _DEFAULT_IMAGE_DIR
            self.styles   = _STYLESHEET
            self.dialogs  = None
            try:
                from Callimachus.v09 import Callimachus
                self.database = Callimachus(_DEFAULT_DB_PATH, _DEFAULT_HW_ROOT)
            except Exception as e:
                print(f'[DBControlPanel] Callimachus v09 init: {e}')
                self.database = None

        self.setStyleSheet(self.styles)
        self.btnSize = 32
        self.initUi()

    def __del__(self):
        pass

    # ── UI ────────────────────────────────────────────────────────────────────

    def initUi(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QGridLayout(central)

        def _btn(svg_name, tip):
            path = os.path.join(self.imageDir, svg_name)
            btn  = QSvgWidget(path) if os.path.exists(path) else QLabel(tip)
            btn.setFixedSize(self.btnSize, self.btnSize)
            btn.setToolTip(tip)
            return btn

        def _blank():
            b = QWidget()
            b.setFixedSize(self.btnSize, self.btnSize)
            return b

        self.noteBtn        = _btn('notepad.svg',           'Add Note')
        self.dependPtolBtn  = _btn('ptolemydependency.svg', 'Add Ptolemy Dependency')
        self.dependSrvBtn   = _btn('serverdependency.svg',  'Add Server Dependency')
        self.sectionBtn     = _btn('section.svg',           'Add Section')
        self.categoryBtn    = _btn('category.svg',          'Add Category')
        self.recipeBtn      = _btn('recipe.svg',            'Add Recipe')
        self.archiveBtn     = _btn('archive.svg',           'Archive URL')
        self.codeBtn        = _btn('codeblock.svg',         'Add Script')

        if self.dialogs:
            self.noteBtn.mousePressEvent       = self.dialogs.addNoteBox
            self.dependPtolBtn.mousePressEvent = self.dialogs.addPtolDependencyBox
            self.dependSrvBtn.mousePressEvent  = self.dialogs.addServerDependencyBox
            self.sectionBtn.mousePressEvent    = self.dialogs.addSectionBox
            self.categoryBtn.mousePressEvent   = self.dialogs.addCategoryBox
            self.recipeBtn.mousePressEvent     = self.dialogs.addRecipe
            self.archiveBtn.mousePressEvent    = self.dialogs.archiveArticle
            self.codeBtn.mousePressEvent       = self.dialogs.addCode

        layout.addWidget(self.noteBtn,       0, 0)
        layout.addWidget(self.dependPtolBtn, 0, 1)
        layout.addWidget(self.dependSrvBtn,  0, 2)
        layout.addWidget(self.sectionBtn,    0, 3)
        layout.addWidget(self.categoryBtn,   0, 4)
        layout.addWidget(self.recipeBtn,     1, 0)
        layout.addWidget(self.archiveBtn,    1, 1)
        layout.addWidget(self.codeBtn,       1, 2)

        blanks = [_blank() for _ in range(17)]
        positions = [(1, 3), (1, 4),
                     (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
                     (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
                     (4, 0), (4, 1), (4, 2), (4, 3), (4, 4)]
        for blank, (r, c) in zip(blanks, positions):
            layout.addWidget(blank, r, c)

        # ── DB stats footer ───────────────────────────────────────────────────
        self.statsLabel = QLabel()
        self.statsLabel.setStyleSheet('color: #666; font-size: 9px;')
        layout.addWidget(self.statsLabel, 5, 0, 1, 5)
        self._refresh_stats()

    def _refresh_stats(self):
        if self.database is None:
            self.statsLabel.setText('Callimachus: not connected')
            return
        try:
            s = self.database.db_stats()
            self.statsLabel.setText(
                f'v{s["version"]}  words={s["total"]}  '
                f'incomplete={s["incomplete"]}  db={os.path.basename(s["db_path"])}')
        except Exception as e:
            self.statsLabel.setText(f'stats error: {e}')


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Callimachus DB CPanel — Ptolemy')
    cpanel = DBControlPanel()
    cpanel.setWindowTitle('Callimachus DB CPanel — Ptolemy')
    cpanel.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
