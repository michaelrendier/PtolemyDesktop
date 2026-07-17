"""
MandosResurrect -- Face restoration protocol.

Called by Aule (normal path) or Mandos (Aule-down path).
Pulls latest checkpoint, hands to Face init, verifies SMNNIP conservation
before marking Face live.

Raises PTL_906 MandosRestoreFailed if checkpoint is absent or conservation fails.
"""

from Mandos.mandos_store import latest
from Pharos.PtolDmesg import dmesg

FACE_NAME = "Mandos"


def resurrect(face_name: str, face_init_fn, smnnip_verify_fn=None):
    """
    Restore face_name from its latest checkpoint.

    face_init_fn(state: dict) -> Face instance
    smnnip_verify_fn(state: dict) -> bool  (optional conservation check)

    Returns the restored Face instance.
    Raises MandosRestoreFailed if checkpoint absent or conservation fails.
    """
    from Pharos.luthspell_error_handler import MandosRestoreFailed

    cp = latest(face_name)
    if cp is None:
        dmesg.error(FACE_NAME, f"No checkpoint found for {face_name} -- cold boot required.")
        raise MandosRestoreFailed(f"No checkpoint found for {face_name}.")

    state = cp.get("state", {})

    if smnnip_verify_fn is not None:
        if not smnnip_verify_fn(state):
            raise MandosRestoreFailed(
                f"SMNNIP conservation check failed on restored state for {face_name}."
            )

    try:
        instance = face_init_fn(state)
    except Exception as exc:
        raise MandosRestoreFailed(
            f"Face init from checkpoint failed for {face_name}: {exc}"
        ) from exc

    dmesg.info(FACE_NAME, f"{face_name} resurrected from checkpoint {cp['timestamp']}.")
    return instance
