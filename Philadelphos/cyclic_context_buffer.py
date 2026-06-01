"""
Ptolemy — Philadelphos Face
Cyclic Context Buffer
Author: O Captain
Architecture: FIFO sliding window, Entry-atomic, blockchain-committed on eviction

Modular hooks (Settings candidates):
  - BUFFER_SIZE_LINES
  - compression model/method
  - blockchain backend
  - hyperindex method
"""

import hashlib
import json
import time
from collections import deque
from typing import Optional, Callable


# ─── Settings (all modular — each gets a Settings tab entry) ─────────────────

BUFFER_SIZE_LINES = 100              # configurable: number of Entry lines
COMPRESSION_MODEL = "octonion_stub"  # module hook: "smip" when Phase 5 wired
HYPERINDEX_METHOD = "octonion"       # module hook: octonion hyperindexing
BLOCKCHAIN_BACKEND = "branch"        # module hook: branch blockchain


# ─── Objects ────────────────────────────────────────────────────────────────

class PromptObject:
    def __init__(self, text: str, timestamp: Optional[float] = None):
        self.text = text
        self.timestamp = timestamp or time.time()

    def to_line(self) -> str:
        return self.text.replace("\n", " ")


class ResponseObject:
    def __init__(self, text: str, timestamp: Optional[float] = None):
        self.text = text
        self.timestamp = timestamp or time.time()

    def to_line(self) -> str:
        return self.text.replace("\n", " ")


class EntryObject:
    """
    Atomic context unit. One prompt + one response = one line in the buffer.
    Compression, hyperindexing, and blockchain commit all fire on this object.
    Entry is NOT removed from buffer until all three succeed (confirmed eviction).
    """

    def __init__(self, prompt: PromptObject, response: ResponseObject):
        self.prompt = prompt
        self.response = response
        self.timestamp = time.time()
        self._compressed = None
        self._hyperindex_address = None
        self._block_hash = None

    def to_line(self) -> str:
        return json.dumps({
            "p": self.prompt.to_line(),
            "r": self.response.to_line(),
            "t": self.timestamp
        }, separators=(',', ':'))

    # ── Module hooks ───────────────────────────────────────────────────────────

    def compress(self, model: str = COMPRESSION_MODEL) -> str:
        """
        L2 compression. Module hook — swap compression backend via Settings.
        Default: octonion_stub — 8-component hash projection, structurally
        correct for when real sedenion→octonion projection is wired (Phase 5).
        """
        p_text = self.prompt.to_line()
        r_text = self.response.to_line()

        if model in ("stub", "octonion_stub"):
            # Hash the full exchange, then derive 8 octonion components.
            # Sedenion dims e8-e15 are volatile and order-dependent — they
            # are deliberately NOT included here. Only the stable octonion
            # core (e0-e7) is preserved. Real SMIP replaces this in Phase 5.
            raw  = f"{p_text}|||{r_text}|||{self.timestamp}"
            h    = hashlib.sha256(raw.encode()).hexdigest()
            segs = [h[i*8:(i+1)*8] for i in range(8)]
            coords = tuple(int(s, 16) for s in segs)
            # Normalise each component to [0,1) for compact representation
            norm   = tuple(c / (0xFFFFFFFF + 1) for c in coords)
            self._compressed = json.dumps({
                "o": norm,           # octonion e0..e7 projection
                "p": p_text[:64],    # prompt fingerprint (head)
                "r": r_text[:64],    # response fingerprint (head)
                "t": self.timestamp,
            }, separators=(',', ':'))
        elif model == "smip":
            # Hook: real sedenion→octonion projection via ValaQuenta (Phase 5)
            try:
                from Ainulindale.ValaQuenta.engine.smnnip_tower import smnnip_tower
                coords = smnnip_tower.octonion_projection(p_text + r_text)
                self._compressed = json.dumps({"o": list(coords), "t": self.timestamp},
                                              separators=(',', ':'))
            except Exception as e:
                raise NotImplementedError(f"SMIP octonion projection failed: {e}")
        else:
            raise NotImplementedError(f"Compression model '{model}' not yet wired")
        return self._compressed

    def hyperindex(self, method: str = HYPERINDEX_METHOD) -> str:
        """
        Octonion hyperindex address = content hash seed.
        Module hook — swap indexing method via Settings.
        Address format: (index, data_length, timestamp) encoded in hash.
        """
        if self._compressed is None:
            raise RuntimeError("compress() must run before hyperindex()")

        seed = f"{self._compressed}|{self.timestamp}"
        h = hashlib.sha256(seed.encode()).hexdigest()

        if method == "octonion":
            # Octonion 8-component address from hash segments
            segments = [h[i*8:(i+1)*8] for i in range(8)]
            self._hyperindex_address = tuple(int(s, 16) for s in segments)
        else:
            raise NotImplementedError(f"Hyperindex method '{method}' not yet wired")

        return self._hyperindex_address

    def commit(self, chain, backend: str = BLOCKCHAIN_BACKEND) -> str:
        """
        Blockchain commit. Module hook — swap blockchain backend via Settings.
        Entry commits to branch chain after compress + hyperindex succeed.
        """
        if self._hyperindex_address is None:
            raise RuntimeError("hyperindex() must run before commit()")

        block_data = {
            "address": self._hyperindex_address,
            "compressed": self._compressed,
            "timestamp": self.timestamp,
            "prev_hash": chain.last_hash()
        }
        self._block_hash = chain.add_block(block_data)
        return self._block_hash

    def evict(self, chain) -> bool:
        """
        Confirmed eviction pipeline: compress → hyperindex → commit.
        Returns True only if all three succeed. Entry stays in buffer until True.
        """
        try:
            self.compress()
            self.hyperindex()
            self.commit(chain)
            return True
        except Exception as e:
            print(f"[CyclibBuffer] Eviction failed, entry retained: {e}")
            return False


