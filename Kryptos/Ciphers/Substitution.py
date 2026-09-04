#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Substitution.py — the general monoalphabetic substitution cipher and the
frequency-analysis attack that breaks it.

The Code Book (CD-ROM Overview):

    "The most general form of substitution allows the cipher alphabet to be any
     rearrangement of the alphabet, so it has 26! or 400 million billion
     billion keys."

    al-Kindi: "if a letter is replaced with a different letter ... the new
     letter will take on all the characteristics of the original ... The most
     obvious trait is frequency."

The old Pycrypt "Scrabble" dialog did two things, both ported here:
  * manual 26-tile mapping  ->  SubstitutionKey built by hand
  * "map by frequency"      ->  solve_by_frequency(): line the ciphertext's
                                letter-frequency order up against English's
                                (`scrabblefreq` in the old build)

Keyword alphabets (freq-analysis lesson: keyword 'BAD' is a *bad* key because
every letter maps to itself except A,B,C,D) are built by keyword_alphabet().
"""

from collections import Counter
from dataclasses import dataclass

from .common import ALPHABET, A, clean, ENGLISH_FREQ_ORDER


@dataclass
class SubstitutionKey:
    """plain -> cipher.  `mapping` is a 26-char string: mapping[i] is the
    cipher letter for ALPHABET[i]."""
    mapping: str = ALPHABET

    def __post_init__(self):
        m = self.mapping.upper()
        if len(m) != A:
            raise ValueError('substitution key must be 26 letters')
        self.mapping = m

    @property
    def inverse(self) -> str:
        inv = [''] * A
        for i, ch in enumerate(self.mapping):
            inv[ALPHABET.index(ch)] = ALPHABET[i]
        return ''.join(inv)

    def encrypt(self, text: str) -> str:
        return _apply(text, self.mapping)

    def decrypt(self, text: str) -> str:
        return _apply(text, self.inverse)


def _apply(text: str, table: str) -> str:
    out = []
    for ch in text:
        if ch.isupper():
            out.append(table[ALPHABET.index(ch)])
        elif ch.islower():
            out.append(table[ALPHABET.index(ch.upper())].lower())
        else:
            out.append(ch)
    return ''.join(out)


def keyword_alphabet(keyword: str) -> SubstitutionKey:
    """Cipher alphabet = unique letters of the keyword, then the rest of the
    alphabet in order.  keyword 'PHANTOM' -> PHANTOMBCDEFGIJKLQRSUVWXYZ."""
    seen = []
    for ch in clean(keyword):
        if ch not in seen:
            seen.append(ch)
    for ch in ALPHABET:
        if ch not in seen:
            seen.append(ch)
    return SubstitutionKey(''.join(seen))


def encrypt(text: str, key) -> str:
    if isinstance(key, str):
        key = keyword_alphabet(key)
    return key.encrypt(text)


def decrypt(text: str, key) -> str:
    if isinstance(key, str):
        key = keyword_alphabet(key)
    return key.decrypt(text)


def frequency_order(text: str) -> str:
    """Letters of `text` most-common first; letters that never appear are
    appended in English-frequency order so the result is always 26 long."""
    counts = Counter(clean(text))
    ordered = [c for c, _ in counts.most_common()]
    for c in ENGLISH_FREQ_ORDER:
        if c not in ordered:
            ordered.append(c)
    return ''.join(ordered)


def solve_by_frequency(ciphertext: str) -> SubstitutionKey:
    """al-Kindi's method, mechanised: the most common ciphertext letter is
    guessed to be E, the next T, and so on down the English order.  Returns a
    SubstitutionKey (plain->cipher) so `.decrypt(ciphertext)` gives the first
    guess at plaintext — a starting point, not the answer."""
    cipher_order = frequency_order(ciphertext)         # cipher letters by freq
    guess = {}                                         # plain -> cipher
    for plain, cipher in zip(ENGLISH_FREQ_ORDER, cipher_order):
        guess[plain] = cipher
    mapping = ''.join(guess[p] for p in ALPHABET)
    return SubstitutionKey(mapping)


if __name__ == '__main__':
    key = keyword_alphabet('PHANTOM')
    assert key.mapping == 'PHANTOMBCDEFGIJKLQRSUVWXYZ', key.mapping
    pt = 'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG'
    assert decrypt(encrypt(pt, key), key) == pt

    # 'BAD' keyword — the freq lesson's cautionary example: only A,B,C,D move.
    bad = keyword_alphabet('BAD')
    assert bad.mapping == 'BADCEFGHIJKLMNOPQRSTUVWXYZ', bad.mapping

    # frequency solve: the commonest ciphertext letter must decrypt to E, the
    # next to T (al-Kindi's first two moves).  It is a *starting point*, not a
    # full solver — deeper recovery needs the pattern-dictionary attack and the
    # hint rules in analysis.py.
    sample = ("IT WAS THE BEST OF TIMES IT WAS THE WORST OF TIMES IT WAS THE "
              "AGE OF WISDOM IT WAS THE AGE OF FOOLISHNESS") * 3
    ct = encrypt(sample, keyword_alphabet('ZEBRAS'))
    k = solve_by_frequency(ct)
    cipher_by_freq = frequency_order(ct)
    assert k.mapping[ALPHABET.index('E')] == cipher_by_freq[0]
    assert k.mapping[ALPHABET.index('T')] == cipher_by_freq[1]
    print('Substitution self-test: HOLDS')
