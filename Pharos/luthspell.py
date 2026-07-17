#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy Project — Root Layer
LuthSpell: BUS Controller + Halting Monitor
Belongs to: Ptolemy (overseer), not a Face

Architecture:
  Ptolemy
  └── LuthSpell
      ├── T0/T1 priority arbitration (traffic circle, not binary gate)
      ├── set_boundary()     — marks inference boundary on T1
      ├── check()            — called each inference step
      ├── halt_pass()        — YOU SHALL NOT PASS (boundary marker, not kill)
      ├── Halting Monitor    — internal sensing organ
      └── reports to Ptolemy → Ptolemy issues redirect

Design:
  - LuthSpell has NO state beyond what the blockchain holds
  - Blockchain = source of truth for boundary and halt records
  - Modular: channel names, priority scheme, blockchain backend all swappable
"""

import hashlib
import time
from enum import IntEnum
from typing import Callable, Optional


# ─── Settings (module hooks → Settings tab) ───────────────────────────────────

CHANNEL_PROMPT         = "PROMPT"
CHANNEL_INFERENCE      = "INFERENCE_COORDS"
CHANNEL_LUTHSPELL      = "LUTHSPELL"
BLOCKCHAIN_BACKEND     = "branch"
PRIORITY_SCHEME        = "rotary"

LUTHSPELL_SETTINGS = {
    "channel_prompt":     CHANNEL_PROMPT,
    "channel_inference":  CHANNEL_INFERENCE,
    "channel_luthspell":  CHANNEL_LUTHSPELL,
    "blockchain_backend": BLOCKCHAIN_BACKEND,
    "priority_scheme":    PRIORITY_SCHEME,
}


class Priority(IntEnum):
    T0 = 0
    T1 = 1


class HaltRecord:
    def __init__(self, reason, coords, boundary_hash, timestamp=None):
        self.reason = reason; self.coords = coords
        self.boundary_hash = boundary_hash
        self.timestamp = timestamp or time.time()
    def to_dict(self):
        return {"reason": self.reason, "coords": str(self.coords),
                "boundary_hash": self.boundary_hash, "timestamp": self.timestamp}


class HaltingMonitor:
    def __init__(self):
        self._boundary = None; self._boundary_hash = None
        self._halt_records = []
    def set_boundary(self, coords):
        seed = f"{str(coords)}|{time.time()}"
        self._boundary = coords
        self._boundary_hash = hashlib.sha256(seed.encode()).hexdigest()
        return self._boundary_hash
    def check(self, coords):
        if self._boundary is None: return False, None
        halt, reason = self._evaluate(coords)
        if halt:
            self._halt_records.append(HaltRecord(reason, coords, self._boundary_hash))
        return halt, reason
    def _evaluate(self, coords):  # module hook
        if coords == self._boundary: return True, "boundary_crossed"
        return False, None
    @property
    def boundary_hash(self): return self._boundary_hash
    @property
    def halt_records(self): return list(self._halt_records)


class BusMessage:
    def __init__(self, channel, payload, priority=Priority.T1):
        self.channel = channel; self.payload = payload
        self.priority = priority; self.timestamp = time.time()


# PtolBusStub replaced by real PtolBus
try:
    from Pharos.PtolBus import PtolBus as PtolBusStub
except ImportError:
    class PtolBusStub:  # fallback for standalone testing
        def __init__(self): self._subscribers = {}
        def subscribe(self, channel, handler):
            self._subscribers.setdefault(channel, []).append(handler)
        def publish(self, message):
            for h in self._subscribers.get(message.channel, []): h(message)


class LuthSpell:
    """Ptolemy's BUS controller. Halting Monitor is internal. No persistent state."""
    def __init__(self, bus=None, chain=None, on_halt=None):
        self._bus = bus or PtolBusStub(); self._chain = chain
        self._on_halt = on_halt; self._monitor = HaltingMonitor()
        self._wired = False
    def wire(self):
        self._bus.subscribe(CHANNEL_PROMPT, self._on_prompt)
        self._bus.subscribe(CHANNEL_INFERENCE, self._on_inference_coord)
        self._wired = True
    def _on_prompt(self, msg):
        if msg.priority <= Priority.T1:
            h = self._monitor.set_boundary(msg.payload)
            self._publish(f"boundary_set:{h[:16]}", Priority.T0)
    def _on_inference_coord(self, msg):
        halt, reason = self._monitor.check(msg.payload)
        if halt: self._halt_pass(reason, msg.payload)
    def _halt_pass(self, reason, coords):
        record = HaltRecord(reason, coords, self._monitor.boundary_hash)
        # Use PtolChain AuditChain if no explicit chain provided
        chain = self._chain
        if chain is None:
            try:
                from Callimachus.BlockChain.PtolChain import AuditChain
                chain = AuditChain('luthspell')
            except Exception:
                chain = None
        if chain:
            chain.add_block(record.to_dict())
        self._publish(f"halt:{reason}", Priority.T0)
        if self._on_halt: self._on_halt(record)
    def arbitrate(self, messages):
        if PRIORITY_SCHEME == "rotary": return sorted(messages, key=lambda m: m.priority)
        raise NotImplementedError(f"Priority scheme '{PRIORITY_SCHEME}' not wired")
    def _publish(self, payload, priority=Priority.T0):
        self._bus.publish(BusMessage(CHANNEL_LUTHSPELL, payload, priority))
    def set_boundary(self, coords): return self._monitor.set_boundary(coords)
    def check(self, coords): return self._monitor.check(coords)
    @property
    def halt_records(self): return self._monitor.halt_records
    def __repr__(self): return f"LuthSpell(wired={self._wired}, halts={len(self.halt_records)})"
