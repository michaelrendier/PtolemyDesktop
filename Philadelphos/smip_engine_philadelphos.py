"""
SMIP Instance Engine -- Philadelphos

Domain: Language geometry, LSH inference, contextual address field

Status: STUB -- pending SMIPEngine base class implementation
         (Philadelphos/smip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Philadelphos"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Philadelphos domain signal. TODO: implement."""
    raise NotImplementedError("Philadelphos SMIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Philadelphos signal. TODO: implement."""
    raise NotImplementedError("Philadelphos SMIP sign() not yet implemented.")
