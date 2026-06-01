# Ptolemy — TODO

Tracked development intentions, hardware notes, and deferred work.
Items move to commits when implemented. GitHub handles version history.

---

## ⚑ PRIORITY 1 — Nature Submission: SMNNIP Paper

**Status:** Active preparation — front of the line  
**Target:** *Nature* (Letter format)  
**Decision date:** April 2026

### What this is

The Standard Model of Neural Network Information Propagation (SMNNIP)
is a unification claim: neural network information propagation is governed
by the same conservation laws, gauge symmetry, and algebraic structure
as fundamental physics. This is not analogy — it is mathematical identity,
demonstrated by a working derivation engine producing verified results.

Primary result: **Noether conservation verified, violation=0.0, conserved=True**  
Confidence: **7+ sigma** (discovery threshold in physics is 5 sigma)  
Proof mechanism: `SMNNIPDerivationEngine` — pure Python, non-obfuscated,
fully reproducible by any reviewer with `python3 derivation.py`

### Why Nature

- Cross-disciplinary unification claim (mathematical physics + CS + information theory)
- 7+ sigma verified result with transparent code proof
- Gauge group U(1)×SU(2)×SU(3) identified in neural information flow
- Noether conservation as the structural constraint
- Algebra tower R->C->H->O->S (Cayley-Dickson / Dixon 1994) as the mechanism
- HyperWebster addressing as the mathematical foundation making terminology precise
- Full SMNNIP derivation, T-transformer architecture, everything open to review

### Affiliation

Independent researcher. No institutional affiliation required.
Nature accepts independent submissions. The result speaks.
ORCID required — register at orcid.org (free, 5 minutes, permanent researcher ID).

### Nature Letter Format Requirements

| Element | Constraint |
|---|---|
| Abstract | 150 words maximum — problem, result, sigma, implication |
| Main text | ~1,500 words + figures |
| Methods | Unlimited — full derivation, HyperWebster math, code here |
| Extended Data | Supporting figures and tables |
| Code statement | Points to Ainulindale repo (public, reproducible) |
| Submission | online.nature.com — account + ORCID required |

### Submission Stack (in order)

1. **Nature** — primary target
2. **Physical Review Letters** — if Nature desk-rejects (~3,000 words, high physics sigma weight)
3. **Journal of Mathematical Physics** — algebra tower as primary contribution
4. **PNAS** — computational + mathematical physics, faster review cycle

### Code Preparation Checklist

- [ ] `python3 derivation.py` runs clean, produces `conserved=True` on any machine
- [ ] Zero exotic dependencies — pure Python proof path must work standalone
- [ ] Ainulindale repo README explains how to reproduce the primary result
- [ ] Ainulindale pull request standards enforce Information Integrity:
      no modification of core constants, derivation output must match
      reference result before any PR is accepted
- [ ] `.gitignore.SSF` protecting SMNNIP implementation files in place
- [ ] Version-tag the submission state: `git tag -a smnnip-nature-v1 -m "Nature submission"`

### Paper Preparation Checklist

- [ ] Abstract draft — 150 words: problem / result / sigma / implication
- [ ] Main text outline — claim, mechanism (algebra tower), verification (sigma)
- [ ] Methods section — full SMNNIP derivation, HyperWebster addressing mathematics,
      transformer architecture, derivation engine description
- [ ] Figure 1 — algebra tower R->C->H->O->S with gauge group overlay
- [ ] Figure 2 — Noether conservation result, violation plot, sigma calculation
- [ ] Figure 3 — HyperWebster addressing as the mathematical bridge
- [ ] Code availability statement — Ainulindale repo URL
- [ ] Author line — michaelrendier, Independent Researcher, Portland OR, USA
- [ ] ORCID registered and attached

### Key Dates Principle

The Ainulindale repo commit history and this TODO entry establish
development timeline independently of submission date.
The paper is the translation. The engine is the proof.
Second Age is the public release of the full architecture.
`.gitignore.SSF` (Servant of the Sacred Fire) protects implementation
until that release. The claim is already timestamped.

### Clay Mathematics Institute — Note

The Clay Institute administers the Millennium Prize Problems (P vs NP,
Riemann Hypothesis, etc.) — not relevant here. Nature is the correct
primary venue for this result. No institutional affiliation required
for submission. Independent researcher status is sufficient.

