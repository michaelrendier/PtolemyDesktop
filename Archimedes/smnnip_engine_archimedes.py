"""
SMNNIP Instance Engine -- Archimedes

Domain: Mathematical conservation, physical law, signal integrity

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Archimedes"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Archimedes domain signal. TODO: implement."""
    raise NotImplementedError("Archimedes SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Archimedes signal. TODO: implement."""
    raise NotImplementedError("Archimedes SMNNIP sign() not yet implemented.")
