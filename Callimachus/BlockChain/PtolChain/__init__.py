#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PtolChain — Canonical Ptolemy blockchain package.
Replaces JackCoin / JackCoin5001 / JackCoin5002 / JackCoin5003 (identical).

AuditChain: lightweight client used by LuthSpell and Aule for audit trail.
Does NOT require a running Flask node — writes directly to chaindata/.

Settings hook → Callimachus > Blockchain settings tab.
"""
import os
import json
import time
import hashlib

from .Config import CHAINDATA_DIR, DEFAULT_PORT, NUM_ZEROS


class AuditBlock:
    """Single audit record block."""
    __slots__ = ('index', 'timestamp', 'data', 'prev_hash', 'nonce', 'hash')

    def __init__(self, index, data, prev_hash, nonce=0):
        self.index     = index
        self.timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self.data      = data
        self.prev_hash = prev_hash
        self.nonce     = nonce
        self.hash      = self._compute()

    def _compute(self) -> str:
        raw = f"{self.index}{self.timestamp}{self.data}{self.prev_hash}{self.nonce}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__slots__}


class AuditChain:
    """
    Lightweight local audit chain.
    No Flask required. Writes JSON blocks to chaindata/<face_id>/.
    Used by:
        LuthSpell  — halt records
        Aule       — forge events
        Callimachus — HW acquisition records

    Usage:
        chain = AuditChain('luthspell')
        chain.add_block({'reason': 'boundary_crossed', 'coords': '...'})
    """

    GENESIS_HASH = '0' * 64

    def __init__(self, face_id: str = 'ptolemy'):
        self.face_id  = face_id
        self._dir     = os.path.join(CHAINDATA_DIR, face_id)
        os.makedirs(self._dir, exist_ok=True)
        self._chain   = self._load()

    # ── Public ────────────────────────────────────────────────────────────────

    def add_block(self, data: dict) -> AuditBlock:
        """Mine and append a block. Returns the new block."""
        prev_hash = self._chain[-1].hash if self._chain else self.GENESIS_HASH
        index     = len(self._chain)
        block     = self._mine(index, json.dumps(data), prev_hash)
        self._chain.append(block)
        self._save(block)
        return block

    def is_valid(self) -> bool:
        for i in range(1, len(self._chain)):
            b, prev = self._chain[i], self._chain[i-1]
            if b.prev_hash != prev.hash:
                return False
            if b.hash != b._compute():
                return False
        return True

    def __len__(self):
        return len(self._chain)

    def __iter__(self):
        return iter(self._chain)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _mine(self, index, data, prev_hash) -> AuditBlock:
        nonce = 0
        target = '0' * NUM_ZEROS
        while True:
            b = AuditBlock(index, data, prev_hash, nonce)
            if b.hash.startswith(target):
                return b
            nonce += 1

    def _save(self, block: AuditBlock):
        path = os.path.join(self._dir, f'{block.index:08d}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(block.to_dict(), f, indent=2)

    def _load(self):
        blocks = []
        files  = sorted(f for f in os.listdir(self._dir) if f.endswith('.json'))
        for fn in files:
            try:
                d = json.load(open(os.path.join(self._dir, fn)))
                b = AuditBlock(d['index'], d['data'], d['prev_hash'], d['nonce'])
                b.timestamp = d['timestamp']
                b.hash      = d['hash']
                blocks.append(b)
            except Exception:
                pass
        return blocks
