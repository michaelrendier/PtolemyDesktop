"""
MandosWatchdog -- heartbeat monitor for Aule.

Mandos watches Aule. If Aule misses MISSED_BEATS consecutive heartbeats,
Mandos declares Aule dead, raises PTL_909 AuleWatchdogTimeout, and gains
supervisor priority.

Aule calls watchdog.beat() on its main loop tick.
"""

import threading
import time

HEARTBEAT_INTERVAL = 5.0
MISSED_BEATS       = 3

_last_beat = 0.0
_lock      = threading.Lock()
_running   = False
_thread    = None
_on_aule_dead = None


def beat():
    """Called by Aule on each main loop tick to signal it is alive."""
    global _last_beat
    with _lock:
        _last_beat = time.monotonic()


def _watch_loop():
    global _running
    missed = 0
    while _running:
        time.sleep(HEARTBEAT_INTERVAL)
        with _lock:
            age = time.monotonic() - _last_beat
        if age > HEARTBEAT_INTERVAL:
            missed += 1
        else:
            missed = 0
        if missed >= MISSED_BEATS:
            _running = False
            _declare_aule_dead()
            return


def _declare_aule_dead():
    from Pharos.luthspell_error_handler import AuleWatchdogTimeout
    from Pharos.PtolDmesg import dmesg
    err = AuleWatchdogTimeout("Aule missed heartbeat -- Mandos gains priority.")
    dmesg.fatal("Mandos", str(err))
    if _on_aule_dead is not None:
        _on_aule_dead(err)


def start(on_aule_dead=None):
    global _running, _thread, _last_beat, _on_aule_dead
    _last_beat    = time.monotonic()
    _on_aule_dead = on_aule_dead
    _running      = True
    _thread = threading.Thread(target=_watch_loop, daemon=True, name="MandosWatchdog")
    _thread.start()


def stop():
    global _running
    _running = False
