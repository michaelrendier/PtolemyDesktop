"""
SMNNIP Instance Engine -- Kryptos

Domain: Entropy distribution, key geometry, cipher conservation

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Kryptos"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Kryptos domain signal. TODO: implement."""
    raise NotImplementedError("Kryptos SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Kryptos signal. TODO: implement."""
    raise NotImplementedError("Kryptos SMNNIP sign() not yet implemented.")
