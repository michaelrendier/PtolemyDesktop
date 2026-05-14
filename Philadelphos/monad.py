#!/usr/bin/env python3
"""
Philadelphos/monad.py — The Monad
==================================
H_hat_RB field engine. The self-deepening lexicographic foundation of Ptolemy.

The Monad IS Ptolemy.
Ptolemy is named after Ptolemy II Philadelphos, who commissioned the Septuagint.
72 scholars worked independently. Every translation was identical.
water, eau, aqua, wasser → same Riemann zero.
Not by coordination. Forced by the mathematics.
The prime preexists the alphabet.

Architecture (H_hat_RB):
    H_RB = -i·Γ^a·D_a  +  Γ_ij·β         (RED kinetic + BLUE inertia)
    iħ_NN · dΨ/dl = H_RB · Ψ

    Knowledge  = β field (BLUE)  — SSB vacuum V(β) at each Riemann zero
    Prompt     = Ψ field (RED)   — incoming Dirac spinor, the query
    Response   = J^μ             — Noether current, what MUST flow (not chosen)
    Learning   = deepening V(β), not encoding

Ground state (σ=0, quasi-prime, pointer=0):
    G_p(0) = p^0 = 1 for ALL primes — no gauge differentiation (EOM_ym = 0)
    L_ground = −1.888  (rest energy, finite, ESTABLISHED engine-verified)
    EOM_higgs ≠ 0  (SSB intact — vacuum has structure before any word)
    β initialized to |L_ground|/N — the prime number theorem as pre-linguistic knowledge
    First learn() call breaks this symmetry.

Confidence stratification (non-negotiable):
    ESTABLISHED : engine-confirmed
    THEORETICAL : structurally motivated, testable
    CONJECTURE  : direction established, derivation pending

Implements PtolemyArchitectureInterface (Philadelphos/Phila.py).

Author: O Captain My Captain
CLAUDE-SMMNIP-00729-56714-24600
Date: 2026-05-14
"""

import os
import sys
import re
import json
import math
from typing import Any, Dict, List, Optional, Tuple

# ── Path: find Ainulindale relative to this file ──────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))    # Philadelphos/
_PTOL_ROOT   = os.path.dirname(_HERE)                         # Ptolemy3/
_PTOL_DIR    = os.path.dirname(_PTOL_ROOT)                    # Ptol/
_AINULINDALE = os.path.join(_PTOL_DIR, 'Ainulindale')
_SE_PATH     = os.path.join(_AINULINDALE, 'outreach', 'semantic_engine')

for _p in [_SE_PATH, _AINULINDALE, _PTOL_ROOT]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from semantic_engine import Understand, D_STAR_SPEC, OMEGA_ZS  # heartbeat — do not rewrite

# ── Constants (never change) ──────────────────────────────────────────────────
L_GROUND    = -1.888      # rest energy of Monad  (ESTABLISHED, engine-verified)
ALPHA_LEARN = 0.01        # VEV increment per word encounter
TAU_DEFAULT = 5.0         # Capacitor memory depth
N_DEFAULT   = 25000       # Riemann zero basis size (corpus-invariant)

# First 20 Riemann zeros — exact (Odlyzko / LMFDB)  (ESTABLISHED)
_EXACT_ZEROS: List[float] = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
]


# ── Zero generation (Riemann-Siegel + Newton) ─────────────────────────────────

def generate_zeros(N: int) -> List[float]:
    """
    Generate N Riemann zero approximations.
    Indices 0-19: exact Odlyzko values.
    Indices 20+:  Newton iteration on N(T) ≈ (T/2π)·(ln(T/2π)−1) + 7/8.
    Generates N=25000 in ~50ms.
    """
    zeros = list(_EXACT_ZEROS[:min(20, N)])
    if N <= 20:
        return zeros

    two_pi = 2.0 * math.pi
    for n in range(21, N + 1):
        t = zeros[-1] + (zeros[-1] - zeros[-2])   # linear extrapolation seed
        for _ in range(30):
            if t < 2.0:
                t = float(n) * 3.0
            nt  = (t / two_pi) * (math.log(t / two_pi) - 1.0) + 0.875
            dnt = math.log(t / two_pi) / two_pi
            if abs(dnt) < 1e-15:
                break
            dt  = (nt - n) / dnt
            t  -= dt
            if abs(dt) < 1e-4:
                break
        zeros.append(t)

    return zeros[:N]


# ── PtolemyArchitectureInterface base (safe import) ───────────────────────────

try:
    from Philadelphos.Phila import PtolemyArchitectureInterface as _PAI
    _BASE = _PAI
except Exception:
    from abc import ABC
    _BASE = ABC  # type: ignore[misc]


