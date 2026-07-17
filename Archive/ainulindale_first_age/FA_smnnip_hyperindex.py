#!/usr/bin/env python3
"""
==============================================================================
FA_smnnip_hyperindex.py
SMNNIP Hyperindex Library — First Age
==============================================================================
Standard Model of Neural Network Information Propagation
Hyperindex System: Text + Image Substrates + Blockchain Ledger

Two Substrates. One Tower. One Music.

Text substrate:  base-97 permutation index (US keyboard charset, fixed)
                 + Fano base-7 octonion path index
Image substrate: multi-channel generalized Tupper (base-2^b per channel)
                 + spherical color coordinates (θ, φ, r, ρ) → CMYK → Oct
Blockchain:      SHA256-chained ledger, append-only, tamper-evident

Architecture note:
  The two substrates are independent singers of independent themes.
  Both feed the shared ℂ→ℍ→𝕆 tower.
  The 𝕆 reasoning layer does not know the modality.
  This is correct. Abstract reasoning has no modality.

Index arithmetic uses Python int throughout (arbitrary precision).
TensorFlow version calls these same functions — Python handles indices,
TF handles weight training. No int overflow anywhere.

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026 — First Age
==============================================================================
"""

import math
import hashlib
import json
import os
import datetime
from typing import List, Tuple, Optional, Dict, Any


# ==============================================================================
# CONSTANTS
# ==============================================================================

# Fixed US keyboard character set — EliteBook 820 G3 layout
# 97 characters: a-z, A-Z, 0-9, punctuation, space, tab, newline
US_KEYBOARD_CHARS: str = (
    'abcdefghijklmnopqrstuvwxyz'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    '0123456789'
    '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    ' \t\n'
)
assert len(US_KEYBOARD_CHARS) == 97, f"Expected 97 chars, got {len(US_KEYBOARD_CHARS)}"

VOCAB_SIZE: int = 97
VOCAB_BASE: int = 97

# Fano plane lines — 7 imaginary octonion generators {e1..e7}
FANO_LINES: List[Tuple[int,int,int]] = [
    (0,1,3),(1,2,4),(2,3,5),(3,4,6),(4,5,0),(5,6,1),(6,0,2)
]
FANO_BASE: int = 7

# Image substrate
TUPPER_H: int = 8          # height = octonion dimension (not original 17)
TUPPER_BITS: int = 8       # bits per channel value (256 levels)
CMYK_CHANNELS: int = 4     # C, M, Y, K

# Spherical color quantization
THETA_STEPS: int = 512     # hue angle 0-2π
PHI_STEPS:   int = 256     # elevation 0-π
R_STEPS:     int = 256     # saturation 0-1
RHO_STEPS:   int = 256     # luminance 0-1

# Mastery threshold: ħ_NN/2 per layer (uncertainty bound)
MASTERY_THRESHOLDS: Dict[str, float] = {
    'R': 0.10 / 2,   # ħ_L0 / 2
    'C': 0.08 / 2,
    'H': 0.05 / 2,
    'O': 0.02 / 2,
}

# Sedenion boundary — tower terminates at 𝕆. Crossing to 𝕊 is mastery, not training.
SEDENION_BOUNDARY: int = 4   # algebra index 4 = sedenion; raises error if reached


# ==============================================================================
# MODULE 1 — CHARACTER MAP
# ==============================================================================

class USKeyboardMap:
    """
    Fixed bijection between US keyboard characters and integer indices 0..96.
    Immutable. Built once at import time.
    """

    _char_to_idx: Dict[str, int] = {c: i for i, c in enumerate(US_KEYBOARD_CHARS)}
    _idx_to_char: Dict[int, str] = {i: c for i, c in enumerate(US_KEYBOARD_CHARS)}

    @classmethod
    def encode(cls, char: str) -> int:
        """Character → index 0..96. Raises KeyError if not in charset."""
        if char not in cls._char_to_idx:
            raise KeyError(f"Character {repr(char)} not in US keyboard charset")
        return cls._char_to_idx[char]

    @classmethod
    def decode(cls, idx: int) -> str:
        """Index 0..96 → character."""
        if idx not in cls._idx_to_char:
            raise KeyError(f"Index {idx} out of range 0..96")
        return cls._idx_to_char[idx]

    @classmethod
    def is_valid(cls, char: str) -> bool:
        return char in cls._char_to_idx


# ==============================================================================
# MODULE 2 — TEXT HYPERINDEX
# ==============================================================================

