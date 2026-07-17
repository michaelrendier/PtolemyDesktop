#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
ptol_blockchain.py — Ptolemy Blockchain Kernel
================================================
Pharos Core Layer

The kernel operative. Not logging infrastructure.
Everything Ptolemy does is a block. The chain is what Ptolemy IS at rest.

Architecture:
    Event-sourced by default:
        Every GUI interaction, bus event, inference coord, error, acquisition.
        What the user was doing at crash time is in the chain.
        Diagnostic root cause is chain traversal, not guesswork.

    Predictive state snapshots (Mandos CHECKPOINT blocks):
        Not periodic. Triggered when error pattern predicts instability:
        - N WARN-level codes in rolling window
        - Any PTL_8xx resource code
        - Escalating severity sequence
        - Specific dangerous code combinations
        Mandos commits full state hash BEFORE the crash, not after.

    Safe mode — two kinds (determined by causal chain analysis):

        UI-generated crash:
            Last N blocks trace back to GUI_INTERACTION event.
            Pharos loads console only (not Interface).
            Desktop 70% transparent grey.
            Console shows: error / recommendations / autofix if available.

        Non-UI crash:
            No GUI events in causal chain of crash block.
            Full desktop boots in SAFE_MODE flag.
            Restricted Face set, T0-only bus.
            Normal navigation, fenced until resume or autofix.

    Sovereign Face chains:
        master.chain   — system index, Face registration, WorldBreak
        pharos.chain   — core / GUI events
        aule.chain     — forge events
        mandos.chain   — checkpoint / resurrection
        <face>.chain   — each Face sovereign, created on FACE_REGISTER

    Bus integration:
        PtolBus CH_BLOCKCHAIN subscriber = chain.bus_handler
        Wire once in ptol_face_wiring.py:
            bus.subscribe(CH_BLOCKCHAIN, chain.bus_handler)
        Bus delivers TO the chain. Chain survives bus death.
        Mandos reads chain directly at resurrection.

    Hash function:
        SHA-256 (stdlib). Swap point: _hash_str().
        Replace with KCF/Horner when Ptolemy++ port is complete.
        Interface unchanged.

Error family (PTL_920-PTL_929):
    PTL_920  ChainIntegrityViolation    block hash mismatch on verify
    PTL_921  ChainLinkBroken            prev_hash does not match predecessor
    PTL_922  ForkDetected               two blocks claim same index
    PTL_923  ChainWriteFailure          disk write failed
    PTL_924  GenesisMissing             chain file exists, no genesis block
    PTL_925  ChainUnauthorized          Face wrote to another Face's chain
    PTL_926  CheckpointUnverifiable     resurrection: block_hash not found
    PTL_927  ChainCorrupted             chain file not valid JSON-lines
    PTL_928  SAFE_MODE_ENTRY            committed as block (not raised)
    PTL_929  PREDICTIVE_SNAPSHOT_FAIL   committed as block (not raised)

Usage:
    from Pharos.ptol_blockchain import chain, EventType, SafeMode

    chain.commit('aule', EventType.FORGE_START, {'job': 'acquire_words_a'})
    chain.commit_gui('MenuBar', 'file_open', path)
    chain.commit_error(error_obj)
    chain.checkpoint('mandos', state_dict)
    mode, ctx = chain.resurrection_mode()
    bus.subscribe(CH_BLOCKCHAIN, chain.bus_handler)
"""

import os
import json
import hashlib
import threading
import datetime
import time
from enum import Enum, IntEnum
from pathlib import Path
from typing import Optional, Callable, Any


# =============================================================================
# HASH FUNCTION
# Swap point for KCF/Horner when Ptolemy++ port is complete.
# =============================================================================

def _hash_str(content: str) -> str:
    """SHA-256. Replace body with KCF/Horner — interface unchanged."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


_GENESIS_HASH = '0' * 64


# =============================================================================
# STORAGE
# =============================================================================

_PRIMARY_DIR  = Path('/var/ptolemy/chain')
_FALLBACK_DIR = Path.home() / 'ptolemy_chain'


