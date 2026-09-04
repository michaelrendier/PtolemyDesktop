#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
analysis.py — the codebreaking side of Pycrypt: "the methods to break each".

Everything here is a pure function on text.  The Pycrypt workbench (stats pane,
the Frequency / Freq-double / Vowel-Trowel toolbar buttons, the cipher dialogs'
"break" actions) calls in here; nothing here touches Qt.

Grounded in The Code Book's own narrative — each tool notes the CD-ROM /
teacher's-notes passage it mechanises:

  * frequency analysis .......... al-Kindi; CD-ROM Overview "Codebreaking"
  * repeated-letter / short-word / e→h hints ... `y9-fa-hints.doc`
  * word-pattern dictionary attack ............. al-Kindi, Code Book ch.1
  * Vowel Trowel (Sukhotin) ................... Code Book ch.1 frequency section
  * Kasiski + Index of Coincidence ............ Babbage/Kasiski, Code Book ch.2-3
  * Enigma key-space ......................... `Will/enigma lesson/enigma-tn.doc`

The old build's `uniquepatterns.py`, `Unscramble.py`, `collectstats()` and the
`randomdictionary()` / `uniqueletter()` / Vowel-Trowel stubs are finished here.
"""

import os
import re
from collections import Counter
from itertools import permutations, product
from math import gcd
from functools import reduce

from Kryptos.Ciphers.common import ALPHABET, A, clean, ENGLISH_FREQ, ENGLISH_FREQ_ORDER

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORDS_DIR = os.path.join(_HERE, 'TheCodeBook', 'data', 'words')

# ── English reference the CD-ROM bar charts / hint sheet use ────────────────
COMMON_DOUBLES   = ['SS', 'EE', 'TT', 'FF', 'LL', 'MM', 'OO']          # y9-fa-hints
COMMON_DIGRAPHS  = ['TH', 'HE', 'IN', 'ER', 'AN', 'RE', 'ND', 'ON', 'EN', 'AT',
                    'OU', 'ED', 'HA', 'TO', 'OR', 'IT', 'IS', 'HI', 'ES', 'NG']
COMMON_TRIGRAPHS = ['THE', 'AND', 'ING', 'HER', 'ERE', 'ENT', 'THA', 'NTH',
                    'WAS', 'ETH', 'FOR', 'DTH']
ONE_LETTER_WORDS   = ['A', 'I']
TWO_LETTER_WORDS   = ['OF', 'TO', 'IN', 'IT', 'IS', 'BE', 'AS', 'AT', 'SO',
                      'WE', 'HE', 'BY', 'OR', 'ON', 'DO']
THREE_LETTER_WORDS = ['THE', 'AND']
VOWELS = set('AEIOU')


# ══════════════════════════════════════════════════════════════════════════
#  Frequency analysis  (collectstats, ported and split from the old UI)
# ══════════════════════════════════════════════════════════════════════════

def letter_counts(text: str) -> dict:
    return dict(Counter(clean(text)))


def letter_frequencies(text: str) -> dict:
    """Percent frequency per letter, 0.0 for absent letters."""
    s = clean(text)
    n = len(s) or 1
    c = Counter(s)
    return {ch: 100.0 * c.get(ch, 0) / n for ch in ALPHABET}


def ngram_counts(text: str, n: int) -> Counter:
    s = clean(text)
    return Counter(s[i:i + n] for i in range(len(s) - n + 1))


def digraph_frequencies(text: str, top: int = 20):
    return ngram_counts(text, 2).most_common(top)


def repeated_pairs(text: str):
    """Every doubled letter (position, pair) — the old collectstats
    `re.finditer(r'(.)\\1')`, kept for the workbench's red highlight."""
    return [(m.start(), m.group(0)) for m in re.finditer(r'(.)\1', clean(text))]


def repeated_triples(text: str):
    return [(m.start(), m.group(0)) for m in re.finditer(r'(.)\1\1', clean(text))]


def chi_squared_english(text: str) -> float:
    """Fit to English letter frequencies; lower = more English-like."""
    s = clean(text)
    n = len(s)
    if not n:
        return float('inf')
    c = Counter(s)
    return sum((c.get(ch, 0) - ENGLISH_FREQ[ch] / 100 * n) ** 2
               / (ENGLISH_FREQ[ch] / 100 * n) for ch in ALPHABET)


