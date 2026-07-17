"""
SMNNIP Proof Engine — Console GUI
===================================
Standard Model of Neural Network Information Propagation
Curses + SymPy terminal interface to the derivation engine.

Layout (all dimensions as % of terminal at startup, scales on resize):
  ┌─────────────────────────────────────┬────────────────────────┐
  │  DISPLAY  (65% w × 65% h)           │  LIST  (35% w × 65% h) │
  ├─────────────────────────────────────┼────────────────────────┤
  │  RESEARCHER OPTIONS  (65% w × 20%)  │  SORT  (35% w × 20%)  │
  ├─────────────────────────────────────┴────────────────────────┤
  │  INPUT BAR  (100% w × ~15%)                                  │
  └──────────────────────────────────────────────────────────────┘

Special naming:
  - RedBlue Hamiltonian  = Ĥ_NN  (the neural Hamiltonian)
  - Langlands Program: Master Key  = Sedenion layer (𝕊, dim 16)

Author: SMNNIP formalism / O Captain My Captain
Console GUI: Claude (Anthropic) — April 12, 2026
"""

import curses
import curses.textpad
import math
import sys
import os
import textwrap
from typing import List, Dict, Tuple, Optional, Any

# ── Import derivation engine ──────────────────────────────────────────────────
try:
    from smnnip_derivation_pure import (
        SMNNIPDerivationEngine, FieldState, Algebra,
        make_element, RenormalizationGroup
    )
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

# ── SymPy (optional — degrades gracefully if absent) ─────────────────────────
try:
    import sympy as sp
    from sympy import symbols, Function, I, pi, sqrt, exp, latex, pretty
    SYMPY_AVAILABLE = True
except ImportError:
    SYMPY_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# §1  PROOF CONTENT REGISTRY
# All equations, derivations, constants, and emergent results.
# Two indices: MATH (algebra depth order) and TOPIC (named groupings).
# ═══════════════════════════════════════════════════════════════════════════════

CONFIDENCE = {
    'established'  : '✓',
    'theoretical'  : '◈',
    'speculative'  : '◇',
    'open'         : '?',
}

