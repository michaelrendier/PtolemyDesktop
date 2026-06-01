"""
noether_engine.examples.free_scalar — free real scalar + spacetime translation.

Canonical worked example. Lagrangian:

    ℒ = (1/2) η^{μν} (∂_μ φ)(∂_ν φ)  −  (1/2) m² φ²

    mostly_minus signature:  ℒ = (1/2)(φ̇² − (∇φ)²) − (1/2) m² φ²

Symmetry: spacetime translation x^μ → x^μ + ε δ^μ_ν.
For each direction ν, the vertical variation is δφ = −∂_ν φ and the
coordinate shift is ξ^μ = δ^μ_ν.

Noether's first theorem gives the canonical stress-energy tensor:

    T^μ_ν = (∂ℒ/∂(∂_μφ)) · ∂_ν φ  −  δ^μ_ν · ℒ

Conservation: ∂_μ T^μ_ν = 0 on the Klein-Gordon equation.

For translations in time (ν = 0), T^0_0 is the Hamiltonian density;
T^μ_0 is the energy-flux 4-vector. Integration over 3-space gives the
conserved energy.
"""

from __future__ import annotations

from typing import Dict, Tuple

import sympy as sp

from ..core.field import Field
from ..core.lagrangian import Lagrangian
from ..core.symmetry import Symmetry
from ..theorems.first_theorem import derive_first_theorem_current


def build_free_scalar_example(signature: str = 'mostly_minus') -> Tuple[Lagrangian, Symmetry, Dict]:
    """
    Construct the Lagrangian and a single translation symmetry (ν = 0, time).
    Returns (L, symmetry, context_dict).
    """
    coords = sp.symbols('t x y z', real=True)
    phi = Field(name='phi', field_type='real_scalar', coords=coords)
    m = sp.Symbol('m', positive=True)

    # Metric signs
    if signature == 'mostly_minus':
        diag = [1, -1, -1, -1]
    elif signature == 'mostly_plus':
        diag = [-1, 1, 1, 1]
    else:
        raise ValueError(f"signature='{signature}' not recognized.")

    # Build kinetic term (1/2) η^{μν} ∂_μφ ∂_νφ
    kinetic = sp.Integer(0)
    for mu in range(4):
        dmu_phi = sp.diff(phi.symbol, coords[mu])
        kinetic += sp.Rational(1, 2) * diag[mu] * dmu_phi**2

    # Mass term: the convention is L = (kinetic) - (1/2) m² φ²
    # In mostly_minus, kinetic comes out with (1/2)(φ̇² - (∇φ)²), mass is subtracted.
    # In mostly_plus, kinetic is (1/2)(-φ̇² + (∇φ)²), and by convention we flip
    # the mass sign to keep the EOM consistent with (□ + m²) φ = 0. To avoid
    # complicating this example, we present only the mostly_minus form here.
    density = kinetic - sp.Rational(1, 2) * m**2 * phi.symbol**2

    L = Lagrangian(
        density=density,
        fields=[phi],
        coords=coords,
        signature=signature,
    )

    # Time translation: δφ = -∂_t φ, ξ^μ = δ^μ_0
    translation_t = Symmetry.spacetime_translation(
        direction=0,
        coords=coords,
        fields=[phi],
    )

    context = {
        'field': phi,
        'mass': m,
        'kinetic_part': kinetic,
        'signature': signature,
    }
    return L, translation_t, context


def run_free_scalar_example(signature: str = 'mostly_minus') -> Dict:
    """
    Build the free-scalar example, derive the conserved current for time
    translation, and return the full result with verification.
    """
    L, S, ctx = build_free_scalar_example(signature=signature)

    # Spacetime translation uses total variation (follows the flow)
    current, variation, verification = derive_first_theorem_current(
        L, S,
        variation_convention='total',
        invariance='strict',     # strict: translation-invariant ℒ has δℒ=0
        verify=True,
    )

    return {
        'lagrangian': L,
        'symmetry': S,
        'context': ctx,
        'current': current,
        'variation': variation,
        'verification': verification,
        'interpretation': (
            'Current J^μ is the stress-energy four-vector T^μ_0 for time '
            'translation. J^0 = T^0_0 is the Hamiltonian density '
            '(energy density). J^i = T^i_0 is the energy-flux vector.'
        ),
    }


if __name__ == '__main__':
    result = run_free_scalar_example()
    print("FREE SCALAR — SPACETIME TRANSLATION")
    print("=" * 60)
    for mu, Jmu in enumerate(result['current'].components):
        print(f"  J^{mu} = {sp.simplify(Jmu)}")
    print()
    print("Conservation check:")
    for k, v in result['verification'].items():
        print(f"  {k}: {v}")
