"""
noether_engine.spacetime.adm — ADM 3+1 split.

DEFERRED TO SESSION 3.

The Arnowitt-Deser-Misner formalism splits 4D spacetime into 3D spatial
slices plus a time coordinate, with lapse N and shift N^i functions
parameterizing the foliation. Noether currents in this formalism are
computed on each slice; the conservation law becomes a Hamiltonian
constraint.

Used in numerical relativity and canonical quantum gravity.
"""

from ..switches import UnsupportedCombinationError


class ADMSpacetime:
    def __init__(self, *args, **kwargs):
        raise UnsupportedCombinationError(
            "Switch combination (spacetime=adm) not yet supported — "
            "reason: ADM 3+1 split scheduled for session 3. "
            "Use spacetime='minkowski' in the meantime."
        )