# ══════════════════════════════════════════════════════════════════════════
#  Index of Coincidence + Kasiski  (Vigenere period recovery)
# ══════════════════════════════════════════════════════════════════════════

def index_of_coincidence(text: str) -> float:
    """Probability two random letters of `text` match.  ~0.067 for English,
    ~0.038 for random / a long-key polyalphabetic cipher.  Friedman's measure
    (the CD-ROM's 'other useful statistics')."""
    s = clean(text)
    n = len(s)
    if n < 2:
        return 0.0
    c = Counter(s)
    return sum(v * (v - 1) for v in c.values()) / (n * (n - 1))


def ioc_by_period(text: str, max_period: int = 20):
    """Average IoC of the `p` columns for each candidate period p.  The period
    whose average IoC jumps toward the English value (~0.067) is the Vigenere
    key length.  Returns [(p, avg_ioc), ...]."""
    s = clean(text)
    out = []
    for p in range(1, max_period + 1):
        cols = [s[i::p] for i in range(p)]
        iocs = [index_of_coincidence(col) for col in cols if len(col) > 1]
        out.append((p, sum(iocs) / len(iocs) if iocs else 0.0))
    return out


def kasiski(text: str, min_len: int = 3, max_len: int = 5):
    """Kasiski examination: find repeated substrings, factor the gaps between
    their occurrences; the most common factors are candidate key lengths.
    (Babbage's and Kasiski's break of Vigenere — Code Book ch.2-3.)

    Returns (candidates, detail) where candidates is [(period, votes), ...]
    best first, and detail is {substring: [gap, gap, ...]}.
    """
    s = clean(text)
    detail = {}
    for L in range(min_len, max_len + 1):
        seen = {}
        for i in range(len(s) - L + 1):
            seg = s[i:i + L]
            if seg in seen:
                detail.setdefault(seg, []).append(i - seen[seg])
            seen[seg] = i
    factor_votes = Counter()
    for gaps in detail.values():
        for g in gaps:
            for f in range(2, min(g, 30) + 1):
                if g % f == 0:
                    factor_votes[f] += 1
    return factor_votes.most_common(), detail


def vigenere_key_from_period(ciphertext: str, period: int) -> str:
    """Given a key length, solve each column as a Caesar shift by chi-squared,
    returning the recovered keyword."""
    s = clean(ciphertext)
    key = []
    for i in range(period):
        col = s[i::period]
        best_k, best_score = 0, float('inf')
        for k in range(A):
            dec = ''.join(ALPHABET[(ALPHABET.index(ch) - k) % A] for ch in col)
            sc = chi_squared_english(dec)
            if sc < best_score:
                best_k, best_score = k, sc
        key.append(ALPHABET[best_k])
    return ''.join(key)


def break_vigenere(ciphertext: str, max_period: int = 20):
    """End to end: pick a period (Kasiski vote, confirmed by IoC), recover the
    keyword, decrypt.  Returns dict(period, key, plaintext, ioc)."""
    votes, _ = kasiski(ciphertext)
    ioc_scores = dict(ioc_by_period(ciphertext, max_period))
    period = None
    for p, _v in votes:
        if 1 < p <= max_period:
            period = p
            break
    if period is None:
        period = max(range(2, max_period + 1), key=lambda p: ioc_scores.get(p, 0))
    key = vigenere_key_from_period(ciphertext, period)
    from Kryptos.Ciphers.Vigenere import decrypt as vig_decrypt
    return {
        'period': period,
        'key': key,
        'plaintext': vig_decrypt(ciphertext, key),
        'ioc': ioc_scores.get(period, 0.0),
    }


# ══════════════════════════════════════════════════════════════════════════
#  Word-pattern dictionary attack  (uniquepatterns.py, finished)
# ══════════════════════════════════════════════════════════════════════════

def pattern_signature(word: str) -> str:
    """A word's repeat pattern as a digit string: first-seen letters get the
    next number, repeats reuse it.  'HELLO' -> '12334', 'PEOPLE' -> '123142'.
    Monoalphabetic substitution preserves this signature, so it keys a
    dictionary lookup (al-Kindi)."""
    seen, out, nxt = {}, [], 1
    for ch in clean(word):
        if ch not in seen:
            seen[ch] = str(nxt)
            nxt += 1
        out.append(seen[ch])
    return ''.join(out)


