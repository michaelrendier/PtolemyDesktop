# T_Man — The Manual

The PtolemyDesktop build manual. One page per build.

**Rule: every build gets a T_Man page.** New module, new command, new wiring —
before the commit lands, its page lands here. Older builds get backfilled as we
pass over them.

This is not the `wiki/` (people, topics, provenance) and not `docs/`
(architecture essays). T_Man is operational: what the build is, how to run it,
the words it introduces, the pathways it opens. A reader should be able to use
the thing from its page alone.

## Voice

- Plain. Operators that work, code that works, a remembered vocabulary.
- **Words** — name every term the build introduces, one line each.
- **Pathways** — write the flows as sentences: *X does A, hands B to Y, Y posts
  C to Z.* Granular, traceable.
- No theory section. The math under the hood is not the subject of a manual
  page; the behaviour is.

## Page shape

See `_TEMPLATE.md`. Sections: **What it is** · **Run it** · **Words** ·
**Pathways** · **Notes**. Header line carries the build date, the files, and the
commit.

## Index

| page | build | files |
|---|---|---|
| [the-console.md](the-console.md) | PtolemyDesktop Core — the console, its two tabs, the stitchboard | `ptolemy_console.py` |
| [the-console-connection.md](the-console-connection.md) | The standardized connection — how the desktop drives the console; update sessions | `console_link.py` |
| [the-faces.md](the-faces.md) | The faces — chat-room identities that report; Ptolemy weighs and routes | `ptolemy_console.py` |
| [the-code-gate.md](the-code-gate.md) | CodeGate — faces propose code writes; Ptolemy approves | `ptolemy_console.py` |
