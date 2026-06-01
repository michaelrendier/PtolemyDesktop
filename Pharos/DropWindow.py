#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
# DropWindow — created when content is dropped onto the empty Ptolemy desktop
# Also used for Archimedes equation evaluation windows
# Includes repass: re-source data without age/staleness taint

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTextEdit, QPushButton,
                             QLineEdit, QTabWidget)
import os, json, time


class DropWindow(QWidget):
    """
    Spawned by desktop drag-drop or Archimedes panel activation.
    Modes:
      - file/url drop  → shows path, file info, repass button
      - text drop      → shows text, eval option
      - arch drop      → equation/constant display with eval + I/O reversal
    """

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumSize(400, 300)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet(
            "QWidget { background: rgba(10,10,20,220); color: #cccccc; }"
            "QPushButton { background: #1a2a3a; color: #88ccff; border: 1px solid #334; "
            "              padding: 3px 8px; }"
            "QPushButton:hover { background: #2a4a6a; }"
            "QTextEdit { background: #050510; color: #aaffcc; border: 1px solid #334; }"
            "QLineEdit { background: #050510; color: #ffffff; border: 1px solid #445; }"
            "QLabel    { color: #aaaaaa; }")

        self._build_ui()
        self._populate()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(6, 6, 6, 6)
        main.setSpacing(4)

        # title bar
        bar = QHBoxLayout()
        self._title = QLabel('Drop Window')
        self._title.setStyleSheet("color:#88ccff; font-weight:bold;")
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.close)
        bar.addWidget(self._title)
        bar.addStretch()
        bar.addWidget(close_btn)
        main.addLayout(bar)

        # tabs: View | Eval | I/O
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { background:#111; color:#888; padding:3px 8px; }"
            "QTabBar::tab:selected { background:#1a3a5a; color:#fff; }"
            "QTabWidget::pane { border:none; }")

        # View tab
        self._view = QTextEdit()
        self._view.setReadOnly(True)
        self._view.setFont(QFont('Monospace', 9))
        self.tabs.addTab(self._view, 'View')

        # Eval tab
        eval_w = QWidget()
        el = QVBoxLayout(eval_w)
        el.setContentsMargins(4, 4, 4, 4)
        self._eval_input = QLineEdit()
        self._eval_input.setPlaceholderText('Expression or substitution…')
        self._eval_output = QTextEdit()
        self._eval_output.setReadOnly(True)
        eval_btn = QPushButton('Evaluate')
        eval_btn.clicked.connect(self._evaluate)
        el.addWidget(QLabel('Input:'))
        el.addWidget(self._eval_input)
        el.addWidget(eval_btn)
        el.addWidget(QLabel('Output:'))
        el.addWidget(self._eval_output)
        self.tabs.addTab(eval_w, 'Eval')

        # I/O (inside-out / reversal) tab
        io_w = QWidget()
        il = QVBoxLayout(io_w)
        il.setContentsMargins(4, 4, 4, 4)
        self._io_target = QLineEdit()
        self._io_target.setPlaceholderText('Target output value…')
        self._io_output = QTextEdit()
        self._io_output.setReadOnly(True)
        io_btn = QPushButton('Reverse (I/O)')
        io_btn.clicked.connect(self._reverse)
        il.addWidget(QLabel('Known output → find input:'))
        il.addWidget(self._io_target)
        il.addWidget(io_btn)
        il.addWidget(self._io_output)
        self.tabs.addTab(io_w, 'I/O')

        main.addWidget(self.tabs)

        # Repass button
        repass_btn = QPushButton('↺ Repass')
        repass_btn.setToolTip(
            'Re-source this data from original pipeline without stale information')
        repass_btn.clicked.connect(self._repass)
        main.addWidget(repass_btn)

        self._timestamp_lbl = QLabel()
        self._timestamp_lbl.setStyleSheet("color:#555; font-size:8px;")
        main.addWidget(self._timestamp_lbl)

    def _populate(self):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        self._timestamp_lbl.setText(f'Acquired: {ts}')

        if 'arch' in self.data:
            d = self.data['arch']
            self._title.setText(f"∑ {d.get('name', 'Archimedes')}")
            lines = [f"Name    : {d.get('name','')}",
                     f"Category: {d.get('category','')}",
                     f"Type    : {d.get('type','')}",
                     f"Value   : {d.get('value','')}",
                     f"Module  : {d.get('module', d.get('path',''))}"]
            self._view.setPlainText('\n'.join(lines))
            # pre-fill eval
            if d.get('type') == 'constant':
                self._eval_input.setText(str(d.get('value', '')))

        elif 'urls' in self.data:
            urls = self.data['urls']
            self._title.setText(f'Drop: {os.path.basename(urls[0]) if urls else "?"}')
            info = []
            for u in urls:
                info.append(u)
                if os.path.exists(u):
                    stat = os.stat(u)
                    info.append(f'  size : {stat.st_size} bytes')
                    info.append(f'  mtime: {time.ctime(stat.st_mtime)}')
            self._view.setPlainText('\n'.join(info))

        elif 'text' in self.data:
            self._title.setText('Drop: Text')
            self._view.setPlainText(self.data['text'])
            self._eval_input.setText(self.data['text'])

    # ── Evaluate ─────────────────────────────────────────────────────────────

    def _evaluate(self):
        expr = self._eval_input.text().strip()
        if not expr:
            return
        try:
            import math
            result = eval(expr, {"__builtins__": {}}, vars(math))
            self._eval_output.setPlainText(str(result))
        except Exception as ex:
            self._eval_output.setPlainText(f'Error: {ex}')

    # ── I/O reversal (numeric only for now) ──────────────────────────────────

    def _reverse(self):
        """
        Given a target output value and a single-variable expression from the
        Eval tab, use scipy.optimize or simple Newton step to find the input.
        Falls back to symbolic note if scipy unavailable.
        """
        target_str = self._io_target.text().strip()
        expr_str   = self._eval_input.text().strip()
        if not target_str or not expr_str:
            self._io_output.setPlainText('Fill both Eval input and I/O target.')
            return
        try:
            target = float(target_str)
        except ValueError:
            self._io_output.setPlainText('Target must be a numeric value.')
            return
        try:
            from scipy.optimize import brentq
            import math
            f = lambda x: eval(expr_str, {"__builtins__": {}, "x": x}, vars(math)) - target
            root = brentq(f, -1e6, 1e6)
            self._io_output.setPlainText(
                f'x ≈ {root}\n(via Brent method on [{-1e6},{1e6}])')
        except ImportError:
            self._io_output.setPlainText(
                f'scipy not available.\n'
                f'Symbolic reversal: solve  {expr_str}  =  {target_str}  for x.\n'
                f'Install scipy for numeric I/O.')
        except Exception as ex:
            self._io_output.setPlainText(f'I/O Error: {ex}')

    # ── Repass ────────────────────────────────────────────────────────────────

    def _repass(self):
        """
        Re-source the data without trusting any cached/aged information.
        For files: re-stat and re-read.
        For arch items: re-import the module live.
        For text: flag as unverified origin.
        No AI/API calls. No cost.
        """
        self._timestamp_lbl.setText('Repassing…')

        if 'arch' in self.data:
            d = self.data['arch']
            mod_path = d.get('module', '')
            name     = d.get('name', '')
            if mod_path and name:
                try:
                    import importlib
                    mod = importlib.import_module(mod_path)
                    importlib.reload(mod)  # force fresh load
                    fresh = getattr(mod, name, None)
                    if fresh is not None:
                        self.data['arch']['value'] = str(fresh)
                        self._populate()
                        self._timestamp_lbl.setText(
                            f'Repass OK: {time.strftime("%H:%M:%S")}')
                        return
                except Exception as ex:
                    self._view.append(f'\nRepass error: {ex}')
            self._timestamp_lbl.setText('Repass: no module path available')

        elif 'urls' in self.data:
            # re-stat files
            info = []
            for u in self.data['urls']:
                if os.path.exists(u):
                    stat = os.stat(u)
                    info.append(u)
                    info.append(f'  size : {stat.st_size} bytes')
                    info.append(f'  mtime: {time.ctime(stat.st_mtime)}')
                else:
                    info.append(f'{u}  [NOT FOUND]')
            self._view.setPlainText('\n'.join(info))
            self._timestamp_lbl.setText(f'Repass OK: {time.strftime("%H:%M:%S")}')

        elif 'text' in self.data:
            self._view.append('\n[repass: text origin unverifiable — mark for review]')
            self._timestamp_lbl.setText(f'Repass: {time.strftime("%H:%M:%S")} — origin unverified')