def _load_wordlist():
    words = set()
    for name in ('two_letter_word_list.txt', 'three_letter_word_list.txt',
                 'double_letter_word_list.txt'):
        p = os.path.join(_WORDS_DIR, name)
        if os.path.isfile(p):
            words |= {w.strip().upper() for w in open(p) if w.strip().isalpha()}
    return words


def pattern_candidates(cipher_word: str, wordlist=None):
    """Plaintext words whose pattern signature matches `cipher_word`'s."""
    wl = wordlist if wordlist is not None else _load_wordlist()
    sig = pattern_signature(cipher_word)
    return sorted(w for w in wl if pattern_signature(w) == sig)


def dictionary_attack(ciphertext: str, wordlist=None):
    """For each distinct cipher word, list plaintext words of the same pattern.
    Returns {cipher_word: [candidate, ...]} — the codebreaker's crib list."""
    wl = wordlist if wordlist is not None else _load_wordlist()
    result = {}
    for w in {clean(tok) for tok in ciphertext.upper().split() if clean(tok)}:
        cands = pattern_candidates(w, wl)
        if cands:
            result[w] = cands
    return result


# ══════════════════════════════════════════════════════════════════════════
#  Vowel Trowel  (Sukhotin's algorithm — the stub, finished)
# ══════════════════════════════════════════════════════════════════════════

def vowel_trowel(text: str):
    """Sukhotin's algorithm: vowels tend to sit next to consonants, not other
    vowels.  Iteratively pick the letter with the highest neighbour-sum as a
    vowel, then subtract its adjacencies so its neighbours are less likely to
    be picked next.  Language-agnostic — no frequency table needed.

    Returns (vowels, consonants) as letter lists, vowels most-confident first.
    """
    s = clean(text)
    idx = {ch: i for i, ch in enumerate(sorted(set(s)))}
    if not idx:
        return [], []
    letters = sorted(idx)
    m = [[0] * len(letters) for _ in letters]
    for a, b in zip(s, s[1:]):
        if a != b:
            m[idx[a]][idx[b]] += 1
            m[idx[b]][idx[a]] += 1
    row_sum = [sum(r) for r in m]
    remaining = set(range(len(letters)))
    vowels = []
    while True:
        cand = max((i for i in remaining), key=lambda i: row_sum[i], default=None)
        if cand is None or row_sum[cand] <= 0:
            break
        vowels.append(cand)
        remaining.discard(cand)
        for j in remaining:
            row_sum[j] -= 2 * m[cand][j]
    v = [letters[i] for i in vowels]
    c = [ch for ch in letters if ch not in set(v)]
    return v, c


# ══════════════════════════════════════════════════════════════════════════
#  Frequency-analysis hints  (y9-fa-hints.doc, mechanised)
# ══════════════════════════════════════════════════════════════════════════

def hints(text: str) -> list[str]:
    """Human-readable guesses straight from the CD-ROM hint sheet."""
    s = clean(text)
    out = []
    if not s:
        return out
    freq = Counter(s)
    top = [c for c, _ in freq.most_common(6)]
    if top:
        out.append(f"Most frequent cipher letter is {top[0]!r} — in English "
                   f"that is almost always E (al-Kindi). Next: {' '.join(top[1:4])}.")

    doubles = Counter(p for _, p in repeated_pairs(s))
    if doubles:
        common = ', '.join(f'{p}×{n}' for p, n in doubles.most_common(4))
        out.append(f"Doubled letters: {common}. English doubles rank "
                   f"SS EE TT FF LL MM OO — the top one is likely one of these.")

    words = [clean(w) for w in text.upper().split() if clean(w)]
    if any(len(w) <= 3 for w in words):
        ones = sorted({w for w in words if len(w) == 1})
        twos = sorted({w for w in words if len(w) == 2})
        threes = sorted({w for w in words if len(w) == 3})
        if ones:
            out.append(f"One-letter words {ones} — must be A or I.")
        if twos:
            out.append(f"Two-letter words {twos} — try {', '.join(TWO_LETTER_WORDS[:8])}…")
        if threes:
            out.append(f"Three-letter words {threes} — most often THE or AND.")

    # e -> h asymmetry: h precedes e (the/then/they) but rarely follows it
    e_guess = top[0] if top else None
    if e_guess:
        before = Counter(a for a, b in zip(s, s[1:]) if b == e_guess)
        after = Counter(b for a, b in zip(s, s[1:]) if a == e_guess)
        asym = {c: before[c] - after.get(c, 0) for c in before}
        if asym:
            h_guess = max(asym, key=asym.get)
            if asym[h_guess] > 0:
                out.append(f"{h_guess!r} comes before {e_guess!r} far more than "
                           f"after it — that asymmetry marks H (as in THE, THEN).")
    return out


