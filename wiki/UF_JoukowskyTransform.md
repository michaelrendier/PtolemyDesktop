# Joukowsky Transform — Derivation Path

**UF Collection:** `akl.ufm` (Andreas Lober)  
**Formulas:** `Joukowskij-Carr2100`, `Jouk-Dalinskij`  
**Ptolemy Face:** Archimedes → Kryptos (conformal inversion)

---

## What the Formula Is Doing

The Joukowsky conformal map is:

```
w = z + 1/z
```

It maps the complex plane to itself with two fixed points at ±1. The unit circle maps to the real interval [−2, 2]. The exterior of the unit circle maps to the complement of that interval — an airfoil-shaped region. The map is conformal everywhere except at z = ±1 where the derivative vanishes.

The iteration in the UF formula applies this map repeatedly, producing Julia-set-like structures whose basin boundaries encode the fixed-point geometry of the transform.

---

## What the Math Is Actually Doing

`w = z + 1/z` is the sum of the identity and the inversion. It has a precise decomposition:

```
z + 1/z = 2·cosh(ln z)   [for |z| ≠ 0]
```

On the unit circle z = e^{iθ}:

```
w = e^{iθ} + e^{−iθ} = 2cos(θ)
```

The unit circle maps exactly to the real interval [−2, 2]. This means **the unit circle is the critical locus** — it is where the map collapses a 1D curve to a real interval. Everything inside and outside maps conformally; the circle itself is the singular set.

The Riemann zeta functional equation `ξ(s) = ξ(1−s)` is a reflection across Re(s) = 1/2. Under the substitution `s = 1/2 + it`, this becomes `ξ(1/2 + it) = ξ(1/2 − it)` — the zeros of ξ on the critical line are symmetric under reflection across the real axis in t-space. The Joukowsky map implements this reflection: `z + 1/z` is invariant under `z → 1/z`, which is exactly the reflection s ↔ 1−s in disguise.

**The fixed locus of z → 1/z is the unit circle. The fixed locus of s ↔ 1−s is the critical line Re(s) = 1/2. These are the same geometric object under the substitution z = e^{2πis}.**

---

## Derivation Path

The J_N inversion in SMIP is `r → 1/r`. This is the radial component of the Joukowsky map restricted to positive reals. The full Joukowsky map extends this to the complex plane, where it becomes a Möbius transformation of the Riemann sphere.

The Riemann zeros lie on the critical line. The Joukowsky map converts the critical line to the unit circle. The **Berry-Keating Hamiltonian H = xp** has classical orbits that are hyperbolas in (x,p) phase space — under the substitution `z = x + ip`, these hyperbolas are the level sets of `|z + 1/z|`. The eigenvalues of H (the Riemann zeros, conjecturally) are therefore the values of t where the Joukowsky level sets close — i.e., where they hit the unit circle.

**Derivation target:** The spectral problem for H = xp with boundary conditions on the unit circle (via Joukowsky) is a **well-posed self-adjoint operator problem** in the Hilbert space `L²(unit circle, dθ)`. The eigenvalues of this problem are computable. If they match the Riemann zeros, the Berry-Keating conjecture is established geometrically. The Joukowsky transform provides the coordinate system in which the boundary conditions become natural.

The d* coordinate `0.24600` is the distance from the real axis to the first Riemann zero under the Joukowsky parametrization. The 0.00070 gap `|d*·ln(10) − Ω|` is the residual after projecting this distance from the natural (Ω) coordinate to the base-10 (d*) coordinate. The Joukowsky map is the projection.

---

## SMIP Connection

J_N is the algebraic core of SMIP's inversion engine. The Joukowsky transform is J_N embedded in the complex plane. The full conformal structure of the Joukowsky map — its fixed points, its critical locus, its branch cuts — is the geometric description of what the Inversion Engine does to information at the sedenion boundary. The unit circle = the sedenion zero-divisor locus = the Riemann critical line: three descriptions of the same object.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
