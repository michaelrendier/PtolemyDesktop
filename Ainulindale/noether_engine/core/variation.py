"""
noether_engine.core.variation — apply a symmetry to a Lagrangian.

Two variation conventions (Switch Axis 5):
  - vertical  : δφ = φ'(x) − φ(x),   same coordinate x, field changes
  - total     : δ̂φ = φ'(x') − φ(x),  follows the flow including ξ^μ ∂_μ φ

For a symmetry δφ (vertical part) and ξ^μ (coordinate shift):
  vertical variation of ℒ: δℒ_vert = ∂ℒ/∂φ · δφ + ∂ℒ/∂(∂_μ φ) · ∂_μ(δφ)
  total variation of ℒ:     δ̂ℒ = δℒ_vert + ξ^μ ∂_μ ℒ

Noether's theorem uses the variation machinery to:
  1. Verify that δℒ is a total divergence (quasi-invariance)
  2. Extract the conserved current J^μ = ∂ℒ/∂(∂_μ φ) · δφ − K^μ (+ ξ^μ ℒ for spacetime)

This module provides the variation functions; theorems/ uses them to build currents.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import sympy as sp

from .field import Field
from .lagrangian import Lagrangian
from .symmetry import Symmetry


class Variation:
    """
    A computed variation δℒ of a Lagrangian under a symmetry.

    Attributes:
      convention   : 'vertical' or 'total'
      delta_L      : sympy expression for δℒ
      K_mu         : if a K^μ was supplied in the symmetry (Bessel-Hagen),
                     this is the boundary term. Otherwise None.
      is_symmetry  : bool — True iff δℒ reduces to ∂_μ K^μ on inspection.
    """

    def __init__(
        self,
        convention: str,
        delta_L: sp.Expr,
        K_mu: Optional[Tuple[sp.Expr, ...]] = None,
        is_symmetry: bool = False,
    ):
        self.convention = convention
        self.delta_L = delta_L
        self.K_mu = K_mu
        self.is_symmetry = is_symmetry


def _apply_vertical_to_field(
    expr: sp.Expr,
    field: Field,
    delta_phi,
    coords: Tuple[sp.Symbol, ...],
) -> sp.Expr:
    """
    Apply the vertical variation δφ to an expression by computing:
        (∂expr/∂φ) · δφ + Σ_μ (∂expr/∂(∂_μφ)) · ∂_μ(δφ)

    This is the "full" vertical variation including derivative terms.
    """
    if field.field_type == 'algebra_valued':
        result = sp.Integer(0)
        for i, (comp, dcomp) in enumerate(zip(field.components, delta_phi)):
            # ∂expr/∂φ_i · δφ_i
            term = sp.diff(expr, comp) * dcomp
            # Σ_μ ∂expr/∂(∂_μ φ_i) · ∂_μ δφ_i
            for mu in range(len(coords)):
                dmu_comp = sp.diff(comp, coords[mu])
                term += sp.diff(expr, dmu_comp) * sp.diff(dcomp, coords[mu])
            result += term
        return result
    else:
        target = field.symbol
        result = sp.diff(expr, target) * delta_phi
        for mu in range(len(coords)):
            dmu_target = sp.diff(target, coords[mu])
            result += sp.diff(expr, dmu_target) * sp.diff(delta_phi, coords[mu])
        return result


def vertical_variation(L: Lagrangian, S: Symmetry) -> Variation:
    """
    Compute the vertical variation δℒ under symmetry S.

    δℒ_vert = Σ_fields [ ∂ℒ/∂φ · δφ + ∂ℒ/∂(∂_μφ) · ∂_μ(δφ) ]
    """
    delta_L = sp.Integer(0)
    for f, dphi in S.field_variations.items():
        delta_L = delta_L + _apply_vertical_to_field(L.density, f, dphi, L.coords)

    delta_L = sp.expand(delta_L)

    # If symmetry carries a K^μ (Bessel-Hagen), check that δℒ == ∂_μ K^μ
    is_symmetry = False
    if S.K_mu is not None:
        divK = sp.Integer(0)
        for mu, Kmu in enumerate(S.K_mu):
            divK = divK + sp.diff(Kmu, L.coords[mu])
        diff = sp.simplify(delta_L - divK)
        is_symmetry = (diff == 0)

    return Variation(
        convention='vertical',
        delta_L=delta_L,
        K_mu=S.K_mu,
        is_symmetry=is_symmetry,
    )


def total_variation(L: Lagrangian, S: Symmetry) -> Variation:
    """
    Compute the total variation δ̂ℒ under symmetry S.

    δ̂ℒ = δℒ_vert + ξ^μ ∂_μ ℒ
    """
    vv = vertical_variation(L, S)
    delta_L = vv.delta_L

    if S.coordinate_shift is not None:
        for mu, xi_mu in enumerate(S.coordinate_shift):
            delta_L = delta_L + xi_mu * sp.diff(L.density, L.coords[mu])

    delta_L = sp.expand(delta_L)

    # For total variation, the expected K^μ structure is different
    # (includes ξ^μ ℒ). We don't auto-check here; theorems/ does that.
    return Variation(
        convention='total',
        delta_L=delta_L,
        K_mu=S.K_mu,
        is_symmetry=False,  # theorems/first_theorem handles the check
    )
