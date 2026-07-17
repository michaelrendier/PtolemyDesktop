"""
noether_engine.core.symmetry — the Symmetry object.

A Symmetry represents an infinitesimal continuous transformation of fields
and/or spacetime coordinates, parameterized by a small parameter ε.

For the first Noether theorem (global symmetry), the transformation law is:
  φ → φ + ε · δφ(φ, ∂φ, x)
  x^μ → x^μ + ε · ξ^μ(x)

The Symmetry object carries:
  - name: human-readable identifier
  - field_variations: dict mapping Field → δφ expression (vertical part)
  - coordinate_shift: optional ξ^μ(x) for spacetime symmetries
  - parameter: the symbolic ε
  - K_mu: optional Bessel-Hagen boundary term (if invariance is divergence/bessel_hagen)

The engine computes δℒ = ∂_μ K^μ for Bessel-Hagen symmetries to verify
quasi-invariance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

import sympy as sp

from .field import Field


class Symmetry:
    """
    An infinitesimal continuous symmetry.

    Parameters:
      name              : identifier
      field_variations  : dict { Field : δφ (symbolic) }
                          δφ is the vertical variation: φ → φ + ε·δφ at the same x.
      coordinate_shift  : optional list [ξ^0, ξ^1, ξ^2, ξ^3] of coordinate
                          shifts; None for internal symmetries.
      parameter         : symbolic ε (default: sp.Symbol('epsilon'))
      K_mu              : optional [K^0, K^1, K^2, K^3] for Bessel-Hagen
                          quasi-invariance (δℒ = ∂_μ K^μ).

    Factory classmethods:
      - Symmetry.spacetime_translation(direction, coords)
      - Symmetry.global_u1_phase(field)
      - Symmetry.global_phase_on_field(field, phase_generator)
    """

    def __init__(
        self,
        name: str,
        field_variations: Dict[Field, Any],
        coordinate_shift: Optional[Sequence[sp.Expr]] = None,
        parameter: Optional[sp.Symbol] = None,
        K_mu: Optional[Sequence[sp.Expr]] = None,
    ):
        self.name = name
        self.field_variations = dict(field_variations)
        self.coordinate_shift = (
            tuple(coordinate_shift) if coordinate_shift is not None else None
        )
        self.parameter = parameter or sp.Symbol('epsilon', positive=True)
        self.K_mu = tuple(K_mu) if K_mu is not None else None

    # ── Factory classmethods for common symmetries ────────────────────────

    @classmethod
    def spacetime_translation(
        cls,
        direction: int,
        coords: Sequence[sp.Symbol],
        fields: Sequence[Field],
    ) -> 'Symmetry':
        """
        Spacetime translation x^μ → x^μ + ε δ^μ_direction.
        Fields transform as φ(x) → φ(x - ε δ^μ_direction e_μ), so the
        vertical variation is δφ = -∂_direction φ.
        """
        n = len(coords)
        shift = [sp.Integer(0)] * n
        shift[direction] = sp.Integer(1)
        field_vars = {
            f: -sp.diff(f.symbol, coords[direction]) for f in fields
            if f.field_type != 'algebra_valued'
        }
        for f in fields:
            if f.field_type == 'algebra_valued':
                field_vars[f] = [-sp.diff(c, coords[direction]) for c in f.components]
        return cls(
            name=f"spacetime_translation_mu_{direction}",
            field_variations=field_vars,
            coordinate_shift=shift,
        )

    @classmethod
    def global_u1_phase(
        cls,
        field: Field,
        charge: sp.Expr = sp.Integer(1),
    ) -> 'Symmetry':
        """
        Global U(1) phase rotation: φ → e^{iεq} φ ≈ φ + iεq φ.
        For complex_scalar: δφ = i·q·φ, δφ* = -i·q·φ*.
        For algebra_valued complex (ℂ): rotate 2-component as (re, im) → (re - εq·im, im + εq·re).
        """
        if field.field_type == 'complex_scalar':
            # δφ = i q φ  (as a sympy complex expression)
            field_vars: Dict[Field, Any] = {field: sp.I * charge * field.symbol}
            return cls(
                name=f"global_u1_phase_on_{field.name}",
                field_variations=field_vars,
            )
        elif field.field_type == 'algebra_valued' and field.algebra == 'C':
            # For ℂ-valued field, the components are (re, im).
            # δ(re + i·im) = i·q·(re + i·im) = -q·im + i·q·re
            # so δre = -q·im,  δim = q·re.
            re, im = field.components
            field_vars = {field: [-charge * im, charge * re]}
            return cls(
                name=f"global_u1_phase_on_{field.name}",
                field_variations=field_vars,
            )
        else:
            raise ValueError(
                f"global_u1_phase not defined for field_type='{field.field_type}'"
                f"{' algebra=' + str(field.algebra) if field.algebra else ''}"
            )

    @classmethod
    def global_phase_non_abelian(
        cls,
        field: Field,
        generator: sp.Matrix,
        parameter_name: str = 'epsilon',
    ) -> 'Symmetry':
        """
        Global non-abelian transformation: Ψ → Ψ + ε · T · Ψ, where T is a
        Lie algebra generator (matrix in the representation Ψ carries).

        For algebra-valued fields, `generator` is the Cayley-Dickson left-
        multiplication matrix of the imaginary unit.
        """
        if field.field_type != 'algebra_valued':
            raise ValueError(
                "global_phase_non_abelian in session 1 is implemented only "
                "for field_type='algebra_valued'. "
                "(Dirac / vector representations are session 2.)"
            )
        # Apply generator matrix to component list
        comps = sp.Matrix(field.components)
        delta_comps = generator * comps
        field_vars = {field: list(delta_comps)}
        return cls(
            name=f"global_generator_on_{field.name}",
            field_variations=field_vars,
            parameter=sp.Symbol(parameter_name, real=True),
        )

    def __repr__(self) -> str:
        return (
            f"Symmetry(name='{self.name}', "
            f"fields={[f.name for f in self.field_variations]}, "
            f"coordinate_shift={self.coordinate_shift})"
        )
