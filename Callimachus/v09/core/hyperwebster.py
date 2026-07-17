#!/usr/bin/env python3
"""
Callimachus — HyperWebster
===========================
Bijective base-N string addressing over Unicode 15.1 Public Charset.

Every finite string over the charset has a unique non-negative integer
address. The mapping is a bijection: no two strings share an address,
every address maps to exactly one string.

Address format:
  label   — SHA-256 of the full integer address. Always 64 hex chars.
             This is the PRIMARY KEY used everywhere in Callimachus.
             Stable, fixed-length, collision-resistant.
  payload — Full integer address encoded in base-N using the charset itself.
             Required only for regeneration. Variable length.
  length  — Character count of original string. Required for regeneration.

Horner's method (bijective base-N):
  index_text:     string → integer  via Horner accumulation
  regenerate:     integer → string  via repeated divmod

The permutation (charset order) is the only variable.
PUBLIC_CHARSET (Unicode codepoint order) = public addressing.
Any other order supplied at init = private/cryptographic addressing.
Permutation management is Kryptos's responsibility.
"""

import hashlib
import sys
import time
from typing import NamedTuple

from .charset import PUBLIC_CHARSET, PUBLIC_CHARSET_STR, PUBLIC_N, PUBLIC_CHAR_INDEX

sys.set_int_max_str_digits(0)


# ---------------------------------------------------------------------------
# Index record
# ---------------------------------------------------------------------------

class IndexRecord(NamedTuple):
    label:     str   # 64-char SHA-256 hex — primary key
    payload:   str   # full coordinate in base-N (for regeneration)
    length:    int   # character count of original text
    timestamp: str   # time.ctime() at index time


# ---------------------------------------------------------------------------
# HyperWebster
# ---------------------------------------------------------------------------

class HyperWebster:
    """
    Bijective base-N string addressing.

    Parameters
    ----------
    charset : list[str] | None
        Ordered character list defining the bijection.
        None → PUBLIC_CHARSET (Unicode 15.1 codepoint order).
        Any other order = private addressing. Supply from Kryptos.
    """

    def __init__(self, charset: list[str] | None = None):
        if charset is None:
            self._chars     = PUBLIC_CHARSET
            self._char_idx  = PUBLIC_CHAR_INDEX
        else:
            assert len(charset) == len(set(charset)), "Charset has duplicates"
            self._chars    = charset
            self._char_idx = {ch: i for i, ch in enumerate(charset)}

        self.N = len(self._chars)

    # ------------------------------------------------------------------
    # Core math
    # ------------------------------------------------------------------

    def _str_to_int(self, text: str) -> int:
        """Bijective base-N: string → non-negative integer."""
        address = 0
        for ch in text:
            try:
                idx = self._char_idx[ch] + 1   # 1-based
            except KeyError:
                raise ValueError(
                    f"Character {ch!r} (U+{ord(ch):04X}) not in charset. "
                    f"Validate text with charset.validate_text() before indexing."
                )
            address = address * self.N + idx
        return address - 1   # 0-based

    def _int_to_str(self, address: int) -> str:
        """Bijective base-N: non-negative integer → string."""
        if address < 0:
            raise ValueError("Address must be non-negative.")
        res     = []
        address += 1
        while address > 0:
            address, rem = divmod(address - 1, self.N)
            res.append(self._chars[rem])
        return ''.join(reversed(res))

    # ------------------------------------------------------------------
    # Label helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _int_to_label(n: int) -> str:
        """SHA-256 of the integer address → 64-char hex label (primary key)."""
        raw = n.to_bytes((n.bit_length() + 7) // 8 or 1, 'big')
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _int_to_payload(n: int, chars: list[str]) -> str:
        """Encode integer as base-N string using charset (compact payload)."""
        if n == 0:
            return chars[0]
        N   = len(chars)
        res = []
        while n > 0:
            n, rem = divmod(n, N)
            res.append(chars[rem])
        return ''.join(reversed(res))

    @staticmethod
    def _payload_to_int(payload: str, char_idx: dict[str, int]) -> int:
        """Decode base-N payload string back to integer."""
        N   = len(char_idx)
        n   = 0
        for ch in payload:
            n = n * N + char_idx[ch]
        return n

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index(self, text: str) -> IndexRecord:
        """
        Index a string.

        Returns IndexRecord(label, payload, length, timestamp).
        label is the PRIMARY KEY for Callimachus/HyperDatabase.
        """
        integer  = self._str_to_int(text)
        label    = self._int_to_label(integer)
        payload  = self._int_to_payload(integer, self._chars)
        return IndexRecord(
            label     = label,
            payload   = payload,
            length    = len(text),
            timestamp = time.ctime(),
        )

    def regenerate(self, payload: str, length: int) -> str:
        """
        Regenerate original string from payload and length.
        label is not needed — payload alone is sufficient.
        length is used to verify round-trip integrity.
        """
        integer = self._payload_to_int(payload, self._char_idx)
        text    = self._int_to_str(integer)
        if len(text) != length:
            raise ValueError(
                f"Regeneration length mismatch: got {len(text)}, expected {length}. "
                "Payload or length record may be corrupted."
            )
        return text

    def label_of(self, text: str) -> str:
        """Fast path: return only the label (primary key) for a string."""
        return self._int_to_label(self._str_to_int(text))

    def address_int(self, text: str) -> int:
        """Return raw integer address. Used by HyperGallery and manifold."""
        return self._str_to_int(text)
