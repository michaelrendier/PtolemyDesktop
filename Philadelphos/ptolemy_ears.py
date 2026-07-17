#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos/ptolemy_ears.py — Prompt Input Function
=====================================================
Ptolemy's Ears: the single normalised text entry point for the
Noether Information Current chain.

Architecture
------------
    [keyboard / QLineEdit] ──┐
                              ├─→  text_input()  →  NoetherChainInput.submit()
    [speech recognition]  ──┘                        ContextBuffer (3 layers)
                                                      Gate (SedenionGate)
                                                      ↓
                                                  response handler
                                                      ↓
                                              ptolemy_tongue (last filter)
                                                      ↓
                                              QLabel / output widget

Pipeline
--------
    1. Submission event (Enter key / Send button / speech endpoint)
    2. _gate_and_submit(): blocks on SedenionGate, encodes sedenion,
       pushes to ContextBuffer, returns BufferedPrompt
    3. response_callback receives model reply text
    4. PtolemyTongue.filter() — fold geometry filter — applied before display
    5. Gate released → chain ready for next input

Threading
---------
    The Qt event loop runs on the main thread.
    Gate.submit() is non-blocking in normal use (gate starts open).
    If the gate is closed (chain still processing), a QThread worker
    queues the submission so the UI never freezes.

Speech
------
    SpeechInput (QAudioRecorder subclass) calls speak_text(text)
    which feeds the same text_input() function.
    Single normalised stream regardless of source.

