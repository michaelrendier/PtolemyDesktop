#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Enigma.py — the historical Wehrmacht Enigma I (3 rotors + reflector +
plugboard), real rotor wirings, plus a hierarchical quaternion-of-
quaternions trace of the signal path.

Cody, 2026-08-25, two passes at the shape:

Pass 1: "plug board + rotors x3 + reflector and back through rotors and
plug board to light...7 imaginary operation vectors." Resolved by
treating the plugboard as a separate pre/post layer OUTSIDE a 7-wide
scrambler (plugboard is a self-inverse involution — swap(swap(x))==x, so
forward and backward through it are the SAME operator, not two — and it's
physically bolted onto the outside of the rotor/reflector core in the
real machine, not one of its internal stages).

Pass 2, CORRECTING the flat 7-slot version: "i was counting rotors as one
object, the 3 rotor form is it's own quaternion, and the other four
imaginary terms their own component vector spaces...The real output part
of the quaternion would be the 'rotor object' slash 'ciphertext'."

So the shape actually built here is hierarchical, not flat:

    EnigmaVector           (real = the ciphertext letter — the lamp)
      plugboard_in           imaginary term 1 — a simple pointing tool
      rotor_forward           imaginary term 2 — its OWN RotorQuaternion
        i, j, k                 the three rotors' own outputs, in order
        real                    the bank's combined output — "the rotor object"
      reflector               imaginary term 3 — a simple pointing tool
      rotor_backward           imaginary term 4 — another RotorQuaternion instance

Four imaginary terms at the top level, exactly as described — two of
them (rotor_forward, rotor_backward) are the SAME structural type
(RotorQuaternion) used twice, not two different kinds of thing, and each
one's own "real" plays the identical ROLE one level down that
EnigmaVector.real plays at the top: the synthesized output of that
level's "single-path vector pointing tools," composed in order.

