#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
PtolBus.py — Ptolemy Message Bus (complete implementation)
===========================================================
Pharos Layer

Architecture flags implemented:
  BUS_IS_THREADS        — Bus owns and IS the thread pool. Ptolemy hands
                          a ResourceBudget at start. Bus manages internally.
  FACE_POST_BOOT        — No Face exists until POST completes. Bus rejects
                          messages to/from unregistered Faces (strict mode).
  PER_FACE_STDIO        — Each Face gets CH_FACE_IN/OUT/ERR channel triple
                          + 4 thread slots (stdin, stdout, stderr, work).
  THREAD_POOL_DYNAMIC   — Ptolemy reserves 5 kernel slots (T0-T4). Per-Face
                          minimum 4. Aule sizes the rest via grant/deny hooks.
  ALL_BUS_EVENTS_TO_DMESG — Every Bus event writes to PtolDmesg. Aule
                          watches dmesg only. Bus never calls Aule directly.
  EARLY_SYMPTOM_DETECTION — HealthMonitor tracks queue backpressure, thread
                          starvation approach. Symptom level 0.0–1.0 on
                          symptom_level_changed signal → TuningDisplay gradient.
  CYCLIC_CONTEXT_BUFFER_SHARED — CH_CONTEXT channel; Ptolemy kernel calls
                          broadcast_context_update(). All Faces read from it.
  LICH (interface)      — engage_emergency(lich): Lich takes authority over
                          Bus during emergency. Bus inversion of authority.

Rotary Semaphore:
  T0 — system / critical    (always first, right of way)
  T1 — user / normal        (right of way)
  T2-T4 — autonomous        (yield in rotary, nice+10 equivalent)
  Within each tier: FIFO by timestamp.

Thread pool:
  Kernel slots K0-K4: permanent, never parked by Bus.
    K0 = BusDispatch (internal queue drain)
    K1 = UserDirective
    K2-K4 = Autonomous (parked on Full Attention Please)
  Face slots: allocated on POST.
    {face_id}_stdin, {face_id}_stdout, {face_id}_stderr, {face_id}_work
  Additional slots: Face requests via CH_LOG → dmesg → Aule.
