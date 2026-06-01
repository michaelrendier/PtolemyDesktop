"""
noether_engine.theorems.first_theorem — Noether's first theorem.

First theorem statement (Noether 1918):
  If a Lagrangian ℒ(φ, ∂φ, x) is invariant (or quasi-invariant up to a total
  divergence) under a continuous global transformation parameterized by
  constant ε, then there exists a current

     J^μ = (∂ℒ/∂(∂_μφ)) · δφ  -  K^μ  [+ ξ^μ ℒ for spacetime]

  which is conserved on-shell: ∂_μ J^μ = 0 when the Euler-Lagrange equations
  are satisfied.

This module is the top-level driver. It:
  1. Computes the variation δℒ under the symmetry
  2. Verifies that δℒ is a total divergence (quasi-invariance)
  3. Assembles the canonical current J^μ
  4. Verifies ∂_μ J^μ = 0 on the E-L equations
  5. Returns the current with full verification metadata

Both vertical and total variations are supported (switch: `variation`).
Strict / divergence / Bessel-Hagen invariance all funnel into the same
final-current formula (Bessel-Hagen is the general case; strict/divergence
are K^μ = 0 or user-supplied K^μ specializations).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import sympy as sp

from ..core.lagrangian import Lagrangian
from ..core.symmetry import Symmetry
from ..core.current import Current, derive_canonical_current
from ..core.variation import Variation, vertical_variation, total_variation
from .bessel_hagen import check_quasi_invariance


def verify_conservation(
    current: Current,
    L: Lagrangian,
    use_equations_of_motion: bool = True,
) -> Dict[str, Any]:
    """
    Check that ∂_μ J^μ = 0 on-shell.

    Returns a dict:
      'divergence_raw'      : raw ∂_μ J^μ (before applying EOM)
      'divergence_on_shell' : ∂_μ J^μ after substituting the E-L equations = 0
      'conserved'           : bool — True iff divergence_on_shell simplifies to 0

    If use_equations_of_motion is False, we only check whether the raw
    divergence simplifies to 0 directly (the off-shell case, usually
    satisfied only for divergence-free currents or quasi-invariant symmetries
    with correctly-subtracted K^μ).
    """
    div_raw = current.divergence(L)
    div_simplified = sp.simplify(div_raw)

    if not use_equations_of_motion:
        return {
            'divergence_raw': div_raw,
            'divergence_on_shell': div_simplified,
            'conserved': (div_simplified == 0),
            'method': 'off_shell_direct',
        }

    # On-shell: substitute E-L equations.
    # For each field, the E-L equation gives us ∂ℒ/∂φ − ∂_μ(∂ℒ/∂(∂_μφ)) = 0,
    # which we can use to simplify the divergence.
    # We attempt to simplify via sympy, then if residual terms remain,
    # we test that each residual is proportional to an E-L equation.
    eoms = L.all_euler_lagrange()

    # Simplest check: if sp.simplify(div_raw) == 0, conservation is automatic.
    if div_simplified == 0:
        return {
            'divergence_raw': div_raw,
            'divergence_on_shell': sp.Integer(0),
            'conserved': True,
            'method': 'trivially_zero',
            'eom_used': False,
        }

    # Otherwise, test whether div_raw vanishes modulo the E-L equations.
    # We do this by symbolic substitution: solve each EOM for a dominant term
    # and substitute. Since general symbolic EOM substitution is ambitious,
    # session 1 supports the common case where the EOM gives us
    # ∂_μ(∂ℒ/∂(∂_μφ)) = ∂ℒ/∂φ, which we can attempt to apply.
    on_shell = div_simplified
    eom_substitutions = {}
    for field_name, eom in eoms.items():
        # Split EOM into dominant term and the rest; attempt to substitute
        # ∂_μ(∂ℒ/∂(∂_μφ)) → ∂ℒ/∂φ where possible. This is a heuristic —
        # a rigorous on-shell reducer is scheduled for session 2.
        pass  # session 2: full EOM substitution via Gröbner basis

    return {
        'divergence_raw': div_raw,
        'divergence_on_shell': on_shell,
        'conserved': (on_shell == 0),
        'method': 'sympy_simplify',
        'eom_used': False,
        'note': (
            'Session 1 uses sympy simplify only. If divergence is nonzero '
            'after simplify, the current MAY still be conserved on the E-L '
            'equations — manual verification recommended. Session 2 will '
            'add rigorous on-shell reduction via Gröbner basis.'
        ),
    }


def derive_first_theorem_current(
    L: Lagrangian,
    S: Symmetry,
    variation_convention: str = 'vertical',
    invariance: str = 'bessel_hagen',
    verify: bool = True,
) -> Tuple[Current, Variation, Dict[str, Any]]:
    """
    Derive the conserved current for symmetry S of Lagrangian L using
    Noether's first theorem.

    Parameters:
      L                    : the Lagrangian
      S                    : the symmetry (with optional K^μ for Bessel-Hagen)
      variation_convention : 'vertical' or 'total'
      invariance           : 'strict', 'divergence', or 'bessel_hagen'
      verify               : whether to compute the conservation check

    Returns:
      (current, variation, verification_dict)

    Raises:
      ValueError if the specified invariance type requires K^μ but none was
      supplied on the Symmetry.
    """
    # Step 1: compute δℒ under the symmetry
    if variation_convention == 'vertical':
        v = vertical_variation(L, S)
    elif variation_convention == 'total':
        v = total_variation(L, S)
    else:
        raise ValueError(
            f"variation_convention='{variation_convention}' invalid; "
            f"must be 'vertical' or 'total'."
        )

    # Step 2: verify quasi-invariance based on the declared invariance type
    if invariance == 'strict':
        # Require δℒ = 0 identically
        simplified = sp.simplify(v.delta_L)
        if simplified != 0:
            raise ValueError(
                f"Strict invariance requested but δℒ = {simplified} ≠ 0. "
                f"Use invariance='divergence' or 'bessel_hagen' for "
                f"quasi-invariant symmetries, or check your symmetry."
            )
    elif invariance in ('divergence', 'bessel_hagen'):
        # Accept δℒ = ∂_μ K^μ with user-supplied K^μ
        qi = check_quasi_invariance(v, L, expected_K=S.K_mu)
        if not qi['is_symmetry']:
            raise ValueError(
                f"Symmetry check failed: δℒ = {qi['delta_L_simplified']} "
                f"does not match ∂_μ K^μ "
                f"(K^μ = {S.K_mu}). "
                f"Difference: {qi['residual']}. "
                f"Either the K^μ is incorrect or the transformation is "
                f"not a symmetry of this Lagrangian."
            )
    else:
        raise ValueError(
            f"invariance='{invariance}' invalid; "
            f"must be 'strict', 'divergence', or 'bessel_hagen'."
        )

    # Step 3: assemble the canonical current
    current = derive_canonical_current(L, S, convention=variation_convention)

    # Step 4: verify conservation ∂_μ J^μ = 0 (on-shell)
    verification = {}
    if verify:
        verification = verify_conservation(current, L)

    return current, v, verification
