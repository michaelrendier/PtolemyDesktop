#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos/output_tuner.py — /OutputTuning shell layer
=========================================================
Ptolemy Project

A standalone debugger for meaning — runs as a separate process layer,
attaching to any point in the SMNNIP pipeline to inspect, reverse, and
tune the output generation process.

ARCHITECTURE:
    /DataInput [--DM] loads corpus → trains tower → saves weights
    /OutputTuning      attaches to saved weights → exposes tuning shell

THE TUNER EXPOSES:
    1. PRE-COLLAPSE VIEW
       The isotropic sphere before Catastrophic Waveform Collapse.
       Shows all focal points, their distances, symmetry state.
       Angle of approach to collapse visible here.

    2. COLLAPSE INSPECTOR
       Step through the CWC at adjustable delta.
       Watch focal points extinct or survive.
       Pre/post angle comparison — how much did the sphere distort?

    3. POST-COLLAPSE CANDIDATES
       Multiple focal point survivors ranked.
       Manual selection of which becomes Tongue input.
       Each candidate shown with its SemanticWord match (if --DM data loaded).

    4. TONGUE LAYER
       Reverse-lookup: attractor → nearest SemanticWord.
       H/4 adjacency window adjustable.
       Shows why each word was or wasn't selected.

    5. REVERSE PATH
       Word → attractor reconstruction.
       Run the pipeline backwards from any output word.
       Compare recovered field to original input field.

    6. INSIDE-OUT PATH  (J_N applied post-output)
       Apply inversion map to the output attractor.
       Find the word at 1/r, θ+π/2.
       Diagnostic: forward output vs inside-out output.
       If antonyms → geometry consistent. If unrelated → inversion symmetry broken.

    7. ISOTROPIC SPHERE VISUALISER
       Show the pre-collapse sphere's actual symmetry.
       Measure deviation from perfect isotropy.
       Predict focal point count from symmetry-breaking degree.

