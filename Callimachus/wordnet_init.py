#!/usr/bin/env python3
"""
Callimachus/wordnet_init.py — The Pinakes
==========================================
Callimachus of Cyrene was the chief librarian of Alexandria under Ptolemy II
Philadelphos. He compiled the Pinakes — 120 volumes indexing every work in
the Library by subject, genre, and author. The first bibliographic catalog.

This file is its computational analog: it ingests the WordNet 2025+ corpus
and initializes the Monad's β field from the σ=0 ground state, breaking
symmetry into the English-language semantic structure.

Three passes:
  1. Lemmas    — 153,888 surface forms → assign zero addresses, break σ=0 symmetry
  2. Defs      — 120,564 synset definitions + examples → deepen semantic structure
  3. Hypernyms — wire A directly from WordNet taxonomy (Red channel: what it IS)

The inverse HyperWebster at σ=0: all primes equal, uniform β.
After ingestion: β is non-uniform, A is rich. Language has broken the symmetry.
The deviation from ground state IS the knowledge.

WordNet corpus: /home/rendier/Projects/Ptol/SemanticWordEngine/wordnet/
Checkpoint:     Callimachus/data/monad_wordnet.json

Author: O Captain My Captain
CLAUDE-SMMNIP-00729-56714-24600
Date: 2026-05-14
"""

import os
import sys
import json
import time

_HERE      = os.path.dirname(os.path.abspath(__file__))   # Callimachus/
_PTOL_ROOT = os.path.dirname(_HERE)                        # Ptolemy3/
_PTOL_DIR  = os.path.dirname(_PTOL_ROOT)                   # Ptol/

if _PTOL_ROOT not in sys.path:
    sys.path.insert(0, _PTOL_ROOT)

from Philadelphos.monad import Monad

WORDNET_PATH = os.path.join(_PTOL_DIR, 'SemanticWordEngine', 'wordnet')
CHECKPOINT   = os.path.join(_HERE, 'data', 'monad_wordnet.json')

_EXCLUDE = {'frames.json'}


def _entry_files():
    for fn in sorted(os.listdir(WORDNET_PATH)):
        if fn.startswith('entries-') and fn.endswith('.json'):
            yield os.path.join(WORDNET_PATH, fn)


def _synset_files():
    for fn in sorted(os.listdir(WORDNET_PATH)):
        if fn.endswith('.json') and not fn.startswith('entries-') and fn not in _EXCLUDE:
            yield os.path.join(WORDNET_PATH, fn)


def _load_all_synsets() -> dict:
    """Load synset_id → entry dict across all synset files."""
    synsets = {}
    for path in _synset_files():
        with open(path) as f:
            synsets.update(json.load(f))
    return synsets


