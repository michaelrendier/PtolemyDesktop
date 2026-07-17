"""
noether_engine.spacetime.euclidean — Euclidean (imaginary-time) spacetime.

DEFERRED TO SESSION 3.

In Euclidean signature (all-plus, after Wick rotation t → -iτ), Noether's
theorem applies with modified sign conventions. Used in statistical field
theory and instanton calculations.
"""

from ..switches import UnsupportedCombinationError


class EuclideanSpacetime:
    def __init__(self, *args, **kwargs):
        raise UnsupportedCombinationError(
            "Switch combination (spacetime=euclidean) not yet supported — "
            "reason: Euclidean / imaginary-time formalism scheduled for "
            "session 3. Use spacetime='minkowski' in the meantime."
        )
