"""
SMNNIP Instance Engine -- Anaximander

Domain: Spatial continuity, route geometry, location field

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Anaximander"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Anaximander domain signal. TODO: implement."""
    raise NotImplementedError("Anaximander SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Anaximander signal. TODO: implement."""
    raise NotImplementedError("Anaximander SMNNIP sign() not yet implemented.")
