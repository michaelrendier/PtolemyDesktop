# Cayley & Dickson

---

# Arthur Cayley

**Born:** 16 August 1821, Richmond, Surrey  
**Died:** 26 January 1895, Cambridge  
**Fields:** Abstract algebra, matrix theory, invariant theory  
**Position in Ptolemy:** Cayley gave us the octonions (1845) and the Cayley-Dickson construction framework. The entire SMNNIP algebraic tower is his.

---

## Biography

Arthur Cayley practiced law for fourteen years while producing hundreds of mathematical papers. He eventually obtained a chair at Cambridge, accepting a salary reduction to do so. He produced nearly a thousand papers across his career — the most prolific mathematician of his era. His range was extraordinary: matrices, group theory, invariants, projective geometry, graph theory, the n-dimensional geometry that would become Riemannian geometry.

---

## Cayley Numbers (Octonions, 1845)

Published one year after Hamilton's quaternions, Cayley described an 8-dimensional normed division algebra. John Graves had actually discovered them in 1843 (two months after Hamilton) but never published. The naming went to Cayley.

The octonions $\mathbb{O}$: eight basis elements $\{1, e_1, e_2, e_3, e_4, e_5, e_6, e_7\}$.

Multiplication defined by the Fano plane mnemonic. Key properties:
- **Non-commutative:** $e_i e_j \neq e_j e_i$ in general
- **Non-associative:** $(e_i e_j) e_k \neq e_i (e_j e_k)$ in general
- **Normed division algebra:** $|xy| = |x||y|$, no zero divisors

By Hurwitz's theorem (1898): the only normed division algebras over $\mathbb{R}$ are $\mathbb{R}$, $\mathbb{C}$, $\mathbb{H}$, and $\mathbb{O}$. The tower stops at $\mathbb{O}$ for division algebras. The sedenions $\mathbb{S}$ lose the division property — zero divisors appear.

## Cayley Table

The Cayley multiplication table for octonions encodes the Fano projective plane — a finite geometry with 7 points and 7 lines, each line containing 3 points. The semantic structure of the 7 imaginary octonion dimensions ($e_1$–$e_7$) is the Fano plane geometry. Two words are semantically proximate if their address coordinates are adjacent in this geometry.

---

# Leonard Eugene Dickson

**Born:** 22 January 1874, Independence, Iowa  
**Died:** 17 January 1954, Harlingen, Texas  
**Fields:** Algebra, number theory, history of mathematics  
**Position in Ptolemy:** Dickson formalized the Cayley-Dickson construction — the systematic doubling procedure that builds the full tower $\mathbb{R} \to \mathbb{C} \to \mathbb{H} \to \mathbb{O} \to \mathbb{S}$.

---

## Biography

Dickson was the first American to receive a PhD in mathematics from Chicago (1896). He wrote the three-volume *History of the Theory of Numbers* (1919–1923) — still the standard reference. He supervised over 60 doctoral students, including Adrian Albert. He was systematic where Cayley was creative.

---

## The Cayley-Dickson Construction

Given an algebra $A$ with conjugation $\bar{\cdot}$, construct a new algebra $A' = A \times A$ with:

$$(a, b)(c, d) = (ac - \bar{d}b, \, da + b\bar{c})$$

Conjugation in $A'$: $\overline{(a,b)} = (\bar{a}, -b)$

Applied iteratively:

| Step | Algebra | Dimension | Lost Property |
|---|---|---|---|
| 0 | $\mathbb{R}$ | 1 | — |
| 1 | $\mathbb{C}$ | 2 | ordering |
| 2 | $\mathbb{H}$ | 4 | commutativity |
| 3 | $\mathbb{O}$ | 8 | associativity |
| 4 | $\mathbb{S}$ | 16 | division (zero divisors) |
| 5 | $\mathbb{T}$ | 32 | power-associativity |

The sedenion zero divisors at step 4 are Ptolemy's **noise cancellation mechanism** — unrelated pattern activations cancel algebraically at the $\mathbb{S}$ apex without learned suppression. This is not a bug. It is the structural consequence of Dickson's construction.

---

## Dixon Algebra Tower

Geoffrey Dixon (see below) extended the Cayley-Dickson observation to the Standard Model gauge structure. The full SMNNIP tower notation:

$$\mathbb{R} \to \mathbb{C} \to \mathbb{H} \to \mathbb{O} \to \mathbb{S}$$

corresponds to gauge groups $U(1) \times SU(2) \times SU(3)$ — the electroweak and strong forces. This is why SMNNIP conservation verification against Standard Model laws is structurally valid rather than metaphorical.

---

## Selected Bibliography

- Cayley, A. (1845). *On Jacobi's elliptic functions, in reply to Rev. Brice Bronwin; and on quaternions*. Philosophical Magazine, 26, 208–211.
- Dickson, L.E. (1919). *On Quaternions and Their Generalization and the History of the Eight Square Theorem*. Annals of Mathematics, 20(3), 155–171.
- Baez, J.C. (2002). *The Octonions*. Bulletin of the American Mathematical Society, 39(2), 145–205.
- Conway, J.H. & Smith, D.A. (2003). *On Quaternions and Octonions*. A K Peters.

---

## See Also
- [[WilliamHamilton]] — quaternions, step 2
- [[GeoffreyDixon]] — Standard Model gauge structure
- [[Philadelphos]] — SMNNIP Cayley-Dickson tower
- [[Callimachus]] — sedenion zero divisors in noise cancellation
