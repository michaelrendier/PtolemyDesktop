#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
FaceIdentity.py — Shell Identity for Ptolemy Faces
====================================================
Pharos Core Layer

Faces are treated as users in the shell. This module defines:

  1. FaceUser — shell username and display name per Face
  2. DaemonIdentity — daemon "login" POST boot report
  3. ShellPrompt — ANSI prompt string factory for in-shell Face messages
  4. FaceReport — structured diagnostic report (Face → Face communication)

Shell model
-----------
  - O Captain gets the normal Linux prompt:  rendier@machine:~$
  - A Face speaking uses:                    [Alexandria]>  (in Face color)
  - A Daemon reports POST-style:             [PharosBus daemon] INIT OK — bus ready

Daemon login convention
-----------------------
  Daemons do not sign in. They report diagnostics at boot, like a POST.
  Format:
      [<DaemonName> daemon] <STATUS> — <message>
  STATUS values: INIT, OK, WARN, FAIL, HALT

Face → Face communication in the shell
---------------------------------------
  Any Face can write to the shell under its own name:
      [Callimachus] → [Archimedes]: index rebuild recommended — 14 incomplete words

Usage
-----
    from Pharos.FaceIdentity import FaceUser, DaemonIdentity, ShellPrompt

    # Get Face identity
    face = FaceUser.ARCHIMEDES
    print(face.username)     # 'archimedes'
    print(face.display)      # 'Archimedes'
    print(face.color)        # '#7ec8e3'

    # Format a Face shell message
    msg = ShellPrompt.face_say('Archimedes', 'index rebuild complete')
    # → '\x1b[38;2;126;200;227m[Archimedes]>\x1b[0m index rebuild complete'

    # Daemon POST report
    boot = DaemonIdentity.post('PharosBus', 'INIT', 'bus ready')
    # → '\x1b[33m[PharosBus daemon] INIT — bus ready\x1b[0m'

    # Face → Face message
    msg = ShellPrompt.face_to_face('Callimachus', 'Archimedes', 'index ready')
    # → '[Callimachus] → [Archimedes]: index ready'
"""

import os
import datetime
from dataclasses import dataclass, field
from typing import Optional

from Pharos.PtolColor import FaceColor


# ══════════════════════════════════════════════════════════════════════════════
#  FaceUser — one record per Face
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class FaceUser:
    """Identity record for a Face acting as a shell user."""
    username: str          # lowercase, no spaces — shell username convention
    display:  str          # CamelCase display name
    color:    str          # hex color from FaceColor
    role:     str          # one-line role description

    def ansi_color(self) -> str:
        """Convert #rrggbb to ANSI 24-bit foreground escape."""
        h = self.color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f'\x1b[38;2;{r};{g};{b}m'

    def prompt_prefix(self) -> str:
        """Colored [Display]> prompt prefix string."""
        return f'{self.ansi_color()}[{self.display}]>\x1b[0m'


# ── Canonical Face registry ────────────────────────────────────────────────────

PHAROS       = FaceUser('pharos',       'Pharos',       FaceColor.PHAROS,       'primary core — runtime, bus, shell, entry point')
CALLIMACHUS  = FaceUser('callimachus',  'Callimachus',  FaceColor.CALLIMACHUS,  'secondary core — all data I/O, sole entry to storage')
ARCHIMEDES   = FaceUser('archimedes',   'Archimedes',   FaceColor.ARCHIMEDES,   'mathematics and science')
ALEXANDRIA   = FaceUser('alexandria',   'Alexandria',   FaceColor.ALEXANDRIA,   'OpenGL visualization')
ANAXIMANDER  = FaceUser('anaximander',  'Anaximander',  FaceColor.ANAXIMANDER,  'navigation and travel')
KRYPTOS      = FaceUser('kryptos',      'Kryptos',      FaceColor.KRYPTOS,      'encryption — .perm files')
PHALERON     = FaceUser('phaleron',     'Phaleron',     FaceColor.PHALERON,     'internal search')
TESLA        = FaceUser('tesla',        'Tesla',        FaceColor.TESLA,        'device interfacing')
MOUSEION     = FaceUser('mouseion',     'Mouseion',     FaceColor.MOUSEION,     'Flask website — thewanderinggod.tech')
PHILADELPHOS = FaceUser('philadelphos', 'Philadelphos', FaceColor.PHILADELPHOS, 'LLM and model experimentation')
PTOLCPP      = FaceUser('ptolcpp',      'PtolCPP',      FaceColor.PTOLCPP,      'C++ port — performance-critical components')
AINULINDALE  = FaceUser('ainulindale',  'Ainulindale',  FaceColor.AINULINDALE,  'prefilter staging — work lands here before Ptolemy integration')

# Lookup by name (case-insensitive)
_REGISTRY: dict[str, FaceUser] = {
    'pharos':       PHAROS,
    'callimachus':  CALLIMACHUS,
    'archimedes':   ARCHIMEDES,
    'alexandria':   ALEXANDRIA,
    'anaximander':  ANAXIMANDER,
    'kryptos':      KRYPTOS,
    'phaleron':     PHALERON,
    'tesla':        TESLA,
    'mouseion':     MOUSEION,
    'philadelphos': PHILADELPHOS,
    'ptolcpp':      PTOLCPP,
    'ainulindale':  AINULINDALE,
}

def get_face(name: str) -> Optional[FaceUser]:
    """Return FaceUser by name (case-insensitive). None if not found."""
    return _REGISTRY.get(name.lower())

def all_faces() -> list[FaceUser]:
    return list(_REGISTRY.values())


