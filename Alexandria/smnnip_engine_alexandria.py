"""
SMNNIP Instance Engine -- Alexandria

Domain: Visual geometry, rendering state, fractal parameter space

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Alexandria"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Alexandria domain signal. TODO: implement."""
    raise NotImplementedError("Alexandria SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Alexandria signal. TODO: implement."""
    raise NotImplementedError("Alexandria SMNNIP sign() not yet implemented.")
