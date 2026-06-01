#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
# LeftPanel — 2-tab sidebar widget
# Tab 0: File tree (directories only, low overhead)
# Tab 1: Archimedes equation/constant browser

from PyQt6.QtCore import Qt, QDir, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget,
                             QTreeView,
                             QTreeWidget, QTreeWidgetItem, QLabel)
try:
    from PyQt6.QtWidgets import QFileSystemModel
except ImportError:
    from PyQt6.QtGui import QFileSystemModel
import importlib, inspect, os

_ARCH_ROOT = os.path.join(os.path.dirname(__file__), '..', 'Archimedes', 'Maths')


class FilePanel(QWidget):
    """Directory-only tree. Low overhead — QFileSystemModel with dir filter."""

    path_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QFileSystemModel(self)
        self.model.setRootPath(QDir.homePath())
        self.model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)

        self.tree = QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.homePath()))
        # hide size/type/date columns
        for col in (1, 2, 3):
            self.tree.hideColumn(col)
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(
            "QTreeView { background: #0a0a0a; color: #cccccc; border: none; }"
            "QTreeView::item:selected { background: #1a3a5a; }")
        self.tree.clicked.connect(self._on_click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)

    def _on_click(self, index):
        path = self.model.filePath(index)
        self.path_selected.emit(path)


class ArchimedesPanel(QWidget):
    """
    Scans Archimedes/Maths Python modules and UFformulary,
    builds a category tree. Items are draggable into the scene.
    Supports: evaluate, reverse (I/O), display formula.
    """

    item_dropped = pyqtSignal(dict)  # emits {'name', 'value', 'category', 'source'}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setStyleSheet(
            "QTreeWidget { background: #0a0a0a; color: #aaffcc; border: none; }"
            "QTreeWidget::item:selected { background: #1a3a2a; }")
        font = QFont('Monospace', 8)
        self.tree.setFont(font)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)

        self._populate()

    def _populate(self):
        self.tree.clear()

        # ── Python modules ───────────────────────────────────────────────────
        py_root = QTreeWidgetItem(self.tree, ['Archimedes :: Python'])
        py_root.setExpanded(False)

        module_map = {
            'Constants':    'Archimedes.Maths.Constants',
            'Calculus':     'Archimedes.Maths.Calculus',
            'Mechanics':    'Archimedes.Maths.Mechanics',
            'Thermodynamics': 'Archimedes.Maths.Thermodynamics',
            'Trigonometry': 'Archimedes.Maths.Trigonometry',
            'Combinatorics':'Archimedes.Maths.Combinatorics',
            'LinearAlgebra':'Archimedes.Maths.LinearAlgebra',
            'Sequences/Fibonacci': 'Archimedes.Maths.Sequences.FibonacciSequence',
            'Sequences/Lucas':     'Archimedes.Maths.Sequences.LucasNumbers',
            'Sequences/Mersenne':  'Archimedes.Maths.Sequences.MersennePrimes',
            'Sequences/DeBruijn':  'Archimedes.Maths.Sequences.DeBruijnSequences',
            'Series/InfiniteSeries': 'Archimedes.Maths.Series.InfiniteSeries',
            'Series/Maclaurin':    'Archimedes.Maths.Series.Maclaurin',
        }

        for display_name, mod_path in module_map.items():
            cat = display_name.split('/')[0]
            # find or create category node
            cat_node = self._get_or_create_child(py_root, cat)
            leaf_name = display_name.split('/')[-1]
            leaf = QTreeWidgetItem(cat_node, [leaf_name])
            leaf.setData(0, Qt.ItemDataRole.UserRole, {'type': 'module', 'path': mod_path})

            # try to enumerate public names
            try:
                mod = importlib.import_module(mod_path)
                for name in dir(mod):
                    if name.startswith('_'):
                        continue
                    obj = getattr(mod, name)
                    if callable(obj) or isinstance(obj, (int, float, str)):
                        entry = QTreeWidgetItem(leaf, [name])
                        val = obj if not callable(obj) else '(fn)'
                        entry.setData(0, Qt.ItemDataRole.UserRole, {
                            'type': 'constant' if not callable(obj) else 'function',
                            'name': name,
                            'value': str(val),
                            'module': mod_path,
                            'category': cat,
                        })
                        entry.setToolTip(0, str(val))
            except Exception as _e:
                print(f'[LeftPanel] import {mod_path}: {_e}')

        # ── UFformulary (directory listing only — files are large) ───────────
        uf_root = QTreeWidgetItem(self.tree, ['Archimedes :: UFformulary'])
        uf_root.setExpanded(False)
        uf_dir = os.path.join(_ARCH_ROOT, 'Formula', 'UFformulary')
        if os.path.isdir(uf_dir):
            ext_groups = {}
            for fname in sorted(os.listdir(uf_dir)):
                ext = fname.rsplit('.', 1)[-1] if '.' in fname else 'other'
                ext_groups.setdefault(ext, []).append(fname)
            for ext, files in sorted(ext_groups.items()):
                ext_node = QTreeWidgetItem(uf_root, [f'.{ext} ({len(files)})'])
                for fname in files:
                    fitem = QTreeWidgetItem(ext_node, [fname])
                    fitem.setData(0, Qt.ItemDataRole.UserRole, {
                        'type': 'ufm_file',
                        'name': fname,
                        'path': os.path.join(uf_dir, fname),
                    })

    def _get_or_create_child(self, parent, name):
        for i in range(parent.childCount()):
            if parent.child(i).text(0) == name:
                return parent.child(i)
        node = QTreeWidgetItem(parent, [name])
        return node


class LeftPanel(QWidget):
    """Two-tab sidebar. Width fixed at 260px."""

    path_selected = pyqtSignal(str)
    arch_item_activated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(260)
        self._focused = False

        self.tabs = QTabWidget(self)
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: none; background: #0a0a0a; }"
            "QTabBar::tab { background: #111; color: #888; padding: 4px 10px; }"
            "QTabBar::tab:selected { background: #1a3a5a; color: #fff; }")

        self.file_panel = FilePanel(self)
        self.arch_panel = ArchimedesPanel(self)

        self.tabs.addTab(self.file_panel, '📁 Files')
        self.tabs.addTab(self.arch_panel, '∑ Archimedes')

        self.file_panel.path_selected.connect(self.path_selected)
        self.arch_panel.tree.itemDoubleClicked.connect(self._on_arch_activate)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

    def set_focused(self, focused: bool):
        self._focused = focused
        self.setWindowOpacity(1.0 if focused else 0.30)

    def _on_arch_activate(self, item, _col):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.arch_item_activated.emit(data)