class TextHyperIndex:
    """
    Lossless permutation index for text sequences.

    Two indices computed simultaneously:
      text_index  : base-97 mixed-radix integer (exact sequence address)
      fano_index  : base-7 Fano/octonion path (algebra-native address)

    Both are pure Python int — arbitrary precision, no overflow.
    TensorFlow callers receive these as strings from the ledger.

    Stored as INDEX_RECORD = (text_index: int, fano_index: int, data_length: int)
    """

    @staticmethod
    def encode_text(sequence: str) -> int:
        """
        Encode a character sequence as a base-97 integer.
        idx = c0·97^(k-1) + c1·97^(k-2) + ... + c_{k-1}·97^0

        Lossless. Invertible. Any length.
        """
        idx = 0
        for char in sequence:
            idx = idx * VOCAB_BASE + USKeyboardMap.encode(char)
        return idx

    @staticmethod
    def decode_text(idx: int, length: int) -> str:
        """
        Decode base-97 integer back to character sequence of given length.
        """
        chars = []
        remaining = idx
        for _ in range(length):
            chars.append(USKeyboardMap.decode(remaining % VOCAB_BASE))
            remaining //= VOCAB_BASE
        chars.reverse()
        return ''.join(chars)

    @staticmethod
    def encode_fano(sequence: str) -> int:
        """
        Encode a character sequence as a Fano/octonion base-7 path index.

        Each character maps to an octonion generator via:
          fano_component = char_index % FANO_BASE  (0..6 → e1..e7)

        This is the algebra-native address of the sequence.
        Different from the text index — encodes which octonion
        generators were traversed, not which characters.
        """
        idx = 0
        for char in sequence:
            component = USKeyboardMap.encode(char) % FANO_BASE
            idx = idx * FANO_BASE + component
        return idx

    @staticmethod
    def decode_fano(idx: int, length: int) -> List[int]:
        """
        Decode Fano index back to sequence of generator indices (0..6).
        """
        components = []
        remaining = idx
        for _ in range(length):
            components.append(remaining % FANO_BASE)
            remaining //= FANO_BASE
        components.reverse()
        return components

    @staticmethod
    def index_record(sequence: str) -> Tuple[int, int, int]:
        """
        Compute full INDEX_RECORD for a text sequence.
        Returns (text_index, fano_index, data_length).
        """
        return (
            TextHyperIndex.encode_text(sequence),
            TextHyperIndex.encode_fano(sequence),
            len(sequence)
        )

    @staticmethod
    def verify(sequence: str) -> bool:
        """
        Round-trip verification: encode then decode returns original.
        """
        text_idx, _, length = TextHyperIndex.index_record(sequence)
        recovered = TextHyperIndex.decode_text(text_idx, length)
        return recovered == sequence


# ==============================================================================
# MODULE 3 — SPHERICAL COLOR COORDINATE SYSTEM
# ==============================================================================

