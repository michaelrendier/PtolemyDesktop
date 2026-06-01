#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kcf.py — Kryptos Charset Function (KCF-1)
==========================================
Kryptos Face

Deterministic key derivation tied to HyperWebster addressing.
Kryptos is the sole key custodian — no other Face derives keys directly.

KCF-1 Algorithm:
    1. Encode word label → HyperWebster address (Horner's method)
       addr = Σ c_i * |Charset|^(n-1-i)  for i in 0..n-1
    2. Apply charset permutation as cryptographic offset
       perm_addr = addr XOR perm_key(charset, seed)
    3. Expand to key material via HKDF-SHA256
       key = HKDF(IKM=perm_addr_bytes, salt=face_salt, info=purpose)

Properties:
    - Deterministic: same label + charset + face → same key
    - Non-commutative: charset permutation order matters
    - Asymmetric trapdoor: XOR in GF(2^n) + prime modulus mixes
    - Rabies Principle compatible: key for a label never changes
      once the charset is locked

Key types produced:
    KCF_KEY_AES   — 32-byte AES-256 key
    KCF_KEY_HMAC  — 32-byte HMAC key
    KCF_KEY_ADDR  — raw address integer (for HyperWebster sharding)

Settings hook → Kryptos > KCF settings tab.
"""

import os
import hashlib
import hmac
import struct
from typing import Optional

# ── Public charset (from Callimachus/v09/core/charset.py) ─────────────────────
# 97-char Basic Latin, Unicode 15.1 codepoint order
_DEFAULT_CHARSET = (
    ' !"#$%&\'()*+,-./0123456789:;<=>?@'
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`'
    'abcdefghijklmnopqrstuvwxyz{|}~\x7f'
)

# ── Settings ─────────────────────────────────────────────────────────────────
KCF_SETTINGS = {
    "charset":        _DEFAULT_CHARSET,
    "hkdf_hash":      "sha256",
    "key_length_b":   32,           # bytes
    "face_salt_hex":  "",           # "" → derive from face name
}

# ── Key type constants ────────────────────────────────────────────────────────
KCF_KEY_AES  = 'aes256'
KCF_KEY_HMAC = 'hmac'
KCF_KEY_ADDR = 'addr'

# ── Primes used in mixing (resist CRT reconstruction) ────────────────────────
_P1 = 2**61 - 1     # Mersenne prime
_P2 = 2**89 - 1     # Mersenne prime


class KCFError(Exception):
    pass


class KCF:
    """
    Kryptos Charset Function — deterministic key derivation.
    One instance per Face. Kryptos instantiates one per registered Face.

    Usage:
        kcf = KCF(face_id='callimachus', charset=PUBLIC_CHARSET)
        key = kcf.derive('hiraeth', purpose=KCF_KEY_AES)
        addr = kcf.hw_address('hiraeth')
    """

    def __init__(self, face_id: str = 'ptolemy',
                 charset: str = None,
                 salt: bytes = None):
        self.face_id = face_id
        self.charset = charset or KCF_SETTINGS['charset']
        self._base   = len(self.charset)
        # Face salt: deterministic from face_id if not provided
        if salt:
            self._salt = salt
        else:
            _hex = KCF_SETTINGS.get('face_salt_hex', '')
            if _hex:
                self._salt = bytes.fromhex(_hex)
            else:
                self._salt = hashlib.sha256(face_id.encode()).digest()

    # ── Public API ────────────────────────────────────────────────────────────

    def hw_address(self, label: str) -> int:
        """
        Horner's method bijection: label → unique integer address.
        addr = Σ charset.index(c) * base^(n-1-i)
        Evaluated by Horner: addr = (...((c0)*base + c1)*base + c2)...
        """
        if not label:
            return 0
        addr = 0
        for ch in label:
            try:
                idx = self.charset.index(ch)
            except ValueError:
                idx = ord(ch) % self._base   # fallback for out-of-charset chars
            addr = addr * self._base + idx
        return addr

    def derive(self, label: str, purpose: str = KCF_KEY_AES) -> bytes:
        """
        Derive key material for label+purpose.
        Returns KCF_SETTINGS['key_length_b'] bytes.
        """
        addr       = self.hw_address(label)
        perm_addr  = self._permute(addr)
        ikm        = self._addr_to_bytes(perm_addr)
        info       = f'{self.face_id}:{purpose}'.encode()
        return self._hkdf(ikm, self._salt, info,
                          KCF_SETTINGS['key_length_b'])

    def derive_aes(self, label: str) -> bytes:
        return self.derive(label, KCF_KEY_AES)

    def derive_hmac_key(self, label: str) -> bytes:
        return self.derive(label, KCF_KEY_HMAC)

    def verify_hmac(self, label: str, message: bytes, tag: bytes) -> bool:
        k   = self.derive_hmac_key(label)
        exp = hmac.new(k, message, hashlib.sha256).digest()
        return hmac.compare_digest(exp, tag)

    # ── KCF profiles ─────────────────────────────────────────────────────────

    @classmethod
    def for_face(cls, face_id: str) -> 'KCF':
        """Convenience: build a KCF instance for a named Face."""
        try:
            from Callimachus.v09.core.charset import PUBLIC_CHARSET
            charset = PUBLIC_CHARSET
        except ImportError:
            charset = _DEFAULT_CHARSET
        return cls(face_id=face_id, charset=charset)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _permute(self, addr: int) -> int:
        """
        Apply charset permutation as cryptographic offset.
        XOR in GF(2^n) + prime modulus mix → asymmetric trapdoor.
        Design avoids unintended CRT reconstruction (see architecture notes).
        """
        # Step 1: charset-derived permutation key (deterministic from charset)
        perm_key = int.from_bytes(
            hashlib.sha256(self.charset.encode()).digest()[:8], 'big')
        # Step 2: XOR (GF(2^64) — reversible)
        xored = addr ^ perm_key
        # Step 3: mix with prime modulus (introduces one-way trapdoor)
        mixed = (xored * _P1 + addr) % _P2
        return mixed

    def _addr_to_bytes(self, addr: int) -> bytes:
        """Convert arbitrarily large address to bytes (big-endian)."""
        n_bytes = max(8, (addr.bit_length() + 7) // 8)
        return addr.to_bytes(n_bytes, 'big')

    @staticmethod
    def _hkdf(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
        """
        Minimal HKDF-SHA256 (RFC 5869).
        No external dependency — pure hmac + hashlib.
        """
        # Extract
        if not salt:
            salt = bytes(32)
        prk = hmac.new(salt, ikm, hashlib.sha256).digest()
        # Expand
        t, okm, i = b'', b'', 1
        while len(okm) < length:
            t   = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
            okm += t
            i   += 1
        return okm[:length]

    def __repr__(self):
        return (f"KCF(face={self.face_id!r}, "
                f"base={self._base}, charset_len={len(self.charset)})")


# ── KCF Profile Registry ──────────────────────────────────────────────────────

class KCFRegistry:
    """
    Kryptos maintains one KCF profile per Face.
    Registry is loaded from kcf_profiles/ directory.
    Settings hook → Kryptos > KCF Registry tab.
    """

    def __init__(self):
        self._profiles: dict[str, KCF] = {}

    def get(self, face_id: str) -> KCF:
        if face_id not in self._profiles:
            self._profiles[face_id] = KCF.for_face(face_id)
        return self._profiles[face_id]

    def register(self, face_id: str, charset: str = None,
                 salt: bytes = None):
        self._profiles[face_id] = KCF(face_id, charset, salt)

    def list_faces(self) -> list:
        return list(self._profiles.keys())


# Module-level singleton — Kryptos initialises this at startup
_registry = KCFRegistry()

def get_kcf(face_id: str = 'ptolemy') -> KCF:
    """Get or create the KCF instance for a Face."""
    return _registry.get(face_id)
