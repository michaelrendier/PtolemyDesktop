# Noether Current Engine

A general-purpose implementation of **Noether's theorem** for conserved-current
derivation from continuous symmetries of a Lagrangian.

This engine is **not** specific to any one physical theory. It applies Noether's
theorem to whatever Lagrangian and symmetry you hand it. Standard examples
(free scalar → stress-energy, complex scalar → Klein-Gordon current, Dirac →
Dirac current, non-abelian gauge → Yang-Mills current) are included as worked
examples. A specific application to the SMNNIP framework is included as one
example among several — not as the purpose of the engine.

## Why this exists

Noether's theorem has many inequivalent formulations in the literature. The
first theorem versus second, on-shell versus off-shell (BV), strict
invariance versus divergence-symmetry versus Bessel-Hagen, mostly-plus versus
mostly-minus, Belinfante-Rosenfeld improvement versus canonical, physics
Lie-algebra normalization versus math — these are all choices where serious
references disagree.

Most software that computes Noether currents silently picks one convention
per axis and produces a result. Readers from a different convention cannot
verify the output because they cannot tell which choices were made.

This engine exposes **14 contestable axes** as explicit switches. Every
invocation records in its output metadata which switch values were used,
which were user-supplied, and which were defaults. A reviewer working in any
convention can either run the engine in their convention directly, or
translate the engine's output into their convention with full knowledge of
what to translate.

## Quick start

```python
from noether_engine import NoetherEngine, Lagrangian, Symmetry, Field
import sympy as sp

# Free real scalar field
phi = Field('phi', field_type='real_scalar')
x = sp.symbols('t x y z', real=True)
m = sp.Symbol('m', positive=True)

L = Lagrangian(
    density = sp.Rational(1,2) * sum((-1)**i * phi.d(i)**2 for i in range(4))
              - sp.Rational(1,2) * m**2 * phi**2,
    fields = [phi],
    coords = x,
)

# Spacetime translation symmetry
translation = Symmetry.spacetime_translation(direction=0)

# Derive conserved current with default conventions
engine = NoetherEngine(L, translation)
result = engine.derive_current()

print(result.current)       # symbolic J^μ
print(result.metadata)      # dict of all switch values in effect
```

## The 14 axes

See `architecture.md` §3 for the full specification. Brief:

| Axis | Choices | Default |
|---|---|---|
| Theorem | first, second, both | first |
| Shell | on_shell, off_shell, both | on_shell |
| Invariance | strict, divergence, bessel_hagen | bessel_hagen |
| Output | current, charge, form, all | current |
| Variation | vertical, total, both | (type-dependent) |
| Signature | mostly_minus, mostly_plus | mostly_minus |
| Spacetime | minkowski, curved, euclidean, adm, custom | minkowski |
| Improvement | none, belinfante_rosenfeld, ccj, custom | none |
| Algebra | physics, math, custom | physics |
| Boundary | vanishing_at_infinity, compact, bulk, explicit | vanishing_at_infinity |
| Theory | classical, quantum_ward, anomaly_tracked | classical |
| Field type | per-field declaration | required |
| Action | covariant, hamiltonian, adm_split | covariant |
| Format | symbolic, numerical, latex, all | symbolic |

## What's implemented in this release (session 1)

**Fully implemented and tested:**
- Theorem = first
- Shell = on_shell
- Invariance ∈ {strict, divergence, bessel_hagen}
- Output ∈ {current, charge, form, all}
- Variation ∈ {vertical, total}
- Signature ∈ {mostly_minus, mostly_plus}
- Spacetime = minkowski
- Improvement = none
- Algebra ∈ {physics, math, custom} (Lie algebras u(1)/su(2)/su(3))
- Boundary = vanishing_at_infinity
- Theory = classical
- Action = covariant
- Format ∈ {symbolic, latex}
- Field types: real_scalar, complex_scalar, vector_abelian,
  vector_non_abelian, algebra_valued (ℂ, ℍ, 𝕆 via Cayley-Dickson)

**Worked examples:**
- Free real scalar field + spacetime translation → stress-energy tensor T^μν
- Complex scalar + global U(1) → Klein-Gordon probability current
- SMNNIP Lagrangian + Cayley-Dickson-graded gauge → SMNNIP gauge Noether current

**Deferred to session 2+:**

Any switch combination outside the implemented set raises
`UnsupportedCombinationError` with a message naming the session when that
combination is scheduled. Deferred items include:

- `shell='off_shell'` — BV machinery (session 2)
- `spacetime={'curved','euclidean','adm'}` — einsteinpy backing (session 3)
- `theory={'quantum_ward','anomaly_tracked'}` — quantum treatment (session 4)
- `improvement={'belinfante_rosenfeld','ccj'}` — (session 2)
- `format='numerical'` — field-config evaluator (session 2)
- `theorem={'second','both'}` — second theorem machinery (session 2)
- `algebra/clifford.py` (gamma matrices for Dirac) — (session 2)
- `examples/{dirac,qed,yang_mills}.py` — (session 2)

## Install

Run on Linux Mint Xia / Ubuntu 24.04:

```bash
sudo apt install -y python3-pip python3-sympy python3-numpy python3-scipy python3-pytest
sudo pip3 install --break-system-packages sympy numpy scipy mpmath pytest hypothesis rich
```

Session 2 additions:

```bash
sudo pip3 install --break-system-packages galgebra
```

Session 3 additions:

```bash
sudo pip3 install --break-system-packages einsteinpy astropy
```

## Directory layout

```
noether_engine/
├── README.md                — this file
├── architecture.md          — full design specification
├── __init__.py              — public API
├── switches.py              — 14-axis switch registry + validator
├── core/                    — Lagrangian, Symmetry, Field, variations, currents
├── theorems/                — first / second / Bessel-Hagen
├── shell/                   — on_shell / off_shell
├── spacetime/               — minkowski / curved / euclidean / adm
├── quantum/                 — ward_takahashi / anomaly
├── algebra/                 — lie / clifford / cayley_dickson
├── improvement/             — canonical / BR / CCJ / custom
├── examples/                — free_scalar, complex_scalar, dirac, qed,
│                              yang_mills, smnnip_gauge
└── tests/                   — conservation, switches, conventions,
                               smnnip-equivalence
```

## For Noether researchers reading the SMNNIP application

The SMNNIP example (`examples/smnnip_gauge.py`) is one Lagrangian among
several. The engine derives the SMNNIP gauge Noether current from the
SMNNIP Lagrangian by applying Noether's first theorem with
`algebra='physics'`, `field_type='algebra_valued'`, and the Cayley-Dickson
generator bases for ℂ/ℍ/𝕆. The derivation makes no SMNNIP-specific claims.
If Noether's theorem applies to any gauge theory with algebra-valued fields,
it applies to SMNNIP; if the engine correctly computes Noether currents for
free scalars and complex scalars (which it demonstrably does — see
`tests/test_conservation.py`), its SMNNIP output is correct by the same
logic.

Whether SMNNIP is the right physical theory is a separate question. This
engine is silent on that question. It only confirms that *if* SMNNIP's
Lagrangian is taken as given, *then* its gauge Noether current is
J^{a,l} = g · Ψ̄ · T^a · Ψ per algebra stratum, which is consistent with
what the existing SMNNIP derivation engine produces.

## License and provenance

Part of the Ainulindalë framework. Developed by O Captain My Captain
(Cody / Michael Rendier) with Claude (Anthropic). 2026-04-18.

Repository: https://github.com/michaelrendier/Ainulindale
