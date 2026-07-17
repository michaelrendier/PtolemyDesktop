#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FractalRenderer — UF Formulary Fractal Generator
=================================================
Alexandria Face

Each fractal = attractor representation of a different process.
Implements the Ultra Fractal (.ufm) public formulary collection
as a Python renderer. All output piped to Mouseion via Alexandria.

Architecture:
    FractalFormula    — base class, one subclass per .ufm formula
    FractalRenderer   — orchestrates formula + coloring + iteration
    FractalView       — Qt widget (QGraphicsProxyWidget in Alexandria)

Currently implemented formulas:
    Mandelbrot        — z² + c (baseline)
    BurningShip       — |Re(z)|+i|Im(z)|)² + c
    Julia             — z² + k (fixed k)
    Newton            — z³ - 1 (Newton basin, tied to StirlingBasin)
    LorenzProjection  — Lorenz attractor projected to 2D slice
    NoetherField      — SMNNIP Noether conservation as coloring field

Settings hook → Alexandria > Fractal settings tab.
"""

import math
import struct
from typing import Optional, Tuple, List

try:
    from PyQt6.QtCore    import Qt, QThread, pyqtSignal, QObject
    from PyQt6.QtGui     import QImage, QPixmap
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                  QComboBox, QPushButton, QLabel,
                                  QSizePolicy)
    _HAS_QT = True
except ImportError:
    _HAS_QT = False

# ── Settings ─────────────────────────────────────────────────────────────────
FRACTAL_SETTINGS = {
    "default_formula": "Mandelbrot",
    "width":           800,
    "height":          600,
    "max_iter":        256,
    "escape_radius":   2.0,
    "center_re":       -0.5,
    "center_im":        0.0,
    "zoom":             1.0,
    "colormap":        "ptolemy",   # ptolemy | grayscale | fire | ice
}

# ── Formula base ──────────────────────────────────────────────────────────────

class FractalFormula:
    """Base class for all UF-style formulas."""
    name = "base"

    def iterate(self, c: complex, max_iter: int, escape: float) -> Tuple[int, complex]:
        """
        Returns (escape_iteration, final_z).
        escape_iteration == max_iter means did NOT escape (interior).
        """
        raise NotImplementedError

    def description(self) -> str:
        return self.name


class Mandelbrot(FractalFormula):
    name = "Mandelbrot"
    def iterate(self, c, max_iter, escape):
        z = 0j
        for i in range(max_iter):
            z = z*z + c
            if abs(z) > escape:
                return i, z
        return max_iter, z
    def description(self): return "z² + c — classic Mandelbrot set"


class BurningShip(FractalFormula):
    name = "BurningShip"
    def iterate(self, c, max_iter, escape):
        z = 0j
        for i in range(max_iter):
            z = complex(abs(z.real), abs(z.imag))**2 + c
            if abs(z) > escape:
                return i, z
        return max_iter, z
    def description(self): return "Burning Ship attractor"


class Julia(FractalFormula):
    name = "Julia"
    def __init__(self, k: complex = complex(-0.7, 0.27015)):
        self.k = k
    def iterate(self, c, max_iter, escape):
        z = c
        for i in range(max_iter):
            z = z*z + self.k
            if abs(z) > escape:
                return i, z
        return max_iter, z
    def description(self): return f"Julia: z² + {self.k}"


class NewtonCubic(FractalFormula):
    """Newton's method on z³ - 1. Ties to StirlingBasin coloring."""
    name = "Newton"
    _ROOTS = [1+0j, complex(-0.5, math.sqrt(3)/2), complex(-0.5, -math.sqrt(3)/2)]

    def iterate(self, c, max_iter, escape):
        z = c if abs(c) > 1e-9 else 0.001+0.001j
        for i in range(max_iter):
            denom = 3 * z*z
            if abs(denom) < 1e-12:
                break
            z = z - (z**3 - 1) / denom
            # Check convergence to any root
            for root in self._ROOTS:
                if abs(z - root) < 1e-6:
                    return i, z
        return max_iter, z

    def basin_index(self, z: complex) -> int:
        """Return which root z converged to (0,1,2) or -1."""
        for i, root in enumerate(self._ROOTS):
            if abs(z - root) < 0.01:
                return i
        return -1

    def description(self): return "Newton basins: z³ - 1 (3 roots)"


