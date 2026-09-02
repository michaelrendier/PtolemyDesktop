# T_Man — The Code Gate

**Build** 2026-09-01 · **Files** `ptolemy_console.py` · **Commit** `442e5a2`

## What it is

Faces can read repository code and **propose** writes to it. Nothing lands on
disk until Ptolemy approves. `.py` files only; the monad state, credentials,
`.git` and the venv are unreachable.

## Run it

In the Chat Tab:

```
/proposals              # pending code proposals
/diff <id>              # the unified diff for one
/approve <id>           # write it (backs up the original first)
/reject <id> [why]      # drop it
```

`--selftest` exercises the loop: Archimedes reads `two_objects.py`, proposes
folding two functions into one (`+2 -6`), Ptolemy approves, the file is
rewritten, a backup is verified, a denied path is rejected.

## Words

| word | meaning |
|---|---|
| **CodeGate** | the gate. Scope = `PTOLEMY_CODE_ROOT` (default: the ThePlace root). `.py` only. Denies `.git`, `.venv`, `__pycache__`, `secrets`, and names matching `*_token*`, `*_secret*`, `*_key*`, `*.bin`. |
| **Proposal** | `pid`, `face`, `path`, `reason`, `new_text`, `diff`, `status` (`pending` / `applied` / `rejected`). A full-file replacement plus its unified diff. |
| **Face.read_code(gate, path)** | open — returns the file text. |
| **Face.propose(gate, path, new_text, reason)** | returns a pending `Proposal`. |
| **gate.approve(pid)** | backs up `<file>.bak.<ts>`, writes `new_text`, marks `applied`, returns `applied #pid «face» path (+A -D)`. |

## Pathways

1. A face calls `read_code` to see the current file, then `propose` with the
   replacement text and a one-line reason. `CodeGate._resolve` checks the path
   is in scope, is `.py`, and hits no deny rule; `difflib` builds the unified
   diff; the `Proposal` is queued `pending`.
2. `/proposals` lists them; `/diff <id>` shows the diff.
3. `/approve <id>` → `gate.approve` writes a `.bak.<timestamp>` copy, then the
   new text; status → `applied`.
4. `/reject <id> why` marks it `rejected`; nothing is written.

## Notes

- Widen or narrow the reach with `PTOLEMY_CODE_ROOT`.
- A proposal is a full-file replacement; keep the diff small — Ptolemy sees it
  before approving.
- Reads are always allowed within scope; only writes are gated.
