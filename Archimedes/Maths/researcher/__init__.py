"""
Archimedes/Maths/researcher/ — the hardcoded Researcher/Engineer maths library.
=============================================================================
A curated working set per field (~15-30 equations), each a `MathDef` built by
`mathengine.build()` so `solvable_for` is computed, not hand-maintained. Every
module: `CATEGORY`, `PAGE = {title, blurb, source}`, `DEFS = [...]`.

This library is the source the granular `monad_mathematics.bin` is built from,
and the dev-facing reference / hard-case fallback. The Face reads the bin day
to day; it calls into here only when the bin lacks an answer.

    catalog()        -> list[MathDef]        every equation
    by_category()    -> dict[str, list]      grouped
    find(id)         -> MathDef | None
    find_by_name(s)  -> MathDef | None       case-insensitive substring
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import Dict, List, Optional

from ..mathdef import MathDef

_SUBPACKAGES = ("foundations", "physics", "engineering")
_MODULES: Dict[str, object] = {}


def _discover() -> None:
    if _MODULES:
        return
    for sub in _SUBPACKAGES:
        try:
            pkg = importlib.import_module(f"{__name__}.{sub}")
        except ModuleNotFoundError:
            continue
        for info in pkgutil.iter_modules(pkg.__path__):
            if info.name.startswith("_"):
                continue
            mod = importlib.import_module(f"{__name__}.{sub}.{info.name}")
            if hasattr(mod, "DEFS"):
                _MODULES[f"{sub}.{info.name}"] = mod


def catalog() -> List[MathDef]:
    _discover()
    out: List[MathDef] = []
    for mod in _MODULES.values():
        out.extend(getattr(mod, "DEFS", []))
    return out


def by_category() -> Dict[str, List[MathDef]]:
    grouped: Dict[str, List[MathDef]] = {}
    for md in catalog():
        grouped.setdefault(md.category, []).append(md)
    return grouped


def pages() -> Dict[str, dict]:
    _discover()
    return {name: getattr(mod, "PAGE", {}) for name, mod in _MODULES.items()}


def find(mid: str) -> Optional[MathDef]:
    for md in catalog():
        if md.id == mid:
            return md
    return None


def _toks(s: str) -> set:
    """Lowercase alnum tokens, trailing-'s' trimmed (crude de-plural/possessive)."""
    raw = "".join(c if c.isalnum() or c == " " else " " for c in s.lower()).split()
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in raw}


def find_by_name(text: str) -> Optional[MathDef]:
    q = _toks(text)
    if not q:
        return None
    best, best_overlap = None, 0
    for md in catalog():
        n = _toks(md.name)
        if q == n:
            return md
        if q <= n or n <= q:                     # one is a token-subset of the other
            ov = len(q & n)
            if ov > best_overlap:
                best, best_overlap = md, ov
    return best


if __name__ == "__main__":
    c = catalog()
    print(f"{len(c)} equations across {len(by_category())} categories:")
    for cat, defs in sorted(by_category().items()):
        print(f"  {cat:26s} {len(defs)}")
    print("find_by_name('newton second law'):", find_by_name("newton second law"))
