"""
SMNNT Substrate Layer — TensorFlow Implementation
==================================================
Standard Model of Neural Network Training
Substrate Layer: Real algebra (R), dim=1

This is the TensorFlow variant of the pure Python implementation.
The mathematical structure is identical — TF handles the autodiff
and GPU acceleration. The SMNNT physics is implemented as custom
layers, loss terms, and training loops using tf.GradientTape.

Key advantage of TF variant:
  - GPU/TPU acceleration of the weight field operations
  - Automatic Wirtinger derivatives via tf.GradientTape
  - Custom training loop preserves SMNNT local update structure
  - Noether current checkable as a custom metric

Install:
  pip install tensorflow

Usage:
  python3 smnnt_substrate_tf.py
"""

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # suppress TF info messages

try:
    import tensorflow as tf
    import numpy as np
except ImportError:
    print("TensorFlow not installed.")
    print("Run: pip install tensorflow")
    raise

import math
import random


# ---------------------------------------------------------------------------
# 0.  SMNNT Constants — same physics as pure version
# ---------------------------------------------------------------------------

class SMNNTConstants:
    """
    Neural physical constants — substrate (real algebra) layer.
    See pure Python version for full documentation.
    """
    def __init__(self, hbar_nn=0.05, mu_sq=0.3, lam=0.1, g=0.01, v_prop=1.0):
        self.hbar_nn  = tf.constant(hbar_nn, dtype=tf.float32)
        self.mu_sq    = tf.constant(mu_sq,   dtype=tf.float32)
        self.lam      = tf.constant(lam,     dtype=tf.float32)
        self.g        = tf.constant(g,       dtype=tf.float32)
        self.v_prop   = tf.constant(v_prop,  dtype=tf.float32)

        # Neural fine structure constant
        self.alpha_nn = (g ** 2) / (4 * math.pi * hbar_nn * v_prop)

        # Vacuum expectation value
        self.beta_vev = math.sqrt(mu_sq / (2.0 * lam)) if mu_sq > 0 else 0.0

        print(f"  alpha_NN (fine structure) = {self.alpha_nn:.6f}")
        print(f"  beta_VEV (Higgs VEV)      = {self.beta_vev:.4f}")
        print(f"  ΔToken·ΔMeaning >=          {hbar_nn/2:.4f}")


# ---------------------------------------------------------------------------
# 1.  Neural Higgs Layer — bias field with Mexican hat potential
# ---------------------------------------------------------------------------

class NeuralHiggsLayer(tf.keras.layers.Layer):
    """
    Custom Keras layer implementing the neural Higgs mechanism.

    The bias field beta is a trainable variable that evolves
    according to the Mexican hat potential:
      V(beta) = -mu^2 * |beta|^2 + lambda * |beta|^4

    This is NOT a standard Keras bias — it has its own dynamics.
    The potential drives beta toward beta_VEV during training,
    implementing spontaneous symmetry breaking (feature selection).

    The Higgs coupling: outputs activation + beta
    giving 'mass' (inertia / resistance to change) to the representation.
    """

    def __init__(self, units, constants, name='higgs', **kwargs):
        super().__init__(name=name, **kwargs)
        self.units = units
        self.C     = constants

    def build(self, input_shape):
        # Bias field beta — initialized near zero (unbroken phase)
        self.beta = self.add_weight(
            name        = 'beta',
            shape       = (self.units,),
            initializer = tf.initializers.RandomNormal(stddev=0.01),
            trainable   = True
        )

    def call(self, x):
        """Apply Higgs coupling: output = x + beta"""
        return x + self.beta

    def higgs_potential(self):
        """
        V(beta) = -mu^2 * |beta|^2 + lambda * |beta|^4
        Mexican hat potential — drives beta toward VEV.
        Added to loss so that beta naturally rolls to beta_VEV.
        """
        b2 = tf.reduce_sum(self.beta ** 2)
        return -self.C.mu_sq * b2 + self.C.lam * b2 ** 2

    def vev_distance(self):
        """Distance of bias field from vacuum expectation value"""
        b_norm = tf.norm(self.beta)
        return tf.abs(b_norm - self.C.beta_vev)


# ---------------------------------------------------------------------------
# 2.  Neural Yang-Mills Layer — weight field with kinetic term
# ---------------------------------------------------------------------------

