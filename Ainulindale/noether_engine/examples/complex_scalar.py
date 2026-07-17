"""
noether_engine.examples.complex_scalar — complex scalar + global U(1).

Canonical worked example. Lagrangian:

    ℒ = η^{μν} (∂_μ φ*)(∂_ν φ)  −  m² φ* φ

Symmetry: global U(1) phase rotation  φ → e^{iα} φ ≈ φ + i α φ.
Vertical variation: δφ = iα φ, δφ* = -iα φ*.

Noether's first theorem gives the conserved probability current:

    J^μ = i q [ (∂^μ φ*) φ  −  φ* (∂^μ φ) ]

Conservation: ∂_μ J^μ = 0 on the Klein-Gordon equation (□ + m²) φ = 0.

For charged-scalar QED, this is the current that couples to the photon.
For this example we use an algebra-valued field with algebra='C' so the
engine treats it as a 2-component (re, im) object, which is how SMNNIP
uses ℂ-valued fields.
"""

from __future__ import annotations

from typing import Dict, Tuple

import sympy as sp

from ..core.field import Field
from ..core.lagrangian import Lagrangian
from ..core.symmetry import Symmetry
from ..theorems.first_theorem import derive_first_theorem_current


def build_complex_scalar_example(signature: str = 'mostly_minus') -> Tuple[Lagrangian, Symmetry, Dict]:
    """
    Construct the Lagrangian using algebra='C' for the complex scalar.
    The field has two real components φ = (φ_re, φ_im) and the global U(1)
    acts as a rotation in the (re, im) plane.
    """
    coords = sp.symbols('t x y z', real=True)
    phi = Field(name='phi', field_type='algebra_valued', algebra='C', coords=coords)
    m = sp.Symbol('m', positive=True)
    q = sp.Symbol('q', real=True)  # charge

    phi_re, phi_im = phi.components

    # Metric signs
    if signature == 'mostly_minus':
        diag = [1, -1, -1, -1]
    elif signature == 'mostly_plus':
        diag = [-1, 1, 1, 1]
    else:
        raise ValueError(f"signature='{signature}' not recognized.")

    # |∂_μ φ|² = (∂_μ φ_re)² + (∂_μ φ_im)²
    kinetic = sp.Integer(0)
    for mu in range(4):
        d_re = sp.diff(phi_re, coords[mu])
        d_im = sp.diff(phi_im, coords[mu])
        kinetic += diag[mu] * (d_re**2 + d_im**2)

    # |φ|² = φ_re² + φ_im²
    mass_sq = phi_re**2 + phi_im**2

    density = kinetic - m**2 * mass_sq

    L = Lagrangian(
        density=density,
        fields=[phi],
        coords=coords,
        signature=signature,
    )

    # Global U(1): δ(re + i·im) = i·q·(re + i·im) = -q·im + i·q·re
    # so δre = -q·im, δim = q·re.
    u1_symmetry = Symmetry.global_u1_phase(phi, charge=q)

    context = {
        'field': phi,
        'mass': m,
        'charge': q,
        'signature': signature,
    }
    return L, u1_symmetry, context


def run_complex_scalar_example(signature: str = 'mostly_minus') -> Dict:
    """
    Build the complex-scalar example, derive the conserved U(1) current,
    and return the full result with verification.
    """
    L, S, ctx = build_complex_scalar_example(signature=signature)

    # Global U(1) is an internal symmetry: use vertical variation.
    current, variation, verification = derive_first_theorem_current(
        L, S,
        variation_convention='vertical',
        invariance='strict',   # global U(1) gives δℒ = 0 exactly
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
            'J^μ is the conserved probability / charge current. Integration '
            'of J^0 over 3-space gives the conserved U(1) charge Q. '
            'In charged-scalar QED, this is the current that couples to A_μ.'
        ),
    }


if __name__ == '__main__':
    result = run_complex_scalar_example()
    print("COMPLEX SCALAR — GLOBAL U(1)")
    print("=" * 60)
    for mu, Jmu in enumerate(result['current'].components):
        print(f"  J^{mu} = {sp.simplify(Jmu)}")
    print()
    print("Conservation check:")
    for k, v in result['verification'].items():
        print(f"  {k}: {v}")
