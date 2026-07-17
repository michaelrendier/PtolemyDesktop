"""
noether_engine.core.lagrangian — the Lagrangian object.

A Lagrangian wraps:
  - a sympy expression for the Lagrangian density ℒ(φ, ∂φ, x)
  - the list of fields appearing in it
  - the spacetime coordinates
  - an optional metric (defaults to Minkowski with user-chosen signature)

It provides methods for:
  - computing ∂ℒ/∂φ (used by Euler-Lagrange and Noether)
  - computing ∂ℒ/∂(∂_μ φ) (used by Noether current assembly)
  - the Euler-Lagrange equation for each field
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import sympy as sp

from .field import Field


def minkowski_metric(signature: str = 'mostly_minus') -> sp.Matrix:
    """Return the 4x4 Minkowski metric in the chosen signature."""
    if signature == 'mostly_minus':
        return sp.Matrix([
            [ 1, 0, 0, 0],
            [ 0,-1, 0, 0],
            [ 0, 0,-1, 0],
            [ 0, 0, 0,-1],
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


class Lagrangian:
    """
    A Lagrangian density with its fields and coordinates.

    Parameters:
      density   : sympy expression for ℒ
      fields    : list of Field objects appearing in density
      coords    : tuple of sympy coordinate symbols
      metric    : sympy Matrix (4x4) metric, or None for Minkowski default
      signature : metric signature if using default Minkowski

    Methods:
      - dL_dphi(field)            : ∂ℒ/∂φ
      - dL_ddphi(field, mu)        : ∂ℒ/∂(∂_μ φ)
      - euler_lagrange(field)      : ∂ℒ/∂φ - ∂_μ(∂ℒ/∂(∂_μ φ))
      - all_euler_lagrange()       : list of E-L equations for all fields
    """

    def __init__(
        self,
        density: sp.Expr,
        fields: Sequence[Field],
        coords: Optional[Sequence[sp.Symbol]] = None,
        metric: Optional[sp.Matrix] = None,
        signature: str = 'mostly_minus',
    ):
        self.density = sp.sympify(density)
        self.fields = list(fields)
        if coords is None and fields:
            coords = fields[0].coords
        self.coords = tuple(coords) if coords is not None else ()
        self.signature = signature
        if metric is None:
            self.metric = minkowski_metric(signature)
        else:
            self.metric = metric

    # ── Field / derivative manipulation helpers ────────────────────────────

    def _field_symbol(self, field: Field) -> sp.Expr:
        """Return the sympy symbol for the field (or its first component)."""
        if field.field_type == 'algebra_valued':
            return field.components[0]
        return field.symbol

    def dL_dphi(self, field: Field, component_index: int = 0) -> sp.Expr:
        """
        ∂ℒ/∂φ — partial derivative of the Lagrangian with respect to the
        field (treating derivatives of the field as independent variables).
        """
        if field.field_type == 'algebra_valued':
            target = field.components[component_index]
        else:
            target = field.symbol
        return sp.diff(self.density, target)

    def dL_ddphi(self, field: Field, mu: int, component_index: int = 0) -> sp.Expr:
        """
        ∂ℒ/∂(∂_μ φ) — partial derivative of the Lagrangian with respect to
        the μ-th spacetime derivative of the field.
        """
        if field.field_type == 'algebra_valued':
            target = field.components[component_index]
        else:
            target = field.symbol
        dphi = sp.diff(target, self.coords[mu])
        return sp.diff(self.density, dphi)

    def euler_lagrange(self, field: Field, component_index: int = 0) -> sp.Expr:
        """
        Euler-Lagrange equation for this field:
          ∂ℒ/∂φ - ∂_μ (∂ℒ/∂(∂_μ φ)) = 0
        Returns the LHS as a sympy expression; = 0 on-shell.
        """
        eom = self.dL_dphi(field, component_index)
        n_coords = len(self.coords)
        for mu in range(n_coords):
            term = self.dL_ddphi(field, mu, component_index)
            eom = eom - sp.diff(term, self.coords[mu])
        return sp.simplify(eom)

    def all_euler_lagrange(self) -> Dict[str, sp.Expr]:
        """Return a dict mapping field name to its E-L equation."""
        out = {}
        for f in self.fields:
            if f.field_type == 'algebra_valued':
                for i in range(f.dim):
                    out[f"{f.name}_{i}"] = self.euler_lagrange(f, component_index=i)
            else:
                out[f.name] = self.euler_lagrange(f)
        return out

    def __repr__(self) -> str:
        return (
            f"Lagrangian(density={self.density}, "
            f"fields={[f.name for f in self.fields]}, "
            f"signature='{self.signature}')"
        )
