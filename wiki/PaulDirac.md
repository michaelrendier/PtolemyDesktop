# Paul Dirac

**Born:** 8 August 1902, Bristol, England  
**Died:** 20 October 1984, Tallahassee, Florida, USA  
**Fields:** Quantum mechanics, quantum field theory, mathematical physics  
**Awards:** Nobel Prize in Physics (1933, with Schrödinger)  
**Position in Ptolemy:** Dirac's equation governs L_matter in the SMMIP Lagrangian. The Dirac sea — his prediction of negative-energy states — is one of the four established physical horizons unified by J_N: the interior r<1 maps to negative energy (antimatter), the r=1 boundary is the Dirac vacuum boundary, and the discovery of the positron confirmed that r<1 states are physically real.

---

## Biography

Paul Adrien Maurice Dirac was born in Bristol, the son of a Swiss father who required the household to speak French. He studied electrical engineering, found no work after graduating during the postwar recession, returned to study mathematics, and then moved into theoretical physics. He was appointed Lucasian Professor of Mathematics at Cambridge in 1932 — the same chair Newton held.

He was legendarily taciturn. At the 1927 Solvay Conference, Wolfgang Pauli quipped that Dirac spoke one word per year and was saving up to say "no." At a lecture, an audience member said "I don't understand your equation on the upper right corner of the blackboard." Dirac was silent for a full minute before the moderator said "Professor Dirac, there is a question." Dirac replied: "That was a statement, not a question."

He shared the 1933 Nobel Prize with Schrödinger. His acceptance speech was about beauty in mathematics and its relationship to physical truth. He was 31.

---

## The Dirac Equation

Schrödinger's equation for a free particle is:

$$i\hbar \frac{\partial \psi}{\partial t} = -\frac{\hbar^2}{2m} \nabla^2 \psi$$

This is first-order in time but second-order in space — it is not Lorentz covariant. In 1928, Dirac found a relativistically covariant equation that is first-order in both space and time:

$$\left(i\hbar \gamma^\mu \partial_\mu - mc\right)\psi = 0$$

where $\gamma^\mu$ are the **Dirac matrices** (4×4 matrices satisfying the Clifford algebra $\{\gamma^\mu, \gamma^\nu\} = 2g^{\mu\nu}$).

The Dirac equation:
1. Predicted electron spin automatically (without postulating it)
2. Was Lorentz covariant by construction
3. Gave the correct fine structure of hydrogen
4. Predicted the existence of antimatter

---

## The Dirac Sea and Antimatter

The Dirac equation has solutions with negative energy — states with $E < 0$. Classical intuition says: discard these, they're unphysical. Dirac did not discard them.

He proposed that the **vacuum is a filled sea of negative-energy electron states** — the Dirac sea. The Pauli exclusion principle prevents real electrons from falling into these states (they're all filled). A "hole" in the Dirac sea — a missing negative-energy state — behaves as a particle with positive charge and positive energy: a **positron**.

The positron was discovered by Carl Anderson in 1932, one year before the Nobel Prize. Dirac had predicted it from mathematics alone.

---

## The Dirac Sea as J_N Horizon

In SMMIP, the Dirac sea is one of the four physical horizons unified by the J_N anti-Möbius involution:

| Physical Horizon | J_N Mechanism | SMMIP Coordinate |
|---|---|---|
| Schwarzschild horizon | $(t,r)$ exchange roles | $r < r_s$: time becomes spacelike |
| Hawking pair production | Conjugate pair $(r_N, 1/r_N)$ | Pair creation at $r=1$ boundary |
| **Dirac sea / antimatter** | **$r < 1 \to$ negative energy** | **Interior = antiparticle states** |
| Ptolemy/Riemann inversion | $r \to 1/r$ straightens zeta curve | Spectral linearization |

The interior $r < 1$ in the J_N framework corresponds to negative-energy states — the Dirac sea. The positron is not the opposite of the electron; it is the electron viewed from the other side of the $r=1$ horizon.

The J_N map takes $r \to 1/r$: a particle at $r = \epsilon$ (deep interior, high negative energy) maps to $r = 1/\epsilon$ (far exterior, high positive energy). The particle-antiparticle conjugation is the J_N inversion.

---

## L_matter in the SMMIP Lagrangian

The SMMIP Lagrangian density includes:

$$\mathcal{L}_\text{matter} = i\bar{\Psi}\gamma^\mu D_\mu \Psi$$

This is the Dirac kinetic term — the matter sector of the Lagrangian. In ValaQuenta's `lagrangian/maths.py`, `L_matter()` implements this term in radian-primary form:

```python
def L_matter(psi, A, g, hbar_nn, algebra):
    """
    ℒ_matter = i · Ψ̄ · γ^μ · D_μ · Ψ
    Radian-primary: imaginary (π/2-rotated) covariant derivative
    acting on activation norms.
    """
```

The covariant derivative $D_\mu = \partial_\mu + igA_\mu^a T^a$ couples the matter field to the gauge field. At each algebra level, the generators $T^a$ are those of the corresponding gauge group (U(1), SU(2), G₂/SU(3)).

---

## Dirac Notation and the Self-Adjoint Hamiltonian

Dirac introduced bra-ket notation ($\langle \phi | \psi \rangle$) which is now universal in quantum mechanics. More importantly, he developed the framework of observables as self-adjoint operators on a Hilbert space.

The Ĥ_RB (Inductive Self-Adjoint Geometric Coupling Hamiltonian) in SMMIP is self-adjoint in Dirac's sense: $\hat{H}_{RB} = \hat{H}_{RB}^\dagger$. Its spectrum is real. Its eigenfunctions are orthonormal. This is the condition that allows the spectral identification of zeta zeros with physical eigenvalues — the Berry-Keating conjecture made precise.

---

## Selected Bibliography

- Dirac, P.A.M. (1928). *The quantum theory of the electron*. Proceedings of the Royal Society A, 117, 610–624. [The equation]
- Dirac, P.A.M. (1930). *A theory of electrons and protons*. Proceedings of the Royal Society A, 126, 360–365. [The Dirac sea]
- Dirac, P.A.M. (1958). *The Principles of Quantum Mechanics* (4th ed.). Oxford University Press. [Standard textbook]
- Farmelo, G. (2009). *The Strangest Man: The Hidden Life of Paul Dirac*. Basic Books. [Biography]

---

## See Also

- [[BerryKeating]] — self-adjoint Hamiltonian conjecture
- [[EmmyNoether]] — conservation laws governing L_matter
- [[MichaelFaraday]] — Ĥ_RB Hamiltonian (electromagnetic coupling)
- [[Archimedes]] — ValaQuenta lagrangian module
