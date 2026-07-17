#!/usr/bin/env python3
"""
Callimachus — HyperGallery
============================
Bijective coordinate system over all finite images of a given spec.
Companion to HyperWebster: where HyperWebster addresses text, HyperGallery
addresses images as unique coordinates in the infinite enumeration of all
possible pixel arrangements.

Fractal containment property:
  Every image that will ever exist already has a coordinate.
  We are discovering its location, not creating it.

No compression entropy: pixel values are exact integers.
No floating-point pathology: sensor readings converted once to fixed
  integers at chosen precision, then addressed exactly forever.

Self-referential master index:
  All ImageRecords serialized to JSON → indexed by HyperWebster →
  single master label for the entire gallery.
  Moving all data = moving one label.

PixelMode:
  BINARY    1 bit/pixel  (Tupper-style B&W bitmaps)
  GRAY8     8 bits/pixel
  RGB24     24 bits/pixel (3 x uint8 channels)
  SPECTRAL  N bands x bit_depth (JWST / detector mode)

VectorAddress:
  Images have large pixel counts → large integers.
  Decomposed into 32-bit component words for practical storage.
  Label = "_".join of zero-padded hex components.
"""

import json
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

from ..core.hyperwebster import HyperWebster

sys.set_int_max_str_digits(0)

_COMPONENT_BASE = 2 ** 32


# ---------------------------------------------------------------------------
# VectorAddress
# ---------------------------------------------------------------------------

@dataclass
class VectorAddress:
    components: list
    length:     int
    timestamp:  str
    meta:       dict = field(default_factory=dict)

    def to_label(self) -> str:
        return "_".join(format(c, "08x") for c in self.components)

    @classmethod
    def from_label(cls, label: str, length: int) -> 'VectorAddress':
        return cls([int(w, 16) for w in label.split("_")], length, "")

    def to_integer(self) -> int:
        n = 0
        for w in reversed(self.components):
            n = n * _COMPONENT_BASE + w
        return n

    @staticmethod
    def from_integer(n: int, length: int,
                     timestamp: str = "", meta: dict = None) -> 'VectorAddress':
        comps = []
        while n > 0:
            n, rem = divmod(n, _COMPONENT_BASE)
            comps.append(rem)
        return VectorAddress(
            comps or [0], length,
            timestamp or time.ctime(), meta or {}
        )

    @property
    def num_words(self) -> int:
        return len(self.components)

    @property
    def num_uvec4s(self) -> int:
        return math.ceil(self.num_words / 4)


# ---------------------------------------------------------------------------
# PixelMode and ImageSpec
# ---------------------------------------------------------------------------

class PixelMode(Enum):
    BINARY   = "binary"
    GRAY8    = "gray8"
    RGB24    = "rgb24"
    SPECTRAL = "spectral"


@dataclass
class ImageSpec:
    width:     int
    height:    int
    mode:      PixelMode
    n_bands:   int = 1
    bit_depth: int = 8

    def __post_init__(self):
        if self.mode == PixelMode.BINARY:
            self.n_bands   = 1
            self.bit_depth = 1
        elif self.mode == PixelMode.GRAY8:
            self.n_bands   = 1
            self.bit_depth = 8
        elif self.mode == PixelMode.RGB24:
            self.n_bands   = 3
            self.bit_depth = 8

    @property
    def depth(self) -> int:
        return 2 ** self.bit_depth

    @property
    def n_pixels(self) -> int:
        return self.width * self.height

    @property
    def n_values(self) -> int:
        return self.n_pixels * self.n_bands


# ---------------------------------------------------------------------------
# ImageRecord
# ---------------------------------------------------------------------------

@dataclass
class ImageRecord:
    label:     str
    length:    int
    timestamp: str
    width:     int
    height:    int
    mode:      str
    n_bands:   int
    bit_depth: int
    tag:       str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# HyperGallery
# ---------------------------------------------------------------------------

