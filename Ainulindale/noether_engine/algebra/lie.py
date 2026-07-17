"""
noether_engine.algebra.lie — standard Lie algebra generators.

Provides generators for u(1), su(2), su(3) in two normalization conventions
(Switch Axis 9):

  'physics' : Tr(T^a T^b) = (1/2) δ^{ab}   — Peskin-Schroeder, Srednicki
  'math'    : Tr(T^a T^b) = 2 δ^{ab}       — some math references

The physics convention is the default. For SU(2) this means T^a = σ^a/2 with
σ^a the Pauli matrices; for SU(3) it means T^a = λ^a/2 with λ^a the
Gell-Mann matrices.

The structure constants f^{abc} are the same in both conventions up to an
overall scale on [T^a, T^b] = i f^{abc} T^c.

Custom normalizations are supported via `algebra='custom'` + user-supplied
generator matrices, scheduled for session 2.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Tuple

import sympy as sp


class LieGeneratorConvention(Enum):
    PHYSICS = 'physics'    # Tr(T^a T^b) = (1/2) δ^{ab}
    MATH = 'math'          # Tr(T^a T^b) = 2 δ^{ab}


GENERATOR_CONVENTIONS = {
    'physics': LieGeneratorConvention.PHYSICS,
    'math': LieGeneratorConvention.MATH,
}


# ── U(1) ───────────────────────────────────────────────────────────────────

def u1_generator(convention: str = 'physics') -> sp.Matrix:
    """
    U(1) has one generator — the identity (or i times identity, depending on
    whether one factors out the i). We return the 1x1 identity matrix, the
    generator of phase rotations e^{iθ}. Convention affects normalization of
    the associated current, not the generator matrix itself.
    """
    return sp.Matrix([[1]])


# ── SU(2) ──────────────────────────────────────────────────────────────────

def _pauli_matrices() -> Tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    """The three Pauli matrices σ^1, σ^2, σ^3."""
    sigma1 = sp.Matrix([[0, 1], [1, 0]])
    sigma2 = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sigma3 = sp.Matrix([[1, 0], [0, -1]])
    return (sigma1, sigma2, sigma3)


def su2_generators(
    convention: str = 'physics',
) -> Tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    """
    SU(2) generators in the fundamental (2-dimensional) representation.

    Physics convention : T^a = σ^a / 2
    Math convention    : T^a = σ^a  (so Tr(T^a T^b) = 2 δ^{ab})
    """
    s1, s2, s3 = _pauli_matrices()
    if convention == 'physics':
        return (s1 / 2, s2 / 2, s3 / 2)
    elif convention == 'math':
        return (s1, s2, s3)
    else:
        raise ValueError(f"Unknown convention: {convention}")


def su2_structure_constants() -> List[List[List[sp.Expr]]]:
    """
    Structure constants f^{abc} for SU(2): [T^a, T^b] = i f^{abc} T^c.
    For SU(2): f^{abc} = ε^{abc} (the Levi-Civita symbol).

    Returns a 3x3x3 nested list with f[a][b][c] = ε^{abc}.
    """
    f = [[[sp.Integer(0) for _ in range(3)] for _ in range(3)] for _ in range(3)]
    # ε^{123} = +1, cyclic
    f[0][1][2] = sp.Integer(1); f[1][2][0] = sp.Integer(1); f[2][0][1] = sp.Integer(1)
    f[0][2][1] = sp.Integer(-1); f[2][1][0] = sp.Integer(-1); f[1][0][2] = sp.Integer(-1)
    return f


# ── SU(3) ──────────────────────────────────────────────────────────────────

def _gell_mann_matrices() -> List[sp.Matrix]:
    """The eight Gell-Mann matrices λ^1 through λ^8."""
    l1 = sp.Matrix([[0,1,0],[1,0,0],[0,0,0]])
    l2 = sp.Matrix([[0,-sp.I,0],[sp.I,0,0],[0,0,0]])
    l3 = sp.Matrix([[1,0,0],[0,-1,0],[0,0,0]])
    l4 = sp.Matrix([[0,0,1],[0,0,0],[1,0,0]])
    l5 = sp.Matrix([[0,0,-sp.I],[0,0,0],[sp.I,0,0]])
    l6 = sp.Matrix([[0,0,0],[0,0,1],[0,1,0]])
    l7 = sp.Matrix([[0,0,0],[0,0,-sp.I],[0,sp.I,0]])
    l8 = sp.Matrix([[1,0,0],[0,1,0],[0,0,-2]]) / sp.sqrt(3)
    return [l1, l2, l3, l4, l5, l6, l7, l8]


def su3_generators(convention: str = 'physics') -> List[sp.Matrix]:
    """
    SU(3) generators in the fundamental (3-dimensional) representation.

    Physics convention : T^a = λ^a / 2
    Math convention    : T^a = λ^a

    Returns a list of 8 matrices.
    """
    gm = _gell_mann_matrices()
    if convention == 'physics':
        return [m / 2 for m in gm]
    elif convention == 'math':
        return gm
    else:
        raise ValueError(f"Unknown convention: {convention}")


# ── Generator commutator helper ────────────────────────────────────────────

def commutator(A: sp.Matrix, B: sp.Matrix) -> sp.Matrix:
    """[A, B] = AB - BA."""
    return A * B - B * A
