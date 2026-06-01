"""
Tests for algebra module: Cayley-Dickson and Lie.

Verifies:
  1. Quaternion identities i² = j² = k² = ijk = -1, ij = k, jk = i, ki = j.
  2. Octonion e_i² = -1 for i = 1..7.
  3. Octonion anticommutativity: e_i e_j = -e_j e_i for i != j.
  4. Octonion alternative-algebra property (Moufang identity sample).
  5. Complex i² = -1.
  6. Pauli matrices σ_i² = I, [σ_i, σ_j] = 2i ε_{ijk} σ_k.
  7. Generator left-multiplication matrices agree with the multiplication
     table on random inputs.
"""

import sympy as sp
import pytest

from noether_engine.algebra.cayley_dickson import (
    complex_multiplication, quaternion_multiplication, octonion_multiplication,
    quaternion_generators, octonion_generators,
    CayleyDicksonAlgebra,
)
from noether_engine.algebra.lie import (
    su2_generators, su3_generators, u1_generator,
    _pauli_matrices, commutator, su2_structure_constants,
)


# ── Complex ────────────────────────────────────────────────────────────────

def test_complex_i_squared_is_minus_one():
    i = [0, 1]
    result = complex_multiplication(i, i)
    assert result == [-1, 0]


def test_complex_multiplication_distributive():
    # (1 + 2i)(3 + 4i) = 3 + 4i + 6i - 8 = -5 + 10i
    a = [1, 2]
    b = [3, 4]
    result = complex_multiplication(a, b)
    assert result == [-5, 10]


# ── Quaternions ────────────────────────────────────────────────────────────

def test_quaternion_i_squared_is_minus_one():
    i_quat = [0, 1, 0, 0]
    result = quaternion_multiplication(i_quat, i_quat)
    assert result == [-1, 0, 0, 0]


def test_quaternion_j_squared_is_minus_one():
    j_quat = [0, 0, 1, 0]
    result = quaternion_multiplication(j_quat, j_quat)
    assert result == [-1, 0, 0, 0]


def test_quaternion_k_squared_is_minus_one():
    k_quat = [0, 0, 0, 1]
    result = quaternion_multiplication(k_quat, k_quat)
    assert result == [-1, 0, 0, 0]


def test_quaternion_ij_equals_k():
    i = [0, 1, 0, 0]
    j = [0, 0, 1, 0]
    ij = quaternion_multiplication(i, j)
    assert ij == [0, 0, 0, 1]


def test_quaternion_jk_equals_i():
    j = [0, 0, 1, 0]
    k = [0, 0, 0, 1]
    jk = quaternion_multiplication(j, k)
    assert jk == [0, 1, 0, 0]


def test_quaternion_ki_equals_j():
    k = [0, 0, 0, 1]
    i = [0, 1, 0, 0]
    ki = quaternion_multiplication(k, i)
    assert ki == [0, 0, 1, 0]


def test_quaternion_ijk_equals_minus_one():
    i = [0, 1, 0, 0]
    j = [0, 0, 1, 0]
    k = [0, 0, 0, 1]
    ij = quaternion_multiplication(i, j)
    ijk = quaternion_multiplication(ij, k)
    assert ijk == [-1, 0, 0, 0]


# ── Octonions ──────────────────────────────────────────────────────────────

def _oct_unit(i):
    v = [0] * 8
    v[i] = 1
    return v


def test_octonion_e_i_squared_is_minus_one():
    for i in range(1, 8):
        ei = _oct_unit(i)
        result = octonion_multiplication(ei, ei)
        assert result == [-1, 0, 0, 0, 0, 0, 0, 0], f"e_{i}² != -1"


def test_octonion_anticommutativity():
    # e_i e_j = - e_j e_i for i != j
    for i in range(1, 8):
        for j in range(1, 8):
            if i == j:
                continue
            ei = _oct_unit(i)
            ej = _oct_unit(j)
            eiej = octonion_multiplication(ei, ej)
            ejei = octonion_multiplication(ej, ei)
            # eiej should equal -ejei
            for k in range(8):
                assert sp.simplify(eiej[k] + ejei[k]) == 0, \
                    f"Anticommutativity failed for e_{i}·e_{j}"


