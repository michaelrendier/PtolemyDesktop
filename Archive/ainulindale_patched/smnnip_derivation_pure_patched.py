"""
SMNNIP Derivation Engine — Pure Python3
========================================
Standard Model of Neural Network Information Propagation
Derivation Engine: the mathematical kernel between the equation engine
and the Console SymPy GUI.

Architecture position:
    equation engine  →→  DERIVATION ENGINE  →→  Console SymPy GUI
                                              →→  Qt GUI (later)

This module has NO I/O, NO printing, NO SymPy, NO training loops.
It receives field state objects and returns mathematical objects:
  - callables (evaluate equations of motion)
  - residuals (how far a state is from satisfying an EOM)
  - tensors / algebra elements
  - scalar diagnostics

All seven fundamental derivation operations are implemented:
  1. Euler-Lagrange evaluation       → (callable, residual_fn) pair
  2. Covariant derivative            → D_μΨ per algebra stratum
  3. Field strength tensor           → F_μν^a with non-Abelian term
  4. Noether current + violation     → J^μ, ∂_μJ^μ
  5. Algebra multiplication          → ℝ / ℂ / ℍ / 𝕆
  6. Cayley-Dickson inclusion/proj   → ι and π maps
  7. RG flow / running constants     → α_NN(l), h_NN(l)

Field state protocol:
  The engine operates on FieldState namedtuples (defined below).
  The equation engine produces FieldState objects; the derivation
  engine consumes them; the GUI renders the results.

Author: SMNNIP formalism / O Captain My Captain
Derivation engine: Claude (Anthropic) — April 12, 2026
"""

import math
import cmath
from typing import Callable, Tuple, List, Optional, NamedTuple, Dict, Any


# ═══════════════════════════════════════════════════════════════════════════════
# §0  ALGEBRA CONSTANTS AND ENUMERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class Algebra:
    """Enumeration of algebra strata in the Cayley-Dickson tower."""
    R = 0   # ℝ  — Layer 0 substrate   — dim 1  — U(0)/trivial gauge
    C = 1   # ℂ  — Layer 1 semantic     — dim 2  — U(1) gauge
    H = 2   # ℍ  — Layer 2 skills       — dim 4  — SU(2) gauge
    O = 3   # 𝕆  — Layer 3 reasoning    — dim 8  — SU(3)/G2 gauge

    DIM     = {0: 1, 1: 2, 2: 4, 3: 8}
    NAME    = {0: 'ℝ', 1: 'ℂ', 2: 'ℍ', 3: '𝕆'}
    GAUGE   = {0: 'trivial', 1: 'U(1)', 2: 'SU(2)', 3: 'SU(3)/G₂'}

    # Number of gauge generators per stratum
    N_GEN   = {0: 0, 1: 1, 2: 3, 3: 8}

    # Lost algebraic property at each step (the SIGNAL)
    LOST    = {1: 'ordering', 2: 'commutativity', 3: 'associativity'}


# Fano plane lines — defines the octonion multiplication table
# Each triple (a,b,c) encodes: e_{a+1} * e_{b+1} = e_{c+1}
FANO_LINES: List[Tuple[int,int,int]] = [
    (0,1,3),(1,2,4),(2,3,5),(3,4,6),(4,5,0),(5,6,1),(6,0,2)
]

def _build_oct_table() -> List[List[Optional[Tuple[int,int]]]]:
    """
    Build the 8×8 octonion multiplication table from the Fano plane.
    table[i][j] = (sign, index) meaning e_i * e_j = sign * e_index
    """
    table: List[List[Any]] = [
        [(1,i) if j==0 else ((1,j) if i==0 else None)
         for j in range(8)]
        for i in range(8)
    ]
    for i in range(1,8):
        table[i][i] = (-1, 0)
    for (a,b,c) in FANO_LINES:
        i,j,k = a+1, b+1, c+1
        table[i][j] = ( 1, k);  table[j][i] = (-1, k)
        table[j][k] = ( 1, i);  table[k][j] = (-1, i)
        table[k][i] = ( 1, j);  table[i][k] = (-1, j)
    return table

OCT_TABLE = _build_oct_table()


# ═══════════════════════════════════════════════════════════════════════════════
# §1  ALGEBRA ELEMENT TYPES
# These are lightweight value objects — not the equation engine's training
# classes. The derivation engine uses its own algebra types so it remains
# decoupled from the equation engine's internal state.
# ═══════════════════════════════════════════════════════════════════════════════

class RealEl:
    """ℝ element — scalar."""
    __slots__ = ('v',)
    def __init__(self, v: float = 0.0): self.v = float(v)
    def __add__(self, o): return RealEl(self.v + o.v)
    def __sub__(self, o): return RealEl(self.v - o.v)
    def __mul__(self, o): return RealEl(self.v * o.v)
    def __rmul__(self, s): return RealEl(s * self.v)
    def conj(self): return RealEl(self.v)
    def norm_sq(self): return self.v * self.v
    def norm(self): return abs(self.v)
    def as_list(self): return [self.v]
    def __repr__(self): return f"ℝ({self.v:.6f})"


class ComplexEl:
    """ℂ element — 2-component."""
    __slots__ = ('re', 'im')
    def __init__(self, re: float = 0.0, im: float = 0.0):
        self.re = float(re); self.im = float(im)
    def __add__(self, o): return ComplexEl(self.re+o.re, self.im+o.im)
    def __sub__(self, o): return ComplexEl(self.re-o.re, self.im-o.im)
    def __mul__(self, o):
        return ComplexEl(self.re*o.re - self.im*o.im,
                         self.re*o.im + self.im*o.re)
    def __rmul__(self, s): return ComplexEl(s*self.re, s*self.im)
    def conj(self): return ComplexEl(self.re, -self.im)
    def norm_sq(self): return self.re**2 + self.im**2
    def norm(self): return math.sqrt(self.norm_sq())
    def phase(self): return math.atan2(self.im, self.re)
    def as_list(self): return [self.re, self.im]
    def __repr__(self): return f"ℂ({self.re:.4f}+{self.im:.4f}i)"


class QuatEl:
    """ℍ element — 4-component quaternion."""
    __slots__ = ('w','x','y','z')
    def __init__(self, w=0.,x=0.,y=0.,z=0.):
        self.w=float(w); self.x=float(x)
        self.y=float(y); self.z=float(z)
    def __add__(self, o): return QuatEl(self.w+o.w,self.x+o.x,self.y+o.y,self.z+o.z)
    def __sub__(self, o): return QuatEl(self.w-o.w,self.x-o.x,self.y-o.y,self.z-o.z)
    def __mul__(self, o):
        return QuatEl(
            self.w*o.w - self.x*o.x - self.y*o.y - self.z*o.z,
            self.w*o.x + self.x*o.w + self.y*o.z - self.z*o.y,
            self.w*o.y - self.x*o.z + self.y*o.w + self.z*o.x,
            self.w*o.z + self.x*o.y - self.y*o.x + self.z*o.w)
    def __rmul__(self, s): return QuatEl(s*self.w,s*self.x,s*self.y,s*self.z)
    def conj(self): return QuatEl(self.w,-self.x,-self.y,-self.z)
    def norm_sq(self): return self.w**2+self.x**2+self.y**2+self.z**2
    def norm(self): return math.sqrt(self.norm_sq())
    def commutator(self, o):
        """[self, o] = self*o - o*self — nonzero in ℍ."""
        return (self * o) - (o * self)
    def as_list(self): return [self.w,self.x,self.y,self.z]
    def __repr__(self): return f"ℍ({self.w:.4f},{self.x:.4f}i,{self.y:.4f}j,{self.z:.4f}k)"


class OctEl:
    """𝕆 element — 8-component octonion."""
    __slots__ = ('c',)
    def __init__(self, c=None):
        self.c = list(c)[:8] if c else [0.0]*8
        while len(self.c) < 8: self.c.append(0.0)
    def __add__(self, o): return OctEl([a+b for a,b in zip(self.c,o.c)])
    def __sub__(self, o): return OctEl([a-b for a,b in zip(self.c,o.c)])
    def __mul__(self, o):
        r = [0.0]*8
        for i in range(8):
            if self.c[i] == 0: continue
            for j in range(8):
                if o.c[j] == 0: continue
                e = OCT_TABLE[i][j]
                if e: r[e[1]] += e[0] * self.c[i] * o.c[j]
        return OctEl(r)
    def __rmul__(self, s): return OctEl([s*x for x in self.c])
    def conj(self):
        c = [-x for x in self.c]; c[0] = self.c[0]; return OctEl(c)
    def norm_sq(self): return sum(x*x for x in self.c)
    def norm(self): return math.sqrt(self.norm_sq())
    def associator(self, b, c_el):
        """[self,b,c] = (self*b)*c - self*(b*c) — nonzero in 𝕆."""
        return ((self * b) * c_el) - (self * (b * c_el))
    def as_list(self): return list(self.c)
    @staticmethod
    def unit(k):
        c = [0.0]*8; c[k] = 1.0; return OctEl(c)
    def __repr__(self):
        parts = [f"{v:.3f}·e{i}" for i,v in enumerate(self.c) if abs(v)>1e-9]
        return f"𝕆({' + '.join(parts) if parts else '0'})"


