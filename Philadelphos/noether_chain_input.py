#!/usr/bin/env python3
"""
==============================================================================
NOETHER INFORMATION CURRENT — TEXT INPUT CHAIN ENTRY
==============================================================================
Ainulindale Conjecture / SMNNIP

Purpose:
    Receives raw text input and initiates the Noether Information Current
    chain. The sedenion acts as the I/O gate. Input is gated on prompt
    submission, buffered in a 3-layer context buffer, and queued for
    processing. Thread pauses on gate close.

Architecture:
    text_input()
        → SedenionGate (I/O gating + zero-divisor collapse detection)
        → ContextBuffer (3-layer: raw FIFO / compressed / HyperWebster index)
        → NoetherCurrentChain (downstream — focal point mapping)

Layer 1: 2x context capacity — raw prompt history (no responses), FIFO cycle
Layer 2: FIFO-out prompt compressed to maintain context depth
Layer 3: HyperWebster index → JSON placement → Vast Repository

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
==============================================================================
"""

import threading
import queue
import time
import hashlib
from typing import Optional, List, Tuple, Any
from dataclasses import dataclass, field
from collections import deque


# ==============================================================================
# SECTION 0: SEDENION GATE
# ==============================================================================

SEDENION_DIM = 16  # 2^4 — one step above octonions via Cayley-Dickson

@dataclass
class SedenionElement:
    """
    A 16-component sedenion.
    Components [0] = real, [1..15] = imaginary units e1..e15.
    Zero divisors exist — their detection is the collapse signal.
    """
    components: List[float] = field(default_factory=lambda: [0.0] * SEDENION_DIM)

    def norm_sq(self) -> float:
        return sum(c * c for c in self.components)

    def is_zero_divisor_candidate(self, threshold: float = 1e-10) -> bool:
        """
        A sedenion near a zero divisor has near-zero norm despite
        non-zero components. This is the catastrophic collapse signal.
        """
        norm = self.norm_sq()
        has_content = any(abs(c) > threshold for c in self.components)
        return has_content and norm < threshold

    @classmethod
    def from_text(cls, text: str) -> "SedenionElement":
        """
        Encode text into a sedenion via SHA-512 hash projection.
        16 components from 16 8-byte chunks of the hash.
        Normalization preserves relative magnitudes.
        """
        h = hashlib.sha512(text.encode("utf-8")).digest()  # 64 bytes
        raw = [
            int.from_bytes(h[i*4:(i+1)*4], "big") / 0xFFFFFFFF
            for i in range(SEDENION_DIM)
        ]
        return cls(components=raw)


class SedenionGate:
    """
    The I/O gate of the Noether Information Current.

    On prompt submission:
        - Gates input (closes)
        - Encodes text to sedenion
        - Detects zero-divisor candidates (focal collapse signal)
        - Buffers prompt
        - Releases gate (opens) when chain is ready for next input
    """

    def __init__(self):
        self._gate = threading.Event()
        self._gate.set()  # open initially

    def submit(self, text: str) -> Tuple[str, SedenionElement, bool]:
        """
        Block until gate is open, then close it, encode, return.
        Returns: (text, sedenion, is_collapse_candidate)
        """
        self._gate.wait()       # block if gate closed
        self._gate.clear()      # close gate — thread paused
        se = SedenionElement.from_text(text)
        collapse = se.is_zero_divisor_candidate()
        return text, se, collapse

    def release(self):
        """Open gate for next input."""
        self._gate.set()


# ==============================================================================
# SECTION 1: CONTEXT BUFFER (3 LAYERS)
# ==============================================================================

# Placeholder — replace with actual Claude context window size
CLAUDE_CONTEXT_TOKENS = 200_000
LAYER1_CAPACITY_TOKENS = CLAUDE_CONTEXT_TOKENS * 2


