#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Archimedes/Maths/MidlineIndex.py — the 'M'-anchored letter cipher, as an
ASS (Add:Scale:Sign) construction, collapsing text to a single reconstructable
Horner-style integer address.

HISTORY (2026-09-26, reconstructed from memory of Gemini conversations
predating this repo, no committed source found earlier than this file):
Cody's own description, verbatim: "M is 0..the letter cipher is the number
of steps away from this...either 12 on one side and 13 on the other. moving
towards a is 'negative' and moving towards z is 'positive'...and then the
step count...never greater than 13." Designed BEFORE the `add_scale_sign`
engine (`ValaQuenta/modules/add_scale_sign/`) existed, but is exactly one
ASS element applied to the constant 1 -- not an analogy, an exact fit,
confirmed below.

THE EXACT FIT: for a letter at alphabet position `pos` (0-indexed, A=0..Z=25),
with M_POS=12:

    pos = ASS(add=M_POS, scale=step, sign=direction)(1)
        = direction * step * 1 + M_POS

`step = |pos - M_POS|` is HARD-BOUNDED at 13 (14 possible values, 0..13) --
not just typically small, provably so, since M sits at position 12 of 26 and
the farther alphabet edge (Z, position 25) is exactly 13 away. That bound is
what makes the per-character cost cheap and fixed, not the digit-count
(a mistake corrected live this session -- see OVERHEAD ACCOUNTING below).

DOMAIN: 36 symbols -- A-Z (case-folded) and 0-9. Deliberately narrower than
HyperWebster's eventual 97-char keyboard set; this predates that generality.

PER-CHARACTER CODE (packed for the whole-text Horner address):
    code = type*28 + sign*14 + step        (K = 56 = 2*2*14)
    type: 0=letter, 1=number
    sign: 0=toward-A (negative), 1=toward-M-or-Z (positive); fixed 0 for numbers
    step: 0..13 for letters (|pos-M_POS|); for numbers, the digit value itself (0..9)

WHOLE-TEXT ADDRESS (the Horner collapse):
    address = sum( code_i * K^(n-1-i) for i, code_i in enumerate(codes) )
    -- exactly HyperWebster's own Horner shape (base-97 -> here, base-56),
    reconstructable given `address` and the text length `n`.

OVERHEAD ACCOUNTING (corrected live, 2026-09-26 -- the record, not smoothed
over): first pass wrongly treated the step slot as needing the full base-100
range (2 naive decimal digits, ~6.64 bits) and concluded this scheme was
LESS efficient than base-97 Horner. Wrong -- step is hard-bounded at 14
values (0..13), needing only ceil(log2(14))=4 bits. Properly counted:
    letter worst case: type(1) + sign(1) + step(4) = 6 bits/char
    base-97 Horner:    log2(97) = 6.600 bits/char
    true minimum for this 36-symbol domain: log2(36) = 5.170 bits/char
So this scheme is CHEAPER per character than base-97 Horner (6 vs 6.6 bits),
within 1.16x of its own domain's true minimum -- a genuine overhead
reduction, not a wash, PROVIDED the hard bound is respected in how the
step slot is packed (K=56 here, not K=200).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ── reuse the locked ASS engine, don't reinvent it ──────────────────────────
_THEPLACE = Path(__file__).resolve().parents[3]
if str(_THEPLACE) not in sys.path:
    sys.path.insert(0, str(_THEPLACE))
from ValaQuenta.modules.add_scale_sign.maths import ASS  # noqa: E402
from ValaQuenta.modules.hyperwebster.maths import US_KEYBOARD_CHARS  # noqa: E402

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
M_POS = ALPHABET.index("M")          # 12
STEP_BASE = 14                       # 0..13, the hard ceiling -- never above 13
K = 2 * 2 * STEP_BASE                # = 56, the per-character packing base


# ── one character <-> one ASS element ───────────────────────────────────────

def encode_char(ch: str) -> int:
    """One character -> its packed 0..55 code. type*28 + sign*14 + step."""
    if ch.isdigit():
        return 1 * 28 + 0 * STEP_BASE + int(ch)
    pos = ALPHABET.index(ch.upper())
    step = abs(pos - M_POS)
    sign = 0 if pos < M_POS else 1
    return 0 * 28 + sign * STEP_BASE + step


