"""
noether_engine.improvement — improvement terms for stress-energy tensor.

DEFERRED TO SESSION 2.

The canonical Noether stress-energy tensor T^μν from the first theorem is
not always symmetric (for fields with spin) and not always trace-free
(even for conformal theories). Improvement terms add a divergence-free
piece that fixes these properties without changing conservation.

belinfante_rosenfeld : symmetrizes T^μν for spin fields
ccj                  : Callan-Coleman-Jackiw conformal improvement
custom               : user-supplied improvement term (available now)
"""

from .custom import apply_custom_improvement

__all__ = ['apply_custom_improvement']
