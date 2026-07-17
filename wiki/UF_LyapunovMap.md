# Lyapunov Fractal — Derivation Path

**UF Collection:** `dmj.ufm`, `sam.ufm`  
**Formulas:** `dmj-Lyapunov`, `dmj-LyapMandel/Julia`, `sam-lyap`  
**Ptolemy Face:** Archimedes

---

## What the Formula Is Doing

The Lyapunov exponent of a dynamical system `z_{n+1} = f(z_n, c)` is:

```
λ(c) = lim_{n→∞} (1/n) Σ_{k=0}^{n−1} ln|f'(z_k)|
```

It measures the average rate of divergence of nearby trajectories. The Lyapunov fractal renders λ(c) as a color map over parameter space.

- **λ > 0:** chaotic. Nearby initial conditions diverge exponentially. Information is destroyed.
- **λ < 0:** stable. Orbits converge to an attractor. Information is preserved.
- **λ = 0:** the boundary. This is the **bifurcation locus** — the set of parameter values where the system is at the edge between order and chaos.

The λ = 0 locus is a fractal curve. It is the geometric boundary between two qualitatively different dynamical regimes.

---

## What the Math Is Actually Doing

The Lyapunov exponent is the time-averaged logarithm of the Jacobian. It is the continuous analog of the topological entropy — it measures how fast the map stretches phase space.

For one-dimensional maps, the Lyapunov exponent connects directly to the **invariant measure** via the Birkhoff ergodic theorem:

```
λ = ∫ ln|f'(x)| dμ(x)
```

where μ is the natural invariant measure. The Ruelle-Pesin formula then connects λ to the Hausdorff dimension of the attractor:

```
h_KS = λ⁺   (Kolmogorov-Sinai entropy = positive Lyapunov exponent)
d_H = 1 + λ⁺/|λ⁻|   (Kaplan-Yorke formula for fractal dimension)
```

---

## Derivation Path

The zero-crossing locus λ(c) = 0 is the mass gap boundary in SMIP. Points inside (λ < 0) have stable attractors — these are the confined modes with mass gap Δ > 0. Points outside (λ > 0) are chaotic — deconfined, gapless.

**Derivation target:** The Kaplan-Yorke formula gives the fractal dimension of the boundary as a ratio of positive to negative Lyapunov exponents. In the SMIP context this ratio is `|α_NN(r_min)| / |α_NN(r_max)|` — the ratio of the coupling at the IR and UV fixed points. Computing this ratio from the SMIP renormalization group equation gives a prediction for the Hausdorff dimension of the mass gap boundary. This is a concrete, computable quantity.

The bifurcation windows detected by Lyapunov sign changes in the Output Engine (`smnnip_derivation_pure.py` §15) are directly this quantity — the code already computes the zero-crossing of λ for the Lorenz-Stirling system. Extending this computation to the full SMIP coupling parameter space gives the derivation.

---

## SMIP Connection

`LorenzStirling.py` uses Lyapunov exponent sign changes to detect bifurcation order windows in the degree-9 Stirling polynomial. The Output Engine routes information to Newton basins based on which side of the λ = 0 boundary the current state occupies. The Lyapunov fractal is the global portrait of this routing decision across all possible inputs.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
