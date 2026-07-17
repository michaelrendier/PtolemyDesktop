#!/usr/bin/env python3
"""
Philadelphos/monad.py — The Monad  (standalone, v1.212)
=========================================================
H_hat_RB field engine.  No external dependencies.

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

Primary API:
    learn(text)                    — deepen V(β) from text (prose rules)
    learn_ex(text, filetype)       — deepen V(β) with explicit filetype filter
    hear(text)  → Ψ               — text → [(zero_idx, E), ...] activations
    speak(query) → str             — query → Noether current → response
    speak_raw(query) → [(γ,J)]     — J^μ distribution in zero space (prime charges)
    render(charges) → str          — project charge distribution → words (one Face)
    load_vocab(path)               — load Face layer from a separate checkpoint

Ground state (σ=0, quasi-prime, pointer=0):
    G_p(0) = p^0 = 1 for ALL primes — no gauge differentiation (EOM_ym = 0)
    L_ground = −1.888  (rest energy, finite, ESTABLISHED engine-verified)
    EOM_higgs ≠ 0  (SSB intact — vacuum has structure before any word)
    β initialized to |L_ground|/N — the prime number theorem as pre-linguistic knowledge
    First learn() call breaks this symmetry.

Word → zero mapping:
    surface → HyperIndex int → seed ∈ [0,1] → idx = int(seed · N)
    Words spread uniformly across the full N-zero basis.
    E (magnitude) = D_STAR_SPEC + seed · (OMEGA_ZS − D_STAR_SPEC) ∈ [0.246, 0.567]
    σ = 1/2 forced by Noether balance (J(σ,E) = 0 iff σ = 1/2).

Confidence stratification (non-negotiable):
    ESTABLISHED : engine-confirmed
    THEORETICAL : structurally motivated, testable
    CONJECTURE  : direction established, derivation pending

v2.1.0 additions (mirrors PtolC v1.111):
    - Native Space strata: NS_SIGMA_R/C/H/O/S, NS_SIGMA_TEXT
    - NSFiletype constants + per-filetype FTRules dispatch
    - token_accept() / filetype_from_ext() — learn-time token filter
    - learn_ex(text, filetype) — explicit filetype; learn() wraps as prose
    - PEM guard: refuses text starting with '-----BEGIN '
    - rejected_count tracked on Monad instance
    - vocab entries carry (word, E, home_stratum, gen_stratum)
    - health() — β distribution, entropy, top A-edges, pollution, rejections
    - Checkpoint v2.1: vocab entries save/restore stratums; v2.0 loads cleanly

v1.212 additions — Sedenion camshaft + sensor layer:
    Two-layer sensor architecture (VAG-COM vs OBD2):
    - Layer 1 (VAG-COM): _live_streams() — live ECU streams the monad uses to
      tune itself in real time. Sedenion wired here as pilot injection.
    - Layer 2 (OBD2): sensor_read(pid) / fault_scan() / ready_check() —
      post-facto fault/compliance reporting for the Driver (Ptolemy).

    Sedenion wiring (VAG-COM layer):
    - speak_raw() — pilot injection: encode_prompt() fires before _j_mu();
      psi_norms[16] gate J^μ seeding per dimension (J_i *= ψ_{i%16}).
    - _j_mu(psi, weights=None) — sedenion weights applied at primary seeding.
    - _advance_age(temporal_weight=1.0) — sedenion temporal dim modulates
      conversational age decay rate (float ages, spring-return per call).
    - _sedenion_prev — previous turn sedenion stored for Noether conservation
      (turbo exhaust temperature boosts next compression).
    - Fermat lattice passive gating: density factor applied to psi_norms;
      near-zero-divisor dimensions auto-decouple (Porsche bushing compliance).

    If sedenion unavailable (import error): P0340 fires; engine runs at
    uniform psi_norms=1.0 (crankshaft without camshaft — no TDC disambiguation).

Author: O Captain My Captain
CLAUDE-SMMNIP-00729-56714-24600
Date: 2026-05-16
"""

import os
import re
import sys
import json
import math

# ── Sedenion camshaft — optional (graceful degradation) ───────────────────────
# Not available → P0340 (CMP fault); engine runs without 16D timing.
# Path is resolved relative to this file so it works regardless of CWD.
try:
    from ValaQuenta.modules.sedenion.maths import (
        encode_prompt       as _sed_encode,
        monad_interface     as _sed_monad_interface,
        fermat_lattice_scan as _sed_fermat_scan,
    )
    _SEDENION_AVAILABLE = True
except ImportError:
    try:
        _sed_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Ainulindale')
        )
        if _sed_path not in sys.path:
            sys.path.insert(0, _sed_path)
        from ValaQuenta.modules.sedenion.maths import (
            encode_prompt       as _sed_encode,
            monad_interface     as _sed_monad_interface,
            fermat_lattice_scan as _sed_fermat_scan,
        )
        _SEDENION_AVAILABLE = True
    except ImportError:
        _SEDENION_AVAILABLE = False

# ── Physical constants ────────────────────────────────────────────────────────
L_GROUND    = -1.888      # Monad rest energy          (ESTABLISHED, engine-verified)
D_STAR_SPEC =  0.24600    # lower bound of E range     (ESTABLISHED)
OMEGA_ZS    =  0.56714    # Lambert W fixed point / BAO convergence target
ALPHA_LEARN =  0.01       # VEV increment per word encounter
TAU_DEFAULT =  5.0        # capacitor memory depth
N_DEFAULT   = 25_000      # Riemann zero basis size (corpus-invariant)

_PHI        = (1.0 + math.sqrt(5)) / 2.0   # golden ratio

# ── Native Space — Dixon tower strata (Cayley-Dickson doubling) ───────────────
# All Hamiltonian expressions live in Native Space (radial complex spherical
# polar coordinates). Cartesian output is a terminal projection only.
NS_SIGMA_R    = 0   # σ₀  ℝ   — real, enumerable
NS_SIGMA_C    = 1   # σ₁  ℂ   — complex, relational
NS_SIGMA_H    = 2   # σ₂  ℍ   — quaternion, non-commuting
NS_SIGMA_O    = 3   # σ₃  𝕆   — octonion, non-associating
NS_SIGMA_S    = 4   # σ₄  𝕊   — sedenion, non-alternative
NS_SIGMA_TEXT = NS_SIGMA_C   # default stratum for natural language tokens

