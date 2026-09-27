"""
PtolemyDesktop/Aule/system_boxkite.py
======================================
Aule's System Monitor Boxkite — "Method 2: Collapsible System Monitor"
(FourthAgePapers/ScalarContextPropagation/NOTEBOOK_PAPER_PLAN.md §11),
built for real, not stubbed.

Live system state, embedded as a 16-vector, read through the box-kite
machinery already built in ValaQuenta/modules/box_kite/maths.py — no new
maths, this file is wiring plus one honest new design choice (how to turn
raw telemetry into a sedenion) that the paper stub flagged as the actual
open work.

WATCH, NOT POLL (Cody, 2026-09-25): a single background thread updates a
live snapshot continuously. Callers read the latest snapshot instantly —
reading never triggers new sampling work. `get_live_state()` is O(1) and
never blocks on I/O.

Design choices made here, explicit rather than buried:

  - 15 channels, one per imaginary sedenion component e1..e15 (CHANNELS).
    NOTE: e8 is structurally excluded from every Assessor (box_kite.md:
    "e8, the Cayley-Dickson doubling generator" — Assessor upper indices
    only ever land on 9..15). Whatever channel is assigned to e8
    (net_recv_bps, below) will therefore never appear in Assessor-specific
    reads (chart_energy, nearest_assessor) even though it still counts
    toward norm() and is eligible for local_curvature's top-3 pool. Known
    consequence of the existing algebra, not a bug introduced here.

  - The real/e0 component is DERIVED, never measured — no 16th sensor.
    First-pass formula, explicitly not claimed as "the" formula: e0 :=
    RMS of the 15 normalized channel values (an honest "how much is
    happening right now" summary). Open to revision.

  - Collapse detection is a first-pass z-score heuristic on a rolling
    windspeed (local_curvature) history — a real, standard change-point
    method, but NOT validated for this domain. Flagged OPEN, same as the
    windspeed-split finding it's built on (Phase 39).

Version: 0.1 — first build.
"""

from __future__ import annotations

import math
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

# ── reuse the existing box-kite engine, don't reinvent it ──────────────────
# box_kite/__init__.py does `from .tools import ...`, which relative-imports
# `...engine.registry` -- that requires ValaQuenta itself to be the package
# root (ThePlace on sys.path, imported as "ValaQuenta.modules.box_kite..."),
# not ValaQuenta's own contents flattened onto sys.path.
_THEPLACE = Path(__file__).resolve().parents[2]
if str(_THEPLACE) not in sys.path:
    sys.path.insert(0, str(_THEPLACE))
from ValaQuenta.modules.box_kite import maths as box_kite  # noqa: E402

# ── defensive Aule import — silent no-op if Aule isn't running ─────────────
try:
    from aule import stream_event as _emit
except ImportError:
    def _emit(channel: str, event_type: str, payload: dict = None, **kwargs):
        pass

CHANNEL_NAME = "system_boxkite"

# ── the 15 channels, in sedenion imaginary-index order 1..15 ───────────────
CHANNELS: List[str] = [
    "cpu_percent",            # e1
    "mem_used_percent",       # e2
    "mem_available_percent",  # e3
    "swap_used_percent",      # e4
    "disk_read_bps",          # e5
    "disk_write_bps",         # e6
    "disk_iops",              # e7
    "net_recv_bps",           # e8  -- outside every Assessor, see module docstring
    "net_sent_bps",           # e9
    "process_count",          # e10
    "thread_count",           # e11
    "load1",                  # e12
    "load5",                  # e13
    "load15",                 # e14
    "ctx_switches_per_sec",   # e15
]
assert len(CHANNELS) == 15

# Reference scales for squashing wildly-different-unit metrics into a
# roughly [0, ~2] range. Not calibrated against real workloads yet --
# first-pass, documented, meant to be replaced with measured references.
_LOG_REF = {
    "disk_read_bps": 1e8, "disk_write_bps": 1e8, "disk_iops": 1e4,
    "net_recv_bps": 1e8, "net_sent_bps": 1e8,
    # process_count/thread_count originally 500/2000 -- measured on the
    # reference machine (idle-ish desktop) at ~0.93-0.94 on that scale,
    # i.e. already saturated regardless of activity. Raised from one real
    # measurement, not recalibrated against a real workload sweep -- still
    # first-pass, now less obviously wrong.
    "process_count": 1000.0, "thread_count": 8000.0,
    "ctx_switches_per_sec": 5e5,
}

