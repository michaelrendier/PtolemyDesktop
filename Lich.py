#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Lich.py — The Undead Emergency Manager                          Phase 6
========================================================================
Lives at Ptolemy ROOT.  Never a Face.  Never dies.

The Lich is the system's immune response.  In normal operation it is
dormant, running a watchdog timer and monitoring the bus health signal.
When Ptolemy fails — bus deadlock, uncaught exception, K0 thread death,
symptom_level spike — the Lich engages and orchestrates recovery.

Authority inversion during emergency
-------------------------------------
  Normal:    Bus manages Faces.  Aule manages bus slot requests.
  Emergency: Lich manages Bus.   Lich manages Aule.  Everything answers
             to Lich.  The Bus is Lich's tool, not its master.

The 7-step engage() sequence
-----------------------------
  1. Graceful Face quit     — bus.terminate() all registered Faces
  2. Freeze SMIP            — close SedenionGate; stop inference threads
  3. Flush caches           — CCB, blockchain pending, ForgeQueue
  4. Force-terminate        — kill threads that ignored step 1
  5. Desktop stays up       — QMainWindow / scene are NEVER touched
  6. Bus restarts clean     — new PtolBus under Lich authority
  7. Aule gets authority    — full thread pool released to Aule

Fast-resume path
-----------------
  After step 7 the bus is fresh and Aule has all slots.  Faces can be
  re-launched by Ptolemy in the same order they were launched at boot.
  The blockchain resurrection_mode() call at next boot detects the crash
  and can restore last known good state.

Threading contract
------------------
  engage() is safe to call from any thread (QTimer callback, signal, or
  sys.excepthook).  All steps guard with try/except — the Lich never
  propagates an exception outward.