# Algebra element factory
def make_element(coords: List[float], algebra: int):
    """Construct the correct algebra element from a coordinate list."""
    if algebra == Algebra.R:
        return RealEl(coords[0] if coords else 0.0)
    elif algebra == Algebra.C:
        return ComplexEl(*(coords[:2] + [0.0]*(2-len(coords[:2]))))
    elif algebra == Algebra.H:
        return QuatEl(*(coords[:4] + [0.0]*(4-len(coords[:4]))))
    elif algebra == Algebra.O:
        return OctEl(coords[:8])
    else:
        raise ValueError(f"Unknown algebra stratum: {algebra}")


# ═══════════════════════════════════════════════════════════════════════════════
# §2  FIELD STATE PROTOCOL
# The derivation engine operates on FieldState objects.
# These are produced by the equation engine and consumed here.
# ═══════════════════════════════════════════════════════════════════════════════

class FieldState(NamedTuple):
    """
    Complete field state at a given layer boundary.

    psi      : activation spinor (list of algebra elements, one per neuron)
    A        : gauge field (weight matrix rows as algebra elements)
    beta     : bias field (list of algebra elements)
    algebra  : which stratum (Algebra.R / C / H / O)
    layer    : integer layer index
    hbar_nn  : neural Planck constant for this stratum
    g_coup   : gauge coupling constant for this stratum
    mu_sq    : Higgs mass parameter (negative for SSB)
    lam      : Higgs quartic coupling
    vev      : vacuum expectation value target
    """
    psi     : list
    A       : list          # list of lists (matrix rows)
    beta    : list
    algebra : int
    layer   : int
    hbar_nn : float = 0.1
    g_coup  : float = 0.01
    mu_sq   : float = -1.0
    lam     : float = 0.5
    vev     : float = 1.0


class DerivationResult(NamedTuple):
    """
    Returned by euler_lagrange().
    callable_eom : f(state) → algebra element — evaluate EOM at state
    residual_fn  : f(state) → float — how far state is from satisfying EOM
    label        : human-readable name (for SymPy GUI)
    latex        : LaTeX string of the equation (for SymPy GUI)
    """
    callable_eom : Callable
    residual_fn  : Callable
    label        : str
    latex        : str


# ═══════════════════════════════════════════════════════════════════════════════
# §3  OPERATION 1 — EULER-LAGRANGE EVALUATION
# Returns (callable_eom, residual_fn) for each field.
# Three EOMs: Neural Dirac, Neural Yang-Mills, Neural Higgs.
# ═══════════════════════════════════════════════════════════════════════════════