# psutil reports these as monotonically-increasing totals since boot, not
# rates. Feeding raw totals into the vector would make it read as constant
# for hours (a few KB/s of change against gigabytes already transferred is
# invisible) -- caught by the first live run of this file, where windspeed
# and peak_dim never moved across 8 ticks despite CPU% visibly changing.
# These get delta'd against the previous sample, per second, before scaling.
_RATE_CHANNELS = {"disk_read_bps", "disk_write_bps", "disk_iops",
                   "net_recv_bps", "net_sent_bps", "ctx_switches_per_sec"}


def _log_scale(value: float, ref: float) -> float:
    """log1p squashing against a reference scale -- 0 at value=0, ~1 near ref."""
    return math.log1p(max(0.0, value)) / math.log1p(ref)


@dataclass
class RawSample:
    values: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0


def sample_raw() -> RawSample:
    """One direct psutil read. Called only by the watcher thread, never by
    a consumer -- this is the 'poll' half, deliberately hidden behind the
    'watch' interface below."""
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    disk = psutil.disk_io_counters()
    net = psutil.net_io_counters()
    load1, load5, load15 = psutil.getloadavg()
    ncpu = psutil.cpu_count() or 1
    ctx = psutil.cpu_stats().ctx_switches

    values = {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "mem_used_percent": vm.percent,
        "mem_available_percent": 100.0 * vm.available / vm.total if vm.total else 0.0,
        "swap_used_percent": sw.percent,
        "disk_read_bps": getattr(disk, "read_bytes", 0),
        "disk_write_bps": getattr(disk, "write_bytes", 0),
        "disk_iops": getattr(disk, "read_count", 0) + getattr(disk, "write_count", 0),
        "net_recv_bps": getattr(net, "bytes_recv", 0),
        "net_sent_bps": getattr(net, "bytes_sent", 0),
        "process_count": len(psutil.pids()),
        "thread_count": sum((p.info.get("num_threads") or 0)
                             for p in psutil.process_iter(["num_threads"])),
        "load1": 100.0 * load1 / ncpu,
        "load5": 100.0 * load5 / ncpu,
        "load15": 100.0 * load15 / ncpu,
        "ctx_switches_per_sec": ctx,
    }
    return RawSample(values=values, timestamp=time.time())


