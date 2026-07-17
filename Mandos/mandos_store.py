"""
MandosStore -- atomic checkpoint store for all Faces.

Written before GC on any FATAL. Keyed by face_name + ISO timestamp.
Holds: navigation state, context buffer head, SMNNIP weights snapshot,
cause of death (error code + message), death timestamp.

PEP 3151 compliant. All failures raise PTL_908 MandosStoreWriteFailed
or PTL_906 MandosRestoreFailed.
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

MANDOS_DIR = Path(__file__).parent / ".mandos_store"
_lock = threading.Lock()


def _ensure_store():
    MANDOS_DIR.mkdir(parents=True, exist_ok=True)


def checkpoint(face_name: str, state: dict) -> Path:
    """
    Atomically write a checkpoint for face_name.
    state must be JSON-serializable.
    Returns the path written.
    Raises MandosStoreWriteFailed (PTL_908) on any failure.
    """
    from Pharos.luthspell_error_handler import MandosStoreWriteFailed
    _ensure_store()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = MANDOS_DIR / f"{face_name}__{ts}.json"
    payload = {"face": face_name, "timestamp": ts, "state": state}
    with _lock:
        try:
            fd, tmp = tempfile.mkstemp(dir=MANDOS_DIR, suffix=".tmp")
            with os.fdopen(fd, "w") as f:
                json.dump(payload, f, indent=2)
            os.replace(tmp, target)
        except Exception as exc:
            raise MandosStoreWriteFailed(
                f"Checkpoint write failed for {face_name}: {exc}"
            ) from exc
    return target


def latest(face_name: str):
    """
    Return the most recent valid checkpoint for face_name, or None.
    Raises MandosRestoreFailed (PTL_906) if a file exists but is corrupt.
    """
    from Pharos.luthspell_error_handler import MandosRestoreFailed
    _ensure_store()
    candidates = sorted(MANDOS_DIR.glob(f"{face_name}__*.json"), reverse=True)
    for path in candidates:
        try:
            with open(path) as f:
                data = json.load(f)
            if data.get("face") == face_name:
                return data
        except Exception as exc:
            raise MandosRestoreFailed(
                f"Checkpoint deserialization failed for {face_name} ({path.name}): {exc}"
            ) from exc
    return None


def list_dead() -> list:
    """Return list of face names that have checkpoints in the store."""
    _ensure_store()
    names = set()
    for p in MANDOS_DIR.glob("*__*.json"):
        names.add(p.stem.split("__")[0])
    return sorted(names)
