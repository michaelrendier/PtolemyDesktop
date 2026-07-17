"""
noether_engine.improvement.custom — user-supplied improvement term.

Any conserved current J^μ can be improved by adding a divergence-free
correction:

    J^μ → J^μ + ∂_ν Θ^{νμ}   with   Θ^{νμ} = -Θ^{μν}   (antisymmetric)

The antisymmetry ensures ∂_μ ∂_ν Θ^{νμ} = 0 automatically, so conservation
is preserved. The improvement does not change the physics of the conserved
charge (the boundary flux is unchanged) but can change the current's
point-by-point tensor properties (e.g., symmetrize a stress-energy tensor).

This module provides the user-supplied path. Named improvements
(Belinfante-Rosenfeld, Callan-Coleman-Jackiw) are session 2.
"""

from __future__ import annotations

from typing import Sequence, Tuple

import sympy as sp

from ..core.current import Current
from ..core.lagrangian import Lagrangian


def apply_custom_improvement(
    current: Current,
    theta: Sequence[Sequence[sp.Expr]],
    L: Lagrangian,
) -> Current:
    """
    Improve the current J^μ by adding ∂_ν Θ^{νμ}.

    Parameters:
      current : the original Current
      theta   : user-supplied 4×4 antisymmetric tensor Θ^{νμ}
      L       : the Lagrangian (provides coordinate list)

    Returns: a new Current with improved components.

    Raises: ValueError if theta is not antisymmetric.
    """
    n = len(L.coords)
    theta_mat = sp.Matrix(theta)
    if theta_mat.shape != (n, n):
        raise ValueError(
            f"Theta must be {n}x{n}, got {theta_mat.shape}."
        )
    # Antisymmetry check
    for mu in range(n):
        for nu in range(n):
            if sp.simplify(theta_mat[mu, nu] + theta_mat[nu, mu]) != 0:
                raise ValueError(
                    f"Theta^{{{mu}{nu}}} + Theta^{{{nu}{mu}}} != 0; "
                    "improvement term must be antisymmetric."
                )

    improved_components = []
    for mu in range(n):
        Jmu_improved = current.components[mu]
        for nu in range(n):
            Jmu_improved = Jmu_improved + sp.diff(theta_mat[nu, mu], L.coords[nu])
        improved_components.append(sp.expand(Jmu_improved))

    return Current(
        components=tuple(improved_components),
        symmetry=current.symmetry,
        convention=current.convention,
        K_mu=current.K_mu,
        xi_mu_L=current.xi_mu_L,
    )