VERIFIED against the one worked example the Enigma-rotor-details literature
carries (Wikipedia, marked "[citation needed]" there too — noted, not
hidden): rotors I, II, III left-to-right, reflector B, all ring settings
A, start position AAA, plaintext AAAAA -> ciphertext BDZGO.
"""

from dataclasses import dataclass, field
from typing import List

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
A = len(ALPHABET)

# ── real historical wirings (Wehrmacht Enigma I, verified 2026-08-25 against
# Wikipedia's "Enigma rotor details" page) ──────────────────────────────────
ROTOR_WIRING = {
    'I':   'EKMFLGDQVZNTOWYHXUSPAIBRCJ',
    'II':  'AJDKSIRUXBLHWTMCQGZNPYFVOE',
    'III': 'BDFHJLCPRTXVZNYEIWGAKMUSQO',
    'IV':  'ESOVPZJAYQUIRHXLNFTGKDCMWB',
    'V':   'VZBRGITYUPSDNHLXAWMJQOFECK',
}
ROTOR_NOTCH = {'I': 'Q', 'II': 'E', 'III': 'V', 'IV': 'J', 'V': 'Z'}

REFLECTOR_WIRING = {
    'B': 'YRUHQSLDPXNGOKMIEBFZCWVJAT',
    'C': 'FVPJIAOYEDRZXWGCTKUQSBNMHL',
}


def _inverse(perm: str) -> str:
    inv = [''] * A
    for i, ch in enumerate(perm):
        inv[ALPHABET.index(ch)] = ALPHABET[i]
    return ''.join(inv)


class Rotor:
    def __init__(self, name: str, position: str = 'A', ring: str = 'A'):
        self.name = name
        self.wiring = ROTOR_WIRING[name]
        self.wiring_inv = _inverse(self.wiring)
        self.notch = ROTOR_NOTCH[name]
        self.position = ALPHABET.index(position)
        self.ring = ALPHABET.index(ring)

    @property
    def at_notch(self) -> bool:
        return ALPHABET[self.position] == self.notch

    def step(self) -> None:
        self.position = (self.position + 1) % A

    def forward(self, c: int) -> int:
        shifted = (c + self.position - self.ring) % A
        out = ALPHABET.index(self.wiring[shifted])
        return (out - self.position + self.ring) % A

    def backward(self, c: int) -> int:
        shifted = (c + self.position - self.ring) % A
        out = ALPHABET.index(self.wiring_inv[shifted])
        return (out - self.position + self.ring) % A


class Plugboard:
    def __init__(self, pairs: str = ''):
        """pairs: e.g. 'AB CD' swaps A<->B and C<->D. Self-inverse by
        construction — swap(swap(x)) == x always."""
        self.map = list(range(A))
        for pair in pairs.split():
            if len(pair) != 2:
                raise ValueError(f'bad plugboard pair: {pair!r}')
            a, b = ALPHABET.index(pair[0].upper()), ALPHABET.index(pair[1].upper())
            self.map[a], self.map[b] = b, a

    def swap(self, c: int) -> int:
        return self.map[c]


@dataclass
class RotorQuaternion:
    """Cody, 2026-08-25, correcting the flat 7-slot version above: "the 3
    rotor form is it's own quaternion...the real output part of the
    quaternion would be the 'rotor object'." The rotor bank is ONE
    structural unit, not three independent slots — real = the bank's own
    combined output (what actually leaves the third rotor it hits),
    i/j/k = the three individual rotors' own outputs along the way. This
    same TYPE is instantiated TWICE per keypress (forward pass, backward
    pass) — one archetype, two uses, not two different kinds of thing."""
    i: str      # first rotor hit
    j: str      # second rotor hit
    k: str      # third rotor hit
    real: str   # the bank's own combined output — "the rotor object"

    def __repr__(self) -> str:
        return f"[{self.real!r} | i={self.i!r} j={self.j!r} k={self.k!r}]"


@dataclass
class EnigmaVector:
    """One keypress. real = the lamp that lights (the ciphertext letter) —
    the SAME role RotorQuaternion.real plays one level down, one scale up.
    Four imaginary terms, each its own component vector space: plugboard
    and reflector are simple single-path pointing tools (one letter in,
    one out); rotor_forward and rotor_backward are each a full
    RotorQuaternion, not a scalar — "real world single-path vector
    pointing tools that in the right order produce a ciphertext real
    component," composed hierarchically rather than flattened into one
    7-wide list."""
    plugboard_in: str
    rotor_forward: RotorQuaternion
    reflector: str
    rotor_backward: RotorQuaternion
    real: str   # plugboard_out — the lamp that lights

    def __repr__(self) -> str:
        return (f"({self.real!r} | plug={self.plugboard_in!r}  "
               f"fwd={self.rotor_forward}  refl={self.reflector!r}  "
               f"bwd={self.rotor_backward})")


class Enigma:
    def __init__(self, rotors: List[str] = ('I', 'II', 'III'),
                positions: str = 'AAA', rings: str = 'AAA',
                reflector: str = 'B', plugboard: str = ''):
        # rotors[0] = leftmost (slow), rotors[-1] = rightmost (fast) — same
        # convention as the Wikipedia worked example ("I, II and III from
        # left to right").
        self.rotor1 = Rotor(rotors[0], positions[0], rings[0])  # left
        self.rotor2 = Rotor(rotors[1], positions[1], rings[1])  # middle
        self.rotor3 = Rotor(rotors[2], positions[2], rings[2])  # right
        self.reflector = REFLECTOR_WIRING[reflector]
        self.plugboard = Plugboard(plugboard)

    def _step_rotors(self) -> None:
        # Standard stepping WITH the double-stepping anomaly: the middle
        # rotor steps if it is AT its own notch (causing itself and the
        # left rotor to step together) OR if the right rotor is at its
        # notch. The right rotor always steps.
        if self.rotor2.at_notch:
            self.rotor1.step()
            self.rotor2.step()
        elif self.rotor3.at_notch:
            self.rotor2.step()
        self.rotor3.step()

    def press(self, letter: str) -> EnigmaVector:
        self._step_rotors()

        p_in = ALPHABET.index(letter.upper())
        c0 = self.plugboard.swap(p_in)

        c1 = self.rotor3.forward(c0)
        c2 = self.rotor2.forward(c1)
        c3 = self.rotor1.forward(c2)
        fwd = RotorQuaternion(i=ALPHABET[c1], j=ALPHABET[c2], k=ALPHABET[c3],
                              real=ALPHABET[c3])

        c4 = ALPHABET.index(self.reflector[c3])

        c5 = self.rotor1.backward(c4)
        c6 = self.rotor2.backward(c5)
        c7 = self.rotor3.backward(c6)
        bwd = RotorQuaternion(i=ALPHABET[c5], j=ALPHABET[c6], k=ALPHABET[c7],
                              real=ALPHABET[c7])

        out = self.plugboard.swap(c7)

        return EnigmaVector(
            plugboard_in=ALPHABET[c0], rotor_forward=fwd,
            reflector=ALPHABET[c4], rotor_backward=bwd, real=ALPHABET[out])

    def encrypt(self, text: str) -> str:
        text = ''.join(ch for ch in text.upper() if ch in ALPHABET)
        return ''.join(self.press(ch).real for ch in text)

    def vector_trace(self, text: str) -> List[EnigmaVector]:
        text = ''.join(ch for ch in text.upper() if ch in ALPHABET)
        return [self.press(ch) for ch in text]


if __name__ == '__main__':
    # The one worked example the literature carries (Wikipedia's own page
    # marks this "[citation needed]" -- noted, not hidden; it is still the
    # standard example nearly every from-scratch implementation checks
    # itself against).
    e = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA',
              reflector='B', plugboard='')
    ct = e.encrypt('AAAAA')
    print(f"rotors I,II,III  reflector B  rings AAA  start AAA")
    print(f"AAAAA -> {ct}   (expected BDZGO)")
    assert ct == 'BDZGO', f"Enigma self-test FAILED: got {ct}, expected BDZGO"
    print("Enigma self-test: HOLDS")
    print()

    # Reciprocity: Enigma is self-inverse at the machine-state level --
    # encrypting the ciphertext with the SAME starting configuration
    # recovers the plaintext, the property the whole machine was built
    # around (a sender and receiver with identical settings).
    e2 = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA', reflector='B')
    pt_back = e2.encrypt(ct)
    print(f"decrypt({ct!r}) -> {pt_back}   (expected AAAAA)")
    assert pt_back == 'AAAAA', "reciprocity FAILED"
    print("reciprocity: HOLDS")
    print()

    e3 = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA',
               reflector='B', plugboard='AB CD')
    print("vector trace, 'HELLO', plugboard AB CD:")
    for o in e3.vector_trace('HELLO'):
        print(f"  {o}")
