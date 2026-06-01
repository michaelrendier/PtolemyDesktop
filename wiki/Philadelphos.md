# Philadelphos

**Historical figure:** Ptolemy II Philadelphos — expanded the Library, commissioned the Septuagint translation  
**Responsibility:** LSH inference layer — language models, speech, cyclic context, two-pass word acquisition

---

## Overview

Philadelphos is Ptolemy's inference Face. It owns the LSH model pipeline, all language model integrations (Claude/Ainur, Gemini, Agora dual-chat), speech input/output, the cyclic context buffer, and the two-pass inline word acquisition pipeline.

---

## Module Tree

```
Philadelphos/
├── ptolemy_core.py           ← LSH model core — 6-layer Monad neural architecture
├── philadelphos_console.py   ← Julius Caesar face config, LuthSpell BUS wiring
├── Phila.py                  ← Main Philadelphos window
├── CommandInput.py           ← Command input handler
├── SpeechInput.py            ← Speech-to-text (ptolemy_ears)
├── ptolemy_ears.py           ← Audio input pipeline
├── ptolemy_tongue.py         ← Text-to-speech output
├── output_tuner.py           ← Output stream tuner
├── cyclic_context_buffer.py  ← FIFO sliding window context — AuditChain backend
├── data_input.py             ← Data ingestion layer
├── LSH_Datatype_parser/
│   ├── acquire.py            ← Batch acquisition pipeline (CLI)
│   └── acquire_inline.py     ← Two-pass inline acquisition (pre/post inference)
├── Ainur/
│   └── ainur.py              ← Claude API integration (Ainur = Valar messenger)
├── Gemini/
│   └── gemini.py             ← Google Gemini integration
├── Agora/
│   └── agora.py              ← Dual-chat: Claude + Gemini in parallel
├── LLM_Datatype_parser/      ← DEPRECATED name — use LSH_Datatype_parser
├── context/
│   ├── context_manager.py    ← Context window management
│   ├── claude_context.json   ← Claude session context state
│   └── gemini_context.json   ← Gemini session context state
└── weights/                  ← LSH model weights (excluded from public release)
```

---

## LSH Model — Monad Architecture

Six-layer stack. Each layer is a monad — isolated, no cross-layer state bleed.

| Layer | Class | Role |
|---|---|---|
| 1 | `CharacterNeuron` | Character-level encoding |
| 2 | `LexicalDimensionNeuron` | Lexical space projection |
| 3 | `GrammarNeuron` | Syntactic structure (language-specific variants) |
| 4 | `WordMonadNetwork` | Word-level monad isolation |
| 5 | `WernickeNetwork` | Comprehension — maps input to meaning |
| 6 | `BrocaNetwork` | Production — maps meaning to output |

Monad isolation is the primary anti-forgetting mechanism. Each monad trains independently. EWC (Elastic Weight Consolidation) strategy for sequential learning.

**Julius Caesar face configuration** (`JULIUS_CAESAR_CONFIG`): corpus = Caesar + Cicero + Cato (Latin). Initial training corpus for LSH experimentation.

---

## Two-Pass Inline Acquisition

`LSH_Datatype_parser/acquire_inline.py` — flat callable API, no batch loop, no argparse.

```python
from Philadelphos.LSH_Datatype_parser.acquire_inline import acquire_pre, acquire_post

# Pass 1 — before inference (enrich command words)
word_data = acquire_pre(tokenize(command))
# inject word_data into inference context

result = lsh_model.infer(command, context)

# Pass 2 — after inference (enrich output words)
output_data = acquire_post(tokenize(result))
# stored/logged — does not alter output text
```

**Pass 1** persists to disk. Returns cached record if word already complete (resume logic).  
**Pass 2** persists by default. `persist=False` for ephemeral enrichment.  
Both passes fire Aule stream events (zero-coupling shim).

---

## Cyclic Context Buffer

FIFO sliding window context management. Unit = lines (one `EntryObject` = `PromptObject` + `ResponseObject`).

```python
from Philadelphos.cyclic_context_buffer import CyclicContextBuffer

buf = CyclicContextBuffer(size_lines=100)
buf.append(prompt, response)
# On eviction: compress → octonion hyperindex → AuditChain commit
```

Confirmed eviction — entry stays until compress + hyperindex + blockchain all succeed. No index manipulation during iteration. AuditChain backend wired (PtolChain).

---

## Speech Pipeline

```
Microphone → ptolemy_ears.py → SpeechInput.py → CommandInput.py → LSH inference
LSH inference → ptolemy_tongue.py → audio output
```

---

## Settings

`Philadelphos/settings/settings.json`  
`Philadelphos/settings/cyclic_context_buffer/settings.json`

| Key | Description |
|---|---|
| `context_buffer_size_lines` | Cyclic buffer depth |
| `default_model` | `ainur` / `gemini` / `agora` |
| `speech_input_enabled` | Microphone active |
| `speech_output_enabled` | TTS active |
| `julius_caesar_corpus` | Training corpus path |

---

## Dependencies

- anthropic (Ainur/Claude API)
- google-generativeai (Gemini API)
- SpeechRecognition / pocketsphinx (speech input)
- pyttsx3 / espeak (speech output)
- Callimachus/v09 (HyperWebster, LSH_Datatype, HyperDatabase)
- Pharos/PtolBus (inference event publishing)
- Aule (stream_event shim)
