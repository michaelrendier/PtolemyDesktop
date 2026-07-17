#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GlyphForge.py — Ptolemy Custom Font Engine
============================================
Kryptos Face

Atomic pixel editor targeting the Unicode Private Use Areas.
Output: TTF font (via fontforge Python API) + BDF bitmap fallback.

The font is infrastructure — not cosmetic.
Anyone rendering Ptolemy math/spectral notation needs this font installed.

PUA Namespace (Ptolemy)
-----------------------
    U+E000–U+E0FF   Ptolemy system glyphs
    U+E100–U+E1FF   Pharos UI symbols
    U+E200–U+E2FF   Ainulindale math operators
    U+E300–U+E3FF   HyperWebster indexing symbols
    U+E400–U+E4FF   Demotic tone / spectral layer markers
    U+E500–U+F8FF   Open / user
    U+F0000–U+FFFFF SPUA-A extended library
    U+100000–U+10FFFF SPUA-B overflow

Pipeline
--------
    GlyphCanvas   pixel grid editor (PyQt5 QWidget)
    GlyphCodex    JSON source of truth + TTF/BDF compiler
    GlyphStrip    PUA range browser
    GlyphForge    QMainWindow, PtolFace compliant

Font distribution: bundled with Ptolemy, registered via fontconfig.
Console (ncurses/libtcod) uses BDF bitmap export.
Qt UI uses QFontDatabase.addApplicationFont().

# TODO:SETTINGS — grid size, cell px, PUA start, font family name → GlyphForge settings tab
# TODO:BUILD — GlyphCanvas (pixel grid QWidget, click/drag toggle)
# TODO:BUILD — GlyphCodex (JSON persistence + TTF compile via fontforge)
# TODO:BUILD — GlyphStrip (horizontal PUA navigator)
# TODO:BUILD — GlyphForge QMainWindow assembly
# TODO:BUILD — fontconfig registration on install
# TODO:BUILD — QFontDatabase.addApplicationFont() call in Ptolemy3 init
"""

from Pharos.PtolFace import PtolFace

# ── PUA constants ─────────────────────────────────────────────────────────────
PUA_BMP_START  = 0xE000
PUA_BMP_END    = 0xF8FF
PUA_SPUA_A     = 0xF0000
PUA_SPUA_B     = 0x100000

FONT_FAMILY    = 'PtolemyGlyphs'
GRID_DEFAULT   = (16, 16)


class GlyphForge(PtolFace):
    """
    Negative space stub.
    Live when GlyphCanvas and GlyphCodex are built.
    """
    # TODO:BUILD
    pass


class GlyphCodex:
    """
    JSON source of truth + TTF/BDF compiler.
    Each glyph: { codepoint, name, namespace, grid, pixels (bitstring) }
    Compile: fontforge.font() → contour trace → generate('PtolemyGlyphs.ttf')
    # TODO:BUILD
    """
    pass


class GlyphCanvas:
    """
    PyQt5 pixel grid. Click/drag toggles pixels.
    Emits glyph_changed(codepoint, pixels) signal.
    # TODO:BUILD
    """
    pass


class GlyphStrip:
    """
    Horizontal PUA codepoint browser.
    Scrolls through assigned/unassigned glyph slots.
    # TODO:BUILD
    """
    pass
