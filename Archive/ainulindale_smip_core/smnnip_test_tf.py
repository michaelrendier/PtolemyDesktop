#!/usr/bin/env python3
"""
==============================================================================
SMNNIP TENSORFLOW ENGINE — TEST AND DIAGNOSTIC HARNESS
==============================================================================
Standard Model of Neural Network Information Propagation
Ainulindalë Conjecture

This file is the test and diagnostic harness for smnnip_lagrangian_tf.py.
It does NOT contain engine logic. It imports the TF engine and drives it.

HOW TO USE:
  1. Edit ResearcherConfig below — all tunable values live here and ONLY here.
  2. Set BREAK_MODE to select the experiment type.
  3. Run: python3 smnnip_test_tf.py

BREAK_MODE options (same as pure harness, but running on TF engine):
  "none"               — Clean run. Also runs physics agreement check
                         against pure Python baseline.
  "boundary_probe"     — Walks inputs toward the algebra boundary.
  "symmetry_violation" — Deliberate gauge break. Noether monitor check.
  "noether_stress"     — Current-violating perturbations.
  "algebra_overflow"   — Drives past Omega saturation boundary.
  "timing_comparison"  — TF-only mode. Benchmarks TF engine vs pure Python
                         on identical data. Reports speedup factor and
                         verifies physics agreement (loss values must match
                         within tolerance).

PHYSICS AGREEMENT REQUIREMENT:
  The TF engine and pure Python engine must agree on loss values to within
  AGREEMENT_TOLERANCE (default: 0.5). If they disagree by more, the TF
  engine is not a valid production version of the pure engine.
  This check runs automatically in BREAK_MODE="none" and "timing_comparison".

Author : O Captain My Captain + Claude (Anthropic)
Date   : April 2026
==============================================================================
"""

import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ── TF Engine import ──────────────────────────────────────────────────────────
try:
    from smnnip_lagrangian_tf import (
        SMNNIPTowerTF, CharacterEncoder as CharacterEncoderTF,
        PhysicalConstants, build_training_data, train_epoch,
        generate_text, get_observer
    )
    TF_AVAILABLE = True
except ImportError as e:
    TF_AVAILABLE = False
    _TF_IMPORT_ERROR = str(e)

# ── Pure engine import (for physics agreement check) ──────────────────────────
try:
    from smnnip_lagrangian_pure import (
        SMNNIPTower as SMNNIPTowerPure,
        CharacterEncoder as CharacterEncoderPure,
        build_training_data as build_training_data_pure,
        train_epoch as train_epoch_pure,
        vec_scale, norm, zeros_vec
    )
    PURE_AVAILABLE = True
except ImportError:
    PURE_AVAILABLE = False


# ==============================================================================
# RESEARCHER CONFIGURATION
# All experimental parameters live here.
# Change values here. Do not edit the engine files.
# ==============================================================================

@dataclass
class ResearcherConfig:
    """
    All tunable research parameters in one place.
    Edit freely. These values never touch the engine source.
    """

    # ── Model architecture ────────────────────────────────────────────────
    hidden_dim:   int   = 32
    context_len:  int   = 4

    # ── Training parameters ───────────────────────────────────────────────
    n_epochs:     int   = 10
    learning_rate: float = 0.005
    max_samples:  int   = 200

    # ── Generation parameters ─────────────────────────────────────────────
    seed_text:    str   = "the "
    gen_chars:    int   = 80
    temperature:  float = 0.8

    # ── Physics agreement tolerance ───────────────────────────────────────
    # Loss values between TF and pure engines must agree within this tolerance.
    # Larger than you might expect because of floating point and init randomness.
    # Lower this if you want a stricter agreement check.
    agreement_tolerance: float = 0.5

    # ── Timing comparison parameters (BREAK_MODE = "timing_comparison") ──
    timing_epochs:      int   = 5      # Epochs to benchmark
    timing_max_samples: int   = 100    # Samples per epoch for timing

    # ── Boundary probe parameters ─────────────────────────────────────────
    probe_start:      float = 0.5
    probe_step:       float = 0.05
    probe_max_steps:  int   = 60
    probe_loss_spike:       float = 50.0
    probe_noether_spike:    float = 1.0
    probe_field_spike:      float = 20.0

    # ── Symmetry violation parameters ─────────────────────────────────────
    violation_phase:  float = 0.3
    violation_layer:  int   = 1

    # ── Noether stress parameters ──────────────────────────────────────────
    stress_perturbation: float = 0.5
    stress_steps:        int   = 20

    # ── Algebra overflow parameters ────────────────────────────────────────
    overflow_scale_start: float = 1.0
    overflow_scale_step:  float = 0.5
    overflow_max_steps:   int   = 30
    omega_limit: float = PhysicalConstants.OMEGA

    # ── Training text ─────────────────────────────────────────────────────
    training_text: str = field(default_factory=lambda: (
        "the quick brown fox jumps over the lazy dog. "
        "pack my box with five dozen liquor jugs. "
        "how vexingly quick daft zebras jump. "
        "the five boxing wizards jump quickly. "
        "sphinx of black quartz judge my vow. "
        "characters form tokens tokens form meaning. "
        "real algebra at the base complex above it. "
        "quaternions for skills octonions for reasoning. "
        "the higgs field gives mass to representations. "
        "noether conservation holds at every boundary. "
        "the uncertainty principle bounds all training. "
    ) * 3)


