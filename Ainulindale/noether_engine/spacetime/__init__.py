"""
noether_engine.spacetime — spacetime-type handlers.

minkowski  : flat 4D, standard signature (implemented)
curved     : Riemannian/Lorentzian with user-supplied metric (session 3)
euclidean  : imaginary-time (session 3)
adm        : 3+1 Hamiltonian split (session 3)
"""

from .minkowski import MinkowskiSpacetime, minkowski_metric_tensor

__all__ = ['MinkowskiSpacetime', 'minkowski_metric_tensor']
