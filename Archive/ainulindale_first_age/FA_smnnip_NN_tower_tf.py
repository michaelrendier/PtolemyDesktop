#!/usr/bin/env python3
"""
==============================================================================
FA_smnnip_NN_tower_tf.py
SMNNIP Neural Network Tower -- TensorFlow -- First Age
==============================================================================
Standard Model of Neural Network Information Propagation

TensorFlow version of the FA_smnnip_NN_tower.

Key design principle:
  TF trains weights (what it is good at).
  Pure Python computes all indices (arbitrary precision, no overflow).
  The two never touch the same data.

Index arithmetic: pure Python int throughout (unlimited precision).
  TF never sees permutation indices. Indices go directly to the ledger
  as decimal strings. No chunking. No int64 overflow. No special cases.

Architecture:
  TextSubstrate  (TF Dense, 97-char fixed vocab)  --+
                                                     +--> SharedUpperTower --> output
  ImageSubstrate (TF Dense, spherical CMYK Oct)   --+

  Corrected Lagrangian: L_NN = (2/pi)*oint[L_kin + L_mat + (1/phi)*L_bias + L_coup]
  Mastery: tf.Variable(trainable=False) boolean flag per weight field

Imports FA_smnnip_hyperindex for all indexing.
Imports FA_smnnip_NN_tower for shared non-TF components (SphericalColor etc).

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026 -- First Age
==============================================================================
"""

import math
import random
import sys
import os
import time
from typing import List, Tuple, Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Pure Python index system (no TF needed for indices)
from FA_smnnip_hyperindex import (
    TextHyperIndex, ImageHyperIndex, MultiChannelTupper,
    SphericalColor, BlockchainLedger,
    layer_to_r, alpha_nn_from_r, polar_lagrangian,
    assert_within_tower, SedenionBoundaryViolation,
    MASTERY_THRESHOLDS, US_KEYBOARD_CHARS, VOCAB_SIZE,
)

# TF import
try:
    import tensorflow as tf
    _TF_OK = True
    print(f"TensorFlow {tf.__version__} loaded")
except ImportError:
    _TF_OK = False
    print("WARNING: TensorFlow not found. Install: pip install tensorflow")
    print("Falling back to pure Python tower.")
    # Fall back to pure python tower transparently
    from FA_smnnip_NN_tower import (
        FATextNNTower, FAImageNNTower, FACombinedNNTower
    )
    # Re-export so caller code works unchanged
    __all__ = ['TFTextNNTower', 'TFImageNNTower', 'TFCombinedNNTower',
               'FATextNNTower', 'FAImageNNTower', 'FACombinedNNTower']

# ── Constants ────────────────────────────────────────────────────────────────

L_TOTAL     = 4
PHI         = (1.0 + math.sqrt(5.0)) / 2.0
BIAS_COUP   = 1.0 / PHI         # 0.6180...
TWO_OVER_PI = 2.0 / math.pi

LNAME  = {0:'R', 1:'C', 2:'H', 3:'O'}
LHBAR  = {0:0.10, 1:0.08, 2:0.05, 3:0.02}
LG     = {0:0.010, 1:0.009, 2:0.007, 3:0.005}
LMU    = {0:0.5,  1:0.5,  2:0.4,  3:0.3}
LLAM   = {0:0.10, 1:0.10, 2:0.12, 3:0.15}


