# Noether Current Engine — Architecture Specification

**Version:** 0.1 (session 1 — 2026-04-18)
**Scope:** Parent engine for conserved-current derivation from Noether's theorem.
**Position:** Peer to `smnnip_lagrangian_pure.py` and `smnnip_inversion_engine_patched.py`.
**Intended audience:** Noether researchers (mathematical physicists working on
classical/quantum conservation laws), not neural-network researchers.

---

## 1. Purpose and positioning

This engine applies **Noether's theorem** — the statement that every continuous
symmetry of an action yields a conserved current — as a general tool. It takes
a Lagrangian and a symmetry as input and returns a conserved current as output.

The engine is **not SMNNIP-specific**. SMNNIP's gauge Noether current is *one*
worked example among several (free scalar, complex scalar, Dirac, QED,
Yang-Mills, SMNNIP). A Noether researcher can read this engine, verify the
construction on standard examples they already know, and only then — if they
choose — examine the SMNNIP application.

If SMNNIP is wrong, this engine still works. If Noether's theorem is wrong —
well, then far more is wrong than this engine.

## 2. Design principles

### 2.1 All contestable options are switches, not defaults

Noether's theorem has multiple inequivalent formulations in the literature.
Different research communities use different conventions. The engine exposes
every contested choice as an explicit switch and refuses to silently choose for
the user.

Defaults exist (the engine can be invoked without specifying all 14 switches)
but every default is logged in the output metadata so the user can see which
conventions their result depends on, and every default is overridable.

### 2.2 Honest error surface

When a switch combination is not yet implemented, the engine raises:

```
UnsupportedCombinationError: combination (X, Y) not yet supported — reason: ...
```

It does not silently fall back. It does not guess. It does not warn and
continue. The user knows exactly what the engine did and didn't do.

### 2.3 Metadata transparency

Every current returned by the engine carries a metadata dict recording:
- which 14 switch settings were in effect
- which were user-supplied and which were defaults
- which intermediate results (Euler-Lagrange equations, K^μ boundary terms,
  improvement terms) were used
- which shell (on-shell / off-shell) the conservation identity holds on
- any approximations made and their order

A Noether researcher reading the output sees immediately what assumptions
produced it and can rerun with different ones.

### 2.4 Separation of concerns

The engine is a **package**, not a single file. Each of the 14 axes has its
own module. Each Noether-theorem variant has its own file. Each worked
example has its own file. A reviewer can audit individual components without
having to read 10,000 lines of unrelated code.

---

## 3. The fourteen contestable axes

Each axis corresponds to a choice on which the Noether literature is not
unanimous. The engine exposes each as a named switch.

### Axis 1 — Theorem variant

- `theorem = 'first'` — Noether's first theorem (global continuous symmetry → conserved current). Default.
- `theorem = 'second'` — Noether's second theorem (local/gauge symmetry → identity among field equations, Bianchi-type).
- `theorem = 'both'` — Run both in parallel, return both.

**Contested because:** Some authors (Brading-Brown, Noether's original 1918
paper in strict reading) insist on sharp separation. Others (many modern QFT
texts) treat second as a corollary of first. The physics produced is the same;
the emphasis differs.

### Axis 2 — Shell condition

- `shell = 'on_shell'` — Conservation law holds when equations of motion are imposed. Standard textbook derivation. Default.
- `shell = 'off_shell'` — Conservation law holds as an algebraic identity without using EOM (BV/cohomological formulation).
- `shell = 'both'` — Return both forms.

**Contested because:** Classical field theory textbooks present on-shell. Modern
BRST/BV treatments work off-shell for deeper reasons (anomaly analysis,
renormalization). Both are correct; one is more general.

### Axis 3 — Invariance type

- `invariance = 'strict'` — δℒ = 0 exactly under the transformation.
- `invariance = 'divergence'` — δℒ = ∂_μ K^μ for some K^μ (quasi-invariance).
- `invariance = 'bessel_hagen'` — Full Bessel-Hagen generalization carrying K^μ through the derivation explicitly. Default.