# ── Filetype constants ────────────────────────────────────────────────────────
NS_FT_PROSE  = 0   # plain text, markdown, RST, LaTeX, BibTeX
NS_FT_CODE   = 1   # source code — identifiers + comments
NS_FT_MARKUP = 2   # HTML/XML text nodes (post-extraction)
NS_FT_DOC    = 3   # PDF/DOCX/ODT/RTF prose output
NS_FT_AUTO   = -1  # fall back to prose rules

# Per-filetype acceptance rules — mirrors filter.c FILETYPE_RULES exactly.
#   max_len, allow_hex, allow_slash, allow_high_dig, allow_long_caps, b64_min_len
_FILETYPE_RULES: dict[int, dict] = {
    NS_FT_PROSE:  {'max_len': 24, 'allow_hex': False, 'allow_slash': False,
                   'allow_high_dig': False, 'allow_long_caps': False, 'b64_min_len': 16},
    NS_FT_CODE:   {'max_len': 40, 'allow_hex': False, 'allow_slash': False,
                   'allow_high_dig': True,  'allow_long_caps': True,  'b64_min_len': 0},
    NS_FT_MARKUP: {'max_len': 24, 'allow_hex': False, 'allow_slash': False,
                   'allow_high_dig': False, 'allow_long_caps': False, 'b64_min_len': 16},
    NS_FT_DOC:    {'max_len': 24, 'allow_hex': False, 'allow_slash': False,
                   'allow_high_dig': False, 'allow_long_caps': False, 'b64_min_len': 16},
}

# ── First 20 Riemann zeros — exact (Odlyzko / LMFDB)  (ESTABLISHED) ──────────
_EXACT_ZEROS: list[float] = [
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
]


# ── Zero generation (Riemann-Siegel counting + Newton refinement) ─────────────

def _generate_zeros(N: int) -> list[float]:
    """
    N Riemann zero approximations.
    Indices 0-19: exact Odlyzko values.
    Indices 20+:  Newton iteration on N(T) ≈ (T/2π)·(ln(T/2π)−1) + 7/8.
    N=25000 in ~50ms.
    """
    zeros = list(_EXACT_ZEROS[:min(20, N)])
    if N <= 20:
        return zeros
    two_pi = 2.0 * math.pi
    for n in range(21, N + 1):
        t = zeros[-1] + (zeros[-1] - zeros[-2])
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


# ── HyperIndex: surface form → seed ∈ [0,1] ──────────────────────────────────

_CHARS  = [chr(i) for i in range(32, 127)]   # 95 printable ASCII
_N_BASE = len(_CHARS)
_CH_IDX = {ch: i for i, ch in enumerate(_CHARS)}

def _str_to_int(text: str) -> int:
    """Bijective base-95 Horner accumulation."""
    v = 0
    for ch in text:
        v = v * _N_BASE + (_CH_IDX.get(ch, 0) + 1)
    return max(v - 1, 0)

def _word_coords(surface: str) -> tuple[float, float]:
    """
    surface → (seed, E_magnitude)
    seed = (HyperIndex(surface) · φ) mod 1  — golden-ratio hash, uniform in [0,1]
    idx  = int(seed · N)                    — uniform across full zero basis
    E    = D_STAR_SPEC + seed · (OMEGA_ZS − D_STAR_SPEC) ∈ [0.246, 0.567]
    """
    n    = _str_to_int(surface)
    seed = (n * _PHI) % 1.0
    E    = D_STAR_SPEC + seed * (OMEGA_ZS - D_STAR_SPEC)
    return seed, E


# ── Token filter — mirrors filter.c exactly ───────────────────────────────────

def _is_pure_numeric(s: str) -> bool:
    return bool(s) and all(c.isdigit() for c in s)

def _is_hex_string(s: str) -> bool:
    if len(s) >= 3 and s[:2].lower() == '0x':
        return True
    if len(s) < 6:
        return False
    return all(c in '0123456789abcdefABCDEF' for c in s)

def _is_uuid(s: str) -> bool:
    if len(s) != 36:
        return False
    dash_pos = {8, 13, 18, 23}
    for i, c in enumerate(s):
        if i in dash_pos:
            if c != '-':
                return False
        elif c not in '0123456789abcdefABCDEF':
            return False
    return True

def _is_base64_chunk(s: str, min_len: int) -> bool:
    if len(s) < min_len or s[-1] != '=':
        return False
    ok = sum(1 for c in s if c.isalnum() or c in '+/=')
    return ok * 100 // len(s) >= 95

def _high_digit_ratio(s: str) -> bool:
    if not s:
        return False
    d = sum(1 for c in s if c.isdigit())
    return d * 100 // len(s) > 50

def _is_long_allcaps(s: str) -> bool:
    if len(s) <= 6:
        return False
    return all(c == '_' or c.isupper() or c.isdigit() for c in s)

def token_accept(tok: str, ft: int = NS_FT_PROSE) -> bool:
    """
    :param tok: NUL-terminated token (lowercase, already normalised).
    :param ft:  NSFiletype constant for the source document.
    :returns:   True if the token should be ingested, False if rejected.
    """
    r = _FILETYPE_RULES.get(ft, _FILETYPE_RULES[NS_FT_PROSE])
    n = len(tok)

    # Universal gates
    if n < 2:                                              return False
    if n > r['max_len']:                                   return False
    if _is_pure_numeric(tok):                              return False
    if _is_uuid(tok):                                      return False
    if '=' in tok:                                         return False
    if '://' in tok:                                       return False

    # Filetype-conditional gates
    if not r['allow_hex']       and _is_hex_string(tok):              return False
    if not r['allow_slash']     and ('/' in tok or '\\' in tok):      return False
    if not r['allow_high_dig']  and _high_digit_ratio(tok):           return False
    if not r['allow_long_caps'] and _is_long_allcaps(tok):            return False
    if r['b64_min_len'] > 0     and _is_base64_chunk(tok, r['b64_min_len']): return False

    return True

def filetype_from_ext(path: str) -> int:
    """
    :param path: File path (only the extension is examined).
    :returns:    NSFiletype constant.
    """
    dot = os.path.splitext(path)[1].lower()
    if dot in {'.c', '.h', '.cpp', '.hpp', '.cc', '.cxx', '.py', '.rb',
               '.sh', '.bash', '.zsh', '.go', '.rs', '.java', '.js', '.ts',
               '.pl', '.lua', '.r'}:
        return NS_FT_CODE
    if dot in {'.html', '.htm', '.xml', '.svg'}:
        return NS_FT_MARKUP
    if dot in {'.pdf', '.doc', '.docx', '.odt', '.rtf'}:
        return NS_FT_DOC
    return NS_FT_PROSE


