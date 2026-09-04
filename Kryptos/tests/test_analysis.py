#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""The 'methods to break each' — cryptanalysis helpers."""

from Kryptos import analysis
from Kryptos.Ciphers.Vigenere import encrypt as vig_enc
from Kryptos.Ciphers.common import clean

DECL = ("WE HOLD THESE TRUTHS TO BE SELF EVIDENT THAT ALL MEN ARE CREATED EQUAL "
        "THAT THEY ARE ENDOWED BY THEIR CREATOR WITH CERTAIN UNALIENABLE RIGHTS "
        "THAT AMONG THESE ARE LIFE LIBERTY AND THE PURSUIT OF HAPPINESS") * 3


def test_pattern_signature():
    assert analysis.pattern_signature('HELLO') == '12334'
    assert analysis.pattern_signature('PEOPLE') == '123142'
    assert analysis.pattern_signature('MISSISSIPPI') == '12332332442'


def test_index_of_coincidence_english_vs_random():
    assert analysis.index_of_coincidence(DECL) > 0.06
    poly = vig_enc(DECL, 'ABCDEFGHIJKLM')            # 13-long key flattens it
    assert analysis.index_of_coincidence(poly) < 0.05


def test_kasiski_and_break_vigenere():
    ct = vig_enc(DECL, 'LIBERTY')
    res = analysis.break_vigenere(ct)
    assert res['period'] == 7
    assert res['key'] == 'LIBERTY'
    assert res['plaintext'] == clean(DECL)


def test_ioc_by_period_peaks_at_key_length():
    ct = vig_enc(DECL, 'PHANTOM')                    # period 7
    scores = dict(analysis.ioc_by_period(ct, 14))
    assert scores[7] == max(scores[p] for p in (2, 3, 4, 5, 6, 7))


def test_vowel_trowel_flags_e():
    v, c = analysis.vowel_trowel(DECL)
    assert 'E' in v[:3]


def test_dictionary_attack_matches_by_pattern():
    from Kryptos.Ciphers.Substitution import encrypt, keyword_alphabet
    ct = encrypt('THE PEOPLE WILL SEE', keyword_alphabet('ZEBRAS'))
    crib = analysis.dictionary_attack(ct)
    # the cipher form of THE must offer THE/AND-shaped 3-letter candidates
    cipher_the = encrypt('THE', keyword_alphabet('ZEBRAS'))
    assert cipher_the in crib
    assert any(len(w) == 3 for w in crib[cipher_the])


def test_enigma_keyspace_matches_codebook_lesson():
    ks = analysis.enigma_keyspace()
    assert ks['rotor_order'] == 60
    assert ks['rotor_positions'] == 17576
    assert ks['optimum_leads'] == 11
    assert analysis.plugboard_settings(10) == 150738274937250


def test_hints_are_generated():
    from Kryptos.Ciphers.Substitution import encrypt, keyword_alphabet
    ct = encrypt(DECL, keyword_alphabet('PHANTOM'))
    h = analysis.hints(ct)
    assert h and any('E' in line for line in h)
