"""
Archimedes/Maths/mathspeak.py — render a maths expression as WORDS.

The maths .bin vocabularies were ingested from raw Wikipedia/arXiv text, so they
carry LaTeX fragments ("f_{1}(s)\\,f_{2}(t"), bibcodes and mojibake instead of
maths. This module is the tokeniser to redo them properly: a sympy expression
tree walked into an English word stream, built on the tier-0 floor
`Aff(1,R) = ADD ⋊ (SCALE × SIGN)`:

    ADD    a + b            "a plus b"        (and "minus" when a term is signed)
    SCALE  a * b  /  a / b  "a times b" / "a over b"
    SIGN   -a               "negative a"

Everything else (powers, roots, functions, calculus operators, relations) is a
named phrase on top of that floor.

    speak("F = m*a")                     -> "F equals m times a"
    speak("a = (-b*x - c)/x**2")         -> "a equals negative b times x minus c, all over x squared"
    speak_words(expr)                    -> ["F", "equals", "m", "times", "a"]

`build_mathwords.py` runs this over the whole researcher catalogue (base
formulae + every rearranged "solved for x" form) to emit a clean maths-words
corpus the monad ingest can rebuild holcus_monad_mathematics.bin from.
"""
from __future__ import annotations

from typing import List

import sympy as sp

try:
    from .mathengine import _parse                                # noqa: PLC0415
except ImportError:                                               # pragma: no cover
    from mathengine import _parse                                 # type: ignore

# ── small-number words ────────────────────────────────────────────────────────
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
         "eighty", "ninety"]
_GREEK = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
          "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
          "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega", "hbar",
          "nabla", "partial", "infinity"}
_FUNC = {
    "sin": "the sine of", "cos": "the cosine of", "tan": "the tangent of",
    "asin": "the arcsine of", "acos": "the arccosine of", "atan": "the arctangent of",
    "sinh": "the hyperbolic sine of", "cosh": "the hyperbolic cosine of",
    "tanh": "the hyperbolic tangent of", "exp": "the exponential of",
    "log": "the natural log of", "ln": "the natural log of", "Abs": "the absolute value of",
    "sign": "the sign of", "sqrt": "the square root of",
    "erf": "the error function of",
    "factorial": "the factorial of", "re": "the real part of", "im": "the imaginary part of",
    "conjugate": "the conjugate of",
}
# gamma / zeta / beta / eta are variable names far more often than the special
# functions in this catalogue — keep them out of _FUNC so they read as atoms.
_REL = {sp.StrictLessThan: "is less than", sp.LessThan: "is at most",
        sp.StrictGreaterThan: "is greater than", sp.GreaterThan: "is at least",
        sp.Ne: "is not equal to"}


def _int_words(n: int) -> str:
    if n < 0:
        return "negative " + _int_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + (("-" + _ONES[n % 10]) if n % 10 else "")
    if n < 1000:
        return _ONES[n // 100] + " hundred" + (
            " " + _int_words(n % 100) if n % 100 else "")
    return str(n)


def _number(x) -> str:
    if x == sp.oo:
        return "infinity"
    if x == -sp.oo:
        return "negative infinity"
    if isinstance(x, sp.Rational) and not x.is_Integer:
        p, q = x.p, x.q
        if (p, q) == (1, 2):
            return "one half"
        if p == 1:
            return "one " + _ordinal(q)
        return f"{_int_words(abs(p))} {_ordinal(q)}" + ("s" if abs(p) != 1 else "")
    if getattr(x, "is_Integer", False):
        return _int_words(int(x))
    return str(x).rstrip("0").rstrip(".") if "." in str(x) else str(x)


def _ordinal(q: int) -> str:
    return {2: "half", 3: "third", 4: "quarter", 5: "fifth", 6: "sixth",
            7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}.get(q, f"over {q}")


def _atom(name: str) -> List[str]:
    low = name.lower()
    if low in _GREEK:
        return [low]
    return [name]


