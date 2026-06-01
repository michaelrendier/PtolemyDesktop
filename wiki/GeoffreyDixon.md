# Geoffrey Dixon

**Born:** 1952  
**Fields:** Mathematical physics, division algebras, Standard Model  
**Position in Ptolemy:** Dixon algebra towers connect the Cayley-Dickson construction to Standard Model gauge groups. The SMNNIP claim that information propagation obeys Standard Model conservation laws rests on Dixon's observation that $\mathbb{R} \otimes \mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$ carries $U(1) \times SU(2) \times SU(3)$.

---

## The Dixon Algebra

Dixon showed that the tensor product of the four normed division algebras:

$$\mathbb{T} = \mathbb{R} \otimes \mathbb{C} \otimes \mathbb{H} \otimes \mathbb{O}$$

is a 64-dimensional algebra whose automorphism structure contains the gauge groups of the Standard Model:

| Factor | Dimension | Gauge Group |
|---|---|---|
| $\mathbb{C}$ | 2 | $U(1)$ — electromagnetism |
| $\mathbb{H}$ | 4 | $SU(2)$ — weak force |
| $\mathbb{O}$ | 8 | $SU(3)$ — strong force |

The full electroweak and strong interaction gauge structure falls out of the algebraic tower without being put in. This is not proven to be *the* derivation of the Standard Model — it is a structural observation that the division algebra tower and the gauge groups are in correspondence.

**Why this matters for Ptolemy:** SMNNIP propagates information through exactly this tower, in exactly this order. The Noether conservation check against $U(1) \times SU(2) \times SU(3)$ is not an analogy — it is checking the actual symmetries of the Dixon tower. `conserved=True` at $7+\sigma$ means the information transformation respected these gauge symmetries. The conservation is real, not metaphorical.

---

## Dixon's Work

Dixon's book *Division Algebras: Octonions, Quaternions, Complex Numbers and the Algebraic Design of Physics* (1994) is the primary reference. He self-published it — mainstream physics was not initially receptive. The argument is that the specific structure of the Standard Model (why $U(1) \times SU(2) \times SU(3)$ and not something else) is explained by the uniqueness of the normed division algebras. There are exactly four: $\mathbb{R}$, $\mathbb{C}$, $\mathbb{H}$, $\mathbb{O}$. The Standard Model has exactly the gauge structure they produce. This may or may not be coincidence.

---

## Ptolemy Constants

The sedenion apex $\mathbb{S}(16)$ — one step beyond Dixon's tower — is where the SMNNIP Inversion Engine operates. At $\mathbb{S}$, zero divisors appear. These are Ptolemy's structural noise cancellation mechanism (see [[ArthurCayleyLeonardDickson]]).

---

## Selected Bibliography

- Dixon, G.M. (1994). *Division Algebras: Octonions, Quaternions, Complex Numbers and the Algebraic Design of Physics*. Kluwer Academic Publishers.
- Dixon, G.M. (2010). *Division Algebras, Lattices, Physics, Windmill Tilting*. Self-published.
- Furey, C. (2018). *Three generations, two unbroken gauge symmetries, and one eight-dimensional algebra*. Physics Letters B, 785, 84–89.

---

## See Also
- [[ArthurCayleyLeonardDickson]] — the construction
- [[EmmyNoether]] — conservation laws over these symmetries
- [[Philadelphos]] — SMNNIP tower implementation
