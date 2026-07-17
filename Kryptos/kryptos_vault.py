#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kryptos_vault.py — Kryptos Encrypted Secrets Store
====================================================
Kryptos Face

AES-256-GCM encrypted key-value store backed by a JSON shard file.
Each secret is encrypted with a key derived by KCF-1 from the secret's label.

Encryption:     AES-256-GCM   (AEAD — authenticated)
Key derivation: KCF.derive_aes(label)   → 32-byte AES key
Nonce:          12 bytes os.urandom per write
Storage:        JSON — {label_hex: {nonce_hex, ct_hex, tag_hex, ts}}

The label itself is the HyperWebster address (Horner bijection) of the
secret's name — same addressing used by Callimachus.  The KCF XOR trapdoor
means the key for a label never changes once the charset is locked.

API:
    vault = KryptosVault(face_id='kryptos')
    vault.store('api_key', b'my-secret-value')
    secret = vault.retrieve('api_key')
    vault.delete('api_key')
    vault.list_labels()

Author: Ptolemy / Kryptos Face
"""

from __future__ import annotations

import os
import json
import hashlib
import datetime
from pathlib import Path
from typing  import Optional, List

from Kryptos.kcf import KCF, KCFError, get_kcf

_HERE      = Path(__file__).resolve().parent
_VAULT_DIR = _HERE / 'vault'

_AES_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _AES_AVAILABLE = True
except ImportError:
    pass


class KryptosVaultError(Exception):
    pass


class KryptosVault:
    """
    AES-256-GCM encrypted secrets store, one file per vault.

    Each entry is keyed by the KCF HyperWebster address of the label string.
    The stored JSON never contains the plaintext label — only its SHA-256 hex.
    """

    def __init__(self, face_id: str = 'kryptos', vault_name: str = 'default'):
        if not _AES_AVAILABLE:
            raise KryptosVaultError(
                'cryptography package required: pip install cryptography')
        self._kcf       = get_kcf(face_id)
        self._path      = _VAULT_DIR / f'{vault_name}.json'
        _VAULT_DIR.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self):
        with open(self._path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)

    # ── Key addressing ────────────────────────────────────────────────────────

    def _entry_key(self, label: str) -> str:
        """Stable entry key: SHA-256 of the label (never the label itself)."""
        return hashlib.sha256(label.encode()).hexdigest()

    # ── Public API ────────────────────────────────────────────────────────────

    def store(self, label: str, secret: bytes) -> None:
        """Encrypt and store a secret under label. Overwrites if exists."""
        aes_key = self._kcf.derive_aes(label)           # 32-byte key
        nonce   = os.urandom(12)                         # 96-bit GCM nonce
        ct_tag  = AESGCM(aes_key).encrypt(nonce, secret, label.encode())
        ct      = ct_tag[:-16]
        tag     = ct_tag[-16:]

        entry_key = self._entry_key(label)
        self._data[entry_key] = {
            'nonce': nonce.hex(),
            'ct':    ct.hex(),
            'tag':   tag.hex(),
            'ts':    datetime.datetime.utcnow().isoformat() + 'Z',
        }
        self._save()

    def retrieve(self, label: str) -> bytes:
        """
        Decrypt and return secret for label.
        Raises KryptosVaultError if label not found or MAC fails.
        """
        entry_key = self._entry_key(label)
        entry = self._data.get(entry_key)
        if entry is None:
            raise KryptosVaultError(f'Label not found: {label!r}')

        aes_key  = self._kcf.derive_aes(label)
        nonce    = bytes.fromhex(entry['nonce'])
        ct       = bytes.fromhex(entry['ct'])
        tag      = bytes.fromhex(entry['tag'])
        ct_tag   = ct + tag

        try:
            return AESGCM(aes_key).decrypt(nonce, ct_tag, label.encode())
        except Exception:
            raise KryptosVaultError(f'Decryption failed for {label!r} — MAC error or wrong key')

    def exists(self, label: str) -> bool:
        return self._entry_key(label) in self._data

    def delete(self, label: str) -> bool:
        """Remove a secret. Returns True if it existed."""
        key = self._entry_key(label)
        if key in self._data:
            del self._data[key]
            self._save()
            return True
        return False

    def list_labels(self) -> List[str]:
        """Return entry key list (SHA-256 hashes — labels are not stored)."""
        return list(self._data.keys())

    def count(self) -> int:
        return len(self._data)

    def vault_path(self) -> Path:
        return self._path

    def __repr__(self):
        return (f'KryptosVault(face={self._kcf.face_id!r}, '
                f'path={self._path.name!r}, entries={self.count()})')


# ── Module-level default vault ────────────────────────────────────────────────

_default_vault: Optional[KryptosVault] = None

def get_vault(face_id: str = 'kryptos') -> KryptosVault:
    """Return (or create) the default vault instance."""
    global _default_vault
    if _default_vault is None:
        _default_vault = KryptosVault(face_id=face_id)
    return _default_vault
