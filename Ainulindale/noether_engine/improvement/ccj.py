"""
noether_engine.improvement.ccj — Callan-Coleman-Jackiw conformal improvement.

DEFERRED TO SESSION 2.

CCJ (1970) showed that for conformal field theories, an improvement term
can be added to make the trace of the stress-energy tensor vanish:

    T^μν_CCJ = T^μν_BR + (1/6)(η^μν ∂² − ∂^μ∂^ν) φ²

for a conformally-coupled scalar. T^μ_μ = 0 becomes an identity rather than
an equation of motion.

References:
  - Callan, C.G., Coleman, S., Jackiw, R. (1970). Ann. Phys. 59.
"""

from ..switches import UnsupportedCombinationError


def ccj_improvement(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Switch combination (improvement=ccj) not yet supported — "
        "reason: conformal-improvement machinery scheduled for session 2. "
        "Use improvement='none' or improvement='custom' in the meantime."
    )
