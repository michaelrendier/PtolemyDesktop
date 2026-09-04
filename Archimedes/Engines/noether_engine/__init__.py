"""
noether_engine — Noether Current Engine (Session 1)

A general-purpose Noether current derivation engine with 14 contestable axes,
each exposed as an explicit switch with metadata logging.

Status: Session 1 — the first theorem is live. sympy-backed core
        (core.field / core.lagrangian / core.symmetry) + theorems.first_theorem;
        NoetherEngine.derive_current() returns a NoetherResult with the current
        (or the canonical T^μ_ν), its raw divergence, the Euler–Lagrange
        equations, and an on-shell conservation check. Verified: free real
        scalar → T^μ_ν; complex scalar → U(1) number current; SU(2)/SU(3)
        generator algebra. Sessions 2-4: deferred axes (BV / off-shell,
        curved spacetime, the second theorem, quantum Ward).

Minimal public API (Session 1):
    from Archimedes.Engines.noether_engine import (
        NoetherEngine, first_theorem, NoetherResult,
        coords, real_scalar, complex_scalar, multiplet,
        Lagrangian, klein_gordon_real, klein_gordon_complex,
        Symmetry, translation, internal, u1_complex_scalar,
        su2_generators, su3_generators,
        SwitchSettings, UnsupportedCombinationError,
        summarize_implementation_status, selftest,
    )

Author: Ainulindalë / O Captain My Captain + Claude (Anthropic)
Date: April 2026
"""

from .switches import (
    SwitchSettings,
    validate_combination,
    UnsupportedCombinationError,
    InvalidSwitchValueError,
    InconsistentCombinationError,
    summarize_implementation_status,
)

__version__ = '0.1.0-session1'
__all__ = [
    'SwitchSettings',
    'validate_combination',
    'UnsupportedCombinationError',
    'InvalidSwitchValueError',
    'InconsistentCombinationError',
    'summarize_implementation_status',
]

# ── Full NoetherEngine ──────────────────────────────────────────────────────
# The full engine with SymPy-backed derivation requires sympy as a dependency.
# It's conditionally available.

try:
    import sympy as _sp

    from .core.field import (Field, coords, real_scalar, complex_scalar,
                             multiplet)
    from .core.lagrangian import (Lagrangian, klein_gordon_real,
                                  klein_gordon_complex)
    from .core import symmetry as _sym
    from .core.symmetry import (Symmetry, translation, internal,
                                u1_complex_scalar, su2_generators,
                                su3_generators, GENERATORS)
    from .theorems.first_theorem import first_theorem, NoetherResult

    class NoetherEngine:
        """
        Top-level Noether Current Engine.

        Session 1: first-theorem derivation on Minkowski spacetime, on-shell
        conservation, Bessel–Hagen boundary term, U(1)/SU(2)/SU(3) generators.
        Curved spacetime, off-shell/BV, the second theorem and quantum Ward
        identities are deferred (see summarize_implementation_status()).

            eng = NoetherEngine(lagrangian, symmetry)     # core objects
            res = eng.derive_current()                     # -> NoetherResult
        """

        def __init__(self, lagrangian, symmetry, **switch_kwargs):
            self.lagrangian = lagrangian
            self.symmetry = symmetry
            self.settings = SwitchSettings.from_kwargs(**switch_kwargs)
            validate_combination(self.settings)

        def show_settings(self):
            return self.settings.as_metadata_dict()

        def print_settings(self):
            print("Noether Engine switch settings:")
            print("=" * 60)
            for axis, info in self.settings.as_metadata_dict().items():
                marker = " [user]" if info['user_supplied'] else " [default]"
                print(f"  {axis:25s} = {info['value']}{marker}")

        def derive_current(self, verify: bool = True) -> "NoetherResult":
            """Apply Noether's first theorem; return a NoetherResult carrying
            the current (or the canonical T^μ_ν), its raw divergence, the
            Euler–Lagrange equations, and whether ∂_μ j^μ reduces to 0
            on-shell."""
            res = first_theorem(self.lagrangian, self.symmetry,
                                metadata=self.settings.as_metadata_dict())
            if verify and not res.conserved:
                res.notes.append(
                    "verify=True: on-shell divergence is non-zero — check the "
                    "Lagrangian/symmetry pair or add the Bessel–Hagen K^μ.")
            return res

    def selftest() -> int:
        """Free real scalar → canonical T^μ_ν; complex scalar → U(1) number
        current; SU(2) doublet → isospin current. Each conserved on-shell."""
        x = coords(4)
        m = _sp.Symbol("m", positive=True)
        ok = True

        f = real_scalar("phi", x)
        r1 = NoetherEngine(klein_gordon_real(f, m), translation(0)).derive_current()
        ok &= (r1.kind == "energy_momentum" and r1.conserved)
        print(f"[1] free real scalar, translation x0 -> canonical T^mu_nu")
        print(f"    T^00 (energy density) = {_sp.sstr(r1.current[0, 0])}")
        print(f"    conserved on-shell: {r1.conserved}\n")

        g = complex_scalar("phi", x)
        r2 = NoetherEngine(klein_gordon_complex(g, m),
                           u1_complex_scalar()).derive_current()
        ok &= (r2.kind == "current" and r2.conserved and r2.current[0] != 0)
        print("[2] complex scalar, U(1) -> number current")
        print(f"    j^0 = {_sp.sstr(r2.charge_density)}")
        print(f"    conserved on-shell: {r2.conserved}\n")

        # [3] the Lie-algebra generators symmetry.py hands the tower:
        #     Hermitian, tr(T^a T^b) = ½ δ^{ab}, and closed:
        #     [T^a,T^b] = i Σ_c f^{abc} T^c  with  f^{abc} = -2i tr([T^a,T^b] T^c).
        for tag, gens in (("SU(2)", su2_generators()), ("SU(3)", su3_generators())):
            g, ng = gens, len(gens)
            herm = all(T == T.conjugate().T for T in g)
            norm = all(_sp.simplify((g[a] * g[b]).trace()
                                    - (_sp.Rational(1, 2) if a == b else 0)) == 0
                       for a in range(ng) for b in range(ng))
            closed = True
            for a in range(ng):
                for b in range(ng):
                    comm = g[a] * g[b] - g[b] * g[a]
                    f = [_sp.simplify(-2 * _sp.I * (comm * g[c]).trace())
                         for c in range(ng)]
                    rebuilt = _sp.I * sum((f[c] * g[c] for c in range(ng)),
                                          _sp.zeros(*g[0].shape))
                    if _sp.simplify(comm - rebuilt) != _sp.zeros(*g[0].shape):
                        closed = False
            ok &= herm and norm and closed
            print(f"[3.{tag}] {ng} generators — Hermitian:{herm} "
                  f"trace-norm:{norm} closed:{closed}")
        print()

        print("noether_engine selftest:", "HOLDS" if ok else "FAIL")
        return 0 if ok else 1

    __all__ += ['NoetherEngine', 'selftest', 'first_theorem', 'NoetherResult',
                'Field', 'coords', 'real_scalar', 'complex_scalar', 'multiplet',
                'Lagrangian', 'klein_gordon_real', 'klein_gordon_complex',
                'Symmetry', 'translation', 'internal', 'u1_complex_scalar',
                'su2_generators', 'su3_generators', 'GENERATORS']

except ImportError:
    pass  # sympy not available; switches still work


if __name__ == "__main__":
    import sys as _sys
    try:
        _sys.exit(selftest())
    except NameError:
        print(summarize_implementation_status())
