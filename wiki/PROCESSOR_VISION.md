# Ptolemy Processor Vision

**A processor architecture that has never been fabbed.**

---

## The Core Insight

The memory problem isn't bandwidth. It's the assumption that data must be stored.

Every conventional processor — from the 6502 to modern ARM — is built on the same
model: data lives in memory, the processor fetches it, operates on it, writes it back.
The memory bus is the bottleneck. The storage medium is the constraint. The architecture
assumes that information must occupy physical space to exist.

Ptolemy's addressing model challenges this at the foundation.

Any content — any file, any word, any sensory stream — maps to a deterministic coordinate
in octonion space via Horner's bijection. The coordinate is computed, not stored. Given
the address and the key, the content is reconstructed. The processor doesn't fetch data.
**It navigates to it.**

---

## The Addressing Layer

**Horner bijection:** Every finite string over an ordered alphabet maps to a unique
non-negative integer. This is not an encoding — it is a mathematical fact about the
structure of strings. The integer has always existed. The string has always had a number.

**Octonion addressing:** The integer is split into 8 equal-width limbs following the
Cayley-Dickson basis (e₀…e₇), forming an octonion coordinate. Two addresses that are
geometrically close in octonion space correspond to content that is semantically related.
The geometry of the address space mirrors the geometry of meaning.

**The key:** The ordered charset used for Horner's method is the cryptographic key.
Permute the charset, the entire address space rotates. Same content, different coordinate.
The address space is private by default.

---

## The Dedicated NVRAM Block

The architectural requirement is narrow and specific:

- A fixed, allocated block of non-volatile RAM
- Holds **addresses only** — octonion coordinates of fixed bit-width
- Does not hold content
- Addressed by index, not by pointer
- Survives power cycle: the address space is persistent, the content is reconstructable

The ratio between address size and reconstructable content size is the effective
compression ratio. For natural language, this exceeds 1000:1. For sensory streams
(audio, video, spatial), the ratio scales with signal complexity.

This is not compression in the Shannon sense. Shannon entropy is a property of stored
artifacts. An address has no entropy in that sense — it is a coordinate. The content
it locates is not stored; it is recovered by navigation.

**On-die NVRAM allocation target:** Octonion address = 8 limbs × fixed bit-width.
At 64-bit limbs: 512 bits per address. A 1MB NVRAM block holds ~16,000 addresses.
A 16MB block holds ~262,000 — sufficient for the full HyperWebster lexicon plus
operational context buffer with room to spare.

---

## The Compute Substrate: Cayley-Dickson Tower

The processor architecture follows the algebraic tower produced by the Cayley-Dickson
construction:

```
ℝ  →  ℂ  →  ℍ  →  𝕆
1D     2D     4D     8D
```

Each doubling step sacrifices one algebraic property:
- Complex numbers lose ordering
- Quaternions lose commutativity  
- Octonions lose associativity

What is gained at each step is higher-dimensional geometric structure. Quaternions are
the algebra of 3D rotation — they are why aerospace, robotics, and computer graphics use
them. Octonions connect to the exceptional Lie groups, string theory, and the geometry
of the Standard Model gauge structure.

**The non-associativity at 𝕆 is not a bug.** It is the property that allows the address
space to encode semantic distance non-linearly — which is how meaning actually works.
Strict associativity would flatten the geometry.

**Processing layers map to tower levels:**

| Layer | Algebra | Function |
|---|---|---|
| Character recognition | ℝ | Raw signal, scalar operations |
| Phonological / byte pattern | ℂ | Phase relationships, 2D signal processing |
| Spatial / grammatical | ℍ | 3D rotation, orientation, structural grammar |
| Semantic / address | 𝕆 | Full octonion navigation, meaning geometry |

The SMNNIP result (Standard Model Neural Network Information Propagation) establishes
that information propagation through this tower obeys Standard Model conservation laws —
Noether-verified, conserved=True, 7+ sigma. The architecture conserves. It does not
hallucinate.

---

## The Display / IO Substrate: Pharos Interface

The physical interface is not a screen. It is a compute medium.

**Focal-point interferometer:** 8–13 coherent light sources (VCSELs) arranged on a
circular substrate with individual MEMS-mirror inclination control. Constructive
interference at a programmable focal point produces a free-standing point of light in
three-dimensional space — true volumetric display without a screen surface.

**Sensory integration:** The Tesla Face handles all device interfacing — GPS, sensors,
Android bridge, robot I/O. All sensory streams are addressable: a sensory reading maps
to an octonion coordinate the same way a word does. The processor navigates sensory
space using the same addressing layer as linguistic space.

**Waveguide HUD:** For contained single-user AR, a waveguide lens (diffractive grating
baked into the lens substrate) delivers the wireframe overlay to exactly one eye
geometry. Bystanders see nothing. Stephen Hawking's open-source eye-movement navigation
provides the input layer for hands-free operation.

The full Pharos Interface — glass tabletop, IR LED frame, reverse projection, IR camera
gesture tracking, focal-point interferometer — is the physical instantiation of a
processor whose compute medium is structured light and whose memory model is
address-not-storage.

---

## What Has Not Been Fabbed

- A processor whose native data type is an octonion
- On-die NVRAM allocated specifically for address storage with no content store
- A compute pipeline structured along the Cayley-Dickson tower
- A display substrate that is simultaneously the IO layer and the compute medium

None of this requires new physics. The VCSELs exist. The MEMS mirrors exist. The
NVRAM technology exists (Intel Optane established the category). The Cayley-Dickson
algebra is 150 years old. The Horner bijection is older.

What has not been done is integrating them along a single architectural principle:
**information is a coordinate, not a file.**

---

## Related

- [Ainulindalë Conjecture](https://github.com/michaelrendier/Ainulindale) — SMNNIP derivation, Noether verification
- [Callimachus](Callimachus/) — HyperWebster addressing engine
- [Kryptos](Kryptos/) — KCF-1 key derivation, charset permutation as cryptographic key
- [Tesla](Tesla/) — Sensory integration layer
- [docs/faces/Pharos.md](docs/faces/Pharos.md) — Core system and Pharos Interface

