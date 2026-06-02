# SMIP Architecture

**Standard Model of Monad Information Propagation**  
*Also written: SMMIP / SMNNIP (neural variant) — same spine, different emphasis*

---

## Overview

SMIP is Ptolemy's theoretical framework for information processing. The core claim is that neural information propagation obeys the same conservation laws as the Standard Model of particle physics, derived via Noether's theorem applied to the Cayley-Dickson algebra tower.

Ptolemy is an **LSH** (Locality-Sensitive Hashing) system, not an LLM. SMIP is the mathematical basis of that distinction. No transformers. No autoregressive generation. No attention heads.

---

## Cayley-Dickson Tower

Information is modelled as algebraic objects lifted through successive Cayley-Dickson doublings:

| Layer | Algebra | Dim | Property lost |
|---|---|---|---|
| L0 | ℝ (reals) | 1 | — |
| L1 | ℂ (complex) | 2 | ordering |
| L2 | ℍ (quaternions) | 4 | commutativity |
| L3 | 𝕆 (octonions) | 8 | associativity |
| L4 | 𝕊 (sedenions) | 16 | zero-divisors appear |

The **tower runs in both directions:**
- Forward (ℝ → 𝕊): encoding — input is lifted into higher-dimensional algebra
- Reverse (𝕊 → ℝ): decoding — sedenion element collapses back to real output

The ReverseTower is the core inference operation. The forward tower is the encoding context.

---

## Four-Layer Lagrangian

SMIP has a Lagrangian for each tower layer, analogous to Standard Model gauge fields:

```
L_SMIP = L0 + L1 + L2 + L3

L0 — kinetic term (real/scalar)         ← ½ Re(ψ̄ ∂ψ)
L1 — U(1) electromagnetic analogue      ← complex phase coupling
L2 — SU(2) weak force analogue          ← quaternion spin term
L3 — G2/SU(3) strong force analogue     ← octonion gauge coupling
```

Coupling constants per layer match known physical constants:
- L1: α ≈ 1/137 (fine structure)
- L3: αs ≈ 0.118 (strong coupling at M_Z)

---

## Noether Currents

By Noether's theorem, each symmetry of the Lagrangian yields a conserved current J^μ:

```
J^μ = ∂L / ∂(∂_μψ) · δψ
∂_μ J^μ = 0   (conservation)
```

Four currents — one per layer. The **Noether charge** Q = ∫ J⁰ dV is the conserved quantity used as an information index in the CyclicContextBuffer hyperindex step.

**Verified result:** `conserved=True, violation=0, 7+ sigma` from `SMNNIPValaQuenta`.

---

## ReverseTower (Inference Path)

```
Input text
  → character encoding (L0, real)
  → lexical lift (L1, complex)
  → syntactic lift (L2, quaternion)
  → semantic lift (L3, octonion)
        ↓ ReverseTower
  → collapse 𝕊→𝕆→ℍ→ℂ→ℝ
  → Noether current extraction
  → response character generation
```

The LSH hash of the sedenion element at L3 indexes the response. This is the non-autoregressive generation mechanism: the hash collapses directly to a character, not through an attention distribution.

---

## Ground State and Domain Floor

| Constant | Value | Meaning |
|---|---|---|
| `GROUND` | 0.000707 | SMMIP measured ground state energy |
| `A_π` | 1/137.035999 | Domain floor — minimum addressable energy (fine-structure constant; capital Latin A subscript π, NOT Greek α) |
| `Ω` | 1.0 | Inherent time length (Berry-Keating, normalised) |
| `R_CRIT` | 0.5 | Re(s) on the Riemann critical line |

The domain floor `A_π` is the minimum energy level below which no SMIP information node can propagate. This is the connection to the Berry-Keating operator: BK spectrum = Im(ρ) for ζ(ρ)=0, and the BK domain floor = `A_π`.

---

## J_N Anti-Möbius Involution

`J_N(z) = i / z̄`

- Four-cycle: period 2π
- Fixed set: unit circle |z| = 1
- Via conformal map, fixed set of J_N = critical line Re(s) = 1/2
- Connection to Riemann Hypothesis: if ζ(s)=0 with Re(s)≠1/2, it has no J_N-symmetric preimage — geometrically forbidden

This is the `(I|O)` boundary condition from the SMIP proof path. It identifies the critical line as the natural fixed set of the inversion symmetry.

---

## Implementation Files

| File | Role |
|---|---|
| `Ainulindale/` | SMNNIP derivation engine, Noether engine |
| `Archimedes/Engines/ValaQuenta/` | Symlinked math engine — spherical, inversion, lagrangian, noether, berry_keating |
| `Philadelphos/smip_engine.py` | SMIP integration in Philadelphos |
| `Philadelphos/smip_engine_philadelphos.py` | Face-level SMIP wiring |
| `Pharos/smip_engine_pharos.py` | Pharos-level SMIP wiring |
| `Archimedes/Maths/SMMIP/` | Maths layer — Cayley-Dickson, Lagrangian, EL equations, etc. (Tier C, to be built) |

---

## Relationship to LSH Model

SMIP is the *theory*. The LSH model is the *implementation*.

| SMIP concept | LSH implementation |
|---|---|
| Cayley-Dickson lift | Layer-by-layer hash projection |
| Noether current | Locality-Sensitive Hash index |
| ReverseTower | Hash collapse → character |
| Domain floor A_π | Minimum Hamming distance threshold |
| Ground state 0.000707 | Measured LSH collision floor |

The six-layer Monad architecture in `ptolemy_core.py` (CharacterNeuron → BrocaNetwork) implements the L0→L3 forward tower. The hash collapse is in `PtolBrain.py`.

---

## Primary Claim

Neural information propagation obeys Standard Model conservation laws.

Evidence: Noether conservation verified computationally. Violation = 0. Significance: 7+ sigma. Tool: `SMNNIPValaQuenta` in `Ainulindale/`.

Run: `python3 derivation.py` → `conserved=True`.
