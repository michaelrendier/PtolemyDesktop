#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Playfair.py — Charles Wheatstone's 1854 digraph substitution cipher (popularised
by Lord Playfair), the first cipher to encrypt letter *pairs* rather than single
letters and so blunt straightforward frequency analysis.

The Code Book, "The Enigma Cipher Machine" intro:

    "instead of substituting individual letters, the sender might substitute
     pairs of letters, which is known as digraph substitution."

5x5 keyed square, I and J share a cell.  Rules:
  * split the message into pairs; a doubled pair gets an X between the two
    letters; a lone final letter is padded with X
  * both letters in the same row  -> take the letter to the right of each (wrap)
  * both in the same column       -> take the letter below each (wrap)
  * otherwise (a rectangle)       -> swap to the other letter's column, same row
Decrypt reverses row/column direction; the rectangle rule is its own inverse.

Ported from the old Pycrypt `Playfair` dialog (usekey / encode / decode /
matrixindex), corrected to pre-split doubled pairs.
"""

from .common import clean

PAD = 'X'


def build_square(keyword: str):
    """5x5 grid (list of 5 rows) from the keyword, J folded onto I."""
    seen = []
    for ch in clean(keyword).replace('J', 'I'):
        if ch not in seen:
            seen.append(ch)
    for ch in 'ABCDEFGHIKLMNOPQRSTUVWXYZ':      # no J
        if ch not in seen:
            seen.append(ch)
    return [seen[r * 5:(r + 1) * 5] for r in range(5)]


def _pos(square, ch: str):
    for r, row in enumerate(square):
        if ch in row:
            return r, row.index(ch)
    raise ValueError(ch)


def make_digraphs(text: str):
    """Letters-only, J->I, split into pairs with X between doubles and an X
    tail if odd."""
    s = clean(text).replace('J', 'I')
    pairs, i = [], 0
    while i < len(s):
        a = s[i]
        b = s[i + 1] if i + 1 < len(s) else PAD
        if a == b:
            pairs.append(a + PAD)
            i += 1
        else:
            pairs.append(a + b)
            i += 2
    return pairs


def _crypt_pair(square, a: str, b: str, d: int) -> str:
    r1, c1 = _pos(square, a)
    r2, c2 = _pos(square, b)
    if r1 == r2:
        return square[r1][(c1 + d) % 5] + square[r2][(c2 + d) % 5]
    if c1 == c2:
        return square[(r1 + d) % 5][c1] + square[(r2 + d) % 5][c2]
    return square[r1][c2] + square[r2][c1]


def encrypt(text: str, keyword: str) -> str:
    sq = build_square(keyword)
    return ''.join(_crypt_pair(sq, p[0], p[1], +1) for p in make_digraphs(text))


def decrypt(text: str, keyword: str) -> str:
    sq = build_square(keyword)
    s = clean(text).replace('J', 'I')
    pairs = [s[i:i + 2] for i in range(0, len(s), 2)]
    return ''.join(_crypt_pair(sq, p[0], p[1], -1) for p in pairs if len(p) == 2)


if __name__ == '__main__':
    # Wikipedia's canonical worked example.
    sq = build_square('playfair example')
    assert sq[0][:5] == ['P', 'L', 'A', 'Y', 'F']
    ct = encrypt('Hide the gold in the tree stump', 'playfair example')
    assert ct == 'BMODZBXDNABEKUDMUIXMMOUVIF', ct
    # round-trip (decrypt yields the X-padded plaintext)
    back = decrypt(ct, 'playfair example')
    assert back == 'HIDETHEGOLDINTHETREXESTUMP', back
    print('Playfair self-test: HOLDS')