class HyperGallery:
    """Bijective coordinate system over all finite images of a given ImageSpec."""

    def __init__(self, spec: ImageSpec):
        self.spec     = spec
        self._N       = spec.depth
        self._records: list[ImageRecord] = []
        self._cache:   dict = {}

    def _pixels_to_int(self, values: list) -> int:
        if len(values) != self.spec.n_values:
            raise ValueError(
                f"Expected {self.spec.n_values} pixel values, got {len(values)}."
            )
        N    = self._N
        addr = 0
        for v in reversed(values):
            if not (0 <= v < N):
                raise ValueError(f"Pixel value {v} out of range 0..{N-1}.")
            addr += (v + 1) * (N ** values.index(v) if False else 1)
            # Horner: accumulate correctly
        # Correct Horner accumulation (not the above stub)
        addr = 0
        for v in values:
            if not (0 <= v < N):
                raise ValueError(f"Pixel value {v} out of range 0..{N-1}.")
            addr = addr * N + (v + 1)
        return addr - 1

    def _int_to_pixels(self, addr: int) -> list:
        if addr < 0:
            raise ValueError("Address must be non-negative.")
        N   = self._N
        n   = self.spec.n_values
        res = []
        addr += 1
        while addr > 0:
            addr, rem = divmod(addr - 1, N)
            res.append(rem)
        while len(res) < n:
            res.append(0)
        return list(reversed(res))

    def index_image(self, values: list, tag: str = "") -> ImageRecord:
        """
        Index pixel values. Returns ImageRecord with VectorAddress label.
        values: flat list of integer pixel values in [0, depth-1].
        For RGB24: [R0,G0,B0, R1,G1,B1, ...]
        For SPECTRAL: all bands for pixel 0, then pixel 1, etc.
        """
        cache_key = tuple(values[:32])
        if cache_key not in self._cache:
            self._cache[cache_key] = self._pixels_to_int(values)
        addr = self._cache[cache_key]
        va   = VectorAddress.from_integer(addr, self.spec.n_values)
        rec  = ImageRecord(
            label     = va.to_label(),
            length    = self.spec.n_values,
            timestamp = time.ctime(),
            width     = self.spec.width,
            height    = self.spec.height,
            mode      = self.spec.mode.value,
            n_bands   = self.spec.n_bands,
            bit_depth = self.spec.bit_depth,
            tag       = tag,
        )
        self._records.append(rec)
        return rec

    def regenerate_image(self, rec: ImageRecord) -> list:
        """Regenerate pixel values from an ImageRecord."""
        va = VectorAddress.from_label(rec.label, rec.length)
        return self._int_to_pixels(va.to_integer())

    def spectral_address_range(self, band_constraints: dict) -> tuple:
        """
        Given per-band constraints {band_idx: (min_val, max_val)},
        return (addr_lo, addr_hi) bounding the candidate image subspace.
        Basis for pre-recombination universe image search (HyperJWST).
        """
        N   = self._N
        n   = self.spec.n_values
        rep = [N // 2] * n
        for band_idx, (lo, hi) in band_constraints.items():
            mid = (lo + hi) // 2
            for px in range(self.spec.n_pixels):
                rep[px * self.spec.n_bands + band_idx] = mid
        addr_mid = self._pixels_to_int(rep)
        delta    = N ** (n - len(band_constraints) * self.spec.n_pixels)
        return (max(0, addr_mid - delta), addr_mid + delta)

    @property
    def records(self) -> list[ImageRecord]:
        return list(self._records)


# ---------------------------------------------------------------------------
# HyperIndex — self-referential master index
# ---------------------------------------------------------------------------

class HyperIndex:
    """
    Maintains a JSON record of all indexed images and text.
    The JSON is itself indexed by HyperWebster (PUBLIC_CHARSET) to produce
    a single master label for the entire gallery state.
    Moving all data = moving one label.

    Uses PUBLIC_CHARSET (Unicode 15.1 codepoint order).
    Previously had a hardcoded keyboard-order charset — retired.
    """

    def __init__(self):
        self._hw              = HyperWebster()   # PUBLIC_CHARSET
        self._text_records:   list = []
        self._image_records:  list = []
        self._master_label:   Optional[str] = None

    def add_text_record(self, record) -> None:
        self._text_records.append(record)
        self._master_label = None   # invalidate cache

    def add_image_record(self, rec: ImageRecord) -> None:
        self._image_records.append(rec.to_dict())
        self._master_label = None

    def to_json(self) -> str:
        return json.dumps({
            "schema":        "HyperIndex/2.0",
            "charset":       "Unicode 15.1 codepoint order",
            "generated":     time.ctime(),
            "text_records":  self._text_records,
            "image_records": self._image_records,
        }, ensure_ascii=False, indent=2)

    def master_label(self) -> str:
        """
        SHA-256 HyperWebster label of the current JSON index state.
        This single label addresses the entire gallery.
        """
        if self._master_label is not None:
            return self._master_label
        js                 = self.to_json()
        self._master_label = self._hw.label_of(js)
        return self._master_label

    def record_count(self) -> int:
        return len(self._text_records) + len(self._image_records)
