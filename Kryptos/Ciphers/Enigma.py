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

# ── ETW / entry wheel ──────────────────────────────────────────────────────
# Enigma I (Wehrmacht / Luftwaffe) wired the entry wheel straight through in
# A-B-C order, so it is the identity.  Kept explicit so the traced path has a
# real ETW hop to draw (the commercial Enigma D used QWERTZ order here).
ETW_IDENTITY = ALPHABET


def load_codebook_cd_rotors(cdrom_dir):
    """Parse Nick Mee / Virtual Image's virtual-Enigma wirings shipped on 'The
    Code Book on CD-ROM' (`ROTOR1.INF`..`ROTOR5.INF`, `reflect1.INF`,
    `reflect2.INF`) into the same shape as ROTOR_WIRING / ROTOR_NOTCH /
    REFLECTOR_WIRING above.

    File format (confirmed by inspection of the CD files):
      ROTORn.INF   — 27 integers: line 0 = turnover/notch contact (0-25),
                     lines 1-26 = the forward wiring permutation
                     (index = input contact, value = output contact)
      reflectn.INF — 26 integers: an involution permutation

    Returns (wiring, notch, reflectors) dicts keyed 'CD-I'..'CD-V' / 'CD-B',
    'CD-C'.  This is the rotor set a Code Book reader would actually have seen;
    it is NOT the historical Wehrmacht wiring, and the CD emulator's exact
    turnover semantics are unverified — so it is offered as an alternate set,
    never the default.
    """
    import os

    def _nums(name):
        with open(os.path.join(cdrom_dir, name)) as f:
            return [int(x) for x in f.read().split()]

    def _perm_to_string(perm):
        return ''.join(ALPHABET[perm[i]] for i in range(A))

    wiring, notch, reflectors = {}, {}, {}
    names = {'CD-I': 'ROTOR1.INF', 'CD-II': 'ROTOR2.INF', 'CD-III': 'ROTOR3.INF',
             'CD-IV': 'ROTOR4.INF', 'CD-V': 'ROTOR5.INF'}
    for label, fname in names.items():
        raw = _nums(fname)
        turnover, perm = raw[0], raw[1:]
        if sorted(perm) != list(range(A)):
            raise ValueError(f'{fname}: wiring is not a permutation of 0-25')
        wiring[label] = _perm_to_string(perm)
        notch[label] = ALPHABET[turnover % A]
    for label, fname in {'CD-B': 'reflect1.INF', 'CD-C': 'reflect2.INF'}.items():
        perm = _nums(fname)
        if sorted(perm) != list(range(A)) or any(perm[perm[i]] != i for i in range(A)):
            raise ValueError(f'{fname}: reflector is not an involution')
        reflectors[label] = _perm_to_string(perm)
    return wiring, notch, reflectors


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

    # ── traced variants: same maths, but also hand back the two INTERNAL
    # contacts the current crosses inside the rotor, so the visualiser can
    # draw the exact wire in use (offset by the rotor's rotation).
    def forward_traced(self, c: int):
        shifted = (c + self.position - self.ring) % A
        out = ALPHABET.index(self.wiring[shifted])
        return (out - self.position + self.ring) % A, shifted, out

    def backward_traced(self, c: int):
        shifted = (c + self.position - self.ring) % A
        out = ALPHABET.index(self.wiring_inv[shifted])
        return (out - self.position + self.ring) % A, shifted, out


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


@dataclass
class Hop:
    """One leg of the electrical path through the machine for a single
    keypress.  `contact_in` / `contact_out` are absolute bus contacts (0-25,
    the fixed frame) — they line up between components, so the visualiser
    connects one Hop's `contact_out` to the next Hop's `contact_in`.

    For rotor hops `internal_in` / `internal_out` are the two contacts the
    current crosses INSIDE the rotor (the wire actually used), and `position`
    is that rotor's stepping position at the moment of the keypress.
    """
    component: str            # 'keyboard' 'plugboard' 'ETW' 'rotor' 'reflector' 'lamp'
    label: str                # 'III' 'II' 'I' 'B' ... or ''
    contact_in: int
    contact_out: int
    internal_in: int = None
    internal_out: int = None
    position: int = None
    leg: str = 'forward'      # 'forward' (key -> reflector) or 'return'

    @property
    def letter_in(self) -> str:
        return ALPHABET[self.contact_in]

    @property
    def letter_out(self) -> str:
        return ALPHABET[self.contact_out]