**Contested because:** Physics textbooks often present strict invariance and
fold K^μ into the current silently. Mathematical treatments (Olver, Kosmann-
Schwarzbach) insist on Bessel-Hagen from the start because the "strict"
version misses genuine symmetries of free-particle and Galilean systems.

### Axis 4 — Output form

- `output = 'current'` — J^μ with ∂_μ J^μ = 0. Default.
- `output = 'charge'` — Q = ∫ J⁰ d³x with dQ/dt = 0.
- `output = 'form'` — (d-1)-form ⋆J with d(⋆J) = 0.
- `output = 'all'` — Return all three.

**Contested because:** QFT uses currents; Hamiltonian mechanics uses charges;
mathematical physics (de Rham cohomology) uses forms. Same information,
different presentations.

### Axis 5 — Variation convention

- `variation = 'vertical'` — δφ = φ'(x) − φ(x) (intrinsic field variation at same point).
- `variation = 'total'` — δ̂φ = φ'(x') − φ(x) (following the flow, includes ξ^μ ∂_μ φ).
- `variation = 'both'` — Return currents under both conventions.

Default: `'vertical'` for internal symmetries (no spacetime flow), `'total'`
for spacetime symmetries.

**Contested because:** Jet-bundle formulations distinguish rigorously; physics
texts often blur. Currents differ by a ξ^μ T^μν_0 term between the two.

### Axis 6 — Metric signature

- `signature = 'mostly_minus'` — (+,−,−,−). Particle physics convention. Default.
- `signature = 'mostly_plus'` — (−,+,+,+). Relativity convention.

**Contested because:** The MTW vs. Weinberg schism is 50+ years old and shows
no sign of resolving. Stress-energy tensor signs flip between conventions.

### Axis 7 — Spacetime type

- `spacetime = 'minkowski'` — Flat 4D, signature per axis 6. Default.
- `spacetime = 'curved'` — Riemannian/Lorentzian with user-supplied metric g_μν(x). Requires einsteinpy or hand-rolled tensor machinery.
- `spacetime = 'euclidean'` — All-plus signature, imaginary time. Thermal field theory.
- `spacetime = 'custom'` — User supplies metric and connection.

**Contested because:** Noether's theorem on curved backgrounds requires careful
handling of the volume element √|g| d⁴x and covariant derivatives. Some
authors carry these through rigorously; others work in local Lorentz frames
and handle globally as a patch-together.

### Axis 8 — Gauge-fixing / improvement

- `improvement = 'none'` — Canonical Noether current, no improvement term. Default.
- `improvement = 'belinfante_rosenfeld'` — Symmetrized stress-energy tensor.
- `improvement = 'callan_coleman_jackiw'` — Conformal improvement (trace-free for conformal theories).
- `improvement = 'custom'` — User-specified improvement term.

**Contested because:** The canonical T^μν is not symmetric for theories with
spin. Belinfante-Rosenfeld makes it symmetric and compatible with general
relativity. CCJ makes it trace-free for conformal theories. Each serves
different physics.

### Axis 9 — Algebra / generator convention

- `algebra = 'physics'` — Tr(T^a T^b) = (1/2) δ^{ab}. Default.
- `algebra = 'math'` — Tr(T^a T^b) = 2 δ^{ab}.
- `algebra = 'custom'` — User-supplied generator normalization.

For non-abelian gauge theories and SMNNIP. For octonions specifically, there
is a further sub-switch:

- `octonion_fano = 'oriented_cyclic'` — standard convention with e₁e₂=e₃ and cyclic. Default.
- `octonion_fano = 'alternate'` — opposite orientation on some cycles.
- `octonion_fano = 'custom'` — user-supplied Fano plane multiplication.

