"""
_generate.py — build the Archimedes Formulary from CANONICAL_MATHS.md.
=====================================================================
Equational-decomposition methodology (Alcubierre-in-reverse): for every
equation, pull each variable across the equals sign and keep the formula for
THAT variable too. `F = m*a` yields `F = m*a`, `m = F/a`, `a = F/m` — each a
first-class formula. A substantial part of engineering maths is exactly this:
one equation, solved for whichever single quantity you are missing.

Reads `Archimedes/CANONICAL_MATHS.md`, writes one static module per `###`
section into `researcher/<tier>/<domain>.py` (MathDef literals — importing the
library stays instant; the sympy work happens here, once).

    python -m Archimedes.Maths.researcher._generate            # write all
    python -m Archimedes.Maths.researcher._generate --dry      # report only
"""
from __future__ import annotations

import re
import signal
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Tuple

import sympy as sp

from ..mathengine import _parse

_SOLVE_TIMEOUT = 3          # seconds per sympy.solve call
# expressions we do not try to rearrange (slow / no clean closed form) — the
# base formula is still emitted; the solvability ladder in build() covers these.
_NO_REARRANGE = ("binomial(", "factorial(", "Integral(", "Sum(", "Product(",
                 "Derivative(", "Matrix(", "limit(")


@contextmanager
def _time_limit(seconds: int):
    def _raise(signum, frame):
        raise TimeoutError
    old = signal.signal(signal.SIGALRM, _raise)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)

_HERE = Path(__file__).resolve().parent
_MD = _HERE.parents[1] / "CANONICAL_MATHS.md"          # Archimedes/CANONICAL_MATHS.md

_ROW = re.compile(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*([\w-]+)\s*\|\s*$")

_TITLES = {
    "rf_microwave": "RF & Microwave", "qft": "Quantum Field Theory",
    "quantum_field_theory": "Quantum Field Theory",
    "quantum_mechanics": "Quantum Mechanics",
    "lagrangian_hamiltonian": "Lagrangian & Hamiltonian Mechanics",
    "differential_equations": "Differential Equations",
    "numerical_methods": "Numerical Methods",
    "electrical_power": "Electrical Power",
    "chemical_engineering": "Chemical Engineering",
    "thermodynamic_cycles": "Thermodynamic Cycles",
    "fluid_machinery": "Fluid Machinery",
    "strength_of_materials": "Strength of Materials",
    "signal_processing": "Signal Processing",
    "control_theory": "Control Theory",
    "vector_calculus": "Vector Calculus",
    "complex_analysis": "Complex Analysis",
    "heat_transfer": "Heat Transfer",
    "statistical_mechanics": "Statistical Mechanics",
    "classical_mechanics": "Classical Mechanics",
    "continuum_mechanics": "Continuum Mechanics",
    "fluid_dynamics": "Fluid Dynamics",
}


def _title(domain: str) -> str:
    return _TITLES.get(domain, domain.replace("_", " ").title())


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:40] or "eq"


def parse_md() -> List[Tuple[str, str, str, str, str]]:
    """-> [(tier, domain, name, expr, jurisdiction), ...]"""
    rows, tier, domain = [], None, None
    for ln in _MD.read_text().splitlines():
        if ln.startswith("## ") and not ln.startswith("### "):
            tier = ln[3:].strip()
        elif ln.startswith("### "):
            domain = ln[4:].strip()
        else:
            m = _ROW.match(ln)
            if not (m and tier in ("foundations", "physics", "engineering")):
                continue
            name, expr, jur = (g.strip() for g in m.groups())
            if expr == "expr" or not name.strip("-") or not expr.strip("-"):
                continue                                   # header / separator row
            rows.append((tier, domain, name, expr, jur))
    return rows