def _resolve_chain_dir() -> Path:
    try:
        _PRIMARY_DIR.mkdir(parents=True, exist_ok=True)
        test = _PRIMARY_DIR / '.write_test'
        test.touch()
        test.unlink()
        return _PRIMARY_DIR
    except (PermissionError, OSError):
        _FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        return _FALLBACK_DIR


_CHAIN_DIR: Path = _resolve_chain_dir()


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType(str, Enum):
    BOOT                  = 'BOOT'
    SHUTDOWN              = 'SHUTDOWN'
    WORLD_BREAK           = 'WORLD_BREAK'
    SAFE_MODE_ENTRY       = 'SAFE_MODE_ENTRY'
    FACE_REGISTER         = 'FACE_REGISTER'
    FACE_IN               = 'FACE_IN'
    FACE_OUT              = 'FACE_OUT'
    GUI_INTERACTION       = 'GUI_INTERACTION'
    GUI_CRASH             = 'GUI_CRASH'
    ERROR_INFO            = 'ERROR_INFO'
    ERROR_WARN            = 'ERROR_WARN'
    ERROR_ERROR           = 'ERROR_ERROR'
    ERROR_FATAL           = 'ERROR_FATAL'
    CHECKPOINT            = 'CHECKPOINT'
    PREDICTIVE_CHECKPOINT = 'PREDICTIVE_CHECKPOINT'
    RESURRECTION          = 'RESURRECTION'
    MANDOS_INTERCEPT      = 'MANDOS_INTERCEPT'
    WORD_ACQUIRED         = 'WORD_ACQUIRED'
    WORD_INCOMPLETE       = 'WORD_INCOMPLETE'
    WORD_FIRST_ENCOUNTER  = 'WORD_FIRST_ENCOUNTER'   # Rabies Principle
    FORGE_START           = 'FORGE_START'
    FORGE_COMPLETE        = 'FORGE_COMPLETE'
    FORGE_FAILURE         = 'FORGE_FAILURE'
    BUS_EVENT             = 'BUS_EVENT'
    INFERENCE_COORD       = 'INFERENCE_COORD'
    HALT_DECISION         = 'HALT_DECISION'
    INFO                  = 'INFO'


# =============================================================================
# SAFE MODE
# =============================================================================

class SafeMode(IntEnum):
    CLEAN   = 0   # No crash — normal boot
    CONSOLE = 1   # UI-generated crash — console only, grey desktop
    DESKTOP = 2   # Non-UI crash — full desktop, restricted Faces


# Predictive snapshot triggers
_PREDICTIVE_TRIGGERS = {
    'warn_window':      5,
    'warn_window_secs': 30,
    'resource_codes': {
        'PTL_801', 'PTL_802', 'PTL_803', 'PTL_804', 'PTL_805',
        'PTL_806', 'PTL_807', 'PTL_808', 'PTL_809', 'PTL_810',
    },
    'danger_sequences': [
        ('PTL_303', 'PTL_401'),   # buffer overflow -> inference failure
        ('PTL_908', 'PTL_910'),   # mandos store fail -> world break
    ],
}

_GUI_LOOKBACK_BLOCKS = 50
_GUI_CAUSAL_WINDOW_SECS = 10.0


# =============================================================================
# BLOCK
# =============================================================================