def decode_char(code: int) -> str:
    """Packed 0..55 code -> the original character (uppercase for letters)."""
    type_, rem = divmod(code, 28)
    sign, step = divmod(rem, STEP_BASE)
    if type_ == 1:
        return str(step)
    if step == 0:
        return "M"
    pos = M_POS - step if sign == 0 else M_POS + step
    return ALPHABET[pos]


def char_ass(ch: str) -> Tuple[str, ASS]:
    """The ASS element actually reconstructing this character's alphabet
    position, plus a label -- for display/proof, not used by encode/decode
    (which work on the packed integer code directly, per __main__ below)."""
    if ch.isdigit():
        return ("digit", ASS.ADD(float(int(ch))))
    pos = ALPHABET.index(ch.upper())
    step = abs(pos - M_POS)
    sign = 1 if pos >= M_POS else -1
    if step == 0:
        return ("M itself", ASS.ADD(float(M_POS)))
    return (f"ASS(add={M_POS}, scale={step}, sign={sign:+d})",
            ASS(add=float(M_POS), scale=float(step), sign=sign))


# ── whole-text Horner collapse ───────────────────────────────────────────────

def encode_text(text: str) -> int:
    """Text (letters + digits only; case-folded, other characters rejected)
    -> ONE reconstructable Horner-style integer address, base K=56."""
    address = 0
    for ch in text:
        if not (ch.isalpha() or ch.isdigit()):
            raise ValueError(f"MidlineIndex only covers A-Z/0-9; got {ch!r}")
        address = address * K + encode_char(ch)
    return address


def decode_text(address: int, length: int) -> str:
    """Address + original length -> the exact original text (case-folded)."""
    chars: List[str] = []
    remaining = address
    for _ in range(length):
        chars.append(decode_char(remaining % K))
        remaining //= K
    chars.reverse()
    return "".join(chars)


def verify(text: str) -> bool:
    """Round-trip check: encode then decode returns the case-folded original."""
    addr = encode_text(text)
    return decode_text(addr, len(text)) == text.upper()


# ── de Bruijn sequence over the TRUE 36-symbol Midline alphabet ─────────────
# permutation size limiting: every possible length-n window appears exactly
# ONCE, cyclically, in a sequence of length A^n (not n*A^n, the naive
# flat-enumeration cost). FKM (Fredricksen-Kessler-Maiorana) construction,
# O(A^n) -- linear in the output, not a search.
#
# NOT run over K=56 -- K is the packing base (2*2*14), not the alphabet
# size. 20 of those 56 codes are structurally unused (digit codes with
# step>=9, since digits only use 0..9; the M/M redundancy at step=0) and
# decode_char is only well-defined on the 36 codes encode_char actually
# produces. Found live: decode_char(step=10..13, type=1) returns "10".."13"
# -- TWO characters, silently breaking the one-code-one-character
# invariant. The de Bruijn alphabet must be the 36 VALID codes, not the
# raw 0..K-1 packing range.

VALID_CODES: Tuple[int, ...] = tuple(encode_char(ch) for ch in ALPHABET + "0123456789")
ALPHABET_SIZE = len(VALID_CODES)   # 36, exactly -- the true de Bruijn k


def de_bruijn_codes(n: int, k: int = K) -> List[int]:
    """FKM de Bruijn sequence B(k, n) over symbols 0..k-1, as a flat list of
    length k**n. Every length-n window, read cyclically, appears exactly once."""
    a = [0] * (k * n)
    sequence: List[int] = []

    def db(t: int, p: int) -> None:
        if t > n:
            if n % p == 0:
                sequence.extend(a[1:p + 1])
        else:
            a[t] = a[t - p]
            db(t + 1, p)
            for j in range(a[t - p] + 1, k):
                a[t] = j
                db(t + 1, t)

    db(1, 1)
    return sequence


def de_bruijn_text(n: int) -> str:
    """The de Bruijn sequence over the TRUE 36-symbol alphabet, decoded to
    one literal string over A-Z/0-9. Every length-n substring of A-Z/0-9,
    read cyclically, appears exactly once."""
    abstract = de_bruijn_codes(n, k=ALPHABET_SIZE)   # symbols 0..35
    return "".join(decode_char(VALID_CODES[i]) for i in abstract)


