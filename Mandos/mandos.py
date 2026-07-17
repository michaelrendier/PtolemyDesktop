"""
Mandos -- Keeper of the Dead.

Holds dormant Face state. Works with Aule (Aule has priority).
If Aule fails, Mandos gains supervisor authority.
If Mandos fails -- world_break().

PTL_910 WorldBreak: the kernel panic. Final write to PtolChain. No return.
"""

import sys
from Mandos.mandos_store    import checkpoint, latest, list_dead
from Mandos.mandos_watchdog import start as start_watchdog, stop as stop_watchdog
from Mandos.mandos_resurrect import resurrect
from Pharos.PtolDmesg       import dmesg

FACE_NAME = "Mandos"

WORLD_BREAK_MESSAGE = (
    "Great is the Fall of Gondolin: "
    "love not too well the work of thy hands and the devices of thy heart; "
    "and remember that the true hope of the Noldor lieth in the West "
    "and cometh from the Sea."
)

_aule_has_priority = True
_aule_init_fn      = None


def start():
    """Start Mandos. Begin watching Aule."""
    start_watchdog(on_aule_dead=_on_aule_dead)
    dmesg.info(FACE_NAME, "Mandos is keeping watch.")


def stop():
    stop_watchdog()


def register_aule_init(fn):
    """Aule registers its own init function here at startup."""
    global _aule_init_fn
    _aule_init_fn = fn


def accept_dead(face_name: str, state: dict):
    """
    Called before GC on any FATAL.
    Serializes Face state to the Mandos store.
    On PTL_908 write failure: log and continue -- do not recurse.
    """
    try:
        path = checkpoint(face_name, state)
        dmesg.info(FACE_NAME, f"{face_name} received into Mandos ({path.name}).")
    except Exception as exc:
        dmesg.fatal(FACE_NAME, f"MandosStoreWriteFailed for {face_name}: {exc}")


def release(face_name: str, face_init_fn, smnnip_verify_fn=None):
    """Release a Face from Mandos. Called by Aule (normal) or self (Aule down)."""
    return resurrect(face_name, face_init_fn, smnnip_verify_fn)


def _on_aule_dead(err):
    """Watchdog callback -- Aule has died. Mandos gains priority."""
    global _aule_has_priority
    _aule_has_priority = False
    dmesg.fatal(FACE_NAME, f"Aule watchdog timeout -- Mandos assumes supervisor authority.")

    try:
        if latest("Aule") and _aule_init_fn is not None:
            dmesg.info(FACE_NAME, "Attempting Aule resurrection from checkpoint.")
            resurrect("Aule", _aule_init_fn)
            _aule_has_priority = True
            dmesg.info(FACE_NAME, "Aule resurrected. Returning priority.")
            return
        dmesg.fatal(FACE_NAME, "Aule resurrection failed. Mandos holds authority. Safe mode.")
    except Exception as exc:
        world_break(cause=str(exc))


def world_break(cause: str = "Mandos FATAL"):
    """
    PTL_910 WorldBreak -- the world is broken.
    Write all state to PtolChain. Print the message. Exit.
    This function does not return.
    """
    dmesg.fatal(FACE_NAME, f"WORLD BREAK -- cause: {cause}")

    try:
        from Callimachus.BlockChain.PtolChain.Chain import PtolChain
        PtolChain().add_block({"event": "WORLD_BREAK", "cause": cause, "dead": list_dead()})
    except Exception:
        pass  # Best-effort only. Do not recurse.

    print(flush=True)
    print(WORLD_BREAK_MESSAGE, flush=True)
    print(flush=True)
    sys.exit(1)
