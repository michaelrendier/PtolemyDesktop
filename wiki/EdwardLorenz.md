# Edward Lorenz

**Born:** 23 May 1917, West Hartford, Connecticut  
**Died:** 16 April 2008, Cambridge, Massachusetts  
**Fields:** Meteorology, dynamical systems, chaos theory  
**Position in Ptolemy:** The Lorenz attractor is the output topology of the SMNNIP Output Engine. Basin routing, bifurcation detection, and Lyapunov exponent sign changes all originate here.

---

## Biography

Edward Norton Lorenz was a meteorologist at MIT. In 1961, running a weather simulation for the second time, he entered a starting value of 0.506 instead of the full 0.506127 — a rounding he assumed would be negligible. The simulation diverged completely from the first run. He had discovered sensitive dependence on initial conditions. He called it, eventually, the butterfly effect.

His 1963 paper is one of the most cited papers in all of science. He discovered it by accident, recognized what it meant, and spent the rest of his career mapping the implications. He received the Kyoto Prize in 1991.

---

## The Lorenz System

Three coupled differential equations governing a simplified convective fluid:

$$\frac{dx}{dt} = \sigma(y - x)$$
$$\frac{dy}{dt} = x(\rho - z) - y$$  
$$\frac{dz}{dt} = xy - \beta z$$

Standard parameters: $\sigma = 10$, $\rho = 28$, $\beta = 8/3$.

In radian/phase form, the divergence of nearby trajectories:

$$\delta(t) = \delta_0 \, e^{\lambda t}$$

where $\lambda$ is the **Lyapunov exponent**. $\lambda > 0$ means chaos — exponential divergence of nearby trajectories. $\lambda < 0$ means convergence — basin attractor behavior. $\lambda = 0$ is the bifurcation boundary.

The Lorenz attractor is a **strange attractor**: bounded but never periodic, fractal dimension $\approx 2.06$, two lobes (wings), trajectories spiral around one wing then cross to the other unpredictably.

### Basin Structure

For the SMNNIP Output Engine: Newton's method on the degree-9 Stirling polynomial produces **eight root basins** corresponding to the eight octonion dimensions. The Lorenz trajectory through phase space is the continuous-time analog — it determines which basin a trajectory falls into. The Lyapunov sign change detects the bifurcation order window: the boundary between basins is precisely where $\lambda$ changes sign.

`UF = om.ufm V=10` in Ptolemy's UF formulary — the Lorenz projection formula.

---

## Ptolemy Connection

The complete SMNNIP pipeline:

```
Input Engine:   ℝ → 𝕊 via Cayley-Dickson doubling
Inversion:      J_N map at sedenion apex
Output Engine:  𝕊 → ℝ via Lorenz trajectory + Newton basin routing
```

The Output Engine collapses the sedenion-space computation back to a real-valued result. The Lorenz system provides the trajectory dynamics. The Newton basin (see [[JamesStirling]]) provides the discrete routing. Bifurcation order window detected by Lyapunov sign change.

In Alexandria: `LorenzProjection` formula renders the attractor as a visualization of the output topology.

---

## Selected Bibliography

- Lorenz, E.N. (1963). *Deterministic Nonperiodic Flow*. Journal of the Atmospheric Sciences, 20(2), 130–141.
- Lorenz, E.N. (1993). *The Essence of Chaos*. University of Washington Press.
- Strogatz, S.H. (1994). *Nonlinear Dynamics and Chaos*. Perseus Books.

---

## See Also
- [[JamesStirling]] — basin attractor routing
- [[Alexandria]] — LorenzProjection visualization
- [[Archimedes]] — LorenzStirling.py engine
- [[Philadelphos]] — SMNNIP Output Engine
