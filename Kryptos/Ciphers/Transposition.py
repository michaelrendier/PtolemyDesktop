#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Transposition.py — the two transposition ciphers from the start of The Code Book:
the rail fence and the scytale.

The Code Book (CD-ROM Overview):

    "The transposition method moves the characters around ... The CD-ROM
     contains examples of transposition, such as the railfence cipher or the
     scytale ..."

    scytale — a strip of leather wound round a wooden staff; you write across
    the wound strip, unwind it, and the letters are jumbled until wound round
    a staff of the same diameter.

The old Pycrypt build implemented both with one shared routine that popped
items out of a shrinking list and padded with 'X'; it did not round-trip.
Rewritten here as two correct, separately-invertible engines.

Letters only, uppercase — the hand-cipher stream.  Padding letter is 'X'
(kept visible so the workbench shows the block size that was used).
"""

from math import ceil

from .common import clean

PAD = 'X'


# ── rail fence — the zig-zag ────────────────────────────────────────────────

def _fence_pattern(length: int, rails: int):
    """Row index for each position along a `rails`-deep zig-zag."""
    if rails < 2:
        return [0] * length
    row, step = 0, 1
    out = []
    for _ in range(length):
        out.append(row)
        if row == 0:
            step = 1
        elif row == rails - 1:
            step = -1
        row += step
    return out


def railfence_encrypt(text: str, rails: int) -> str:
    s = clean(text)
    if rails < 2:
        return s
    rows = [[] for _ in range(rails)]
    for ch, r in zip(s, _fence_pattern(len(s), rails)):
        rows[r].append(ch)
    return ''.join(''.join(r) for r in rows)


def railfence_decrypt(text: str, rails: int) -> str:
    s = clean(text)
    if rails < 2:
        return s
    pattern = _fence_pattern(len(s), rails)
    counts = [pattern.count(r) for r in range(rails)]
    # slice the ciphertext back into rows
    rows, i = [], 0
    for c in counts:
        rows.append(list(s[i:i + c]))
        i += c
    # walk the zig-zag, pulling the next letter from each row in turn
    idx = [0] * rails
    out = []
    for r in pattern:
        out.append(rows[r][idx[r]])
        idx[r] += 1
    return ''.join(out)


# ── scytale — column transposition by rod diameter ─────────────────────────

def scytale_encrypt(text: str, diameter: int) -> str:
    """Write the message in rows `diameter` wide (row by row), then read it off
    column by column — what you get winding the strip off the rod."""
    s = clean(text)
    if diameter < 2:
        return s
    if len(s) % diameter:
        s += PAD * (diameter - len(s) % diameter)
    rows = len(s) // diameter
    return ''.join(s[r * diameter + c] for c in range(diameter) for r in range(rows))


def scytale_decrypt(text: str, diameter: int) -> str:
    s = clean(text)
    if diameter < 2:
        return s
    rows = ceil(len(s) / diameter)
    # ciphertext is column-major; refill columns, read rows
    grid = [['' for _ in range(diameter)] for _ in range(rows)]
    k = 0
    for c in range(diameter):
        for r in range(rows):
            if k < len(s):
                grid[r][c] = s[k]
                k += 1
    out = ''.join(grid[r][c] for r in range(rows) for c in range(diameter))
    return out.rstrip(PAD)


if __name__ == '__main__':
    msg = 'WE ARE DISCOVERED FLEE AT ONCE'
    for n in range(2, 9):
        assert railfence_decrypt(railfence_encrypt(msg, n), n) == clean(msg), n
        assert scytale_decrypt(scytale_encrypt(msg, n), n) == clean(msg), n
    # canonical rail-fence example (3 rails)
    assert railfence_encrypt('WEAREDISCOVEREDFLEEATONCE', 3) == 'WECRLTEERDSOEEFEAOCAIVDEN'
    print('Transposition self-test: HOLDS')