---

## PRIORITY 2 — Incoming Hardware: Dell XPS 13 9345

**Status:** Purchasing in ~days

| Component | Spec |
|---|---|
| CPU | Snapdragon X Elite X1E-80-100 — 12 cores / 3.4 GHz (4.0 GHz boost) |
| NPU | Qualcomm Hexagon — 45 TOPS |
| GPU | Qualcomm Adreno — 3.8 TFLOPS |
| RAM | 32 GB LPDDR5X (minimum — get this config) |
| Storage | 1 TB NVMe PCIe 4.0 |
| OS | Ubuntu 24.04 LTS (official Dell support confirmed) |
| Wi-Fi | Qualcomm FastConnect 7800 — Wi-Fi 7 / BT 5.4 |

**On arrival:**
- [ ] Run `inxi -Fxz` and update `docs/Hardware/` with XPS hardware report
- [ ] Update README.md hardware table
- [ ] Verify Ubuntu 24.04 lowlatency kernel availability for JACK/PipeWire audio
- [ ] Confirm HYPER_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY env vars transferred
- [ ] Test Aule monitor live stream against acquire.py on new hardware
- [ ] Benchmark HWAS Horner vs SHA-256 on ARM (AVX2 gone — NEON instead)

---

## PRIORITY 3 — Qualcomm Integration Primer

**Status:** Deferred — implement after XPS 13 9345 arrives

The Qualcomm AI Hub developer access (API keys in hand) enables a distinct
inference pathway for SMNNIP that bypasses the CPU-only constraint.

### The Three-Layer Stack

```
PyTorch (training, local CPU)
    |
    v  torch.jit.trace()
qai_hub.submit_compile_job()   <-- target: "Snapdragon X Elite CRD"
    |
    v  compile to ONNX / QNN
Hexagon NPU (45 TOPS on-device inference)
```

### Key Facts
- `qai_hub_models` requires x64 Python on ARM Windows (not ARM64 Python)
- On Ubuntu ARM: native Python works, no emulation needed
- AI Hub Workbench hosts real Snapdragon X Elite devices in cloud for profiling
- PyTorch 2.7+ has ARM-native builds; Hexagon NPU via ONNX Runtime / DirectML
- Target device string: `hub.Device("Snapdragon X Elite CRD")`

### Tasks
- [ ] `pip install qai_hub qai_hub_models` on XPS after arrival
- [ ] `qai-hub configure --api_token <QUALCOMM_AI_HUB_TOKEN>`
- [ ] Trace a SMNNIP layer with `torch.jit.trace()` as proof of concept
- [ ] Submit compile job targeting Snapdragon X Elite CRD
- [ ] Profile on cloud-hosted device via AI Hub Workbench
- [ ] Compare Hexagon NPU inference latency vs CPU baseline
- [ ] Document results in `docs/Philadelphos/` as Qualcomm integration report
- [ ] Add `QUALCOMM_AI_HUB_TOKEN` to `.env.example`
- [ ] Integrate compile/profile workflow into Aule Forge as a named script

### Reference
- AI Hub Workbench docs: https://workbench.aihub.qualcomm.com/docs/
- AI Hub Models (GitHub): https://github.com/qualcomm/ai-hub-models
- Snapdragon X Elite device string: "Snapdragon X Elite CRD"

---

## Ptolemy Faces — Pending Work

### Philadelphos — Modular Neural Architecture Slot
- [ ] Scaffold empty model slot — `NEURAL_ARCHITECTURE = None` as the
      user-defined variable. Community contributors plug in their own model.
      SMNNIP is the reference implementation, protected by `.gitignore.SSF`
- [ ] Document the interface contract: what any plugged-in architecture must expose
- [ ] Julius Caesar face configuration (corpus: Caesar, Cicero, Cato)
- [ ] Connect Julius Caesar face to Aule stream monitoring

### Callimachus / HyperWebster
- [ ] Split 180,000-word dictionary into 26 alphabetical files
- [ ] Run `acquire.py` full pass — return with results + 23 sample JSON files
- [ ] Review incomplete flag firing on `hiraeth` and other edge cases
- [ ] Begin Callimachus SQL deprecation — replace row IDs with HyperWebster addresses

