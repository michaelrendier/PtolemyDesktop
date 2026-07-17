#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
PtolColor.py — Official Ptolemy Color Palette
==============================================
Pharos Core Layer

Macedonian royal color scheme. Source: Vergina archaeological record,
Argead dynastic tradition, and Hellenistic court usage.

Three tiers:
    ROYAL   — Argead / Ptolemaic dynasty colors (deepest, most restricted)
    COURT   — Companion Cavalry, phalanx, ceremonial
    SHELL   — Shell identity colors per Face and per prompt mode

Usage
-----
    from Pharos.PtolColor import PtolColor, FaceColor
    from PyQt6.QtGui import QColor

    bg = QColor(PtolColor.ROYAL_BLUE)
    fg = QColor(FaceColor.ARCHIMEDES)
"""

try:
    from PyQt6.QtGui import QColor as _QColor
    _HAS_QCOLOR = True
except ImportError:
    _QColor = None
    _HAS_QCOLOR = False


# ── Tier 1: Royal ─────────────────────────────────────────────────────────────
# Argead Star: gold on deep blue. The dynasty's identity mark.
# Ptolemaic Purple: restricted to the king, later the inner circle.

class PtolColor:
    # Argead / Vergina
    ROYAL_BLUE      = '#1a2a6c'   # deep Vergina blue — Argead Star background
    ROYAL_GOLD      = '#c9a227'   # Vergina star — hammered gold
    ROYAL_PURPLE    = '#4b0082'   # Ptolemaic porphyra — king's cloak

    # Companion Cavalry / Phalanx
    SARISSA_RED     = '#8b1a1a'   # deep crimson — Hetairoi cloaks, Philip's uniform
    CRIMSON         = '#dc143c'   # Alexander's chlamys — full campaign red

    # Armor and ceremonial
    LINEN_WHITE     = '#f5f0e0'   # linothorax — glued linen armor
    POLISHED_GOLD   = '#ffd700'   # greaves, helmet ornaments, procession weaponry
    MARBLE_WHITE    = '#e8e8e0'   # Alexandria great procession — marble base

    # Dark field / background
    NIGHT           = '#0a0a12'   # shell background — deep night sky
    STONE           = '#2a2a3a'   # secondary background — cut stone

    # Convenience: QColor factories
    @staticmethod
    def qcolor(hex_str: str) -> object:
        return _QColor(hex_str)

    @staticmethod
    def royal_blue()   -> object: return _QColor(PtolColor.ROYAL_BLUE)
    @staticmethod
    def royal_gold()   -> object: return _QColor(PtolColor.ROYAL_GOLD)
    @staticmethod
    def royal_purple() -> object: return _QColor(PtolColor.ROYAL_PURPLE)
    @staticmethod
    def sarissa_red()  -> object: return _QColor(PtolColor.SARISSA_RED)
    @staticmethod
    def crimson()      -> object: return _QColor(PtolColor.CRIMSON)


# ── Tier 2: Face shell identity colors ────────────────────────────────────────
# One color per Face. Used in shell prompt, daemon POST report, and Face tab.
# Chosen for readability on NIGHT (#0a0a12) background.
# Convention: cooler/calmer = data/storage Faces; warmer = action/interface Faces.

class FaceColor:
    PHAROS          = '#00ccff'   # core — cyan, primary identity
    CALLIMACHUS     = '#c9a227'   # archive — royal gold, keeper of the Library
    ARCHIMEDES      = '#7ec8e3'   # mathematics — sky blue, clean and precise
    ALEXANDRIA      = '#9b59b6'   # OpenGL — violet, visual/spectral
    ANAXIMANDER     = '#27ae60'   # navigation — sea green, cartographer
    KRYPTOS         = '#e74c3c'   # encryption — danger red, guarded
    PHALERON        = '#f39c12'   # search — amber, light in the port
    TESLA           = '#1abc9c'   # device — teal, electric/interfacing
    MOUSEION        = '#3498db'   # web/Flask — Hellenistic blue, public face
    PHILADELPHOS    = '#d4a0ff'   # LLM — lavender, Ptolemy II's scholars
    PTOLCPP         = '#e8e8e0'   # C++ port — marble white, precision layer
    AINULINDALE     = '#5dade2'   # prefilter — Iluvatar's song, cosmic blue

    # Daemon POST color — all daemons share this; name distinguishes them
    DAEMON          = '#ffcc00'   # amber-gold — POST diagnostic color

    # O Captain — the operator's own prompt color
    OPERATOR        = '#f5f0e0'   # linen white — neutral, above all Faces

    @staticmethod
    def for_face(face_name: str) -> str:
        """Return hex color string for a Face by name (case-insensitive)."""
        return _FACE_COLOR_MAP.get(face_name.lower(), FaceColor.PHAROS)


_FACE_COLOR_MAP = {
    'pharos':       FaceColor.PHAROS,
    'callimachus':  FaceColor.CALLIMACHUS,
    'archimedes':   FaceColor.ARCHIMEDES,
    'alexandria':   FaceColor.ALEXANDRIA,
    'anaximander':  FaceColor.ANAXIMANDER,
    'kryptos':      FaceColor.KRYPTOS,
    'phaleron':     FaceColor.PHALERON,
    'tesla':        FaceColor.TESLA,
    'mouseion':     FaceColor.MOUSEION,
    'philadelphos': FaceColor.PHILADELPHOS,
    'ptolcpp':      FaceColor.PTOLCPP,
    'ainulindale':  FaceColor.AINULINDALE,
    'daemon':       FaceColor.DAEMON,
}


# ── Tier 3: Shell MetaPrompt mode colors ──────────────────────────────────────
# Matches PtolShell._MODES. Kept here as single source of truth.

class ShellModeColor:
    PTOLEMY  = PtolColor.ROYAL_BLUE   # Ptolemy C/O — Argead blue
    PYTHON   = '#00ff66'              # Python3 REPL — green
    SHELL    = '#ffcc00'              # bash — amber
    ROOT     = '#ff4444'              # root — red
    FACE     = None                   # resolved per-Face from FaceColor