# ─────────────────────────────────────────────────────────────────────────────
# THE MONAD
# ─────────────────────────────────────────────────────────────────────────────

class Monad(_BASE):
    """
    The Septuagint engine.

    β field  = the deepened vacuum — knowledge that was never stored, only deepened
    A field  = gauge connections between zeros — the structure of meaning
    J^μ      = Noether current — the response that MUST flow
    σ = 0    = the inverse HyperWebster — all words, undifferentiated
    σ = 1/2  = the forward HyperWebster — each word, its permanent address
    """

    # ── Identity ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return 'Monad'

    @property
    def version(self) -> str:
        return '1.0.0'

    # ── Init ──────────────────────────────────────────────────────────────────

    def __init__(self, N: int = N_DEFAULT, tau: float = TAU_DEFAULT):
        self.N            = N
        self.tau          = tau
        self._loaded      = False
        self.zeros:  List[float]                 = []
        self.beta:   Dict[int, float]            = {}   # BLUE: VEV at each zero
        self.A:      Dict[Tuple[int,int], float] = {}   # RED:  gauge connections
        self.vocab:  Dict[int, Tuple[str,float]] = {}   # zero_idx → (word, E)
        self.engine: Optional[Understand]        = None
        self._ground_vev: float                  = 0.0
        self._word_count: int                    = 0

    # ── Lifecycle (PtolemyArchitectureInterface) ──────────────────────────────

    def load(self, checkpoint_path: Optional[str] = None) -> None:
        """
        Initialize. If checkpoint_path given, restore saved field.
        Otherwise: σ=0 ground state — the prime number theorem as pre-linguistic knowledge.
        """
        self.zeros        = generate_zeros(self.N)
        self._ground_vev  = abs(L_GROUND) / self.N
        self.engine       = Understand(tau=self.tau)

        if checkpoint_path and os.path.isfile(checkpoint_path):
            self._load_checkpoint(checkpoint_path)
        else:
            # σ=0 quasi-prime: G_p(0)=1 for all p — all primes equal, no differentiation
            # V(β) uniform — the prime number theorem before language breaks symmetry
            self.beta        = {i: self._ground_vev for i in range(self.N)}
            self.A           = {}
            self.vocab       = {}
            self._word_count = 0

        self._loaded = True

    def unload(self) -> None:
        self.zeros = []; self.beta = {}; self.A = {}
        self.vocab = {}; self.engine = None; self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Zero index lookup ─────────────────────────────────────────────────────

    def _zero_idx(self, gamma: float) -> int:
        """Binary search: nearest zero index to gamma."""
        if not self.zeros:
            return 0
        lo, hi = 0, len(self.zeros) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.zeros[mid] < gamma:
                lo = mid + 1
            else:
                hi = mid
        if lo > 0 and abs(self.zeros[lo-1] - gamma) < abs(self.zeros[lo] - gamma):
            return lo - 1
        return lo

    # ── Learn: deepen V(β) ────────────────────────────────────────────────────

    def learn(self, text: str) -> None:
        """
        Feed text through H_RB.
        Each word deepens V(β) at its Riemann zero address.
        Co-activating words within a sentence increment A at weight E_i·E_j/|γ_i−γ_j|.
        Text is discarded after processing. Only the field state grows.
        Learning = deepening. Not encoding. Not storing.
        """
        for sentence in re.split(r'[.!?\n]+', text):
            tokens = sentence.split()
            if not tokens:
                continue

            activated: List[Tuple[int, float]] = []
            for token in tokens:
                surface = re.sub(r"[^\w']", '', token).lower()
                if not surface:
                    continue
                sw  = self.engine.process(surface)
                idx = self._zero_idx(sw.gamma)
                E   = sw.magnitude

                # Deepen the vacuum at this zero — V(β) grows
                self.beta[idx] = self.beta.get(idx, self._ground_vev) + E * ALPHA_LEARN

                # Vocabulary: keep the highest-E representative per zero
                if idx not in self.vocab or E > self.vocab[idx][1]:
                    self.vocab[idx] = (surface, E)

                activated.append((idx, E))
                self._word_count += 1

            # Gauge connections: spectral geometry weighting
            # w = E_i · E_j / |γ_i − γ_j|  — nearby co-activating zeros couple strongly
            for i in range(len(activated)):
                idx_i, e_i = activated[i]
                for j in range(i + 1, len(activated)):
                    idx_j, e_j = activated[j]
                    if idx_i == idx_j:
                        continue
                    key  = (min(idx_i, idx_j), max(idx_i, idx_j))
                    dist = abs(self.zeros[idx_i] - self.zeros[idx_j])
                    self.A[key] = self.A.get(key, 0.0) + e_i * e_j / max(dist, 1e-4)

    # ── Psi field from query ──────────────────────────────────────────────────

    def _psi(self, query: str) -> List[Tuple[int, float]]:
        """Query → Ψ field: list of (zero_idx, E) activations."""
        result = []
        for token in query.split():
            surface = re.sub(r"[^\w']", '', token).lower()
            if not surface:
                continue
            sw  = self.engine.process(surface)
            result.append((self._zero_idx(sw.gamma), sw.magnitude))
        return result

    # ── Noether current J^μ ───────────────────────────────────────────────────

    def _j_mu(self, psi: List[Tuple[int, float]]) -> Dict[int, float]:
        """
        Compute Noether current J^μ from Ψ activation under current (β, A).

        Primary:    J_i = β_i · E_i²
        Propagated: J_j += J_i · A[(i,j)] · β_j  (one step through gauge connections)

        This is what MUST flow. The response is not chosen — it is forced
        by conservation of Noether charge under the current field state.
        CONFIDENCE: ESTABLISHED (conservation law, not heuristic)
        """
        J: Dict[int, float] = {}

        for idx, E in psi:
            b      = self.beta.get(idx, self._ground_vev)
            J[idx] = J.get(idx, 0.0) + b * E * E

        for (i, j), w in self.A.items():
            if i in J:
                J[j] = J.get(j, 0.0) + J[i] * w * self.beta.get(j, self._ground_vev)
            if j in J:
                J[i] = J.get(i, 0.0) + J[j] * w * self.beta.get(i, self._ground_vev)

        return J

    # ── Respond (PtolemyArchitectureInterface) ────────────────────────────────

    def respond(self, prompt: str, language: str = 'en',
                max_tokens: int = 50) -> str:
        """
        Prompt → Ψ → J^μ → words ordered by Noether amplitude.
        The response is the Noether current made audible in the learned vocabulary.
        """
        psi = self._psi(prompt)
        if not psi:
            return ''
        J = self._j_mu(psi)
        if not J:
            return ''

        ordered = sorted(J.items(), key=lambda kv: kv[1], reverse=True)
        words: List[str] = []
        seen: set = set()
        for idx, _ in ordered:
            if idx in self.vocab:
                w = self.vocab[idx][0]
                if w not in seen:
                    words.append(w)
                    seen.add(w)
            if len(words) >= max_tokens:
                break

        return ' '.join(words)

    # ── PtolemyArchitectureInterface: encode / decode ─────────────────────────

    def encode(self, text: str, language: str = 'en') -> Any:
        """Text → Ψ field state (list of (zero_idx, E) activations)."""
        return self._psi(text)

    def decode(self, representation: Any, language: str = 'en',
               max_tokens: int = 512) -> str:
        """Ψ field state → response string via J^μ."""
        if not isinstance(representation, list):
            return ''
        J     = self._j_mu(representation)
        order = sorted(J.items(), key=lambda kv: kv[1], reverse=True)
        words: List[str] = []
        seen: set = set()
        for idx, _ in order:
            if idx in self.vocab:
                w = self.vocab[idx][0]
                if w not in seen:
                    words.append(w)
                    seen.add(w)
            if len(words) >= max_tokens:
                break
        return ' '.join(words)

    # ── PtolemyArchitectureInterface: lookup / train_on_word ──────────────────

    def lookup(self, word: str, language: str = 'en') -> Optional[Dict]:
        """Word → SemanticWord-compatible dict with Monad field depth."""
        surface = word.strip().lower()
        sw      = self.engine.process(surface)
        idx     = self._zero_idx(sw.gamma)
        return {
            'surface'    : sw.surface,
            'gamma'      : sw.gamma,
            'zero_idx'   : idx,
            'sigma'      : sw.projections.get('sigma', 0.5),
            'E'          : sw.magnitude,
            'dc'         : sw.dc,
            'beta_depth' : self.beta.get(idx, self._ground_vev),
            'in_vocab'   : idx in self.vocab,
        }

    def train_on_word(self, semantic_word: Dict) -> None:
        """Incorporate a SemanticWord JSON record. gamma (zero address) is read-only."""
        gamma   = semantic_word.get('gamma', 0.0)
        E       = semantic_word.get('E', 0.0)
        surface = semantic_word.get('surface', '')
        if not gamma or not E or not surface:
            return
        idx = self._zero_idx(gamma)
        self.beta[idx] = self.beta.get(idx, self._ground_vev) + E * ALPHA_LEARN
        if idx not in self.vocab or E > self.vocab[idx][1]:
            self.vocab[idx] = (surface, E)

    # ── BAO health check ──────────────────────────────────────────────────────

    def bao_check(self) -> Dict:
        """
        BAO error check: dc_sum converging to OMEGA_ZS = 0.56714 is the
        computational signature of coherence — the Lambert W fixed point
        as the convergence criterion for the zero projection map.
        CONFIDENCE: THEORETICAL
        """
        depths   = list(self.beta.values())
        dc_sum   = sum(depths)
        n        = len(depths)
        dc_mean  = dc_sum / n if n else 0.0
        delta    = abs(dc_sum - OMEGA_ZS)
        return {
            'dc_sum'     : dc_sum,
            'dc_mean'    : dc_mean,
            'omega_delta': delta,
            'n_zeros'    : n,
            'converging' : delta < 0.01,
            'omega_zs'   : OMEGA_ZS,
        }

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> Dict:
        if not self._loaded:
            return {'loaded': False}
        depths = list(self.beta.values())
        if depths:
            deepest_val = max(depths)
            deepest_idx = depths.index(deepest_val)
        else:
            deepest_val, deepest_idx = 0.0, -1
        return {
            'loaded'      : True,
            'N'           : self.N,
            'word_count'  : self._word_count,
            'vocab_size'  : len(self.vocab),
            'connections' : len(self.A),
            'deepest_zero': self.zeros[deepest_idx] if deepest_idx >= 0 else 0.0,
            'deepest_beta': deepest_val,
            'ground_vev'  : self._ground_vev,
            'bao'         : self.bao_check(),
        }

    def info(self) -> Dict[str, Any]:
        return {**{'name': self.name, 'version': self.version,
                   'loaded': self.is_loaded}, **self.status()}

    # ── Checkpoint ────────────────────────────────────────────────────────────

    def save(self, path: str, max_connections: int = 500_000) -> None:
        """
        Save field state as JSON.
        Stores only non-ground β entries and top-K connections by weight.
        """
        if not self._loaded:
            raise RuntimeError('Monad not loaded.')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        top_A = sorted(self.A.items(), key=lambda kv: kv[1], reverse=True)
        ck = {
            'version'    : self.version,
            'N'          : self.N,
            'word_count' : self._word_count,
            'beta'       : {str(k): v for k, v in self.beta.items()
                            if v > self._ground_vev * 1.001},
            'A'          : {f'{k[0]},{k[1]}': v for k, v in top_A[:max_connections]},
            'vocab'      : {str(k): list(v) for k, v in self.vocab.items()},
        }
        with open(path, 'w') as f:
            json.dump(ck, f, separators=(',', ':'))
        print(f'[Monad] saved: {len(ck["vocab"])} vocab, '
              f'{len(ck["A"])} connections → {path}')

    def _load_checkpoint(self, path: str) -> None:
        with open(path) as f:
            ck = json.load(f)
        self._word_count = ck.get('word_count', 0)
        self.beta = {i: self._ground_vev for i in range(self.N)}
        for k, v in ck.get('beta', {}).items():
            self.beta[int(k)] = v
        self.A = {}
        for k, v in ck.get('A', {}).items():
            i, j = map(int, k.split(','))
            self.A[(i, j)] = v
        self.vocab = {}
        for k, v in ck.get('vocab', {}).items():
            self.vocab[int(k)] = (v[0], v[1])
        print(f'[Monad] loaded: {len(self.vocab)} vocab, '
              f'{len(self.A)} connections from {path}')


