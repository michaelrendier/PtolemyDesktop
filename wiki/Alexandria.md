# Alexandria

**Historical figure:** The Library of Alexandria  
**Responsibility:** Visualization — OpenGL rendering, fractal generation, engine registry, Mouseion pipe

---

## Overview

Alexandria is Ptolemy's visualization Face. It owns all rendering pipelines and exposes them to Mouseion for web display. Alexandria has access to ALL Ptolemy engines — mathematical, physical, and signal — and renders their output as visual artifacts.

The core design principle: **a fractal is an attractor representation of a process.** Every engine in Ptolemy has a corresponding visualization in Alexandria.

---

## Modules

| Module | Description |
|---|---|
| `Core.py` | Engine registry — registers and retrieves all Alexandria renderers |
| `FractalRenderer.py` | UF formulary renderer — Mandelbrot, BurningShip, Julia, Newton, LorenzProjection |
| `Earth.py` | Geographic visualization — city/location overlays |
| `EarthItem.py` | Individual map item — location marker with metadata |
| `GoogleEarth.py` | Google Earth integration layer |

---

## Engine Registry Pattern

```python
from Alexandria import register_engine, get_engine, set_mouseion_pipe

# Register a renderer
register_engine("lorenz", LorenzRenderer)

# Pipe output to Mouseion web interface
set_mouseion_pipe(mouseion_instance)
```

All engines registered at import. Mouseion pipe set at runtime by `Ptolemy3.py`.

---

## FractalRenderer

Implements the public UF formulary collection (`.ufm` files in `Archimedes/Maths/Formula/UFformulary/`).

| Formula | Description |
|---|---|
| Mandelbrot | Standard z² + c iteration |
| BurningShip | `abs(z)² + c` variant |
| Julia | Fixed-c parameter set |
| Newton | Newton basin fractal — maps to Stirling basin engine |
| LorenzProjection | 2D projection of Lorenz attractor trajectory |

Parameters per renderer: `width`, `height`, `max_iter`, `center`, `zoom`, formula-specific params.

---

## Views (planned)

| View | Data source |
|---|---|
| Lorenz-Stirling | `Archimedes/Maths/LorenzStirling.py` |
| Noether Spectrograph | `Archimedes/Engines/noether_spectrograph.py` |
| Bifurcation Diagram | `LorenzStirling.BifurcationAnalysis` |
| Multidimensional Decomposition | SMNNIP CD tower layers |
| Fractal Generator | UF formulary full collection |

All views pipe to Mouseion via `set_mouseion_pipe()`.

---

## Settings

`Alexandria/settings/settings.json` — managed by `Pharos/ptolemy_settings.py`.

Key settings: `default_renderer`, `render_width`, `render_height`, `max_iterations`, `mouseion_pipe_enabled`.

---

## Dependencies

- PyQt5 (rendering surface)
- numpy (array operations)
- Pharos/PtolBus (event publishing)
- Archimedes engines (data sources)
- Mouseion (display target)