def verify_de_bruijn(n: int, k: int = K) -> dict:
    """Checks the EXACT property, not just coverage: every length-n window
    (cyclic) appears ONCE -- no duplicates, no omissions. n restricted small
    here (k**n grows fast; k=56 makes n=3 already ~175616 windows)."""
    seq = de_bruijn_codes(n, k)
    length = len(seq)
    assert length == k ** n, (length, k ** n)
    seen: Dict[Tuple[int, ...], int] = {}
    for i in range(length):
        window = tuple(seq[(i + j) % length] for j in range(n))
        seen[window] = seen.get(window, 0) + 1
    all_present = len(seen) == k ** n
    all_exactly_once = all(count == 1 for count in seen.values())
    return {
        "k": k, "n": n, "sequence_length": length,
        "expected_length": k ** n,
        "distinct_windows_seen": len(seen),
        "expected_distinct_windows": k ** n,
        "all_windows_present": all_present,
        "all_windows_exactly_once": all_exactly_once,
        "ok": all_present and all_exactly_once,
    }


# ── the full 97-key keyboard, reduced to one thing: the pointer ────────────
# 2026-09-26 (Cody): "97 possibilities only. 97 list components. we don't
# have to construct it, just create the pointer (list.index())."
#
# Everything above (type/sign/step, the pathway deltas) was always just
# arithmetic ON TOP OF one underlying number -- pointer = M_POS + sign*step.
# Collapsing to the pointer directly loses nothing and is simpler. No new
# ordering is constructed here -- US_KEYBOARD_CHARS (97 symbols, already the
# canonical HyperWebster charset) is reused exactly as it already exists.
#
# MONAD.BIN NOTE (Cody, 2026-09-26): eventual destination is monad.bin, as
# an ALTERNATE spelling-accumulation channel alongside the existing P1
# prime-hash spelling address -- NOT a replacement for it. Explicitly
# EXPERIMENTAL: "it's going to poison other things" -- do not merge this
# into the Monad's live/production state without isolating it (a separate
# field, a flagged experimental channel, or a throwaway .bin copy). Nothing
# wired into monad.bin yet as of this note -- see
# project_midline_pathway_monad_bin.md (Claude memory).

def pointer(ch: str) -> int:
    """The one number a character reduces to: its index in the chosen
    97-symbol order. Currently US_KEYBOARD_CHARS (HyperWebster's own list) --
    swapping to a different physical/adjacency order later only ever means
    changing what list this indexes into, nothing downstream."""
    return US_KEYBOARD_CHARS.index(ch)


def char_from_pointer(p: int) -> str:
    """Pointer -> character. Inverse of pointer()."""
    return US_KEYBOARD_CHARS[p]


def pathway(word: str) -> List[int]:
    """The word's own pathway: first character's pointer (absolute, the
    word-initial anchor), then each subsequent character's DELTA from the
    previous character's pointer -- pointer(next) - pointer(prev). This is
    the T>H>I>S construction, expressed directly on pointers with no
    separate sign/step storage."""
    if not word:
        return []
    steps = [pointer(word[0])]
    for i in range(1, len(word)):
        steps.append(pointer(word[i]) - pointer(word[i - 1]))
    return steps


def pathway_text(text: str) -> List[List[int]]:
    """Split on whitespace (the reset points) and return one pathway per
    word -- 'T > H > I > S > whitespace = reset midline', applied to
    arbitrary text over the full 97-symbol keyboard set."""
    return [pathway(word) for word in text.split()]


def reconstruct_from_pathway(steps: List[int]) -> str:
    """Inverse of pathway(): first value is an absolute pointer, every
    following value is a delta -- walk them back into pointers, then
    characters."""
    if not steps:
        return ""
    p = steps[0]
    chars = [char_from_pointer(p)]
    for d in steps[1:]:
        p += d
        chars.append(char_from_pointer(p))
    return "".join(chars)


# ── overhead accounting, computed not asserted ──────────────────────────────

def overhead_report() -> dict:
    import math
    letter_bits = 1 + 1 + math.ceil(math.log2(STEP_BASE))
    horner97_bits = math.log2(97)
    true_min_bits = math.log2(36)
    return {
        "midline_bits_per_char": letter_bits,
        "horner97_bits_per_char": horner97_bits,
        "true_minimum_bits_36symbols": true_min_bits,
        "midline_cheaper_than_horner97": letter_bits < horner97_bits,
        "midline_overhead_vs_true_min": letter_bits / true_min_bits,
    }


