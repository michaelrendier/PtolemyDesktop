# T_Man — The Console

**Build** 2026-09-01 · **Files** `ptolemy_console.py` · **Commits** `116cd4b`,
`17d31a0`, `f09c876`

## What it is

PtolemyDesktop Core. A curses program with two tabs — the **Chat Tab** (talk to
Ptolemy) and the **ValaQuenta Tab** (the derivation browser). One object, the
**StitchBoard**, routes every line: to the monad, to a face, to a command, or
to a shell. Run standalone it draws its own tabs; installed in the desktop it
runs headless (`--port`) and the desktop draws them.

## Run it

```
python3 ptolemy_console.py            # standalone, both tabs
python3 ptolemy_console.py --port     # headless, frame protocol (the desktop drives it)
python3 ptolemy_console.py --selftest # route a few turns, print, exit
```

`--selftest` prints `status: monad:… active:… support:4 faces` then a handful of
routed turns, ending `selftest OK`.

In the Chat Tab: type and Enter. `Tab` opens the ValaQuenta Tab. `q` + Enter
quits.

## Words

| word | meaning |
|---|---|
| **StitchBoard** | the router. `route(line)` classifies a line and dispatches it; `drain()` pulls queued face posts; `review_faces()` is Ptolemy reading them. |
| **MonadLink** | the speaking channel. Wraps `VAPMIP.monad.Engine` if present, else a stand-in. `/monad off` detaches it; the harness stays live. |
| **ActiveHarness** | the tool/collaboration channel. Wraps `VAPMIP.harness.Harness` with the monad attached. `present(content, kind)`. |
| **SupportHarness** | the faces' room (see [the-faces.md](the-faces.md)). |
| **Chat Tab** | this window. Default channel points at the monad. |
| **ValaQuenta Tab** | the `DerivationBrowser`. **Archimedes runs it.** |
| **hibernated** | `--port` mode: no curses, plain-text frames in and out, the desktop renders. |
| `/diag` | one line: support status, active status. |
| `/tool <text>` | hand `<text>` to the active harness as a tool request. |
| `/enc <query>` | ask Archimedes — encyclopedia, `run <engine>.<eq>` to compute, `tour <engine>` for the guided walk. |

## Pathways

1. A line arrives. `StitchBoard.route()` checks it: a leading `/` is a command
   (`/diag`, `/tool`, `/faces`, `/poll`, `/enc`, `/proposals`, `/monad`);
   anything else goes to the monad channel — `MonadLink.say()`, or, when the
   monad is detached, a stand-in reply.
2. Each event-loop tick the console calls `board.drain()` (face posts) and
   `board.review_faces()` (Ptolemy's acks) and prints both into the Chat Tab.
3. `Tab` calls `Archimedes.run_tab(scr)` → `DerivationBrowser(scr, registry)`.
   `←`/`q` returns to the Chat Tab.
4. In `--port` mode the same `route()` runs, but replies leave as
   `{"t":"chat","text":…}` frames on stdout and the desktop reads them
   (see [the-console-connection.md](the-console-connection.md)).

## Notes

- The ValaQuenta registry loads lazily on first use, with stdout suppressed —
  in `--port` mode stdout is the frame pipe.
- The stand-in monad does not fabricate content; it reflects structure and
  tells you to attach VAPMIP for a real reply.
- `q` only quits from the Chat Tab, not from inside the ValaQuenta Tab.