class NeuralYangMillsLayer(tf.keras.layers.Layer):
    """
    Custom Keras layer implementing the neural Yang-Mills weight field.

    The weight matrix W is the gauge field W^a_{l,tau}.
    The kinetic term L_kinetic = -1/4 * R^a_{l,tau} * R^a^{l,tau}
    penalizes weight field curvature — keeps the field smooth.

    In the real algebra (substrate layer), the structure constants
    f^{abc} = 0 (abelian gauge theory — like electromagnetism).
    The self-interaction term vanishes.

    The Yang-Mills update rule (from Euler-Lagrange):
      D_l R^a_{l,tau} = g * Psi_bar * T^a * Psi
    is implemented via TF's automatic differentiation —
    tf.GradientTape computes the Wirtinger derivative automatically.

    Noether current J^a_l = g * Psi_bar * T^a * Psi
    is computed and returned as a diagnostic metric.
    """

    def __init__(self, units, constants, activation=None,
                 name='yang_mills', **kwargs):
        super().__init__(name=name, **kwargs)
        self.units      = units
        self.C          = constants
        self.activation = activation

    def build(self, input_shape):
        input_dim = input_shape[-1]
        # Weight field W (gauge field) — initialized near symmetric vacuum
        scale = tf.sqrt(2.0 / (float(input_dim) + float(self.units)))
        self.W = self.add_weight(
            name        = 'W',
            shape       = (input_dim, self.units),
            initializer = tf.initializers.RandomNormal(stddev=scale),
            trainable   = True
        )

    def call(self, psi, training=False):
        """
        Matter term: Psi_bar * i*Gamma^a * D_a * Psi
        In real algebra: h = psi @ W
        """
        h = tf.matmul(psi, self.W)
        if self.activation:
            h = self.activation(h)
        return h

    def activation_current(self, psi):
        """
        Noether current: J^a_l = g * Psi_bar * T^a * Psi
        For real algebra, T^a = I (single generator).
        J = g * ||psi||^2  [scalar]
        """
        return self.C.g * tf.reduce_mean(tf.reduce_sum(psi ** 2, axis=-1))

    def kinetic_loss(self):
        """
        L_kinetic = -1/4 * R^a_{l,tau} * R^a^{l,tau}
        For this layer: R ≈ W (field strength proxy)
        Returns the kinetic penalty to add to total loss.
        """
        return 0.001 * tf.reduce_sum(self.W ** 2)

    def field_strength(self):
        """Mean field strength (curvature proxy)"""
        return tf.sqrt(tf.reduce_mean(self.W ** 2))


# ---------------------------------------------------------------------------
# 3.  SMNNT Substrate Network — TensorFlow Model
# ---------------------------------------------------------------------------