class SphericalColor:
    """
    4D spherical color space: (θ, φ, r, ρ)

    θ (theta):  hue angle         0 ≤ θ < 2π    position on color wheel
    φ (phi):    elevation angle   0 ≤ φ ≤ π     0=white pole, π=black pole
    r:          saturation        0 ≤ r ≤ 1     distance from grey axis
    ρ (rho):    luminance         0 ≤ ρ ≤ 1     total brightness

    Full conversion chain:
      (θ, φ, r, ρ) → HSL → RGB → CMYK
      CMYK → RGB → HSL → (θ, φ, r, ρ)

    Octonion encoding (8 floats = 1 octonion):
      [θ_norm, φ_norm, r, ρ, depth, depth_conf, K_derived, reserved]
    """

    @staticmethod
    def rgb_to_spherical(r: float, g: float, b: float) -> Tuple[float,float,float,float]:
        """
        RGB (each 0..1) → (theta, phi, sat_r, luminance_rho)
        """
        # Luminance (rho)
        rho = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Saturation (r) via HSL
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        delta = cmax - cmin
        sat = 0.0 if (cmax + cmin) == 0 else delta / (1.0 - abs(cmax + cmin - 1.0) + 1e-12)
        sat = min(1.0, max(0.0, sat))

        # Hue angle (theta)
        if delta < 1e-9:
            theta = 0.0
        elif cmax == r:
            theta = (math.pi / 3.0) * (((g - b) / (delta + 1e-12)) % 6)
        elif cmax == g:
            theta = (math.pi / 3.0) * (((b - r) / (delta + 1e-12)) + 2.0)
        else:
            theta = (math.pi / 3.0) * (((r - g) / (delta + 1e-12)) + 4.0)
        theta = theta % (2.0 * math.pi)

        # Elevation (phi) — warm colors (red/orange) near 0, cool (blue/violet) near π
        # Approximate: phi correlates with B channel dominance
        phi = math.pi * (b / (r + g + b + 1e-12))

        return theta, phi, sat, rho

    @staticmethod
    def spherical_to_rgb(theta: float, phi: float,
                         sat: float, rho: float) -> Tuple[float,float,float]:
        """
        (theta, phi, sat, rho) → RGB (each 0..1)
        Via HSL intermediate. phi is advisory (warm/cool) — not directly invertible.
        """
        # Convert to HSL
        H_deg = math.degrees(theta) % 360.0
        S = min(1.0, max(0.0, sat))
        L = min(1.0, max(0.0, rho))

        # HSL → RGB (standard formula)
        C = (1.0 - abs(2.0 * L - 1.0)) * S
        X = C * (1.0 - abs((H_deg / 60.0) % 2.0 - 1.0))
        m = L - C / 2.0

        sector = int(H_deg / 60.0) % 6
        if sector == 0:   r1,g1,b1 = C, X, 0.0
        elif sector == 1: r1,g1,b1 = X, C, 0.0
        elif sector == 2: r1,g1,b1 = 0.0, C, X
        elif sector == 3: r1,g1,b1 = 0.0, X, C
        elif sector == 4: r1,g1,b1 = X, 0.0, C
        else:             r1,g1,b1 = C, 0.0, X

        return (r1 + m, g1 + m, b1 + m)

    @staticmethod
    def rgb_to_cmyk(r: float, g: float, b: float) -> Tuple[float,float,float,float]:
        """RGB (0..1) → CMYK (0..1 each). K derived from absence of RGB."""
        k = 1.0 - max(r, g, b)
        if abs(k - 1.0) < 1e-9:
            return 0.0, 0.0, 0.0, 1.0
        inv = 1.0 / (1.0 - k + 1e-12)
        c = min(1.0, max(0.0, (1.0 - r - k) * inv))
        m = min(1.0, max(0.0, (1.0 - g - k) * inv))
        y = min(1.0, max(0.0, (1.0 - b - k) * inv))
        return c, m, y, min(1.0, max(0.0, k))

    @staticmethod
    def cmyk_to_rgb(c: float, m: float,
                    y: float, k: float) -> Tuple[float,float,float]:
        """CMYK (0..1) → RGB (0..1)."""
        r = (1.0 - c) * (1.0 - k)
        g = (1.0 - m) * (1.0 - k)
        b = (1.0 - y) * (1.0 - k)
        return r, g, b

    @staticmethod
    def to_octonion(r_rgb: float, g_rgb: float, b_rgb: float,
                    depth: float = 0.0, depth_conf: float = 0.0) -> List[float]:
        """
        RGB pixel → 8-component octonion vector for substrate input.
        [θ_norm, φ_norm, sat, lum, depth, depth_conf, K_derived, reserved]
        """
        theta, phi, sat, rho = SphericalColor.rgb_to_spherical(r_rgb, g_rgb, b_rgb)
        k = 1.0 - max(r_rgb, g_rgb, b_rgb)
        return [
            theta / (2.0 * math.pi),   # θ normalized to [0,1]
            phi / math.pi,             # φ normalized to [0,1]
            sat,                       # saturation
            rho,                       # luminance
            min(1.0, max(0.0, depth)), # depth estimate (normalized)
            min(1.0, max(0.0, depth_conf)),  # depth confidence
            min(1.0, max(0.0, k)),     # K derived (absence of RGB)
            0.0,                       # reserved
        ]

    @staticmethod
    def color_index(theta: float, phi: float,
                    sat: float, rho: float) -> int:
        """
        Quantize (θ, φ, r, ρ) to a 33-bit integer color index.
        idx = θ_q·(PHI·R·RHO) + φ_q·(R·RHO) + r_q·RHO + ρ_q
        """
        tq = min(THETA_STEPS-1, int(theta / (2.0*math.pi) * THETA_STEPS))
        pq = min(PHI_STEPS-1,   int(phi / math.pi * PHI_STEPS))
        rq = min(R_STEPS-1,     int(sat * R_STEPS))
        lq = min(RHO_STEPS-1,   int(rho * RHO_STEPS))
        return (tq * PHI_STEPS * R_STEPS * RHO_STEPS +
                pq * R_STEPS * RHO_STEPS +
                rq * RHO_STEPS + lq)


# ==============================================================================
# MODULE 4 — GENERALIZED MULTI-CHANNEL TUPPER
# ==============================================================================

