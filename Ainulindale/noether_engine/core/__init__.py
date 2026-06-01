"""
noether_engine.core — foundational classes.

Field       : a field with declared type and algebra
Lagrangian  : a Lagrangian density with associated fields and coordinates
Symmetry    : an infinitesimal symmetry transformation
Variation   : apply a symmetry to a Lagrangian (vertical / total)
Current     : conserved current assembly
NoetherResult: structured output with metadata
"""

from .field import Field
from .lagrangian import Lagrangian
from .symmetry import Symmetry
from .variation import Variation, vertical_variation, total_variation
from .current import Current, derive_canonical_current
from .charge import charge_from_current, form_from_current
from .result import NoetherResult

__all__ = [
    'Field',
    'Lagrangian',
    'Symmetry',
    'Variation',
    'vertical_variation',
    'total_variation',
    'Current',
    'derive_canonical_current',
    'charge_from_current',
    'form_from_current',
    'NoetherResult',
]
