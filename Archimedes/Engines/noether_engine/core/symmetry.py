"""
noether_engine.core.symmetry — the transformations Noether's first theorem
acts on.

A `Symmetry` carries, per unit infinitesimal parameter ε:

    delta_x[μ]        X^μ(x)      — the coordinate shift          (spacetime)
    delta_field(comps) -> [Ψ_a]  — the TOTAL field variation      (internal + drag)
    boundary(comps, L) -> [K^μ]  — the Bessel–Hagen term, δL = ε ∂_μ K^μ

`kind` is `"spacetime"` (energy–momentum) or `"internal"` (a charge current).
The Lie-algebra generators below are the Session-1 set the tower uses:
U(1) → 1, SU(2) → 3, SU(3) → 8 (matching noether_spectrograph.py).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import sympy as sp

I = sp.I


@dataclass
class Symmetry:
    name: str
    kind: str                                   # "spacetime" | "internal"
    delta_x: List[sp.Expr]
    delta_field: Callable[[Sequence[sp.Expr]], List[sp.Expr]]
    boundary: Optional[Callable[[Sequence[sp.Expr], sp.Expr], List[sp.Expr]]] = None
    generator: Optional[sp.Matrix] = None       # the Lie-algebra element, if any

    def K(self, comps: Sequence[sp.Expr], L: sp.Expr, dim: int) -> List[sp.Expr]:
        if self.boundary is None:
            return [sp.Integer(0)] * dim
        return list(self.boundary(comps, L))


# ── spacetime translations → the canonical energy–momentum tensor ───────────
def translation(nu: int, dim: int = 4) -> Symmetry:
    """x^μ → x^μ + ε δ^μ_ν, φ_a unchanged (vertical part is the drag −ε ∂_ν φ_a)."""
    dx = [sp.Integer(1) if mu == nu else sp.Integer(0) for mu in range(dim)]
    return Symmetry(name=f"translation_{nu}", kind="spacetime",
                    delta_x=dx, delta_field=lambda comps: [sp.Integer(0)] * len(comps))


# ── internal (vertical) symmetries → charge currents ───────────────────────
def internal(generator: sp.Matrix, dim: int = 4, name: str = "internal") -> Symmetry:
    """δφ = i ε G φ  (φ the column of components), x unchanged."""
    G = sp.Matrix(generator)

    def dfield(comps: Sequence[sp.Expr]) -> List[sp.Expr]:
        col = sp.Matrix(list(comps))
        return list(I * (G * col))

    return Symmetry(name=name, kind="internal",
                    delta_x=[sp.Integer(0)] * dim, delta_field=dfield,
                    generator=G)


def u1_complex_scalar(dim: int = 4) -> Symmetry:
    """U(1) on (φ, φ̄):  δφ = i ε φ,  δφ̄ = −i ε φ̄  (number current)."""
    return internal(sp.diag(1, -1), dim=dim, name="U(1)")


# ── Lie-algebra generators (Hermitian, normalised tr(T^aT^b)=½δ^{ab}) ──────
def u1_generator() -> List[sp.Matrix]:
    return [sp.Matrix([[1]])]


def su2_generators() -> List[sp.Matrix]:
    s1 = sp.Matrix([[0, 1], [1, 0]])
    s2 = sp.Matrix([[0, -I], [I, 0]])
    s3 = sp.Matrix([[1, 0], [0, -1]])
    return [s / 2 for s in (s1, s2, s3)]


def su3_generators() -> List[sp.Matrix]:
    l1 = sp.Matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]])
    l2 = sp.Matrix([[0, -I, 0], [I, 0, 0], [0, 0, 0]])
    l3 = sp.Matrix([[1, 0, 0], [0, -1, 0], [0, 0, 0]])
    l4 = sp.Matrix([[0, 0, 1], [0, 0, 0], [1, 0, 0]])
    l5 = sp.Matrix([[0, 0, -I], [0, 0, 0], [I, 0, 0]])
    l6 = sp.Matrix([[0, 0, 0], [0, 0, 1], [0, 1, 0]])
    l7 = sp.Matrix([[0, 0, 0], [0, 0, -I], [0, I, 0]])
    l8 = sp.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, -2]]) / sp.sqrt(3)
    return [l / 2 for l in (l1, l2, l3, l4, l5, l6, l7, l8)]


GENERATORS = {
    "u1": u1_generator, "U(1)": u1_generator,
    "su2": su2_generators, "SU(2)": su2_generators,
    "su3": su3_generators, "SU(3)": su3_generators,
}
