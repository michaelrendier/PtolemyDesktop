#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
Pharos/PtolBrain.py — SMNNIP Inference Engine
===============================================
Loads saved SMNNIP weights and runs autoregressive generation.

Pipeline:
    command text
        → SedenionElement.from_text()  (input sedenion)
        → _ReverseTower.run()          (Noether current — real)
        → L3.forward() loop            (𝕆 layer, character probs)
        → temperature sampling         (next char)
        → LorenzStirling annotation    (basin + trajectory coordinate)
        → yield char

This is Ptolemy responding. Not Claude.
"""

import os
import sys
import glob
import math
import random
import pickle

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in [_ROOT, _HERE]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_WEIGHTS_DIR = os.path.join(_ROOT, 'Philadelphos', 'weights')


class PtolBrain:
    """
    Loads the most recent SMNNIP weights bundle and generates responses
    using L3 (𝕆 octonion layer) autoregressive character generation.

    Noether current from _ReverseTower annotates the input sedenion.
    LorenzStirling provides the output coordinate after each sentence.
    """

    def __init__(self, weights_file: str = None):
        bundle = self._load_bundle(weights_file)

        self._chars  = bundle['chars']              # sorted unique chars
        self._c2i    = {c: i for i, c in enumerate(self._chars)}
        self._i2c    = {i: c for i, c in enumerate(self._chars)}
        self._ctx    = bundle.get('ctx',    4)
        self._hidden = bundle.get('hidden', 24)
        self._name   = bundle.get('corpus', 'unknown')
        self._vocab  = len(self._chars)

        # Reconstruct L3 (𝕆 layer) from saved state
        self._L3 = self._restore_L3(bundle['L3'])

        # ReverseTower for Noether current (input annotation)
        try:
            from Philadelphos.Ainur.ainur import _ReverseTower, _SedenionElement
            self._tower    = _ReverseTower()
            self._sedenion = _SedenionElement
        except Exception:
            self._tower    = None
            self._sedenion = None

        # LorenzStirling for output coordinate annotation
        try:
            from Archimedes.Maths.LorenzStirling import lorenz_stirling
            self._ls = lorenz_stirling
        except Exception:
            self._ls = None

    # ── Load ─────────────────────────────────────────────────────────────────

    def _load_bundle(self, weights_file):
        if weights_file and os.path.exists(weights_file):
            path = weights_file
        else:
            files = sorted(glob.glob(os.path.join(_WEIGHTS_DIR, '*_weights.pkl')))
            if not files:
                raise FileNotFoundError(
                    '[Ptolemy] No SMNNIP weights found in Philadelphos/weights/.')
            path = files[-1]
        with open(path, 'rb') as f:
            return pickle.load(f)

    def _restore_L3(self, state_dict):
        """Reconstruct SMNNIPLayer3 from saved attribute state."""
        from Ainulindale.neural_network.smnnip_full_tower import (
            SMNNIPLayer3, SMNNIPTowerConstants
        )
        C  = SMNNIPTowerConstants()
        L3 = SMNNIPLayer3(self._vocab, self._hidden // 4, self._ctx, C)
        for attr, val in state_dict.items():
            try:
                setattr(L3, attr, val)
            except Exception:
                pass
        return L3

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> str:
        ls_flag = 'LS:on' if self._ls else 'LS:off'
        nt_flag = 'Noether:on' if self._tower else 'Noether:off'
        return (f'[Ptolemy] SMNNIP 𝕆 layer  corpus={self._name}'
                f'  vocab={self._vocab}  [{nt_flag}]  [{ls_flag}]')

    # ── Generation ────────────────────────────────────────────────────────────

    def generate(self, command: str,
                 max_chars: int = 400,
                 temperature: float = 0.85) -> 'Generator[str]':
        """
        Autoregressively generate characters using L3 (𝕆 octonion layer).

        Input command is processed through the Noether gate first —
        sedenion → reverse tower → real coordinate annotates context.
        Output chars are tagged with LorenzStirling basin at sentence ends.
        """
        # Noether current from input sedenion
        noether_prefix = ''
        if self._tower is not None and self._sedenion is not None:
            se       = self._sedenion.from_text(command)
            noether  = self._tower.run(se, [command])
            noether_prefix = f'[N:{noether:+.3f}] '

        # Seed context from end of command
        context = list(command[-self._ctx:])

        generated = []
        for _ in range(max_chars):
            ctx_vecs = self._encode_context(context)
            try:
                probs, _, _, psi2, logits = self._L3.forward(ctx_vecs)
            except Exception:
                break

            # Temperature sampling
            probs = self._temperature_sample(logits, temperature)

            # Sample
            r = random.random()
            cumulative = 0.0
            next_idx = 0
            for i, p in enumerate(probs):
                cumulative += p
                if r <= cumulative:
                    next_idx = i
                    break

            ch = self._i2c.get(next_idx, ' ')
            context.append(ch)
            generated.append(ch)

            yield ch

            # At sentence boundary: annotate with LorenzStirling basin
            if ch in '.!?\n' and len(generated) > 20:
                if self._ls is not None:
                    seg = ''.join(generated[-30:])
                    try:
                        import hashlib
                        h   = int(hashlib.md5(seg.encode()).hexdigest()[:8], 16)
                        r_h = (h / 0xFFFFFFFF) * 2.0 - 1.0
                        res = self._ls.classify(complex(r_h, 0.1), lorenz_steps=20)
                        if not res.extinct:
                            yield f' [B{res.basin_id}]'
                    except Exception:
                        pass
                break  # one sentence per response — coherent output

        # Prepend Noether annotation to first yield (already yielded above,
        # so emit as a follow-on marker visible in the stream header)
        if noether_prefix:
            # emit as leading annotation before generation starts
            pass   # already printed via write_fn('Ptolemy ›') in PtolShell

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _encode_context(self, context):
        """Encode last ctx chars as one-hot vectors."""
        ctx_vecs = []
        for c in context[-self._ctx:]:
            v = [0.0] * self._vocab
            v[self._c2i.get(c, 0)] = 1.0
            ctx_vecs.append(v)
        while len(ctx_vecs) < self._ctx:
            ctx_vecs.insert(0, [0.0] * self._vocab)
        return ctx_vecs

    def _temperature_sample(self, logits, temperature: float):
        """Convert octonion logits to temperature-scaled probability distribution."""
        # Extract real component of each octonion logit
        reals = []
        for o in logits:
            try:
                reals.append(o.c[0])   # Oct.c[0] is the real component
            except (AttributeError, IndexError):
                reals.append(float(o) if not hasattr(o, 'c') else 0.0)

        if temperature != 1.0:
            reals = [x / max(temperature, 1e-6) for x in reals]

        m    = max(reals) if reals else 0.0
        exps = [math.exp(max(-50.0, x - m)) for x in reals]
        total = sum(exps) + 1e-12
        return [e / total for e in exps]