**Contested because:** Physics and math communities use different Lie algebra
normalizations. Octonions admit 480 distinct Fano conventions; different
authors pick different ones. All produce correct physics *if you stay within
one convention throughout*.

### Axis 10 — Boundary conditions

- `boundary = 'vanishing_at_infinity'` — Fields → 0 at spatial infinity, standard QFT. Default.
- `boundary = 'compact_support'` — Fields identically zero outside a compact region.
- `boundary = 'bulk_only'` — Ignore boundary; return bulk conservation law only.
- `boundary = 'explicit'` — User supplies boundary conditions; engine returns charge + boundary flux separately.

**Contested because:** Asymptotic falloff determines whether the charge is
actually conserved (whether the ∫ J⁰ d³x integral converges) and whether
soft-theorem-type contributions appear.

### Axis 11 — Classical / quantum

- `theory = 'classical'` — Classical Noether, ∂_μ J^μ = 0. Default.
- `theory = 'quantum_ward'` — Ward-Takahashi identities: ⟨∂_μ J^μ O⟩ = Σ contact terms.
- `theory = 'anomaly_tracked'` — Full quantum treatment; classical conservation may fail by ABJ anomaly, trace anomaly, etc. Returns anomaly coefficient if nonzero.

**Contested because:** Anomalies are the subtle, deep case. Classical
conservation can genuinely fail quantum-mechanically. A Noether engine that
doesn't acknowledge this is a classical-only engine.

### Axis 12 — Field type declaration

Per-field switches (supplied as part of the Lagrangian input):

- `real_scalar`
- `complex_scalar`
- `dirac_4_component`
- `weyl_2_component`
- `majorana`
- `vector_abelian`
- `vector_non_abelian`
- `tensor_spin_2`
- `algebra_valued` (with sub-switches: `complex`, `quaternion`, `octonion`, `clifford`)

**Contested because:** Noether variations have different forms for different
spin types. Dirac spinors transform under γ matrices; vectors transform under
vector rep; tensors under tensor rep. Getting these right is where most Noether
derivation bugs live.

### Axis 13 — Action prescription

- `action = 'covariant'` — S = ∫ d⁴x √|g| ℒ. Default.
- `action = 'hamiltonian'` — Legendre transform first, symmetry applied to H.
- `action = 'adm_split'` — 3+1 decomposition (ADM formalism). For GR applications.

**Contested because:** Covariant and Hamiltonian give equivalent physics but
very different intermediate expressions. ADM is essential for numerical
relativity but awkward for relativistic QFT.

### Axis 14 — Output format

- `format = 'symbolic'` — Sympy expression. Default.
- `format = 'numerical'` — Evaluated on a user-supplied field configuration. Returns numpy array.
- `format = 'latex'` — LaTeX string for paper inclusion.
- `format = 'all'` — Dict with symbolic, numerical-on-test-config, and latex.

---

## 4. Switch combinations: the compatibility matrix

Not every combination of 14 switches is implementable, and some combinations
are mathematically inconsistent. The engine maintains an explicit compatibility
matrix in `switches.py`. Three categories:

**IMPLEMENTED (session 1):**
- theorem=first, shell=on_shell, invariance∈{strict, divergence, bessel_hagen},
  output∈{current, charge, form, all}, variation∈{vertical, total},
  signature∈{mostly_minus, mostly_plus}, spacetime=minkowski, improvement=none,
  algebra=physics, boundary=vanishing_at_infinity, theory=classical,
  action=covariant, format∈{symbolic, latex}

- Same but with theorem=second for gauge Lagrangians

**DEFERRED (session 2+) — raises UnsupportedCombinationError with session N target:**
- shell=off_shell (requires BV machinery — session 2)
- spacetime∈{curved, euclidean, adm_split} (requires einsteinpy — session 3)
- theory∈{quantum_ward, anomaly_tracked} (requires quantum machinery — session 4)
- improvement∈{belinfante_rosenfeld, ccj, custom} (session 2)
- action∈{hamiltonian, adm_split} (session 3)
- format=numerical (requires field-config evaluator — session 2)

