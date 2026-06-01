"""
Ainulindalë — The Secret Fire Face of Ptolemy
==============================================
Standard Model of Neural Network Information Propagation (SMNNIP)

Submodules:
  core/        — SMNNIP derivation, lagrangian, inversion engines
  console/     — curses SymPy proof engine GUI
  neural_network/ — full tower implementations
  sonification/   — Ainulindalë sonification engines
  substrate/   — SMNNT pure substrate
  first_age/   — First Age hyperindex
  gemini/      — Gemini EHS integration
  tower/       — Full tower variants

Author: O Captain My Captain + Claude (Anthropic)
Date: April 2026 — First Age
"""

# Core engine convenience imports
try:
    from .core.smnnip_derivation_pure import (
        SMNNIPDerivationEngine,
        FieldState,
        Algebra,
        make_element,
        RealEl, ComplexEl, QuatEl, OctEl,
    )
    from .core.smnnip_inversion_engine import (
        PhysicalConstants,
        GradientFlow,
        InversionMap,
        RecursionAttractor,
        get_observer,
    )
    _CORE_AVAILABLE = True
except Exception as _e:
    _CORE_AVAILABLE = False
    _CORE_ERROR = str(_e)

__version__ = '1.0.0-first-age'
