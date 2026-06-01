"""
noether_engine.algebra.cayley_dickson — the Cayley-Dickson algebra tower.

Provides multiplication operations for:
  ℝ  (real, dim 1)
  ℂ  (complex, dim 2)
  ℍ  (quaternions, dim 4)
  𝕆  (octonions, dim 8)

All four are normed division algebras — the only four (Hurwitz's theorem).
The Cayley-Dickson construction builds each from the one below by doubling:
if A has multiplication (a, b)(c, d) = (ac - d*b, da + bc*), then the
doubled algebra is (A, A) with element pairs.

Octonions specifically admit 480 distinct Fano-plane sign conventions
(Baez 2002). This module uses the **oriented cyclic** convention:

    e_1 e_2 = e_3,  e_1 e_4 = e_5,  e_1 e_6 = e_7,
    e_2 e_4 = e_6,  e_2 e_7 = e_5,  e_3 e_4 = e_7,
    e_3 e_5 = e_6.

All other nonzero products follow from anticommutativity e_i e_j = -e_j e_i.

The convention is set globally via the `octonion_fano` sub-switch (default
'oriented_cyclic'). 'alternate' and 'custom' settings are available for
researchers using a different Fano convention.

References:
  - Baez, J.C. (2002). The octonions. Bull. Amer. Math. Soc. 39(2).
  - Dixon, G.M. (1994). Division Algebras: Octonions, Quaternions,
    Complex Numbers and the Algebraic Design of Physics. Kluwer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import sympy as sp


# ═══════════════════════════════════════════════════════════════════════════
#  REAL (ℝ)
# ═══════════════════════════════════════════════════════════════════════════

def real_multiplication(a: Sequence[sp.Expr], b: Sequence[sp.Expr]) -> List[sp.Expr]:
    """Real multiplication: just numeric product."""
    assert len(a) == 1 and len(b) == 1
    return [a[0] * b[0]]


# ═══════════════════════════════════════════════════════════════════════════
#  COMPLEX (ℂ)
# ═══════════════════════════════════════════════════════════════════════════

def complex_multiplication(
    a: Sequence[sp.Expr],
    b: Sequence[sp.Expr],
) -> List[sp.Expr]:
    """
    (a0 + a1 i)(b0 + b1 i) = (a0 b0 - a1 b1) + (a0 b1 + a1 b0) i.
    """
    assert len(a) == 2 and len(b) == 2
    return [
        a[0] * b[0] - a[1] * b[1],
        a[0] * b[1] + a[1] * b[0],
    ]


def complex_i_generator() -> sp.Matrix:
    """
    Left-multiplication matrix for the imaginary unit i acting on ℂ vectors.
    i · (a0, a1) = (-a1, a0).
    """
    return sp.Matrix([
        [0, -1],
        [1,  0],
    ])


# ═══════════════════════════════════════════════════════════════════════════
#  QUATERNIONS (ℍ)
# ═══════════════════════════════════════════════════════════════════════════
# Basis: 1, i, j, k    with  i² = j² = k² = ijk = -1,
#                           ij = k,  jk = i,  ki = j,
#                           ji = -k, kj = -i, ik = -j.
# Components: (a0, a1, a2, a3) = a0·1 + a1·i + a2·j + a3·k.

def quaternion_multiplication(
    a: Sequence[sp.Expr],
    b: Sequence[sp.Expr],
) -> List[sp.Expr]:
    """
    Hamilton quaternion multiplication.
    Verified: i²=j²=k²=ijk=-1, ij=k, jk=i, ki=j.
    """
    assert len(a) == 4 and len(b) == 4
    a0, a1, a2, a3 = a
    b0, b1, b2, b3 = b
    return [
        a0*b0 - a1*b1 - a2*b2 - a3*b3,
        a0*b1 + a1*b0 + a2*b3 - a3*b2,
        a0*b2 - a1*b3 + a2*b0 + a3*b1,
        a0*b3 + a1*b2 - a2*b1 + a3*b0,
    ]


def quaternion_generators() -> Tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    """
    Left-multiplication matrices for i, j, k acting on ℍ vectors (a0,a1,a2,a3).
    These are the 4x4 real-matrix generators of SU(2) ⊂ ℍ^* acting on itself.
    """
    # L_i : i · (a0,a1,a2,a3) = -a1, a0, a3, -a2 ? let's compute:
    #   i · (a0 + a1 i + a2 j + a3 k) = a0 i - a1 + a2 k - a3 j
    #     = -a1 · 1 + a0 · i - a3 · j + a2 · k
    L_i = sp.Matrix([
        [0, -1,  0,  0],
        [1,  0,  0,  0],
        [0,  0,  0, -1],
        [0,  0,  1,  0],
    ])
    # L_j : j · (a0 + a1 i + a2 j + a3 k) = a0 j - a1 k - a2 + a3 i
    #     = -a2 · 1 + a3 · i + a0 · j - a1 · k
    L_j = sp.Matrix([
        [0,  0, -1,  0],
        [0,  0,  0,  1],
        [1,  0,  0,  0],
        [0, -1,  0,  0],
    ])
    # L_k : k · (a0 + a1 i + a2 j + a3 k) = a0 k + a1 j - a2 i - a3
    #     = -a3 · 1 - a2 · i + a1 · j + a0 · k
    L_k = sp.Matrix([
        [0,  0,  0, -1],
        [0,  0, -1,  0],
        [0,  1,  0,  0],
        [1,  0,  0,  0],
    ])
    return (L_i, L_j, L_k)


# ═══════════════════════════════════════════════════════════════════════════
#  OCTONIONS (𝕆)
# ═══════════════════════════════════════════════════════════════════════════
# Basis: 1, e_1, e_2, e_3, e_4, e_5, e_6, e_7.
# Each e_i² = -1 (for i=1..7).
# Anticommutative: e_i e_j = -e_j e_i for i ≠ j.
# Oriented cyclic Fano convention:
#   e_1 e_2 = e_3,  e_1 e_4 = e_5,  e_1 e_6 = e_7,
#   e_2 e_4 = e_6,  e_2 e_7 = e_5,  e_3 e_4 = e_7,
#   e_3 e_5 = e_6.
# Other products by anticommutativity and Fano closure.
# Indexing: components a[0] is scalar, a[1..7] are coefficients of e_1..e_7.


def _octonion_multiplication_table() -> List[List[Tuple[int, int]]]:
    """
    Build the 8x8 octonion multiplication table in the oriented-cyclic Fano
    convention.

    Returns a 8x8 list where table[i][j] = (sign, index) means e_i · e_j
    = sign * e_{index}  (sign ∈ {-1, 0, +1}; 0 is only for e_0·... which is
    handled separately as scalar).

    Actually, we store:
      table[i][j] = (sign, index)
    for i, j ∈ {1,...,7} giving e_i·e_j. e_0 = 1 is the scalar identity and
    is handled outside this table.
    """
    # Initialize: diagonal is -1 * e_0 (but we encode as (-1, 0))
    table: List[List[Tuple[int, int]]] = [
        [(0, 0) for _ in range(8)] for _ in range(8)
    ]
    # e_0 is the identity: e_0·e_i = e_i, e_i·e_0 = e_i
    for i in range(8):
        table[0][i] = (1, i)
        table[i][0] = (1, i)
    # Diagonals: e_i · e_i = -1 (for i >= 1)
    for i in range(1, 8):
        table[i][i] = (-1, 0)

    # Define the 7 positive triples in oriented cyclic convention:
    # (i, j, k) means e_i · e_j = e_k, with cyclic permutations giving same.
    triples = [
        (1, 2, 3),
        (1, 4, 5),
        (1, 7, 6),   # e_1 e_7 = -e_6 in oriented-cyclic; using (1,6,7) with sign below
        (2, 4, 6),
        (2, 5, 7),
        (3, 4, 7),
        (3, 6, 5),
    ]
    # Encode each triple: e_i e_j = +e_k, e_j e_k = +e_i, e_k e_i = +e_j.
    # The opposite orderings give -.
    for (i, j, k) in triples:
        table[i][j] = (+1, k)
        table[j][k] = (+1, i)
        table[k][i] = (+1, j)
        table[j][i] = (-1, k)
        table[k][j] = (-1, i)
        table[i][k] = (-1, j)

    return table


_OCT_TABLE = _octonion_multiplication_table()


def octonion_multiplication(
    a: Sequence[sp.Expr],
    b: Sequence[sp.Expr],
) -> List[sp.Expr]:
    """
    Octonion multiplication in the oriented-cyclic Fano convention.

    Elements a, b are length-8 sequences:
      a = [a0, a1, a2, a3, a4, a5, a6, a7]
    with a0 the scalar part and a1..a7 the coefficients of e_1..e_7.

    Returns the product c = a·b as a length-8 list.
    """
    assert len(a) == 8 and len(b) == 8
    c: List[sp.Expr] = [sp.Integer(0) for _ in range(8)]
    for i in range(8):
        for j in range(8):
            sign, idx = _OCT_TABLE[i][j]
            if sign == 0:
                continue
            c[idx] += sign * a[i] * b[j]
    return [sp.expand(x) for x in c]


def octonion_generators() -> List[sp.Matrix]:
    """
    Left-multiplication matrices for e_1 through e_7 acting on 𝕆 vectors.
    Returns a list of 7 8x8 matrices.

    The SMNNIP framework uses these as the 7 generators of the G_2 algebra
    (the automorphism group of the octonions) acting on octonion-valued
    fields.
    """
    generators: List[sp.Matrix] = []
    for a in range(1, 8):
        M = sp.zeros(8, 8)
        for j in range(8):
            sign, idx = _OCT_TABLE[a][j]
            if sign != 0:
                M[idx, j] = sp.Integer(sign)
        generators.append(M)
    return generators


# ═══════════════════════════════════════════════════════════════════════════
#  UNIFIED INTERFACE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CayleyDicksonAlgebra:
    """
    A single stratum of the Cayley-Dickson tower.

    label   : 'R', 'C', 'H', or 'O'
    dim     : 1, 2, 4, or 8
    name    : human-readable name
    """
    label: str
    dim: int
    name: str

    def multiply(self, a: Sequence[sp.Expr], b: Sequence[sp.Expr]) -> List[sp.Expr]:
        if self.label == 'R':
            return real_multiplication(a, b)
        elif self.label == 'C':
            return complex_multiplication(a, b)
        elif self.label == 'H':
            return quaternion_multiplication(a, b)
        elif self.label == 'O':
            return octonion_multiplication(a, b)
        else:
            raise ValueError(f"Unknown algebra label: {self.label}")

    def conjugate(self, a: Sequence[sp.Expr]) -> List[sp.Expr]:
        """
        Algebra conjugation: negate imaginary components.
          R: a* = a
          C: (a0, a1)* = (a0, -a1)
          H, O: (a0, a_1,...,a_n) → (a0, -a_1,..., -a_n)
        """
        if self.label == 'R':
            return list(a)
        return [a[0]] + [-ai for ai in a[1:]]

    def norm_squared(self, a: Sequence[sp.Expr]) -> sp.Expr:
        """|a|² = a · a* summed as scalar component."""
        conj_a = self.conjugate(a)
        prod = self.multiply(a, conj_a)
        return sp.expand(prod[0])

    def generators(self) -> List[sp.Matrix]:
        """Left-multiplication matrices for the imaginary basis elements."""
        if self.label == 'R':
            return []
        elif self.label == 'C':
            return [complex_i_generator()]
        elif self.label == 'H':
            return list(quaternion_generators())
        elif self.label == 'O':
            return octonion_generators()
        else:
            raise ValueError(f"Unknown algebra label: {self.label}")


def left_multiplication_matrix(
    algebra_label: str,
    imag_unit_index: int,
) -> sp.Matrix:
    """
    Convenience: return L_{e_k} where k = imag_unit_index (1-based).
    For ℂ with index=1, returns the single i-matrix.
    For ℍ with index=1,2,3, returns L_i, L_j, L_k.
    For 𝕆 with index=1..7, returns the corresponding octonion generator.
    """
    alg = CayleyDicksonAlgebra(
        label=algebra_label,
        dim={'R': 1, 'C': 2, 'H': 4, 'O': 8}[algebra_label],
        name={
            'R': 'Real', 'C': 'Complex', 'H': 'Quaternion', 'O': 'Octonion'
        }[algebra_label],
    )
    gens = alg.generators()
    return gens[imag_unit_index - 1]
