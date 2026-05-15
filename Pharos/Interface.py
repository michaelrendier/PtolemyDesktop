#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Interface.py — Pharos Interface Behavior
=========================================
Behavior layer only. All geometry is in PharosGeometry.py.

User(PharosLayout):
    - _wire_callbacks()  — all mousePressEvent assignments, one place
    - miniaturize/restore
    - Face menu dispatch
    - Blockchain commit on menu open
"""

from PyQt6.QtCore    import QTimer
from PyQt6.QtWidgets import QApplication

from Pharos.PharosGeometry import PharosLayout

import sys


class User(PharosLayout):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._mini = False
        self._mini_timer = QTimer(self)
        self._mini_timer.setInterval(30000)
        self._mini_timer.setSingleShot(True)
        self._mini_timer.timeout.connect(self.miniaturize)
        self._mini_timer.start()

    # ── override hooks so callbacks are wired after geometry is built ──────────

    def initUi(self):
        super().initUi()
        self._wire_callbacks()

    def clearLayout(self):
        super().clearLayout()
        self._wire_callbacks()

    # ── single binding table ───────────────────────────────────────────────────

    def _wire_callbacks(self):
        self.powerBtn.mousePressEvent        = self.power
        self.alexandriaBtn.mousePressEvent   = self.alexandriaMenu
        self.archimedesBtn.mousePressEvent   = self.archimedesMenu
        self.anaximanderBtn.mousePressEvent  = self.anaximanderMenu
        self.callimachusBtn.mousePressEvent  = self.callimachusMenu
        self.kryptosBtn.mousePressEvent      = self.kryptosMenu
        self.mouseionBtn.mousePressEvent     = self.mouseionMenu
        self.phaleronBtn.mousePressEvent     = self.phaleronMenu
        self.pharosBtn.mousePressEvent       = self.pharosMenu
        self.teslaBtn.mousePressEvent        = self.teslaMenu
        self.treasureHuntBtn.mousePressEvent = self.Ptolemy.openSearch
        self.navigationBtn.mousePressEvent   = self.Ptolemy.openNavigation
        self.coreBtn.mousePressEvent         = self.Ptolemy.openCore
        self.earthBtn.mousePressEvent        = self.Ptolemy.openEarth
        self.graphBtn.mousePressEvent        = self.Ptolemy.openGraphPlot
        self.fractalBtn.mousePressEvent      = self.Ptolemy.openFractal
        self.stanDevBtn.mousePressEvent      = self.Ptolemy.openStanDev
        self.dbCPanelBtn.mousePressEvent     = self.Ptolemy.openDbCPanel
        self.libraryBtn.mousePressEvent      = self.Ptolemy.openLibrary
        self.wikiGroupBtn.mousePressEvent    = self.Ptolemy.openWikiGroup
        self.indicator.mousePressEvent       = lambda e: self.output and self.output('Thread Indicator')

    # ── mouse ──────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._restart_mini_timer()

    # ── miniaturize ────────────────────────────────────────────────────────────

    def _restart_mini_timer(self):
        if self._mini:
            self.restore()
        self._mini_timer.stop()
        self._mini_timer.start()

    def miniaturize(self):
        self._mini = True
        self.display.hide()
        for name in self.sysTrayList[1:-1]:
            btn = getattr(self, name + 'Btn', None)
            if btn:
                btn.hide()
        self._overlay.set_mini(True)

    def restore(self):
        self._mini = False
        self.display.show()
        for name in self.sysTrayList[1:-1]:
            btn = getattr(self, name + 'Btn', None)
            if btn:
                btn.show()
        self._overlay.set_mini(False)

    # ── system ─────────────────────────────────────────────────────────────────

    def power(self, event):
        self.Ptolemy.close()

    def _chain_commit(self, face: str, action: str):
        try:
            from Pharos.ptol_blockchain import chain
            chain.commit_gui(f'Interface:{face}', action, {})
        except Exception:
            pass

    # ── face menus ─────────────────────────────────────────────────────────────

    def archimedesMenu(self, event):
        self._chain_commit('Archimedes', 'menu_open')
        self._overlay.changeIdentity('Archimedes')
        self.clearLayout()
        self.layout.addWidget(self.graphBtn,   11, 2, 1, 1)
        self.layout.addWidget(self.fractalBtn, 11, 3, 1, 1)

    def alexandriaMenu(self, event):
        self._chain_commit('Alexandria', 'menu_open')
        self._overlay.changeIdentity('Alexandria')
        self.clearLayout()
        self.layout.addWidget(self.coreBtn,  11, 2, 1, 1)
        self.layout.addWidget(self.earthBtn, 11, 3, 1, 1)

    def anaximanderMenu(self, event):
        self._chain_commit('Anaximander', 'menu_open')
        self._overlay.changeIdentity('Anaximander')
        self.clearLayout()
        self.layout.addWidget(self.navigationBtn, 11, 2, 1, 1)

    def callimachusMenu(self, event):
        self._chain_commit('Callimachus', 'menu_open')
        self._overlay.changeIdentity('Callimachus')
        self.clearLayout()
        self.layout.addWidget(self.dbCPanelBtn, 11, 2, 1, 1)

    def kryptosMenu(self, event):
        self._chain_commit('Kryptos', 'menu_open')
        self._overlay.changeIdentity('Kryptos')
        self.clearLayout()

    def mouseionMenu(self, event):
        self._chain_commit('Mouseion', 'menu_open')
        self._overlay.changeIdentity('Mouseion')
        self.clearLayout()
        self.layout.addWidget(self.libraryBtn,   11, 2, 1, 1)
        self.layout.addWidget(self.wikiGroupBtn, 11, 3, 1, 1)

    def phaleronMenu(self, event):
        self._chain_commit('Phaleron', 'menu_open')
        self._overlay.changeIdentity('Phaleron')
        self.clearLayout()
        self.layout.addWidget(self.treasureHuntBtn, 11, 2, 1, 1)

    def pharosMenu(self, event):
        self._chain_commit('Pharos', 'menu_open')
        self._overlay.changeIdentity('Pharos')
        self.clearLayout()
        self.originalLayout()

    def teslaMenu(self, event):
        self._chain_commit('Tesla', 'menu_open')
        self._overlay.changeIdentity('Tesla')
        self.clearLayout()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Interface')
    Iface = User()
    Iface.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
