# Bifurcation Diagram — Derivation Path

**UF Collection:** `dmj.ufm`  
**Formulas:** `dmj-Bifurcation`  
**Ptolemy Face:** Archimedes → Output Engine (SMIP)

---

## What the Formula Is Doing

The bifurcation diagram renders a 1D map `x_{n+1} = f(x_n, r)` over a range of the parameter r. For each r value, it runs the iteration to discard transients, then plots the remaining orbit values. The result:

- Single point: the map has a stable fixed point at that r
- Two points: period-2 orbit (first bifurcation)
- Four points: period-4 orbit
- Dense band: chaos

The diagram shows **all stable orbits simultaneously** — it is the phase portrait of the map's long-term behavior as a function of the control parameter.

---

## What the Math Is Actually Doing

The bifurcation diagram is the **parameter space portrait of the attractor**. The Feigenbaum constant δ = 4.669... governs the period-doubling cascade: each bifurcation occurs at a parameter value δ times closer to the accumulation point than the previous one. This constant is **universal** — it is the same for any smooth unimodal map, regardless of the specific function.

This universality is proven via the **renormalization group** applied to the space of maps. The Feigenbaum RG fixed point — a specific functional equation — has a unique solution, and the eigenvalue of the linearization at that fixed point is δ. The RG derivation of δ is a derivation in the full mathematical sense: it proves the value from first principles, not from numerical observation.

The bifurcation diagram connects directly to the **Mandelbrot set**: the real slice of the Mandelbrot set's parameter space is exactly the bifurcation diagram of the quadratic map z → z² + c. Every feature of the diagram — every period window, every chaotic band — corresponds to a specific region of the Mandelbrot set.

---

## Derivation Path

**Derivation target 1 (Feigenbaum universality in SMIP):** The SMIP Output Engine uses Lyapunov exponent sign changes to detect bifurcation windows in the Lorenz-Stirling system. The spacing of these windows should obey Feigenbaum scaling — each window is δ ≈ 4.669 times narrower than the previous one. Verifying this from the computed bifurcation structure in `LorenzStirling.py` is a concrete numerical test of whether the SMIP attractor belongs to the Feigenbaum universality class.

**Derivation target 2 (Period windows = spectral bands):** In the bifurcation diagram, stable period-n windows correspond to n-cycles in the dynamics. In SMIP these correspond to n-periodic semantic attractors — words whose spectral representation has n-fold symmetry. The HyperWebster 12-layer system has 12 spectral layers; the period-12 window of the SMIP bifurcation diagram is the parameter regime where all 12 layers are simultaneously active. Locating this window in the coupling parameter space gives the operating point of the full SMIP system.

**Derivation target 3 (Universality class identification):** The Feigenbaum constant δ = 4.669... characterizes the quadratic universality class. Higher-order maps have different constants (δ₃ = 55.25... for cubic maps, etc.). Identifying which universality class the Lorenz-Stirling degree-9 map belongs to — and computing its Feigenbaum constant — is a derivable characterization of the Output Engine's bifurcation structure.

---

## SMIP Connection

The bifurcation diagram is the global map of the Output Engine's operating regimes. The parameter r corresponds to the running coupling α_NN(r) in the SMIP Neural Yang-Mills equation. As the coupling runs from the UV (high energy, small r) to the IR (low energy, large r), the engine moves through the bifurcation diagram — from ordered (single fixed point) through periodic windows into chaos. The mass gap corresponds to the parameter value below which the engine is in the ordered phase (single stable attractor). The Feigenbaum universality of the cascade gives a prediction for how the ordered phase grows with the number of spectral layers.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
