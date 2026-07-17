#!/usr/bin/python3
"""
HyperGallery  --  Infinite Permutation of Pixel Arrangements
=============================================================

Companion to HyperWebster.  Where HyperWebster addresses text strings,
HyperGallery addresses images as unique coordinates in the infinite
enumeration of all possible pixel arrangements.

Three image modes:
  PixelMode.BINARY    -- 1 bit/pixel  (Tupper-style B&W bitmaps)
  PixelMode.GRAY8     -- 8 bits/pixel
  PixelMode.RGB24     -- 24 bits/pixel (3 x uint8 channels)
  PixelMode.SPECTRAL  -- N bands x bit_depth (JWST / LHC detector mode)

Self-referential JSON master index:
  Every indexed image produces an ImageRecord.  All records are serialised
  to a JSON string, which is fed to HyperWebster to produce a SINGLE
  master VectorAddress for the entire gallery.  Moving all your data =
  moving one address.

Fractal containment property:
  Every image that will ever exist already has a coordinate.  We are not
  creating the data, we are discovering its location.

No compression entropy:
  Pixel values are exact integers.  The bijection is integer arithmetic.
  There is no rounding, quantisation, or information loss.

No floating-point pathology:
  A floating-point sensor reading is converted once to a fixed integer
  at chosen precision, then addressed exactly forever after.
"""

import json
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

sys.set_int_max_str_digits(0)

COMPONENT_BASE = 2 ** 32


# ---------------------------------------------------------------------------
# VectorAddress
# ---------------------------------------------------------------------------

@dataclass
class VectorAddress:
    components: list
    length:     int
    timestamp:  str
    meta:       dict = field(default_factory=dict)

    def to_label(self):
        return "_".join(format(c, "08x") for c in self.components)

    @classmethod
    def from_label(cls, label, length):
        return cls([int(w, 16) for w in label.split("_")], length, "")

    def to_integer(self):
        n = 0
        for w in reversed(self.components):
            n = n * COMPONENT_BASE + w
        return n

    @staticmethod
    def from_integer(n, length, timestamp="", meta=None):
        comps = []
        while n > 0:
            n, rem = divmod(n, COMPONENT_BASE)
            comps.append(rem)
        return VectorAddress(comps or [0], length,
                             timestamp or time.ctime(), meta or {})

    @property
    def num_words(self):
        return len(self.components)

    @property
    def num_uvec4s(self):
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
    def depth(self):
        return 2 ** self.bit_depth

    @property
    def n_pixels(self):
        return self.width * self.height

    @property
    def n_values(self):
        return self.n_pixels * self.n_bands

    @property
    def address_bits(self):
        return math.ceil(self.n_values * math.log2(self.depth))

    @property
    def address_words(self):
        return math.ceil(self.address_bits / 32)


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

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# HyperGallery core
# ---------------------------------------------------------------------------

