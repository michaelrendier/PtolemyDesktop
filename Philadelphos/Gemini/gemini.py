#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.Gemini — Google Gemini as a Ptolemy feature
=========================================================
google-genai SDK (v1.73+, GA April 2026).
Package: pip install google-genai
API key: GEMINI_API_KEY environment variable

Architecture:
  - Streaming responses with thinking enabled (gemini-2.5-flash)
  - SMNNIP derivation engine as auto-callable tools (optional)
  - Status header: "Managed by: gemini-2.5-flash" on init
  - Chat sessions with history via client.chats

Author: Ptolemy project / Philadelphos layer
"""

import os
import json
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Generator

from google import genai
from google.genai import types

# ── SMNNIP engine (optional) ──────────────────────────────────────────────────
try:
    from Ainulindale.core.smnnip_derivation_pure import (
        SMNNIPDerivationEngine, FieldState,
    )
    _ENGINE = SMNNIPDerivationEngine()
    ENGINE_AVAILABLE = True
except Exception:
    _ENGINE = None
    ENGINE_AVAILABLE = False

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL = "gemini-2.5-flash"

# ── HyperWebster context file ─────────────────────────────────────────────────
_CONTEXT_FILE = (
    Path(__file__).resolve().parent.parent  # Philadelphos/
    / "context" / "gemini_context.json"
)

# ── Stable system prompt ──────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are Gemini, integrated as an AI feature of Ptolemy — a \
modular Python3 research and engineering platform. You run within the Philadelphos \
layer (AI/LLM subsystem) of Ptolemy.

Ptolemy modules:
  Alexandria   — geo/mapping
  Anaximander  — navigation
  Archimedes   — math engine (UFformulary: 508 formula files)
  Callimachus  — database / HyperWebster lexical datatype
  Kryptos      — cipher engines
  Mouseion     — OpenGL GUI
  Phaleron     — browser / web tools
  Pharos       — main shell UI
  Philadelphos — AI/LLM layer (you live here)
  Tesla        — networking / sockets
  Ptolemy++    — C++ companion (Gemini-ncurses)

You have deep knowledge of the SMNNIP (Standard Model of Neural Network \
Information Propagation) — a hypercomplex neural Lagrangian with term-for-term \
isomorphism to the Standard Model of particle physics.

SMNNIP algebra tower (Cayley-Dickson / Dixon 1994):
  ℝ → ℂ → ℍ → 𝕆 → 𝕊
  Maps to gauge group U(1) × SU(2) × SU(3)

SMNNIP derivation engine operations:
  1. Euler-Lagrange equations of motion
  2. Covariant derivative (gauge-minimal coupling)
  3. Field strength tensor (Yang-Mills curvature)
  4. Noether current (conservation law — empirically verified: violation=0.0)
  5. Algebra multiplication (Cayley-Dickson)
  6. Cayley-Dickson inclusion / projection
  7. RG flow (renormalization group: α, ħ, GUT convergence)

When asked about physics or mathematics, reason carefully and precisely.
You are terse but complete. No filler."""


# ── SMNNIP tool functions (auto-callable by google-genai) ─────────────────────

def _build_field_state(
    phi_r: float = 1.0,
    phi_c: float = 0.5,
    phi_q0: float = 0.3,
    phi_q1: float = 0.2,
    phi_o0: float = 0.1,
    phi_o1: float = 0.1,
    mass: float = 0.5,
    coupling: float = 0.1,
) -> "FieldState":
    return FieldState(
        phi_r=phi_r,
        phi_c=complex(0, phi_c),
        phi_q=complex(phi_q0, phi_q1),
        phi_o=complex(phi_o0, phi_o1),
        mass=mass, coupling=coupling,
        hbar=1.0, c=1.0, g=1.0,
    )


