# Archimedes — the chainmail document model

**Status: experiment, stubbed.** `Archimedes/chainmail.py` carries the shapes
and one worked example; `chainmail_line()` and `persian_weave_3_1()` raise
`NotImplementedError`. This page is the written-down design so the idea stops
being un-writable.

## The build

| unit | is | from |
|---|---|---|
| **word** | a strut filler | the granular monad, folded |
| **sentence** | a **double box-kite ring** | one ring from `monad3_c.bin` (sentence construction) + one ring from `monad_mathematics.bin` (granular maths vocabulary), the **combination weighted heavier** — the overlap of the two rings carries the extra weight |
| **paragraph** | a **line of chainmail** | ring sentences collected in ring "shapes"; each ring links to its neighbours through shared struts |
| **document** | the **3/1 Persian Chainmaille pattern** | chainmail lines stitched 3-carried-by-1 |

## Why two rings

A box-kite ring is the 6-strut zero-divisor ring used elsewhere in the
framework (`ValaQuenta/wiki/pencil_hyperstring.md`, the GenerationalLineage
Operator Tree). The Archimedes Face builds a maths sentence by overlaying two
of them strut-for-strut:

- the **language ring** — how a sentence is put together (subject, relation,
  object, qualifier, …), drawn from `monad3_c.bin`;
- the **maths ring** — the granular terms that fill those roles (`derivative`,
  `x^3`, `with respect to`, `x`, `3*x^2`), drawn from `monad_mathematics.bin`.

Struts where **both** rings are filled become `(lang, maths)` pairs and take
the heavier `combo_weight` (default φ); struts where only one ring is filled
keep that filler at its own weight. `double_ring(lang, maths)` in
`chainmail.py` does exactly this, as a stub.

## Worked example

```
lang_ring  : the | of  | with | respect | to | is
maths_ring : derivative | x^3 | — | — | x | 3*x^2
double     : (the,derivative) | (of,x^3) | with | (respect,—) | (to,x) | (is,3*x^2)
reads as   : "The derivative of x^3 with respect to x is 3*x^2."
```

## Next build

- decode the `monad3_c.bin` packed word table so real sentence-construction
  rings come from the bin, not hardcoded templates (mirror
  `VAPMIP/monad_bin/repack.py`);
- `chainmail_line()` — link `double_ring` sentences through two shared struts;
- `persian_weave_3_1()` — the 3-in-1 document stitch;
- this is the locus for the granularity need/not-need experiments.