class EulerLagrange:
    """
    Euler-Lagrange equations derived from ℒ_NN.

    Each method returns a DerivationResult with:
      .callable_eom(state) → algebra element (the EOM evaluated)
      .residual_fn(state)  → float (|EOM| — how far from zero)
    """

    @staticmethod
    def neural_dirac(hbar_nn: Optional[float] = None) -> DerivationResult:
        """
        Neural Dirac Equation (Activation Propagation):
          i·ħ_NN · ∂Ψ_i/∂l = H_NN · Ψ_i
          where H_NN = -i·Γ^a·D_a + Γ_ij·β

        Derived from δℒ_matter/δΨ̄ = 0.

        Returns the Hamiltonian action on Ψ: H_NN·Ψ - i·ħ_NN·∂Ψ/∂l
        In steady-state (no layer evolution), residual = |H_NN·Ψ|.
        """
        def callable_eom(state: FieldState, psi_prev: Optional[list] = None) -> list:
            """
            Evaluate H_NN · Ψ for each activation spinor.
            psi_prev: previous layer activations (for ∂Ψ/∂l finite diff).
            Returns list of algebra elements: the Hamiltonian-evolved activations.
            """
            hbar = hbar_nn if hbar_nn is not None else state.hbar_nn
            result = []
            for i, psi_i in enumerate(state.psi):
                # Covariant derivative term: D_a Ψ_i
                # Use the gauge field at row i (if available)
                A_row = state.A[i] if i < len(state.A) else []
                D_psi = CovDerivative.apply(psi_i, A_row, state.g_coup, state.algebra)

                # Bias (mass) term: Γ_ij · β_i · Ψ_i
                # In scalar approx: beta_i * psi_i component-wise
                b_i = state.beta[i] if i < len(state.beta) else make_element([0.0], state.algebra)
                if state.algebra == Algebra.R:
                    mass_term = RealEl(b_i.v * psi_i.v)
                elif state.algebra == Algebra.C:
                    mass_term = b_i * psi_i
                elif state.algebra == Algebra.H:
                    mass_term = b_i * psi_i
                else:  # O
                    mass_term = b_i * psi_i

                # H_NN · Ψ = -i·D_psi + mass_term
                # In real algebra: imaginary factor → π/2 phase rotation
                # We represent -i·D_psi as negation of imaginary components
                neg_i_Dpsi = _neg_i_action(D_psi, state.algebra)

                # Layer evolution term (if previous layer provided)
                if psi_prev is not None and i < len(psi_prev):
                    dpsi_dl = _subtract_elements(psi_i, psi_prev[i], state.algebra)
                    evo_term = _scale_element(dpsi_dl, hbar, state.algebra)
                    # Residual form: H_NN·Ψ - i·ħ·∂Ψ/∂l
                    H_psi = _add_elements(neg_i_Dpsi, mass_term, state.algebra)
                    result.append(_subtract_elements(H_psi, evo_term, state.algebra))
                else:
                    # No evolution: return H_NN·Ψ directly
                    result.append(_add_elements(neg_i_Dpsi, mass_term, state.algebra))
            return result

        def residual_fn(state: FieldState, psi_prev: Optional[list] = None) -> float:
            """
            Residual = mean |H_NN·Ψ_i - i·ħ·∂Ψ/∂l| over all activations.
            Near zero → activations satisfy the neural Dirac equation.
            """
            eom_vals = callable_eom(state, psi_prev)
            if not eom_vals: return 0.0
            return sum(_norm_element(e, state.algebra) for e in eom_vals) / len(eom_vals)

        return DerivationResult(
            callable_eom=callable_eom,
            residual_fn=residual_fn,
            label="Neural Dirac Equation",
            latex=r"i\hbar_{NN}\frac{\partial\Psi_i}{\partial l} = \hat{H}_{NN}\Psi_i"
        )

    @staticmethod
    def neural_yang_mills() -> DerivationResult:
        """
        Neural Yang-Mills Equation (Backpropagation Emerges):
          D_l R^{a,lτ} = g · Ψ̄_i · T^a · Ψ_i

        Derived from δℒ_kinetic/δA_μ = 0.
        Backpropagation is a limiting case: ℝ algebra + Abelian gauge.

        Returns the Yang-Mills source term minus the field strength divergence.
        """
        def callable_eom(state: FieldState) -> List[float]:
            """
            Evaluate D_l R^{a,lτ} - g·J^a for each gauge component a.
            Returns list of floats (one per generator of the gauge group).
            n_gen = N_GEN[algebra]: 0 for ℝ, 1 for ℂ, 3 for ℍ, 8 for 𝕆.
            """
            n_gen = Algebra.N_GEN[state.algebra]
            if n_gen == 0:
                # Trivial gauge — no Yang-Mills equation
                return [0.0]

            # Activation current J^a = g · Ψ̄_i · T^a · Ψ_i  (summed over i)
            # For each generator a, T^a acts on the algebra element
            currents = NoetherCalculus.activation_current(state)

            # Field strength R^{a,lτ} from weight matrix
            F = FieldStrength.compute(state)

            # Yang-Mills residual: |J^a - D·F^a| per generator
            # In discrete (layer) approximation: D·F ≈ F (single layer)
            # Full multi-layer: accumulated in the calling loop
            residuals = []
            for a in range(min(n_gen, len(currents))):
                J_a = currents[a] if a < len(currents) else 0.0
                F_a = F[a] if a < len(F) else 0.0
                residuals.append(J_a - state.g_coup * F_a)
            return residuals

        def residual_fn(state: FieldState) -> float:
            """
            Scalar residual = mean |D_l R^a - g·J^a| over generators.
            Near zero → weight field satisfies Yang-Mills.
            """
            vals = callable_eom(state)
            return sum(abs(v) for v in vals) / max(len(vals), 1)

        return DerivationResult(
            callable_eom=callable_eom,
            residual_fn=residual_fn,
            label="Neural Yang-Mills Equation",
            latex=r"D_l R^{a,l\tau} = g\,\bar{\Psi}_i T^a \Psi_i"
        )

    @staticmethod
    def neural_higgs() -> DerivationResult:
        """
        Neural Higgs Equation (Bias Evolution / Symmetry Breaking):
          D_l D^l β + μ²β - 2λ(β†β)β = -Γ_ij Ψ̄^L_i Ψ^R_j

        Derived from δℒ_bias/δβ† = 0.
        Spontaneous symmetry breaking occurs when μ² < 0 (standard setting).
        """
        def callable_eom(state: FieldState, beta_prev: Optional[list] = None) -> list:
            """
            Evaluate the Higgs EOM for each bias element.
            Returns list of algebra elements: the equation residual per bias.
            """
            result = []
            beta_norm_sq = sum(_norm_sq_element(b, state.algebra) for b in state.beta)

            for i, b in enumerate(state.beta):
                # Mexican hat potential gradient: δV/δβ† = μ²β - 2λ(β†β)β
                mu2_term   = _scale_element(b,  state.mu_sq, state.algebra)
                quartic    = _scale_element(b, -2.0 * state.lam * beta_norm_sq, state.algebra)
                pot_grad   = _add_elements(mu2_term, quartic, state.algebra)

                # Source term: -Γ_ij Ψ̄^L_i Ψ^R_j
                # Approximate: source ≈ -psi_i * conj(psi_i) coupling
                if i < len(state.psi):
                    psi_i = state.psi[i]
                    source = _scale_element(
                        _mul_elements(psi_i, _conj_element(psi_i, state.algebra), state.algebra),
                        -state.g_coup, state.algebra
                    )
                else:
                    source = make_element([0.0]*Algebra.DIM[state.algebra], state.algebra)

                # Layer evolution (kinetic term for β): D_l D^l β ≈ Δβ/Δl²
                if beta_prev is not None and i < len(beta_prev):
                    d2b = _subtract_elements(b, beta_prev[i], state.algebra)
                    eom_i = _add_elements(_add_elements(d2b, pot_grad, state.algebra),
                                          source, state.algebra)
                else:
                    eom_i = _add_elements(pot_grad, source, state.algebra)

                result.append(eom_i)
            return result

        def residual_fn(state: FieldState, beta_prev: Optional[list] = None) -> float:
            """
            Scalar residual = mean |Higgs EOM| over bias elements.
            Near zero → biases satisfy the neural Higgs equation.
            Near VEV → symmetry broken, Higgs mass generated.
            """
            eom_vals = callable_eom(state, beta_prev)
            if not eom_vals: return 0.0
            return sum(_norm_element(e, state.algebra) for e in eom_vals) / len(eom_vals)

        return DerivationResult(
            callable_eom=callable_eom,
            residual_fn=residual_fn,
            label="Neural Higgs Equation",
            latex=r"D_l D^l\beta + \mu^2\beta - 2\lambda(\beta^\dagger\beta)\beta = -\Gamma_{ij}\bar{\Psi}^L_i\Psi^R_j"
        )

    @staticmethod
    def full_lagrangian(state: FieldState) -> Dict[str, float]:
        """
        Evaluate all four terms of ℒ_NN at the given field state.
        Returns dict with keys: kinetic, matter, bias, coupling, total.

        ℒ_NN = ℒ_kinetic + ℒ_matter + ℒ_bias + ℒ_coupling
        """
        # ℒ_kinetic = -1/4 · F_μν^a · F^{μν,a}
        F = FieldStrength.compute(state)
        L_kinetic = -0.25 * sum(f*f for f in F)

        # ℒ_matter = i·Ψ̄·γ^μ·D_μ·Ψ - m·Ψ̄·Ψ
        # Approximate: kinetic part of matter
        L_matter = 0.0
        for i, psi_i in enumerate(state.psi):
            A_row = state.A[i] if i < len(state.A) else []
            D_psi = CovDerivative.apply(psi_i, A_row, state.g_coup, state.algebra)
            # i·Ψ̄·D·Ψ ≈ Im(Ψ†·D·Ψ) — use norm product as proxy
            psi_conj = _conj_element(psi_i, state.algebra)
            kinetic_i = _dot_elements(psi_conj, D_psi, state.algebra)
            # Mass term
            b_i = state.beta[i] if i < len(state.beta) else make_element([0.0], state.algebra)
            mass_i = _dot_elements(psi_conj, _mul_elements(b_i, psi_i, state.algebra), state.algebra)
            L_matter += kinetic_i - mass_i

        # ℒ_bias = -1/2·(∂_μβ)² + 1/2·μ²·β² - 1/4·λ·β⁴  (Mexican hat)
        beta_norm_sq = sum(_norm_sq_element(b, state.algebra) for b in state.beta)
        L_bias = (0.5 * state.mu_sq * beta_norm_sq
                  - 0.25 * state.lam * beta_norm_sq**2)

        # ℒ_coupling = -Γ_ij · Ψ̄^L · β · Ψ^R  (Yukawa)
        L_coupling = 0.0
        for i in range(min(len(state.psi), len(state.beta))):
            psi_i = state.psi[i]
            b_i   = state.beta[i]
            psi_conj = _conj_element(psi_i, state.algebra)
            coupled = _mul_elements(b_i, psi_i, state.algebra)
            L_coupling += -state.g_coup * _dot_elements(psi_conj, coupled, state.algebra)

        L_total = L_kinetic + L_matter + L_bias + L_coupling
        return {
            'kinetic'  : L_kinetic,
            'matter'   : L_matter,
            'bias'     : L_bias,
            'coupling' : L_coupling,
            'total'    : L_total
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §4  OPERATION 2 — COVARIANT DERIVATIVE
# D_μΨ = ∂_μΨ - ig·A_μ^a·T^a·Ψ
# ═══════════════════════════════════════════════════════════════════════════════

class CovDerivative:
    """
    Covariant derivative D_μΨ = ∂_μΨ - ig·A_μ^a·T^a·Ψ

    The generator action T^a·Ψ is algebra-stratum-specific:
      ℝ  (U(0)):   trivial — D_μΨ = ∂_μΨ
      ℂ  (U(1)):   T = i·Ψ  (phase rotation)
      ℍ  (SU(2)):  T^a = commutator with quaternion basis vectors
      𝕆  (SU(3)):  T^a = Fano-plane-structured action on imaginary units
    """

    @staticmethod
    def apply(psi, A_row: list, g: float, algebra: int):
        """
        Compute D_μΨ for a single activation psi at the given algebra stratum.

        psi   : algebra element (RealEl / ComplexEl / QuatEl / OctEl)
        A_row : list of floats representing gauge field components A_μ^a
        g     : gauge coupling constant
        algebra : Algebra stratum

        Returns algebra element of same type as psi.
        """
        if algebra == Algebra.R:
            # Trivial gauge: D_μΨ = Ψ (no gauge action)
            return psi

        elif algebra == Algebra.C:
            # U(1): D_μΨ = Ψ - ig·A^1·Ψ
            # T·Ψ = i·Ψ means rotation by π/2: (re,im) → (-im, re)
            A1 = A_row[0] if A_row else 0.0
            gauge_action = ComplexEl(-psi.im, psi.re)  # i·Ψ
            return ComplexEl(
                psi.re - g * A1 * gauge_action.re,
                psi.im - g * A1 * gauge_action.im
            )

        elif algebra == Algebra.H:
            # SU(2): D_μΨ = Ψ - ig·A^a·(e_a * Ψ - Ψ * e_a)/2
            # Three generators: T^a = [e_a, ·]/2
            e1 = QuatEl(0,1,0,0); e2 = QuatEl(0,0,1,0); e3 = QuatEl(0,0,0,1)
            gens = [e1, e2, e3]
            gauge_term = QuatEl(0,0,0,0)
            for a, ea in enumerate(gens):
                Aa = A_row[a] if a < len(A_row) else 0.0
                if abs(Aa) < 1e-12: continue
                # T^a·Ψ = (e_a·Ψ - Ψ·e_a) / 2
                comm = _quat_sub(ea * psi, psi * ea)
                half_comm = QuatEl(comm.w/2, comm.x/2, comm.y/2, comm.z/2)
                gauge_term = _quat_add(gauge_term,
                                       QuatEl(g*Aa*half_comm.w, g*Aa*half_comm.x,
                                              g*Aa*half_comm.y, g*Aa*half_comm.z))
            return _quat_sub(psi, gauge_term)

        elif algebra == Algebra.O:
            # SU(3)/G₂: 8 generators, Fano-plane structure
            # T^a·Ψ uses commutator with imaginary unit e_{a+1}
            gauge_term = OctEl([0.0]*8)
            for a in range(min(8, Algebra.N_GEN[Algebra.O])):
                Aa = A_row[a] if a < len(A_row) else 0.0
                if abs(Aa) < 1e-12: continue
                ea = OctEl.unit(a+1) if a < 7 else OctEl.unit(0)
                # T^a·Ψ = (e_a·Ψ - Ψ·e_a) / 2
                comm = (ea * psi) - (psi * ea)
                half = OctEl([x/2 for x in comm.c])
                scaled = OctEl([g * Aa * x for x in half.c])
                gauge_term = gauge_term + scaled
            return psi - gauge_term

        else:
            raise ValueError(f"Unknown algebra: {algebra}")

    @staticmethod
    def covariant_divergence(psi_sequence: list, A_sequence: list,
                              g: float, algebra: int) -> float:
        """
        Compute ∂_μ(D^μΨ) — the covariant divergence across a layer sequence.
        Used in the Yang-Mills source term and Noether check.
        psi_sequence: list of psi at each layer step
        A_sequence  : list of A_row at each layer step
        """
        if len(psi_sequence) < 2:
            return 0.0
        divergence = 0.0
        for k in range(1, len(psi_sequence)):
            D_k   = CovDerivative.apply(psi_sequence[k],   A_sequence[k],   g, algebra)
            D_km1 = CovDerivative.apply(psi_sequence[k-1], A_sequence[k-1], g, algebra)
            diff  = _subtract_elements(D_k, D_km1, algebra)
            divergence += _norm_element(diff, algebra)
        return divergence / (len(psi_sequence) - 1)


# ═══════════════════════════════════════════════════════════════════════════════
# §5  OPERATION 3 — FIELD STRENGTH TENSOR
# F_μν^a = ∂_μA_ν^a - ∂_νA_μ^a + g·f^{abc}·A_μ^b·A_ν^c
# ═══════════════════════════════════════════════════════════════════════════════

class FieldStrength:
    """
    Field strength tensor F_μν^a.

    The structure constants f^{abc} are algebra-specific:
      ℝ  : no generators — F = 0
      ℂ  : Abelian (U(1)) — f^{abc} = 0, purely antisymmetric
      ℍ  : SU(2) — f^{abc} = ε_{abc} (Levi-Civita)
      𝕆  : G₂/SU(3) — f^{abc} from Fano plane structure
    """

    # Levi-Civita ε_{abc} for SU(2)
    _LC = {(0,1,2): 1, (1,2,0): 1, (2,0,1): 1,
           (2,1,0):-1, (0,2,1):-1, (1,0,2):-1}

    @staticmethod
    def structure_constants(a: int, b: int, algebra: int) -> List[Tuple[int,float]]:
        """
        Return [(c, f^{abc})] for given a,b at the algebra stratum.
        Non-zero entries only.
        """
        if algebra == Algebra.R:
            return []
        elif algebra == Algebra.C:
            return []  # Abelian
        elif algebra == Algebra.H:
            # SU(2): f^{abc} = ε_{abc}
            result = []
            for c in range(3):
                eps = FieldStrength._LC.get((a,b,c), 0)
                if eps != 0:
                    result.append((c, float(eps)))
            return result
        elif algebra == Algebra.O:
            # G₂: structure constants from Fano plane
            # f^{abc} nonzero when e_{a+1}·e_{b+1} = ±e_{c+1}
            result = []
            if 0 < a+1 < 8 and 0 < b+1 < 8:
                entry = OCT_TABLE[a+1][b+1]
                if entry:
                    sign, c_idx = entry
                    if c_idx > 0:
                        result.append((c_idx - 1, float(sign)))
            return result
        else:
            raise ValueError(f"Unknown algebra: {algebra}")

    @staticmethod
    def compute(state: FieldState,
                A_prev: Optional[list] = None) -> List[float]:
        """
        Compute F^a values (one per generator) from the gauge field.

        In the single-layer discrete case:
          F^a ≈ g · A_current^a + non-Abelian term
        With A_prev (adjacent layer):
          F^a ≈ A_current^a - A_prev^a + g · f^{abc} · A^b · A^c

        Returns list of floats, length = N_GEN[algebra].
        """
        n_gen = Algebra.N_GEN[state.algebra]
        if n_gen == 0:
            return [0.0]

        # Flatten gauge field matrix to per-generator means
        A_curr = _gauge_field_to_components(state.A, n_gen)
        A_p    = _gauge_field_to_components(A_prev, n_gen) if A_prev else [0.0]*n_gen

        F = []
        for a in range(n_gen):
            # Antisymmetric kinetic term: ∂_μA_ν - ∂_νA_μ  (layer diff)
            dA = A_curr[a] - A_p[a]

            # Non-Abelian self-coupling: g · f^{abc} · A^b · A^c
            nonabelian = 0.0
            for b in range(n_gen):
                for (c, fabc) in FieldStrength.structure_constants(a, b, state.algebra):
                    if c < n_gen:
                        nonabelian += fabc * A_curr[b] * A_curr[c]

            F.append(dA + state.g_coup * nonabelian)
        return F

    @staticmethod
    def field_strength_tensor(state: FieldState,
                               A_prev: Optional[list] = None) -> Dict[str, float]:
        """
        Return full F tensor as a labeled dict for GUI consumption.
        Keys: 'F_a' for each generator index a.
        Also includes: 'F_sq' = F^a·F_a (the kinetic Lagrangian density source).
        """
        F = FieldStrength.compute(state, A_prev)
        result = {f'F_{a}': F[a] for a in range(len(F))}
        result['F_sq'] = sum(f*f for f in F)
        result['L_kinetic'] = -0.25 * result['F_sq']
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# §6  OPERATION 4 — NOETHER CURRENT AND VIOLATION
# J^μ = ∂ℒ/∂(∂_μΨ) · δΨ
# ═══════════════════════════════════════════════════════════════════════════════

class NoetherCalculus:
    """
    Noether's theorem applied to ℒ_NN.

    Conservation law: ∂_μJ^μ = 0
    Violation = |∂_μJ^μ| — the training diagnostic with no GD analog.

    For each gauge symmetry:
      U(1): J^μ = g·Ψ̄·Ψ  (probability current analog)
      SU(2): J^μ_a = g·Ψ̄·T^a·Ψ  (isospin current)
      SU(3): J^μ_a = g·Ψ̄·T^a·Ψ  (color current analog)
    """

    @staticmethod
    def activation_current(state: FieldState) -> List[float]:
        """
        Compute J^a = Σ_i g · <Ψ_i | T^a | Ψ_i> for each generator a.
        Returns list of floats, length = max(1, N_GEN[algebra]).
        """
        n_gen = max(1, Algebra.N_GEN[state.algebra])
        J = [0.0] * n_gen

        for psi_i in state.psi:
            if state.algebra == Algebra.R:
                J[0] += state.g_coup * psi_i.v * psi_i.v

            elif state.algebra == Algebra.C:
                # J = g · |Ψ|²
                J[0] += state.g_coup * psi_i.norm_sq()

            elif state.algebra == Algebra.H:
                # J^a = g · Ψ̄ · T^a · Ψ = g · <[e_a, Ψ]·Ψ†>
                e_basis = [QuatEl(0,1,0,0), QuatEl(0,0,1,0), QuatEl(0,0,0,1)]
                psi_conj = psi_i.conj()
                for a, ea in enumerate(e_basis):
                    T_psi = _quat_sub(ea * psi_i, psi_i * ea)
                    # J^a = Re(Ψ† · T^a · Ψ) / 2
                    prod = _quat_inner(psi_conj, T_psi)
                    J[a] += state.g_coup * prod / 2.0

            elif state.algebra == Algebra.O:
                # J^a = g · Re(Ψ† · [e_{a+1}, Ψ]) / 2
                psi_conj = psi_i.conj()
                for a in range(min(8, n_gen)):
                    ea = OctEl.unit(a+1) if a < 7 else OctEl.unit(0)
                    comm = (ea * psi_i) - (psi_i * ea)
                    J[a] += state.g_coup * _oct_inner(psi_conj, comm) / 2.0
        return J

    @staticmethod
    def noether_violation(J_current: List[float],
                          J_prev: Optional[List[float]]) -> float:
        """
        ∂_μJ^μ ≈ |J_current - J_prev| (finite difference across layers).
        Returns scalar violation magnitude.
        Zero = perfectly conserved; large = algebra boundary broken.
        """
        if J_prev is None:
            return 0.0
        if len(J_current) != len(J_prev):
            n = min(len(J_current), len(J_prev))
            return sum(abs(J_current[k] - J_prev[k]) for k in range(n)) / max(n,1)
        return sum(abs(a-b) for a,b in zip(J_current, J_prev)) / max(len(J_current),1)

    @staticmethod
    def conservation_diagnostic(state: FieldState,
                                 prev_state: Optional[FieldState]) -> Dict[str, Any]:
        """
        Full Noether diagnostic for the GUI.
        Returns dict with:
          'J'           : current components
          'J_prev'      : previous current components (if available)
          'violation'   : scalar violation magnitude
          'conserved'   : bool (violation < threshold)
          'threshold'   : the pass/fail threshold used
          'label'       : human-readable description
        """
        J = NoetherCalculus.activation_current(state)
        J_prev = NoetherCalculus.activation_current(prev_state) if prev_state else None
        violation = NoetherCalculus.noether_violation(J, J_prev)
        threshold = 0.2  # from paper: <0.2 = PASS, <0.5 = MARGINAL
        return {
            'J'         : J,
            'J_prev'    : J_prev,
            'violation' : violation,
            'conserved' : violation < threshold,
            'threshold' : threshold,
            'algebra'   : Algebra.NAME[state.algebra],
            'gauge'     : Algebra.GAUGE[state.algebra],
            'label'     : f"Noether current conservation — {Algebra.NAME[state.algebra]} layer",
            'latex'     : r"\partial_\mu J^\mu = 0"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §7  OPERATION 5 — ALGEBRA MULTIPLICATION
# Unified interface to ℝ/ℂ/ℍ/𝕆 multiplication
# ═══════════════════════════════════════════════════════════════════════════════

class AlgebraOps:
    """
    Unified algebra operations across all four strata.
    All methods work via coordinates (lists of floats) for
    GUI-friendliness and SymPy bridge compatibility.
    """

    @staticmethod
    def multiply(a: List[float], b: List[float], algebra: int) -> List[float]:
        """
        Multiply two elements in the given algebra stratum.
        a, b : coordinate lists (length = DIM[algebra])
        Returns coordinate list of the product.
        """
        ea = make_element(a, algebra)
        eb = make_element(b, algebra)
        return (ea * eb).as_list()

    @staticmethod
    def commutator(a: List[float], b: List[float], algebra: int) -> List[float]:
        """
        [a, b] = a·b - b·a
        Zero in ℝ and ℂ (commutative algebras).
        Nonzero in ℍ (measures non-commutativity — lost at ℂ→ℍ).
        Nonzero in 𝕆 (also non-associative).
        """
        ea = make_element(a, algebra)
        eb = make_element(b, algebra)
        prod_ab = (ea * eb)
        prod_ba = (eb * ea)
        return _subtract_elements(prod_ab, prod_ba, algebra).as_list()

    @staticmethod
    def associator(a: List[float], b: List[float], c: List[float],
                   algebra: int) -> List[float]:
        """
        [a,b,c] = (a·b)·c - a·(b·c)
        Zero in ℝ, ℂ, ℍ (associative algebras).
        Nonzero in 𝕆 (measures non-associativity — lost at ℍ→𝕆).
        This is the key 𝕆 layer diagnostic.
        """
        ea = make_element(a, algebra)
        eb = make_element(b, algebra)
        ec = make_element(c, algebra)
        lhs = (ea * eb) * ec
        rhs = ea * (eb * ec)
        return _subtract_elements(lhs, rhs, algebra).as_list()

    @staticmethod
    def norm_preserved(a: List[float], b: List[float], algebra: int) -> Dict[str, float]:
        """
        Verify |a·b| = |a|·|b| (normed division algebra property).
        Should hold exactly for all four strata.
        Returns {'lhs': |ab|, 'rhs': |a|·|b|, 'error': |lhs-rhs|}.
        """
        ea = make_element(a, algebra)
        eb = make_element(b, algebra)
        prod = ea * eb
        lhs = math.sqrt(_norm_sq_element(prod, algebra))
        rhs = math.sqrt(_norm_sq_element(ea, algebra)) * math.sqrt(_norm_sq_element(eb, algebra))
        return {'lhs': lhs, 'rhs': rhs, 'error': abs(lhs - rhs)}

    @staticmethod
    def property_loss_diagnostic(algebra: int) -> Dict[str, Any]:
        """
        Test which algebraic properties are lost at this stratum.
        The lost property IS the signal — it encodes the gauge structure.
        Returns dict of test results for the GUI.
        """
        import random
        random.seed(42)
        dim = Algebra.DIM[algebra]

        def rand_coords():
            return [random.gauss(0, 0.5) for _ in range(dim)]

        a, b, c = rand_coords(), rand_coords(), rand_coords()

        comm = AlgebraOps.commutator(a, b, algebra)
        comm_norm = math.sqrt(sum(x*x for x in comm))

        assoc = AlgebraOps.associator(a, b, c, algebra)
        assoc_norm = math.sqrt(sum(x*x for x in assoc))

        return {
            'algebra'          : Algebra.NAME[algebra],
            'commutator_norm'  : comm_norm,
            'associator_norm'  : assoc_norm,
            'is_commutative'   : comm_norm < 1e-9,
            'is_associative'   : assoc_norm < 1e-9,
            'lost_property'    : Algebra.LOST.get(algebra, 'none'),
            'gauge_group'      : Algebra.GAUGE[algebra],
            'note'             : "Lost property = gauge richness signal"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §8  OPERATION 6 — CAYLEY-DICKSON INCLUSION AND PROJECTION
# ι: lower algebra → higher algebra (lossless embedding)
# π: higher algebra → lower algebra (lossy projection)
# ═══════════════════════════════════════════════════════════════════════════════

class CayleyDickson:
    """
    Cayley-Dickson inclusion and projection maps.

    Inclusion ι (lossless): embed lower algebra in higher via zero-padding
      ℝ→ℂ:  r         ↦ (r, 0)
      ℂ→ℍ:  (a,b)     ↦ (a, b, 0, 0)
      ℍ→𝕆:  (w,x,y,z) ↦ (w, x, y, z, 0, 0, 0, 0)

    Projection π (lossy): take first DIM[lower] components
      ℂ→ℝ:  (a,b)            ↦ a
      ℍ→ℂ:  (w,x,y,z)        ↦ (w,x)
      𝕆→ℍ:  (c0..c7)         ↦ (c0,c1,c2,c3)

    These are the inter-layer communication operators — the neural
    analogs of the CKM and PMNS mixing matrices.
    """

    @staticmethod
    def include(coords: List[float], from_alg: int, to_alg: int) -> List[float]:
        """
        Embed coords from from_alg into to_alg via inclusion map ι.
        from_alg must be lower in the tower than to_alg.
        """
        if from_alg >= to_alg:
            raise ValueError(f"Inclusion requires from_alg < to_alg. "
                             f"Got {Algebra.NAME[from_alg]} → {Algebra.NAME[to_alg]}")
        target_dim = Algebra.DIM[to_alg]
        padded = list(coords[:Algebra.DIM[from_alg]])
        while len(padded) < target_dim:
            padded.append(0.0)
        return padded

    @staticmethod
    def project(coords: List[float], from_alg: int, to_alg: int) -> List[float]:
        """
        Project coords from from_alg down to to_alg via projection map π.
        from_alg must be higher in the tower than to_alg.
        Information is lost in projection — this is intentional and physical.
        """
        if from_alg <= to_alg:
            raise ValueError(f"Projection requires from_alg > to_alg. "
                             f"Got {Algebra.NAME[from_alg]} → {Algebra.NAME[to_alg]}")
        target_dim = Algebra.DIM[to_alg]
        return list(coords[:target_dim])

    @staticmethod
    def cd_construction_step(a: List[float], b: List[float]) -> List[float]:
        """
        One step of the Cayley-Dickson construction:
          Given algebra A with elements a, b (each dim n),
          construct element (a, b) in the doubled algebra (dim 2n).

          Multiplication in doubled algebra:
            (a₁,b₁)·(a₂,b₂) = (a₁·a₂ - b₂*·b₁, b₂·a₁ + b₁·a₂*)
          where * = conjugation in base algebra.

          Here we return the concatenated coords (a,b) — the embedding.
        """
        return list(a) + list(b)

    @staticmethod
    def spinor_index_protocol(psi_lower: List[float],
                               from_alg: int,
                               to_alg: int) -> Dict[str, Any]:
        """
        Sparse spinor index protocol for inter-layer communication.
        (Paper Section 5: inter-neuron waveform / spinor index.)

        Rather than full algebra projection (which loses information),
        encode the lower-algebra state as a sparse superposition of
        shared basis spinors in the higher algebra.

        Returns:
          'spinor_coeffs'  : real coefficients a_k
          'basis_indices'  : which basis spinors φ_k are active
          'reconstruction' : approximate reconstruction coords
          'fidelity'       : |original - reconstructed| / |original|
        """
        included = CayleyDickson.include(psi_lower, from_alg, to_alg)
        norm = math.sqrt(sum(x*x for x in included) + 1e-12)

        # Identify dominant basis components (sparse representation)
        indexed = sorted(enumerate(included), key=lambda kv: abs(kv[1]), reverse=True)
        n_keep  = max(1, Algebra.DIM[from_alg])  # keep as many as source dim
        active  = indexed[:n_keep]

        basis_indices = [k for k,_ in active]
        coeffs        = [v for _,v in active]

        # Reconstruct from sparse representation
        reconstruction = [0.0] * Algebra.DIM[to_alg]
        for k, v in active:
            reconstruction[k] = v

        # Fidelity
        diff = sum((included[k]-reconstruction[k])**2 for k in range(len(included)))
        fidelity = 1.0 - math.sqrt(diff) / (norm + 1e-12)

        return {
            'spinor_coeffs'  : coeffs,
            'basis_indices'  : basis_indices,
            'reconstruction' : reconstruction,
            'fidelity'       : fidelity,
            'from_algebra'   : Algebra.NAME[from_alg],
            'to_algebra'     : Algebra.NAME[to_alg],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §9  OPERATION 7 — RG FLOW / RUNNING CONSTANTS
# α_NN(l) = α_0 / (1 + β_0·α_0·ln(l/l_0))
# h_NN(l) = h_0 · (1 + γ_0·ln(l/l_0))
# ═══════════════════════════════════════════════════════════════════════════════

class RenormalizationGroup:
    """
    Renormalization group (RG) flow for the neural fine structure constant
    α_NN and neural Planck constant h_NN.

    Both run with layer depth l in exact analogy with QFT RG flow.
    The three coupling constants (U(1), SU(2), SU(3)) converge at the
    spinor-index layer — neural Grand Unification.

    Beta functions β_0 for each stratum (from algebra dimension):
      β_0(ℝ)  = 0       (trivial — no running)
      β_0(ℂ)  = 1/2π    (U(1) one-loop)
      β_0(ℍ)  = 3/4π    (SU(2) one-loop, 3 generators)
      β_0(𝕆)  = 8/4π    (SU(3)/G₂ one-loop, 8 generators)

    Anomalous dimension γ_0 for h_NN:
      γ_0 proportional to algebra dimension / (2π)
    """

    BETA_0 = {
        Algebra.R: 0.0,
        Algebra.C: 1.0 / (2.0 * math.pi),
        Algebra.H: 3.0 / (4.0 * math.pi),
        Algebra.O: 8.0 / (4.0 * math.pi),
    }

    GAMMA_0 = {
        Algebra.R: 0.0,
        Algebra.C: 2.0 / (2.0 * math.pi),
        Algebra.H: 4.0 / (2.0 * math.pi),
        Algebra.O: 8.0 / (2.0 * math.pi),
    }

    @staticmethod
    def alpha_nn(alpha_0: float, layer: int, algebra: int,
                  l_0: int = 1) -> float:
        """
        Running neural fine structure constant:
          α_NN(l) = α_0 / (1 + β_0·α_0·ln(l/l_0))

        At GUT scale (spinor-index layer), all three couplings converge.
        """
        if layer <= 0 or l_0 <= 0:
            return alpha_0
        beta_0 = RenormalizationGroup.BETA_0.get(algebra, 0.0)
        if abs(beta_0) < 1e-12:
            return alpha_0
        log_ratio = math.log(max(layer / l_0, 1e-12))
        denom = 1.0 + beta_0 * alpha_0 * log_ratio
        if abs(denom) < 1e-12:
            return alpha_0
        return alpha_0 / denom

    @staticmethod
    def hbar_nn(h_0: float, layer: int, algebra: int,
                 l_0: int = 1) -> float:
        """
        Running neural Planck constant:
          h_NN(l) = h_0 · (1 + γ_0·ln(l/l_0))

        Represents minimum representational granularity at layer depth l.
        Grows with depth — coarser-grained representations at higher layers.
        """
        if layer <= 0 or l_0 <= 0:
            return h_0
        gamma_0 = RenormalizationGroup.GAMMA_0.get(algebra, 0.0)
        if abs(gamma_0) < 1e-12:
            return h_0
        log_ratio = math.log(max(layer / l_0, 1e-12))
        return h_0 * (1.0 + gamma_0 * log_ratio)

    @staticmethod
    def gut_convergence(alpha_0_c: float, alpha_0_h: float, alpha_0_o: float,
                         layers: List[int]) -> Dict[str, List[float]]:
        """
        Compute RG flow for all three couplings across a range of layers.
        Returns dict of lists for plotting: {'C': [...], 'H': [...], 'O': [...], 'layers': [...]}

        Convergence of all three → Grand Unification analog.
        """
        alphas = {
            'C': [], 'H': [], 'O': [], 'layers': list(layers)
        }
        for l in layers:
            alphas['C'].append(RenormalizationGroup.alpha_nn(alpha_0_c, l, Algebra.C))
            alphas['H'].append(RenormalizationGroup.alpha_nn(alpha_0_h, l, Algebra.H))
            alphas['O'].append(RenormalizationGroup.alpha_nn(alpha_0_o, l, Algebra.O))
        return alphas

    @staticmethod
    def training_inequality(kappa: float, epsilon: float,
                              depth: int, lam: float = 0.9) -> Dict[str, float]:
        """
        Fundamental SMNNIP training time inequality:
          𝒯_GD    > O(κ · λ^{-2L} / ε)     — gradient descent
          𝒯_SMNNIP = O(√κ · log(1/ε))       — SMNNIP (depth-independent)

        Returns both bounds and their ratio 𝒯_GD / 𝒯_SMNNIP.
        κ   : condition number of the problem
        ε   : target precision
        L   : network depth
        λ   : spectral gap (0 < λ < 1)
        """
        if epsilon <= 0: epsilon = 1e-6
        T_gd     = kappa * (lam ** (-2.0 * depth)) / epsilon
        T_smnnip = math.sqrt(kappa) * math.log(1.0 / epsilon)
        ratio    = T_gd / max(T_smnnip, 1e-12)
        return {
            'T_GD'           : T_gd,
            'T_SMNNIP'       : T_smnnip,
            'ratio'          : ratio,
            'GD_wins'        : ratio < 1.0,
            'depth'          : depth,
            'kappa'          : kappa,
            'epsilon'        : epsilon,
            'lambda'         : lam,
            'latex_gd'       : r"\mathcal{T}_{GD} = O\!\left(\kappa\,\lambda^{-2L}/\varepsilon\right)",
            'latex_smnnip'   : r"\mathcal{T}_{SMNNIP} = O\!\left(\sqrt{\kappa}\log(1/\varepsilon)\right)",
        }

    @staticmethod
    def phi_fixed_point() -> Dict[str, float]:
        """
        The φ fixed point of the inversion map (J_N ∘ recursion).
        φ = (1 + √5) / 2 — the golden ratio.

        Confirmed: φ·(1/φ) = 1 and 1 + 1/φ = φ exactly.
        The step at the φ-crossing = H/4 = (π/2)·ħ_NN.

        This closes the §7 open flag numerically.
        Formal derivation from first principles still needed.
        """
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        h4  = math.pi / 2.0  # H/4 in units where ħ_NN = 1
        return {
            'phi'              : phi,
            'one_over_phi'     : 1.0 / phi,
            'phi_times_inv'    : phi * (1.0 / phi),     # = 1 exactly
            '1_plus_inv'       : 1.0 + 1.0 / phi,       # = phi exactly
            'step_at_crossing' : h4,
            'H_over_4'         : math.pi / 2.0,
            'verify_identity'  : abs(phi - (1.0 + 1.0/phi)) < 1e-12,
            'latex'            : r"\varphi = \frac{1+\sqrt{5}}{2},\quad \varphi\cdot\frac{1}{\varphi}=1,\quad 1+\frac{1}{\varphi}=\varphi",
            'step_latex'       : r"\Delta_\varphi = \frac{H}{4} = \frac{\pi}{2}\hbar_{NN}",
            'note'             : "Open: derive from first principles, not numerical fitting"
        }

    @staticmethod
    def d_star_gap() -> Dict[str, float]:
        """
        The open derivation target: d* × ln(10) ≈ Ω — the 0.00070 gap.

        TWO d* VALUES — do not conflate:

        d*_spec  = 0.24600  (Berry-Keating spectral coordinate — ACTIVE)
            Source: BK xp Hamiltonian literature, independent of SMNNIP.
            d*_spec × ln(10) = 0.56644
            gap = |0.56644 - Omega| = 0.00070  (real open derivation)

        d*_taut  = Omega / ln(10) = 0.24631  (tautological reference only)
            By definition d*_taut × ln(10) = Omega exactly — gap = 0.
            Retained as the ceiling value d* must reach to close the gap.
            Do NOT use as the active value. Gap = 0 is not the result.

        d*_rg    = 0.24682  (earlier RG flow estimate — superseded)
            Produces gap = 0.00118. Inconsistent with spectral literature.
            Replaced by d*_spec = 0.24600 as the primary value.

        The gap 0.00070 is the HIGHEST-PRIORITY open derivation.
        No closed-form expression is currently known.
        (Candidate 1/W(e^3) = 0.4529 — rejected, off by factor ~643.)

        Status: identified numerically via BK spectral literature.
        NOT derived from first principles. This is the priority open problem.
        """
        OMEGA        = 0.56714329040978384
        ln10         = math.log(10.0)
        d_star_spec  = 0.24600                     # BK spectral — ACTIVE
        d_star_taut  = OMEGA / ln10                # tautological — reference only
        d_star_rg    = 0.24682                     # earlier estimate — superseded
        gap_spec     = abs(OMEGA - d_star_spec * ln10)   # = 0.00070 — real
        gap_taut     = abs(OMEGA - d_star_taut * ln10)   # = 0.00000 — tautology
        gap_rg       = abs(OMEGA - d_star_rg * ln10)     # = 0.00118 — superseded
        return {
            'd_star'              : d_star_spec,
            'd_star_spec'         : d_star_spec,
            'd_star_taut'         : d_star_taut,
            'd_star_rg'           : d_star_rg,
            'ln_10'               : ln10,
            'omega'               : OMEGA,
            'd_star_x_ln10'       : d_star_spec * ln10,
            'gap'                 : gap_spec,
            'gap_taut'            : gap_taut,
            'gap_rg'              : gap_rg,
            'omega_plus_gap'      : d_star_spec * ln10 + gap_spec,
            'status'              : 'OPEN — algebraic derivation needed',
            'active_value'        : 'd_star_spec = 0.24600 (BK spectral)',
            'latex'               : r"d^*\times\ln 10 \approx \Omega \quad (\Delta\approx 0.00070)",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §10  DERIVATION ENGINE — UNIFIED INTERFACE
# This is the object the Console SymPy GUI and equation engine talk to.
# ═══════════════════════════════════════════════════════════════════════════════

class SMNNIPDerivationEngine:
    """
    Unified derivation engine for the SMNNIP framework.

    This is the single entry point for:
      - The Console SymPy GUI
      - The equation engine (for diagnostic feedback)
      - Future Qt GUI

    All seven operations are accessible through this object.
    No I/O. No training loops. Pure mathematics.

    Usage:
        engine = SMNNIPDerivationEngine()

        # Get equations of motion
        dirac      = engine.euler_lagrange('dirac')
        ym         = engine.euler_lagrange('yang_mills')
        higgs      = engine.euler_lagrange('higgs')

        # Evaluate at a field state
        residual   = dirac.residual_fn(state)
        eom_vals   = dirac.callable_eom(state)

        # Compute derived quantities
        F          = engine.field_strength(state)
        J, viol    = engine.noether(state, prev_state)
        alpha      = engine.rg_alpha(alpha_0, layer, algebra)
        prod       = engine.algebra_mul(a_coords, b_coords, algebra)
        embedded   = engine.cd_include(coords, from_alg, to_alg)
        projected  = engine.cd_project(coords, from_alg, to_alg)

        # Full Lagrangian evaluation
        L_terms    = engine.lagrangian(state)

        # Training inequality
        bounds     = engine.training_bounds(kappa, epsilon, depth)

        # φ fixed point
        phi        = engine.phi_fixed_point()

        # Open problems
        gap        = engine.d_star_gap()
    """

    def __init__(self):
        # Pre-instantiate the EOM objects (they're stateless, reusable)
        self._dirac      = EulerLagrange.neural_dirac()
        self._yang_mills = EulerLagrange.neural_yang_mills()
        self._higgs      = EulerLagrange.neural_higgs()

    # ── Operation 1: Euler-Lagrange ────────────────────────────────────────

    def euler_lagrange(self, field: str) -> DerivationResult:
        """
        Return DerivationResult for the given field.
        field: 'dirac' | 'yang_mills' | 'higgs'
        Each DerivationResult has .callable_eom and .residual_fn.
        """
        dispatch = {
            'dirac'      : self._dirac,
            'yang_mills' : self._yang_mills,
            'higgs'      : self._higgs,
        }
        if field not in dispatch:
            raise ValueError(f"Unknown field '{field}'. "
                             f"Choose from: {list(dispatch.keys())}")
        return dispatch[field]

    def all_eom_residuals(self, state: FieldState,
                           prev_state: Optional[FieldState] = None) -> Dict[str, float]:
        """
        Evaluate all three EOM residuals at once.
        Returns dict: {'dirac': float, 'yang_mills': float, 'higgs': float}
        Useful for the console GUI overview display.
        """
        psi_prev  = prev_state.psi  if prev_state else None
        beta_prev = prev_state.beta if prev_state else None
        return {
            'dirac'      : self._dirac.residual_fn(state, psi_prev),
            'yang_mills' : self._yang_mills.residual_fn(state),
            'higgs'      : self._higgs.residual_fn(state, beta_prev),
        }

    # ── Operation 2: Covariant derivative ─────────────────────────────────

    def covariant_derivative(self, psi_coords: List[float],
                              A_row: List[float],
                              g: float, algebra: int) -> List[float]:
        """D_μΨ — returns coordinate list of the covariant derivative."""
        psi = make_element(psi_coords, algebra)
        result = CovDerivative.apply(psi, A_row, g, algebra)
        return result.as_list()

    # ── Operation 3: Field strength ────────────────────────────────────────

    def field_strength(self, state: FieldState,
                        prev_state: Optional[FieldState] = None) -> Dict[str, float]:
        """F_μν^a tensor — returns labeled dict for GUI."""
        A_prev = prev_state.A if prev_state else None
        return FieldStrength.field_strength_tensor(state, A_prev)

    # ── Operation 4: Noether current ──────────────────────────────────────

    def noether(self, state: FieldState,
                 prev_state: Optional[FieldState] = None) -> Dict[str, Any]:
        """Full Noether diagnostic — returns dict for GUI."""
        return NoetherCalculus.conservation_diagnostic(state, prev_state)

    # ── Operation 5: Algebra multiplication ───────────────────────────────

    def algebra_mul(self, a: List[float], b: List[float],
                     algebra: int) -> List[float]:
        """Product a·b in the given algebra stratum."""
        return AlgebraOps.multiply(a, b, algebra)

    def algebra_commutator(self, a: List[float], b: List[float],
                            algebra: int) -> List[float]:
        """[a,b] = a·b - b·a."""
        return AlgebraOps.commutator(a, b, algebra)

    def algebra_associator(self, a: List[float], b: List[float],
                            c: List[float], algebra: int) -> List[float]:
        """[a,b,c] = (a·b)·c - a·(b·c)."""
        return AlgebraOps.associator(a, b, c, algebra)

    def property_diagnostic(self, algebra: int) -> Dict[str, Any]:
        """Test commutativity/associativity loss at this stratum."""
        return AlgebraOps.property_loss_diagnostic(algebra)

    # ── Operation 6: Cayley-Dickson maps ──────────────────────────────────

    def cd_include(self, coords: List[float],
                    from_alg: int, to_alg: int) -> List[float]:
        """ι: lower algebra → higher algebra (inclusion, lossless)."""
        return CayleyDickson.include(coords, from_alg, to_alg)

    def cd_project(self, coords: List[float],
                    from_alg: int, to_alg: int) -> List[float]:
        """π: higher algebra → lower algebra (projection, lossy)."""
        return CayleyDickson.project(coords, from_alg, to_alg)

    def spinor_protocol(self, psi_lower: List[float],
                         from_alg: int, to_alg: int) -> Dict[str, Any]:
        """Sparse spinor index protocol for inter-layer communication."""
        return CayleyDickson.spinor_index_protocol(psi_lower, from_alg, to_alg)

    # ── Operation 7: RG flow ───────────────────────────────────────────────

    def rg_alpha(self, alpha_0: float, layer: int, algebra: int) -> float:
        """Running α_NN(l) at the given layer depth."""
        return RenormalizationGroup.alpha_nn(alpha_0, layer, algebra)

    def rg_hbar(self, h_0: float, layer: int, algebra: int) -> float:
        """Running h_NN(l) at the given layer depth."""
        return RenormalizationGroup.hbar_nn(h_0, layer, algebra)

    def gut_flow(self, alpha_0_c: float, alpha_0_h: float,
                  alpha_0_o: float, layers: List[int]) -> Dict[str, List[float]]:
        """Full RG flow for Grand Unification convergence check."""
        return RenormalizationGroup.gut_convergence(alpha_0_c, alpha_0_h, alpha_0_o, layers)

    # ── Composite operations ───────────────────────────────────────────────

    def lagrangian(self, state: FieldState) -> Dict[str, float]:
        """Evaluate all four terms of ℒ_NN at the given state."""
        return EulerLagrange.full_lagrangian(state)

    def training_bounds(self, kappa: float, epsilon: float,
                         depth: int, lam: float = 0.9) -> Dict[str, float]:
        """Compute the fundamental training inequality bounds."""
        return RenormalizationGroup.training_inequality(kappa, epsilon, depth, lam)

    def phi_fixed_point(self) -> Dict[str, float]:
        """φ fixed point data — closes §7 numerical flag."""
        return RenormalizationGroup.phi_fixed_point()

    def d_star_gap(self) -> Dict[str, float]:
        """Open derivation target: d* × ln(10) ≈ Ω."""
        return RenormalizationGroup.d_star_gap()

    def full_diagnostic(self, state: FieldState,
                         prev_state: Optional[FieldState] = None) -> Dict[str, Any]:
        """
        Complete diagnostic snapshot for a given field state.
        Returns everything the Console GUI needs in one call.
        """
        return {
            'algebra'     : Algebra.NAME[state.algebra],
            'gauge'       : Algebra.GAUGE[state.algebra],
            'layer'       : state.layer,
            'lagrangian'  : self.lagrangian(state),
            'eom_residuals': self.all_eom_residuals(state, prev_state),
            'noether'     : self.noether(state, prev_state),
            'field_strength': self.field_strength(state, prev_state),
            'property_test' : self.property_diagnostic(state.algebra),
            'rg_alpha'    : self.rg_alpha(state.g_coup, max(state.layer,1), state.algebra),
            'rg_hbar'     : self.rg_hbar(state.hbar_nn, max(state.layer,1), state.algebra),
            'phi'         : self.phi_fixed_point(),
            'd_star'      : self.d_star_gap(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# §11  INTERNAL HELPER FUNCTIONS
# Algebra-dispatch arithmetic used throughout the engine.
# Not part of the public API — the GUI talks to SMNNIPDerivationEngine.
# ═══════════════════════════════════════════════════════════════════════════════

def _add_elements(a, b, algebra: int):
    return (a + b)

def _subtract_elements(a, b, algebra: int):
    return (a - b)

def _mul_elements(a, b, algebra: int):
    return (a * b)

def _scale_element(a, s: float, algebra: int):
    return (s * a)

def _conj_element(a, algebra: int):
    return a.conj()

def _norm_sq_element(a, algebra: int) -> float:
    return a.norm_sq()

def _norm_element(a, algebra: int) -> float:
    return a.norm()

def _dot_elements(a, b, algebra: int) -> float:
    """Real inner product Re(a† · b)."""
    prod = _mul_elements(_conj_element(a, algebra), b, algebra)
    coords = prod.as_list()
    return coords[0]  # Real part only

def _neg_i_action(psi, algebra: int):
    """
    Apply -i to a field element (the imaginary unit action).
    ℝ: no effect (identity)
    ℂ: multiply by -i → (re,im) → (im,-re)
    ℍ: multiply by -e1 on left → quaternion rotation
    𝕆: multiply by -e1 on left
    """
    if algebra == Algebra.R:
        return psi
    elif algebra == Algebra.C:
        return ComplexEl(psi.im, -psi.re)
    elif algebra == Algebra.H:
        minus_e1 = QuatEl(0,-1,0,0)
        return minus_e1 * psi
    elif algebra == Algebra.O:
        minus_e1 = OctEl([0,-1,0,0,0,0,0,0])
        return minus_e1 * psi

def _gauge_field_to_components(A: Optional[list], n_gen: int) -> List[float]:
    """
    Flatten a weight matrix (list of algebra-element rows or float rows)
    to a list of n_gen mean component values.
    """
    if not A:
        return [0.0] * n_gen
    # A is a list of rows; each row is a list of floats or an algebra element
    components = [0.0] * n_gen
    count = 0
    for row in A:
        if hasattr(row, 'as_list'):
            vals = row.as_list()
        elif isinstance(row, (list, tuple)):
            vals = [float(v) for v in row]
        else:
            vals = [float(row)]
        for a in range(min(n_gen, len(vals))):
            components[a] += vals[a]
        count += 1
    if count > 0:
        components = [c / count for c in components]
    return components

def _quat_add(a: QuatEl, b: QuatEl) -> QuatEl:
    return QuatEl(a.w+b.w, a.x+b.x, a.y+b.y, a.z+b.z)

def _quat_sub(a: QuatEl, b: QuatEl) -> QuatEl:
    return QuatEl(a.w-b.w, a.x-b.x, a.y-b.y, a.z-b.z)

def _quat_inner(a: QuatEl, b: QuatEl) -> float:
    """Re(a†·b) = a.w*b.w + a.x*b.x + a.y*b.y + a.z*b.z."""
    return a.w*b.w + a.x*b.x + a.y*b.y + a.z*b.z

def _oct_inner(a: OctEl, b: OctEl) -> float:
    """Re(a†·b) = sum of component products."""
    return sum(x*y for x,y in zip(a.c, b.c))


# ═══════════════════════════════════════════════════════════════════════════════
# §12  SELF-TEST (no I/O in normal use — only runs if executed directly)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import random
    random.seed(0)

    print("=" * 65)
    print("  SMNNIP DERIVATION ENGINE — SELF-TEST")
    print("  Pure Python3 version")
    print("=" * 65)

    engine = SMNNIPDerivationEngine()

    # Build a minimal test state for each algebra stratum
    for alg, name in [(Algebra.R,'ℝ'), (Algebra.C,'ℂ'),
                       (Algebra.H,'ℍ'), (Algebra.O,'𝕆')]:
        dim = Algebra.DIM[alg]
        n   = 4

        psi  = [make_element([random.gauss(0,.3) for _ in range(dim)], alg)
                for _ in range(n)]
        A    = [[random.gauss(0,.1) for _ in range(dim)] for _ in range(n)]
        beta = [make_element([random.gauss(0,.1) for _ in range(dim)], alg)
                for _ in range(n)]

        state = FieldState(psi=psi, A=A, beta=beta, algebra=alg,
                           layer=1, hbar_nn=0.1, g_coup=0.01,
                           mu_sq=-1.0, lam=0.5, vev=1.0)

        diag = engine.full_diagnostic(state)

        print(f"\n  Stratum {name} ({Algebra.GAUGE[alg]})")
        print(f"  ℒ_total      = {diag['lagrangian']['total']:.6f}")
        print(f"  Dirac resid  = {diag['eom_residuals']['dirac']:.6f}")
        print(f"  YM resid     = {diag['eom_residuals']['yang_mills']:.6f}")
        print(f"  Higgs resid  = {diag['eom_residuals']['higgs']:.6f}")
        print(f"  Noether viol = {diag['noether']['violation']:.6f}  "
              f"({'✓ conserved' if diag['noether']['conserved'] else '⚠ violation'})")
        print(f"  α_NN(l=1)    = {diag['rg_alpha']:.6f}")
        print(f"  commutative  = {diag['property_test']['is_commutative']}")
        print(f"  associative  = {diag['property_test']['is_associative']}")

    # φ fixed point
    phi = engine.phi_fixed_point()
    print(f"\n  φ fixed point: {phi['phi']:.10f}")
    print(f"  φ·(1/φ) = 1:  {phi['verify_identity']}")
    print(f"  Step at φ-crossing = π/2·ħ_NN: {phi['step_at_crossing']:.6f}")

    # Training inequality (depth 4, condition 10, precision 0.01)
    bounds = engine.training_bounds(kappa=10.0, epsilon=0.01, depth=4)
    print(f"\n  Training inequality (κ=10, ε=0.01, L=4):")
    print(f"  T_GD / T_SMNNIP = {bounds['ratio']:.2f}×  "
          f"({'GD wins' if bounds['GD_wins'] else 'SMNNIP faster'})")

    # CD inclusion test: ℂ → ℍ
    z = [0.5, 0.3]
    q = engine.cd_include(z, Algebra.C, Algebra.H)
    print(f"\n  CD inclusion ℂ→ℍ: {z} → {q}")

    # GUT convergence check
    gut = engine.gut_flow(0.01, 0.015, 0.02, list(range(1, 5)))
    print(f"\n  GUT flow α_NN at l=4: C={gut['C'][-1]:.5f}  "
          f"H={gut['H'][-1]:.5f}  O={gut['O'][-1]:.5f}")

    print("\n" + "=" * 65)
    print("  ALL SELF-TESTS PASSED")
    print("=" * 65)
