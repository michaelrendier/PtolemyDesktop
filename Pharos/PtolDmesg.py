#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
PtolDmesg.py — Ptolemy System Message Log
==========================================
Pharos Core Layer

Faces SUBMIT events. Aule (the Forge) is the SOLE WRITER to dmesg.
Mirrors Linux kernel ring buffer — one file, all voices, timestamped.

Architecture:
    Face  →  dmesg.submit(face, message)  →  Aule writes to disk
    Aule  →  dmesg._write_line()          →  /var/ptolemy/dmesg.log

No Face writes directly. All writes pass through Aule's forge queue.
Aule may annotate, repair, escalate, or hold entries before committing.

Log file:  /var/ptolemy/dmesg.log  (fallback: ~/ptolemy_dmesg.log)

Format:
    [  0.000] pharos      :: boot initiated
    [  0.012] pharos      :: core online
    [  0.034] aule        :: forge ready
    [  1.204] archimedes  :: /math triggered — "E=mc^2"
    [  2.891] aule        :: WARN — archimedes code write detected
    [  2.901] aule        :: PASS

Severity prefixes (written inline):
    (none)   — nominal / informational
    WARN     — degraded, continuing
    ERROR    — failure, attempting recovery
    FATAL    — unrecoverable, Aule notified
    POST     — boot self-test result
    FACE_IN  — Face subshell spawned
    FACE_OUT — Face subshell exited

Usage (every Face does this on spawn):
    from Pharos.PtolDmesg import dmesg

    dmesg.write('archimedes', 'SymPy loaded OK')
    dmesg.post('archimedes', passed=True)
    dmesg.warn('tesla', 'no devices detected')
    dmesg.error('callimachus', 'DB connection failed')
    dmesg.face_in('archimedes')
    dmesg.face_out('archimedes')

Thread-safe. Multiple Faces may write concurrently.
"""

import os
import threading
import datetime
from pathlib import Path
from typing import Optional


# ── Log file location ─────────────────────────────────────────────────────────

_PRIMARY_PATH   = Path('/var/ptolemy/dmesg.log')
_FALLBACK_PATH  = Path.home() / 'ptolemy_dmesg.log'

def _resolve_log_path() -> Path:
    try:
        _PRIMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _PRIMARY_PATH.touch(exist_ok=True)
        return _PRIMARY_PATH
    except PermissionError:
        return _FALLBACK_PATH

_LOG_PATH: Path = _resolve_log_path()

# Boot epoch — all timestamps relative to first import
_BOOT_TIME: float = datetime.datetime.now().timestamp()


# ── PtolDmesg ─────────────────────────────────────────────────────────────────

class PtolDmesg:
    """
    Thread-safe dmesg writer.
    One instance shared across all Faces via module-level `dmesg` singleton.
    """

    def __init__(self, log_path: Path):
        self._path  = log_path
        self._lock  = threading.Lock()
        self._boot  = _BOOT_TIME

    # ── Internal ──────────────────────────────────────────────────────────────

    def _elapsed(self) -> str:
        """Seconds since boot, kernel dmesg style: [  1.234]"""
        secs = datetime.datetime.now().timestamp() - self._boot
        return f'[{secs:8.3f}]'

    def _forge_write(self, face: str, message: str) -> None:
        """Aule owns this. Sole writer to dmesg. Faces call submit methods."""
        face_col = f'{face:<12}'
        line = f'{self._elapsed()} {face_col} :: {message}\n'
        with self._lock:
            try:
                with open(self._path, 'a', encoding='utf-8') as f:
                    f.write(line)
            except OSError:
                pass

    def _write_line(self, face: str, message: str) -> None:
        self._forge_write(face, message)

    # ── Public API — Faces SUBMIT, Aule WRITES via Forge ──────────────────────

    def write(self, face: str, message: str) -> None:
        """Submit nominal message. Aule writes it."""
        self._forge_write(face.lower(), message)

    def warn(self, face: str, message: str) -> None:
        self._write_line(face.lower(), f'WARN — {message}')

    def error(self, face: str, message: str) -> None:
        self._write_line(face.lower(), f'ERROR — {message}')

    def fatal(self, face: str, message: str) -> None:
        self._write_line(face.lower(), f'FATAL — {message}')

    def post(self, face: str, passed: bool, detail: str = '') -> None:
        """POST self-test result on Face spawn."""
        status = 'PASS' if passed else 'FAIL'
        msg = f'POST {status}'
        if detail:
            msg += f' — {detail}'
        self._write_line(face.lower(), msg)

    def face_in(self, face: str) -> None:
        """Face subshell spawned."""
        self._write_line(face.lower(), f'FACE_IN — subshell active')

    def face_out(self, face: str) -> None:
        """Face subshell exited, returned to Ptolemy root."""
        self._write_line(face.lower(), f'FACE_OUT — returned to ptolemy')

    def bus(self, face: str, channel: str, message: str) -> None:
        """Bus event — Face wrote to a named channel."""
        self._write_line(face.lower(), f'BUS:{channel} — {message}')

    def boot(self) -> None:
        """Write boot header. Called once by Pharos on system start."""
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._lock:
            try:
                with open(self._path, 'a', encoding='utf-8') as f:
                    f.write(f'\n{"="*60}\n')
                    f.write(f'Ptolemy boot  {ts}\n')
                    f.write(f'log: {self._path}\n')
                    f.write(f'{"="*60}\n')
            except OSError:
                pass

    def tail(self, n: int = 40) -> list[str]:
        """Return last n lines from dmesg log."""
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                return f.readlines()[-n:]
        except OSError:
            return []

    def clear(self) -> None:
        """Clear the log (operator use only)."""
        with self._lock:
            try:
                with open(self._path, 'w', encoding='utf-8') as f:
                    f.write('')
            except OSError:
                pass

    @property
    def path(self) -> Path:
        return self._path


# ── Module-level singleton ────────────────────────────────────────────────────
# Every Face does:  from Pharos.PtolDmesg import dmesg

dmesg = PtolDmesg(_LOG_PATH)
