"""
noether_engine.algebra.clifford — Clifford algebra / gamma matrices.

DEFERRED TO SESSION 2.

For Dirac fields, Noether's theorem requires gamma matrices γ^μ satisfying
the Clifford algebra {γ^μ, γ^ν} = 2 η^{μν}. The Dirac Noether current is

    J^μ = Ψ̄ γ^μ Ψ    with    Ψ̄ = Ψ† γ^0.

The vector/tensor variations for Lorentz symmetries also need spinor
representations via σ^{μν} = (i/4) [γ^μ, γ^ν].

Session 2 will implement:
  - Dirac representation (γ^0 block-diagonal)
  - Weyl/chiral representation (γ^5 diagonal)
  - Majorana representation (real γ^μ)
  - bilinears and their transformation laws
  - conjugate Dirac field Ψ̄
  - spinor-index-aware variation machinery

galgebra package will be used where its conventions match; hand-rolled gamma
matrices are straightforward where it does not.
"""

from __future__ import annotations

from ..switches import UnsupportedCombinationError


def dirac_gamma_matrices(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Dirac gamma matrices (field_type='dirac_4_component') not yet "
        "supported — reason: spinor representation machinery scheduled for "
        "session 2. Use field_type='real_scalar', 'complex_scalar', or "
        "'algebra_valued' in the meantime."
    )
