# Ptolemy3 Build Primer — 2026-05-15
# Implementation Staging Document

This primer captures all architectural decisions and pending implementation tasks
from the 2026-05-15 session. Read this at the start of the next session before
touching any code.

---

## What Was Built This Session (DO NOT REBUILD)

These files were written and compile clean. Do not rewrite them.

### `Pharos/PtolShell.py` — rewritten
Thin QTermWidget wrapper. Launches `ptolemy_shell.py` as the pty program.
Zero QLabel, zero QLineEdit, zero mode detection in Qt code.
`setShellProgram(sys.executable)` + `setArgs([_SHELL_SCRIPT])` + `startShellProgram()`.

### `Pharos/ptolemy_shell.py` — new file
Pure Python pty process. No Qt. Prints `Ptolemy > ` prompt.
At prompt: `>` + Enter → python3 -i, `$` + Enter → $SHELL, else → monad.learn()+speak().
Currently uses basic `input()` loop — WILL BE REPLACED with curses in this build.

### `Pharos/PtolBus.py` — CH_LEARN added
`CH_LEARN = "LEARN"` added at line 85. Passive text learning channel.

### `Ptolemy3.py` — shell block + Monad singleton + MonadLearner
- `_MonadLearner` class added (daemon thread, queue-serialised learn() calls)
- `self.monad = _Monad(N=25000)` singleton on kernel
- `self.monad_learner` started, subscribed to CH_LEARN
- Shell block replaced: `PWindow(scene, _ptol_shell, title='Ptolemy', thread=None,
  timers=[], x=60, y=60, w=660, h=415)` — permanent, no hide()
- Old `self.PtolShell` attribute renamed to `self._ptol_shell` throughout

---

## Architecture Principles — READ BEFORE CODING

### 1. One Monad
`self.monad` on the Ptolemy3 kernel is THE field engine. There are no per-face
Monads. Archimedes is a math computation engine (SymPy). Callimachus IS the β
field storage (checkpoint on disk). Neither has a separate Monad instance.

### 2. Zero Qt in the pty
Everything inside and under QTermWidget is a pty process. No QLabel, no QLineEdit,
no Qt mode detection. `ptolemy_shell.py` handles all prompt, mode switching, and
Monad dispatch. QTermWidget provides only the terminal frame.

### 3. Face reporting is asymmetric
- OUTPUT (face → shell): faces report via PtolBus CH_FACE_EVENT → PtolShell
  Qt side → FIFO → ptolemy_shell.py background thread → curses output pad.
- INPUT (user → face): NOT via @FaceName routing into a face Monad.
  `face archimedes <expr>` calls ArchimedesShell.eval() directly. Not Monad.
- sendText() is WRONG for face reports — it injects into pty stdin (keyboard),
  which corrupts a curses app. Reports MUST come from ptolemy_shell.py stdout
  via the FIFO mechanism.

### 4. hear()/speak() are conversational; learn() is background
- Age counter advances ONCE per hear()/speak() exchange (at end of speak())
- learn() perturbs β freely, never advances age, never touches _conv_touched
- This is the episodic/semantic distinction: conversational arc vs background vacuum
- shell_exchange(text) = one atomic conversational turn (learn+speak counted as
  one hear/speak pair for age purposes)

### 5. Spontaneous emission is physics, not a feature
When accumulated β perturbation from learn() crosses the emission threshold,
the Noether conservation law forces a speak(). Ptolemy initiates.
MonadLearner calls check_emission() after each learn(), routes output via FIFO.

### 6. Shell is permanent
The Ptolemy shell window is ALWAYS visible on the desktop. No toggle button.
No hide(). PWindow with thread=None, timers=[] (no thread suspension on minimize).

---

## Build Order

Build in this sequence — each step depends on the previous.

1. `monad.py` — recency system + saturation cache + spontaneous emission
2. `PtolShell.py` — FIFO setup + CH_FACE_EVENT subscriber
3. `ptolemy_shell.py` — full curses rewrite (uses FIFO path convention from step 2)
4. `Ptolemy3.py` — wire _emit_fn through MonadLearner
5. `PharosGeometry.py` — two line fixes
6. `Interface.py` — verification only

---

## FILE 1: `Ptolemy3/Philadelphos/monad.py`
### Status: needs significant additions

