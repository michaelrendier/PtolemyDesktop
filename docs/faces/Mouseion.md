# Mouseion

**Historical figure:** The Mouseion — the research institute of the Library of Alexandria (precursor to the modern museum/university)  
**Responsibility:** Flask web interface (thewanderinggod.tech), OpenGL viewer, library display

---

## Overview

Mouseion is Ptolemy's outward-facing Face. It hosts the Flask web application at `thewanderinggod.tech` and provides browser-based access to Ptolemy's content and visualization output. It is also the display target for Alexandria's rendering pipeline.

---

## Module Tree

```
Mouseion/
├── TWG/                          ← The Wandering God — Flask application
│   ├── WanderingRoutes.py        ← URL routing
│   ├── WanderingFunctions.py     ← View functions
│   ├── WanderingForms.py         ← Form definitions
│   ├── WanderingConfig.py        ← Flask configuration
│   ├── menuapp.py                ← Menu application entry point
│   ├── run_flask.sh              ← Launch script
│   ├── templates/                ← Jinja2 HTML templates
│   └── static/                   ← CSS, JS, images, fonts, PDFs
├── Library.py                    ← Library content management
├── WikiGroup.py                  ← Wikipedia group fetcher
├── GLViewer.py                   ← OpenGL viewer widget
├── GLGUI.py                      ← OpenGL GUI wrapper
└── Games/
    ├── PlayingCards/             ← Card game utilities
    └── RogueAI/                  ← Roguelike game engine
```

---

## Flask Application (TWG)

`thewanderinggod.tech` — public-facing Flask site.

Key routes defined in `WanderingRoutes.py`:
- Article browsing and editing
- Category management
- Herb database
- Library viewer
- Admin panel

**TLS:** Kryptos manages the TLS certificate. All HTTP → HTTPS redirect enforced.

---

## Alexandria Pipe

Alexandria renders to Mouseion via the pipe set in `Ptolemy3.py`:

```python
from Alexandria import set_mouseion_pipe
set_mouseion_pipe(mouseion_instance)
```

Rendered frames (fractals, Lorenz, spectrograph) are delivered to Mouseion's viewer endpoint for browser display.

---

## Settings

`Mouseion/settings/settings.json`

| Key | Description |
|---|---|
| `flask_host` | Bind address (default: 0.0.0.0) |
| `flask_port` | HTTP port (default: 5000) |
| `tls_enabled` | HTTPS via Kryptos certificate |
| `debug_mode` | Flask debug flag (never True in production) |

---

## Dependencies

- Flask
- Jinja2
- PyQt5 / PyOpenGL (GLViewer)
- Alexandria (render pipe source)
- Kryptos (TLS)
- Pharos/PtolBus (event subscriber for live display updates)
