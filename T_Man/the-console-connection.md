# T_Man — The Console Connection

**Build** 2026-09-01 · **Files** `console_link.py` · **Commits** `f3825cd`,
`5589682`

## What it is

The standardized link between PtolemyDesktop (Qt / PGui) and the console. The
desktop spawns `ptolemy_console.py --port` over a pty and exchanges
newline-delimited JSON frames with it. The same link also runs **update
sessions**: feed it a new PyQt6 face file and it wires the missing PGui pieces.

## Run it

```
python3 console_link.py --roundtrip                # spawn + say + radio + feed_pyqt6; prints PASS
python3 console_link.py Phaleron/APISniff/APISniffCL.py   # run one update session, print the result JSON
```

`--roundtrip` ends `ROUNDTRIP: PASS`.

## Words

| word | meaning |
|---|---|
| **ConsolePort** | the transport. `send(frame)` writes one JSON line; `recv()` reads one. `.stdio()` is the console's own side. |
| **ConsoleClient** | the desktop's side. `attach()` spawns the console over a pty; a background thread reads every frame into a queue. `say`, `command`, `feed_pyqt6`, `ping`, `events`, `close`. |
| **PtolemyDesktopBridge** | the object the compositor passes in as `ptolemy=`. Carries a `ConsoleClient` plus the hooks the desktop already calls (`openFace`, `openShell`, `openSettings`, `close`). `pump()` on a QTimer drains radio/status frames to callbacks. `with_monad=False` detaches the speaking monad. |
| **update session** | `run_update_session(face.py)` — AST-parses a face file (never runs it), finds the Qt widgets it uses, adds the missing `P<Widget> = Q<Widget>` shims to `Pharos/PGui.py`, extracts its menu, flags Qt5-only names, registers it with the active harness. |
| **frame** | `{"t": <type>, …}`. In: `say`, `cmd`, `update`, `ping`, `attach`, `quit`. Out: `chat`, `radio`, `status`, `update.result`, `pong`, `error`. Each carries an `id` echoed back so a reply is matched to its request. |

## Pathways

1. `ConsoleClient.attach()` opens a pty, sets it raw and echo-off, spawns
   `ptolemy_console.py --port` with the slave as stdin/stdout, wraps the master,
   starts the reader thread, sends `{"t":"attach"}`.
2. `say(text)` sends `{"t":"say","text":…,"id":N}`; `_await("chat", id=N)` waits
   for the matching `chat` frame; radio/status frames that arrive meanwhile are
   put back for `events()`.
3. `feed_pyqt6(path)` sends `{"t":"update","path":…}`; the console runs
   `run_update_session` and returns one `update.result` frame with
   `face_classes`, `pgui_added`, `qt5_only`, `menu`.
4. `close()` sends `{"t":"quit"}`, terminates the process, closes the master,
   joins the reader — no daemon-thread abort at exit.
5. `PtolemyDesktopBridge.pump()` (QTimer) drains `client.events()`: `radio` →
   `on_radio`, `status` → `on_status`, `derive` → `on_derive`.

## Notes

- Update sessions never edit the existing PGui import tuple — they own a marked
  line `# --- QtWidgets auto-added by update sessions ---` and extend it.
- Only real QtWidgets classes get a `P` shim; QtCore/QtGui types are reported,
  not aliased; Qt5-only names (`QtWebKit`, `QDesktopWidget`, …) are flagged for a
  manual port.
- The frame reader is a background thread; long `Engine.generate` calls do not
  block the desktop.
