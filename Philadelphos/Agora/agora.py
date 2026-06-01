#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.Agora — Ptolemy dual-AI parallel chat
====================================================
The Agora routes a single query to Claude and Gemini independently
and in parallel. The models never see each other's responses.

Sigma valuation rationale:
  When two models are queried independently on the same question,
  their responses are statistically uncorrelated (assuming no
  shared training contamination on the specific query). Agreement
  between independent responses increases confidence (sigma).
  Disagreement surfaces genuine uncertainty or domain boundaries.
  Cross-contamination — showing one model the other's response —
  collapses independence and reduces the measurement to 1 sigma
  (correlated noise), defeating the purpose.

Usage:
    agora = Agora()
    result = agora.query("Derive the SMNNIP Noether current.")
    print(result.claude)
    print(result.gemini)
    print(result.agreement_flag)   # rough lexical overlap signal

    # Streaming to terminal (interleaved, labeled)
    agora.stream_to_terminal("What is the GUT convergence scale?")

Author: Ptolemy project / Philadelphos layer
"""

import threading
import datetime
from dataclasses import dataclass, field
from typing import Optional, Generator, Tuple

from Philadelphos.Ainur.ainur import Ainur
from Philadelphos.Gemini.gemini import Gemini


# ── Result container ──────────────────────────────────────────────────────────

@dataclass
class AgoraResult:
    """
    Container for a dual-AI query result.

    Fields:
        query:          The original query sent to both models.
        claude:         Full response text from Claude.
        gemini:         Full response text from Gemini.
        claude_error:   Error string if Claude failed, else None.
        gemini_error:   Error string if Gemini failed, else None.
        elapsed_s:      Wall-clock seconds for both responses to complete.
        agreement_flag: True if responses share significant vocabulary overlap.
                        Rough signal only — not a substitute for reading both.
        timestamp:      UTC ISO timestamp.
    """
    query:          str
    claude:         str  = ""
    gemini:         str  = ""
    claude_error:   Optional[str] = None
    gemini_error:   Optional[str] = None
    elapsed_s:      float = 0.0
    agreement_flag: Optional[bool] = None
    timestamp:      str  = field(
        default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z"
    )

    def _word_set(self, text: str) -> set:
        return {w.lower().strip(".,;:!?()[]") for w in text.split() if len(w) > 4}

    def compute_agreement(self, threshold: float = 0.35) -> bool:
        """
        Jaccard similarity on content words (>4 chars).
        Above threshold → agreement_flag = True.
        This is a rough lexical signal, not semantic equivalence.
        """
        a = self._word_set(self.claude)
        b = self._word_set(self.gemini)
        if not a or not b:
            self.agreement_flag = None
            return None
        jaccard = len(a & b) / len(a | b)
        self.agreement_flag = jaccard >= threshold
        return self.agreement_flag

    def sigma_note(self) -> str:
        """Human-readable sigma valuation note."""
        if self.agreement_flag is None:
            return "sigma: insufficient data"
        if self.agreement_flag:
            return "sigma: models converge — higher confidence"
        return "sigma: models diverge — review both responses carefully"

    def __str__(self) -> str:
        lines = [
            f"Query: {self.query}",
            f"Timestamp: {self.timestamp}",
            f"Elapsed: {self.elapsed_s:.1f}s",
            "",
            "── Claude (" + ("ok" if not self.claude_error else f"error: {self.claude_error}") + ") ──",
            self.claude or "[no response]",
            "",
            "── Gemini (" + ("ok" if not self.gemini_error else f"error: {self.gemini_error}") + ") ──",
            self.gemini or "[no response]",
            "",
            self.sigma_note(),
        ]
        return "\n".join(lines)


# ── Agora class ───────────────────────────────────────────────────────────────

class Agora:
    """
    Ptolemy dual-AI chat — Claude + Gemini in parallel, independently.

    Both models receive the same query simultaneously via threads.
    Neither model sees the other's response at any point.
    History is maintained separately within each model's own session.

    Usage:
        agora = Agora()
        result = agora.query("What is the Yang-Mills field strength tensor?")
        print(result)

        # Stream both to terminal with labels
        agora.stream_to_terminal("Explain RG flow in SMNNIP.")

        # Clear history on both independently
        agora.clear_history()
    """

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
    ):
        print("Agora — initializing Claude...")
        self.claude = Ainur(api_key=claude_api_key)

        print("Agora — initializing Gemini...")
        self.gemini = Gemini(api_key=gemini_api_key)

        self._ready_claude = self.claude.status.ready
        self._ready_gemini = self.gemini.status.ready

        status_parts = []
        if self._ready_claude:
            status_parts.append("Claude:ready")
        else:
            status_parts.append(f"Claude:error({self.claude.status.error})")
        if self._ready_gemini:
            status_parts.append("Gemini:ready")
        else:
            status_parts.append(f"Gemini:error({self.gemini.status.error})")

        print(f"Agora — [{' | '.join(status_parts)}]")
        print("Agora — model independence maintained for sigma valuation")

    # ── Parallel query ────────────────────────────────────────────────────────

    def query(self, message: str) -> AgoraResult:
        """
        Send message to both Claude and Gemini in parallel.
        Blocks until both complete. Returns AgoraResult.

        Models are queried in separate threads — neither sees the other's
        response at any point during or after generation.
        """
        result = AgoraResult(query=message)
        t_start = datetime.datetime.utcnow()

        claude_done = threading.Event()
        gemini_done = threading.Event()

        def run_claude():
            try:
                result.claude = self.claude.chat(message)
            except Exception as exc:
                result.claude_error = str(exc)
            finally:
                claude_done.set()

        def run_gemini():
            try:
                result.gemini = self.gemini.chat(message)
            except Exception as exc:
                result.gemini_error = str(exc)
            finally:
                gemini_done.set()

        t1 = threading.Thread(target=run_claude, daemon=True)
        t2 = threading.Thread(target=run_gemini, daemon=True)
        t1.start()
        t2.start()
        claude_done.wait()
        gemini_done.wait()

        result.elapsed_s = (datetime.datetime.utcnow() - t_start).total_seconds()
        result.compute_agreement()
        return result

    # ── Streaming to terminal ─────────────────────────────────────────────────

    def stream_to_terminal(self, message: str) -> AgoraResult:
        """
        Stream both models to the terminal simultaneously, labeled.

        Output is interleaved line-by-line from two threads, prefixed:
          [Claude] ...
          [Gemini] ...

        Returns AgoraResult with full collected responses after streaming.
        Maintains model independence — output is separated by label only.
        """
        import sys

        result    = AgoraResult(query=message)
        lock      = threading.Lock()
        t_start   = datetime.datetime.utcnow()
        c_buf: list[str] = []
        g_buf: list[str] = []

        def stream_claude():
            try:
                for chunk in self.claude.stream(message):
                    c_buf.append(chunk)
                    with lock:
                        sys.stdout.write(f"\033[36m[Claude]\033[0m {chunk}")
                        sys.stdout.flush()
                result.claude = "".join(c_buf)
            except Exception as exc:
                result.claude_error = str(exc)
                with lock:
                    print(f"\033[36m[Claude error]\033[0m {exc}")

        def stream_gemini():
            try:
                for chunk in self.gemini.stream(message):
                    g_buf.append(chunk)
                    with lock:
                        sys.stdout.write(f"\033[33m[Gemini]\033[0m {chunk}")
                        sys.stdout.flush()
                result.gemini = "".join(g_buf)
            except Exception as exc:
                result.gemini_error = str(exc)
                with lock:
                    print(f"\033[33m[Gemini error]\033[0m {exc}")

        t1 = threading.Thread(target=stream_claude, daemon=True)
        t2 = threading.Thread(target=stream_gemini, daemon=True)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        print()  # trailing newline

        result.elapsed_s = (datetime.datetime.utcnow() - t_start).total_seconds()
        result.compute_agreement()
        return result

    def clear_history(self) -> None:
        """Clear conversation history on both models independently."""
        self.claude.clear_history()
        self.gemini.clear_history()
        print("Agora — history cleared on both models independently")

    def __repr__(self) -> str:
        return (
            f"Agora(claude={self._ready_claude}, gemini={self._ready_gemini})"
        )


# ── Standalone REPL ───────────────────────────────────────────────────────────

def _repl() -> None:
    """Interactive Agora REPL — queries both models, prints labeled results."""
    from Philadelphos.data_input import parse_and_run as _data_input
    print("=" * 70)
    agora = Agora()
    if not agora._ready_claude and not agora._ready_gemini:
        print("Neither model is available. Check API keys.")
        return
    print()
    print("Commands: 'quit' | 'clear' | 'last' (reprint last result)")
    print("=" * 70)
    last_result: Optional[AgoraResult] = None

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Agora.")
            break
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Exiting Agora.")
            break
        if user_input.lower() == "clear":
            agora.clear_history()
            continue
        if user_input.lower() == "last" and last_result:
            print(last_result)
            continue
        if user_input.lower().startswith("/datainput"):
            _data_input(user_input, ainur_instance=agora.claude)
            continue

        print()
        result = agora.stream_to_terminal(user_input)
        last_result = result
        print()
        print(f"  Elapsed: {result.elapsed_s:.1f}s  |  {result.sigma_note()}")


if __name__ == "__main__":
    _repl()