# ==============================================================================
# BREAK MODE SELECTION
# ==============================================================================

BREAK_MODE: str = "none"
# BREAK_MODE: str = "boundary_probe"
# BREAK_MODE: str = "symmetry_violation"
# BREAK_MODE: str = "noether_stress"
# BREAK_MODE: str = "algebra_overflow"
# BREAK_MODE: str = "timing_comparison"


# ==============================================================================
# PHYSICS AGREEMENT CHECK
# The TF engine must agree with the pure engine on the physics.
# ==============================================================================

def check_physics_agreement(cfg: ResearcherConfig) -> bool:
    """
    Runs one epoch on both engines with the same training text.
    Verifies loss values agree within cfg.agreement_tolerance.
    Returns True if agreement passes.
    """
    if not PURE_AVAILABLE:
        _print("Pure engine not available — cannot verify physics agreement.")
        return False
    if not TF_AVAILABLE:
        _print("TF engine not available.")
        return False

    _print("── Physics Agreement Check (TF vs Pure) ──")

    # Use a fixed seed for fair comparison
    random.seed(42)

    # Pure engine
    enc_pure  = CharacterEncoderPure(cfg.training_text)
    tower_pure = SMNNIPTowerPure(
        vocab_size=enc_pure.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )
    data_pure = build_training_data_pure(cfg.training_text, enc_pure, cfg.context_len)

    random.seed(42)
    t0 = time.time()
    pure_loss, pure_viol, pure_vev = train_epoch_pure(
        tower_pure, data_pure, cfg.learning_rate, min(cfg.max_samples, 50)
    )
    pure_time = time.time() - t0

    # TF engine
    random.seed(42)
    enc_tf    = CharacterEncoderTF(cfg.training_text)
    tower_tf  = SMNNIPTowerTF(
        vocab_size=enc_tf.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )
    data_tf = build_training_data(cfg.training_text, enc_tf, cfg.context_len)

    random.seed(42)
    t0 = time.time()
    tf_loss, tf_viol, tf_vev = train_epoch(
        tower_tf, data_tf, cfg.learning_rate, min(cfg.max_samples, 50)
    )
    tf_time = time.time() - t0

    # Compare
    loss_diff  = abs(tf_loss - pure_loss)
    viol_diff  = abs(tf_viol - pure_viol)
    agrees     = loss_diff < cfg.agreement_tolerance

    _print(f"  Pure engine:  loss={pure_loss:.4f}  noether={pure_viol:.6f}  "
           f"time={pure_time:.3f}s")
    _print(f"  TF engine:    loss={tf_loss:.4f}  noether={tf_viol:.6f}  "
           f"time={tf_time:.3f}s")
    _print(f"  Loss diff:    {loss_diff:.4f}  (tolerance: {cfg.agreement_tolerance})")
    _print(f"  Agreement:    {'✓ PASS' if agrees else '✗ FAIL — engines diverge'}")

    if tf_time > 0 and pure_time > 0:
        speedup = pure_time / tf_time
        _print(f"  Speedup (TF/Pure): {speedup:.2f}x  "
               f"({'TF faster' if speedup > 1 else 'Pure faster'} for this sample size)")

    return agrees


