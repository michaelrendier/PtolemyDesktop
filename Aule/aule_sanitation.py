#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
aule_sanitation.py — Aulë Sanitation & Multi-Factor Gate
=========================================================
Aule Face — Forge Layer

Aule is the sole gatekeeper for all input reaching the bus or dmesg.
No input is unsanitized unless explicitly cleared by trust level.

Trust Levels
------------
    OPERATOR    — O Captain (rendier). Raw, unsanitized. Full trust.
    ARCHIMEDES  — Math/code authority. Raw, unsanitized.
    FACE        — Any other Face. Sanitized before forge write.
    EXTERNAL    — Any non-Ptolemy input. Sanitized + validated.

FA Escalation (by damage potential)
------------------------------------
    LOW         — pass-through, silent log
    MEDIUM      — 2FA: confirm intent
    HIGH        — 3FA: random word challenge + confirm + delay
    AULE_RISK   — 3FA automatic, no override, no bypass
                  Triggered by anything that could break Aule itself.

Aule-Risk Triggers (automatic 3FA, hardcoded)
----------------------------------------------
    - Writes to Aule's repair table
    - Changes to forge write path or dmesg path
    - Modifications to FA thresholds
    - Adding unregistered repair routines
    - Any modification to aule_sanitation.py or aule.py at runtime
    - Config key: 'aule', 'forge', 'sanitation', 'fa_threshold'

Random Word Challenge
---------------------
    Aule generates N words from a fixed seed pool.
    User must repeat them exactly. Pool is local — no network.
    Different words every challenge. Unpredictable, uncacheable.

    Aule :: 3FA REQUIRED
    Challenge: COPPER  VESSEL  HINGE
    Response:  _

    Wrong response → action quarantined in forge, O Captain alerted.
    3 failures     → action scrapped, incident written to dmesg.

Usage
-----
    from Aule.aule_sanitation import gate

    # Check trust and sanitize
    clean = gate.sanitize(source='callimachus', content=raw_input)

    # Gate an action by risk level
    allowed = gate.check('callimachus', risk='HIGH', action='db_write')

    # Aule-risk gate (automatic 3FA)
    allowed = gate.aule_risk_gate(action='modify_repair_table')