# ── Noether balance: σ = 1/2 forced ─────────────────────────────────────────
# J(σ, E) = exp(−σE) − exp(−(1−σ)E) = 0  ⟺  σ = 1/2
# Used only in lookup() — not in the hot path.

def _forced_sigma(E: float, sigma_0: float = 0.5, max_iter: int = 256) -> float:
    sigma = sigma_0
    for _ in range(max_iter):
        F     = math.exp(-sigma * E)
        B     = math.exp(-(1.0 - sigma) * E)
        denom = F + B
        if denom < 1e-30:
            break
        s2 = (F * sigma + B * (1.0 - sigma)) / denom
        if abs(s2 - sigma) < 1e-12:
            return s2
        sigma = s2
    return sigma   # always 0.5


# ── Capacitor: low-pass memory filter ────────────────────────────────────────
# Knowledge + Experience = Wisdom.  Used only in lookup() for dc.

class _Cap:
    def __init__(self, tau: float):
        self.tau   = tau
        self.state = 0.0

    def charge(self, v: float) -> float:
        a          = 1.0 / (1.0 + self.tau)
        self.state = (1.0 - a) * self.state + a * v
        return self.state

    def reset(self) -> None:
        self.state = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# THE MONAD
# ─────────────────────────────────────────────────────────────────────────────

