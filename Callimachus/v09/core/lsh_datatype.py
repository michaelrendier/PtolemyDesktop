#!/usr/bin/env python3
"""
Callimachus — LSH_Datatype
===========================
Lagrange Self-Adjoint Hyperindexing Datatype.

TODO: Mathematical rigor — self-adjoint operator proof.
      Hermitian/self-adjoint claim: the Horner bijection operator equals
      its own adjoint over the charset space. Requires formal proof.
      See Hermitian TODO in SERVER_SPEC.md.

12 spectral layers. Fixed array.
Acquisition-only layers: 0-5. AI-writable layers: 6-11.
layer_writable_mask = 0x0FC0  (bits 6-11 set)

Rabies Principle: first_encountered is PERMANENTLY IMMUTABLE after first set.
  - Python: raises AttributeError on any write attempt after construction
  - C++ canonical: const field
  - SQLite: enforced by trigger

Layer map:
  0  word_surface       acquisition-only
  1  canonical_form     acquisition-only
  2  pos_primary        acquisition-only
  3  pos_secondary      acquisition-only
  4  etymology          acquisition-only
  5  definition_core    acquisition-only
  6  definition_ext     AI-writable
  7  semantic_vector    AI-writable
  8  relational_graph   AI-writable
  9  contextual_usage   AI-writable
  10 spectral_tone      AI-writable  (demotic Unicode Tag glyph sequence)
  11 cross_lang_bridge  AI-writable
"""

import time
from typing import Any

_WRITABLE_MASK: int = 0x0FC0
_LAYER_COUNT:   int = 12

LAYER_NAMES = [
    "word_surface", "canonical_form", "pos_primary", "pos_secondary",
    "etymology", "definition_core", "definition_ext", "semantic_vector",
    "relational_graph", "contextual_usage", "spectral_tone", "cross_lang_bridge",
]


class LSH_Datatype:
    """
    Lagrange Self-Adjoint Hyperindexing word datatype.
    Always construct via from_acquisition() for new words.
    """

    __slots__ = ('hw_label', 'first_encountered', '_layers',
                 '_writable_mask', 'charset_standard')

    def __init__(self, hw_label: str, first_encountered: str,
                 charset_standard: str = "Unicode 15.1"):
        object.__setattr__(self, 'hw_label',          hw_label)
        object.__setattr__(self, 'first_encountered', first_encountered)
        object.__setattr__(self, 'charset_standard',  charset_standard)
        object.__setattr__(self, '_writable_mask',    _WRITABLE_MASK)
        object.__setattr__(self, '_layers',           [None] * _LAYER_COUNT)

    def __setattr__(self, name, value):
        if name == 'first_encountered':
            raise AttributeError(
                "first_encountered is immutable (Rabies Principle)."
            )
        object.__setattr__(self, name, value)

    @classmethod
    def from_acquisition(cls, hw_label: str, word_surface: str,
                         canonical: str, pos_primary: str = None,
                         pos_secondary: str = None, etymology: str = None,
                         definition: str = None) -> 'LSH_Datatype':
        inst = cls(hw_label=hw_label, first_encountered=time.ctime())
        inst._layers[0] = word_surface
        inst._layers[1] = canonical
        inst._layers[2] = pos_primary
        inst._layers[3] = pos_secondary
        inst._layers[4] = etymology
        inst._layers[5] = definition
        return inst

    def get_layer(self, index: int) -> Any:
        if not 0 <= index < _LAYER_COUNT:
            raise IndexError(f"Layer {index} out of range.")
        return self._layers[index]

    def set_layer(self, index: int, value: Any) -> None:
        if not 0 <= index < _LAYER_COUNT:
            raise IndexError(f"Layer {index} out of range.")
        if not (self._writable_mask >> index) & 1:
            raise PermissionError(
                f"Layer {index} ({LAYER_NAMES[index]}) is acquisition-only."
            )
        self._layers[index] = value

    def to_dict(self) -> dict:
        return {
            "hw_label":          self.hw_label,
            "first_encountered": self.first_encountered,
            "charset_standard":  self.charset_standard,
            "layers":            {LAYER_NAMES[i]: self._layers[i]
                                  for i in range(_LAYER_COUNT)},
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'LSH_Datatype':
        inst = cls.__new__(cls)
        object.__setattr__(inst, 'hw_label',          d['hw_label'])
        object.__setattr__(inst, 'first_encountered', d['first_encountered'])
        object.__setattr__(inst, 'charset_standard',  d.get('charset_standard', 'Unicode 15.1'))
        object.__setattr__(inst, '_writable_mask',    _WRITABLE_MASK)
        layers = [None] * _LAYER_COUNT
        for i, name in enumerate(LAYER_NAMES):
            layers[i] = d['layers'].get(name)
        object.__setattr__(inst, '_layers', layers)
        return inst

    def __repr__(self):
        return (f"LSH_Datatype(label={self.hw_label[:12]}…, "
                f"word={self._layers[0]!r})")