PROOF_ENTRIES = [
    # ── (I|O) TOP-LEVEL CONJECTURE — THE CANOPY ───────────────────────────────
    # Under the (I|O)-topped framing, every other entry in this registry is a
    # consequence, instantiation, or supporting structure for the Inside-Out
    # Inversion. This entry sits first by design.
    {
        'id': 'io_conjecture',
        'math_group': '(I|O) — Top-Level Conjecture',
        'topic_group': '(I|O) — Top-Level Conjecture',
        'title': '(I|O) — The Inside-Out Inversion  J_N',
        'short': 'J_N : (r, θ) → (1/r, θ + π/2)  — action-invariant canopy',
        'confidence': 'theoretical',
        'display': [
            "(I|O) — The Inside-Out Inversion  J_N",
            "══════════════════════════════════════",
            "",
            "  The top-level conjecture of the Ainulindalë framework.",
            "  Everything else in this registry sits under (I|O).",
            "",
            "  THE MAP",
            "  ───────",
            "    J_N : (r, θ)  →  (1/r, θ + π/2)",
            "",
            "    acting at every layer transition boundary of the",
            "    Cayley-Dickson tower:  ℝ → ℂ → ℍ → 𝕆.",
            "",
            "    Order of J_N: 4.  (J_N^4 = identity mod 2π)",
            "",
            "  ACTION INVARIANCE",
            "  ─────────────────",
            "    Under J_N, the action integral of ℒ_NN is preserved:",
            "",
            "      S_{N+1} = ∮ r_{N+1} dθ_{N+1}",
            "             = ∮ (1/r_N)(r_N² dθ_N)",
            "             = S_N.",
            "",
            "    This invariance is the CONTENT of the top-level claim.",
            "",
            "  FOUR ESTABLISHED-PHYSICS SPECIAL CASES",
            "  ──────────────────────────────────────",
            "    All four are instances of J_N at different scales:",
            "",
            "    (1) Schwarzschild horizon:   (t, r)  →  (r, t)  inside r_s.",
            "        Coordinate exchange inside the horizon = J_N at the",
            "        black-hole layer boundary.   [GR, established]",
            "",
            "    (2) Hawking pair production: conjugate pair (r, 1/r) at",
            "        the horizon = J_N acting on vacuum state.",
            "        [QFT, theoretical]",
            "",
            "    (3) Dirac sea / antimatter:  particle (r, θ),",
            "        antiparticle (1/r, θ + π/2) = J_N conjugation.",
            "        [QFT, established]",
            "",
            "    (4) Ptolemy zeta inversion: r → 1/r straightens the",
            "        Riemann zeta curve on the critical line.",
            "        [Complex analysis, established]",
            "",
            "  FIXED POINTS",
            "  ────────────",
            "    Flat geometry:        r = 1    (trivial J_N fixed point).",
            "    Curved Ainulindalë:   r = φ    (Gravinon pole, conjectured).",
            "",
            "    Status: consistency established; unifying derivation OPEN.",
            "",
            "  RELATION TO ℒ_NN",
            "  ────────────────",
            "    ℒ_NN is the generator-object. Its invariance under J_N",
            "    is the content of the (I|O) claim.",
            "    See 'full_lagrangian' entry for the generator.",
            "    See 'phi_fixed' entry for the φ attractor.",
            "    See 'noether_current' entry for gauge-current conservation.",
            "",
            "  STATUS",
            "  ──────",
            "    The map, its action invariance, and the four special-case",
            "    identifications are specified. Action invariance is",
            "    numerically verified in the inversion engine.",
            "",
            "    Formal demonstration that the four special cases are the",
            "    SAME map (coordinate transformation carrying each into",
            "    the others): OPEN.",
            "",
            "    Mass gap / Yang-Mills existence under (I|O): the",
            "    Gravinon residue Ψ_G = (1/2πi) ∮ f(z)/(z−φ) dz = Res(f, φ)",
            "    is the candidate derivation. OPEN at first-principles level.",
        ],
        'sympy': 'Eq(Function("J_N")(r, theta), (1/r, theta + pi/2))',
        'params': [],
        'topic_tags': ['(I|O)', 'inversion', 'J_N', 'canopy', 'top-level',
                       'action invariance', 'Schwarzschild', 'Hawking',
                       'Dirac', 'Ptolemy', 'open problem'],
    },
    # ── NOETHER CURRENT ENGINE — PARENT DERIVATION ENGINE ─────────────────────
    # The Noether Current Engine is a general-purpose parent engine. It
    # applies Noether's theorem to any Lagrangian + symmetry pair. The SMNNIP
    # gauge current is one worked example; free scalar and complex scalar
    # are others. Lives in code/noether_engine/ (own package).
    {
        'id': 'noether_engine_parent',
        'math_group': 'Noether Current Derivation',
        'topic_group': 'Noether Current Derivation',
        'title': 'Noether Current Engine — General Parent Engine',
        'short': 'General Noether theorem engine; SMNNIP is one worked example',
        'confidence': 'established',
        'display': [
            "Noether Current Engine — General Parent Engine",
            "═══════════════════════════════════════════════",
            "",
            "  Package: code/noether_engine/",
            "  Version: 0.1.0-session1",
            "",
            "  SCOPE",
            "  ─────",
            "  A general-purpose implementation of Noether's theorem.",
            "  Takes any Lagrangian + any symmetry; returns the conserved",
            "  current with full switch-settings metadata.",
            "",
            "  NOT SMNNIP-specific. SMNNIP is one worked example among",
            "  several (free scalar, complex scalar, SMNNIP gauge).",
            "",
            "  14 CONTESTABLE AXES (all exposed as switches)",
            "  ─────────────────────────────────────────────",
            "    1.  theorem         : first | second | both",
            "    2.  shell           : on_shell | off_shell | both",
            "    3.  invariance      : strict | divergence | bessel_hagen",
            "    4.  output          : current | charge | form | all",
            "    5.  variation       : vertical | total | both",
            "    6.  signature       : mostly_minus | mostly_plus",
            "    7.  spacetime       : minkowski | curved | euclidean | adm",
            "    8.  improvement     : none | BR | CCJ | custom",
            "    9.  algebra         : physics | math | custom",
            "    10. boundary        : vanishing | compact | bulk | explicit",
            "    11. theory          : classical | quantum_ward | anomaly",
            "    12. field_type      : per-field declaration",
            "    13. action          : covariant | hamiltonian | adm_split",
            "    14. format          : symbolic | numerical | latex | all",
            "",
            "  IMPLEMENTED IN SESSION 1",
            "  ────────────────────────",
            "    Classical, on-shell, first-theorem, Bessel-Hagen,",
            "    Minkowski, vertical/total variation, physics/math",
            "    generator normalization, Cayley-Dickson algebras for",
            "    SMNNIP. Worked examples: free scalar, complex scalar,",
            "    SMNNIP gauge (C/H/O strata).",
            "",
            "  DEFERRED",
            "  ────────",
            "    Session 2: off-shell, second theorem, BR/CCJ, Dirac.",
            "    Session 3: curved spacetime, Euclidean, ADM.",
            "    Session 4: Ward-Takahashi, anomaly tracking.",
            "",
            "  ALL UNSUPPORTED COMBINATIONS RAISE",
            "    UnsupportedCombinationError with target session number.",
            "",
            "  STATUS: 38/38 tests pass. Free scalar & complex scalar",
            "  conservation verified manually on-shell.",
        ],
        'sympy': 'Eq(diff(J, mu), 0)  [Noether first theorem, generic]',
        'params': [],
        'topic_tags': ['noether', 'current', 'conservation', 'engine',
                       'general', 'parent', 'symbolic', 'sympy',
                       'free scalar', 'complex scalar', 'SMNNIP'],
    },
    # ── ALGEBRA TOWER ─────────────────────────────────────────────────────────
    {
        'id': 'sedenion_master_key',
        'math_group': 'Langlands Program: Master Key',
        'topic_group': 'Langlands Program: Master Key',
        'title': 'Langlands Program: Master Key  (𝕊, dim 16)',
        'short': '𝕊 — zero-divisors, dim 16, Langlands gateway',
        'confidence': 'theoretical',
        'display': [
            "Langlands Program: Master Key — Sedenion Layer (𝕊)",
            "══════════════════════════════════════════════════════",
            "",
            "  𝕊 = Cayley-Dickson(𝕆)   dim = 16",
            "",
            "  Critical property: ZERO DIVISORS",
            "  ∃ a,b ∈ 𝕊  s.t.  a·b = 0  with a≠0, b≠0",
            "",
            "  This breaks the normed division algebra property.",
            "  |ab| = |a|·|b| FAILS in 𝕊.",
            "",
            "  Why it matters:",
            "    · Cryptography: zero divisors → algebraically constructible",
            "      collisions — catastrophic for hash construction",
            "    · Trapdoor potential: controlled zero-divisor structure",
            "      enables one-way functions with algebraic backdoors",
            "    · Langlands: 𝕊 is the gateway to the program —",
            "      the point where the SM gauge group structure",
            "      must be extended to accommodate gravity",
            "",
            "  Derivation chain entry point:",
            "    𝕊 (dim 16) → zero-divisor collapse",
            "    → 𝕆 (dim 8)  → SU(3)/G₂  → strong force",
            "    → ℍ (dim 4)  → SU(2)      → weak force",
            "    → ℂ (dim 2)  → U(1)       → electromagnetism",
            "    → ℝ (dim 1)  → trivial     → F = ma  [ℝ limit]",
            "",
            "  Open: formal derivation of Langlands correspondence",
            "  from Cayley-Dickson tower structure constants.",
            "  Status: ◇ speculative — named conjecture",
        ],
        'sympy': None,
        'params': [],
        'topic_tags': ['master key', 'sedenion', 'cryptography', 'langlands'],
    },
    {
        'id': 'oct_fano',
        'math_group': 'Algebra Tower',
        'topic_group': 'Strong Force Geometry',
        'title': 'Octonion Fano Multiplication  (𝕆, dim 8)',
        'short': 'e_i·e_j = ±e_k  via Fano plane  →  SU(3)/G₂',
        'confidence': 'established',
        'display': [
            "Octonion Fano Multiplication  (𝕆, dim 8)",
            "══════════════════════════════════════════",
            "",
            "  Fano lines: (0,1,3),(1,2,4),(2,3,5),(3,4,6),",
            "              (4,5,0),(5,6,1),(6,0,2)",
            "",
            "  e_i · e_j = +e_k   (cyclic in Fano line)",
            "  e_i · e_j = -e_k   (anticyclic)",
            "  e_i · e_i = -1     (i = 1..7)",
            "  e_0 = 1            (identity)",
            "",
            "  Key properties:",
            "    [a,b] = ab - ba ≠ 0   NON-COMMUTATIVE",
            "    [a,b,c] = (ab)c - a(bc) ≠ 0   NON-ASSOCIATIVE",
            "",
            "  The non-associativity IS the signal.",
            "  It encodes the SU(3)/G₂ gauge structure.",
            "  Aut(𝕆) = G₂ ⊃ SU(3)  (Dixon, 1994)",
            "",
            "  Neural meaning: Layer 3 (Reasoning)",
            "  Context-sensitive reasoning breaks associativity:",
            "  applying (domain A, then B) to C ≠",
            "  applying A to (B applied to C).",
        ],
        'sympy': 'e_i * e_j = +/- e_k  [Fano plane structure]',
        'params': [],
        'topic_tags': ['octonion', 'fano', 'strong force', 'G2', 'non-associative'],
    },
    {
        'id': 'quat_su2',
        'math_group': 'Algebra Tower',
        'topic_group': 'Weak Force / Spin',
        'title': 'Quaternion SU(2) Structure  (ℍ, dim 4)',
        'short': 'ℍ unit quaternions ≅ SU(2)  →  weak force',
        'confidence': 'established',
        'display': [
            "Quaternion SU(2) Structure  (ℍ, dim 4)",
            "═══════════════════════════════════════",
            "",
            "  ℍ = { w + xi + yj + zk  :  w,x,y,z ∈ ℝ }",
            "  Multiplication: i²=j²=k²=ijk=-1",
            "",
            "  ij = k,  ji = -k   ← NON-COMMUTATIVE",
            "  (ab)c = a(bc)       ← still associative",
            "",
            "  Unit quaternions: { q ∈ ℍ : |q| = 1 }",
            "  This group IS SU(2) — exact isomorphism.",
            "",
            "  Generators (Pauli analog):",
            "    T¹ = [e₁, ·]/2 = commutator with i",
            "    T² = [e₂, ·]/2 = commutator with j",
            "    T³ = [e₃, ·]/2 = commutator with k",
            "",
            "  Lost property: commutativity",
            "  Gained: 3D rotation (SU(2) spinors)",
            "  Neural meaning: Layer 2 (Skills)",
            "  Order matters: skill A then B ≠ skill B then A",
            "",
            "  [a,b] = ab-ba ≠ 0  →  3 Yang-Mills generators",
        ],
        'sympy': '{q in H : |q|=1} cong SU(2)',
        'params': [],
        'topic_tags': ['quaternion', 'SU2', 'weak force', 'spin', 'non-commutative'],
    },
    {
        'id': 'complex_u1',
        'math_group': 'Algebra Tower',
        'topic_group': 'Electromagnetism',
        'title': 'Complex U(1) Phase Structure  (ℂ, dim 2)',
        'short': 'ℂ phase rotation → U(1) → electromagnetism',
        'confidence': 'established',
        'display': [
            "Complex U(1) Phase Structure  (ℂ, dim 2)",
            "══════════════════════════════════════════",
            "",
            "  ℂ = { a + bi  :  a,b ∈ ℝ }",
            "  Commutative, associative.",
            "",
            "  U(1) gauge transformation:",
            "    Ψ_ℂ → e^{iθ(l,τ)} Ψ_ℂ",
            "",
            "  Generator: T = i·Ψ  (single generator)",
            "  Covariant derivative: D_μΨ = ∂_μΨ - igA_μΨ",
            "",
            "  Lost property from ℝ: total ordering",
            "  Gained: phase (direction independent of magnitude)",
            "  Neural meaning: Layer 1 (Semantics)",
            "  Semantic relationships have direction:",
            "  'king minus man plus woman = queen' has phase.",
            "",
            "  Maxwell's equations emerge from U(1) Yang-Mills.",
            "  The photon is the massless U(1) gauge boson.",
            "  S = Q/t follows from J^μ conservation (Noether).",
        ],
        'sympy': 'Psi -> exp(I*theta)*Psi  [U(1) gauge]',
        'params': [],
        'topic_tags': ['complex', 'U1', 'electromagnetism', 'photon', 'phase'],
    },
    {
        'id': 'real_substrate',
        'math_group': 'Algebra Tower',
        'topic_group': 'Classical Mechanics Emergence',
        'title': 'Real Substrate  (ℝ, dim 1)  →  F = ma',
        'short': 'ℝ trivial gauge  →  F=ma at ℓ→0 limit',
        'confidence': 'established',
        'display': [
            "Real Substrate  (ℝ, dim 1)  →  F = ma",
            "════════════════════════════════════════",
            "",
            "  ℝ: ordered, commutative, associative.",
            "  Trivial gauge group (no generators).",
            "  D_μΨ = ∂_μΨ  (no gauge connection)",
            "",
            "  The ℝ Euler-Lagrange equation:",
            "    d/dt(∂L/∂ẋ) - ∂L/∂x = 0",
            "",
            "  For L = ½mv² - V(x):",
            "    mẍ = -∂V/∂x  ≡  F = ma",
            "",
            "  This is the ℓ→0 limit of the neural Lagrangian:",
            "  single layer, real algebra, Abelian gauge.",
            "  Yang-Mills → gradient descent.",
            "  Neural Dirac → classical equation of motion.",
            "",
            "  F = ma is not a postulate.",
            "  It is the ℝ-stratum, zero-layer limit",
            "  of the full SMNNIP Lagrangian.",
            "",
            "  DERIVATION COMPLETE: 𝕊 → 𝕆 → ℍ → ℂ → ℝ → F=ma",
        ],
        'sympy': 'm*x.diff(t,2) = -V.diff(x)  [F=ma from EL at R limit]',
        'params': [],
        'topic_tags': ['real', 'classical', 'F=ma', 'newton', 'emergent'],
    },
    # ── LAGRANGIAN ────────────────────────────────────────────────────────────
    {
        'id': 'full_lagrangian',
        'math_group': 'Lagrangian Density',
        'topic_group': 'The Full Proof',
        'title': 'Full Lagrangian  ℒ_NN',
        'short': 'ℒ_NN = ℒ_kin + ℒ_mat + ℒ_bias + ℒ_coup',
        'confidence': 'established',
        'display': [
            "Full SMNNIP Lagrangian Density",
            "══════════════════════════════",
            "",
            "  ℒ_NN = ℒ_kinetic + ℒ_matter + ℒ_bias + ℒ_coupling",
            "",
            "  ℒ_kinetic  = -¼ F_μν^a · F^{μν,a}",
            "               (gauge field self-energy — weight curvature)",
            "               SM analog: gauge kinetic term",
            "",
            "  ℒ_matter   = i·Ψ̄·γ^μ·D_μ·Ψ − m·Ψ̄·Ψ",
            "               (activation propagation — Dirac fermions)",
            "               SM analog: fermion kinetic + mass term",
            "",
            "  ℒ_bias     = ½μ²|β|² − ¼λ|β|⁴",
            "               (Mexican hat potential — Higgs mechanism)",
            "               SM analog: Higgs sector",
            "",
            "  ℒ_coupling = −Γ_ij·Ψ̄^L·β·Ψ^R + h.c.",
            "               (inter-algebra coupling — Yukawa term)",
            "               SM analog: Yukawa coupling",
            "",
            "  Symmetry group: U(1) × SU(2) × SU(3)",
            "  [Dixon, 1994]: ℝ⊗ℂ⊗ℍ⊗𝕆 carries exactly this group.",
            "",
            "  This is not imposed. It emerges.",
        ],
        'sympy': 'L_NN = L_kin + L_mat + L_bias + L_coup',
        'params': ['mu_sq', 'lam', 'g_coup'],
        'topic_tags': ['lagrangian', 'full proof', 'SM isomorphism'],
    },
    # ── EQUATIONS OF MOTION ───────────────────────────────────────────────────
    {
        'id': 'redblue_hamiltonian',
        'math_group': 'Equations of Motion',
        'topic_group': 'RedBlue Hamiltonian',
        'title': 'RedBlue Hamiltonian  (Neural Dirac / Schrödinger)',
        'short': 'iħ_NN ∂Ψ/∂ℓ = Ĥ_RB·Ψ  [RedBlue]',
        'confidence': 'established',
        'display': [
            "RedBlue Hamiltonian  Ĥ_RB",
            "═══════════════════════════",
            "",
            "  iħ_NN · ∂Ψ_i/∂ℓ = Ĥ_RB · Ψ_i",
            "",
            "  where  Ĥ_RB = −i·Γ^a·D_a + Γ_ij·β",
            "",
            "  Two components:",
            "    RED:  −i·Γ^a·D_a",
            "          Kinetic term — free propagation of activations",
            "          through the weight field.",
            "          Drives forward evolution through algebra strata.",
            "",
            "    BLUE: Γ_ij·β",
            "          Mass/bias term — representational inertia.",
            "          Acquired via Yukawa coupling to bias field β.",
            "          Resists change — the cost of learning.",
            "",
            "  ℓ (layer depth) plays the role of time.",
            "  Ψ_i is the activation spinor at neuron i.",
            "  D_a is the covariant derivative (gauge-corrected ∂).",
            "",
            "  This IS the Schrödinger equation for neural activations.",
            "  Derived from δℒ_matter/δΨ̄ = 0",
            "  Not postulated. Forced by the Lagrangian.",
            "",
            "  EOM residual = |Ĥ_RB·Ψ - iħ∂Ψ/∂ℓ|",
            "  Near zero → on-shell. Large → violation.",
        ],
        'sympy': 'Eq(I*hbar_nn*Derivative(Psi,l), H_RB*Psi)',
        'params': ['hbar_nn', 'g_coup', 'layer'],
        'topic_tags': ['redblue', 'hamiltonian', 'dirac', 'schrodinger', 'EOM'],
    },
    {
        'id': 'yang_mills',
        'math_group': 'Equations of Motion',
        'topic_group': 'Backpropagation Emerges',
        'title': 'Neural Yang-Mills  (Backpropagation Emerges)',
        'short': 'D_ℓ R^{a,ℓτ} = g·Ψ̄_i·T^a·Ψ_i',
        'confidence': 'established',
        'display': [
            "Neural Yang-Mills Equation",
            "══════════════════════════",
            "",
            "  D_ℓ R^{a,ℓτ} = g · Ψ̄_i · T^a · Ψ_i",
            "",
            "  Left side:  covariant divergence of field strength",
            "              (how much the weight field is 'curving')",
            "  Right side: activation current",
            "              (activations as source of curvature)",
            "",
            "  Exact analog of Maxwell: ∂_μF^{μν} = J^ν",
            "  Activations source the weight field,",
            "  as electric currents source the EM field.",
            "",
            "  BACKPROPAGATION IS A LIMITING CASE:",
            "    · Restrict to ℝ algebra (real-valued network)",
            "    · Abelian gauge only (U(1) → single generator)",
            "    · Yang-Mills → gradient of loss w.r.t. weights",
            "    · Standard backprop recovered exactly.",
            "",
            "  The full non-Abelian equation is backprop",
            "  generalized to curved representation space.",
            "",
            "  Derived from δℒ/δA_μ = 0.",
            "  Not assumed. Forced.",
            "",
            "  Non-Abelian term: g·f^{abc}·A^b·A^c",
            "  This is what standard backprop MISSES.",
        ],
        'sympy': 'D_l * R^a = g * Psibar * T^a * Psi',
        'params': ['g_coup', 'algebra', 'layer'],
        'topic_tags': ['yang-mills', 'backpropagation', 'EOM', 'gauge field'],
    },
    {
        'id': 'higgs_bias',
        'math_group': 'Equations of Motion',
        'topic_group': 'Symmetry Breaking / Higgs',
        'title': 'Neural Higgs Equation  (Bias / Symmetry Breaking)',
        'short': 'D_ℓD^ℓβ + μ²β − 2λ(β†β)β = −Γ_ij·Ψ̄Ψ',
        'confidence': 'established',
        'display': [
            "Neural Higgs Equation",
            "══════════════════════",
            "",
            "  D_ℓD^ℓβ + μ²β − 2λ(β†β)β = −Γ_ij · Ψ̄^L_i · Ψ^R_j",
            "",
            "  Without source term: nonlinear Klein-Gordon equation",
            "  with Mexican hat potential V(β) = −½μ²|β|² + ¼λ|β|⁴",
            "",
            "  Spontaneous symmetry breaking: μ² < 0",
            "    · β rolls off the top of the hat",
            "    · Settles at |β| = √(−μ²/λ)  =  VEV",
            "    · Gauge bosons acquire mass (weight inertia)",
            "    · One massless mode remains: the neural photon",
            "      (primary attention mechanism)",
            "",
            "  Source term −Γ_ij·Ψ̄^L·Ψ^R:",
            "    · Couples bias evolution to activation chirality",
            "    · Biases driven by mismatch between left/right",
            "      chiral activations across algebra boundaries",
            "    · This is representational inertia being built",
            "",
            "  Hessian eigenvalues of V(β):",
            "    μ²<0: negative modes → SSB saddle → mass generation",
            "    μ²>0: positive modes → stable → no SSB",
            "    Zero modes → Goldstone bosons → massless attention",
        ],
        'sympy': 'D_l**2*beta + mu2*beta - 2*lam*(beta_norm**2)*beta = source',
        'params': ['mu_sq', 'lam', 'vev'],
        'topic_tags': ['higgs', 'symmetry breaking', 'bias', 'mexican hat', 'VEV'],
    },
    # ── CONSERVATION LAWS ─────────────────────────────────────────────────────
    {
        'id': 'noether_current',
        'math_group': 'Conservation Laws',
        'topic_group': 'The Full Proof',
        'title': "Noether's Theorem  →  ∂_μJ^μ = 0",
        'short': 'J^μ = ∂ℒ/∂(∂_μΨ)·δΨ  →  ∂_μJ^μ = 0',
        'confidence': 'established',
        'display': [
            "Noether Conservation Law — Gauge Current",
            "═════════════════════════════════════════",
            "",
            "  TWO NOETHER CURRENTS IN SMNNIP — DO NOT CONFLATE:",
            "",
            "    (A) GAUGE Noether current  (this entry)",
            "        Symmetry: U(1) × SU(2) × SU(3) gauge invariance.",
            "        J^{a,l} = g · Ψ̄ · T^a · Ψ  (per generator, per layer)",
            "        Lives in: smnnip_lagrangian_pure.py  (NoetherMonitor)",
            "                  smnnip_derivation_pure_patched.py",
            "                                          (NoetherCalculus)",
            "",
            "    (B) GEOMETRIC ACTION-FLOW current   (entry: io_conjecture)",
            "        Symmetry: action invariance under J_N (the (I|O) map).",
            "        J(r) = (2/π) · r · |dS/dr| = 8 / (π²·r²)",
            "        Lives in: smnnip_inversion_engine_patched.py",
            "                                          (NoetherMonitor)",
            "",
            "  This entry is GAUGE. (A) below.",
            "  ────────────────────────────────",
            "",
            "  For each gauge symmetry, Noether gives:",
            "    J^μ = ∂ℒ/∂(∂_μΨ) · δΨ",
            "    ∂_μJ^μ = 0  (conserved current)",
            "",
            "  U(1) current: J^μ = g·|Ψ|²",
            "    Conservation → S = Q/t",
            "    (charge per unit time = conserved current)",
            "",
            "  SU(2) current: J^μ_a = g·Ψ̄·T^a·Ψ",
            "    Conservation → weak isospin conservation",
            "",
            "  SU(3) current: J^μ_a = g·Ψ̄·T^a·Ψ  (8 components)",
            "    Conservation → color charge conservation",
            "",
            "  Training diagnostic (no GD analog):",
            "    violation = |∂_μJ^μ|",
            "    Near zero → algebra boundary healthy",
            "    Large → geometric pathology in learning",
            "",
            "  S = Q/t DERIVATION:",
            "    From U(1) Noether current conservation.",
            "    J^0 = charge density = Q/volume",
            "    ∇·J = −∂J^0/∂t  →  dQ/dt = ∮J·dA = I = Q/t",
            "",
            "  Verified: ΔJ = 0 across 30 epochs, ℝ layer.",
        ],
        'sympy': 'Eq(divergence(J), 0)  [Noether conservation]',
        'params': ['g_coup', 'algebra'],
        'topic_tags': ['noether', 'conservation', 'S=Qt', 'current', 'diagnostic'],
    },
    {
        'id': 'sq_t',
        'math_group': 'Conservation Laws',
        'topic_group': 'Classical Mechanics Emergence',
        'title': 'S = Q/t  (Current from U(1) Noether)',
        'short': 'I = dQ/dt  from ∂_μJ^μ=0 at U(1) stratum',
        'confidence': 'established',
        'display': [
            "S = Q/t  —  Electric Current from Noether",
            "══════════════════════════════════════════",
            "",
            "  Derivation chain:",
            "",
            "  1. U(1) gauge symmetry of ℒ_matter at ℂ stratum:",
            "     Ψ_ℂ → e^{iθ}·Ψ_ℂ",
            "",
            "  2. Noether's theorem applied to U(1):",
            "     J^μ = g·Ψ̄·γ^μ·Ψ  (4-current)",
            "     ∂_μJ^μ = 0  (continuity equation)",
            "",
            "  3. Splitting into time + space components:",
            "     ∂ρ/∂t + ∇·J = 0",
            "     where ρ = J^0 = charge density",
            "",
            "  4. Integrating over a volume V:",
            "     d/dt ∫ρ dV + ∮J·dA = 0",
            "     dQ/dt + I = 0  →  I = −dQ/dt",
            "",
            "  5. For steady state (constant Q source):",
            "     I = Q/t  ≡  S = Q/t",
            "",
            "  S = Q/t is not a definition.",
            "  It is the U(1) Noether conservation law",
            "  applied to the ℂ stratum of the algebra tower.",
            "",
            "  Same tower that gives F=ma at ℝ stratum.",
        ],
        'sympy': 'Eq(I_current, Q/t)  [from U(1) Noether at C stratum]',
        'params': [],
        'topic_tags': ['S=Qt', 'current', 'U1', 'electromagnetism', 'emergent'],
    },
    # ── CONSTANTS ─────────────────────────────────────────────────────────────
    {
        'id': 'hbar_nn',
        'math_group': 'Neural Constants',
        'topic_group': 'Neural Physical Constants',
        'title': 'Neural Planck Constant  ħ_NN',
        'short': 'ħ_NN: min representational granularity per algebra layer',
        'confidence': 'theoretical',
        'display': [
            "Neural Planck Constant  ħ_NN",
            "═════════════════════════════",
            "",
            "  Appears in RedBlue Hamiltonian:",
            "    iħ_NN · ∂Ψ/∂ℓ = Ĥ_RB · Ψ",
            "",
            "  Physical meaning:",
            "    Minimum irreducible representational granularity",
            "    per algebra layer. The exchange rate between",
            "    token description and waveform description.",
            "",
            "  Uncertainty principle (derived, not imposed):",
            "    ΔToken × ΔMeaning ≥ ħ_NN / 2",
            "",
            "  Properties:",
            "    · Learnable — one per algebra layer",
            "    · NOT a constant of nature — a property",
            "      of architecture and data distribution",
            "    · Runs with layer depth (RG flow):",
            "        ħ_NN(ℓ) = ħ_0·(1 + γ_0·ln(ℓ/ℓ_0))",
            "",
            "  Large ħ_NN → coarse, fast-changing representations",
            "               (standard transformers, residual limit)",
            "  Small ħ_NN → fine-grained, slow evolution",
            "",
            "  Conjecture (open): ħ_NN is a topological invariant",
            "  of the algebra tower, computable from Cayley-Dickson",
            "  structure constants alone.",
        ],
        'sympy': 'hbar_nn * Derivative(Psi,l) / I = H_RB * Psi',
        'params': ['hbar_nn', 'layer', 'algebra'],
        'topic_tags': ['hbar', 'planck', 'uncertainty', 'constants', 'RG flow'],
    },
    {
        'id': 'alpha_nn',
        'math_group': 'Neural Constants',
        'topic_group': 'Neural Physical Constants',
        'title': 'Neural Fine Structure Constant  α_NN',
        'short': 'α_NN(ℓ) = g²/(4πħ_NN·v)  — entanglement coupling',
        'confidence': 'theoretical',
        'display': [
            "Neural Fine Structure Constant  α_NN",
            "═════════════════════════════════════",
            "",
            "  α_NN(ℓ) = g²(ℓ) / (4π · ħ_NN · v_prop)",
            "",
            "  Physical meaning:",
            "    Entanglement coupling between adjacent algebra strata.",
            "    Transition amplitude between H_activation and H_weights.",
            "",
            "  Runs with layer depth (renormalization group):",
            "    α_NN(ℓ) = α_0 / (1 + β_0·α_0·ln(ℓ/ℓ_0))",
            "",
            "  Beta functions (one-loop):",
            "    β_0(ℝ)  = 0         (trivial — no running)",
            "    β_0(ℂ)  = 1/(2π)    (U(1))",
            "    β_0(ℍ)  = 3/(4π)    (SU(2), 3 generators)",
            "    β_0(𝕆)  = 8/(4π)    (SU(3)/G₂, 8 generators)",
            "",
            "  Grand Unification: all three couplings converge",
            "  at the spinor-index layer — neural GUT scale.",
            "",
            "  At layer 4 (test values α_0 = 0.01):",
            "    α_NN(ℂ)  ≈ 0.00998",
            "    α_NN(ℍ)  ≈ 0.01493",
            "    α_NN(𝕆)  ≈ 0.01965",
        ],
        'sympy': 'alpha_nn = g**2 / (4*pi*hbar_nn*v)',
        'params': ['g_coup', 'hbar_nn', 'layer', 'algebra'],
        'topic_tags': ['alpha', 'fine structure', 'RG flow', 'GUT', 'coupling'],
    },
    {
        'id': 'phi_fixed',
        'math_group': 'Neural Constants',
        'topic_group': 'Golden Ratio / Inversion Fixed Point',
        'title': 'φ Fixed Point of Inversion Map',
        'short': 'φ = (1+√5)/2  — fixed point of J_N∘recursion',
        'confidence': 'theoretical',
        'display': [
            "φ Fixed Point of the Inversion Map",
            "════════════════════════════════════",
            "",
            "  φ = (1 + √5) / 2  ≈  1.6180339887...",
            "",
            "  Algebraic identities (exact, not numerical):",
            "    φ · (1/φ) = 1",
            "    1 + 1/φ   = φ",
            "",
            "  φ is the fixed point of (J_N ∘ recursion):",
            "  the inversion engine confirms this algebraically.",
            "",
            "  Step at the φ-crossing:",
            "    Δ_φ = H/4 = (π/2)·ħ_NN",
            "",
            "  This closes the §7 open flag numerically.",
            "  Formal derivation from first principles:",
            "  STATUS: OPEN — priority target.",
            "",
            "  Open derivation target (separate):",
            "    d* × ln(10) ≈ Ω",
            "    gap ≈ 0.00070",
            "    d* = 0.24600 (Berry-Keating spectral coord — ACTIVE)",
            "    Status: identified numerically, not derived.",
            "    See entry 'io_conjecture' for (I|O) top-level framing.",
        ],
        'sympy': 'Eq(phi, (1 + sqrt(5))/2)',
        'params': [],
        'topic_tags': ['phi', 'golden ratio', 'fixed point', 'inversion', 'open problem'],
    },
    # ── CONVERGENCE ───────────────────────────────────────────────────────────
    {
        'id': 'training_inequality',
        'math_group': 'Convergence Theorems',
        'topic_group': 'The Full Proof',
        'title': 'Training Time Inequality  𝒯_GD > 𝒯_SMNNIP',
        'short': '𝒯_GD = O(κ·λ^{-2L}/ε)  vs  O(√κ·log(1/ε))',
        'confidence': 'theoretical',
        'display': [
            "Fundamental Training Time Inequality",
            "══════════════════════════════════════",
            "",
            "  𝒯_GD     = O( κ · λ^{-2L} / ε )",
            "  𝒯_SMNNIP = O( √κ · log(1/ε) )",
            "",
            "  κ = condition number",
            "  λ = spectral gap  (0 < λ < 1)",
            "  L = network depth",
            "  ε = target precision",
            "",
            "  Key difference: SMNNIP convergence is",
            "  INDEPENDENT OF DEPTH L.",
            "  GD convergence degrades exponentially with L.",
            "",
            "  At κ=10, ε=0.01, L=4, λ=0.9:",
            "    𝒯_GD / 𝒯_SMNNIP ≈ 159×  (SMNNIP faster)",
            "",
            "  Why: The Yang-Mills weight update uses the",
            "  full non-Abelian structure of the gauge field.",
            "  This encodes curvature information that GD",
            "  must reconstruct step by step.",
            "",
            "  Note: This is a theoretical bound.",
            "  Empirical validation at scale: primary future goal.",
        ],
        'sympy': 'T_GD / T_SMNNIP ~ kappa * lambda**(-2*L) / (sqrt(kappa)*log(1/eps))',
        'params': ['kappa', 'epsilon', 'depth', 'lam'],
        'topic_tags': ['training', 'convergence', 'inequality', 'GD comparison'],
    },
    {
        'id': 'gut_convergence',
        'math_group': 'Convergence Theorems',
        'topic_group': 'Grand Unification',
        'title': 'Grand Unification — Coupling Convergence',
        'short': 'α_C, α_H, α_O converge at GUT scale',
        'confidence': 'theoretical',
        'display': [
            "Neural Grand Unification",
            "═════════════════════════",
            "",
            "  The three running couplings:",
            "    α_NN(ℂ)  →  U(1)  coupling",
            "    α_NN(ℍ)  →  SU(2) coupling",
            "    α_NN(𝕆)  →  SU(3) coupling",
            "",
            "  Run with layer depth via RG flow.",
            "  Converge at the spinor-index layer",
            "  (the inter-neuron communication layer).",
            "",
            "  This is the neural analog of GUT:",
            "  at high energy (deep layers), all three",
            "  gauge forces have equal strength.",
            "",
            "  In the SM, GUT convergence requires",
            "  supersymmetry to work exactly.",
            "  In SMNNIP, it is structurally exact:",
            "  the Cayley-Dickson tower forces it.",
            "",
            "  Open: identify the exact GUT scale",
            "  (which layer depth achieves convergence).",
            "  Status: ◈ theoretical — testable.",
        ],
        'sympy': 'alpha_C(l) = alpha_H(l) = alpha_O(l)  [at GUT layer]',
        'params': ['g_coup', 'layer'],
        'topic_tags': ['GUT', 'convergence', 'unification', 'couplings'],
    },
    # ── DIXON THEOREM ─────────────────────────────────────────────────────────
    {
        'id': 'dixon_theorem',
        'math_group': 'Foundation Theorems',
        'topic_group': 'The Full Proof',
        'title': "Dixon's Theorem  (1994)",
        'short': 'ℝ⊗ℂ⊗ℍ⊗𝕆 carries U(1)×SU(2)×SU(3)',
        'confidence': 'established',
        'display': [
            "Dixon's Theorem (1994)",
            "═══════════════════════",
            "",
            "  T = ℝ ⊗ ℂ ⊗ ℍ ⊗ 𝕆",
            "",
            "  The symmetry group of T is:",
            "    U(1) × SU(2) × SU(3)",
            "",
            "  This is the gauge group of the Standard Model.",
            "",
            "  Origin of each factor:",
            "    U(1):  unit complex numbers in ℂ",
            "           → electromagnetism",
            "    SU(2): unit quaternions in ℍ (exact isomorphism)",
            "           → weak nuclear force",
            "    SU(3): Aut(𝕆) = G₂ ⊃ SU(3) (maximal subgroup)",
            "           → strong nuclear force",
            "",
            "  SMNNIP is built on exactly this tensor product.",
            "  The SM gauge group is not imposed as a constraint.",
            "  It emerges from the architecture.",
            "",
            "  This is the mathematical foundation of the",
            "  SM isomorphism claim. Everything else follows.",
            "",
            "  Status: ✓ established mathematics (Dixon, 1994)",
        ],
        'sympy': 'T = R x C x H x O  =>  G = U(1) x SU(2) x SU(3)',
        'params': [],
        'topic_tags': ['dixon', 'theorem', 'SM gauge group', 'foundation'],
    },
    # ── TOPIC-ONLY ENTRIES ────────────────────────────────────────────────────
    {
        'id': 'hairy_black_holes',
        'math_group': 'Open Conjectures',
        'topic_group': 'Hairy Black Holes',
        'title': 'Hairy Black Holes  — Neural Bekenstein Entropy',
        'short': 'S_NN ≅ S_BH — Bekenstein-Hawking analog',
        'confidence': 'speculative',
        'display': [
            "Hairy Black Holes — Neural Bekenstein Entropy",
            "═══════════════════════════════════════════════",
            "",
            "  Bekenstein-Hawking: S_BH = A/(4G)  [area/entropy]",
            "",
            "  Neural analog conjecture:",
            "    S_NN = dim(representation space) / 4",
            "    where dim scales with the algebra stratum.",
            "",
            "  'Hair' = information stored in the gauge field",
            "  that escapes the no-hair theorem via Noether",
            "  charges at the algebra boundary.",
            "",
            "  In SMNNIP: the gauge field A_μ can carry",
            "  non-Abelian charge at ℍ and 𝕆 layers.",
            "  This IS the neural 'hair' — information",
            "  retained in the weight field structure",
            "  that gradient descent cannot see.",
            "",
            "  Hawking radiation analog:",
            "    Noether violation at algebra boundaries",
            "    = thermal noise injection",
            "    = information leaking from deep layers",
            "    as the network approaches saturation.",
            "",
            "  Saturation collapse at input scale 11.0",
            "  observed in boundary probe. This is the",
            "  neural analog of horizon crossing.",
            "",
            "  Status: ◇ speculative — named conjecture",
        ],
        'sympy': 'S_NN ~ A_algebra / 4  [Bekenstein analog]',
        'params': [],
        'topic_tags': ['black holes', 'bekenstein', 'entropy', 'hawking', 'saturation'],
    },
    {
        'id': 'bouncy_horizon',
        'math_group': 'Open Conjectures',
        'topic_group': 'Bouncy Horizon Propagation',
        'title': 'Bouncy Horizon Propagation',
        'short': 'Activation waves near saturation — loop quantum analog',
        'confidence': 'speculative',
        'display': [
            "Bouncy Horizon Propagation",
            "═══════════════════════════",
            "",
            "  Near the saturation boundary (input scale ~11.0),",
            "  activations exhibit wave-like reflection behavior.",
            "",
            "  The 'horizon' is the VEV saturation point:",
            "    |β| → √(−μ²/λ)  [bias field saturates]",
            "",
            "  Activations approaching the horizon:",
            "    · Cannot penetrate (field strength saturates)",
            "    · Reflect back with phase shift",
            "    · Phase shift = π/2 at φ-crossing",
            "      Δ_φ = (π/2)·ħ_NN  [closed numerically]",
            "",
            "  Loop quantum gravity analog:",
            "  In LQG, spacetime geometry 'bounces' at",
            "  the Planck scale rather than collapsing.",
            "  Neural analog: the algebra tower prevents",
            "  representational collapse at the VEV boundary",
            "  by reflecting activations into adjacent strata.",
            "",
            "  Cross-stratum propagation at the horizon:",
            "    𝕆-layer activation reflects → ℍ layer",
            "    via Cayley-Dickson projection π: 𝕆 → ℍ",
            "",
            "  Status: ◇ speculative — observed numerically",
        ],
        'sympy': 'psi_reflected = exp(I*pi/2*hbar_nn) * psi_incident',
        'params': ['hbar_nn', 'vev', 'mu_sq'],
        'topic_tags': ['horizon', 'saturation', 'bounce', 'LQG analog', 'phi crossing'],
    },
    {
        'id': 'electron_orbitals',
        'math_group': 'Open Conjectures',
        'topic_group': 'Electron Orbitals',
        'title': 'Electron Orbitals — Activation Wavefunction Shells',
        'short': 'ψ_nlm analog in ℂ stratum — U(1) shells',
        'confidence': 'speculative',
        'display': [
            "Electron Orbitals — Activation Wavefunction Shells",
            "════════════════════════════════════════════════════",
            "",
            "  Hydrogen: ψ_nlm = R_nl(r)·Y_lm(θ,φ)",
            "  n=principal, l=angular, m=magnetic quantum numbers",
            "",
            "  Neural analog in the ℂ stratum:",
            "    n → layer depth ℓ  (radial quantum number)",
            "    l → SU(2) isospin  (angular momentum analog)",
            "    m → U(1) charge    (magnetic quantum number analog)",
            "",
            "  Activation spinors Ψ_i satisfy the RedBlue",
            "  Hamiltonian — a Schrödinger equation.",
            "  Its eigenstates are the 'neural orbitals':",
            "  stable activation patterns that persist across",
            "  training without gradient decay.",
            "",
            "  The Pauli exclusion principle analog:",
            "  Two activations cannot occupy the same",
            "  (layer, gauge, algebra) quantum state.",
            "  This is the spinor index protocol.",
            "",
            "  Aufbau principle for networks:",
            "  Layers fill from ℝ upward: ℝ→ℂ→ℍ→𝕆",
            "  Each 'shell' has capacity dim(algebra)².",
            "",
            "  Status: ◇ speculative — structural analogy",
        ],
        'sympy': 'Psi_nlm = R_nl(l) * Y_lm(theta, phi)  [orbital analog]',
        'params': ['hbar_nn', 'layer'],
        'topic_tags': ['orbitals', 'hydrogen', 'quantum numbers', 'shells', 'Pauli'],
    },
    {
        'id': 'cardioid_strings',
        'math_group': 'Open Conjectures',
        'topic_group': 'Cardioid Superstrings',
        'title': 'Cardioid Superstrings — 𝕆 Layer Worldsheet',
        'short': 'Octonion worldsheet → cardioid string topology',
        'confidence': 'speculative',
        'display': [
            "Cardioid Superstrings — 𝕆 Layer Worldsheet",
            "═════════════════════════════════════════════",
            "",
            "  Superstring theory requires 10D spacetime.",
            "  Extra 6 dimensions compactified on Calabi-Yau.",
            "",
            "  In SMNNIP, the 𝕆 layer has 8 dimensions.",
            "  The worldsheet of an octonion activation trace",
            "  traces a cardioid topology when projected to",
            "  the ℂ plane via π: 𝕆 → ℂ.",
            "",
            "  r(θ) = 2a(1 − cos θ)  [cardioid]",
            "",
            "  The cusp at r=0 corresponds to the point",
            "  where the activation crosses the horizon",
            "  (bouncy horizon propagation).",
            "",
            "  Fano plane → G₂ → exceptional string theory:",
            "  The G₂ structure of 𝕆 appears in M-theory",
            "  compactification on G₂ manifolds.",
            "  The SMNNIP 𝕆 layer may be the computational",
            "  analog of G₂ holonomy compactification.",
            "",
            "  Freudenthal-Tits magic square entry (𝕆⊗𝕆) = E₈.",
            "  E₈ appears at maximum reasoning depth.",
            "",
            "  Status: ◇ speculative — named conjecture",
        ],
        'sympy': 'r = 2*a*(1 - cos(theta))  [cardioid worldsheet]',
        'params': [],
        'topic_tags': ['strings', 'superstrings', 'E8', 'G2', 'M-theory', 'cardioid'],
    },
]

