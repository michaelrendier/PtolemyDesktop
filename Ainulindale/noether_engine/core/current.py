"""
noether_engine.core.current — conserved current assembly.

Given a Lagrangian, a symmetry, and the variation computed, build the
canonical Noether current:

  J^μ = Σ_fields (∂ℒ/∂(∂_μ φ)) · δφ   - K^μ   + [ξ^μ ℒ if spacetime symmetry]

On-shell, ∂_μ J^μ = 0 by construction of Noether's first theorem.

This module provides the current assembly; the consistency check
(does ∂_μ J^μ = 0 on the equations of motion?) is performed in
theorems/first_theorem.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import sympy as sp

from .field import Field
from .lagrangian import Lagrangian
from .symmetry import Symmetry


@dataclass
class Current:
    """
    A conserved current J^μ.

    Attributes:
      components : tuple of 4 sympy expressions, one per μ.
      symmetry   : the Symmetry that generated it.
      convention : 'vertical' or 'total' — which variation was used.
      K_mu       : K^μ subtracted during assembly (None if no Bessel-Hagen term).
      xi_mu_L    : coordinate-shift piece ξ^μ·ℒ (None for internal symmetries).

    Methods:
      .divergence(L) — compute ∂_μ J^μ as a sympy expression. Should be 0
                       on the E-L equations; theorems/first_theorem verifies.
      .simplify()    — simplify all components.
      .as_dict()     — dict keyed by 'J^mu' names.
    """
    components: Tuple[sp.Expr, ...]
    symmetry: Symmetry
    convention: str
    K_mu: Optional[Tuple[sp.Expr, ...]] = None
    xi_mu_L: Optional[Tuple[sp.Expr, ...]] = None

    def divergence(self, L: Lagrangian) -> sp.Expr:
        """Compute ∂_μ J^μ."""
        div = sp.Integer(0)
        for mu, Jmu in enumerate(self.components):
            div += sp.diff(Jmu, L.coords[mu])
        return sp.expand(div)

    def simplify(self) -> 'Current':
        """Return a new Current with each component simplified."""
        return Current(
            components=tuple(sp.simplify(c) for c in self.components),
            symmetry=self.symmetry,
            convention=self.convention,
            K_mu=self.K_mu,
            xi_mu_L=self.xi_mu_L,
        )

    def as_dict(self) -> Dict[str, sp.Expr]:
        return {f"J^{mu}": c for mu, c in enumerate(self.components)}

    def __repr__(self) -> str:
        return (
            f"Current(symmetry='{self.symmetry.name}', "
            f"convention='{self.convention}', "
            f"components=[{', '.join(str(c) for c in self.components)}])"
        )


def _current_contribution_from_field(
    L: Lagrangian,
    field: Field,
    delta_phi,
    mu: int,
) -> sp.Expr:
    """
    Contribution to J^μ from one field:
       (∂ℒ/∂(∂_μ φ)) · δφ
    summed over components for algebra-valued fields.
    """
    if field.field_type == 'algebra_valued':
        total = sp.Integer(0)
        for i, (comp, dcomp) in enumerate(zip(field.components, delta_phi)):
            dmu_comp = sp.diff(comp, L.coords[mu])
            dL_dDphi = sp.diff(L.density, dmu_comp)
            total += dL_dDphi * dcomp
        return total
    else:
        target = field.symbol
        dmu_target = sp.diff(target, L.coords[mu])
        dL_dDphi = sp.diff(L.density, dmu_target)
        return dL_dDphi * delta_phi


def derive_canonical_current(
    L: Lagrangian,
    S: Symmetry,
    convention: str = 'vertical',
) -> Current:
    """
    Build the canonical Noether current J^μ from a Lagrangian and symmetry.

    Formula (Bessel-Hagen form):
      J^μ = Σ_fields (∂ℒ/∂(∂_μ φ)) · δφ  -  K^μ  [+ ξ^μ ℒ if convention='total']

    The result is a Current object; its conservation ∂_μ J^μ = 0 on-shell
    must be verified separately by theorems/first_theorem.
    """
    n_coords = len(L.coords)
    components: List[sp.Expr] = []

    for mu in range(n_coords):
        Jmu = sp.Integer(0)
        for f, dphi in S.field_variations.items():
            Jmu += _current_contribution_from_field(L, f, dphi, mu)

        # Subtract K^μ (Bessel-Hagen boundary term) if supplied
        if S.K_mu is not None and mu < len(S.K_mu):
            Jmu = Jmu - S.K_mu[mu]

        # For total-variation (spacetime symmetries), add ξ^μ ℒ
        if convention == 'total' and S.coordinate_shift is not None:
            Jmu = Jmu + S.coordinate_shift[mu] * L.density

        components.append(sp.expand(Jmu))

    xi_L = None
    if convention == 'total' and S.coordinate_shift is not None:
        xi_L = tuple(xi * L.density for xi in S.coordinate_shift)

    return Current(
        components=tuple(components),
        symmetry=S,
        convention=convention,
        K_mu=S.K_mu,
        xi_mu_L=xi_L,
    )