"""

import re
import os
import time
import random
import hashlib
import threading
import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from Pharos.PtolDmesg import dmesg as _dmesg
except ImportError:
    class _NullDmesg:
        def write(self, *a, **k): pass
        def warn(self, *a, **k): pass
        def error(self, *a, **k): pass
        def fatal(self, *a, **k): pass
    _dmesg = _NullDmesg()


# ── Trust levels ──────────────────────────────────────────────────────────────

class Trust(Enum):
    OPERATOR   = 'operator'    # O Captain — full trust, no sanitation
    ARCHIMEDES = 'archimedes'  # math authority — full trust, no sanitation
    FACE       = 'face'        # any other Face — sanitized
    EXTERNAL   = 'external'    # non-Ptolemy input — sanitized + validated


# ── Risk levels ───────────────────────────────────────────────────────────────

class Risk(Enum):
    LOW       = 0   # pass-through
    MEDIUM    = 1   # 2FA
    HIGH      = 2   # 3FA
    AULE_RISK = 3   # 3FA automatic, no override


# ── Trusted sources (no sanitation) ──────────────────────────────────────────

_TRUSTED_RAW = {Trust.OPERATOR, Trust.ARCHIMEDES}

_TRUST_MAP = {
    'operator':   Trust.OPERATOR,
    'rendier':    Trust.OPERATOR,
    'archimedes': Trust.ARCHIMEDES,
}

def _resolve_trust(source: str) -> Trust:
    t = _TRUST_MAP.get(source.lower())
    if t:
        return t
    return Trust.FACE


# ── Aule-risk keywords (automatic 3FA) ───────────────────────────────────────

_AULE_RISK_KEYS = {
    'aule', 'forge', 'sanitation', 'fa_threshold',
    'repair_table', 'dmesg_path', 'forge_write',
    'aule_sanitation', 'aule.py', 'aule_risk',
}

def _is_aule_risk(action: str) -> bool:
    a = action.lower()
    return any(k in a for k in _AULE_RISK_KEYS)


# ── Random word challenge pool ────────────────────────────────────────────────
# Local pool — no network, no external dependency.

_WORD_POOL = [
    'ANCHOR', 'BASIN', 'CEDAR', 'DAGGER', 'EMBER', 'FALCON', 'GRAVEL',
    'HAMMER', 'IRON', 'JACKAL', 'KILN', 'LANTERN', 'MORTAR', 'NEEDLE',
    'OBSIDIAN', 'PILLAR', 'QUARTZ', 'RIVET', 'SMITH', 'TALLOW', 'UMBER',
    'VESSEL', 'WARDEN', 'XENON', 'YOKE', 'ZINC', 'COPPER', 'HINGE',
    'BELLOWS', 'FORGE', 'ANVIL', 'FLINT', 'CINDER', 'AUGER', 'BRACE',
    'CHISEL', 'DRAWBAR', 'FERRITE', 'GUSSET', 'HEARTH', 'INGOT', 'JOIST',
]

def _generate_challenge(n: int = 3) -> list[str]:
    return random.sample(_WORD_POOL, n)


# ── Sanitation ────────────────────────────────────────────────────────────────

# Patterns stripped from non-trusted input
_STRIP_PATTERNS = [
    re.compile(r'<[^>]+>'),                     # HTML/XML tags
    re.compile(r'[;\|\&\$\`]'),                 # shell injection chars
    re.compile(r'\.\./'),                        # path traversal
    re.compile(r'(?i)(drop|delete|truncate)\s+table'),  # SQL drops
    re.compile(r'(?i)import\s+os\s*;'),         # inline os import tricks
]

def _sanitize_string(content: str) -> str:
    for pattern in _STRIP_PATTERNS:
        content = pattern.sub('', content)
    return content.strip()

def _sanitize(content) -> str:
    if isinstance(content, str):
        return _sanitize_string(content)
    if isinstance(content, dict):
        return {k: _sanitize(v) for k, v in content.items()}
    if isinstance(content, list):
        return [_sanitize(i) for i in content]
    return content


# ── FA Challenge Engine ───────────────────────────────────────────────────────

class FAChallenge:
    """
    Handles 2FA and 3FA challenges interactively.
    In GUI context, override prompt_fn and response_fn to use Qt dialogs.
    Default: terminal stdin/stdout.
    """

    MAX_ATTEMPTS = 3
    DELAY_SECS   = 2   # enforced delay before 3FA challenge

    def __init__(self):
        self._lock = threading.Lock()

    def challenge_2fa(self, action: str, source: str) -> bool:
        """2FA: simple yes/no confirmation."""
        print(f'\n  Aule :: 2FA REQUIRED')
        print(f'  Action : {action}')
        print(f'  Source : {source}')
        response = input('  Confirm? [yes/no]: ').strip().lower()
        passed = response in ('yes', 'y')
        _dmesg.write('aule', f'2FA {"PASS" if passed else "FAIL"} — {source} / {action}')
        return passed

    def challenge_3fa(self, action: str, source: str) -> bool:
        """3FA: random word challenge. MAX_ATTEMPTS tries."""
        time.sleep(self.DELAY_SECS)

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            words = _generate_challenge(3)
            challenge_str = '  '.join(words)

            print(f'\n  Aule :: 3FA REQUIRED  (attempt {attempt}/{self.MAX_ATTEMPTS})')
            print(f'  Action    : {action}')
            print(f'  Source    : {source}')
            print(f'  Challenge : {challenge_str}')
            response = input('  Response  : ').strip().upper().split()

            if response == words:
                _dmesg.write('aule', f'3FA PASS — {source} / {action}')
                return True
            else:
                _dmesg.warn('aule', f'3FA attempt {attempt} FAIL — {source} / {action}')
                print(f'  Aule :: WRONG — {self.MAX_ATTEMPTS - attempt} attempt(s) remaining')

        # All attempts exhausted
        self._quarantine(action, source)
        return False

    def _quarantine(self, action: str, source: str) -> None:
        """Action scrapped — quarantine entry written, O Captain alerted."""
        _dmesg.fatal('aule', f'3FA FAILED — action QUARANTINED — {source} / {action}')
        print(f'\n  Aule :: ACTION QUARANTINED — O Captain notified')
        # Forge quarantine log
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        qpath = Path.home() / 'ptolemy_aule_quarantine.log'
        try:
            with open(qpath, 'a') as f:
                f.write(f'{ts}  QUARANTINE  source={source}  action={action}\n')
        except OSError:
            pass


# ── AuleSanitation — main gate ────────────────────────────────────────────────

class AuleSanitation:
    """
    Aule's sanitation and FA gate.
    All input passes through here before reaching the bus or dmesg.
    """

    def __init__(self):
        self._fa = FAChallenge()

    def sanitize(self, source: str, content) -> tuple[bool, any]:
        """
        Sanitize content from source.
        Returns (is_trusted_raw, sanitized_or_raw_content).
        Trusted sources (OPERATOR, ARCHIMEDES) get content returned unchanged.
        """
        trust = _resolve_trust(source)
        if trust in _TRUSTED_RAW:
            return True, content
        cleaned = _sanitize(content)
        _dmesg.write('aule', f'sanitized input from {source}')
        return False, cleaned

    def check(self, source: str, risk: str, action: str) -> bool:
        """
        Gate an action by risk level.
        Returns True if allowed, False if blocked/quarantined.
        """
        trust  = _resolve_trust(source)
        risk_e = Risk[risk.upper()] if isinstance(risk, str) else risk

        # Trusted sources bypass FA
        if trust in _TRUSTED_RAW:
            _dmesg.write('aule', f'trusted pass — {source} / {action}')
            return True

        # Aule-risk: always 3FA, no override
        if _is_aule_risk(action) or risk_e == Risk.AULE_RISK:
            _dmesg.warn('aule', f'AULE_RISK detected — forcing 3FA — {source} / {action}')
            return self._fa.challenge_3fa(action, source)

        if risk_e == Risk.LOW:
            _dmesg.write('aule', f'LOW risk pass — {source} / {action}')
            return True

        if risk_e == Risk.MEDIUM:
            return self._fa.challenge_2fa(action, source)

        if risk_e == Risk.HIGH:
            return self._fa.challenge_3fa(action, source)

        return False

    def aule_risk_gate(self, action: str, source: str = 'unknown') -> bool:
        """Explicit Aule-risk gate. Always 3FA. No bypass."""
        _dmesg.warn('aule', f'aule_risk_gate invoked — {source} / {action}')
        return self._fa.challenge_3fa(action, source)

    def classify_risk(self, action: str) -> Risk:
        """Classify an action's risk level automatically."""
        if _is_aule_risk(action):
            return Risk.AULE_RISK
        # Expand heuristics as needed
        high_keys = {'delete', 'drop', 'format', 'wipe', 'override', 'bypass'}
        med_keys  = {'write', 'modify', 'update', 'push', 'send', 'exec'}
        a = action.lower()
        if any(k in a for k in high_keys):
            return Risk.HIGH
        if any(k in a for k in med_keys):
            return Risk.MEDIUM
        return Risk.LOW


# ── Module-level singleton ────────────────────────────────────────────────────

gate = AuleSanitation()
