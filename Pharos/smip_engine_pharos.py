"""
SMIP Instance Engine -- Pharos

Domain: System health, bus patterns, resource usage, error signatures

Status: STUB -- pending SMIPEngine base class implementation
         (Philadelphos/smip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Pharos"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Pharos domain signal. TODO: implement."""
    raise NotImplementedError("Pharos SMIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Pharos signal. TODO: implement."""
    raise NotImplementedError("Pharos SMIP sign() not yet implemented.")
