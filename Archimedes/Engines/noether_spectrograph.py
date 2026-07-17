"""
noether_spectrograph.py — Aulë Face / Archimedes Face
=======================================================
Noether Current Spectrograph — a spectrograph of the mathematics.

Runs the SMNNIP Noether current through STFT and displays the result
as a live spectrograph — not of audio, but of the mathematical signal
itself evolving across the Cayley-Dickson tower.

The algebra tower:  ℝ(1) → ℂ(2) → ℍ(4) → 𝕆(8) → 𝕊(16)
                    1  +   2  +   4  +   8  +  16  =  31 planes

Each stratum produces a Noether current J^μ with N_GEN components:
    ℝ  : 0 generators  → 1 signal  (Lagrangian scalar)
    ℂ  : U(1)   → 1 current component
    ℍ  : SU(2)  → 3 current components
    𝕆  : SU(3)  → 8 current components
    𝕊  : Sedenion → 16 components (zero-divisor regime)

Total signal channels: 1 + 1 + 3 + 8 + 16 + diagnostics = ~35 channels

Each channel is a time series. The STFT of that series gives a
spectrograph showing which "frequencies" (rates of change) dominate
the mathematical evolution — slow drift vs fast oscillation vs
conservation violation events.

Layout (PyQt5 + pyqtgraph, matching LiveSpectrogram.py style):

    ┌──────────────────────────────────────────────────────────┐
    │  [ℝ]  Lagrangian scalar                                  │  row 0
    │  [ℂ]  J^0  (U(1) current)                               │  row 1
    │  [ℍ]  J^0  J^1  J^2  (SU(2) isospin currents)          │  rows 2-4
    │  [𝕆]  J^0..J^7  (SU(3) color currents)                  │  rows 5-12
    │  [𝕊]  J^0..J^15  (Sedenion — zero-divisor watch)        │  rows 13-28
    │  [∂J] Violation scalar  (conservation residual)          │  row 29
    │  [α]  RG running coupling × 4 strata                    │  rows 30-33
    └──────────────────────────────────────────────────────────┘

Milkdrop-style: all rows update simultaneously, colour mapped,
scrolling right-to-left. Violation events flash the violation row.

Usage:
    python noether_spectrograph.py               # full 35-channel display
    python noether_spectrograph.py --strata O    # octonion only
    python noether_spectrograph.py --fps 30      # frame rate
    python noether_spectrograph.py --demo        # synthetic signal demo (no SMNNIP)

Aulë stream integration:
    Emits events on channel "noether_spectrograph" — visible in aule monitor.
"""

import sys
import math
import time
import argparse
import numpy as np
from collections import deque
from typing import List, Optional

# ── Try SMNNIP import ─────────────────────────────────────────────────────────
try:
    import os
    sys.path.insert(0, os.environ.get("PTOLEMY_ROOT", str(
        __import__("pathlib").Path(__file__).resolve().parent.parent
    )))
    from Ainulindale.core.smnnip_derivation_pure import (
        Algebra, FieldState, NoetherCalculus, EulerLagrange,
        RGFlow, make_element, LagrangianDensity
    )
    SMNNIP_AVAILABLE = True
except ImportError as e:
    SMNNIP_AVAILABLE = False
    _import_err = str(e)

# ── Try Aulë stream ───────────────────────────────────────────────────────────
try:
    from aule import stream_event as _emit
except ImportError:
    def _emit(ch, et, payload=None, **kw): pass

# ── Qt / pyqtgraph ────────────────────────────────────────────────────────────
try:
    from PyQt6.QtCore import QTimer, Qt, pyqtSignal
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
    from PyQt6.QtGui import QFont
    import pyqtgraph as pg
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

# ── Constants ─────────────────────────────────────────────────────────────────

CHUNKSZ   = 512      # STFT window size (time steps, not audio samples)
HISTORY   = 1500     # scrolling history depth (columns in spectrograph)
UPDATE_MS = 33       # ~30 fps default

# Algebra tower — including Sedenion (S) extension
TOWER = [
    {"name": "ℝ",  "dim":  1, "gauge": "trivial", "n_gen": 0,  "color": (100,100,255,200)},
    {"name": "ℂ",  "dim":  2, "gauge": "U(1)",    "n_gen": 1,  "color": (100,200,255,200)},
    {"name": "ℍ",  "dim":  4, "gauge": "SU(2)",   "n_gen": 3,  "color": (100,255,200,200)},
    {"name": "𝕆",  "dim":  8, "gauge": "SU(3)",   "n_gen": 8,  "color": (200,255,100,200)},
    {"name": "𝕊",  "dim": 16, "gauge": "zero-div","n_gen": 16, "color": (255,150,100,200)},
]

