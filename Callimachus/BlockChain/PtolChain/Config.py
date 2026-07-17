#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
PtolChain Config — canonical JackCoin configuration
Port and peers driven by Ptolemy settings / environment.
Settings hook → Callimachus > Blockchain tab.
"""
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE          = os.path.dirname(os.path.abspath(__file__))
CHAINDATA_DIR  = os.path.join(_HERE, 'chaindata') + os.sep
BROADCASTED_BLOCK_DIR = os.path.join(CHAINDATA_DIR, 'bblocks') + os.sep

os.makedirs(CHAINDATA_DIR, exist_ok=True)
os.makedirs(BROADCASTED_BLOCK_DIR, exist_ok=True)

# ── Settings (module hook → Callimachus > Blockchain settings tab) ─────────────
DEFAULT_PORT = int(os.environ.get('PTOLEMY_CHAIN_PORT', 5000))
PEERS = [
    f'http://localhost:{p}/'
    for p in range(5000, 5004)
    if p != DEFAULT_PORT
]

# ── Chain parameters ──────────────────────────────────────────────────────────
NUM_ZEROS = 5   # PoW difficulty

BLOCK_VAR_CONVERSIONS = {
    'index':     int,
    'nonce':     int,
    'hash':      str,
    'prev_hash': str,
    'timestamp': str,
}

# ── Branch chain identity ─────────────────────────────────────────────────────
# Each Ptolemy Face gets its own branch chain for audit trail.
# Master chain is the root. Branch chains commit to master on flush.
FACE_BRANCHES = {
    'pharos':       5000,
    'callimachus':  5001,
    'archimedes':   5002,
    'kryptos':      5003,
}
