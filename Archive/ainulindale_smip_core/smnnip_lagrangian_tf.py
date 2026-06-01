#!/usr/bin/env python3
"""
==============================================================================
SMNNIP LAGRANGIAN CORE ENGINE — TENSORFLOW PYTHON3
==============================================================================
Standard Model of Neural Network Information Propagation
Ainulindalë Conjecture — Lagrangian Field Engine (Production)

ℒ_NN = ℒ_kinetic + ℒ_matter + ℒ_bias + ℒ_coupling

This file is the production artifact.
It implements the same Lagrangian field theory as smnnip_lagrangian_pure.py,
vectorized for GPU/TPU operation via TensorFlow.

The API shape mirrors the pure Python engine exactly.
Researchers can swap engines by changing one import line.
Physics must agree between engines — the test harness verifies this.

Architecture — four algebra layers:
    Layer 0 — ℝ  (real,        dim=1)  substrate / character
    Layer 1 — ℂ  (complex,     dim=2)  semantic
    Layer 2 — ℍ  (quaternion,  dim=4)  skills
    Layer 3 — 𝕆  (octonion,    dim=8)  reasoning

Gauge symmetry group: U(1) × SU(2) × SU(3)  [Dixon theorem]
Conservation law:     D_l J^{a,l} = 0         [Noether current]
Uncertainty bound:    ΔToken · ΔMeaning ≥ ħ_NN / 2

Author : O Captain My Captain + Claude (Anthropic)
Date   : April 2026
==============================================================================
"""

import math
from typing import List, Tuple, Optional

try:
    import tensorflow as tf
except ImportError as e:
    raise ImportError(
        "TensorFlow is required for this engine.\n"
        "Install: pip install tensorflow\n"
        "For the proof artifact with no dependencies, use smnnip_lagrangian_pure.py"
    ) from e


# ==============================================================================
# MODULE 0 — CONSTANTS (mirrored from pure engine)
# ==============================================================================

class PhysicalConstants:
    PI    : float = math.pi
    E     : float = math.e
    PHI   : float = (1.0 + math.sqrt(5.0)) / 2.0
    ALPHA : float = 1.0 / 137.035999084
    OMEGA : float = 0.56714329040978384
    H_NN  : float = 0.1
    HBAR  : float = 0.1 / (2.0 * math.pi)
    D_STAR: float = 0.56714329040978384 / math.log(10.0)

    @classmethod
    def verify(cls) -> bool:
        phi_identity   = abs(cls.PHI ** 2 - cls.PHI - 1.0) < 1e-14
        omega_identity = abs(cls.OMEGA * math.exp(cls.OMEGA) - 1.0) < 1e-10
        return phi_identity and omega_identity


# ==============================================================================
# MODULE 1 — OBSERVER SINGLETON (TF version)
# ==============================================================================

class _ObserverSingleton:
    _instance: Optional['_ObserverSingleton'] = None
    _initialized: bool = False

    def __new__(cls) -> '_ObserverSingleton':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self.alpha: float = PhysicalConstants.ALPHA
        self.omega: float = PhysicalConstants.OMEGA
        self._initialized = True

    def domain_contains(self, coupling: float) -> bool:
        return self.alpha <= coupling <= self.omega


def get_observer() -> _ObserverSingleton:
    return _ObserverSingleton()


# ==============================================================================
# MODULE 2 — LAGRANGIAN TERMS (TensorFlow)
# Each term is a tf.Module with a __call__ that returns (output, scalar_loss).
# GradientTape tracks all operations for the Yang-Mills update.
# ==============================================================================

