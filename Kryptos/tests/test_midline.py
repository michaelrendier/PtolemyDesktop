#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Midline: the 4-digit code T S DD over 96 characters, base-96 Horner address.

Rules under test (Cody, 2026-10-12): type 0 Upper / 1 Lower / 2 Digit / 3 Punct;
letters signed from the anchor M/m (step 0..13, anchor = sign 0); digits sign-less;
punctuation = LF, space + 32 symbols in ASCII order, even 17/17 split; tab = four
spaces; exactly 96 valid codes, nothing else decodes."""

import string
from itertools import product

import pytest

from Kryptos.Ciphers import Midline
from PtolemyDesktop.Archimedes.Maths import MidlineIndex as mi

DOMAIN = '\n' + ''.join(chr(c) for c in range(0x20, 0x7F))        # 96 characters


# ── the code table ─────────────────────────────────────────────────────────
@pytest.mark.parametrize('ch,code', [
    ('M', 0), ('A', 12), ('Z', 113), ('m', 1000), ('a', 1012), ('z', 1113),
    ('0', 2000), ('9', 2009), ('\n', 3000), (' ', 3001), ('!', 3002),
    ('/', 3016), (':', 3100), ('~', 3116),
])
def test_known_codes(ch, code):
    assert mi.encode_char(ch) == code
    assert mi.decode_char(code) == ch


def test_exactly_96_valid_codes_one_per_character():
    assert len(mi.VALID_CODES) == len(set(mi.VALID_CODES)) == mi.K == 96
    assert sorted(mi.decode_char(c) for c in mi.VALID_CODES) == sorted(DOMAIN)
    assert list(mi.VALID_CODES) == sorted(mi.VALID_CODES)


def test_every_other_four_digit_number_is_rejected():
    for code in range(10000):
        if code not in mi.CODE_INDEX:
            with pytest.raises(ValueError):
                mi.decode_char(code)


def test_digits_have_no_sign():
    assert [mi.encode_char(d) for d in string.digits] == list(range(2000, 2010))


def test_anchor_takes_sign_zero_and_letter_steps_are_bounded():
    for t, alpha in ((0, string.ascii_uppercase), (1, string.ascii_lowercase)):
        for ch in alpha:
            code = mi.encode_char(ch)
            sign, step = code // 100 % 10, code % 100
            assert code // 1000 == t and step <= 13
            assert (sign == 0) == (ch <= alpha[12])             # A..M toward A, N..Z toward Z


def test_punctuation_halves_are_17_and_17():
    assert len(mi.PUNCT) == 34 and mi.PUNCT_HALF == 17
    assert mi.PUNCT[:2] == '\n ' and mi.PUNCT[2:17] == '!"#$%&\'()*+,-./'
    assert mi.PUNCT[17:] == ':;<=>?@[\\]^_`{|}~'


# ── the address ────────────────────────────────────────────────────────────
def test_every_pair_roundtrips():
    for a, b in product(DOMAIN, repeat=2):
        assert mi.decode_text(mi.encode_text(a + b), 2) == a + b


@pytest.mark.parametrize('text', [
    'HELLO2026', 'Hello, World -3!', '-3', '~!;:', 'a  b', 'line1\nline2\n', 'M', 'm',
])
def test_text_roundtrip_is_case_exact(text):
    assert mi.verify(text)
    assert mi.decode_text(mi.encode_text(text), len(text)) == text


def test_case_is_not_folded():
    assert mi.encode_text('hello') != mi.encode_text('HELLO')


def test_address_cost_is_log2_96_per_character():
    t = DOMAIN * 40
    bits = mi.encode_text(t).bit_length()
    assert abs(bits - len(t) * 6.585) < 8                       # leading digits move it by < log2(96) bits


def test_normalise_turns_tab_into_four_spaces():
    assert mi.normalise('a\tb') == 'a    b'
    assert mi.verify(mi.normalise('a\tb'))


@pytest.mark.parametrize('bad', ['\t', '\r', 'é', '\x00'])
def test_outside_the_domain_raises(bad):
    with pytest.raises(ValueError):
        mi.encode_char(bad)
    with pytest.raises(ValueError):
        mi.encode_text('a' + bad)


def test_de_bruijn_over_96_symbols():
    r = mi.verify_de_bruijn(2, k=mi.ALPHABET_SIZE)
    assert r['ok'] and r['sequence_length'] == 96 ** 2
    assert len(mi.de_bruijn_text(2)) == 96 ** 2


# ── the Kryptos workbench wrapper ──────────────────────────────────────────
def test_wrapper_roundtrip_keeps_case_spaces_and_linefeeds():
    text = 'The Two Trees 2026, -3!\nSecond line'
    enc = Midline.encrypt(text)
    assert enc.key == len(text)
    assert Midline.decrypt(enc.text, enc.key).text == text


def test_wrapper_tab_becomes_four_spaces_and_unsupported_is_dropped():
    enc = Midline.encrypt('a\tb\rcé')
    assert Midline.decrypt(enc.text, enc.key).text == 'a    bc'


def test_wrapper_empty_input():
    assert Midline.encrypt('é\r').text == ''