# ─── Branch Blockchain — backed by PtolChain AuditChain ────────────────────────────────────────────────

# PtolChain AuditChain backend
try:
    from Callimachus.BlockChain.PtolChain import AuditChain as _AuditChain
    _HAS_AUDIT_CHAIN = True
except ImportError:
    _AuditChain = None
    _HAS_AUDIT_CHAIN = False

class BranchBlock:
    def __init__(self, data: dict, prev_hash: str):
        self.data = data
        self.prev_hash = prev_hash
        self.timestamp = time.time()
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        raw = json.dumps(self.data, sort_keys=True) + self.prev_hash + str(self.timestamp)
        return hashlib.sha256(raw.encode()).hexdigest()


class BranchBlockchain:
    """
    Branch chain for Cyclic Context Buffer.
    Module hook: swap full blockchain backend via Settings.
    """
    def __init__(self, branch_name: str = "context_buffer"):
        self.branch_name = branch_name
        self.chain: list[BranchBlock] = []
        self._genesis()

    def _genesis(self):
        genesis = BranchBlock({"genesis": self.branch_name}, "0" * 64)
        self.chain.append(genesis)

    def last_hash(self) -> str:
        return self.chain[-1].hash

    def add_block(self, data: dict) -> str:
        block = BranchBlock(data, self.last_hash())
        self.chain.append(block)
        return block.hash

    def __len__(self):
        return len(self.chain) - 1  # exclude genesis


# ─── Cyclic Context Buffer ─────────────────────────────────────────────────────

class CyclicContextBuffer:
    """
    Philadelphos Face — Cyclic Context Buffer
    FIFO sliding window. Unit: lines (Entry objects).
    New In, Old Out. Confirmed eviction only.
    """

    def __init__(self,
                 size: int = BUFFER_SIZE_LINES,
                 chain: Optional[BranchBlockchain] = None,
                 on_evict: Optional[Callable] = None):
        self.size = size
        self.chain = chain or BranchBlockchain()
        self.on_evict = on_evict  # optional callback hook
        self._buffer: deque[EntryObject] = deque()

    def add(self, prompt: PromptObject, response: ResponseObject) -> EntryObject:
        """Add new Entry. If buffer full, evict oldest (confirmed) before appending."""
        entry = EntryObject(prompt, response)

        if len(self._buffer) >= self.size:
            self._evict_oldest()

        self._buffer.append(entry)
        return entry

    def _evict_oldest(self):
        """
        Confirmed eviction: oldest entry stays until evict() returns True.
        No index manipulation during iteration.
        """
        oldest = self._buffer[0]
        success = oldest.evict(self.chain)
        if success:
            self._buffer.popleft()
            if self.on_evict:
                self.on_evict(oldest)
        # If failed: entry retained, buffer temporarily over-capacity by 1

    def get_lines(self) -> list[str]:
        return [e.to_line() for e in self._buffer]

    def __len__(self):
        return len(self._buffer)

    def __repr__(self):
        return f"CyclicContextBuffer(size={self.size}, current={len(self._buffer)}, blocks={len(self.chain)})"


# ─── Settings stub (module hook for future Settings tab) ──────────────────────

CONTEXT_BUFFER_SETTINGS = {
    "buffer_size_lines": BUFFER_SIZE_LINES,
    "compression_model": COMPRESSION_MODEL,
    "hyperindex_method": HYPERINDEX_METHOD,
    "blockchain_backend": BLOCKCHAIN_BACKEND,
}
