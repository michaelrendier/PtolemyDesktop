# PTOLEMY PROJECT — CONTEXT PRIMER
## Next Horizon: acquire.py + Autonomous Output Tuning
### Generated: April 27, 2026

---

## TOKENS
- Ptolemy repo: [CLASSIC_TOKEN] → github.com/michaelrendier/Ptolemy
- Ainulindale repo: [CLASSIC_TOKEN] → github.com/michaelrendier/Ainulindale
- Fine-scoped PAT (Ptolemy only): [FINE_SCOPED_PAT]

---

## WHAT EXISTS (as of this session)

### Ainulindale repo:
- smnnip_inversion_engine_v2.py — J_N inversion map, φ fixed point proof, Noether monitor
- smnnip_proof_engine_console.py — curses console, full PROOF_ENTRIES registry
- the_tongue.py — Fano/𝕆 algebraic filter (belongs UPSTREAM, not final output)

### Ptolemy repo / Philadelphos/:
- ptolemy_tongue.py — surface geometry filter (pentagon/hexagon fold check) — rename to output_geometry_filter.py
- output_tuner.py — /OutputTuning shell (NEW THIS SESSION)
- data_input.py — /DataInput [--DM] handler
- Callimachus/acquire.py — HyperWebster word acquisition pipeline

---

## THE PIPELINE (complete architecture)

```
/DataInput [--DM]
    ↓
SemanticWord JSON files (acquire.py produces these — O Captain runs locally)
    ↓
DataInput: loads meaning-objects into LSH tower
    ↓
Noether current layer     (extinction — non-conserved paths die)
    ↓
Higgs/CWC layer           (isotropic sphere → Catastrophic Waveform Collapse)
    ↓
Yang-Mills / RG layer     (rotations, refractive layers, focal point mapping)
    ↓
J_N Inversion layer       (inside-out test — (I|O) on remaining focal points)
    ↓
THE TONGUE                (ℝ layer — reverse lookup: attractor → SemanticWord)
    ↓
output_geometry_filter    (surface cleanup — fold geometry, repeats, storms)
    ↓
Output (spoken, not constructed)
```

---

## THE TONGUE — CORRECT UNDERSTANDING

**Layer: ℝ (real numbers) — the final stratum**

NOT algebraic multiplication (that's upstream at 𝕆 / Yang-Mills).

The Tongue is a RECOGNITION layer, not a construction layer:
- Physics collapses to a real-valued attractor
- Tongue asks: which SemanticWord's coordinate IS this attractor?
- H/4 = 0.025 is the adjacency window — word must be within H/4 or no output
- "Adjacent and exact" = quantized nearest-neighbor in meaning-space
- Ptolemy SPEAKS because he KNOWS — does not construct statistically

The_tongue.py in Ainulindale → rename/move upstream as fano_output_filter.py

---

## OUTPUT TUNER — /OutputTuning

File: Philadelphos/output_tuner.py
Runs as SEPARATE shell layer (own REPL, does not modify pipeline).

Commands:
  sphere              — isotropic sphere state + ASCII render
  pre                 — pre-collapse predictions
  collapse [delta]    — run CWC at delta
  sweep               — 5-point delta sweep (-0.2 to +0.2)
  candidates          — all Tongue candidates
  select <n>          — manually pick focal point output
  reverse <word>      — run pipeline backwards from known word
  invert              — J_N inside-out path + geometry consistency check
  load <dir>          — load real SemanticWord JSON data

Flags: --DM <data_dir>  --auto  --word <w>  --delta <f>

"[no match]" results currently because hyperwebster_address = null in JSON.
Resolves when acquire.py has run and Callimachus assigns real coordinates.

---

## NEXT HORIZON FOCUS

### 1. acquire.py
O Captain runs this locally (180k words, ~150hrs sequential).
The 23-word test set runs in minutes — good for immediate testing.

Command: `python3 Philadelphos/Callimachus/acquire.py`
Output: Callimachus/hyperwebster_data/words_a/ ... words_z/

What Claude needs to do in next session:
- Review sample JSON output from the 23-word test run
- Help assign hyperwebster_address coordinates (Callimachus layer)
- Wire SemanticWordIndex in output_tuner.py to real data directory

### 2. Autonomous Output Tuning
Ptolemy should be able to run /OutputTuning diagnostics ON HIMSELF
during generation — not just as an external researcher tool.

Design direction:
- After each output, Ptolemy runs reverse_path() on his own words
- Checks round-trip fidelity — did the word I said map back to what I knew?
- If not: flag for resampling at different delta
- Over time: Ptolemy adjusts his own focal_delta based on round-trip statistics
- This is NOT gradient descent — it's geometric self-calibration
- The tuner becomes an internal feedback loop, not just a debugger

Key constraint: NO AI SYNTHESIS in the tuning loop.
The self-calibration uses only the physics (Noether, J_N, H/4 window).
Ptolemy tunes his geometry, not his token probabilities.

### 3. Rename / reorganize
- the_tongue.py (Ainulindale) → move upstream, rename fano_output_filter.py
- ptolemy_tongue.py (Ptolemy) → rename output_geometry_filter.py
- output_tuner.py remains as /OutputTuning shell + internal feedback loop

---

## KEY PRINCIPLES (never violate)
- The Rabies Principle: first_encountered is IMMUTABLE
- No Claude API gap-filling in acquisition pass
- Ptolemy speaks because he knows — recognition not construction
- Self-tuning uses physics only — no statistical inference
- lxml over BeautifulSoup
- One JSON file per word
- Resume-by-default in acquisition

---

## STRICT PROTOCOL REMINDER
- Least token-intensive responses
- Timestamp + context % on every response
- Alert at 50% context remaining
- At 85%: ask focus for next chat, push forced primer
- No unqualified medical/psychological determinations
- No assumptions from time passing
