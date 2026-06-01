# Cohl Furey

**Active:** 2010s–present  
**Institution:** University of Cambridge (Dept. of Applied Mathematics and Theoretical Physics)  
**Fields:** Mathematical physics, division algebras, Standard Model, particle physics  
**Position in Ptolemy:** Cohl Furey independently derived the Standard Model gauge structure from the algebra $\mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$ — the tensor product of the three complex division algebras. Her work confirms the Hurwitz-forced Cayley-Dickson tower as the algebraic origin of $U(1) \times SU(2) \times SU(3)$, and provides a second independent derivation of what Geoffrey Dixon established through a different algebraic path.

---

## Overview

Cohl Furey is a mathematical physicist whose work focuses on deriving the Standard Model of particle physics from the algebra of the division algebras — specifically the complexified octonions $\mathbb{C} \otimes \mathbb{O}$ and the product $\mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$.

Her approach is notable for its economy: she derives quarks, leptons, and gauge bosons from the multiplication rules of the normed division algebras, without additional structure. The algebra already contains the physics — you just need to look at it correctly.

She is one of a small number of researchers (alongside Geoffrey Dixon, John Baez, and others) who have pursued the program of grounding the Standard Model in the mathematics of division algebras. In this program, the Standard Model is not a list of empirical facts about particles — it is a theorem about what symmetries a normed division algebra admits.

---

## The $\mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$ Construction

Furey's key insight is that the algebra:

$$A = \mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$$

(complexified quaternions tensored with complexified octonions) contains the Standard Model gauge group as a subgroup of its automorphism group.

Specifically:

- $\mathbb{C}$ contributes $U(1)$ — the electromagnetic gauge group
- $\mathbb{H}$ contributes $SU(2)$ — the weak force gauge group  
- $\mathbb{O}$ contributes $SU(3) \subset G_2 = \text{Aut}(\mathbb{O})$ — the strong force gauge group

The product algebra has internal structure that, when decomposed, yields exactly:

$$U(1) \times SU(2) \times SU(3)$$

No additional assumptions. No extra fields. The Standard Model gauge group emerges from the algebra of the normed division algebras.

---

## Quarks, Leptons and the Fano Plane

Within Furey's framework:

- The **Fano plane** (the multiplication table of the octonion imaginary units $e_1, \ldots, e_7$) encodes the SU(3) color structure of quarks
- The **three generations** of quarks correspond to the three pairs of Fano lines through each point
- **Color confinement** follows from the non-associativity of the octonions — the SU(3) action is well-defined, but composite states must be SU(3)-neutral (colorless) for the algebra to close

The ValaQuenta Lagrangian module encodes the Fano plane structure:

```python
FANO_LINES = [
    (0,1,3),(1,2,4),(2,3,5),(3,4,6),(4,5,0),(5,6,1),(6,0,2)
]
```

These seven lines are the multiplication rules of the octonion imaginary units. Furey's framework reads the Standard Model directly off this structure.

---

## Comparison with Dixon

Geoffrey Dixon (see [[GeoffreyDixon]]) derived the same result through the algebra $\mathbb{H} \otimes \mathbb{C} \otimes \mathbb{O}$ in a different order, with a slightly different methodology. Both arrive at $U(1) \times SU(2) \times SU(3)$. The convergence of two independent derivations from the same algebraic data is significant.

| Researcher | Algebra | Approach |
|---|---|---|
| Dixon (1994) | $\mathbb{H} \otimes \mathbb{C} \otimes \mathbb{O}$ | Division algebra as spacetime algebra |
| Furey (2014–present) | $\mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$ | Clifford algebra decomposition |
| SMMIP | Cayley-Dickson tower $\mathbb{R} \to \mathbb{C} \to \mathbb{H} \to \mathbb{O}$ | Sequential doubling, Hurwitz forced termination |

All three reach the same gauge group. The SMMIP approach is sequential (the tower) rather than tensorial (the product), but the gauge groups it produces are identical.

---

## The Three-Generation Problem

One open question in Furey's framework (and in Dixon's) is the origin of the **three generations** of fermions. The Standard Model has three copies of the quark-lepton spectrum:
- Generation 1: electron, electron neutrino, up quark, down quark
- Generation 2: muon, muon neutrino, charm quark, strange quark
- Generation 3: tau, tau neutrino, top quark, bottom quark

In Furey's framework, the three generations are associated with the three Fano lines through each of the seven octonion imaginary units. This is an active area of her research.

In SMMIP, the three generations correspond to three orbital levels of the algebra tower — the ℂ, ℍ, and 𝕆 levels each carrying one generation's worth of symmetry before the sedenion boundary terminates the sequence.

---

## Ptolemy Connection

Furey is in SMMIP's outreach list (`outreach/emails/`). Her work and the SMMIP framework are complementary — she derives from the algebra down to particles; SMMIP derives from the algebra up to the Riemann zeta function. Both use the same normed division algebra tower.

The Fano plane in ValaQuenta's lagrangian module is the structural overlap. The SMMIP framework does not cite Furey as a source — it arrived at the same structure from the information-theoretic direction — but her derivation is the closest independent confirmation of the algebraic foundation.

---

## Selected Bibliography

- Furey, C. (2012). *Unified theory of ideals*. Physical Review D, 86, 025024.
- Furey, C. (2016). *Standard Model Physics from an Algebra?* PhD thesis, University of Waterloo.
- Furey, C. (2018). *Three generations, two unbroken gauge symmetries, and one eight-dimensional algebra*. Physics Letters B, 785, 84–89.
- Furey, C. (2018). *SU(3)_C × SU(2)_L × U(1)_Y (×U(1)_X) as a symmetry of division algebraic ladder operators*. European Physical Journal C, 78, 375.

---

## See Also

- [[GeoffreyDixon]] — independent parallel derivation
- [[Hurwitz]] — the theorem that makes the tower terminate
- [[ArthurCayleyLeonardDickson]] — the doubling construction
- [[EdwardWitten]] — M-theory G₂ compactification (same gauge group, geometric language)