if _TF_OK:

    # =========================================================================
    # TF LAYER WITH MASTERY
    # =========================================================================

    class TFMasteredLayer(tf.keras.layers.Layer):
        """
        Yang-Mills weight layer with mastery crystallization.

        When mastered:
          - trainable=False set on all weights
          - forward pass still runs (zero cost: no gradient computation)
          - mastery flag stored as non-trainable tf.Variable

        Index arithmetic (permutation, Tupper, Fano): pure Python.
        TF never sees the indices. They go straight to the ledger.
        """

        def __init__(self, in_d, out_d, layer_idx, name_sfx='', **kw):
            super().__init__(name=f"mastered_L{layer_idx}_{name_sfx}", **kw)
            self.in_d       = in_d
            self.out_d      = out_d
            self.layer_idx  = layer_idx
            self.hbar       = LHBAR[layer_idx]
            self.g_coup     = LG[layer_idx]
            self.r          = layer_to_r(layer_idx, L_TOTAL)
            self.alpha_nn   = alpha_nn_from_r(self.g_coup, self.hbar, self.r)
            self._threshold = MASTERY_THRESHOLDS[LNAME[layer_idx]]
            self._mastered_flag = False

            assert_within_tower(layer_idx)

            scale = math.sqrt(2.0 / (in_d + out_d))
            self.W = self.add_weight(
                name='W', shape=(in_d, out_d),
                initializer=tf.initializers.TruncatedNormal(stddev=scale),
                trainable=True
            )
            self.b = self.add_weight(
                name='b', shape=(out_d,),
                initializer='zeros', trainable=True
            )
            # Non-trainable mastery flag (survives save/load)
            self.mastered = self.add_weight(
                name='mastered', shape=(), dtype=tf.bool,
                initializer=tf.initializers.Constant(False),
                trainable=False
            )
            # VEV reference
            self.vev_ref = self.add_weight(
                name='vev_ref', shape=(), dtype=tf.float32,
                initializer='zeros', trainable=False
            )

        def call(self, psi):
            out = tf.matmul(psi, self.W) + self.b
            return tf.nn.relu(out)

        def field_strength(self):
            return float(tf.norm(self.W).numpy())

        def noether_current(self, psi):
            return float(self.g_coup * tf.reduce_sum(psi * psi).numpy())

        def l_kinetic(self):
            return -0.25 * self.field_strength()**2

        def vev_distance(self, vev):
            return abs(self.field_strength() - vev)

        def check_mastery(self, vev):
            if self._mastered_flag:
                return True
            if self.vev_distance(vev) < self._threshold:
                self._mastered_flag = True
                self.mastered.assign(True)
                self.vev_ref.assign(float(vev))
                # Freeze weights
                self.W.assign(self.W)  # no-op for value; trainable cleared below
                # TF: set non-trainable by rebuilding trainable list
                self._set_mastered()
            return self._mastered_flag

        def _set_mastered(self):
            """Freeze this layer's weights."""
            self.W._trainable = False
            self.b._trainable = False

        def is_mastered(self):
            return self._mastered_flag


    class TFHiggsLayer(tf.keras.layers.Layer):
        """Higgs bias field with (1/phi) polar correction and mastery."""

        def __init__(self, size, layer_idx, mu_sq, lam, **kw):
            super().__init__(name=f"higgs_L{layer_idx}", **kw)
            self.size     = size
            self.layer_idx = layer_idx
            self.mu_sq    = mu_sq
            self.lam      = lam
            self.vev      = math.sqrt(mu_sq/(2.0*lam)) if mu_sq > 0 else 0.0
            self._threshold = MASTERY_THRESHOLDS[LNAME[layer_idx]]
            self._mastered  = False

            self.beta = self.add_weight(
                name='beta', shape=(size,),
                initializer=tf.initializers.TruncatedNormal(stddev=0.01),
                trainable=True
            )

        def call(self, psi):
            return psi + self.beta

        def potential(self):
            b2 = float(tf.reduce_sum(self.beta * self.beta).numpy())
            return -self.mu_sq*b2 + self.lam*b2*b2

        def polar_l_bias(self):
            return BIAS_COUP * self.potential()

        def vev_distance(self):
            b_norm = float(tf.norm(self.beta).numpy())
            return abs(b_norm - self.vev)

        def check_mastery(self):
            if self._mastered: return True
            if self.vev_distance() < self._threshold:
                self._mastered = True
                self.beta._trainable = False
            return self._mastered

        def is_mastered(self): return self._mastered


    # =========================================================================
    # TEXT SUBSTRATE (TF)
    # =========================================================================

    class TFTextSubstrate(tf.keras.Model):
        """
        TF Layer 0: 97-char fixed vocab -> hidden_dim.
        Index arithmetic: pure Python (no TF int overflow).
        """

        def __init__(self, hidden_dim, ctx_len):
            super().__init__(name='text_substrate')
            self.vocab_size = VOCAB_SIZE
            self.hidden_dim = hidden_dim
            self.ctx_len    = ctx_len
            self.in_dim     = VOCAB_SIZE * ctx_len
            self.r          = layer_to_r(0, L_TOTAL)  # r=1.0

            # Python-side char maps (not TF)
            self._c2i = {c: i for i, c in enumerate(US_KEYBOARD_CHARS)}
            self._i2c = {i: c for i, c in enumerate(US_KEYBOARD_CHARS)}

            self.W = TFMasteredLayer(self.in_dim, hidden_dim, 0, 'text')
            self.H = TFHiggsLayer(hidden_dim, 0, LMU[0], LLAM[0])

        def one_hot_batch(self, contexts: List[str]) -> tf.Tensor:
            """
            Pure Python encodes context strings to one-hot tensors.
            Index arithmetic (char -> int) stays in Python.
            """
            batch = []
            for ctx in contexts:
                flat = []
                for c in ctx[-self.ctx_len:]:
                    v = [0.0] * self.vocab_size
                    if c in self._c2i:
                        v[self._c2i[c]] = 1.0
                    flat.extend(v)
                while len(flat) < self.in_dim:
                    flat.append(0.0)
                batch.append(flat[:self.in_dim])
            return tf.constant(batch, dtype=tf.float32)

        def call(self, psi_input):
            out = self.W(psi_input)
            out = self.H(out)
            return out

        def hyperindex(self, ctx: str):
            """Pure Python index -- no TF involved."""
            return TextHyperIndex.index_record(ctx)


    # =========================================================================
    # IMAGE SUBSTRATE (TF)
    # =========================================================================

    class TFImageSubstrate(tf.keras.Model):
        """
        TF Layer 0: 8x8 RGB tile -> spherical CMYK Oct -> hidden_dim.
        Spherical color encoding: pure Python (SphericalColor).
        Tupper index: pure Python (MultiChannelTupper).
        TF only handles the Dense layer weights.
        """

        def __init__(self, hidden_dim, tile=8, img_w=8, img_h=8):
            super().__init__(name='image_substrate')
            self.tile       = tile
            self.in_dim     = tile * tile * 8
            self.hidden_dim = hidden_dim
            self.img_w      = img_w
            self.img_h      = img_h

            self.W = TFMasteredLayer(self.in_dim, hidden_dim, 0, 'image')
            self.H = TFHiggsLayer(hidden_dim, 0, LMU[0], LLAM[0])

        def encode_batch(self, tiles, depths=None, confs=None):
            """
            Pure Python spherical CMYK encoding.
            Returns tf.Tensor for TF to process.
            """
            batch = []
            for bi, tile in enumerate(tiles):
                d = depths[bi] if depths else 0.0
                c = confs[bi]  if confs  else 0.0
                flat = []
                for x in range(self.tile):
                    for y in range(self.tile):
                        try:   rv,gv,bv = tile[x][y]
                        except: rv,gv,bv = 0.0,0.0,0.0
                        flat.extend(SphericalColor.to_octonion(rv,gv,bv,d,c))
                while len(flat) < self.in_dim: flat.append(0.0)
                batch.append(flat[:self.in_dim])
            return tf.constant(batch, dtype=tf.float32)

        def call(self, psi_input):
            out = self.W(psi_input)
            out = self.H(out)
            return out

        def hyperindex(self, rgb_tile, tx=0, ty=0, depth=0.0, conf=0.0):
            """Pure Python Tupper index -- no TF."""
            return ImageHyperIndex.index_record(
                rgb_tile, tx, ty, self.img_w, self.img_h, depth, conf)

        def tile_r(self, tx, ty):
            return ImageHyperIndex.tile_radial_r(tx, ty, self.img_w, self.img_h)


    # =========================================================================
    # SHARED UPPER TOWER TF (C -> H -> O)
    # =========================================================================

    class TFSharedUpperTower(tf.keras.Model):
        """
        TF C->H->O tower. Receives from either substrate.
        Sedenion boundary enforced.
        Polar Lagrangian computed using Python float ops on TF tensors
        (extracted via .numpy() -- outside the graph for logging only).
        """

        def __init__(self, hidden_dim, output_dim):
            super().__init__(name='shared_upper_tower')
            assert_within_tower(1)
            assert_within_tower(2)
            assert_within_tower(3)

            self.hidden_dim = hidden_dim
            self.output_dim = output_dim

            self.W1 = TFMasteredLayer(hidden_dim, hidden_dim, 1, 'C')
            self.H1 = TFHiggsLayer(hidden_dim, 1, LMU[1], LLAM[1])
            self.W2 = TFMasteredLayer(hidden_dim, hidden_dim, 2, 'H')
            self.H2 = TFHiggsLayer(hidden_dim, 2, LMU[2], LLAM[2])
            self.W3 = TFMasteredLayer(hidden_dim, output_dim, 3, 'O')
            self.H3 = TFHiggsLayer(output_dim, 3, LMU[3], LLAM[3])

            self.noether_hist:    List[float] = []
            self.lagrangian_hist: List[float] = []

        def call(self, sub_out, training=False):
            p1 = self.W1(sub_out);  p1 = self.H1(p1)
            p2 = self.W2(p1);       p2 = self.H2(p2)
            p3 = self.W3(p2);       p3 = self.H3(p3)
            return p3

        def polar_lagrangian_diagnostics(self, sub_out_np,
                                          layer=1) -> float:
            """
            Compute polar Lagrangian scalar for diagnostics.
            Uses Python floats (outside graph). Not used in gradient computation.
            """
            if hasattr(sub_out_np, 'numpy'):
                psi = sub_out_np.numpy().flatten().tolist()
            else:
                psi = list(sub_out_np)
            L_kin  = -0.25 * self.W1.field_strength()**2
            L_mat  = sum(x*x for x in psi[:8]) * 0.1
            L_bias = self.H1.polar_l_bias()
            L_coup = -self.W1.g_coup * sum(x*x for x in psi[:8])
            return polar_lagrangian(L_kin, L_mat, L_bias, L_coup,
                                    layer=layer, L_total=L_TOTAL)

        def noether_violation(self, sub_out) -> float:
            """Noether current conservation diagnostic (Python float)."""
            if hasattr(sub_out, 'numpy'):
                psi = sub_out.numpy().flatten().tolist()
            else:
                psi = list(sub_out)
            J1 = self.W1.g_coup * sum(x*x for x in psi)
            J2 = self.W2.g_coup * sum(x*x for x in psi)
            J3 = self.W3.g_coup * sum(x*x for x in psi)
            return (abs(J2-J1) + abs(J3-J2)) / 2.0

        def check_all_mastery(self, vev=0.5) -> Dict[str, bool]:
            return {
                'W1': self.W1.check_mastery(vev),
                'H1': self.H1.check_mastery(),
                'W2': self.W2.check_mastery(vev),
                'H2': self.H2.check_mastery(),
                'W3': self.W3.check_mastery(vev),
                'H3': self.H3.check_mastery(),
            }

        def mastered_count(self):
            return sum(1 for f in
                       [self.W1,self.H1,self.W2,self.H2,self.W3,self.H3]
                       if f.is_mastered())


    # =========================================================================
    # TF TEXT NN TOWER
    # =========================================================================

    class TFTextNNTower:
        """
        TF text tower: TextSubstrate -> SharedUpperTower -> softmax.
        Pure Python computes all permutation indices.
        TF handles all weight gradients via GradientTape.
        """

        def __init__(self, hidden_dim=64, ctx_len=8,
                     ledger_path='FA_hyperindex_ledger'):
            self.ctx_len    = ctx_len
            self.hidden_dim = hidden_dim
            self.out_dim    = VOCAB_SIZE

            self.substrate = TFTextSubstrate(hidden_dim, ctx_len)
            self.tower     = TFSharedUpperTower(hidden_dim, VOCAB_SIZE)
            self.opt       = tf.keras.optimizers.Adam(learning_rate=0.005)
            self.ledger    = BlockchainLedger(ledger_path)

            self._c2i = {c:i for i,c in enumerate(US_KEYBOARD_CHARS)}
            self._i2c = {i:c for i,c in enumerate(US_KEYBOARD_CHARS)}
            self.loss_hist: List[float] = []
            self._epoch = 0; self._step = 0

            # Build models by calling with dummy input
            dummy = self.substrate.one_hot_batch([' ' * ctx_len])
            sub_out = self.substrate(dummy, training=False)
            self.tower(sub_out, training=False)

        @tf.function
        def _forward_tf(self, psi_input):
            sub_out = self.substrate(psi_input, training=True)
            logits  = self.tower(sub_out, training=True)
            return logits, sub_out

        def train_step(self, context: str, target: str, lr: float = 0.005):
            """
            One training step.
            Index arithmetic: pure Python.
            Weight updates: TF GradientTape.
            """
            if target not in self._c2i:
                return None, None
            ti = self._c2i[target]

            psi_input = self.substrate.one_hot_batch([context])
            target_t  = tf.constant([ti], dtype=tf.int32)

            all_vars = (self.substrate.trainable_variables +
                        self.tower.trainable_variables)

            with tf.GradientTape() as tape:
                sub_out = self.substrate(psi_input, training=True)
                logits  = self.tower(sub_out, training=True)
                probs   = tf.nn.softmax(logits)
                loss    = tf.reduce_mean(
                    tf.nn.sparse_softmax_cross_entropy_with_logits(
                        labels=target_t, logits=logits
                    )
                )

            grads = tape.gradient(loss, all_vars)
            self.opt.apply_gradients(zip(grads, all_vars))

            loss_val   = float(loss.numpy())
            noether    = self.tower.noether_violation(sub_out[0])

            # Pure Python index (no TF arithmetic, no overflow)
            text_idx, fano_idx, data_len = self.substrate.hyperindex(context)

            mastery = self.tower.check_all_mastery(vev=0.5)
            any_m   = any(mastery.values())

            self.ledger.append(
                'text', self._epoch, self._step,
                text_idx, data_len, LNAME[0], noether, any_m,
                {'fano': str(fano_idx), 'loss': loss_val}
            )
            self.loss_hist.append(loss_val)
            self._step += 1
            return loss_val, noether

        def train_epoch(self, text: str, lr: float = 0.005,
                        max_steps: int = 500):
            valid = [(text[i:i+self.ctx_len], text[i+self.ctx_len])
                     for i in range(len(text)-self.ctx_len-1)
                     if text[i+self.ctx_len] in self._c2i]
            random.shuffle(valid)
            valid = valid[:max_steps]
            tl = tn = 0.0; n = 0
            for ctx, tgt in valid:
                ctx = ''.join(c if c in self._c2i else ' ' for c in ctx)
                l, no = self.train_step(ctx, tgt, lr)
                if l is not None:
                    tl += l; tn += no; n += 1
            self._epoch += 1
            n = max(1, n)
            return tl/n, tn/n

        def generate(self, seed: str, length: int = 100,
                     temp: float = 1.0) -> str:
            ctx = seed[-self.ctx_len:]
            ctx = ''.join(c if c in self._c2i else ' ' for c in ctx)
            out = seed
            for _ in range(length):
                psi  = self.substrate.one_hot_batch([ctx])
                so   = self.substrate(psi, training=False)
                log  = self.tower(so, training=False)
                if temp != 1.0:
                    log = log / temp
                probs = tf.nn.softmax(log)[0].numpy()
                ch = int(tf.random.categorical(
                    tf.math.log(tf.maximum(probs, 1e-12))[None], 1)[0,0])
                c  = self._i2c.get(ch, '?')
                out += c
                ctx = (ctx + c)[-self.ctx_len:]
            return out

        def status(self):
            v,_,msg = self.ledger.verify()
            return (f"TF Mastery: tower {self.tower.mastered_count()}/6 "
                    f"| steps={self._step} | {msg[:30]}")


    # =========================================================================
    # TF IMAGE NN TOWER
    # =========================================================================

    class TFImageNNTower:
        """TF image tower: ImageSubstrate -> SharedUpperTower -> class output."""

        def __init__(self, hidden_dim=64, n_classes=16, tile=8,
                     img_w=8, img_h=8,
                     ledger_path='FA_hyperindex_ledger'):
            self.hidden_dim = hidden_dim
            self.n_classes  = n_classes

            self.substrate = TFImageSubstrate(hidden_dim, tile, img_w, img_h)
            self.tower     = TFSharedUpperTower(hidden_dim, n_classes)
            self.opt       = tf.keras.optimizers.Adam(learning_rate=0.005)
            self.ledger    = BlockchainLedger(ledger_path)
            self._epoch = 0; self._step = 0

            # Build
            dummy_tile = [[(0.5,0.5,0.5) for _ in range(tile)]
                          for _ in range(tile)]
            dummy_t = self.substrate.encode_batch([dummy_tile])
            so = self.substrate(dummy_t, training=False)
            self.tower(so, training=False)

        def train_step(self, rgb_tile, target_class: int, lr=0.005,
                       tx=0, ty=0, depth=0.0, conf=0.0):
            psi_input = self.substrate.encode_batch([rgb_tile],[depth],[conf])
            target_t  = tf.constant([target_class], dtype=tf.int32)

            all_vars = (self.substrate.trainable_variables +
                        self.tower.trainable_variables)

            with tf.GradientTape() as tape:
                sub_out = self.substrate(psi_input, training=True)
                logits  = self.tower(sub_out, training=True)
                loss    = tf.reduce_mean(
                    tf.nn.sparse_softmax_cross_entropy_with_logits(
                        labels=target_t, logits=logits
                    )
                )

            grads = tape.gradient(loss, all_vars)
            self.opt.apply_gradients(zip(grads, all_vars))

            loss_val = float(loss.numpy())
            noether  = self.tower.noether_violation(sub_out[0])

            # Pure Python Tupper index
            idx = self.substrate.hyperindex(rgb_tile, tx, ty, depth, conf)
            tile_idx = idx.get('k_C', '0')

            mastery = self.tower.check_all_mastery()
            self.ledger.append(
                'image', self._epoch, self._step,
                tile_idx, self.substrate.tile**2,
                LNAME[0], noether, any(mastery.values()),
                {'color': idx.get('color_index','0'),
                 'r': idx.get('radial_r', 0.0),
                 'loss': loss_val}
            )
            self._step += 1
            return loss_val, noether


    # =========================================================================
    # TF COMBINED TOWER
    # =========================================================================

    class TFCombinedNNTower:
        """
        The Two Towers (TF) -- one shared upper tower, two substrates.
        Independent themes. One Music.
        """

        def __init__(self, hidden_dim=64, ctx_len=8, n_classes=16,
                     ledger_path='FA_hyperindex_ledger'):
            out_dim = max(VOCAB_SIZE, n_classes)
            self.text_sub  = TFTextSubstrate(hidden_dim, ctx_len)
            self.img_sub   = TFImageSubstrate(hidden_dim)
            self.tower     = TFSharedUpperTower(hidden_dim, out_dim)
            self.ledger    = BlockchainLedger(ledger_path)
            self._c2i = {c:i for i,c in enumerate(US_KEYBOARD_CHARS)}
            self._epoch = 0; self._step = 0

            # Build
            dummy_ctx = self.text_sub.one_hot_batch([' ' * ctx_len])
            so = self.text_sub(dummy_ctx, training=False)
            self.tower(so, training=False)

        def forward_text(self, ctx: str) -> List[float]:
            psi = self.text_sub.one_hot_batch([ctx])
            so  = self.text_sub(psi, training=False)
            l   = self.tower(so, training=False)
            return tf.nn.softmax(l[0,:VOCAB_SIZE]).numpy().tolist()

        def forward_image(self, rgb_tile, depth=0.0, conf=0.0):
            psi = self.img_sub.encode_batch([rgb_tile],[depth],[conf])
            so  = self.img_sub(psi, training=False)
            l   = self.tower(so, training=False)
            return tf.nn.softmax(l[0]).numpy().tolist()

        def mastery_summary(self):
            v,_,msg = self.ledger.verify()
            return {
                'tower_mastered': self.tower.mastered_count(),
                'text_W': self.text_sub.W.is_mastered(),
                'img_W':  self.img_sub.W.is_mastered(),
                'chain':  v,
                'blocks': self.ledger._block_id,
            }


