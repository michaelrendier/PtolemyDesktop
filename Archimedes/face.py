"""
Archimedes/face.py — the robotic Professorial chat bot.
======================================================
A literal chat bot: NOT a thinking model, NOT predictive. It parses a sentence
(`Archimedes/parser.py`, an Infocom parser), decides whether the question is
established maths/physics it covers, and if so builds a LITERAL response —
an operation construction ("the derivative of x³ w.r.t. x is 3·x²") or an
analysis-result sentence — from hardcoded sentence templates filled with terms
from the weighted bins.

Two bins (already weighted; read as-is, no hashing):
    monad3_c.bin          — sentence constructions  (read in place, header only
                            for now; templates carry the constructions until the
                            packed reader lands)
    monad_mathematics.bin — granular maths vocabulary  (copied into Archimedes/;
                            the Face "controls" this copy)

The Face does not compute while speaking. Where a value is needed it makes ONE
deterministic `Archimedes.Maths.mathengine` call and phrases the result.

    face = ArchimedesFace()
    face.answer("differentiate x^3")
    # "The derivative of x^3 with respect to x is 3*x**2."
    face.answer("prove the Ainulindale conjecture")   # -> None  (Ptolemy keeps it)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from .parser import ZorkParser, ParseResult
from . import monadbin

_HERE = Path(__file__).resolve().parent
_PLACE = _HERE.parents[1]

# default bin locations
MATHS_BIN = _HERE / "monad_mathematics.bin"
MATHS_BIN_SRC = _PLACE / "PTorrent/bin_archive/clean/monad_mathematics.bin"
SENTENCE_BIN = Path(os.environ.get(
    "ARCHIMEDES_MONAD3C", _PLACE / "VAPMIP/PtolC/monad3_c.bin"))

# operations the Face will answer; anything else -> None (Ptolemy keeps it)
_MATHS_OPS = {"state", "evaluate", "integrate", "differentiate", "solve",
              "factor", "simplify", "expand", "limit", "sum", "convert", "help"}
# keywords that mark a question as framework ("engineered-operator") maths
_FRAMEWORK = ("ainulindale", "engineered operator", "0_rb", "sigma_rb", "box-kite",
              "box kite", "zero divisor", "generational lineage", "emerger",
              "sedenion facet", "oblique gear", "two trees")


def _supers(s: str) -> str:
    """x**3 -> x³, light cosmetic only."""
    m = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵",
         "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    out, i = [], 0
    while i < len(s):
        if s[i:i + 2] == "**" and i + 2 < len(s) and s[i + 2].isdigit():
            j = i + 2
            run = ""
            while j < len(s) and s[j].isdigit():
                run += s[j]
                j += 1
            out.append("".join(m[c] for c in run))
            i = j
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


class ArchimedesFace:
    """The Professor. Robotic. Deterministic: same question -> same answer."""

    def __init__(self, maths_bin: str | Path = MATHS_BIN,
                 sentence_bin: str | Path = SENTENCE_BIN) -> None:
        self.parser = ZorkParser()
        self.sentence_forms = monadbin.load_sentence_forms(sentence_bin) \
            if Path(sentence_bin).exists() else None
        src = maths_bin if Path(maths_bin).exists() else MATHS_BIN_SRC
        self.maths_vocab = monadbin.load_maths(src) if Path(src).exists() else None
        self._granular_loaded = self.maths_vocab is not None

    # ── the one entry point ───────────────────────────────────────────────
    def answer(self, text: str) -> Optional[str]:
        low = (text or "").lower()
        if any(k in low for k in _FRAMEWORK):
            return None                                # framework maths — Ptolemy keeps it
        pr = self.parser.parse(text)
        if not pr.ok:
            return None                                 # not a maths command — Ptolemy keeps it
        if pr.operation not in _MATHS_OPS:
            return None
        if self.needs_granularity(pr):
            self._ensure_granular()
        return self._construct(pr)

    def needs_granularity(self, pr: ParseResult) -> bool:
        return pr.operation in {"state", "convert"} or bool(pr.topic)

    def _ensure_granular(self) -> None:
        if not self._granular_loaded and MATHS_BIN_SRC.exists():
            self.maths_vocab = monadbin.load_maths(MATHS_BIN_SRC)
            self._granular_loaded = True

    # ── literal construction (templates now; monad3_c enrichment later) ────
    def _construct(self, pr: ParseResult) -> str:
        op = pr.operation
        from .Maths import mathengine as ME

        try:
            if op == "help":
                return ("I state, evaluate, integrate, differentiate, solve, "
                        "factor, simplify, expand, take limits and sums, and "
                        "convert units. Ask e.g. 'integrate x^2 from 0 to 5'.")

            if op == "differentiate" and pr.expr:
                var = pr.wrt or "x"
                d = ME.differentiate(pr.expr, var)
                return _supers(f"The derivative of {pr.expr} with respect to {var} is {d}.")

            if op == "integrate" and pr.expr:
                var = pr.wrt or "x"
                if pr.lo is not None and pr.hi is not None:
                    val = ME.integrate(pr.expr, var, pr.lo, pr.hi)
                    return _supers(f"The definite integral of {pr.expr} with respect "
                                   f"to {var} from {pr.lo} to {pr.hi} is {val}.")
                anti = ME.integrate(pr.expr, var)
                return _supers(f"An antiderivative of {pr.expr} with respect to "
                               f"{var} is {anti} + C.")

            if op == "sum" and pr.expr:
                var = pr.wrt or "k"
                if pr.lo is not None and pr.hi is not None:
                    val = ME.summation(pr.expr, var, pr.lo, pr.hi)
                    return _supers(f"The sum of {pr.expr} for {var} from {pr.lo} "
                                   f"to {pr.hi} is {val}.")

            if op in ("simplify", "factor", "expand") and pr.expr:
                import sympy as sp                                 # noqa: PLC0415
                e = ME.symbolic(pr.expr)
                fn = {"simplify": sp.simplify, "factor": sp.factor,
                      "expand": sp.expand}[op]
                return _supers(f"{pr.expr} {op}s to {fn(e)}.")

            if op == "limit" and pr.expr:
                import sympy as sp                                 # noqa: PLC0415
                var = pr.wrt or "x"
                pt = pr.lo if pr.lo is not None else 0
                lim = sp.limit(ME.symbolic(pr.expr), sp.Symbol(var), sp.sympify(pt))
                return _supers(f"The limit of {pr.expr} as {var} → {pt} is {lim}.")

            if op == "solve" and pr.expr and pr.wrt:
                import sympy as sp                                 # noqa: PLC0415
                sols = sp.solve(ME.symbolic(pr.expr), sp.Symbol(pr.wrt))
                rhs = ", ".join(str(s) for s in sols) if sols else "no closed form"
                return _supers(f"Solving {pr.expr} for {pr.wrt}: {pr.wrt} = {rhs}.")

            if op == "state" and pr.topic:
                return self._state_topic(pr.topic, pr.wrt)

            if op == "evaluate" and pr.expr:
                import sympy as sp                                 # noqa: PLC0415
                return _supers(f"{pr.expr} = {sp.N(ME.symbolic(pr.expr))}.")

        except Exception as e:                                     # noqa: BLE001
            return (f"I could not carry that out ({type(e).__name__}). "
                    f"Rephrase, or check the expression '{pr.expr}'.")

        return None

    def _state_topic(self, topic: str, wrt: Optional[str] = None) -> Optional[str]:
        try:
            import re                                              # noqa: PLC0415
            from .Maths.researcher import find_by_name             # noqa: PLC0415
            base = re.sub(r"\s+(solved|for|rearranged)\s*$", "", topic.strip())
            # "state the quadratic formula for a" -> the __a decomposed form;
            # fall back to the base equation if the rearrangement isn't listed
            md = (find_by_name(f"{base} solved for {wrt}") if wrt else None) \
                or find_by_name(base)
            if md:
                src = f"  (source: {md.source})" if md.source else ""
                return _supers(f"{md.name}: {md.expr}{src}.")
        except Exception:                                          # noqa: BLE001
            pass
        # No catalogued formula -> None, Ptolemy keeps it (the file's own
        # stated contract). There WAS a fallback here that flagged a topic
        # as "in the maths vocabulary" whenever the LAST WORD of the topic
        # matched anywhere in the 9MB scraped monad_mathematics.bin corpus —
        # far too weak a bar (arXiv text mentions "internet", "color",
        # nearly any noun) to gate real conversation into a dead-end
        # placeholder ("the named-formula catalogue is not built yet")
        # instead of falling through to Ptolemy. Confirmed live: "what are
        # you watching on the internet?" and "what is your favorite
        # color?" were both hijacked this way, because OPERATION_VERBS
        # also aliases bare "what" to "state" (parser.py) — every "what
        # ...?" question reaches here. Removed rather than tightened: a
        # last-word corpus hit is not evidence of anything, and the
        # catalogue this was meant to gate ("named-formula catalogue")
        # does not exist yet regardless.
        return None


def verify() -> Dict[str, Any]:
    f = ArchimedesFace()
    d = f.answer("differentiate x^3")
    ok_d = d is not None and "derivative of x" in d and "x²" in d and "3" in d
    i = f.answer("integrate x^2 from 0 to 5")
    ok_i = i is not None and "125/3" in i.replace(" ", "")
    n = f.answer("prove the Ainulindale conjecture")
    ok_n = n is None
    det = f.answer("differentiate x^3") == d
    ok_bins = f.maths_vocab is not None and f.sentence_forms is not None \
        and f.sentence_forms.magic_ok
    return {"ok": all([ok_d, ok_i, ok_n, det, ok_bins]),
            "differentiate": ok_d, "integrate_definite": ok_i,
            "framework_declined": ok_n, "deterministic": det,
            "both_bins_open": ok_bins, "sample": d}


if __name__ == "__main__":
    import json
    fa = ArchimedesFace()
    for q in ("differentiate x^3", "integrate x^2 from 0 to 5",
              "simplify (x^2 - 1)/(x - 1)", "limit sin(x)/x",
              "solve F = m*a for a", "help",
              "prove the Ainulindale conjecture"):
        print(f">>> {q}\n    {fa.answer(q)}")
    print(json.dumps(verify(), indent=2, default=str))
