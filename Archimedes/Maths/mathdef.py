r"""
Archimedes/Maths/mathdef.py — the C-fluent maths record.
========================================================
One record per equation. Flat fields, a one-line pipe grammar so the C harness
(`PtolC/monad_harness.c` — `mh_parse_mathdef()`, TODO) and the Python Face
speak the SAME data set.

    MATHDEF v1 | <id> | <category> | <name> | <expr> | <v1,v2,…> | <var:rung;…> | <var:unit;…> | <source>

Pipe-delimited; a literal `|` inside a field is escaped `\|`. `solvable_for`
rung values: symbolic | implicit | numeric | tabulated | none.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

GRAMMAR = ("MATHDEF v1 | <id> | <category> | <name> | <expr> | <v1,…> | "
           "<var:rung;…> | <var:unit;…> | <source>")
RUNGS = ("symbolic", "implicit", "numeric", "tabulated", "none")


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace("|", "\\|")


def _unesc(s: str) -> str:
    out, i, n = [], 0, len(s)
    while i < n:
        if s[i] == "\\" and i + 1 < n:
            out.append(s[i + 1])
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _split_pipes(line: str) -> List[str]:
    fields, cur, i, n = [], [], 0, len(line)
    while i < n:
        c = line[i]
        if c == "\\" and i + 1 < n:
            cur.append(line[i + 1])
            i += 2
        elif c == "|":
            fields.append("".join(cur).strip())
            cur = []
            i += 1
        else:
            cur.append(c)
            i += 1
    fields.append("".join(cur).strip())
    return fields


@dataclass
class MathDef:
    id: str
    category: str
    name: str
    expr: str
    variables: List[str] = field(default_factory=list)
    solvable_for: Dict[str, str] = field(default_factory=dict)
    units: Dict[str, str] = field(default_factory=dict)
    source: str = ""
    notes: List[str] = field(default_factory=list)

    def to_line(self) -> str:
        v = ",".join(self.variables)
        sf = ";".join(f"{k}:{val}" for k, val in self.solvable_for.items())
        un = ";".join(f"{k}:{val}" for k, val in self.units.items() if val)
        return " | ".join([
            "MATHDEF v1", _esc(self.id), _esc(self.category), _esc(self.name),
            _esc(self.expr), _esc(v), _esc(sf), _esc(un), _esc(self.source),
        ])

    @classmethod
    def parse_line(cls, line: str) -> "MathDef":
        f = _split_pipes(line)
        if not f or f[0] != "MATHDEF v1":
            raise ValueError(f"not a MATHDEF v1 line: {line[:40]!r}")
        _, mid, cat, name, expr, vs, sf, un, src = (f + [""] * 9)[:9]
        variables = [x for x in vs.split(",") if x]
        solvable = {}
        for part in sf.split(";"):
            if ":" in part:
                k, val = part.split(":", 1)
                solvable[k] = val
        units = {}
        for part in un.split(";"):
            if ":" in part:
                k, val = part.split(":", 1)
                units[k] = val
        return cls(id=mid, category=cat, name=name, expr=expr,
                   variables=variables, solvable_for=solvable, units=units,
                   source=src)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "category": self.category, "name": self.name,
                "expr": self.expr, "variables": self.variables,
                "solvable_for": self.solvable_for, "units": self.units,
                "source": self.source, "notes": self.notes}


def verify() -> Dict[str, Any]:
    md = MathDef(
        id="mech.newton_second", category="classical_mechanics",
        name="Newton's second law | the F=ma one", expr="F = m*a",
        variables=["F", "m", "a"],
        solvable_for={"F": "symbolic", "m": "symbolic", "a": "symbolic"},
        units={"F": "N", "m": "kg", "a": "m/s**2"},
        source="Newton; NIST")
    line = md.to_line()
    back = MathDef.parse_line(line)
    ok_round = back.to_line() == line
    ok_pipe = "\\|" in line and back.name == "Newton's second law | the F=ma one"
    ok_fields = (back.variables == ["F", "m", "a"]
                 and back.solvable_for["a"] == "symbolic"
                 and back.units["F"] == "N")
    return {"ok": ok_round and ok_pipe and ok_fields,
            "round_trip_identical": ok_round, "pipe_escaped": ok_pipe,
            "fields": ok_fields}


if __name__ == "__main__":
    print(GRAMMAR)
    print(verify())
    md = MathDef("test.x", "cat", "a name", "y = k*x", ["y", "k", "x"])
    print(md.to_line())