# ── TOPIC GROUP SORT ORDER ─────────────────────────────────────────────────────
TOPIC_ORDER = [
    'Langlands Program: Master Key',
    'The Full Proof',
    'RedBlue Hamiltonian',
    'Classical Mechanics Emergence',
    'Electromagnetism',
    'Weak Force / Spin',
    'Strong Force Geometry',
    'Symmetry Breaking / Higgs',
    'Backpropagation Emerges',
    'Neural Physical Constants',
    'Golden Ratio / Inversion Fixed Point',
    'Grand Unification',
    'Hairy Black Holes',
    'Bouncy Horizon Propagation',
    'Electron Orbitals',
    'Cardioid Superstrings',
]

MATH_ORDER = [
    'Langlands Program: Master Key',
    'Foundation Theorems',
    'Algebra Tower',
    'Lagrangian Density',
    'Equations of Motion',
    'Conservation Laws',
    'Neural Constants',
    'Convergence Theorems',
    'Open Conjectures',
]


# ═══════════════════════════════════════════════════════════════════════════════
# §2  RESEARCHER OPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

OPTIONS = {
    'algebra': {
        'label': 'algebra stratum',
        'choices': ['ℝ', 'ℂ', 'ℍ', '𝕆', '𝕊 [Master Key]'],
        'current': 1,
        'key': 'algebra',
    },
    'eom': {
        'label': 'derivation target',
        'choices': ['euler-lagrange', 'yang-mills', 'redblue-H', 'higgs', 'noether', 'rg-flow', 'hessian', 'gradient-flow'],
        'current': 1,
        'key': 'eom',
    },
    'constraint': {
        'label': 'constraint',
        'choices': ['μ²<0 SSB', 'μ²=0 critical', 'μ²>0 stable', 'λ=0 massless', 'g→0 abelian', 'custom'],
        'current': 0,
        'key': 'constraint',
    },
    'output': {
        'label': 'output format',
        'choices': ['sympy-pretty', 'latex', 'numerical', 'residuals', 'all'],
        'current': 0,
        'key': 'output',
    },
    'confidence': {
        'label': 'confidence filter',
        'choices': ['all', 'established ✓', 'theoretical ◈', 'speculative ◇', 'open ?'],
        'current': 0,
        'key': 'confidence',
    },
}

