#!/usr/bin/python3
"""
HyperWebster - Infinite Permutation Indexer
============================================
Maps any string to a unique coordinate in the infinite permutation of a
fixed character set, and back again.

Address design
--------------
The raw integer coordinate of a long string is enormous — an 11,000-char
file sits at a ~73,000-bit integer, which gives an ~18,000-char hex string.
To keep addresses a *fixed* 64 characters we split the concept in two:

  label    — SHA-256 of the raw integer address (always 64 hex chars).
             Used as the stable, human-friendly "pointer".

  payload  — The full integer address, base-N encoded using the same
             character set.  Required only for regeneration.

Index record (named tuple):
  (label, payload, length, timestamp)
    label     : str  — 64-char SHA-256 hex string  (the "address")
    payload   : str  — full coordinate, base-N encoded (compact but variable)
    length    : int  — character count of the original text
    timestamp : str  — time.ctime() at indexing time

Regeneration only needs (payload, length).
The label alone uniquely identifies the text for lookup/comparison.
"""

import hashlib
import sys
import time
from typing import NamedTuple


class IndexRecord(NamedTuple):
    label:     str   # 64-char SHA-256 hex — the fixed-length "address"
    payload:   str   # full coordinate encoded in base-N (for regeneration)
    length:    int   # character count of the original text
    timestamp: str   # time.ctime() at index time


class HyperWebster:
    """
    Bijective base-N encoding over an ordered character set.

    Every finite string over `self.characters` has a unique non-negative
    integer coordinate (address).  Addresses are exposed as fixed-length
    SHA-256 labels; the full integer is stored as a compact base-N payload.
    """

    _DEFAULT_CHARS = (
        r"""`1234567890-="""
        "\t"
        r"""qwertyuiop[]\asdfghjkl;'"""
        "\n"
        r"""zxcvbnm,./ ~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?"""
    )

    def __init__(self, characters: str = _DEFAULT_CHARS):
        self.characters  = characters
        self.char_list   = list(self.characters)
        self.N           = len(self.char_list)
        self._char_index = {ch: i for i, ch in enumerate(self.char_list)}
        sys.set_int_max_str_digits(0)

    # ------------------------------------------------------------------
    # Core math: string <-> integer  (bijective base-N)
    # ------------------------------------------------------------------

    def _str_to_int(self, text: str) -> int:
        """String -> unique non-negative integer (bijective base-N)."""
        address = 0
        for i, ch in enumerate(reversed(text)):
            try:
                index = self._char_index[ch] + 1   # 1-based
            except KeyError:
                raise ValueError(f"Character {ch!r} is not in the character set.")
            address += index * (self.N ** i)
        return address - 1                          # 0-based

    def _int_to_str(self, address: int) -> str:
        """Non-negative integer -> string (bijective base-N)."""
        if address < 0:
            raise ValueError("Address must be non-negative.")
        res     = []
        address += 1
        while address > 0:
            address, rem = divmod(address - 1, self.N)
            res.append(self.char_list[rem])
        return "".join(reversed(res))

    # ------------------------------------------------------------------
    # Payload encoding: integer <-> base-N string
    # ------------------------------------------------------------------

    def _int_to_payload(self, n: int) -> str:
        """Encode a large integer as a base-N string (compact, variable length)."""
        if n == 0:
            return self.char_list[0]
        digits = []
        while n > 0:
            n, rem = divmod(n, self.N)
            digits.append(self.char_list[rem])
        return "".join(reversed(digits))

    def _payload_to_int(self, payload: str) -> int:
        """Decode a base-N payload string back to an integer."""
        n = 0
        for ch in payload:
            n = n * self.N + self._char_index[ch]
        return n

    # ------------------------------------------------------------------
    # Label: fixed-length 64-char SHA-256 of the raw hex address
    # ------------------------------------------------------------------

    @staticmethod
    def _make_label(integer_address: int) -> str:
        """SHA-256 of the integer address -> fixed 64-char hex label."""
        raw = format(integer_address, "x").encode()
        return hashlib.sha256(raw).hexdigest()   # always 64 chars

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_text(self, text: str) -> IndexRecord:
        """
        Index a block of text.

        Returns an IndexRecord with:
          label     -- 64-char fixed-length SHA-256 address label
          payload   -- compact base-N encoded integer (for regeneration)
          length    -- character count
          timestamp -- time.ctime()
        """
        integer_address = self._str_to_int(text)
        return IndexRecord(
            label     = self._make_label(integer_address),
            payload   = self._int_to_payload(integer_address),
            length    = len(text),
            timestamp = time.ctime(),
        )

    def regenerate_from_record(self, record: IndexRecord) -> str:
        """Regenerate text from an IndexRecord (uses payload + length)."""
        return self.regenerate(record.payload, record.length)

    def regenerate(self, payload: str, length: int) -> str:
        """
        Regenerate text from a payload string and expected length.

        Parameters
        ----------
        payload : the `payload` field from an IndexRecord
        length  : the `length` field from an IndexRecord
        """
        integer_address = self._payload_to_int(payload)
        text            = self._int_to_str(integer_address)
        if len(text) != length:
            raise ValueError(
                f"Length mismatch: got {len(text)}, expected {length}. "
                "Payload or length may be corrupted."
            )
        return text


# ---------------------------------------------------------------------------
# Demo / smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    hw = HyperWebster()

    samples = [
        "Hello, World!",
        "python3",
        "The quick brown fox jumps over the lazy dog.\n",
        "`~!@#",
    ]

    sql_path = os.path.join(os.path.dirname(__file__), "TESTdb-struct.sql")
    if os.path.exists(sql_path):
        with open(sql_path) as fh:
            samples.append(fh.read())

    print("=" * 72)
    print(f"{'HyperWebster  --  Infinite Permutation Indexer':^72}")
    print(f"Character-set size: {hw.N} symbols")
    print("=" * 72)

    all_ok = True
    for sample in samples:
        record    = hw.index_text(sample)
        recovered = hw.regenerate_from_record(record)
        ok        = recovered == sample

        if not ok:
            all_ok = False

        preview = repr(sample[:40] + ("..." if len(sample) > 40 else ""))
        print(f"\nInput     : {preview}  ({len(sample)} chars)")
        print(f"Label     : {record.label}  ({len(record.label)} chars) <- always 64")
        print(f"Payload   : {record.payload[:60]}{'...' if len(record.payload)>60 else ''}  ({len(record.payload)} chars)")
        print(f"Length    : {record.length}")
        print(f"Timestamp : {record.timestamp}")
        print(f"Round-trip: {'PASS' if ok else 'FAIL'}")

    print("\n" + "=" * 72)
    print("All round-trips passed." if all_ok else "SOME ROUND-TRIPS FAILED.")
