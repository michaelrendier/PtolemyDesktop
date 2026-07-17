---
description: Launch the Gemini REPL — Google Gemini as a Ptolemy feature (requires GEMINI_API_KEY)
allowed-tools: Bash(python3 -m Philadelphos.Gemini.gemini:*)
---

Launch the Gemini REPL — Gemini 2.5 Flash integrated as a Ptolemy component.

Set your Google AI API key first:

```
export GEMINI_API_KEY=AIza...
```

Then run from the Ptolemy root:

```
cd /home/rendier/Ptolemy && python3 -m Philadelphos.Gemini.gemini
```

Or import in code:

```python
from Philadelphos.Gemini import Gemini

gem = Gemini()                    # prints: Managed by: gemini-2.5-flash  [SMNNIP:on]  [ready]

# Streaming
for chunk in gem.stream("Derive the SMNNIP Noether current."):
    print(chunk, end="", flush=True)

# Single-shot
response = gem.chat("What is the GUT convergence scale?")
```

Features:
- Package: google-genai v1.73+ (GA, April 2026)
- Model: gemini-2.5-flash with dynamic thinking budget
- Auto function calling: smnnip_lagrangian, smnnip_noether, smnnip_rg_flow
- Persistent chat session with history
- Status header: Managed by: gemini-2.5-flash  [SMNNIP:on]  [ready]
