"""
noether_engine.core.field — the field content a Lagrangian is built on.

A `Field` is a named list of sympy component functions of the spacetime
coordinates, plus a signature-aware metric.  Real and complex scalars are the
Session-1 working set; a complex scalar is carried as two independent real
components ``[phi, phibar]`` (never sympy `conjugate`, which does not
differentiate cleanly), which is exactly the pair U(1) rotates.

    x   = coords(4)                     # (x0, x1, x2, x3), x0 = time
    phi = real_scalar("phi", x)
    cx  = complex_scalar("phi", x)      # cx.components == [phi, phibar]
"""
from __future__ import annotations

from dataclasses import dataclass, field as _dc_field
from typing import List, Sequence, Tuple

import sympy as sp

# mostly-minus (particle physics) and mostly-plus (GR) diag metrics
_SIGNATURES = {
    "mostly_minus": (1, -1, -1, -1),
    "mostly_plus": (-1, 1, 1, 1),
}


def coords(dim: int = 4, names: str = "x") -> Tuple[sp.Symbol, ...]:
    """Spacetime coordinate symbols (x0..x{dim-1}); x0 is time."""
    return tuple(sp.Symbol(f"{names}{i}", real=True) for i in range(dim))


@dataclass
class Field:
    name: str
    coords: Tuple[sp.Symbol, ...]
    components: List[sp.Expr]              # Function applications f(x0,...)
    signature: str = "mostly_minus"
    is_complex: bool = False
    comp_names: List[str] = _dc_field(default_factory=list)

    # ── metric ────────────────────────────────────────────────────────────
    @property
    def eta(self) -> Tuple[int, ...]:
        return _SIGNATURES[self.signature]

    def metric(self) -> sp.Matrix:
        return sp.diag(*self.eta)

    # ── derivatives ──────────────────────────────────────────────────────
    def d(self, comp: sp.Expr, mu: int) -> sp.Expr:
        """Lower-index partial ∂_μ comp."""
        return sp.Derivative(comp, self.coords[mu])

    def box(self, comp: sp.Expr) -> sp.Expr:
        """d'Alembertian □comp = η^{μν} ∂_μ ∂_ν comp (diag metric)."""
        return sum(self.eta[mu] * sp.Derivative(comp, self.coords[mu], 2)
                   for mu in range(len(self.coords)))

    @property
    def dim(self) -> int:
        return len(self.coords)

    @property
    def n_components(self) -> int:
        return len(self.components)


def real_scalar(name: str, x: Sequence[sp.Symbol],
                signature: str = "mostly_minus") -> Field:
    phi = sp.Function(name, real=True)(*x)
    return Field(name=name, coords=tuple(x), components=[phi],
                 signature=signature, is_complex=False, comp_names=[name])


def complex_scalar(name: str, x: Sequence[sp.Symbol],
                   signature: str = "mostly_minus") -> Field:
    """φ and φ̄ as two independent real components — the pair U(1) rotates."""
    phi = sp.Function(name, real=True)(*x)
    bar = sp.Function(name + "bar", real=True)(*x)
    return Field(name=name, coords=tuple(x), components=[phi, bar],
                 signature=signature, is_complex=True,
                 comp_names=[name, name + "bar"])


def multiplet(name: str, x: Sequence[sp.Symbol], n: int,
              signature: str = "mostly_minus") -> Field:
    """An n-component real multiplet φ_1..φ_n (isospin / colour carriers)."""
    comps = [sp.Function(f"{name}{i+1}", real=True)(*x) for i in range(n)]
    return Field(name=name, coords=tuple(x), components=comps,
                 signature=signature, is_complex=False,
                 comp_names=[f"{name}{i+1}" for i in range(n)])
