"""
SMNNIP Instance Engine -- Tesla

Domain: Sensor stream continuity, device state, physical signal conservation

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Tesla"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Tesla domain signal. TODO: implement."""
    raise NotImplementedError("Tesla SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Tesla signal. TODO: implement."""
    raise NotImplementedError("Tesla SMNNIP sign() not yet implemented.")
