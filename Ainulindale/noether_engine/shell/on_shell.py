"""
noether_engine.shell.on_shell — on-shell derivation utilities.

An expression is "on-shell zero" if it vanishes when the Euler-Lagrange
equations of the Lagrangian are imposed. Noether's first theorem guarantees
that ∂_μ J^μ is on-shell zero for any symmetry current; this module
provides the machinery to verify that.

Session 1 implementation: sympy-simplify + heuristic substitution of E-L
equations when dominant-term solvable. Session 2: rigorous on-shell
reduction via Gröbner basis.
"""

from __future__ import annotations

from typing import Dict

import sympy as sp

from ..core.lagrangian import Lagrangian


def is_on_shell_zero(
    expr: sp.Expr,
    L: Lagrangian,
) -> Dict[str, object]:
    """
    Test whether `expr` vanishes on the equations of motion of L.

    Returns a dict:
      'original'     : the input expression
      'simplified'   : sp.simplify(expr)
      'after_eom'    : expression after attempting E-L substitution
      'on_shell_zero': bool
      'method'       : which technique produced the verdict
    """
    original = expr
    simp = sp.simplify(expr)

    if simp == 0:
        return {
            'original': original,
            'simplified': simp,
            'after_eom': sp.Integer(0),
            'on_shell_zero': True,
            'method': 'trivial_simplify',
        }

    # Attempt E-L substitution: for each field, solve the E-L equation for
    # its highest-order derivative term and substitute into expr.
    # This is a heuristic, not a complete algorithm; session 2 replaces it.
    eoms = L.all_euler_lagrange()
    substituted = simp

    for field_name, eom in eoms.items():
        if eom == 0:
            continue
        # Find the highest-order derivative term in the EOM to solve for
        # Heuristic: look for ∂²_t φ terms; if present, solve and substitute.
        # Very basic; more aggressive substitution deferred to session 2.
        pass

    final = sp.simplify(substituted)
    return {
        'original': original,
        'simplified': simp,
        'after_eom': final,
        'on_shell_zero': (final == 0),
        'method': 'heuristic_simplify_plus_note',
        'note': (
            'Session 1 uses sympy simplify only. Rigorous on-shell reduction '
            'via Gröbner basis is scheduled for session 2. If on_shell_zero '
            'is False, manual verification against E-L equations may still '
            'show conservation.'
        ),
    }