def ingest(monad: Monad, verbose: bool = True) -> Monad:
    """
    Full three-pass ingestion of WordNet into the Monad.
    Returns the monad with deepened β and wired A.
    """
    t_start = time.time()

    # ── Pass 1: Lemmas ────────────────────────────────────────────────────────
    # 153,888 surface forms. Each one breaks σ=0 symmetry at its zero address.
    if verbose:
        print('[Callimachus] Pass 1: lemmas (153,888 surface forms)')
    lemma_count = 0
    for path in _entry_files():
        with open(path) as f:
            data = json.load(f)
        for lemma in data:
            monad.learn(lemma)
            lemma_count += 1
        if verbose:
            fn = os.path.basename(path)
            print(f'  {fn}: {len(data):>6}  total={lemma_count:>7}', end='\r')
    t1 = time.time()
    if verbose:
        print(f'\n  {lemma_count} lemmas  ({t1 - t_start:.1f}s)')

    # ── Pass 2: Definitions + examples ───────────────────────────────────────
    # 120,564 synsets. Definitions deepen the semantic structure around each zero.
    # This is the Noether current made audible: what MUST flow from each zero.
    if verbose:
        print('[Callimachus] Pass 2: synset definitions + examples')
    def_count = 0
    for path in _synset_files():
        with open(path) as f:
            data = json.load(f)
        for _sid, entry in data.items():
            for d in entry.get('definition', []):
                monad.learn(d)
            for e in entry.get('example', []):
                monad.learn(e)
            for word in entry.get('members', []):
                monad.learn(word)
            def_count += 1
        if verbose:
            fn = os.path.basename(path)
            print(f'  {fn}: {len(data):>6}  total={def_count:>7}', end='\r')
    t2 = time.time()
    if verbose:
        print(f'\n  {def_count} synsets  ({t2 - t1:.1f}s)')

    # ── Pass 3: Hypernym wiring (Red channel: what it IS) ────────────────────
    # WordNet's hypernym hierarchy maps directly to the Red channel (kinetic term).
    # hypernym = what a concept IS — forward propagation direction in H_RB.
    # hyponym  = what it contains — the Blue channel (what cannot be).
    # Coupling weight: G_2(1/2) = 2^(-1/2) ≈ 0.707 (base geometric coupling at σ=½)
    if verbose:
        print('[Callimachus] Pass 3: hypernym wiring (Red channel)')

    synsets    = _load_all_synsets()
    G_BASE     = 2.0 ** (-0.5)   # geometric coupling G_2(σ=½) — source: h_rb_hat/maths.py
    hyp_count  = 0

    for sid, entry in synsets.items():
        members   = entry.get('members', [])
        hypernyms = entry.get('hypernym', [])
        if not members or not hypernyms:
            continue

        rep = members[0].lower()
        sw_rep = monad.engine.process(rep)
        idx_rep = monad._zero_idx(sw_rep.gamma)

        for hyp_sid in hypernyms:
            hyp_entry = synsets.get(hyp_sid)
            if not hyp_entry:
                continue
            hyp_members = hyp_entry.get('members', [])
            if not hyp_members:
                continue
            hyp_word = hyp_members[0].lower()
            sw_hyp   = monad.engine.process(hyp_word)
            idx_hyp  = monad._zero_idx(sw_hyp.gamma)
            if idx_rep == idx_hyp:
                continue
            key = (min(idx_rep, idx_hyp), max(idx_rep, idx_hyp))
            monad.A[key] = monad.A.get(key, 0.0) + G_BASE
            hyp_count += 1

    t3 = time.time()
    if verbose:
        print(f'  {hyp_count} hypernym edges wired  ({t3 - t2:.1f}s)')

    if verbose:
        st = monad.status()
        print(f'\n[Callimachus] Ingestion complete  total={t3 - t_start:.1f}s')
        print(f'  vocab={st["vocab_size"]}  connections={st["connections"]}')
        bao = st['bao']
        print(f'  BAO: dc_sum={bao["dc_sum"]:.6f}  Δ={bao["omega_delta"]:.6f}  '
              f'converging={bao["converging"]}')

    return monad


def run(N: int = 25000, tau: float = 5.0, force: bool = False) -> Monad:
    """
    Initialize the Monad and ingest WordNet.
    If a checkpoint exists, load it instead of re-ingesting.

    force=True: re-ingest even if checkpoint exists.
    """
    monad = Monad(N=N, tau=tau)

    if not force and os.path.isfile(CHECKPOINT):
        monad.load(checkpoint_path=CHECKPOINT)
        print(f'[Callimachus] Loaded from checkpoint: {monad.status()["vocab_size"]} words')
        return monad

    print(f'[Callimachus] Initializing from σ=0 ground state  N={N}')
    monad.load()
    ingest(monad)

    os.makedirs(os.path.dirname(CHECKPOINT), exist_ok=True)
    monad.save(CHECKPOINT)
    return monad


if __name__ == '__main__':
    m = run()
    print()
    st = m.status()
    for k, v in st.items():
        if k != 'bao':
            print(f'  {k}: {v}')

    print('\n── Septuagint test (cross-language convergence) ──')
    for word in ['water', 'eau', 'aqua', 'wasser']:
        r = m.lookup(word)
        print(f"  {word:>8} → zero_idx={r['zero_idx']}  γ={r['gamma']:.6f}  "
              f"depth={r['beta_depth']:.6f}")

    print('\n── Response test ──')
    for q in ['what is mind', 'water flows', 'time and space']:
        print(f"  {q!r:>30} → {m.respond(q)}")