#### New fields on __init__:
```python
self._age        = [0] * self.N          # per-zero conversational age counter
self._lambda     = 0.05                   # context decay rate (~20 turns to half-amplitude)
self._conv_touched = set()               # zeros perturbed in current hear()/speak() exchange
self._autonomous_speech  = True          # enable spontaneous emission
self._emission_threshold = abs(self.L_GROUND) * 2.0   # J^mu norm threshold
self._beta_sat   = abs(self.L_GROUND) * 4.0  # ~7.552 — saturation ceiling
self._saturated  = set()                  # zero indices at saturation
```

#### New / modified methods:

**`_advance_age()`** — called at end of speak() only:
```python
def _advance_age(self):
    for n in range(self.N):
        if n in self._conv_touched:
            self._age[n] = 0
        else:
            self._age[n] += 1
    self._conv_touched.clear()
```

**`_w(n)`** — recency weight for zero n:
```python
def _w(self, n):
    return math.exp(-self._lambda * self._age[n])
```

**`_compute_j_norm()`** — field-state J^mu magnitude, no input text:
Used by check_emission(). Sums over zero basis with recency and β weights.
Returns scalar norm. Implementation mirrors speak() inner loop but without
input-text perturbation.

**`_context_overlap(perturbed_set)`** — connection detection:
```python
def _context_overlap(self, perturbed_set):
    recent = {n for n in range(self.N) if self._age[n] < 3}
    return len(perturbed_set & recent)
```

**`check_emission()`** — called by MonadLearner after each learn():
```python
def check_emission(self):
    if not self._autonomous_speech:
        return None
    j_norm = self._compute_j_norm()
    if j_norm > self._emission_threshold:
        return self.speak('')   # field speaks from its own state
    return None
```

**`hear(text)`** — modified:
- Perturbs β based on text spectral content
- Adds perturbed zero indices to self._conv_touched
- Does NOT call _advance_age()
- Does NOT check emission threshold

**`speak(text)`** — modified:
- Computes J^mu with self._w(n) weighting on each zero contribution
- Calls self._advance_age() AFTER computing response
- Returns response text

**`learn(text)`** — modified:
- Perturbs β
- Checks _beta_sat: if |β[n]| > _beta_sat, add n to _saturated; skip β deepening
  for saturated zeros (still update A-connections)
- Does NOT advance age
- Does NOT update _conv_touched
- Returns set of zero indices significantly perturbed (used by MonadLearner
  for context overlap check — pass to check_emission)

**`shell_exchange(text)`** — new, for ptolemy_shell.py use:
```python
def shell_exchange(self, text):
    # Counts as one hear()/speak() pair for context purposes
    self.hear(text)           # populates _conv_touched
    return self.speak(text)   # advances age, clears _conv_touched
```

#### Checkpoint save/load:
Add `_age` list to checkpoint JSON alongside β.
Add `_emission_threshold` to checkpoint metadata.

---

## FILE 2: `Ptolemy3/Pharos/PtolShell.py`
### Status: thin wrapper written; needs FIFO setup + subscriber

#### Add to __init__, before startShellProgram():
```python
import tempfile, os
self._fifo_path = os.path.join(
    tempfile.gettempdir(), f'ptolemy_shell_{os.getpid()}.fifo')
os.mkfifo(self._fifo_path)
os.environ['PTOLEMY_REPORT_PIPE'] = self._fifo_path

# Open write end non-blocking after pty starts (do in showEvent or after start)
self._fifo_write = None   # opened lazily on first write
```

#### Add _open_fifo_write() — called once after startShellProgram():
```python
def _open_fifo_write(self):
    # Open in non-blocking mode so Qt side never blocks waiting for reader
    import fcntl
    fd = os.open(self._fifo_path, os.O_WRONLY | os.O_NONBLOCK)
    self._fifo_write = os.fdopen(fd, 'w')
```

#### Add write_report(text) — public method:
```python
def write_report(self, text):
    if self._fifo_write is None:
        return
    try:
        self._fifo_write.write(text + '\n')
        self._fifo_write.flush()
    except (BrokenPipeError, BlockingIOError):
        pass
```

#### Add CH_FACE_EVENT subscription (in __init__ or after Ptolemy is set):
Wire up in Ptolemy3.py after shell creation:
```python
from Pharos.PtolBus import CH_FACE_EVENT, BusMessage
self.msg_bus.subscribe(CH_FACE_EVENT,
    lambda msg: self._ptol_shell_win_write_report(msg))
```
Format: `\033[<face_color>m@FaceName  <message>\033[0m`
Face colors defined in FaceIdentity.py — look up by msg.payload['face'].