class Block:
    """
    Immutable. Hash sealed at construction.
    payload_hash guards payload integrity independently of block hash.
    Block hash covers all structural fields.
    """

    __slots__ = ('index', 'timestamp', 'face', 'chain_name',
                 'event_type', 'payload', 'payload_hash',
                 'prev_hash', 'hash', 'safe_mode')

    def __init__(
        self,
        index:      int,
        face:       str,
        chain_name: str,
        event_type: str,
        payload:    dict,
        prev_hash:  str,
        safe_mode:  bool = False,
    ):
        self.index        = index
        self.timestamp    = datetime.datetime.utcnow().timestamp()
        self.face         = face.lower()
        self.chain_name   = chain_name.lower()
        self.event_type   = str(event_type)
        self.payload      = payload
        self.payload_hash = _hash_str(
            json.dumps(payload, sort_keys=True, default=str)
        )
        self.prev_hash    = prev_hash
        self.safe_mode    = safe_mode
        self.hash         = self._compute_hash()

    def _compute_hash(self) -> str:
        content = json.dumps({
            'index':        self.index,
            'timestamp':    self.timestamp,
            'face':         self.face,
            'chain':        self.chain_name,
            'event_type':   self.event_type,
            'payload_hash': self.payload_hash,
            'prev_hash':    self.prev_hash,
            'safe_mode':    self.safe_mode,
        }, sort_keys=True)
        return _hash_str(content)

    def to_dict(self) -> dict:
        return {
            'index':        self.index,
            'timestamp':    self.timestamp,
            'face':         self.face,
            'chain':        self.chain_name,
            'event_type':   self.event_type,
            'payload':      self.payload,
            'payload_hash': self.payload_hash,
            'prev_hash':    self.prev_hash,
            'safe_mode':    self.safe_mode,
            'hash':         self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Block':
        b = cls.__new__(cls)
        b.index        = d['index']
        b.timestamp    = d['timestamp']
        b.face         = d['face']
        b.chain_name   = d['chain']
        b.event_type   = d['event_type']
        b.payload      = d['payload']
        b.payload_hash = d['payload_hash']
        b.prev_hash    = d['prev_hash']
        b.safe_mode    = d.get('safe_mode', False)
        b.hash         = d['hash']
        return b

    def verify(self) -> tuple[bool, str]:
        expected_ph = _hash_str(
            json.dumps(self.payload, sort_keys=True, default=str)
        )
        if self.payload_hash != expected_ph:
            return False, f'payload_hash mismatch at block {self.index}'
        if self.hash != self._compute_hash():
            return False, f'block hash mismatch at block {self.index}'
        return True, 'ok'

    def __repr__(self) -> str:
        return (f'Block(i={self.index}, face={self.face!r}, '
                f'evt={self.event_type!r}, h=…{self.hash[-8:]})')


# =============================================================================
# FACE CHAIN
# =============================================================================

class FaceChain:
    """
    Sovereign chain for one Face (or master).
    JSON-lines: one block per line. fsync on every write.
    Thread-safe. Append-only.
    """

    def __init__(self, name: str, chain_dir: Path):
        self._name      = name.lower()
        self._path      = chain_dir / f'{self._name}.chain'
        self._lock      = threading.Lock()
        self._last_hash = _GENESIS_HASH
        self._index     = 0
        self._safe      = False
        self._init_chain()

    def _init_chain(self) -> None:
        if self._path.exists():
            last = self._read_last_block()
            if last:
                self._last_hash = last.hash
                self._index     = last.index + 1
                self._safe      = last.safe_mode
        else:
            self._write_genesis()

    def _write_genesis(self) -> None:
        g = Block(
            index=0,
            face='pharos',
            chain_name=self._name,
            event_type=EventType.BOOT,
            payload={
                'genesis': True,
                'chain':   self._name,
                'created': datetime.datetime.utcnow().isoformat(),
            },
            prev_hash=_GENESIS_HASH,
        )
        if self._append_block(g):
            self._last_hash = g.hash
            self._index     = 1

    def _read_last_block(self) -> Optional[Block]:
        try:
            with open(self._path, 'rb') as f:
                f.seek(0, 2)
                size = f.tell()
                if size == 0:
                    return None
                f.seek(max(0, size - 8192))
                lines = f.read().decode('utf-8', errors='replace').splitlines()
                for line in reversed(lines):
                    line = line.strip()
                    if line:
                        try:
                            return Block.from_dict(json.loads(line))
                        except (json.JSONDecodeError, KeyError):
                            continue
        except OSError:
            pass
        return None

    def _append_block(self, block: Block) -> bool:
        try:
            with open(self._path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(block.to_dict(), default=str) + '\n')
                f.flush()
                os.fsync(f.fileno())
            return True
        except OSError:
            return False

    def commit(
        self,
        face:       str,
        event_type: str,
        payload:    dict,
        safe_mode:  bool = False,
    ) -> 'Block':
        if self._name != 'master' and face.lower() != self._name:
            raise ChainUnauthorized(
                f'{face} attempted write to {self._name} chain',
                context={'face': face, 'chain': self._name},
            )
        with self._lock:
            if (self._last_hash == _GENESIS_HASH and self._index == 0
                    and self._path.exists()
                    and self._path.stat().st_size > 0):
                raise ChainCorrupted(
                    f'{self._name} chain file exists but genesis unreadable',
                    context={'path': str(self._path)},
                )
            block = Block(
                index=self._index,
                face=face,
                chain_name=self._name,
                event_type=event_type,
                payload=payload,
                prev_hash=self._last_hash,
                safe_mode=safe_mode,
            )
            if not self._append_block(block):
                raise ChainWriteFailure(
                    f'{self._name} chain write failed at index {self._index}',
                    context={'chain': self._name, 'index': self._index},
                )
            self._last_hash = block.hash
            self._index    += 1
            return block

    def verify_full(self) -> tuple[bool, list[str]]:
        errors    = []
        prev_hash = _GENESIS_HASH
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        block = Block.from_dict(json.loads(line))
                    except (json.JSONDecodeError, KeyError) as e:
                        errors.append(f'line {lineno}: {e}')
                        continue
                    valid, reason = block.verify()
                    if not valid:
                        errors.append(reason)
                    if block.index > 0 and block.prev_hash != prev_hash:
                        errors.append(
                            f'block {block.index}: link broken '
                            f'(expected …{prev_hash[-8:]} '
                            f'got …{block.prev_hash[-8:]})'
                        )
                    prev_hash = block.hash
        except OSError as e:
            errors.append(f'unreadable: {e}')
        return len(errors) == 0, errors

    def find_by_hash(self, target: str) -> Optional[Block]:
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get('hash') == target:
                            return Block.from_dict(d)
                    except (json.JSONDecodeError, KeyError):
                        pass
        except OSError:
            pass
        return None

    def find_last_checkpoint(self) -> Optional[Block]:
        result = None
        ctypes = {EventType.CHECKPOINT, EventType.PREDICTIVE_CHECKPOINT}
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        if d.get('event_type') in ctypes:
                            result = Block.from_dict(d)
                    except (json.JSONDecodeError, KeyError):
                        pass
        except OSError:
            pass
        return result

    def tail(self, n: int = 20) -> list[Block]:
        blocks = []
        try:
            with open(self._path, 'rb') as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - n * 600))
                lines = f.read().decode('utf-8', errors='replace').splitlines()
            for line in lines[-n:]:
                line = line.strip()
                if line:
                    try:
                        blocks.append(Block.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, KeyError):
                        pass
        except OSError:
            pass
        return blocks[-n:]

    def recent_events(self, event_types: set, since_secs: float) -> list[Block]:
        cutoff = time.time() - since_secs
        return [b for b in self.tail(n=200)
                if b.timestamp >= cutoff and b.event_type in event_types]

    @property
    def name(self) -> str:
        return self._name

    @property
    def last_hash(self) -> str:
        with self._lock:
            return self._last_hash

    @property
    def length(self) -> int:
        with self._lock:
            return self._index


