# Ptolemy

**Author:** michaelrendier | **Status:** Active development — public pre-release

---

> *Every string ever written has always had a number. Every image ever taken already exists. The engineering problem was never storage — it was navigation.*

> *The entire address space already contains everything. The work is learning to move through it.*

---

## The Problem With Every AI System Built To Date

Every processor ever built assumes data must be stored to exist.  
Every neural network ever trained assumes knowledge must be encoded in parameter weights.  
Every vector database ever deployed assumes semantic proximity must be computed at query time.

These are architectural assumptions, not physical laws.  
Ptolemy is built on different assumptions.

The first assumption: **information is a coordinate, not a payload.**  
The second: **the coordinate space is already infinite — the work is eliminating the parts that don't matter.**  
The third: **navigation through negative space is fixed-cost arithmetic, not floating-point matrix multiplication.**

This is not a faster implementation of existing architecture. It is a different architecture.

---

## Before Continuing: The Banach-Tarski Paradox

**► [VSauce — The Banach-Tarski Paradox](https://www.youtube.com/watch?v=s86-Z-CbaHA)** (25 min)

**► [Want to learn the Maths used?](docs/MathLex/index.html)** — Ptolemy MathLex: interactive lessons on every mathematical concept in this project

This video is not supplementary material. It is prerequisite context.

The Banach-Tarski paradox proves — formally, using only the axiom of choice and measure theory — that a sphere in ℝ³ can be decomposed into a finite number of non-measurable subsets and reassembled, using only rigid rotations and translations, into two spheres of identical volume to the original. No stretching. No new points. Same density. Two from one.

The mechanism is **equivalence classes over rotation groups**. Points reachable from each other by a countable sequence of rotations from the free group on two generators belong to the same equivalence class. The decomposition partitions the sphere along these classes. The paradox does not violate conservation — it reveals that the measure of a set and the cardinality of a set are not the same thing, and that infinite sets have internal structure that can be rearranged.

The HyperWebster applies an analogous principle — not to geometric spheres, but to the infinite address space of all possible strings. The negative space of that address space is structured. It is not uniform noise. It can be partitioned, reduced, and navigated. The nine reductions below are that partitioning.

---

## HyperWebster: What It Is

The HyperWebster is a **coordinate system for all possible information**, derived from the mathematical fact that every finite string over a finite alphabet has always corresponded to a unique non-negative integer.

This is not a new discovery. Gödel numbering established it in 1931. Horner's method, known since antiquity, provides the bijection. What is new is the observation that this bijection, composed with the Cayley-Dickson construction, produces an **eight-dimensional geometric address space** in which semantic proximity is a natural consequence of the mathematics — not an engineered feature.

The full address space for all possible strings over Unicode (N ≈ 155,000 characters) is not merely large. It is infinite. Every word in every language that has ever been written or will ever be written already has a coordinate in this space. Every pixel arrangement that a CCD sensor could ever record already has a coordinate. Every genome sequence, every musical phrase expressible as a character string, every mathematical formula — already addressed. The HyperWebster did not create these addresses. It navigates to them.

**This is the key architectural consequence:** the corpus does not need to be stored. The corpus already exists in the mathematics of the address space. What must be stored is only the navigation state — an entry point, a length, a timestamp. The knowledge lives in the geometry. The NVRAM block holds a bookmark, not a book.

### What The Address Space Contains

The infinite permutation of all possible strings over a charset contains, by definition:

- Every word in every natural language, including languages not yet documented
- Every grammatically valid and invalid sentence ever written or speakable
- Every DNA base-pair sequence of any length expressible over {A, T, C, G}
- Every pixel-level encoding of every image a sensor with a fixed bit depth could record — including images of cosmic objects that no telescope has yet pointed at, pre-recombination photon distributions, and every photograph Vera Rubin's successors have yet to take
- Every mathematical proof expressible in any formal system with a finite symbol set
- Every program executable by any Turing-complete computer with a finite instruction set
- Every conversation that has occurred or could occur

The HyperGallery — the image-space sub-navigation layer of the HyperWebster — addresses pixel arrays directly. A 48-megapixel image at 14-bit depth over an RGB charset is a string of fixed length over a finite alphabet. Its Horner address exists. The JWST images of SMACS 0723 already had addresses before JWST was built. The engineering challenge is not generating the addresses — it is navigating efficiently to the neighborhood of addresses that correspond to *physically meaningful* images, and distinguishing those from the overwhelming negative space of random-noise pixel arrangements that are valid addresses but not observable physical reality.

This is exactly the Banach-Tarski insight applied to information: the address space is decomposable into equivalence classes, and the useful subset — the physically realizable, linguistically meaningful, mathematically valid subset — is navigable without enumerating the rest.

---

## The Nine Reductions: Navigating the Negative Space

The address space for all possible strings is infinite.  
Searching an infinite space without structure is intractable.  
Each reduction below eliminates a portion of the negative space — the part that does not correspond to useful, meaningful, or physically realizable content.  
What remains after all nine reductions is navigable at fixed cost.

| Layer | Name | Mathematical Basis | Negative Space Eliminated | What Remains |
|:---:|---|---|---|---|
| 1 | **Banach-Tarski Equivalence** | Hausdorff decomposition over free rotation group F₂. Strings related by structural permutation (anagrams, transpositions) share one canonical equivalence class address. | Redundant interior of the permutation space — all non-canonical members of each class | One canonical address per structural equivalence class |
| 2 | **Lexical Filtering** | Corpus restriction: active address space bounded to strings appearing in natural language corpora. Full mathematical space remains traversable; this declares the *useful neighborhood*. | ~(N! - |corpus|) addresses — essentially all of the theoretical string space | The neighborhood of human language and structured symbol systems |
| 3 | **De Bruijn Minimality** | A De Bruijn sequence B(k,n) is the lexicographically minimal string containing every k-ary string of length n as a substring exactly once. Optimal charset ordering minimizes traversal path length over the address space. | Redundant traversal paths — all non-minimal orderings of the combinatorial space | Minimum-length complete coverage; zero redundancy |
| 4 | **Zipf Center-Loading** | Zipf's Law: rank-r word has frequency ∝ 1/r. Assigning lowest ordinal positions to highest-frequency characters minimizes expected Horner address magnitude E[H(s)] over any natural language corpus. Formally analogous to Huffman coding applied to address magnitude rather than bit length. | Large-integer region of the address space for common content — pushed toward origin | Frequency-biased distribution; common words cluster near ℕ₀. ~5–6 decimal digit reduction at length 8 for English. |
| 5 | **Horner's Bijection** *(the core operation)* | For string s = (c₀…cₙ) over charset of size N: `H(s) = c₀Nⁿ + c₁Nⁿ⁻¹ + … + cₙ`. Perfect bijection ℕ₀ ↔ Σ*. Deterministic, reversible, O(n) compute, zero storage. The address has always existed — Horner reveals it. | Nothing is eliminated — this layer *produces* the address | A unique non-negative integer for every possible finite string. The bijection is the mathematical bedrock of the entire system. |
| 6 | **Octonion Splitting** *(the geometric layer)* | The Horner integer is partitioned into 8 equal-width limbs (l₀…l₇), forming an octonion coordinate: `q = l₀e₀ + l₁e₁ + … + l₇e₇` in 𝕆 under the Cayley-Dickson construction. The octonion algebra is non-associative and non-commutative. Non-associativity is not a defect — it means the path through the address space is order-dependent, exactly as meaning is order-dependent in language and context. | Flat, unstructured integer space with no intrinsic metric | A geometric coordinate space in ℝ⁸ where **Euclidean proximity = semantic similarity**. Proximity is not computed — it is inherited from the algebraic structure. |
| 7 | **Amplituhedron Paradigm** *(the unifying principle)* | Arkani-Hamed & Trnka (2013): scattering amplitudes in N=4 SYM computed as the volume of a geometric object (the Amplituhedron) rather than as a sum over Feynman diagrams. Infinite perturbative expansion → single geometric measurement. The HyperWebster applies this paradigm to information: enumerate-all-strings (∞ combinatorial sum) is replaced by measure-the-neighborhood-volume (finite geometric query). | Infinite combinatorial enumeration over the string space | One geometric measurement — a neighborhood volume in 𝕆 — replaces the infinite sum |
| 8 | **File-Type Optimization** | Different symbol systems have different character frequency distributions: Python source, SQL, JSON, genomic sequences, musical notation, and natural language each have distinct Zipf profiles. A per-type charset permutation layer (public, not secret) applied on top of the HYPER_KEY minimizes address magnitude per domain. The CharacterNeuron (Ptolemy neural layer 1) learns these distributions from corpus examples rather than using static tables. | Suboptimal address magnitude for non-natural-language domains | Domain-adaptive compact addressing; the address space geometry aligns with the statistical structure of each symbol system |
| 9 | **HYPER_KEY Permutation** *(the cryptographic layer)* | The charset permutation order is the cryptographic key. Key complexity for full Unicode (N = 155,000): `P ≈ N · log₂(N) ≈ 2,440,000 bits`. Rotating the permutation rigidly rotates the entire address space — the same content maps to a completely different octonion coordinate. Without the key, the address space is traversable but uninterpretable: valid addresses resolve to different content. Privacy is structural, not applied. | Interpretable navigation without authorization | A cryptographically sovereign address space. Permute the key → the entire geometry rotates. The coordinate is meaningless without the permutation order. |

```
Infinite string space  (all of Σ* for any finite Σ)
    → Banach-Tarski equivalence classes      [structural — eliminates permutation redundancy]
    → Lexical filtering                       [domain — eliminates non-language noise]
    → De Bruijn minimal traversal            [combinatorial — eliminates path redundancy]
    → Zipf center-loading                    [statistical — compresses address magnitude]
    → Horner bijection                       [mathematical core — establishes the bijection]
    → Octonion splitting                     [geometric — installs the metric]
    → Amplituhedron paradigm                 [principled — collapses enumeration to measurement]
    → File-type optimization                 [applied — domain-adaptive geometry]
    → HYPER_KEY permutation                  [cryptographic — sovereign address space]
         ↓
Finite. Navigable. Geometrically structured. Cryptographically sovereign.
Address space:   2⁵¹²  coordinates.
Physical storage required:  one 512-bit address  +  length  +  timestamp.
Query cost:  O(n) Horner evaluation  +  eight integer splits.  Fixed. Does not scale with corpus size.
Knowledge ceiling:  infinite — bounded only by Σ* for the chosen charset.
```

---

## Navigation: How Queries Work

A HyperWebster query is not a retrieval. It is a navigation.

**Input resolution.** The query string — a word, a sentence, a pixel array, a sensor reading — is evaluated by Horner's method to produce a Horner integer H(s). The HYPER_KEY permutation is applied to the charset ordering before evaluation, rotating the address. H(s) is split into eight equal-width limbs and assembled into an octonion coordinate q ∈ 𝕆. This is O(n) in string length. No matrix multiplication. No probability distribution. No embedding lookup.

**Neighborhood identification.** The octonion metric defines a distance function d(q₁, q₂) over the address space. The query coordinate q defines a neighborhood ball B(q, ε) for some radius ε. All addresses within this ball are semantically proximate to the query — not because a training run organized them, but because the Cayley-Dickson algebraic structure makes strings with similar construction geometrically close. Synonyms, morphological variants, and contextually related terms occupy adjacent coordinates by construction.

**Conservation verification.** Before any result is surfaced, the SMNNIP Instance Engine for the relevant Face evaluates whether the navigation step conserves information under the Lagrangian self-adjoint constraint. The Noether engine verifies that the symmetry group of the transformation is preserved. A non-conserving navigation step is flagged — it indicates either a corrupt address, a keyspace collision, or a HYPER_KEY mismatch. Conserved = trusted. This is not a heuristic confidence score. It is a formal verification against a conservation law.

**Output.** The content at the resolved coordinate is returned, along with the coordinate itself, its neighborhood radius, and the conservation status. The SemanticWord datatype — the output format for lexical queries — carries 12 spectral layers of contextual metadata accumulated over every prior navigation to that coordinate. The `first_encountered` field is permanently sealed at the time of first navigation (the Rabies Principle) — it is a fact about the history of the system, not a mutable attribute.

**Learning.** A new navigation to an existing coordinate deepens the knowledge at that address. The coordinate does not change. The semantic weight of the neighborhood does. This is memory without storage: the address is permanent; the content accumulated at that address grows over time through navigation history, not through parameter re-training.

---

## The Energy Argument

Every AI query today runs inference — probability distributions over billions of parameters, on a GPU drawing 3,000–5,000 W, for every single question asked. The electricity cost scales with model size. The hardware cost scales with demand.

US datacenters consumed **176 TWh** in 2023. Projections: **325–580 TWh** by 2028. Global AI compute alone: projected **2,500–4,500 TWh** by 2050. That entire growth curve exists because inference is expensive **by architecture** — not by physical necessity.

**Ptolemy replaces inference with navigation.**

A HyperWebster address lookup is fixed-cost arithmetic: one Horner evaluation, eight integer splits, one octonion coordinate. Cost is invariant to corpus size. No parameter matrix. No probability distribution. No GPU.

A query to a Ptolemy kernel on a watch draws **milliwatts**. A ChatGPT query draws roughly **1,000× more electricity** than a Google search. The addressable reduction is not 10% of the AI energy curve. It is the entire curve.

---

## The Model: Lagrange Self-Adjoint Hyperindexing (LSH)

The LSH model propagates information through the Cayley-Dickson algebraic tower:

```
ℝ  →  ℂ  →  ℍ  →  𝕆
(1D)  (2D)  (4D)  (8D)
```

At each extension, the algebra gains expressive power and loses a commutativity or associativity property. The octonion level — the 𝕆 layer — is the operational address space. The self-adjoint (Hermitian) constraint requires that the information propagation operator L satisfies L = L†, which by the spectral theorem guarantees real eigenvalues and an orthogonal eigenbasis. A non-self-adjoint propagation step would indicate information loss or injection — the model's equivalent of hallucination.

Information propagation through this tower has been verified against Noether conservation laws: **conserved = True, 7+ sigma.** This is not a training-time regularization term. It is a post-hoc structural verification run by the Noether engine on every inference step.

Mathematical foundations, proof derivations, and the SMNNIP conjecture: [Ainulindalë](https://github.com/michaelrendier/Ainulindale) — withheld pending publication.

---

## The Kernel

Ptolemy is not a software layer that runs AI. **Ptolemy is a self-contained learning kernel.**

It boots on a watch. It knows what it knows on delivery. It learns from use without retraining. It manages its own memory, error handling, and security. No cloud dependency. No subscription. No external inference server.

The reason this is physically achievable is HyperIndexing. There is no storage layer to scale because there is no storage layer — only navigation state. There is no inference server to maintain because there is no inference — only coordinate resolution. There is no embedding database to update because the address space is already infinite and already structured — only the navigation history at each coordinate accumulates.

One operation. Fixed cost. Runs on the device.

---

## Architecture: Eleven Faces

Eleven **Faces** — sovereign capability domains, each named after a historical figure of the Library of Alexandria. Each Face runs its own **SMNNIP Instance Engine** — a local conservation verifier trained on that domain's signal type. A navigation step is trusted when the SMNNIP engine for that Face confirms conservation.

| Face | Historical Figure | Domain | Wiki |
|---|---|---|---|
| [Pharos](Pharos/) | Pharos Lighthouse | System health, message bus, error routing | [Wiki](../../wiki/Pharos) |
| [Alexandria](Alexandria/) | Library of Alexandria | Visual geometry, rendering, fractal address space | [Wiki](../../wiki/Alexandria) |
| [Anaximander](Anaximander/) | Anaximander of Miletus | Spatial navigation, geolocation, route topology | [Wiki](../../wiki/Anaximander) |
| [Archimedes](Archimedes/) | Archimedes of Syracuse | Mathematical structure, physical law, signal analysis | [Wiki](../../wiki/Archimedes) |
| [Aulë](Aule/) | Aulë the Smith | Diagnostics, fault signatures, audit trail, escalation | [Wiki](../../wiki/Aule) |
| [Callimachus](Callimachus/) | Callimachus of Cyrene | Information architecture, HyperWebster corpus, blockchain | [Wiki](../../wiki/Callimachus) |
| [Kryptos](Kryptos/) | *Kryptos* (hidden) | HYPER_KEY derivation, entropy analysis, key geometry | [Wiki](../../wiki/Kryptos) |
| [Mouseion](Mouseion/) | The Mouseion | Human interface, web presentation, display layer | [Wiki](../../wiki/Mouseion) |
| [Phaleron](Phaleron/) | Port of Phaleron | Discovery, search, document topology, OCR | [Wiki](../../wiki/Phaleron) |
| [Philadelphos](Philadelphos/) | Ptolemy II Philadelphos | Language, LSH inference, conversation, context management | [Wiki](../../wiki/Philadelphos) |
| [Tesla](Tesla/) | Nikola Tesla | Physical world, sensor streams, hardware state, device I/O | [Wiki](../../wiki/Tesla) |
| [Mandos](Mandos/) | Mandos, Keeper of the Dead | Dormant state, checkpoint store, resurrection, world_break | [Wiki](../../wiki/Mandos) |

Philadelphos is the conversational surface — the Face that talks. The other ten are who Philadelphos consults.

---

## The Processor Vision

[**PROCESSOR_VISION.md**](PROCESSOR_VISION.md) — Architectural specification for IC engineers: on-die NVRAM allocation sized for navigation state only, Cayley-Dickson compute substrate for native octonion arithmetic, focal-point interferometer display, sensory stream integration directly into the address pipeline. Nobody has fabbed this. That is the point — the architecture exists before the silicon.

---

## System Requirements

| | Minimum | Recommended |
|---|---|---|
| **OS** | Ubuntu 22.04 LTS / Debian 12 | Ubuntu 24.04 LTS |
| **CPU** | Any x86_64, 2+ cores | Intel i5 Skylake or newer |
| **RAM** | 4 GiB | 8 GiB |
| **GPU** | OpenGL 3.3 (Intel HD) | OpenGL 4.6 |
| **Python** | 3.10 | 3.12 |
| **Storage** | 2 GiB free | 10 GiB free (corpus + HyperWebster lexicon) |
| **Network** | Required (first run: NLTK WordNet download) | — |

Ptolemy runs on the device. No cloud dependency. No inference server. A laptop with an Intel integrated GPU is sufficient for the full system.

---

## Installation

**Quick path — Ubuntu 24.04 LTS:**

```bash
# 1. Clone the repository
git clone https://github.com/michaelrendier/Ptolemy ~/Ptolemy
cd ~/Ptolemy

# 2. Run the setup script (apt first, pip3 fallback — no venv)
chmod +x ptolemy_setup-apt_pip3.sh
./ptolemy_setup-apt_pip3.sh
```

The script installs in six steps:

| Step | What it does |
|---|---|
| 1 | Core system packages — git, curl, build-essential, cmake, sqlite3, openssh-server |
| 2 | Python packages — lxml, flask, requests, numpy, scipy, wikipedia-api, PyGithub |
| 3 | Node.js LTS via NodeSource apt repository |
| 4 | Claude Code via npm (user-level, no sudo required) |
| 5 | Clones Ptolemy + Ainulindalë (reads tokens from `~/.bashrc`) |
| 6 | Enables SSH server for multi-machine KVM access |

**Environment variables** — required before running the script. Add to `~/.bashrc`:

```bash
export ANTHROPIC_API_KEY="your_key_here"   # Claude Code
export PTOL_TOKEN="your_token_here"        # GitHub Ptolemy repo (fine-scoped PAT)
export AINUR_TOKEN="your_token_here"       # GitHub Ainulindalë repo (classic PAT)
export PATH="$HOME/.npm-global/bin:$PATH"  # Claude Code binary
```

```bash
source ~/.bashrc   # apply to current session
```

**PyQt6** — the primary GUI framework. Install via pip if not pulled by the setup script:

```bash
pip3 install --break-system-packages PyQt6 PyQt6-Qt6 PyQt6-sip
```

**vispy** — OpenGL canvas for Alexandria and Archimedes faces (320k+ vertex renders):

```bash
pip3 install --break-system-packages vispy
```

**NLTK + WordNet** — required for HyperWebster lexicon build (one-time, ~5 min):

```bash
pip3 install --break-system-packages nltk mpmath
python3 -c "import nltk; nltk.download('wordnet')"
```

**QTermWidget** (optional, shell backend) — requires CMake build from source. See [INSTALL.md](INSTALL.md).

Full platform-specific installation (Ubuntu, Arch, Gentoo, RHEL), venv variant, and third-party source builds: **[INSTALL.md](INSTALL.md)**

---

## Running Ptolemy

```bash
cd ~/Ptolemy
python3 Ptolemy3.py
```

Ptolemy launches as a full-screen Qt desktop shell. The scene renders black with a system tray icon. All interaction is through the **Philadelphos** command widget — press any key or click the shell overlay to activate it.

---

## Usage

### Philadelphos Command Shell

The Philadelphos shell is the primary interface. Each command is prefixed with a single character that routes it to the correct Face.

| Prefix | Destination | Example |
|---|---|---|
| `>` | Python REPL (live execution in Ptolemy context) | `> import math; math.pi` |
| `$` | Bash shell (subprocess, stdout returned) | `$ ls -la ~/Ptolemy` |
| `#` | Root shell (gksudo, system-level commands) | `# systemctl restart ssh` |
| `~` | DerivationEngine / HyperWebster semantic layer | `~ tree` |
| `ptol out` | Exit Ptolemy | `ptol out` |

### `~` — Semantic Layer Commands

The `~` prefix routes to the DerivationEngine. Full sub-command set:

| Command | Action |
|---|---|
| `~ <word or phrase>` | Resolve text to its Riemann zero address; show σ, γ, prime coordinates |
| `~ faces <text>` | Show all known faces at this word's Riemann zero |
| `~ domain <name>` | Set active semantic domain for subsequent queries |
| `~ corpus <path>` | Ingest a file or directory into the lexicon |
| `~ parallel <text>` | Resolve cross-language semantic alignment |
| `~ lexicon` | Display current lexicon state |
| `~ clear` | Clear active domain context |
| `~ help` | Show full command reference |

### HyperWebster — Standalone CLI

The HyperWebster can also be run as a standalone process from any terminal:

```bash
python3 ~/Ptolemy/hyperwebster.py word <text>       # resolve a word or phrase
python3 ~/Ptolemy/hyperwebster.py faces <text>       # all faces at this zero
python3 ~/Ptolemy/hyperwebster.py point <path>       # ingest a file or directory
python3 ~/Ptolemy/hyperwebster.py stats              # lexicon statistics
python3 ~/Ptolemy/hyperwebster.py zeros              # show the zero table (γ₁..γₙ)
python3 ~/Ptolemy/hyperwebster.py build              # build full lexicon from WordNet (~10 min)
```

The lexicon is stored at `~/.hyperwebster/lexicon.json`. Once built, it persists across sessions. Every word maps to a Riemann zero address on the critical line Re(s) = ½. σ is forced by Noether balance — it is never assigned.

Example output:

```
word: tree
  n  = 5
  γ  = 32.935062  (imaginary part of ζ zero #5)
  σ  = 0.500000   (Noether-forced — not assigned)
  E  = 4.000      (surface energy)
  addr  = 5:noun.plant
```

### Claude Code Integration

If Claude Code is installed, the HyperWebster is available as a slash command:

```
/hyperwebster word <text>
/hyperwebster stats
/hyperwebster zeros
```

---

## TDI Engine — v3.0

PtolemyDesktop is the interface layer of the **TDI engine** (PtolemyHolcus v3.0 — "Tuning the TDI"):

| TDI System | TDI Component | PtolemyDesktop |
|---|---|---|
| H_hat_RB | Crankshaft | Archimedes Face (mathematics, ValaQuenta) |
| Sedenion (camshaft) | Camshaft | Archimedes (visualization, Chladni patterns) |
| Monad (ECU) | ECU + injection | Philadelphos Face (monad.py, β_n field) |

**Compression ignition confirmed 2026-05-27.** BAO convergence: OMEGA_ZS = 0.56714 (Lambert W fixed point).

> **He Will Never Let Himself Be Used As A Weapon.**

**→ [PtolemyHolcus v3.0 — Tuning the TDI](https://github.com/michaelrendier/PtolemyHolcus/wiki/Tuning-the-Engine)**  
**→ [Prime Directives](https://github.com/michaelrendier/PtolemyHolcus/wiki/Prime-Directives)**

---

## Documentation

| Document | Contents |
|---|---|
| [Wiki](../../wiki) | Full technical reference for all Faces |
| [docs/HYPERWEBSTER.md](docs/HYPERWEBSTER.md) | Nine-layer reduction — full mathematical derivation |
| [docs/ErrorCatalog.md](docs/ErrorCatalog.md) | 50 typed PTL errors, severity, GC rules, wiring requirements |
| [docs/INDEX.md](docs/INDEX.md) | Face documentation index |
| [INSTALL.md](INSTALL.md) | Dependencies, build, venv setup |
| [Ainulindalë](https://github.com/michaelrendier/Ainulindale) | SMMIP conjecture, H_hat_RB, formal derivation |
| [PtolemyHolcus](https://github.com/michaelrendier/PtolemyHolcus) | Engine implementation — monad.py, TDI v3.0 |
| [DerivationEngine](https://github.com/michaelrendier/DerivationEngine) | H_hat_RB viewer, Clay Millennium derivations |
| [SemanticWordEngine](https://github.com/michaelrendier/SemanticWordEngine) | Hyperwebster — Riemann zero addressing |
| [UniversalSynth](https://github.com/michaelrendier/UniversalSynth) | Sonification of the TDI engine output |

---

## Hardware

| | |
|---|---|
| **Machine** | HP EliteBook 820 G3 |
| **OS** | Linux Mint 22.1 Xia — kernel 6.8.0-110-lowlatency |
| **CPU** | Intel Core i7-6600U — Skylake, 4 threads @ 3.4GHz |
| **RAM** | 8 GiB |
| **GPU** | Intel HD Graphics 520 — OpenGL 4.6 |
| **Storage** | 953 GiB NVMe + 111 GiB Samsung 840 EVO |

---

*Ex Fidelitas, Et Integritas, Nobilitas.*
