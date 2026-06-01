# AGM Iteration — Derivation Path

**UF Collection:** `akl.ufm` (Andreas Lober)  
**Formulas:** `agm`, `AGMinsky`, `agm_deriv`  
**Ptolemy Face:** Archimedes

---

## What the Formula Is Doing

The Arithmetic-Geometric Mean iteration starts with two values a₀, b₀ and repeats:

```
a_{n+1} = (a_n + b_n) / 2
b_{n+1} = √(a_n · b_n)
```

The two sequences converge to a common limit AGM(a₀, b₀) with **quadratic convergence** — the number of correct decimal digits doubles at every step. This is the fastest-known convergence rate for any fixed-point iteration.

The UF formula applies this iteration in the complex plane to produce fractal basin structures encoding which initial values converge and which diverge.

---

## What the Math Is Actually Doing

The AGM is not merely a fast algorithm. It is the **uniformization map for elliptic curves**. Specifically:

```
AGM(1, √(1−k²)) = π / (2K(k))
```

where K(k) is the complete elliptic integral of the first kind. This means the AGM converts elliptic integral values — which encode the periods of elliptic curves — into simple arithmetic operations.

Elliptic curves are the objects at the center of the Langlands correspondence. The Modularity Theorem (formerly Taniyama-Shimura) states that every rational elliptic curve is a modular form. The AGM is the computational bridge between the analytic side (elliptic integrals, modular forms) and the algebraic side (elliptic curves, L-functions).

The quadratic convergence of the AGM is not accidental. It arises because the AGM fixed point is a **superattracting fixed point** — the derivative of the iteration map vanishes there. In dynamical systems terms: every nearby orbit converges in a number of steps proportional to `log log(1/ε)` rather than `log(1/ε)`. The AGM achieves the theoretical minimum iteration count for a fixed-point algorithm.

---

## Derivation Path

The Riemann hypothesis asserts that the zeros of ζ(s) with Re(s) > 0 all have Re(s) = 1/2. The zeros are deeply connected to the periods of elliptic curves via the L-function correspondence: if E is an elliptic curve over ℚ, its L-function L(E,s) has zeros encoding the curve's arithmetic.

The AGM computes the periods of elliptic curves. The 0.00070 gap `|d*·ln(10) − Ω|` may be a correction term in the AGM expansion of K(k) evaluated at a specific modulus k determined by the SMIP spectral coordinate d*.

**Derivation target:** Find the elliptic modulus k* such that:

```
π / (2K(k*)) = d*
```

Then compute the AGM correction series around this value. The first correction term in the AGM series expansion of K(k) near k* is a candidate closed form for the 0.00070 gap. If this term equals `|d*·ln(10) − Ω|`, the gap is derived as an elliptic period correction — connecting SMIP's spectral coordinate directly to the Langlands-Modularity framework.

The `agm_deriv` formula in the UF library computes the derivative of the AGM iteration — this is exactly the quantity needed to compute the correction term.

---

## SMIP Connection

The SMIP φ fixed point is the attractor of the Output Engine. Quadratic convergence to φ means the engine reaches the fixed point in the minimum number of steps — the AGM convergence rate is the theoretical optimum. The `agm` formula visualizes the basin of this convergence in the complex parameter plane, showing which input states reach φ and which escape. The AGM basin boundary is the boundary of the SMIP output distribution support.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