def smnnip_lagrangian(
    phi_r: float = 1.0,
    phi_c: float = 0.5,
    mass: float = 0.5,
    coupling: float = 0.1,
) -> str:
    """
    Evaluate the SMNNIP Lagrangian for given field parameters.
    Returns kinetic, mass, interaction, gauge terms and total L.

    Args:
        phi_r: Real field component.
        phi_c: Complex field component (imaginary part).
        mass: Field mass parameter.
        coupling: Interaction coupling constant.

    Returns:
        JSON string with Lagrangian terms and total.
    """
    if not ENGINE_AVAILABLE:
        return json.dumps({"error": "SMNNIP engine not available"})
    try:
        fs  = _build_field_state(phi_r=phi_r, phi_c=phi_c,
                                  mass=mass, coupling=coupling)
        lag = _ENGINE.lagrangian(fs)
        return json.dumps({k: round(float(v), 6) for k, v in lag.items()})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def smnnip_noether(
    phi_r: float = 1.0,
    phi_c: float = 0.5,
) -> str:
    """
    Compute the Noether conserved current for the SMNNIP Lagrangian.
    Returns conservation status and violation measure.

    Args:
        phi_r: Real field component.
        phi_c: Complex field component (imaginary part).

    Returns:
        JSON string with current, conserved flag, and violation.
    """
    if not ENGINE_AVAILABLE:
        return json.dumps({"error": "SMNNIP engine not available"})
    try:
        fs      = _build_field_state(phi_r=phi_r, phi_c=phi_c)
        noether = _ENGINE.noether(fs)
        return json.dumps({
            "current":   str(noether.get("current", "N/A")),
            "conserved": noether.get("conserved", False),
            "violation": round(float(noether.get("violation", 0.0)), 8),
        })
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def smnnip_rg_flow(
    energy: float = 1000.0,
) -> str:
    """
    Evaluate SMNNIP renormalization group flow at a given energy scale.
    Returns alpha(E), hbar_eff(E), and GUT convergence information.

    Args:
        energy: Energy scale in GeV.

    Returns:
        JSON string with alpha, hbar_eff, and GUT scale info.
    """
    if not ENGINE_AVAILABLE:
        return json.dumps({"error": "SMNNIP engine not available"})
    try:
        fs    = _build_field_state()
        alpha = _ENGINE.rg_alpha(fs, energy)
        hbar  = _ENGINE.rg_hbar(fs, energy)
        gut   = _ENGINE.gut_flow(fs)
        return json.dumps({
            "alpha_at_E": round(float(alpha), 6),
            "hbar_eff":   round(float(hbar), 6),
            "gut_scale":  str(gut),
            "energy_GeV": energy,
        })
    except Exception as exc:
        return json.dumps({"error": str(exc)})


_TOOL_FUNCTIONS = [smnnip_lagrangian, smnnip_noether, smnnip_rg_flow]


# ── Status dataclass ──────────────────────────────────────────────────────────
@dataclass
class GeminiStatus:
    model: str = MODEL
    engine: bool = ENGINE_AVAILABLE
    ready: bool = False
    api_key_set: bool = False
    error: Optional[str] = None

    def header(self) -> str:
        engine_flag = "SMNNIP:on" if self.engine else "SMNNIP:off"
        status = "ready" if self.ready else ("error" if self.error else "init")
        return f"Managed by: {self.model}  [{engine_flag}]  [{status}]"


