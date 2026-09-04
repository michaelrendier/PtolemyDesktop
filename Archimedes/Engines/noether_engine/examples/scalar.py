"""
noether_engine.examples.scalar — the two textbook checks, as callables.

    energy_momentum_real_scalar()  -> NoetherResult   (canonical T^μ_ν)
    number_current_complex_scalar() -> NoetherResult  (U(1) current)

Both must come back `conserved` on-shell; see the package `selftest()`.
"""
from __future__ import annotations

import sympy as sp

from .. import (NoetherEngine, coords, real_scalar, complex_scalar,
                klein_gordon_real, klein_gordon_complex, translation,
                u1_complex_scalar)

_M = sp.Symbol("m", positive=True)


def energy_momentum_real_scalar(nu: int = 0):
    x = coords(4)
    L = klein_gordon_real(real_scalar("phi", x), _M)
    return NoetherEngine(L, translation(nu)).derive_current()


def number_current_complex_scalar():
    x = coords(4)
    L = klein_gordon_complex(complex_scalar("phi", x), _M)
    return NoetherEngine(L, u1_complex_scalar()).derive_current()


if __name__ == "__main__":
    print(energy_momentum_real_scalar())
    print()
    print(number_current_complex_scalar())