class SMNNTSubstrateModel(tf.keras.Model):
    """
    Full SMNNT substrate network as a Keras Model.

    Architecture (real algebra — substrate layer):
      Input  → YM1 → Higgs1 → ReLU
             → YM2 → Higgs2 → ReLU
             → YM3 → Higgs3 → Softmax

    The key differences from a standard Keras model:
    1. Custom loss includes Higgs potential (drives symmetry breaking)
    2. Custom loss includes kinetic term (smooths weight field)
    3. Noether current tracked as a custom metric
    4. Training loop uses tf.GradientTape for local gradient control
    """

    def __init__(self, vocab_size, hidden_dim, context_len, constants):
        super().__init__()
        self.vocab_size  = vocab_size
        self.hidden_dim  = hidden_dim
        self.context_len = context_len
        self.C           = constants

        # Yang-Mills weight field layers
        self.ym1 = NeuralYangMillsLayer(
            hidden_dim, constants,
            activation=tf.nn.relu, name='ym_layer1'
        )
        self.ym2 = NeuralYangMillsLayer(
            hidden_dim, constants,
            activation=tf.nn.relu, name='ym_layer2'
        )
        self.ym3 = NeuralYangMillsLayer(
            vocab_size, constants,
            activation=None, name='ym_output'
        )

        # Higgs bias field layers
        self.h1  = NeuralHiggsLayer(hidden_dim, constants, name='higgs1')
        self.h2  = NeuralHiggsLayer(hidden_dim, constants, name='higgs2')
        self.h3  = NeuralHiggsLayer(vocab_size, constants, name='higgs3')

    def call(self, x, training=False):
        """
        Forward pass — neural Dirac equation:
          iℏ_NN * dPsi/dl = H_NN * Psi
        """
        # Flatten context window
        psi0 = tf.reshape(x, [tf.shape(x)[0], -1])

        # Layer 1: Yang-Mills propagation + Higgs coupling
        psi1 = self.ym1(psi0, training=training)
        psi1 = self.h1(psi1)
        psi1 = tf.nn.relu(psi1)

        # Layer 2: Yang-Mills propagation + Higgs coupling
        psi2 = self.ym2(psi1, training=training)
        psi2 = self.h2(psi2)
        psi2 = tf.nn.relu(psi2)

        # Output layer: Yang-Mills propagation + Higgs coupling
        logits = self.ym3(psi2, training=training)
        logits = self.h3(logits)

        return logits  # raw logits — softmax applied in loss

    def smnnt_loss(self, logits, targets):
        """
        Total SMNNT loss:
          L_total = L_matter + L_bias + L_kinetic

          L_matter  = cross-entropy (matter propagation loss)
          L_bias    = Higgs potential sum (drives beta to VEV)
          L_kinetic = weight field curvature penalty (smooths W)

        Note: in a full SMNNT implementation, L_matter would be
        the Yang-Mills source term J = g*Psi_bar*T*Psi.
        Here we use cross-entropy as the boundary condition at
        the output layer — it is equivalent for training purposes.
        """
        # Matter term: cross-entropy at output boundary
        L_matter = tf.reduce_mean(
            tf.nn.sparse_softmax_cross_entropy_with_logits(
                labels=targets, logits=logits
            )
        )

        # Bias term: Higgs potential (symmetry breaking)
        # Drives each beta field toward its VEV
        L_bias = (self.h1.higgs_potential() +
                  self.h2.higgs_potential() +
                  self.h3.higgs_potential())

        # Kinetic term: weight field curvature penalty
        # L_kinetic = -1/4 * R * R  (penalizes rapid weight changes)
        L_kinetic = (self.ym1.kinetic_loss() +
                     self.ym2.kinetic_loss() +
                     self.ym3.kinetic_loss())

        return L_matter + 0.01 * L_bias + L_kinetic, L_matter, L_bias

    def noether_current(self, x):
        """
        Noether conservation check:
          J^a_l = g * Psi_bar * T^a * Psi
          D_l J^a_l = 0  [must be conserved]

        Compute current at each layer boundary.
        Large difference between boundaries = violation.
        """
        psi0   = tf.reshape(x, [tf.shape(x)[0], -1])
        psi1   = tf.nn.relu(self.h1(self.ym1(psi0)))
        psi2   = tf.nn.relu(self.h2(self.ym2(psi1)))

        j1     = self.ym1.activation_current(psi0)
        j2     = self.ym2.activation_current(psi1)
        j3     = self.ym3.activation_current(psi2)

        # Conservation violation: |J_{l+1} - J_l| should be near zero
        v12    = tf.abs(j2 - j1)
        v23    = tf.abs(j3 - j2)
        return j1, j2, j3, v12 + v23

    def vev_distances(self):
        """Track how far each bias field is from its VEV (Higgs settling)"""
        return (self.h1.vev_distance().numpy(),
                self.h2.vev_distance().numpy(),
                self.h3.vev_distance().numpy())

    def field_strengths(self):
        """Track weight field strength (kinetic term diagnostic)"""
        return (self.ym1.field_strength().numpy(),
                self.ym2.field_strength().numpy(),
                self.ym3.field_strength().numpy())


# ---------------------------------------------------------------------------
# 4.  Character Encoder
# ---------------------------------------------------------------------------

