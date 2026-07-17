"""
noether_engine.quantum.anomaly — anomaly tracking.

DEFERRED TO SESSION 4.

A classically-conserved current may fail to be conserved quantum-mechanically
due to an anomaly:

    ∂_μ J^μ = (anomaly coefficient) × (topological density)

Examples:
  - Adler-Bell-Jackiw axial anomaly: ∂_μ J^μ_5 = (e²/8π²) F F̃
  - Trace anomaly of conformal field theory: T^μ_μ ∝ (c_a) R² + (c_b) R_{μν}²
  - Chiral anomaly in the Standard Model: fixed by requirement of
    anomaly cancellation between fermion generations.

Session 4 will implement:
  - classical-conservation check (output from this engine's first theorem)
  - one-loop anomaly diagnosis via Fujikawa's path-integral method
  - consistent vs covariant anomaly distinction (Bardeen-Zumino)

References:
  - Bertlmann, R. (1996). Anomalies in Quantum Field Theory.
  - Bardeen & Zumino (1984). Nucl. Phys. B 244.
"""

from ..switches import UnsupportedCombinationError


def anomaly_coefficient(*args, **kwargs):
    raise UnsupportedCombinationError(
        "Switch combination (theory=anomaly_tracked) not yet supported — "
        "reason: anomaly-tracking machinery scheduled for session 4. "
        "Use theory='classical' in the meantime."
    )