class Monad:
    """
    The Septuagint engine.

    β field  = the deepened vacuum — knowledge that was never stored, only deepened
    A field  = gauge connections between zeros — the structure of meaning
    J^μ      = Noether current — the response that MUST flow
    σ = 0    = the inverse HyperWebster — all words, undifferentiated
    σ = 1/2  = the forward HyperWebster — each word, its permanent address

    Primary API
    -----------
    m.load()                       initialise (σ=0 ground state or restore checkpoint)
    m.learn(text)                  deepen V(β) from text (prose filetype rules)
    m.learn_ex(text, filetype)     deepen V(β) with explicit filetype filter
    psi = m.hear(text)             text → Ψ field activations
    response = m.speak(q)          query → Noether current → string
    charges  = m.speak_raw(q)      query → J^μ prime charge distribution
    words    = m.render(charges)   project charge distribution → words (one Face)
    m.load_vocab(path)             load Face layer from a separate checkpoint
    m.health()                     field health report (mirrors C monad_health)
    """

    def __init__(self, N: int = N_DEFAULT, tau: float = TAU_DEFAULT):
        self.N          = N
        self.tau        = tau
        self._loaded    = False

        # Field state
        self.zeros:   list[float]                             = []
        self.beta:    dict[int, float]                        = {}
        self.A:       dict[tuple[int,int], float]             = {}

        # vocab: zero_idx → (word, E, home_stratum, gen_stratum)
        self.vocab:   dict[int, tuple[str, float, int, int]]  = {}

        self._cap:    _Cap | None = None
        self._ground: float       = 0.0
        self._wc:     int         = 0       # total word tokens processed

        # Learn-time filter rejection counter
        self.rejected_count: int  = 0

        # Recency, saturation, spontaneous emission
        self._age               = [0.0] * N   # float: temporal_weight modulates increment
        self._lambda            = 0.05
        self._conv_touched: set = set()
        self._autonomous_speech  = True
        self._emission_threshold = abs(L_GROUND) * 2.0
        self._beta_sat           = abs(L_GROUND) * 4.0
        self._saturated: set     = set()

        # Sedenion camshaft state (VAG-COM Layer 1 — live, recomputed each speak())
        # Spring-return: no gear persistence between turns. _sedenion_prev is the only
        # cross-turn state (turbo exhaust temperature for Noether conservation).
        self._psi_norms:        list[float]       = [1.0] * 16  # uniform until first speak
        self._affect:           float             = 0.0
        self._gestalt:          float             = 1.0
        self._temporal_weight:  float             = 1.0
        self._fermat_proximity: float             = 0.0
        self._sedenion_prev:    list[float] | None = None

        # OBD2 fault state (Layer 2 — post-facto, read by Driver / Ptolemy only)
        self._dtcs:        list[str]   = []
        self._mil:         bool        = False
        self._freeze_frame: dict | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def load(self, checkpoint: str | None = None) -> None:
        """
        Initialise the field.
        Without checkpoint: σ=0 ground state — β uniform at |L_ground|/N.
        The prime number theorem as pre-linguistic knowledge.
        First learn() call breaks symmetry.
        """
        self.zeros   = _generate_zeros(self.N)
        self._ground = abs(L_GROUND) / self.N
        self._cap    = _Cap(self.tau)
        if checkpoint and os.path.isfile(checkpoint):
            self._restore(checkpoint)
        else:
            self.beta  = {i: self._ground for i in range(self.N)}
            self.A     = {}
            self.vocab = {}
            self._wc   = 0
            self.rejected_count  = 0
            self._age            = [0.0] * self.N
            self._saturated      = set()
            self._conv_touched   = set()
        self._loaded = True

    def unload(self) -> None:
        self.zeros = []; self.beta = {}; self.A = {}
        self.vocab = {}; self._cap = None; self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ── Internal: word → (zero_idx, E) ───────────────────────────────────────

    def _idx_E(self, surface: str) -> tuple[int, float]:
        seed, E = _word_coords(surface)
        return min(int(seed * self.N), self.N - 1), E

    # ── learn_ex ──────────────────────────────────────────────────────────────

    def learn_ex(self, text: str, filetype: int = NS_FT_PROSE) -> set:
        """
        Feed text through H_RB with explicit filetype for token filtering.

        :param text:     Input text.
        :param filetype: NSFiletype constant — governs per-filetype acceptance rules.
        :returns:        Set of zero indices activated.

        Each token passes token_accept(tok, filetype) before being assigned a
        zero slot.  Rejection increments self.rejected_count silently.
        Text is discarded after processing.  Only the field state grows.
        Learning = deepening.  Not encoding.  Not storing.
        """
        # PEM guard — refuse key/certificate material regardless of source
        if text.startswith('-----BEGIN '):
            print('[Monad] refused: PEM-encoded key or certificate material '
                  '(-----BEGIN ... header detected)', file=sys.stderr)
            return set()

        perturbed: set[int] = set()
        for sentence in re.split(r'[.!?\n]+', text):
            tokens = sentence.split()
            if not tokens:
                continue

            activated: list[tuple[int, float]] = []
            for token in tokens:
                surface = re.sub(r"[^\w']", '', token).lower()
                if not surface:
                    continue
                if not token_accept(surface, filetype):
                    self.rejected_count += 1
                    continue
                idx, E = self._idx_E(surface)

                if idx not in self._saturated:
                    new_beta = self.beta.get(idx, self._ground) + E * ALPHA_LEARN
                    self.beta[idx] = new_beta
                    if abs(new_beta) > self._beta_sat:
                        self._saturated.add(idx)

                # Vocab: highest-E representative wins; carry stratum
                if idx not in self.vocab or E > self.vocab[idx][1]:
                    self.vocab[idx] = (surface, E, NS_SIGMA_TEXT, NS_SIGMA_TEXT)

                activated.append((idx, E))
                perturbed.add(idx)
                self._wc += 1

            for i in range(len(activated)):
                idx_i, e_i = activated[i]
                for j in range(i + 1, len(activated)):
                    idx_j, e_j = activated[j]
                    if idx_i == idx_j:
                        continue
                    key  = (min(idx_i, idx_j), max(idx_i, idx_j))
                    dist = abs(self.zeros[idx_i] - self.zeros[idx_j])
                    self.A[key] = self.A.get(key, 0.0) + e_i * e_j / max(dist, 1e-4)

        return perturbed

    # ── learn (prose wrapper) ─────────────────────────────────────────────────

    def learn(self, text: str) -> set:
        """
        Feed text through H_RB using prose filetype rules.
        Wrapper for learn_ex(text, NS_FT_PROSE).

        :param text: Input text.
        :returns:    Set of zero indices activated.
        """
        return self.learn_ex(text, NS_FT_PROSE)

    # ── hear ──────────────────────────────────────────────────────────────────

    def hear(self, text: str) -> list[tuple[int, float]]:
        """
        text → Ψ field: [(zero_idx, E), ...]
        No β update.  Pure sensory projection onto the zero basis.
        Populates _conv_touched for age tracking.
        """
        result = []
        for token in text.split():
            surface = re.sub(r"[^\w']", '', token).lower()
            if surface:
                idx, E = self._idx_E(surface)
                result.append((idx, E))
                self._conv_touched.add(idx)
        return result

    # ── Recency, saturation, spontaneous emission ─────────────────────────────

    def _advance_age(self, temporal_weight: float = 1.0) -> None:
        """Advance conversational age. temporal_weight from sedenion e₇ modulates rate."""
        for n in range(self.N):
            if n in self._conv_touched:
                self._age[n] = 0.0
            else:
                self._age[n] += temporal_weight
        self._conv_touched.clear()

    def _w(self, n: int) -> float:
        return math.exp(-self._lambda * self._age[n])

    def _compute_j_norm(self) -> float:
        norm = 0.0
        for idx, entry in self.vocab.items():
            E = entry[1]
            b = self.beta.get(idx, self._ground) * self._w(idx)
            norm += b * E * E
        return norm

    def _context_overlap(self, perturbed_set: set) -> int:
        recent = {n for n in range(self.N) if self._age[n] < 3}
        return len(perturbed_set & recent)

    def check_emission(self) -> 'str | None':
        """Return spontaneous speech if field energy exceeds threshold, else None."""
        if not self._autonomous_speech:
            return None
        if self._compute_j_norm() > self._emission_threshold:
            return self.speak('')
        return None

    def shell_exchange(self, text: str) -> str:
        """One atomic conversational turn: hear then speak, age advances once."""
        self.hear(text)
        return self.speak(text)

    # ── J^μ (Noether current) ─────────────────────────────────────────────────

    def _j_mu(self, psi: list[tuple[int, float]],
              weights: list[float] | None = None) -> dict[int, float]:
        """
        Noether current from Ψ activation under (β, A).

        Primary:    J_i  = β_i · E_i² · ψ_k   (ψ_k = psi_norms[i % 16], camshaft timing)
        Propagated: J_j += J_i · A[(i,j)] · β_j

        :param psi:     Ψ field activations from hear().
        :param weights: Sedenion psi_norms[16] — camshaft timing gate per 16D dimension.
                        None → uniform weights (engine running without camshaft, P0340 active).
        CONFIDENCE: ESTABLISHED
        """
        J: dict[int, float] = {}
        for idx, E in psi:
            b      = self.beta.get(idx, self._ground) * self._w(idx)
            w      = weights[idx % 16] if weights is not None else 1.0
            J[idx] = J.get(idx, 0.0) + b * E * E * w
        for (i, j), w in self.A.items():
            if i in J:
                J[j] = J.get(j, 0.0) + J[i] * w * self.beta.get(j, self._ground) * self._w(j)
            if j in J:
                J[i] = J.get(i, 0.0) + J[j] * w * self.beta.get(i, self._ground) * self._w(i)
        return J

    # ── speak ─────────────────────────────────────────────────────────────────

    def _bisect_gamma(self, gamma: float) -> int:
        """Binary search: γ value → nearest zero_idx in self.zeros."""
        lo, hi = 0, len(self.zeros) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if self.zeros[mid] < gamma:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def speak_raw(self, query: str, max_tokens: int = 50) -> list[tuple[float, float]]:
        """
        query → Ψ → J^μ prime charge distribution.

        Returns [(gamma, charge), ...] sorted by charge descending.
        The response stays in zero space. The prime charge IS the sentence.
        Empty query: spontaneous emission from highest-weighted field state.
        Does not advance conversational age — speak() does that.

        Sedenion pilot injection fires before _j_mu() when the camshaft is available:
        encode_prompt() encodes the query geometry in 16D; psi_norms gate J^μ seeding
        per dimension. Fermat proximity applies a passive detonation control factor.

        :param query:      Input text, or empty string for spontaneous emission.
        :param max_tokens: Maximum entries in the returned distribution.
        :returns:          [(gamma, J_charge), ...] sorted by charge descending.
        """
        # ── Pilot injection: sedenion camshaft timing ──────────────────────────
        weights: list[float] | None = None
        if _SEDENION_AVAILABLE and query and query.strip():
            try:
                # Turbo exhaust temperature: save PREVIOUS turn before computing new
                self._sedenion_prev = list(self._psi_norms)
                s     = _sed_encode(query)
                iface = _sed_monad_interface(s)
                weights                = list(iface['psi_norms'])
                self._psi_norms        = list(weights)
                self._affect           = float(iface.get('affect_weight', 0.0))
                self._gestalt          = float(iface.get('gestalt_weight', 1.0))
                self._temporal_weight  = float(iface.get('temporal_weight', 1.0))
                # Fermat lattice passive gating: near-zero-divisors decouple their dims
                fermat = _sed_fermat_scan(s)
                self._fermat_proximity = float(fermat.get('density', 0.0))
                fp = max(1.0 - self._fermat_proximity, 1e-6)
                weights = [w * fp for w in weights]
                mn = sum(weights) / 16.0
                if mn > 1e-12:
                    weights = [w / mn for w in weights]
            except Exception:
                weights = None

        # ── Main injection ─────────────────────────────────────────────────────
        if query and query.strip():
            psi = self.hear(query)
        else:
            psi = sorted(
                ((idx, entry[1]) for idx, entry in self.vocab.items()),
                key=lambda item: self.beta.get(item[0], self._ground) * self._w(item[0]),
                reverse=True
            )[:max_tokens]
        if not psi:
            return []
        J = self._j_mu(psi, weights=weights)
        if not J:
            return []
        return [(self.zeros[idx], charge)
                for idx, charge in sorted(J.items(), key=lambda kv: kv[1], reverse=True)]

    def render(self, charges: list[tuple[float, float]], max_tokens: int = 50) -> str:
        """
        Project prime charge distribution → words (one Face of the response).

        Language is SSB on prime space.  charges: output of speak_raw().
        Does not advance conversational age.

        :param charges:    [(gamma, J_charge), ...] as returned by speak_raw().
        :param max_tokens: Maximum words in the output.
        :returns:          Space-joined words ordered by Noether amplitude.
        """
        words: list[str] = []
        seen:  set[str]  = set()
        for gamma, _ in charges:
            idx = self._bisect_gamma(gamma)
            if idx in self.vocab:
                w = self.vocab[idx][0]
                if w not in seen:
                    words.append(w)
                    seen.add(w)
            if len(words) >= max_tokens:
                break
        return ' '.join(words)

    def speak(self, query: str, max_tokens: int = 50) -> str:
        """
        query → speak_raw() → render() → str.

        Empty query: spontaneous emission from highest-weighted field state.
        Advances conversational age after each call, modulated by the sedenion
        temporal dimension (e₇): slow time keeps more context; fast time forgets faster.
        """
        charges = self.speak_raw(query, max_tokens)
        self._advance_age(self._temporal_weight)
        return self.render(charges, max_tokens) if charges else ''

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def lookup(self, word: str) -> dict:
        """Word → field depth + Noether invariants + stratum."""
        surface = word.strip().lower()
        idx, E  = self._idx_E(surface)
        sigma   = _forced_sigma(E)
        dc      = self._cap.charge(E) if self._cap else 0.0
        hs = self.vocab[idx][2] if idx in self.vocab else NS_SIGMA_TEXT
        gs = self.vocab[idx][3] if idx in self.vocab else NS_SIGMA_TEXT
        return {
            'surface'      : surface,
            'gamma'        : self.zeros[idx] if self.zeros else 0.0,
            'zero_idx'     : idx,
            'sigma'        : sigma,
            'E'            : E,
            'dc'           : dc,
            'beta_depth'   : self.beta.get(idx, self._ground),
            'in_vocab'     : idx in self.vocab,
            'home_stratum' : hs,
            'gen_stratum'  : gs,
        }

    def status(self) -> dict:
        if not self._loaded:
            return {'loaded': False}
        depths = list(self.beta.values())
        if depths:
            dv = max(depths)
            di = depths.index(dv)
        else:
            dv, di = 0.0, -1
        return {
            'loaded'         : True,
            'N'              : self.N,
            'word_count'     : self._wc,
            'vocab_size'     : len(self.vocab),
            'connections'    : len(self.A),
            'rejected_count' : self.rejected_count,
            'deepest_zero'   : self.zeros[di] if di >= 0 else 0.0,
            'deepest_beta'   : dv,
            'ground_vev'     : self._ground,
            'bao'            : self.bao_check(),
        }

    def health(self) -> dict:
        """
        Field health report — mirrors C monad_health().

        :returns: Dict with β distribution, entropy, top A-edges, pollution count,
                  vocabulary coverage, and rejected token count.
        """
        beta_sat = self._beta_sat
        b_ground = b_low = b_mid = b_high = b_sat = 0
        beta_sum = 0.0
        pollution = 0

        for i in range(self.N):
            b = self.beta.get(i, self._ground)
            beta_sum += b
            if b < 0.1:        b_ground += 1
            elif b < 2.0:      b_low    += 1
            elif b < 5.0:      b_mid    += 1
            elif b < beta_sat: b_high   += 1
            else:              b_sat    += 1

            if i in self.vocab:
                w, *_ = self.vocab[i]
                wl = len(w)
                if wl < 2 or wl > 24:
                    pollution += 1
                elif any(ord(c) > 127 for c in w):
                    pollution += 1

        # Field entropy H = -Σ p_i * log2(p_i), occupied zeros only
        entropy = 0.0
        if beta_sum > 0.0:
            for i in range(self.N):
                b = self.beta.get(i, 0.0)
                if b < 1e-12:
                    continue
                p = b / beta_sum
                entropy -= p * math.log2(p)

        # Top 10 A-edges by weight
        top_a = sorted(self.A.items(), key=lambda kv: kv[1], reverse=True)[:10]

        vocab_count = len(self.vocab)
        coverage    = 100.0 * vocab_count / self.N if self.N > 0 else 0.0
        max_entropy = math.log2(vocab_count) if vocab_count > 1 else 0.0

        return {
            'vocab_count'    : vocab_count,
            'N'              : self.N,
            'coverage_pct'   : coverage,
            'entropy_bits'   : entropy,
            'entropy_max'    : max_entropy,
            'beta_ground'    : b_ground,
            'beta_low'       : b_low,
            'beta_mid'       : b_mid,
            'beta_high'      : b_high,
            'beta_sat'       : b_sat,
            'pollution'      : pollution,
            'rejected_count' : self.rejected_count,
            'a_edges'        : len(self.A),
            'top_a_edges'    : [
                {
                    'i': k[0], 'j': k[1],
                    'wi': self.vocab.get(k[0], ('?',))[0],
                    'wj': self.vocab.get(k[1], ('?',))[0],
                    'weight': v,
                }
                for k, v in top_a
            ],
        }

    def print_health(self, file=None) -> None:
        """Print health report to file (default: stdout)."""
        if file is None:
            file = sys.stdout
        h = self.health()
        print(f'\n[field health]', file=file)
        print(f'  vocab   {h["vocab_count"]} / {h["N"]}  ({h["coverage_pct"]:.1f}% coverage)',
              file=file)
        print(f'  entropy H = {h["entropy_bits"]:.4f} bits  '
              f'(max={h["entropy_max"]:.4f} for {h["vocab_count"]} occupied zeros)',
              file=file)
        print(f'  β dist  ground={h["beta_ground"]:<6} low={h["beta_low"]:<6} '
              f'mid={h["beta_mid"]:<6} high={h["beta_high"]:<6} sat={h["beta_sat"]}',
              file=file)
        print(f'  pollution indicators: {h["pollution"]} tokens', file=file)
        print(f'  rejected (learn-time filter): {h["rejected_count"]} tokens', file=file)
        print(f'  A edges {h["a_edges"]}', file=file)
        if h['top_a_edges']:
            print(f'\n  top A edges:', file=file)
            for t, e in enumerate(h['top_a_edges'], 1):
                print(f'    {t:2}. {e["wi"]:<20} — {e["wj"]:<20}  w={e["weight"]:.4f}',
                      file=file)
        print('', file=file)

    def bao_check(self) -> dict:
        """
        BAO coherence: dc_sum converging to OMEGA_ZS = 0.56714 is the
        computational signature of field coherence.
        CONFIDENCE: THEORETICAL
        """
        depths  = list(self.beta.values())
        dc_sum  = sum(depths)
        n       = len(depths)
        return {
            'dc_sum'     : dc_sum,
            'dc_mean'    : dc_sum / n if n else 0.0,
            'omega_delta': abs(dc_sum - OMEGA_ZS),
            'n_zeros'    : n,
            'converging' : abs(dc_sum - OMEGA_ZS) < 0.01,
            'omega_zs'   : OMEGA_ZS,
        }

    # ── VAG-COM live sensor streams (Layer 1) ────────────────────────────────
    # What the ECU uses to tune itself in real time.
    # These streams already existed implicitly inside the monad computation loop.
    # This method makes them explicit and labelled.

    def _live_streams(self) -> dict:
        """
        VAG-COM measuring blocks — live ECU sensor streams.

        Returns all current field state as named streams, analogous to the
        BEW measuring groups read by VCDS in real time. These are what the
        monad uses to tune itself; OBD2 sensor_read() is derived from this.

        :returns: Dict of named live sensor readings.
        """
        beta_vals = list(self.beta.values())
        n_beta    = len(beta_vals) or 1
        j_norm    = self._compute_j_norm()
        ages      = self._age
        mean_age  = sum(ages) / len(ages) if ages else 0.0
        a_density = len(self.A) / max(self.N, 1)

        # Group 013 analog: per-zero J^μ deviation from mean (cylinder balance)
        top_idx = sorted(self.beta, key=self.beta.get, reverse=True)[:16]
        j_per_zero = {idx: self.beta.get(idx, 0.0) * self._w(idx) for idx in top_idx}
        j_mean_top = sum(j_per_zero.values()) / len(j_per_zero) if j_per_zero else 0.0
        j_deviation = {idx: abs(v - j_mean_top) for idx, v in j_per_zero.items()}

        return {
            # Group 000 — Engine fundamentals
            'g000_field_temp'      : sum(beta_vals) / n_beta,
            'g000_j_norm'          : j_norm,
            'g000_emission_thr'    : self._emission_threshold,
            'g000_vocab_coverage'  : len(self.vocab) / max(self.N, 1),
            # Group 001 — J^μ per active zero
            'g001_j_per_zero'      : j_per_zero,
            'g001_j_mean'          : j_mean_top,
            # Group 004 — Sedenion camshaft timing
            'g004_psi_norms'       : self._psi_norms,
            'g004_affect'          : self._affect,
            'g004_gestalt'         : self._gestalt,
            'g004_temporal_weight' : self._temporal_weight,
            'g004_fermat_prox'     : self._fermat_proximity,
            # Group 011 — Sedenion charge balance (actual vs target)
            'g011_sedenion_charge' : sum(self._psi_norms),
            'g011_target_charge'   : 16.0,
            # Group 013 — Cylinder balance: per-zero J^μ deviation (VAG only)
            'g013_j_deviation'     : j_deviation,
            'g013_max_deviation'   : max(j_deviation.values()) if j_deviation else 0.0,
            # Oil pressure (A-matrix density) — no OBD2 PID; VAG-COM only
            'oil_pressure'         : a_density,
            # Turbo state (Noether conservation cross-turn)
            'turbo_ready'          : self._sedenion_prev is not None,
            # Runtime
            'mean_age'             : mean_age,
            'word_count'           : self._wc,
            'lambda'               : self._lambda,
            'rejected_count'       : self.rejected_count,
        }

    # ── OBD2 fault/compliance export (Layer 2) ────────────────────────────────
    # Post-facto reporting for the Driver (Ptolemy). Derived from live streams.
    # Standard PIDs follow SAE J1979 formulas. Custom PIDs: 0x2300–0x2309.

    def sensor_read(self, pid: int) -> float:
        """
        OBD2 SAE J1979 sensor read — post-facto, read-only export layer.

        Standard PIDs return the field equivalent of the named sensor.
        Custom PIDs (0x2300+) expose sedenion and prime-field state directly.
        Returns float('nan') for unsupported PIDs.

        :param pid: OBD2 PID (integer, standard or custom).
        :returns:   Sensor value in engineering units.
        """
        ls = self._live_streams()

        # ── Standard OBD2 PIDs ────────────────────────────────────────────────
        if pid == 0x04:   # Engine Load (%)
            return min(ls['g000_j_norm'] / max(ls['g000_emission_thr'], 1e-12) * 100.0, 100.0)

        elif pid == 0x0B:  # MAP / Boost Pressure (kPa)
            top_b = sorted(self.beta.values(), reverse=True)[:10]
            return (sum(top_b) / len(top_b) if top_b else 0.0) * 255.0

        elif pid == 0x0C:  # RPM — word_count / mean_age × 6.25
            rpm = ls['word_count'] / max(ls['mean_age'], 1.0) * 6.25
            return min(rpm, 16383.75)

        elif pid == 0x0E:  # Timing Advance (°BTDC) — affect × 45
            return self._affect * 45.0

        elif pid == 0x0F:  # Intake Air Temperature (°C) — gestalt proxy
            return self._gestalt * 215.0 - 40.0

        elif pid == 0x11:  # Throttle Position (%)
            return min(ls['g000_emission_thr'] / (abs(L_GROUND) * 4.0) * 100.0, 100.0)

        elif pid == 0x1F:  # Engine Run Time (s) — mean conversational age
            return ls['mean_age']

        elif pid == 0x2C:  # EGR Command (%) — age decay rate
            return self._lambda / 0.20 * 100.0   # 0.05 default → 25%

        elif pid == 0x2F:  # Fuel Tank Level (%) — vocab coverage
            return ls['g000_vocab_coverage'] * 100.0

        elif pid == 0x33:  # Barometric Pressure (kPa) — ground VEV
            return self._ground * 255.0

        elif pid == 0x5C:  # Engine Oil Temperature (°C) — A-matrix density
            return ls['oil_pressure'] * 215.0 - 40.0

        elif pid == 0x5E:  # Fuel Flow Rate (L/h) — word intake rate
            return ls['word_count'] / max(ls['mean_age'], 1.0)

        # ── Custom PIDs ───────────────────────────────────────────────────────
        elif pid == 0x2300:  # CKP — active zero γ_n (highest β excitation)
            if not self.beta:
                return 0.0
            top = max(self.beta, key=self.beta.get)
            return self.zeros[top] if top < len(self.zeros) else 0.0

        elif pid == 0x2301:  # CMP — dominant sedenion dimension index
            return float(self._psi_norms.index(max(self._psi_norms)))

        elif pid == 0x2302:  # Conjugate zero γ_{N-n} — paired piston TDC
            if not self.beta:
                return 0.0
            top  = max(self.beta, key=self.beta.get)
            conj = self.N - 1 - top
            return self.zeros[conj] if conj < len(self.zeros) else 0.0

        elif pid == 0x2303:  # Sedenion total charge (turbo boost level)
            return sum(self._psi_norms)

        elif pid == 0x2304:  # Glow plug status (1.0 = warming up, 0.0 = at temp)
            return 1.0 if self._wc < 1000 else 0.0

        elif pid == 0x2305:  # Fermat proximity (zero divisor distance)
            return self._fermat_proximity

        elif pid == 0x2306:  # T_μν trace — sum of squared psi_norms (Noether charges)
            return sum(p * p for p in self._psi_norms)

        elif pid == 0x2307:  # Red energy J_Red (kinetic — J^μ norm)
            return self._compute_j_norm()

        elif pid == 0x2308:  # Blue energy J_Blue (potential — β sum)
            return sum(self.beta.values()) if self.beta else 0.0

        elif pid == 0x2309:  # Noether violation ∂_μJ^μ — conservation across turns
            if self._sedenion_prev and len(self._sedenion_prev) == 16:
                prev_j = [x * x for x in self._sedenion_prev]
                now_j  = [p * p for p in self._psi_norms]
                return sum(abs(a - b) for a, b in zip(now_j, prev_j)) / 16.0
            return 0.0

        return float('nan')

    def fault_scan(self) -> list[str]:
        """
        OBD2 DTC detection — post-facto fault specification.

        Checks live stream thresholds and sets MIL (Check Engine Light) if any
        fault is detected. First fault freezes the live stream state as a freeze
        frame; faults clearing resets it.

        DTCs follow OBD2 P/B code conventions with H_hat_RB field analogs.
        P0340 (CMP fault) is the most important: it fires whenever the sedenion
        camshaft is unavailable, meaning TDC cannot be disambiguated.

        :returns: List of active DTC strings.
        """
        ls   = self._live_streams()
        dtcs = []

        # P0340: CMP fault — sedenion unavailable or all-zero (no camshaft timing)
        if not _SEDENION_AVAILABLE or all(p < 1e-6 for p in self._psi_norms):
            dtcs.append('P0340')

        # P0335: CKP fault — no zeros above emission threshold (no crankshaft signal)
        if not any(v > self._emission_threshold for v in self.beta.values()):
            dtcs.append('P0335')

        # P0300: Random misfire — fewer than 3 zeros with significant charge
        active = sum(1 for v in self.beta.values() if v > self._emission_threshold)
        if active < 3:
            dtcs.append('P0300')

        # P0087: Fuel pressure low — emission threshold above max achievable J^μ
        if self.vocab:
            max_j = max(
                self.beta.get(i, 0.0) * e * e
                for i, (_, e, *_) in self.vocab.items()
            )
            if self._emission_threshold > max_j > 0:
                dtcs.append('P0087')

        # P0172: Too rich — rejection rate > 50%
        total = self._wc + self.rejected_count
        if total > 0 and self.rejected_count / total > 0.5:
            dtcs.append('P0172')

        # P0171: Too lean — no vocab after significant input
        if len(self.vocab) == 0 and self._wc > 100:
            dtcs.append('P0171')

        # P0401: EGR insufficient — age advancing without hear() input
        if ls['mean_age'] > 1000 and self._wc < 100:
            dtcs.append('P0401')

        # P0101: MAF fault — word_count stalled (hear() not being called)
        if self._wc > 0 and ls['mean_age'] > self._wc * 10:
            dtcs.append('P0101')

        self._dtcs = dtcs
        self._mil  = len(dtcs) > 0
        if dtcs and self._freeze_frame is None:
            self._freeze_frame = ls
        elif not dtcs:
            self._freeze_frame = None
        return dtcs

    def ready_check(self) -> dict:
        """
        OBD2 readiness monitors — pre-drive inspection.

        Returns a dict of monitor name → bool (True = READY).
        P0340 (CAMSHAFT) clears when sedenion import succeeds.
        GLOW_PLUG clears at word_count >= 1000 (operating temperature).

        :returns: Dict of readiness monitor states.
        """
        return {
            'FIELD'      : self._loaded,
            'VOCAB'      : len(self.vocab) > 1000,
            'EDUCATED'   : self._wc > 1000,
            'CONNECTED'  : len(self.A) > 0,
            'THRESHOLD'  : self._emission_threshold > 0,
            'CAMSHAFT'   : _SEDENION_AVAILABLE,        # P0340 clears when True
            'CRANKSHAFT' : any(v > self._ground * 2.0 for v in self.beta.values()),
            'GLOW_PLUG'  : self._wc >= 1000,           # warm-up complete
        }

    # ── Checkpoint ────────────────────────────────────────────────────────────

    def save(self, path: str, max_connections: int = 500_000) -> None:
        """
        Save field state as JSON (v2.1).
        Vocab entries: [word, E, home_stratum, gen_stratum].
        Only non-ground β entries and top-K connections by weight are stored.
        """
        if not self._loaded:
            raise RuntimeError('Monad not loaded.')
        dirpart = os.path.dirname(path)
        if dirpart:
            os.makedirs(dirpart, exist_ok=True)
        top_A = sorted(self.A.items(), key=lambda kv: kv[1], reverse=True)
        ck = {
            'version'            : '2.1.0',
            'N'                  : self.N,
            'word_count'         : self._wc,
            'rejected_count'     : self.rejected_count,
            'emission_threshold' : self._emission_threshold,
            'beta'               : {str(k): v for k, v in self.beta.items()
                                    if v > self._ground * 1.001},
            'A'                  : {f'{k[0]},{k[1]}': v
                                    for k, v in top_A[:max_connections]},
            # vocab: [word, E, home_stratum, gen_stratum]
            'vocab'              : {str(k): list(v) for k, v in self.vocab.items()},
            'age'                : self._age,
        }
        with open(path, 'w') as f:
            json.dump(ck, f, separators=(',', ':'))
        print(f'[Monad] saved {len(ck["vocab"])} vocab  '
              f'{len(ck["A"])} connections → {path}')

    def _restore(self, path: str) -> None:
        with open(path) as f:
            ck = json.load(f)
        self._wc             = ck.get('word_count', 0)
        self.rejected_count  = ck.get('rejected_count', 0)
        self._emission_threshold = ck.get('emission_threshold', abs(L_GROUND) * 2.0)
        self.beta = {i: self._ground for i in range(self.N)}
        for k, v in ck.get('beta', {}).items():
            self.beta[int(k)] = v
        self.A = {}
        for k, v in ck.get('A', {}).items():
            i, j = map(int, k.split(','))
            self.A[(i, j)] = v
        self.vocab = {}
        for k, v in ck.get('vocab', {}).items():
            # v2.0 format: [word, E] — default stratums to NS_SIGMA_TEXT
            # v2.1 format: [word, E, home_stratum, gen_stratum]
            if len(v) >= 4:
                self.vocab[int(k)] = (v[0], v[1], int(v[2]), int(v[3]))
            else:
                self.vocab[int(k)] = (v[0], v[1], NS_SIGMA_TEXT, NS_SIGMA_TEXT)
        loaded_age = ck.get('age', None)
        if loaded_age and len(loaded_age) == self.N:
            self._age = [float(a) for a in loaded_age]
        else:
            self._age = [0.0] * self.N
        print(f'[Monad] restored {len(self.vocab)} vocab  '
              f'{len(self.A)} connections from {path}')

    def load_vocab(self, path: str) -> None:
        """
        Load only the vocab (Face layer) from a JSON checkpoint.

        β, A, age, and word_count are untouched — call load() first for the
        field state, then load_vocab() for the rendering layer:
            m.load('monad.json'); m.load_vocab('monad_wordnet.json')

        :param path: Path to a JSON checkpoint saved by save().
        :raises RuntimeError: If monad is not loaded.
        """
        if not self._loaded:
            raise RuntimeError('Monad not loaded — call load() first.')
        with open(path) as f:
            ck = json.load(f)
        self.vocab = {}
        for k, v in ck.get('vocab', {}).items():
            if len(v) >= 4:
                self.vocab[int(k)] = (v[0], v[1], int(v[2]), int(v[3]))
            else:
                self.vocab[int(k)] = (v[0], v[1], NS_SIGMA_TEXT, NS_SIGMA_TEXT)
        print(f'[Monad] vocab loaded from {path}  vocab={len(self.vocab)}')


