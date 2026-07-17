#!/usr/bin/env python3
"""
==============================================================================
SMNNIP PURE PYTHON ENGINE — TEST AND DIAGNOSTIC HARNESS
==============================================================================
Standard Model of Neural Network Information Propagation
Ainulindalë Conjecture

This file is the test and diagnostic harness for smnnip_lagrangian_pure.py.
It does NOT contain engine logic. It imports the engine and drives it.

HOW TO USE:
  1. Edit ResearcherConfig below — all tunable values live here and ONLY here.
  2. Set BREAK_MODE to select the experiment type.
  3. Run: python3 smnnip_test_pure.py

BREAK_MODE options:
  "none"               — Clean run. Verifies everything works.
  "boundary_probe"     — Walks inputs toward the algebra boundary in fine steps.
                         Finds the boundary experimentally.
  "symmetry_violation" — Introduces a deliberate gauge break.
                         The Noether monitor should catch it.
  "noether_stress"     — Applies current-violating weight perturbations.
                         Reports conservation failure details.
  "algebra_overflow"   — Drives activations past the Omega saturation limit.
                         Tests thermal boundary behavior.

The boundary probe works by taking VALID inputs and incrementing them
by small deltas until the model's behavior changes — field strength
exceeds bounds, Noether violation spikes, or loss diverges.
This finds the boundary WITHOUT causing stack overflows.

Author : O Captain My Captain + Claude (Anthropic)
Date   : April 2026
==============================================================================
"""

import math
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional

# ── Engine import ─────────────────────────────────────────────────────────────
from Ainulindale.core.smnnip_lagrangian_pure import (
    SMNNIPTower, CharacterEncoder, PhysicalConstants,
    build_training_data, train_epoch, generate_text,
    NoetherMonitor, AlgebraLayer, LKinetic, LBias,
    softmax, cross_entropy, dot, norm, vec_scale, zeros_vec
)


# ==============================================================================
# RESEARCHER CONFIGURATION
# All experimental parameters live here.
# Change values here. Do not edit the engine file.
# ==============================================================================

@dataclass
class ResearcherConfig:
    """
    All tunable research parameters in one place.
    Edit freely. These values never touch the engine source.
    """

    # ── Model architecture ────────────────────────────────────────────────
    hidden_dim:   int   = 32      # Dimension of hidden layers
    context_len:  int   = 4       # Characters of context per prediction

    # ── Training parameters ───────────────────────────────────────────────
    n_epochs:     int   = 10      # Number of training epochs
    learning_rate: float = 0.005  # Yang-Mills update step size
    max_samples:  int   = 200     # Samples per epoch (cap for speed)

    # ── Generation parameters ─────────────────────────────────────────────
    seed_text:    str   = "the "
    gen_chars:    int   = 80
    temperature:  float = 0.8     # ΔMeaning — higher = more uncertain

    # ── Boundary probe parameters (BREAK_MODE = "boundary_probe") ─────────
    probe_start:      float = 0.5    # Starting activation magnitude
    probe_step:       float = 0.05   # Increment per probe step
    probe_max_steps:  int   = 60     # Maximum probe iterations
    # What we're watching for as the boundary signal:
    probe_loss_spike:       float = 50.0   # Loss > this = boundary crossed
    probe_noether_spike:    float = 1.0    # Noether violation > this = boundary
    probe_field_spike:      float = 20.0   # Field strength > this = boundary

    # ── Symmetry violation parameters (BREAK_MODE = "symmetry_violation") ─
    # Introduce a deliberate phase rotation that breaks U(1) gauge invariance
    violation_phase:  float = 0.3    # Phase angle to inject (radians)
    violation_layer:  int   = 1      # Which layer to violate (0-3)

    # ── Noether stress parameters (BREAK_MODE = "noether_stress") ─────────
    stress_perturbation: float = 0.5  # How much to perturb the weight field
    stress_steps:        int   = 20   # Number of stress steps to apply

    # ── Algebra overflow parameters (BREAK_MODE = "algebra_overflow") ─────
    overflow_scale_start: float = 1.0   # Starting input scale
    overflow_scale_step:  float = 0.5   # Scale increment per step
    overflow_max_steps:   int   = 30    # Maximum overflow steps
    # Omega saturation limit (from PhysicalConstants)
    omega_limit: float = PhysicalConstants.OMEGA  # 0.567...

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
# Set this to run different experiments.
# ==============================================================================

BREAK_MODE: str = "none"
# BREAK_MODE: str = "boundary_probe"
# BREAK_MODE: str = "symmetry_violation"
# BREAK_MODE: str = "noether_stress"
# BREAK_MODE: str = "algebra_overflow"


