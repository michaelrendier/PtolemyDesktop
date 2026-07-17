"""
noether_engine.theorems.second_theorem — Noether's second theorem.

DEFERRED TO SESSION 2.

The second theorem addresses local (gauge) symmetries and produces not a
conserved current but an identity among the Euler-Lagrange equations:

  Σ_fields (operator)(E-L_field) = 0

This "Noether identity" is the Bianchi-type identity of the theory.

For a gauge field A_μ and matter Ψ transforming as δA_μ = ∂_μ α + ... and
δΨ = iα Ψ + ..., the second theorem gives

  D_μ J^μ = 0

where D_μ is the gauge-covariant derivative and J^μ is the matter current.

This is deeply connected to the fact that gauge symmetries are
"redundancies" rather than "symmetries proper" — the second theorem tells us
the independent degrees of freedom are fewer than the field components.

References:
  - Noether, E. (1918). §II.
  - Brading, K. & Brown, H.R. (2003).
  - Sundermeyer, K. (1982). Constrained dynamics.
"""

from ..switches import UnsupportedCombinationError


def derive_second_theorem_identity(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Switch combination (theorem=second or theorem=both) not yet "
        "supported — reason: second-theorem (local gauge) machinery "
        "scheduled for session 2. Use theorem='first' in the meantime."
    )