Usage
-----
    ears = PtolemyEars(parent=ptolemy_widget)
    ears.set_response_handler(my_display_fn)
    ears.text_input("Hello, Ptolemy.")         # programmatic
    # or connect ears.lineEdit.returnPressed → ears.on_submit()

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
"""

from __future__ import annotations
import threading
from typing import Callable, Optional

from PyQt6.QtCore    import Qt, QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtGui     import QFont, QKeySequence
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit,
                              QPushButton, QLabel, QSizePolicy)

# Local imports — lazy so Ptolemy can boot without full Ainulindale chain loaded
def _get_chain():
    """Lazy import of NoetherChainInput to avoid circular boot."""
    from Philadelphos.noether_chain_input import NoetherChainInput
    return NoetherChainInput

def _get_tongue():
    """Lazy import of PtolemyTongue."""
    from Philadelphos.ptolemy_tongue import PtolemyTongue
    return PtolemyTongue


# ══════════════════════════════════════════════════════════════════════════════
#  GateWorker — off-thread submission when gate is closed
# ══════════════════════════════════════════════════════════════════════════════

class _GateWorker(QObject):
    """
    Runs submit() on a QThread so the Qt event loop never stalls
    when the SedenionGate is temporarily closed (chain processing).
    Emits submitted(text, BufferedPrompt) on completion.
    """
    submitted = pyqtSignal(str, object)   # (raw_text, BufferedPrompt)
    error     = pyqtSignal(str)

    def __init__(self, chain, text: str, parent=None):
        super().__init__(parent)
        self._chain = chain
        self._text  = text

    def run(self):
        try:
            prompt = self._chain.submit(self._text)
            self.submitted.emit(self._text, prompt)
        except Exception as e:
            self.error.emit(str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  PtolemyEars — main class
# ══════════════════════════════════════════════════════════════════════════════

class PtolemyEars(QWidget):
    """
    Ptolemy's text input widget.

    Provides:
        - QLineEdit for keyboard input
        - Submit button (Enter / click)
        - speak_text(text) slot for speech input (same pipeline)
        - Sedenion-gated submission via NoetherChainInput
        - Tongue-filtered response delivery
    """

    # Qt signals
    prompt_submitted = pyqtSignal(str)        # raw prompt text, before gate
    response_ready   = pyqtSignal(str)        # filtered response text

    def __init__(self, parent=None):
        super().__init__(parent)

        self._chain          : Optional[object] = None   # NoetherChainInput
        self._tongue         : Optional[object] = None   # PtolemyTongue
        self._response_handler: Optional[Callable[[str], None]] = None
        self._worker_thread  : Optional[QThread] = None
        self._processing     : bool = False

        self._build_ui()
        self._init_chain()

    # ── UI ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText("Speak to Ptolemy…")
        self.lineEdit.setFont(QFont('Ubuntu Mono', 10))
        self.lineEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lineEdit.returnPressed.connect(self.on_submit)
        layout.addWidget(self.lineEdit)

        self.sendBtn = QPushButton("→", self)
        self.sendBtn.setFixedWidth(28)
        self.sendBtn.setFont(QFont('Ubuntu Mono', 11))
        self.sendBtn.setToolTip("Submit (Enter)")
        self.sendBtn.clicked.connect(self.on_submit)
        layout.addWidget(self.sendBtn)

        self.statusLabel = QLabel("●", self)
        self.statusLabel.setFixedWidth(14)
        self.statusLabel.setFont(QFont('Ubuntu Mono', 9))
        self.statusLabel.setToolTip("Gate status: green=open, amber=processing")
        self._set_gate_indicator(open=True)
        layout.addWidget(self.statusLabel)

    def _set_gate_indicator(self, open: bool):
        color = '#00ff88' if open else '#ffaa00'
        self.statusLabel.setStyleSheet(f'color: {color}; background: transparent;')

    # ── Chain init ────────────────────────────────────────────────────────

    def _init_chain(self):
        """Initialise NoetherChainInput and PtolemyTongue. Non-fatal if missing."""
        try:
            ChainCls  = _get_chain()
            self._chain = ChainCls()
        except Exception as e:
            print(f"[PtolemyEars] NoetherChainInput unavailable: {e}")
            self._chain = None

        try:
            TongueCls    = _get_tongue()
            self._tongue = TongueCls()
        except Exception as e:
            print(f"[PtolemyEars] PtolemyTongue unavailable: {e}")
            self._tongue = None

    # ── Public API ────────────────────────────────────────────────────────

    def set_response_handler(self, fn: Callable[[str], None]):
        """Register function to receive filtered response text."""
        self._response_handler = fn
        self.response_ready.connect(fn)

    def text_input(self, text: str):
        """
        Programmatic input — same path as keyboard/speech.
        Can be called from any thread; gates automatically.
        """
        self._submit(text)

    def speak_text(self, text: str):
        """
        Speech recognition endpoint.
        SpeechInput calls this when a transcription is ready.
        Feeds the same normalised pipeline as keyboard input.
        """
        self.text_input(text)

    # ── Submission flow ───────────────────────────────────────────────────

    def on_submit(self):
        """Triggered by Enter key or Send button."""
        text = self.lineEdit.text().strip()
        if not text:
            return
        self.lineEdit.clear()
        self._submit(text)

    def _submit(self, text: str):
        """Gate → chain → response → tongue → display."""
        if not text:
            return

        self.prompt_submitted.emit(text)
        self._processing = True
        self._set_gate_indicator(open=False)

        if self._chain is None:
            # No chain — pass text through directly
            self._on_chain_complete(text, None)
            return

        # Off-thread to avoid stalling Qt event loop on gate.wait()
        worker      = _GateWorker(self._chain, text)
        thread      = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.submitted.connect(self._on_gate_submitted)
        worker.error.connect(self._on_gate_error)
        worker.submitted.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        self._worker_thread = thread
        thread.start()

    def _on_gate_submitted(self, text: str, prompt):
        """
        Gate has passed. BufferedPrompt is in context buffer.
        In the full pipeline this is where the model processes the prompt.
        For now: emit response_ready with the prompt text (echo mode until
        model is wired) then release the gate.
        """
        response = self._generate_response(text, prompt)
        self._on_chain_complete(text, response)

    def _on_gate_error(self, error_msg: str):
        print(f"[PtolemyEars] Gate error: {error_msg}")
        self._finish_cycle("")

    def _on_chain_complete(self, prompt_text: str, response: Optional[str]):
        """Apply tongue filter then deliver response."""
        if response is None:
            response = f"[echo] {prompt_text}"

        # Tongue filter — fold geometry applied last
        if self._tongue is not None:
            response = self._tongue.filter(response)

        # Release gate for next input
        if self._chain is not None:
            try:
                self._chain.release()
            except Exception:
                pass

        self._finish_cycle(response)

    def _finish_cycle(self, response: str):
        """Emit result and reset processing state."""
        self._processing = False
        self._set_gate_indicator(open=True)
        if response:
            self.response_ready.emit(response)

    def _generate_response(self, prompt_text: str, prompt) -> str:
        """
        Model invocation stub.
        Replaced when a PtolemyArchitectureInterface is plugged in.
        Currently returns a diagnostic echo.
        """
        # When NEURAL_ARCHITECTURE is loaded (ptolemy_core.py), wire here:
        #   return NEURAL_ARCHITECTURE.infer(prompt_text)
        sedenion_info = ""
        if prompt is not None:
            sedenion_info = (f" | sedenion_norm={prompt.sedenion.norm_sq():.4f}"
                             f" | tokens={prompt.token_count}"
                             f" | collapse={prompt.collapse_candidate}")
        return f"[Ptolemy{sedenion_info}] {prompt_text}"
