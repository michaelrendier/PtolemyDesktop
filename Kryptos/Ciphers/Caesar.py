#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Caesar.py — the Caesar shift cipher and its generalisation, the affine cipher.

The Code Book (CD-ROM Overview, "The Birth of Cryptography"):

    "we can think of the Caesar cipher in terms of addition. If each letter is
     labelled 0-25, then encryption involves adding a fixed value to each
     number ... If encryption is addition, then decryption is subtraction.
     ... Z=25, and 25+2=27, and 27=1(mod26), and 1=B, so Z would be encrypted
     as B."

        c = (p + k) mod 26            encrypt
        p = (c - k) mod 26            decrypt

The affine cipher combines a multiply and an add:

        c = (a*p + b) mod 26          decrypt: p = a^-1 * (c - b) mod 26

    "Although it is okay to multiply by 3, it is not okay to multiply by 2 ...
     you can only multiply by a number that does not share a factor with 26."
     (a must be coprime to 26 — else the map is many-to-one.)  The affine
     lesson's proof of that is quoted in `docs/` of the Kryptos face.

This module is pure functions — the Pycrypt CaesarDialog and the analysis
brute-forcer both call in here.
"""

from math import gcd

from .common import ALPHABET, A, modinv, only_letters_preserving_case, ENGLISH_FREQ

# a-values coprime to 26 — the only valid affine multipliers
COPRIME_A = [a for a in range(1, A) if gcd(a, A) == 1]   # 1,3,5,7,9,11,15,17,19,21,23,25


def _map_case(ch: str, fn) -> str:
    """Apply fn(index)->index to a letter, keeping its case; pass others through."""
    if ch.isupper():
        return ALPHABET[fn(ALPHABET.index(ch)) % A]
    if ch.islower():
        return ALPHABET[fn(ALPHABET.index(ch.upper())) % A].lower()
    return ch


def shift(text: str, k: int) -> str:
    """Caesar encrypt: c = (p + k) mod 26.  Non-letters pass through unchanged
    (the old Pycrypt Caesar dialog kept spaces and punctuation in place)."""
    return ''.join(_map_case(ch, lambda p: p + k) for ch in text)


def unshift(text: str, k: int) -> str:
    """Caesar decrypt: p = (c - k) mod 26."""
    return ''.join(_map_case(ch, lambda c: c - k) for ch in text)


def affine(text: str, a: int, b: int) -> str:
    """Affine encrypt: c = (a*p + b) mod 26.  Raises if a is not coprime to 26."""
    if gcd(a, A) != 1:
        raise ValueError(f'affine multiplier a={a} shares a factor with 26 '
                         f'(many-to-one — not a cipher)')
    return ''.join(_map_case(ch, lambda p: a * p + b) for ch in text)


def affine_decrypt(text: str, a: int, b: int) -> str:
    """Affine decrypt: p = a^-1 * (c - b) mod 26."""
    ainv = modinv(a, A)
    return ''.join(_map_case(ch, lambda c: ainv * (c - b)) for ch in text)


def brute_force(text: str):
    """All 25 non-trivial Caesar shifts (the Code Book: "each member of the
    group could check a different shift").  Returns [(k, plaintext), ...]."""
    return [(k, unshift(text, k)) for k in range(1, A)]


def _chi_squared(text: str) -> float:
    """Goodness-of-fit of `text` to English letter frequencies — lower is
    more English-like.  Used to rank brute-force candidates."""
    up = [c for c in text.upper() if c in ALPHABET]
    n = len(up)
    if n == 0:
        return float('inf')
    score = 0.0
    for letter in ALPHABET:
        observed = up.count(letter)
        expected = ENGLISH_FREQ[letter] / 100.0 * n
        if expected:
            score += (observed - expected) ** 2 / expected
    return score


def best_shift(text: str):
    """Most English-like Caesar shift.  Returns (k, plaintext, chi2)."""
    ranked = sorted(((k, pt, _chi_squared(pt)) for k, pt in brute_force(text)),
                    key=lambda t: t[2])
    return ranked[0]


def affine_break(text: str, top: int = 3):
    """Try every valid (a, b); rank by chi-squared against English.

    Code Book affine lesson — the keyspace is only 12*26 = 312, so exhaustive
    search is instant.  Returns the `top` best [(a, b, plaintext, chi2), ...].
    """
    cands = []
    for a in COPRIME_A:
        for b in range(A):
            pt = affine_decrypt(text, a, b)
            cands.append((a, b, pt, _chi_squared(pt)))
    cands.sort(key=lambda t: t[3])
    return cands[:top]


if __name__ == '__main__':
    # Overview doc worked example: shift of 2, Z -> B.
    assert shift('Z', 2) == 'B'
    assert shift('ABC XYZ', 2) == 'CDE ZAB'
    assert unshift(shift('THE QUICK BROWN FOX', 7), 7) == 'THE QUICK BROWN FOX'

    # Affine lesson: "One Ring to rule them all ..." decodes with a^-1 = 9 (a=3).
    ct = affine('ONE RING TO RULE THEM ALL', 3, 5)
    assert affine_decrypt(ct, 3, 5) == 'ONE RING TO RULE THEM ALL'
    try:
        affine('TEST', 2, 1)          # 2 shares a factor with 26
    except ValueError:
        pass
    else:
        raise AssertionError('affine a=2 should be rejected')

    k, pt, _ = best_shift(shift('ATTACK AT DAWN THE SECRET IS SAFE', 11))
    assert k == 11 and pt == 'ATTACK AT DAWN THE SECRET IS SAFE', (k, pt)

    a, b, pt, _ = affine_break(affine('THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG', 7, 3))[0]
    assert (a, b) == (7, 3), (a, b, pt)
    print('Caesar / affine self-test: HOLDS')
