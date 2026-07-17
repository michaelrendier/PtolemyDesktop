"""
noether_engine.core.field — the Field object.

A Field represents one field in the Lagrangian. Fields have:
  - a name
  - a field type (determines variation rules)
  - optional algebra labeling (ℝ, ℂ, ℍ, 𝕆 for SMNNIP-style algebra-valued fields)
  - optional generator index (for gauge fields) and spacetime index

The Field class also provides the symbolic-derivative shorthand phi.d(mu).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import sympy as sp


# Supported field types. Each type determines how infinitesimal variations act.
FIELD_TYPES = frozenset({
    'real_scalar',
    'complex_scalar',
    'dirac_4_component',     # (session 2 — requires gamma matrices)
    'weyl_2_component',      # (session 2)
    'majorana',              # (session 2)
    'vector_abelian',        # e.g. photon A_μ
    'vector_non_abelian',    # e.g. gluon A^a_μ
    'tensor_spin_2',         # e.g. metric perturbation h_{μν} (session 3)
    'algebra_valued',        # ℂ / ℍ / 𝕆 — for SMNNIP
})

# Supported algebra labels (relevant when field_type='algebra_valued')
ALGEBRA_LABELS = frozenset({'R', 'C', 'H', 'O'})


class Field:
    """
    A field in a Lagrangian.

    Attributes:
      name           : string identifier
      field_type     : one of FIELD_TYPES
      algebra        : for algebra_valued — 'R', 'C', 'H', or 'O'
      coords         : tuple of sympy coordinate symbols (default (t, x, y, z))
      symbol         : sympy Function(name)(*coords) instance
      spacetime_index: optional, for vector/tensor fields
      gauge_index    : optional, for non-abelian gauge fields
      components     : for algebra_valued or dirac fields, list of component symbols

    A Field behaves as a sympy expression (via the .symbol attribute) but also
    carries enough metadata for the variation machinery to know how to act on it.
    """

    def __init__(
        self,
        name: str,
        field_type: str = 'real_scalar',
        algebra: Optional[str] = None,
        coords: Optional[Sequence[sp.Symbol]] = None,
        spacetime_index: Optional[str] = None,
        gauge_index: Optional[str] = None,
    ):
        if field_type not in FIELD_TYPES:
            raise ValueError(
                f"field_type='{field_type}' not recognized. "
                f"Valid types: {sorted(FIELD_TYPES)}"
            )

        if field_type == 'algebra_valued':
            if algebra is None:
                raise ValueError(
                    "field_type='algebra_valued' requires algebra label "
                    "in {'R', 'C', 'H', 'O'}."
                )
            if algebra not in ALGEBRA_LABELS:
                raise ValueError(
                    f"algebra='{algebra}' not recognized. "
                    f"Valid labels: {sorted(ALGEBRA_LABELS)}"
                )

        self.name = name
        self.field_type = field_type
        self.algebra = algebra
        self.spacetime_index = spacetime_index
        self.gauge_index = gauge_index

        if coords is None:
            coords = sp.symbols('t x y z', real=True)
        self.coords = tuple(coords)

        # Build the sympy function symbol
        self.symbol = sp.Function(name)(*self.coords)

        # For algebra-valued fields, build component symbols
        if field_type == 'algebra_valued':
            dim = {'R': 1, 'C': 2, 'H': 4, 'O': 8}[algebra]
            self.components = [
                sp.Function(f"{name}_{i}")(*self.coords) for i in range(dim)
            ]
            self.dim = dim
        else:
            self.components = [self.symbol]
            self.dim = 1

    def d(self, mu: int) -> sp.Expr:
        """
        Partial derivative ∂_μ φ with respect to the μ-th coordinate.

        For scalar fields, returns ∂_μ φ. For multi-component fields, returns
        a list of ∂_μ φ_i (one per component).
        """
        if self.field_type == 'algebra_valued':
            return [sp.diff(comp, self.coords[mu]) for comp in self.components]
        return sp.diff(self.symbol, self.coords[mu])

    def conjugate(self) -> 'Field':
        """
        Return the conjugate field φ* (or Ψ̄ for fermions).

        For real_scalar, returns self.
        For complex_scalar, returns the complex-conjugate field.
        For algebra_valued, returns the algebra conjugate (negate imaginary parts).
        """
        if self.field_type == 'real_scalar':
            return self
        if self.field_type == 'complex_scalar':
            conj = Field(
                name=f"{self.name}_star",
                field_type='complex_scalar',
                coords=self.coords,
            )
            conj._is_conjugate_of = self
            return conj
        if self.field_type == 'algebra_valued':
            conj = Field(
                name=f"{self.name}_conj",
                field_type='algebra_valued',
                algebra=self.algebra,
                coords=self.coords,
            )
            conj._is_conjugate_of = self
            return conj
        raise NotImplementedError(
            f"conjugate() for field_type='{self.field_type}' not implemented in session 1."
        )

    def __repr__(self) -> str:
        parts = [f"name='{self.name}'", f"type='{self.field_type}'"]
        if self.algebra:
            parts.append(f"algebra='{self.algebra}'")
        if self.spacetime_index:
            parts.append(f"st_index='{self.spacetime_index}'")
        if self.gauge_index:
            parts.append(f"gauge_index='{self.gauge_index}'")
        return f"Field({', '.join(parts)})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Field):
            return NotImplemented
        return (
            self.name == other.name
            and self.field_type == other.field_type
            and self.algebra == other.algebra
            and self.coords == other.coords
        )

    def __hash__(self) -> int:
        return hash((self.name, self.field_type, self.algebra, self.coords))
