"""
noether_engine.theorems.bessel_hagen — Bessel-Hagen quasi-invariance.

Bessel-Hagen (1921) generalized Noether's first theorem to transformations
under which the Lagrangian is invariant only up to a total divergence:

  δℒ = ∂_μ K^μ

rather than requiring δℒ = 0 exactly. The conserved current is then

  J^μ = (∂ℒ/∂(∂_μφ)) · δφ − K^μ  [+ ξ^μ ℒ for spacetime]

This module:
  - checks whether a supplied K^μ satisfies δℒ = ∂_μ K^μ
  - (session 2) attempts to find K^μ symbolically given a quasi-invariant δℒ

The user typically supplies K^μ along with the symmetry when constructing a
Symmetry object. For standard spacetime translations the K^μ happens to be
zero (δℒ vanishes exactly under δφ = -∂_μ φ for translation-invariant ℒ).
For Galilean boosts and conformal transformations, K^μ is nonzero and the
Bessel-Hagen formalism is required.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import sympy as sp

from ..core.lagrangian import Lagrangian
from ..core.variation import Variation


def check_quasi_invariance(
    v: Variation,
    L: Lagrangian,
    expected_K: Optional[Tuple[sp.Expr, ...]] = None,
) -> Dict[str, Any]:
    """
    Verify that the variation δℒ equals ∂_μ K^μ for the supplied K^μ.

    If expected_K is None, treat as strict invariance (K^μ = 0 required).

    Returns a dict:
      'delta_L_simplified' : simplified δℒ
      'divK_simplified'    : simplified ∂_μ K^μ
      'residual'           : δℒ - ∂_μ K^μ, simplified
      'is_symmetry'        : bool — True iff residual simplifies to 0
    """
    delta_L_simp = sp.simplify(v.delta_L)

    if expected_K is None:
        divK = sp.Integer(0)
        divK_simp = sp.Integer(0)
    else:
        divK = sp.Integer(0)
        for mu, Kmu in enumerate(expected_K):
            divK = divK + sp.diff(Kmu, L.coords[mu])
        divK_simp = sp.simplify(divK)

    residual = sp.simplify(delta_L_simp - divK_simp)
    is_symmetry = (residual == 0)

    return {
        'delta_L_simplified': delta_L_simp,
        'divK_simplified': divK_simp,
        'residual': residual,
        'is_symmetry': is_symmetry,
    }


def find_K_mu_symbolically(
    v: Variation,
    L: Lagrangian,
) -> Optional[Tuple[sp.Expr, ...]]:
    """
    Attempt to find K^μ such that δℒ = ∂_μ K^μ.

    Session 1 implementation: return None (not yet implemented).
    Session 2: implement via Hodge decomposition / de Rham on the jet bundle.

    A general-purpose K^μ finder is a hard symbolic problem; several packages
    exist (FieldsX, Olver's Maple implementation). For session 1 we expect
    the user to supply K^μ along with the symmetry.
    """
    return None