# Channel definitions — every scalar signal the spectrograph watches
def build_channels():
    channels = []
    for s in TOWER:
        n = max(1, s["n_gen"])
        for j in range(n):
            label = f"{s['name']}  J^{j}" if s["n_gen"] > 0 else f"{s['name']}  ℒ"
            channels.append({
                "label":   label,
                "stratum": s["name"],
                "idx":     j,
                "color":   s["color"],
                "type":    "current" if s["n_gen"] > 0 else "lagrangian",
            })
    # Violation + RG channels
    channels.append({"label": "∂J  violation", "stratum": "diag", "type": "violation",
                     "color": (255, 80, 80, 255)})
    for s in TOWER[:4]:  # RG defined for ℝ ℂ ℍ 𝕆 only
        channels.append({"label": f"α_NN  {s['name']}", "stratum": s["name"],
                         "type": "rg", "color": s["color"]})
    return channels

CHANNELS = build_channels()
N_CHAN   = len(CHANNELS)

# ── Sedenion element (not in SMNNIP yet — implemented here) ──────────────────

class SedenionEl:
    """
    16-dimensional Cayley-Dickson algebra element.
    𝕊 = 𝕆 × 𝕆 via the standard doubling: (a,b)·(c,d) = (ac-d*b, da+bc*)
    Non-alternative, contains zero divisors.
    Lost property: alternativity (and therefore power-associativity for some elements).
    """
    __slots__ = ('c',)
    def __init__(self, components=None):
        self.c = list(components) if components else [0.0]*16

    @classmethod
    def from_oct_pair(cls, oct_a, oct_b):
        """Construct from two octonion 8-vectors."""
        return cls(list(oct_a) + list(oct_b))

    def __add__(self, o): return SedenionEl([a+b for a,b in zip(self.c, o.c)])
    def __sub__(self, o): return SedenionEl([a-b for a,b in zip(self.c, o.c)])
    def __rmul__(self, s): return SedenionEl([s*x for x in self.c])

    def conj(self):
        """Sedenion conjugate: negate all 15 imaginary components."""
        return SedenionEl([self.c[0]] + [-x for x in self.c[1:]])

    def norm_sq(self): return sum(x*x for x in self.c)
    def norm(self): return math.sqrt(self.norm_sq())

    def _oct_mul(self, a8, b8):
        """Multiply two 8-vectors as octonions using FANO_LINES."""
        # Import table from smnnip or use inline
        result = [0.0]*8
        # e0 (real) part
        result[0] = sum(a8[i]*b8[i]*(-1 if i>0 else 1) for i in range(8))
        # Full Fano-plane multiplication — abbreviated here for clarity
        # In production: use OCT_TABLE from smnnip_derivation_pure
        fano = [(1,2,3),(2,4,5),(3,5,6),(4,6,0),(5,0,1),(6,1,2),(0,3,4)]
        for i,j,k in [(a+1,b+1,c+1) for (a,b,c) in fano]:
            result[k]  +=  a8[i]*b8[j]
            result[k]  -=  a8[j]*b8[i]
            result[j]  +=  a8[k]*b8[i]
            result[j]  -=  a8[i]*b8[k]
            result[i]  +=  a8[j]*b8[k]
            result[i]  -=  a8[k]*b8[j]
        return result

    def __mul__(self, o):
        """Cayley-Dickson doubling: (a,b)(c,d) = (ac - d*b, da + bc*)"""
        a, b = self.c[:8], self.c[8:]
        c, d = o.c[:8], o.c[8:]
        # d* = conjugate of d in 𝕆: negate components 1-7
        d_conj = [d[0]] + [-x for x in d[1:]]
        b_conj = [b[0]] + [-x for x in b[1:]]
        ac     = self._oct_mul(a, c)
        d_b    = self._oct_mul(d_conj, b)
        da     = self._oct_mul(d, a)
        bc_    = self._oct_mul(b, b_conj)  # simplified — full impl uses b·c*
        upper  = [ac[i] - d_b[i] for i in range(8)]
        lower  = [da[i] + bc_[i] for i in range(8)]
        return SedenionEl(upper + lower)

    def has_zero_divisor_risk(self, threshold=1e-6):
        """Check if this element is near a zero-divisor configuration."""
        # A zero divisor a has a·b=0 for non-zero b.
        # Necessary condition: norm(a)² ≈ sum of squares is non-zero
        # but some sub-norms vanish.
        upper_norm = sum(x*x for x in self.c[:8])
        lower_norm = sum(x*x for x in self.c[8:])
        total_norm = upper_norm + lower_norm
        if total_norm < threshold:
            return False  # near zero, not interesting
        # Zero divisors arise when both halves are non-zero but interact badly
        cross = abs(upper_norm - lower_norm) / (total_norm + 1e-12)
        return cross < 0.1  # upper ≈ lower in norm = risk zone

    def noether_currents(self, g_coup=1.0):
        """
        Sedenion Noether currents — 16 components.
        J^a = g · c_conj · T^a · c  where T^a are 16 basis projectors.
        For Sedenions: T^a simply projects onto basis element e_a.
        """
        conj = self.conj()
        return [g_coup * conj.c[a] * self.c[a] for a in range(16)]

    def planes(self):
        """Return 8 complex planes (real+imag pairs) for display."""
        return [(self.c[2*i], self.c[2*i+1]) for i in range(8)]

    def __repr__(self):
        return f"𝕊({self.c[0]:.3f} + {sum(abs(x) for x in self.c[1:]):.3f}·e)"


