# archimedes_maths_v1 — the first Archimedes maths corpus (archived 2026-09-04)

The v1 attempt at giving Archimedes a body of maths: a Wikipedia LaTeX
scraper plus hand-written formula classes. Superseded by the v2 pipeline and
kept here for reference only — **nothing in the tree imports these**.

| file | what it was |
|---|---|
| `acquire.py` | the Math Crawler — scrape LaTeX from authoritative sources, write it into per-topic modules. Stalled on the LaTeX→sympy-string translator (the "I can't write it down" bug). |
| `wikiformulas.py` | stub target the crawler was meant to fill. |
| `Formula.py`, `math2.py`, `math3.py`, `MyMath.py` | hand-rolled `constant` / formula classes — constants, ad-hoc solved forms, `inspect`-driven glue. Overlapping drafts of the same idea. |
| `EverythingFormula.py` | the Tupper's-self-referential-formula toy (`turtle`). |
| `pydata.py` | a periodic-table dataclass. |

## Why archived

v2 replaced all of it:

- **`Archimedes/CANONICAL_MATHS.md`** — one curated list, `name | expr | jurisdiction`, no scraping.
- **`Archimedes/Maths/researcher/**`** — 38 modules generated from that list by
  `researcher/_generate.py`, with the equational decomposition (every variable
  pulled across `=`). 1739 formulae, imports instantly.
- **`Archimedes/Maths/mathengine.py`** — the solvability ladder
  (`symbolic → implicit → numeric → tabulated`), the single answer to
  "sympy/numpy/pandas each differ".
- **`Archimedes/Maths/mathdef.py`** — the C-fluent `MATHDEF v1 | …` record.

## Kept in place (still current, not archived)

`Maths/Constants.py`, `Maths/UnitVector.py` (→ also `Archimedes/UnitVector.py`),
`Archimedes/UniMath.py`, `Maths/LorenzStirling.py`, `Maths/GraphPlot.py`,
`Maths/ArchimedesShell.py`, `Maths/Sequences/`, `Maths/Series/`, and the
`Maths/Formula/` package (UFformulary data — a different thing from the moved
`Formula.py`).
