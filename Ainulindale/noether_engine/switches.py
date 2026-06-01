"""
noether_engine.switches — 14-axis switch registry and combination validator.

This module is the authoritative source for which switch values exist, which
combinations are implemented in which session, and how the engine validates
user-supplied switch settings.

Exposed classes:
  - Switch              — one contestable axis with choices and default
  - SwitchRegistry      — the 14-axis registry, singleton
  - SwitchSettings      — a concrete choice across all 14 axes
  - CombinationStatus   — IMPLEMENTED / DEFERRED / INCONSISTENT per combination

Exposed exceptions:
  - UnsupportedCombinationError — raised when an unsupported combination is requested
  - InconsistentCombinationError — raised when a combination is mathematically invalid
  - InvalidSwitchValueError — raised when a switch is given an unknown value

See architecture.md §3 for the full axis specification.
See architecture.md §4 for the compatibility matrix.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple


# =============================================================================
#  EXCEPTIONS
# =============================================================================

class SwitchError(Exception):
    """Base class for switch-related errors."""
    pass


class InvalidSwitchValueError(SwitchError):
    """Raised when a switch is set to a value outside its declared choices."""
    pass


class UnsupportedCombinationError(SwitchError):
    """
    Raised when the engine is asked to run a switch combination that is
    within the declared switch space but not yet implemented.

    The error message names the offending combination and the target session
    for its implementation.
    """
    pass


class InconsistentCombinationError(SwitchError):
    """
    Raised when the engine is asked to run a switch combination that is
    mathematically inconsistent (not a matter of implementation effort but
    of incompatibility — e.g. boundary=compact_support with spacetime=curved
    on a non-compact manifold).
    """
    pass


# =============================================================================
#  SWITCH — one contestable axis
# =============================================================================

@dataclass(frozen=True)
class Switch:
    """
    One contestable axis of Noether's theorem.

    name          : short identifier (e.g. 'theorem', 'shell', 'signature')
    description   : one-line description for documentation
    choices       : frozenset of acceptable values
    default       : the default value if user does not specify
    default_reason: one-line rationale for the default (logged in metadata)
    references    : list of literature references where this axis is discussed
    """
    name: str
    description: str
    choices: FrozenSet[str]
    default: str
    default_reason: str
    references: Tuple[str, ...] = ()

    def validate(self, value: str) -> None:
        """
        Check that `value` is one of the declared choices.
        Raises InvalidSwitchValueError otherwise.
        """
        if value not in self.choices:
            raise InvalidSwitchValueError(
                f"Switch '{self.name}' received value '{value}'; "
                f"valid choices are {sorted(self.choices)}."
            )


# =============================================================================
#  THE 14 AXES
# =============================================================================

AXIS_1_THEOREM = Switch(
    name='theorem',
    description='Noether theorem variant',
    choices=frozenset({'first', 'second', 'both'}),
    default='first',
    default_reason="First theorem (global symmetry → current) is the most common use case.",
    references=(
        "Noether, E. (1918). Invariante Variationsprobleme.",
        "Brading, K. & Brown, H.R. (2003). Noether's theorems and gauge symmetries.",
    ),
)

AXIS_2_SHELL = Switch(
    name='shell',
    description='On-shell vs off-shell derivation',
    choices=frozenset({'on_shell', 'off_shell', 'both'}),
    default='on_shell',
    default_reason="Standard textbook derivation. Off-shell requires BV machinery (session 2).",
    references=(
        "Peskin & Schroeder (1995), §2.",
        "Henneaux, M. & Teitelboim, C. (1992). Quantization of Gauge Systems.",
    ),
)

AXIS_3_INVARIANCE = Switch(
    name='invariance',
    description='Invariance type under the symmetry',
    choices=frozenset({'strict', 'divergence', 'bessel_hagen'}),
    default='bessel_hagen',
    default_reason="Most general formulation; strict and divergence are special cases.",
    references=(
        "Bessel-Hagen, E. (1921). Über die Erhaltungssätze der Elektrodynamik.",
        "Olver, P.J. (1993). Applications of Lie Groups to Differential Equations.",
    ),
)

AXIS_4_OUTPUT = Switch(
    name='output',
    description='Conserved-object output form',
    choices=frozenset({'current', 'charge', 'form', 'all'}),
    default='current',
    default_reason="Current form is the most immediate output of Noether's theorem.",
    references=(
        "Weinberg, S. (1995). QFT Vol I, §7.",
    ),
)

AXIS_5_VARIATION = Switch(
    name='variation',
    description='Field variation convention',
    choices=frozenset({'vertical', 'total', 'both'}),
    default='vertical',   # type-dependent — for spacetime symmetries this auto-switches to 'total'
    default_reason="Vertical variation for internal symmetries; auto-switches to 'total' for spacetime flows.",
    references=(
        "Olver, P.J. (1993), §4.3.",
    ),
)

AXIS_6_SIGNATURE = Switch(
    name='signature',
    description='Metric signature convention',
    choices=frozenset({'mostly_minus', 'mostly_plus'}),
    default='mostly_minus',
    default_reason="Particle-physics convention (Peskin-Schroeder, Srednicki).",
    references=(
        "Peskin & Schroeder (1995). Mostly-minus.",
        "Misner, Thorne & Wheeler (1973). Mostly-plus.",
    ),
)

AXIS_7_SPACETIME = Switch(
    name='spacetime',
    description='Spacetime type',
    choices=frozenset({'minkowski', 'curved', 'euclidean', 'adm', 'custom'}),
    default='minkowski',
    default_reason="Flat 4D Minkowski is the baseline. Curved/euclidean/adm require session 3 machinery.",
    references=(
        "Wald, R.M. (1984). General Relativity.",
        "Misner, Thorne & Wheeler (1973).",
    ),
)

AXIS_8_IMPROVEMENT = Switch(
    name='improvement',
    description='Improvement term for stress-energy tensor',
    choices=frozenset({'none', 'belinfante_rosenfeld', 'ccj', 'custom'}),
    default='none',
    default_reason="Canonical Noether current, no improvement. BR/CCJ in session 2.",
    references=(
        "Belinfante, F.J. (1940).",
        "Callan, Coleman, Jackiw (1970). Ann. Phys. 59.",
    ),
)

AXIS_9_ALGEBRA = Switch(
    name='algebra',
    description='Lie algebra generator normalization',
    choices=frozenset({'physics', 'math', 'custom'}),
    default='physics',
    default_reason="Tr(T^a T^b) = (1/2) δ^{ab} — physics convention.",
    references=(
        "Peskin & Schroeder (1995), §15.",
        "Georgi, H. (1999). Lie Algebras in Particle Physics.",
    ),
)

AXIS_10_BOUNDARY = Switch(
    name='boundary',
    description='Boundary condition on fields',
    choices=frozenset({'vanishing_at_infinity', 'compact_support', 'bulk_only', 'explicit'}),
    default='vanishing_at_infinity',
    default_reason="Standard QFT asymptotic falloff; ensures charge convergence.",
    references=(
        "Weinberg, S. (1995), §2.6.",
    ),
)

AXIS_11_THEORY = Switch(
    name='theory',
    description='Classical vs quantum treatment',
    choices=frozenset({'classical', 'quantum_ward', 'anomaly_tracked'}),
    default='classical',
    default_reason="Classical Noether is the starting point. Quantum/anomaly in session 4.",
    references=(
        "Bardeen, W.A. & Zumino, B. (1984). Nucl. Phys. B 244.",
        "Bertlmann, R. (1996). Anomalies in Quantum Field Theory.",
    ),
)

AXIS_12_FIELD_TYPE = Switch(
    name='field_type_policy',
    description="How field types are specified (informational — per-field declaration is mandatory)",
    choices=frozenset({'per_field_required'}),
    default='per_field_required',
    default_reason="Field type is a property of each Field object; no engine-wide default.",
    references=(
        "See noether_engine.core.field for supported field types.",
    ),
)

AXIS_13_ACTION = Switch(
    name='action',
    description='Action-integral prescription',
    choices=frozenset({'covariant', 'hamiltonian', 'adm_split'}),
    default='covariant',
    default_reason="Covariant Lagrangian density S = ∫ d⁴x √|g| ℒ is standard.",
    references=(
        "Wald, R.M. (1984), §9.",
        "Misner, Thorne & Wheeler (1973), §21.",
    ),
)

AXIS_14_FORMAT = Switch(
    name='format',
    description='Output format',
    choices=frozenset({'symbolic', 'numerical', 'latex', 'all'}),
    default='symbolic',
    default_reason="Sympy symbolic output is the most flexible for downstream use.",
    references=(),
)


ALL_AXES: Tuple[Switch, ...] = (
    AXIS_1_THEOREM, AXIS_2_SHELL, AXIS_3_INVARIANCE, AXIS_4_OUTPUT,
    AXIS_5_VARIATION, AXIS_6_SIGNATURE, AXIS_7_SPACETIME, AXIS_8_IMPROVEMENT,
    AXIS_9_ALGEBRA, AXIS_10_BOUNDARY, AXIS_11_THEORY, AXIS_12_FIELD_TYPE,
    AXIS_13_ACTION, AXIS_14_FORMAT,
)

AXIS_BY_NAME: Dict[str, Switch] = {ax.name: ax for ax in ALL_AXES}


# =============================================================================
#  SUB-SWITCHES (depend on parent switch values)
# =============================================================================

OCTONION_FANO_CHOICES = frozenset({'oriented_cyclic', 'alternate', 'custom'})
OCTONION_FANO_DEFAULT = 'oriented_cyclic'


# =============================================================================
#  COMBINATION STATUS — compatibility matrix
# =============================================================================

@dataclass(frozen=True)
class CombinationStatus:
    """
    Status of a switch combination.

    status       : 'implemented', 'deferred', or 'inconsistent'
    session      : target session number for deferred items (None if implemented or inconsistent)
    reason       : explanation for deferred/inconsistent cases
    """
    status: str
    session: Optional[int]
    reason: str


IMPLEMENTED = CombinationStatus('implemented', None, '')


def _deferred(session: int, reason: str) -> CombinationStatus:
    return CombinationStatus('deferred', session, reason)


def _inconsistent(reason: str) -> CombinationStatus:
    return CombinationStatus('inconsistent', None, reason)


# Deferred combinations: each tuple is (switch_name, value) that triggers deferral.
# Multiple triggers on the same switch value are ORed; across switch names, ANDed.
# For session 1 we list single-switch-value deferrals.

DEFERRED_SWITCH_VALUES: Dict[Tuple[str, str], CombinationStatus] = {
    ('shell', 'off_shell'):             _deferred(2, "BV/cohomological machinery required."),
    ('shell', 'both'):                  _deferred(2, "Requires off_shell implementation."),
    ('theorem', 'second'):              _deferred(2, "Second-theorem gauge-identity machinery required."),
    ('theorem', 'both'):                _deferred(2, "Requires second-theorem implementation."),
    ('improvement', 'belinfante_rosenfeld'): _deferred(2, "Symmetrization of stress-energy tensor."),
    ('improvement', 'ccj'):             _deferred(2, "Callan-Coleman-Jackiw conformal improvement."),
    ('spacetime', 'curved'):            _deferred(3, "Curved-spacetime covariant derivatives require einsteinpy."),
    ('spacetime', 'euclidean'):         _deferred(3, "Imaginary-time Euclidean formalism."),
    ('spacetime', 'adm'):               _deferred(3, "ADM 3+1 split."),
    ('spacetime', 'custom'):            _deferred(3, "User-supplied metric and connection."),
    ('action', 'hamiltonian'):          _deferred(3, "Legendre-transform machinery."),
    ('action', 'adm_split'):            _deferred(3, "ADM formalism."),
    ('theory', 'quantum_ward'):         _deferred(4, "Ward-Takahashi identities."),
    ('theory', 'anomaly_tracked'):      _deferred(4, "ABJ/trace anomaly tracking."),
    ('format', 'numerical'):            _deferred(2, "Field-configuration evaluator."),
    ('format', 'all'):                  _deferred(2, "Requires format='numerical' implementation."),
    ('algebra', 'custom'):              _deferred(2, "User-supplied generator normalization with full validation."),
}


# =============================================================================
#  SWITCH SETTINGS — concrete choice across all axes
# =============================================================================

@dataclass
class SwitchSettings:
    """
    A concrete selection of values across all 14 axes.

    Stored as a dict for flexibility; .as_metadata_dict() produces the record
    logged in every engine result.
    """
    values: Dict[str, str] = field(default_factory=dict)
    user_supplied: Set[str] = field(default_factory=set)

    @classmethod
    def from_kwargs(cls, **kwargs: Any) -> 'SwitchSettings':
        """
        Build from a user-supplied dict of switch values. Unknown keys raise
        InvalidSwitchValueError. Missing keys fall back to axis defaults.
        """
        inst = cls()
        # Accept unknown keys only if they are recognized sub-switches.
        recognized_extras = {'octonion_fano'}

        for key, val in kwargs.items():
            if key in AXIS_BY_NAME:
                ax = AXIS_BY_NAME[key]
                ax.validate(val)
                inst.values[key] = val
                inst.user_supplied.add(key)
            elif key == 'octonion_fano':
                if val not in OCTONION_FANO_CHOICES:
                    raise InvalidSwitchValueError(
                        f"octonion_fano='{val}' not in {sorted(OCTONION_FANO_CHOICES)}."
                    )
                inst.values[key] = val
                inst.user_supplied.add(key)
            else:
                raise InvalidSwitchValueError(
                    f"Unknown switch '{key}'. Valid switches: "
                    f"{sorted(list(AXIS_BY_NAME.keys()) + list(recognized_extras))}."
                )

        # Fill in defaults for axes not supplied
        for ax in ALL_AXES:
            if ax.name not in inst.values:
                inst.values[ax.name] = ax.default

        # Fill in default for octonion_fano if not supplied
        if 'octonion_fano' not in inst.values:
            inst.values['octonion_fano'] = OCTONION_FANO_DEFAULT

        return inst

    def get(self, name: str) -> str:
        return self.values[name]

    def is_default(self, name: str) -> bool:
        return name not in self.user_supplied

    def as_metadata_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Produce the metadata record for the output.

        Returns a dict mapping each switch name to a dict with:
          'value'        : the value in effect
          'user_supplied': True if user supplied this value, False if default
          'default_reason': (if default) why this default was chosen
          'choices'      : the valid choices for this switch
          'references'   : literature references for this axis
        """
        out: Dict[str, Dict[str, Any]] = {}
        for ax in ALL_AXES:
            entry = {
                'value': self.values[ax.name],
                'user_supplied': ax.name in self.user_supplied,
                'choices': sorted(ax.choices),
                'references': list(ax.references),
            }
            if ax.name not in self.user_supplied:
                entry['default_reason'] = ax.default_reason
            out[ax.name] = entry
        # Also include sub-switches
        if 'octonion_fano' in self.values:
            out['octonion_fano'] = {
                'value': self.values['octonion_fano'],
                'user_supplied': 'octonion_fano' in self.user_supplied,
                'choices': sorted(OCTONION_FANO_CHOICES),
                'references': [
                    "Baez, J.C. (2002). The octonions. Bull. AMS 39(2).",
                ],
            }
        return out