**INCONSISTENT — always raises UnsupportedCombinationError:**
- signature=mostly_plus with certain spinor conventions (engine warns and
  blocks until user confirms spinor convention matches)
- algebra=custom without sub-switch normalization specified
- boundary=compact_support with spacetime=curved and non-compact manifold

---

## 5. Module layout

```
noether_engine/
├── __init__.py              — public API (NoetherEngine class, factory)
├── README.md                — researcher-facing overview
├── architecture.md          — this document
├── switches.py              — 14-axis switch registry and validator
├── core/
│   ├── __init__.py
│   ├── lagrangian.py        — Lagrangian object (symbolic)
│   ├── symmetry.py          — Symmetry object (infinitesimal transformation)
│   ├── field.py             — Field object (per-type, per-algebra)
│   ├── variation.py         — vertical / total variation machinery
│   ├── current.py           — conserved current assembly
│   ├── charge.py            — charge, form conversions
│   └── metadata.py          — output metadata tracking
├── theorems/
│   ├── __init__.py
│   ├── first_theorem.py     — global symmetry → current
│   ├── second_theorem.py    — local gauge → Bianchi identities
│   └── bessel_hagen.py      — divergence-symmetry generalization
├── shell/
│   ├── __init__.py
│   ├── on_shell.py          — EOM-dependent derivation
│   └── off_shell.py         — BV/cohomological (session 2)
├── spacetime/
│   ├── __init__.py
│   ├── minkowski.py         — flat metric, standard signature
│   ├── curved.py            — general Riemannian/Lorentzian (session 3)
│   ├── euclidean.py         — imaginary-time (session 3)
│   └── adm.py               — 3+1 split (session 3)
├── quantum/
│   ├── __init__.py
│   ├── ward_takahashi.py    — Ward identities (session 4)
│   └── anomaly.py           — ABJ/trace anomaly (session 4)
├── algebra/
│   ├── __init__.py
│   ├── lie.py               — standard Lie algebras (u(1), su(2), su(3))
│   ├── clifford.py          — gamma matrices, spinors (session 2)
│   └── cayley_dickson.py    — ℝ/ℂ/ℍ/𝕆 for SMNNIP
├── improvement/
│   ├── __init__.py
│   ├── belinfante_rosenfeld.py  — (session 2)
│   ├── ccj.py                   — (session 2)
│   └── custom.py                — always available
├── examples/
│   ├── __init__.py
│   ├── free_scalar.py       — translation → T^μν
│   ├── complex_scalar.py    — global U(1) → Klein-Gordon current
│   ├── dirac.py             — global U(1) → Dirac current (session 2)
│   ├── qed.py               — local U(1) → second theorem (session 2)
│   ├── yang_mills.py        — non-abelian gauge (session 2)
│   └── smnnip_gauge.py      — SMNNIP ℒ_NN gauge Noether current
└── tests/
    ├── __init__.py
    ├── test_conservation.py     — conservation law holds symbolically
    ├── test_conventions.py      — equivalence under convention changes
    ├── test_switches.py         — unsupported combinations raise correctly
    └── test_smnnip_matches_existing.py   — matches NoetherCalculus output
```

---

## 6. Public API

### 6.1 Minimal invocation

```python
from noether_engine import NoetherEngine, Lagrangian, Symmetry, Field
import sympy as sp

# Define field
phi = Field(name='phi', field_type='real_scalar')

# Define Lagrangian symbolically
x = sp.symbols('t x y z')
lagrangian = Lagrangian(
    density = sp.Rational(1,2) * (phi.d(0)**2 - phi.d(1)**2 - phi.d(2)**2 - phi.d(3)**2)
              - sp.Rational(1,2) * sp.Symbol('m')**2 * phi**2,
    fields = [phi],
    coords = x,
)

# Define symmetry (translation in direction μ)
mu = sp.symbols('mu')
symmetry = Symmetry(
    name = 'spacetime_translation',
    infinitesimal = {phi: -sp.diff(phi, x[mu]) * sp.Symbol('epsilon')},
    parameter = sp.Symbol('epsilon'),
)

# Invoke engine with all defaults
engine = NoetherEngine(lagrangian, symmetry)
result = engine.derive_current()

print(result.current)       # sympy expression for J^μ
print(result.metadata)      # dict of all 14 switch values used
```

