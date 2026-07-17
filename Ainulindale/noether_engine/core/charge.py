"""
noether_engine.core.charge — charge and form conversions from a current.

The conserved current J^μ can be re-expressed as:
  - the charge Q = ∫ J^0 d^3x   (with dQ/dt = 0)
  - the (d-1)-form ⋆J            (with d(⋆J) = 0)

Both are equivalent to J^μ with ∂_μ J^μ = 0; the choice of presentation
is a matter of which downstream formalism (Lagrangian field theory,
Hamiltonian mechanics, de Rham cohomology) the user works in.

Session 1 provides symbolic versions. Session 2 will add numerical
evaluation of the integral on user-supplied field configurations.
"""

from __future__ import annotations

from typing import Optional, Tuple

import sympy as sp

from .current import Current
from .lagrangian import Lagrangian


def charge_from_current(
    current: Current,
    L: Lagrangian,
    time_coord_index: int = 0,
    spatial_volume_symbol: str = 'V',
) -> sp.Expr:
    """
    Return the charge expression:
      Q(t) = ∫ J^0 d^{d-1}x

    Session 1 returns a symbolic ∫ expression over the spatial coordinates
    (excluding the time coordinate at index `time_coord_index`). The user
    is responsible for evaluating the integral on a specific field
    configuration if they want a number.

    The integral is returned as sp.Integral for user inspection.
    """
    J0 = current.components[time_coord_index]

    spatial_coords = tuple(
        c for i, c in enumerate(L.coords) if i != time_coord_index
    )

    # Build sp.Integral symbolically
    integrand = J0
    result: sp.Expr = integrand
    for c in spatial_coords:
        result = sp.Integral(result, (c, -sp.oo, sp.oo))

    return result


def form_from_current(
    current: Current,
    L: Lagrangian,
) -> sp.Expr:
    """
    Return the Hodge-dual (d-1)-form ⋆J symbolically.

    In 4D with metric signature determined by L.signature, the Hodge dual of
    a 1-form J = J_μ dx^μ is a 3-form:

      ⋆J = (1/3!) ε_{μ α β γ} J^μ dx^α ∧ dx^β ∧ dx^γ

    Session 1 returns a symbolic placeholder marked with the signature and
    the four J^μ components. A full exterior-algebra computation is
    delegated to session 2 when `sympy.diffgeom` usage is formalized.
    """
    # Symbolic marker; real exterior-algebra structure deferred to session 2.
    return sp.Function('HodgeDual')(
        *current.components,
        sp.Symbol(f"signature_{L.signature}"),
    )
