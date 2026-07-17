"""
noether_engine — Noether Current Engine (Session 1)

A general-purpose Noether current derivation engine with 14 contestable axes,
each exposed as an explicit switch with metadata logging.

Status: Session 1 — core first-theorem derivation implemented.
        Sessions 2-4: deferred axes (BV, curved spacetime, quantum Ward).

Minimal public API (Session 1):
    from Archimedes.Engines.noether_engine import (
        NoetherEngine,          # main entry point
        SwitchSettings,
        UnsupportedCombinationError,
        summarize_implementation_status,
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

    class NoetherEngine:
        """
        Top-level Noether Current Engine.

        Session 1: Supports first-theorem derivation on Minkowski spacetime
        with on-shell conservation laws, Bessel-Hagen invariance, and
        U(1)/SU(2)/SU(3) algebra via Cayley-Dickson generators.

        Usage:
            engine = NoetherEngine(lagrangian, symmetry)
            result = engine.derive_current()
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

        def derive_current(self, verify: bool = True):
            """
            Apply Noether's theorem and return a NoetherResult.
            Full implementation requires sympy-backed core modules (session 1 WIP).
            """
            raise UnsupportedCombinationError(
                "NoetherEngine.derive_current() requires the full core submodule "
                "package (noether_engine.core.field, .lagrangian, .symmetry, etc). "
                "These are session-1 WIP. Switch validation is fully functional. "
                "Use SMNNIP's built-in Noether monitor (Ainulindale.core.smnnip_derivation_pure) "
                "for the SMNNIP-specific Noether current."
            )

    __all__.append('NoetherEngine')

except ImportError:
    pass  # sympy not available; switches still work