# =============================================================================
# PREDICTIVE ENGINE
# =============================================================================

class _PredictiveEngine:
    """
    Watches error stream. Triggers Mandos snapshot before predicted crash.
    """

    def __init__(self, on_trigger: Callable[[str], None]):
        self._on_trigger   = on_trigger
        self._warn_times:  list[float] = []
        self._recent_codes: list[str]  = []
        self._lock         = threading.Lock()
        self._triggered    = False

    def observe(self, ptl_code: str, severity_name: str) -> None:
        with self._lock:
            now = time.time()
            if severity_name == 'WARN':
                self._warn_times.append(now)
                window = _PREDICTIVE_TRIGGERS['warn_window_secs']
                self._warn_times = [t for t in self._warn_times
                                    if now - t <= window]
                if (len(self._warn_times)
                        >= _PREDICTIVE_TRIGGERS['warn_window']):
                    self._fire(
                        f'{len(self._warn_times)} WARNs in {window}s'
                    )
                    return
            if ptl_code in _PREDICTIVE_TRIGGERS['resource_codes']:
                self._fire(f'resource pressure: {ptl_code}')
                return
            self._recent_codes.append(ptl_code)
            if len(self._recent_codes) > 20:
                self._recent_codes.pop(0)
            for seq in _PREDICTIVE_TRIGGERS['danger_sequences']:
                if len(seq) <= len(self._recent_codes):
                    if tuple(self._recent_codes[-len(seq):]) == tuple(seq):
                        self._fire(f'danger sequence: {" → ".join(seq)}')
                        return
            if self._triggered:
                self._triggered = False

    def _fire(self, reason: str) -> None:
        if not self._triggered:
            self._triggered = True
            try:
                self._on_trigger(reason)
            except Exception:
                pass