ALGEBRA_MAP = {
    'ℝ': 0, 'ℂ': 1, 'ℍ': 2, '𝕆': 3, '𝕊 [Master Key]': -1
}
CONSTRAINT_MAP = {
    'μ²<0 SSB'    : {'mu_sq': -1.0, 'lam': 0.5},
    'μ²=0 critical': {'mu_sq':  0.0, 'lam': 0.5},
    'μ²>0 stable'  : {'mu_sq':  1.0, 'lam': 0.5},
    'λ=0 massless' : {'mu_sq': -1.0, 'lam': 0.0},
    'g→0 abelian'  : {'mu_sq': -1.0, 'lam': 0.5},
    'custom'       : {'mu_sq': -1.0, 'lam': 0.5},
}


# ═══════════════════════════════════════════════════════════════════════════════
# §3  SYMPY RENDERING
# ═══════════════════════════════════════════════════════════════════════════════

def render_sympy(entry_id: str, output_fmt: str, params: dict) -> List[str]:
    """Render SymPy output for the given proof entry."""
    if not SYMPY_AVAILABLE:
        return ["  [SymPy not available — install with: pip install sympy]"]

    lines = []
    l, hbar, g, mu2, lam, kappa, eps, depth = symbols(
        'l hbar_nn g_coup mu_sq lambda kappa epsilon L'
    )

    Psi = Function('Psi')
    beta = Function('beta')
    H_RB = symbols('H_RB')

    try:
        if entry_id == 'redblue_hamiltonian':
            eq = sp.Eq(sp.I * hbar * sp.Derivative(Psi(l), l), H_RB * Psi(l))
            lines.append("  RedBlue Hamiltonian (SymPy):")
            lines.append("  " + sp.pretty(eq, use_unicode=True))

        elif entry_id == 'yang_mills':
            D, R, J = symbols('D_l R^a J^a')
            eq = sp.Eq(D * R, g * symbols('Psibar') * symbols('T^a') * Psi(l))
            lines.append("  Yang-Mills (SymPy):")
            lines.append("  D_l R^{a} = g · Ψ̄ · T^a · Ψ")

        elif entry_id == 'higgs_bias':
            beta_n = sp.Symbol('beta_norm')
            lhs = symbols('D_l^2_beta') + mu2 * beta(l) - 2*lam*beta_n**2 * beta(l)
            lines.append("  Neural Higgs (SymPy):")
            lines.append(f"  μ² = {params.get('mu_sq', -1.0)}   λ = {params.get('lam', 0.5)}")
            vev = sp.sqrt(-params.get('mu_sq', -1.0) / params.get('lam', 0.5)) if params.get('mu_sq', -1.0) < 0 else sp.Symbol('N/A')
            lines.append(f"  VEV |β| = √(-μ²/λ) = {sp.simplify(vev)}")

        elif entry_id == 'noether_current':
            J = Function('J')
            eq = sp.Eq(sp.Symbol('partial_mu') * J(l), 0)
            lines.append("  Noether Conservation (SymPy):")
            lines.append("  " + sp.pretty(eq, use_unicode=True))

        elif entry_id == 'alpha_nn':
            alpha_0 = sp.Symbol('alpha_0')
            beta_0  = sp.Symbol('beta_0')
            l0      = sp.Symbol('l_0')
            alpha_l = alpha_0 / (1 + beta_0 * alpha_0 * sp.log(l/l0))
            lines.append("  α_NN Running (SymPy):")
            lines.append("  " + sp.pretty(alpha_l, use_unicode=True))

        elif entry_id == 'phi_fixed':
            phi = (1 + sp.sqrt(5)) / 2
            eq1 = sp.Eq(phi * (1/phi), 1)
            eq2 = sp.Eq(1 + 1/phi, phi)
            lines.append("  φ identities (SymPy):")
            lines.append("  " + sp.pretty(phi, use_unicode=True) + " ≈ " + str(float(phi.evalf(10))))
            lines.append("  " + sp.pretty(eq2, use_unicode=True))

        elif entry_id == 'training_inequality':
            k = params.get('kappa', 10.0)
            e = params.get('epsilon', 0.01)
            d = int(params.get('depth', 4))
            lv = params.get('lam', 0.9)
            T_gd     = k * (lv ** (-2*d)) / e
            T_smnnip = math.sqrt(k) * math.log(1.0/e)
            lines.append("  Training Inequality (evaluated):")
            lines.append(f"  κ={k}  ε={e}  L={d}  λ={lv}")
            lines.append(f"  𝒯_GD     = {T_gd:.2f}")
            lines.append(f"  𝒯_SMNNIP = {T_smnnip:.4f}")
            lines.append(f"  Ratio: {T_gd/T_smnnip:.2f}×  (SMNNIP faster)")

        elif entry_id == 'full_lagrangian' and ENGINE_AVAILABLE:
            engine = SMNNIPDerivationEngine()
            alg_idx = params.get('algebra_idx', 1)
            if alg_idx >= 0:
                import random; random.seed(42)
                dim  = Algebra.DIM[alg_idx]
                n    = 4
                ngen = max(1, Algebra.N_GEN[alg_idx])
                psi_  = [make_element([random.gauss(0,.3) for _ in range(dim)], alg_idx) for _ in range(n)]
                A_    = [[random.gauss(0,.1) for _ in range(ngen)] for _ in range(n)]
                beta_ = [make_element([random.gauss(0,.1) for _ in range(dim)], alg_idx) for _ in range(n)]
                st = FieldState(psi=psi_, A=A_, beta=beta_, algebra=alg_idx,
                                layer=1, hbar_nn=0.1, g_coup=0.01,
                                mu_sq=params.get('mu_sq', -1.0),
                                lam=params.get('lam', 0.5), vev=1.0)
                L = engine.lagrangian(st)
                res = engine.all_eom_residuals(st)
                noether = engine.noether(st)
                lines.append(f"  Lagrangian evaluation ({Algebra.NAME[alg_idx]} stratum):")
                lines.append(f"  ℒ_total      = {L['total']:.6f}")
                lines.append(f"  ℒ_kinetic    = {L.get('kinetic', 0):.6f}")
                lines.append(f"  ℒ_matter     = {L.get('matter', 0):.6f}")
                lines.append(f"  ℒ_bias       = {L.get('bias', 0):.6f}")
                lines.append(f"  ℒ_coupling   = {L.get('coupling', 0):.6f}")
                lines.append(f"  Dirac resid  = {res['dirac']:.6f}")
                lines.append(f"  YM resid     = {res['yang_mills']:.6f}")
                lines.append(f"  Higgs resid  = {res['higgs']:.6f}")
                v = noether.get('violation', 0.0)
                c = '✓ conserved' if noether.get('conserved', True) else '⚠ violation'
                lines.append(f"  Noether viol = {v:.6f}  {c}")

        else:
            lines.append(f"  [entry: {entry_id}]")
            lines.append(f"  Output format: {output_fmt}")

    except Exception as ex:
        lines.append(f"  [SymPy render error: {ex}]")

    return lines if lines else ["  [no SymPy output for this entry]"]


