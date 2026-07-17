# Kryptos

**Historical figure:** *Kryptos* — Greek: "hidden"  
**Responsibility:** Encryption, HyperWebster key derivation, Kryptos Complexity Factor

---

## Overview

Kryptos is Ptolemy's encryption Face and the sole custodian of all cryptographic keys. It owns the Kryptos Complexity Factor (KCF-1) key derivation scheme, HyperWebster-addressed encryption, and all cipher implementations. **No other Face generates or stores keys independently.**

---

## Module Tree

```
Kryptos/
├── kcf.py                    ← KCF-1: Horner→permute→HKDF-SHA256 key derivation
├── GlyphForge.py             ← Glyph generation for demotic tone system
├── Ciphers/
│   └── LFSR.py               ← Linear Feedback Shift Register cipher
├── CipherStatistics/
│   └── CipherStats.py        ← Statistical cipher analysis tools
├── Steganography/            ← Steganographic encoding (stub)
└── TheCodeBook/
    ├── TextAnalysis/         ← Frequency analysis, cipher identification
    ├── Unscramble/           ← Anagram/unscramble engine
    └── Scrabble/             ← Scrabble scoring (word game utility)
```

---

## KCF-1 — Kryptos Complexity Factor

Deterministic key derivation tied to HyperWebster addressing. Formal specification: `docs/Kryptos/KCF-1_Kryptos_Complexity_Factor.docx`.

**Pipeline:**
```
word → HyperWebster Horner address → charset permutation (XOR + prime mix)
     → HKDF-SHA256(ikm=permuted_address, salt=word, info=purpose)
     → derived key
```

```python
from Kryptos.kcf import KCF, KCF_KEY_AES, KCF_KEY_SIGNING

kcf = KCF()
key = kcf.derive("ptolemy", purpose=KCF_KEY_AES)    # 32-byte AES key
sig = kcf.derive("ptolemy", purpose=KCF_KEY_SIGNING) # signing key
addr = kcf.hw_address("ptolemy")                     # HW address only
```

**Key properties:**
- Deterministic — same word + same charset permutation = same key, always
- The charset permutation IS the master secret (managed by Kryptos)
- HKDF ensures purpose-separated keys from the same root material
- No key storage — keys are recomputed on demand

---

## Key Custody Rules

| Protocol | Owner | Purpose |
|---|---|---|
| TLS | Kryptos | Mouseion Flask → HTTPS |
| SSH | Kryptos | Tesla device communication |
| AES-256 | Kryptos | File/data encryption |
| HW addressing | Kryptos | Public charset = public; permuted = private |

**Kryptos is the only Face that calls `kcf.derive()`.** Other Faces request keys via Kryptos interface — they never derive independently.

---

## Benchmarks

KCF-1 benchmarked against: MD5, SHA-256, SHA-512, SHA3-256, AES-128/256, ChaCha20, RSA-2048/4096, PBKDF2.

Full results: `docs/Kryptos/KCF-1-BM_Benchmark_Report.docx`

---

## Pre-Release Checklist

Before Ptolemy goes public, the following must be completed (see `docs/Kryptos/Kryptos_Repository_Preparation.docx`):
- `git filter-repo` scrub of full history
- Verify no tokens/API keys in `.git/`
- Confirm `.env` in `.gitignore`, `.env.example` committed
- `.gitignore.SSF` in place

---

## Settings

`Kryptos/settings/settings.json`

| Key | Description |
|---|---|
| `kdf_algorithm` | Key derivation function (default: HKDF-SHA256) |
| `key_length_bytes` | Derived key length (default: 32) |
| `charset_permutation` | Active permutation identifier (references `HYPER_KEY` env var) |

---

## Dependencies

- hashlib (stdlib — SHA-256)
- hmac (stdlib — HKDF)
- Callimachus/v09/core/hyperwebster (Horner addressing)
- Callimachus/v09/core/charset (PUBLIC_CHARSET)