# ── the walk ────────────────────────────────────────────────────────────────
def _w(e) -> List[str]:
    e = sp.sympify(e)

    if isinstance(e, sp.Equality):
        return _w(e.lhs) + ["equals"] + _w(e.rhs)
    for typ, phrase in _REL.items():
        if isinstance(e, typ):
            return _w(e.lhs) + phrase.split() + _w(e.rhs)

    if e.is_Number:
        return _number(e).split()
    if e.is_Symbol:
        return _atom(e.name)

    if isinstance(e, sp.Add):
        terms = list(e.args)
        out = _w(terms[0])
        for t in terms[1:]:
            neg = t.could_extract_minus_sign()
            out += ["minus" if neg else "plus"] + _w(-t if neg else t)
        return out

    if isinstance(e, sp.Mul):
        c, rest = e.as_coeff_Mul()
        sign = ""
        if c.is_negative:
            sign, c = "negative", -c
        # a fractional coefficient reads as a word ("one half g t squared"),
        # not a trailing "all over two"
        frac_lead: List[str] = []
        if c.is_Rational and not c.is_Integer and c.p == 1:
            frac_lead = _number(c).split()
            c = sp.Integer(1)
        num, den = [], []
        factors = ([] if c == 1 else [c]) + list(sp.Mul.make_args(rest))
        for f in factors:
            if f.is_Pow and f.exp.is_negative:
                den.append(sp.Pow(f.base, -f.exp))
            elif f.is_Rational and not f.is_Integer:
                if f.p != 1:
                    num.append(sp.Integer(f.p))
                den.append(sp.Integer(f.q))
            else:
                num.append(f)
        nums = num or [sp.Integer(1)]
        out = ([sign] if sign else []) + frac_lead
        if frac_lead and nums != [sp.Integer(1)]:
            out += ["times"]
        out += _join([_w(x) for x in nums], "times")
        if den:
            dtxt = _join([_w(x) for x in den], "times")
            if len(nums) > 1 or sign:
                out += [",", "all", "over"] + dtxt
            else:
                out += ["over"] + dtxt
        return out

    if isinstance(e, sp.Pow):
        b, ex = e.base, e.exp
        if ex == sp.Rational(1, 2):
            return ["the", "square", "root", "of"] + _paren(b)
        if ex == -1:
            return ["one", "over"] + _paren(b)
        if ex == 2:
            return _paren(b) + ["squared"]
        if ex == 3:
            return _paren(b) + ["cubed"]
        return _paren(b) + ["to", "the", "power"] + _w(ex)

    if isinstance(e, sp.Derivative):
        f = e.expr
        var = e.variables[0]
        order = len(e.variables)
        pre = {1: "the derivative", 2: "the second derivative",
               3: "the third derivative"}.get(order, f"the {order}th derivative")
        return pre.split() + ["of"] + _w(f) + ["with", "respect", "to"] + _w(var)

    if isinstance(e, sp.Integral):
        f = e.function
        lims = e.limits[0]
        if len(lims) == 3:
            x, a, b = lims
            return (["the", "integral", "from"] + _w(a) + ["to"] + _w(b) + ["of"]
                    + _w(f) + ["with", "respect", "to"] + _w(x))
        return (["the", "integral", "of"] + _w(f)
                + ["with", "respect", "to"] + _w(lims[0]))

    if isinstance(e, (sp.Sum, sp.Product)):
        word = "sum" if isinstance(e, sp.Sum) else "product"
        f = e.function
        x, a, b = e.limits[0]
        return (["the", word, "from"] + _w(a) + ["to"] + _w(b) + ["of"] + _w(f))

    head = type(e).__name__
    if head == "binomial":
        n, k = e.args
        return _w(n) + ["choose"] + _w(k)
    if head in _FUNC:
        inner = []
        for i, a in enumerate(e.args):
            if i:
                inner += ["and"]
            inner += _w(a)
        return _FUNC[head].split() + inner

    # fallback: function-name of args
    inner: List[str] = []
    for i, a in enumerate(e.args):
        if i:
            inner += ["and"]
        inner += _w(a)
    return [f"the {head.lower()} of"] + inner if inner else [head.lower()]


def _paren(b) -> List[str]:
    inner = _w(b)
    if b.is_Atom or (b.is_Pow and b.exp in (2, 3, sp.Rational(1, 2))):
        return inner
    if isinstance(b, (sp.Add, sp.Mul)):
        return ["the", "quantity"] + inner
    return inner


def _join(parts: List[List[str]], sep: str) -> List[str]:
    out: List[str] = []
    for i, p in enumerate(parts):
        if i:
            out.append(sep)
        out += p
    return out


# ── public ──────────────────────────────────────────────────────────────────
def speak_words(expr) -> List[str]:
    if isinstance(expr, str):
        expr = _parse(expr)
    return [t for t in _w(expr) if t]


def speak(expr) -> str:
    toks = speak_words(expr)
    s = " ".join(toks).replace(" ,", ",")
    return s[0:1].upper() + s[1:] if s else s


def speak_mathdef(md) -> str:
    """'<name>: <spoken expr>.'  — one clean maths-words sentence."""
    try:
        body = speak(md.expr)
    except Exception:                                             # noqa: BLE001
        body = md.expr
    return f"{md.name}: {body}."


def verify() -> dict:
    # sympy canonicalises commutative args, so a Mul's word order is its
    # sorted order, not the source order — assert structure, not the string.
    x, t = sp.symbols("x t")
    f = sp.Function("f")
    checks = [
        ("F = m*a", lambda s: s.lower() in ("f equals a times m", "f equals m times a")),
        ("a = F/m", lambda s: s.lower() == "a equals f over m"),
        ("E = m*c^2", lambda s: "c squared" in s and s.lower().startswith("e equals")),
        ("P*V = n*R*T", lambda s: "equals" in s and s.count("times") == 3),
        ("S = a/(1 - r)", lambda s: "over one minus r" in s),
        ("Integral(x^2, (x, 0, 5))",
         lambda s: s == "The integral from zero to five of x squared "
                        "with respect to x"),
        ("k = 2*S/(a1 + an)", lambda s: "all over a1 plus an" in s),
        (sp.Derivative(f(x), x),
         lambda s: s == "The derivative of the f of x with respect to x"),
        (sp.Eq(sp.Symbol("y"), sp.Rational(1, 2) * sp.Symbol("g") * t**2),
         lambda s: "one half" in s and "t squared" in s),
    ]
    out, ok = {}, True
    for src, test in checks:
        got = speak(src)
        out[str(src)] = got
        if not test(got):
            ok = False
    return {"ok": ok, "rendered": out}


if __name__ == "__main__":
    import json
    print(json.dumps(verify(), indent=2))
