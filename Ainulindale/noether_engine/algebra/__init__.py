"""
noether_engine.algebra — algebras for representing fields and generators.

lie             : standard Lie algebra generators (u(1), su(2), su(3))
clifford        : gamma matrices for Dirac spinors (session 2)
cayley_dickson  : ℝ/ℂ/ℍ/𝕆 tower via Cayley-Dickson doubling (for SMNNIP)
"""

from .lie import (
    u1_generator, su2_generators, su3_generators,
    LieGeneratorConvention, GENERATOR_CONVENTIONS,
)
from .cayley_dickson import (
    CayleyDicksonAlgebra, real_multiplication, complex_multiplication,
    quaternion_multiplication, octonion_multiplication,
    left_multiplication_matrix,
)

__all__ = [
    'u1_generator', 'su2_generators', 'su3_generators',
    'LieGeneratorConvention', 'GENERATOR_CONVENTIONS',
    'CayleyDicksonAlgebra',
    'real_multiplication', 'complex_multiplication',
    'quaternion_multiplication', 'octonion_multiplication',
    'left_multiplication_matrix',
]