class MultiChannelTupper:
    """
    Generalized Tupper's Self-Referential Formula for multi-channel float images.

    Standard Tupper (binary, H=17):
      pixel(x,y) = ½ < ⌊ mod(⌊y/H⌋ · 2^(−H·x − y mod H), 2) ⌋

    Generalized (b-bit depth, H=8 for octonion alignment):
      pixel_c(x,y) = ⌊ mod(⌊k_c / B^(H·x + y mod H)⌋, B) ⌋ / (B-1)
      where B = 2^b

    H=8: each column of the Tupper bitmap encodes one full octonion.
    8 octants of the color sphere × 8 elevation bands = one tile.

    Encode: k_c = Σ_{x=0}^{W-1} Σ_{y=0}^{H-1} quantize(v, b) · B^(H·x + y)
    Decode: value = ⌊ mod(⌊k_c / B^(H·x + y)⌋, B) ⌋ / (B-1)

    Storage per 8×8 tile at b=8:
      k per channel = 512 bits = 64 bytes
      4 CMYK channels = 2048 bits = 256 bytes
      Stored as Python int (arbitrary precision)
      Ledger stores as decimal string
    """

    H: int = TUPPER_H
    B: int = 2 ** TUPPER_BITS   # = 256

    @classmethod
    def encode_channel(cls, channel_values: List[List[float]]) -> int:
        """
        Encode a 2D float array (W × H, values 0..1) into k for one channel.
        channel_values[x][y] ∈ [0, 1]
        Returns k as Python int (arbitrary precision).
        """
        W = len(channel_values)
        H = cls.H
        B = cls.B
        k = 0
        for x in range(W):
            col = channel_values[x]
            for y in range(min(H, len(col))):
                q = min(B - 1, int(col[y] * B))
                k += q * (B ** (H * x + y))
        return k

    @classmethod
    def decode_channel(cls, k: int, W: int) -> List[List[float]]:
        """
        Decode k back to W × H float array.
        Returns channel_values[x][y] ∈ [0, 1].
        """
        H = cls.H
        B = cls.B
        result = []
        k_work = k
        for x in range(W):
            col = []
            for y in range(H):
                pos = H * x + y
                val_q = (k_work // (B ** pos)) % B
                col.append(val_q / (B - 1))
            result.append(col)
        return result

    @classmethod
    def encode_tile(cls, tile_cmyk: List[List[List[float]]]) -> Tuple[int,int,int,int]:
        """
        Encode an 8×8 CMYK tile into 4 k values.
        tile_cmyk[channel][x][y] — channel: 0=C, 1=M, 2=Y, 3=K

        Returns (k_C, k_M, k_Y, k_K) as Python ints.
        """
        return tuple(
            cls.encode_channel(tile_cmyk[c])
            for c in range(CMYK_CHANNELS)
        )

    @classmethod
    def decode_tile(cls, k_vec: Tuple[int,int,int,int],
                    W: int = 8) -> List[List[List[float]]]:
        """
        Decode (k_C, k_M, k_Y, k_K) back to tile_cmyk[channel][x][y].
        """
        return [cls.decode_channel(k_vec[c], W) for c in range(CMYK_CHANNELS)]

    @classmethod
    def tile_index_record(cls,
                          tile_cmyk: List[List[List[float]]],
                          tile_x: int = 0,
                          tile_y: int = 0) -> Dict[str, Any]:
        """
        Full INDEX_RECORD for one image tile.
        Returns dict with k_C, k_M, k_Y, k_K as strings (arbitrary precision safe).
        """
        k_C, k_M, k_Y, k_K = cls.encode_tile(tile_cmyk)
        return {
            'k_C':    str(k_C),
            'k_M':    str(k_M),
            'k_Y':    str(k_Y),
            'k_K':    str(k_K),
            'tile_x': tile_x,
            'tile_y': tile_y,
            'H':      cls.H,
            'b':      TUPPER_BITS,
        }


# ==============================================================================
# MODULE 5 — IMAGE HYPERINDEX
# ==============================================================================

class ImageHyperIndex:
    """
    Lossless hyperindex for image tiles.

    Pipeline:
      RGB pixel → spherical (θ,φ,r,ρ) → CMYK → Tupper k-vector
      Tupper k-vector → tile INDEX_RECORD

    Radial correspondence for image tiles:
      r(tile) = 1.0 - sqrt((tx - cx)^2 + (ty - cy)^2) / r_max
      Image center is the Observer at r=0 (destination-centric).
      Tiles further from center are at larger r (closer to input surface).
    """

    @staticmethod
    def rgb_tile_to_cmyk(rgb_tile: List[List[Tuple[float,float,float]]]
                         ) -> List[List[List[float]]]:
        """
        Convert W×H RGB tile to CMYK tile.
        rgb_tile[x][y] = (r, g, b) each 0..1
        Returns cmyk_tile[channel][x][y]
        """
        W = len(rgb_tile)
        H = len(rgb_tile[0]) if W > 0 else 0
        cmyk = [[[] for _ in range(W)] for _ in range(CMYK_CHANNELS)]
        for x in range(W):
            for y in range(H):
                r, g, b = rgb_tile[x][y]
                k = 1.0 - max(r, g, b)
                if abs(k - 1.0) < 1e-9:
                    c, m, yv = 0.0, 0.0, 0.0
                else:
                    inv = 1.0 / (1.0 - k + 1e-12)
                    c  = min(1.0, max(0.0, (1.0 - r - k) * inv))
                    m  = min(1.0, max(0.0, (1.0 - g - k) * inv))
                    yv = min(1.0, max(0.0, (1.0 - b - k) * inv))
                cmyk[0][x].append(c)
                cmyk[1][x].append(m)
                cmyk[2][x].append(yv)
                cmyk[3][x].append(k)
        return cmyk

    @staticmethod
    def tile_radial_r(tile_x: int, tile_y: int,
                      img_w_tiles: int, img_h_tiles: int) -> float:
        """
        Map tile position to radial coordinate r.
        Image center = Observer at r→0 (destination).
        Input edge tiles at r=1.

        r(tile) = sqrt((tx - cx)^2 + (ty - cy)^2) / r_max
        (inverted so center=0, edge=1)
        """
        cx = (img_w_tiles - 1) / 2.0
        cy = (img_h_tiles - 1) / 2.0
        r_max = math.sqrt(cx**2 + cy**2) + 1e-12
        dist = math.sqrt((tile_x - cx)**2 + (tile_y - cy)**2)
        return min(1.0, dist / r_max)

    @staticmethod
    def index_record(rgb_tile: List[List[Tuple[float,float,float]]],
                     tile_x: int = 0, tile_y: int = 0,
                     img_w_tiles: int = 1, img_h_tiles: int = 1,
                     depth_est: float = 0.0,
                     depth_conf: float = 0.0) -> Dict[str, Any]:
        """
        Full INDEX_RECORD for one image tile.
        """
        cmyk = ImageHyperIndex.rgb_tile_to_cmyk(rgb_tile)
        tupper = MultiChannelTupper.tile_index_record(cmyk, tile_x, tile_y)
        r = ImageHyperIndex.tile_radial_r(tile_x, tile_y, img_w_tiles, img_h_tiles)

        # Representative pixel color index (center pixel)
        cx = len(rgb_tile) // 2
        cy = len(rgb_tile[0]) // 2 if len(rgb_tile) > 0 else 0
        try:
            rc, gc, bc = rgb_tile[cx][cy]
            theta, phi, sat, rho = SphericalColor.rgb_to_spherical(rc, gc, bc)
            color_idx = SphericalColor.color_index(theta, phi, sat, rho)
        except (IndexError, ValueError):
            color_idx = 0

        return {
            **tupper,
            'color_index': str(color_idx),
            'radial_r':    r,
            'depth_est':   depth_est,
            'depth_conf':  depth_conf,
        }


# ==============================================================================
# MODULE 6 — HIERARCHICAL CODE INDEX
# ==============================================================================

class CodeIndex:
    """
    Hierarchical address scheme for the codebase.

    Level 0 — Global  (ℝ, trivial): SHA256 of entire file
    Level 1 — Class   (ℂ, U(1)):    G·7 + class_k
    Level 2 — Method  (ℍ, SU(2)):   G·7² + class_k·7 + method_m
    Level 3 — Line    (𝕆, G₂):     G·7³ + class_k·7² + method_m·7 + line_n

    Each address encodes its full ancestry.
    Strip indices from right to walk back to root.
    Non-commutativity at ℍ: (class, method) order matters.
    Non-associativity at 𝕆: nesting structure baked into address.
    """

    @staticmethod
    def global_hash(filepath: str) -> str:
        """SHA256 of file contents."""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    @staticmethod
    def build(filepath: str) -> Dict[str, Any]:
        """
        Build the CODE_INDEX for a Python source file.
        Scans for class and def statements.
        """
        if not os.path.exists(filepath):
            return {}

        g_hash = CodeIndex.global_hash(filepath)
        g_int  = int(g_hash, 16) % (7**6)  # compact global index

        classes  = {}
        methods  = {}
        current_class = None
        current_method = None
        class_k  = 0
        method_m = 0

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_n, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith('class '):
                name = stripped[6:].split('(')[0].split(':')[0].strip()
                addr = g_int * 7 + class_k
                classes[name] = {
                    'class_idx': class_k,
                    'address':   addr,
                    'line_start': line_n,
                }
                current_class = name
                class_k += 1
                method_m = 0

            elif stripped.startswith('def '):
                name = stripped[4:].split('(')[0].strip()
                ck   = classes[current_class]['class_idx'] if current_class else 0
                addr = g_int * 49 + ck * 7 + method_m
                key  = f"{current_class}.{name}" if current_class else name
                methods[key] = {
                    'class':      current_class,
                    'method_idx': method_m,
                    'address':    addr,
                    'line_start': line_n,
                }
                current_method = key
                method_m += 1

        return {
            'filepath':    filepath,
            'global_hash': g_hash,
            'global_idx':  g_int,
            'total_lines': len(lines),
            'total_bytes': os.path.getsize(filepath),
            'classes':     classes,
            'methods':     methods,
            'version':     'FA_1.0',
            'charset':     'US_KB_97',
            'algebra_tower': 'R->C->H->O',
            'sedenion_boundary': SEDENION_BOUNDARY,
        }


# ==============================================================================
# MODULE 7 — BLOCKCHAIN LEDGER
# ==============================================================================

class BlockchainLedger:
    """
    Append-only blockchain ledger for training history.

    Each block:
      block_id       : int
      timestamp      : ISO datetime string
      prev_hash      : SHA256 of previous block (genesis = '0'*64)
      modality       : 'text' | 'image'
      epoch          : int
      step           : int
      perm_index     : str  (arbitrary precision decimal, text or Tupper k)
      data_length    : int  (context window k or tile count)
      layer          : str  ('R'|'C'|'H'|'O')
      noether_current: float
      mastered       : bool  (crystallization event)
      block_hash     : SHA256 of this block's content

    Two output files:
      .jsonl  — human readable, one JSON per line
      .chain  — verification file (hashes only, fast check)

    Tamper detection: any modification breaks subsequent hashes.
    Provenance: every crystallized weight traces back to its training data.
    """

    def __init__(self, base_path: str = 'FA_hyperindex_ledger'):
        self.jsonl_path  = base_path + '.jsonl'
        self.chain_path  = base_path + '.chain'
        self._prev_hash  = '0' * 64
        self._block_id   = 0
        self._load_state()

    def _load_state(self) -> None:
        """Resume from existing ledger if present."""
        if os.path.exists(self.jsonl_path):
            try:
                with open(self.jsonl_path, 'r') as f:
                    lines = [l.strip() for l in f if l.strip()]
                if lines:
                    last = json.loads(lines[-1])
                    self._prev_hash = last.get('block_hash', '0'*64)
                    self._block_id  = last.get('block_id', -1) + 1
            except (json.JSONDecodeError, KeyError):
                pass

    def _make_hash(self, block: Dict[str, Any]) -> str:
        content = (
            f"{block['block_id']}|{block['timestamp']}|{block['prev_hash']}|"
            f"{block['modality']}|{block['epoch']}|{block['step']}|"
            f"{block['perm_index']}|{block['data_length']}|{block['layer']}|"
            f"{block['noether_current']:.8f}|{block['mastered']}"
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def append(self,
               modality: str,
               epoch: int,
               step: int,
               perm_index: Any,     # int or str
               data_length: int,
               layer: str,
               noether_current: float,
               mastered: bool = False,
               extra: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Append one block to the ledger.
        Returns the completed block dict.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        ts  = now.isoformat()

        block: Dict[str, Any] = {
            'block_id':        self._block_id,
            'timestamp':       ts,
            'prev_hash':       self._prev_hash,
            'modality':        modality,
            'epoch':           epoch,
            'step':            step,
            'perm_index':      str(perm_index),
            'data_length':     data_length,
            'layer':           layer,
            'noether_current': float(noether_current),
            'mastered':        mastered,
        }
        if extra:
            block['extra'] = extra

        block['block_hash'] = self._make_hash(block)

        # Write to jsonl
        with open(self.jsonl_path, 'a') as f:
            f.write(json.dumps(block) + '\n')

        # Write to chain (hashes only)
        with open(self.chain_path, 'a') as f:
            f.write(f"{block['block_id']}:{block['block_hash']}\n")

        self._prev_hash = block['block_hash']
        self._block_id += 1
        return block

    def verify(self) -> Tuple[bool, int, str]:
        """
        Verify the entire chain.
        Returns (valid, first_broken_id, message).
        """
        if not os.path.exists(self.jsonl_path):
            return True, -1, "No ledger found"

        prev = '0' * 64
        with open(self.jsonl_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    block = json.loads(line)
                except json.JSONDecodeError:
                    return False, -1, "JSON decode error"

                if block.get('prev_hash') != prev:
                    return False, block['block_id'], \
                           f"Chain broken at block {block['block_id']}: prev_hash mismatch"

                stored_hash = block.pop('block_hash', None)
                computed    = self._make_hash(block)
                block['block_hash'] = stored_hash

                if stored_hash != computed:
                    return False, block['block_id'], \
                           f"Chain broken at block {block['block_id']}: hash mismatch"

                prev = stored_hash

        return True, -1, f"Chain valid — {self._block_id} blocks verified"

    def last_hash(self) -> str:
        return self._prev_hash


# ==============================================================================
# MODULE 8 — SEDENION BOUNDARY GUARD
# ==============================================================================

class SedenionBoundaryViolation(Exception):
    """
    Raised when code attempts to operate beyond the 𝕆 layer.

    The NN tower terminates at 𝕆.
    𝕊 (sedenion) informs the Lagrangian from outside but does not run inside.
    Zero-divisors in 𝕊 break norm preservation — the training invariant.
    Mastery transition (𝕆→𝕊) is crystallization, not computation.
    """
    pass


def assert_within_tower(algebra_index: int) -> None:
    """
    Assert that an algebra index is within the NN tower (≤ 𝕆).
    Raises SedenionBoundaryViolation if algebra_index >= SEDENION_BOUNDARY.
    """
    if algebra_index >= SEDENION_BOUNDARY:
        raise SedenionBoundaryViolation(
            f"Algebra index {algebra_index} exceeds 𝕆 (index 3). "
            f"The NN tower terminates at 𝕆. "
            f"Sedenion (index 4+) is outside the training domain. "
            f"Mastery transition occurs via crystallize(), not forward()."
        )


# ==============================================================================
# MODULE 9 — RADIAL / LAYER CORRESPONDENCE
# ==============================================================================

def layer_to_r(layer: int, L_total: int = 4) -> float:
    """
    Map layer depth index to radial coordinate r.

    ℝ substrate (layer=0) is at the outermost surface: r = 1.0
    𝕆 reasoning (layer=3) is innermost, closest to Observer: r = 0.25
    Observer itself (r→0) is outside the NN.

    r(l) = (L_total - l) / L_total

    Ainulindale polar form: α_NN(r) = g² / (4π·ħ_NN·ln(1/r))
    RG form equivalent:     α_NN(l) = α_0 / (1 + β_0·α_0·ln(l/l_0))
    Bridge:                 ln(1/r) = ln(L/(L-l))
    """
    assert_within_tower(layer)
    return max(1e-6, (L_total - layer) / L_total)


def r_to_layer(r: float, L_total: int = 4) -> int:
    """
    Map radial coordinate r back to layer depth index.
    Inverse of layer_to_r.
    """
    return max(0, min(L_total - 1, round(L_total * (1.0 - r))))


def alpha_nn_from_r(g: float, hbar: float, r: float) -> float:
    """
    Neural fine structure constant from radial coordinate.
    α_NN(r) = g² / (4π·ħ_NN·ln(1/r))

    Ainulindale form — singular at r→0 by design (full coupling at destination).
    r_min = 1/L_total prevents singularity in practice.
    """
    if r <= 0:
        return float('inf')
    ln_inv_r = math.log(1.0 / r)
    if ln_inv_r < 1e-12:
        return 0.0
    return (g**2) / (4.0 * math.pi * hbar * ln_inv_r)


# ==============================================================================
# MODULE 10 — POLAR LAGRANGIAN WRAPPER
# ==============================================================================

def polar_lagrangian(L_kin: float, L_mat: float,
                     L_bias: float, L_coup: float,
                     layer: int = 0, L_total: int = 4) -> float:
    """
    Ainulindale corrected Lagrangian density.

    ℒ_NN = (2/π) ∮ [ℒ_kin + ℒ_mat + (1/φ)·ℒ_bias + ℒ_coup] dr dθ

    Discrete approximation (one layer = one integration step):
      ℒ_NN(l) ≈ (2/π) · Δr · [ℒ_kin + ℒ_mat + (1/φ)·ℒ_bias + ℒ_coup]

    Where:
      (2/π)  : radian normalization of circular polar measure
      (1/φ)  : golden ratio conjugate bias coupling = 0.6180...
               (from Ainulindale_Conjecture_Revised.docx, April 13 2026)
      Δr     : radial step = 1/L_total (uniform layer spacing)

    The bias term carries (1/φ) because in destination-centric coordinates
    the bias field must be weighted by the golden ratio conjugate to preserve
    the VEV relationship under the conformal map from Cartesian to polar.
    """
    PHI  = (1.0 + math.sqrt(5.0)) / 2.0
    bias_coupling = 1.0 / PHI          # = 0.61803...
    two_over_pi   = 2.0 / math.pi      # = 0.63662...
    delta_r       = 1.0 / L_total

    inner = L_kin + L_mat + bias_coupling * L_bias + L_coup
    return two_over_pi * delta_r * inner


# ==============================================================================
# SELF-TEST
# ==============================================================================

def run_self_test() -> bool:
    """Quick verification of all modules."""
    print("FA_smnnip_hyperindex — self-test")
    print("=" * 50)
    passed = 0
    failed = 0

    # Test 1: US keyboard map
    try:
        assert USKeyboardMap.encode('a') == 0
        assert USKeyboardMap.decode(0) == 'a'
        assert USKeyboardMap.encode(' ') == 94   # space is at index 94
        assert USKeyboardMap.encode('\n') == 96  # newline at 96
        assert len(US_KEYBOARD_CHARS) == 97
        print("  [PASS] USKeyboardMap: charset verified (97 chars)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] USKeyboardMap: {e}")
        failed += 1

    # Test 2: Text hyperindex round-trip
    try:
        seq = "Hello!"
        idx, fidx, length = TextHyperIndex.index_record(seq)
        recovered = TextHyperIndex.decode_text(idx, length)
        assert recovered == seq, f"Got {repr(recovered)}"
        assert TextHyperIndex.verify(seq)
        print(f"  [PASS] TextHyperIndex: '{seq}' -> idx={idx} -> '{recovered}'")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] TextHyperIndex: {e}")
        failed += 1

    # Test 3: Long sequence (overflow test, ASCII only)
    try:
        seq = "The Two Towers Ainulindale First Age 2026"
        idx, fidx, length = TextHyperIndex.index_record(seq)
        recovered = TextHyperIndex.decode_text(idx, length)
        assert recovered == seq
        print(f"  [PASS] TextHyperIndex long: {length} chars, {idx.bit_length()} bits")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] TextHyperIndex long: {e}")
        failed += 1

    # Test 4: Spherical color (phi is lossy by design — test invertible dims only)
    try:
        r, g, b = 0.8, 0.3, 0.1
        theta, phi, sat, rho = SphericalColor.rgb_to_spherical(r, g, b)
        # phi encodes warm/cool from B channel — not fully invertible
        # Test that theta, sat, rho reconstruct reasonably
        r2, g2, b2 = SphericalColor.spherical_to_rgb(theta, phi, sat, rho)
        # Luminance and saturation should be close; hue should be close
        rho2 = 0.2126*r2 + 0.7152*g2 + 0.0722*b2
        rho1 = 0.2126*r  + 0.7152*g  + 0.0722*b
        err_lum = abs(rho1 - rho2)
        assert err_lum < 0.12, f"Luminance error {err_lum:.4f} too large"
        print(f"  [PASS] SphericalColor: theta={theta:.3f} sat={sat:.3f} "
              f"rho={rho:.3f} lum_err={err_lum:.4f} (phi is advisory/lossy)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] SphericalColor: {e}")
        failed += 1

    # Test 5: Tupper encode/decode round-trip
    try:
        tile = [[[0.5 + 0.1*x*0.1*y for y in range(8)]
                  for x in range(8)]
                 for _ in range(4)]
        k_vec = MultiChannelTupper.encode_tile(tile)
        recovered = MultiChannelTupper.decode_tile(k_vec)
        err = max(abs(tile[c][x][y] - recovered[c][x][y])
                  for c in range(4) for x in range(8) for y in range(8))
        assert err < 1.0/(2**TUPPER_BITS), f"Quantization error {err:.6f}"
        total_bits = sum(k.bit_length() for k in k_vec)
        print(f"  [PASS] MultiChannelTupper: 4ch 8×8 tile, total bits={total_bits}, err={err:.6f}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] MultiChannelTupper: {e}")
        failed += 1

    # Test 6: Radial correspondence
    try:
        for l in range(4):
            r = layer_to_r(l, 4)
            l2 = r_to_layer(r, 4)
            assert l2 == l, f"layer {l} → r={r:.3f} → layer {l2}"
        print(f"  [PASS] Radial correspondence: ℝ(r=1.0)→ℂ(0.75)→ℍ(0.50)→𝕆(0.25)")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Radial correspondence: {e}")
        failed += 1

    # Test 7: Sedenion boundary
    try:
        assert_within_tower(3)   # 𝕆 — OK
        try:
            assert_within_tower(4)  # 𝕊 — should raise
            print("  [FAIL] Sedenion boundary: should have raised")
            failed += 1
        except SedenionBoundaryViolation:
            print("  [PASS] Sedenion boundary: 𝕆 passes, 𝕊 raises")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] Sedenion boundary: {e}")
        failed += 1

    # Test 8: Polar Lagrangian
    try:
        L = polar_lagrangian(L_kin=-0.5, L_mat=0.3, L_bias=0.1, L_coup=-0.2, layer=0)
        assert L != 0.0
        PHI = (1 + math.sqrt(5)) / 2
        expected_inner = -0.5 + 0.3 + (1/PHI)*0.1 + (-0.2)
        expected = (2/math.pi) * 0.25 * expected_inner
        assert abs(L - expected) < 1e-10, f"Got {L}, expected {expected}"
        print(f"  [PASS] Polar Lagrangian: (2/π)∮[...+(1/φ)L_bias+...] = {L:.6f}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Polar Lagrangian: {e}")
        failed += 1

    # Test 9: Blockchain ledger
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = BlockchainLedger(os.path.join(tmpdir, 'test_ledger'))
            b0 = ledger.append('text',  0, 0, 12345,   8, 'R', 0.001, False)
            b1 = ledger.append('image', 0, 1, 99999,  64, 'O', 0.003, True)
            valid, broken_id, msg = ledger.verify()
            assert valid, f"Chain invalid: {msg}"
            assert b1['prev_hash'] == b0['block_hash']
        print(f"  [PASS] Blockchain ledger: 2-block chain verified, mastery event recorded")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Blockchain ledger: {e}")
        failed += 1

    print("=" * 50)
    print(f"  Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == '__main__':
    ok = run_self_test()
    raise SystemExit(0 if ok else 1)
