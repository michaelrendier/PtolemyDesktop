---
description: Launch the SMNNIP Derivation Engine console — curses GUI with live SymPy math
allowed-tools: Bash(python3 derivation.py:*), Bash(python3 -m Ainulindale.console.smnnip_proof_engine_console:*)
---

Launch the SMNNIP Proof Engine — curses console GUI wired to the live derivation engine with SymPy.

Run from the Ptolemy root:

```bash
cd /home/rendier/Ptolemy && python3 derivation.py
```

Or module form:

```bash
cd /home/rendier/Ptolemy && python3 -m Ainulindale.console.smnnip_proof_engine_console
```

The console provides:
- Full algebra tower: ℝ → ℂ → ℍ → 𝕆 → 𝕊 (Langlands Master Key)
- Live derivation engine: Lagrangian, Yang-Mills, Hamiltonian, Noether conservation
- SymPy rendering: press `s` to toggle symbolic math output
- MATH / TOPIC sort modes: press `m` to toggle
- Parameter input: type `param=value` in the input bar, `Enter` to apply
- Researcher options: `Tab` to cycle, `←→` to change values

## /derivation shortcut

This triggers the full SMNNIP derivation console via `python3 derivation.py` at the Ptolemy root.