def _rearrangements(expr: str) -> List[Tuple[str, str]]:
    """-> [(var, 'var = solution'), ...] for every variable with a clean form."""
    if any(tok in expr for tok in _NO_REARRANGE):
        return []
    try:
        obj = _parse(expr)
    except Exception:
        return []
    if not isinstance(obj, sp.Equality):
        return []
    syms = sorted(obj.free_symbols, key=lambda s: s.name)
    if len(syms) > 6:
        return []
    out = []
    for v in syms:
        if obj.lhs == v and not obj.rhs.has(v):        # already isolated
            continue
        try:
            with _time_limit(_SOLVE_TIMEOUT):
                sols = sp.solve(obj, v, dict=False)
        except (TimeoutError, Exception):
            continue
        sols = [s for s in sols if not s.has(sp.I) or s.is_real is not False]
        # keep only compact closed forms
        sols = [s for s in sols if len(str(s)) <= 160 and not s.has(sp.Piecewise)]
        if not sols or len(sols) > 3:
            continue
        if len(sols) == 1:
            out.append((v.name, f"{v.name} = {sp.sstr(sols[0])}"))
        else:
            for i, s in enumerate(sols):
                out.append((f"{v.name}#{i}", f"{v.name} = {sp.sstr(s)}"))
    return out


_HEAD = '''\
"""{title} — {nbase} base formulae, {nre} rearrangements.
Generated by researcher/_generate.py from Archimedes/CANONICAL_MATHS.md —
equational decomposition: each equation solved for every variable with a
closed form. Do not edit by hand; re-run the generator.
"""
{marker}from ...mathdef import MathDef

CATEGORY = {cat!r}
PAGE = {{"title": {title!r}, "jurisdiction": {pj!r},
        "blurb": "{title}: {nbase} standard relations, each rearranged for "
                 "every variable that has a closed form ({nre} derived forms)."}}
JURISDICTION = {jur!r}

DEFS = [
'''


def _emit_def(md_id, cat, name, expr, variables, solvable) -> str:
    return (f"    MathDef(id={md_id!r}, category={cat!r}, name={name!r},\n"
            f"            expr={expr!r}, variables={variables!r},\n"
            f"            solvable_for={solvable!r}),\n")


def generate(dry: bool = False) -> Dict[str, int]:
    rows = parse_md()
    by_dom: Dict[Tuple[str, str], List] = {}
    for tier, domain, name, expr, jur in rows:
        by_dom.setdefault((tier, domain), []).append((name, expr, jur))

    stats = {"modules": 0, "base": 0, "rearranged": 0}
    for (tier, domain), items in by_dom.items():
        cat = domain
        jmap: Dict[str, str] = {}
        defs_src: List[str] = []
        nbase = nre = 0
        for name, expr, jur in items:
            base_id = f"{domain}.{_slug(name)}"
            try:
                obj = _parse(expr)
                variables = sorted(s.name for s in obj.free_symbols)
            except Exception:
                variables = []
            jmap[base_id] = jur
            defs_src.append(_emit_def(base_id, cat, name, expr, variables, {}))
            nbase += 1
            for tag, form in _rearrangements(expr):
                v = tag.split("#")[0]
                suffix = tag.replace("#", "_")
                rid = f"{base_id}__{suffix}"
                rname = f"{name} — solved for {v}"
                try:
                    rvars = sorted(s.name for s in _parse(form).free_symbols)
                except Exception:
                    rvars = []
                jmap[rid] = jur
                defs_src.append(_emit_def(rid, cat, rname, form, rvars, {}))
                nre += 1

        pj = items[0][2]
        # Navier-Stokes lands in fluid_dynamics; the marker lives only there.
        marker = ('__author__ = "rendier"\n'
                  '__dr' + 'crawford__ = "HOT"\n\n'
                  if domain == "fluid_dynamics" else "")
        src = _HEAD.format(title=_title(domain), cat=cat, pj=pj, marker=marker,
                           jur=jmap, nbase=nbase, nre=nre) \
            + "".join(defs_src) + "]\n"
        stats["modules"] += 1
        stats["base"] += nbase
        stats["rearranged"] += nre
        if dry:
            print(f"  {tier}/{domain}.py  base={nbase} rearranged={nre}")
        else:
            (_HERE / tier / f"{domain}.py").write_text(src)
    return stats


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    s = generate(dry=dry)
    print(f"{'(dry) ' if dry else ''}{s['modules']} modules, "
          f"{s['base']} base + {s['rearranged']} rearranged "
          f"= {s['base'] + s['rearranged']} formulae")
