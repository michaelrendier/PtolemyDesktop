#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PtolFace.py — Bus Contract Mixin
==================================
Pharos Face / Core Layer

Every Face that plugs into PtolBus inherits this mixin.
It provides the threading contract (_ptol_thread, _ptol_timers)
and a standard lifecycle without requiring Faces to know about the bus.

Usage
-----
    class TreasureHunt(QMainWindow, PtolFace):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.ptol_init()          # call after super().__init__
            # ... your __init__ ...

        def ptol_start(self):
            \"\"\"Called by bus on launch/resume. Start your timers here.\"\"\"
            self.my_timer.start()

        def ptol_stop(self):
            \"\"\"Called by bus on suspend. Stop your timers here.\"\"\"
            self.my_timer.stop()

        def ptol_close(self):
            \"\"\"Called by bus on terminate. Clean up resources here.\"\"\"
            pass

Bus threading contract
----------------------
    face._ptol_thread   QThread or None
    face._ptol_timers   list of QTimer
    face._ptol_id       face_id assigned by bus on launch
    face._ptol_bus      PtolBus reference (set by bus on launch)
"""

from PyQt6.QtCore import QThread, QTimer


class PtolFace:
    """
    Mixin for all Ptolemy Faces.
    Provides bus contract, lifecycle hooks, and convenience helpers.
    Inherit alongside QWidget / QMainWindow.
    """

    def ptol_init(self):
        """Call at the top of your Face __init__, after super().__init__."""
        self._ptol_thread: QThread = None
        self._ptol_timers: list    = []
        self._ptol_id:     str     = None
        self._ptol_bus            = None

    # ── Lifecycle hooks — override in Face ───────────────────────────────────

    def ptol_start(self):
        """Resume: called on launch and restore from minimize. Start timers."""
        if not self._ptol_id:
            return
        ptol = self.ptolemy
        if ptol:
            try:
                ptol.msg_bus.post_face(
                    self._ptol_id, self.__class__.__name__, [], thread_req=4)
            except Exception:
                pass
            try:
                from Pharos.PtolDmesg import dmesg
                dmesg.face_in(self._ptol_id)
            except Exception:
                pass

    def ptol_stop(self):
        """Suspend: called on minimize. Stop timers."""
        pass

    def ptol_close(self):
        """Terminate: called on window close. Release resources."""
        if not self._ptol_id:
            return
        ptol = self.ptolemy
        if ptol:
            try:
                ptol.msg_bus.unpost_face(self._ptol_id)
            except Exception:
                pass
            try:
                from Pharos.PtolDmesg import dmesg
                dmesg.face_out(self._ptol_id)
            except Exception:
                pass

    # ── Convenience ──────────────────────────────────────────────────────────

    def ptol_register_timer(self, interval_ms: int, slot) -> QTimer:
        """
        Create and register a QTimer with the bus contract.
        Bus will stop/start it on suspend/resume automatically.

            self.poll_timer = self.ptol_register_timer(500, self.poll)
        """
        t = QTimer(self if hasattr(self, 'startTimer') else None)
        t.setInterval(interval_ms)
        t.timeout.connect(slot)
        self._ptol_timers.append(t)
        return t

    def ptol_register_thread(self, thread: QThread) -> QThread:
        """Register a QThread with the bus contract."""
        self._ptol_thread = thread
        return thread

    @property
    def ptolemy(self):
        """Convenience accessor for the root Ptolemy instance via bus."""
        if self._ptol_bus is not None:
            return self._ptol_bus.Ptolemy
        # fallback — walk parent chain
        p = self.parent() if hasattr(self, 'parent') else None
        while p is not None:
            if hasattr(p, 'bus') and hasattr(p, 'scene'):
                return p
            p = p.parent() if hasattr(p, 'parent') else None
        return None
