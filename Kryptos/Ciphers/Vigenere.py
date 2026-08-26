#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Vigenere.py — the historical Vigenere cipher, English 26-letter alphabet,
tabula recta, encrypt/decrypt exactly as done by hand since the 16th
century — plus a quaternion-SHAPED view of what one ciphertext letter
actually is.

Cody, 2026-08-25: "that cipher is, in quaternion, just the real output,
and the three imaginary 'what line, what position on line, what
character set(order)'...those three components result in a ciphertext
output."

One ciphertext letter is the REAL component. The three things that
generated it are the imaginary components:

    w (real)  the ciphertext letter itself — the one thing anyone
              intercepting the message actually sees
    i         LINE — which repetition of the key this position falls on
              (position // key_length)
    j         POSITION ON LINE — where within one key cycle
              (position % key_length)
    k         CHARACTER SET — which letter of the key is in force here,
              kept as the literal key CHARACTER rather than forced into
              a number it doesn't need to be (Cody: "even if one of those
              dimensions is a python object...lol")

FORWARD (encrypt) is exactly w = f(i, j, k) — well-defined, always, one
equation with three knowns producing one output.

BACKWARD is the honest limit, stated plainly rather than oversold: given
ONLY w — one letter — there is no way to recover THREE unknowns (i, j, k)
from it alone. That isn't a property of quaternions failing; one equation
can't determine three unknowns regardless of what algebra it's written
in. The real "return path" this cipher has always had is decrypt() below
— it recovers plaintext because the KEY (k, and therefore what j means)
is already known, exactly as it has been since Vigenere's own century.
Where the (i, j, k) decomposition genuinely earns its keep is comparing
MANY positions against each other at once, grouped by j — see
quaternion_trace()'s demo at the bottom, and SedenionFactoralRelativity's
crystal/factoral-spiral tools (PW11, PW13) for the real machinery that
does that comparison, which this file does not reimplement.
"""

from dataclasses import dataclass
from typing import List

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
A = len(ALPHABET)


def _clean(text: str) -> str:
    """Historical Vigenere: uppercase letters only, everything else
    (spaces, punctuation) dropped — the tabula recta has no entry for them."""
    return ''.join(ch for ch in text.upper() if ch in ALPHABET)


def encrypt(plaintext: str, key: str) -> str:
    pt = _clean(plaintext)
    key = _clean(key)
    if not key:
        raise ValueError("key must contain at least one letter")
    out = []
    for i, ch in enumerate(pt):
        p = ALPHABET.index(ch)
        k = ALPHABET.index(key[i % len(key)])
        out.append(ALPHABET[(p + k) % A])
    return ''.join(out)


def decrypt(ciphertext: str, key: str) -> str:
    ct = _clean(ciphertext)
    key = _clean(key)
    if not key:
        raise ValueError("key must contain at least one letter")
    out = []
    for i, ch in enumerate(ct):
        c = ALPHABET.index(ch)
        k = ALPHABET.index(key[i % len(key)])
        out.append(ALPHABET[(c - k) % A])
    return ''.join(out)


@dataclass
class VigenereQuaternion:
    """One ciphertext letter, in the (w, i, j, k) shape Cody described.
    w is the observable; i, j, k are the hidden generative coordinates
    that produced it. k is kept as the literal key CHARACTER, not
    coerced into a number — it doesn't need to be one to be useful here."""
    w: str    # ciphertext letter — the real component
    i: int    # line — which repetition of the key
    j: int    # position on this line (0..key_length-1)
    k: str    # character set — the key letter in force here

    def __repr__(self) -> str:
        return f"({self.w!r} | line={self.i}, pos={self.j}, key={self.k!r})"


def quaternion_trace(plaintext: str, key: str) -> List[VigenereQuaternion]:
    """encrypt(), returning the full (w,i,j,k) record for every position
    instead of just the ciphertext string."""
    pt = _clean(plaintext)
    key = _clean(key)
    K = len(key)
    trace = []
    for pos, ch in enumerate(pt):
        p = ALPHABET.index(ch)
        kc = key[pos % K]
        k_val = ALPHABET.index(kc)
        w = ALPHABET[(p + k_val) % A]
        trace.append(VigenereQuaternion(w=w, i=pos // K, j=pos % K, k=kc))
    return trace


if __name__ == '__main__':
    plaintext = "ATTACKATDAWN"
    key = "LEMON"

    ct = encrypt(plaintext, key)
    pt_back = decrypt(ct, key)
    print(f"plaintext:  {plaintext}")
    print(f"key:        {key}")
    print(f"ciphertext: {ct}")
    print(f"decrypted:  {pt_back}")
    assert pt_back == _clean(plaintext), "round-trip failed"
    print()

    print("quaternion trace (w | line, pos, key-char):")
    for q in quaternion_trace(plaintext, key):
        print(f"  {q}")

    # The grouping the classical Kasiski/Friedman method (and this
    # project's own PW11 crystal) already exploits: every position
    # sharing the same j (position on line) shares the same k (key
    # character) BY CONSTRUCTION, for the true key length — grouping by j
    # and checking that k is constant within each group is the same
    # observation "period recovery" is built on, just read directly here
    # instead of inferred from repeat-distances.
    print()
    print("grouped by j (position on line) -- k is constant within each group:")
    trace = quaternion_trace(plaintext, key)
    by_j = {}
    for q in trace:
        by_j.setdefault(q.j, []).append(q)
    for j in sorted(by_j):
        ks = {q.k for q in by_j[j]}
        print(f"  j={j}: {[q.w for q in by_j[j]]}  key-chars used: {ks} "
             f"({'constant' if len(ks) == 1 else 'VARIES'})")
