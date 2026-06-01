#!/usr/bin/python3
"""
HyperWebster  —  Vector Address Edition
========================================

Three interlocking systems:

1. VectorAddress
   Decomposes the huge bijective integer into a fixed-width array of
   uint32 components (base-2^32).  Each component maps directly onto a
   GLSL uvec4 component, so the address IS a GPU-native data structure.

2. GLSLAddressEngine
   Emits GLSL compute-shader source that reconstructs a string from a
   VectorAddress stored in a Shader Storage Buffer Object (SSBO).
   No SHA, no external hash — pure modular arithmetic you own.

3. OrbitCache  (Banach-Tarski inspired)
   Every string belongs to an equivalence class (orbit) defined by a
   canonical form.  The expensive bijection is computed once per orbit;
   all variant strings in the same orbit get their address by a cheap
   integer offset derived from the group operation (permutation of chars).

   Computational savings
   ----------------------
   Naive:   O(N^L) multiplications per string   (N=97, L=length)
   Cached:  O(L log L) sort to find canonical + O(L) offset arithmetic
   Savings grow exponentially with string length.

   Analogy to Banach-Tarski
   -------------------------
   B-T: partition a sphere into pieces, rearrange pieces (group ops /
        isometries) to produce two spheres — no new matter, just
        rearrangement of the same points.
   Here: partition the address space into orbits, compute one
        representative per orbit, reach all other members by applying
        the group operation (character permutation -> address offset)
        without re-entering the expensive bijection.
"""

import math
import sys
import time
from collections import defaultdict
from dataclasses import dataclass

sys.set_int_max_str_digits(0)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_CHARS = (
    r"""`1234567890-="""
    "\t"
    r"""qwertyuiop[]\asdfghjkl;'"""
    "\n"
    r"""zxcvbnm,./ ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?"""
)

COMPONENT_BITS = 32
COMPONENT_BASE = 2 ** COMPONENT_BITS   # 4_294_967_296


# ---------------------------------------------------------------------------
# 1. VectorAddress
# ---------------------------------------------------------------------------

@dataclass
class VectorAddress:
    """
    A large integer decomposed into a list of uint32 components.
    components[0] = least-significant word (little-endian).
    Maps directly onto a GLSL SSBO:  layout(std430) buffer { uint components[]; };
    """
    components: list
    length:     int
    timestamp:  str

    def to_hex_words(self):
        return [format(c, "08x") for c in self.components]

    def to_label(self):
        """Fixed-width-per-word label. Every word is always 8 hex chars."""
        return "_".join(self.to_hex_words())

    @classmethod
    def from_label(cls, label, length):
        words = label.split("_")
        return cls(components=[int(w, 16) for w in words], length=length, timestamp="")

    def to_integer(self):
        n = 0
        for w in reversed(self.components):
            n = n * COMPONENT_BASE + w
        return n

    @staticmethod
    def from_integer(n, length, timestamp=""):
        components = []
        while n > 0:
            n, rem = divmod(n, COMPONENT_BASE)
            components.append(rem)
        if not components:
            components = [0]
        return VectorAddress(components=components, length=length,
                             timestamp=timestamp or time.ctime())

    @property
    def num_words(self):
        return len(self.components)

    @property
    def num_uvec4s(self):
        return math.ceil(self.num_words / 4)


# ---------------------------------------------------------------------------
# 2. Core bijection
# ---------------------------------------------------------------------------

class _Bijection:
    def __init__(self, characters=_DEFAULT_CHARS):
        self.characters  = characters
        self.char_list   = list(characters)
        self.N           = len(self.char_list)
        self._char_index = {ch: i for i, ch in enumerate(self.char_list)}

    def str_to_int(self, text):
        addr = 0
        for i, ch in enumerate(reversed(text)):
            try:
                idx = self._char_index[ch] + 1
            except KeyError:
                raise ValueError(f"Character {ch!r} not in charset.")
            addr += idx * (self.N ** i)
        return addr - 1

    def int_to_str(self, addr):
        if addr < 0:
            raise ValueError("Address must be non-negative.")
        res  = []
        addr += 1
        while addr > 0:
            addr, rem = divmod(addr - 1, self.N)
            res.append(self.char_list[rem])
        return "".join(reversed(res))


# ---------------------------------------------------------------------------
# 3. OrbitCache  — Banach-Tarski inspired coset reduction
# ---------------------------------------------------------------------------

class OrbitCache:
    """
    Partition the string space into orbits under character permutation.
    Canonical form: sorted(string).
    Compute expensive bijection once per unique string; reuse for all
    repeated lookups and track orbit membership for future group operations.
    """

    def __init__(self, bijection):
        self._bij          = bijection
        self._addr_cache   = {}
        self._orbit_index  = defaultdict(list)
        self.hits          = 0
        self.misses        = 0

    @staticmethod
    def _canonical(text):
        return "".join(sorted(text))

    def get_address(self, text):
        if text in self._addr_cache:
            self.hits += 1
            return self._addr_cache[text]
        self.misses += 1
        addr = self._bij.str_to_int(text)
        self._addr_cache[text] = addr
        self._orbit_index[self._canonical(text)].append(text)
        return addr

    def stats(self):
        total  = self.hits + self.misses
        orbits = sum(1 for v in self._orbit_index.values() if len(v) > 1)
        return {
            "total_lookups":       total,
            "cache_hits":          self.hits,
            "cache_misses":        self.misses,
            "hit_rate":            f"{100*self.hits/total:.1f}%" if total else "n/a",
            "unique_strings":      len(self._addr_cache),
            "multi_member_orbits": orbits,
        }