class SystemBoxkiteWatcher:
    """
    WATCH, not poll: a background thread keeps one live snapshot fresh.
    Consumers call get_live_state() / get_vector() and read instantly --
    they never trigger a psutil call themselves.
    """

    def __init__(self, interval: float = 1.0, windspeed_history: int = 30):
        self.interval = interval
        self._lock = threading.Lock()
        self._latest: Optional[RawSample] = None
        self._prev_counters: Optional[RawSample] = None
        self._vector: List[float] = [0.0] * 16
        self._windspeed_history: deque = deque(maxlen=windspeed_history)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── lifecycle ───────────────────────────────────────────────────────
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True,
                                         name="SystemBoxkiteWatcher")
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)

    def _run(self):
        psutil.cpu_percent(interval=None)  # prime it; first call is always 0.0
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                _emit(CHANNEL_NAME, "watcher_error", {"error": str(e)})
            self._stop.wait(self.interval)

    def _tick(self):
        sample = sample_raw()
        rates = self._to_rates(sample)
        vector = self._build_vector(rates)
        windspeed = box_kite.local_curvature(vector)

        with self._lock:
            self._prev_counters = self._latest
            self._latest = sample
            self._vector = vector
            collapsed = self._check_collapse(windspeed)
            self._windspeed_history.append(windspeed)

        if collapsed is not None:
            self._handle_collapse(vector, windspeed, collapsed)

    def _to_rates(self, sample: RawSample) -> Dict[str, float]:
        """Counter channels become per-second deltas against the previous
        sample; everything else passes through unchanged. First tick (no
        previous sample) reports 0 for the rate channels, not the raw total."""
        out = dict(sample.values)
        prev = self._prev_counters
        if prev is None:
            dt = None
        else:
            dt = sample.timestamp - prev.timestamp
        for name in _RATE_CHANNELS:
            if prev is None or not dt or dt <= 0:
                out[name] = 0.0
            else:
                out[name] = max(0.0, (sample.values[name] - prev.values[name]) / dt)
        return out

    # ── vector construction ────────────────────────────────────────────
    def _build_vector(self, values: Dict[str, float]) -> List[float]:
        imag: List[float] = []
        for name in CHANNELS:
            raw = values[name]
            if name in _LOG_REF:
                imag.append(_log_scale(raw, _LOG_REF[name]))
            else:
                imag.append(raw / 100.0)  # percentages -> [0, ~1(+)]

        # e0: derived, never measured -- RMS of the 15 imaginary readings.
        e0 = math.sqrt(sum(x * x for x in imag) / len(imag)) if imag else 0.0
        return [e0] + imag

    # ── collapse detection (first-pass, OPEN, not validated) ───────────
    def _check_collapse(self, windspeed: float) -> Optional[Dict[str, float]]:
        hist = self._windspeed_history
        if len(hist) < 5:
            return None
        mean = sum(hist) / len(hist)
        var = sum((x - mean) ** 2 for x in hist) / len(hist)
        std = math.sqrt(var)
        if std < 1e-9:
            return None
        z = (windspeed - mean) / std
        if abs(z) >= 3.0:  # first-pass threshold, not tuned
            return {"z": z, "mean": mean, "std": std, "windspeed": windspeed}
        return None

    def _handle_collapse(self, vector: List[float], windspeed: float,
                          stats: Dict[str, float]):
        chart = box_kite.chart_of(vector, check_zd=False)
        r = chart["peak_dim"] if 1 <= chart["peak_dim"] <= 15 else chart["dominant_chart"]
        try:
            pencil = box_kite.pencil(r) if 1 <= r <= 15 else None
        except ValueError:
            pencil = None

        event = {
            "point": r,
            "pencil": pencil,
            "windspeed": windspeed,
            "z_score": stats["z"],
            "fixed_point_weight": chart["fixed_point_weight"],
            "nearest_assessor": chart["nearest_assessor"],
        }
        _emit(CHANNEL_NAME, "collapse", event)

    # ── public read interface — instant, never blocks ──────────────────
    def get_live_state(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if self._latest is None:
                return None
            return {
                "timestamp": self._latest.timestamp,
                "raw": dict(self._latest.values),
                "vector": list(self._vector),
            }

    def get_vector(self) -> List[float]:
        with self._lock:
            return list(self._vector)

    def get_windspeed_history(self) -> List[float]:
        with self._lock:
            return list(self._windspeed_history)


# ── module-level singleton, matching the _aule_channel() convention ───────
_watcher: Optional[SystemBoxkiteWatcher] = None


def get_watcher(interval: float = 1.0) -> SystemBoxkiteWatcher:
    global _watcher
    if _watcher is None:
        _watcher = SystemBoxkiteWatcher(interval=interval)
        _watcher.start()
        _emit(CHANNEL_NAME, "watcher_start", {"interval": interval})
    return _watcher


if __name__ == "__main__":
    print("=" * 78)
    print("Aule System Monitor Boxkite -- self-test (watch, not poll)")
    print("=" * 78)
    w = get_watcher(interval=0.5)
    for i in range(8):
        time.sleep(0.6)
        state = w.get_live_state()
        if state is None:
            print(f"[{i}] no data yet")
            continue
        v = state["vector"]
        chart = box_kite.chart_of(v, check_zd=False)
        print(f"[{i}] e0={v[0]:.4f}  windspeed={box_kite.local_curvature(v):.4f}  "
              f"peak_dim={chart['peak_dim']:>2}  "
              f"fixed_point_weight={chart['fixed_point_weight']:.4f}  "
              f"cpu%={state['raw']['cpu_percent']:.1f}  "
              f"mem%={state['raw']['mem_used_percent']:.1f}")
    w.stop()
    print("stopped cleanly.")
