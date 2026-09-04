"""
Archimedes/monadbin.py — read the two monad .bin vocabularies.
=============================================================
No hashing, no learning — the bins are already weighted; we read them as-is.

    monad_mathematics.bin  — pickle dict {version, vocab, words, beta, E, A,
                             age, n}. The granular MATHS VOCABULARY.
    monad3_c.bin           — C "MONAD3C\\0" packed format written by ptol.c.
                             The SENTENCE CONSTRUCTIONS. A full Python reader for
                             the packed word table is a TODO (mirror
                             VAPMIP/monad_bin/repack.py); until then we read the
                             header for metadata and the Face uses its built-in
                             sentence templates, enriched by this bin when the
                             reader lands.
"""
from __future__ import annotations

import pickle
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional

_MONAD3C_MAGIC = b"MONAD3C\x00"


class MathsVocab:
    """The granular maths vocabulary from monad_mathematics.bin (pickle)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        with open(self.path, "rb") as f:
            self._d: Dict[str, Any] = pickle.load(f)
        self.version = self._d.get("version", "?")
        self.n = int(self._d.get("n", 0))
        self.words: List[str] = list(self._d.get("words", []))
        self.vocab = self._d.get("vocab", {})          # word -> index (or similar)
        self.beta = self._d.get("beta")
        self.E = self._d.get("E")

    def has(self, term: str) -> bool:
        t = term.lower().strip()
        if isinstance(self.vocab, dict) and t in self.vocab:
            return True
        return t in (w.lower() for w in self.words if isinstance(w, str))

    def nearest(self, term: str, k: int = 5) -> List[str]:
        """Cheap lexical neighbours — a starter until the weighted lookup is
        wired. Substring match over the word list."""
        t = term.lower().strip()
        hits = [w for w in self.words if isinstance(w, str) and t in w.lower()]
        return hits[:k]

    def __repr__(self) -> str:
        return f"MathsVocab({self.path.name}, v{self.version}, {self.n} words)"


class SentenceForms:
    """monad3_c.bin header + a TODO for the packed word table."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.ok = False
        self.magic_ok = False
        self.version: Optional[int] = None
        self.counts: List[int] = []
        try:
            with open(self.path, "rb") as f:
                head = f.read(8)
                self.magic_ok = head == _MONAD3C_MAGIC
                if self.magic_ok:
                    (self.version,) = struct.unpack("<i", f.read(4))
                    self.counts = list(struct.unpack("<8i", f.read(32)))
                    self.ok = True
        except Exception:                                          # noqa: BLE001
            pass
        # the packed word table decode is not implemented — Face uses templates
        self.words_usable = False

    def __repr__(self) -> str:
        return (f"SentenceForms({self.path.name}, magic={self.magic_ok}, "
                f"v{self.version}, words_usable={self.words_usable})")


def load_maths(path: str | Path) -> MathsVocab:
    return MathsVocab(path)


def load_sentence_forms(path: str | Path) -> SentenceForms:
    return SentenceForms(path)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    place = here.parents[1]
    mm = place / "PTorrent/bin_archive/clean/monad_mathematics.bin"
    m3 = place / "VAPMIP/PtolC/monad3_c.bin"
    if mm.exists():
        v = load_maths(mm)
        print(v, "| has('integral'):", v.has("integral"),
              "| nearest('deriv'):", v.nearest("deriv"))
    if m3.exists():
        print(load_sentence_forms(m3))