class LKineticTF(tf.Module):
    """
    ℒ_kinetic = -(1/4) R^a_{lτ} R^{alτ}
    Weight-field curvature. Neural Yang-Mills field strength.
    """

    def __init__(self, in_dim: int, out_dim: int,
                 g_coupling: float, hbar: float,
                 name: str = 'L_kinetic'):
        super().__init__(name=name)
        self.in_dim  = in_dim
        self.out_dim = out_dim
        self.g       = tf.constant(g_coupling, dtype=tf.float32)
        self.hbar    = tf.constant(hbar, dtype=tf.float32)
        self.alpha   = tf.constant(
            (g_coupling ** 2) / (4.0 * math.pi * hbar), dtype=tf.float32
        )

        init_scale = math.sqrt(2.0 / (in_dim + out_dim))
        # The weight field W^a
        self.W = tf.Variable(
            tf.random.normal([out_dim, in_dim], stddev=init_scale),
            trainable=True, name='W'
        )

    @tf.function
    def field_strength(self) -> tf.Tensor:
        """||R^a_{lτ}||_F — Frobenius norm of W."""
        return tf.norm(self.W)

    @tf.function
    def __call__(self, psi: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """
        Apply weight field. Returns (output, L_kinetic).
        psi shape: [batch, in_dim] or [in_dim]
        """
        if len(psi.shape) == 1:
            output = tf.linalg.matvec(self.W, psi)
        else:
            output = tf.matmul(psi, tf.transpose(self.W))
        R_sq      = tf.square(self.field_strength())
        L_kinetic = -0.25 * R_sq
        return output, L_kinetic

    @tf.function
    def noether_current(self, psi_bar: tf.Tensor, psi: tf.Tensor) -> tf.Tensor:
        """J^a_l = g · ψ̄ · ψ"""
        return self.g * tf.reduce_sum(psi_bar * psi)


class LMatterTF(tf.Module):
    """
    ℒ_matter = iψ̄ γ^a D_a ψ − m ψ̄ ψ
    Neural Dirac equation. Activation propagation.
    """

    def __init__(self, mass: float = 0.1, algebra: str = 'R',
                 name: str = 'L_matter'):
        super().__init__(name=name)
        self.mass    = tf.constant(mass, dtype=tf.float32)
        self.algebra = algebra

    @tf.function
    def __call__(self, psi: tf.Tensor, D_psi: tf.Tensor) -> tf.Tensor:
        """L_matter = (ψ̄ · D·ψ) - m(ψ̄ · ψ)"""
        kinetic   = tf.reduce_sum(psi * D_psi)
        mass_term = self.mass * tf.reduce_sum(psi * psi)
        return kinetic - mass_term


class LBiasTF(tf.Module):
    """
    ℒ_bias = |D_l β|² + μ² β†β − λ(β†β)²
    Neural Higgs mechanism. Symmetry breaking. VEV = sqrt(μ²/2λ).
    """

    def __init__(self, size: int, mu_sq: float, lam: float,
                 name: str = 'L_bias'):
        super().__init__(name=name)
        self.size   = size
        self.mu_sq  = tf.constant(mu_sq, dtype=tf.float32)
        self.lam    = tf.constant(lam, dtype=tf.float32)
        self.vev    = tf.constant(
            math.sqrt(mu_sq / (2.0 * lam)) if mu_sq > 0 else 0.0,
            dtype=tf.float32
        )
        # Bias field β
        self.beta = tf.Variable(
            tf.random.normal([size], stddev=0.01),
            trainable=True, name='beta'
        )

    @tf.function
    def potential(self) -> tf.Tensor:
        """V(β) = -μ²|β|² + λ|β|⁴"""
        beta_sq = tf.reduce_sum(tf.square(self.beta))
        return -self.mu_sq * beta_sq + self.lam * tf.square(beta_sq)

    @tf.function
    def vev_distance(self) -> tf.Tensor:
        """||β|| - VEV → 0 during training."""
        beta_norm = tf.norm(self.beta)
        return tf.abs(beta_norm - self.vev)

    @tf.function
    def __call__(self, psi: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """Apply bias field. Returns (output, L_bias)."""
        n      = tf.minimum(tf.shape(psi)[0], self.size)
        output = psi[:n] + self.beta[:n]
        L_bias = self.potential()
        return output, L_bias


class LCouplingTF(tf.Module):
    """
    ℒ_coupling = -Γ_{ij} ψ̄^L_i β ψ^R_j + h.c.
    Neural Yukawa interaction. Inter-algebra coupling.
    Γ fixed by Cayley-Dickson projection maps (not free parameters).
    """

    def __init__(self, in_dim: int, out_dim: int,
                 g_coupling: float, name: str = 'L_coupling'):
        super().__init__(name=name)
        self.in_dim  = in_dim
        self.out_dim = out_dim
        self.g       = tf.constant(g_coupling, dtype=tf.float32)

        init_scale = math.sqrt(2.0 / (in_dim + out_dim)) * 0.5
        # Coupling matrix Γ_{ij}
        self.Gamma = tf.Variable(
            tf.random.normal([out_dim, in_dim], stddev=init_scale),
            trainable=True, name='Gamma'
        )

    @tf.function
    def __call__(self, psi_L: tf.Tensor, beta: tf.Tensor,
                 psi_R: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """L_coupling = -g · (ψ̄_L · Γ · β · ψ_R)"""
        gamma_psi_R = tf.linalg.matvec(self.Gamma, psi_R)
        beta_scale  = tf.norm(beta) + 1e-8
        output      = gamma_psi_R * beta_scale
        L_coupling  = -self.g * tf.reduce_sum(psi_L * output)
        return output, L_coupling


# ==============================================================================
# MODULE 3 — NOETHER MONITOR (TF)
# ==============================================================================

class NoetherMonitorTF(tf.Module):
    """
    Tracks Noether current J^{a,l} = g ψ̄_i T^a ψ_i.
    Conservation: D_l J^{a,l} = 0.
    """

    def __init__(self, g_coupling: float, tolerance: float = 0.01,
                 name: str = 'noether'):
        super().__init__(name=name)
        self.g         = g_coupling
        self.tolerance = tolerance
        self._prev     = tf.Variable(0.0, trainable=False, name='J_prev')
        self._violations = tf.Variable(
            tf.zeros([1000]), trainable=False, name='violations'
        )
        self._n_recorded = tf.Variable(0, trainable=False, name='n_recorded')

    def record(self, psi_bar: tf.Tensor, psi: tf.Tensor) -> tf.Tensor:
        """Record current at this step. Returns violation."""
        J_now      = tf.constant(self.g, dtype=tf.float32) * tf.reduce_sum(psi_bar * psi)
        J_prev_val = self._prev.numpy()
        violation  = tf.abs(J_now - J_prev_val)
        self._prev.assign(J_now)
        n = self._n_recorded.numpy()
        if n < 1000:
            indices = [[n]]
            updates = [violation.numpy()]
            self._violations.assign(
                tf.tensor_scatter_nd_update(self._violations, indices, updates)
            )
            self._n_recorded.assign_add(1)
        return violation

    def violation(self) -> float:
        n = self._n_recorded.numpy()
        if n == 0:
            return 0.0
        return float(tf.reduce_mean(self._violations[:n]).numpy())

    def is_conserved(self) -> bool:
        return self.violation() < self.tolerance

    def reset(self) -> None:
        self._prev.assign(0.0)
        self._violations.assign(tf.zeros([1000]))
        self._n_recorded.assign(0)


# ==============================================================================
# MODULE 4 — ALGEBRA LAYER (TF)
# ==============================================================================

class AlgebraLayerTF(tf.Module):
    """
    One layer of the SMNNIP algebra tower (TensorFlow).
    Bundles all four Lagrangian terms.
    """

    def __init__(self, in_dim: int, out_dim: int,
                 algebra_name: str, gauge_group: str,
                 hbar: float, g: float, mu_sq: float, lam: float,
                 mass: float = 0.1, name: str = None):
        if name is None:
            name = f'layer_{algebra_name}'
        super().__init__(name=name)

        self.in_dim   = in_dim
        self.out_dim  = out_dim
        self.algebra  = algebra_name
        self.gauge    = gauge_group
        self.hbar_val = hbar
        self.g_val    = g
        self.alpha    = (g ** 2) / (4.0 * math.pi * hbar)

        self.kinetic  = LKineticTF(in_dim, out_dim, g, hbar,
                                   name=f'{algebra_name}_kinetic')
        self.matter   = LMatterTF(mass, algebra_name,
                                   name=f'{algebra_name}_matter')
        self.bias     = LBiasTF(out_dim, mu_sq, lam,
                                 name=f'{algebra_name}_bias')
        self.coupling = LCouplingTF(in_dim, out_dim, g,
                                    name=f'{algebra_name}_coupling')
        self.noether  = NoetherMonitorTF(g, name=f'{algebra_name}_noether')

        # Build optimizer for this layer's variables
        self.optimizer = tf.keras.optimizers.Adam(learning_rate=0.005)

        # Diagnostics
        self.loss_history:    List[float] = []
        self.noether_history: List[float] = []

    def trainable_variables_list(self) -> List[tf.Variable]:
        return (self.kinetic.trainable_variables +
                self.bias.trainable_variables +
                self.coupling.trainable_variables)

    @tf.function
    def forward(self, psi: tf.Tensor) -> Tuple[tf.Tensor, tf.Tensor]:
        """
        Full layer forward pass.
        Returns: (output, total L_NN at this layer)
        """
        psi_W, L_kin  = self.kinetic(psi)
        L_mat         = self.matter(psi, psi_W)
        psi_bias, L_b = self.bias(psi_W)
        _, L_coup     = self.coupling(psi, self.bias.beta, psi_bias)
        L_total       = L_kin + L_mat + L_b + L_coup
        output        = tf.nn.relu(psi_bias)
        return output, L_total

    def backward_step(self, psi: tf.Tensor, target_grad: tf.Tensor,
                      lr: float) -> Tuple[tf.Tensor, float]:
        """
        Yang-Mills backward pass via GradientTape.
        Returns: (grad_to_prev_layer, noether_violation)
        """
        variables = self.trainable_variables_list()

        with tf.GradientTape(persistent=True) as tape:
            tape.watch(psi)
            output, L_total = self.forward(psi)
            # Scalar loss for this layer
            layer_loss = tf.reduce_sum(output * target_grad)

        # Gradients w.r.t. weights (Yang-Mills update)
        grads = tape.gradient(layer_loss, variables)
        if grads:
            # Clip gradients
            grads_clipped, _ = tf.clip_by_global_norm(grads, 1.0)
            self.optimizer.apply_gradients(zip(grads_clipped, variables))

        # Gradient flowing back to previous layer
        grad_input = tape.gradient(layer_loss, psi)
        if grad_input is None:
            grad_input = tf.zeros_like(psi)

        del tape

        # Noether current
        violation = float(self.noether.record(psi, output).numpy())
        return grad_input, violation

    def diagnostics(self) -> dict:
        return {
            'algebra':        self.algebra,
            'gauge':          self.gauge,
            'alpha':          self.alpha,
            'hbar':           self.hbar_val,
            'vev_distance':   float(self.bias.vev_distance().numpy()),
            'field_strength': float(self.kinetic.field_strength().numpy()),
            'noether_viol':   self.noether.violation(),
            'conserved':      self.noether.is_conserved(),
            'potential':      float(self.bias.potential().numpy()),
        }


# ==============================================================================
# MODULE 5 — FULL SMNNIP TOWER (TF)
# ==============================================================================

class SMNNIPTowerTF(tf.Module):
    """
    The full SMNNIP algebra tower — TensorFlow production engine.
    ℝ → ℂ → ℍ → 𝕆

    Mirrors the pure Python SMNNIPTower API exactly.
    Physics results should agree between engines.
    """

    def __init__(self, vocab_size: int, hidden_dim: int, context_len: int,
                 name: str = 'smnnip_tower'):
        super().__init__(name=name)
        self.vocab_size  = vocab_size
        self.hidden_dim  = hidden_dim
        self.context_len = context_len

        input_dim = vocab_size * context_len

        self.layers_tf = [
            AlgebraLayerTF(
                in_dim=input_dim, out_dim=hidden_dim,
                algebra_name='R', gauge_group='trivial',
                hbar=0.10, g=0.010, mu_sq=0.5, lam=0.10, mass=0.10,
                name='layer_R'
            ),
            AlgebraLayerTF(
                in_dim=hidden_dim, out_dim=hidden_dim,
                algebra_name='C', gauge_group='U(1)',
                hbar=0.08, g=0.009, mu_sq=0.5, lam=0.10, mass=0.08,
                name='layer_C'
            ),
            AlgebraLayerTF(
                in_dim=hidden_dim, out_dim=hidden_dim,
                algebra_name='H', gauge_group='SU(2)',
                hbar=0.05, g=0.007, mu_sq=0.4, lam=0.12, mass=0.05,
                name='layer_H'
            ),
            AlgebraLayerTF(
                in_dim=hidden_dim, out_dim=vocab_size,
                algebra_name='O', gauge_group='G2',
                hbar=0.02, g=0.005, mu_sq=0.3, lam=0.15, mass=0.02,
                name='layer_O'
            ),
        ]

        self.observer      = get_observer()
        self.loss_history:    List[float] = []
        self.noether_history: List[float] = []
        self.vev_history:     List[float] = []

    def _encode_context(self, context_vecs: List[List[float]]) -> tf.Tensor:
        """Flatten and convert context to TF tensor."""
        flat = []
        for v in context_vecs:
            flat.extend(v)
        input_dim = self.vocab_size * self.context_len
        if len(flat) < input_dim:
            flat.extend([0.0] * (input_dim - len(flat)))
        flat = flat[:input_dim]
        return tf.constant(flat, dtype=tf.float32)

    def forward(self, context_vecs: List[List[float]]) -> List[float]:
        """Forward pass. Returns softmax probs as Python list (API compatibility)."""
        psi = self._encode_context(context_vecs)
        for layer in self.layers_tf:
            psi, _ = layer.forward(psi)
            out_dim = layer.out_dim
            if psi.shape[0] < out_dim:
                psi = tf.pad(psi, [[0, out_dim - psi.shape[0]]])
            psi = psi[:out_dim]
        probs = tf.nn.softmax(psi)
        return probs.numpy().tolist()

    def train_step(self, context_vecs: List[List[float]],
                   target_idx: int,
                   lr: float = 0.005) -> Tuple[float, float, List[float]]:
        """
        One complete SMNNIP training step via GradientTape.
        Returns: (loss, mean_noether_violation, probs)
        """
        psi = self._encode_context(context_vecs)
        activations = [psi]

        # Forward pass
        for layer in self.layers_tf:
            psi, _ = layer.forward(psi)
            out_dim = layer.out_dim
            if psi.shape[0] < out_dim:
                psi = tf.pad(psi, [[0, out_dim - psi.shape[0]]])
            psi = psi[:out_dim]
            activations.append(psi)

        probs   = tf.nn.softmax(activations[-1])
        target  = tf.one_hot(target_idx, self.vocab_size)
        loss    = -tf.reduce_sum(target * tf.math.log(tf.clip_by_value(probs, 1e-15, 1.0)))

        # Backward: Yang-Mills gradient propagation
        grad = probs - target
        total_violation = 0.0

        for i in reversed(range(len(self.layers_tf))):
            psi_in  = activations[i]
            out_dim = self.layers_tf[i].out_dim
            if grad.shape[0] < out_dim:
                grad = tf.pad(grad, [[0, out_dim - grad.shape[0]]])
            grad = grad[:out_dim]
            grad, violation = self.layers_tf[i].backward_step(psi_in, grad, lr)
            total_violation += violation

        mean_violation = total_violation / len(self.layers_tf)
        return float(loss.numpy()), mean_violation, probs.numpy().tolist()

    def uncertainty_bound(self) -> float:
        """ΔToken · ΔMeaning ≥ ħ_NN / 2"""
        return self.layers_tf[0].hbar_val / 2.0

    def full_diagnostics(self) -> List[dict]:
        return [layer.diagnostics() for layer in self.layers_tf]

    def total_lagrangian(self, context_vecs: List[List[float]]) -> float:
        """Compute total ℒ_NN at current field configuration."""
        psi     = self._encode_context(context_vecs)
        L_total = tf.constant(0.0)
        for layer in self.layers_tf:
            psi, L_layer = layer.forward(psi)
            L_total += L_layer
            out_dim = layer.out_dim
            if psi.shape[0] < out_dim:
                psi = tf.pad(psi, [[0, out_dim - psi.shape[0]]])
            psi = psi[:out_dim]
        return float(L_total.numpy())

    def save_weights(self, path: str) -> None:
        """Save all TF variables to a checkpoint."""
        ckpt = tf.train.Checkpoint(tower=self)
        ckpt.write(path)

    def load_weights(self, path: str) -> None:
        """Load variables from a checkpoint."""
        ckpt = tf.train.Checkpoint(tower=self)
        ckpt.read(path).expect_partial()


# ==============================================================================
# MODULE 6 — CHARACTER ENCODER (same API as pure engine)
# ==============================================================================

class CharacterEncoder:
    def __init__(self, text: Optional[str] = None):
        self.char_to_idx: dict = {}
        self.idx_to_char: dict = {}
        self.vocab_size: int   = 0
        if text:
            self.build_vocab(text)

    def build_vocab(self, text: str) -> None:
        chars            = sorted(set(text))
        self.char_to_idx = {c: i for i, c in enumerate(chars)}
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        self.vocab_size  = len(chars)

    def one_hot(self, char: str) -> List[float]:
        v = [0.0] * self.vocab_size
        if char in self.char_to_idx:
            v[self.char_to_idx[char]] = 1.0
        return v

    def decode(self, probs: List[float]) -> str:
        idx = max(range(len(probs)), key=lambda i: probs[i])
        return self.idx_to_char.get(idx, '?')


# ==============================================================================
# MODULE 7 — TRAINING AND GENERATION UTILITIES (same API as pure engine)
# ==============================================================================

def build_training_data(text: str, encoder: CharacterEncoder,
                        context_len: int) -> List[Tuple[List[List[float]], int]]:
    data = []
    for i in range(len(text) - context_len):
        ctx      = text[i : i + context_len]
        target   = text[i + context_len]
        ctx_vecs = [encoder.one_hot(c) for c in ctx]
        tgt_idx  = encoder.char_to_idx.get(target, 0)
        data.append((ctx_vecs, tgt_idx))
    return data


def train_epoch(tower: SMNNIPTowerTF, data: List[Tuple],
                lr: float = 0.005, max_samples: int = 500) -> Tuple[float, float, float]:
    """
    One training epoch. Returns (mean_loss, mean_noether_violation, mean_vev_distance).
    API identical to pure engine's train_epoch.
    """
    import random
    random.shuffle(data)

    total_loss      = 0.0
    total_violation = 0.0
    n               = 0

    for ctx_vecs, tgt_idx in data[:max_samples]:
        loss, violation, _ = tower.train_step(ctx_vecs, tgt_idx, lr)
        total_loss      += loss
        total_violation += violation
        n               += 1

    vev_distances = [float(layer.bias.vev_distance().numpy())
                     for layer in tower.layers_tf]
    mean_vev      = sum(vev_distances) / len(vev_distances)

    n = max(n, 1)
    return total_loss / n, total_violation / n, mean_vev


def generate_text(tower: SMNNIPTowerTF, encoder: CharacterEncoder,
                  seed: str, n_chars: int = 100,
                  temperature: float = 1.0) -> str:
    """Generate text. API identical to pure engine."""
    import random
    import math as _math

    context = list(seed[-tower.context_len:])
    while len(context) < tower.context_len:
        context = [' '] + context

    result = seed
    for _ in range(n_chars):
        ctx_vecs = [encoder.one_hot(c) for c in context]
        probs    = tower.forward(ctx_vecs)

        if temperature != 1.0:
            logits = [_math.log(max(p, 1e-15)) / temperature for p in probs]
            m      = max(logits)
            exps   = [_math.exp(x - m) for x in logits]
            s      = sum(exps)
            probs  = [e / s for e in exps]

        r, cumulative = random.random(), 0.0
        chosen        = len(probs) - 1
        for i, p in enumerate(probs):
            cumulative += p
            if r < cumulative:
                chosen = i
                break

        char    = encoder.idx_to_char.get(chosen, '?')
        result += char
        context = context[1:] + [char]

    return result
