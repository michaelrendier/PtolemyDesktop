"""
noether_engine — general Noether Current Engine.

Public API for the Ainulindalë Noether Current Engine. This package applies
Noether's theorem to a user-supplied Lagrangian and symmetry, producing the
conserved current with full switch-settings metadata.

Typical usage:

    from noether_engine import NoetherEngine, Lagrangian, Symmetry, Field
    import sympy as sp

    phi = Field('phi', field_type='real_scalar')
    x = sp.symbols('t x y z', real=True)
    m = sp.Symbol('m', positive=True)
    density = sp.Rational(1,2)*(sp.diff(phi.symbol, x[0])**2
                                - sum(sp.diff(phi.symbol, x[i])**2 for i in (1,2,3)))
              - sp.Rational(1,2) * m**2 * phi.symbol**2
    L = Lagrangian(density=density, fields=[phi], coords=x)

    translation = Symmetry.spacetime_translation(direction=0, coords=x, fields=[phi])
    engine = NoetherEngine(L, translation)
    result = engine.derive_current()

    print(result.summary())

See README.md for overview, architecture.md for full specification.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import sympy as sp

from .switches import (
    SwitchSettings, validate_combination,
    UnsupportedCombinationError, InvalidSwitchValueError,
    InconsistentCombinationError,
    summarize_implementation_status,
)
from .core.field import Field
from .core.lagrangian import Lagrangian
from .core.symmetry import Symmetry
from .core.variation import Variation, vertical_variation, total_variation
from .core.current import Current, derive_canonical_current
from .core.charge import charge_from_current, form_from_current
from .core.result import NoetherResult
from .theorems.first_theorem import derive_first_theorem_current, verify_conservation
from .theorems.bessel_hagen import check_quasi_invariance

# For convenience / researcher access:
from .algebra.lie import (
    u1_generator, su2_generators, su3_generators,
    su2_structure_constants,
)
from .algebra.cayley_dickson import (
    CayleyDicksonAlgebra,
    complex_multiplication, quaternion_multiplication, octonion_multiplication,
    quaternion_generators, octonion_generators,
    left_multiplication_matrix,
)
from .spacetime.minkowski import MinkowskiSpacetime, minkowski_metric_tensor


__version__ = '0.1.0-session1'
__all__ = [
    'NoetherEngine',
    'Lagrangian', 'Symmetry', 'Field',
    'Current', 'Variation', 'NoetherResult',
    'SwitchSettings',
    'UnsupportedCombinationError', 'InvalidSwitchValueError',
    'InconsistentCombinationError',
    'summarize_implementation_status',
    'u1_generator', 'su2_generators', 'su3_generators',
    'CayleyDicksonAlgebra',
    'quaternion_generators', 'octonion_generators',
    'MinkowskiSpacetime', 'minkowski_metric_tensor',
]


class NoetherEngine:
    """
    Top-level Noether Current Engine.

    Takes a Lagrangian and a Symmetry; applies Noether's theorem under the
    chosen (or default) switch settings; returns a NoetherResult.

    Usage:
      engine = NoetherEngine(L, S)                          # all defaults
      engine = NoetherEngine(L, S, theorem='first',         # explicit
                             signature='mostly_plus')
      result = engine.derive_current()
      print(result.summary())

    If the user selects a switch combination that is not yet implemented,
    .derive_current() raises UnsupportedCombinationError with a message
    naming the axis, value, and target session.
    """

    def __init__(
        self,
        lagrangian: Lagrangian,
        symmetry: Symmetry,
        **switch_kwargs: Any,
    ):
        self.lagrangian = lagrangian
        self.symmetry = symmetry
        self.settings = SwitchSettings.from_kwargs(**switch_kwargs)
        # Validate the combination NOW rather than waiting for derive_current()
        validate_combination(self.settings)

    # ── Introspection ─────────────────────────────────────────────────────

    def show_settings(self) -> Dict[str, Dict[str, Any]]:
        """Return the full metadata dict of switch settings in effect."""
        return self.settings.as_metadata_dict()

    def print_settings(self) -> None:
        """Print switch settings in readable form."""
        print("Noether Engine switch settings:")
        print("=" * 60)
        for axis, info in self.settings.as_metadata_dict().items():
            marker = " [user]" if info['user_supplied'] else " [default]"
            print(f"  {axis:25s} = {info['value']}{marker}")

    # ── Main derivation entry point ───────────────────────────────────────

    def derive_current(self, verify: bool = True) -> NoetherResult:
        """
        Apply Noether's theorem and return the full result.

        Parameters:
          verify : if True, compute ∂_μ J^μ and check on-shell vanishing.

        Returns: NoetherResult with current, charge (if output includes it),
                 LaTeX (if format includes it), metadata, and verification.
        """
        theorem = self.settings.get('theorem')
        shell = self.settings.get('shell')
        invariance = self.settings.get('invariance')
        output_mode = self.settings.get('output')
        variation_mode = self.settings.get('variation')
        format_mode = self.settings.get('format')

        # Step 1: decide variation convention
        # Default: 'vertical' for internal symmetries, 'total' for spacetime.
        if variation_mode == 'vertical':
            vc = 'vertical'
        elif variation_mode == 'total':
            vc = 'total'
        elif variation_mode == 'both':
            # For 'both', we default to the type-appropriate one for the
            # primary output and include the other in metadata.
            vc = 'total' if self.symmetry.coordinate_shift is not None else 'vertical'
        else:
            vc = 'vertical'

        # Auto-switch: if this is a spacetime-flow symmetry and variation
        # was left at default 'vertical', switch to 'total'.
        if (
            self.settings.is_default('variation')
            and self.symmetry.coordinate_shift is not None
        ):
            vc = 'total'

        # Step 2: dispatch by theorem
        if theorem == 'first':
            current, variation, verification_raw = derive_first_theorem_current(
                self.lagrangian, self.symmetry,
                variation_convention=vc,
                invariance=invariance,
                verify=verify,
            )
        else:
            raise UnsupportedCombinationError(
                f"theorem={theorem} not implemented in session 1."
            )

        # Step 3: build output in requested form(s)
        result_charge: Optional[sp.Expr] = None
        result_form: Optional[sp.Expr] = None
        if output_mode in ('charge', 'all'):
            result_charge = charge_from_current(current, self.lagrangian)
        if output_mode in ('form', 'all'):
            result_form = form_from_current(current, self.lagrangian)

        # Step 4: LaTeX
        result_latex: Optional[Dict[str, str]] = None
        if format_mode in ('latex', 'all'):
            result_latex = {
                f"J^{mu}": sp.latex(c) for mu, c in enumerate(current.components)
            }
            if result_charge is not None:
                result_latex['Q'] = sp.latex(result_charge)

        # Step 5: assemble NoetherResult
        return NoetherResult(
            current=current,
            charge=result_charge,
            form=result_form,
            latex=result_latex,
            metadata=self.settings.as_metadata_dict(),
            verification=verification_raw,
            variation=variation.delta_L,
            K_mu=variation.K_mu,
        )


if __name__ == '__main__':
    # Print status summary when module is executed directly
    print(summarize_implementation_status())
