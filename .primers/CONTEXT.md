# Ptolemy — Session Context Primer

> Read this at the start of any new Claude Code session to restore full context.
> Last updated: 2026-04-18

---

## Project

**Ptolemy** — modular Python3 research and engineering platform.
- Author: michaelrendier
- Repo: github.com/michaelrendier/Ptolemy
- Root: `/home/rendier/Ptolemy`
- Branch: `main`

### Modules

| Module | Role |
|---|---|
| Alexandria | geo / mapping |
| Anaximander | navigation |
| Archimedes | math engine — UFformulary (508 formula files: `.ufm .ucl .ulb .upr .uxf`) |
| Callimachus | database / HyperWebster lexical datatype |
| Kryptos | cipher engines |
| Mouseion | OpenGL GUI |
| Phaleron | browser / web tools |
| Pharos | main shell UI |
| **Philadelphos** | **LSH inference layer — Claude (Ainur), Gemini, Agora dual-chat** |
| Tesla | networking / sockets |
| Ptolemy++ | C++ companion (Gemini-ncurses) |

---

## Environment Variables

**Critical distinction: tokens ≠ API keys.**

| Variable | Type | Purpose | Status |
|---|---|---|---|
| `PTOL_TOKEN` | GitHub PAT | Full git management — github.com/michaelrendier/Ptolemy | set |
| `AINUR_TOKEN` | GitHub PAT | Repo access — github.com/michaelrendier/Ainulindale | set |
| `ANTHROPIC_API_KEY` | API key | Claude / Anthropic API — `Philadelphos.Ainur` | **pending — user obtaining** |
| `GEMINI_API_KEY` | API key | Google Gemini API — `Philadelphos.Gemini` | set |

> `*_TOKEN` = GitHub fine-grained PAT. Never use as an API key.
> `*_API_KEY` = AI service key. Never use as a repo token.

---

## AI Features — Philadelphos Layer

### Claude (`Philadelphos/Ainur/`)
- SDK: `anthropic` (pip install anthropic)
- Model: `claude-opus-4-6`
- Thinking: `{"type": "adaptive"}` (no beta header needed on Opus 4.6)
- Streaming: yes — `.stream()` context manager
- Prompt caching: system prompt cached via `cache_control: ephemeral`
- Tools: `smnnip_lagrangian`, `smnnip_noether`, `smnnip_rg_flow` (manual loop)
- Context file: `Philadelphos/context/claude_context.json`
- REPL: `python3 -m Philadelphos.Ainur.ainur`
- Slash command: `/ainur`

### Gemini (`Philadelphos/Gemini/`)
- SDK: `google-genai` v1.73.1 (GA, April 2026) — `from google import genai`
- Model: `gemini-2.5-flash`
- Thinking: `ThinkingConfig(thinking_budget=-1)` — dynamic
- Streaming: `client.models.generate_content_stream()` / `chat.send_message_stream()`
- Auto function calling: tool Python callables passed directly to `GenerateContentConfig`
- Chat session: `client.chats.create()` maintains history natively
- Context file: `Philadelphos/context/gemini_context.json`
- REPL: `python3 -m Philadelphos.Gemini.gemini`
- Slash command: `/gemini`

### Agora (`Philadelphos/Agora/`) — dual-AI chat
- Routes a single query to Claude and Gemini **independently and in parallel**
- Responses collected separately — models never see each other's output
- **Sigma valuation**: model independence is load-bearing.
  Agreement between independently-queried models = higher statistical confidence.
  Disagreement = flags genuine uncertainty or domain boundary.
  Cross-contamination would collapse sigma to 1 (correlated, not independent).
- REPL: `python3 -m Philadelphos.Agora.agora`
- Slash command: `/agora`

---

## LSH — Ainulindale

**Standard Model of Neural Network Information Propagation**
- Repo: github.com/michaelrendier/Ainulindale
- Ptolemy path: `Philadelphos/Ainulindale/`
- Algebra tower: ℝ → ℂ → ℍ → 𝕆 → 𝕊 (Cayley-Dickson / Dixon 1994)
- Gauge group: U(1) × SU(2) × SU(3)
- Noether conservation: empirically verified — `violation=0.0, conserved=True`
- Console: `python3 derivation.py` or `/derivation`
- Engine: `LSHValaQuenta` in `Philadelphos/Ainulindale/core/smnnip_derivation_pure.py`

---

## HyperWebster Context Files

Persistent JSON memory stores — loaded on session start, updated on session end.

| File | Scope |
|---|---|
| `Philadelphos/context/claude_context.json` | Claude identity, LSH knowledge, session memory, I/O log |
| `Philadelphos/context/gemini_context.json` | Gemini identity, LSH knowledge, session memory, I/O log |
| `Philadelphos/context/ptolemy_context.json` | Master index — aggregates both + runtime I/O stream + event log |

Manager: `from Philadelphos.context.context_manager import PtolemyContext`

---

## Session Rules (persistent)

1. **Always save `.bak` before editing any file** — `cp file file.bak` first, no exceptions.
2. **Destructive ops require triple-factor auth** — 3 random words typed back before any `rm -rf` or wipe.
3. **`claude_code/` is Claude's working directory** — full write/delete access, no auth challenges.
4. **Tokens ≠ API keys** — never cross-use them.
5. **Model independence in Agora** — Claude and Gemini never see each other's responses. Sigma valuation depends on it.

---

## What Was Built (2026-04-18 session)

- `.gitignore` — comprehensive, cleaned repo
- `Philadelphos/Ainulindale/` — LSH model integrated from Ainulindale repo
- `Philadelphos/CommandInput.py` — Qt stack retired, replaced with curses launcher
- `.claude/commands/derivation.md` — `/derivation` slash command
- `derivation.py` — standalone root launcher for LSH console
- `Philadelphos/Ainur/` — Claude API module (anthropic SDK)
- `Philadelphos/Gemini/` — Gemini API module (google-genai SDK)
- `Philadelphos/Agora/` — dual-AI parallel chat with sigma valuation
- `Philadelphos/context/` — three HyperWebster JSON context files + PtolemyContext manager
- `.env.example` — documents all env vars with type annotations
- `CONTEXT.md` — this file
