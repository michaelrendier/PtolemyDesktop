"""
noether_engine.improvement.belinfante_rosenfeld — BR symmetrization.

DEFERRED TO SESSION 2.

The canonical stress-energy tensor T^μν from the first theorem is not
symmetric for fields with intrinsic spin. Belinfante (1940) and Rosenfeld
(1940) independently constructed a symmetric improvement:

    T^μν_BR = T^μν_canonical + ∂_λ B^{λμν}

where B^{λμν} is built from the spin current S^{λμν}:

    B^{λμν} = (1/2)(S^{λμν} + S^{μνλ} − S^{νμλ})

The result T^μν_BR is symmetric, conserved, and agrees with the stress-
energy tensor that sources general relativity.

References:
  - Belinfante, F.J. (1940). Physica 7.
  - Rosenfeld, L. (1940). Mém. Acad. Roy. Belg. 18.
  - Weinberg, S. (1972). Gravitation and Cosmology. Ch. 12.
"""

from ..switches import UnsupportedCombinationError


def belinfante_rosenfeld_improvement(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Switch combination (improvement=belinfante_rosenfeld) not yet "
        "supported — reason: spin-current machinery scheduled for session 2. "
        "Use improvement='none' or improvement='custom' in the meantime."
    )
