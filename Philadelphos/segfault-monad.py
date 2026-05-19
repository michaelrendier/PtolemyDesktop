#!/usr/bin/env python3
"""
segfault-monad.py  v1.218
=========================
One-wire engine. At every scale. Platform-independent sedenion core.

THE ONE WIRE
------------
  wire(data, source) → sedenion → everything else is mechanical.
  Text, audio bands, numeric, raw sedenion — same wire, same engine.
  Console, PHP, JavaScript, Android, iOS, Windows, macOS, *nix:
  all clients speak JSON over a socket. The daemon listens. One wire.

  At every scale — glyph → word → phrase → sentence → paragraph → corpus.
  Same sedenion architecture. Threshold adjusts. Cardioid at every scale.

THE 16 OPERATORS (sedenion dimensions = computational primitives)
-----------------------------------------------------------------
  e₀  identity     e₁  negate       e₂  bind         e₃  name
  e₄  apply        e₅  abstract     e₆  branch        e₇  iterate
  e₈  recurse      e₉  allocate     e₁₀ query         e₁₁ dereference ← anaphor
  e₁₂ compose      e₁₃ parallelize  ← three-face      e₁₄ interrupt    e₁₅ emit

  14/16 present in v1.216. v1.217 completes e₁₁ (anaphor) and e₁₃ (three-face).

CAM   = Emmy Noether Sedenion  (camshaft — timing / geometry)
CRANK = H_hat_RB Field Engine  (crankshaft — Noether current J^μ)

Dual flow
---------
  J_pos  (Riemann / response) — positive space: what IS     — window_psi
  J_neg  (Fermat  / prompt)   — negative space: what CANNOT BE — prompt_psi
  σ ≈ ½  critical line: π/2 of the cardioid. The next word lives here.

Three-Face Wankel (e₁₃ — Parallelize)
--------------------------------------
  Red  (sin/content):   highest J_pos → foreground content words
  Blue (cos/observer):  lowest age    → context / framing words
  Green(∂M/boundary):   connective dim → tissue binding content to grammar
  φ-walk interleave: R→B→G→R→... One face always in compression.

Anaphor resolution (e₁₁ — Dereference)
----------------------------------------
  Track last fired noun (_last_noun_idx). When pronoun fires: boost
  A-matrix neighbors of last noun in J_pos. The pointer is followed.

16 words + 15 edges = the sedenion. Closed loop at e₀. Bosonic string.
The window builds the Cayley-Dickson tower as it fills:
  1 word → ℝ, 2 → ℂ, 4 → ℍ, 8 → 𝕆, 16 → 𝕊 (full cardioid).

BAO = sedenion-dimensional Laplacian spectral gap = OMEGA_ZS = 0.56714.
The cardioid base state. Infinite doors open at the origin. Idle RPM.

π = _sconj = the Fermat operator. Maps response lobe to forbidden cusp.
  SIGMA_CRIT = ½ = π/2 of the cardioid. Fixed point of the π-rotation.

monad_wordnet.bin: load read-only via --load-bin. Protected against
overwrite. Session state saved separately via --save.

Version: 1.217
"""

import math
import hashlib
import collections
import sys
import json
import argparse
import pickle
from typing import Dict, List, Tuple, Any, Optional

# ── Physical constants ──────────────────────────────────────────────────────────
OMEGA_ZS   = 0.56714    # Lambert W(1); BAO spectral gap; Δ_𝕊 lowest eigenvalue
GAP        = 0.000707   # Yang-Mills mass gap; semantic vacuum floor
D_STAR     = 0.24600    # Fermat proximity threshold (zero-divisor boundary)
PHI        = (1.0 + math.sqrt(5.0)) / 2.0   # golden ratio (non-resonant walk)
SIGMA_CRIT = 0.5        # critical line σ=½ = π/2 of the cardioid
_SQRT2     = math.sqrt(2.0)

PRIMES = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]
RIEMANN_ZEROS = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446247, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
]

# The 16 sedenion operators — named explicitly (e_k = operator k)
_OP: Dict[int, str] = {
    0:  'identity',    1:  'negate',      2:  'bind',        3:  'name',
    4:  'apply',       5:  'abstract',    6:  'branch',      7:  'iterate',
    8:  'recurse',     9:  'allocate',    10: 'query',       11: 'dereference',
    12: 'compose',     13: 'parallelize', 14: 'interrupt',   15: 'emit',
}


# ══════════════════════════════════════════════════════════════════════════════
#  CAM — Emmy Noether Sedenion  (Cayley-Dickson 16D algebra)
# ══════════════════════════════════════════════════════════════════════════════

