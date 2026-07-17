---
description: Launch the Ainur REPL — Claude as a Ptolemy feature (requires AINUR_TOKEN=<Anthropic API key>)
allowed-tools: Bash(python3 -m Philadelphos.Ainur.ainur:*)
---

Launch the Ainur REPL — Claude Opus 4.6 integrated as a Ptolemy component.

Set your Anthropic API key first:

```
export AINUR_TOKEN=sk-ant-...
```

Then run from the Ptolemy root:

```
cd /home/rendier/Ptolemy && python3 -m Philadelphos.Ainur.ainur
```

Or import in code:

```python
from Philadelphos.Ainur import Ainur

ainur = Ainur()                    # prints: Managed by: claude-opus-4-6  [SMNNIP:on]  [ready]
print(ainur.status.header())

# Streaming chat
for chunk in ainur.stream("Derive the SMNNIP Noether current."):
    print(chunk, end="", flush=True)

# Single-shot
response = ainur.chat("What is the GUT convergence scale?")
```

Features:
- Model: `claude-opus-4-6` with adaptive thinking
- Prompt caching: Ptolemy/SMNNIP system context cached at Anthropic
- Tools: `smnnip_lagrangian`, `smnnip_noether`, `smnnip_rg_flow`
- Conversation history across turns
- Status header: `Managed by: claude-opus-4-6  [SMNNIP:on]  [ready]`