# =============================================================================
#  VALIDATOR — check combinations against the compatibility matrix
# =============================================================================

def validate_combination(settings: SwitchSettings) -> None:
    """
    Check that the combination of settings is implemented in this session.

    Raises:
      UnsupportedCombinationError — if the combination is deferred
      InconsistentCombinationError — if the combination is mathematically invalid

    Does not return; either succeeds silently or raises.
    """
    # Check single-switch-value deferrals
    for (switch_name, switch_value), status in DEFERRED_SWITCH_VALUES.items():
        if settings.values.get(switch_name) == switch_value:
            raise UnsupportedCombinationError(
                f"Switch combination ({switch_name}={switch_value}) not yet supported — "
                f"reason: {status.reason} Scheduled for session {status.session}. "
                f"Use an implemented alternative or wait for session {status.session} release."
            )

    # Check pair-wise inconsistencies
    # (No cross-axis inconsistencies trigger in session-1 implemented set.
    #  Placeholder for future additions — e.g. boundary=compact_support with
    #  spacetime=custom and non-compact metric.)
    pass


def summarize_implementation_status() -> str:
    """
    Produce a human-readable summary of what is implemented vs deferred.
    For use in the engine's --help output and documentation.
    """
    lines = []
    lines.append("NOETHER CURRENT ENGINE — IMPLEMENTATION STATUS")
    lines.append("=" * 60)
    lines.append("")
    lines.append("IMPLEMENTED (session 1):")
    for ax in ALL_AXES:
        impl = sorted(
            v for v in ax.choices
            if (ax.name, v) not in DEFERRED_SWITCH_VALUES
        )
        lines.append(f"  {ax.name:22s} : {impl}")
    lines.append("")
    lines.append("DEFERRED:")
    by_session: Dict[int, List[str]] = {}
    for (name, val), status in DEFERRED_SWITCH_VALUES.items():
        by_session.setdefault(status.session, []).append(f"{name}={val}")
    for session in sorted(by_session):
        lines.append(f"  session {session}:")
        for item in sorted(by_session[session]):
            lines.append(f"    - {item}")
    return "\n".join(lines)


if __name__ == '__main__':
    print(summarize_implementation_status())
