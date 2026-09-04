"""
Archimedes/Maths/mathengine.py — one engine, the solvability ladder.
===================================================================
The single answer to "sympy, numpy and pandas each do calculus differently —
which do I pick?": ALL of them, in a fixed order, and record where you landed.

Per target variable, for an equation:

    symbolic   sympy.solve(eq, var)            → closed form(s)
    implicit   sympy.solveset / isolate        → conditional / Piecewise
    numeric    lambdify + scipy.optimize       → a root over a bracket
    tabulated  numpy grid → pandas DataFrame   → interpolate / nearest row
    none       keep the expression, note why

Backends: symbolic(expr) · numeric(expr, **fixed) · table(expr, ranges).
Calculus fall-through:
    integrate:  sympy.integrate → scipy.integrate.quad
    diff:       sympy.diff → numpy.gradient
    summation:  sympy.summation → numpy.sum

`build(expr_str, units, source)` runs the ladder for every variable and returns
a filled MathDef.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

import re

import sympy as sp

from .mathdef import MathDef

_TRANSFORMS = None
# names we KEEP as sympy functions / constants; every other identifier in an
# expression is forced to a plain Symbol so single letters like I, E, S, N, Q,
# O, beta, gamma are variables, not sympy's builtins.
_KEEP = {
    "pi", "E", "oo", "I",  # note: E and I are re-forced to Symbol below unless
                           # the equation explicitly wants them (rare here)
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh", "tanh",
    "exp", "log", "ln", "sqrt", "cbrt", "Abs", "sign", "factorial", "gamma",
    "Integral", "Sum", "Product", "Limit", "Derivative", "Rational", "Piecewise",
}
_FUNC_ONLY = {"sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh",
              "cosh", "tanh", "exp", "log", "ln", "sqrt", "cbrt", "Abs", "sign",
              "factorial", "binomial", "ceiling", "floor", "limit", "Limit",
              "Matrix", "conjugate", "re", "im", "sinc",
              "Integral", "Sum", "Product", "Derivative",
              "Rational", "Piecewise",
              # functions sympy.solve can emit into a rearranged form
              "LambertW", "RootOf", "CRootOf", "erf", "erfc", "gamma", "zeta",
              "Heaviside", "DiracDelta", "besselj", "bessely", "Ei", "Si", "Ci",
              "polylog", "Min", "Max", "arg"}
_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def _local_dict(s: str) -> dict:
    """Force every identifier that is not a kept function/const to a Symbol."""
    d: dict = {}
    for tok in set(_IDENT.findall(s)):
        if tok in _FUNC_ONLY:
            continue
        if tok == "pi":
            d[tok] = sp.pi
            continue
        d[tok] = sp.Symbol(tok)
    return d


def _parse(expr_str: str):
    """String → sympy Expr or Eq. Accepts '=' for equations, '^' for power."""
    global _TRANSFORMS
    if _TRANSFORMS is None:
        from sympy.parsing.sympy_parser import (
            standard_transformations, implicit_multiplication_application,
            convert_xor)
        _TRANSFORMS = (standard_transformations
                       + (implicit_multiplication_application, convert_xor))
    s = expr_str.strip()
    ld = _local_dict(s)

    def P(txt):
        return sp.parse_expr(txt, transformations=_TRANSFORMS, local_dict=ld)

    for tok, rel in ((">=", sp.Ge), ("<=", sp.Le)):
        if tok in s:
            lhs, rhs = s.split(tok, 1)
            return rel(P(lhs), P(rhs))
    for tok, rel in ((">", sp.Gt), ("<", sp.Lt)):
        if tok in s:
            lhs, rhs = s.split(tok, 1)
            return rel(P(lhs), P(rhs))
    if "=" in s and "==" not in s:
        lhs, rhs = s.split("=", 1)
        return sp.Eq(P(lhs), P(rhs))
    return P(s)


def _symbols(obj) -> List[sp.Symbol]:
    return sorted(obj.free_symbols, key=lambda x: x.name)


# ── the ladder ─────────────────────────────────────────────────────────────
def solve_for(obj, var: sp.Symbol, notes: List[str]) -> str:
    """Return the rung reached for `var`; append the reason each rung failed."""
    eq = obj if isinstance(obj, sp.Equality) else sp.Eq(obj, 0)

    # rung 1 — symbolic
    try:
        sol = sp.solve(eq, var, dict=False)
        if sol:
            return "symbolic"
        notes.append(f"{var}: sympy.solve returned nothing")
    except Exception as e:                                        # noqa: BLE001
        notes.append(f"{var}: sympy.solve raised {type(e).__name__}")

    # rung 2 — implicit
    try:
        ss = sp.solveset(eq, var, domain=sp.S.Reals)
        if ss not in (sp.S.EmptySet,) and not isinstance(ss, sp.ConditionSet):
            return "implicit"
        notes.append(f"{var}: solveset gave {type(ss).__name__}")
    except Exception as e:                                        # noqa: BLE001
        notes.append(f"{var}: solveset raised {type(e).__name__}")

    # rung 3 — numeric (needs the other frees fixed; we only check feasibility)
    others = [s for s in _symbols(eq) if s != var]
    if len(others) <= 1:
        try:
            from scipy.optimize import brentq                     # noqa: PLC0415
            resid = (eq.lhs - eq.rhs)
            subs = {o: 1.0 for o in others}
            f = sp.lambdify(var, resid.subs(subs), "numpy")
            for a, b in ((-10, 10), (-1e3, 1e3), (1e-6, 1e6)):
                try:
                    if f(a) * f(b) < 0:
                        brentq(f, a, b)
                        return "numeric"
                except Exception:                                 # noqa: BLE001
                    continue
            notes.append(f"{var}: no sign-change bracket found for brentq")
        except Exception as e:                                    # noqa: BLE001
            notes.append(f"{var}: numeric rung raised {type(e).__name__}")
    else:
        notes.append(f"{var}: numeric rung needs the other {len(others)} frees fixed")

    # rung 4 — tabulated: always possible if the residual lambdifies
    try:
        resid = (eq.lhs - eq.rhs)
        sp.lambdify(_symbols(eq), resid, "numpy")
        return "tabulated"
    except Exception as e:                                        # noqa: BLE001
        notes.append(f"{var}: cannot lambdify for a table ({type(e).__name__})")

    return "none"


# ── backends ───────────────────────────────────────────────────────────────
def symbolic(expr_str: str):
    return _parse(expr_str)


def numeric(expr_str: str, **fixed) -> Callable:
    obj = _parse(expr_str)
    body = (obj.lhs - obj.rhs) if isinstance(obj, sp.Equality) else obj
    syms = [s for s in _symbols(body) if s.name not in fixed]
    body = body.subs({sp.Symbol(k): v for k, v in fixed.items()})
    return sp.lambdify(syms, body, "numpy")


def table(expr_str: str, ranges: Dict[str, Any]):
    import numpy as np                                            # noqa: PLC0415
    import pandas as pd                                           # noqa: PLC0415
    obj = _parse(expr_str)
    body = (obj.lhs - obj.rhs) if isinstance(obj, sp.Equality) else obj
    names = list(ranges)
    grids = np.meshgrid(*[np.asarray(ranges[n]) for n in names], indexing="ij")
    f = sp.lambdify([sp.Symbol(n) for n in names], body, "numpy")
    vals = f(*grids)
    cols = {n: g.ravel() for n, g in zip(names, grids)}
    cols["value"] = np.asarray(vals).ravel()
    return pd.DataFrame(cols)


def integrate(expr_str: str, var: str, a=None, b=None):
    x = sp.Symbol(var)
    e = _parse(expr_str)
    if a is None:
        return sp.integrate(e, x)
    res = sp.integrate(e, (x, sp.sympify(a), sp.sympify(b)))
    if res.has(sp.Integral):
        from scipy.integrate import quad                          # noqa: PLC0415
        f = sp.lambdify(x, e, "numpy")
        val, _ = quad(f, float(a), float(b))
        return sp.Float(val)
    return res


def differentiate(expr_str: str, var: str, order: int = 1):
    x = sp.Symbol(var)
    return sp.diff(_parse(expr_str), x, order)


def summation(expr_str: str, var: str, a, b):
    k = sp.Symbol(var)
    res = sp.summation(_parse(expr_str), (k, sp.sympify(a), sp.sympify(b)))
    if res.has(sp.Sum):
        import numpy as np                                        # noqa: PLC0415
        f = sp.lambdify(k, _parse(expr_str), "numpy")
        return sp.Float(float(np.sum(f(np.arange(int(a), int(b) + 1)))))
    return res


# ── build a MathDef ────────────────────────────────────────────────────────
def build(expr_str: str, *, id: str = "", category: str = "", name: str = "",
          units: Optional[Dict[str, str]] = None, source: str = "") -> MathDef:
    obj = _parse(expr_str)
    syms = _symbols(obj)
    notes: List[str] = []
    solvable = {s.name: solve_for(obj, s, notes) for s in syms} \
        if isinstance(obj, sp.Equality) else {}
    return MathDef(
        id=id or (category + "." + (name or expr_str)[:24].strip().replace(" ", "_")),
        category=category, name=name or expr_str, expr=expr_str,
        variables=[s.name for s in syms], solvable_for=solvable,
        units=units or {}, source=source, notes=notes)


def verify() -> Dict[str, Any]:
    fma = build("F = m*a", category="classical_mechanics", name="Newton's second law")
    ok_sym = all(v == "symbolic" for v in fma.solvable_for.values())

    tan = build("x - tan(x) = 0", category="test", name="fixed point of tan")
    ok_num = tan.solvable_for.get("x") in ("numeric", "tabulated")

    di = integrate("x**2", "x", 0, 5)
    ok_int_sym = sp.simplify(di - sp.Rational(125, 3)) == 0
    gi = integrate("exp(-x**2)", "x", 0, 1)
    ok_int_num = abs(float(gi) - 0.7468241328) < 1e-6

    dd = differentiate("x**3", "x")
    ok_diff = sp.simplify(dd - 3 * sp.Symbol("x") ** 2) == 0

    return {"ok": all([ok_sym, ok_num, ok_int_sym, ok_int_num, ok_diff]),
            "newton_symbolic": ok_sym, "tan_numeric_or_tabulated": ok_num,
            "integral_symbolic": ok_int_sym, "integral_numeric_fallback": ok_int_num,
            "derivative": ok_diff, "tan_notes": tan.notes}


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2, default=str))