### Kryptos
- [ ] Implement KCF-1 equation in Python (`kryptos/kcf.py`)
- [ ] Build Kryptos Encrypted Secrets Store — AES-256 + HyperWebster addressing
- [ ] Add `kcf_profiles/` registry of per-Face KCF configurations

### Aule
- [ ] Wire `stream_event()` shim into `acquire.py`
- [ ] Wire shim into `Philadelphos/Ainur/ainur.py` (API call monitoring)
- [ ] Test full monitor -> forge -> replay cycle on live acquisition run

### Ptolemy++
- [ ] Port HWAS Horner computation to C++ with GMP
- [ ] Benchmark C++/GMP vs Python bignum (projected 50-100x speedup)
- [ ] Expose via Python bindings (pybind11)

### Repository — Pre-Public Checklist
- [ ] Scrub git history with `git filter-repo` before going public
- [ ] Verify no secrets remain: `grep -r "TOKEN\|API_KEY" .git/`
- [ ] Confirm `.env` in `.gitignore`, `.env.example` committed
- [ ] `.gitignore.SSF` in place and contents verified
- [ ] Set repository visibility to public (post-SMNNIP publication / Second Age)

---

## LuthSpell / LSH — Stub Hooks Needing Real Implementation

- [ ] `HaltingMonitor._evaluate()` — stub → real inference coord evaluation
- [ ] `PtolBusStub` → real `PtolBus` with queue + rotary semaphore
- [ ] Blockchain backend for halt record commits
- [ ] `cyclic_context_buffer.py` compression model: stub → Philadelphos/Ainur NLP
- [ ] `cyclic_context_buffer.py` hyperindex method: stub → full octonion/Cayley-Dickson
- [ ] `cyclic_context_buffer.py` blockchain backend: stub → real branch chain
- [ ] `ErrorHandler._emit()`: stdout stub → real log backend
- [ ] `GarbageCollector`: Python stub → C++ RAII mirror in Ptolemy++ (deferred)

## Settings Tabs Needed (one per module hook)

- [ ] `buffer_size_lines` · `compression_model` · `hyperindex_method` · `blockchain_backend`
- [ ] `priority_scheme` · `gc_on_fatal` / `gc_on_error` · `log_backend`
- [ ] `report_to_ptolemy_severity` · `halt_evaluation_logic`
- [ ] Ptolemy Settings system — **PRIORITY after working prototype + desktop**

## LSH / Architecture Design

- [ ] Design single-chip processor based on Ptolemy + Cayley-Dickson Tower (own repo when ready)
- [ ] Full blockchain architecture: master chain + Face branch chains
- [ ] `philadelphos_console.py`: instantiate LuthSpell as BUS controller in `main()`
- [ ] Wire `CyclicContextBuffer` into Philadelphos Face
- [ ] LSH Model: full Lagrange Self-Adjoint Hyperindexing implementation
- [ ] GrammarNeuron layer (resolves "it" pronoun structural problem)
- [ ] WordMonad isolation enforcement
- [ ] `acquire.py` → `WordAcquisitionRecord` dataclass (Option C: thin + `to_semantic_word()` bridge)

## Processor Architecture Research

**Status:** Concept — separate project, not Ptolemy

Methodology derived from SMNNIP / HyperWebster addressing applied to
processor architecture design. Own repo when ready. Not tracked here.

---

## .gitignore Layer Architecture

Ptolemy uses layered `.gitignore` files — one at root, one per Face where
needed. This allows directory structure to be cloned without data contents.

**Root `.gitignore`** — global rules (secrets, cache, ML binaries, media)
**`.gitignore.SSF`** — Servant of the Sacred Fire. Personal IP protection
layer. Named artifact with identity and timestamp. Contents define what
never appears publicly until Second Age. Grows as needed.
**`Aule/.gitignore`** — excludes streams/, replays/, probe_history/, aule.log

**Clone vs Pull Request:**
- Clone: copies entire repo to local machine. Gitignored files never included.
  Directory structure present, protected contents absent.
- Pull Request: contributor proposes merging changes from their branch.
  Gitignored files cannot appear in any PR — they were never committed.
- Both respect all .gitignore layers. IP is structurally protected.

---

*Last updated: April 2026*