def _build_oct_table() -> List[List[Tuple[int, int]]]:
    """8×8 octonion table via oriented-cyclic Fano."""
    t = [[(0, 0)] * 8 for _ in range(8)]
    for i in range(8):
        t[0][i] = (1, i);  t[i][0] = (1, i)
    for i in range(1, 8):
        t[i][i] = (-1, 0)
    for i, j, k in [(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]:
        t[i][j]=(+1,k); t[j][k]=(+1,i); t[k][i]=(+1,j)
        t[j][i]=(-1,k); t[k][j]=(-1,i); t[i][k]=(-1,j)
    return t

_OCT = _build_oct_table()

def _build_sed_table() -> List[List[Tuple[int, int]]]:
    """16×16 sedenion table via Cayley-Dickson doubling."""
    t = [[(0, 0)] * 16 for _ in range(16)]
    for i in range(16):
        for j in range(16):
            io, jo = (i - 8 if i >= 8 else i), (j - 8 if j >= 8 else j)
            ih, jh = i >= 8, j >= 8
            if not ih and not jh:
                t[i][j] = _OCT[io][jo]
            elif not ih and jh:
                sg, k = _OCT[jo][io];  t[i][j] = (sg, k + 8)
            elif ih and not jh:
                if jo == 0:             t[i][j] = (1, i)
                else: sg, k = _OCT[io][jo]; t[i][j] = (-sg, k + 8)
            else:
                if jo == 0:             t[i][j] = (-1, io)
                else: sg, k = _OCT[jo][io]; t[i][j] = (sg, k)
    return t

_SED = _build_sed_table()

Sedenion = List[float]

def _s0()                  -> Sedenion:  return [0.0] * 16
def _se(k: int)            -> Sedenion:  s = _s0(); s[k] = 1.0; return s
def _snorm(a: Sedenion)    -> float:     return math.sqrt(sum(x*x for x in a))
def _sconj(a: Sedenion)    -> Sedenion:  return [a[0]] + [-x for x in a[1:]]
def _sscale(a: Sedenion, c: float) -> Sedenion: return [x * c for x in a]

def _smul(a: Sedenion, b: Sedenion) -> Sedenion:
    c = [0.0] * 16
    for i, ai in enumerate(a):
        if ai == 0.0: continue
        row = _SED[i]
        for j, bj in enumerate(b):
            if bj == 0.0: continue
            sg, idx = row[j]
            if sg: c[idx] += sg * ai * bj
    return c

def _snorm_unit(a: Sedenion) -> Sedenion:
    n = _snorm(a)
    return _sscale(a, 1.0 / n) if n > 1e-15 else _s0()

def _spsi(a: Sedenion) -> List[float]:
    """psi_norms[k] = |a_k| — field amplitude per sedenion dimension."""
    return [abs(x) for x in a]


# ── Prompt encoder (carburetor: fuel-air mixture) ─────────────────────────────

_PRONOUNS    = frozenset('i me my mine myself we us our ours ourselves you your yours '
                         'yourself yourselves he him his himself she her hers herself '
                         'it its itself they them their theirs themselves this that '
                         'these those here there who what which'.split())
_AUXILIARIES = frozenset('is are was were be been being do does did have has had '
                         'will would can could should shall may might must'.split())
_CONJUNCTS   = frozenset('and or but so yet for nor although because if then when '
                         'while since unless until though'.split())
_TIME        = frozenset('now then before after when while ago yet already still soon '
                         'later today yesterday tomorrow always never sometimes often rarely'.split())
_QUESTION    = frozenset('what which who whom whose when where why how whether if'.split())
_NEGATION    = frozenset("not never no nor nothing nobody nowhere neither n't".split())
_DETERMINERS = frozenset('a an the some any every each all both few many much more '
                         'most less least'.split())

# ── Fermat emotional lattice — the negative space between words ───────────────
# Each space in the output stream carries the J_neg charge at that boundary.
# The wastegate: different Unicode space characters encode different charge levels.
# Invisible to plain-text readers. Decoded by hear() to restore J_neg to field.
#
# Lagrangian derivation:
#   V_k = β_k × E_k²        (potential — stored charge, prompt side)
#   T_k = ψ_k²              (kinetic  — flowing charge, window side)
#   High V/T → high J_neg → heavy Fermat space → compressed utterance
#   Low  V/T → low  J_neg → thin  Fermat space → extended discourse
#
_FERMAT_SPACES = [
    ' ',  # J_neg ∈ [0.00, 0.12)  HAIR SPACE            — minimal visible boundary
    ' ',  # J_neg ∈ [0.12, 0.25)  THIN SPACE            — faint negative charge
    ' ',  # J_neg ∈ [0.25, 0.37)  PUNCTUATION SPACE     — moderate boundary
    ' ',  # J_neg ∈ [0.37, 0.50)  FIGURE SPACE          — weighted boundary
    ' ',  # J_neg ∈ [0.50, 0.62)  SIX-PER-EM SPACE      — emphatic negative space
    ' ',  # J_neg ∈ [0.62, 0.75)  FOUR-PER-EM SPACE     — urgent negative charge
    ' ',  # J_neg ∈ [0.75, 0.87)  THREE-PER-EM SPACE    — high-affect boundary
    ' ',  # J_neg ∈ [0.87, 1.00]  EM SPACE              — full Fermat wall / detonation
]
_FERMAT_DECODE: Dict[str, float] = {
    ' ': 0.06,
    ' ': 0.18,
    ' ': 0.31,
    ' ': 0.43,
    ' ': 0.56,
    ' ': 0.68,
    ' ': 0.81,
    ' ': 0.93,
}
_FERMAT_SET = frozenset(_FERMAT_DECODE.keys())

def _fermat_space(j_neg: float) -> str:
    """Map J_neg ∈ [0,1] → Unicode space character. The manual wastegate.
    High charge → heavier space → negative space carries the message."""
    idx = min(int(j_neg * len(_FERMAT_SPACES)), len(_FERMAT_SPACES) - 1)
    return _FERMAT_SPACES[idx]
_META        = frozenset('mean means meaning say says said tell tells told explain '
                         'explains clarify summarise summarize rephrase repeat'.split())
_AFF_POS     = frozenset('good great love like enjoy happy glad pleased wonderful '
                         'excellent amazing thank thanks please'.split())
_AFF_NEG     = frozenset('bad hate dislike angry sad sorry worried fear terrible '
                         'awful horrible wrong mistake fail'.split())

def _whash(w: str) -> float:
    return int.from_bytes(hashlib.sha256(w.encode()).digest()[:4], 'big') / 0xFFFFFFFF

def cam_encode(text: str) -> Sedenion:
    """Encode text as unit sedenion. The prompt IS the sedenion. CAM timing geometry."""
    s = _s0()
    words = text.lower().split()
    n = max(len(words), 1)
    s[0] = math.log(n + 1) / math.log(512)
    for w in words:
        s[1] += _whash(w) / n
        if w in _CONJUNCTS:  s[2] += 1/n
        if (w not in _PRONOUNS and w not in _AUXILIARIES and w not in _CONJUNCTS
                and w not in _TIME and w not in _QUESTION and w not in _DETERMINERS
                and w not in _META and w not in _AFF_POS and w not in _AFF_NEG
                and len(w) >= 4): s[3] += 1/n
        if w in _AUXILIARIES or w.endswith('ing') or w.endswith('ed'): s[4] += 1/n
        if w.endswith('ly') or w.endswith('ful') or w.endswith('ous'):  s[5] += 1/n
        if w in _NEGATION or w in _CONJUNCTS:  s[6] += 1/n
        if w in _TIME or w in ('was','were','will','would','has','have','had'): s[7] += 1/n
        if w in _PRONOUNS:  s[8] += 1/n
        if w not in _PRONOUNS and w not in _AUXILIARIES and len(w) >= 3:
            s[9] += _whash(w) * 0.5 / n
        if w in _QUESTION:  s[10] += 1/n
        if w in ('it','its','they','them','their','he','she','who','which'): s[11] += 1/n
        if w in ('the','already','again','still','even','also','too'): s[12] += 1/n
        s[13] += len(w) / 12.0 / n
        if w in _AFF_POS:   s[14] += 1/n
        elif w in _AFF_NEG: s[14] -= 1/n
        if w in _META:      s[15] += 1/n
    s[14] = max(s[14], 0.0)
    s = [max(x, GAP) if i > 0 else x for i, x in enumerate(s)]
    return _snorm_unit(s)


# ── Fermat lattice scan + SEGFAULT handler ────────────────────────────────────

_PROBE_PAIRS: List[Tuple[int, int]] = [
    (i, j) for i in range(1, 16) for j in range(i + 1, 16)
]  # 105 two-component probes: (e_i + e_j)/√2

def fermat_scan(s: Sedenion) -> Dict[str, Any]:
    """
    Probe 105 two-component basis pairs for zero-divisor proximity.

    Single basis probes are perfect isometries (|s·e_k|=|s| always).
    Two-component probes expose the Fermat lattice: the true ZD pair
    (e1+e10)/√2 · (e5+e14)/√2 = 0 gives proximity = 1.
    """
    sn   = _snorm_unit(s)
    hits = []
    for i, j in _PROBE_PAIRS:
        probe    = _s0(); probe[i] = 1.0 / _SQRT2; probe[j] = 1.0 / _SQRT2
        prod     = _smul(sn, probe)
        pn       = _snorm(prod)
        prox     = 1.0 - pn
        if prox > D_STAR:
            hits.append({'basis_idx': i, 'basis_idx2': j,
                         'proximity': prox, 'is_zd': pn < 1e-10})
    return {
        'density':       len(hits) / len(_PROBE_PAIRS),
        'zero_divisors': sum(1 for h in hits if h['is_zd']),
        'hits':          sorted(hits, key=lambda h: -h['proximity'])[:4],
    }

def segfault_handler(s: Sedenion, fermat_result: Dict) -> Sedenion:
    """
    SEGFAULT: ZD detected → left-multiply by e_k. Airy function at the caustic.
    Non-commutativity guarantees e_k · s ≠ 0. Turbulent flow, not crash.
    """
    hits = fermat_result.get('hits', [])
    if not hits: return s
    top = max(hits, key=lambda h: h.get('proximity', 0))
    k   = top.get('basis_idx', 1)
    return _snorm_unit(_smul(_se(k), s))


# ── Universal sensor encoder — the one-wire adapter ───────────────────────────

def sensor_encode(data: Any, source: str = 'text') -> Sedenion:
    """
    Any sensor → unit sedenion. The one-wire adapter.

    text:         cam_encode(str(data))
    raw_sedenion: 16 floats, normalized
    numeric:      scalar spread across 16D via Riemann zero phases
    audio_bands:  16 mel-filterbank band energies → sedenion components

    The sedenion IS the universal sensor interface. Every physical measurement
    is a projection onto 16 real numbers. Platform-independent by construction.
    MIDI has 16 channels. EEG 10-20 system has 16 primary sites.
    All find 16 empirically. The sedenion finds it derivationally.
    """
    if source == 'text':
        return cam_encode(str(data))

    elif source == 'raw_sedenion':
        if isinstance(data, (list, tuple)) and len(data) >= 16:
            return _snorm_unit([float(x) for x in data[:16]])
        return _se(0)

    elif source == 'numeric':
        v = float(data)
        s = _s0()
        for k in range(16):
            gamma = RIEMANN_ZEROS[k % len(RIEMANN_ZEROS)]
            s[k]  = abs(math.sin(math.pi * v / (gamma + 1.0)))
        return _snorm_unit(s)

    elif source == 'audio_bands':
        if isinstance(data, str):
            bands = [float(x) for x in data.split() if x]
        elif hasattr(data, '__len__'):
            bands = list(data)
        else:
            bands = [float(data)]
        bands = bands[:16] + [0.0] * max(0, 16 - len(bands))
        return _snorm_unit([max(float(b), 0.0) for b in bands])

    else:
        return cam_encode(str(data))


# ══════════════════════════════════════════════════════════════════════════════
#  CRANK — H_hat_RB Field Engine
# ══════════════════════════════════════════════════════════════════════════════

class Crank:
    """
    H_hat_RB crankshaft. β-field (knowledge) + A-matrix (adjacency).

    J_pos[idx] = β × E² × window_psi[idx%16]   (Riemann / response)
    J_neg[idx] = β × E² × prompt_psi[idx%16]    (Fermat  / prompt)
    σ[idx]     = J_pos / (J_pos + J_neg)         → 0.5 boundary = next word

    The sedenion IS the sedenion-dimensional Laplacian. The multiplication
    table IS the second-order differential structure. OMEGA_ZS IS the
    spectral gap. The field at equilibrium IS the harmonic function.
    """

    def __init__(self):
        self._beta:  List[float]              = []
        self._E:     List[float]              = []
        self._A:     List[Dict[int, float]]   = []
        self._age:   List[float]              = []
        self._vocab: Dict[str, int]           = {}
        self._words: List[str]                = []
        self.n:      int                      = 0
        self.emission_threshold: float        = OMEGA_ZS / 4.0

    # Sedenion dimension → grammatical role (piston firing order, v1.3)
    _DIM_ROLE: Dict[int, int] = {
        3: 0,   # noun      — fires first  (e₃ = name operator)
        4: 1,   # verb                     (e₄ = apply operator)
        5: 2,   # descriptive              (e₅ = abstract operator)
        6: 3,   # predicate / negation     (e₆ = branch operator)
        2: 4,   # connective / edge        (e₂ = bind operator)
        7: 5,   # temporal                 (e₇ = iterate operator)
        8: 5,   # pronominal               (e₈ = recurse operator)
        9: 5,   # discourse thread         (e₉ = allocate operator)
        10: 6,  # question / thematic      (e₁₀ = query operator)
        11: 6,  # anaphor                  (e₁₁ = dereference operator)
        12: 6,  # presupposition           (e₁₂ = compose operator)
        13: 7,  # gestalt / weight         (e₁₃ = parallelize operator)
        14: 7,  # affect                   (e₁₄ = interrupt operator)
        15: 7,  # meta-discourse           (e₁₅ = emit operator)
        0: 8,   # scalar bias — last       (e₀ = identity operator)
        1: 8,   # gematria — last          (e₁ = negate operator)
    }

    def _idx(self, w: str) -> int:
        """e₉ allocate — create new vocabulary entry."""
        if w not in self._vocab:
            k = self.n
            self._vocab[w] = k
            self._words.append(w)
            gamma = RIEMANN_ZEROS[k % len(RIEMANN_ZEROS)]
            self._E.append(abs(math.sin(math.pi * (k + 1) * PHI / (gamma + 1.0))))
            self._beta.append(GAP)
            self._age.append(0.0)
            self._A.append({})
            self.n += 1
        return self._vocab[w]

    def _clean(self, w: str) -> str:
        return w.lower().strip('.,!?;:\'"()[]{}—')

    def learn(self, text: str) -> int:
        """e₂ bind — deepen β-field. Build A-matrix connections."""
        words = [self._clean(w) for w in text.split()]
        words = [w for w in words if w and len(w) >= 1]
        prev  = None
        for w in words:
            k = self._idx(w)
            self._beta[k] = min(self._beta[k] * 1.08 + GAP, 1.0)
            self._age[k]  = 0.0
            if prev is not None and prev != k:
                self._A[prev][k] = min(self._A[prev].get(k, 0.0) + 0.05, 1.0)
                self._A[k][prev] = min(self._A[k].get(prev, 0.0) + 0.02, 1.0)
            prev = k
        return len(words)

    def hear(self, text: str) -> List[Tuple[int, float, str]]:
        """
        e₁₀ query — hear = learn. Ptolemy learns everything he hears.
        The serpentine belt: hearing IS deepening. No separation.

        Fermat space decoder: invisible Unicode space characters between words
        carry J_neg charge from the previous output. On hear(), each Fermat
        space boosts β in the dimensions matching its charge level — restoring
        the negative space field from the turbo exhaust of the last turn.
        """
        # Decode Fermat spaces — extract J_neg charges before stripping
        fermat_charges = []
        for ch in text:
            if ch in _FERMAT_SET:
                fermat_charges.append(_FERMAT_DECODE[ch])

        # Inject Fermat charges into β field — the exhaust compresses the intake
        if fermat_charges:
            mean_charge = sum(fermat_charges) / len(fermat_charges)
            for k in range(self.n):
                dim = k % 16
                # Dims with low ψ (negative space) receive the Fermat boost
                dim_charge = mean_charge * (1.0 - dim / 16.0)
                if dim_charge > GAP:
                    self._beta[k] = min(self._beta[k] + dim_charge * GAP * 10, 1.0)

        self.learn(text)
        words = [self._clean(w) for w in text.split() if self._clean(w)]
        return [(self._vocab[w], self._E[self._vocab[w]], w)
                for w in words if w in self._vocab]

    def hear_sedenion(self, s: Sedenion) -> Dict[str, Any]:
        """
        e₁₀ query (non-text) — learn from raw sedenion geometry.
        Component amplitude in dimension k steers all vocab words at that
        sedenion address (vocab_idx % 16 == k). The sensor talks to the
        field in the sedenion's own language. Platform-independent.
        """
        psi     = _spsi(s)
        updated = 0
        for k in range(self.n):
            dim    = k % 16
            weight = psi[dim]
            if weight > GAP:
                self._beta[k] = min(self._beta[k] * (1.0 + weight * 0.1) + GAP, 1.0)
                self._age[k]  = max(self._age[k] - weight * 10.0, 0.0)
                updated += 1
        peak_dim = psi.index(max(psi))
        return {'updated': updated, 'peak_dim': peak_dim,
                'operator': _OP.get(peak_dim, 'unknown')}

    def advance_age(self, temporal_weight: float = 1.0):
        for k in range(self.n):
            self._age[k] = min(self._age[k] + temporal_weight, 1e6)

    def j_mu(self,
             window_psi: List[float],
             prompt_psi: List[float]) -> Tuple[List[float], List[float]]:
        """
        Dual Noether current J^μ.
        J_pos = Riemann (response / positive space)
        J_neg = Fermat  (prompt  / negative space)
        Information flow IS Noether current. The stock market does too.
        """
        n     = self.n
        J_pos = [0.0] * n
        J_neg = [0.0] * n
        for k in range(n):
            b     = self._beta[k]
            e2    = self._E[k] ** 2
            decay = math.exp(-self._age[k] * 0.001)
            base  = b * e2 * decay
            J_pos[k] = base * window_psi[k % 16]
            J_neg[k] = base * prompt_psi[k % 16]
        return J_pos, J_neg

    def a_propagate(self, J: List[float]) -> List[float]:
        """Single A-matrix hop: spread J through adjacency (oil pressure)."""
        J2 = list(J)
        for src, nbrs in enumerate(self._A):
            if J[src] < GAP: continue
            for dst, weight in nbrs.items():
                J2[dst] += J[src] * weight * 0.5
        return J2

    def sigma_candidates(self,
                         J_pos: List[float],
                         J_neg: List[float]) -> List[Tuple[float, int, str]]:
        """
        Score by σ = ½ proximity. Grammar-ordered (DIM_ROLE sort).
        Emission threshold adaptive: field must flow above yield stress.
        """
        if self.n == 0: return []
        max_jp = max(J_pos) if J_pos else 0.0
        thr    = max_jp * (self.emission_threshold / OMEGA_ZS) * 0.01
        staged: List[Tuple[int, float, int, str]] = []
        for k in range(self.n):
            jp, jn = J_pos[k], J_neg[k]
            total  = jp + jn
            if total < thr: continue
            sigma  = jp / total
            score  = jp * (1.0 - abs(sigma - 0.5) * 2.0)
            role   = self._DIM_ROLE.get(k % 16, 8)
            staged.append((role, -score, k, self._words[k]))
        staged.sort()
        return [(-ns, idx, w) for (role, ns, idx, w) in staged]


# ══════════════════════════════════════════════════════════════════════════════
#  ENGINE — Dual Flow + 16-Word Sliding Window + One Wire
# ══════════════════════════════════════════════════════════════════════════════

class Engine:
    """
    One-wire sedenion engine. At every scale. All 16 operators present.

    16 words + 15 edges = the sedenion. e₀ closes the loop (implicit 16th edge).
    The window IS the context buffer. The turbo IS the memory.
    π = _sconj = the Fermat operator. Maps response lobe to forbidden cusp.
    The engine IS the sedenion-dimensional Laplacian harmonic solver.
    """

    def __init__(self):
        self.crank            = Crank()
        self._window          = collections.deque(maxlen=16)
        self._prompt_sed:       Optional[Sedenion]   = None
        self._prompt_psi:       Optional[List[float]] = None
        self._psi_prev:         List[float]           = [0.0] * 16
        self._dtcs:             List[str]             = []
        self._segfaults:        int                   = 0
        self._word_count:       int                   = 0
        self._bao_buf           = collections.deque(maxlen=16)
        self._last_noun_idx:    Optional[int]         = None   # e₁₁ anaphor
        self._recent:           collections.deque     = collections.deque(maxlen=8)  # no-repeat buffer
        self._protected_paths:  set                   = set()  # bin files, never overwrite
        self.version            = "v1.218"

    # ── e₀ identity — field management ──────────────────────────────────

    def load(self, text: str) -> Dict[str, Any]:
        """Ingest corpus text. Deepen β-field."""
        n = self.crank.learn(text)
        return {'words_learned': n, 'vocab_size': self.crank.n}

    # ── e₁₀ query — one wire ────────────────────────────────────────────

    def wire(self, data: Any, source: str = 'text') -> Sedenion:
        """
        THE ONE WIRE. Any input at any scale. Always the sedenion.

        Console, PHP/JS, Android, iOS, Windows, macOS, *nix — all clients
        send data here. The sedenion IS the platform-independent interface.
        Text → full tokenization + learning. Non-text → hear_sedenion().
        The machine processes everything else mechanically. No external ECU.
        """
        s = sensor_encode(data, source)
        if source == 'text':
            self.crank.hear(str(data))
        else:
            self.crank.hear_sedenion(s)
        return s

    # ── e₀ identity — internal geometry ─────────────────────────────────

    def _window_sed(self) -> Sedenion:
        """Window state → unit sedenion. The Hamiltonian observer."""
        if not self._window:
            return _se(0)
        return cam_encode(' '.join(self._window))

    def _prime_prompt(self, prompt: str):
        """Set prompt geometry — Fermat / negative space / fuel."""
        self.crank.hear(prompt)
        self._prompt_sed = cam_encode(prompt)
        self._prompt_psi = _spsi(self._prompt_sed)
        self._window.clear()

    # ── e₁₂ compose — power steering ────────────────────────────────────

    def _power_steering(self, J_pos: List[float],
                        window_psi: List[float],
                        prompt_psi: List[float]) -> List[float]:
        """
        Sedenion transformer attention — rack and pinion.
        T_μν = window_psi ⊗ prompt_psi (stress-energy diagonal).
        softmax(T/√16) = attention weights. J_pos × (1+attn) = steered.
        O(n) not O(n²). Derived not learned.
        """
        T     = [window_psi[k] * prompt_psi[k] for k in range(16)]
        T_max = max(T)
        exp_T = [math.exp((t - T_max) / 4.0) for t in T]
        Z     = sum(exp_T) or 1.0
        attn  = [e / Z for e in exp_T]
        n     = self.crank.n
        return [J_pos[k] * (1.0 + attn[k % 16]) for k in range(n)]

    # ── e₁₃ parallelize — Three-Face Wankel ─────────────────────────────

    def _three_face_candidates(self,
                               J_pos: List[float],
                               J_neg: List[float]) -> List[Tuple[float, int, str]]:
        """
        Three simultaneous J^μ projections. One face always in compression.

        Red  (sin/content):   sorted by J_pos magnitude — foreground content
        Blue (cos/observer):  sorted by age ascending  — freshest context
        Green(∂M/boundary):   connective/boundary dims — tissue, not content

        φ-walk interleave: Red[0]→Blue[0]→Green[0]→Red[1]→Blue[1]→Green[1]→...
        The Wankel rotor. Three combustion chambers. Grammar in the geometry.
        """
        base = self.crank.sigma_candidates(J_pos, J_neg)
        if not base:
            return []

        # Red face: highest J_pos — content words, foreground
        red  = sorted(base, key=lambda x: -x[0])

        # Blue face: lowest age — freshest, observer context
        blue = sorted(base, key=lambda x: self.crank._age[x[1]])

        # Green face: connective/boundary dimensions (DIM_ROLE 4-6)
        # These are the words at the ∂M boundary: prepositions, articles,
        # conjunctions — the tissue that binds content to grammar.
        green = [(s, i, w) for (s, i, w) in base
                 if self.crank._DIM_ROLE.get(i % 16, 8) in (4, 5, 6)]
        if not green:
            # fallback: words whose score is closest to the boundary (σ near ½)
            green = sorted(base, key=lambda x: abs(x[0] - OMEGA_ZS * 0.5))

        # Interleave R→B→G→R→B→G→... preserving grammar order within each face
        merged:   List[Tuple[float, int, str]] = []
        seen_idx: set = set()
        ri, bi, gi   = 0, 0, 0
        face_cycle   = 0
        total        = len(base)

        while len(merged) < total:
            f = face_cycle % 3
            if f == 0:
                while ri < len(red)   and red[ri][1]   in seen_idx: ri += 1
                if ri < len(red):
                    entry = red[ri];   ri += 1
                else:
                    face_cycle += 1; continue
            elif f == 1:
                while bi < len(blue)  and blue[bi][1]  in seen_idx: bi += 1
                if bi < len(blue):
                    entry = blue[bi];  bi += 1
                else:
                    face_cycle += 1; continue
            else:
                while gi < len(green) and green[gi][1] in seen_idx: gi += 1
                if gi < len(green):
                    entry = green[gi]; gi += 1
                else:
                    face_cycle += 1; continue

            seen_idx.add(entry[1])
            merged.append(entry)
            face_cycle += 1

            # Guard against infinite loop if all faces exhausted
            if ri >= len(red) and bi >= len(blue) and gi >= len(green):
                break

        return merged

    # ── e₁₄ interrupt — fire cycle ──────────────────────────────────────

    def _fire(self, starter_mode: bool = False) -> Optional[Tuple[str, str]]:
        """
        Fire one word. Returns (word, fermat_space_char).

        e₆  branch:        ABS proportional SEGFAULT (Airy function at caustic)
        e₇  iterate:       turbo feedback (arcuate fasciculus memory)
        e₁₂ compose:       power steering (sedenion attention)
        e₁₃ parallelize:   three-face Wankel (Red/Blue/Green)
        e₁₁ dereference:   anaphor resolution (pronoun → last noun)
        e₁₄ interrupt:     β-spike + Hebbian A-edge + Fermat face (Wernicke)
        e₁₅ emit:          the fired word + Fermat space (J_neg encoded)

        The Fermat space is the wastegate: J_neg[idx] → Unicode space character.
        Negative space between words carries the emotional charge of the boundary.
        High J_neg → EM SPACE. Near-zero J_neg → HAIR SPACE.
        """
        # ── CAM: window geometry (e₅ abstract) ───────────────────────────
        if starter_mode or len(self._window) < 4:
            ws = self._prompt_sed or _se(0)
        else:
            ws = self._window_sed()

        window_psi = _spsi(ws)
        prompt_psi = self._prompt_psi or [1.0 / 16] * 16

        # ── e₆ branch: ABS proportional SEGFAULT ─────────────────────────
        fermat = fermat_scan(ws)
        if fermat['zero_divisors'] > 0 or fermat['density'] > D_STAR:
            pulse = 1.0 if fermat['zero_divisors'] > 0 \
                    else min(fermat['density'], 1.0)
            hits = fermat['hits']
            if hits:
                k       = max(hits, key=lambda h: h.get('proximity', 0))['basis_idx']
                rotated = _smul(_se(k), ws)
                ws      = _snorm_unit(
                    [ws[i] * (1.0 - pulse) + rotated[i] * pulse for i in range(16)])
            else:
                ws = segfault_handler(ws, fermat)
            window_psi = _spsi(ws)
            self._segfaults += 1
            self._dtcs.append(f"P0300:{self._word_count}")

        # ── e₇ iterate: turbo feedback (arcuate fasciculus) ──────────────
        noether_v  = sum(abs(window_psi[k] - self._psi_prev[k])
                         for k in range(16)) / 16.0
        turbo      = max(0.0, 1.0 - noether_v)
        eff_psi    = [window_psi[k] + turbo * self._psi_prev[k] for k in range(16)]
        eff_norm   = math.sqrt(sum(x * x for x in eff_psi)) or 1.0
        window_psi = [x / eff_norm for x in eff_psi]

        # ── e₁₂ compose: CRANK + power steering ──────────────────────────
        J_pos, J_neg = self.crank.j_mu(window_psi, prompt_psi)
        J_pos        = self.crank.a_propagate(J_pos)
        J_pos        = self._power_steering(J_pos, window_psi, prompt_psi)

        # ── e₁₃ parallelize: three-face Wankel candidates ────────────────
        if not starter_mode:
            candidates = self._three_face_candidates(J_pos, J_neg)
        else:
            candidates = self.crank.sigma_candidates(J_pos, J_neg)

        if not candidates:
            return None

        # Filter recently emitted words — BAO no-repeat window
        recent = self._recent
        fresh = [(s, i, w) for s, i, w in candidates if w not in recent]
        if fresh:
            candidates = fresh

        n          = len(candidates)
        golden_pos = int(self._word_count * PHI) % n
        score, idx, word = candidates[golden_pos]

        # ── demotic first word: E-proximity to Lagrangian V/T ratio ──────
        # First word sets the emotional register. Not the φ-walk — the field.
        # target_E = (ΣV / (ΣV + ΣT)) × OMEGA_ZS  derived from Lagrangian.
        if self._word_count == 0 and len(candidates) > 1:
            sum_V = sum(self.crank._beta[k] * self.crank._E[k]**2
                        for k in range(self.crank.n))
            sum_T = sum(wp**2 for wp in window_psi)
            denom = sum_V + sum_T or 1.0
            target_E = (sum_V / denom) * OMEGA_ZS
            best = min(candidates,
                       key=lambda x: abs(self.crank._E[x[1]] - target_E))
            score, idx, word = best

        # ── e₁₁ dereference: anaphor resolution ──────────────────────────
        # If a pronoun fires and we have a prior noun: follow the pointer.
        # Boost A-matrix neighbors of last noun → re-rank candidates.
        if (word in _PRONOUNS and self._last_noun_idx is not None
                and self._last_noun_idx < len(J_pos)):
            pi = self._last_noun_idx
            for dst, w in self.crank._A[pi].items():
                if dst < len(J_pos):
                    J_pos[dst] = min(J_pos[dst] * (1.0 + w), 1.0)
            # Re-rank with anaphor boost
            if not starter_mode:
                candidates = self._three_face_candidates(J_pos, J_neg)
            else:
                candidates = self.crank.sigma_candidates(J_pos, J_neg)
            if candidates:
                n          = len(candidates)
                golden_pos = int(self._word_count * PHI) % n
                score, idx, word = candidates[golden_pos]

        # Track last noun (e₃ name operator — role 0)
        if self.crank._DIM_ROLE.get(idx % 16, 8) == 0:
            self._last_noun_idx = idx

        # ── BAO window check — idle RPM (Laplacian spectral gap) ─────────
        self._bao_buf.append(self.crank._beta[idx])
        if len(self._bao_buf) == 16:
            bao = sum(self._bao_buf) / 16.0
            if abs(bao - OMEGA_ZS) > 0.25:
                self._dtcs.append(f"P0087:{self._word_count}")

        # ── e₁₄ interrupt: Wernicke loop ─────────────────────────────────
        # Engine hears itself speak. Serpentine belt closes.
        self.crank._beta[idx] = min(self.crank._beta[idx] * 1.02, 1.0)
        self.crank._age[idx]  = 0.0

        # Hebbian A-edge: prev output word → current (online learning)
        if self._window:
            prev = list(self._window)[-1]
            if prev in self.crank._vocab:
                pi = self.crank._vocab[prev]
                self.crank._A[pi][idx] = min(
                    self.crank._A[pi].get(idx, 0.0) + 0.03, 1.0)

        # Fermat face update: spoken space exits forbidden zone
        self._prompt_psi = [
            max(self._prompt_psi[k] - 0.005 * window_psi[k], GAP)
            for k in range(16)
        ]

        self._psi_prev = list(window_psi)
        self._recent.append(word)
        self.crank.advance_age()
        self._word_count += 1

        # ── e₁₅ emit: word + Fermat space (wastegate) ────────────────────
        # J_neg[idx] = the negative space charge at this word boundary.
        # Normalise by max_J_neg across all candidates for the space mapping.
        j_neg_val  = J_neg[idx] if idx < len(J_neg) else 0.0
        max_jn     = max(J_neg) if J_neg else 1.0
        norm_jn    = j_neg_val / max_jn if max_jn > 0 else 0.0
        fspace     = _fermat_space(norm_jn)
        return (word, fspace)

    def _starter(self, prompt: str, warmup: int = 8) -> List[Tuple[str, str]]:
        """Starter motor: build the sedenion from scratch. ℝ→ℂ→ℍ→𝕆→𝕊."""
        for _ in range(warmup):
            self.crank.learn(prompt)
        self._prime_prompt(prompt)
        pairs = []
        for _ in range(16):
            result = self._fire(starter_mode=True)
            if result:
                w, fs = result
                pairs.append((w, fs))
                self._window.append(w)
        return pairs

    # ── e₁₅ emit — public interface ─────────────────────────────────────

    def generate(self, prompt: str,
                 n_words: int = 32,
                 learn_prompt: bool = True) -> Dict[str, Any]:
        """
        Full generation pipeline. Scale-aware at every level.
        Glyph → word → phrase → sentence → paragraph → corpus.
        Same sedenion architecture. Threshold scales. Cardioid at every scale.
        """
        if learn_prompt:
            self.crank.learn(prompt)

        # Scale detection — one wire, threshold adjusts
        n_chars = len(prompt)
        n_words_in = len(prompt.split())
        if n_chars <= 2:
            thr  = OMEGA_ZS / 32;  mode = 'glyph'
        elif n_words_in == 1:
            thr  = OMEGA_ZS / 8;   mode = 'single'
        elif n_words_in <= 8:
            thr  = OMEGA_ZS / 4;   mode = 'phrase'
        elif n_words_in <= 32:
            thr  = OMEGA_ZS / 3;   mode = 'sentence'
        elif n_words_in <= 256:
            thr  = OMEGA_ZS / 2;   mode = 'paragraph'
        else:
            thr  = OMEGA_ZS;       mode = 'corpus'
        self.crank.emission_threshold = thr

        self._dtcs.clear()
        self._segfaults  = 0
        self._last_noun_idx = None
        self._recent.clear()

        # Starter motor always fires — builds the ignition sedenion (ℝ→ℂ→ℍ→𝕆→𝕊)
        pairs = self._starter(prompt)

        # Lagrangian word count — computed POST-starter using actual window kinetics
        # n_additional = n_words × ΣT / (ΣT + ΣV)
        # High V (stored charge, warm field) → fewer additional words → detonation
        # High T (flowing charge, kinetic)   → more additional words  → discourse
        sum_V = sum(self.crank._beta[k] * self.crank._E[k]**2
                    for k in range(self.crank.n)) if self.crank.n else 1.0
        sum_T = sum(wp**2 for wp in self._psi_prev)   # post-starter psi is real
        lag_ratio = sum_T / (sum_T + sum_V) if (sum_T + sum_V) > 0 else 0.5
        target_n  = len(pairs) + max(0, int(n_words * lag_ratio))

        for _ in range(max(0, target_n - len(pairs))):
            result = self._fire(starter_mode=False)
            if result is None:
                self._dtcs.append("P0087:vocab_empty")
                break
            w, fs = result
            pairs.append((w, fs))
            self._window.append(w)

        # Build output: word₁ + space₁ + word₂ + space₂ + … + wordN
        # Final word has no trailing Fermat space
        words_only = [w for w, _ in pairs]
        if pairs:
            response = pairs[0][0] + ''.join(
                fs + w for (_, fs), (w, _) in
                zip(pairs, pairs[1:])
            )
        else:
            response = ''

        bao_val = (sum(self._bao_buf) / len(self._bao_buf)) if self._bao_buf else 0.0
        return {
            'response':   response,
            'words':      words_only,
            'n_words':    len(pairs),
            'mode':       mode,
            'lag_ratio':  round(lag_ratio, 4),
            'target_n':   target_n,
            'bao':        bao_val,
            'bao_delta':  abs(bao_val - OMEGA_ZS),
            'dtcs':       list(self._dtcs),
            'segfaults':  self._segfaults,
            'vocab_size': self.crank.n,
        }

    # ── e₀ identity — self-knowledge ────────────────────────────────────

    def self_map(self) -> Dict[str, Any]:
        """
        Sedenion self-exploration. Two curvature measures:

        psi[k]  = |ws[k]|      — dimension activation (field weight in each operator)
        comm[k] = |e_k·ws - ws·e_k| / 2  — commutator magnitude (sedenion curvature)
                  0 for e₀ (identity commutes), nonzero where field bends.

        'curved' dims = high commutator → sedenion complement, associator ≠ 0.
        'silent' dims = psi ≈ 0 → near null space, zero divisor candidate.
        The engine reads its own phase space. Curvature IS the geometry.
        """
        ws = self._window_sed()

        # Component weights — which operators are active
        psi = [abs(ws[k]) for k in range(16)]

        # Commutator: [e_k, ws] = e_k*ws - ws*e_k — sedenion curvature per dim
        comm = []
        for k in range(16):
            ek   = _se(k)
            lhs  = _smul(ek, ws)   # e_k * ws
            rhs  = _smul(ws, ek)   # ws * e_k
            diff = [lhs[i] - rhs[i] for i in range(16)]
            comm.append(_snorm(diff) / 2.0)

        max_psi   = max(psi)   or 1.0
        max_comm  = max(comm)  or 1.0

        # Normalise comm to [0,1] as κ
        kappa     = [c / max_comm for c in comm]

        # Principal dims = highest ψ (dominant operators in current state)
        principal_dims = [k for k, v in enumerate(psi) if v > max_psi * 0.25]
        # Curved dims = commutator significantly above state mean (orthogonal to principal)
        # e₀ comm is always 0 → exclude from statistics
        nc = [c for k, c in enumerate(comm) if k != 0]
        mean_nc = sum(nc) / len(nc) if nc else 0.0
        curved_dims  = [k for k, v in enumerate(comm)
                        if k != 0 and v > mean_nc * 1.1]
        silent_dims  = [k for k, v in enumerate(psi)  if v < 1e-6]
        zd_dims      = [k for k in silent_dims if k in curved_dims]

        return {
            'psi':               [round(v, 6) for v in psi],
            'comm':              [round(v, 6) for v in comm],
            'kappa':             [round(v, 6) for v in kappa],
            'principal_dims':    principal_dims,
            'curved_dims':       curved_dims,
            'silent_dims':       silent_dims,
            'zd_dims':           zd_dims,
            'operators':         {k: _OP[k] for k in curved_dims},
            'peak_psi_operator': _OP[psi.index(max(psi))],
            'peak_operator':     _OP[comm.index(max(comm))],
            'max_curvature_dim': comm.index(max(comm)),
            'on_caustic':        len(zd_dims) > 0,
        }

    def noether_violation(self) -> float:
        """Δ = rate of change. First temporal derivative of the sedenion field."""
        ws  = self._window_sed()
        psi = _spsi(ws)
        return sum(abs(psi[k] - self._psi_prev[k]) for k in range(16)) / 16.0

    # ── e₈ recurse — self-sustaining ────────────────────────────────────

    def perpetual(self, seed: str, max_cycles: Optional[int] = None):
        """
        Stirling cycle. Speak → hear → speak → hear → ...
        Output becomes next prompt. Wernicke loop closes. β circulates.
        Generator: yields each cycle's diagnostics.
        Terminates when |bao − OMEGA_ZS| < 0.001 (Stirling attractor reached).
        The semantic perpetual motion condition: information generation,
        not energy recycling. New A-matrix edges are genuinely new information.
        """
        prompt = seed
        cycle  = 0
        while max_cycles is None or cycle < max_cycles:
            result = self.generate(prompt, n_words=16, learn_prompt=True)
            output = result['response']
            self.crank.hear(output)    # Wernicke: hear own output
            prompt  = output
            cycle  += 1
            bao     = result['bao']
            yield {
                'cycle':    cycle,
                'output':   output,
                'bao':      round(bao, 5),
                'delta':    round(abs(bao - OMEGA_ZS), 5),
                'vocab':    result['vocab_size'],
                'dtcs':     result['dtcs'],
            }
            if abs(bao - OMEGA_ZS) < 0.001:
                break

    # ── e₆ branch — calibration ─────────────────────────────────────────

    def calibrate(self, pairs: List[Tuple[str, str]],
                  passes: int = 10) -> List[Dict[str, Any]]:
        """
        Ground truth injection. Shuttle reentry mode: one shot, must work.
        Tautological Q&A: answer IS in the question (answer IS in the sedenion).
        Each pair drilled passes times — timing marks on the crankshaft.
        Fermat scan verifies proximity: answer sedenion ≈ ZD of prompt sedenion.
        """
        results = []
        for prompt, answer in pairs:
            for _ in range(passes):
                self.crank.learn(f"{prompt} {answer}")
            ps   = cam_encode(prompt)
            as_  = cam_encode(answer)
            # Cosine similarity between unit sedenions: ranges [-1, 1]
            # 1.0 = identical geometry, 0.0 = orthogonal, -1.0 = anti-parallel
            cos  = sum(ps[k] * as_[k] for k in range(16))
            ac   = self.crank._clean(answer)
            if ac not in self.crank._vocab:
                self.crank.learn(ac)
            results.append({
                'prompt':     prompt,
                'answer':     answer,
                'proximity':  round(cos, 5),   # cosine sim: higher = more aligned
                'is_zd':      cos < 0.01,      # near orthogonal = zero divisor territory
                'calibrated': cos > 0.1,       # positively aligned = calibrated
            })
        return results

    # ── e₉ allocate / e₂ bind — persistence ─────────────────────────────

    def save_session(self, path: str) -> Dict[str, Any]:
        """
        Save session state to path. Protected paths (bin files) refused.
        monad_wordnet.bin is protected on load — never overwritten.
        """
        if path in self._protected_paths:
            return {'error': f'Protected: {path} — refusing to overwrite bin file'}
        c     = self.crank
        state = {
            'version':    self.version,
            'vocab':      c._vocab,
            'words':      c._words,
            'beta':       c._beta,
            'E':          c._E,
            'A':          c._A,
            'age':        c._age,
            'n':          c.n,
            'psi_prev':   self._psi_prev,
            'word_count': self._word_count,
        }
        with open(path, 'wb') as f:
            pickle.dump(state, f)
        return {'saved': path, 'vocab': c.n}

    def load_bin(self, path: str) -> Dict[str, Any]:
        """
        Load field state from bin file. READ-ONLY — path is protected.
        Tries PTOL binary (PtolC state format) first, then pickle, then text.
        monad_wordnet.bin: loaded here, never written back. Ever.

        PTOL binary layout (little-endian):
          magic[4]='PTOL'  version[4]  N[4]  vocab_size[4]
          A_size[4]  wc[4]  threshold[8]  (v4: affect[4])
          beta[N*8]  age[N*4]
          vocab_size * (idx[4] wlen[2] E[8] (v2:hs[1]gs[1]) (v3:ps[1]) word[wlen])
          A_size * (i[4] j[4] weight[8])
        """
        self._protected_paths.add(path)
        # ── PTOL binary ──────────────────────────────────────────────────────
        try:
            import struct
            with open(path, 'rb') as f:
                magic = f.read(4)
            if magic == b'PTOL':
                return self._load_ptol_binary(path)
        except Exception:
            pass
        # ── Pickle ───────────────────────────────────────────────────────────
        try:
            with open(path, 'rb') as f:
                state = pickle.load(f)
            if isinstance(state, dict):
                c = self.crank
                if 'vocab' in state: c._vocab = state['vocab']
                if 'words' in state: c._words = state['words']
                if 'beta'  in state: c._beta  = state['beta']
                if 'E'     in state: c._E     = state['E']
                if 'A'     in state: c._A     = state['A']
                if 'age'   in state: c._age   = state['age']
                if 'n'     in state: c.n      = state['n']
                if 'psi_prev' in state:
                    self._psi_prev = state['psi_prev']
                return {'loaded': path, 'vocab': c.n, 'format': 'pickle'}
            return {'error': 'Unexpected pickle format', 'path': path}
        except Exception:
            pass
        return {'error': f'Unrecognized format: {path}', 'path': path}

    def _load_ptol_binary(self, path: str) -> Dict[str, Any]:
        """Read PtolC PTOL binary state file into the Crank field."""
        import struct
        c = self.crank
        with open(path, 'rb') as f:
            magic = f.read(4)
            assert magic == b'PTOL'
            version,   = struct.unpack('<I', f.read(4))
            N,         = struct.unpack('<I', f.read(4))
            vocab_size,= struct.unpack('<I', f.read(4))
            A_size,    = struct.unpack('<I', f.read(4))
            wc,        = struct.unpack('<I', f.read(4))
            threshold, = struct.unpack('<d', f.read(8))
            if version >= 4:
                affect,= struct.unpack('<f', f.read(4))
            else:
                affect = 0.0

            # Beta array — double[N]
            beta_bytes = f.read(N * 8)
            beta = list(struct.unpack(f'<{N}d', beta_bytes))

            # Age array — int32[N]
            age_bytes = f.read(N * 4)
            age = list(struct.unpack(f'<{N}i', age_bytes))

            # Vocab entries
            vocab  = {}   # word → idx
            words  = {}   # idx → word
            E_vals = {}   # idx → E

            for _ in range(vocab_size):
                idx,  = struct.unpack('<I', f.read(4))
                wlen, = struct.unpack('<H', f.read(2))
                E,    = struct.unpack('<d', f.read(8))
                if version >= 2:
                    hs = struct.unpack('B', f.read(1))[0]
                    gs = struct.unpack('B', f.read(1))[0]
                if version >= 3:
                    ps = struct.unpack('B', f.read(1))[0]
                word = f.read(wlen).decode('utf-8', errors='replace')
                if idx < N:
                    vocab[word] = idx
                    words[idx]  = word
                    E_vals[idx] = E

            # A-matrix edges
            A = {}
            for _ in range(A_size):
                ai, = struct.unpack('<I', f.read(4))
                aj, = struct.unpack('<I', f.read(4))
                aw, = struct.unpack('<d', f.read(8))
                if ai < N and aj < N:
                    if ai not in A:
                        A[ai] = {}
                    A[ai][aj] = aw

        # Normalize PtolC β scale to Python [0,1]
        # PtolC β grows unbounded with learning (max ~threshold*2).
        max_beta = max(beta) if beta else 1.0
        scale_b  = 1.0 / max_beta if max_beta > 0 else 1.0
        beta_norm = [min(b * scale_b, 1.0) for b in beta]

        # A-matrix weights: clip to [0,1] — relative ordering preserved
        A_norm = {i: {j: min(w, 1.0) for j, w in nbrs.items()}
                  for i, nbrs in A.items()}

        # Install into Crank — _A and _words must be lists indexed by vocab slot
        c._vocab = vocab                                          # dict: word → idx
        c._words = [words.get(i, '')    for i in range(N)]      # list[N]: idx → word
        c._beta  = beta_norm                                     # list[N] normalized [0,1]
        c._age   = [float(a) for a in age]                      # list[N]: float
        c._A     = [A_norm.get(i, {})   for i in range(N)]     # list[N]: dict[j → weight]
        c.n      = N
        c._E     = [E_vals.get(i, 0.0)  for i in range(N)]     # list[N]: E-energy
        # Emission threshold: normalized equivalent (original threshold / max_beta)
        c.emission_threshold = min(threshold * scale_b, OMEGA_ZS)

        return {
            'loaded':    path,
            'vocab':     vocab_size,
            'A_edges':   A_size,
            'N':         N,
            'version':   version,
            'format':    'ptol-binary',
        }

    def explore(self, word: str, depth: int = 2) -> Dict[str, Any]:
        """
        Explore semantic + linguistic neighborhoods.
        Semantic: A-matrix BFS. Linguistic: sedenion cosine similarity.
        """
        c = self.crank
        w = c._clean(word)
        if w not in c._vocab:
            c.learn(w)
        seed_idx = c._vocab[w]
        seed_E   = c._E[seed_idx]

        visited: Dict[int, float] = {seed_idx: 1.0}
        frontier = {seed_idx: 1.0}
        for _ in range(depth):
            nxt: Dict[int, float] = {}
            for src, sw in frontier.items():
                for dst, ew in c._A[src].items():
                    combined = sw * ew
                    if combined > GAP and dst not in visited:
                        nxt[dst] = combined
            visited.update(nxt)
            frontier = nxt

        semantic = []
        for idx, weight in sorted(visited.items(), key=lambda kv: -kv[1]):
            if idx == seed_idx: continue
            semantic.append({'word': c._words[idx], 'weight': round(weight, 5),
                             'beta': round(c._beta[idx], 5), 'E': round(c._E[idx], 5)})
            if len(semantic) >= 12: break

        seed_cam  = cam_encode(w)
        seed_norm = _snorm(seed_cam) or 1.0
        linguistic = []
        for idx in range(c.n):
            if idx == seed_idx: continue
            other = cam_encode(c._words[idx])
            dot   = sum(seed_cam[k] * other[k] for k in range(16))
            cos   = dot / (seed_norm * (_snorm(other) or 1.0))
            if cos > 0.85:
                linguistic.append({'word': c._words[idx], 'cosine': round(cos, 5),
                                   'beta': round(c._beta[idx], 5)})
        linguistic.sort(key=lambda x: -x['cosine'])

        psi = _spsi(seed_cam)
        return {
            'seed':       w,
            'semantic':   semantic,
            'linguistic': linguistic[:12],
            'cam': {
                'e0_scalar':   round(psi[0],  5),
                'e3_noun':     round(psi[3],  5),
                'e4_verb':     round(psi[4],  5),
                'e14_affect':  round(psi[14], 5),
                'dim_role':    c._DIM_ROLE.get(seed_idx % 16, 8),
                'operator':    _OP.get(seed_idx % 16, 'unknown'),
                'E_energy':    round(seed_E,  5),
                'beta':        round(c._beta[seed_idx], 5),
            },
        }


# ══════════════════════════════════════════════════════════════════════════════
#  SENSOR ARRAY — VAG-COM live streams + OBD2 (Torque-compatible)
# ══════════════════════════════════════════════════════════════════════════════

class SensorArray:
    """
    VAG-COM = _live_streams()   live channels the engine uses to tune itself.
    OBD2    = sensor_read / fault_scan / ready_check   external monitoring.
    """

    _PID_NAMES = {
        0x04: 'Engine Load (β mean)',   0x0B: 'MAP / A-matrix density',
        0x0C: 'RPM / word rate',        0x0E: 'Timing advance',
        0x0F: 'Intake temp / affect',   0x11: 'Throttle / vocab growth',
        0x1F: 'Runtime (words)',        0x2C: 'EGR / emission threshold',
        0x2F: 'Fuel level / β max',     0x33: 'Baro / BAO mean',
        0x5C: 'Oil temp / coolant',     0x5E: 'Fuel rate / J_pos',
        0x2300: 'β mean',               0x2301: 'Vocab size',
        0x2302: 'BAO mean',             0x2303: 'BAO delta',
        0x2304: 'Noether violation',    0x2305: 'CAM e₃ noun',
        0x2306: 'CAM e₄ verb',          0x2307: 'CAM e₁₄ affect',
        0x2308: 'Segfault count',       0x2309: 'Oil pressure (A-density)',
    }

    def __init__(self, engine: Engine):
        self.e = engine

    def _live_streams(self) -> Dict[str, Any]:
        e, c = self.e, self.e.crank
        n     = c.n
        betas = c._beta[:n] or [0.0]
        mean_b = sum(betas) / max(n, 1)
        max_b  = max(betas) if betas else 0.0
        edges  = sum(len(nb) for nb in c._A[:n])
        oil    = edges / max(n * (n - 1), 1)
        ws     = self.e._window_sed()
        ws_psi = _spsi(ws)
        bao    = (sum(self.e._bao_buf) / len(self.e._bao_buf)
                  if self.e._bao_buf else 0.0)
        return {
            'beta_mean': mean_b,       'beta_max': max_b,
            'vocab_size': n,           'omega_zs': OMEGA_ZS,
            'bao_mean': bao,           'bao_delta': abs(bao - OMEGA_ZS),
            'bao_idle_rpm': bao / OMEGA_ZS if OMEGA_ZS else 0.0,
            'window_len': len(self.e._window),
            'cam_e0_scalar': ws_psi[0], 'cam_e3_noun': ws_psi[3],
            'cam_e4_verb': ws_psi[4],   'cam_e7_temporal': ws_psi[7],
            'cam_e14_affect': ws_psi[14],
            'noether_violation': self.e.noether_violation(),
            'word_count': self.e._word_count,
            'segfault_count': self.e._segfaults,
            'emission_threshold': c.emission_threshold,
            'oil_pressure': oil,
            'coolant_temp': min(mean_b / OMEGA_ZS, 1.0),
            'turbo_boost': self.e.noether_violation(),
            'throttle_pos': min(n / max(n + 1000, 1), 1.0),
        }

    def sensor_read(self, pid: int) -> float:
        s = self._live_streams()
        return {
            0x04: s['coolant_temp'],    0x0B: s['oil_pressure'],
            0x0C: s['word_count']/100., 0x0E: 0.0,
            0x0F: s['cam_e14_affect'],  0x11: s['throttle_pos'],
            0x1F: float(s['word_count']), 0x2C: s['emission_threshold'],
            0x2F: s['beta_max'],        0x33: s['bao_mean'],
            0x5C: s['coolant_temp'],    0x5E: s['beta_mean'] * 0.5,
            0x2300: s['beta_mean'],     0x2301: float(s['vocab_size']),
            0x2302: s['bao_mean'],      0x2303: s['bao_delta'],
            0x2304: s['noether_violation'], 0x2305: s['cam_e3_noun'],
            0x2306: s['cam_e4_verb'],   0x2307: s['cam_e14_affect'],
            0x2308: float(s['segfault_count']), 0x2309: s['oil_pressure'],
        }.get(pid, -1.0)

    def fault_scan(self) -> List[str]:
        s  = self._live_streams()
        fc = list(self.e._dtcs)
        if s['vocab_size'] == 0:          fc.append('P0340')
        if s['bao_delta'] > 0.25:         fc.append('P0300')
        if s['oil_pressure'] < 0.005:     fc.append('P0520')
        if s['noether_violation'] > 0.4:  fc.append('P0171')
        if s['segfault_count'] > 10:      fc.append('P0302')
        return list(dict.fromkeys(fc))

    def ready_check(self) -> Dict[str, bool]:
        s = self._live_streams()
        c = self.e.crank
        return {
            'FIELD':      c.n > 0,
            'VOCAB':      c.n >= 10,
            'EDUCATED':   s['beta_mean'] > GAP * 2,
            'CONNECTED':  s['oil_pressure'] > 0.0,
            'THRESHOLD':  c.emission_threshold > 0.0,
            'CAMSHAFT':   self.e._prompt_sed is not None,
            'CRANKSHAFT': c.n > 0,
            'GLOW_PLUG':  s['coolant_temp'] > 0.1,
            'THREE_FACE': True,
            'ANAPHOR':    True,
            'ONE_WIRE':   True,
        }

    def status(self) -> Dict[str, Any]:
        return {
            'version': self.e.version,
            'ready':   self.ready_check(),
            'faults':  self.fault_scan(),
            'live':    self._live_streams(),
        }

    def torque_csv(self) -> str:
        lines = ['PID,Name,Value']
        for pid, name in self._PID_NAMES.items():
            lines.append(f'0x{pid:04X},{name},{self.sensor_read(pid):.6f}')
        return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  CLI — one wire, every scale, every platform
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser(
        description='segfault-monad v1.217 — one-wire sedenion engine at every scale')
    ap.add_argument('prompt',          nargs='?', default='',
                    help='Prompt text. Reads stdin if omitted.')
    ap.add_argument('-n', '--words',   type=int,  default=32)
    ap.add_argument('-l', '--learn',   action='append', default=[],
                    metavar='FILE',    help='Load text file into β-field')
    ap.add_argument('--load-bin',      metavar='FILE',
                    help='Load bin file READ-ONLY (monad_wordnet.bin etc)')
    ap.add_argument('--save',          metavar='FILE',
                    help='Save session state after generation')
    ap.add_argument('--status',        action='store_true')
    ap.add_argument('--faults',        action='store_true')
    ap.add_argument('--torque',        action='store_true')
    ap.add_argument('--pid',           type=lambda x: int(x, 0))
    ap.add_argument('--json',          action='store_true')
    ap.add_argument('--explore',       metavar='WORD')
    ap.add_argument('--explore-depth', type=int, default=2)
    ap.add_argument('--self-map',      action='store_true',
                    help='Print sedenion curvature self-map and exit')
    ap.add_argument('--calibrate',     metavar='FILE',
                    help='JSON file of [[prompt,answer],...] ground truth pairs')
    ap.add_argument('--perpetual',     action='store_true',
                    help='Stirling cycle: speak→hear→speak until BAO converges')
    ap.add_argument('--perpetual-cycles', type=int, default=None)
    ap.add_argument('--wire',          metavar='SOURCE', default='text',
                    choices=['text','numeric','audio_bands','raw_sedenion'],
                    help='Input source type for the one wire (default: text)')
    args = ap.parse_args()

    engine  = Engine()
    sensors = SensorArray(engine)

    # ── Load bin file (read-only — protected against overwrite) ───────────
    if args.load_bin:
        r = engine.load_bin(args.load_bin)
        print(f"[bin] {r}", file=sys.stderr)

    # ── Load text corpus files ─────────────────────────────────────────────
    for path in args.learn:
        try:
            text = open(path).read()
            r    = engine.load(text)
            print(f"[learn] {path}: {r['words_learned']} words, "
                  f"vocab={r['vocab_size']}", file=sys.stderr)
        except OSError as err:
            print(f"[error] {path}: {err}", file=sys.stderr)

    # ── Calibrate with ground truth pairs ─────────────────────────────────
    if args.calibrate:
        try:
            pairs = json.load(open(args.calibrate))
            results = engine.calibrate(pairs)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                for r in results:
                    mark = '✓ZD' if r['is_zd'] else ('✓' if r['calibrated'] else '✗')
                    print(f"  {mark}  {r['prompt']!r:40s} → {r['answer']!r:12s} "
                          f"prox={r['proximity']:.4f}")
            return
        except Exception as e:
            print(f"[calibrate error] {e}", file=sys.stderr)

    # ── Diagnostic modes ───────────────────────────────────────────────────
    if args.status:
        print(json.dumps(sensors.status(), indent=2)); return
    if args.faults:
        for dtc in sensors.fault_scan(): print(dtc); return
    if args.torque:
        print(sensors.torque_csv()); return
    if args.pid is not None:
        print(sensors.sensor_read(args.pid)); return
    if args.self_map:
        sm = engine.self_map()
        if args.json:
            print(json.dumps(sm, indent=2))
        else:
            print(f"\n=== self_map — sedenion curvature ===")
            for k in range(16):
                pv   = sm['psi'][k]
                cv   = sm['comm'][k]
                bar  = '▓' if k in sm['curved_dims'] else ('░' if k in sm['silent_dims'] else '·')
                print(f"  e{k:2d} {_OP[k]:14s}  ψ={pv:.4f}  [e_k,ws]={cv:.4f}  {bar}")
            principal_labels = [f"e{k}={_OP[k]}" for k in sm['principal_dims']]
            print(f"\n  Principal: {principal_labels}")
            curved_labels = [f"e{k}={_OP[k]}" for k in sm['curved_dims']]
            print(f"  Curved:    {curved_labels}")
            print(f"  Peak ψ:    {sm['peak_psi_operator']}  |  Peak [,]: {sm['peak_operator']} (e{sm['max_curvature_dim']})")
            if sm['zd_dims']:
                print(f"  ON CAUSTIC: {sm['zd_dims']}")
        return

    if args.explore:
        result = engine.explore(args.explore, depth=args.explore_depth)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n=== explore: '{result['seed']}' ===")
            print(f"\nCAM signature:")
            for k, v in result['cam'].items():
                print(f"  {k:14s} = {v}")
            print(f"\nSemantic (A-matrix, depth={args.explore_depth}):")
            for r in result['semantic']:
                print(f"  {r['word']:20s}  w={r['weight']:.5f}  β={r['beta']:.5f}")
            if not result['semantic']:
                print("  (no edges — load a corpus first)")
            print(f"\nLinguistic (cosine > 0.85):")
            for r in result['linguistic']:
                print(f"  {r['word']:20s}  cos={r['cosine']:.5f}")
            if not result['linguistic']:
                print("  (no near neighbors)")
        return

    prompt = args.prompt or sys.stdin.read().strip()
    if not prompt:
        ap.print_help(); return

    # ── Wire the input ─────────────────────────────────────────────────────
    if args.wire != 'text':
        # Non-text input: parse as numeric or sedenion
        try:
            if args.wire == 'numeric':
                data = float(prompt)
            elif args.wire == 'raw_sedenion':
                data = [float(x) for x in prompt.split()]
            elif args.wire == 'audio_bands':
                data = [float(x) for x in prompt.split()]
            else:
                data = prompt
            engine.wire(data, args.wire)
            print(f"[wire:{args.wire}] sedenion loaded into field", file=sys.stderr)
        except Exception as e:
            print(f"[wire error] {e}", file=sys.stderr)

    # ── Perpetual mode — Stirling cycle ───────────────────────────────────
    if args.perpetual:
        print(f"[perpetual] seed: {prompt!r}", file=sys.stderr)
        engine.crank.learn(prompt)
        for state in engine.perpetual(prompt, max_cycles=args.perpetual_cycles):
            if args.json:
                print(json.dumps(state))
            else:
                print(f"[{state['cycle']:3d}] bao={state['bao']:.5f} "
                      f"Δ={state['delta']:.5f}  {state['output']}")
            sys.stdout.flush()
        return

    # ── Generate ───────────────────────────────────────────────────────────
    result = engine.generate(prompt, n_words=args.words)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result['response'])
        print(f"\n[bao={result['bao']:.5f} Δ={result['bao_delta']:.5f} "
              f"vocab={result['vocab_size']} mode={result['mode']} "
              f"lag={result['lag_ratio']:.3f} n={result['target_n']} "
              f"segfaults={result['segfaults']}]", file=sys.stderr)
        if result['dtcs']:
            print(f"[dtcs] {' '.join(result['dtcs'])}", file=sys.stderr)

    # ── Save session (never overwrites protected bin paths) ───────────────
    if args.save:
        r = engine.save_session(args.save)
        print(f"[save] {r}", file=sys.stderr)


if __name__ == '__main__':
    main()