class LorenzProjection(FractalFormula):
    """Lorenz attractor trajectory density, projected to XZ plane."""
    name = "LorenzProjection"

    def __init__(self, sigma=10.0, rho=28.0, beta=8/3, steps=2000):
        self.sigma = sigma; self.rho = rho; self.beta = beta
        self.steps = steps

    def iterate(self, c, max_iter, escape):
        # Use c as initial condition seed
        x, y, z = c.real, c.imag, abs(c)
        dt = 0.005
        for i in range(min(max_iter, self.steps)):
            dx = self.sigma * (y - x)
            dy = x * (self.rho - z) - y
            dz = x * y - self.beta * z
            x += dx * dt; y += dy * dt; z += dz * dt
            if abs(x) > 100 or abs(y) > 100:
                return i, complex(x, z)
        return max_iter, complex(x, z)

    def description(self): return f"Lorenz XZ projection σ={self.sigma} ρ={self.rho}"


# ── Colormap ──────────────────────────────────────────────────────────────────

def _ptolemy_color(t: float) -> Tuple[int,int,int]:
    """Ptolemy palette: deep teal → cyan → white interior."""
    if t >= 1.0:
        return (5, 13, 13)   # interior — near black
    r = int(0   + t * 0)
    g = int(100 + t * 155)
    b = int(120 + t * 135)
    return (min(r,255), min(g,255), min(b,255))

def _grayscale(t: float) -> Tuple[int,int,int]:
    v = int(t * 255)
    return (v, v, v)

def _fire(t: float) -> Tuple[int,int,int]:
    r = int(min(255, t * 3 * 255))
    g = int(min(255, max(0, (t*3 - 1) * 255)))
    b = int(min(255, max(0, (t*3 - 2) * 255)))
    return (r, g, b)

_COLORMAPS = {
    'ptolemy':   _ptolemy_color,
    'grayscale': _grayscale,
    'fire':      _fire,
}


# ── Renderer ──────────────────────────────────────────────────────────────────

class FractalRenderer:
    """
    Renders a formula to a raw RGB byte buffer.
    Width × Height × 3 bytes (R,G,B).
    Piped to Alexandria → Mouseion for web display.
    """

    FORMULAS = {
        'Mandelbrot':       Mandelbrot,
        'BurningShip':      BurningShip,
        'Julia':            Julia,
        'Newton':           NewtonCubic,
        'LorenzProjection': LorenzProjection,
    }

    def __init__(self, formula_name: str = None):
        name = formula_name or FRACTAL_SETTINGS['default_formula']
        cls  = self.FORMULAS.get(name, Mandelbrot)
        self.formula   = cls()
        self.width     = FRACTAL_SETTINGS['width']
        self.height    = FRACTAL_SETTINGS['height']
        self.max_iter  = FRACTAL_SETTINGS['max_iter']
        self.escape    = FRACTAL_SETTINGS['escape_radius']
        self.center    = complex(FRACTAL_SETTINGS['center_re'],
                                 FRACTAL_SETTINGS['center_im'])
        self.zoom      = FRACTAL_SETTINGS['zoom']
        self.colormap  = _COLORMAPS.get(FRACTAL_SETTINGS['colormap'],
                                        _ptolemy_color)

    def pixel_to_complex(self, px: int, py: int) -> complex:
        scale = 3.5 / (self.zoom * self.width)
        re = self.center.real + (px - self.width  / 2) * scale
        im = self.center.imag - (py - self.height / 2) * scale
        return complex(re, im)

    def render(self) -> bytes:
        """Render to raw RGB bytes. Width×Height×3."""
        buf = bytearray(self.width * self.height * 3)
        for py in range(self.height):
            for px in range(self.width):
                c = self.pixel_to_complex(px, py)
                n, z = self.formula.iterate(c, self.max_iter, self.escape)
                t = n / self.max_iter
                r, g, b = self.colormap(t)
                idx = (py * self.width + px) * 3
                buf[idx]   = r
                buf[idx+1] = g
                buf[idx+2] = b
        return bytes(buf)

    def render_and_pipe(self, view_name: str = 'fractal'):
        """Render and send to Alexandria → Mouseion."""
        raw = self.render()
        try:
            from Alexandria import pipe_to_mouseion
            pipe_to_mouseion(view_name, {
                'formula':  self.formula.name,
                'width':    self.width,
                'height':   self.height,
                'rgb_bytes': len(raw),   # actual bytes not serialised — use file
                'description': self.formula.description(),
            })
        except Exception:
            pass
        return raw

    @classmethod
    def list_formulas(cls) -> List[str]:
        return list(cls.FORMULAS.keys())


# ── NoetherField formula (SMMIP Noether current as coloring field) ────────────