# ══════════════════════════════════════════════════════════════════════════
#  Anagram / transposition unscramble  (Unscramble.py, de-CLI'd)
# ══════════════════════════════════════════════════════════════════════════

def unscramble(letters: str, length: int = None, repeat: bool = False,
               pattern: str = None, wordlist=None):
    """Real words makeable from `letters`.  `pattern` uses '*' for unknowns
    (e.g. 'C*T').  Ported from the old Unscramble dialog."""
    letters = clean(letters)
    length = length or len(letters)
    wl = wordlist if wordlist is not None else _load_wordlist()
    src = product(letters, repeat=length) if repeat else permutations(letters, length)
    found = sorted({''.join(p) for p in src if ''.join(p) in wl})
    if pattern:
        pat = clean(pattern.replace('*', '.'))
        rx = re.compile('^' + pat.replace('.', '[A-Z]') + '$')
        found = [w for w in found if rx.match(w)]
    return found


# ══════════════════════════════════════════════════════════════════════════
#  Strength of Enigma  (enigma-tn.doc — key-space counting, not a break)
# ══════════════════════════════════════════════════════════════════════════

def _fact(n):
    return reduce(lambda a, b: a * b, range(1, n + 1), 1)


def plugboard_settings(n_leads: int) -> int:
    """Ways to place n plug leads: 26·25·…·(26−(2n−1)) / (n! · 2ⁿ)
    (enigma-tn.doc Q3 / 'A Stage Further')."""
    num = 1
    for k in range(2 * n_leads):
        num *= (26 - k)
    return num // (_fact(n_leads) * (2 ** n_leads))


def enigma_keyspace(rotor_choose=3, rotor_pool=5, n_leads=10):
    """The pieces the Code Book asks pupils to multiply out."""
    order = 1
    for k in range(rotor_choose):
        order *= (rotor_pool - k)                       # 5·4·3 = 60
    positions = 26 ** rotor_choose                      # 26³ = 17576
    plug = plugboard_settings(n_leads)
    optimum_leads = max(range(1, 14), key=plugboard_settings)   # → 11
    return {
        'rotor_order': order,
        'rotor_positions': positions,
        'plugboard': plug,
        'total_without_plug': order * positions,
        'total': order * positions * plug,
        'optimum_leads': optimum_leads,
        'note': ("Reflector guarantees no letter ever encrypts to itself — the "
                 "crib weakness Bletchley exploited (enigma-tn.doc)."),
    }


if __name__ == '__main__':
    assert pattern_signature('HELLO') == '12334'
    assert pattern_signature('PEOPLE') == '123142'
    assert abs(index_of_coincidence('THE QUICK BROWN FOX' * 20) - 0.067) < 0.02

    from Kryptos.Ciphers.Vigenere import encrypt as vig_enc
    plain = ("WE HOLD THESE TRUTHS TO BE SELF EVIDENT THAT ALL MEN ARE CREATED "
             "EQUAL THAT THEY ARE ENDOWED BY THEIR CREATOR WITH CERTAIN "
             "UNALIENABLE RIGHTS THAT AMONG THESE ARE LIFE LIBERTY AND THE "
             "PURSUIT OF HAPPINESS") * 2
    ct = vig_enc(plain, 'LIBERTY')
    res = break_vigenere(ct)
    assert res['key'] == 'LIBERTY', res
    assert res['plaintext'] == clean(plain), res['plaintext'][:60]
    print(f"Vigenere break: period {res['period']}, key {res['key']!r}, "
          f"IoC {res['ioc']:.3f}  — HOLDS")

    v, c = vowel_trowel("WE HOLD THESE TRUTHS TO BE SELF EVIDENT" * 8)
    assert 'E' in v[:3], (v, c)
    print(f"Vowel Trowel: vowels ~ {v[:6]}  — HOLDS")

    ks = enigma_keyspace()
    assert ks['rotor_order'] == 60 and ks['rotor_positions'] == 17576
    assert ks['optimum_leads'] == 11
    assert plugboard_settings(10) == 150738274937250
    print(f"Enigma key-space: {ks['total']:.3e} total, optimum {ks['optimum_leads']} "
          f"leads  — HOLDS")
    print('analysis self-test: HOLDS')
