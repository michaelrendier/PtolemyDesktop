"""
Pharos/ptol_face_wiring.py
--------------------------
Standard wiring factory for all Ptolemy Faces.

Usage in every Face module:

    from Pharos.ptol_face_wiring import wire_face, face_handler

    wire_face(FACE_NAME, get_state_fn=lambda: {"key": "value"})

    # Then in any try/except:
    try:
        ...
    except Exception as e:
        face_handler(FACE_NAME).handle(e)

Mandos checkpoint-before-GC is automatic via ErrorHandler._mandos_intercept().
Blockchain subscriber wired on every Face registration.
"""

from __future__ import annotations
from typing import Callable

from Pharos.luthspell_error_handler import ErrorHandler, GarbageCollector
from Pharos.PtolDmesg import dmesg
from Pharos.ptol_blockchain import chain, EventType
from Pharos.PtolBus import CH_BLOCKCHAIN

_registry: dict[str, dict] = {}


def wire_face(
    face_name:    str,
    bus=None,
    get_state_fn: Callable | None = None,
) -> ErrorHandler:
    """
    Wire ErrorHandler + GC + blockchain for a Face.
    Idempotent -- safe to call on restart.

    Args:
        face_name:    Face identifier (e.g. 'aule', 'archimedes')
        bus:          PtolBus instance. If provided, wires blockchain subscriber.
        get_state_fn: () -> dict  serializable state for Mandos checkpoint.

    Returns the ErrorHandler for this Face.
    """
    gc      = GarbageCollector()
    handler = ErrorHandler(
        gc=gc,
        face_name=face_name,
        on_error=lambda e: _on_face_error(face_name, e),
        get_state_fn=get_state_fn,
    )
    _registry[face_name] = {"handler": handler, "gc": gc, "bus": bus}

    # Register Face in sovereign chain
    try:
        chain.commit(face_name, EventType.FACE_REGISTER, {
            'face': face_name,
        })
    except Exception:
        pass  # Chain error must not block Face startup

    # Wire bus blockchain subscriber once (on the PtolBus instance)
    if bus is not None:
        try:
            bus.subscribe(CH_BLOCKCHAIN, chain.bus_handler)
        except Exception:
            pass

    dmesg.face_in(face_name)
    return handler


def _on_face_error(face_name: str, error) -> None:
    """On-error callback: write to dmesg AND blockchain."""
    dmesg.error(face_name, str(error))
    try:
        chain.commit_error(error)
    except Exception:
        pass


def face_handler(face_name: str) -> ErrorHandler:
    """Return the wired ErrorHandler for face_name."""
    from Pharos.luthspell_error_handler import ModuleNotWired
    entry = _registry.get(face_name)
    if entry is None:
        raise ModuleNotWired(
            f"{face_name} has no wired ErrorHandler. Call wire_face() first."
        )
    return entry["handler"]


def face_gc(face_name: str) -> GarbageCollector:
    """Return the GarbageCollector for face_name."""
    from Pharos.luthspell_error_handler import ModuleNotWired
    entry = _registry.get(face_name)
    if entry is None:
        raise ModuleNotWired(
            f"{face_name} has no wired GC. Call wire_face() first."
        )
    return entry["gc"]


def all_wired() -> list[str]:
    """Return list of all wired Face names."""
    return list(_registry.keys())