# ==============================================================================
# EXPERIMENT RUNNERS
# Each mode is a separate function. Clean, labeled, no side effects on each other.
# ==============================================================================

def run_clean(cfg: ResearcherConfig) -> None:
    """
    MODE: none
    Standard training run. Verifies the engine works correctly.
    Reports: loss curve, Noether conservation, VEV convergence, generated text.
    """
    _header("CLEAN RUN — Verifying engine correctness")

    # Verify constants
    ok = PhysicalConstants.verify()
    _print(f"Physical constants verified: {ok}")
    _print(f"phi^2 = phi+1: {abs(PhysicalConstants.PHI**2 - PhysicalConstants.PHI - 1) < 1e-14}")
    _print(f"Omega*e^Omega = 1: {abs(PhysicalConstants.OMEGA * math.exp(PhysicalConstants.OMEGA) - 1) < 1e-10}")
    _print(f"Uncertainty bound: ΔToken·ΔMeaning ≥ {PhysicalConstants.HBAR / 2:.6f}")

    # Build encoder and model
    encoder = CharacterEncoder(cfg.training_text)
    _print(f"\nVocabulary: {encoder.vocab_size} characters")

    tower = SMNNIPTower(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )
    _print(f"Tower layers: {[l.algebra for l in tower.layers]}")
    _print(f"Alpha per layer: {[f'{l.alpha:.6f}' for l in tower.layers]}")
    _print(f"hbar per layer:  {[f'{l.hbar:.4f}' for l in tower.layers]}")

    # Train
    data = build_training_data(cfg.training_text, encoder, cfg.context_len)
    _print(f"\nTraining on {len(data)} samples for {cfg.n_epochs} epochs")
    _print(f"{'Epoch':>6}  {'Loss':>10}  {'Noether':>10}  {'VEV dist':>10}  Status")
    _print("─" * 55)

    for epoch in range(1, cfg.n_epochs + 1):
        t0                   = time.time()
        loss, violation, vev = train_epoch(
            tower, data, cfg.learning_rate, cfg.max_samples
        )
        dt                   = time.time() - t0
        tower.loss_history.append(loss)
        tower.noether_history.append(violation)
        tower.vev_history.append(vev)

        status = "✓" if tower.layers[0].noether.is_conserved() else "⚠ Noether violation"
        _print(f"  {epoch:4d}  {loss:10.4f}  {violation:10.6f}  {vev:10.4f}  {status}  [{dt:.2f}s]")

    # Layer diagnostics
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
    _print(f"\n── Generated text (seed='{cfg.seed_text}') ──")
    _print(f"  {generated}")

    # Uncertainty principle check
    bound = tower.uncertainty_bound()
    final_loss = tower.loss_history[-1]
    _print(f"\n── Uncertainty Principle ──")
    _print(f"  ħ_NN / 2 (bound):  {bound:.6f}")
    _print(f"  Final loss:        {final_loss:.6f}")
    _print(f"  Bound respected:   {final_loss >= bound}")