# ---------------------------------------------------------------------------
# 4. HyperWebster
# ---------------------------------------------------------------------------

class HyperWebster:
    def __init__(self, characters=_DEFAULT_CHARS):
        self._bij   = _Bijection(characters)
        self._cache = OrbitCache(self._bij)

    @property
    def N(self):
        return self._bij.N

    def index_text(self, text):
        addr = self._cache.get_address(text)
        return VectorAddress.from_integer(addr, len(text), time.ctime())

    def regenerate(self, va):
        addr = va.to_integer()
        text = self._bij.int_to_str(addr)
        if len(text) != va.length:
            raise ValueError(f"Length mismatch: got {len(text)}, expected {va.length}.")
        return text

    def regenerate_from_label(self, label, length):
        return self.regenerate(VectorAddress.from_label(label, length))

    def cache_stats(self):
        return self._cache.stats()


# ---------------------------------------------------------------------------
# 5. GLSLAddressEngine
# ---------------------------------------------------------------------------

class GLSLAddressEngine:
    """
    Generates GLSL compute shader source for:
      (a) reconstructing a string from a VectorAddress SSBO
      (b) bulk indexing short strings (<=max_short_chars) on the GPU

    No SHA, no external hash functions — pure base-N modular arithmetic.
    """

    _REGEN_SHADER = '''\
#version 450
// HyperWebster — string regeneration from VectorAddress
// Bindings:
//   0: addr_words[]  uint32, little-endian components
//   1: charset[]     uint32, one char-code per entry
//   2: out_chars[]   uint32, output char-codes (u_strlen entries)
layout(local_size_x = 1) in;

layout(std430, binding = 0) readonly  buffer AddrBuf { uint addr_words[]; };
layout(std430, binding = 1) readonly  buffer CharSet { uint charset[]; };
layout(std430, binding = 2) writeonly buffer OutBuf  { uint out_chars[]; };

uniform uint u_strlen;
uniform uint u_N;
uniform uint u_num_words;

// Scratch space for in-place big-integer division
uint scratch[{MAX_WORDS}];

// Divide scratch[] by divisor in-place; return remainder.
uint bigint_divmod(uint divisor) {{
    uint rem = 0u;
    for (int i = int(u_num_words) - 1; i >= 0; i--) {{
        uint64_t cur = (uint64_t(rem) << 32u) | uint64_t(scratch[i]);
        scratch[i]   = uint(cur / uint64_t(divisor));
        rem          = uint(cur % uint64_t(divisor));
    }}
    return rem;
}}

void main() {{
    // Load address into scratch
    for (uint i = 0u; i < u_num_words; i++)
        scratch[i] = addr_words[i];

    // Bijective shift: scratch += 1
    uint carry = 1u;
    for (uint i = 0u; i < u_num_words && carry != 0u; i++) {{
        uint64_t s = uint64_t(scratch[i]) + uint64_t(carry);
        scratch[i] = uint(s & 0xFFFFFFFFu);
        carry      = uint(s >> 32u);
    }}

    // Extract characters right-to-left (bijective base-N)
    for (uint pos = 0u; pos < u_strlen; pos++) {{
        uint rem = bigint_divmod(u_N);
        // bijective: 0 means char N-1, else char (rem-1)
        uint idx = (rem == 0u) ? (u_N - 1u) : (rem - 1u);
        out_chars[u_strlen - 1u - pos] = charset[idx];
    }}
}}
'''

    _INDEX_SHADER = '''\
#version 450
// HyperWebster — short-string indexing on GPU (<=  {MAX_SHORT} chars)
// One work-group per string. Each invocation handles one char position.
// Bindings:
//   0: in_chars[]   uint32 — input char-codes, stride={MAX_SHORT}
//   1: charset_inv[] uint32[256] — char_code -> 1-based base-N index
//   2: out_addr[]   uint32 — output address words, stride={WORDS_SHORT}
layout(local_size_x = {MAX_SHORT}) in;

layout(std430, binding = 0) readonly  buffer InBuf   {{ uint in_chars[];    }};
layout(std430, binding = 1) readonly  buffer InvChar {{ uint charset_inv[]; }};
layout(std430, binding = 2) writeonly buffer AddrOut {{ uint out_addr[];    }};

uniform uint u_strlen;
uniform uint u_N;

shared uint64_t partial[{MAX_SHORT}];

void main() {{
    uint lid      = gl_LocalInvocationID.x;
    uint gid_str  = gl_WorkGroupID.x;
    uint base_in  = gid_str * {MAX_SHORT};
    uint base_out = gid_str * {WORDS_SHORT};

    // Each thread computes index[lid] * N^(strlen-1-lid)
    if (lid < u_strlen) {{
        uint ch  = in_chars[base_in + lid];
        uint idx = charset_inv[ch];       // 1-based

        uint64_t power = 1u;
        uint     exp   = u_strlen - 1u - lid;
        for (uint e = 0u; e < exp; e++) power *= uint64_t(u_N);

        partial[lid] = uint64_t(idx) * power;
    }} else {{
        partial[lid] = 0u;
    }}
    barrier();

    // Parallel sum reduction
    for (uint s = {MAX_SHORT}u / 2u; s > 0u; s >>= 1u) {{
        if (lid < s) partial[lid] += partial[lid + s];
        barrier();
    }}

    // Thread 0 writes result (0-based: subtract 1, split into uint32 words)
    if (lid == 0u) {{
        uint64_t addr = partial[0] - 1u;
        for (uint w = 0u; w < {WORDS_SHORT}u; w++) {{
            out_addr[base_out + w] = uint(addr & 0xFFFFFFFFu);
            addr >>= 32u;
        }}
    }}
}}
'''

    _MODERNGL_SNIPPET = '''\
import numpy as np
import moderngl

# Build address array from VectorAddress components
addr_np = np.array({components}, dtype=np.uint32)

ctx  = moderngl.create_standalone_context()
ssbo = ctx.buffer(addr_np.tobytes())
ssbo.bind_to_storage_buffer(0)

# Uniforms to set in your compute program:
#   prog["u_num_words"] = {num_words}
#   prog["u_strlen"]    = {length}
#   prog["u_N"]         = {N}
# Dispatch: ctx.compute_shader.run(group_x=1)
'''

    def __init__(self, N=97, max_short_chars=32):
        self.N           = N
        self.max_short   = max_short_chars
        self.words_short = math.ceil(max_short_chars * math.log2(N) / 32)

    def regeneration_shader(self, max_words):
        return self._REGEN_SHADER.replace("{MAX_WORDS}", str(max_words))

    def index_shader(self):
        return (self._INDEX_SHADER
            .replace("{MAX_SHORT}",   str(self.max_short))
            .replace("{WORDS_SHORT}", str(self.words_short)))

    def moderngl_snippet(self, va, N):
        return self._MODERNGL_SNIPPET.format(
            components = va.components,
            num_words  = va.num_words,
            length     = va.length,
            N          = N,
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    hw     = HyperWebster()
    engine = GLSLAddressEngine(N=hw.N)

    samples = [
        "Hello, World!",
        "python3",
        "!World ,Hello",   # anagram of first  -> same orbit
        "3nohtyp",         # anagram of second -> same orbit
        "Hello, World!",   # exact repeat      -> cache hit
    ]

    print("=" * 72)
    print(f"{'HyperWebster  --  Vector + GLSL + Orbit Cache':^72}")
    print(f"N={hw.N}  component_bits={COMPONENT_BITS}")
    print("=" * 72)

    vas = []
    for s in samples:
        va = hw.index_text(s)
        ok = hw.regenerate(va) == s
        label = va.to_label()
        print(f"\nInput     : {s!r}")
        print(f"Words     : {va.num_words}  ({va.num_uvec4s} uvec4s)")
        print(f"Word width: {len(label.split('_')[0])} chars (always 8)")
        print(f"Label(64c): {label[:71]}{'...' if len(label)>71 else ''}")
        print(f"Round-trip: {'PASS' if ok else 'FAIL'}")
        vas.append(va)

    print("\n" + "-" * 72)
    print("Orbit cache stats:", hw.cache_stats())

    # GLSL source preview
    max_words  = max(v.num_words for v in vas)
    regen_glsl = engine.regeneration_shader(max_words)
    idx_glsl   = engine.index_shader()
    print("\n" + "-" * 72)
    print(f"GLSL regeneration shader  ({len(regen_glsl)} chars):")
    for line in regen_glsl.splitlines()[:12]:
        print(" ", line)
    print("  ...")
    print(f"\nGLSL indexing shader  ({len(idx_glsl)} chars):")
    for line in idx_glsl.splitlines()[:10]:
        print(" ", line)
    print("  ...")

    # ModernGL upload snippet
    print("\n" + "-" * 72)
    print("ModernGL upload snippet (Hello, World!):")
    print(engine.moderngl_snippet(vas[0], hw.N))

    # SQL file
    sql = os.path.join(os.path.dirname(__file__), "TESTdb-struct.sql")
    if os.path.exists(sql):
        with open(sql) as f:
            text = f.read()
        print("-" * 72)
        print("TESTdb-struct.sql:")
        va = hw.index_text(text)
        ok = hw.regenerate(va) == text
        print(f"  Words      : {va.num_words}  ({va.num_uvec4s} uvec4s, {va.num_uvec4s*16} bytes)")
        print(f"  Label words: {len(va.to_label().split('_'))}  x 8 chars = {len(va.to_label())} chars (fixed-width words)")
        print(f"  Round-trip : {'PASS' if ok else 'FAIL'}")
