"""
SMNNIP Instance Engine -- Mandos

Domain: System state integrity, dormant checkpoint verification

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Mandos"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Mandos domain signal. TODO: implement."""
    raise NotImplementedError("Mandos SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Mandos signal. TODO: implement."""
    raise NotImplementedError("Mandos SMNNIP sign() not yet implemented.")
