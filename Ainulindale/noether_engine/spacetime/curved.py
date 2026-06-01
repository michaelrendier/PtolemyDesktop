"""
noether_engine.spacetime.curved — curved-spacetime Noether currents.

DEFERRED TO SESSION 3.

In curved spacetime, Noether's theorem requires:
  - a user-supplied metric g_μν(x)
  - Christoffel symbols Γ^ρ_μν computed from the metric
  - covariant derivatives ∇_μ replacing partials ∂_μ
  - the volume element √|g| d^4x in the action

The conservation law becomes ∇_μ J^μ = 0, equivalently
  (1/√|g|) ∂_μ (√|g| J^μ) = 0.

Implementation will use einsteinpy for metric/Christoffel/Riemann computation.

References:
  - Wald, General Relativity (1984), §9
  - MTW, Gravitation (1973), §21
  - einsteinpy docs: https://einsteinpy.org/
"""

from __future__ import annotations

from ..switches import UnsupportedCombinationError


class CurvedSpacetime:
    def __init__(self, *args, **kwargs):
        raise UnsupportedCombinationError(
            "Switch combination (spacetime=curved) not yet supported — "
            "reason: curved-spacetime covariant derivatives require einsteinpy "
            "machinery. Scheduled for session 3. "
            "Use spacetime='minkowski' or wait for session 3 release."
        )
