# T_Man — The Faces

**Build** 2026-09-01 · **Files** `ptolemy_console.py` · **Commit** `65e9682`

## What it is

Four named identities that speak in the Chat Tab. They are **not processes** —
they are chat-room members. They post passive reports and warnings; Ptolemy
weighs their opinions and routes any action through his harness. Only Archimedes
acts on its own.

## Run it

```
python3 ptolemy_console.py --selftest    # shows the faces, a radio check, a poll
```

In the Chat Tab:

```
/faces                     # the roster + each face's last drift
/radio                     # run a check now — every face posts a line
/poll <topic>              # weighted opinions; Ptolemy names who to follow
/enc <query>               # ask Archimedes
```

## Words

| word | meaning |
|---|---|
| **Face** | `name`, `role`; `probe() -> drift 0..1`; `opinion(topic) -> (stance, weight)`; `act(request)` only if `active`. A drift over `THRESHOLD` (0.25) posts a `HARDENING` line tagged with an intrusion type. |
| **FacePost** | one line from a face: `who`, `level` (`info` / `warn` / `hardening`), `text`, `intrusion`, `weight`. Renders as `« Name » …`. |
| **Aulë** | The Forge — process & backlog monitor. Passive. |
| **Mandos** | The Watchdog — heartbeat & supervisor priority. Passive. |
| **Phaleron** | The Librarian (Demetrius of Phaleron, first head of the Library of Alexandria) — Tool Master, catalogue, user portal. Passive, advises. |
| **Archimedes** | The Professor / The Encyclopedia — the one face that acts; runs the ValaQuenta Tab. |
| **review_faces()** | Ptolemy reading the room: for each unacked `warn`/`hardening` post he routes it through the active harness once and prints `ptolemy: ack «face» [type] → …`. |
| **poll_opinions(topic)** | asks every face; sorts by weight; a face with no topical view is a weak voice, so a face with a real stance leads. |

## Pathways

1. `SupportHarness._loop` (daemon thread) calls `radio_check()` every ~8 s: each
   `Face.report()` runs its `probe()` and returns a `FacePost`; the line goes to
   `board.sink`.
2. Each console tick `board.drain()` prints the sink into the Chat Tab, then
   `board.review_faces()` routes any warning through the active harness and
   prints Ptolemy's ack.
3. `/poll open the tool file` → `poll_opinions` → Phaleron 0.90 "in my catalogue
   — proceed via the portal", the rest 0.20 "no strong view" → `ptolemy directs:
   follow Phaleron`.
4. `/enc <query>` → `Archimedes.act()` (see [the-console.md](the-console.md)).

## Notes

- `register(name, probe, adjust)` still takes a bare probe — it wraps it as a
  passive `Face`.
- `note_portal(load)` feeds Phaleron the current tool/portal load.
- The faces here are the console's SupportHarness set; the wider `docs/faces/`
  roster (Alexandria, Tesla, …) is a separate layer.
