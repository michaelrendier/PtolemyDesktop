"""
Archimedes/parser.py — the Zork sentence parser, reproduced for maths.
=====================================================================
Infocom-style. Reproduced from the engineering reference
`VAPMIP/zork_parser.py` (do not import it), maths-tuned: the verb governs and
names a maths OPERATION; the rest of the sentence is an expression, a named
topic, and prepositional phrases (`from 0 to 5`, `with respect to x`, `for a`).

Philosophy, unchanged from the reference: vocabulary first, verb governs,
grammar is a table, unknown words fail loudly and helpfully. No hashing, no
learning — the parser is hardcoded context. It sits between raw user input and
the Archimedes Face's monad lookup.

    parser = ZorkParser()
    r = parser.parse("integrate x^2 from 0 to 5")
    # r.operation == 'integrate'  r.expr == 'x^2'  r.lo == '0'  r.hi == '5'

Author: Ptolemy Project / Archimedes Face
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ── the maths operations and their verb lists ───────────────────────────────
OPERATION_VERBS: Dict[str, List[str]] = {
    "state":        ["state", "define", "recall", "give", "tell", "what", "quote"],
    "evaluate":     ["evaluate", "eval", "compute", "calculate", "calc", "value"],
    "integrate":    ["integrate", "integral", "antiderivative", "quad"],
    "differentiate": ["differentiate", "derive", "derivative", "diff", "ddx"],
    "solve":        ["solve", "root", "roots", "isolate", "rearrange"],
    "factor":       ["factor", "factorise", "factorize"],
    "simplify":     ["simplify", "reduce", "collect"],
    "expand":       ["expand"],
    "limit":        ["limit", "lim"],
    "sum":          ["sum", "series", "summation", "sigma"],
    "analyse":      ["analyse", "analyze", "check", "examine", "inspect", "diagnose"],
    "convert":      ["convert", "express"],
    "help":         ["help", "list", "topics", "categories", "?"],
}
VERB_TO_OP: Dict[str, str] = {v: op for op, vs in OPERATION_VERBS.items() for v in vs}

# preposition phrases that carry structured maths fields
PREPS = frozenset([
    "from", "to", "with", "respect", "wrt", "for", "in", "of", "at", "as",
    "about", "over", "between",
])
# only "the" — in maths sentences "a", "an", "x", "n" are variables, not articles
ARTICLES = frozenset(["the"])

# a token run is an "expression" if it carries maths punctuation / digits
_EXPR_RE = re.compile(r"[0-9^*/+\-()=]|\bx\b|\bpi\b|\be\b|_|\\")

# rest-of-sentence templates (VERB is implicit first), for diagnostics
TEMPLATES = [
    (),                       # help / bare
    ("E",),                   # differentiate x^3
    ("N",),                   # state newton's second law
    ("E", "P", "N"),          # differentiate x^3 with respect to x
    ("E", "P", "N", "P", "N"),  # integrate x^2 from 0 to 5
    ("N", "P", "N"),          # solve F=m*a for a
]


@dataclass
class ParseResult:
    operation: str = "identity"
    verb_word: str = ""
    expr: Optional[str] = None      # the maths expression, verbatim
    topic: Optional[str] = None     # a named law / formula / category
    wrt: Optional[str] = None       # variable: diff / solve target
    lo: Optional[str] = None        # lower bound (integrate / sum)
    hi: Optional[str] = None        # upper bound
    raw: str = ""
    error: Optional[str] = None
    remainder: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_request(self) -> str:
        """A normalised request string for the Face / monad lookup."""
        if not self.ok:
            return ""
        bits = [self.operation]
        if self.expr:
            bits.append(self.expr)
        elif self.topic:
            bits.append(self.topic)
        if self.wrt:
            bits.append(f"wrt {self.wrt}")
        if self.lo is not None or self.hi is not None:
            bits.append(f"[{self.lo}..{self.hi}]")
        return " ".join(bits)

    def __repr__(self) -> str:
        if not self.ok:
            return f"ParseResult(ERROR: {self.error})"
        return (f"ParseResult({self.operation}, expr={self.expr!r}, topic={self.topic!r}, "
                f"wrt={self.wrt!r}, bounds=({self.lo},{self.hi}))")


class ZorkParser:
    """Infocom-style parser: verb-first, grammar-table, loud on the unknown."""

    def __init__(self, extra_verbs: Optional[Dict[str, str]] = None) -> None:
        self._verb_map = dict(VERB_TO_OP)
        if extra_verbs:
            self._verb_map.update(extra_verbs)
        self._last_expr: Optional[str] = None      # anaphor: "it"

    # ── public ─────────────────────────────────────────────────────────────
    def parse(self, text: str) -> ParseResult:
        text = (text or "").strip()
        if not text:
            return self._err(text, "I beg your pardon?")
        sentences = self._split_conjunctions(text)
        r = self._parse_one(sentences[0])
        if len(sentences) > 1:
            r.remainder = sentences[1:]
        return r

    def parse_all(self, text: str) -> List[ParseResult]:
        return [self._parse_one(s) for s in self._split_conjunctions((text or "").strip())]

    def add_verb(self, word: str, operation: str) -> None:
        self._verb_map[word.lower()] = operation

    def vocabulary(self) -> Dict[str, List[str]]:
        return dict(OPERATION_VERBS)

    def explain(self, r: ParseResult) -> str:
        if not r.ok:
            return f"PARSE ERROR: {r.error}"
        return "\n".join([
            f"Verb:   {r.verb_word!r} -> {r.operation}",
            f"Expr:   {r.expr or '(none)'}",
            f"Topic:  {r.topic or '(none)'}",
            f"wrt:    {r.wrt or '(none)'}",
            f"Bounds: {r.lo} .. {r.hi}",
            f"Request: {r.to_request()!r}",
        ])

    # ── private ────────────────────────────────────────────────────────────
    def _parse_one(self, text: str) -> ParseResult:
        tokens = self._tokenize(text)
        if not tokens:
            return self._err(text, "I beg your pardon?")

        # two-word verb ("look for") — not common here but keep the mechanism
        verb_op = None
        verb_used = tokens[0]
        if len(tokens) >= 2 and f"{tokens[0]} {tokens[1]}" in self._verb_map:
            verb_used = f"{tokens[0]} {tokens[1]}"
            verb_op = self._verb_map[verb_used]
            tokens = [verb_used] + tokens[2:]
        elif tokens[0] in self._verb_map:
            verb_op = self._verb_map[tokens[0]]
        else:
            return self._err(
                text,
                f"I don't know the word '{tokens[0]}'. Try: state, evaluate, "
                f"integrate, differentiate, solve, simplify, expand, limit, "
                f"sum, analyse, convert, help")

        rest = [t for t in tokens[1:] if t not in ARTICLES]
        # anaphor
        rest = [self._last_expr if t == "it" and self._last_expr else t for t in rest]

        r = ParseResult(operation=verb_op, verb_word=verb_used, raw=text)
        self._fill_slots(r, rest)
        if r.expr:
            self._last_expr = r.expr
        return r

    def _fill_slots(self, r: ParseResult, rest: List[str]) -> None:
        if not rest:
            return
        # carve prepositional phrases first
        # "... from A to B", "... with respect to X", "... wrt X", "... for X"
        i = 0
        head: List[str] = []
        while i < len(rest):
            t = rest[i]
            if t in ("wrt",) or (t == "with" and rest[i + 1:i + 3] == ["respect", "to"]):
                step = 1 if t == "wrt" else 3
                if i + step < len(rest):
                    r.wrt = rest[i + step]
                i += step + 1
                continue
            if t == "for" and i + 1 < len(rest):
                r.wrt = rest[i + 1]
                i += 2
                continue
            if t == "from" and i + 1 < len(rest):
                r.lo = rest[i + 1]
                i += 2
                continue
            if t == "to" and i + 1 < len(rest) and r.lo is not None:
                r.hi = rest[i + 1]
                i += 2
                continue
            if t == "between" and rest[i + 1:i + 4] and rest[i + 2] == "and":
                r.lo, r.hi = rest[i + 1], rest[i + 3]
                i += 4
                continue
            if t in ("of", "in", "as", "about", "over", "at"):
                i += 1
                continue
            head.append(t)
            i += 1

        phrase = " ".join(head).strip()
        if not phrase:
            return
        if _EXPR_RE.search(phrase):
            r.expr = phrase
        else:
            r.topic = phrase

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower().strip().rstrip("?.!")
        # keep maths punctuation attached; split on spaces and commas/semicolons
        toks = [t for t in re.split(r"[\s,;]+", text) if t]
        if toks and toks[0] not in self._verb_map:
            m = self._expand_prefix(toks[0])
            if m:
                toks[0] = m
        return toks

    def _expand_prefix(self, prefix: str) -> Optional[str]:
        if len(prefix) < 4:
            return None
        for w in self._verb_map:
            if w.startswith(prefix) or prefix.startswith(w[:6]):
                return w
        return None

    def _split_conjunctions(self, text: str) -> List[str]:
        parts = re.split(r"\s+and\s+", text, flags=re.IGNORECASE)
        if len(parts) <= 1:
            return [text]
        out = [parts[0].strip()]
        for p in parts[1:]:
            p = p.strip()
            if not p:
                continue
            first = p.split()[0].lower() if p.split() else ""
            if first in self._verb_map:
                out.append(p)
            else:
                out[-1] = out[-1] + " and " + p
        return out

    def _err(self, raw: str, msg: str) -> ParseResult:
        return ParseResult(operation="identity", verb_word="", raw=raw, error=msg)


def verify() -> Dict[str, Any]:
    p = ZorkParser()
    a = p.parse("integrate x^2 from 0 to 5")
    ok_int = a.operation == "integrate" and a.expr == "x^2" and a.lo == "0" and a.hi == "5"
    b = p.parse("differentiate x^3 with respect to x")
    ok_diff = b.operation == "differentiate" and b.expr == "x^3" and b.wrt == "x"
    c = p.parse("state newton's second law")
    ok_state = c.operation == "state" and c.topic == "newton's second law" and c.expr is None
    d = p.parse("solve F = m*a for a")
    ok_solve = d.operation == "solve" and d.wrt == "a" and (d.expr or "").replace(" ", "") == "f=m*a"
    e = p.parse("frobnicate the widget")
    ok_unknown = (not e.ok) and "don't know" in (e.error or "")
    f = p.parse("differentiate x^3 and integrate x^2 from 0 to 1")
    ok_conj = f.operation == "differentiate" and f.remainder and \
        f.remainder[0].startswith("integrate")
    return {"ok": all([ok_int, ok_diff, ok_state, ok_solve, ok_unknown, ok_conj]),
            "integrate_bounds": ok_int, "differentiate_wrt": ok_diff,
            "state_topic": ok_state, "solve_for": ok_solve,
            "unknown_verb_loud": ok_unknown, "conjunction": ok_conj}


if __name__ == "__main__":
    par = ZorkParser()
    for s in ("integrate x^2 from 0 to 5", "differentiate x^3 with respect to x",
              "state newton's second law", "solve F = m*a for a",
              "simplify (x^2 - 1)/(x - 1)", "limit sin(x)/x", "help",
              "frobnicate the widget"):
        r = par.parse(s)
        print(f">>> {s}")
        print("   ", par.explain(r).replace("\n", "\n    "))
    print(verify())
