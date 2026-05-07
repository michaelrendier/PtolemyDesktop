"""
Philadelphos/smip_engine.py
------------------------------
SMIPEngine -- base class for all Face SMIP Instance Engines.

SMIP: Standard Model of Information Propagation
        (Ainulindale Conjecture)

Every Face runs a sovereign instance of this engine trained on its
domain-specific signal. The engine verifies that each inference step
conserves information under the Lagrangian self-adjoint constraint.

Mathematical basis (Ainulindale):
  - Lagrangian: L_NN = L_kinetic + L_matter + L_bias + L_coupling
  - Noether current: D_l J^{a,l} = 0  (gauge conservation across layers)
  - Self-adjoint constraint: operator L satisfies L = L-dagger
    -> real eigenvalues guaranteed by spectral theorem
    -> violation = information loss or injection = hallucination precursor
  - Conservation verified via NoetherMonitor.is_conserved()
    criterion: mean Noether violation < 0.2 per layer (empirical 7+ sigma)

The self-adjoint / Hermitian claim:
  The propagation operator for each algebra layer (R -> C -> H -> O) is
  constructed to be self-adjoint by the Yang-Mills weight update rule,
  which is derived from the Euler-Lagrange equation of L_NN, not assumed.
  The h.c. (Hermitian conjugate) terms in the coupling Lagrangian ensure
  L_NN is real-valued. A non-self-adjoint step produces a non-real
  eigenvalue, which surfaces as a SelfAdjointViolation (PTL_605).

  TODO (blocks academic submission, not Woz):
    Formal proof that YM update rule guarantees self-adjointness for
    arbitrary layer depth and coupling constant g.
    Currently verified empirically in smip_full_tower.py benchmarks.
    See: Callimachus/v09/core/lsh_datatype.py for the open TODO.

Source: https://github.com/michaelrendier/Ainulindale
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class SMIPEngine(ABC):
    """
    Abstract base for all Face SMIP Instance Engines.

    Subclass and implement verify() and sign() for each Face domain.
    Wire via Pharos.ptol_face_wiring.wire_face() -- do not instantiate directly.
    """

    #: Face name -- set in subclass
    FACE_NAME: str = "Unknown"

    #: Noether violation threshold. Violation above this = not conserved.
    CONSERVATION_THRESHOLD: float = 0.2

    @abstractmethod
    def verify(self, signal: Any) -> bool:
        """
        Verify that signal conserves information under the SMIP Lagrangian.

        Returns True if conserved, False if violation detected.
        Raise PTL_605 SelfAdjointViolation for hard operator failures.
        Raise PTL_602 InferenceCoordInvalid for address space violations.

        signal: domain-specific input -- word vector, sensor reading,
                octonion coordinate, bus message, etc.
        """

    @abstractmethod
    def sign(self, signal: Any) -> Any:
        """
        Sign a verified signal -- attach conservation certificate.

        Only called after verify() returns True.
        Returns the signed signal (domain-specific format).
        """

    def is_conserved(self, noether_violation: float) -> bool:
        """
        Standard conservation check against empirical threshold.
        Override for domain-specific criteria.
        """
        return abs(noether_violation) < self.CONSERVATION_THRESHOLD

    def handle_violation(self, signal: Any, violation: float) -> None:
        """
        Called when verify() detects a conservation violation.
        Default: raise SelfAdjointViolation (PTL_605).
        Override for domain-specific degraded-mode behaviour.
        """
        from Pharos.luthspell_error_handler import SelfAdjointViolation
        raise SelfAdjointViolation(
            f"{self.FACE_NAME} conservation violation: {violation:.6f} "
            f"(threshold {self.CONSERVATION_THRESHOLD})"
        )
