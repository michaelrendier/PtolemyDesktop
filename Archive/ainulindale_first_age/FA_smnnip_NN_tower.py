#!/usr/bin/env python3
"""
==============================================================================
FA_smnnip_NN_tower.py
SMNNIP Neural Network Tower -- Pure Python3 -- First Age
==============================================================================
Standard Model of Neural Network Information Propagation
FA_smnnip_NN_tower: The Neural Network Training Tower

Two independent substrates. One shared tower. One Music.

  TextSubstrate  (R, 97-char fixed vocab)
      -> CayleyDickson.include() -> hidden_dim
      |
  ImageSubstrate (R, 1 Oct group/tile, spherical CMYK)
      -> CayleyDickson.include() -> hidden_dim
      |
      +--------------------------+
             C layer  U(1)         <- both modalities arrive as same shape
             H layer  SU(2)
             O layer  G2/SU(3)     <- sedenion boundary enforced
             |
           Output

Corrected Ainulindale Lagrangian (Ainulindale_Conjecture_Revised.docx Apr 13):
  L_NN = (2/pi) oint [L_kin + L_mat + (1/phi)*L_bias + L_coup] dr dtheta

Running coupling (Ainulindale radial form):
  alpha_NN(r) = g^2 / (4*pi*hbar_NN*ln(1/r))
  Bridge to RG: ln(1/r) = ln(L/(L-l))

Mastery: weights crystallize when vev_distance < hbar_NN/2

Blockchain ledger records every training step and crystallization.

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

from FA_smnnip_hyperindex import (
    TextHyperIndex, ImageHyperIndex, MultiChannelTupper,
    SphericalColor, BlockchainLedger,
    layer_to_r, r_to_layer, alpha_nn_from_r, polar_lagrangian,
    assert_within_tower, SedenionBoundaryViolation,
    MASTERY_THRESHOLDS, US_KEYBOARD_CHARS, VOCAB_SIZE,
)

try:
    from smnnip_derivation_pure import RenormalizationGroup, Algebra
    _DERIV = True
except ImportError:
    _DERIV = False

try:
    from smnnip_lagrangian_pure import PhysicalConstants
    _LAG = True
except ImportError:
    _LAG = False

# ── Minimal math helpers ─────────────────────────────────────────────────────

def _dot(a, b):   return sum(x*y for x,y in zip(a,b))
def _norm(v):     return math.sqrt(sum(x*x for x in v))
def _clip(x, lo=-10.0, hi=10.0): return max(lo, min(hi, x))
def _zeros(n):    return [0.0]*n
def _matvec(M, v): return [_dot(row, v) for row in M]
def _relu(v):     return [max(0.0, x) for x in v]

def _softmax(v):
    m = max(v)
    e = [math.exp(x - m) for x in v]
    s = sum(e) + 1e-12
    return [x/s for x in e]

def _cross_entropy(probs, idx):
    return -math.log(max(probs[idx], 1e-12))

# ── Constants ────────────────────────────────────────────────────────────────

L_TOTAL      = 4
PHI          = (1.0 + math.sqrt(5.0)) / 2.0
BIAS_COUP    = 1.0 / PHI        # 0.6180... (1/phi, Ainulindale corrected)
TWO_OVER_PI  = 2.0 / math.pi   # 0.6366...

LNAME  = {0:'R', 1:'C', 2:'H', 3:'O'}
LGAUGE = {0:'trivial', 1:'U(1)', 2:'SU(2)', 3:'G2/SU(3)'}
LHBAR  = {0:0.10, 1:0.08, 2:0.05, 3:0.02}
LG     = {0:0.010, 1:0.009, 2:0.007, 3:0.005}
LMU    = {0:0.5,  1:0.5,  2:0.4,  3:0.3}
LLAM   = {0:0.10, 1:0.10, 2:0.12, 3:0.15}

# ==============================================================================
# MASTERED WEIGHT FIELD
# ==============================================================================

class MasteredWeightField:
    """Yang-Mills weight field with mastery crystallization."""

    def __init__(self, in_d, out_d, layer):
        self.in_d  = in_d
        self.out_d = out_d
        self.layer = layer
        self.hbar  = LHBAR[layer]
        self.g     = LG[layer]
        self.r     = layer_to_r(layer, L_TOTAL)
        self.alpha = alpha_nn_from_r(self.g, self.hbar, self.r)
        self._mastered  = False
        self._threshold = MASTERY_THRESHOLDS[LNAME[layer]]

        sc = math.sqrt(2.0 / (in_d + out_d))
        self.W  = [[random.gauss(0.0, sc) for _ in range(out_d)]
                   for _ in range(in_d)]
        self.dW = [[0.0]*out_d for _ in range(in_d)]

    def is_mastered(self):   return self._mastered
    def forward(self, psi):
        return [sum(self.W[j][i]*psi[j] for j in range(min(self.in_d,len(psi))))
                for i in range(self.out_d)]
    def field_strength(self):
        return math.sqrt(sum(w**2 for row in self.W for w in row))
    def noether(self, psi):  return self.g * _dot(psi, psi)

    def update(self, psi, grad, lr, mom=0.9):
        if self._mastered:
            gi = _zeros(self.in_d)
            for i in range(min(self.out_d, len(grad))):
                for j in range(self.in_d):
                    gi[j] += self.W[j][i] * grad[i]
            return gi
        gn = _norm(grad)
        sc = min(1.0, 1.0/(gn+1e-12)) if gn > 1.0 else 1.0
        gi = _zeros(self.in_d)
        for i in range(min(self.out_d, len(grad))):
            for j in range(min(self.in_d, len(psi))):
                dw = psi[j] * grad[i] * sc
                self.dW[j][i] = mom*self.dW[j][i] - lr*dw
                self.W[j][i]  = _clip(self.W[j][i] + self.dW[j][i])
                gi[j] += self.W[j][i] * grad[i]
        return gi

    def check_mastery(self, vev):
        if self._mastered: return True
        if abs(self.field_strength() - vev) < self._threshold:
            self._mastered = True
            self.dW = [[0.0]*self.out_d for _ in range(self.in_d)]
        return self._mastered

    def vev_dist(self, vev):
        return abs(self.field_strength() - vev)


# ==============================================================================
# MASTERED BIAS FIELD
# ==============================================================================

class MasteredBiasField:
    """Higgs bias field with (1/phi) polar correction and mastery."""

    def __init__(self, size, layer, mu_sq, lam):
        self.size  = size
        self.layer = layer
        self.mu_sq = mu_sq
        self.lam   = lam
        self.vev   = math.sqrt(mu_sq/(2.0*lam)) if mu_sq > 0 else 0.0
        self._mastered  = False
        self._threshold = MASTERY_THRESHOLDS[LNAME[layer]]
        self.beta = [random.gauss(0.0, 0.01) for _ in range(size)]
        self.vel  = _zeros(size)

    def is_mastered(self):  return self._mastered
    def apply(self, psi):
        return [psi[i] + self.beta[i] for i in range(min(len(psi), self.size))]

    def potential(self):
        b2 = sum(b*b for b in self.beta)
        return -self.mu_sq*b2 + self.lam*b2*b2

    def polar_l_bias(self):
        """L_bias with (1/phi) Ainulindale correction."""
        return BIAS_COUP * self.potential()

    def vev_dist(self):
        return abs(math.sqrt(sum(b*b for b in self.beta)) - self.vev)

    def update(self, overlap, lr, mom=0.9):
        if self._mastered: return
        b2 = sum(b*b for b in self.beta)
        for i in range(self.size):
            dV    = (-2.0*self.mu_sq + 4.0*self.lam*b2) * self.beta[i]
            drive = -overlap[i] if i < len(overlap) else 0.0
            self.vel[i]  = mom*self.vel[i] - lr*(dV+drive)
            self.beta[i] = _clip(self.beta[i] + self.vel[i])

    def check_mastery(self):
        if self._mastered: return True
        if self.vev_dist() < self._threshold:
            self._mastered = True
            self.vel = _zeros(self.size)
        return self._mastered


# ==============================================================================
# TEXT SUBSTRATE
# ==============================================================================

class TextSubstrate:
    """Layer 0: US keyboard 97-char fixed vocab -> hidden_dim."""

    def __init__(self, hidden_dim, ctx_len):
        self.vocab_size = VOCAB_SIZE
        self.hidden_dim = hidden_dim
        self.ctx_len    = ctx_len
        self.in_dim     = VOCAB_SIZE * ctx_len
        self.r          = layer_to_r(0, L_TOTAL)  # r=1.0

        self._c2i = {c: i for i, c in enumerate(US_KEYBOARD_CHARS)}
        self._i2c = {i: c for i, c in enumerate(US_KEYBOARD_CHARS)}

        self.W = MasteredWeightField(self.in_dim, hidden_dim, 0)
        self.B = MasteredBiasField(hidden_dim, 0, LMU[0], LLAM[0])

    def one_hot(self, c):
        v = _zeros(self.vocab_size)
        if c in self._c2i: v[self._c2i[c]] = 1.0
        return v

    def encode(self, ctx):
        flat = []
        for c in ctx[-self.ctx_len:]:
            flat.extend(self.one_hot(c))
        while len(flat) < self.in_dim: flat.append(0.0)
        return flat[:self.in_dim]

    def forward(self, ctx):
        psi = self.encode(ctx)
        out = self.W.forward(psi)
        out = self.B.apply(out)
        out = _relu(out)
        L_kin  = -0.25 * self.W.field_strength()**2
        J      = self.W.noether(psi)
        return out, L_kin, J

    def backward(self, ctx, grad, lr):
        psi = self.encode(ctx)
        gi  = self.W.update(psi, grad, lr)
        self.B.update(grad, lr)
        wm = self.W.check_mastery(self.B.vev)
        bm = self.B.check_mastery()
        return gi, wm, bm

    def hyperindex(self, ctx):
        return TextHyperIndex.index_record(ctx)


# ==============================================================================
# IMAGE SUBSTRATE
# ==============================================================================

class ImageSubstrate:
    """Layer 0: 8x8 RGB tile -> spherical CMYK Oct -> hidden_dim."""

    def __init__(self, hidden_dim, tile=8, img_w=8, img_h=8):
        self.tile    = tile
        self.in_dim  = tile * tile * 8
        self.hidden_dim = hidden_dim
        self.img_w   = img_w
        self.img_h   = img_h

        self.W = MasteredWeightField(self.in_dim, hidden_dim, 0)
        self.B = MasteredBiasField(hidden_dim, 0, LMU[0], LLAM[0])

    def encode(self, rgb_tile, depth=0.0, conf=0.0):
        flat = []
        for x in range(self.tile):
            for y in range(self.tile):
                try:   rv,gv,bv = rgb_tile[x][y]
                except: rv,gv,bv = 0.0,0.0,0.0
                flat.extend(SphericalColor.to_octonion(rv,gv,bv,depth,conf))
        while len(flat) < self.in_dim: flat.append(0.0)
        return flat[:self.in_dim]

    def forward(self, rgb_tile, depth=0.0, conf=0.0):
        psi = self.encode(rgb_tile, depth, conf)
        out = self.W.forward(psi)
        out = self.B.apply(out)
        out = _relu(out)
        L_kin = -0.25 * self.W.field_strength()**2
        J     = self.W.noether(psi)
        return out, L_kin, J

    def backward(self, rgb_tile, grad, lr, depth=0.0, conf=0.0):
        psi = self.encode(rgb_tile, depth, conf)
        gi  = self.W.update(psi, grad, lr)
        self.B.update(grad, lr)
        wm = self.W.check_mastery(self.B.vev)
        bm = self.B.check_mastery()
        return gi, wm, bm

    def tile_r(self, tx, ty):
        return ImageHyperIndex.tile_radial_r(tx, ty, self.img_w, self.img_h)

    def hyperindex(self, rgb_tile, tx=0, ty=0, depth=0.0, conf=0.0):
        return ImageHyperIndex.index_record(
            rgb_tile, tx, ty, self.img_w, self.img_h, depth, conf)


# ==============================================================================
# SHARED UPPER TOWER (C -> H -> O)
# ==============================================================================

class SharedUpperTower:
    """
    Shared C->H->O tower. Receives from either substrate.
    By layer C the modality is forgotten -- one Music.
    Sedenion boundary enforced at O (index 3).
    """

    def __init__(self, hidden_dim, output_dim):
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        assert_within_tower(1)
        assert_within_tower(2)
        assert_within_tower(3)

        self.W1 = MasteredWeightField(hidden_dim, hidden_dim, 1)
        self.B1 = MasteredBiasField(hidden_dim, 1, LMU[1], LLAM[1])
        self.W2 = MasteredWeightField(hidden_dim, hidden_dim, 2)
        self.B2 = MasteredBiasField(hidden_dim, 2, LMU[2], LLAM[2])
        self.W3 = MasteredWeightField(hidden_dim, output_dim, 3)
        self.B3 = MasteredBiasField(output_dim, 3, LMU[3], LLAM[3])

        self.noether_hist:    List[float] = []
        self.lagrangian_hist: List[float] = []

    def _fwd(self, psi, W, B, layer):
        assert_within_tower(layer)
        out   = W.forward(psi)
        out   = B.apply(out)
        out   = _relu(out)
        L_kin = -0.25 * W.field_strength()**2
        L_mat = _dot(psi, psi) * 0.1
        L_b   = B.polar_l_bias()
        L_c   = -W.g * _dot(psi, psi)
        L_p   = polar_lagrangian(L_kin, L_mat, L_b, L_c,
                                  layer=layer, L_total=L_TOTAL)
        J     = W.noether(psi)
        return out, L_p, J

    def forward(self, sub_out):
        p, L1, J1 = self._fwd(sub_out, self.W1, self.B1, 1)
        p, L2, J2 = self._fwd(p, self.W2, self.B2, 2)
        p, L3, J3 = self._fwd(p, self.W3, self.B3, 3)
        L_tot = L1 + L2 + L3
        viol  = (abs(J2-J1) + abs(J3-J2)) / 2.0
        self.noether_hist.append(viol)
        self.lagrangian_hist.append(L_tot)
        return p, L_tot, viol

    def backward(self, grad, lr, sub_out):
        hd = self.hidden_dim
        g3 = self.W3.update(sub_out[:hd], grad, lr)
        self.B3.update(grad, lr)
        g2 = self.W2.update(sub_out[:hd], g3[:hd], lr)
        self.B2.update(g3[:hd], lr)
        g1 = self.W1.update(sub_out[:hd], g2[:hd], lr)
        self.B1.update(g2[:hd], lr)
        mastery = {
            'W1': self.W1.check_mastery(self.B1.vev),
            'B1': self.B1.check_mastery(),
            'W2': self.W2.check_mastery(self.B2.vev),
            'B2': self.B2.check_mastery(),
            'W3': self.W3.check_mastery(self.B3.vev),
            'B3': self.B3.check_mastery(),
        }
        return g1, mastery

    def mastered(self):
        return sum(1 for f in
                   [self.W1,self.B1,self.W2,self.B2,self.W3,self.B3]
                   if f.is_mastered())


# ==============================================================================
# TEXT NN TOWER
# ==============================================================================

class FATextNNTower:
    """TextSubstrate -> SharedUpperTower -> softmax."""

    def __init__(self, hidden_dim=64, ctx_len=8,
                 ledger_path='FA_hyperindex_ledger'):
        self.ctx_len    = ctx_len
        self.hidden_dim = hidden_dim
        self.out_dim    = VOCAB_SIZE
        self.substrate  = TextSubstrate(hidden_dim, ctx_len)
        self.tower      = SharedUpperTower(hidden_dim, VOCAB_SIZE)
        self.ledger     = BlockchainLedger(ledger_path)
        self._c2i       = {c:i for i,c in enumerate(US_KEYBOARD_CHARS)}
        self._i2c       = {i:c for i,c in enumerate(US_KEYBOARD_CHARS)}
        self.loss_hist: List[float] = []
        self._epoch = 0; self._step = 0

    def forward(self, ctx):
        s,_,_ = self.substrate.forward(ctx)
        l,_,_ = self.tower.forward(s)
        return _softmax(l)

    def train_step(self, ctx, target, lr=0.005):
        s, Ls, Js = self.substrate.forward(ctx)
        l, Lt, Jt = self.tower.forward(s)
        probs     = _softmax(l)
        ti        = self._c2i.get(target, 0)
        loss      = _cross_entropy(probs, ti)
        noether   = (Js + Jt) / 2.0

        grad  = [p-(1.0 if i==ti else 0.0) for i,p in enumerate(probs)]
        gs, m = self.tower.backward(grad, lr, s)
        self.substrate.backward(ctx, gs[:self.hidden_dim], lr)

        ti_txt, fi, dl = self.substrate.hyperindex(ctx)
        self.ledger.append('text', self._epoch, self._step,
                           ti_txt, dl, LNAME[0], noether,
                           any(m.values()),
                           {'fano':str(fi), 'loss':loss})
        self.loss_hist.append(loss)
        self._step += 1
        return loss, noether

    def train_epoch(self, text, lr=0.005, max_steps=500):
        valid  = [(i, text[i:i+self.ctx_len], text[i+self.ctx_len])
                  for i in range(len(text)-self.ctx_len-1)
                  if text[i+self.ctx_len] in self._c2i]
        random.shuffle(valid)
        valid = valid[:max_steps]
        tl = tn = 0.0
        for _, ctx, tgt in valid:
            ctx = ''.join(c if c in self._c2i else ' ' for c in ctx)
            l, n = self.train_step(ctx, tgt, lr)
            tl += l; tn += n
        self._epoch += 1
        n = max(1, len(valid))
        return tl/n, tn/n

    def generate(self, seed, length=100, temp=1.0):
        ctx = seed[-self.ctx_len:]
        ctx = ''.join(c if c in self._c2i else ' ' for c in ctx)
        out = seed
        for _ in range(length):
            p = self.forward(ctx)
            if temp != 1.0:
                p = _softmax([math.log(x+1e-12)/temp for x in p])
            rv = random.random(); cu = 0.0; ch = 0
            for i, pv in enumerate(p):
                cu += pv
                if rv < cu: ch = i; break
            c  = self._i2c.get(ch, '?')
            out += c
            ctx = (ctx + c)[-self.ctx_len:]
        return out

    def status(self):
        v,_,msg = self.ledger.verify()
        return (f"Mastery: tower {self.tower.mastered()}/6 "
                f"| steps={self._step} | chain={msg[:30]}")


# ==============================================================================
# IMAGE NN TOWER
# ==============================================================================

class FAImageNNTower:
    """ImageSubstrate -> SharedUpperTower -> class output."""

    def __init__(self, hidden_dim=64, n_classes=16, tile=8,
                 img_w=8, img_h=8,
                 ledger_path='FA_hyperindex_ledger'):
        self.hidden_dim = hidden_dim
        self.n_classes  = n_classes
        self.substrate  = ImageSubstrate(hidden_dim, tile, img_w, img_h)
        self.tower      = SharedUpperTower(hidden_dim, n_classes)
        self.ledger     = BlockchainLedger(ledger_path)
        self._epoch = 0; self._step = 0

    def forward(self, rgb_tile, depth=0.0, conf=0.0):
        s,_,_ = self.substrate.forward(rgb_tile, depth, conf)
        l,_,_ = self.tower.forward(s)
        return _softmax(l)

    def train_step(self, rgb_tile, target_class, lr=0.005,
                   tx=0, ty=0, depth=0.0, conf=0.0):
        s, Ls, Js = self.substrate.forward(rgb_tile, depth, conf)
        l, Lt, Jt = self.tower.forward(s)
        probs     = _softmax(l)
        loss      = _cross_entropy(probs, target_class)
        noether   = (Js + Jt) / 2.0

        grad  = [p-(1.0 if i==target_class else 0.0)
                 for i,p in enumerate(probs)]
        gs, m = self.tower.backward(grad, lr, s)
        self.substrate.backward(rgb_tile, gs[:self.hidden_dim],
                                lr, depth, conf)

        idx = self.substrate.hyperindex(rgb_tile, tx, ty, depth, conf)
        self.ledger.append('image', self._epoch, self._step,
                           idx.get('k_C','0'),
                           self.substrate.tile**2,
                           LNAME[0], noether, any(m.values()),
                           {'color':idx.get('color_index','0'),
                            'r':idx.get('radial_r',0.0),
                            'loss':loss})
        self._step += 1
        return loss, noether


# ==============================================================================
# COMBINED TOWER (BOTH SUBSTRATES -> ONE SHARED TOWER)
# ==============================================================================

class FACombinedNNTower:
    """
    The Two Towers -- one shared upper tower, two independent substrates.

    TextSubstrate  --> |
                       +--> SharedUpperTower --> output
    ImageSubstrate --> |

    Independent themes. One Music.
    """

    def __init__(self, hidden_dim=64, ctx_len=8, n_classes=16,
                 ledger_path='FA_hyperindex_ledger'):
        out_dim = max(VOCAB_SIZE, n_classes)
        self.text_sub  = TextSubstrate(hidden_dim, ctx_len)
        self.img_sub   = ImageSubstrate(hidden_dim)
        self.tower     = SharedUpperTower(hidden_dim, out_dim)
        self.ledger    = BlockchainLedger(ledger_path)
        self._c2i      = {c:i for i,c in enumerate(US_KEYBOARD_CHARS)}
        self._i2c      = {i:c for i,c in enumerate(US_KEYBOARD_CHARS)}

    def forward_text(self, ctx):
        s,_,_ = self.text_sub.forward(ctx)
        l,_,_ = self.tower.forward(s)
        return _softmax(l[:VOCAB_SIZE])

    def forward_image(self, rgb_tile, depth=0.0, conf=0.0):
        s,_,_ = self.img_sub.forward(rgb_tile, depth, conf)
        l,_,_ = self.tower.forward(s)
        return _softmax(l)

    def mastery_summary(self):
        v,_,msg = self.ledger.verify()
        return {
            'tower_mastered': self.tower.mastered(),
            'text_W': self.text_sub.W.is_mastered(),
            'text_B': self.text_sub.B.is_mastered(),
            'img_W':  self.img_sub.W.is_mastered(),
            'img_B':  self.img_sub.B.is_mastered(),
            'chain':  v,
            'blocks': self.ledger._block_id,
        }


# ==============================================================================
# DEMO
# ==============================================================================

def run_demo():
    print("FA_smnnip_NN_tower -- Pure Python3 -- First Age")
    print("=" * 60)
    print(f"Lagrangian: (2/pi)*oint[L_kin + L_mat + (1/phi)*L_bias + L_coup]")
    print(f"phi = {PHI:.6f}   1/phi = {BIAS_COUP:.6f}")
    print(f"Radial: r(layer=0)={layer_to_r(0):.2f}  r(layer=3)={layer_to_r(3):.2f}")
    print()

    # Text tower
    print("-- Text Tower --")
    txt = FATextNNTower(hidden_dim=32, ctx_len=4,
                         ledger_path='/tmp/FA_demo_ledger')
    corpus = (
        "the algebra tower is primary. the world is secondary. "
        "noether conservation holds at every boundary. "
        "permutations are the discrete skeleton of rotations. "
        "the two towers sing different themes into one music. "
    ) * 3
    for ep in range(3):
        loss, noether = txt.train_epoch(corpus, lr=0.005, max_steps=80)
        print(f"  Epoch {ep+1}: loss={loss:.4f}  noether={noether:.4f}")
    print(f"  Generated: {repr(txt.generate('the ', length=30))}")
    print(f"  {txt.status()}")
    print()

    # Image tower
    print("-- Image Tower --")
    img = FAImageNNTower(hidden_dim=32, n_classes=8,
                          ledger_path='/tmp/FA_demo_ledger')
    tile = [[(x/7, y/7, 0.5) for y in range(8)] for x in range(8)]
    loss, noether = img.train_step(tile, target_class=3, tx=2, ty=2)
    th, ph, sa, ro = SphericalColor.rgb_to_spherical(0.5, 0.5, 0.5)
    print(f"  Tile step: loss={loss:.4f}  noether={noether:.4f}")
    print(f"  Center pixel: theta={th:.3f} phi={ph:.3f} "
          f"sat={sa:.3f} lum={ro:.3f}")
    print()

    # Combined
    print("-- Combined Tower (Two Themes -> One Music) --")
    comb = FACombinedNNTower(hidden_dim=32, ctx_len=4,
                              ledger_path='/tmp/FA_demo_ledger')
    print(f"  {comb.mastery_summary()}")
    print()

    # Blockchain
    print("-- Blockchain Verify --")
    led = BlockchainLedger('/tmp/FA_demo_ledger')
    v, _, msg = led.verify()
    print(f"  {msg}")
    print()

    # Hyperindex
    print("-- Hyperindex --")
    seq = "the "
    ti, fi, dl = TextHyperIndex.index_record(seq)
    rec = TextHyperIndex.decode_text(ti, dl)
    print(f"  '{seq}' -> text_idx={ti} ({ti.bit_length()} bits) "
          f"fano={fi} -> '{rec}'")
    k  = MultiChannelTupper.encode_tile(
         [[[0.25*c for _ in range(8)] for _ in range(8)]
          for c in range(4)])
    print(f"  Tupper k_C={str(k[0])[:18]}... ({k[0].bit_length()} bits)")
    print()

    print("=" * 60)
    print("Done. Ledger: /tmp/FA_demo_ledger.jsonl + .chain")


if __name__ == '__main__':
    run_demo()