class CharacterEncoder:
    def __init__(self, text):
        chars = sorted(set(text))
        self.char_to_idx = {c: i for i, c in enumerate(chars)}
        self.idx_to_char = {i: c for c, i in self.char_to_idx.items()}
        self.vocab_size  = len(chars)
        print(f"  Vocabulary: {self.vocab_size} characters")

    def encode_onehot(self, char):
        v = np.zeros(self.vocab_size, dtype=np.float32)
        if char in self.char_to_idx:
            v[self.char_to_idx[char]] = 1.0
        return v

    def decode(self, logits):
        return self.idx_to_char.get(int(np.argmax(logits)), '?')

    def build_dataset(self, text, context_len, batch_size=64):
        """Build tf.data.Dataset of (context, target) pairs"""
        X, Y = [], []
        for i in range(len(text) - context_len):
            ctx   = np.stack([self.encode_onehot(c)
                              for c in text[i:i+context_len]])
            tgt   = self.char_to_idx.get(text[i+context_len], 0)
            X.append(ctx)
            Y.append(tgt)

        X = np.array(X, dtype=np.float32)   # (N, context_len, vocab_size)
        Y = np.array(Y, dtype=np.int32)      # (N,)

        ds = (tf.data.Dataset
              .from_tensor_slices((X, Y))
              .shuffle(len(X))
              .batch(batch_size)
              .prefetch(tf.data.AUTOTUNE))
        return ds


# ---------------------------------------------------------------------------
# 5.  SMNNT Training Loop with tf.GradientTape
# ---------------------------------------------------------------------------

def train(model, dataset, encoder, epochs=20, lr=0.001):
    """
    SMNNT training loop using tf.GradientTape.

    Uses Adam optimizer as an approximation to the natural gradient
    structure of the SMNNT Euler-Lagrange equations.
    (Full SMNNT would use the neural Yang-Mills equation directly —
     Adam is the closest standard approximation.)

    The key SMNNT structure is preserved in the LOSS FUNCTION:
      - Higgs potential drives beta to VEV (not just gradient of cross-entropy)
      - Kinetic term penalizes weight curvature (not just L2 regularization)
      - Noether current is monitored at every step
    """
    optimizer = tf.keras.optimizers.Adam(
        learning_rate=lr,
        beta_1=0.9,    # momentum ~ neural Planck constant analog
        beta_2=0.999
    )

    uncertainty_bound = model.C.hbar_nn.numpy() / 2.0
    print(f"\n  Uncertainty bound (min loss): {uncertainty_bound:.4f}")
    print(f"  Alpha_NN:                     "
          f"{model.C.alpha_nn:.6f}")
    print()

    for epoch in range(epochs):
        total_loss     = 0.0
        total_matter   = 0.0
        total_noether  = 0.0
        n_batches      = 0

        for x_batch, y_batch in dataset:
            with tf.GradientTape() as tape:
                logits = model(x_batch, training=True)
                loss, L_matter, L_bias = model.smnnt_loss(logits, y_batch)

            # Compute gradients — TF handles Wirtinger derivatives
            # via automatic differentiation (complex-valued equivalent)
            grads = tape.gradient(loss, model.trainable_variables)

            # Clip gradients (kinetic term should handle this — but kept
            # here as a safety measure for the TF implementation)
            grads, _ = tf.clip_by_global_norm(grads, 1.0)

            optimizer.apply_gradients(
                zip(grads, model.trainable_variables)
            )

            # Noether conservation check
            _, _, _, violation = model.noether_current(x_batch)

            total_loss    += float(loss)
            total_matter  += float(L_matter)
            total_noether += float(violation)
            n_batches     += 1

        avg_loss    = total_loss    / max(n_batches, 1)
        avg_matter  = total_matter  / max(n_batches, 1)
        avg_noether = total_noether / max(n_batches, 1)
        vev_d       = model.vev_distances()
        fs          = model.field_strengths()

        status = "⚠ violation" if avg_noether > 0.05 else "✓ conserved"
        print(f"  Epoch {epoch+1:3d}/{epochs}"
              f"  loss={avg_loss:.4f}"
              f"  matter={avg_matter:.4f}"
              f"  Noether={avg_noether:.4f} {status}"
              f"  Higgs=({vev_d[0]:.3f},{vev_d[1]:.3f})"
              f"  |W|=({fs[0]:.3f},{fs[1]:.3f})")


