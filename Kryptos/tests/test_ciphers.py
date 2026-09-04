#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Round-trips + known-answer vectors for every Pycrypt cipher engine."""

import pytest

from Kryptos.Ciphers import Caesar, Transposition, Substitution, Playfair, Vigenere
from Kryptos.Ciphers.Enigma import Enigma
from Kryptos.Ciphers.common import clean

PT = 'THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG'


# ── Caesar / affine ────────────────────────────────────────────────────────
def test_caesar_overview_vector():
    assert Caesar.shift('Z', 2) == 'B'                 # CD-ROM Overview example


@pytest.mark.parametrize('k', range(1, 26))
def test_caesar_roundtrip(k):
    assert Caesar.unshift(Caesar.shift(PT, k), k) == PT


def test_caesar_brute_force_finds_shift():
    k, pt, _ = Caesar.best_shift(Caesar.shift(PT, 11))
    assert (k, pt) == (11, PT)


def test_affine_rejects_non_coprime():
    with pytest.raises(ValueError):
        Caesar.affine('ABC', 2, 1)


def test_affine_roundtrip_and_break():
    ct = Caesar.affine(PT, 7, 3)
    assert Caesar.affine_decrypt(ct, 7, 3) == PT
    a, b, _, _ = Caesar.affine_break(ct)[0]
    assert (a, b) == (7, 3)


# ── transposition ─────────────────────────────────────────────────────────
@pytest.mark.parametrize('n', range(2, 10))
def test_railfence_roundtrip(n):
    assert Transposition.railfence_decrypt(
        Transposition.railfence_encrypt(PT, n), n) == clean(PT)


@pytest.mark.parametrize('n', range(2, 10))
def test_scytale_roundtrip(n):
    assert Transposition.scytale_decrypt(
        Transposition.scytale_encrypt(PT, n), n) == clean(PT)


def test_railfence_known_vector():
    assert Transposition.railfence_encrypt('WEAREDISCOVEREDFLEEATONCE', 3) == \
        'WECRLTEERDSOEEFEAOCAIVDEN'


# ── substitution ──────────────────────────────────────────────────────────
def test_keyword_alphabet_bad_keyword():
    # freq-analysis lesson: keyword 'BAD' moves only A B C D
    assert Substitution.keyword_alphabet('BAD').mapping == \
        'BADCEFGHIJKLMNOPQRSTUVWXYZ'


def test_substitution_roundtrip():
    key = Substitution.keyword_alphabet('PHANTOM')
    assert Substitution.decrypt(Substitution.encrypt(PT, key), key) == PT


# ── playfair ──────────────────────────────────────────────────────────────
def test_playfair_known_vector():
    ct = Playfair.encrypt('Hide the gold in the tree stump', 'playfair example')
    assert ct == 'BMODZBXDNABEKUDMUIXMMOUVIF'
    assert Playfair.decrypt(ct, 'playfair example') == 'HIDETHEGOLDINTHETREXESTUMP'


# ── vigenere ──────────────────────────────────────────────────────────────
def test_vigenere_known_vector():
    assert Vigenere.encrypt('ATTACKATDAWN', 'LEMON') == 'LXFOPVEFRNHR'
    assert Vigenere.decrypt('LXFOPVEFRNHR', 'LEMON') == 'ATTACKATDAWN'


# ── enigma ────────────────────────────────────────────────────────────────
def test_enigma_bdzgo():
    e = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA', reflector='B')
    assert e.encrypt('AAAAA') == 'BDZGO'


def test_enigma_reciprocal():
    cfg = dict(rotors=['II', 'IV', 'V'], positions='BLA', rings='CDE',
               reflector='B', plugboard='AB CD EF')
    msg = 'THECODEBOOKBYSIMONSINGH'
    assert Enigma(**cfg).encrypt(Enigma(**cfg).encrypt(msg)) == msg


def test_enigma_no_letter_maps_to_itself():
    e = Enigma(rotors=['I', 'II', 'III'], positions='QEV', rings='AAA', reflector='B')
    ct = e.encrypt('A' * 200)
    assert 'A' not in ct                          # the crib weakness Bletchley used


def test_trace_path_is_contiguous_and_matches_encrypt():
    e = Enigma(rotors=['I', 'II', 'III'], positions='AAA', rings='AAA', reflector='B')
    lamps = ''
    for ch in 'AAAAA':
        p = e.trace_path(ch)
        lamps += p.lamp
        for h1, h2 in zip(p.hops, p.hops[1:]):
            assert h1.contact_out == h2.contact_in
        assert [h.component for h in p.hops] == [
            'keyboard', 'plugboard', 'ETW', 'rotor', 'rotor', 'rotor',
            'reflector', 'rotor', 'rotor', 'rotor', 'ETW', 'plugboard', 'lamp']
    assert lamps == 'BDZGO'


def test_codebook_cd_rotor_set_parses_if_present():
    import os
    from Kryptos.Ciphers.Enigma import load_codebook_cd_rotors
    cd = os.path.join(os.path.dirname(__file__), '..', 'TheCodeBook',
                      'cdrom', 'Codebook')
    if not os.path.isfile(os.path.join(cd, 'ROTOR1.INF')):
        pytest.skip('CD-ROM tree not present')
    w, n, refl = load_codebook_cd_rotors(cd)
    assert set(w) == {'CD-I', 'CD-II', 'CD-III', 'CD-IV', 'CD-V'}
    assert set(refl) == {'CD-B', 'CD-C'}
    assert all(len(v) == 26 and set(v) == set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
               for v in w.values())