# ==============================================================================
# DEMO
# ==============================================================================

def run_demo():
    print("FA_smnnip_NN_tower_tf -- TensorFlow -- First Age")
    print("=" * 60)

    if not _TF_OK:
        print("TensorFlow not available. Running pure Python fallback.")
        from FA_smnnip_NN_tower import run_demo as py_demo
        py_demo()
        return

    print(f"TF {tf.__version__} | "
          f"Lagrangian: (2/pi)*oint[...+(1/phi)*L_bias+...]")
    print(f"1/phi = {BIAS_COUP:.6f} | "
          f"Index arithmetic: pure Python (no TF int overflow)")
    print()

    # Text tower
    print("-- TF Text Tower --")
    txt = TFTextNNTower(hidden_dim=32, ctx_len=4,
                         ledger_path='/tmp/FA_tf_demo_ledger')
    corpus = (
        "the algebra tower is primary. the world is secondary. "
        "noether conservation holds at every boundary. "
        "the two towers sing different themes into one music. "
    ) * 3
    for ep in range(3):
        loss, noether = txt.train_epoch(corpus, lr=0.005, max_steps=80)
        print(f"  Epoch {ep+1}: loss={loss:.4f}  noether={noether:.4f}")
    print(f"  Generated: {repr(txt.generate('the ', length=30))}")
    print(f"  {txt.status()}")
    print()

    # Image tower
    print("-- TF Image Tower --")
    img = TFImageNNTower(hidden_dim=32, n_classes=8,
                          ledger_path='/tmp/FA_tf_demo_ledger')
    tile = [[(x/7, y/7, 0.5) for y in range(8)] for x in range(8)]
    loss, noether = img.train_step(tile, target_class=3, tx=2, ty=2)
    print(f"  Tile step: loss={loss:.4f}  noether={noether:.4f}")
    print()

    # Combined
    print("-- TF Combined Tower (Two Themes -> One Music) --")
    comb = TFCombinedNNTower(hidden_dim=32, ctx_len=4,
                              ledger_path='/tmp/FA_tf_demo_ledger')
    print(f"  {comb.mastery_summary()}")
    print()

    # Blockchain
    led = BlockchainLedger('/tmp/FA_tf_demo_ledger')
    v,_,msg = led.verify()
    print(f"-- Blockchain: {msg} --")
    print()

    # Verify index is pure Python (demo: long context no overflow)
    seq = "the two towers" * 10
    ti, fi, dl = TextHyperIndex.index_record(seq)
    rec = TextHyperIndex.decode_text(ti, dl)
    print(f"-- Index demo: {dl} chars, {ti.bit_length()} bits "
          f"(pure Python, no TF int used) --")
    assert rec == seq, "Index round-trip failed"
    print(f"   Round-trip verified.")
    print()

    print("=" * 60)
    print("Done. Ledger: /tmp/FA_tf_demo_ledger.jsonl + .chain")


if __name__ == '__main__':
    run_demo()
