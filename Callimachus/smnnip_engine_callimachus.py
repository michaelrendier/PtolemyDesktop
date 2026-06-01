"""
SMNNIP Instance Engine -- Callimachus

Domain: Information architecture, HyperWebster address geometry, blockchain state

Status: STUB -- pending SMNNIPEngine base class implementation
         (Philadelphos/smnnip_engine.py)

Wired via ptol_face_wiring on module import.
"""

from Pharos.ptol_face_wiring import wire_face
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Callimachus"

# Wire ErrorHandler + GC. Mandos checkpoint-before-GC is automatic.
_handler = wire_face(FACE_NAME)


def verify(signal):
    """Verify conservation of Callimachus domain signal. TODO: implement."""
    raise NotImplementedError("Callimachus SMNNIP verify() not yet implemented.")


def sign(signal):
    """Sign a verified Callimachus signal. TODO: implement."""
    raise NotImplementedError("Callimachus SMNNIP sign() not yet implemented.")
