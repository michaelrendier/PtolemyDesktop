#!/usr/bin/env python3
"""
Callimachus/checkpoint_export.py — Export Monad JSON checkpoint to fast binary.

The binary is loaded by the C ptolemy binary at startup.  Run this once after
wordnet_init.py (and optionally pep_init.py) to produce monad_wordnet.bin.

Binary format (little-endian throughout):
    Header  (28 bytes):
        magic[4]          "PTOL"
        version[4]        uint32 = 1
        N[4]              uint32
        vocab_size[4]     uint32
        A_size[4]         uint32
        word_count[4]     uint32
        threshold[8]      double  (emission_threshold)

    Beta section:
        N × double        (ground value for zeros absent from checkpoint)

    Age section:
        N × int32

    Vocab section (vocab_size entries):
        idx[4]            uint32
        E[8]              double
        word_len[2]       uint16
        word[word_len]    bytes (UTF-8, no null terminator in file)

    A section (A_size entries):
        i[4]              uint32
        j[4]              uint32
        weight[8]         double

Note: Riemann zeros are NOT stored.  The C binary regenerates them via Newton
      iteration on startup (~50ms for N=25000).

Usage:
    python3 Callimachus/checkpoint_export.py
    python3 Callimachus/checkpoint_export.py --input X.json --output X.bin
"""

import sys
import os
import struct
import json
import argparse
import time

_DEFAULT_IN  = os.path.join(os.path.dirname(__file__), 'data', 'monad_wordnet.json')
_DEFAULT_OUT = os.path.join(os.path.dirname(__file__), 'data', 'monad_wordnet.bin')

MAGIC   = b'PTOL'
VERSION = 1


def export(json_path: str, bin_path: str) -> None:
    """
    Convert Monad JSON checkpoint to compact binary for the C binary.

    :param json_path: Source JSON checkpoint (from monad.save()).
    :param bin_path:  Destination binary path.
    """
    print(f'[export] Loading {json_path} ...')
    t0 = time.time()
    with open(json_path) as f:
        ck = json.load(f)

    N              = int(ck['N'])
    word_count     = int(ck.get('word_count', 0))
    threshold      = float(ck.get('emission_threshold', abs(-1.888) * 2.0))
    ground         = 1.888 / N

    # Dense beta array — fill ground for absent entries
    beta = [ground] * N
    for k, v in ck.get('beta', {}).items():
        idx = int(k)
        if 0 <= idx < N:
            beta[idx] = float(v)

    # Dense age array
    age_src = ck.get('age', [])
    if len(age_src) == N:
        age = [int(x) for x in age_src]
    else:
        age = [0] * N

    # Vocab entries: (idx, E, word_bytes)
    vocab_entries = []
    for k, v in ck.get('vocab', {}).items():
        idx  = int(k)
        word = str(v[0])
        E    = float(v[1])
        wb   = word.encode('utf-8', errors='replace')[:254]  # cap at 254 bytes
        vocab_entries.append((idx, E, wb))

    # A edges: (i, j, weight)
    a_entries = []
    for k, v in ck.get('A', {}).items():
        i, j = map(int, k.split(','))
        a_entries.append((i, j, float(v)))

    print(f'[export] N={N}  vocab={len(vocab_entries)}  A={len(a_entries)}  '
          f'load={time.time()-t0:.2f}s')
    t1 = time.time()

    os.makedirs(os.path.dirname(bin_path), exist_ok=True)
    with open(bin_path, 'wb') as f:
        # Header
        f.write(MAGIC)
        f.write(struct.pack('<IIIIId',
                            VERSION, N,
                            len(vocab_entries), len(a_entries),
                            word_count, threshold))

        # Beta
        f.write(struct.pack(f'<{N}d', *beta))

        # Age
        f.write(struct.pack(f'<{N}i', *age))

        # Vocab
        for (idx, E, wb) in vocab_entries:
            f.write(struct.pack('<IHd', idx, len(wb), E))
            f.write(wb)

        # A
        for (i, j, w) in a_entries:
            f.write(struct.pack('<IId', i, j, w))

    size_mb = os.path.getsize(bin_path) / 1e6
    print(f'[export] Written → {bin_path}  {size_mb:.1f} MB  '
          f'({time.time()-t1:.2f}s write)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Export Monad JSON checkpoint to binary.')
    ap.add_argument('--input',  default=_DEFAULT_IN,  help='Source JSON checkpoint')
    ap.add_argument('--output', default=_DEFAULT_OUT, help='Destination binary path')
    args = ap.parse_args()
    export(args.input, args.output)
