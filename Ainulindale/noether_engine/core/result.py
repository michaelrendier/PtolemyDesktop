"""
noether_engine.core.result — the NoetherResult container.

Every engine invocation returns a NoetherResult with:
  - current     : the Current object (J^μ components)
  - charge      : optional charge expression (if output includes 'charge')
  - form        : optional (d-1)-form (if output includes 'form')
  - latex       : LaTeX string (if format includes 'latex')
  - metadata    : full record of switch settings used
  - verification: record of conservation checks performed
  - variation   : the δℒ that was computed along the way
  - K_mu        : the K^μ used (if Bessel-Hagen)
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Any, Dict, List, Optional

import sympy as sp

from .current import Current


@dataclass
class NoetherResult:
    """
    Structured return value from NoetherEngine.derive_current().
    """
    current: Current
    charge: Optional[sp.Expr] = None
    form: Optional[sp.Expr] = None
    latex: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = dc_field(default_factory=dict)
    verification: Dict[str, Any] = dc_field(default_factory=dict)
    variation: Optional[sp.Expr] = None
    K_mu: Optional[tuple] = None

    def summary(self) -> str:
        """Plain-text summary suitable for console output."""
        lines = []
        lines.append("Noether Current Derivation Result")
        lines.append("=" * 60)
        lines.append(f"Symmetry: {self.current.symmetry.name}")
        lines.append(f"Convention: {self.current.convention}")
        lines.append("")
        lines.append("Conserved current components:")
        for mu, Jmu in enumerate(self.current.components):
            lines.append(f"  J^{mu} = {Jmu}")
        if self.charge is not None:
            lines.append("")
            lines.append("Charge:")
            lines.append(f"  Q = {self.charge}")
        lines.append("")
        lines.append("Conservation check:")
        for key, val in self.verification.items():
            lines.append(f"  {key}: {val}")
        lines.append("")
        lines.append("Metadata (switch values in effect):")
        for axis, info in self.metadata.items():
            marker = " [user]" if info.get('user_supplied') else " [default]"
            lines.append(f"  {axis:25s} = {info['value']}{marker}")
        return "\n".join(lines)
