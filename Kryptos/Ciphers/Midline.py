#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
Midline.py — the 'M'-anchored (Modifier, Step) cipher, as a Kryptos/Pycrypt
tool.

Every other cipher in this package works letters-only, 26-symbol, historical
by-hand mechanics (`common.py`). This one covers 36 symbols (A-Z case-folded
plus 0-9) and is not a historical cipher at all -- it is Cody's own pre-
HyperWebster address scheme (predates `add_scale_sign`, reconstructed
2026-09-26), included here because it IS a cipher in the plain sense: a
reversible transform of text into another representation (a single integer),
keyed by a fixed anchor character ('M') rather than a shared secret.

Core mechanics live in `Archimedes/Maths/MidlineIndex.py` (shared, not
duplicated here) -- Archimedes owns the maths, Kryptos owns the workbench
framing (`CipherResult`, dialog-facing functions).
"""
import sys
from pathlib import Path

from .common import CipherResult

_THEPLACE = Path(__file__).resolve().parents[3]
if str(_THEPLACE) not in sys.path:
    sys.path.insert(0, str(_THEPLACE))
from PtolemyDesktop.Archimedes.Maths.MidlineIndex import (  # noqa: E402
    encode_text, decode_text, M_POS, K,
)


def encrypt(text: str) -> CipherResult:
    """Text (A-Z/0-9 only, case-folded) -> a single reconstructable integer
    address, returned as a decimal string plus the length needed to decode."""
    cleaned = ''.join(ch for ch in text if ch.isalnum())
    if not cleaned:
        return CipherResult('', note='no A-Z/0-9 characters found')
    address = encode_text(cleaned)
    return CipherResult(
        text=str(address),
        note=f"Midline address, base {K}, anchor 'M' (position {M_POS}); "
             f"length {len(cleaned)} required to decode",
        key=len(cleaned),
        extra={'length': len(cleaned), 'base': K, 'anchor': 'M'},
    )


def decrypt(address_str: str, length: int) -> CipherResult:
    """Integer address (as produced by encrypt) + original length -> text."""
    text = decode_text(int(address_str), length)
    return CipherResult(text=text, note=f'decoded {length} characters', key=length)


if __name__ == '__main__':
    enc = encrypt('The Two Trees 2026')
    dec = decrypt(enc.text, enc.key)
    assert dec.text == 'THETWOTREES2026', dec.text
    print('Midline cipher self-test: HOLDS')
    print(f"  'The Two Trees 2026' -> {enc.text}  ({enc.note})")
    print(f"  -> decoded: {dec.text}")
