# PtolShell — Command Shell & MetaPrompt Routing

`Pharos/PtolShell.py`

---

## Overview

PtolShell is the QTermWidget-backed command shell at the heart of the Ptolemy UI. It is not a terminal emulator replacement — QTermWidget owns all display, pty, ANSI, and interactive programs. PtolShell's mode detector intercepts only the **input bar**: the single-line `QLineEdit` above QTermWidget.

The key design: **Faces are shell users**. Each Face can POST at boot and speak through the shell via Face C/O mode. The Ptolemy buffer is its own conversation space — not piped to QTermWidget.

---

## MetaPrompt Modes

Mode is determined by the prefix of the input:

| Prefix | Mode | Label | Color | Backend |
|---|---|---|---|---|
| (none) | Ptolemy C/O | `Ptolemy` | Royal Blue | LSH inference — own CyclicContextBuffer |
| `>>>` | Python3 REPL | `Python3` | Green | `python3 -i` pty |
| `$` | System C/O | `Shell` | Yellow | `/bin/bash` pty |
| `#` | Root C/O | `Root` | Red | `/bin/bash --login` pty |
| `@Name` | Face C/O | `@FaceName` | Face color | Face speaks in shell |

**Ptolemy C/O** is the default. It behaves like a BBS-style buffered conversation: stateful, not a pty. Commands are `/slash` prefixed. This is where LLH inference lives.

**Face C/O** format:
```
@Archimedes: index rebuild complete
@Callimachus→@Archimedes: index ready
```

---

## Ptolemy C/O — Inference Pipeline

Input → `_ptolemy_respond()`:

```
input text
  → SedenionGate.close()          # gate: closes on submit
  → NoetherChainInput             # Philadelphos/noether_chain_input.py
  → PtolBrain.query()             # LSH inference — PtolBrain.py
  → PhiladelphosConsole (fallback)# Path B — when no weights loaded
  → PtolemyTongue.filter()        # FoldGeometry text repair
  → _ccb_add(prompt, response)    # CyclicContextBuffer.append()
  → SedenionGate.open()           # gate: opens after response
  → response_display()            # write to terminal
```

`_ptol_busy` flag gates Qt-side: while True, input bar is disabled and gate indicator is lit.

**SedenionGate:** `threading.Event`. Closed (prompt submission) / open (response delivered). AEAD-like: prompt cannot enter while previous response is still generating.

---

## Slash Commands (Ptolemy C/O)

| Command | Action |
|---|---|
| `face <name>` | Open a Face window |
| `faces` | List all registered Faces |
| `bus` | Show PtolBus status |
| `/math` | Open Archimedes SymPy REPL |
| `/data <path>` | Run DataInput training pipeline |
| `help` | Command reference |

---

## DataInput (`/data`)

Runs `handle_data_input()` in a background QThread. On completion:

```python
def _run():
    handle_data_input(corpus_path=corpus_path, ...)
    self._brain = None                    # invalidate brain cache
    QTimer.singleShot(0, lambda: _write('[DataInput] Training complete.', '#aaffcc'))
```

`QTimer.singleShot(0, fn)` — thread-safe bridge. Schedules UI write on Qt main event loop from the background thread.

`self._brain = None` — forces next inference call to reload PtolBrain from disk with fresh weights.

---

## Face Registration (POST)

Faces register themselves at boot via `FaceIdentity.py`:

```python
from Pharos.FaceIdentity import DaemonIdentity, register_face

register_face(DaemonIdentity(face_id='archimedes', display='Archimedes'))
```

Registered Faces appear in `faces` command output and can use Face C/O mode (`@Archimedes`).

---

## Thread Architecture

| Thread | Name | Purpose |
|---|---|---|
| Main | Qt UI | Input bar, terminal display |
| `_AinurThread` | Ainur | Claude API streaming — chunk by chunk |
| `_GeminiThread` | Gemini | Gemini streaming generation |
| `_DataInputThread` | DataInput | LSH model training |
| `_BrainThread` | PtolBrain | LSH inference (when loaded) |

All threads emit Qt signals back to main thread. Never write to Qt widgets directly from background threads.

---

## PtolBrain Cache

`self._brain` — module-level singleton. Loaded lazily on first inference call:

```python
if self._brain is None:
    from Pharos.PtolBrain import PtolBrain
    self._brain = PtolBrain()
```

Invalidated (`self._brain = None`) after DataInput training completes. Next inference call loads fresh weights.

---

## Color Constants

| Mode | Color | Reference |
|---|---|---|
| Ptolemy C/O | Royal Blue `#1a2a6c` | `PtolColor.ROYAL_BLUE` |
| Python3 REPL | `#00ff66` | `ShellModeColor.PYTHON` |
| System Shell | `#ffcc00` | `ShellModeColor.SHELL` |
| Root Shell | `#ff4444` | `ShellModeColor.ROOT` |
| Ptolemy response | `#aaffcc` | `PtolColor.RESPONSE` |
| Error | `#ff5555` | `PtolColor.ERROR` |

---

## Dependencies

- `QTermWidget` (terminal widget — optional, graceful degradation)
- `Pharos.PtolBus` (inference event publishing)
- `Pharos.PtolBrain` (LSH inference engine)
- `Pharos.FaceIdentity` (Face registration)
- `Pharos.PtolColor` (colour palette)
- `Philadelphos.noether_chain_input` (NoetherChainInput)
- `Philadelphos.data_input` (DataInput pipeline)
- `Philadelphos.Ainur.ainur` (Claude API)
- `Philadelphos.Gemini.gemini` (Gemini API)
