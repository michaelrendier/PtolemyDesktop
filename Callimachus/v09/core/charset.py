#!/usr/bin/env python3
"""
Callimachus — Charset Registry
================================
Unicode Standard: 15.1
Wire Encoding:    UTF-8

Two charset modes:

  PUBLIC  — Unicode codepoint order over Basic Latin (U+0020–U+007E) + tab + newline.
            This is the world-facing standard. Any party with Unicode 15.1 can
            verify or reconstruct the bijection independently. No secret required.

  PRIVATE — Permutation of PUBLIC charset supplied as a permutation index
            (integer in [0, N!-1]). This is the cryptographic key.
            Permutation generation/storage lives in Kryptos, not here.
            Callimachus receives a pre-ordered char list; it does not know
            whether it is operating in PUBLIC or PRIVATE mode.

Unicode blocks in PUBLIC charset:
  U+0009  CHARACTER TABULATION     (control — functional whitespace)
  U+000A  LINE FEED                (control — functional whitespace)
  U+0020–U+007E  Basic Latin       (95 printable characters)
  Total: 97 characters

UTF-8 note:
  UTF-8 is the encoding standard for all Callimachus I/O.
  Codepoint ORDER is determined by Unicode 15.1 integer values (ord()).
  UTF-8 byte representation is for wire/storage only — never for ordering.
"""

import sys
sys.set_int_max_str_digits(0)

# ---------------------------------------------------------------------------
# Public charset — Unicode 15.1 codepoint order
# Basic Latin printable (U+0020–U+007E) + tab (U+0009) + newline (U+000A)
# Sorted by codepoint value (ord()) — this IS the canonical public order.
# ---------------------------------------------------------------------------

_BASIC_LATIN_PRINTABLE = [chr(i) for i in range(0x0020, 0x007F)]  # 95 chars
_CONTROLS = ['\t', '\n']                                            #  2 chars
_PUBLIC_RAW = _CONTROLS + _BASIC_LATIN_PRINTABLE                   # 97 chars

# Canonical: sort by Unicode codepoint value
PUBLIC_CHARSET: list[str] = sorted(_PUBLIC_RAW, key=ord)
PUBLIC_CHARSET_STR: str   = ''.join(PUBLIC_CHARSET)
PUBLIC_N: int             = len(PUBLIC_CHARSET)  # 97

assert PUBLIC_N == 97, f"Charset count error: {PUBLIC_N}"
assert len(set(PUBLIC_CHARSET)) == PUBLIC_N, "Duplicate characters in charset"

# Verify Unicode standard
_UNICODE_STANDARD = "15.1"
_WIRE_ENCODING    = "UTF-8"

# O(1) reverse lookup
PUBLIC_CHAR_INDEX: dict[str, int] = {ch: i for i, ch in enumerate(PUBLIC_CHARSET)}


def describe_charset() -> str:
    """Human-readable charset description for documentation/logging."""
    lines = [
        f"Unicode Standard : {_UNICODE_STANDARD}",
        f"Wire Encoding    : {_WIRE_ENCODING}",
        f"Charset Size     : {PUBLIC_N}",
        f"Order            : Unicode codepoint (ord()) ascending",
        f"Blocks           : Basic Latin U+0020–U+007E (95) + TAB U+0009 + LF U+000A",
        f"First char       : U+{ord(PUBLIC_CHARSET[0]):04X} {repr(PUBLIC_CHARSET[0])}",
        f"Last char        : U+{ord(PUBLIC_CHARSET[-1]):04X} {repr(PUBLIC_CHARSET[-1])}",
    ]
    return '\n'.join(lines)


def validate_text(text: str) -> list[str]:
    """
    Return list of characters in text not in PUBLIC_CHARSET.
    Empty list = text is fully addressable.
    Used by Callimachus before indexing to flag out-of-charset content.
    """
    return [ch for ch in text if ch not in PUBLIC_CHAR_INDEX]