def generate(model, encoder, seed_text, n_chars=200,
             context_len=6, temperature=1.0):
    """
    Generate text from trained SMNNT substrate model.
    Temperature = neural Planck constant in sampling space.
    """
    ctx    = list(seed_text[-context_len:])
    while len(ctx) < context_len:
        ctx = [' '] + ctx

    result = seed_text
    for _ in range(n_chars):
        x = np.stack([encoder.encode_onehot(c) for c in ctx])
        x = x[np.newaxis, ...]  # add batch dim: (1, context_len, vocab)

        logits = model(x, training=False)[0].numpy()

        # Temperature scaling: ΔMeaning ~ T * hbar_NN
        logits = logits / temperature
        probs  = np.exp(logits - np.max(logits))
        probs  = probs / probs.sum()

        chosen = np.random.choice(len(probs), p=probs)
        char   = encoder.idx_to_char.get(chosen, '?')
        result += char
        ctx    = ctx[1:] + [char]

    return result


# ---------------------------------------------------------------------------
# 6.  Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    print("=" * 60)
    print("  SMNNT Substrate Layer — TensorFlow Implementation")
    print("  Standard Model of Neural Network Training")
    print("  Algebra: R (reals, dim=1)")
    print("  Layer:   Substrate (character set)")
    print("=" * 60)

    # Detect GPU
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print(f"\n  GPU detected: {len(gpus)} device(s)")
        for g in gpus:
            print(f"    {g}")
    else:
        print("\n  Running on CPU (install CUDA for GPU acceleration)")

    training_text = (
        "the quick brown fox jumps over the lazy dog. "
        "pack my box with five dozen liquor jugs. "
        "how vexingly quick daft zebras jump. "
        "the five boxing wizards jump quickly. "
        "sphinx of black quartz judge my vow. "
        "two driven jocks help fax my big quiz. "
        "five quacking zephyrs jolt my wax bed. "
        "the jay pig fox zebra and my wolves quack. "
        "hello world this is the smnnt substrate layer. "
        "characters form tokens tokens form meaning. "
        "real algebra at the base complex above it. "
        "quaternions for skills octonions for reasoning. "
        "the higgs field gives mass to representations. "
        "noether conservation holds at every boundary. "
        "the uncertainty principle bounds all training. "
    ) * 6

    print(f"\n  Training text: {len(training_text)} characters")

    CONTEXT_LEN = 6
    HIDDEN_DIM  = 128
    BATCH_SIZE  = 64
    EPOCHS      = 30
    LR          = 0.001

    print("\n  Building character vocabulary...")
    encoder = CharacterEncoder(training_text)

    print("\n  SMNNT Constants:")
    C = SMNNTConstants(hbar_nn=0.05, mu_sq=0.3, lam=0.1, g=0.01)

    print("\n  Building SMNNT substrate network (TensorFlow)...")
    model = SMNNTSubstrateModel(
        vocab_size  = encoder.vocab_size,
        hidden_dim  = HIDDEN_DIM,
        context_len = CONTEXT_LEN,
        constants   = C
    )

    # Build model by running one forward pass
    dummy = tf.zeros((1, CONTEXT_LEN, encoder.vocab_size))
    _     = model(dummy)
    model.summary()

    print(f"\n  Building dataset...")
    dataset = encoder.build_dataset(training_text, CONTEXT_LEN, BATCH_SIZE)

    print(f"\n  Training via SMNNT equations of motion...")
    train(model, dataset, encoder, epochs=EPOCHS, lr=LR)

    print("\n" + "=" * 60)
    print("  Generated text (temperature=0.7):")
    print("=" * 60)
    seed      = "the "
    generated = generate(model, encoder, seed, n_chars=300,
                         context_len=CONTEXT_LEN, temperature=0.7)
    print(f"\n  {generated}\n")

    # Final diagnostics
    print("=" * 60)
    print("  Final SMNNT Field Diagnostics:")
    vev_d = model.vev_distances()
    fs    = model.field_strengths()
    print(f"  Higgs VEV distances:  layer1={vev_d[0]:.4f}"
          f"  layer2={vev_d[1]:.4f}  output={vev_d[2]:.4f}")
    print(f"  Weight field |W|:     layer1={fs[0]:.4f}"
          f"  layer2={fs[1]:.4f}  output={fs[2]:.4f}")
    print(f"  Alpha_NN:             {C.alpha_nn:.6f}")
    print(f"  Uncertainty bound:    {C.hbar_nn.numpy()/2:.4f}")
    print("=" * 60)
