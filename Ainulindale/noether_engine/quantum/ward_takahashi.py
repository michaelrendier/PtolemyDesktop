"""
noether_engine.quantum.ward_takahashi — Ward-Takahashi identities.

DEFERRED TO SESSION 4.

Classical Noether conservation ∂_μ J^μ = 0 becomes, in a quantum theory,
the Ward-Takahashi identity for correlation functions:

    ∂_μ ⟨J^μ(x) O(y_1)...O(y_n)⟩ = Σ contact terms

where the contact terms arise from the action of the symmetry on the O(y_i).
This is the quantum statement of Noether's theorem.

For QED: the photon self-energy is transverse, the electron form factor is
constrained by current conservation, the running of couplings is tied to
anomalous dimensions of currents.

Session 4 will implement the classical Ward identity derivation; full
regularization-dependent quantum treatment is likely session 5.
"""

from ..switches import UnsupportedCombinationError


def ward_identity(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Switch combination (theory=quantum_ward) not yet supported — "
        "reason: Ward-Takahashi machinery scheduled for session 4. "
        "Use theory='classical' in the meantime."
    )