# ==============================================================================
# EXPERIMENT RUNNERS
# ==============================================================================

def run_clean(cfg: ResearcherConfig) -> None:
    """
    MODE: none
    TF engine clean run + physics agreement verification.
    """
    _header("CLEAN RUN (TF ENGINE) — Verifying correctness and physics agreement")

    if not TF_AVAILABLE:
        _print(f"TF engine unavailable: {_TF_IMPORT_ERROR}")
        return

    # Physics agreement first
    agreement_ok = check_physics_agreement(cfg)
    if not agreement_ok:
        _print("\n⚠  Physics agreement FAILED. TF engine diverges from pure engine.")
        _print("   The TF engine is not a valid production version.")
        _print("   Do not use for research runs until agreement is restored.")

    # Full TF training run
    _print("\n── Full TF Training Run ──")
    encoder = CharacterEncoderTF(cfg.training_text)
    tower   = SMNNIPTowerTF(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    data = build_training_data(cfg.training_text, encoder, cfg.context_len)
    _print(f"Training on {len(data)} samples for {cfg.n_epochs} epochs")
    _print(f"{'Epoch':>6}  {'Loss':>10}  {'Noether':>10}  {'VEV dist':>10}  Status")
    _print("─" * 55)

    for epoch in range(1, cfg.n_epochs + 1):
        t0                   = time.time()
        loss, violation, vev = train_epoch(
            tower, data, cfg.learning_rate, cfg.max_samples
        )
        dt = time.time() - t0
        tower.loss_history.append(loss)

        conserved = all(l.noether.is_conserved() for l in tower.layers_tf)
        status    = "✓" if conserved else "⚠ Noether violation"
        _print(f"  {epoch:4d}  {loss:10.4f}  {violation:10.6f}  {vev:10.4f}  "
               f"{status}  [{dt:.2f}s]")

    # Diagnostics
    _print("\n── Layer Diagnostics ──")
    for d in tower.full_diagnostics():
        _print(f"  {d['algebra']:2s} [{d['gauge']:8s}]  "
               f"α={d['alpha']:.6f}  ħ={d['hbar']:.3f}  "
               f"VEV_dist={d['vev_distance']:.4f}  "
               f"F={d['field_strength']:.4f}  "
               f"Noether={'✓' if d['conserved'] else '✗'}")

    # Generate
    generated = generate_text(
        tower, encoder, cfg.seed_text, cfg.gen_chars, cfg.temperature
    )
    _print(f"\n── Generated text ──")
    _print(f"  {generated}")

    bound = tower.uncertainty_bound()
    _print(f"\n── Uncertainty Principle ──")
    _print(f"  ħ_NN / 2 (bound):  {bound:.6f}")
    _print(f"  Final loss:        {tower.loss_history[-1]:.6f}")
    _print(f"  Bound respected:   {tower.loss_history[-1] >= bound}")


def run_timing_comparison(cfg: ResearcherConfig) -> None:
    """
    MODE: timing_comparison (TF-only mode)
    Benchmarks TF vs pure Python on identical workloads.
    Reports: time per epoch, samples/sec, speedup factor.
    Physics agreement is checked first — if engines disagree, the
    speedup measurement is meaningless (faster wrong is not better).
    """
    _header("TIMING COMPARISON — TF vs Pure Python throughput")

    if not TF_AVAILABLE or not PURE_AVAILABLE:
        _print("Both engines required for timing comparison.")
        return

    # Check physics agreement first
    _print("Step 1: Verifying physics agreement before benchmarking...")
    agreement_ok = check_physics_agreement(cfg)
    if not agreement_ok:
        _print("\n⚠  Cannot benchmark meaningfully — engines disagree on physics.")
        return

    _print("\nStep 2: Benchmark (physics verified)...")

    sample_sizes = [50, 100, 200]

    for n_samples in sample_sizes:
        _print(f"\n  Samples per epoch: {n_samples}")
        _print(f"  {'Engine':>10}  {'Epoch':>6}  {'Time':>8}  {'Loss':>8}  {'Samples/s':>10}")
        _print(f"  {'─'*50}")

        # ── Pure Python benchmark ──────────────────────────────────────────
        random.seed(42)
        enc_p  = CharacterEncoderPure(cfg.training_text)
        t_p    = SMNNIPTowerPure(
            vocab_size=enc_p.vocab_size,
            hidden_dim=cfg.hidden_dim,
            context_len=cfg.context_len
        )
        data_p = build_training_data_pure(cfg.training_text, enc_p, cfg.context_len)

        pure_times = []
        for epoch in range(1, cfg.timing_epochs + 1):
            t0   = time.time()
            loss, _, _ = train_epoch_pure(t_p, data_p, cfg.learning_rate, n_samples)
            dt   = time.time() - t0
            pure_times.append(dt)
            sps  = n_samples / max(dt, 1e-6)
            _print(f"  {'Pure':>10}  {epoch:6d}  {dt:8.3f}s  {loss:8.4f}  {sps:10.1f}")

        # ── TF benchmark ──────────────────────────────────────────────────
        random.seed(42)
        enc_tf  = CharacterEncoderTF(cfg.training_text)
        t_tf    = SMNNIPTowerTF(
            vocab_size=enc_tf.vocab_size,
            hidden_dim=cfg.hidden_dim,
            context_len=cfg.context_len
        )
        data_tf = build_training_data(cfg.training_text, enc_tf, cfg.context_len)

        tf_times = []
        for epoch in range(1, cfg.timing_epochs + 1):
            t0   = time.time()
            loss, _, _ = train_epoch(t_tf, data_tf, cfg.learning_rate, n_samples)
            dt   = time.time() - t0
            tf_times.append(dt)
            sps  = n_samples / max(dt, 1e-6)
            _print(f"  {'TF':>10}  {epoch:6d}  {dt:8.3f}s  {loss:8.4f}  {sps:10.1f}")

        # ── Summary ──────────────────────────────────────────────────────
        avg_pure = sum(pure_times) / len(pure_times)
        avg_tf   = sum(tf_times)   / len(tf_times)
        speedup  = avg_pure / max(avg_tf, 1e-9)
        _print(f"\n  Avg pure: {avg_pure:.3f}s/epoch  |  "
               f"Avg TF: {avg_tf:.3f}s/epoch  |  "
               f"Speedup: {speedup:.2f}x ({'TF faster' if speedup > 1 else 'Pure faster'})")
        _print(f"  Note: TF overhead dominates at small batch sizes.")
        _print(f"        Speedup increases with larger models and batch sizes.")


def run_boundary_probe(cfg: ResearcherConfig) -> None:
    """MODE: boundary_probe — TF engine version."""
    _header("BOUNDARY PROBE (TF ENGINE) — Finding the algebra boundary")

    if not TF_AVAILABLE:
        _print(f"TF engine unavailable: {_TF_IMPORT_ERROR}")
        return

    encoder = CharacterEncoderTF(cfg.training_text)
    tower   = SMNNIPTowerTF(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    _print(f"Probe start: {cfg.probe_start}  step: {cfg.probe_step}")
    _print(f"{'Step':>5}  {'Scale':>8}  {'Loss':>10}  {'Noether':>10}  Signal")
    _print("─" * 55)

    baseline_loss  = None
    boundary_found = False

    for step in range(cfg.probe_max_steps):
        scale      = cfg.probe_start + step * cfg.probe_step
        scaled_ctx = [[x * scale for x in v] for v in sample_ctx]

        try:
            loss, violation, probs = tower.train_step(scaled_ctx, sample_tgt, lr=0.001)

            if baseline_loss is None:
                baseline_loss = loss

            signals = []
            if loss > cfg.probe_loss_spike:
                signals.append(f"LOSS_SPIKE({loss:.1f})")
            if violation > cfg.probe_noether_spike:
                signals.append(f"NOETHER({violation:.3f})")
            if any(math.isnan(p) or math.isinf(p) for p in probs):
                signals.append("NAN_PROBS")
            if math.isnan(loss) or math.isinf(loss):
                signals.append("NAN_LOSS")

            signal_str = ", ".join(signals) if signals else "—"
            _print(f"  {step:4d}  {scale:8.3f}  {loss:10.4f}  {violation:10.6f}  {signal_str}")

            if signals and not boundary_found:
                boundary_found = True
                _print(f"\n  *** BOUNDARY at scale={scale:.3f}: {signal_str} ***")
                break

        except Exception as e:
            _print(f"  {step:4d}  {scale:8.3f}  EXCEPTION: {type(e).__name__}: {e}")
            boundary_found = True
            break

    if not boundary_found:
        _print(f"\n  No boundary found within {cfg.probe_max_steps} steps.")


def run_symmetry_violation(cfg: ResearcherConfig) -> None:
    """MODE: symmetry_violation — TF engine version."""
    _header("SYMMETRY VIOLATION (TF ENGINE)")

    if not TF_AVAILABLE:
        _print(f"TF engine unavailable: {_TF_IMPORT_ERROR}")
        return

    import tensorflow as tf

    encoder = CharacterEncoderTF(cfg.training_text)
    tower   = SMNNIPTowerTF(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    data = build_training_data(cfg.training_text, encoder, cfg.context_len)

    # Brief clean training
    _print("Training 3 clean epochs for baseline...")
    for _ in range(3):
        train_epoch(tower, data, cfg.learning_rate, cfg.max_samples)

    baseline_violations = [l.noether.violation() for l in tower.layers_tf]
    _print(f"Baseline violations: {[f'{v:.6f}' for v in baseline_violations]}")

    # Inject violation into target layer's W
    target_layer = tower.layers_tf[cfg.violation_layer]
    _print(f"\nInjecting phase {cfg.violation_phase:.3f} rad into "
           f"layer {cfg.violation_layer} ({target_layer.algebra})...")

    cos_p = math.cos(cfg.violation_phase)
    sin_p = math.sin(cfg.violation_phase)

    # TF: modify W in-place
    W_np = target_layer.kinetic.W.numpy()
    for i in range(W_np.shape[0]):
        for j in range(W_np.shape[1]):
            w_perp = random.gauss(0, abs(W_np[i, j]) + 0.01)
            W_np[i, j] = W_np[i, j] * cos_p + w_perp * sin_p
    target_layer.kinetic.W.assign(tf.constant(W_np, dtype=tf.float32))

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    _print(f"\n{'Step':>5}  {'Loss':>10}  {'MaxNoether':>12}  Detected")
    _print("─" * 45)

    for step in range(10):
        loss, _, _ = tower.train_step(sample_ctx, sample_tgt, cfg.learning_rate)
        violations = [l.noether.violation() for l in tower.layers_tf]
        max_v      = max(violations)
        detected   = any(v > b * 1.5 for v, b in zip(violations, baseline_violations))
        _print(f"  {step:4d}  {loss:10.4f}  {max_v:12.6f}  "
               f"{'✓ DETECTED' if detected else '— not yet'}")


def run_noether_stress(cfg: ResearcherConfig) -> None:
    """MODE: noether_stress — TF engine version."""
    _header("NOETHER STRESS (TF ENGINE)")

    if not TF_AVAILABLE:
        _print(f"TF engine unavailable: {_TF_IMPORT_ERROR}")
        return

    import tensorflow as tf

    encoder = CharacterEncoderTF(cfg.training_text)
    tower   = SMNNIPTowerTF(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    _print(f"Perturbation magnitude: {cfg.stress_perturbation}  Steps: {cfg.stress_steps}")
    _print(f"{'Step':>5}  {'Perturb':>10}  {'Loss':>10}  {'MaxNoether':>12}  Status")
    _print("─" * 55)

    for step in range(cfg.stress_steps):
        scale = cfg.stress_perturbation * (1.0 + step * 0.1)

        # Perturb W fields
        for layer in tower.layers_tf:
            W_np  = layer.kinetic.W.numpy()
            noise = tf.random.normal(W_np.shape, stddev=scale * 0.1).numpy()
            layer.kinetic.W.assign(tf.constant(W_np + noise, dtype=tf.float32))

        loss, violation, _ = tower.train_step(sample_ctx, sample_tgt, lr=0.0)
        violations         = [l.noether.violation() for l in tower.layers_tf]
        max_v              = max(violations)
        n_broken           = sum(1 for l in tower.layers_tf if not l.noether.is_conserved())
        status             = f"✓ all ok" if n_broken == 0 else f"✗ {n_broken}/4 broken"

        _print(f"  {step:4d}  {scale:10.4f}  {loss:10.4f}  {max_v:12.6f}  {status}")


def run_algebra_overflow(cfg: ResearcherConfig) -> None:
    """MODE: algebra_overflow — TF engine version."""
    _header("ALGEBRA OVERFLOW (TF ENGINE) — Probing Omega thermal boundary")

    if not TF_AVAILABLE:
        _print(f"TF engine unavailable: {_TF_IMPORT_ERROR}")
        return

    encoder = CharacterEncoderTF(cfg.training_text)
    tower   = SMNNIPTowerTF(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    OMEGA = PhysicalConstants.OMEGA
    ALPHA = PhysicalConstants.ALPHA

    _print(f"Observer domain: [{ALPHA:.8f}, {OMEGA:.8f}]")
    _print(f"{'Step':>5}  {'Scale':>8}  {'Loss':>10}  {'α_NN(R)':>10}  Overflow")
    _print("─" * 50)

    for step in range(cfg.overflow_max_steps):
        scale      = cfg.overflow_scale_start + step * cfg.overflow_scale_step
        scaled_ctx = [[x * scale for x in v] for v in sample_ctx]

        try:
            loss, violation, _ = tower.train_step(scaled_ctx, sample_tgt, lr=0.0)

            layer_alphas = []
            for l in tower.layers_tf:
                r = float(l.kinetic.field_strength().numpy())
                if r > 1.0:
                    log_r = math.log(r)
                    a_run = (l.g_val ** 2) / (4.0 * math.pi * l.hbar_val * log_r)
                else:
                    a_run = l.alpha
                layer_alphas.append(a_run)

            overflow = any(a > OMEGA for a in layer_alphas)
            _print(f"  {step:4d}  {scale:8.3f}  {loss:10.4f}  {layer_alphas[0]:10.6f}  "
                   f"{'OVERFLOW ***' if overflow else '—'}")

            if overflow:
                _print(f"\n  *** OMEGA BOUNDARY BREACHED at scale={scale:.3f} ***")
                break

        except Exception as e:
            _print(f"  {step:4d}  {scale:8.3f}  EXCEPTION: {type(e).__name__}: {e}")
            break


# ==============================================================================
# UTILITIES
# ==============================================================================

def _header(title: str) -> None:
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()

def _print(msg: str = "") -> None:
    print(f"  {msg}" if msg else "")


# ==============================================================================
# MAIN DISPATCH
# ==============================================================================

def main() -> None:
    if not TF_AVAILABLE:
        print(f"\nERROR: TensorFlow not available: {_TF_IMPORT_ERROR}")
        print("Install: pip install tensorflow")
        print("For pure Python testing, use smnnip_test_pure.py")
        return

    cfg = ResearcherConfig()

    print()
    print("=" * 70)
    print("  SMNNIP TENSORFLOW — TEST AND DIAGNOSTIC HARNESS")
    print(f"  BREAK_MODE: {BREAK_MODE!r}")
    print("=" * 70)

    valid_modes = {
        "none":               run_clean,
        "boundary_probe":     run_boundary_probe,
        "symmetry_violation": run_symmetry_violation,
        "noether_stress":     run_noether_stress,
        "algebra_overflow":   run_algebra_overflow,
        "timing_comparison":  run_timing_comparison,
    }

    if BREAK_MODE not in valid_modes:
        print(f"\n  ERROR: Unknown BREAK_MODE {BREAK_MODE!r}")
        print(f"  Valid modes: {list(valid_modes.keys())}")
        return

    t0 = time.time()
    valid_modes[BREAK_MODE](cfg)
    dt = time.time() - t0

    print()
    print("=" * 70)
    print(f"  Run complete. Elapsed: {dt:.2f}s")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