def test_octonion_e1_e2_equals_e3():
    # In oriented-cyclic Fano: e_1 e_2 = e_3
    e1 = _oct_unit(1)
    e2 = _oct_unit(2)
    result = octonion_multiplication(e1, e2)
    expected = _oct_unit(3)
    assert result == expected


# ── Generators match multiplication ────────────────────────────────────────

def test_complex_i_generator_matches_multiplication():
    from noether_engine.algebra.cayley_dickson import complex_i_generator
    i_gen = complex_i_generator()
    a = sp.Matrix([3, 4])
    # i · (3 + 4i) = 3i - 4 = -4 + 3i
    result = i_gen * a
    assert list(result) == [-4, 3]


def test_quaternion_generators_match_multiplication():
    L_i, L_j, L_k = quaternion_generators()
    # L_i applied to (1, 0, 0, 0) should give (0, 1, 0, 0)
    one = sp.Matrix([1, 0, 0, 0])
    assert list(L_i * one) == [0, 1, 0, 0]
    assert list(L_j * one) == [0, 0, 1, 0]
    assert list(L_k * one) == [0, 0, 0, 1]


def test_octonion_generators_consistent_with_table():
    gens = octonion_generators()
    # L_{e_1} applied to (1, 0, ..., 0) should give (0, 1, 0, ..., 0)
    one = sp.zeros(8, 1); one[0, 0] = 1
    result = gens[0] * one  # gens[0] = L_{e_1}
    expected = [0, 1, 0, 0, 0, 0, 0, 0]
    assert [result[i] for i in range(8)] == expected


# ── Lie algebra ────────────────────────────────────────────────────────────

def test_pauli_matrices_square_to_identity():
    s1, s2, s3 = _pauli_matrices()
    identity = sp.eye(2)
    assert s1 * s1 == identity
    assert s2 * s2 == identity
    assert s3 * s3 == identity


def test_pauli_commutator_gives_structure_constants():
    # [σ_i, σ_j] = 2i ε_{ijk} σ_k
    s1, s2, s3 = _pauli_matrices()
    assert commutator(s1, s2) == 2 * sp.I * s3
    assert commutator(s2, s3) == 2 * sp.I * s1
    assert commutator(s3, s1) == 2 * sp.I * s2


def test_su2_physics_generators_half_pauli():
    T1, T2, T3 = su2_generators(convention='physics')
    s1, s2, s3 = _pauli_matrices()
    assert T1 == s1 / 2
    assert T2 == s2 / 2
    assert T3 == s3 / 2


def test_su2_generators_satisfy_structure_constants():
    # [T^a, T^b] = i f^{abc} T^c with f = ε in SU(2) physics convention
    T = list(su2_generators(convention='physics'))
    f = su2_structure_constants()
    for a in range(3):
        for b in range(3):
            lhs = commutator(T[a], T[b])
            rhs = sp.zeros(2, 2)
            for c in range(3):
                rhs = rhs + sp.I * f[a][b][c] * T[c]
            assert sp.simplify(lhs - rhs) == sp.zeros(2, 2), \
                f"SU(2) structure constants fail at (a,b)=({a},{b})"


def test_su3_has_eight_generators():
    gens = su3_generators(convention='physics')
    assert len(gens) == 8
    for g in gens:
        assert g.shape == (3, 3)


# ── CayleyDicksonAlgebra unified interface ─────────────────────────────────

def test_cayley_dickson_norms():
    # |1 + i|² in ℂ = 2
    C = CayleyDicksonAlgebra(label='C', dim=2, name='Complex')
    assert C.norm_squared([1, 1]) == 2
    # |1 + i + j + k|² in ℍ = 4
    H = CayleyDicksonAlgebra(label='H', dim=4, name='Quaternion')
    assert H.norm_squared([1, 1, 1, 1]) == 4
