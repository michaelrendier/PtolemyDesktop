---
description: Launch the Ainulindalë sonification engine — maps SMNNIP physics to sound
allowed-tools: Bash(python3 Ainulindale/sonification/*:*), Bash(python3 -m Ainulindale.sonification.*:*)
---

# /cymatics — Ainulindalë Sonification Engine

Launches the Ainulindalë sonification pipeline. Maps the SMNNIP Cayley-Dickson
algebra tower to a particle-instrument orchestration (no floating point in signal chain).

## Usage

```bash
# Movement I — Introduction (particles introduced solo, Peter and the Wolf structure)
python3 Ainulindale/sonification/ainulindale_sonification_mv1.py

# Mars sonification
python3 Ainulindale/sonification/ainulindale_mars.py

# Electron orbitals
python3 Ainulindale/sonification/ainulindale_electron_orbitals.py

# Beginning of light
python3 Ainulindale/sonification/ainulindale_beginning_of_light.py
```

## Architecture

All frequencies: exact rational arithmetic (fractions.Fraction)
All durations: exact integer sample counts
WAV output: pure PCM 16-bit signed integer — NO floating point in signal chain

## Algebra → Instrument mapping

| Stratum | Gauge | Particle | Instrument |
|---------|-------|----------|------------|
| ℝ | trivial | Higgs | Cello (low, sustained) |
| ℂ | U(1) | Photon | Flute (high, pure) |
| ℍ | SU(2) | W±, Z⁰ | French Horn / Tuba |
| 𝕆 | SU(3) | Gluons (8) | Percussion (8 voices) |

## Noether integration

Conservation violation events → amplitude anomalies in output WAV.
Quasi-particle rests follow Fibonacci ratios (Gravinon = 144/89 beats).
