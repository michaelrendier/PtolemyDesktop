#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'
"""
RSA.py — real RSA (small pedagogical primes, real math, no shortcuts),
used as the CONTROL CASE for SedenionFactoralRelativity's pathway
decomposition tool (PW14).

Cody, 2026-08-25, the corrected framing: "the point here is not RSA but
building a mathematical 'pathway decomposition' using 'process
operators'...the purpose of RSA here is to be an example of
decompositional vector spaces that we can use as a control group...
regardless of actual mathematical equations or operations associated
with an Octonion or a Quaternion...RSA is a specific standardized
definition that has a minimum set of tools necessary to [produce an
output], and those tools are one component of each of the imaginary
units, like in the vigenere cipher."

So this file is NOT trying to answer "how many imaginary components does
RSA need" as if there were one number to find — it's a real, well-defined
algorithm used to exercise `pathway_decomposition()` (engine/lineage.py)
against a GENUINE dependency graph, not a forced linear chain: CRT-
decrypt's `m1` and `m2` each depend only on the ciphertext (independent
of each other); the CRT term `h` depends on BOTH; the final `m` depends
on `h` AND `m2` again (`m2` fans out to two later operators — the thing
a chain-only tool cannot represent at all). Whatever count of named
operators a process's own minimum tool-set turns out to need is what
`pathway_decomposition()` reports — never fit to a preferred dimension.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'SedenionFactoralRelativity'))
from engine.lineage import ProcessOperator, pathway_decomposition  # noqa: E402


def _is_prime(n: int) -> bool:
    return n > 1 and all(n % f for f in range(2, int(n ** 0.5) + 1))


def generate_keys(p: int, q: int, e: int = 17) -> dict:
    """Real key generation, real primes supplied by the caller (this file
    does not hunt for large primes — that's a different, well-covered
    problem; p=61, q=53 below are the standard small pedagogical pair,
    verified prime here rather than trusted from memory)."""
    if not (_is_prime(p) and _is_prime(q)):
        raise ValueError("p and q must both be prime")
    n = p * q
    phi = (p - 1) * (q - 1)
    from math import gcd
    if gcd(e, phi) != 1:
        raise ValueError(f"e={e} is not coprime to phi(n)={phi}")
    d = pow(e, -1, phi)
    return {'p': p, 'q': q, 'n': n, 'phi': phi, 'e': e, 'd': d}


def encrypt(m: int, keys: dict) -> int:
    return pow(m, keys['e'], keys['n'])


def decrypt_direct(c: int, keys: dict) -> int:
    return pow(c, keys['d'], keys['n'])


def decrypt_crt_pathway(c: int, keys: dict) -> dict:
    """The real-world fast implementation (~4x fewer modexp bits than
    decrypt_direct), decomposed as a genuine dependency graph — the
    control case: m1 and m2 are SIBLINGS (both depend only on `input`,
    not on each other), h depends on both, m depends on h AND m2. This
    is not representable as a linear chain without lying about the
    structure (an earlier version of this file did exactly that, papering
    over the fan-out with closures — corrected, not patched over)."""
    p, q, d = keys['p'], keys['q'], keys['d']
    dP, dQ, qInv = d % (p - 1), d % (q - 1), pow(q, -1, p)

    ops = [
        ProcessOperator('m1', lambda cc: pow(cc, dP, p), depends_on=('input',)),
        ProcessOperator('m2', lambda cc: pow(cc, dQ, q), depends_on=('input',)),
        ProcessOperator('h', lambda m1, m2: (qInv * (m1 - m2)) % p,
                        depends_on=('m1', 'm2')),
        ProcessOperator('m', lambda h, m2: m2 + h * q, depends_on=('h', 'm2')),
    ]
    return pathway_decomposition(c, ops, output_name='m')


def key_lifecycle_pathway(p: int, q: int, e: int, m: int) -> dict:
    """prime p -> prime q -> n -> phi(n) -> e -> d -> encrypt -> decrypt,
    as one traced process — a DIFFERENT real decomposition of "RSA," not
    a re-measurement of decrypt_crt_pathway's. Both are genuine; there is
    no single "correct" number of components for an algorithm this large,
    only whichever real sub-process you point the tool at."""
    ops = [
        ProcessOperator('prime_p', lambda _: p, depends_on=('input',)),
        ProcessOperator('prime_q', lambda _: q, depends_on=('input',)),
        ProcessOperator('modulus_n', lambda pp, qq: pp * qq,
                        depends_on=('prime_p', 'prime_q')),
        ProcessOperator('totient', lambda pp, qq: (pp - 1) * (qq - 1),
                        depends_on=('prime_p', 'prime_q')),
        ProcessOperator('public_e', lambda _: e, depends_on=('input',)),
        ProcessOperator('private_d', lambda ee, phi: pow(ee, -1, phi),
                        depends_on=('public_e', 'totient')),
        ProcessOperator('ciphertext', lambda ee, n: pow(m, ee, n),
                        depends_on=('public_e', 'modulus_n')),
        ProcessOperator('plaintext', lambda ct, dd, n: pow(ct, dd, n),
                        depends_on=('ciphertext', 'private_d', 'modulus_n')),
    ]
    return pathway_decomposition(None, ops, output_name='plaintext')


if __name__ == '__main__':
    keys = generate_keys(p=61, q=53, e=17)
    print(f"keys: {keys}")

    m = 65
    c = encrypt(m, keys)
    m_direct = decrypt_direct(c, keys)
    crt = decrypt_crt_pathway(c, keys)
    print(f"m={m} -> c={c} -> direct-decrypt={m_direct}  "
         f"crt-pathway-decrypt={crt['real']}")
    assert m_direct == m and crt['real'] == m, "RSA self-test FAILED"
    print("RSA self-test (direct AND pathway-CRT agree with the original message): HOLDS")
    print()

    print("CRT-decrypt pathway decomposition:")
    print(f"  real={crt['real']}  dim={crt['dim']}  order={crt['order']}")
    for name, val in crt['imaginary']:
        print(f"    imaginary: {name} = {val}")
    print("  m2 feeds both 'h' and the final 'm' — a real fan-out, not a chain")
    print()

    lifecycle = key_lifecycle_pathway(p=61, q=53, e=17, m=65)
    print("Full key-lifecycle pathway decomposition:")
    print(f"  real={lifecycle['real']}  dim={lifecycle['dim']}  "
         f"order={lifecycle['order']}")
    for name, val in lifecycle['imaginary']:
        print(f"    imaginary: {name} = {val}")
    assert lifecycle['real'] == m, "lifecycle pathway FAILED"
    print()
    print("Two different, both real, decompositions of 'RSA' — not one number. "
         "The point was never which count is 'right'; it's that "
         "pathway_decomposition() resolves whatever dependency shape the "
         "process actually has, including genuine fan-out, correctly.")
