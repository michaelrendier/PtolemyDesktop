#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
UnitVector.py — dimensional analysis as exponent-vector arithmetic.

The 7 SI base dimensions are the irreducible leaves; every named compound
unit (Newton, Joule, Watt, Tesla, ...) is a composite with an exact,
computable lineage back to them -- the same leaf/composite structure this
project already uses for numbers (prime/composite) and operators
(irreducible/derived). Multiplying quantities ADDS exponent vectors;
dividing SUBTRACTS; cancellation is a component landing on zero -- no
special-casing needed, it falls out of vector arithmetic.

UniMath.py (this directory) is the label-glyph layer, downstream of this:
once a UnitVector's non-zero components are known, that's what picks which
display glyph applies. This file is the algebra UniMath.py has no notion of.

Console notation renders through sympy (Mul/Pow of the 7 base symbols),
matching the curses UI's own sympy-based notation display -- not a bespoke
pretty-printer duplicating what sympy already renders correctly.
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Tuple, Optional
import sympy

# Order fixed: kg, m, s, A, K, mol, cd (SI base dimensions)
BASE_NAMES = ('kg', 'm', 's', 'A', 'K', 'mol', 'cd')
BASE_SYMBOLS = tuple(sympy.Symbol(n) for n in BASE_NAMES)


@dataclass(frozen=True)
class UnitVector:
    """A unit as a point in the Q^7 lattice of SI base-dimension exponents,
    plus a scalar conversion factor (how many of the coherent base-SI
    combination one unit of this equals). Composing units is vector
    arithmetic; a named compound is a fixed point in this lattice with a
    known lineage back to the 7 leaves."""

    exponents: Tuple[Fraction, ...] = field(default_factory=lambda: (Fraction(0),) * 7)
    scale: Fraction = Fraction(1)
    name: Optional[str] = None          # the compound's own name, if it has one
    lineage: Tuple[str, ...] = ()       # named units/leaves it was built FROM

    def __post_init__(self):
        if len(self.exponents) != 7:
            raise ValueError("UnitVector needs exactly 7 exponents (kg,m,s,A,K,mol,cd)")

    # -- vector arithmetic: this IS the whole engine ------------------------

    def __mul__(self, other: "UnitVector") -> "UnitVector":
        return UnitVector(
            tuple(a + b for a, b in zip(self.exponents, other.exponents)),
            self.scale * other.scale,
        )

    def __truediv__(self, other: "UnitVector") -> "UnitVector":
        return UnitVector(
            tuple(a - b for a, b in zip(self.exponents, other.exponents)),
            self.scale / other.scale,
        )

    def __pow__(self, n) -> "UnitVector":
        n = Fraction(n)
        new_scale = Fraction(float(self.scale) ** float(n)).limit_denominator(10 ** 9)
        return UnitVector(tuple(e * n for e in self.exponents), new_scale)

    @property
    def is_dimensionless(self) -> bool:
        return all(e == 0 for e in self.exponents)

    def matches(self, other: "UnitVector") -> bool:
        """Same physical setting -- same exponent vector, scale ignored
        (kg*m/s^2 and a differently-scaled force unit are still both a force)."""
        return self.exponents == other.exponents

    # -- sympy notation, for the curses console -----------------------------

    def to_sympy(self):
        expr = sympy.Integer(1)
        for sym, exp in zip(BASE_SYMBOLS, self.exponents):
            if exp != 0:
                expr *= sym ** sympy.Rational(exp.numerator, exp.denominator)
        return expr

    def pretty(self) -> str:
        if self.is_dimensionless:
            return "1  (dimensionless)"
        return sympy.pretty(self.to_sympy())

    def __repr__(self) -> str:
        label = f"{self.name} = " if self.name else ""
        return f"{label}{self.pretty()}"


# ── the 7 leaves ─────────────────────────────────────────────────────────

