"""
Aule/aule_wiring.py
-------------------
Aule-specific wiring:
  - ErrorHandler + GC via ptol_face_wiring
  - Mandos.start() + register_aule_init()
  - Watchdog heartbeat: call aule_beat() on every Aule main loop tick

Aule is the supervisor. Mandos watches Aule.
If Aule stops beating for 3 x 5s intervals, Mandos gains priority.
"""

from Pharos.ptol_face_wiring import wire_face, face_handler

FACE_NAME = "Aule"

_handler = None


def init_aule_wiring(get_state_fn=None):
    """
    Call once at Aule startup, before any other Aule operations.
    Starts Mandos watchdog and registers Aule resurrection function.
    """
    global _handler
    _handler = wire_face(FACE_NAME, get_state_fn=get_state_fn)

    # Start Mandos and register Aule init so Mandos can resurrect us
    try:
        from Mandos.mandos import start as mandos_start, register_aule_init
        mandos_start()
        register_aule_init(lambda state: _aule_cold_init(state))
    except Exception as e:
        from Pharos.PtolDmesg import dmesg
        dmesg.error(FACE_NAME, f"Mandos start failed (non-fatal for Aule boot): {e}")

    return _handler


def aule_beat():
    """
    Call on every Aule main loop tick.
    Signals Mandos watchdog that Aule is alive.
    """
    try:
        from Mandos.mandos_watchdog import beat
        beat()
    except Exception:
        pass  # Watchdog failure must not crash the main loop


def _aule_cold_init(state: dict):
    """
    Aule resurrection function registered with Mandos.
    Called by Mandos if Aule dies and needs to be restored from checkpoint.
    Returns a minimal sentinel -- full Aule re-init happens in aule.py main().
    """
    from Pharos.PtolDmesg import dmesg
    dmesg.info(FACE_NAME, f"Aule resurrection called with state keys: {list(state.keys())}")
    # Re-wire on resurrection
    init_aule_wiring()
    return {"resurrected": True, "state": state}