# ══════════════════════════════════════════════════════════════════════════════
#  DaemonIdentity — POST-style boot reports
# ══════════════════════════════════════════════════════════════════════════════

class DaemonStatus:
    INIT = 'INIT'   # first contact — daemon starting
    OK   = 'OK'     # nominal
    WARN = 'WARN'   # degraded but running
    FAIL = 'FAIL'   # component failed, daemon continuing
    HALT = 'HALT'   # daemon stopping


class DaemonIdentity:
    """
    Daemons do not sign in — they report like POST.
    Format:  [DaemonName daemon] STATUS — message
    """

    # ANSI: daemon reports in amber-gold
    _DAEMON_COLOR = FaceColor.DAEMON
    _ANSI_DAEMON  = '\x1b[38;2;255;204;0m'
    _ANSI_WARN    = '\x1b[38;2;255;165;0m'
    _ANSI_FAIL    = '\x1b[38;2;220;50;50m'
    _ANSI_RESET   = '\x1b[0m'

    @staticmethod
    def post(daemon_name: str, status: str, message: str) -> str:
        """
        Format a daemon POST report string (ANSI colored).
        Output goes to stdout/shell — not Qt widget.

            DaemonIdentity.post('PharosBus', DaemonStatus.INIT, 'bus ready')
            → '[PharosBus daemon] INIT — bus ready'
        """
        color = DaemonIdentity._ANSI_DAEMON
        if status in (DaemonStatus.WARN,):
            color = DaemonIdentity._ANSI_WARN
        elif status in (DaemonStatus.FAIL, DaemonStatus.HALT):
            color = DaemonIdentity._ANSI_FAIL
        return f"{color}[{daemon_name} daemon] {status} — {message}{DaemonIdentity._ANSI_RESET}"

    @staticmethod
    def print_post(daemon_name: str, status: str, message: str) -> None:
        """Print a POST report directly to stdout."""
        print(DaemonIdentity.post(daemon_name, status, message), flush=True)

    @staticmethod
    def boot_sequence(daemon_name: str, items: list[tuple[str, str]]) -> None:
        """
        Print a full boot sequence — like BIOS POST rows.
        items: list of (component, message) tuples. All print as OK unless
               message starts with WARN/FAIL/HALT.

        Usage:
            DaemonIdentity.boot_sequence('PharosBus', [
                ('registry',    'initialized'),
                ('thread pool', 'WARN — only 2 workers available'),
                ('PtolBus IPC', 'OK — socket bound'),
            ])
        """
        ts = datetime.datetime.now().strftime('%H:%M:%S')
        print(f'\x1b[2m{ts}\x1b[0m  \x1b[1m[{daemon_name} daemon]\x1b[0m  boot sequence', flush=True)
        for component, message in items:
            msg_upper = message.upper()
            if any(msg_upper.startswith(s) for s in ('FAIL', 'HALT')):
                status = DaemonStatus.FAIL
            elif msg_upper.startswith('WARN'):
                status = DaemonStatus.WARN
            else:
                status = DaemonStatus.OK
            print(f'  {DaemonIdentity.post(component, status, message)}', flush=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ShellPrompt — Face message formatting for PtolShell output
# ══════════════════════════════════════════════════════════════════════════════

class ShellPrompt:
    """
    Format ANSI strings for Face messages in the shell.
    All methods return strings — callers write to shell/pty.
    """

    @staticmethod
    def face_say(face_name: str, message: str) -> str:
        """
        A Face speaking in the shell under its own name.
        [Archimedes]> index rebuild complete
        """
        face = get_face(face_name)
        if face is None:
            return f'[{face_name}]> {message}'
        return f'{face.prompt_prefix()} {message}'

    @staticmethod
    def face_to_face(sender: str, recipient: str, message: str) -> str:
        """
        Face → Face communication in the shell.
        [Callimachus] → [Archimedes]: index ready
        """
        s = get_face(sender)
        r = get_face(recipient)

        s_str = f'{s.ansi_color()}[{s.display}]\x1b[0m' if s else f'[{sender}]'
        r_str = f'{r.ansi_color()}[{r.display}]\x1b[0m' if r else f'[{recipient}]'
        arrow = '\x1b[2m→\x1b[0m'
        return f'{s_str} {arrow} {r_str}: {message}'

    @staticmethod
    def face_report(sender: str, severity: str, message: str) -> str:
        """
        A Face filing a diagnostic report.
        [Kryptos] WARN: .perm file checksum mismatch on startup
        severity: INFO | WARN | ERROR | FATAL
        """
        face = get_face(sender)
        sev_colors = {
            'INFO':  '\x1b[36m',   # cyan
            'WARN':  '\x1b[33m',   # amber
            'ERROR': '\x1b[31m',   # red
            'FATAL': '\x1b[35m',   # magenta
        }
        sev_color = sev_colors.get(severity.upper(), '\x1b[0m')
        prefix = f'{face.ansi_color()}[{face.display}]\x1b[0m' if face else f'[{sender}]'
        return f'{prefix} {sev_color}{severity.upper()}\x1b[0m: {message}'

    @staticmethod
    def print_face_say(face_name: str, message: str) -> None:
        print(ShellPrompt.face_say(face_name, message), flush=True)

    @staticmethod
    def print_face_to_face(sender: str, recipient: str, message: str) -> None:
        print(ShellPrompt.face_to_face(sender, recipient, message), flush=True)

    @staticmethod
    def print_face_report(sender: str, severity: str, message: str) -> None:
        print(ShellPrompt.face_report(sender, severity, message), flush=True)
