"""
noether_engine.shell.off_shell — BV/cohomological off-shell derivation.

DEFERRED TO SESSION 2.

The off-shell formulation treats the conservation law as an algebraic identity
that does not require imposing the equations of motion. This is the
Batalin-Vilkovisky (BV) formalism applied to Noether currents.

In BV terms: the Koszul-Tate differential δ encodes the equations of motion
as δ-exactness, and an off-shell conserved current is a δ-cocycle modulo
δ-coboundaries. The cohomology is computed against the BV complex.

References:
  - Henneaux & Teitelboim, Quantization of Gauge Systems (1992)
  - Barnich, Brandt & Henneaux, Local BRST cohomology (2000)
"""

from __future__ import annotations

from ..switches import UnsupportedCombinationError


def derive_off_shell_current(*args, **kwargs):
    """Not yet implemented."""
    raise UnsupportedCombinationError(
        "Switch combination (shell=off_shell) not yet supported — "
        "reason: BV/cohomological machinery required. Scheduled for session 2. "
        "Use shell='on_shell' in the meantime."
    )