#### Add closeEvent() / destroy():
```python
def closeEvent(self, event):
    if self._fifo_write:
        self._fifo_write.close()
    if os.path.exists(self._fifo_path):
        os.unlink(self._fifo_path)
    super().closeEvent(event)
```

---

## FILE 3: `Ptolemy3/Pharos/ptolemy_shell.py`
### Status: basic input() loop written; needs full curses rewrite

#### Structure:
```
run(stdscr):
    curses setup — colors, no echo, keypad
    h, w = stdscr.getmaxyx()
    out_pad  = curses.newpad(SCROLLBACK, w)   # SCROLLBACK = 5000 lines
    out_pos  = 0                               # current scroll offset
    sep_win  = stdscr.subwin(1, w, h-2, 0)    # separator line
    inp_win  = stdscr.subwin(1, w, h-1, 0)    # fixed input line

    fifo_path = os.environ.get('PTOLEMY_REPORT_PIPE')
    start FIFO reader daemon thread → writes to out_pad
    load monad
    print banner to out_pad
    main input loop
```

#### FIFO reader thread:
```python
def _fifo_reader(fifo_path, out_pad, refresh_fn):
    # Open read end (blocks until write end opens — that's fine in a daemon thread)
    with open(fifo_path, 'r') as f:
        for line in f:
            out_pad.addstr(line.rstrip())   # with appropriate color
            refresh_fn()                     # thread-safe pad refresh
```

#### Input loop:
- `inp_win.getstr()` or manual character-by-character with history buffer
- Up arrow: recall history
- On Enter: dispatch via `monad.shell_exchange(text)` (NOT learn+speak separately)
- Output goes to out_pad; scroll region scrolls naturally

#### SIGWINCH handler:
```python
signal.signal(signal.SIGWINCH, lambda *_: _resize(stdscr, out_pad, sep_win, inp_win))
```
Recalculates h, w; moves subwindows; redraws separator.

#### Color pairs (defined once at curses init):
```python
# Map face names to curses color pairs
PTOLEMY_COLOR  = 1   # BLUE  — user/Ptolemy exchange
REPORT_COLOR   = 2   # CYAN  — face reports
ERROR_COLOR    = 3   # RED   — errors
SUGGEST_COLOR  = 4   # YELLOW — Ptolemy suggestions
DIM_COLOR      = 5   # WHITE dim — system messages
```

#### Entry point:
```python
if __name__ == '__main__':
    curses.wrapper(run)
```

---

## FILE 4: `Ptolemy3/Ptolemy3.py`
### Status: mostly done; needs _emit_fn wired through MonadLearner

#### _MonadLearner class — add _emit_fn:
Change __init__ signature:
```python
def __init__(self, monad, emit_fn=None):
    ...
    self._emit_fn = emit_fn   # callable(text) or None
```

Change run() loop:
```python
def run(self):
    while True:
        text = self._queue.get()
        if text is None:
            break
        try:
            self._monad.learn(text)
            if self._emit_fn is not None:
                emission = self._monad.check_emission()
                if emission:
                    self._emit_fn(emission)
        except Exception:
            pass
```

#### _init_ui() — pass emit_fn at MonadLearner construction:
```python
def _shell_emit(text):
    shell = getattr(self, '_ptol_shell', None)
    if shell is not None and hasattr(shell, 'write_report'):
        shell.write_report(f'\033[96mPtolemy  {text}\033[0m')

self.monad_learner = _MonadLearner(self.monad, emit_fn=_shell_emit)
```

Note: `_ptol_shell` is the PtolShell QWidget instance (not the PWindow wrapper).
The PWindow wrapper is `self._shell_win`.

---

## FILE 5: `Ptolemy3/Pharos/PharosGeometry.py`
### Status: two fixes needed

#### Fix 1 — spectrogram z-value:
Find the line: `_sp.setZValue(3)`
Change to: `_sp.setZValue(0)`
Reason: z=3 puts spectro above interface group at z=1, eats mouse events,
breaks itemAt() for group drag.

