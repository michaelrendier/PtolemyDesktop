#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.data_input — /DataInput command handler
=====================================================
Ptolemy Project

Usage (from any Ptolemy REPL):
    /DataInput          — prompt for directory, ingest, report
    /DataInput --DM     — same + 5-point diagnostic mode tuning sweep

Flow:
    1. Ask for absolute path to text corpus directory
    2. Load all .txt files via load_corpus()
    3. Start SMNNIP tower (ℝ → ℂ → ℍ → 𝕆)
    4. Train on corpus
    5. Save weights to Philadelphos/weights/
    6. Report "Data Consumed"
    7. Stop tower
    --DM: after ingestion, run 5 diagnostic responses on a sample prompt
          at δ = -0.2, -0.1, 0.0, +0.1, +0.2 to map the focal collapse curve

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
"""

from __future__ import annotations

import os
import sys
import json
import pickle
import datetime
from typing import Optional, Tuple

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Weights directory ─────────────────────────────────────────────────────────
_WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights")


def _ensure_weights_dir():
    os.makedirs(_WEIGHTS_DIR, exist_ok=True)


def _weights_path(corpus_name: str) -> str:
    return os.path.join(_WEIGHTS_DIR, f"{corpus_name}_weights.pkl")


# ==============================================================================
# WEIGHT SAVE / LOAD
# ==============================================================================

def save_weights(L0, L1, L2, L3, C, chars, corpus_name: str,
                 ctx: int = 4, hidden: int = 24) -> str:
    """Serialize trained layer weights + vocab to pickle. Returns path."""
    _ensure_weights_dir()
    path = _weights_path(corpus_name)

    def _layer_state(layer):
        state = {}
        for attr in vars(layer):
            val = getattr(layer, attr)
            if hasattr(val, '__dict__') or isinstance(val, (list, float, int)):
                try:
                    state[attr] = val
                except Exception:
                    pass
        return state

    bundle = {
        "corpus":    corpus_name,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "chars":     chars,    # sorted unique chars from corpus — needed for inference
        "ctx":       ctx,      # context window used during training
        "hidden":    hidden,   # hidden size used during training
        "L0": _layer_state(L0),
        "L1": _layer_state(L1),
        "L2": _layer_state(L2),
        "L3": _layer_state(L3),
    }

    with open(path, "wb") as f:
        pickle.dump(bundle, f)

    return path


def load_weights(corpus_name: str) -> Optional[dict]:
    """Load saved weights bundle. Returns dict or None."""
    path = _weights_path(corpus_name)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def weights_exist(corpus_name: str) -> bool:
    return os.path.exists(_weights_path(corpus_name))


# ==============================================================================
# DIAGNOSTIC MODE — 5-point focal sweep
# ==============================================================================

_DM_DELTAS = [-0.2, -0.1, 0.0, 0.1, 0.2]
_DM_LABELS = [
    "δ=-0.2  [before collapse — wide]",
    "δ=-0.1  [just before collapse]",
    "δ= 0.0  [natural catastrophic collapse]",
    "δ=+0.1  [just after crest]",
    "δ=+0.2  [after crest — narrow]",
]


def run_diagnostic_mode(corpus_text: str, ainur_instance=None) -> None:
    """
    5-point focal sweep on a sample from the corpus.
    Uses the Noether reverse tower at each delta to show collapse curve.
    If ainur_instance provided, also runs through Ainur.stream() for each point.
    """
    from Philadelphos.Ainur.ainur import (
        _SedenionElement, _ReverseTower, _ContextBuffer
    )

    # Pull a representative sample from corpus — first 200 chars of meaningful text
    sample = ""
    for line in corpus_text.split("\n"):
        line = line.strip()
        if len(line) > 40:
            sample = line[:200]
            break
    if not sample:
        sample = corpus_text[:200].strip()

    print("\n" + "═" * 60)
    print("  DIAGNOSTIC MODE — Focal Collapse Sweep")
    print(f"  Sample: \"{sample[:80]}...\"")
    print("═" * 60)

    tower = _ReverseTower()
    buf   = _ContextBuffer()
    se    = _SedenionElement.from_text(sample)
    buf.push(sample, se)

    for delta, label in zip(_DM_DELTAS, _DM_LABELS):
        tower.focal_delta = delta
        val = tower.run(se, buf.snapshot())

        # Survivor count for this delta
        focal_map  = tower._focal_map(se.components)
        extinct    = tower._extinct(focal_map)
        survivors  = len(extinct)
        candidates = len(focal_map)

        print(f"\n  {label}")
        print(f"  Noether val : {val:+.6f}")
        print(f"  Survivors   : {survivors}/{candidates}")
        print(f"  Collapse sig: {se.is_zero_divisor()}")

        if ainur_instance is not None:
            try:
                ainur_instance._tower.focal_delta = delta
                print(f"  Response    : ", end="", flush=True)
                for chunk in ainur_instance.stream(
                    f"[DM δ={delta:+.1f}] {sample[:100]}",
                    use_history=False
                ):
                    print(chunk, end="", flush=True)
                print()
            except Exception as e:
                print(f"  [stream error: {e}]")

    print("\n" + "═" * 60)
    print("  Diagnostic complete. Review survivor counts and responses")
    print("  to determine optimal focal_delta for this corpus.")
    print("═" * 60 + "\n")

    # Reset tower delta
    if ainur_instance is not None:
        ainur_instance._tower.focal_delta = 0.0


# ==============================================================================
# MAIN HANDLER
# ==============================================================================

def handle_data_input(diagnostic_mode: bool = False,
                      ainur_instance=None) -> None:
    """
    Full /DataInput handler.

    1. Prompt for corpus directory
    2. Validate path
    3. Load corpus
    4. Start + train SMNNIP tower
    5. Save weights
    6. Report "Data Consumed"
    7. Stop tower
    8. If --DM: run 5-point diagnostic sweep
    """
    from Ainulindale.neural_network.smnnip_full_tower import (
        load_corpus, train_tower
    )

    # ── Step 1: Get path ──────────────────────────────────────────────────────
    print("\n[DataInput] Enter absolute path to corpus directory:")
    try:
        path = input("  Path: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n[DataInput] Cancelled.")
        return

    # ── Step 2: Validate ──────────────────────────────────────────────────────
    if not os.path.isabs(path):
        print(f"[DataInput] Error: path must be absolute. Got: {path!r}")
        return
    if not os.path.exists(path):
        print(f"[DataInput] Error: path does not exist: {path!r}")
        return

    # Count available files
    if os.path.isdir(path):
        txt_files = [f for f in os.listdir(path) if f.endswith(".txt")]
        if not txt_files:
            print(f"[DataInput] Error: no .txt files found in {path!r}")
            return
        corpus_name = os.path.basename(path.rstrip("/\\")) or "corpus"
        print(f"[DataInput] Found {len(txt_files)} .txt file(s) in {path!r}")
    else:
        corpus_name = os.path.splitext(os.path.basename(path))[0]
        print(f"[DataInput] Loading single file: {path!r}")

    # ── Step 3: Load corpus ───────────────────────────────────────────────────
    print(f"[DataInput] Loading corpus...")
    corpus_text = load_corpus(path)
    char_count  = len(corpus_text)
    word_count  = len(corpus_text.split())
    print(f"[DataInput] Corpus: {char_count:,} chars / {word_count:,} words")

    if char_count < 100:
        print("[DataInput] Error: corpus too small (< 100 chars). Aborting.")
        return

    # ── Step 4: Start + train SMNNIP tower ───────────────────────────────────
    print(f"\n[DataInput] Starting SMNNIP tower  ℝ → ℂ → ℍ → 𝕆")
    print(f"[DataInput] Training on: {corpus_name}")
    print()

    # Scale epochs/cap to corpus size — keep it reasonable for first run
    epochs = 10
    cap    = min(500, char_count // 10)
    cap    = max(cap, 50)

    try:
        L0, L1, L2, L3, C, chars = train_tower(
            corpus_text,
            epochs=epochs,
            lr=0.005,
            cap=cap,
            hidden=24,
            ctx=4,
        )
    except Exception as e:
        print(f"\n[DataInput] Tower training error: {e}")
        return

    # ── Step 5: Save weights ──────────────────────────────────────────────────
    print(f"\n[DataInput] Saving weights...")
    try:
        weights_path = save_weights(L0, L1, L2, L3, C, chars, corpus_name, ctx=4, hidden=24)
        print(f"[DataInput] Weights saved → {weights_path}")
    except Exception as e:
        print(f"[DataInput] Warning: could not save weights: {e}")

    # ── Step 6: Data Consumed ─────────────────────────────────────────────────
    print(f"\n{'═' * 50}")
    print(f"  Data Consumed")
    print(f"  Corpus  : {corpus_name}")
    print(f"  Files   : {len(txt_files) if os.path.isdir(path) else 1}")
    print(f"  Chars   : {char_count:,}")
    print(f"  Epochs  : {epochs}")
    print(f"  L0 loss : {L0.loss_hist[-1]:.4f}  (ℝ substrate)")
    print(f"  L1 loss : {L1.loss_hist[-1]:.4f}  (ℂ semantic)")
    print(f"  L2 loss : {L2.loss_hist[-1]:.4f}  (ℍ skills)")
    print(f"  L3 loss : {L3.loss_hist[-1]:.4f}  (𝕆 reasoning)")
    print(f"{'═' * 50}\n")

    # ── Step 7: Tower stopped ─────────────────────────────────────────────────
    # L0-L3 go out of scope — tower stops
    del L0, L1, L2, L3
    print("[DataInput] Tower stopped.")

    # ── Step 8: Diagnostic mode ───────────────────────────────────────────────
    if diagnostic_mode:
        run_diagnostic_mode(corpus_text, ainur_instance=ainur_instance)


# ==============================================================================
# COMMAND PARSER — called from REPL
# ==============================================================================

def parse_and_run(command: str, ainur_instance=None) -> bool:
    """
    Parse a /DataInput command string and run the handler.
    Returns True if command was handled, False if not a DataInput command.

    Accepts:
        /DataInput
        /DataInput --DM
        /datainput --dm   (case-insensitive)
    """
    parts = command.strip().split()
    if not parts:
        return False

    cmd = parts[0].lower()
    if cmd != "/datainput":
        return False

    flags  = [p.lower() for p in parts[1:]]
    dm     = "--dm" in flags

    handle_data_input(diagnostic_mode=dm, ainur_instance=ainur_instance)
    return True
