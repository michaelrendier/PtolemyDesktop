---
description: Launch the Agora — dual-AI chat routing queries to Claude and Gemini independently in parallel
allowed-tools: Bash(python3 -m Philadelphos.Agora.agora:*)
---

Launch the Ptolemy Agora — Claude + Gemini queried in parallel, independently.

Requires both API keys:

```
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=AIza...
```

Run from Ptolemy root:

```
cd /home/rendier/Ptolemy && python3 -m Philadelphos.Agora.agora
```

Or import:

```python
from Philadelphos.Agora import Agora

agora = Agora()

# Blocking — both models complete before returning
result = agora.query("What is the SMNNIP Noether current?")
print(result.claude)
print(result.gemini)
print(result.sigma_note())

# Streaming to terminal with [Claude] / [Gemini] labels
agora.stream_to_terminal("Derive the Yang-Mills field strength tensor.")
```

Sigma valuation:
- Models are queried in separate threads — neither sees the other's response
- agreement_flag: Jaccard similarity on content words >= 0.35
- Convergence = higher confidence | Divergence = review both carefully
- Cross-contamination would collapse sigma — model independence is preserved by design