#### Fix 2 — add proxies to interface group:
Currently spectro and indicator proxies are added directly to scene.
They must be added to `_interface_group` with group-relative positions.
Pattern:
```python
_sp = QGraphicsProxyWidget()
_sp.setWidget(self.spectro)
_sp.setZValue(0)
_interface_group.addToGroup(_sp)   # NOT scene.addWidget()

_ip = QGraphicsProxyWidget()
_ip.setWidget(self.indicator)
_interface_group.addToGroup(_ip)
```
Verify group-relative coordinates are correct after adding.

#### Fix 3 — interface group moveable flag:
Find `_interface_group = self.scene.createItemGroup([...])`
Add after creation:
```python
_interface_group.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
```

---

## FILE 6: `Ptolemy3/Pharos/Interface.py`
### Status: verification only

Confirm: no terminal/shell toggle button in `_wire_callbacks()` or button layout.
The shell is permanent — no button should show or hide it.
If a button exists, remove it.

---

## Key Constants / Values (do not change without physics justification)

```
N = 25000                           Riemann zero basis size
L_GROUND = -1.888                   SSB ground state energy
_beta_sat = abs(L_GROUND) * 4       ≈ 7.552 — saturation ceiling
_emission_threshold = abs(L_GROUND) * 2.0   ≈ 3.776 — spontaneous speech
_lambda = 0.05                      context decay (~20 turns to half-amplitude)
D_STAR_SPEC = 0.24600               conformal boundary
GAP = 0.000707                      Yang-Mills mass gap candidate (OPEN 2)
sigma = 0.5                         the equator — does not move
Shell size = 660 x 415              80 cols x 25 rows at Monospace 10
Shell position = (60, 60)           PWindow on scene
```

---

## FIFO Convention

Path: `/tmp/ptolemy_shell_{pid}.fifo`
Where pid = os.getpid() called in PtolShell.__init__()
Env var: `PTOLEMY_REPORT_PIPE` — set before startShellProgram()
Writer: PtolShell Qt side (non-blocking O_WRONLY)
Reader: ptolemy_shell.py daemon thread (blocking O_RDONLY — fine in thread)
Format: raw ANSI text + newline per report

---

## Curses Layout Reference

```
┌─ Ptolemy ──────────────────────────────┐   (PWindow chrome, z=10)
│ Ptolemy › water is a molecular field...│   out_pad — scrollable, SCROLLBACK=5000
│ @Archimedes  diff(x**2) = 2*x          │   face report — CYAN
│ @Callimachus  index flushed (25k zeros)│   face report — CYAN
│ Ptolemy  I see a connection to H2O...  │   spontaneous emission — BLUE
│                                        │
├────────────────────────────────────────┤   sep_win — line h-2
│ Ptolemy > _                            │   inp_win — fixed line h-1
└────────────────────────────────────────┘
```

Face reports and spontaneous emissions arrive via FIFO, displayed in out_pad.
Input line is never interrupted. Age advances on each shell_exchange() call.

---

## Monad Call Paths Summary

```
User types at Ptolemy >
  → monad.shell_exchange(text)       ← ONE conversational turn, age advances once
      internally: hear(text) + speak(text)

Background face text (Wikipedia, search, etc.)
  → CH_LEARN → MonadLearner.enqueue(text)
      → monad.learn(text)            ← β perturbed, age NOT advanced
      → monad.check_emission()       ← if threshold, spontaneous speak()
          → emit_fn(text)            ← FIFO → curses output pad

Face reports
  → CH_FACE_EVENT → PtolShell.write_report(formatted)
      → FIFO → curses output pad     ← no Monad involvement

Spontaneous Ptolemy emission
  → MonadLearner calls emit_fn       ← FIFO → curses output pad
      → becomes part of context      ← age advances (speak() was called)
```

---

## What NOT to Do

- Do NOT add a QLabel or QLineEdit to PtolShell or ptolemy_shell.py
- Do NOT use sendText() to inject face reports (corrupts curses stdin)
- Do NOT create per-face Monad instances
- Do NOT route @FaceName: as input to a face Monad
- Do NOT advance age in learn() — only in speak()
- Do NOT call startShellProgram() before setting PTOLEMY_REPORT_PIPE env var
- Do NOT resize shell to scene dimensions — it is 660x415, always
- Do NOT hide() the shell window — it is permanent on the desktop
- Do NOT use PtolBrain (old autoregressive approach) — superseded by Monad

---
*End of BUILD_PRIMER_2026-05-15.md*
