# William Rowan Hamilton

**Born:** 4 August 1805, Dublin, Ireland  
**Died:** 2 September 1865, Dublin  
**Fields:** Classical mechanics, optics, algebra  
**Position in Ptolemy:** Hamiltonians govern the LLH (Lagrangian Laplacian Hamiltonian) system. The quaternion — Hamilton's invention — is the first step of the Cayley-Dickson tower: $\mathbb{R} \to \mathbb{C} \to \mathbb{H}$.

---

## Biography

William Rowan Hamilton was a prodigy — he knew thirteen languages by thirteen years old. He became Astronomer Royal of Ireland at 22, while still an undergraduate. He spent the next forty years at Dunsink Observatory outside Dublin, eventually neglecting his duties entirely in pursuit of algebra.

On 16 October 1843, walking along the Royal Canal in Dublin, he realized the solution to the problem he had been working on for years. He carved the fundamental quaternion equations into the stone of Broom Bridge with his penknife:

$$i^2 = j^2 = k^2 = ijk = -1$$

The plaque is still there. The carving is not.

He spent the last 22 years of his life writing *Elements of Quaternions*, which he never finished. It was published posthumously in 1866 — 800 pages for what could be stated in a few lines. His personal life collapsed. He drank. He died before seeing quaternions find their application.

---

## Mathematical Contributions

### Quaternions

Four-dimensional normed division algebra over $\mathbb{R}$:

$$q = a + bi + cj + dk, \quad a,b,c,d \in \mathbb{R}$$

Multiplication rules:

$$i^2 = j^2 = k^2 = -1$$
$$ij = k, \quad jk = i, \quad ki = j$$
$$ji = -k, \quad kj = -i, \quad ik = -j$$

**Non-commutative.** $ij \neq ji$. This was shocking in 1843 — no algebra of numbers had ever been non-commutative. Hamilton had discovered that extending dimensions requires sacrificing commutativity. Cayley and Dickson would later formalize this: each doubling sacrifices one property.

In radian/rotation form, a unit quaternion $q = \cos\frac{\theta}{2} + \sin\frac{\theta}{2}(ai + bj + ck)$ represents a rotation by $\theta$ around axis $(a,b,c)$:

$$\mathbf{v}' = q \mathbf{v} q^{-1}$$

Quaternions are the canonical representation of 3D rotation — no gimbal lock, efficient composition, smooth interpolation (SLERP).

### Hamiltonian Mechanics

Reformulation of classical mechanics. State = position $q$ + momentum $p$. The Hamiltonian $H(q,p)$ (usually total energy) governs evolution:

$$\dot{q}_i = \frac{\partial H}{\partial p_i}, \quad \dot{p}_i = -\frac{\partial H}{\partial q_i}$$

In radian/action form, Hamilton's principal function $S$:

$$H\left(q, \frac{\partial S}{\partial q}, t\right) + \frac{\partial S}{\partial t} = 0$$

The Hamilton-Jacobi equation. It connects to the Schrödinger equation through the substitution $S \to -i\hbar \ln \psi$. This is the bridge from classical to quantum mechanics — and from Lagrangian to Hamiltonian mechanics in the LLH system.

### Hodograph

Hamilton invented the concept of the hodograph — the curve traced by the tip of the velocity vector. Less famous but elegant.

---

## Cayley-Dickson Position

$\mathbb{H}$ is the third step in the Cayley-Dickson tower:

$$\mathbb{R} \xrightarrow{\text{+complex}} \mathbb{C} \xrightarrow{\text{+quaternion}} \mathbb{H} \xrightarrow{\text{+octonion}} \mathbb{O} \xrightarrow{\text{+sedenion}} \mathbb{S}$$

Properties surrendered at each step:
- $\mathbb{C}$: loses ordering
- $\mathbb{H}$: loses commutativity  
- $\mathbb{O}$: loses associativity
- $\mathbb{S}$: loses division algebra (zero divisors appear)

---

## Ptolemy Connection

The LLH system — Lagrangian, Laplacian, Hamiltonian — is Ptolemy's information propagation framework. The Hamiltonian component governs the energy-like conservation quantity at each step. Noether's theorem connects symmetries to conserved Hamiltonian quantities. The quaternion is the first non-trivial geometric step in the addressing tower.

---

## Selected Bibliography

- Hamilton, W.R. (1844). *On Quaternions*. Proceedings of the Royal Irish Academy, 3, 1–16.
- Hamilton, W.R. (1866). *Elements of Quaternions*. Longmans Green (posthumous).
- Hankins, T.L. (1980). *Sir William Rowan Hamilton*. Johns Hopkins University Press.

---

## See Also
- [[ArthurCayleyLeonardDickson]] — the doubling construction
- [[Archimedes]] — quaternion operations
- [[Philadelphos]] — LLH system, SMNNIP tower