def base(dim: str) -> "UnitVector":
    i = BASE_NAMES.index(dim)
    exps = [Fraction(0)] * 7
    exps[i] = Fraction(1)
    return UnitVector(tuple(exps), Fraction(1), name=dim, lineage=())


KG, M, S, A, K, MOL, CD = (base(n) for n in BASE_NAMES)
DIMENSIONLESS = UnitVector(name='1')
LITER = UnitVector((M ** 3).exponents, Fraction(1, 1000), name='L', lineage=('m',))

# ── named compounds — exact SI derivations, lineage recorded ────────────
# Each line is a real generational step: built FROM the named unit(s) in
# its `lineage`, not asserted independently. Verified against standard SI
# derivations, not measured.

NEWTON  = UnitVector((KG * M / (S ** 2)).exponents, Fraction(1), name='N',  lineage=('kg', 'm', 's'))
JOULE   = UnitVector((NEWTON * M).exponents,        Fraction(1), name='J',  lineage=('N', 'm'))
WATT    = UnitVector((JOULE / S).exponents,         Fraction(1), name='W',  lineage=('J', 's'))
PASCAL  = UnitVector((NEWTON / (M ** 2)).exponents, Fraction(1), name='Pa', lineage=('N', 'm'))
COULOMB = UnitVector((A * S).exponents,             Fraction(1), name='C',  lineage=('A', 's'))
VOLT    = UnitVector((WATT / A).exponents,          Fraction(1), name='V',  lineage=('W', 'A'))
OHM     = UnitVector((VOLT / A).exponents,          Fraction(1), name='Ω',  lineage=('V', 'A'))
FARAD   = UnitVector((COULOMB / VOLT).exponents,    Fraction(1), name='F',  lineage=('C', 'V'))
WEBER   = UnitVector((VOLT * S).exponents,          Fraction(1), name='Wb', lineage=('V', 's'))
TESLA   = UnitVector((WEBER / (M ** 2)).exponents,  Fraction(1), name='T',  lineage=('Wb', 'm'))
HENRY   = UnitVector((WEBER / A).exponents,         Fraction(1), name='H',  lineage=('Wb', 'A'))

LEAVES = {n: base(n) for n in BASE_NAMES}
LINEAGE_TABLE = {
    'N': NEWTON, 'J': JOULE, 'W': WATT, 'Pa': PASCAL, 'C': COULOMB,
    'V': VOLT, 'Ω': OHM, 'F': FARAD, 'Wb': WEBER, 'T': TESLA, 'H': HENRY,
    **LEAVES,
}


def trace_lineage(u: "UnitVector", depth: int = 0) -> str:
    """A unit's generational lineage back to the 7 leaves, as a tree."""
    label = u.name or u.pretty()
    lines = [f"{'  ' * depth}{label}"]
    for parent_name in u.lineage:
        if parent_name in BASE_NAMES:
            lines.append(f"{'  ' * (depth + 1)}{parent_name}  (leaf)")
        else:
            parent = LINEAGE_TABLE.get(parent_name)
            if parent is not None:
                lines.append(trace_lineage(parent, depth + 1))
    return "\n".join(lines)


if __name__ == '__main__':
    print("=== UnitVector: dimensional analysis as exponent-vector arithmetic ===\n")

    print("Tesla's lineage:")
    print(trace_lineage(TESLA))
    print("\nJoule's lineage:")
    print(trace_lineage(JOULE))

    print("\n--- Cancellation, not asserted -- run and checked ---")
    concentration = MOL / LITER
    print(f"concentration = mol/L = {concentration!r}")
    recombined = concentration * LITER
    print(f"concentration * L    = {recombined!r}")
    print(f"exponents match MOL exactly: {recombined.exponents == MOL.exponents}")
    print(f"scale matches MOL exactly:   {recombined.scale == MOL.scale}")

    print("\n--- Joule really is kg*m^2*s^-2, checked against its own build path ---")
    direct = KG * (M ** 2) / (S ** 2)
    print(f"kg*m^2/s^2 exponents == Joule's exponents: {direct.exponents == JOULE.exponents}")
