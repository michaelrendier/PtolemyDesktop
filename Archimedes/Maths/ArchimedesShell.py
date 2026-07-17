#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArchimedesShell — /math Subshell
===================================
Archimedes Face

Provides the /math interactive shell inside PtolShell.
Triggered by: face archimedes  OR  /math prefix in Ptolemy mode.

Features:
  - SymPy REPL (symbols auto-created, LaTeX output optional)
  - Direct access to Archimedes Maths modules
  - LorenzStirling engine access
  - Results piped to PtolBus CH_FACE_EVENT for Tuning Display
  - Active mode: long-running computations run in a thread

Namespace auto-loaded:
  sp               — sympy
  symbols()        — sympy.symbols
  x,y,z,t,n       — pre-declared symbols
  calc             — Calculus()
  ls               — LorenzStirling()
  plot()           — GraphPlot wrapper

Usage (from PtolShell /math mode):
    > integrate(sin(x), x)
    > diff(exp(x**2), x)
    > ls.classify(0.5+0.3j)
    > help_math()

Settings hook → Archimedes > Shell settings tab.
"""

import sys
import code
import threading
from io import StringIO
from typing import Optional

# ── Settings ─────────────────────────────────────────────────────────────────
SHELL_SETTINGS = {
    "latex_output":       False,   # render results as LaTeX string
    "auto_simplify":      True,    # run sp.simplify on results
    "precision":          15,      # sp.N precision
    "timeout_s":          10,      # thread timeout for long calcs
}


def _build_namespace() -> dict:
    """Build the math REPL namespace."""
    ns = {}

    # ── SymPy ─────────────────────────────────────────────────────────────
    try:
        import sympy as sp
        from sympy import (
            symbols, Symbol, Function,
            sin, cos, tan, exp, log, sqrt, pi, E, I, oo, zoo,
            integrate, diff, solve, simplify, factor, expand,
            Matrix, det, trace, eye, zeros, ones,
            series, limit, summation, product,
            fourier_transform, laplace_transform,
            latex, pretty, pprint,
            N, Rational, Integer, Float,
            atan2, asin, acos, atan,
        )
        x, y, z, t, n, k, m = symbols('x y z t n k m')
        ns.update(locals())
        ns['sp'] = sp
    except ImportError:
        pass

    # ── Archimedes modules ────────────────────────────────────────────────
    try:
        from Archimedes.Maths.Calculus import Calculus
        ns['calc'] = Calculus()
    except Exception:
        pass

    try:
        from Archimedes.Maths.LorenzStirling import LorenzStirling, LorenzSystem, StirlingBasin
        ns['ls']      = LorenzStirling()
        ns['lorenz']  = LorenzSystem()
        ns['stirling']= StirlingBasin()
    except Exception:
        pass

    try:
        from Archimedes.Maths.GraphPlot import GraphPlot
        ns['GraphPlot'] = GraphPlot
    except Exception:
        pass

    # ── Help ──────────────────────────────────────────────────────────────
    def help_math():
        lines = [
            "ArchimedesShell — /math mode",
            "  sp              sympy module",
            "  x,y,z,t,n,k,m  pre-declared symbols",
            "  calc            Calculus() — .derivative(), .partial_derivative()",
            "  ls              LorenzStirling() — .classify(z)",
            "  lorenz          LorenzSystem() — .trajectory()",
            "  stirling        StirlingBasin() — .iterate(z)",
            "  latex(expr)     LaTeX string",
            "  pprint(expr)    pretty-print",
            "  help_math()     this help",
        ]
        return '\n'.join(lines)
    ns['help_math'] = help_math

    return ns


class ArchimedesShell:
    """
    Single-use math evaluator + interactive REPL wrapper.
    Used by PtolShell when in /math mode.
    """

    def __init__(self, output_fn=None, bus=None):
        """
        output_fn: callable(text, color) — routes output to PtolShell display
        bus:       PtolBus instance for result emission
        """
        self._output = output_fn or (lambda t, c='#aaffcc': print(t))
        self._bus    = bus
        self._ns     = _build_namespace()
        self._ns['__name__'] = '__archimedes__'

    def eval(self, expr: str) -> Optional[str]:
        """
        Evaluate a single expression in the math namespace.
        Returns string result or None on error.
        Emits result to PtolBus.
        """
        result_holder = [None]
        error_holder  = [None]

        def _run():
            buf = StringIO()
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout = buf
            sys.stderr = buf
            try:
                try:
                    # Try eval first (expression)
                    val = eval(compile(expr, '<archimedes>', 'eval'), self._ns)
                    if val is not None:
                        if SHELL_SETTINGS['latex_output']:
                            try:
                                import sympy as sp
                                result_holder[0] = sp.latex(val)
                            except Exception:
                                result_holder[0] = str(val)
                        elif SHELL_SETTINGS['auto_simplify']:
                            try:
                                import sympy as sp
                                result_holder[0] = str(sp.simplify(val))
                            except Exception:
                                result_holder[0] = str(val)
                        else:
                            result_holder[0] = str(val)
                except SyntaxError:
                    # Fall through to exec (statement)
                    exec(compile(expr, '<archimedes>', 'exec'), self._ns)
                    result_holder[0] = buf.getvalue() or '(ok)'
            except Exception as e:
                error_holder[0] = f'{type(e).__name__}: {e}'
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=SHELL_SETTINGS['timeout_s'])

        if t.is_alive():
            self._output('TIMEOUT — computation exceeded limit', '#ff5555')
            return None

        if error_holder[0]:
            self._output(error_holder[0], '#ff5555')
            return None

        result = result_holder[0]
        if result:
            self._output(f'  {result}', '#aaffcc')
            self._emit(expr, result)
        return result

    def _emit(self, expr: str, result: str):
        if self._bus is None:
            return
        try:
            from Pharos.PtolBus import BusMessage, CH_FACE_EVENT, Priority
            self._bus.publish(BusMessage(
                CH_FACE_EVENT,
                {'face': 'archimedes', 'expr': expr, 'result': result},
                Priority.T1, sender='ArchimedesShell'))
        except Exception:
            pass