@dataclass
class Path:
    """The full, ordered traversal for one keypress — 'the one function behind
    the scenes'.  Everything the visualiser draws comes from here."""
    letter: str               # key pressed
    lamp: str                 # lamp lit (ciphertext letter)
    hops: List[Hop]
    windows: str              # rotor window letters after stepping, e.g. 'ABQ'
    stepped: List[str] = field(default_factory=list)   # which rotors stepped
    double_step: bool = False

    def __repr__(self) -> str:
        chain = ' → '.join(h.letter_in for h in self.hops) + f' → {self.lamp}'
        return f"Path({self.letter}→{self.lamp} | windows={self.windows} | {chain})"


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
        self._reflector_name = reflector
        self.reflector = REFLECTOR_WIRING[reflector]
        self.plugboard = Plugboard(plugboard)

    def _step_rotors(self):
        # Standard stepping WITH the double-stepping anomaly: the middle
        # rotor steps if it is AT its own notch (causing itself and the
        # left rotor to step together) OR if the right rotor is at its
        # notch. The right rotor always steps.
        stepped, double = [], False
        if self.rotor2.at_notch:
            self.rotor1.step(); self.rotor2.step()
            stepped += ['left', 'middle']
            double = True
        elif self.rotor3.at_notch:
            self.rotor2.step()
            stepped.append('middle')
        self.rotor3.step()
        stepped.append('right')
        return stepped, double

    @property
    def windows(self) -> str:
        """The three letters visible in the rotor windows, left to right."""
        return (ALPHABET[self.rotor1.position]
                + ALPHABET[self.rotor2.position]
                + ALPHABET[self.rotor3.position])

    def trace_path(self, letter: str) -> 'Path':
        """THE traversal — historically accurate, one source of truth.

        Advances the machine state (with double-stepping), then walks the
        entire electrical circuit and records every leg as a Hop:

            key → plugboard → ETW → rotor III → II → I
                → reflector
                → rotor I → II → III → ETW → plugboard → lamp

        `press()` / `encrypt()` / `vector_trace()` all build on this; the SVG
        visualiser draws ONLY what this returns.
        """
        stepped, double = self._step_rotors()
        hops: List[Hop] = []

        x = ALPHABET.index(letter.upper())
        hops.append(Hop('keyboard', '', x, x, leg='forward'))

        c = self.plugboard.swap(x)
        hops.append(Hop('plugboard', '', x, c, leg='forward'))
        hops.append(Hop('ETW', '', c, c, leg='forward'))

        for rot, name in ((self.rotor3, 'III'), (self.rotor2, 'II'), (self.rotor1, 'I')):
            nxt, ii, io = rot.forward_traced(c)
            hops.append(Hop('rotor', name, c, nxt, ii, io, rot.position, 'forward'))
            c = nxt

        r = ALPHABET.index(self.reflector[c])
        hops.append(Hop('reflector', self._reflector_name, c, r, leg='return'))
        c = r

        for rot, name in ((self.rotor1, 'I'), (self.rotor2, 'II'), (self.rotor3, 'III')):
            nxt, ii, io = rot.backward_traced(c)
            hops.append(Hop('rotor', name, c, nxt, ii, io, rot.position, 'return'))
            c = nxt

        hops.append(Hop('ETW', '', c, c, leg='return'))
        out = self.plugboard.swap(c)
        hops.append(Hop('plugboard', '', c, out, leg='return'))
        hops.append(Hop('lamp', '', out, out, leg='return'))

        return Path(letter=ALPHABET[x], lamp=ALPHABET[out], hops=hops,
                    windows=self.windows, stepped=stepped, double_step=double)

    def press(self, letter: str) -> EnigmaVector:
        """Kept for the (w, i, j, k) quaternion framing — now just a repackage
        of trace_path()'s Hop list."""
        path = self.trace_path(letter)
        h = path.hops
        # h: [key, plug, ETW, rIII, rII, rI, reflector, rI, rII, rIII, ETW, plug, lamp]
        fwd = RotorQuaternion(i=h[3].letter_out, j=h[4].letter_out,
                              k=h[5].letter_out, real=h[5].letter_out)
        bwd = RotorQuaternion(i=h[7].letter_out, j=h[8].letter_out,
                              k=h[9].letter_out, real=h[9].letter_out)
        return EnigmaVector(
            plugboard_in=h[1].letter_out, rotor_forward=fwd,
            reflector=h[6].letter_out, rotor_backward=bwd, real=path.lamp)

    def encrypt(self, text: str) -> str:
        text = ''.join(ch for ch in text.upper() if ch in ALPHABET)
        return ''.join(self.trace_path(ch).lamp for ch in text)

    def path_trace(self, text: str) -> List['Path']:
        text = ''.join(ch for ch in text.upper() if ch in ALPHABET)
        return [self.trace_path(ch) for ch in text]

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
    print()

    # trace_path is the single source of truth: its lamp must equal encrypt(),
    # its hop chain must be contiguous (each hop's out == next hop's in), and
    # the first keypress from AAA must step the fast rotor A -> B.
    e4 = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA', reflector='B')
    p = e4.trace_path('A')
    assert p.lamp == 'B', p
    assert p.windows == 'AAB', p.windows
    for h1, h2 in zip(p.hops, p.hops[1:]):
        assert h1.contact_out == h2.contact_in, (h1, h2)
    assert [h.component for h in p.hops] == [
        'keyboard', 'plugboard', 'ETW', 'rotor', 'rotor', 'rotor',
        'reflector', 'rotor', 'rotor', 'rotor', 'ETW', 'plugboard', 'lamp']
    e5 = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA', reflector='B')
    assert ''.join(e5.trace_path(c).lamp for c in 'AAAAA') == 'BDZGO'
    print("trace_path self-test: HOLDS  (chain contiguous, lamp == encrypt)")

    # optional: The Code Book CD-ROM rotor set, if the CD tree is present
    import os
    _cd = os.path.join(os.path.dirname(__file__), '..', 'TheCodeBook',
                       'cdrom', 'Codebook')
    if os.path.isfile(os.path.join(_cd, 'ROTOR1.INF')):
        w, n, refl = load_codebook_cd_rotors(_cd)
        assert set(w) == {'CD-I', 'CD-II', 'CD-III', 'CD-IV', 'CD-V'}
        assert set(refl) == {'CD-B', 'CD-C'}
        print(f"Code Book CD rotor set parsed: {sorted(w)} + {sorted(refl)}")