"""

import time
import queue
import threading
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, QThread, QMutex, QMutexLocker, pyqtSignal

try:
    from Pharos.PtolDmesg import dmesg as _dmesg
except ImportError:
    _dmesg = None

def _log(message: str, severity: str = '') -> None:
    if _dmesg is None:
        return
    if severity == 'WARN':
        _dmesg.warn('ptolemybus', message)
    elif severity == 'ERROR':
        _dmesg.error('ptolemybus', message)
    elif severity == 'FATAL':
        _dmesg.fatal('ptolemybus', message)
    else:
        _dmesg.write('ptolemybus', message)


# ── Channel names ─────────────────────────────────────────────────────────────

CH_PROMPT     = "PROMPT"
CH_INFERENCE  = "INFERENCE_COORDS"
CH_LUTHSPELL  = "LUTHSPELL"
CH_FACE_EVENT = "FACE_EVENT"
CH_SENSOR     = "SENSOR"
CH_LOG        = "LOG"
CH_BLOCKCHAIN = "BLOCKCHAIN"
CH_SETTINGS   = "SETTINGS"
CH_CONTEXT    = "CONTEXT"        # CyclicContextBuffer broadcasts (shared)
CH_DMESG      = "DMESG"          # Bus-internal events reflected to dmesg
CH_LEARN      = "LEARN"          # Passive text learning — any face publishes text here


# ── Priority ──────────────────────────────────────────────────────────────────

class Priority(IntEnum):
    T0 = 0   # system / critical — always first, right of way
    T1 = 1   # user / normal     — right of way
    T2 = 2   # autonomous        — yields in rotary
    T3 = 3   # autonomous        — yields
    T4 = 4   # autonomous        — lowest, yields


# ── Settings ──────────────────────────────────────────────────────────────────

PTOL_BUS_SETTINGS = {
    "priority_scheme":      "rotary",
    "queue_maxsize":        1024,
    "dispatch_interval_ms": 10,
    "log_channel":          CH_LOG,
    "strict_post":          False,   # if True: reject msgs from unregistered Faces
    "health_poll_interval": 5,       # seconds between HealthMonitor polls
    "max_face_threads":     40,      # soft cap; Aule can raise
}


# ── ResourceBudget ────────────────────────────────────────────────────────────

@dataclass
class ResourceBudget:
    """
    Ptolemy hands this to Bus at startup via Bus.handshake().
    Bus manages allocation internally within this budget.
    """
    kernel_threads:     int = 5     # K0-K4, permanent, never parked
    max_face_threads:   int = 40    # soft cap
    dispatch_interval_ms: int = 10
    queue_maxsize:      int = 1024


# ── FaceRecord ────────────────────────────────────────────────────────────────

@dataclass
class FaceRecord:
    """
    Per-Face registration record. Created by post_face(). No Face exists
    to the system until its FaceRecord state reaches 'active'.
    """
    face_id:       str
    name:          str
    subscriptions: List[str]     # channels registered at POST
    thread_req:    int           # threads requested at POST
    thread_alloc:  int   = 0     # threads actually granted
    ch_in:         str   = ''    # CH_FACE_IN_{face_id}
    ch_out:        str   = ''    # CH_FACE_OUT_{face_id}
    ch_err:        str   = ''    # CH_FACE_ERR_{face_id}
    state:         str   = 'posting'  # posting → active → suspended → terminated
    post_time:     float = 0.0


# ── ThreadSlot ────────────────────────────────────────────────────────────────

@dataclass
class ThreadSlot:
    """One managed thread in the Bus-owned pool."""
    slot_id:    str
    role:       str                  # 'dispatch', 'kernel_K1', 'face_stdin', …
    face_id:    Optional[str]        # None = kernel slot
    thread:     Optional[QThread]    # None = unallocated
    state:      str = 'unallocated'  # unallocated | idle | running | parked
    wait_start: float = 0.0          # time.time() when parked; 0 = not parked


# ── BusMessage ────────────────────────────────────────────────────────────────

class BusMessage:
    """Atomic unit on the bus."""
    __slots__ = ('channel', 'payload', 'priority', 'timestamp', 'sender')

    def __init__(self, channel: str, payload,
                 priority: Priority = Priority.T1,
                 sender: str = None):
        self.channel   = channel
        self.payload   = payload
        self.priority  = priority
        self.timestamp = time.time()
        self.sender    = sender

    def __lt__(self, other):
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp < other.timestamp

    def __repr__(self):
        return (f"BusMessage(ch={self.channel!r}, pri={self.priority.name}, "
                f"sender={self.sender!r})")


# ── HealthMonitor — EARLY_SYMPTOM_DETECTION ──────────────────────────────────

class HealthMonitor:
    """
    Tracks system health from Bus metrics. Symptom level 0.0–1.0.
    Zero = nominal. One = critical intervention needed.

    Monitors:
      - Queue depth growth rate (backpressure indicator)
      - Thread starvation approach (long park times)
      - Queue depth absolute (overload indicator)

    Connects to TuningDisplay via bus.symptom_level_changed signal.
    """

    _WINDOW          = 12    # samples in moving window
    _BACKPRESSURE_CAP = 50   # queue depth delta/poll that maxes symptom
    _DEPTH_CAP        = 800  # absolute queue depth that triggers warning
    _STARVATION_SEC   = 30.0 # seconds parked before flagging starvation

    def __init__(self, bus: 'PtolBus'):
        self._bus            = bus
        self._depth_history  = deque(maxlen=self._WINDOW)
        self._symptom        = 0.0
        self._last_poll      = time.time()

    def poll(self) -> float:
        now   = time.time()
        depth = self._bus.queue_depth()
        self._depth_history.append((now, depth))

        scores = []

        # Backpressure: rate of queue growth
        if len(self._depth_history) >= 2:
            _, d0 = self._depth_history[-2]
            _, d1 = self._depth_history[-1]
            delta = max(0, d1 - d0)
            scores.append(min(1.0, delta / self._BACKPRESSURE_CAP))

        # Absolute depth
        scores.append(min(1.0, depth / self._DEPTH_CAP))

        # Thread starvation: any slot parked longer than threshold?
        starvation = 0.0
        for slot in self._bus._thread_pool.values():
            if slot.state == 'parked' and slot.wait_start > 0:
                waited = now - slot.wait_start
                starvation = max(starvation,
                                 min(1.0, waited / self._STARVATION_SEC))
        scores.append(starvation)

        self._symptom = max(scores) if scores else 0.0
        self._last_poll = now
        return self._symptom

    @property
    def symptom_level(self) -> float:
        return self._symptom

    def report(self) -> dict:
        depths = [d for _, d in self._depth_history]
        return {
            'symptom_level':  self._symptom,
            'queue_depth':    self._bus.queue_depth(),
            'depth_history':  depths,
            'depth_delta':    (depths[-1] - depths[-2]) if len(depths) >= 2 else 0,
        }


# ── _DispatchThread ───────────────────────────────────────────────────────────

class _DispatchThread(QThread):
    """
    K0 — Bus internal dispatch worker. Permanent, never parked.
    Drains priority queue, delivers to subscribers, polls HealthMonitor.
    """

    def __init__(self, bus: 'PtolBus'):
        super().__init__(bus)
        self._bus    = bus
        self._active = True
        self.setObjectName('PtolBus_K0_dispatch')

    def stop(self):
        self._active = False

    def run(self):
        self.setPriority(QThread.Priority.HighPriority)
        _log('K0 dispatch thread started')
        interval   = self._bus._budget.dispatch_interval_ms / 1000.0
        poll_every = max(1, int(PTOL_BUS_SETTINGS['health_poll_interval'] / interval))
        tick       = 0
        while self._active:
            self._bus._drain()
            tick += 1
            if tick % poll_every == 0:
                level = self._bus._health.poll()
                if level > 0.0:
                    self._bus.symptom_level_changed.emit(level)
                    if level >= 0.75:
                        _log(f'symptom_level={level:.2f} — intervention advised', 'WARN')
            time.sleep(interval)
        _log('K0 dispatch thread stopped')


# ── PtolBus ───────────────────────────────────────────────────────────────────

class PtolBus(QObject):
    """
    Ptolemy Message Bus — complete implementation.

    Lifecycle:
        bus = PtolBus(ptolemy)
        bus.handshake(ResourceBudget(...))   # optional — uses defaults if skipped
        bus.start()                          # starts K0 dispatch thread

        rec = bus.post_face('pharos', 'Pharos', [CH_PROMPT], thread_req=4)
        bus.subscribe(CH_PROMPT, my_handler)
        bus.publish(BusMessage(CH_PROMPT, "hello"))
        bus.stop()

    Convenience:
        bus.emit(channel, payload, priority=Priority.T1, sender=None)

    Context broadcast (Ptolemy kernel only):
        bus.broadcast_context_update({'layer': 1, 'data': ...})

    Lich emergency:
        bus.engage_emergency(lich_instance)
    """

    # ── Signals ───────────────────────────────────────────────────────────────
    message_dispatched    = pyqtSignal(str, str)    # channel, sender
    face_posted           = pyqtSignal(str)          # face_id
    face_unposted         = pyqtSignal(str)          # face_id
    thread_allocated      = pyqtSignal(str, int)     # face_id, count
    symptom_level_changed = pyqtSignal(float)        # 0.0–1.0
    emergency_engaged     = pyqtSignal(str)          # reason

    def __init__(self, ptolemy=None, parent=None):
        super().__init__(parent or ptolemy)
        self.Ptolemy = ptolemy

        # ── Message queue ─────────────────────────────────────────────────────
        self._budget    = ResourceBudget()
        self._queue     = queue.PriorityQueue(maxsize=self._budget.queue_maxsize)
        self._seq       = 0
        self._mutex     = QMutex()

        # ── Subscribers ───────────────────────────────────────────────────────
        self._subscribers: Dict[str, List[Callable]] = {}

        # ── Thread pool ───────────────────────────────────────────────────────
        self._thread_pool: Dict[str, ThreadSlot] = {}
        self._thread:      _DispatchThread        = _DispatchThread(self)

        # ── Face registry ─────────────────────────────────────────────────────
        self._face_registry: Dict[str, FaceRecord] = {}
        self._strict_post = PTOL_BUS_SETTINGS['strict_post']

        # ── Health monitor ────────────────────────────────────────────────────
        self._health = HealthMonitor(self)

        # ── Lich reference ────────────────────────────────────────────────────
        self._lich = None

    # ── Handshake / Init ──────────────────────────────────────────────────────

    def handshake(self, budget: ResourceBudget) -> None:
        """
        Ptolemy calls this once at startup to hand Bus its resource budget.
        Bus manages all allocation internally from this point.
        Optional — Bus uses ResourceBudget defaults if not called.
        """
        self._budget = budget
        self._queue  = queue.PriorityQueue(maxsize=budget.queue_maxsize)
        self._thread._bus = self
        _log(f'handshake — kernel_threads={budget.kernel_threads} '
             f'max_face_threads={budget.max_face_threads}')
        self._init_kernel_slots()

    def _init_kernel_slots(self) -> None:
        """Initialise K0-K4 kernel thread slots. K0 = dispatch thread."""
        roles = ['dispatch', 'user_directive',
                 'autonomous_K2', 'autonomous_K3', 'autonomous_K4']
        for i in range(self._budget.kernel_threads):
            slot_id = f'kernel_K{i}'
            self._thread_pool[slot_id] = ThreadSlot(
                slot_id  = slot_id,
                role     = roles[i] if i < len(roles) else f'kernel_K{i}',
                face_id  = None,
                thread   = self._thread if i == 0 else None,
                state    = 'running' if i == 0 else 'unallocated',
            )
        _log(f'kernel slots initialised: {list(self._thread_pool.keys())}')

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start K0 dispatch thread. Initialise kernel slots if not done."""
        if not self._thread_pool:
            self._init_kernel_slots()
        self._thread.start()
        _log('bus started — K0 dispatch running')

    def stop(self) -> None:
        """Graceful shutdown: drain queue, stop K0, park all face threads."""
        self._thread.stop()
        self._thread.quit()
        self._thread.wait(2000)
        for slot in self._thread_pool.values():
            if slot.thread and slot.thread is not self._thread:
                slot.thread.quit()
                slot.thread.wait(1000)
        _log('bus stopped — all threads halted')

    # ── FACE_POST_BOOT ────────────────────────────────────────────────────────

    def post_face(self, face_id: str, name: str,
                  subscriptions: List[str],
                  thread_req: int = 4) -> FaceRecord:
        """
        Face.POST() — register a Face with the Bus.
        Allocates stdio channel triple and thread slots.
        No Face exists to the system until this completes successfully.
        Returns the FaceRecord.
        """
        with QMutexLocker(self._mutex):
            if face_id in self._face_registry:
                _log(f'POST duplicate: {face_id} already registered', 'WARN')
                return self._face_registry[face_id]

        ch_in, ch_out, ch_err = self._alloc_stdio(face_id)
        alloc = self._alloc_face_threads(face_id, thread_req)

        rec = FaceRecord(
            face_id       = face_id,
            name          = name,
            subscriptions = subscriptions,
            thread_req    = thread_req,
            thread_alloc  = alloc,
            ch_in         = ch_in,
            ch_out        = ch_out,
            ch_err        = ch_err,
            state         = 'active',
            post_time     = time.time(),
        )

        with QMutexLocker(self._mutex):
            self._face_registry[face_id] = rec
            for ch in subscriptions:
                self._subscribers.setdefault(ch, [])

        _log(f'POST {name} ({face_id}) — channels: {ch_in}/{ch_out}/{ch_err} '
             f'threads: {alloc}/{thread_req}')
        if _dmesg:
            _dmesg.post(name.lower(), passed=True,
                        detail=f'bus registered — {alloc} threads')
        self.face_posted.emit(face_id)
        return rec

    def unpost_face(self, face_id: str) -> None:
        """Face shutdown — deregister and release thread slots."""
        with QMutexLocker(self._mutex):
            rec = self._face_registry.pop(face_id, None)
        if rec is None:
            return
        self._release_face_threads(face_id)
        rec.state = 'terminated'
        _log(f'UNPOST {rec.name} ({face_id})')
        self.face_unposted.emit(face_id)

    def is_posted(self, face_id: str) -> bool:
        return face_id in self._face_registry

    def face_record(self, face_id: str) -> Optional[FaceRecord]:
        return self._face_registry.get(face_id)

    def posted_faces(self) -> List[str]:
        return list(self._face_registry.keys())

    # ── PER_FACE_STDIO ────────────────────────────────────────────────────────

    def _alloc_stdio(self, face_id: str) -> tuple:
        """Allocate CH_FACE_IN/OUT/ERR channel triple for a Face."""
        return (f'FACE_IN_{face_id}',
                f'FACE_OUT_{face_id}',
                f'FACE_ERR_{face_id}')

    # ── THREAD_POOL_DYNAMIC ───────────────────────────────────────────────────

    def _alloc_face_threads(self, face_id: str, count: int) -> int:
        """
        Allocate thread slots for a Face.
        First 4 roles are canonical stdio triple + work. Beyond 4: extra_N.
        Returns actual number allocated.
        """
        _roles = ['stdin', 'stdout', 'stderr', 'work']
        allocated = 0
        for i in range(count):
            role     = _roles[i] if i < len(_roles) else f'extra_{i}'
            slot_id  = f'{face_id}_{role}'
            self._thread_pool[slot_id] = ThreadSlot(
                slot_id = slot_id,
                role    = f'face_{role}',
                face_id = face_id,
                thread  = None,
                state   = 'idle',
            )
            allocated += 1
        _log(f'thread_alloc {face_id}: {allocated} slots')
        self.thread_allocated.emit(face_id, allocated)
        return allocated

    def _release_face_threads(self, face_id: str) -> None:
        """Release all thread slots belonging to a Face."""
        to_remove = [sid for sid, s in self._thread_pool.items()
                     if s.face_id == face_id]
        for sid in to_remove:
            slot = self._thread_pool.pop(sid)
            if slot.thread:
                slot.thread.quit()
                slot.thread.wait(500)
        if to_remove:
            _log(f'thread_release {face_id}: freed {len(to_remove)} slots')

    def request_threads(self, face_id: str, count: int) -> None:
        """
        Face requests additional threads beyond the POST allocation.
        Routes to Aule via CH_LOG → dmesg. Aule calls _aule_grant/deny.
        """
        self.emit(CH_LOG, {
            'type':             'thread_request',
            'face_id':          face_id,
            'slots_requested':  count,
        }, Priority.T0, sender='PtolBus')
        _log(f'thread_request: {face_id} wants {count} additional slots')

    def _aule_grant(self, face_id: str, slots: int) -> None:
        """Aule calls this to grant a thread allocation request."""
        alloc = self._alloc_face_threads(face_id, slots)
        rec   = self._face_registry.get(face_id)
        if rec:
            rec.thread_alloc += alloc
        _log(f'aule_grant: {face_id} +{alloc} slots (total={rec.thread_alloc if rec else alloc})')

    def _aule_deny(self, face_id: str, reason: str = '') -> None:
        """Aule calls this to deny a thread allocation request."""
        _log(f'aule_deny: {face_id} — {reason}', 'WARN')
        self.emit(CH_LOG, {
            'type':    'thread_denied',
            'face_id': face_id,
            'reason':  reason,
        }, Priority.T1, sender='PtolBus')

    def park_autonomous(self) -> None:
        """
        Full Attention Please — park K2/K3/K4 (autonomous slots).
        Threads finish current atomic op, then park. Not killed.
        """
        for slot in self._thread_pool.values():
            if slot.role in ('autonomous_K2', 'autonomous_K3', 'autonomous_K4'):
                if slot.state == 'running':
                    slot.state      = 'parked'
                    slot.wait_start = time.time()
        _log('autonomous threads K2-K4 parked (Full Attention Please)')

    def resume_autonomous(self) -> None:
        """Resume K2/K3/K4 from parked state."""
        for slot in self._thread_pool.values():
            if slot.role in ('autonomous_K2', 'autonomous_K3', 'autonomous_K4'):
                if slot.state == 'parked':
                    slot.state      = 'running'
                    slot.wait_start = 0.0
        _log('autonomous threads K2-K4 resumed')

    # ── Pub/Sub ───────────────────────────────────────────────────────────────

    def subscribe(self, channel: str, handler: Callable,
                  face_id: str = None) -> None:
        """Register handler for channel. Thread-safe."""
        with QMutexLocker(self._mutex):
            self._subscribers.setdefault(channel, [])
            if handler not in self._subscribers[channel]:
                self._subscribers[channel].append(handler)

    def unsubscribe(self, channel: str, handler: Callable) -> None:
        with QMutexLocker(self._mutex):
            subs = self._subscribers.get(channel, [])
            if handler in subs:
                subs.remove(handler)

    def publish(self, message: BusMessage) -> None:
        """
        Enqueue message. Non-blocking.
        T0 messages: force-insert on full queue (evict oldest T1).
        T1-T4 messages: silently dropped if queue full.
        """
        if self._strict_post and message.sender:
            if (message.sender not in ('PtolBus', 'ptolemy') and
                    message.sender not in self._face_registry):
                _log(f'REJECT unregistered sender: {message.sender}', 'WARN')
                return

        self._seq += 1
        try:
            self._queue.put_nowait((message.priority, self._seq, message))
        except queue.Full:
            if message.priority == Priority.T0:
                self._evict_and_insert(message)
            else:
                _log(f'queue full — dropped {message.channel} from {message.sender}',
                     'WARN')

    def emit(self, channel: str, payload,
             priority: Priority = Priority.T1,
             sender: str = None) -> None:
        """Convenience: build and publish a BusMessage."""
        self.publish(BusMessage(channel, payload, priority, sender))

    # ── CYCLIC_CONTEXT_BUFFER_SHARED ──────────────────────────────────────────

    def broadcast_context_update(self, payload) -> None:
        """
        Ptolemy kernel calls this when CyclicContextBuffer has a new context
        slice. All Faces subscribed to CH_CONTEXT receive it.
        CCB is owned by Ptolemy kernel — Bus delivers, does not own.
        """
        self.emit(CH_CONTEXT, payload, Priority.T1, sender='ptolemy')

    # ── LICH interface ────────────────────────────────────────────────────────

    def engage_emergency(self, lich, reason: str = 'emergency') -> None:
        """
        Lich calls this during emergency. Lich takes authority over Bus.
        Inversion: normally Bus manages Faces; in emergency Lich manages Bus.

        Lich.engage() sequence (orchestrated by Lich, not Bus):
          1. graceful Face quit
          2. stop SMIP distribution
          3. flush caches
          4. force-terminate stragglers
          5. Desktop stays up
          6. Bus restarts clean under Lich
          7. Aule gets full thread pool authority

        Bus role here: drain T1-T4, keep T0 (dispatch) alive.
        """
        self._lich = lich
        _log(f'EMERGENCY engaged — Lich has authority. Reason: {reason}', 'WARN')
        self.emergency_engaged.emit(reason)

        # Drain all non-critical messages from queue
        drained = 0
        while not self._queue.empty():
            try:
                pri, _, msg = self._queue.get_nowait()
                if pri == Priority.T0:
                    self._queue.put_nowait((pri, self._seq, msg))
            except queue.Empty:
                break
            drained += 1
        if drained:
            _log(f'emergency drain: removed {drained} non-T0 messages')

        # Park all autonomous slots
        self.park_autonomous()

    def disengage_emergency(self) -> None:
        """Lich calls this when system is stable. Bus resumes normal authority."""
        self._lich = None
        self.resume_autonomous()
        _log('emergency disengaged — Bus resuming normal authority')

    # ── Internal ──────────────────────────────────────────────────────────────

    def _evict_and_insert(self, message: BusMessage) -> None:
        """T0 critical: evict oldest non-T0 item to make room."""
        items   = []
        evicted = False
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                if not evicted and item[0] != Priority.T0:
                    evicted = True
                else:
                    items.append(item)
            except queue.Empty:
                break
        for item in items:
            try:
                self._queue.put_nowait(item)
            except queue.Full:
                break
        self._seq += 1
        try:
            self._queue.put_nowait((message.priority, self._seq, message))
        except queue.Full:
            _log('T0 eviction failed — queue still full', 'ERROR')

    def _drain(self) -> None:
        """
        Called by K0 dispatch thread.
        Rotary scheme: drain ALL T0 → then ALL T1 → then T2-T4 in order.
        """
        buckets: Dict[int, list] = {0: [], 1: [], 2: [], 3: [], 4: []}
        while not self._queue.empty():
            try:
                pri, seq, msg = self._queue.get_nowait()
                buckets[pri].append(msg)
            except queue.Empty:
                break

        for pri in sorted(buckets):
            for msg in buckets[pri]:
                self._deliver(msg)

    def _deliver(self, message: BusMessage) -> None:
        """Deliver one message to all subscribers. Catches handler exceptions."""
        with QMutexLocker(self._mutex):
            handlers = list(self._subscribers.get(message.channel, []))

        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                if message.channel != CH_LOG:
                    self.emit(CH_LOG,
                              {'error': str(e), 'channel': message.channel},
                              Priority.T0, sender='PtolBus')
                _log(f'handler exception on {message.channel}: {e}', 'ERROR')

        self.message_dispatched.emit(message.channel, message.sender or '')

    # ── Status ────────────────────────────────────────────────────────────────

    def queue_depth(self) -> int:
        return self._queue.qsize()

    def subscriber_count(self, channel: str) -> int:
        return len(self._subscribers.get(channel, []))

    def channels(self) -> List[str]:
        return list(self._subscribers.keys())

    def thread_pool_status(self) -> dict:
        return {
            sid: {'role': s.role, 'face': s.face_id, 'state': s.state}
            for sid, s in self._thread_pool.items()
        }

    def health_report(self) -> dict:
        return self._health.report()

    def __repr__(self):
        return (f"PtolBus(faces={len(self._face_registry)}, "
                f"channels={len(self._subscribers)}, "
                f"queue={self.queue_depth()}, "
                f"threads={len(self._thread_pool)}, "
                f"symptom={self._health.symptom_level:.2f})")
