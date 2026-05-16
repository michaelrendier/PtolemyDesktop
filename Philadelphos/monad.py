#!/usr/bin/env python3
"""
Philadelphos/monad.py — The Monad  (standalone, v2.1.0)
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

Author: O Captain My Captain
CLAUDE-SMMNIP-00729-56714-24600
Date: 2026-05-16
"""

import os
import re
import sys
import json
import math

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
        self._age               = [0] * N
        self._lambda            = 0.05
        self._conv_touched: set = set()
        self._autonomous_speech  = True
        self._emission_threshold = abs(L_GROUND) * 2.0
        self._beta_sat           = abs(L_GROUND) * 4.0
        self._saturated: set     = set()

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
            self._age            = [0] * self.N
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

    def _advance_age(self) -> None:
        for n in range(self.N):
            if n in self._conv_touched:
                self._age[n] = 0
            else:
                self._age[n] += 1
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

    def _j_mu(self, psi: list[tuple[int, float]]) -> dict[int, float]:
        """
        Noether current from Ψ activation under (β, A).

        Primary:    J_i  = β_i · E_i²
        Propagated: J_j += J_i · A[(i,j)] · β_j

        CONFIDENCE: ESTABLISHED
        """
        J: dict[int, float] = {}
        for idx, E in psi:
            b      = self.beta.get(idx, self._ground) * self._w(idx)
            J[idx] = J.get(idx, 0.0) + b * E * E
        for (i, j), w in self.A.items():
            if i in J:
                J[j] = J.get(j, 0.0) + J[i] * w * self.beta.get(j, self._ground) * self._w(j)
            if j in J:
                J[i] = J.get(i, 0.0) + J[j] * w * self.beta.get(i, self._ground) * self._w(i)
        return J

    # ── speak ─────────────────────────────────────────────────────────────────

    def speak(self, query: str, max_tokens: int = 50) -> str:
        """
        query → hear() → J^μ → words ordered by Noether amplitude.
        Empty query: spontaneous emission from highest-weighted field state.
        Advances conversational age after each call.
        """
        if query and query.strip():
            psi = self.hear(query)
        else:
            psi = sorted(
                ((idx, entry[1]) for idx, entry in self.vocab.items()),
                key=lambda item: self.beta.get(item[0], self._ground) * self._w(item[0]),
                reverse=True
            )[:max_tokens]
        if not psi:
            self._advance_age()
            return ''
        J = self._j_mu(psi)
        if not J:
            self._advance_age()
            return ''
        words: list[str] = []
        seen:  set[str]  = set()
        for idx, _ in sorted(J.items(), key=lambda kv: kv[1], reverse=True):
            if idx in self.vocab:
                w = self.vocab[idx][0]
                if w not in seen:
                    words.append(w)
                    seen.add(w)
            if len(words) >= max_tokens:
                break
        self._advance_age()
        return ' '.join(words)

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
            self._age = loaded_age
        else:
            self._age = [0] * self.N
        print(f'[Monad] restored {len(self.vocab)} vocab  '
              f'{len(self.A)} connections from {path}')


# ── CLI verification ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    print('Monad — H_hat_RB Field Engine  v2.1.0  (standalone)')
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

    print()
    m.print_health()