"""

import sys
import os
import signal
import threading
import traceback
from enum import Enum, auto

from PyQt6.QtCore    import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import QApplication


# ══════════════════════════════════════════════════════════════════════════════
#  State machine
# ══════════════════════════════════════════════════════════════════════════════

class LichState(Enum):
    DORMANT    = auto()   # monitoring; normal operation
    ENGAGING   = auto()   # 7-step sequence in progress
    ENGAGED    = auto()   # full emergency authority held
    RESTORING  = auto()   # bus restarted; returning authority
    DISENGAGED = auto()   # returned to normal; will transition to DORMANT


# ══════════════════════════════════════════════════════════════════════════════
#  LichKing
# ══════════════════════════════════════════════════════════════════════════════

class LichKing(QObject):
    """
    The Undead Emergency Manager.

    Instantiate once, after msg_bus.start(), at Ptolemy.__init__ end.
    Pass the live Ptolemy instance — Lich holds a weak reference to it
    via normal attribute access (not a hard circular ref).

    Usage
    -----
        self.lich = LichKing(self)       # self = Ptolemy instance
        # That's it.  Lich wires itself.

    Manual engagement (e.g., from a debug shell)
    ----------------------------------------------
        ptolemy.lich.engage('manual override')
        ptolemy.lich.disengage()
    """

    state_changed  = pyqtSignal(str)    # LichState.name
    recovery_done  = pyqtSignal()       # fired when disengage() completes

    _AUTO_ENGAGE_THRESHOLD = 0.85       # symptom_level above which auto-engage
    _GRACE_MS              = 3000       # ms before force-terminate kicks in
    _WATCHDOG_MS           = 5000       # watchdog poll interval

    def __init__(self, ptolemy, parent=None):
        super().__init__(parent)
        self._ptolemy  = ptolemy
        self._state    = LichState.DORMANT
        self._lock     = threading.Lock()
        self._reason   = ''
        self._original_excepthook = sys.excepthook

        self._watchdog = QTimer(self)
        self._watchdog.setInterval(self._WATCHDOG_MS)
        self._watchdog.timeout.connect(self._watchdog_tick)
        self._watchdog.start()

        self._install_hooks()
        self._wire_bus()
        self._log('dormant — watchdog active')

    # ── Public API ─────────────────────────────────────────────────────────────

    def engage(self, reason: str = 'manual') -> None:
        """
        Engage emergency authority.  Safe to call from any thread.
        Idempotent: re-entrant calls while already ENGAGING/ENGAGED are dropped.
        """
        with self._lock:
            if self._state in (LichState.ENGAGING, LichState.ENGAGED):
                return
            self._state  = LichState.ENGAGING
            self._reason = reason

        self.state_changed.emit('ENGAGING')
        self._log(f'ENGAGE — reason: {reason}', 'WARN')

        try:
            self._step1_graceful_face_quit()
            self._step2_freeze_smip()
            self._step3_flush_caches()
            self._step4_force_terminate()
            # Step 5: Desktop stays up.  QMainWindow/scene are never touched.
            self._step6_restart_bus()
            self._step7_aule_authority()
        except Exception as exc:
            self._log(f'engage sequence error (non-fatal): {exc}', 'ERROR')

        with self._lock:
            self._state = LichState.ENGAGED
        self.state_changed.emit('ENGAGED')
        self._log('ENGAGED — authority held.  Call disengage() to restore.')

    def disengage(self) -> None:
        """Return authority to the bus and resume normal operation."""
        with self._lock:
            if self._state not in (LichState.ENGAGED, LichState.RESTORING):
                return
            self._state = LichState.RESTORING
        self.state_changed.emit('RESTORING')
        self._log('DISENGAGE — restoring normal authority')

        try:
            msg_bus = getattr(self._ptolemy, 'msg_bus', None)
            if msg_bus:
                msg_bus.disengage_emergency()
        except Exception as exc:
            self._log(f'disengage error: {exc}', 'WARN')

        # Re-open SedenionGate
        shell = getattr(self._ptolemy, 'PtolShell', None)
        if shell and hasattr(shell, '_ptol_busy'):
            shell._ptol_busy = False
            self._log('  SedenionGate reopened')

        with self._lock:
            self._state = LichState.DORMANT
        self.state_changed.emit('DORMANT')
        self.recovery_done.emit()
        self._log('DORMANT — normal operation resumed')

    @property
    def state(self) -> LichState:
        return self._state

    @property
    def is_engaged(self) -> bool:
        return self._state == LichState.ENGAGED

    # ── Step 1: Graceful Face quit ─────────────────────────────────────────────

    def _step1_graceful_face_quit(self) -> None:
        self._log('step 1 — graceful Face quit')
        bus = getattr(self._ptolemy, 'bus', None)
        if bus and hasattr(bus, '_registry'):
            for fid in list(bus._registry.keys()):
                try:
                    bus.terminate(fid)
                    self._log(f'    terminated: {fid}')
                except Exception as exc:
                    self._log(f'    terminate {fid} failed: {exc}', 'WARN')

        # Signal the bus to drain non-T0 and park autonomous slots
        msg_bus = getattr(self._ptolemy, 'msg_bus', None)
        if msg_bus:
            try:
                msg_bus.engage_emergency(self, reason=self._reason)
                self._log('    bus in emergency mode')
            except Exception as exc:
                self._log(f'    bus engage_emergency failed: {exc}', 'WARN')

    # ── Step 2: Freeze SMIP ────────────────────────────────────────────────────

    def _step2_freeze_smip(self) -> None:
        self._log('step 2 — freeze SMIP pipeline')
        shell = getattr(self._ptolemy, 'PtolShell', None)
        if shell is None:
            return

        # Close SedenionGate
        if hasattr(shell, '_ptol_busy'):
            shell._ptol_busy = True
            self._log('    SedenionGate closed')

        # Stop active inference thread (PtolBrain path)
        for attr in ('_smip_thread', '_phila'):
            t = getattr(shell, attr, None)
            if t is None:
                continue
            try:
                if hasattr(t, 'isRunning') and t.isRunning():
                    t.quit()
                    t.wait(self._GRACE_MS // 2)
                    self._log(f'    {attr} stopped')
            except Exception as exc:
                self._log(f'    {attr} stop error: {exc}', 'WARN')

    # ── Step 3: Flush caches ───────────────────────────────────────────────────

    def _step3_flush_caches(self) -> None:
        self._log('step 3 — flush caches')

        # CyclicContextBuffer
        ccb = getattr(self._ptolemy, 'ccb', None)
        if ccb:
            try:
                if hasattr(ccb, 'flush'):
                    ccb.flush()
                    self._log('    CCB flushed')
            except Exception as exc:
                self._log(f'    CCB flush error: {exc}', 'WARN')

        # Blockchain — flush any pending uncommitted transactions
        chain = getattr(self._ptolemy, '_chain', None)
        if chain:
            for method in ('flush_pending', 'commit_pending', 'flush'):
                if hasattr(chain, method):
                    try:
                        getattr(chain, method)()
                        self._log(f'    blockchain.{method}() called')
                        break
                    except Exception as exc:
                        self._log(f'    blockchain.{method} error: {exc}', 'WARN')
                        break

        # ForgeQueue — flush queued forge jobs
        fq = getattr(self._ptolemy, 'forge_queue', None)
        if fq:
            for method in ('flush', 'drain'):
                if hasattr(fq, method):
                    try:
                        getattr(fq, method)()
                        self._log(f'    ForgeQueue.{method}() called')
                        break
                    except Exception as exc:
                        self._log(f'    ForgeQueue.{method} error: {exc}', 'WARN')
                        break

    # ── Step 4: Force-terminate ────────────────────────────────────────────────

    def _step4_force_terminate(self) -> None:
        self._log('step 4 — force-terminate stragglers')
        msg_bus = getattr(self._ptolemy, 'msg_bus', None)
        if msg_bus is None:
            return
        slots = getattr(msg_bus, '_slots', {})
        for name, slot in slots.items():
            thread = getattr(slot, 'thread', None)
            if thread is None:
                continue
            role = getattr(slot, 'role', '')
            # Only force non-kernel face threads; never kill K0-K4
            if not role.startswith('face_'):
                continue
            try:
                if hasattr(thread, 'isRunning') and thread.isRunning():
                    thread.terminate()
                    thread.wait(500)
                    self._log(f'    force-terminated: {name} ({role})')
            except Exception as exc:
                self._log(f'    force-terminate {name} error: {exc}', 'WARN')

    # Step 5: Desktop stays up.  QMainWindow / scene are NEVER touched.
    # The desktop is the floor.  It cannot be a Face.  It cannot die.

    # ── Step 6: Restart bus ────────────────────────────────────────────────────

    def _step6_restart_bus(self) -> None:
        self._log('step 6 — restart bus clean')
        old_bus = getattr(self._ptolemy, 'msg_bus', None)
        if old_bus is None:
            return

        try:
            old_bus.stop()
            self._log('    old bus stopped')
        except Exception as exc:
            self._log(f'    old bus stop error: {exc}', 'WARN')

        try:
            from Pharos.PtolBus import PtolBus as _PtolBus
            new_bus = _PtolBus(ptolemy=self._ptolemy, parent=self._ptolemy)
            new_bus.start()
            self._ptolemy.msg_bus = new_bus
            self._log('    new bus started')

            # Re-wire Lich monitoring to new bus
            new_bus.symptom_level_changed.connect(self._on_symptom_change)
            new_bus.emergency_engaged.connect(
                lambda r: self._log(f'bus emergency signal: {r}')
            )

            # Re-wire blockchain subscriber
            chain = getattr(self._ptolemy, '_chain', None)
            if chain and hasattr(chain, 'bus_handler'):
                from Pharos.PtolBus import CH_BLOCKCHAIN
                new_bus.subscribe(CH_BLOCKCHAIN, chain.bus_handler)
                self._log('    blockchain subscriber rewired')

            # Re-wire luthspell
            ls = getattr(self._ptolemy, 'luthspell', None)
            if ls and hasattr(ls, 'wire'):
                ls.wire()
                self._log('    luthspell rewired')

        except Exception as exc:
            self._log(f'step 6 error: {exc}', 'ERROR')

    # ── Step 7: Aule authority ─────────────────────────────────────────────────

    def _step7_aule_authority(self) -> None:
        self._log('step 7 — Aule gets full thread pool authority')
        fq = getattr(self._ptolemy, 'forge_queue', None)
        if fq is None:
            self._log('    ForgeQueue not present', 'WARN')
            return

        # claim_full_authority is a future ForgeQueue method (Phase 7)
        if hasattr(fq, 'claim_full_authority'):
            try:
                fq.claim_full_authority()
                self._log('    Aule: full authority claimed')
            except Exception as exc:
                self._log(f'    claim_full_authority error: {exc}', 'WARN')
        else:
            # Stub: resume any stalled forge jobs
            try:
                if hasattr(fq, 'resume') and not fq.isRunning():
                    fq.resume()
                self._log('    Aule: ForgeQueue active (claim_full_authority pending Phase 7)')
            except Exception as exc:
                self._log(f'    Aule stub error: {exc}', 'WARN')

    # ── Watchdog ───────────────────────────────────────────────────────────────

    def _watchdog_tick(self) -> None:
        """Periodic K0 liveness check.  If K0 is dead, engage."""
        if self._state != LichState.DORMANT:
            return
        msg_bus = getattr(self._ptolemy, 'msg_bus', None)
        if msg_bus is None:
            return
        slots = getattr(msg_bus, '_slots', {})
        k0 = slots.get('dispatch_K0')
        if k0 is None:
            return
        thread = getattr(k0, 'thread', None)
        if thread is not None and hasattr(thread, 'isRunning'):
            if not thread.isRunning():
                self.engage(reason='watchdog: K0 dispatch thread dead')

    def _on_symptom_change(self, level: float) -> None:
        """Auto-engage when bus health degrades past threshold."""
        if self._state != LichState.DORMANT:
            return
        if level >= self._AUTO_ENGAGE_THRESHOLD:
            self.engage(
                reason=f'watchdog: symptom_level {level:.2f} >= {self._AUTO_ENGAGE_THRESHOLD}'
            )

    # ── System hooks ───────────────────────────────────────────────────────────

    def _install_hooks(self) -> None:
        """Override sys.excepthook and SIGTERM handler."""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._excepthook

        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (OSError, ValueError):
            pass   # may not be main thread; safe to skip

        self._log('hooks installed: excepthook, SIGTERM')

    def _excepthook(self, exc_type, exc_value, exc_tb) -> None:
        tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self._log(f'UNCAUGHT EXCEPTION:\n{tb}', 'ERROR')
        if self._state == LichState.DORMANT:
            self.engage(reason=f'uncaught exception: {exc_type.__name__}')
        self._original_excepthook(exc_type, exc_value, exc_tb)

    def _signal_handler(self, signum, frame) -> None:
        self._log(f'signal {signum} received')
        if self._state == LichState.DORMANT:
            self.engage(reason=f'signal {signum}')

    # ── Bus wiring ─────────────────────────────────────────────────────────────

    def _wire_bus(self) -> None:
        """Connect to msg_bus signals for passive monitoring."""
        msg_bus = getattr(self._ptolemy, 'msg_bus', None)
        if msg_bus is None:
            return
        try:
            msg_bus.symptom_level_changed.connect(self._on_symptom_change)
            msg_bus.emergency_engaged.connect(
                lambda r: self._log(f'bus emergency signal received: {r}')
            )
            self._log('wired to msg_bus signals')
        except Exception as exc:
            self._log(f'bus wire error: {exc}', 'WARN')

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = 'INFO') -> None:
        tag = f'[Lich/{level}]'
        print(f'{tag} {msg}', flush=True)
        try:
            from Pharos.PtolDmesg import dmesg
            if level == 'ERROR':
                dmesg.fail('lich', msg)
            elif level == 'WARN':
                dmesg.warn('lich', msg)
            else:
                dmesg.write('lich', msg)
        except Exception:
            pass
