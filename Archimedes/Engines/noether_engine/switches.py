"""
noether_engine.switches — 14-axis switch system for the Noether Current Engine.

Every contestable choice in Noether's theorem is an explicit switch.
Defaults exist; all defaults are logged in output metadata.
UnsupportedCombinationError raised for unimplemented combinations.

Author: Ainulindalë / O Captain My Captain + Claude
Session 1 — April 2026
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ── Error types ──────────────────────────────────────────────────────────────

class SwitchError(Exception):
    """Base class for switch-related errors."""

class UnsupportedCombinationError(SwitchError):
    """Raised when a switch combination is not yet implemented."""

class InvalidSwitchValueError(SwitchError):
    """Raised when an invalid value is given for a known switch."""

class InconsistentCombinationError(SwitchError):
    """Raised when switches are mutually contradictory."""


# ── Switch definitions ───────────────────────────────────────────────────────

_SWITCH_DEFS = {
    'theorem':     {'choices': frozenset({'first', 'second', 'both'}),              'default': 'first'},
    'shell':       {'choices': frozenset({'on_shell', 'off_shell', 'both'}),        'default': 'on_shell'},
    'invariance':  {'choices': frozenset({'strict', 'divergence', 'bessel_hagen'}), 'default': 'bessel_hagen'},
    'output':      {'choices': frozenset({'current', 'charge', 'form', 'all'}),     'default': 'current'},
    'variation':   {'choices': frozenset({'vertical', 'total', 'both'}),            'default': 'vertical'},
    'signature':   {'choices': frozenset({'mostly_minus', 'mostly_plus'}),          'default': 'mostly_minus'},
    'spacetime':   {'choices': frozenset({'minkowski', 'curved', 'euclidean', 'adm', 'custom'}), 'default': 'minkowski'},
    'improvement': {'choices': frozenset({'none', 'belinfante_rosenfeld', 'ccj', 'custom'}), 'default': 'none'},
    'algebra':     {'choices': frozenset({'physics', 'math', 'custom'}),            'default': 'physics'},
    'boundary':    {'choices': frozenset({'vanishing_at_infinity', 'compact', 'bulk', 'explicit'}), 'default': 'vanishing_at_infinity'},
    'theory':      {'choices': frozenset({'classical', 'quantum_ward', 'anomaly_tracked'}), 'default': 'classical'},
    'action':      {'choices': frozenset({'covariant', 'hamiltonian', 'adm_split'}), 'default': 'covariant'},
    'format':      {'choices': frozenset({'symbolic', 'numerical', 'latex', 'all'}), 'default': 'symbolic'},
}

# Session 1 deferred values
_DEFERRED: Dict[Tuple[str, str], str] = {
    ('shell', 'off_shell'):               'session 2 — BV machinery',
    ('shell', 'both'):                    'session 2 — requires off_shell',
    ('theorem', 'second'):                'session 2 — gauge-identity machinery',
    ('theorem', 'both'):                  'session 2',
    ('improvement', 'belinfante_rosenfeld'): 'session 2',
    ('improvement', 'ccj'):               'session 2',
    ('improvement', 'custom'):            'session 2',
    ('spacetime', 'curved'):              'session 3 — einsteinpy backing',
    ('spacetime', 'euclidean'):           'session 3',
    ('spacetime', 'adm'):                 'session 3',
    ('spacetime', 'custom'):              'session 3',
    ('action', 'hamiltonian'):            'session 3',
    ('action', 'adm_split'):              'session 3',
    ('theory', 'quantum_ward'):           'session 4',
    ('theory', 'anomaly_tracked'):        'session 4',
    ('format', 'numerical'):              'session 2',
    ('algebra', 'custom'):                'session 2',
}


@dataclass
class SwitchSettings:
    """A concrete selection of values across all 13 axes."""
    values: Dict[str, str] = field(default_factory=dict)
    user_supplied: Set[str] = field(default_factory=set)

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> 'SwitchSettings':
        inst = cls()
        for key, val in kwargs.items():
            if key not in _SWITCH_DEFS:
                raise InvalidSwitchValueError(
                    f"Unknown switch '{key}'. Valid: {sorted(_SWITCH_DEFS.keys())}"
                )
            if val not in _SWITCH_DEFS[key]['choices']:
                raise InvalidSwitchValueError(
                    f"Switch '{key}' value '{val}' invalid. "
                    f"Valid: {sorted(_SWITCH_DEFS[key]['choices'])}"
                )
            inst.values[key] = val
            inst.user_supplied.add(key)
        # fill defaults
        for axis, defn in _SWITCH_DEFS.items():
            if axis not in inst.values:
                inst.values[axis] = defn['default']
        return inst

    def get(self, name: str) -> str:
        return self.values[name]

    def is_default(self, name: str) -> bool:
        return name not in self.user_supplied

    def as_metadata_dict(self) -> Dict[str, Dict[str, Any]]:
        return {
            axis: {
                'value': val,
                'user_supplied': axis in self.user_supplied,
                'default': _SWITCH_DEFS[axis]['default'],
                'choices': sorted(_SWITCH_DEFS[axis]['choices']),
            }
            for axis, val in self.values.items()
        }


def validate_combination(settings: SwitchSettings) -> None:
    """Raise UnsupportedCombinationError if any switch value is deferred."""
    for axis, val in settings.values.items():
        key = (axis, val)
        if key in _DEFERRED:
            raise UnsupportedCombinationError(
                f"Combination ({axis}={val!r}) not yet supported — "
                f"{_DEFERRED[key]}. Use an implemented alternative."
            )


def summarize_implementation_status() -> str:
    lines = ['Noether Engine — Session 1 Implementation Status', '=' * 60]
    for axis, defn in _SWITCH_DEFS.items():
        impl = sorted(v for v in defn['choices'] if (axis, v) not in _DEFERRED)
        deferred = sorted(v for v in defn['choices'] if (axis, v) in _DEFERRED)
        lines.append(f"\n  {axis}:")
        lines.append(f"    ✓ {impl}")
        if deferred:
            lines.append(f"    ○ {deferred} (deferred)")
    return '\n'.join(lines)


if __name__ == '__main__':
    print(summarize_implementation_status())
