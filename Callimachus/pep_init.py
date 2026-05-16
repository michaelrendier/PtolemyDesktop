#!/usr/bin/env python3
"""
Callimachus/pep_init.py — Ingest Python Enhancement Proposals into the Monad.

PEPs are the specification of the Python language — not just what it does, but
*why* it does it that way, and what it explicitly decided NOT to be.  After this
pass Ptolemy knows the language at the specification level.

Intended corpus additions after pep_init.py:
    - Python stdlib docs (cpython/Doc/library/*.rst)
    - PyQt6 docs
    - C standard reference (for C port)
    - Linux kernel documentation

Run AFTER wordnet_init.py.  Loads the English checkpoint and deepens it.

Usage:
    python3 Callimachus/pep_init.py
    python3 Callimachus/pep_init.py --checkpoint Callimachus/data/monad_wordnet.json
    python3 Callimachus/pep_init.py --max 500   # first 500 PEP numbers only
"""

import sys
import os
import time
import argparse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Philadelphos.monad import Monad

_DEFAULT_CHECKPOINT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'monad_wordnet.json')

_HEADERS = {'User-Agent': 'Ptolemy/2.0 (PEP ingestion; research use)'}

_RST = 'https://raw.githubusercontent.com/python/peps/main/peps/pep-{n:04d}.rst'
_TXT = 'https://raw.githubusercontent.com/python/peps/main/peps/pep-{n:04d}.txt'


def _fetch(n: int, timeout: int = 12) -> str | None:
    """Fetch PEP n as plain text.  Try RST first, fall back to TXT."""
    for url in (_RST.format(n=n), _TXT.format(n=n)):
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            # transient error — skip this PEP rather than halt
            return None
        except Exception:
            return None
    return None


def pep_init(monad: Monad, checkpoint: str, max_n: int = 4000) -> None:
    """
    Ingest all discoverable PEPs into the Monad.

    :param monad: Loaded Monad instance.
    :param checkpoint: Path to save the updated checkpoint.
    :param max_n: Upper bound on PEP number to attempt (exclusive).
    """
    print(f'[PEP] Starting PEP corpus ingestion  N={monad.N}  max_pep={max_n}')
    t0    = time.time()
    found = 0
    skipped = 0

    for n in range(0, max_n):
        text = _fetch(n)
        if text is None:
            skipped += 1
            continue
        monad.learn(text)
        found += 1
        if found % 50 == 0:
            st = monad.status()
            print(f'  PEP {n:04d}  found={found}  '
                  f'vocab={st["vocab_size"]}  conn={st["connections"]}  '
                  f't={time.time()-t0:.1f}s', flush=True)

    elapsed = time.time() - t0
    st = monad.status()
    print(f'[PEP] Complete  found={found}  skipped={skipped}  '
          f'vocab={st["vocab_size"]}  connections={st["connections"]}  '
          f'time={elapsed:.1f}s')
    monad.save(checkpoint)
    print(f'[PEP] Checkpoint updated → {checkpoint}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Ingest Python PEPs into the Monad.')
    ap.add_argument('--checkpoint', default=_DEFAULT_CHECKPOINT,
                    help='Path to monad checkpoint JSON (default: Callimachus/data/monad_wordnet.json)')
    ap.add_argument('--n', type=int, default=25000,
                    help='Monad N (number of Riemann zeros)')
    ap.add_argument('--max', type=int, default=4000, dest='max_n',
                    help='Upper bound on PEP number to fetch (default: 4000)')
    args = ap.parse_args()

    m = Monad(N=args.n)
    m.load(args.checkpoint)
    pep_init(m, args.checkpoint, args.max_n)