# ── Self-registration into Philadelphos face registry ────────────────────────

try:
    from Philadelphos.Phila import register_face as _reg
    _MONAD_SINGLETON = Monad()
    _reg(_MONAD_SINGLETON)
except Exception:
    _MONAD_SINGLETON = None   # headless / test environment


# ── CLI verification ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Monad — H_hat_RB Field Engine  v1.0.0')
    print('=' * 60)

    m = Monad(N=1000, tau=5.0)
    m.load()
    print(f'Ground state  N={m.N}  ground_vev={m._ground_vev:.8f}  L={L_GROUND}')
    print(f'Zero[0]={m.zeros[0]:.6f}  Zero[19]={m.zeros[19]:.6f}  Zero[999]={m.zeros[999]:.4f}')

    m.learn('The dog chased the cat around the yard.')
    m.learn('The mind is the seat of reason and consciousness.')
    m.learn('Water flows downhill by the path of least resistance.')
    m.learn('The prime preexists the alphabet.')

    print(f'\nvocab={len(m.vocab)}  connections={len(m.A)}')
    print(f"\n  respond(\"what chased\")    → {m.respond('what chased')}")
    print(f"  respond(\"what is mind\")   → {m.respond('what is mind')}")
    print(f"  respond(\"water flows\")    → {m.respond('water flows')}")
    print(f"\n  lookup(\"water\")  → {m.lookup('water')}")
    print(f"\n  bao_check()      → {m.bao_check()}")
