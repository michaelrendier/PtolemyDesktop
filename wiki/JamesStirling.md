# James Stirling

**Born:** 1692, Garden, Stirlingshire, Scotland  
**Died:** 5 December 1770, Edinburgh  
**Fields:** Analysis, series, interpolation  
**Position in Ptolemy:** The Stirling polynomial provides the degree-9 basin attractor system. Newton's method on the Stirling polynomial produces eight root basins — the output routing topology of the SMNNIP Output Engine.

---

## Biography

James Stirling studied at Glasgow and Oxford (expelled for Jacobite connections), spent years in Venice, and corresponded with Newton. His major work *Methodus Differentialis* (1730) systematized interpolation and introduced the formula now bearing his name. He spent his later career managing a mining company in Scotland — mathematics was a side occupation for much of his life. His work was recognized by contemporaries including Euler and Maclaurin.

---

## Stirling's Approximation

The approximation for large factorials:

$$n! \approx \sqrt{2\pi n} \left(\frac{n}{e}\right)^n$$

In radian/logarithmic form:

$$\ln(n!) \approx n\ln(n) - n + \frac{1}{2}\ln(2\pi n)$$

Full asymptotic series:

$$\ln\Gamma(z) = z\ln z - z - \frac{1}{2}\ln\frac{z}{2\pi} + \frac{1}{12z} - \frac{1}{360z^3} + \cdots$$

This is not merely an approximation for computation — it describes how rapidly-growing functions behave asymptotically. In the context of Ptolemy's Lorenz-Stirling system, the polynomial root structure of the Stirling expansion governs basin topology.

---

## Stirling Numbers

**Stirling numbers of the second kind** $S(n,k)$: the number of ways to partition a set of $n$ elements into $k$ non-empty subsets.

$$x^n = \sum_{k=0}^{n} S(n,k) \, x^{(k)}$$

where $x^{(k)} = x(x-1)(x-2)\cdots(x-k+1)$ is the falling factorial.

The generating polynomial structure — mapping power bases to factorial bases — is the algebraic origin of the degree-9 polynomial used in the SMNNIP basin system.

---

## Ptolemy Connection — Degree-9 Stirling Basin System

Newton's method applied to the degree-9 Stirling polynomial produces **eight root basins** corresponding to the eight octonion dimensions ($e_0$ through $e_7$). Each basin is an attractor — a trajectory falling into basin $k$ routes to octonion dimension $k$.

The UF formulary constant `om.ufm V=10` sets the iteration depth. The eight basins map to:

| Basin | Octonion Dim | Semantic Role |
|---|---|---|
| 0 | $e_0$ | Real component — scalar ground |
| 1–7 | $e_1$–$e_7$ | Imaginary octonion — semantic dimensions |

Bifurcation boundary between basins detected by Lyapunov sign change (see [[EdwardLorenz]]). The joint system is `LorenzStirling.py` in Archimedes.

---

## Selected Bibliography

- Stirling, J. (1730). *Methodus Differentialis*. London.
- Abramowitz, M. & Stegun, I.A. (1964). *Handbook of Mathematical Functions*. NIST. Ch. 6 (Gamma function) and Ch. 24 (Stirling numbers).
- Graham, R.L., Knuth, D.E. & Patashnik, O. (1994). *Concrete Mathematics*. Addison-Wesley. Ch. 6.

---

## See Also
- [[EdwardLorenz]] — joint basin-attractor system
- [[Archimedes]] — LorenzStirling.py
- [[Alexandria]] — Newton basin fractal visualization