MODES:
    Interactive shell   — full REPL with commands
    --DM                — loads SemanticWord JSON data for real word matching
    --auto              — runs all diagnostics non-interactively, prints report
    --word <w>          — run reverse path from known word
    --delta <f>         — override collapse delta

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
"""

from __future__ import annotations

import os
import sys
import math
import json
import glob
import argparse
import textwrap
from typing import Any, Dict, List, Optional, Tuple

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE  = os.path.dirname(os.path.abspath(__file__))
_ROOT  = os.path.dirname(_HERE)
for _p in [_ROOT, _HERE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Constants (mirror inversion engine) ──────────────────────────────────────
PI      = math.pi
PHI     = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
H_NN    = 0.1
HBAR_NN = H_NN / (2.0 * PI)
H4      = H_NN / 4.0          # = (π/2)·ħ_NN — adjacency window


# ==============================================================================
# §1  SEMANTIC WORD INDEX
#     Loads SemanticWord JSON files produced by acquire.py.
#     Provides reverse-lookup: attractor coordinate → nearest word.
# ==============================================================================

class SemanticWordIndex:
    """
    In-memory index of SemanticWord JSON records from HyperWebster.
    Provides:
        lookup(r)       → nearest word to real-valued attractor coordinate r
        reverse(word)   → real-valued coordinate for a known word
        candidates(r,n) → n nearest words within H/4 window

    Coordinate assignment (stub until Horner/Callimachus layer runs):
        Each word is assigned a real coordinate based on:
          - phonological weight (IPA length proxy)
          - semantic density (definition length + synonym count)
          - alphabetical position (normalized 0..1)
        This is a stub — replace with hyperwebster_address when available.
    """

    def __init__(self):
        self._words: Dict[str, Dict] = {}       # word → record
        self._coords: Dict[str, float] = {}     # word → real coordinate
        self._sorted: List[Tuple[float, str]] = []  # sorted (coord, word)
        self.loaded = False
        self.data_dir: Optional[str] = None

    def load_from_dir(self, data_dir: str) -> int:
        """
        Load all SemanticWord JSON files from a HyperWebster data directory.
        Expected structure: data_dir/words_a/*.json ... words_z/*.json
        Returns number of words loaded.
        """
        self.data_dir = data_dir
        count = 0
        pattern = os.path.join(data_dir, "words_*", "*.json")
        for path in sorted(glob.glob(pattern)):
            try:
                record = json.loads(open(path, encoding="utf-8").read())
                word = record.get("word", "")
                if not word:
                    continue
                self._words[word] = record
                self._coords[word] = self._assign_coordinate(word, record)
                count += 1
            except Exception:
                pass
        self._sorted = sorted((c, w) for w, c in self._coords.items())
        self.loaded = count > 0
        return count

    def load_synthetic(self, words: List[str]) -> None:
        """
        Load a synthetic word list (no JSON data) for testing.
        Assigns stub coordinates only.
        """
        for i, word in enumerate(words):
            self._words[word] = {"word": word, "semantic": {}, "resonance": {}}
            self._coords[word] = self._assign_coordinate(word, {})
        self._sorted = sorted((c, w) for w, c in self._coords.items())
        self.loaded = len(words) > 0

    def _assign_coordinate(self, word: str, record: Dict) -> float:
        """
        Coordinate via LorenzStirling basin attractor.

        Word properties → complex plane → Stirling V=10 basin classification
        → Lorenz trajectory within basin → real coordinate in [PHI_INV, PHI].

        Falls back to alphabetical/density blend if LorenzStirling unavailable.
        """
        # Alphabetical component (0..1) — first 4 chars
        alpha = 0.0
        if word:
            alpha = sum((ord(c) - ord('a')) / 25.0
                        for c in word[:4].lower()
                        if 'a' <= c <= 'z') / max(1, min(4, len(word)))

        # Semantic density (0..1)
        defs = record.get("semantic", {}).get("sense_inventory", [])
        syns = record.get("semantic", {}).get("synonyms", [])
        density = min(1.0, (len(defs) * 0.1 + len(syns) * 0.02))

        # Map to complex plane: real=alpha, imag=density, scaled to [-1.5, 1.5]
        z = complex(alpha * 3.0 - 1.5, density * 3.0 - 1.5)

        try:
            from Archimedes.Maths.LorenzStirling import lorenz_stirling
            result = lorenz_stirling.classify(z, lorenz_steps=50)
            if result.extinct:
                # Extinct point — use fallback blend
                coord = 0.7 * alpha + 0.3 * density
            else:
                # basin_id 1-8 → 0..1
                basin_norm = (result.basin_id - 1) / 7.0
                # Lorenz z-position is in [0, ~50]; normalize
                lz = max(0.0, min(50.0, result.lorenz_pos[2])) / 50.0
                coord = 0.6 * basin_norm + 0.4 * lz
        except Exception:
            coord = 0.7 * alpha + 0.3 * density

        return PHI_INV + coord * (PHI - PHI_INV)

    def lookup(self, r: float, window: float = H4) -> Optional[Dict]:
        """
        Reverse lookup: find nearest word to attractor value r.
        Returns None if no word is within `window` of r.
        """
        if not self._sorted:
            return None
        # Binary search for nearest
        lo, hi = 0, len(self._sorted) - 1
        best_dist = float('inf')
        best_idx  = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            c, w = self._sorted[mid]
            d = abs(c - r)
            if d < best_dist:
                best_dist = d
                best_idx  = mid
            if c < r:
                lo = mid + 1
            else:
                hi = mid - 1
        coord, word = self._sorted[best_idx]
        if best_dist > window:
            return None
        return {
            "word":     word,
            "coord":    coord,
            "distance": best_dist,
            "within_H4": best_dist <= H4,
            "record":   self._words.get(word, {}),
        }

    def candidates(self, r: float, n: int = 5,
                   window: float = H4 * 4) -> List[Dict]:
        """Return n nearest words within window, ranked by distance."""
        results = []
        for coord, word in self._sorted:
            d = abs(coord - r)
            if d <= window:
                results.append({
                    "word":     word,
                    "coord":    coord,
                    "distance": d,
                    "within_H4": d <= H4,
                    "record":   self._words.get(word, {}),
                })
        results.sort(key=lambda x: x["distance"])
        return results[:n]

    def reverse(self, word: str) -> Optional[float]:
        """Return coordinate for a known word, or None."""
        return self._coords.get(word)

    def summary(self) -> str:
        return (f"SemanticWordIndex: {len(self._words)} words loaded"
                + (f" from {self.data_dir}" if self.data_dir else " [synthetic]"))


# ==============================================================================
# §2  ISOTROPIC SPHERE
#     Models the pre-collapse field as a sphere in (r, θ) space.
#     Measures symmetry breaking — predicts focal point count.
# ==============================================================================

class IsotropicSphere:
    """
    The information field before Catastrophic Waveform Collapse.

    An isotropic sphere has equal energy density at all angles.
    Symmetry breaking (non-isotropy) distorts it — the distortion
    determines how many focal points survive CWC.

    Perfect isotropy  → 1 focal point (full collapse)
    Mild distortion   → 2-3 focal points
    Strong distortion → many focal points (incomplete collapse)

    The sphere is parameterised by:
        r_base      : base radius (default 1.0)
        components  : list of (r_i, θ_i, amplitude_i) active poles
        delta       : collapse parameter (from --DM sweep)
    """

    N_SAMPLE = 64  # angular sample points for symmetry measurement

    def __init__(self, r_base: float = 1.0):
        self.r_base = r_base
        self.components: List[Tuple[float, float, float]] = []
        self.delta = 0.0

    def add_component(self, r: float, theta: float, amplitude: float):
        self.components.append((r, theta, amplitude))

    def from_text(self, text: str):
        """
        Build sphere components from input text.
        Each word maps to a (r, θ, amplitude) pole.
        This is a stub — replace with SMNNIP tower output when available.
        """
        words = text.split()[:16]  # cap at 16 poles
        for i, word in enumerate(words):
            # Stub coordinate from word properties
            r = PHI_INV + (len(word) % 7) / 14.0
            theta = (i / max(1, len(words))) * 2 * PI
            amp = 1.0 / (1.0 + i * 0.1)
            self.add_component(r, theta, amp)
        return self

    def energy_at(self, theta: float) -> float:
        """Total energy density at angle theta."""
        e = 0.0
        for r, t, amp in self.components:
            angular_weight = (1.0 + math.cos(theta - t)) / 2.0
            e += amp * r * angular_weight
        return e

    def isotropy_deviation(self) -> float:
        """
        Measure of non-isotropy. 0.0 = perfect sphere. Higher = more distorted.
        Computed as std-dev of energy sampled at N_SAMPLE angles,
        normalised by mean energy.
        """
        if not self.components:
            return 0.0
        angles = [2 * PI * i / self.N_SAMPLE for i in range(self.N_SAMPLE)]
        energies = [self.energy_at(a) for a in angles]
        mean = sum(energies) / len(energies)
        if mean < 1e-12:
            return 0.0
        variance = sum((e - mean) ** 2 for e in energies) / len(energies)
        return math.sqrt(variance) / mean

    def predicted_focal_count(self) -> int:
        """
        Predict number of focal points post-CWC from isotropy deviation.
        Based on symmetry-breaking degree:
            dev < 0.1  → 1 (full collapse)
            dev < 0.3  → 2
            dev < 0.6  → 3-4
            dev >= 0.6 → many (use energy maxima count)
        """
        dev = self.isotropy_deviation()
        if dev < 0.1:
            return 1
        elif dev < 0.3:
            return 2
        elif dev < 0.6:
            return min(4, int(dev * 6))
        else:
            return self._count_energy_maxima()

    def _count_energy_maxima(self) -> int:
        angles = [2 * PI * i / self.N_SAMPLE for i in range(self.N_SAMPLE)]
        energies = [self.energy_at(a) for a in angles]
        count = 0
        n = len(energies)
        for i in range(n):
            if energies[i] > energies[(i - 1) % n] and \
               energies[i] > energies[(i + 1) % n]:
                count += 1
        return max(1, count)

    def focal_points(self, delta: float = 0.0) -> List[Dict]:
        """
        Find focal points — energy maxima after applying collapse delta.
        delta shifts the collapse threshold: negative = wider, positive = tighter.
        """
        angles = [2 * PI * i / self.N_SAMPLE for i in range(self.N_SAMPLE)]
        energies = [self.energy_at(a) + delta for a in angles]
        mean = sum(energies) / len(energies)

        # Threshold: mean + delta * std
        std = math.sqrt(sum((e - mean)**2 for e in energies) / len(energies))
        threshold = mean + abs(delta) * std

        points = []
        n = len(energies)
        for i in range(n):
            e = energies[i]
            if e >= threshold and \
               e >= energies[(i-1) % n] and \
               e >= energies[(i+1) % n]:
                theta = angles[i]
                # Find r from components via nearest-angle match
                r = self._r_at_angle(theta)
                points.append({
                    "r":        r,
                    "theta":    theta,
                    "energy":   e,
                    "angle_deg": math.degrees(theta),
                })

        return points if points else [{"r": PHI, "theta": 0.0,
                                       "energy": max(energies),
                                       "angle_deg": 0.0}]

    def _r_at_angle(self, theta: float) -> float:
        """Interpolate r value at given angle from components."""
        if not self.components:
            return self.r_base
        total_w = 0.0
        total_r = 0.0
        for r, t, amp in self.components:
            w = amp * (1.0 + math.cos(theta - t)) / 2.0
            total_w += w
            total_r += w * r
        return total_r / max(1e-12, total_w)

    def collapse_angle_pre(self) -> float:
        """Angle of the dominant pole before collapse (degrees)."""
        if not self.components:
            return 0.0
        best = max(self.components, key=lambda c: c[2])
        return math.degrees(best[1])

    def collapse_angle_post(self, delta: float = 0.0) -> float:
        """Angle of primary focal point after collapse (degrees)."""
        fps = self.focal_points(delta)
        return fps[0]["angle_deg"] if fps else 0.0

    def render_ascii(self, width: int = 48) -> List[str]:
        """Simple ASCII representation of energy distribution."""
        angles = [2 * PI * i / width for i in range(width)]
        energies = [self.energy_at(a) for a in angles]
        max_e = max(energies) if energies else 1.0
        bar_h = 6
        lines = []
        for row in range(bar_h, 0, -1):
            line = "  "
            for e in energies:
                norm = e / max(max_e, 1e-12)
                line += "█" if norm >= row / bar_h else " "
            lines.append(line)
        lines.append("  " + "─" * width)
        lines.append("  0" + " " * (width // 2 - 1) + "π" +
                     " " * (width // 2 - 2) + "2π")
        return lines


# ==============================================================================
# §3  FOCAL POINT INSPECTOR
#     CWC step-by-step with delta control.
#     Pre/post angle comparison.
#     J_N inversion for inside-out path.
# ==============================================================================

class FocalInspector:
    """
    Inspects the Catastrophic Waveform Collapse process.
    Controls delta (collapse sharpness).
    Computes forward output, reverse path, and inside-out (J_N) path.
    """

    def __init__(self, sphere: IsotropicSphere, index: SemanticWordIndex):
        self.sphere  = sphere
        self.index   = index
        self.delta   = 0.0
        self._history: List[Dict] = []

    def run(self, delta: Optional[float] = None) -> Dict:
        """
        Run the full collapse + Tongue at given delta.
        Returns a result dict with all diagnostic information.
        """
        if delta is not None:
            self.delta = delta

        # Pre-collapse state
        pre_angle  = self.sphere.collapse_angle_pre()
        isotropy   = self.sphere.isotropy_deviation()
        pred_count = self.sphere.predicted_focal_count()

        # Collapse
        focal_pts  = self.sphere.focal_points(self.delta)
        post_angle = focal_pts[0]["angle_deg"] if focal_pts else 0.0
        angle_diff = abs(post_angle - pre_angle)

        # Tongue: reverse lookup for each focal point
        tongue_candidates = []
        for fp in focal_pts:
            r = fp["r"]
            word_match = self.index.lookup(r) if self.index.loaded else None
            all_near   = self.index.candidates(r, n=3) if self.index.loaded else []
            tongue_candidates.append({
                "focal":   fp,
                "primary": word_match,
                "nearby":  all_near,
            })

        # Inside-out path (J_N on primary focal point)
        inv_candidates = []
        for fp in focal_pts[:2]:
            r_inv   = 1.0 / fp["r"] if fp["r"] != 0 else float('inf')
            t_inv   = (fp["theta"] + PI / 2) % (2 * PI)
            w_inv   = self.index.lookup(r_inv) if self.index.loaded else None
            all_inv = self.index.candidates(r_inv, n=3) if self.index.loaded else []
            inv_candidates.append({
                "r_inv":   r_inv,
                "t_inv":   t_inv,
                "primary": w_inv,
                "nearby":  all_inv,
            })

        result = {
            "delta":          self.delta,
            "pre_angle_deg":  pre_angle,
            "post_angle_deg": post_angle,
            "angle_diff_deg": angle_diff,
            "isotropy_dev":   isotropy,
            "predicted_fps":  pred_count,
            "actual_fps":     len(focal_pts),
            "focal_points":   focal_pts,
            "tongue":         tongue_candidates,
            "inside_out":     inv_candidates,
        }

        self._history.append(result)
        return result

    def reverse_path(self, word: str) -> Dict:
        """
        Run the pipeline backwards from a known word.
        word → coordinate → field reconstruction → comparison to input.
        """
        coord = self.index.reverse(word)
        if coord is None:
            return {"error": f"word '{word}' not in index"}

        # Reconstruct what sphere components would produce this coordinate
        # as primary focal point — compare to actual sphere
        actual_fps = self.sphere.focal_points(self.delta)
        actual_primary_r = actual_fps[0]["r"] if actual_fps else PHI

        reconstruction_error = abs(coord - actual_primary_r)
        lossless = reconstruction_error < H4

        # What word does the forward path produce?
        forward = self.index.lookup(actual_primary_r)
        forward_word = forward["word"] if forward else None

        return {
            "input_word":        word,
            "word_coord":        coord,
            "actual_primary_r":  actual_primary_r,
            "reconstruction_err": reconstruction_error,
            "lossless":          lossless,
            "forward_word":      forward_word,
            "round_trips":       forward_word == word,
            "H4_window":         H4,
        }

    def delta_sweep(self, deltas: Optional[List[float]] = None) -> List[Dict]:
        """Run collapse at multiple delta values. Returns sweep results."""
        if deltas is None:
            deltas = [-0.2, -0.1, 0.0, 0.1, 0.2]
        return [self.run(d) for d in deltas]


# ==============================================================================
# §4  OUTPUT TUNER SHELL
#     Interactive REPL + non-interactive --auto mode.
# ==============================================================================

TUNER_HELP = """
OutputTuning Shell — Commands
══════════════════════════════
  sphere              Show isotropic sphere state + ASCII render
  pre                 Pre-collapse view: focal point predictions
  collapse [delta]    Run collapse at delta (default 0.0)
  sweep               Run 5-point delta sweep (-0.2 to +0.2)
  candidates          Show all Tongue candidates for current state
  select <n>          Select focal point n as output
  reverse <word>      Run reverse path from known word
  invert              Show inside-out (J_N) path for current output
  load <dir>          Load SemanticWord JSON data from directory
  delta <f>           Set collapse delta
  status              Show current tuner state
  history             Show results of all runs this session
  reset               Reset sphere to default state
  help                This help
  quit / exit         Exit tuner
"""

class OutputTuner:
    """
    Interactive output tuning shell.
    Runs as a separate layer — does not modify the main pipeline.
    All changes are advisory / diagnostic only.
    """

    BANNER = """
╔══════════════════════════════════════════════════════╗
║   Ptolemy OutputTuning — Diagnostic Shell            ║
║   /OutputTuning  [--DM <data_dir>] [--auto]          ║
║   [--word <w>] [--delta <f>]                         ║
╚══════════════════════════════════════════════════════╝"""

    def __init__(self, dm_dir: Optional[str] = None):
        self.index    = SemanticWordIndex()
        self.sphere   = IsotropicSphere()
        self.inspector: Optional[FocalInspector] = None
        self._current_result: Optional[Dict] = None
        self._selected_candidate: Optional[Dict] = None
        self._dm_dir  = dm_dir

        # Load data if --DM dir provided
        if dm_dir:
            self._load_data(dm_dir)
        else:
            # Synthetic word list for testing without real data
            self._load_synthetic()

        self._reset_sphere()

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_data(self, data_dir: str) -> None:
        if not os.path.isdir(data_dir):
            print(f"  [!] Data dir not found: {data_dir}")
            self._load_synthetic()
            return
        n = self.index.load_from_dir(data_dir)
        if n == 0:
            print(f"  [!] No SemanticWord JSON files found in {data_dir}")
            self._load_synthetic()
        else:
            print(f"  [✓] Loaded {n} words from {data_dir}")

    def _load_synthetic(self) -> None:
        synthetic = [
            "the","run","water","red","abandon","ephemeral","melancholy",
            "serendipity","threshold","petrichor","sonder","lacuna",
            "ineffable","qualia","palimpsest","liminal","apophenia",
            "hiraeth","redwood","synchronicity","bread","void","numinous",
        ]
        self.index.load_synthetic(synthetic)
        print(f"  [~] Synthetic index: {len(synthetic)} test words")

    def _reset_sphere(self, text: str = "") -> None:
        self.sphere = IsotropicSphere()
        if text:
            self.sphere.from_text(text)
        else:
            # Default sphere: four symmetric poles
            for i in range(4):
                theta = i * PI / 2
                self.sphere.add_component(
                    r=PHI - i * 0.1,
                    theta=theta,
                    amplitude=1.0 / (1 + i * 0.2)
                )
        self.inspector = FocalInspector(self.sphere, self.index)

    # ── Display helpers ───────────────────────────────────────────────────────

    def _w(self, width: int = 54) -> str:
        return "─" * width

    def _print_result(self, result: Dict,
                      selected_idx: Optional[int] = None) -> None:
        d  = result
        fw = 54

        print(f"\n  {'─'*fw}")
        print(f"  δ = {d['delta']:+.3f}")
        print(f"  Pre-collapse angle  : {d['pre_angle_deg']:+.2f}°")
        print(f"  Post-collapse angle : {d['post_angle_deg']:+.2f}°")
        print(f"  Angle shift         : {d['angle_diff_deg']:.2f}°")
        print(f"  Isotropy deviation  : {d['isotropy_dev']:.4f}"
              f"  (0=perfect sphere)")
        print(f"  Predicted focal pts : {d['predicted_fps']}")
        print(f"  Actual focal pts    : {d['actual_fps']}")
        print()

        for i, tc in enumerate(d["tongue"]):
            fp = tc["focal"]
            marker = "▶" if i == (selected_idx or 0) else " "
            print(f"  {marker} [{i+1}] r={fp['r']:.4f}  "
                  f"θ={fp['angle_deg']:+.1f}°  "
                  f"E={fp['energy']:.4f}")

            if tc["primary"]:
                pw = tc["primary"]
                print(f"       Tongue → \"{pw['word']}\"  "
                      f"dist={pw['distance']:.4f}  "
                      f"{'✓ H/4' if pw['within_H4'] else '○ outside H/4'}")
            else:
                print(f"       Tongue → [no word within H/4 window]")

            if tc["nearby"] and len(tc["nearby"]) > 1:
                near_words = [f"\"{n['word']}\"({n['distance']:.3f})"
                              for n in tc["nearby"][1:3]]
                print(f"       Nearby : {', '.join(near_words)}")

        if d["inside_out"]:
            print()
            print(f"  Inside-out path (J_N: r→1/r, θ→θ+π/2):")
            for io in d["inside_out"]:
                r_inv = io["r_inv"]
                print(f"    r_inv={r_inv:.4f}  θ_inv={math.degrees(io['t_inv']):.1f}°",
                      end="")
                if io["primary"]:
                    pw = io["primary"]
                    print(f"  → \"{pw['word']}\"  dist={pw['distance']:.4f}")
                else:
                    print(f"  → [no match]")

        print(f"  {'─'*fw}")

    def _print_sphere(self) -> None:
        s   = self.sphere
        dev = s.isotropy_deviation()
        pred = s.predicted_focal_count()
        print(f"\n  Isotropic Sphere")
        print(f"  {'─'*48}")
        print(f"  r_base              : {s.r_base:.4f}")
        print(f"  Active poles        : {len(s.components)}")
        print(f"  Isotropy deviation  : {dev:.4f}")
        isotropy_bar = int((1.0 - min(dev, 1.0)) * 20)
        print(f"  Symmetry            : [{'█'*isotropy_bar}{'░'*(20-isotropy_bar)}]"
              f"  {'perfect' if dev < 0.05 else 'distorted' if dev < 0.3 else 'broken'}")
        print(f"  Predicted focal pts : {pred}")
        print(f"  H/4 window          : {H4:.6f}")
        print(f"  φ                   : {PHI:.6f}")
        print(f"  1/φ                 : {PHI_INV:.6f}")
        print()
        for line in s.render_ascii(48):
            print(line)
        print()
        for i, (r, t, amp) in enumerate(s.components):
            print(f"  Pole {i+1}: r={r:.4f}  θ={math.degrees(t):.1f}°  amp={amp:.3f}")

    def _print_sweep(self, sweep: List[Dict]) -> None:
        labels = ["δ=-0.2 [wide]",
                  "δ=-0.1 [pre]",
                  "δ= 0.0 [natural]",
                  "δ=+0.1 [post]",
                  "δ=+0.2 [narrow]"]
        print(f"\n  Delta Sweep — Focal Collapse Curve")
        print(f"  {'─'*60}")
        print(f"  {'Label':22}  {'FPs':4}  {'Angle':8}  {'Isotropy':9}  Output")
        print(f"  {'─'*60}")
        for i, (r, label) in enumerate(zip(sweep, labels)):
            fp_count = r["actual_fps"]
            angle    = r["post_angle_deg"]
            iso      = r["isotropy_dev"]
            # Primary tongue output
            primary  = ""
            if r["tongue"] and r["tongue"][0]["primary"]:
                primary = f'"{r["tongue"][0]["primary"]["word"]}"'
            elif r["tongue"]:
                primary = "[no match]"
            print(f"  {label:22}  {fp_count:4}  {angle:+8.2f}°  {iso:9.4f}  {primary}")
        print(f"  {'─'*60}")

    def _print_reverse(self, result: Dict) -> None:
        if "error" in result:
            print(f"  [!] {result['error']}")
            return
        rt = "✓ round-trips" if result["round_trips"] else "✗ does not round-trip"
        ll = "✓ lossless" if result["lossless"] else "✗ lossy"
        print(f"\n  Reverse Path: \"{result['input_word']}\"")
        print(f"  {'─'*48}")
        print(f"  Word coordinate     : {result['word_coord']:.6f}")
        print(f"  Pipeline primary r  : {result['actual_primary_r']:.6f}")
        print(f"  Reconstruction err  : {result['reconstruction_err']:.6f}")
        print(f"  H/4 window          : {result['H4_window']:.6f}")
        print(f"  Lossless test       : {ll}")
        print(f"  Forward word        : \"{result['forward_word']}\"")
        print(f"  Round-trip          : {rt}")

    # ── Interactive shell ─────────────────────────────────────────────────────

    def run_shell(self) -> None:
        print(self.BANNER)
        print(f"\n  {self.index.summary()}")
        print(f"  Type 'help' for commands.\n")

        while True:
            try:
                raw = input("  tuner › ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n  [OutputTuning exited]")
                break

            if not raw:
                continue

            parts = raw.split()
            cmd   = parts[0].lower()

            if cmd in ("quit", "exit", "q"):
                print("  [OutputTuning exited]")
                break

            elif cmd == "help":
                print(TUNER_HELP)

            elif cmd == "sphere":
                self._print_sphere()

            elif cmd == "pre":
                dev   = self.sphere.isotropy_deviation()
                pred  = self.sphere.predicted_focal_count()
                angle = self.sphere.collapse_angle_pre()
                print(f"\n  Pre-Collapse State")
                print(f"  Isotropy deviation  : {dev:.4f}")
                print(f"  Pre-collapse angle  : {angle:.2f}°")
                print(f"  Predicted focal pts : {pred}")
                note = ("Perfect sphere — will collapse to single focal point."
                        if dev < 0.1 else
                        f"Distorted sphere — expect {pred} focal point(s) post-collapse.")
                print(f"  Note: {note}")

            elif cmd == "collapse":
                delta = 0.0
                if len(parts) > 1:
                    try:
                        delta = float(parts[1])
                    except ValueError:
                        print(f"  [!] Invalid delta: {parts[1]}")
                        continue
                result = self.inspector.run(delta)
                self._current_result = result
                self._print_result(result)

            elif cmd == "sweep":
                sweep = self.inspector.delta_sweep()
                self._print_sweep(sweep)

            elif cmd == "candidates":
                if not self._current_result:
                    print("  [!] Run 'collapse' first.")
                    continue
                print(f"\n  All Tongue Candidates (δ={self._current_result['delta']:+.3f})")
                for i, tc in enumerate(self._current_result["tongue"]):
                    fp = tc["focal"]
                    print(f"\n  [{i+1}] r={fp['r']:.4f}  θ={fp['angle_deg']:+.1f}°")
                    for near in tc["nearby"]:
                        mark = "✓" if near["within_H4"] else "○"
                        print(f"     {mark} \"{near['word']}\"  "
                              f"coord={near['coord']:.4f}  "
                              f"dist={near['distance']:.4f}")

            elif cmd == "select":
                if not self._current_result:
                    print("  [!] Run 'collapse' first.")
                    continue
                try:
                    idx = int(parts[1]) - 1
                    tongue = self._current_result["tongue"]
                    if not (0 <= idx < len(tongue)):
                        print(f"  [!] Index out of range (1-{len(tongue)})")
                        continue
                    self._selected_candidate = tongue[idx]
                    fp = tongue[idx]
                    w  = fp["primary"]["word"] if fp["primary"] else "[no word]"
                    print(f"  Selected focal point {idx+1} → \"{w}\"")
                    self._print_result(self._current_result, selected_idx=idx)
                except (IndexError, ValueError):
                    print("  Usage: select <n>")

            elif cmd == "reverse":
                if len(parts) < 2:
                    print("  Usage: reverse <word>")
                    continue
                word = parts[1].lower()
                result = self.inspector.reverse_path(word)
                self._print_reverse(result)

            elif cmd == "invert":
                if not self._current_result:
                    print("  [!] Run 'collapse' first.")
                    continue
                io = self._current_result["inside_out"]
                if not io:
                    print("  No inside-out data.")
                    continue
                print(f"\n  Inside-Out Path (J_N applied to output)")
                print(f"  Forward output:", end="")
                fwd = self._current_result["tongue"]
                if fwd and fwd[0]["primary"]:
                    print(f" \"{fwd[0]['primary']['word']}\"")
                else:
                    print(" [no match]")
                for i, item in enumerate(io):
                    print(f"\n  J_N({i+1}): r→{item['r_inv']:.4f}  "
                          f"θ→{math.degrees(item['t_inv']):.1f}°")
                    if item["primary"]:
                        print(f"   Inside-out word: \"{item['primary']['word']}\"")
                        # Semantic relationship check
                        fw_word = (fwd[0]["primary"]["word"]
                                   if fwd and fwd[0]["primary"] else None)
                        io_word = item["primary"]["word"]
                        if fw_word:
                            print(f"   Geometry check: forward=\"{fw_word}\" "
                                  f"↔ inside-out=\"{io_word}\"")
                            print(f"   [Check manually: are these antonyms, "
                                  f"duals, or unrelated?]")
                    else:
                        print(f"   Inside-out word: [no match — inversion gap]")

            elif cmd == "load":
                if len(parts) < 2:
                    print("  Usage: load <data_dir>")
                    continue
                self._load_data(parts[1])
                self.inspector = FocalInspector(self.sphere, self.index)

            elif cmd == "delta":
                if len(parts) < 2:
                    print(f"  Current delta: {self.inspector.delta:+.3f}")
                    continue
                try:
                    self.inspector.delta = float(parts[1])
                    print(f"  Delta set to {self.inspector.delta:+.3f}")
                except ValueError:
                    print(f"  [!] Invalid delta: {parts[1]}")

            elif cmd == "status":
                print(f"\n  Status")
                print(f"  {'─'*40}")
                print(f"  {self.index.summary()}")
                print(f"  Sphere poles    : {len(self.sphere.components)}")
                print(f"  Isotropy dev    : {self.sphere.isotropy_deviation():.4f}")
                print(f"  Current delta   : {self.inspector.delta:+.3f}")
                print(f"  Runs this session: {len(self.inspector._history)}")
                if self._selected_candidate and self._selected_candidate.get("primary"):
                    print(f"  Selected output : "
                          f"\"{self._selected_candidate['primary']['word']}\"")

            elif cmd == "history":
                if not self.inspector._history:
                    print("  No runs yet.")
                    continue
                print(f"\n  Session History ({len(self.inspector._history)} runs)")
                print(f"  {'─'*50}")
                print(f"  {'#':3}  {'δ':6}  {'FPs':4}  {'Angle':8}  Primary output")
                for i, r in enumerate(self.inspector._history):
                    fp_count = r["actual_fps"]
                    angle    = r["post_angle_deg"]
                    primary  = ""
                    if r["tongue"] and r["tongue"][0]["primary"]:
                        primary = f'"{r["tongue"][0]["primary"]["word"]}"'
                    print(f"  {i+1:3}  {r['delta']:+.3f}  {fp_count:4}  "
                          f"{angle:+8.2f}°  {primary}")

            elif cmd == "reset":
                self._reset_sphere()
                print("  Sphere reset to default state.")

            else:
                print(f"  [!] Unknown command: {cmd}  (type 'help')")

    # ── Auto mode ─────────────────────────────────────────────────────────────

    def run_auto(self, word: Optional[str] = None,
                 delta: Optional[float] = None) -> None:
        """Non-interactive: run all diagnostics and print report."""
        print(self.BANNER)
        print(f"\n  {self.index.summary()}")
        print(f"\n  AUTO MODE — Full Diagnostic Report")
        print(f"  {'═'*54}")

        # Sphere
        self._print_sphere()

        # Pre-collapse
        dev  = self.sphere.isotropy_deviation()
        pred = self.sphere.predicted_focal_count()
        print(f"\n  Pre-Collapse: isotropy_dev={dev:.4f}  predicted_fps={pred}")

        # Sweep
        sweep = self.inspector.delta_sweep()
        self._print_sweep(sweep)

        # Natural collapse
        result = self.inspector.run(delta if delta is not None else 0.0)
        self._current_result = result
        self._print_result(result)

        # Reverse path
        if word:
            rp = self.inspector.reverse_path(word)
            self._print_reverse(rp)
        elif self.index.loaded:
            # Use first available word
            first = list(self.index._words.keys())[0] if self.index._words else None
            if first:
                rp = self.inspector.reverse_path(first)
                self._print_reverse(rp)

        print(f"\n  {'═'*54}")
        print(f"  Auto report complete.")


# ==============================================================================
# §5  COMMAND PARSER — called from Ptolemy REPL
# ==============================================================================

def parse_and_run(command: str) -> bool:
    """
    Parse /OutputTuning command and run the tuner.
    Returns True if handled.

    Accepts:
        /OutputTuning
        /OutputTuning --DM <data_dir>
        /OutputTuning --auto
        /OutputTuning --word <word>
        /OutputTuning --delta <f>
    """
    parts = command.strip().split()
    if not parts:
        return False
    if parts[0].lower() != "/outputtuning":
        return False

    # Parse flags
    dm_dir  = None
    auto    = False
    word    = None
    delta   = None

    i = 1
    while i < len(parts):
        p = parts[i].lower()
        if p == "--dm" and i + 1 < len(parts):
            dm_dir = parts[i + 1]; i += 2
        elif p == "--auto":
            auto = True; i += 1
        elif p == "--word" and i + 1 < len(parts):
            word = parts[i + 1]; i += 2
        elif p == "--delta" and i + 1 < len(parts):
            try:
                delta = float(parts[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1

    tuner = OutputTuner(dm_dir=dm_dir)
    if auto:
        tuner.run_auto(word=word, delta=delta)
    else:
        if word:
            tuner.run_auto(word=word, delta=delta)
        else:
            tuner.run_shell()

    return True


# ==============================================================================
# §6  STANDALONE ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Ptolemy OutputTuning — diagnostic shell for output generation"
    )
    parser.add_argument("--dm", metavar="DATA_DIR",
                        help="Load SemanticWord JSON data from directory")
    parser.add_argument("--auto", action="store_true",
                        help="Non-interactive: run all diagnostics and exit")
    parser.add_argument("--word", metavar="WORD",
                        help="Run reverse path from this word")
    parser.add_argument("--delta", type=float, default=None,
                        help="Override collapse delta (default 0.0)")
    args = parser.parse_args()

    tuner = OutputTuner(dm_dir=args.dm)
    if args.auto or args.word:
        tuner.run_auto(word=args.word, delta=args.delta)
    else:
        tuner.run_shell()


if __name__ == "__main__":
    main()