### 6.2 Full explicit invocation

```python
engine = NoetherEngine(
    lagrangian, symmetry,
    theorem = 'first',
    shell = 'on_shell',
    invariance = 'bessel_hagen',
    output = 'all',
    variation = 'total',
    signature = 'mostly_minus',
    spacetime = 'minkowski',
    improvement = 'none',
    algebra = 'physics',
    boundary = 'vanishing_at_infinity',
    theory = 'classical',
    action = 'covariant',
    format = 'all',
)
result = engine.derive_current()

print(result.current)
print(result.charge)
print(result.form)
print(result.latex)
print(result.metadata)
```

### 6.3 Error surface

```python
engine = NoetherEngine(lagrangian, symmetry, spacetime='curved')
engine.derive_current()
# raises UnsupportedCombinationError:
#   "combination (spacetime=curved) not yet supported —
#    reason: curved-spacetime covariant derivatives require einsteinpy
#    machinery scheduled for session 3. Use spacetime='minkowski' or
#    wait for session 3 release."
```

---

## 7. Testing strategy

### 7.1 Conservation-law property testing

For every implemented switch combination and every worked example, the engine
must produce a current whose divergence is zero on-shell. This is verified
symbolically in `tests/test_conservation.py`:

```python
result = engine.derive_current()
divergence = sum(sp.diff(result.current[mu], x[mu]) for mu in range(4))
simplified = sp.simplify(divergence.subs(eom_substitutions))
assert simplified == 0
```

### 7.2 Convention-equivalence testing

Physical observables must not depend on conventions. If a user changes
`signature` from `mostly_minus` to `mostly_plus`, the current changes sign in
coordinated ways but the conserved charge must be the same (up to an overall
sign that propagates consistently). This is tested in `test_conventions.py`.

### 7.3 Unsupported-combination testing

Every entry in the DEFERRED and INCONSISTENT categories of section 4 must
raise `UnsupportedCombinationError` with an informative message.
`test_switches.py` enumerates these.

### 7.4 SMNNIP equivalence testing

The SMNNIP gauge Noether current derived by this engine must match the output
of `NoetherCalculus.activation_current` in the existing derivation engine,
modulo convention translation. `test_smnnip_matches_existing.py` verifies this
as a check on both engines.

### 7.5 Property-based testing (hypothesis)

For Lagrangians and symmetries generated randomly within well-defined classes
(polynomial-in-fields, up to degree 4, with integer or symbolic coefficients),
conservation must hold. `hypothesis` generates thousands of cases; each must
pass.

---

## 8. Session plan

### Session 1 (this session)

**Deliverables:**
- `architecture.md` — this document
- `README.md` — researcher front door
- `switches.py` — full 14-axis registry, compatibility matrix, validator
- `core/` — all five modules
- `theorems/first_theorem.py` — complete
- `theorems/bessel_hagen.py` — complete
- `shell/on_shell.py` — complete
- `spacetime/minkowski.py` — complete
- `algebra/lie.py` — complete (u(1), su(2), su(3))
- `algebra/cayley_dickson.py` — complete (ℝ/ℂ/ℍ/𝕆)
- `examples/free_scalar.py` — translation → T^μν, fully worked
- `examples/complex_scalar.py` — global U(1) → KG current, fully worked
- `examples/smnnip_gauge.py` — SMNNIP gauge Noether current under this engine
- `tests/` — conservation, switches, SMNNIP-match tests

