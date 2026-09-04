#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
common.py — shared primitives for the Kryptos / Pycrypt cipher engines.

Every engine in this package works on the historical 26-letter English
alphabet, uppercase, non-letters dropped — exactly as the ciphers were worked
by hand.  The Code Book's own convention: "the tabula recta has no entry for
[spaces, punctuation]" (Vigenere), and al-Kindi's frequency method assumes a
letters-only stream.

`CipherResult` is the small value object the Pycrypt dialogs pass back into the
Change Text pane: the transformed text plus a short human note (what key was
used, what the tool found) so the workbench can show its working.
"""

from dataclasses import dataclass, field
from typing import Optional

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
A = len(ALPHABET)

# English single-letter frequency order, most common first.  Same ordering the
# old Pycrypt build carried in `frequency_english` (ETAOIN SHRDLU ...), used by
# the monoalphabetic "map by frequency" auto-solve.
ENGLISH_FREQ_ORDER = 'ETAOINSHRDLCUMWFGYPBVKJXQZ'

# Approximate English letter frequencies (%), al-Kindi's "fingerprint".
# Source: standard corpus values, matching the bar charts on the CD-ROM
# frequency-analysis pages.
ENGLISH_FREQ = {
    'A': 8.17, 'B': 1.49, 'C': 2.78, 'D': 4.25, 'E': 12.70, 'F': 2.23,
    'G': 2.02, 'H': 6.09, 'I': 6.97, 'J': 0.15, 'K': 0.77, 'L': 4.03,
    'M': 2.41, 'N': 6.75, 'O': 7.51, 'P': 1.93, 'Q': 0.10, 'R': 5.99,
    'S': 6.33, 'T': 9.06, 'U': 2.76, 'V': 0.98, 'W': 2.36, 'X': 0.15,
    'Y': 1.97, 'Z': 0.07,
}


def clean(text: str) -> str:
    """Uppercase, letters only — the hand-cipher input stream."""
    return ''.join(ch for ch in text.upper() if ch in ALPHABET)


def letters_only(text: str) -> str:
    """Alias kept for readability at call sites that mean 'strip to letters'."""
    return clean(text)


def only_letters_preserving_case(text: str) -> str:
    return ''.join(ch for ch in text if ch.upper() in ALPHABET)


def egcd(a: int, b: int):
    if a == 0:
        return b, 0, 1
    g, y, x = egcd(b % a, a)
    return g, x - (b // a) * y, y


def modinv(a: int, m: int = A) -> int:
    """Multiplicative inverse of a mod m; raises if gcd(a, m) != 1 — the
    coprime rule the affine cipher turns on (Code Book affine lesson)."""
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f'{a} has no inverse mod {m} (shares a factor with {m})')
    return x % m


@dataclass
class CipherResult:
    """What a Pycrypt cipher dialog hands back to the workbench."""
    text: str
    note: str = ''
    key: Optional[object] = None
    extra: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text
