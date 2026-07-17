# Aulë Sanitation — Multi-Factor Input Gate

`Aule/aule_sanitation.py`

---

## Overview

Aulë Sanitation is Ptolemy's sole input gatekeeper. **No input reaches the bus or dmesg unsanitized unless explicitly cleared by trust level.** All input — from Faces, devices, or external sources — passes through `gate` before touching any shared system.

---

## Trust Levels

| Level | `Trust` enum | Sources | Treatment |
|---|---|---|---|
| `OPERATOR` | `Trust.OPERATOR` | `operator`, `rendier` | Raw — no sanitation, full trust |
| `ARCHIMEDES` | `Trust.ARCHIMEDES` | `archimedes` | Raw — math/code authority, no sanitation |
| `FACE` | `Trust.FACE` | Any other Face name | Sanitized before forge write |
| `EXTERNAL` | `Trust.EXTERNAL` | Non-Ptolemy input | Sanitized + validated |

OPERATOR and ARCHIMEDES bypass both sanitation and FA entirely.

---

## Risk Levels & Factor Authentication

| Level | `Risk` enum | FA Required | Notes |
|---|---|---|---|
| `LOW` | `Risk.LOW` | None | Pass-through, silent log |
| `MEDIUM` | `Risk.MEDIUM` | 2FA | Confirm intent |
| `HIGH` | `Risk.HIGH` | 3FA | Random word challenge + confirm + delay |
| `AULE_RISK` | `Risk.AULE_RISK` | 3FA automatic | No override, no bypass — hardcoded |

---

## Aule-Risk Triggers (automatic 3FA, hardcoded)

Any action containing these keywords triggers `AULE_RISK` — 3FA with no override:

```python
_AULE_RISK_KEYS = {
    'aule', 'forge', 'sanitation', 'fa_threshold',
    'repair_table', 'dmesg_path', 'forge_write',
    'aule_sanitation', 'aule.py', 'aule_risk',
}
```

This protects Aule from modifying itself. Any config key containing `aule`, `forge`, or `sanitation` is automatically elevated to `AULE_RISK`.

---

## 3FA Random Word Challenge

Aule generates 3 random words from a fixed local pool (40 entries — no network):

```
Aule :: 3FA REQUIRED  (attempt 1/3)
Action    : modify_repair_table
Source    : callimachus
Challenge : COPPER  VESSEL  HINGE
Response  : _
```

User must repeat the words exactly. Different words every challenge (random, not sequential). 3 attempts max.

**On failure:**
- Action quarantined in forge
- O Captain alerted (dmesg FATAL)
- Quarantine written to `~/ptolemy_aule_quarantine.log`
- 3 failures: action scrapped

---

## Sanitation Patterns

Applied to FACE and EXTERNAL trust input:

| Pattern | Threat |
|---|---|
| `<[^>]+>` | HTML/XML injection |
| `[;\|&$\`]` | Shell injection characters |
| `\.\./` | Path traversal |
| `(drop\|delete\|truncate)\s+table` | SQL drops |
| `import\s+os\s*;` | Inline OS import tricks |

Dict and list inputs are recursively sanitized.

---

## Usage

```python
from Aule.aule_sanitation import gate

# Sanitize input (returns trusted_raw flag + cleaned content)
is_raw, content = gate.sanitize(source='callimachus', content=raw_input)

# Gate an action by risk level
allowed = gate.check('callimachus', risk='HIGH', action='db_write')
if not allowed:
    return  # blocked or quarantined

# Explicit Aule-risk gate (always 3FA, no bypass)
allowed = gate.aule_risk_gate(action='modify_repair_table', source='archimedes')

# Auto-classify risk
risk = gate.classify_risk('delete_word_from_db')  # → Risk.HIGH
```

---

## Automatic Risk Classification

`gate.classify_risk(action)` heuristic:

| Keyword category | Risk | Keywords |
|---|---|---|
| Aule-risk | `AULE_RISK` | (see `_AULE_RISK_KEYS` above) |
| High | `HIGH` | `delete`, `drop`, `format`, `wipe`, `override`, `bypass` |
| Medium | `MEDIUM` | `write`, `modify`, `update`, `push`, `send`, `exec` |
| Low | `LOW` | Everything else |

---

## FA Challenge Engine

`FAChallenge` class handles the interactive challenges. In GUI context, override `prompt_fn` and `response_fn` to use Qt dialogs instead of stdin/stdout:

```python
class QtFAChallenge(FAChallenge):
    def challenge_3fa(self, action, source):
        words = _generate_challenge(3)
        # Show Qt dialog with words, wait for user input
        ...
```

The base class uses terminal stdin/stdout (suitable for PtolShell System C/O mode).

---

## Module-level Singleton

```python
from Aule.aule_sanitation import gate

# gate is a module-level AuleSanitation() instance
# Import it from anywhere — same object, thread-safe (threading.Lock inside FAChallenge)
```

---

## Dependencies

- `Pharos.PtolDmesg` (dmesg write on all gate events)
- `threading.Lock` (FAChallenge thread safety)
- `pathlib.Path` (quarantine log write)
- No network dependencies (word pool is local)
