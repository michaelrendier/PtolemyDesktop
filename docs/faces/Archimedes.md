# Archimedes

**Historical figure:** Archimedes of Syracuse — mathematician, physicist, engineer  
**Responsibility:** Mathematics, science, signal processing, spectral analysis

---

## Overview

Archimedes is Ptolemy's mathematics and science Face. It provides computation engines, formula libraries, signal processing tools, and a live SymPy REPL shell. All mathematical engines used by other Faces originate here.

---

## Module Tree

```
Archimedes/
├── Maths/
│   ├── ArchimedesShell.py       ← /math SymPy REPL, threaded eval
│   ├── LorenzStirling.py        ← Lorenz attractor + Stirling basin engines
│   ├── Calculus.py
│   ├── LinearAlgebra.py
│   ├── Matrix.py
│   ├── Trigonometry.py
│   ├── Thermodynamics.py
│   ├── Electromagnetism.py
│   ├── StatisticsAndProbability.py
│   ├── GraphPlot.py
│   ├── Constants.py
│   ├── Formula/
│   │   └── UFformulary/         ← Full UF public formula collection (.ufm)
│   └── Sequences/, Series/      ← Number sequences and infinite series
├── Engines/
│   ├── noether_engine/          ← Noether symmetry/conservation engine
│   └── noether_spectrograph.py  ← Spectral visualization of conserved quantities
├── SpectroSecurity/
│   ├── LiveSpectrogram.py       ← Real-time audio spectrogram
│   └── WaveSpectrogram.py       ← File-based spectrogram
└── Actuary/
    └── Actuary.py               ← Statistical/actuarial functions
```

---

## ArchimedesShell

Live SymPy REPL accessible via `/math` command in PtolShell.

```
Ptolemy> /math
Archimedes Math Shell — SymPy 1.x
>>> integrate(sin(x), x)
-cos(x)
>>> solve(x**2 - 4, x)
[-2, 2]
```

Evaluation is threaded — does not block the main Pharos UI. Results published to PtolBus `CH_ARCHIMEDES`.

---

## LorenzStirling

Standalone module combining three engines for SMNNIP visualization:

| Engine | Function |
|---|---|
| `LorenzAttractorEngine` | Trajectory, Lyapunov exponent, Poincaré section, rho sweep |
| `StirlingBasinEngine` | Newton's method on S₁₀(z), 8 root basins |
| `BifurcationAnalysis` | Order windows, Lyapunov sign, bifurcation diagram |

Used by Alexandria FractalRenderer and Ainulindale SMNNIP pipeline.

---

## Noether Engine

Full implementation of Noether's theorem — finds conserved quantities from Lagrangian symmetries.

| Submodule | Description |
|---|---|
| `algebra/` | Cayley-Dickson, Clifford, Lie algebras |
| `core/` | Charge, current, field, Lagrangian, symmetry, variation |
| `spacetime/` | Minkowski, Euclidean, curved, ADM formulations |
| `quantum/` | Anomaly detection, Ward-Takahashi identities |
| `theorems/` | First theorem, Second theorem, Bessel-Hagen extension |

---

## UFformulary

The complete public UF (UltraFractal) formula collection — hundreds of `.ufm` files. Alexandria's FractalRenderer reads these directly to generate fractal visualizations.

---

## Settings

`Archimedes/settings/archimedes_shell/settings.json`

| Key | Description |
|---|---|
| `sympy_timeout_s` | Max eval time before thread kill |
| `output_format` | `latex` / `unicode` / `ascii` |
| `publish_to_bus` | Publish results to PtolBus |

SpectroSecurity settings: `Archimedes/SpectroSecurity/settings.json`

---

## Dependencies

- SymPy (math shell)
- NumPy / SciPy (numerical computation)
- Matplotlib (GraphPlot)
- PyAudio / sounddevice (SpectroSecurity)
- Pharos/PtolBus (result publishing)
- Alexandria (visualization target)