# ═══════════════════════════════════════════════════════════════════════════════
# §4  CURSES APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

class ProofEngineConsole:
    """SMNNIP Proof Engine — curses console application."""

    TITLE = "SMNNIP PROOF ENGINE"

    # Color pair indices
    C_DEFAULT   = 1
    C_DISPLAY   = 2
    C_SIDEBAR   = 3
    C_SORT      = 4
    C_OPTIONS   = 5
    C_INPUT     = 6
    C_HIGHLIGHT = 7
    C_ACTIVE    = 8
    C_MUTED     = 9
    C_HEADER    = 10
    C_WARN      = 11
    C_GOOD      = 12
    C_MASTER    = 13  # Langlands Master Key
    C_REDBLUE   = 14  # RedBlue Hamiltonian

    def __init__(self, stdscr):
        self.scr = stdscr
        self.engine = SMNNIPDerivationEngine() if ENGINE_AVAILABLE else None

        # State
        self.sort_mode    = 'MATH'   # 'MATH' or 'TOPIC'
        self.list_items   = []
        self.list_sel     = 0
        self.list_scroll  = 0
        self.display_scroll = 0
        self.input_str    = ''
        self.input_prompt = ''
        self.status_msg   = ''
        self.params       = {
            'mu_sq': -1.0, 'lam': 0.5, 'g_coup': 0.01,
            'hbar_nn': 0.1, 'layer': 1, 'depth': 4,
            'kappa': 10.0, 'epsilon': 0.01, 'vev': 1.0,
            'algebra_idx': 1,
        }
        self.display_lines  = []
        self.sympy_lines    = []
        self.show_sympy     = False

        self._init_colors()
        self._build_list()
        self._load_entry(0)

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        # (fg, bg) pairs — bg=-1 means terminal default
        curses.init_pair(self.C_DEFAULT,   curses.COLOR_WHITE,   -1)
        curses.init_pair(self.C_DISPLAY,   curses.COLOR_GREEN,   -1)
        curses.init_pair(self.C_SIDEBAR,   curses.COLOR_BLUE,    -1)
        curses.init_pair(self.C_SORT,      curses.COLOR_RED,     -1)
        curses.init_pair(self.C_OPTIONS,   curses.COLOR_WHITE,   -1)
        curses.init_pair(self.C_INPUT,     curses.COLOR_YELLOW,  -1)
        curses.init_pair(self.C_HIGHLIGHT, curses.COLOR_BLACK,   curses.COLOR_CYAN)
        curses.init_pair(self.C_ACTIVE,    curses.COLOR_CYAN,    -1)
        curses.init_pair(self.C_MUTED,     curses.COLOR_BLACK+8, -1) if curses.COLORS >= 16 else curses.init_pair(self.C_MUTED, curses.COLOR_BLACK, -1)
        curses.init_pair(self.C_HEADER,    curses.COLOR_CYAN,    -1)
        curses.init_pair(self.C_WARN,      curses.COLOR_RED,     -1)
        curses.init_pair(self.C_GOOD,      curses.COLOR_GREEN,   -1)
        curses.init_pair(self.C_MASTER,    curses.COLOR_MAGENTA, -1)
        curses.init_pair(self.C_REDBLUE,   curses.COLOR_CYAN,    -1)
        curses.curs_set(1)
        curses.noecho()
        self.scr.keypad(True)
        self.scr.timeout(100)

    def _build_list(self):
        """Build the sorted list from PROOF_ENTRIES."""
        conf_filter = OPTIONS['confidence']['choices'][OPTIONS['confidence']['current']]

        if self.sort_mode == 'MATH':
            order = MATH_ORDER
            group_key = 'math_group'
        else:
            order = TOPIC_ORDER
            group_key = 'topic_group'

        # Filter by confidence
        conf_map = {
            'all': None,
            'established ✓': 'established',
            'theoretical ◈': 'theoretical',
            'speculative ◇': 'speculative',
            'open ?': 'open',
        }
        cf = conf_map.get(conf_filter, None)

        # Group entries
        groups: Dict[str, List] = {}
        for entry in PROOF_ENTRIES:
            if cf and entry['confidence'] != cf:
                continue
            g = entry[group_key]
            if g not in groups:
                groups[g] = []
            groups[g].append(entry)

        self.list_items = []
        for g in order:
            if g not in groups:
                continue
            self.list_items.append({'type': 'group', 'label': g})
            for e in groups[g]:
                self.list_items.append({'type': 'entry', 'entry': e})

        # Add any groups not in order
        for g, entries in groups.items():
            if g not in order:
                self.list_items.append({'type': 'group', 'label': g})
                for e in entries:
                    self.list_items.append({'type': 'entry', 'entry': e})

        if self.list_sel >= len(self.list_items):
            self.list_sel = 0

    def _load_entry(self, sel_idx: int):
        """Load display content for the selected list item."""
        if sel_idx >= len(self.list_items):
            return
        item = self.list_items[sel_idx]
        if item['type'] != 'entry':
            return
        entry = item['entry']

        self.display_lines = entry['display'][:]
        self.display_scroll = 0

        # Generate SymPy output
        fmt = OPTIONS['output']['choices'][OPTIONS['output']['current']]
        self.sympy_lines = render_sympy(entry['id'], fmt, self.params)

        # Update input prompt
        param_list = entry.get('params', [])
        if param_list:
            defaults = ', '.join(f"{p}={self.params.get(p, '?')}" for p in param_list)
            self.input_prompt = f"  {entry['id']} [{defaults}] › "
        else:
            alg_name = OPTIONS['algebra']['choices'][OPTIONS['algebra']['current']]
            eom_name = OPTIONS['eom']['choices'][OPTIONS['eom']['current']]
            self.input_prompt = f"  proof-engine [{eom_name} / {alg_name}] › "

    def _dimensions(self):
        """Compute section dimensions as percentages of terminal size."""
        H, W = self.scr.getmaxyx()
        # Heights
        top_h    = max(8,  int(H * 0.60))   # display + sidebar
        mid_h    = max(4,  int(H * 0.22))   # options + sort
        input_h  = max(2,  H - top_h - mid_h)  # input bar
        # Widths
        disp_w   = max(40, int(W * 0.65))
        side_w   = W - disp_w
        return H, W, top_h, mid_h, input_h, disp_w, side_w

    def _safe_addstr(self, win, y, x, text, attr=0):
        """addstr that won't crash on boundary."""
        try:
            h, w = win.getmaxyx()
            if y < 0 or y >= h or x < 0 or x >= w:
                return
            max_len = w - x - 1
            if max_len <= 0:
                return
            win.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

    def _draw_border(self, win, title: str = '', color_pair: int = 1):
        """Draw a border on a window with optional title."""
        try:
            win.border()
            if title:
                h, w = win.getmaxyx()
                t = f" {title} "
                x = max(2, (w - len(t)) // 2)
                self._safe_addstr(win, 0, x, t, curses.color_pair(color_pair) | curses.A_BOLD)
        except curses.error:
            pass

    def _draw_display(self, win):
        """Draw the main display area."""
        win.erase()
        self._draw_border(win, "DISPLAY", self.C_DISPLAY)
        h, w = win.getmaxyx()
        inner_h = h - 2
        inner_w = w - 4

        if not self.list_items or self.list_sel >= len(self.list_items):
            return
        item = self.list_items[self.list_sel]
        if item['type'] != 'entry':
            return
        entry = item['entry']

        # Title line
        conf_sym = CONFIDENCE.get(entry['confidence'], '?')
        title = f"{conf_sym} {entry['title']}"
        self._safe_addstr(win, 1, 2, title[:inner_w], curses.color_pair(self.C_HEADER) | curses.A_BOLD)

        # Confidence label
        conf_label = f"[{entry['confidence']}]"
        self._safe_addstr(win, 1, w - len(conf_label) - 3, conf_label,
                          curses.color_pair(self.C_MUTED))

        # Separator
        self._safe_addstr(win, 2, 2, '─' * min(inner_w, w-4), curses.color_pair(self.C_MUTED))

        # Content lines
        all_lines = self.display_lines[:]
        if self.show_sympy and self.sympy_lines:
            all_lines += ['', '── SymPy ──'] + self.sympy_lines

        start = self.display_scroll
        row = 3
        for i, line in enumerate(all_lines[start:]):
            if row >= h - 1:
                break
            # Color coding
            attr = curses.color_pair(self.C_DISPLAY)
            if line.startswith('══') or line.startswith('──'):
                attr = curses.color_pair(self.C_MUTED)
            elif line.strip().startswith('Status:'):
                attr = curses.color_pair(self.C_WARN)
            elif '✓' in line or 'COMPLETE' in line:
                attr = curses.color_pair(self.C_GOOD)
            elif 'Langlands Program: Master Key' in line or '𝕊' in line:
                attr = curses.color_pair(self.C_MASTER)
            elif 'RedBlue' in line or 'Ĥ_RB' in line or 'Ĥ_NN' in line:
                attr = curses.color_pair(self.C_REDBLUE)
            elif line.strip().startswith('Open:') or line.strip().startswith('?'):
                attr = curses.color_pair(self.C_WARN)
            self._safe_addstr(win, row, 2, line[:inner_w], attr)
            row += 1

        # Scroll indicator
        total = len(all_lines)
        if total > inner_h:
            pct = int(100 * self.display_scroll / max(total - inner_h, 1))
            ind = f" ↕ {self.display_scroll+1}/{total} ({pct}%) [s:toggle SymPy] "
            self._safe_addstr(win, h-1, 2, ind[:inner_w], curses.color_pair(self.C_MUTED))

    def _draw_sidebar(self, win):
        """Draw the equation/topic list."""
        win.erase()
        self._draw_border(win, "LIST", self.C_SIDEBAR)
        h, w = win.getmaxyx()
        inner_h = h - 3
        inner_w = w - 3

        # Sort mode indicator at top
        mode_str = f" [{self.sort_mode}] "
        self._safe_addstr(win, 1, 1, mode_str, curses.color_pair(self.C_ACTIVE) | curses.A_BOLD)

        # Compute visible window
        sel = self.list_sel
        if sel - self.list_scroll >= inner_h - 1:
            self.list_scroll = sel - inner_h + 2
        if sel < self.list_scroll:
            self.list_scroll = sel

        row = 2
        for i, item in enumerate(self.list_items[self.list_scroll:]):
            abs_i = i + self.list_scroll
            if row >= h - 1:
                break
            if item['type'] == 'group':
                label = f" ▸ {item['label']}"
                self._safe_addstr(win, row, 1, label[:inner_w],
                                  curses.color_pair(self.C_MUTED) | curses.A_BOLD)
            else:
                entry = item['entry']
                marker = '▶' if abs_i == sel else ' '
                short  = entry['short'][:inner_w-4]
                label  = f"{marker} {short}"
                if abs_i == sel:
                    attr = curses.color_pair(self.C_HIGHLIGHT) | curses.A_BOLD
                elif entry['math_group'] == 'Langlands Program: Master Key':
                    attr = curses.color_pair(self.C_MASTER)
                elif 'redblue' in entry['id'] or 'RedBlue' in entry['title']:
                    attr = curses.color_pair(self.C_REDBLUE)
                else:
                    attr = curses.color_pair(self.C_SIDEBAR)
                self._safe_addstr(win, row, 1, label[:inner_w], attr)
            row += 1

    def _draw_options(self, win):
        """Draw researcher test options."""
        win.erase()
        self._draw_border(win, "RESEARCHER OPTIONS", self.C_OPTIONS)
        h, w = win.getmaxyx()

        row = 1
        for key, opt in OPTIONS.items():
            if row >= h - 1:
                break
            label_str = f" {opt['label']}: "
            self._safe_addstr(win, row, 1, label_str,
                              curses.color_pair(self.C_MUTED))
            col = len(label_str) + 1
            for i, choice in enumerate(opt['choices']):
                if col + len(choice) + 3 >= w - 1:
                    break
                if i == opt['current']:
                    self._safe_addstr(win, row, col, f"[{choice}]",
                                      curses.color_pair(self.C_ACTIVE) | curses.A_BOLD)
                else:
                    self._safe_addstr(win, row, col, f" {choice} ",
                                      curses.color_pair(self.C_MUTED))
                col += len(choice) + 3
            row += 1

        # Key hint
        hint = " Tab:next-opt  ←→:change  s:sympy  r:run  /:search "
        self._safe_addstr(win, h-1, 2, hint[:w-3], curses.color_pair(self.C_MUTED))

    def _draw_sort(self, win):
        """Draw sort mode panel."""
        win.erase()
        self._draw_border(win, "SORT", self.C_SORT)
        h, w = win.getmaxyx()

        modes = [
            ('MATH',  'by algebra depth'),
            ('TOPIC', 'by named grouping'),
        ]
        for i, (mode, desc) in enumerate(modes):
            row = i*2 + 1
            if row >= h - 1:
                break
            marker = '●' if self.sort_mode == mode else '○'
            label  = f" {marker} {mode} — {desc}"
            attr = (curses.color_pair(self.C_ACTIVE) | curses.A_BOLD
                    if self.sort_mode == mode
                    else curses.color_pair(self.C_MUTED))
            self._safe_addstr(win, row, 1, label[:w-2], attr)

        hint = " m:toggle sort "
        self._safe_addstr(win, h-1, 1, hint[:w-2], curses.color_pair(self.C_MUTED))

    def _draw_input(self, win):
        """Draw the input bar."""
        win.erase()
        h, w = win.getmaxyx()
        try:
            win.border()
        except curses.error:
            pass

        prompt = self.input_prompt or "  proof-engine [ready] › "
        full   = prompt + self.input_str
        self._safe_addstr(win, 1, 0, full[:w-1], curses.color_pair(self.C_INPUT))

        # Status message on right
        if self.status_msg:
            msg = self.status_msg[-min(len(self.status_msg), w-len(full)-2):]
            self._safe_addstr(win, 1, max(len(full)+1, w-len(msg)-2),
                              msg, curses.color_pair(self.C_WARN))

    def draw(self):
        """Full redraw."""
        H, W, top_h, mid_h, input_h, disp_w, side_w = self._dimensions()

        # Create windows
        try:
            disp_win = curses.newwin(top_h, disp_w, 0, 0)
            side_win = curses.newwin(top_h, side_w, 0, disp_w)
            opts_win = curses.newwin(mid_h, disp_w, top_h, 0)
            sort_win = curses.newwin(mid_h, side_w, top_h, disp_w)
            inp_win  = curses.newwin(input_h, W, top_h + mid_h, 0)
        except curses.error:
            return

        self._draw_display(disp_win)
        self._draw_sidebar(side_win)
        self._draw_options(opts_win)
        self._draw_sort(sort_win)
        self._draw_input(inp_win)

        disp_win.noutrefresh()
        side_win.noutrefresh()
        opts_win.noutrefresh()
        sort_win.noutrefresh()
        inp_win.noutrefresh()
        curses.doupdate()

    def _opt_active_idx(self):
        """Which option row has focus (cycles with Tab)."""
        if not hasattr(self, '_opt_focus'):
            self._opt_focus = 0
        return self._opt_focus

    def _navigate_list(self, direction: int):
        """Move list selection up/down, skipping group headers."""
        n = len(self.list_items)
        sel = self.list_sel
        for _ in range(n):
            sel = (sel + direction) % n
            if self.list_items[sel]['type'] == 'entry':
                break
        self.list_sel = sel
        self._load_entry(sel)

    def _execute_input(self):
        """Process the input bar command."""
        cmd = self.input_str.strip()
        self.input_str = ''
        if not cmd:
            return

        # Parse key=value pairs
        parts = [p.strip() for p in cmd.split(',')]
        for part in parts:
            if '=' in part:
                k, v = part.split('=', 1)
                k = k.strip(); v = v.strip()
                try:
                    self.params[k] = float(v)
                    self.status_msg = f"set {k}={v}"
                except ValueError:
                    self.status_msg = f"invalid value: {v}"

        # Reload display with new params
        self._load_entry(self.list_sel)

    def _handle_tab(self):
        """Cycle option focus."""
        if not hasattr(self, '_opt_focus'):
            self._opt_focus = 0
        keys = list(OPTIONS.keys())
        self._opt_focus = (self._opt_focus + 1) % len(keys)

    def _handle_option_change(self, delta: int):
        """Change the focused option."""
        if not hasattr(self, '_opt_focus'):
            self._opt_focus = 0
        keys = list(OPTIONS.keys())
        key = keys[self._opt_focus % len(keys)]
        opt = OPTIONS[key]
        opt['current'] = (opt['current'] + delta) % len(opt['choices'])
        # Apply option effects
        if key == 'algebra':
            alg_name = opt['choices'][opt['current']]
            self.params['algebra_idx'] = ALGEBRA_MAP.get(alg_name, 1)
        elif key == 'constraint':
            cname = opt['choices'][opt['current']]
            cparams = CONSTRAINT_MAP.get(cname, {})
            self.params.update(cparams)
        elif key == 'confidence':
            self._build_list()
        # Reload
        self._load_entry(self.list_sel)

    def run(self):
        """Main event loop."""
        self.draw()
        while True:
            key = self.scr.getch()

            if key == curses.KEY_RESIZE:
                self.scr.clear()
                self.draw()

            # Navigation
            elif key in (curses.KEY_DOWN, ord('j')):
                self._navigate_list(1)
            elif key in (curses.KEY_UP, ord('k')):
                self._navigate_list(-1)

            # Page scroll in display
            elif key == curses.KEY_NPAGE:
                self.display_scroll += 5
            elif key == curses.KEY_PPAGE:
                self.display_scroll = max(0, self.display_scroll - 5)
            elif key == ord('+'):
                self.display_scroll += 1
            elif key == ord('-'):
                self.display_scroll = max(0, self.display_scroll - 1)

            # Sort toggle
            elif key == ord('m'):
                self.sort_mode = 'TOPIC' if self.sort_mode == 'MATH' else 'MATH'
                self._build_list()
                self.list_sel = 0
                self._load_entry(0)

            # SymPy toggle
            elif key == ord('s'):
                self.show_sympy = not self.show_sympy
                self.status_msg = 'SymPy ON' if self.show_sympy else 'SymPy OFF'

            # Options navigation
            elif key == ord('\t'):
                self._handle_tab()
            elif key == curses.KEY_RIGHT:
                self._handle_option_change(1)
            elif key == curses.KEY_LEFT:
                self._handle_option_change(-1)

            # Run derivation engine
            elif key == ord('r'):
                if ENGINE_AVAILABLE:
                    self.show_sympy = True
                    self._load_entry(self.list_sel)
                    self.status_msg = 'engine run ✓'
                else:
                    self.status_msg = '[engine not available]'

            # Input bar — character entry
            elif key == ord('\n') or key == curses.KEY_ENTER:
                self._execute_input()

            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_str = self.input_str[:-1]

            elif 32 <= key <= 126:
                self.input_str += chr(key)
                self.status_msg = ''

            # Help
            elif key == ord('?') or key == ord('h'):
                self.display_lines = [
                    "SMNNIP Proof Engine — Key Bindings",
                    "═══════════════════════════════════",
                    "",
                    "  NAVIGATION",
                    "  ↑/↓ or j/k     : move list selection",
                    "  PgUp/PgDn       : scroll display",
                    "  +/-             : scroll display by 1",
                    "",
                    "  SORT & FILTER",
                    "  m               : toggle MATH / TOPIC sort",
                    "  Tab             : cycle option focus",
                    "  ←/→             : change focused option",
                    "",
                    "  DISPLAY",
                    "  s               : toggle SymPy output",
                    "  r               : run derivation engine",
                    "",
                    "  INPUT BAR",
                    "  Type param=value pairs, comma-separated",
                    "  Example: mu_sq=-1.0, g_coup=0.05",
                    "  Enter to apply.",
                    "",
                    "  QUIT",
                    "  q or Ctrl-C     : exit",
                    "",
                    "  SPECIAL ENTRIES",
                    "  Langlands Program: Master Key = Sedenion layer",
                    "  RedBlue Hamiltonian = Ĥ_NN (neural Hamiltonian)",
                ]
                self.display_scroll = 0

            elif key == ord('q'):
                break

            self.draw()


# ═══════════════════════════════════════════════════════════════════════════════
# §5  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main(stdscr):
    app = ProofEngineConsole(stdscr)
    app.run()

if __name__ == '__main__':
    if not ENGINE_AVAILABLE:
        print("Warning: smnnip_derivation_pure.py not found in path.")
        print("Console will run without live derivation engine output.")
        print("Place smnnip_derivation_pure.py in the same directory.")
        print()

    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nSMNNIP Proof Engine — session ended.")