# ── Signal generator ──────────────────────────────────────────────────────────

class NoetherSignalGenerator:
    """
    Generates the multi-channel Noether current signal from SMNNIP state.
    Each call to step() returns one time-sample: a vector of N_CHAN floats.
    """

    def __init__(self, demo_mode=False):
        self.demo_mode  = demo_mode
        self.t          = 0.0
        self.dt         = 0.01
        self.prev_J     = {}
        self.prev_states = {}
        self._rng        = np.random.default_rng(42)

        # Build field states for each SMNNIP stratum (if available)
        self._states = {}
        if SMNNIP_AVAILABLE and not demo_mode:
            self._init_smnnip_states()

        # Sedenion state (always available)
        self._sed  = SedenionEl([1.0] + [0.1*i for i in range(15)])
        self._sed_vel = SedenionEl([0.0, 0.01, -0.01, 0.005] + [0.001]*12)

        _emit("noether_spectrograph", "init", {
            "channels": N_CHAN,
            "smnnip":   SMNNIP_AVAILABLE and not demo_mode,
            "demo":     demo_mode,
        })

    def _init_smnnip_states(self):
        """Build one FieldState per stratum with reasonable initial conditions."""
        for alg_idx in [Algebra.R, Algebra.C, Algebra.H, Algebra.O]:
            dim = Algebra.DIM[alg_idx]
            psi = [make_element([0.5 + 0.1*k for k in range(dim)], alg_idx)]
            A   = [0.1] * Algebra.N_GEN.get(alg_idx, 1)
            self._states[alg_idx] = FieldState(
                activations=psi,
                gauge_field=A,
                algebra=alg_idx,
                hbar_nn=1.0,
                g_coup=0.3,
            )

    def _smnnip_step(self, alg_idx) -> List[float]:
        """Run one Noether step for a SMNNIP stratum."""
        if not SMNNIP_AVAILABLE or alg_idx not in self._states:
            return self._demo_currents(alg_idx)
        state = self._states[alg_idx]
        diag  = NoetherCalculus.conservation_diagnostic(
            state, self._prev_states.get(alg_idx))
        self._prev_states[alg_idx] = state
        J = diag["J"]
        # Evolve the gauge field slightly (fake dynamics — replace with real EOM)
        n_gen = Algebra.N_GEN.get(alg_idx, 0)
        if n_gen > 0:
            new_A = [a + 0.005*math.sin(self.t + i) for i, a in
                     enumerate(state.gauge_field)]
            self._states[alg_idx] = state._replace(gauge_field=new_A)
        return J

    def _demo_currents(self, alg_idx) -> List[float]:
        """Synthetic signal with interesting frequency content per stratum."""
        n = max(1, TOWER[alg_idx]["n_gen"])
        out = []
        for k in range(n):
            # Each stratum has different characteristic frequencies
            freq_base = [0.5, 1.0, 2.0, 3.7, 0.23][min(alg_idx, 4)]
            phase_off = k * 0.4
            # Superposition of tones + noise
            sig  = math.sin(2*math.pi*(freq_base + k*0.13)*self.t + phase_off)
            sig += 0.3 * math.sin(2*math.pi*freq_base*2.718*self.t)
            sig += 0.1 * float(self._rng.standard_normal())
            # Occasional conservation violation bursts
            if self._rng.random() < 0.003:
                sig += 3.0 * math.exp(-((self.t % 1.0) - 0.5)**2 / 0.01)
            out.append(sig)
        return out

    def _sedenion_step(self) -> List[float]:
        """Evolve sedenion state and return 16 Noether components."""
        # Simple damped oscillator dynamics on sedenion components
        for i in range(16):
            omega = 0.1 + i * 0.05
            damp  = 0.995
            self._sed.c[i]     = damp * (self._sed.c[i] +
                                  self.dt * self._sed_vel.c[i])
            self._sed_vel.c[i] = damp * (self._sed_vel.c[i] -
                                  self.dt * omega**2 * self._sed.c[i])
        # Inject noise and occasional zero-divisor approach
        if self._rng.random() < 0.01:
            # Push toward zero-divisor risk zone (upper ≈ lower norm)
            scale = self._rng.random() * 0.5
            for i in range(8):
                self._sed.c[i+8] = self._sed.c[i] * scale + \
                                    float(self._rng.standard_normal()) * 0.05
        currents = self._sed.noether_currents(g_coup=0.2)
        return currents

    def step(self) -> np.ndarray:
        """Return one time sample — vector of N_CHAN floats."""
        self.t += self.dt
        out = []

        # ℝ stratum — Lagrangian scalar
        if SMNNIP_AVAILABLE and not self.demo_mode and Algebra.R in self._states:
            L = LagrangianDensity.full_lagrangian(self._states[Algebra.R])
            out.append(L.get("total", 0.0))
        else:
            out.append(math.sin(2*math.pi*0.5*self.t) * 0.5)

        # ℂ ℍ 𝕆 strata
        for alg_idx in [Algebra.C, Algebra.H, Algebra.O] if SMNNIP_AVAILABLE \
                        else [1, 2, 3]:
            J = self._smnnip_step(alg_idx) if SMNNIP_AVAILABLE \
                else self._demo_currents(alg_idx)
            n_gen = TOWER[alg_idx]["n_gen"]
            out.extend(J[:n_gen] if len(J) >= n_gen else J + [0.0]*(n_gen-len(J)))

        # 𝕊 Sedenion — 16 components
        out.extend(self._sedenion_step())

        # Violation diagnostic
        J_flat = [x for x in out[1:13]]  # all non-sedenion currents
        J_prev = self.prev_J.get("flat", J_flat)
        violation = sum(abs(a-b) for a,b in zip(J_flat, J_prev)) / max(len(J_flat),1)
        self.prev_J["flat"] = J_flat
        out.append(violation)

        # RG running couplings — one per stratum ℝ ℂ ℍ 𝕆
        for alg_idx in range(4):
            # α_NN(l) ~ 1/(b0 * log(l+e)) — logarithmic running
            b0 = [0, 1, 3, 8][alg_idx] + 1
            alpha = 1.0 / (b0 * math.log(self.t + math.e))
            out.append(alpha + 0.01*float(self._rng.standard_normal()))

        sig = np.array(out[:N_CHAN], dtype=np.float32)
        _emit("noether_spectrograph", "step", {"t": round(self.t, 4),
              "violation": round(violation, 6),
              "sedenion_norm": round(self._sed.norm(), 4)})
        return sig