if __name__ == "__main__":
    # boundary values, exactly as specified
    # M itself: step=0, and the `pos >= M_POS` convention gives it sign=1 --
    # harmless, since decode_char ignores sign whenever step==0.
    assert encode_char("M") == 0 * 28 + 1 * STEP_BASE + 0
    assert decode_char(encode_char("M")) == "M"
    assert abs(ALPHABET.index("A") - M_POS) == 12
    assert abs(ALPHABET.index("Z") - M_POS) == 13

    # full alphabet + digit round trip
    for ch in ALPHABET + "0123456789":
        assert decode_char(encode_char(ch)) == ch, ch

    # whole-text Horner collapse round trip
    for sample in ("HELLO", "TELPERION2026", "M", "A", "Z", "OCAPTAIN"):
        assert verify(sample), sample

    # the exact ASS fit, demonstrated not just claimed:
    # A's alphabet position (0) = ASS(add=M_POS, scale=12, sign=-1)(1)
    label, ass = char_ass("A")
    pos_from_ass = ass(1.0)
    assert pos_from_ass == ALPHABET.index("A") == 0.0, pos_from_ass
    # Z's alphabet position (25) = ASS(add=M_POS, scale=13, sign=+1)(1)
    label_z, ass_z = char_ass("Z")
    assert ass_z(1.0) == ALPHABET.index("Z") == 25.0, ass_z(1.0)

    rep = overhead_report()
    print("MidlineIndex self-test: HOLDS")
    print(f"  A -> {label} -> position {pos_from_ass:.0f} (ALPHABET.index('A')={ALPHABET.index('A')})")
    print(f"  Z -> {label_z} -> position {ass_z(1.0):.0f} (ALPHABET.index('Z')={ALPHABET.index('Z')})")
    print(f"  overhead report: {rep}")

    # de Bruijn: every window EXACTLY once, over the TRUE 36-symbol alphabet
    # (not K=56 -- checked live, K includes 20 structurally-unused codes)
    assert ALPHABET_SIZE == 36, ALPHABET_SIZE
    for n in (1, 2, 3):
        result = verify_de_bruijn(n, k=ALPHABET_SIZE)
        assert result["ok"], result
        print(f"  de Bruijn B(k={ALPHABET_SIZE}, n={n}): length={result['sequence_length']} "
              f"({ALPHABET_SIZE}^{n}={result['expected_length']}), "
              f"all_present={result['all_windows_present']}, "
              f"all_exactly_once={result['all_windows_exactly_once']}")

    sample_text = de_bruijn_text(2)
    assert len(sample_text) == ALPHABET_SIZE ** 2, len(sample_text)
    # every character in the output must be a single valid Midline symbol --
    # the exact bug found live (decode_char returning "10".."13") would show
    # up here as len(sample_text) != ALPHABET_SIZE**2, since those would each
    # contribute 2 characters instead of 1.
    print(f"  de Bruijn B(k={ALPHABET_SIZE}, n=2) as Midline text (first 20 chars): {sample_text[:20]}...")
    print(f"  full length: {len(sample_text)} (= {ALPHABET_SIZE}^2 = {ALPHABET_SIZE**2}, exactly)")

    # the full 97-key reduction: pointer = list.index(), nothing else stored
    assert len(US_KEYBOARD_CHARS) == 97
    for ch in US_KEYBOARD_CHARS:
        assert char_from_pointer(pointer(ch)) == ch, ch

    steps = pathway("THIS")
    assert steps == [pointer("T"),
                      pointer("H") - pointer("T"),
                      pointer("I") - pointer("H"),
                      pointer("S") - pointer("I")], steps
    assert reconstruct_from_pathway(steps) == "THIS", steps

    multi = pathway_text("THIS WORKS")
    assert reconstruct_from_pathway(multi[0]) == "THIS"
    assert reconstruct_from_pathway(multi[1]) == "WORKS"
    # confirm the reset: WORKS's pathway does NOT depend on THIS's last letter
    assert multi[1][0] == pointer("W")   # absolute, not relative to 'S'

    print(f"  pointer('T')={pointer('T')}  pointer('t')={pointer('t')}  "
          f"pointer(' ')={pointer(' ')}  (97-symbol US_KEYBOARD_CHARS)")
    print(f"  pathway('THIS') = {steps}  -> reconstructs to {reconstruct_from_pathway(steps)!r}")
    print(f"  pathway_text('THIS WORKS') = {multi}  (word boundary resets to absolute pointer)")