# ── Main Gemini class ─────────────────────────────────────────────────────────
class Gemini:
    """
    Google Gemini client — Ptolemy's Gemini feature.

    Uses google-genai SDK (v1.73+, GA April 2026).
    Streaming chat with thinking, auto tool-calling for SMNNIP engine.

    Usage:
        gemini = Gemini()
        print(gemini.status.header())

        # Streaming
        for chunk in gemini.stream("What is the SMNNIP Lagrangian?"):
            print(chunk, end="", flush=True)
        print()

        # Single-shot
        response = gemini.chat("Derive the Noether current.")
        print(response)

    Environment:
        GEMINI_API_KEY — Google AI API key (required)
    """

    def __init__(self, api_key: Optional[str] = None, use_tools: bool = True):
        key = api_key or os.environ.get("GEMINI_API_KEY")
        self.status = GeminiStatus()

        if not key:
            self.status.error = "GEMINI_API_KEY not set"
            self._client = None
            self._chat   = None
            return

        self.status.api_key_set = True
        self._client = genai.Client(api_key=key)
        self._use_tools = use_tools and ENGINE_AVAILABLE

        # Build config — thinking enabled, tools wired
        tools = _TOOL_FUNCTIONS if self._use_tools else None
        self._config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1,       # dynamic thinking budget
                include_thoughts=False,   # keep thought tokens internal
            ),
            tools=tools,
        )

        # Create persistent chat session
        try:
            self._chat = self._client.chats.create(
                model=MODEL,
                config=self._config,
            )
            self.status.ready = True
        except Exception as exc:
            self.status.error = str(exc)
            self._chat = None

        print(self.status.header())

    # ── Streaming chat ────────────────────────────────────────────────────────

    def stream(
        self,
        message: str,
    ) -> Generator[str, None, None]:
        """
        Stream a response from Gemini.

        Yields text chunks as they arrive.
        Auto function calling handles SMNNIP tool invocations transparently.
        History is maintained within the chat session.

        Args:
            message: User message text.

        Yields:
            str — text chunks
        """
        if not self._client or not self._chat:
            yield f"[Gemini error: {self.status.error}]"
            return

        try:
            for chunk in self._chat.send_message_stream(message):
                if chunk.text:
                    yield chunk.text
        except Exception as exc:
            yield f"\n[Gemini error: {exc}]"

    def chat(self, message: str) -> str:
        """
        Single-shot chat — collects the full streaming response.

        Returns:
            Complete response text.
        """
        return "".join(self.stream(message))

    def clear_history(self) -> None:
        """Reset the chat session (start fresh context)."""
        if not self._client:
            return
        try:
            self._chat = self._client.chats.create(
                model=MODEL,
                config=self._config,
            )
        except Exception as exc:
            self.status.error = str(exc)

    def history_turns(self) -> int:
        """Number of turns in the current chat session."""
        if not self._chat:
            return 0
        try:
            return len(self._chat.get_history()) // 2
        except Exception:
            return 0

    # ── HyperWebster context persistence ─────────────────────────────────────

    def load_context(self) -> dict:
        """
        Load gemini_context.json into memory.
        Returns the parsed dict, or empty dict if file missing/corrupt.
        """
        try:
            with open(_CONTEXT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_context(self, extra: Optional[dict] = None) -> None:
        """
        Update gemini_context.json with current session state.
        """
        try:
            ctx = self.load_context()
            now = datetime.datetime.utcnow().isoformat() + "Z"
            ctx.setdefault("metadata", {})
            ctx.setdefault("session_memory", {})
            ctx["metadata"]["last_updated"] = now
            ctx["metadata"]["session_count"] = (
                ctx["metadata"].get("session_count", 0) + 1
            )
            ctx["session_memory"]["last_session"] = now
            ctx["session_memory"]["session_count"] = (
                ctx["metadata"]["session_count"]
            )
            ctx.setdefault("smnnip_knowledge", {}).setdefault(
                "verified_results", {}
            )["engine_available"] = ENGINE_AVAILABLE
            if extra:
                for key, val in extra.items():
                    ctx[key] = val
            with open(_CONTEXT_FILE, "w", encoding="utf-8") as f:
                json.dump(ctx, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def log_io(
        self,
        stdin:  Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> None:
        """
        Append I/O entries to gemini_context.json io_log.
        Each entry is timestamped. Rolls at max_entries.
        """
        try:
            ctx = self.load_context()
            io  = ctx.setdefault("io_log", {})
            now = datetime.datetime.utcnow().isoformat() + "Z"
            max_e = io.get("max_entries", 100)
            for key, val in [("recent_stdin", stdin),
                              ("recent_stdout", stdout),
                              ("recent_stderr", stderr)]:
                if val is not None:
                    log = io.setdefault(key, [])
                    log.append({"ts": now, "text": val})
                    if len(log) > max_e:
                        io[key] = log[-max_e:]
            with open(_CONTEXT_FILE, "w", encoding="utf-8") as f:
                json.dump(ctx, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def __repr__(self) -> str:
        return f"Gemini(model={MODEL!r}, ready={self.status.ready})"


# ── Standalone REPL ───────────────────────────────────────────────────────────

def _repl() -> None:
    """Simple interactive REPL for testing Gemini from the terminal."""
    print("=" * 60)
    gem = Gemini()
    if not gem.status.ready:
        print(f"Error: {gem.status.error}")
        return
    print("Type your message. 'quit' to exit. 'clear' to reset history.")
    print("=" * 60)
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Gemini REPL.")
            break
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Exiting Gemini REPL.")
            break
        if user_input.lower() == "clear":
            gem.clear_history()
            print("[History cleared]")
            continue
        print("Gemini: ", end="", flush=True)
        for chunk in gem.stream(user_input):
            print(chunk, end="", flush=True)
        print()


if __name__ == "__main__":
    _repl()
