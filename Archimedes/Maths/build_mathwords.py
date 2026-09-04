"""
Archimedes/Maths/build_mathwords.py — emit a clean maths-WORDS corpus.

Walks the researcher catalogue (every base formula + every rearranged
"solved for x" form — the 1/2-line equations) and renders each through
`mathspeak.speak`, producing one plain-English sentence per formula. This is
the corpus the monad ingest should rebuild holcus_monad_mathematics.bin from,
in place of the raw Wikipedia/arXiv text (LaTeX, bibcodes, mojibake) it
currently carries.

    python -m Archimedes.Maths.build_mathwords              # -> stdout
    python -m Archimedes.Maths.build_mathwords -o maths_words_corpus.txt

Each line:  "<name>: <spoken expression>. <jurisdiction> jurisdiction."
Sentences are the ingest unit; the vocabulary is ADD/SCALE/SIGN + number
words + the symbol names, nothing else.
"""
from __future__ import annotations

import argparse
import sys

try:
    from .mathspeak import speak
    from .researcher import catalog, by_category
except ImportError:                                              # pragma: no cover
    from mathspeak import speak                                  # type: ignore
    from researcher import catalog, by_category                  # type: ignore


def lines() -> list:
    out = []
    for md in catalog():
        try:
            body = speak(md.expr)
        except Exception as e:                                    # noqa: BLE001
            body = f"{md.expr}   [unspoken: {type(e).__name__}]"
        jur = (getattr(md, "jurisdiction", "") or "").strip()
        tail = f" {jur} jurisdiction." if jur else ""
        out.append(f"{md.name}: {body}.{tail}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", default="-", help="output file, or - for stdout")
    ap.add_argument("--stats", action="store_true", help="counts only")
    args = ap.parse_args()

    ls = lines()
    if args.stats:
        cats = by_category()
        print(f"{len(ls)} sentences across {len(cats)} categories")
        unspoken = sum(1 for l in ls if "[unspoken:" in l)
        print(f"{unspoken} did not render ({100 * unspoken / max(1, len(ls)):.1f}%)")
        return 0

    text = "\n".join(ls) + "\n"
    if args.out == "-":
        sys.stdout.write(text)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {len(ls)} sentences -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