def _rough_token_count(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def _compress_prompt(text: str, target_ratio: float = 0.5) -> str:
    """
    Layer 2 compression: truncate to target_ratio of original length
    to maintain context depth when FIFO-evicting from Layer 1.
    Replace with semantic compression when available.
    """
    cutoff = max(64, int(len(text) * target_ratio))
    if len(text) <= cutoff:
        return text
    return text[:cutoff] + "…[compressed]"


@dataclass
class BufferedPrompt:
    text: str
    sedenion: SedenionElement
    collapse_candidate: bool
    token_count: int
    timestamp: float = field(default_factory=time.time)
    compressed: bool = False


class ContextBuffer:
    """
    3-layer context buffer.

    Layer 1: Raw prompt FIFO deque, capacity = 2x Claude context.
             Prompts only — no responses.
    Layer 2: When Layer 1 is full, FIFO-out prompt is compressed
             before being passed to Layer 3.
    Layer 3: HyperWebster indexing stub — emits (word_key, prompt)
             pairs for JSON placement in the Vast Repository.
    """

    def __init__(self):
        self._layer1: deque = deque()
        self._layer1_tokens: int = 0
        self._layer3_queue: queue.Queue = queue.Queue()

    def push(self, prompt: BufferedPrompt):
        """Accept a new prompt into Layer 1."""
        # Evict from front if over capacity
        while (self._layer1_tokens + prompt.token_count > LAYER1_CAPACITY_TOKENS
               and self._layer1):
            evicted = self._layer1.popleft()
            self._layer1_tokens -= evicted.token_count
            self._layer2_compress_and_forward(evicted)

        self._layer1.append(prompt)
        self._layer1_tokens += prompt.token_count

    def _layer2_compress_and_forward(self, prompt: BufferedPrompt):
        """Compress evicted prompt and forward to Layer 3."""
        compressed_text = _compress_prompt(prompt.text)
        prompt.text = compressed_text
        prompt.token_count = _rough_token_count(compressed_text)
        prompt.compressed = True
        self._layer3_index(prompt)

    def _layer3_index(self, prompt: BufferedPrompt):
        """
        Layer 3: HyperWebster indexing.
        Tokenizes prompt into words, queues (word, timestamp, snippet) for
        ingestion via Callimachus/hyperwebster_layer3.py → JSON word shards.
        Full addressing (Horner bijection / Cayley-Dickson) handled by bridge.
        Bridge lazy-loaded: Ainulindale boots cleanly without Callimachus.
        """
        words   = prompt.text.split()
        snippet = prompt.text[:128]
        for word in words:
            key = word.lower().strip(".,!?;:\"'")
            if key:
                self._layer3_queue.put((key, prompt.timestamp, snippet))

        # Opportunistic drain to HyperWebster bridge
        self._try_drain_to_hw()

    # -- HyperWebster bridge (lazy) ----------------------------------------

    _hw_bridge = None          # class-level singleton, set on first successful import
    _hw_tried  = False

    def _try_drain_to_hw(self):
        """
        Drain Layer 3 queue to HyperWebster bridge when available.
        Silently no-ops if Callimachus is not on the path.
        """
        if not ContextBuffer._hw_tried:
            ContextBuffer._hw_tried = True
            try:
                import importlib, sys, os
                # Allow callimachus to be found from Ptolemy root
                ptol_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                if ptol_root not in sys.path:
                    sys.path.insert(0, ptol_root)
                from Callimachus.hyperwebster_layer3 import HyperWebsterLayer3
                ContextBuffer._hw_bridge = HyperWebsterLayer3()
            except Exception:
                pass  # Callimachus unavailable — Layer 3 queue holds entries

        bridge = ContextBuffer._hw_bridge
        if bridge is None:
            return
        entries = self.layer3_drain()
        if entries:
            try:
                bridge.ingest(entries)
            except Exception:
                pass  # non-fatal — entries lost but pipeline continues

    def layer3_drain(self) -> List[Tuple[str, float, str]]:
        """Drain all pending Layer 3 index entries."""
        entries = []
        while not self._layer3_queue.empty():
            try:
                entries.append(self._layer3_queue.get_nowait())
            except queue.Empty:
                break
        return entries

    def layer1_snapshot(self) -> List[str]:
        """Return current Layer 1 prompt texts."""
        return [p.text for p in self._layer1]

    @property
    def layer1_depth(self) -> int:
        return len(self._layer1)

    @property
    def layer1_token_fill(self) -> int:
        return self._layer1_tokens


# ==============================================================================
# SECTION 2: CHAIN ENTRY POINT
# ==============================================================================

class NoetherChainInput:
    """
    Text input entry point for the Noether Information Current chain.

    Usage:
        chain = NoetherChainInput()
        result = chain.submit("your text here")
        # result.sedenion, result.collapse_candidate, result.layer1_depth
        chain.release()   # open gate for next input
    """

    def __init__(self):
        self.gate = SedenionGate()
        self.buffer = ContextBuffer()

    def submit(self, text: str) -> BufferedPrompt:
        """
        Gate → encode → buffer. Returns the BufferedPrompt.
        Caller must call .release() when downstream processing is done.
        """
        raw_text, sedenion, collapse = self.gate.submit(text)
        tokens = _rough_token_count(raw_text)
        prompt = BufferedPrompt(
            text=raw_text,
            sedenion=sedenion,
            collapse_candidate=collapse,
            token_count=tokens,
        )
        self.buffer.push(prompt)
        return prompt

    def release(self):
        """Release gate for next input."""
        self.gate.release()

    def status(self) -> dict:
        return {
            "layer1_depth": self.buffer.layer1_depth,
            "layer1_tokens": self.buffer.layer1_token_fill,
            "layer1_capacity": LAYER1_CAPACITY_TOKENS,
            "layer3_pending": self.buffer._layer3_queue.qsize(),
        }


# ==============================================================================
# SECTION 3: SMOKE TEST
# ==============================================================================

if __name__ == "__main__":
    chain = NoetherChainInput()

    test_inputs = [
        "The sedenion is the I/O gate of the Noether Information Current.",
        "Multiple focal points collapse to a single non-extinct data collection.",
        "Catastrophic waveform collapse — tuning shifts the focal point.",
    ]

    for text in test_inputs:
        print(f"\n[INPUT] {text[:60]}...")
        p = chain.submit(text)
        print(f"  sedenion norm_sq : {p.sedenion.norm_sq():.6f}")
        print(f"  collapse signal  : {p.collapse_candidate}")
        print(f"  tokens (est)     : {p.token_count}")
        print(f"  layer1 depth     : {chain.buffer.layer1_depth}")
        chain.release()

    print("\n[LAYER 3 INDEX ENTRIES]")
    for entry in chain.buffer.layer3_drain():
        print(f"  key={entry[0]!r:20s} ts={entry[1]:.2f}")

    print("\n[STATUS]", chain.status())