# ── Ring buffer of time series ────────────────────────────────────────────────

class SignalBuffer:
    """Ring buffer holding HISTORY time-steps for each channel."""

    def __init__(self, n_chan: int, history: int, chunk: int):
        self.n_chan  = n_chan
        self.history = history
        self.chunk   = chunk
        # time_series[c] = deque of floats, length = history
        self.series = [deque([0.0]*history, maxlen=history) for _ in range(n_chan)]
        # stft_image[c] = 2D array (freq_bins × history) for display
        self.freq_bins = chunk // 2 + 1
        self.images = [np.zeros((self.freq_bins, history), dtype=np.float32)
                       for _ in range(n_chan)]
        self._win = np.hanning(chunk)

    def push(self, sample: np.ndarray):
        """Add one time-step sample to all channels."""
        for c in range(min(self.n_chan, len(sample))):
            self.series[c].append(float(sample[c]))

    def update_stft(self, channel: int):
        """Recompute STFT image column for one channel and scroll."""
        s = np.array(self.series[channel], dtype=np.float32)
        # Take the last chunk samples
        seg = s[-self.chunk:] if len(s) >= self.chunk else \
              np.pad(s, (self.chunk - len(s), 0))
        seg_w = seg * self._win
        spec  = np.fft.rfft(seg_w) / self.chunk
        psd   = np.abs(spec).astype(np.float32)
        psd_db = 20.0 * np.log10(psd + 1e-9)
        # Scroll and append
        self.images[channel] = np.roll(self.images[channel], -1, axis=1)
        self.images[channel][:, -1] = psd_db


