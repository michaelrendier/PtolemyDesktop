"""
SMNNIP Instance Engine -- Mouseion

Domain: Interface patterns, user interaction geometry, presentation state

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Mouseion"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Mouseion domain signal. TODO: implement."""
    raise NotImplementedError("Mouseion SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Mouseion signal. TODO: implement."""
    raise NotImplementedError("Mouseion SMNNIP sign() not yet implemented.")
