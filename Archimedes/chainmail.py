"""
Archimedes/chainmail.py — the document-construction experiment (STUB).
====================================================================
Where monad granularity in sentence -> paragraph -> document is explored. NOT
implemented here beyond shapes and a worked example — this is the written-down
design so the idea stops being un-writable.

Model
-----
  double_ring(lang_ring, maths_ring)
      A SENTENCE is a *double box-kite ring*: one box-kite ring drawn from
      monad3_c.bin (sentence construction) + one box-kite ring drawn from
      monad_mathematics.bin (granular maths vocabulary), with the COMBINATION
      weighted heavier — the overlap of the two rings carries the extra weight.

  sentence_ring(words)          words folded (granular monad) into one ring.
  chainmail_line(rings)         ring sentences collected in ring "shapes" —
                                a line of chainmail.
  persian_weave_3_1(lines)      chainmail lines stitched into the 3/1 Persian
                                Chainmaille pattern = a higher-order document.

A box-kite ring here = the 6-strut zero-divisor ring structure used elsewhere
in the framework (see ValaQuenta/wiki/pencil_hyperstring.md,
GenerationalLineage wiki). Each strut is a slot; a "double" ring overlays the
language ring and the maths ring strut-for-strut.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_STRUTS = 6                      # box-kite: 6 struts / a hexagonal ring


@dataclass
class Ring:
    """One box-kite ring. `slots` are the 6 strut fillers; `weight` scales it."""
    slots: List[Any] = field(default_factory=lambda: [None] * _STRUTS)
    weight: float = 1.0
    source: str = ""             # "monad3_c" | "monad_mathematics" | "double"

    def filled(self) -> int:
        return sum(1 for s in self.slots if s is not None)


def sentence_ring(words: List[str], source: str = "") -> Ring:
    """Fold a short word list onto the 6 struts. STUB — first-6 placement."""
    r = Ring(source=source)
    for i, w in enumerate(words[:_STRUTS]):
        r.slots[i] = w
    return r


def double_ring(lang_ring: Ring, maths_ring: Ring,
                combo_weight: float = 1.6180339887) -> Ring:
    """One language ring + one maths ring, overlaid strut-for-strut, the
    combination weighted heavier (default: the overlap carries φ).

    STUB: struts where BOTH rings are filled become (lang, maths) pairs and
    take `combo_weight`; struts where only one is filled keep that filler at
    its own weight.
    """
    out = Ring(source="double")
    w_lang, w_maths = lang_ring.weight, maths_ring.weight
    total = 0.0
    for i in range(_STRUTS):
        a, b = lang_ring.slots[i], maths_ring.slots[i]
        if a is not None and b is not None:
            out.slots[i] = (a, b)
            total += combo_weight
        elif a is not None:
            out.slots[i] = a
            total += w_lang
        elif b is not None:
            out.slots[i] = b
            total += w_maths
    out.weight = total / _STRUTS
    return out


def chainmail_line(rings: List[Ring]) -> Dict[str, Any]:
    """Ring sentences collected in ring 'shapes' = a line of chainmail. STUB."""
    raise NotImplementedError(
        "chainmail_line: collect double_ring sentences into a linked line — "
        "next build. Shape: [ring]-[ring]-[ring], each ring linked through two "
        "shared struts to its neighbours (the 'shape').")


def persian_weave_3_1(lines: List[Any]) -> Dict[str, Any]:
    """Chainmail lines stitched into the 3/1 Persian Chainmaille pattern =
    a higher-order document. STUB."""
    raise NotImplementedError(
        "persian_weave_3_1: 3 lines carried by 1 (the 3-in-1 Persian weave) — "
        "the document-level stitch. Next build.")


def _worked_example() -> Dict[str, Any]:
    lang = sentence_ring(["the", "of", "with", "respect", "to", "is"],
                         source="monad3_c")
    maths = sentence_ring(["derivative", "x^3", "", "", "x", "3*x^2"],
                          source="monad_mathematics")
    d = double_ring(lang, maths)
    return {"lang_ring": lang.slots, "maths_ring": maths.slots,
            "double_ring": d.slots, "double_weight": round(d.weight, 4),
            "reads_as": "The derivative of x^3 with respect to x is 3*x^2."}


if __name__ == "__main__":
    import json
    print(json.dumps(_worked_example(), indent=2, default=str))