# ── CLI verification ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Monad — H_hat_RB Field Engine  v1.212  (standalone)')
    print('=' * 60)

    m = Monad(N=1000, tau=5.0)
    m.load()
    print(f'Ground state  N={m.N}  ground={m._ground:.8f}  L={L_GROUND}')
    print(f'Zero[0]={m.zeros[0]:.6f}  Zero[19]={m.zeros[19]:.6f}  Zero[999]={m.zeros[999]:.4f}')

    m.learn('The dog chased the cat around the yard.')
    m.learn('The mind is the seat of reason and consciousness.')
    m.learn('Water flows downhill by the path of least resistance.')
    m.learn('The prime preexists the alphabet.')

    print(f'\nvocab={len(m.vocab)}  connections={len(m.A)}  rejected={m.rejected_count}')
    print(f'\n  speak("what chased")    → {m.speak("what chased")}')
    print(f'  speak("what is mind")   → {m.speak("what is mind")}')
    print(f'  speak("water flows")    → {m.speak("water flows")}')

    psi = m.hear('consciousness reason')
    print(f'\n  hear("consciousness reason") → {psi}')

    print(f'\n  lookup("water")  → {m.lookup("water")}')
    print(f'\n  bao_check()      → {m.bao_check()}')

    # Test: PEM guard
    m.learn('-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----')
    print(f'\n  [PEM guard: above learn() should have been refused]')

    # Test: learn_ex with code filetype
    m.learn_ex('def calculate_entropy(beta_values): return sum(v for v in beta_values)',
               NS_FT_CODE)
    print(f'  vocab after code learn_ex={len(m.vocab)}  rejected={m.rejected_count}')

    # Test: filetype_from_ext
    assert filetype_from_ext('notes.txt')   == NS_FT_PROSE
    assert filetype_from_ext('engine.py')   == NS_FT_CODE
    assert filetype_from_ext('index.html')  == NS_FT_MARKUP
    assert filetype_from_ext('thesis.pdf')  == NS_FT_DOC
    print('\n  filetype_from_ext: all assertions passed')

    # ── VAG-COM / OBD2 sensor layer ───────────────────────────────────────────
    print('\n[sensor layer]')
    print(f'  sedenion available : {_SEDENION_AVAILABLE}')
    rc = m.ready_check()
    print('  ready_check:')
    for k, v in rc.items():
        mark = 'READY' if v else 'NOT READY'
        print(f'    {k:<12} {mark}')

    dtcs = m.fault_scan()
    print(f'  MIL: {"ON" if m._mil else "off"}   DTCs: {dtcs if dtcs else "none"}')

    print('\n  OBD2 PIDs:')
    pid_names = {
        0x04: 'Engine Load %', 0x0C: 'RPM', 0x0E: 'Timing Advance °',
        0x0F: 'IAT °C', 0x11: 'Throttle %', 0x2F: 'Fuel Level %',
        0x2300: 'CKP γ_n', 0x2301: 'CMP dim', 0x2302: 'Conj γ_{N-n}',
        0x2303: 'Sed charge', 0x2304: 'Glow plug', 0x2305: 'Fermat prox',
        0x2307: 'J_Red', 0x2308: 'J_Blue', 0x2309: 'Noether ∂J',
    }
    for pid, name in pid_names.items():
        val = m.sensor_read(pid)
        print(f'    PID 0x{pid:04X}  {name:<20} = {val:.6f}')

    print()
    m.print_health()
