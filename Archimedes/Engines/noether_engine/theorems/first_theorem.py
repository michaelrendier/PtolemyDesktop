"""
noether_engine.theorems.first_theorem — Noether's FIRST theorem.

A continuous symmetry of the action gives a current that is conserved on-shell.
Per unit parameter ε, with coordinate shift X^μ, total field variation Ψ_a and
Bessel–Hagen term K^μ (δL = ε ∂_μ K^μ), the vertical variation is

    δ₀φ_a = Ψ_a − X^μ ∂_μ φ_a

and the Noether current is

    j^μ = Σ_a ( ∂L/∂(∂_μ φ_a) ) δ₀φ_a  +  L X^μ  +  K^μ ,      ∂_μ j^μ ≐ 0 .

For a spacetime translation this collapses to the canonical stress tensor
T^μ_ν = Σ_a π^μ_a ∂_ν φ_a − δ^μ_ν L, and the engine returns the whole tensor
and checks ∂_μ T^μ_ν = 0 for every ν.

`conserved` is decided by reducing ∂_μ j^μ with the Euler–Lagrange equations
(each solved for its ∂_t² term) and asking sympy whether what remains is 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field as _dc_field
from typing import Any, Dict, List, Optional, Union

import sympy as sp

from ..core.lagrangian import Lagrangian
from ..core.symmetry import Symmetry


@dataclass
class NoetherResult:
    kind: str                                   # "current" | "energy_momentum"
    symmetry: str
    current: Union[List[sp.Expr], sp.Matrix]    # j^μ, or T^μ_ν as a Matrix
    charge_density: Optional[sp.Expr]           # j^0
    divergence: Union[sp.Expr, List[sp.Expr]]   # ∂_μ j^μ  (raw, before on-shell)
    conserved: bool                             # after Euler–Lagrange reduction
    eom: List[sp.Expr]
    metadata: Dict[str, Any] = _dc_field(default_factory=dict)
    notes: List[str] = _dc_field(default_factory=list)

    def __str__(self) -> str:
        head = f"NoetherResult[{self.kind}] — {self.symmetry}"
        cons = "conserved on-shell ✓" if self.conserved else "NOT conserved ✗"
        if isinstance(self.current, sp.Matrix):
            body = "  T^mu_nu =\n" + sp.pretty(self.current, use_unicode=True)
        else:
            body = "\n".join(f"  j^{mu} = {sp.sstr(j)}"
                             for mu, j in enumerate(self.current))
        return f"{head}\n{body}\n  {cons}"


# ── on-shell reduction ─────────────────────────────────────────────────────
def _on_shell(expr: sp.Expr, eoms: List[sp.Expr], comps: List[sp.Expr],
              coords) -> sp.Expr:
    """Reduce `expr` with the Euler–Lagrange system, solving it as a coupled
    set for the ∂_t² term of every component (the EL equation from varying
    φ_a need not be the one that carries ∂_t² φ_a — for a complex field it
    carries ∂_t² φ̄)."""
    expr = sp.expand(sp.sympify(expr).doit())
    eqs = [sp.Eq(sp.sympify(E), 0) for E in eoms]
    d2s = [sp.Derivative(c, coords[0], 2) for c in comps]
    unknown = [d for d in d2s
               if any(e.has(d) for e in eqs) and expr.has(d)]
    if unknown:
        sols = sp.solve(eqs, unknown, dict=True)
        if sols:
            expr = sp.expand(expr.subs(sols[0], simultaneous=True).doit())
    return sp.simplify(expr)


def _canonical_stress(L: Lagrangian) -> sp.Matrix:
    fld = L.field
    dim = fld.dim
    coords = fld.coords
    n = fld.n_components
    Lx = L.expr
    T = sp.zeros(dim, dim)
    for mu in range(dim):
        for nu in range(dim):
            s = sum(L.conjugate_momentum(a, mu)
                    * sp.Derivative(fld.components[a], coords[nu])
                    for a in range(n))
            if mu == nu:
                s = s - Lx
            T[mu, nu] = sp.simplify(s)
    return T


def first_theorem(L: Lagrangian, sym: Symmetry,
                  metadata: Optional[Dict[str, Any]] = None,
                  do_simplify: bool = True) -> NoetherResult:
    fld = L.field
    coords = fld.coords
    dim = fld.dim
    comps = fld.components
    n = len(comps)
    eoms = L.eom()
    notes: List[str] = []

    X = [sp.sympify(x) for x in sym.delta_x]
    K = sym.K(comps, L.expr, dim)

    if sym.kind == "spacetime":
        T = _canonical_stress(L)
        div = []
        conserved = True
        for nu in range(dim):
            d = sum(sp.Derivative(T[mu, nu], coords[mu]).doit() for mu in range(dim))
            r = _on_shell(d, eoms, comps, coords)
            div.append(sp.simplify(d))
            conserved = conserved and (r == 0)
        notes.append("canonical (Hilbert-improvement OFF); "
                     "∂_μ T^μ_ν checked for every ν")
        return NoetherResult(
            kind="energy_momentum", symmetry=sym.name, current=T,
            charge_density=sp.simplify(sum(T[0, nu] for nu in range(dim))),
            divergence=div, conserved=conserved, eom=eoms,
            metadata=metadata or {}, notes=notes)

    # internal symmetry -> a charge current
    Psi = [sp.sympify(p) for p in sym.delta_field(comps)]
    psi0 = [Psi[a] - sum(X[mu] * sp.Derivative(comps[a], coords[mu])
                         for mu in range(dim))
            for a in range(n)]

    j: List[sp.Expr] = []
    for mu in range(dim):
        jm = sum(L.conjugate_momentum(a, mu) * psi0[a] for a in range(n))
        jm = jm + L.expr * X[mu] + K[mu]
        j.append(sp.simplify(jm) if do_simplify else sp.expand(jm))

    div_raw = sum(sp.Derivative(j[mu], coords[mu]).doit() for mu in range(dim))
    reduced = _on_shell(div_raw, eoms, comps, coords)
    conserved = (reduced == 0)
    if not conserved:
        notes.append(f"∂_μ j^μ did not reduce to 0 — residue {sp.sstr(reduced)}")

    return NoetherResult(
        kind="current", symmetry=sym.name, current=j, charge_density=j[0],
        divergence=sp.simplify(div_raw), conserved=conserved, eom=eoms,
        metadata=metadata or {}, notes=notes)
