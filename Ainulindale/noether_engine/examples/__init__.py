"""
noether_engine.examples — worked examples of Noether's theorem.

Each example is a self-contained script that builds a Lagrangian, declares
a symmetry, runs the engine, and verifies the resulting current satisfies
∂_μ J^μ = 0 on-shell.

The examples exist to give Noether researchers standard test cases that
confirm the engine's machinery works correctly before examining the SMNNIP
application.

Implemented in session 1:
  free_scalar       : free real scalar, spacetime translation → stress-energy tensor
  complex_scalar    : complex scalar, global U(1) → probability current
  smnnip_gauge      : SMNNIP ℒ_NN gauge Noether current — the application

Deferred to session 2:
  dirac             : Dirac field, global U(1) → Dirac current
  qed               : QED, local U(1) → Ward identity (second theorem)
  yang_mills        : non-abelian gauge, global transformation → color current
"""

from .free_scalar import build_free_scalar_example, run_free_scalar_example
from .complex_scalar import build_complex_scalar_example, run_complex_scalar_example
from .smnnip_gauge import build_smnnip_gauge_example, run_smnnip_gauge_example

__all__ = [
    'build_free_scalar_example', 'run_free_scalar_example',
    'build_complex_scalar_example', 'run_complex_scalar_example',
    'build_smnnip_gauge_example', 'run_smnnip_gauge_example',
]