class NoetherField(FractalFormula):
    """
    Noether Information Current field.
    Each pixel c is passed through the SMMIP reverse tower (Sedenion → Reals).
    The resulting Noether current value drives the color field.
    Connects Alexandria visual output to Archimedes/ValaQuenta math engine.
    """
    name = "NoetherField"

    def __init__(self):
        self._tower = None

    def _get_tower(self):
        if self._tower is None:
            try:
                from Philadelphos.philadelphos_console import ReverseTower
                self._tower = ReverseTower()
            except Exception:
                self._tower = False
        return self._tower if self._tower else None

    def iterate(self, c: complex, max_iter: int, escape: float) -> Tuple[int, complex]:
        tower = self._get_tower()
        if tower is None:
            # Fallback: Mandelbrot when tower unavailable
            z = 0j
            for i in range(max_iter):
                z = z*z + c
                if abs(z) > escape:
                    return i, z
            return max_iter, z

        import hashlib as _hl
        # Map complex c → sedenion via SHA encoding of the coordinate string
        coord_str = f'{c.real:.6f},{c.imag:.6f}'
        try:
            from Philadelphos.philadelphos_console import SedenionElement
            se = SedenionElement.from_text(coord_str)
            reals, diag = tower.run(se, [coord_str])
            r = abs(reals[0]) if reals else 0.0
            # Map Noether current to iteration count for coloring
            n = int(r * max_iter) % max_iter
            return n, complex(r, diag.get('survivors', 1))
        except Exception:
            return max_iter, c

    def description(self) -> str:
        return "Noether Current field — SMMIP Sedenion→Reals coloring"


# Register NoetherField in FractalRenderer.FORMULAS
FractalRenderer.FORMULAS['NoetherField'] = NoetherField


# ── Render thread ─────────────────────────────────────────────────────────────

if _HAS_QT:
    class _RenderThread(QThread):
        finished = pyqtSignal(bytes, int, int)

        def __init__(self, renderer: FractalRenderer, parent=None):
            super().__init__(parent)
            self._renderer = renderer

        def run(self):
            raw = self._renderer.render()
            self.finished.emit(raw, self._renderer.width, self._renderer.height)


    # ── FractalView Qt widget ─────────────────────────────────────────────────

    class FractalView(QWidget):
        """
        Qt widget for Alexandria Face fractal display.
        Formula selector + render button + live canvas.
        Rendered via off-thread _RenderThread.
        """

        def __init__(self, parent=None):
            super().__init__(parent)
            self._renderer = FractalRenderer()
            self._thread   = None
            self._build_ui()

        def _build_ui(self):
            self.setStyleSheet('background: #050510; color: #aaffcc;')
            self.setMinimumSize(400, 340)

            root = QVBoxLayout(self)
            root.setContentsMargins(4, 4, 4, 4)
            root.setSpacing(4)

            # ── Toolbar ───────────────────────────────────────────────────────
            bar = QHBoxLayout()
            self._combo = QComboBox()
            self._combo.addItems(FractalRenderer.list_formulas())
            self._combo.setStyleSheet(
                'background: #0a0a20; color: #aaffcc; border: 1px solid #224;')
            bar.addWidget(self._combo)

            self._render_btn = QPushButton('Render')
            self._render_btn.setStyleSheet(
                'background: #0a0a20; color: #aaffcc; border: 1px solid #446;')
            self._render_btn.setFixedWidth(70)
            self._render_btn.clicked.connect(self._render)
            bar.addWidget(self._render_btn)

            self._status = QLabel('Ready')
            self._status.setStyleSheet('color: #557; font-size: 9px;')
            bar.addWidget(self._status)
            bar.addStretch()
            root.addLayout(bar)

            # ── Canvas ────────────────────────────────────────────────────────
            self._canvas = QLabel()
            self._canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding,
                                       QSizePolicy.Policy.Expanding)
            self._canvas.setStyleSheet('background: #020210;')
            root.addWidget(self._canvas)

        def _render(self):
            if self._thread and self._thread.isRunning():
                return
            formula = self._combo.currentText()
            self._renderer = FractalRenderer(formula)
            # Fit resolution to widget size
            w = max(200, self._canvas.width())
            h = max(150, self._canvas.height())
            self._renderer.width  = w
            self._renderer.height = h
            self._render_btn.setEnabled(False)
            self._status.setText(f'Rendering {formula}…')
            self._thread = _RenderThread(self._renderer, self)
            self._thread.finished.connect(self._on_done)
            self._thread.start()

        def _on_done(self, raw: bytes, w: int, h: int):
            img = QImage(raw, w, h, w * 3, QImage.Format.Format_RGB888)
            self._canvas.setPixmap(QPixmap.fromImage(img))
            self._render_btn.setEnabled(True)
            self._status.setText(f'Done  {w}×{h}')