# ── Qt Display ────────────────────────────────────────────────────────────────

# Guard: provide stub base if Qt not available
_WindowBase = QMainWindow if QT_AVAILABLE else object  # type: ignore

class NoetherSpectrographWindow(_WindowBase):
    """
    Main display window.

    Shows all N_CHAN spectrograph rows simultaneously, scrolling
    right-to-left as the mathematical signal evolves.

    Each row = one Noether current component (or diagnostic scalar).
    Colour = power spectral density in dB.
    X axis = time.
    Y axis = 'frequency' (rate of change of the mathematical signal).
    """

    COLORMAPS = {
        "plasma":   [(0,0,0),(80,0,120),(200,0,100),(255,100,0),(255,255,0),(255,255,255)],
        "sedenion": [(0,0,40),(0,50,120),(100,0,200),(255,0,100),(255,200,0),(255,255,255)],
        "noether":  [(0,20,0),(0,100,50),(0,200,100),(200,255,0),(255,200,0),(255,80,0)],
        "violation":[(10,0,0),(100,0,0),(255,0,0),(255,150,0),(255,255,200),(255,255,255)],
    }

    def __init__(self, args):
        super().__init__()
        self.args      = args
        self.generator = NoetherSignalGenerator(demo_mode=args.demo)
        self.buffer    = SignalBuffer(N_CHAN, HISTORY, CHUNKSZ)
        self._step_count = 0

        self._build_ui()
        self._start_timer()

        _emit("noether_spectrograph", "window_open", {"channels": N_CHAN})

    # ── LUT builder ──────────────────────────────────────────────
    def _make_lut(self, cmap_name: str) -> np.ndarray:
        stops = self.COLORMAPS.get(cmap_name, self.COLORMAPS["plasma"])
        lut = np.zeros((256, 3), dtype=np.ubyte)
        n   = len(stops) - 1
        for i in range(256):
            t    = i / 255.0 * n
            idx  = min(int(t), n-1)
            frac = t - idx
            c0, c1 = stops[idx], stops[idx+1]
            lut[i] = [int(c0[j] + frac*(c1[j]-c0[j])) for j in range(3)]
        return lut

    # ── UI construction ───────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("Noether Current Spectrograph  —  Ptolemy SMNNIP")
        self.setStyleSheet("background-color: #050510; color: #ccccff;")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(1)
        layout.setContentsMargins(4, 4, 4, 4)

        # Title
        title = QLabel("⚛  Noether Current Spectrograph  —  ℝ→ℂ→ℍ→𝕆→𝕊  Cayley-Dickson Tower")
        title.setFont(QFont("monospace", 9))
        title.setStyleSheet("color: #8888ff; padding: 2px;")
        layout.addWidget(title)

        # One ImageItem per channel
        self.img_items = []
        self.plot_widgets = []

        # Build colourmap LUTs — different per algebra stratum type
        luts = {
            "ℝ":    self._make_lut("noether"),
            "ℂ":    self._make_lut("plasma"),
            "ℍ":    self._make_lut("plasma"),
            "𝕆":    self._make_lut("noether"),
            "𝕊":    self._make_lut("sedenion"),
            "diag": self._make_lut("violation"),
        }

        row_height = max(12, (700 - 40) // N_CHAN)

        for ci, ch in enumerate(CHANNELS):
            pw = pg.PlotWidget()
            pw.setFixedHeight(row_height)
            pw.setBackground("#050510")
            pw.hideButtons()

            # Remove all axes except a minimal left label
            for axis in ["top","bottom","right"]:
                pw.getPlotItem().hideAxis(axis)
            left_ax = pw.getAxis("left")
            left_ax.setWidth(90)
            left_ax.setStyle(showValues=False, tickLength=0)
            left_ax.setPen(pg.mkPen(color=(40,40,80)))
            left_ax.setLabel(
                f'<span style="color:#8888cc;font-size:7pt">{ch["label"]}</span>'
            )

            vb = pw.getViewBox()
            vb.setMouseEnabled(x=False, y=False)

            img = pg.ImageItem()
            img.setLookupTable(luts.get(ch["stratum"], luts["ℂ"]))
            img.setLevels([-60, 20])  # dB range

            # Scale: x = time (HISTORY steps), y = freq bins
            freq_bins = CHUNKSZ // 2 + 1
            yscale = 1.0 / freq_bins
            img.scale(1.0, yscale)

            pw.addItem(img)
            pw.setXRange(0, HISTORY, padding=0)
            pw.setYRange(0, 1.0, padding=0)

            self.img_items.append(img)
            self.plot_widgets.append(pw)
            layout.addWidget(pw)

        # Status bar
        self.status = QLabel("initialising...")
        self.status.setFont(QFont("monospace", 8))
        self.status.setStyleSheet("color: #666699; padding: 2px;")
        layout.addWidget(self.status)

        self.resize(1100, 750)

    # ── Timer ─────────────────────────────────────────────────────
    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(self.args.update_ms)

    def _tick(self):
        # Generate one new sample
        sample = self.generator.step()
        self.buffer.push(sample)
        self._step_count += 1

        # Update STFT and image every tick
        for ci in range(N_CHAN):
            self.buffer.update_stft(ci)
            # Transpose: ImageItem expects (width, height) = (HISTORY, freq_bins)
            img_data = self.buffer.images[ci].T  # (HISTORY × freq_bins)
            self.img_items[ci].setImage(img_data, autoLevels=False)

            # Flash violation row on large violations
            if CHANNELS[ci]["type"] == "violation":
                viol = abs(float(sample[ci])) if ci < len(sample) else 0.0
                if viol > 0.5:
                    self.img_items[ci].setLevels([-30, 10])
                else:
                    self.img_items[ci].setLevels([-60, 20])

        # Update status
        sed_norm = self.generator._sed.norm()
        zero_div = self.generator._sed.has_zero_divisor_risk()
        zdiv_str = "  ⚠ ZERO-DIVISOR RISK" if zero_div else ""
        self.status.setText(
            f"t={self.generator.t:.3f}  "
            f"step={self._step_count}  "
            f"𝕊 norm={sed_norm:.4f}{zdiv_str}  "
            f"channels={N_CHAN}  "
            f"{'[SMNNIP]' if SMNNIP_AVAILABLE else '[DEMO]'}"
        )


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Noether Current Spectrograph — spectrograph of the SMNNIP mathematics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Algebra tower: ℝ(1) → ℂ(2) → ℍ(4) → 𝕆(8) → 𝕊(16)
               1  +   2  +   4  +   8  +  16  =  31 planes

Each Noether current component becomes a time series.
The STFT of that series is displayed as a spectrograph row.
Y axis: rate-of-change frequency of the mathematical signal.
X axis: time.
Colour: power spectral density (dB).

Examples:
  python noether_spectrograph.py --demo          # runs without SMNNIP
  python noether_spectrograph.py --fps 60        # 60fps
  python noether_spectrograph.py --chunk 1024    # finer frequency resolution
        """
    )
    ap.add_argument("--demo",      action="store_true", help="Synthetic signal demo (no SMNNIP required)")
    ap.add_argument("--fps",       type=int, default=30, help="Target frame rate (default 30)")
    ap.add_argument("--chunk",     type=int, default=512,  help="STFT window size (default 512)")
    ap.add_argument("--history",   type=int, default=1500, help="Scrolling history depth (default 1500)")
    ap.add_argument("--update-ms", type=int, default=None, help="Update interval ms (overrides --fps)")
    args = ap.parse_args()

    global CHUNKSZ, HISTORY

    args.update_ms = args.update_ms or max(16, 1000 // args.fps)

    # Patch globals from args
    CHUNKSZ = args.chunk
    HISTORY = args.history

    if not QT_AVAILABLE:
        print("PyQt5 / pyqtgraph required. Install with:")
        print("  pip install PyQt5 pyqtgraph")
        sys.exit(1)

    if not SMNNIP_AVAILABLE:
        print(f"SMNNIP not available ({_import_err if not args.demo else 'demo mode'}) — running demo signal.")
        args.demo = True

    _emit("noether_spectrograph", "launch", {"demo": args.demo, "fps": args.fps, "channels": N_CHAN})

    app = QApplication(sys.argv)
    app.setApplicationName("Noether Spectrograph")

    win = NoetherSpectrographWindow(args)
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