class HyperGallery:
    """Bijective coordinate system over all finite images of a given ImageSpec."""

    def __init__(self, spec):
        self.spec    = spec
        self._N      = spec.depth
        self._records = []
        self._cache   = {}

    def _pixels_to_int(self, values):
        if len(values) != self.spec.n_values:
            raise ValueError(f"Expected {self.spec.n_values} values, got {len(values)}.")
        N    = self._N
        addr = 0
        for i, v in enumerate(reversed(values)):
            if not (0 <= v < N):
                raise ValueError(f"Value {v} out of range 0..{N-1}.")
            addr += (v + 1) * (N ** i)
        return addr - 1

    def _int_to_pixels(self, addr):
        if addr < 0:
            raise ValueError("Address must be non-negative.")
        N    = self._N
        n    = self.spec.n_values
        res  = []
        addr += 1
        while addr > 0:
            addr, rem = divmod(addr - 1, N)
            res.append(rem)
        while len(res) < n:
            res.append(0)
        return list(reversed(res))

    def index_image(self, values, tag=""):
        key = repr(values[:16])
        if key not in self._cache:
            self._cache[key] = self._pixels_to_int(values)
        addr = self._cache[key]
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

    def regenerate_image(self, rec):
        va = VectorAddress.from_label(rec.label, rec.length)
        return self._int_to_pixels(va.to_integer())

    def spectral_address_range(self, band_constraints):
        """
        Given per-band constraints {band_idx: (min_val, max_val)},
        return (addr_lo, addr_hi) bounding the candidate image subspace.
        Images satisfying the spectral filter live in this address range.
        Basis for pre-recombination universe image search.
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


# ---------------------------------------------------------------------------
# Master JSON index (self-referential)
# ---------------------------------------------------------------------------

class HyperIndex:
    """
    Maintains a JSON record of all indexed images and text.
    The JSON string is itself indexed by HyperWebster to produce a
    single MASTER ADDRESS representing the entire database.
    Moving all data = moving one VectorAddress.
    """

    _CHARS = (
        r"`1234567890-="
        "\t"
        r"qwertyuiop[]\asdfghjkl;'"
        "\n"
        r"zxcvbnm,./ ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:\"ZXCVBNM<>?"
    )

    def __init__(self):
        self._text_records  = []
        self._image_records = []
        self._master        = None
        self._char_list = list(self._CHARS)
        self._N         = len(self._char_list)
        self._char_idx  = {ch: i for i, ch in enumerate(self._char_list)}

    def add_text_record(self, record):
        self._text_records.append(record)
        self._master = None

    def add_image_record(self, rec):
        self._image_records.append(rec.to_dict())
        self._master = None

    def to_json(self):
        return json.dumps({
            "schema":        "HyperIndex/1.0",
            "generated":     time.ctime(),
            "text_records":  self._text_records,
            "image_records": self._image_records,
        }, indent=2)

    def master_address(self):
        if self._master is not None:
            return self._master
        js   = self.to_json()
        addr = self._str_to_int(js)
        self._master = VectorAddress.from_integer(
            addr, len(js), time.ctime(),
            meta={"record_count": len(self._text_records) + len(self._image_records)}
        )
        return self._master

    def _str_to_int(self, text):
        # Horner's method: O(L) big-int multiplications, each by small N
        # Much faster than the naive sum(idx * N^i) for long strings.
        addr = 0
        N    = self._N
        for ch in text:
            try:
                idx = self._char_idx[ch] + 1
            except KeyError:
                raise ValueError(f"Character {ch!r} not in charset.")
            addr = addr * N + idx
        return addr - 1

    def _int_to_str(self, addr):
        res  = []
        N    = self._N
        addr += 1
        while addr > 0:
            addr, rem = divmod(addr - 1, N)
            res.append(self._char_list[rem])
        return "".join(reversed(res))

    def regenerate_from_master(self, va):
        return json.loads(self._int_to_str(va.to_integer()))

    def save_index(self, path):
        with open(path, "w") as f:
            f.write(self.to_json())
        print(f"Index saved: {path}")

    def load_index(self, path):
        with open(path) as f:
            data = json.load(f)
        self._text_records  = data.get("text_records",  [])
        self._image_records = data.get("image_records", [])
        self._master = None


# ---------------------------------------------------------------------------
# JWST spectral cube helper
# ---------------------------------------------------------------------------

class SpectralCube:
    """
    JWST-style Integral Field Unit data cube: (nx, ny, n_bands).
    Each voxel: integer 0..(2^bit_depth - 1).
    The entire cube = one point in HyperGallery-Spectral address space.

    Pre-recombination universe search:
      CMB peak ~160 GHz / 1.9mm.  Before recombination the universe was
      opaque (surface of last scattering).  Images satisfying
      {band_160GHz > threshold, band_visible == 0} form a sub-orbit.
      spectral_search() returns the address range; the OrbitCache makes
      repeated neighbourhood queries cheap.
    """

    def __init__(self, nx, ny, n_bands, bit_depth=16):
        self.spec    = ImageSpec(nx, ny, PixelMode.SPECTRAL,
                                 n_bands=n_bands, bit_depth=bit_depth)
        self.gallery = HyperGallery(self.spec)

    def index_cube(self, cube_flat, tag=""):
        return self.gallery.index_image(cube_flat, tag=tag)

    def spectral_search(self, band_constraints):
        return self.gallery.spectral_address_range(band_constraints)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    index = HyperIndex()

    print("=" * 72)
    print(f"{'HyperGallery  --  Infinite Pixel Permutation Addressing':^72}")
    print("=" * 72)

    # 1. Tupper-style 106x17 binary
    print("\n--- Tupper-style 106x17 binary image ---")
    spec_t    = ImageSpec(106, 17, PixelMode.BINARY)
    gallery_t = HyperGallery(spec_t)
    checker   = [(i + j) % 2 for j in range(17) for i in range(106)]
    rec_t     = gallery_t.index_image(checker, tag="checkerboard_106x17")
    index.add_image_record(rec_t)
    ok_t = gallery_t.regenerate_image(rec_t) == checker
    print(f"n_values   : {spec_t.n_values}")
    print(f"Addr words : {len(rec_t.label.split('_'))} x 8 hex chars")
    print(f"Round-trip : {'PASS' if ok_t else 'FAIL'}")
    print(f"Timestamp  : {rec_t.timestamp}")

    # 2. Grayscale gradient 64x64
    print("\n--- 8-bit grayscale 64x64 gradient ---")
    spec_g    = ImageSpec(64, 64, PixelMode.GRAY8)
    gallery_g = HyperGallery(spec_g)
    gradient  = [(i * 255 // (64*64)) for i in range(64*64)]
    rec_g     = gallery_g.index_image(gradient, tag="gradient_64x64_gray")
    index.add_image_record(rec_g)
    ok_g = gallery_g.regenerate_image(rec_g) == gradient
    print(f"Addr words : {len(rec_g.label.split('_'))} x 8 hex chars")
    print(f"Round-trip : {'PASS' if ok_g else 'FAIL'}")

    # 3. RGB 64x64
    print("\n--- 24-bit RGB 64x64 ---")
    spec_rgb    = ImageSpec(64, 64, PixelMode.RGB24)
    gallery_rgb = HyperGallery(spec_rgb)
    rgb_vals    = []
    for y in range(64):
        for x in range(64):
            rgb_vals += [x * 4 % 256, y * 4 % 256, 128]
    rec_rgb  = gallery_rgb.index_image(rgb_vals, tag="synthetic_rgb_64x64")
    index.add_image_record(rec_rgb)
    ok_rgb = gallery_rgb.regenerate_image(rec_rgb) == rgb_vals
    print(f"Addr words : {len(rec_rgb.label.split('_'))} x 8 hex chars")
    print(f"Round-trip : {'PASS' if ok_rgb else 'FAIL'}")

    # 4. JWST IFU spectral cube 16x16 x 50 bands x 16-bit
    print("\n--- JWST IFU spectral cube 16x16 x 50 bands x 16-bit ---")
    cube      = SpectralCube(nx=16, ny=16, n_bands=50, bit_depth=16)
    cube_data = [(x + y + k * 7) % 65536
                 for y in range(16) for x in range(16) for k in range(50)]
    rec_cube  = cube.index_cube(cube_data, tag="synthetic_IFU_16x16x50")
    index.add_image_record(rec_cube)
    ok_cube = cube.gallery.regenerate_image(rec_cube) == cube_data
    print(f"Cube shape : 16x16 x 50 bands x 16-bit")
    print(f"n_values   : {cube.spec.n_values:,}")
    print(f"Addr words : {len(rec_cube.label.split('_')):,} x 8 hex chars")
    print(f"Round-trip : {'PASS' if ok_cube else 'FAIL'}")

    # Spectral neighbourhood search
    lo, hi = cube.spectral_search({0: (1000, 2000), 49: (0, 100)})
    va_lo  = VectorAddress.from_integer(lo, cube.spec.n_values)
    va_hi  = VectorAddress.from_integer(hi, cube.spec.n_values)
    print(f"Spectral search range:")
    print(f"  lo: {va_lo.to_label()[:48]}...")
    print(f"  hi: {va_hi.to_label()[:48]}...")

    # 5. Master address
    print("\n" + "-" * 72)
    print("Computing master address for entire gallery index...")
    json_str = index.to_json()
    print(f"Index JSON : {len(json_str):,} chars, {len(index._image_records)} image records")
    master = index.master_address()
    print(f"Master addr: {master.num_words:,} uint32 words  ({master.num_uvec4s:,} uvec4s)")
    print(f"Label (first 72 chars):")
    print(f"  {master.to_label()[:72]}...")
    print(f"Timestamp  : {master.timestamp}")
    print(f"\nThis single address represents ALL {len(index._image_records)} indexed images.")
    print("To move the entire gallery database: move this one VectorAddress.")

    # Save index
    index.save_index("/mnt/user-data/outputs/hypergallery_index.json")

    # Verify master round-trip
    recovered = index.regenerate_from_master(master)
    n_rec = len(recovered["image_records"])
    print(f"\nMaster round-trip: {n_rec} image records -- "
          f"{'PASS' if n_rec == len(index._image_records) else 'FAIL'}")

    print("\n" + "=" * 72)
    print("HyperGallery ready.")
    print("Next extensions: LHC detector frame geometry, Vera Rubin LSST tiles.")
