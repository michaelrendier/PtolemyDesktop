"""
noether_engine.spacetime.minkowski — flat 4D Minkowski spacetime.

Provides:
  - minkowski_metric_tensor(signature) — the 4x4 metric matrix
  - MinkowskiSpacetime — spacetime handler with metric, inverse, indices

The signature switch (Axis 6) is threaded through here: 'mostly_minus' gives
η = diag(+1, -1, -1, -1), 'mostly_plus' gives η = diag(-1, +1, +1, +1).

For Noether currents on Minkowski, raising/lowering indices is handled by
the metric; the Christoffel symbols vanish so covariant derivatives reduce
to partials. Curved-spacetime machinery lives in spacetime/curved.py
(deferred to session 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import sympy as sp


def minkowski_metric_tensor(signature: str = 'mostly_minus') -> sp.Matrix:
    """
    Return the 4x4 Minkowski metric in the chosen signature.

    signature='mostly_minus'  →  η_μν = diag(+1, -1, -1, -1)  (particle physics)
    signature='mostly_plus'   →  η_μν = diag(-1, +1, +1, +1)  (relativity)
    """
    if signature == 'mostly_minus':
        return sp.Matrix([
            [1, 0, 0, 0],
            [0,-1, 0, 0],
            [0, 0,-1, 0],
            [0, 0, 0,-1],
        ])
    elif signature == 'mostly_plus':
        return sp.Matrix([
            [-1, 0, 0, 0],
            [ 0, 1, 0, 0],
            [ 0, 0, 1, 0],
            [ 0, 0, 0, 1],
        ])
    else:
        raise ValueError(f"signature='{signature}' not recognized.")


@dataclass
class MinkowskiSpacetime:
    """
    Handler for flat Minkowski spacetime.

    Attributes:
      dim        : dimension (default 4)
      signature  : 'mostly_minus' or 'mostly_plus'
      coords     : tuple of sympy coordinate symbols
      metric     : 4x4 sympy Matrix (η_μν)
      metric_inv : 4x4 sympy Matrix (η^μν = η_μν^{-1})
    """
    signature: str = 'mostly_minus'
    dim: int = 4
    coords: Tuple[sp.Symbol, ...] = ()
    metric: sp.Matrix = None  # filled in __post_init__
    metric_inv: sp.Matrix = None

    def __post_init__(self):
        if not self.coords:
            object.__setattr__(
                self, 'coords',
                tuple(sp.symbols('t x y z', real=True))
            )
        object.__setattr__(self, 'metric',
                           minkowski_metric_tensor(self.signature))
        object.__setattr__(self, 'metric_inv', self.metric.inv())

    def lower_index(self, vector: Sequence[sp.Expr]) -> Tuple[sp.Expr, ...]:
        """V_μ = η_μν V^ν — lower an upper index."""
        V_up = sp.Matrix(vector)
        V_down = self.metric * V_up
        return tuple(V_down)

    def raise_index(self, covector: Sequence[sp.Expr]) -> Tuple[sp.Expr, ...]:
        """V^μ = η^μν V_ν — raise a lower index."""
        V_down = sp.Matrix(covector)
        V_up = self.metric_inv * V_down
        return tuple(V_up)

    def contract(
        self,
        A: Sequence[sp.Expr],
        B: Sequence[sp.Expr],
    ) -> sp.Expr:
        """A_μ B^μ = η_μν A^ν B^μ."""
        total = sp.Integer(0)
        for mu in range(self.dim):
            for nu in range(self.dim):
                total += self.metric[mu, nu] * A[mu] * B[nu]
        return sp.expand(total)

    def volume_element(self) -> sp.Expr:
        """The volume element √|g| d^4x — in Minkowski, |det η| = 1."""
        return sp.Abs(self.metric.det()) ** sp.Rational(1, 2)
