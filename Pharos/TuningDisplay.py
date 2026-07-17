#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TuningDisplay — Output Stream Monitor
========================================
Pharos Face / Tuning Display

Live monitor for PtolBus message streams.
Subscribes to all channels and renders a scrolling feed
with per-channel color coding and priority indicators.

Also wires directly to output_tuner.py diagnostics:
    Pre-collapse view, CWC inspector, focal point candidates.

Layout:
    [channel filter bar]     [pause] [clear] [save]
    ─────────────────────────────────────────────────
    T0 ◆ LUTHSPELL   halt:boundary_crossed          <timestamp>
    T1 ○ FACE_EVENT  archimedes › result: x+1       <timestamp>
    T1 ○ LOG         PtolBus: handler error          <timestamp>
    ...

Settings hook → Ptolemy Settings > Tuning Display tab.
"""

import time
from PyQt6.QtCore    import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui     import QColor, QFont, QTextCursor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QTextEdit, QPushButton, QLineEdit,
                              QLabel, QCheckBox)

try:
    from Pharos.PGui import PWidget
    _BASE = PWidget
except ImportError:
    _BASE = QWidget

# ── Channel color map ─────────────────────────────────────────────────────────
_CH_COLORS = {
    'LUTHSPELL':        '#ff4444',
    'PROMPT':           '#00ccff',
    'INFERENCE_COORDS': '#44ffaa',
    'FACE_EVENT':       '#ffcc00',
    'SENSOR':           '#ff8800',
    'LOG':              '#888888',
    'BLOCKCHAIN':       '#aa88ff',
    'SETTINGS':         '#88ccff',
}
_DEFAULT_COLOR = '#cccccc'
_T0_MARKER = '◆'
_T1_MARKER = '○'

# ── Settings ─────────────────────────────────────────────────────────────────
TUNING_SETTINGS = {
    "max_lines":        500,
    "auto_scroll":      True,
    "show_timestamp":   True,
    "channel_filter":   [],        # empty = show all
    "font_size":        10,
}


class TuningDisplay(_BASE):
    """
    Live PtolBus stream monitor.
    Subscribes to all channels on attach.
    """

    new_entry = pyqtSignal(str, str, str, float)   # channel, payload, pri, ts

    def __init__(self, bus=None, parent=None):
        super().__init__(parent)
        self._bus     = bus
        self._paused  = False
        self._filter  = set()   # channels to show; empty = all
        self._lines   = 0
        self._build_ui()
        if bus:
            self.attach(bus)
        # Route new_entry signal to UI (thread-safe)
        self.new_entry.connect(self._append_entry)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Toolbar ───────────────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText('channel filter (blank=all)')
        self._filter_input.setFixedHeight(22)
        self._filter_input.returnPressed.connect(self._apply_filter)
        toolbar.addWidget(self._filter_input)

        self._pause_btn = QPushButton('⏸ Pause')
        self._pause_btn.setFixedWidth(72)
        self._pause_btn.setFixedHeight(22)
        self._pause_btn.clicked.connect(self._toggle_pause)
        toolbar.addWidget(self._pause_btn)

        clear_btn = QPushButton('✕ Clear')
        clear_btn.setFixedWidth(64)
        clear_btn.setFixedHeight(22)
        clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # ── Stream view ───────────────────────────────────────────────────
        self._view = QTextEdit()
        self._view.setReadOnly(True)
        self._view.setFont(QFont('JetBrains Mono', TUNING_SETTINGS['font_size']))
        self._view.setStyleSheet(
            'background: #050d0d; color: #cdd6e0; border: 1px solid #00ccff22;')
        layout.addWidget(self._view)

        # ── Status bar ────────────────────────────────────────────────────
        self._status = QLabel('Tuning Display — not attached')
        self._status.setStyleSheet('color: #3a5a5a; font-size: 9px;')
        layout.addWidget(self._status)

        self.setMinimumSize(480, 300)
        self.setStyleSheet('background: #050d0d;')

    # ── Bus attachment ────────────────────────────────────────────────────────

    def attach(self, bus):
        """Subscribe to all known channels on the bus."""
        self._bus = bus
        channels = [
            'LUTHSPELL', 'PROMPT', 'INFERENCE_COORDS',
            'FACE_EVENT', 'SENSOR', 'LOG', 'BLOCKCHAIN', 'SETTINGS',
        ]
        for ch in channels:
            bus.subscribe(ch, self._on_message)
        # Also subscribe to any future channels via bus signal
        try:
            bus.message_dispatched.connect(lambda ch, src: None)
        except Exception:
            pass
        self._status.setText(f'Attached — {len(channels)} channels')

    def _on_message(self, msg):
        """Called from dispatch thread — emit signal to UI thread."""
        if self._paused:
            return
        ch  = getattr(msg, 'channel', '?')
        if self._filter and ch not in self._filter:
            return
        pri = getattr(msg, 'priority', 1)
        pay = str(getattr(msg, 'payload', ''))[:200]
        ts  = getattr(msg, 'timestamp', time.time())
        self.new_entry.emit(ch, pay, str(int(pri)), ts)

    def _append_entry(self, channel: str, payload: str, pri: str, ts: float):
        """Append a line to the stream view (UI thread)."""
        if self._lines >= TUNING_SETTINGS['max_lines']:
            # Trim top
            cur = self._view.textCursor()
            cur.movePosition(QTextCursor.Start)
            cur.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 20)
            cur.removeSelectedText()
        else:
            self._lines += 1

        color  = _CH_COLORS.get(channel, _DEFAULT_COLOR)
        marker = _T0_MARKER if pri == '0' else _T1_MARKER
        ts_str = (f'  <span style="color:#333">{time.strftime("%H:%M:%S", time.localtime(ts))}</span>'
                  if TUNING_SETTINGS['show_timestamp'] else '')

        html = (f'<span style="color:{color}">'
                f'{marker} {channel:<20s}</span>'
                f'<span style="color:#aaa">{payload[:120]}</span>'
                f'{ts_str}<br>')

        cur = self._view.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        self._view.setTextCursor(cur)
        self._view.insertHtml(html)

        if TUNING_SETTINGS['auto_scroll']:
            self._view.verticalScrollBar().setValue(
                self._view.verticalScrollBar().maximum())

    # ── Controls ──────────────────────────────────────────────────────────────

    def _toggle_pause(self):
        self._paused = not self._paused
        self._pause_btn.setText('▶ Resume' if self._paused else '⏸ Pause')

    def _clear(self):
        self._view.clear()
        self._lines = 0

    def _apply_filter(self):
        text = self._filter_input.text().strip().upper()
        self._filter = set(text.split()) if text else set()
        self._status.setText(
            f'Filter: {self._filter}' if self._filter else 'No filter — showing all')