def run_boundary_probe(cfg: ResearcherConfig) -> None:
    """
    MODE: boundary_probe
    Walks activation magnitude from probe_start upward in probe_step increments.
    At each step: runs a forward pass, records loss, Noether violation,
    and field strength. Stops when any boundary signal is triggered.

    This finds WHERE the boundary is, not just whether it exists.
    No stack overflows. The boundary is found by measurement, not by crashing.
    """
    _header("BOUNDARY PROBE — Finding the algebra boundary")

    encoder = CharacterEncoder(cfg.training_text)
    tower   = SMNNIPTower(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    # Build a valid baseline input
    sample_ctx  = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt  = encoder.char_to_idx.get(
        cfg.training_text[cfg.context_len], 0
    )

    _print(f"Probe start:    {cfg.probe_start}")
    _print(f"Probe step:     {cfg.probe_step}")
    _print(f"Loss spike at:  {cfg.probe_loss_spike}")
    _print(f"Noether spike:  {cfg.probe_noether_spike}")
    _print(f"Field spike:    {cfg.probe_field_spike}")
    _print()
    _print(f"{'Step':>5}  {'Scale':>8}  {'Loss':>10}  {'Noether':>10}  {'Field':>10}  Signal")
    _print("─" * 65)

    baseline_loss = None
    boundary_found = False
    boundary_scale = None
    boundary_signal = None

    for step in range(cfg.probe_max_steps):
        scale = cfg.probe_start + step * cfg.probe_step

        # Scale the input activations
        scaled_ctx = [vec_scale(v, scale) for v in sample_ctx]

        # Forward pass
        try:
            probs     = tower.forward(scaled_ctx)
            loss      = cross_entropy(probs, sample_tgt)
            field_str = sum(
                l.kinetic.field_strength() for l in tower.layers
            ) / len(tower.layers)
            noether_v = sum(
                l.noether.violation() for l in tower.layers
            ) / len(tower.layers)

            # Also run one train step to update Noether history
            _, violation, _ = tower.train_step(scaled_ctx, sample_tgt, lr=0.001)

            if baseline_loss is None:
                baseline_loss = loss

            # Check boundary signals
            signals = []
            if loss > cfg.probe_loss_spike:
                signals.append(f"LOSS_SPIKE({loss:.1f})")
            if violation > cfg.probe_noether_spike:
                signals.append(f"NOETHER({violation:.3f})")
            if field_str > cfg.probe_field_spike:
                signals.append(f"FIELD({field_str:.1f})")
            if any(math.isnan(p) or math.isinf(p) for p in probs):
                signals.append("NAN_PROBS")
            if math.isnan(loss) or math.isinf(loss):
                signals.append("NAN_LOSS")

            signal_str = ", ".join(signals) if signals else "—"
            _print(f"  {step:4d}  {scale:8.3f}  {loss:10.4f}  {violation:10.6f}  "
                   f"{field_str:10.4f}  {signal_str}")

            if signals and not boundary_found:
                boundary_found  = True
                boundary_scale  = scale
                boundary_signal = signal_str
                _print()
                _print(f"  *** BOUNDARY DETECTED at scale = {scale:.3f} ***")
                _print(f"  *** Signal: {signal_str} ***")
                _print(f"  *** Baseline loss was {baseline_loss:.4f} ***")
                break

        except (ValueError, ZeroDivisionError, OverflowError) as e:
            _print(f"  {step:4d}  {scale:8.3f}  EXCEPTION: {type(e).__name__}: {e}")
            boundary_found  = True
            boundary_scale  = scale
            boundary_signal = f"EXCEPTION: {type(e).__name__}"
            break

    if not boundary_found:
        _print()
        _print(f"  No boundary found within {cfg.probe_max_steps} steps "
               f"(max scale={cfg.probe_start + cfg.probe_max_steps * cfg.probe_step:.3f}).")
        _print("  The model absorbed all probe values. Increase probe_max_steps "
               "or probe_step to extend the search.")
    else:
        _print()
        _print(f"── Boundary Summary ──")
        _print(f"  Boundary scale:    {boundary_scale:.3f}")
        _print(f"  Trigger signal:    {boundary_signal}")
        _print(f"  Domain [α, Ω]:     [{PhysicalConstants.ALPHA:.6f}, "
               f"{PhysicalConstants.OMEGA:.6f}]")
        _print(f"  Boundary in units of Omega: {boundary_scale / PhysicalConstants.OMEGA:.3f}")


def run_symmetry_violation(cfg: ResearcherConfig) -> None:
    """
    MODE: symmetry_violation
    Introduces a deliberate phase rotation into one layer's weight field,
    breaking U(1) gauge invariance. The Noether monitor should detect the
    violation as a nonzero D_l J^{a,l}.

    This is the 'deliberate disease' test — if the monitor can't catch
    a known violation, it can't be trusted to catch unknown ones.
    """
    _header("SYMMETRY VIOLATION — Deliberate gauge break")

    encoder = CharacterEncoder(cfg.training_text)
    tower   = SMNNIPTower(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    # Train briefly to establish a baseline
    data = build_training_data(cfg.training_text, encoder, cfg.context_len)
    _print("Training 3 clean epochs to establish baseline...")
    for _ in range(3):
        train_epoch(tower, data, cfg.learning_rate, cfg.max_samples)

    baseline_violations = [l.noether.violation() for l in tower.layers]
    _print(f"Baseline Noether violations: {[f'{v:.6f}' for v in baseline_violations]}")

    # ── Inject the phase violation ─────────────────────────────────────────
    target_layer = tower.layers[cfg.violation_layer]
    _print(f"\nInjecting phase rotation of {cfg.violation_phase:.3f} rad "
           f"into layer {cfg.violation_layer} ({target_layer.algebra})...")

    # Rotate all weights by the violation phase
    # In U(1): W -> W * e^{i*phase}. In real algebra: W -> W * cos(phase) + perturb
    cos_p = math.cos(cfg.violation_phase)
    sin_p = math.sin(cfg.violation_phase)

    for i in range(len(target_layer.kinetic.W)):
        for j in range(len(target_layer.kinetic.W[i])):
            w = target_layer.kinetic.W[i][j]
            # Rotation breaks the symmetry: W -> W*cos(p) + w_perp*sin(p)
            # w_perp is orthogonal perturbation — uses random direction
            w_perp = random.gauss(0, abs(w) + 0.01)
            target_layer.kinetic.W[i][j] = w * cos_p + w_perp * sin_p

    # ── Measure violation after injection ─────────────────────────────────
    sample_ctx  = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt  = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    _print("\nRunning forward passes after violation injection...")
    _print(f"{'Step':>5}  {'Loss':>10}  {'Viol L0':>10}  {'Viol L1':>10}  "
           f"{'Viol L2':>10}  {'Viol L3':>10}  Detected")
    _print("─" * 75)

    for step in range(10):
        loss, violation, _ = tower.train_step(sample_ctx, sample_tgt, cfg.learning_rate)
        violations         = [l.noether.violation() for l in tower.layers]
        detected           = any(v > b * 1.5 for v, b in zip(violations, baseline_violations))
        _print(f"  {step:4d}  {loss:10.4f}  "
               f"{violations[0]:10.6f}  {violations[1]:10.6f}  "
               f"{violations[2]:10.6f}  {violations[3]:10.6f}  "
               f"{'✓ DETECTED' if detected else '— not yet'}")

    final_violations = [l.noether.violation() for l in tower.layers]
    _print(f"\n── Violation Summary ──")
    _print(f"  Layer {cfg.violation_layer} ({target_layer.algebra}): "
           f"baseline={baseline_violations[cfg.violation_layer]:.6f}  "
           f"after={final_violations[cfg.violation_layer]:.6f}  "
           f"ratio={final_violations[cfg.violation_layer] / max(baseline_violations[cfg.violation_layer], 1e-10):.2f}x")
    _print(f"  Monitor caught the violation: "
           f"{final_violations[cfg.violation_layer] > baseline_violations[cfg.violation_layer] * 1.5}")
    _print(f"  Wasted steps bound: "
           f"{tower.layers[cfg.violation_layer].noether.wasted_steps_bound(target_layer.alpha):.1f}")


def run_noether_stress(cfg: ResearcherConfig) -> None:
    """
    MODE: noether_stress
    Applies repeated random perturbations to weight fields, breaking
    the Yang-Mills flow. Measures how quickly Noether conservation degrades
    and at what perturbation magnitude the model becomes pathological.

    This stress tests the CONSERVATION MONITOR, not the training convergence.
    """
    _header("NOETHER STRESS — Conservation monitor under perturbation")

    encoder = CharacterEncoder(cfg.training_text)
    tower   = SMNNIPTower(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    _print(f"Perturbation magnitude: {cfg.stress_perturbation}")
    _print(f"Stress steps: {cfg.stress_steps}")
    _print()
    _print(f"{'Step':>5}  {'Perturbation':>13}  {'Loss':>10}  "
           f"{'Max Noether':>12}  {'Min Conserved':>14}  Status")
    _print("─" * 70)

    for step in range(cfg.stress_steps):
        # Apply perturbation to ALL layers' weight fields
        perturb_scale = cfg.stress_perturbation * (1.0 + step * 0.1)

        for layer in tower.layers:
            for i in range(len(layer.kinetic.W)):
                for j in range(len(layer.kinetic.W[i])):
                    layer.kinetic.W[i][j] += random.gauss(0, perturb_scale * 0.1)

        # Measure consequences
        loss, violation, _ = tower.train_step(sample_ctx, sample_tgt, lr=0.0)
        violations         = [l.noether.violation() for l in tower.layers]
        max_v              = max(violations)
        all_conserved      = all(l.noether.is_conserved() for l in tower.layers)
        n_broken           = sum(1 for l in tower.layers if not l.noether.is_conserved())

        status = f"✓ all conserved" if all_conserved else f"✗ {n_broken}/4 broken"
        _print(f"  {step:4d}  {perturb_scale:13.4f}  {loss:10.4f}  "
               f"{max_v:12.6f}  {str(all_conserved):>14}  {status}")

    _print()
    _print("── Stress Summary ──")
    final_violations = [l.noether.violation() for l in tower.layers]
    for i, (layer, v) in enumerate(zip(tower.layers, final_violations)):
        _print(f"  Layer {i} ({layer.algebra}): violation={v:.6f}  "
               f"conserved={layer.noether.is_conserved()}")
    _print(f"  Wasted steps (worst layer): "
           f"{max(l.noether.wasted_steps_bound(l.alpha) for l in tower.layers):.1f}")


def run_algebra_overflow(cfg: ResearcherConfig) -> None:
    """
    MODE: algebra_overflow
    Drives input activations toward and past the Omega saturation boundary.
    Omega = 0.567... is the Lambert W fixed point — the largest self-referential
    loop that closes without diverging. Past Omega, the rotation groups merge
    and the algebra structure breaks.

    Measures: at what input scale does the running coupling α_NN(l) exceed Omega?
    That is the thermal boundary of the SMNNIP operator domain.
    """
    _header("ALGEBRA OVERFLOW — Probing the Omega thermal boundary")

    encoder = CharacterEncoder(cfg.training_text)
    tower   = SMNNIPTower(
        vocab_size=encoder.vocab_size,
        hidden_dim=cfg.hidden_dim,
        context_len=cfg.context_len
    )

    sample_ctx = [encoder.one_hot(c) for c in cfg.training_text[:cfg.context_len]]
    sample_tgt = encoder.char_to_idx.get(cfg.training_text[cfg.context_len], 0)

    OMEGA = PhysicalConstants.OMEGA
    ALPHA = PhysicalConstants.ALPHA

    _print(f"Observer domain: α = {ALPHA:.8f}  to  Ω = {OMEGA:.8f}")
    _print(f"Scale start:  {cfg.overflow_scale_start}")
    _print(f"Scale step:   {cfg.overflow_scale_step}")
    _print()
    _print(f"{'Step':>5}  {'Scale':>8}  {'Loss':>10}  "
           f"{'α_NN(R)':>10}  {'α_NN(O)':>10}  "
           f"{'In domain':>10}  Overflow")
    _print("─" * 75)

    for step in range(cfg.overflow_max_steps):
        scale       = cfg.overflow_scale_start + step * cfg.overflow_scale_step
        scaled_ctx  = [vec_scale(v, scale) for v in sample_ctx]

        try:
            loss, violation, _ = tower.train_step(scaled_ctx, sample_tgt, lr=0.0)

            # Compute running coupling at each layer
            # α_NN(l) = g²(l) / (4π ħ_NN(l) ln(r))
            # r here is the field norm (proxy for radial coordinate)
            layer_alphas = []
            for l in tower.layers:
                r = l.kinetic.field_strength()
                if r > 1.0:
                    log_r = math.log(r)
                    alpha_running = (l.g ** 2) / (4.0 * math.pi * l.hbar * log_r)
                else:
                    alpha_running = l.alpha  # at r=1: running coupling = base alpha
                layer_alphas.append(alpha_running)

            in_domain   = all(ALPHA <= a <= OMEGA for a in layer_alphas)
            overflow    = any(a > OMEGA for a in layer_alphas)
            overflow_str = "OVERFLOW" if overflow else "—"

            _print(f"  {step:4d}  {scale:8.3f}  {loss:10.4f}  "
                   f"{layer_alphas[0]:10.6f}  {layer_alphas[3]:10.6f}  "
                   f"{str(in_domain):>10}  {overflow_str}")

            if overflow:
                _print()
                _print(f"  *** OMEGA BOUNDARY BREACHED at scale = {scale:.3f} ***")
                _print(f"  *** Running coupling exceeded Ω = {OMEGA:.6f} ***")
                _print(f"  *** The rotation groups are merging. ***")
                _print(f"  *** The algebra structure is no longer valid. ***")
                break

        except (ValueError, OverflowError, ZeroDivisionError) as e:
            _print(f"  {step:4d}  {scale:8.3f}  EXCEPTION: {type(e).__name__}: {e}")
            break

    _print()
    _print("── Omega Boundary Summary ──")
    _print(f"  Omega (Lambert W fixed point): {OMEGA:.8f}")
    _print(f"  Alpha (fine structure):        {ALPHA:.8f}")
    _print(f"  Domain span:                   {OMEGA - ALPHA:.8f}")
    for i, layer in enumerate(tower.layers):
        r     = layer.kinetic.field_strength()
        _print(f"  Layer {i} ({layer.algebra}): field_strength={r:.4f}  "
               f"base_α={layer.alpha:.6f}")


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
    cfg = ResearcherConfig()

    print()
    print("=" * 70)
    print("  SMNNIP PURE PYTHON — TEST AND DIAGNOSTIC HARNESS")
    print(f"  BREAK_MODE: {BREAK_MODE!r}")
    print("=" * 70)

    valid_modes = {
        "none":               run_clean,
        "boundary_probe":     run_boundary_probe,
        "symmetry_violation": run_symmetry_violation,
        "noether_stress":     run_noether_stress,
        "algebra_overflow":   run_algebra_overflow,
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