# =============================================================================
# PTOL BLOCKCHAIN — KERNEL OPERATIVE
# =============================================================================

class PtolBlockchain:
    """
    Multi-chain ledger. Master + sovereign Face chains.
    Singleton: from Pharos.ptol_blockchain import chain
    """

    def __init__(self, chain_dir: Path):
        self._dir    = chain_dir
        self._lock   = threading.Lock()
        self._chains: dict[str, FaceChain] = {}
        self._safe   = False
        self._chains['master'] = FaceChain('master', chain_dir)
        self._predictor = _PredictiveEngine(
            on_trigger=self._predictive_snapshot
        )

    # ── Chain access ──────────────────────────────────────────────────────────

    def _get_or_create(self, name: str) -> FaceChain:
        name = name.lower()
        with self._lock:
            if name not in self._chains:
                self._chains[name] = FaceChain(name, self._dir)
            return self._chains[name]

    # ── Core commit ───────────────────────────────────────────────────────────

    def commit(
        self,
        face:        str,
        event_type:  str,
        payload:     dict,
        also_master: bool = False,
    ) -> Optional[Block]:
        fc    = self._get_or_create(face)
        block = fc.commit(face, event_type, payload, safe_mode=self._safe)
        if also_master and block:
            self._mirror_to_master(face, block, event_type, payload)
        return block

    def commit_master(self, face: str, event_type: str,
                      payload: dict) -> Optional[Block]:
        return self._chains['master'].commit(
            face, event_type, payload, safe_mode=self._safe
        )

    def _mirror_to_master(self, face: str, source: Block,
                          event_type: str, payload: dict) -> None:
        try:
            self._chains['master'].commit('pharos', event_type, {
                'from_face':  face,
                'from_index': source.index,
                'from_hash':  source.hash,
                'detail':     payload.get('detail',
                              payload.get('message',
                              payload.get('code', ''))),
            }, safe_mode=self._safe)
        except ChainError:
            pass

    # ── Error handler ─────────────────────────────────────────────────────────

    def commit_error(self, error: Any) -> Optional[Block]:
        """
        Replaces ErrorHandler._emit() stdout stub.
        Wire: ERROR_HANDLER_SETTINGS['log_backend'] = 'blockchain'
        """
        face     = getattr(error, 'face_name', 'pharos') or 'pharos'
        sev      = getattr(error, 'severity', None)
        sev_name = sev.name if hasattr(sev, 'name') else str(sev)
        code     = getattr(error, 'code', 'PTL_999')

        etype = {
            'INFO':  EventType.ERROR_INFO,
            'WARN':  EventType.ERROR_WARN,
            'ERROR': EventType.ERROR_ERROR,
            'FATAL': EventType.ERROR_FATAL,
        }.get(sev_name, EventType.ERROR_ERROR)

        payload = (error.to_dict() if hasattr(error, 'to_dict')
                   else {'code': code, 'detail': str(error)})

        self._predictor.observe(code, sev_name)
        return self.commit(face, etype, payload,
                           also_master=(sev_name == 'FATAL'))

    # ── GUI interaction ───────────────────────────────────────────────────────

    def commit_gui(self, widget: str, action: str,
                   detail: str = '') -> Optional[Block]:
        """
        Called from Interface.py on every user interaction.
        Causal chain analysis reads these at resurrection.
        """
        return self.commit('pharos', EventType.GUI_INTERACTION, {
            'widget': widget,
            'action': action,
            'detail': detail,
        })

    # ── Mandos checkpoint ─────────────────────────────────────────────────────

    def checkpoint(self, face: str, state_dict: dict,
                   predictive: bool = False) -> Optional[Block]:
        etype = (EventType.PREDICTIVE_CHECKPOINT if predictive
                 else EventType.CHECKPOINT)
        payload = {
            'state_hash': _hash_str(
                json.dumps(state_dict, sort_keys=True, default=str)
            ),
            'state':      state_dict,
            'predictive': predictive,
        }
        block = self.commit(face, etype, payload)
        if block:
            try:
                self._chains['master'].commit('mandos', etype, {
                    'face':       face,
                    'block_hash': block.hash,
                    'predictive': predictive,
                }, safe_mode=self._safe)
            except ChainError:
                pass
        return block

    def _predictive_snapshot(self, reason: str) -> None:
        try:
            from Mandos.mandos import get_state
            state = get_state() or {}
            state['_predictive_reason'] = reason
            self.checkpoint('mandos', state, predictive=True)
        except Exception:
            try:
                self._chains['master'].commit('pharos', EventType.ERROR_FATAL, {
                    'code':   'PTL_929',
                    'detail': f'predictive snapshot failed: {reason}',
                }, safe_mode=self._safe)
            except Exception:
                pass

    # ── Resurrection gate ─────────────────────────────────────────────────────

    def resurrection_mode(self) -> tuple[SafeMode, dict]:
        """
        Called at boot. Determines safe mode from causal chain analysis.

        Returns:
            (SafeMode.CLEAN,   {})           no crash
            (SafeMode.CONSOLE, {crash_info}) UI-generated crash
            (SafeMode.DESKTOP, {crash_info}) non-UI crash
        """
        master_tail = self._chains['master'].tail(n=_GUI_LOOKBACK_BLOCKS)
        crash_block = None
        crash_events = {
            EventType.WORLD_BREAK,
            EventType.ERROR_FATAL,
            EventType.GUI_CRASH,
        }
        for block in reversed(master_tail):
            if block.event_type in crash_events:
                crash_block = block
                break

        if crash_block is None:
            return SafeMode.CLEAN, {}

        # Check pharos chain for GUI_INTERACTION near crash time
        ui_caused   = False
        crash_time  = crash_block.timestamp
        pharos      = self._get_or_create('pharos')
        recent      = pharos.tail(n=_GUI_LOOKBACK_BLOCKS)

        for block in reversed(recent):
            if block.timestamp > crash_time:
                continue
            if crash_time - block.timestamp > _GUI_CAUSAL_WINDOW_SECS:
                break
            if block.event_type == EventType.GUI_INTERACTION:
                ui_caused = True
                break

        ctx = {
            'crash_hash':   crash_block.hash,
            'crash_event':  crash_block.event_type,
            'crash_time':   crash_block.timestamp,
            'crash_face':   crash_block.face,
            'crash_code':   crash_block.payload.get('code', ''),
            'crash_detail': crash_block.payload.get('detail', ''),
            'ui_caused':    ui_caused,
        }
        return (SafeMode.CONSOLE if ui_caused else SafeMode.DESKTOP), ctx

    def verify_checkpoint(self, block_hash: str) -> tuple[bool, Optional[Block]]:
        """Mandos resurrection gate. Scan all chains for hash."""
        for fc in self._chains.values():
            block = fc.find_by_hash(block_hash)
            if block:
                valid, _ = block.verify()
                return valid, (block if valid else None)
        return False, None

    def last_checkpoint(self) -> Optional[Block]:
        """Most recent CHECKPOINT across all chains. Mandos reads at boot."""
        result = None
        result_ts = 0.0
        for fc in self._chains.values():
            b = fc.find_last_checkpoint()
            if b and b.timestamp > result_ts:
                result    = b
                result_ts = b.timestamp
        return result

    # ── Safe mode ─────────────────────────────────────────────────────────────

    def enter_safe_mode(self, mode: SafeMode, reason: str) -> None:
        self._safe = True
        try:
            self._chains['master'].commit('pharos', EventType.SAFE_MODE_ENTRY, {
                'code':   'PTL_928',
                'mode':   mode.name,
                'reason': reason,
            }, safe_mode=True)
        except ChainError:
            pass

    def exit_safe_mode(self) -> None:
        self._safe = False

    @property
    def in_safe_mode(self) -> bool:
        return self._safe

    # ── Bus subscriber ────────────────────────────────────────────────────────

    def bus_handler(self, message: Any) -> None:
        """
        Wire to CH_BLOCKCHAIN:
            bus.subscribe(CH_BLOCKCHAIN, chain.bus_handler)
        Every bus message becomes a block.
        Never raises — would kill the bus.
        """
        try:
            payload    = getattr(message, 'payload', {})
            sender     = getattr(message, 'sender', 'pharos') or 'pharos'
            if not isinstance(payload, dict):
                payload = {'data': str(payload)}
            event_type = payload.get('event_type', EventType.BUS_EVENT)
            self.commit(sender, event_type, payload)
        except Exception:
            pass

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def tail(self, face: str, n: int = 20) -> list[Block]:
        return self._get_or_create(face).tail(n)

    def chain_lengths(self) -> dict[str, int]:
        return {n: fc.length for n, fc in self._chains.items()}

    def verify_all(self) -> dict[str, tuple[bool, list[str]]]:
        """Full integrity check. Slow — diagnostic only."""
        return {n: fc.verify_full() for n, fc in self._chains.items()}

    @property
    def chain_dir(self) -> Path:
        return self._dir


