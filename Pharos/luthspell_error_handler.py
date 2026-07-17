#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy Project -- Pharos
LuthSpell: Error Handler + Garbage Collector + Full PTL Error Catalog

Mandos is wired here as the fatal interceptor.
On any FATAL: checkpoint to Mandos BEFORE GC runs.
On PTL_910 WorldBreak: Mandos.world_break() -- no return.

PEP 3151 compliant. All PTL errors subclass PtolemyError(Exception).
"""

from __future__ import annotations
import time, traceback
from enum import IntEnum
from typing import Callable, Optional, Any


ERROR_HANDLER_SETTINGS = {
    "gc_on_fatal":                   True,
    "gc_on_error":                   False,
    "log_backend":                   "stdout",
    "report_to_ptolemy_severity":    "ERROR",
}


class Severity(IntEnum):
    INFO = 0
    WARN = 1
    ERROR = 2
    FATAL = 3


# =============================================================================
# Base
# =============================================================================

class PtolemyError(Exception):
    code       = "PTL_000"
    severity   = Severity.ERROR
    gc_trigger = False

    def __init__(self, detail="", context=None):
        self.detail    = detail
        self.context   = context
        self.timestamp = time.time()
        super().__init__(f"[{self.code}] {detail}")

    def to_dict(self):
        return {
            "code":      self.code,
            "severity":  self.severity.name,
            "detail":    self.detail,
            "context":   str(self.context),
            "timestamp": self.timestamp,
        }


# =============================================================================
# PTL_1xx -- Bus
# =============================================================================

class BusChannelNotFound(PtolemyError):
    """PTL_101: Published message targets a channel with no subscribers."""
    code = "PTL_101"; severity = Severity.WARN

class BusMessageMalformed(PtolemyError):
    """PTL_102: BusMessage missing required fields or has invalid payload type."""
    code = "PTL_102"; severity = Severity.ERROR

class BusOverflow(PtolemyError):
    """PTL_103: Priority queue full and T1 eviction failed. GC triggered."""
    code = "PTL_103"; severity = Severity.FATAL; gc_trigger = True

class BusPriorityViolation(PtolemyError):
    """PTL_104: Message priority value outside T0/T1 range."""
    code = "PTL_104"; severity = Severity.ERROR

class BusDeadlock(PtolemyError):
    """PTL_105: Dispatch thread detected circular wait condition. GC triggered."""
    code = "PTL_105"; severity = Severity.FATAL; gc_trigger = True

class BusQueueFull(PtolemyError):
    """PTL_106: queue.Full raised during bus put -- subscriber not consuming."""
    code = "PTL_106"; severity = Severity.ERROR; gc_trigger = True

class BusDispatchFailed(PtolemyError):
    """PTL_107: Unhandled exception during message dispatch to subscriber."""
    code = "PTL_107"; severity = Severity.ERROR


# =============================================================================
# PTL_2xx -- LuthSpell
# =============================================================================

class BoundaryNotSet(PtolemyError):
    """PTL_201: LuthSpell.check() called before set_boundary() on this inference."""
    code = "PTL_201"; severity = Severity.WARN

class HaltPassFailed(PtolemyError):
    """PTL_202: halt_pass() could not write HaltRecord to blockchain. FATAL."""
    code = "PTL_202"; severity = Severity.FATAL; gc_trigger = True

class BoundaryCorrupted(PtolemyError):
    """PTL_203: Boundary hash mismatch -- record tampered or bit-flipped. FATAL."""
    code = "PTL_203"; severity = Severity.FATAL; gc_trigger = True

class InfiniteHaltLoop(PtolemyError):
    """PTL_204: halt_pass() triggered from within a halt handler. FATAL."""
    code = "PTL_204"; severity = Severity.FATAL; gc_trigger = True

class RedirectFailed(PtolemyError):
    """PTL_205: Ptolemy could not redirect inference after halt. FATAL."""
    code = "PTL_205"; severity = Severity.FATAL; gc_trigger = True

class PrioritySchemeNotWired(PtolemyError):
    """PTL_206: PRIORITY_SCHEME value has no wired implementation in luthspell.py."""
    code = "PTL_206"; severity = Severity.ERROR


# =============================================================================
# PTL_3xx -- Buffer
# =============================================================================

class BufferEvictionFailed(PtolemyError):
    """PTL_301: CyclicContextBuffer eviction policy could not free a slot."""
    code = "PTL_301"; severity = Severity.ERROR

class BufferIntegrityViolation(PtolemyError):
    """PTL_302: Buffer checksum mismatch -- context window corrupted. FATAL."""
    code = "PTL_302"; severity = Severity.FATAL; gc_trigger = True

class BufferOverCapacity(PtolemyError):
    """PTL_303: Buffer write exceeds max capacity and eviction is disabled."""
    code = "PTL_303"; severity = Severity.ERROR

class CompressionFailed(PtolemyError):
    """PTL_304: HyperWebster payload compression/encoding step failed."""
    code = "PTL_304"; severity = Severity.ERROR

class HyperindexFailed(PtolemyError):
    """PTL_305: Horner bijection could not index string -- charset mismatch."""
    code = "PTL_305"; severity = Severity.ERROR

class CompressionModelNotWired(PtolemyError):
    """PTL_306: Compression model name has no wired implementation."""
    code = "PTL_306"; severity = Severity.ERROR

class HyperindexMethodNotWired(PtolemyError):
    """PTL_307: Hyperindex method name has no wired implementation."""
    code = "PTL_307"; severity = Severity.ERROR

class BufferCommitOutOfOrder(PtolemyError):
    """PTL_308: commit() called before compress()/hyperindex() -- sequencing violation."""
    code = "PTL_308"; severity = Severity.ERROR


# =============================================================================
# PTL_4xx -- Blockchain
# =============================================================================

class BlockchainCommitFailed(PtolemyError):
    """PTL_401: PtolChain block write failed -- disk, lock, or integrity error. FATAL."""
    code = "PTL_401"; severity = Severity.FATAL; gc_trigger = True

class ChainIntegrityViolation(PtolemyError):
    """PTL_402: Block hash chain broken -- tampering or corruption detected. FATAL."""
    code = "PTL_402"; severity = Severity.FATAL; gc_trigger = True

class GenesisBlockMissing(PtolemyError):
    """PTL_403: Chain opened but genesis block absent -- uninitialized or deleted. FATAL."""
    code = "PTL_403"; severity = Severity.FATAL; gc_trigger = True

class BranchOrphan(PtolemyError):
    """PTL_404: Branch block references unknown parent hash."""
    code = "PTL_404"; severity = Severity.ERROR


# =============================================================================
# PTL_5xx -- Acquisition
# =============================================================================

class WordAcquisitionFailed(PtolemyError):
    """PTL_501: acquire() returned empty result for all sources."""
    code = "PTL_501"; severity = Severity.WARN

class AcquisitionAPITimeout(PtolemyError):
    """PTL_502: FreeDictionary/Datamuse/Wiktionary request timed out."""
    code = "PTL_502"; severity = Severity.WARN

class WordRecordCorrupted(PtolemyError):
    """PTL_503: JSON shard on disk failed validation -- field missing or wrong type."""
    code = "PTL_503"; severity = Severity.ERROR

class RabiesViolation(PtolemyError):
    """PTL_504: first_encountered IMMUTABLE. Write attempted -- code error, not memory.
    FATAL, gc_trigger=False. Fix the code. Do not catch and continue."""
    code = "PTL_504"; severity = Severity.FATAL; gc_trigger = False

class SemanticWordBridgeFailed(PtolemyError):
    """PTL_505: Cross-language bridge could not resolve meaning vector."""
    code = "PTL_505"; severity = Severity.ERROR

class AcquisitionSourceParseError(PtolemyError):
    """PTL_506: Per-source parse failure during acquisition (HTML, JSON, API response)."""
    code = "PTL_506"; severity = Severity.WARN


# =============================================================================
# PTL_6xx -- LSH
# =============================================================================

class MonadIsolationViolation(PtolemyError):
    """PTL_601: WordMonad state was written from outside its owning layer. FATAL."""
    code = "PTL_601"; severity = Severity.FATAL; gc_trigger = True

class InferenceCoordInvalid(PtolemyError):
    """PTL_602: Octonion coordinate outside valid address space bounds."""
    code = "PTL_602"; severity = Severity.ERROR

class LSHModelNotInitialized(PtolemyError):
    """PTL_603: LSH inference called before model weights loaded. FATAL, no GC."""
    code = "PTL_603"; severity = Severity.FATAL; gc_trigger = False

class GrammarNeuronFailed(PtolemyError):
    """PTL_604: GrammarNeuron could not parse sentence structure for this language."""
    code = "PTL_604"; severity = Severity.WARN

class SelfAdjointViolation(PtolemyError):
    """PTL_605: Operator failed self-adjoint check -- Hermitian property violated."""
    code = "PTL_605"; severity = Severity.ERROR


# =============================================================================
# PTL_7xx -- Module / Settings
# =============================================================================

class ModuleNotWired(PtolemyError):
    """PTL_701: Face module called before PtolBus.subscribe() completed wiring."""
    code = "PTL_701"; severity = Severity.ERROR

class SettingsKeyMissing(PtolemyError):
    """PTL_702: Required key absent from settings.json -- module cannot start."""
    code = "PTL_702"; severity = Severity.ERROR

class ModuleSwapFailed(PtolemyError):
    """PTL_703: Hot-swap failed -- old module unloaded, new failed to wire. FATAL."""
    code = "PTL_703"; severity = Severity.FATAL; gc_trigger = True

class SettingsIntegrityViolation(PtolemyError):
    """PTL_704: settings.json checksum mismatch -- file tampered after load. FATAL."""
    code = "PTL_704"; severity = Severity.FATAL; gc_trigger = False

class SettingsValidationError(PtolemyError):
    """PTL_705: Settings value failed validation rule -- wrong type or out of range."""
    code = "PTL_705"; severity = Severity.ERROR


# =============================================================================
# PTL_8xx -- I/O and System Resources
# =============================================================================

class DmesgWriteFailed(PtolemyError):
    """PTL_801: PtolDmesg could not write to log -- OSError or PermissionError."""
    code = "PTL_801"; severity = Severity.WARN

class FaceImportFailed(PtolemyError):
    """PTL_802: Face module found but failed to import -- syntax or dependency error."""
    code = "PTL_802"; severity = Severity.ERROR

class ContextPersistFailed(PtolemyError):
    """PTL_803: context_manager could not read/write context file -- FileNotFoundError or JSONDecodeError."""
    code = "PTL_803"; severity = Severity.ERROR

class ForgeJobFailed(PtolemyError):
    """PTL_804: forge_queue subprocess failed or timed out. GC triggered."""
    code = "PTL_804"; severity = Severity.ERROR; gc_trigger = True

class ShellCommandFailed(PtolemyError):
    """PTL_805: PtolShell command raised unhandled exception."""
    code = "PTL_805"; severity = Severity.WARN


# =============================================================================
# PTL_9xx -- System
# =============================================================================

class PtolemyNotInitialized(PtolemyError):
    """PTL_901: Face or subsystem called before Ptolemy root initialised. FATAL."""
    code = "PTL_901"; severity = Severity.FATAL; gc_trigger = False

class FaceNotFound(PtolemyError):
    """PTL_902: PtolBus.import_face() could not locate named Face module."""
    code = "PTL_902"; severity = Severity.ERROR

class LuthSpellNotWired(PtolemyError):
    """PTL_903: System operation called before LuthSpell.wire() completed. FATAL."""
    code = "PTL_903"; severity = Severity.FATAL; gc_trigger = False

class MandosRestoreFailed(PtolemyError):
    """PTL_906: Checkpoint found but deserialization failed -- cold boot required."""
    code = "PTL_906"; severity = Severity.FATAL; gc_trigger = False

class SupervisorRestartBudgetExceeded(PtolemyError):
    """PTL_907: Aule N/T restart ceiling hit -- Face enters Mandos dormant state."""
    code = "PTL_907"; severity = Severity.FATAL; gc_trigger = False

class MandosStoreWriteFailed(PtolemyError):
    """PTL_908: Could not serialize checkpoint before GC -- state is lost."""
    code = "PTL_908"; severity = Severity.FATAL; gc_trigger = False

class AuleWatchdogTimeout(PtolemyError):
    """PTL_909: Mandos declares Aule dead -- Mandos gains supervisor priority."""
    code = "PTL_909"; severity = Severity.FATAL; gc_trigger = False

class WorldBreak(PtolemyError):
    """PTL_910: Mandos FATAL -- final PtolChain write, kernel panic, sys.exit(1)."""
    code = "PTL_910"; severity = Severity.FATAL; gc_trigger = False

class UnknownError(PtolemyError):
    """PTL_999: Unclassified exception -- wraps any non-PtolemyError. GC triggered."""
    code = "PTL_999"; severity = Severity.FATAL; gc_trigger = True

# PTL_904, PTL_905 reserved.


# =============================================================================
# GarbageCollector
# =============================================================================

class GarbageCollector:
    """
    Ptolemy GC -- object registry with triggered collection.

    All objects that need cleanup on fatal errors register here via gc.register(self).
    Call gc.release(self) on clean teardown.
    ErrorHandler calls collect() when error.gc_trigger is True.
    Aule is the sole external caller of collect() outside ErrorHandler.

    PTL_504 RabiesViolation: FATAL, gc_trigger=False -- logical error, not memory leak.
    """

    def __init__(self):
        self._registry: dict[int, Any] = {}
        self._gc_log:   list[dict]     = []

    def register(self, obj):
        self._registry[id(obj)] = obj

    def release(self, obj):
        self._registry.pop(id(obj), None)

    def collect(self, reason="triggered") -> int:
        count = len(self._registry)
        self._gc_log.append({"reason": reason, "count": count, "timestamp": time.time()})
        self._registry.clear()
        return count

    @property
    def gc_log(self):
        return list(self._gc_log)

    def __len__(self):
        return len(self._registry)


# =============================================================================
# ErrorHandler
# Mandos is the fatal interceptor.
# On FATAL: checkpoint to Mandos BEFORE GC.
# On PTL_910: Mandos.world_break() -- no return.
# =============================================================================

class ErrorHandler:
    """
    Central error handler for all Faces.

    Wire on Face spawn:
        gc      = GarbageCollector()
        handler = ErrorHandler(gc=gc, face_name=FACE_NAME,
                               on_error=lambda e: dmesg.error(FACE_NAME, str(e)))

    Mandos intercept is automatic for all FATAL errors.
    Provide get_state_fn to enable checkpoint-before-GC.
    """

    def __init__(
        self,
        gc:           GarbageCollector | None = None,
        on_error:     Callable | None         = None,
        face_name:    str                     = "Unknown",
        get_state_fn: Callable | None         = None,
    ):
        self._gc          = gc or GarbageCollector()
        self._on_error    = on_error
        self._face_name   = face_name
        self._get_state   = get_state_fn   # () -> dict  serializable state snapshot
        self._log:        list[dict] = []

    def handle(self, error, context=None) -> Severity:
        if not isinstance(error, PtolemyError):
            error = UnknownError(detail=str(error), context=traceback.format_exc())

        record = error.to_dict()
        if context:
            record["handler_context"] = str(context)
        self._log.append(record)
        self._emit(error)

        if error.severity == Severity.FATAL:
            self._mandos_intercept(error)

        if error.gc_trigger:
            record["gc_collected"] = self._gc.collect(reason=error.code)

        min_sev = Severity[ERROR_HANDLER_SETTINGS["report_to_ptolemy_severity"]]
        if error.severity >= min_sev and self._on_error:
            self._on_error(error)

        if isinstance(error, WorldBreak):
            self._world_break(error)

        return error.severity

    def _mandos_intercept(self, error: PtolemyError):
        """Checkpoint to Mandos before GC runs. Best-effort -- never raises."""
        try:
            from Mandos.mandos import accept_dead
            state = self._get_state() if self._get_state else {}
            state["_fatal_error"] = error.to_dict()
            accept_dead(self._face_name, state)
        except Exception as exc:
            # Mandos store write failed -- log it, continue to GC
            self._emit_raw(f"[MANDOS] checkpoint failed for {self._face_name}: {exc}")

    def _world_break(self, error: PtolemyError):
        """PTL_910 -- hand off to Mandos.world_break(). Does not return."""
        try:
            from Mandos.mandos import world_break
            world_break(cause=error.detail)
        except Exception as exc:
            # Mandos itself is broken -- raw exit
            import sys
            print(
                "Great is the Fall of Gondolin: "
                "love not too well the work of thy hands and the devices of thy heart; "
                "and remember that the true hope of the Noldor lieth in the West "
                "and cometh from the Sea.",
                flush=True
            )
            sys.exit(1)

    def _emit(self, error: PtolemyError):
        # Blockchain is the primary log backend.
        # stdout fallback retained for dev/debug.
        backend = ERROR_HANDLER_SETTINGS["log_backend"]
        if backend == "stdout":
            print(f"[{error.severity.name}] {error.code}: {error.detail}")
        elif backend == "blockchain":
            try:
                from Pharos.ptol_blockchain import chain
                chain.commit_error(error)
            except Exception as exc:
                print(f"[{error.severity.name}] {error.code}: {error.detail}")
                print(f"[CHAIN] emit failed: {exc}")
        # dmesg-only mode: no commit, no print (safe mode restricted)

    def _emit_raw(self, msg: str):
        backend = ERROR_HANDLER_SETTINGS["log_backend"]
        if backend in ("stdout", "blockchain"):
            print(msg)

    @property
    def log(self):
        return list(self._log)

    @property
    def gc(self):
        return self._gc
