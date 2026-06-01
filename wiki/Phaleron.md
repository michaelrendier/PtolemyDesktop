# Phaleron

**Historical figure:** Port of Phaleron — the ancient harbour of Athens, gateway to knowledge from the wider world  
**Responsibility:** Internal search, code browsing, API inspection, URL rendering

---

## Overview

Phaleron is Ptolemy's search and discovery Face. It provides internal search across Ptolemy's own codebase and data, API inspection tools, URL rendering, and a suite of information-retrieval utilities. The port metaphor is apt — Phaleron is where external information enters the system.

---

## Module Tree

```
Phaleron/
├── phaleron_search.py        ← Primary search interface
├── phaleron_display.py       ← Search result display widget
├── APISniff/
│   ├── APISniff.py           ← Live API traffic inspection
│   ├── APISniffCL.py         ← Command-line API sniffer
│   ├── CodeBrowser.py        ← Source code browser with syntax highlighting
│   └── Dialogs.py            ← UI dialogs for APISniff
├── TreasureHunt/
│   ├── TreasureHunt.py       ← Full-text search engine
│   └── Search.py             ← Search algorithm (Dijkstra-based)
├── Library/
│   └── LibraryBook.py        ← Book/document record format
├── Polyglot/
│   └── ThePolyglot.py        ← Multi-language text handling
├── ImageReader/
│   ├── ImageText.py          ← OCR text extraction from images
│   └── text_detection.py     ← OpenCV text detection
├── NextEpisode/
│   └── NextEpisode.py        ← TV show episode tracker
├── PennyWatcher/
│   └── PennyStock.py         ← Stock watch utility
├── AutoTicker/
│   └── AutoTicker.py         ← Automated ticker/scroll display
├── render_url.py             ← URL fetch and render
└── Syntax.py                 ← Syntax highlighting engine
```

---

## TreasureHunt Search

Primary internal search engine. Dijkstra-based relevance scoring over Ptolemy's file and data corpus.

Accessible via:
- Pharos sidebar search
- `/search` PtolShell command
- Direct: `from Phaleron.TreasureHunt.TreasureHunt import TreasureHunt`

---

## APISniff

Live inspection of API calls made by any Ptolemy Face. Useful for debugging Datamuse, Wiktionary, and Wikipedia calls during acquisition runs.

```python
from Phaleron.APISniff.APISniff import APISniff
sniffer = APISniff()
sniffer.start()   # intercepts all requests.get() calls
```

---

## OCR Pipeline

`ImageReader/` — OpenCV-based text detection from images.

Planned use: ancient manuscript OCR feeding directly into HyperWebster acquisition (LSH_Datatype layer 5 `definition_core` from primary sources rather than web APIs).

---

## Settings

`Phaleron/settings/settings.json`

| Key | Description |
|---|---|
| `default_search_engine` | `phaleron` / `duckduckgo` / `wikipedia` |
| `result_limit` | Max search results returned (default: 20) |
| `render_url_enabled` | URL renderer active flag |

---

## Dependencies

- requests (URL fetching)
- OpenCV (image text detection)
- PyQt5 (display widgets)
- Pharos/PtolBus (search event publishing)