# =============================================================================
# BLOCKCHAIN ERROR FAMILY — PTL_920-PTL_929
# Register these in luthspell_error_handler.py PTL_9xx section.
# =============================================================================

class ChainError(Exception):
    code = 'PTL_920'
    def __init__(self, detail='', context=None):
        self.detail  = detail
        self.context = context
        super().__init__(f'[{self.code}] {detail}')

class ChainIntegrityViolation(ChainError):
    """PTL_920: Block hash mismatch on verify."""
    code = 'PTL_920'

class ChainLinkBroken(ChainError):
    """PTL_921: prev_hash does not match predecessor."""
    code = 'PTL_921'

class ForkDetected(ChainError):
    """PTL_922: Two blocks claim same index."""
    code = 'PTL_922'

class ChainWriteFailure(ChainError):
    """PTL_923: Disk write failed — block not committed."""
    code = 'PTL_923'

class GenesisMissing(ChainError):
    """PTL_924: Chain file exists but no valid genesis block."""
    code = 'PTL_924'

class ChainUnauthorized(ChainError):
    """PTL_925: Face attempted write to another Face's sovereign chain."""
    code = 'PTL_925'

class CheckpointUnverifiable(ChainError):
    """PTL_926: Resurrection: block_hash not found in any chain."""
    code = 'PTL_926'

class ChainCorrupted(ChainError):
    """PTL_927: Chain file is not valid JSON-lines."""
    code = 'PTL_927'

# PTL_928 SAFE_MODE_ENTRY    — committed as block, not raised.
# PTL_929 PREDICTIVE_SNAPSHOT_FAIL — committed as block, not raised.


# =============================================================================
# SINGLETON
# =============================================================================

chain = PtolBlockchain(_CHAIN_DIR)
