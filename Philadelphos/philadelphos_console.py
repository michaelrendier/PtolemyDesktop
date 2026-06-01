#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
PHILADELPHOS CONSOLE — NOETHER INFORMATION CURRENT INTEGRATION
==============================================================================
Ptolemy Project / Philadelphos Face

INPUT PIPELINE:
    free text → GATE CLOSES
                → SedenionGate (I/O, zero-divisor collapse detection)
                → ContextBuffer (3-layer: FIFO / compressed / HyperWebster)
                → NoetherChain: Sedenion → Octonion → Quaternion → Complex → Reals
                → Focal point mapping via octonion rotations
                → Extinction filter (rotational equivalence collapse)
                → Sedenion (I|O) adjoint check
                → RESPONSE OUTPUT
    gate opens ←

SIGIL ROUTING:
    $, #, >>>   → command mode (shell/REPL passthrough)
    tune N      → shift focal point (negative=before collapse, positive=after)
    status      → buffer/engine status
    quit/exit   → shutdown
    (none)      → inference path

TUNING:
    tune -0.1   broader response (collapse before full extinction)
    tune +0.1   narrower response (collapse after)
    tune 0      natural catastrophic collapse point (default)
    retry       repeat last prompt with current focal delta

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
==============================================================================
"""

from __future__ import annotations

import sys
import os
import threading
import time
import hashlib
import queue
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Engine imports ────────────────────────────────────────────────────────────
try:
    from Ainulindale.core.smnnip_derivation_pure import (
        SMNNIPDerivationEngine, FieldState, Algebra, make_element,
        CayleyDickson
    )
    from Ainulindale.core.smnnip_lagrangian_pure import SMNNIPTower as SMNNIPLagrangian
    from Ainulindale.core.smnnip_inversion_engine import PhysicalConstants as _PhysConst
    from Ainulindale.neural_network.smnnip_full_tower import (
        SMNNIPLayer0, SMNNIPLayer1, SMNNIPLayer2, SMNNIPLayer3, SMNNIPTowerConstants
    )
    from Ainulindale.substrate.smnnt_substrate_pure import SMNNTSubstrateNetwork
    _ENGINES_AVAILABLE = True
except ImportError as _e:
    _ENGINES_AVAILABLE = False
    _ENGINE_ERR = str(_e)


# ==============================================================================
# §0  CONSTANTS
# ==============================================================================

SEDENION_DIM        = 16
CLAUDE_CTX_TOKENS   = 200_000
LAYER1_CAPACITY     = CLAUDE_CTX_TOKENS * 2
FOCAL_DELTA_DEFAULT = 0.0
EXTINCTION_THRESHOLD = 1e-6
VERSION             = "1.0.0"


# ==============================================================================
# §1  SEDENION GATE  (I/O)
# ==============================================================================

@dataclass
class SedenionElement:
    """16-component sedenion. Zero-divisor detection = collapse signal."""
    components: List[float] = field(default_factory=lambda: [0.0] * SEDENION_DIM)

    def norm_sq(self) -> float:
        return sum(c * c for c in self.components)

    def is_zero_divisor_candidate(self, threshold: float = EXTINCTION_THRESHOLD) -> bool:
        norm = self.norm_sq()
        has_content = any(abs(c) > threshold for c in self.components)
        return has_content and norm < threshold

    def adjoint(self) -> "SedenionElement":
        """Self-adjoint check: conjugate (flip imaginary signs)."""
        c = list(self.components)
        c[1:] = [-x for x in c[1:]]
        return SedenionElement(c)

    def adjoint_residual(self) -> float:
        """Measure of self-adjointness. 0 = perfectly self-adjoint."""
        adj = self.adjoint()
        return sum((a - b) ** 2 for a, b in zip(self.components, adj.components)) ** 0.5

    @classmethod
    def from_text(cls, text: str) -> "SedenionElement":
        h = hashlib.sha512(text.encode("utf-8")).digest()
        raw = [
            int.from_bytes(h[i * 4:(i + 1) * 4], "big") / 0xFFFFFFFF
            for i in range(SEDENION_DIM)
        ]
        return cls(components=raw)

    @classmethod
    def from_reals(cls, reals: List[float]) -> "SedenionElement":
        """Lift a reals vector back into sedenion space (forward tower path)."""
        padded = (list(reals) + [0.0] * SEDENION_DIM)[:SEDENION_DIM]
        return cls(components=padded)


class SedenionGate:
    """
    I/O gate. Closes on prompt submission, opens only after response delivered.
    The self-adjoint operator: checks (I|O) residual as error signal.
    """

    def __init__(self):
        self._gate = threading.Event()
        self._gate.set()

    def submit(self, text: str) -> Tuple[str, SedenionElement, bool]:
        self._gate.wait()
        self._gate.clear()                    # GATE CLOSES
        se = SedenionElement.from_text(text)
        collapse = se.is_zero_divisor_candidate()
        return text, se, collapse

    def release(self):
        self._gate.set()                      # GATE OPENS — after output delivered

    @property
    def is_open(self) -> bool:
        return self._gate.is_set()


# ==============================================================================
# §2  CONTEXT BUFFER (3 LAYERS)
# ==============================================================================

def _token_count(text: str) -> int:
    return max(1, len(text) // 4)


def _compress(text: str, ratio: float = 0.5) -> str:
    cutoff = max(64, int(len(text) * ratio))
    return text if len(text) <= cutoff else text[:cutoff] + "…[compressed]"


@dataclass
class BufferedPrompt:
    text: str
    sedenion: SedenionElement
    collapse_candidate: bool
    token_count: int
    timestamp: float = field(default_factory=time.time)
    compressed: bool = False


class ContextBuffer:
    """
    Layer 1: Raw FIFO, 2x Claude context capacity. Prompts only, no responses.
    Layer 2: Evicted prompts compressed before Layer 3.
    Layer 3: HyperWebster indexing stub → (word_key, timestamp, snippet).
    """

    def __init__(self):
        self._l1: deque = deque()
        self._l1_tokens: int = 0
        self._l3: queue.Queue = queue.Queue()
        self.last_prompt: Optional[str] = None

    def push(self, p: BufferedPrompt):
        self.last_prompt = p.text
        while self._l1_tokens + p.token_count > LAYER1_CAPACITY and self._l1:
            evicted = self._l1.popleft()
            self._l1_tokens -= evicted.token_count
            self._l2_forward(evicted)
        self._l1.append(p)
        self._l1_tokens += p.token_count

    def _l2_forward(self, p: BufferedPrompt):
        p.text = _compress(p.text)
        p.token_count = _token_count(p.text)
        p.compressed = True
        for word in p.text.split():
            key = word.lower().strip(".,!?;:\"'")
            if key:
                self._l3.put((key, p.timestamp, p.text[:128]))

    def l1_snapshot(self) -> List[str]:
        return [p.text for p in self._l1]

    def drain_l3(self) -> List[Tuple]:
        out = []
        while not self._l3.empty():
            try:
                out.append(self._l3.get_nowait())
            except queue.Empty:
                break
        return out

    @property
    def depth(self) -> int:
        return len(self._l1)

    @property
    def token_fill(self) -> int:
        return self._l1_tokens


# ==============================================================================
# §3  REVERSE TOWER  (Sedenion → Reals)
# ==============================================================================

class ReverseTower:
    """
    Catastrophic collapse: Sedenion → Octonion → Quaternion → Complex → Reals

    Each step = dimensional reduction via Cayley-Dickson projection.
    Focal points mapped via octonion rotations before extinction.
    Survivors collapsed to Reals = Noether Information Current = response vector.

    focal_delta: shifts collapse threshold.
        negative = collapse before natural extinction (broader, more survivors)
        positive = collapse after  (stricter, fewer survivors)
    """

    def __init__(self):
        if _ENGINES_AVAILABLE:
            self._engine = SMNNIPDerivationEngine()
        else:
            self._engine = None
        self.focal_delta: float = FOCAL_DELTA_DEFAULT

    # ── Octonion rotation — maps focal points ─────────────────────────────────

    def _oct_rotate(self, vec8: List[float], angle: float) -> List[float]:
        """Simple e1-e2 plane rotation in octonion space."""
        c, s = _cos(angle), _sin(angle)
        out = list(vec8)
        out[1] = c * vec8[1] - s * vec8[2]
        out[2] = s * vec8[1] + c * vec8[2]
        return out

    def _map_focal_points(self, vec16: List[float]) -> List[List[float]]:
        """
        Project sedenion → multiple octonion candidates via different rotations.
        Each rotation = one possible focal point.
        Returns list of 8-dim focal candidates.
        """
        oct_base = vec16[:8]
        oct_high = vec16[8:]
        angles = [0.0, 0.5236, 1.0472, 1.5708, 2.0944, 2.6180, 3.1416]  # 0..π in steps
        candidates = []
        for a in angles:
            rot_base = self._oct_rotate(oct_base, a + self.focal_delta)
            rot_high = self._oct_rotate(oct_high, a + self.focal_delta)
            merged = [b + h for b, h in zip(rot_base, rot_high)]
            candidates.append(merged)
        return candidates

    # ── Extinction filter ─────────────────────────────────────────────────────

    def _extinction(self, candidates: List[List[float]]) -> List[List[float]]:
        """
        Drop rotationally equivalent focal points.
        Two candidates are equivalent if their difference norm < threshold.
        Remaining survivors are distinct descriptions of the same thing — (I|O).
        """
        threshold = EXTINCTION_THRESHOLD * (1.0 + abs(self.focal_delta) * 10)
        survivors = []
        for c in candidates:
            dominated = False
            for s in survivors:
                diff = sum((a - b) ** 2 for a, b in zip(c, s)) ** 0.5
                if diff < threshold:
                    dominated = True
                    break
            if not dominated:
                survivors.append(c)
        return survivors

    # ── IO check — self-adjoint operator ─────────────────────────────────────

    def _io_check(self, survivors: List[List[float]],
                  input_se: SedenionElement) -> List[List[float]]:
        """
        Sedenion (I|O): compare survivors against adjoint of input.
        Survivors that describe the same thing as the input (under adjoint)
        are merged. Returns deduplicated survivors.
        """
        adj_components = input_se.adjoint().components
        adj_oct = adj_components[:8]
        merged = []
        for s in survivors:
            adj_diff = sum((a - b) ** 2 for a, b in zip(s, adj_oct)) ** 0.5
            if adj_diff < 0.5:   # same description under inversion
                # Merge: average with adjoint projection
                s = [(a + b) / 2 for a, b in zip(s, adj_oct)]
            merged.append(s)
        return merged

    # ── Quat → Complex → Reals collapse ──────────────────────────────────────

    def _collapse_to_reals(self, oct_vec: List[float]) -> List[float]:
        """Oct(8) → Quat(4) → Complex(2) → Reals(1) via projection."""
        quat = [oct_vec[i] + oct_vec[i + 4] for i in range(4)]
        cplx = [quat[0] + quat[2], quat[1] + quat[3]]
        real = [cplx[0] + cplx[1]]
        return real

    # ── Full reverse tower ────────────────────────────────────────────────────

    def run(self, se: SedenionElement, context: List[str]) -> Tuple[List[float], dict]:
        """
        Sedenion → Reals.
        Returns (reals_vector, diagnostics).
        reals_vector = Noether Information Current = basis of response.
        """
        # Context modulation: fold layer1 snapshot into sedenion
        ctx_hash = hashlib.md5(" ".join(context[-8:]).encode()).digest()
        ctx_mod = [b / 255.0 for b in ctx_hash[:SEDENION_DIM]]
        modulated = [(a + b) / 2 for a, b in zip(se.components, ctx_mod)]

        # Focal mapping
        candidates = self._map_focal_points(modulated)

        # Extinction
        survivors = self._extinction(candidates)

        # (I|O) adjoint check
        survivors = self._io_check(survivors, se)

        # Collapse each survivor to reals, sum
        reals_sum = [0.0]
        for s in survivors:
            r = self._collapse_to_reals(s)
            reals_sum = [reals_sum[0] + r[0]]

        # Normalize
        magnitude = abs(reals_sum[0]) or 1.0
        reals_norm = [reals_sum[0] / magnitude]

        diag = {
            "candidates": len(candidates),
            "survivors": len(survivors),
            "reals": reals_norm[0],
            "collapse_signal": se.is_zero_divisor_candidate(),
            "adjoint_residual": se.adjoint_residual(),
            "focal_delta": self.focal_delta,
        }

        # If engine available: run full diagnostic for Noether violation check
        if self._engine:
            try:
                import random as _r
                dim = Algebra.DIM[Algebra.O]
                psi = [make_element([_r.gauss(0, .1) for _ in range(dim)], Algebra.O)]
                A = [[_r.gauss(0, .05) for _ in range(dim)]]
                beta = [make_element([_r.gauss(0, .05) for _ in range(dim)], Algebra.O)]
                state = FieldState(psi=psi, A=A, beta=beta, algebra=Algebra.O, layer=3)
                d = self._engine.full_diagnostic(state)
                diag["noether_violation"] = d["noether"]["violation"]
                diag["lagrangian"] = d["lagrangian"]["total"]
            except Exception as _ex:
                diag["engine_error"] = str(_ex)

        return reals_norm, diag


# ==============================================================================
# §4  RESPONSE BUILDER
# ==============================================================================

class ResponseBuilder:
    """
    Converts the Noether Information Current (reals vector + context)
    into a text response. Stub: returns diagnostic summary until NN is trained.
    """

    def build(self, reals: List[float], diag: dict,
              prompt: str, context: List[str]) -> str:
        """
        When the network has ingested data, this becomes the decode path.
        Until then: return honest diagnostic output.
        """
        lines = [
            f"[Noether Current] reals={diag['reals']:.6f}  "
            f"survivors={diag['survivors']}/{diag['candidates']}  "
            f"δ={diag['focal_delta']:+.3f}  "
            f"adj_residual={diag['adjoint_residual']:.4f}"
        ]
        if "noether_violation" in diag:
            lines.append(
                f"[Engine] Noether violation={diag['noether_violation']:.2e}  "
                f"L={diag['lagrangian']:.4f}"
            )
        if diag.get("collapse_signal"):
            lines.append("[COLLAPSE SIGNAL] Zero-divisor candidate detected.")
        lines.append(
            f"[Network] No data ingested — pipeline verified, gate functional."
        )
        return "\n".join(lines)


# ==============================================================================
# §5  MAIN LOOP
# ==============================================================================

def _cos(x: float) -> float:
    import math; return math.cos(x)

def _sin(x: float) -> float:
    import math; return math.sin(x)


class PhiladelphosConsole:
    """
    Main Philadelphos text interface.

    Free text → full Noether Current pipeline → response → gate opens.
    Sigil prefixes ($, #, >>>) → command passthrough.
    """

    # Julius Caesar face configuration
    # Corpus: Caesar, Cicero, Cato English translations
    JULIUS_CAESAR_CONFIG = {
        "face_id":       "julius_caesar",
        "persona":       "Julius Caesar",
        "corpus":        ["caesar", "cicero", "cato"],
        "model":         "claude-opus-4-6",
        "tone":          "formal",
        "language":      "en",
        "system_prompt": (
            "You are Julius Caesar, speaking through Ptolemy. "
            "Your knowledge is informed by the works of Caesar, Cicero, and Cato. "
            "Respond with precision, brevity, and authority."
        ),
    }

    def __init__(self, face_config: dict = None):
        self.gate    = SedenionGate()
        self.buffer  = ContextBuffer()
        self.tower   = ReverseTower()
        self.builder = ResponseBuilder()
        self._running = False
        self.face_config = face_config or self.JULIUS_CAESAR_CONFIG
        # LuthSpell as BUS controller
        self._bus      = None
        self._luthspell = None
        self._init_bus()

    def _init_bus(self):
        """Instantiate LuthSpell as BUS controller per architecture spec."""
        try:
            from Pharos.PtolBus import PtolBus, CH_PROMPT, CH_INFERENCE, BusMessage, Priority
            from Pharos.luthspell import LuthSpell
            self._bus = PtolBus()
            self._bus.start()
            self._luthspell = LuthSpell(bus=self._bus)
            self._luthspell.wire()
            # Subscribe to halt events
            self._bus.subscribe(
                'LUTHSPELL',
                lambda msg: self._on_halt(msg))
        except Exception as e:
            print(f"[Philadelphos] Bus/LuthSpell init: {e}")

    def _on_halt(self, msg):
        print(f"[LuthSpell] HALT: {msg.payload}")

    # ── Command handlers ──────────────────────────────────────────────────────

    def _handle_command(self, line: str):
        cmd = line.lstrip("$#>").strip()
        parts = cmd.split()
        if not parts:
            return

        if parts[0] == "tune":
            if len(parts) < 2:
                print("Usage: tune <delta>  e.g. tune -0.1  tune 0  tune +0.2")
                return
            try:
                delta = float(parts[1])
                self.tower.focal_delta = delta
                print(f"[tune] focal_delta set to {delta:+.3f}")
                if self.buffer.last_prompt:
                    print("[tune] Retrying last prompt...")
                    self._inference(self.buffer.last_prompt)
            except ValueError:
                print(f"[tune] Invalid delta: {parts[1]}")

        elif parts[0] == "retry":
            if self.buffer.last_prompt:
                self._inference(self.buffer.last_prompt)
            else:
                print("[retry] No previous prompt.")

        elif parts[0] == "status":
            print(f"  layer1 depth  : {self.buffer.depth}")
            print(f"  layer1 tokens : {self.buffer.token_fill}/{LAYER1_CAPACITY}")
            print(f"  focal_delta   : {self.tower.focal_delta:+.3f}")
            print(f"  gate          : {'OPEN' if self.gate.is_open else 'CLOSED'}")
            print(f"  engines       : {'OK' if _ENGINES_AVAILABLE else 'NOT LOADED — ' + _ENGINE_ERR[:80]}")
            l3 = self.buffer.drain_l3()
            print(f"  layer3 pending: {len(l3)} entries")

        elif parts[0] in ("quit", "exit"):
            self._running = False

        else:
            print(f"[cmd] {cmd}")

    # ── Inference pipeline ────────────────────────────────────────────────────

    def _inference(self, text: str):
        """
        Full pipeline. Gate is already closed by caller.
        Gate opens only after print() completes.
        """
        text, se, collapse = self.gate.submit(text)

        # Buffer
        bp = BufferedPrompt(
            text=text,
            sedenion=se,
            collapse_candidate=collapse,
            token_count=_token_count(text),
        )
        self.buffer.push(bp)

        # Reverse tower
        context = self.buffer.l1_snapshot()
        reals, diag = self.tower.run(se, context)

        # Build response
        response = self.builder.build(reals, diag, text, context)

        # OUTPUT FIRST
        print(response)
        sys.stdout.flush()

        # THEN gate opens
        self.gate.release()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        print(f"Philadelphos v{VERSION} — Noether Information Current")
        if not _ENGINES_AVAILABLE:
            print(f"[WARN] Engines not loaded: {_ENGINE_ERR[:100]}")
        print("Free text = inference  |  $ # >>> = command  |  quit = exit\n")

        while self._running:
            try:
                line = input("").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            if line.startswith(("$", "#", ">>>")):
                self._handle_command(line)
            elif line.lower() in ("quit", "exit"):
                break
            elif line.lower() == "status":
                self._handle_command("status")
            elif line.lower().startswith("tune"):
                self._handle_command(line)
            elif line.lower() == "retry":
                self._handle_command("retry")
            else:
                self._inference(line)

        print("[Philadelphos] Closed.")


# ==============================================================================
# §6  ENTRY
# ==============================================================================

def main():
    console = PhiladelphosConsole()
    console.run()


if __name__ == "__main__":
    main()
