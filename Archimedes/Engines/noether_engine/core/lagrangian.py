"""
noether_engine.core.lagrangian — a first-order Lagrangian density and its
Euler–Lagrange operator.

`L(φ_a, ∂_μ φ_a)` is a plain sympy expression in a `Field`'s components and
their first derivatives.  `euler_lagrange(a)` returns

    ∂L/∂φ_a  −  ∂_μ ( ∂L/∂(∂_μ φ_a) )

as a sympy expression; `eom()` is the tuple over all components.  The partials
are taken by the standard dummy-substitution trick so that ∂L/∂φ_a holds the
derivatives fixed and ∂L/∂(∂_μ φ_a) holds φ_a fixed.
"""
from __future__ import annotations

from typing import List, Tuple

import sympy as sp

from .field import Field


def _partials(L: sp.Expr, comp: sp.Expr,
              coords: Tuple[sp.Symbol, ...]) -> Tuple[sp.Expr, List[sp.Expr]]:
    """(∂L/∂comp, [∂L/∂(∂_μ comp) for μ]) — derivatives held fixed for the
    first, the field held fixed for the rest."""
    dim = len(coords)
    d_syms = [sp.Dummy(f"d{i}") for i in range(dim)]
    fwd = {sp.Derivative(comp, coords[i]): d_syms[i] for i in range(dim)}
    L_d = L.subs(fwd, simultaneous=True)          # first-derivs -> dummies

    c_sym = sp.Dummy("c")
    L_dc = L_d.subs(comp, c_sym)                  # field -> dummy too

    dL_dcomp = sp.diff(L_dc, c_sym)
    dL_dd = [sp.diff(L_d, d_syms[i]) for i in range(dim)]

    back = {v: k for k, v in fwd.items()}
    back[c_sym] = comp
    dL_dcomp = dL_dcomp.subs(c_sym, comp).subs(back, simultaneous=True)
    dL_dd = [e.subs(back, simultaneous=True) for e in dL_dd]
    return dL_dcomp, dL_dd


class Lagrangian:
    def __init__(self, expr: sp.Expr, field: Field, name: str = "L") -> None:
        self.expr = sp.sympify(expr)
        self.field = field
        self.name = name
        self._pcache: dict = {}

    # ── partials ─────────────────────────────────────────────────────────
    def partials(self, a: int) -> Tuple[sp.Expr, List[sp.Expr]]:
        if a not in self._pcache:
            self._pcache[a] = _partials(self.expr, self.field.components[a],
                                        self.field.coords)
        return self._pcache[a]

    def conjugate_momentum(self, a: int, mu: int) -> sp.Expr:
        """π^μ_a = ∂L/∂(∂_μ φ_a)."""
        return self.partials(a)[1][mu]

    # ── Euler–Lagrange ───────────────────────────────────────────────────
    def euler_lagrange(self, a: int) -> sp.Expr:
        dL_dcomp, dL_dd = self.partials(a)
        coords = self.field.coords
        div = sum(sp.Derivative(dL_dd[mu], coords[mu]).doit()
                  for mu in range(len(coords)))
        return sp.simplify(dL_dcomp - div)

    def eom(self) -> List[sp.Expr]:
        """One Euler–Lagrange expression per component; `= 0` on-shell."""
        return [self.euler_lagrange(a)
                for a in range(self.field.n_components)]


# ── ready-made densities (Session-1 working set) ────────────────────────────
def klein_gordon_real(field: Field, m: sp.Symbol) -> Lagrangian:
    """L = ½ η^{μν} ∂_μ φ ∂_ν φ − ½ m² φ²  (mostly-minus: ½φ̇² − ½(∇φ)² − ½m²φ²)."""
    phi = field.components[0]
    eta = field.eta
    kin = sum(eta[mu] * sp.Derivative(phi, field.coords[mu])**2
              for mu in range(field.dim)) / 2
    return Lagrangian(kin - m**2 * phi**2 / 2, field, "L_KG")


def klein_gordon_complex(field: Field, m: sp.Symbol) -> Lagrangian:
    """L = η^{μν} ∂_μ φ ∂_ν φ̄ − m² φ φ̄."""
    phi, bar = field.components
    eta = field.eta
    kin = sum(eta[mu] * sp.Derivative(phi, field.coords[mu])
              * sp.Derivative(bar, field.coords[mu])
              for mu in range(field.dim))
    return Lagrangian(kin - m**2 * phi * bar, field, "L_cKG")
