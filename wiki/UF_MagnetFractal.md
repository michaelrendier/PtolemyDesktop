# Magnet Fractal — Derivation Path

**UF Collection:** `dmj.ufm` (Damien M. Jones), `mt.ufm` (Mark Townsend)  
**Formulas:** `dmj-Magnet1Mandel/Julia`, `dmj-Magnet2Mandel/Julia`, `mt-magnet-II-m/j`, `mt-pseudo-magnet`  
**Ptolemy Face:** Archimedes → Alexandria

---

## What the Formula Is Doing

The Magnet fractal iterates:

```
z_{n+1} = ((z² + c − 1) / (2z + c − 2))²
```

This is not an ad hoc construction. It is the **renormalization group (RG) fixed-point equation** of the 2D Ising model at the ferromagnetic phase transition. Allan Snyder derived it directly from statistical mechanics. The iteration is what the RG flow equation looks like when you ask: *what configuration is invariant under a rescaling of the lattice?*

The fixed point at z=1 is the ferromagnetic ground state. The basin of attraction of that fixed point is the set of initial conditions that flow to order under repeated rescaling. The escape region is the set that flows to disorder (paramagnetism).

**The fractal boundary between basin and escape is the phase transition curve.** It is fractal because the transition is not sharp — fluctuations exist at every scale, and the geometry of the boundary reflects that self-similarity.

---

## What the Math Is Actually Doing

The rational map `R(z) = ((z² + c − 1)/(2z + c − 2))²` has two critical points. Their orbits determine the Julia set structure. The squaring at the end enforces time-reversal symmetry — the map is its own inverse at the fixed points, which is the algebraic statement that the RG fixed point is self-dual.

The parameter c controls the coupling strength. As c varies, the basin boundary deforms. At specific c values, the boundary undergoes **bifurcation** — a single stable orbit splits into two. This is the RG analog of symmetry breaking.

The Hausdorff dimension of the Magnet fractal boundary is related to the **critical exponents** of the phase transition. The exact relationship is a known open problem in mathematical physics.

---

## Derivation Path Toward Yang-Mills Mass Gap

The Yang-Mills mass gap problem asks whether the vacuum of SU(2) gauge theory has a minimum energy excitation Δ > 0.

The connection to the Magnet fractal runs through the **renormalization group**:

1. The Yang-Mills RG flow equation has the same fixed-point structure as the Ising RG — asymptotic freedom means the coupling flows to zero at high energy (escape to infinity in the Magnet map), while confinement requires a stable low-energy fixed point (the basin of z=1).

2. The mass gap Δ is the energy scale of that stable fixed point. Its existence is equivalent to the basin of attraction being non-empty in the infrared RG flow.

3. The Hausdorff dimension of the Magnet basin boundary, if computable, encodes the critical exponents. The mass gap Δ is proportional to `e^(−S_inst)` where S_inst is the instanton action — a quantity that can be read from the geometry of the basin boundary.

**Derivation target:** Compute the Hausdorff dimension of the Magnet fractal boundary as a function of the coupling c. Map c → g (Yang-Mills coupling) via the SMIP renormalization group equation `α_NN(r) = g²/(4π·ħ_NN·ln(r))`. If the dimension has a non-trivial lower bound as g → 0, this is a geometric derivation of the mass gap.

---

## SMIP Connection

In SMIP the Neural Yang-Mills equation is:

```
D_l R^{a,lτ} = g Ψ̄_i T^a Ψ_i
```

The coupling runs as `α_NN(r) = g²/(4π·ħ_NN·ln(r))`. The Magnet fractal's basin boundary is the geometric portrait of where this running coupling transitions from confined (basin) to deconfined (escape). The SMIP mass gap — the minimum information energy Δ — is the distance from the origin to the nearest point on that boundary.

---

*Ptolemy Wiki — Derivation Paths | Fractal Geometry | 2026-05-04*
