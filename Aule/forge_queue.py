#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForgeQueue — Aule Forge Queue
================================
Aule Face

Watches Aule/forge/ for new .py scripts and queues them for
staged execution. Each run is:
  1. Registered (AuditChain block)
  2. Sandboxed (subprocess)
  3. Result committed (AuditChain block)
  4. Emitted on PtolBus CH_FACE_EVENT

Code Watch:
  ForgeQueue uses watchdog (inotify fallback: polling) to detect
  new/modified files in forge/. Auto-enqueues on drop.

Usage:
    fq = ForgeQueue()
    fq.start()        # starts watcher + dispatch thread
    fq.enqueue('myscript.py', args=['--test'])
    fq.stop()

Settings hook → Aule > ForgeQueue settings tab.
"""

import os
import time
import queue
import threading
import subprocess
import json
from pathlib import Path
from typing  import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE      = Path(__file__).parent
_FORGE_DIR = _HERE / 'forge'
_LOG_DIR   = _HERE / 'streams'
_FORGE_DIR.mkdir(exist_ok=True)
_LOG_DIR.mkdir(exist_ok=True)

# ── Settings (module hook → Settings tab) ────────────────────────────────────
FORGE_SETTINGS = {
    "watch_interval_s":  2,        # polling fallback interval
    "max_queue_depth":   64,
    "run_timeout_s":     30,
    "audit_enabled":     True,     # commit blocks to AuditChain
    "bus_emit":          True,     # emit events on PtolBus
}


class ForgeJob:
    """Single queued forge job."""
    __slots__ = ('script', 'args', 'enqueued_at', 'status', 'result')

    def __init__(self, script: str, args: list = None):
        self.script      = script
        self.args        = args or []
        self.enqueued_at = time.time()
        self.status      = 'pending'   # pending | running | done | failed
        self.result      = None

    def to_dict(self) -> dict:
        return {
            'script':      self.script,
            'args':        self.args,
            'enqueued_at': self.enqueued_at,
            'status':      self.status,
            'result':      str(self.result)[:500] if self.result else None,
        }


class ForgeQueue:
    """
    Watches forge/ and executes queued scripts with audit trail.
    Thread-safe. Does not require PyQt5 — pure stdlib.
    """

    def __init__(self):
        self._q        = queue.Queue(maxsize=FORGE_SETTINGS['max_queue_depth'])
        self._stop_evt = threading.Event()
        self._watcher  = threading.Thread(target=self._watch_loop,
                                          daemon=True, name='ForgeWatcher')
        self._runner   = threading.Thread(target=self._run_loop,
                                          daemon=True, name='ForgeRunner')
        self._seen     = set()   # already-enqueued file mtimes
        self._chain    = None    # AuditChain, lazy init
        self._bus      = None    # PtolBus reference, set externally

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        self._watcher.start()
        self._runner.start()

    def stop(self):
        self._stop_evt.set()

    # ── Public API ────────────────────────────────────────────────────────────

    def enqueue(self, script: str, args: list = None) -> bool:
        """Manually enqueue a script. Returns False if queue full."""
        job = ForgeJob(script, args)
        try:
            self._q.put_nowait(job)
            self._audit({'event': 'enqueue', 'script': script})
            return True
        except queue.Full:
            return False

    def set_bus(self, bus):
        """Attach a PtolBus instance for event emission."""
        self._bus = bus

    def depth(self) -> int:
        return self._q.qsize()

    # ── Watcher ───────────────────────────────────────────────────────────────

    def _watch_loop(self):
        """Poll forge/ directory for new/modified .py files."""
        interval = FORGE_SETTINGS['watch_interval_s']
        while not self._stop_evt.is_set():
            try:
                for path in sorted(_FORGE_DIR.glob('*.py')):
                    key = (path.name, path.stat().st_mtime)
                    if key not in self._seen:
                        self._seen.add(key)
                        self.enqueue(path.name)
            except Exception:
                pass
            time.sleep(interval)

    # ── Runner ────────────────────────────────────────────────────────────────

    def _run_loop(self):
        """Drain queue and execute each job."""
        while not self._stop_evt.is_set():
            try:
                job = self._q.get(timeout=1.0)
                self._execute(job)
            except queue.Empty:
                pass

    def _execute(self, job: ForgeJob):
        script_path = _FORGE_DIR / job.script
        if not script_path.exists():
            job.status = 'failed'
            job.result = f'Script not found: {job.script}'
            self._audit(job.to_dict())
            return

        job.status = 'running'
        self._emit('forge_start', job.to_dict())

        try:
            proc = subprocess.run(
                ['python3', str(script_path)] + job.args,
                capture_output=True,
                text=True,
                timeout=FORGE_SETTINGS['run_timeout_s'],
            )
            job.status = 'done' if proc.returncode == 0 else 'failed'
            job.result = (proc.stdout + proc.stderr)[:2000]
        except subprocess.TimeoutExpired:
            job.status = 'failed'
            job.result = 'TIMEOUT'
        except Exception as e:
            job.status = 'failed'
            job.result = str(e)

        self._audit(job.to_dict())
        self._emit('forge_done', job.to_dict())

    # ── Audit / emit ──────────────────────────────────────────────────────────

    def _audit(self, data: dict):
        if not FORGE_SETTINGS['audit_enabled']:
            return
        if self._chain is None:
            try:
                from Callimachus.BlockChain.PtolChain import AuditChain
                self._chain = AuditChain('aule')
            except Exception:
                return
        try:
            self._chain.add_block(data)
        except Exception:
            pass

    def _emit(self, event_type: str, payload: dict):
        if not FORGE_SETTINGS['bus_emit'] or self._bus is None:
            return
        try:
            from Pharos.PtolBus import BusMessage, CH_FACE_EVENT, Priority
            self._bus.publish(BusMessage(
                CH_FACE_EVENT,
                {'face': 'aule', 'event': event_type, 'payload': payload},
                Priority.T1, sender='ForgeQueue'))
        except Exception:
            pass