All remaining modules: skeleton files with class signatures and raise
UnsupportedCombinationError stubs.

### Session 2

- `shell/off_shell.py` — BV/cohomological derivation
- `improvement/*.py` — Belinfante-Rosenfeld, CCJ
- `theorems/second_theorem.py` — complete
- `algebra/clifford.py` — gamma matrices, spinors
- `examples/dirac.py`, `examples/qed.py`, `examples/yang_mills.py`

### Session 3

- `spacetime/curved.py` — einsteinpy-backed
- `spacetime/euclidean.py` — imaginary time
- `spacetime/adm.py` — 3+1 split
- `action/hamiltonian.py` — Legendre transform

### Session 4

- `quantum/ward_takahashi.py` — Ward identities
- `quantum/anomaly.py` — ABJ + trace anomalies
- Full property-based test suite via hypothesis

---

## 9. Open questions (for future sessions)

**Q1.** Should the engine support **supersymmetry** transformations as a
first-class axis, or is supersymmetry handled as a particular case of
`variation='total'` with anticommuting parameters? Current thinking: treat
as separate axis (#15) when SUSY support lands.

**Q2.** The **Poincaré algebra** generates 10 Noether currents (4 translations
+ 6 Lorentz rotations) automatically. Should there be a helper
`engine.poincare_currents()` that returns all 10 at once, or should the user
invoke the engine 10 times with different symmetry objects?

**Q3.** Engine output is currently **per-current**. For theories with many
symmetries, should there be a batch mode? Related to Q2.

**Q4.** When the Lagrangian has **auxiliary fields** (non-dynamical), does the
variation need to eliminate them first, or does the engine carry them through?
Classical answer: eliminate first. Modern BV answer: carry through and use
BRST cohomology. Session 2 decision point.

---

## 10. References (sources the engine's conventions are anchored to)

These are the foundational references for each axis. The engine's behavior on
each axis matches at least one of these conventions exactly.

- **Noether, E. (1918).** *Invariante Variationsprobleme.*
  Göttingen Nachrichten. The original theorems.

- **Bessel-Hagen, E. (1921).** *Über die Erhaltungssätze der Elektrodynamik.*
  Math. Ann. 84. The K^μ generalization.

- **Olver, P.J. (1993).** *Applications of Lie Groups to Differential
  Equations.* Springer GTM 107. Rigorous jet-bundle formulation.

- **Kosmann-Schwarzbach, Y. (2011).** *The Noether Theorems: Invariance and
  Conservation Laws in the Twentieth Century.* Springer. Historical and
  conceptual analysis of the ambiguities.

- **Weinberg, S. (1995).** *The Quantum Theory of Fields, Vol. I.*
  Mostly-plus signature, Hamiltonian orientation.

- **Peskin, M.E. & Schroeder, D.V. (1995).** *An Introduction to Quantum
  Field Theory.* Mostly-minus signature, path-integral orientation.

- **Misner, C.W., Thorne, K.S., Wheeler, J.A. (1973).** *Gravitation.*
  Mostly-plus signature, geometric orientation.

- **Belinfante, F.J. (1940).** Symmetrized stress-energy tensor.
  Physica 7.

- **Callan, C.G., Coleman, S., Jackiw, R. (1970).** *A new improved
  energy-momentum tensor.* Ann. Phys. 59. Conformal improvement.

- **Wald, R.M. (1993).** *Black hole entropy is the Noether charge.*
  Phys. Rev. D 48. Noether on curved backgrounds.

- **Henneaux, M. & Teitelboim, C. (1992).** *Quantization of Gauge Systems.*
  Princeton. BV/BRST formulation, off-shell Noether.

- **Bardeen, W.A. & Zumino, B. (1984).** *Consistent and covariant
  anomalies in gauge and gravitational theories.* Nucl. Phys. B 244.
  Anomaly classification.

---

**End of architecture specification.**

Further modules cross-reference this document by section number.
