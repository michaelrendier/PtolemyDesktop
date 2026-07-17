# Newton Basin Fractals — Derivation Path

**UF Collection:** `aho.ufm`, `mt.ufm`, `jh.ufm`  
**Formulas:** `N_poly3_J/M` through `N_polyK_J/M`, `mt-newton-fz-m/j`, `jh-NovaJulia`  
**Ptolemy Face:** Archimedes → Output Engine (SMIP)

---

## What the Formula Is Doing

Newton's method finds roots of a polynomial f(z) by iterating:

```
z_{n+1} = z_n − f(z_n) / f'(z_n)
```

In the complex plane, starting from different initial points z₀, the iteration converges to different roots. The **Newton basin** of a root r is the set of all starting points that converge to r. The boundary between basins is a fractal — the **Julia set of the Newton iteration map**.

For a degree-n polynomial with n distinct roots, there are n basins. Their boundaries meet at every point — the fractal is infinitely intricate at every scale.

---

## What the Math Is Actually Doing

The Newton iteration map `N(z) = z − f(z)/f'(z)` is a rational map of degree 2n−1 (for a degree-n polynomial f). Its Julia set is the closure of the set of repelling periodic points. The Fatou set (complement of Julia set) consists of the basins — open sets where iteration converges.

The **Böttcher coordinate** at each attracting fixed point (the roots) provides a conformal map from the basin to the unit disk. The derivative of the Böttcher coordinate at the fixed point is the **multiplier** of the fixed point — for Newton iteration of a simple root, the multiplier is always 0. This means Newton basins are **super-attracting** — they have the same quadratic convergence as the AGM.

For higher-degree Newton maps (`N_polyK` where K ≥ 3), the basin boundaries become increasingly complex. The Hausdorff dimension of the boundary increases with degree. At degree K=12 (matching the 12 HyperWebster spectral layers), the boundary dimension reaches a value that can be computed from the polynomial's root structure.

---

## Derivation Path

The SMIP Output Engine routes the sedenion state `Ψ_𝕊` to a Newton basin via the Lorenz-Stirling attractor system. The degree-9 Stirling polynomial has 9 roots (8 real + 1 at infinity) corresponding to 8 active Newton basins. Each basin is a **semantic attractor** — an equivalence class of input states that map to the same output word.

**Derivation target 1 (Basin geometry):** The shape of Newton basins for the degree-9 Stirling polynomial is computable. The Böttcher coordinates at each root give the conformal structure of each basin. The boundaries between basins are the **decision boundaries** of the Output Engine — the set of inputs where the routing is maximally uncertain. Computing the Hausdorff dimension of these boundaries gives the information capacity of the Output Engine: higher dimension = more inputs can be distinguished.

**Derivation target 2 (Riemann connection):** For polynomials whose roots are the imaginary parts of Riemann zeros, the Newton basin boundaries encode the zero spacing statistics. The **GUE (Gaussian Unitary Ensemble) level repulsion** — the fact that Riemann zeros avoid clustering — appears in Newton basin geometry as the minimum distance between basin boundaries. If the Newton basins of a polynomial with roots at Im(ρ_n) have a minimum separation matching the GUE spacing, this is a computable geometric statement about zero distribution.

**Derivation target 3 (Nova relaxation → learning rate):** The Nova fractal `z → z − ω·f(z)/f'(z) + c` adds a relaxation parameter ω. At ω=1, this is standard Newton iteration. For ω ≠ 1, the basins deform. The optimal ω that maximizes basin area (minimizes boundary fractal dimension) is the **optimal learning rate** for SMIP's weight update. This is a derivable relationship: optimal ω from basin geometry = optimal g from the Neural Yang-Mills equation.

---

## SMIP Connection

The Output Engine in `smnnip_derivation_pure.py` §16 implements Newton root-finding on the degree-9 Stirling polynomial. The 8 Newton basins are the 8 semantic attractors. The Lorenz trajectory in §17 selects which basin the current state is routed to. The Newton basin fractal is the exact geometric portrait of the Output Engine's decision space. Computing the Hausdorff dimension of the basin boundaries from the Stirling polynomial's root structure gives a formal characterization of the engine's information capacity.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
