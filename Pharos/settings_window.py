#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy — Settings Window
==========================
Pharos Face

Layout:
  ┌─[PTOL]──[Ptolemy Settings]────────────[_][□][✕]─┐
  │  ┌──────────┬──────────────────────────────────┐  │
  │  │ Modules  │  [tab per discovered module]     │  │
  │  │ ──────── │  ┌──────────────────────────┐   │  │
  │  │ Inputs   │  │ key  │ value  │ stub?     │   │  │
  │  │          │  │ ...  │ ...    │ ...       │   │  │
  │  └──────────┴──┴──────────────────────────┘   │  │
  │                                   [Save] [Scan] │  │
  └──────────────────────────────────────────────────┘

Left sidebar: "Modules" header + list of module names
              "Inputs" header + sensor list (greyed if inactive)
Right panel:  tab content for selected module or sensor

Sensor rows: label, active indicator (green dot / grey dot), Settings btn
"""

from PyQt6.QtCore    import Qt, QSize
from PyQt6.QtGui     import QColor, QPalette, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QFrame, QSizePolicy,
    QCheckBox, QLineEdit, QComboBox, QScrollArea
)

from Pharos.ptolemy_settings import PtolemySettings, ModuleSettings

# ── Palette (matches Pharos dark theme) ───────────────────────────────────────
_BG       = '#050d0d'
_PANEL    = '#0a1414'
_BORDER   = '#00ffff22'
_ACCENT   = '#00ffff'
_DIM      = '#3a5a5a'
_TEXT     = '#cdd6e0'
_STUB     = '#f0a04a'
_ACTIVE   = '#00ff88'
_INACTIVE = '#3a4a4a'

_STYLE = f"""
QWidget              {{ background: {_BG}; color: {_TEXT}; font-family: 'JetBrains Mono', monospace; font-size: 11px; }}
QListWidget          {{ background: {_PANEL}; border: 1px solid {_BORDER}; }}
QListWidget::item    {{ padding: 6px 10px; }}
QListWidget::item:selected {{ background: #0d3030; color: {_ACCENT}; }}
QTableWidget         {{ background: {_PANEL}; gridline-color: {_BORDER}; border: none; }}
QHeaderView::section {{ background: #0a1a1a; color: {_DIM}; border: none; padding: 4px; }}
QPushButton          {{ background: #0d2020; border: 1px solid {_DIM}; color: {_ACCENT};
                        padding: 4px 12px; }}
QPushButton:hover    {{ border-color: {_ACCENT}; }}
QLineEdit            {{ background: #0d2020; border: 1px solid {_DIM}; color: {_TEXT}; padding: 2px 6px; }}
QComboBox            {{ background: #0d2020; border: 1px solid {_DIM}; color: {_TEXT}; padding: 2px 6px; }}
QLabel#section       {{ color: {_DIM}; font-size: 10px; padding: 8px 10px 2px 10px; }}
QLabel#stub          {{ color: {_STUB}; font-size: 10px; }}
QLabel#active_dot    {{ font-size: 14px; }}
QFrame#divider       {{ background: {_BORDER}; max-height: 1px; }}
"""


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("section")
    return lbl


class SensorRow(QWidget):
    """One sensor input row: dot | label | [Settings]"""

    def __init__(self, sensor_id: str, info: dict, settings_engine: PtolemySettings, parent=None):
        super().__init__(parent)
        self._sid = sensor_id
        self._engine = settings_engine
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        active = info.get("active", False)
        dot = QLabel("●")
        dot.setObjectName("active_dot")
        dot.setStyleSheet(f"color: {'#00ff88' if active else '#3a4a4a'};")
        dot.setFixedWidth(18)

        lbl = QLabel(info.get("label", sensor_id))
        if not active:
            lbl.setStyleSheet(f"color: {_INACTIVE};")

        layout.addWidget(dot)
        layout.addWidget(lbl)
        layout.addStretch()


class ModuleSettingsPanel(QWidget):
    """Table view for one module's settings dict."""

    def __init__(self, module: ModuleSettings, parent=None):
        super().__init__(parent)
        self._module = module
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        header = QLabel(f"{module.display}  <span style='color:{_DIM}'>v{module.version} · {module.face}</span>")
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(div)

        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Key", "Value", "Type", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        self._populate()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignRight)

    def _populate(self):
        s = self._module.settings
        self._table.setRowCount(len(s))
        self._editors = {}

        for row, (key, meta) in enumerate(s.items()):
            self._table.setItem(row, 0, QTableWidgetItem(key))

            val_type = meta.get("type", "str")
            value    = meta.get("value")
            stub     = meta.get("stub", False)

            # Value editor
            if val_type == "bool":
                cb = QCheckBox()
                cb.setChecked(bool(value))
                cell = QWidget()
                lay  = QHBoxLayout(cell)
                lay.addWidget(cb)
                lay.setContentsMargins(4,0,4,0)
                self._table.setCellWidget(row, 1, cell)
                self._editors[key] = ("bool", cb)
            elif val_type == "enum":
                combo = QComboBox()
                combo.addItems(meta.get("options", []))
                combo.setCurrentText(str(value))
                self._table.setCellWidget(row, 1, combo)
                self._editors[key] = ("enum", combo)
            else:
                le = QLineEdit(str(value))
                self._table.setCellWidget(row, 1, le)
                self._editors[key] = (val_type, le)

            self._table.setItem(row, 2, QTableWidgetItem(val_type))

            status = QTableWidgetItem("STUB" if stub else "wired")
            status.setForeground(QColor(_STUB if stub else _ACTIVE))
            self._table.setItem(row, 3, status)

    def _save(self):
        for key, (typ, widget) in self._editors.items():
            if typ == "bool":
                self._module.set(key, widget.isChecked())
            elif typ == "enum":
                self._module.set(key, widget.currentText())
            elif typ == "int":
                try:
                    self._module.set(key, int(widget.text()))
                except ValueError:
                    pass
            elif typ == "float":
                try:
                    self._module.set(key, float(widget.text()))
                except ValueError:
                    pass
            else:
                self._module.set(key, widget.text())


class SensorsPanel(QWidget):
    """Sensor inputs panel — all sensors listed, greyed if inactive."""

    def __init__(self, settings_engine: PtolemySettings, parent=None):
        super().__init__(parent)
        self._engine = settings_engine
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        lbl = QLabel("Sensor Inputs")
        lbl.setStyleSheet(f"color: {_ACCENT}; font-size: 13px;")
        layout.addWidget(lbl)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(div)

        note = QLabel("Active streams show green ●. Greyed sensors have no incoming data.")
        note.setStyleSheet(f"color: {_DIM}; font-size: 10px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        for sid, info in settings_engine.sensor_inputs.items():
            layout.addWidget(SensorRow(sid, info, settings_engine))

        layout.addStretch()


class PtolemySettingsWindow(QWidget):
    """
    Main Settings window.
    Launched from the Pharos power button right-click menu.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ptolemy Settings")
        self.setMinimumSize(740, 480)
        self.setStyleSheet(_STYLE)

        self._engine = PtolemySettings()
        self._engine.scan()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Left sidebar ──────────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"background: {_PANEL};")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        sb_layout.addWidget(_section_label("Modules"))
        self._mod_list = QListWidget()
        self._mod_list.setFrameShape(QFrame.Shape.NoFrame)
        sb_layout.addWidget(self._mod_list)

        div = QFrame()
        div.setObjectName("divider")
        div.setFrameShape(QFrame.Shape.HLine)
        sb_layout.addWidget(div)

        sb_layout.addWidget(_section_label("Inputs"))
        self._input_list = QListWidget()
        self._input_list.setFrameShape(QFrame.Shape.NoFrame)
        self._input_list.setMaximumHeight(160)
        sb_layout.addWidget(self._input_list)

        splitter.addWidget(sidebar)

        # ── Right panel (stacked) ─────────────────────────────────────────────
        self._stack = QStackedWidget()
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(1, 1)

        root_layout.addWidget(splitter)

        # ── Bottom bar ────────────────────────────────────────────────────────
        bar = QWidget()
        bar.setStyleSheet(f"background: {_PANEL}; border-top: 1px solid {_BORDER};")
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(8, 4, 8, 4)

        self._status = QLabel(f"{len(self._engine.modules)} modules loaded")
        self._status.setStyleSheet(f"color: {_DIM};")
        bar_layout.addWidget(self._status)
        bar_layout.addStretch()

        scan_btn = QPushButton("Rescan")
        scan_btn.clicked.connect(self._rescan)
        bar_layout.addWidget(scan_btn)

        root_layout.addWidget(bar)

        self._build_sidebar()
        self._mod_list.currentRowChanged.connect(self._on_mod_select)
        self._input_list.currentRowChanged.connect(self._on_input_select)

        if self._mod_list.count():
            self._mod_list.setCurrentRow(0)

    def _build_sidebar(self):
        self._mod_list.clear()
        self._input_list.clear()
        # Clear stack
        while self._stack.count():
            self._stack.removeWidget(self._stack.widget(0))

        self._mod_panels = []
        for mod in self._engine.modules:
            self._mod_list.addItem(mod.display)
            panel = ModuleSettingsPanel(mod)
            self._stack.addWidget(panel)
            self._mod_panels.append(panel)

        # Sensors entry
        self._sensors_panel = SensorsPanel(self._engine)
        self._stack.addWidget(self._sensors_panel)
        self._sensors_stack_idx = self._stack.count() - 1

        for sid, info in self._engine.sensor_inputs.items():
            active = info.get("active", False)
            dot    = "● " if active else "○ "
            item   = QListWidgetItem(dot + info.get("label", sid))
            if not active:
                item.setForeground(QColor(_INACTIVE))
            self._input_list.addItem(item)

        if self._engine.errors:
            self._status.setText(
                f"{len(self._engine.modules)} modules · {len(self._engine.errors)} load errors"
            )
            self._status.setStyleSheet(f"color: {_STUB};")

    def _on_mod_select(self, row):
        if 0 <= row < len(self._mod_panels):
            self._input_list.clearSelection()
            self._stack.setCurrentWidget(self._mod_panels[row])

    def _on_input_select(self, row):
        if row >= 0:
            self._mod_list.clearSelection()
            self._stack.setCurrentIndex(self._sensors_stack_idx)

    def _rescan(self):
        self._engine.scan()
        self._build_sidebar()
        self._status.setText(f"{len(self._engine.modules)} modules loaded")

    def select_section(self, section: str):
        """
        Navigate to a named module section.
        Accepts module_id (snake_case) or display name.
        Falls back silently if not found.
        """
        section_lower = section.lower()
        for row, mod in enumerate(self._engine.modules):
            if (mod.module_id.lower() == section_lower or
                    mod.display.lower() == section_lower or
                    mod.face.lower() == section_lower):
                self._mod_list.setCurrentRow(row)
                return
        # Try sensor inputs
        for row, sid in enumerate(self._engine.sensor_inputs.keys()):
            if sid.lower() == section_lower:
                self._input_list.setCurrentRow(row)
                return


# Alias so Ptolemy3.py can import either name
SettingsWindow = PtolemySettingsWindow
