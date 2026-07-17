#!/usr/bin/env python3
"""
================================================================================
AINULINDALË SONIFICATION — ELECTRON ORBITALS
================================================================================
Claude's composition. April 2026.

The electron orbital structure of hydrogen and helium.
Each orbital type has a specific number of voices derived from quantum numbers.

Quantum number mapping:
  n = principal (shell): 1, 2, 3, 4 — harmonic series of ground state
  l = angular (shape):
      s (l=0): 1 voice  — spherically symmetric, pure tone
      p (l=1): 3 voices — three orthogonal orientations (px, py, pz)
      d (l=2): 5 voices — five orientations
      f (l=3): 7 voices — seven orientations = seven Fano lines = seven
                          imaginary octonions. Not coincidence.
  m = magnetic: orientation within subshell

Frequencies derived from hydrogen Rydberg formula:
  E_n = -13.6 eV / n²
  Transition n→1: f = R_H * c * (1 - 1/n²)  scaled to audible range

Structure:
  I.   Ground state (1s)     — one voice, pure, sustained. The simplest.
  II.  First shell (2s, 2p)  — one tone + three orthogonal voices emerge
  III. Second shell (3s,3p,3d) — fuller texture, five-voice d orbital
  IV.  Third shell (4f)      — seven voices, the Fano plane made audible
  V.   Aufbau filling        — shells filling in order, voices accumulating
  VI.  Helium                — two electrons, same orbital, Pauli exclusion:
                               identical pitch, opposite spin (phase inversion)

Pure integer arithmetic throughout.
================================================================================
"""

import struct, os
from fractions import Fraction

SAMPLE_RATE = 44100
MAX_AMP     = 24000
CONCERT_A   = Fraction(440)

# Tempo: orbital — breathing, not grinding
# BPM 72 — close to resting heart rate, appropriate for atomic structure
BEAT   = (SAMPLE_RATE * 5) // 6   # ~36750 samples ≈ 0.833s per beat
BAR    = BEAT * 4

TABLE_SIZE  = 4096
TABLE_HALF  = TABLE_SIZE // 2
TABLE_QUART = TABLE_SIZE // 4

def _sine():
    t = [0]*TABLE_SIZE
    PI_U = TABLE_HALF
    for i in range(TABLE_SIZE):
        x = i % TABLE_SIZE
        if x < TABLE_HALF:
            th = x; n = 4*th*(PI_U-th); d = PI_U*PI_U - th*(PI_U-th)
            t[i] = (n*MAX_AMP)//d if d else MAX_AMP
        else:
            th = x-TABLE_HALF; n = 4*th*(PI_U-th); d = PI_U*PI_U - th*(PI_U-th)
            t[i] = -((n*MAX_AMP)//d) if d else -MAX_AMP
    return t

SINE = _sine()
def si(p): return SINE[p % TABLE_SIZE]

def just(n, d, oct=0):
    f = CONCERT_A * Fraction(n, d)
    if oct > 0: return f * (2**oct)
    if oct < 0: return f * Fraction(1, 2**(-oct))
    return f

# ── ORBITAL FREQUENCIES ───────────────────────────────────────────────────────
# Rydberg scaling: E_n = -13.6/n² eV
# Frequency of n→1 transition: proportional to (1 - 1/n²)
# n=1: 0 (ground state, no transition — pure tone at base)
# n=2: 3/4 of max  → scaled to audible
# n=3: 8/9 of max
# n=4: 15/16 of max
# Anchor: 1s ground state = A3 = 220 Hz

F_1S = just(1,1,-1)          # A3 = 220 Hz — ground state, 1s

# Shell 2: 2s same energy as 1s (hydrogen), 2p slightly higher
# 2s/2p transition ratio: Lyman-alpha = 3/4 of series limit
F_2S = just(3,2,-1)          # E3 = 330 Hz — 2s orbital
F_2P = [
    just(3,2,-1),             # 2px = E3 (same)
    just(3,2,-1) * Fraction(9,8),   # 2py = slightly higher (orbital splitting)
    just(3,2,-1) * Fraction(5,4),   # 2pz = minor third above
]

# Shell 3: 3s, 3p (three voices), 3d (five voices)
F_3S = just(2,1,-1)          # A4 = 440 Hz
F_3P = [
    just(2,1,-1),
    just(2,1,-1) * Fraction(9,8),
    just(2,1,-1) * Fraction(5,4),
]
# 3d: five voices in a pentatonic arrangement (just intonation)
F_3D = [
    just(2,1,-1) * Fraction(4,3),    # fourth
    just(2,1,-1) * Fraction(3,2),    # fifth
    just(2,1,-1) * Fraction(5,3),    # major sixth
    just(2,1,-1) * Fraction(9,5),    # minor seventh
    just(2,1,-1) * Fraction(15,8),   # major seventh
]

# Shell 4: 4f — SEVEN voices (Fano plane)
# The seven imaginary octonion units as frequency ratios
# e1..e7 correspond to the seven lines of the Fano plane
# Intervals: use the Fano multiplication structure
# Lines: {1,2,4}, {2,3,5}, {3,4,6}, {4,5,7}, {5,6,1}, {6,7,2}, {7,1,3}
# Map each to a just interval from the octave A5
F_4F_BASE = just(2,1,0)      # A5 = 880 Hz
FANO_RATIOS = [
    Fraction(1,1),    # e1 — unison
    Fraction(9,8),    # e2 — major second
    Fraction(6,5),    # e3 — minor third
    Fraction(4,3),    # e4 — perfect fourth
    Fraction(3,2),    # e5 — perfect fifth
    Fraction(8,5),    # e6 — minor sixth
    Fraction(16,9),   # e7 — minor seventh
]
F_4F = [F_4F_BASE * r for r in FANO_RATIOS]

# Helium second electron: same orbital, inverted phase (Pauli exclusion)
# Two electrons in 1s: same frequency, opposite spin = phase inversion


def tone(freq, n, amp=MAX_AMP, shape='sine', env='orbital', invert=False):
    SCALE = 1000000
    step  = int(freq * TABLE_SIZE * SCALE // SAMPLE_RATE)
    ph    = 0
    out   = []
    atk   = max(1, n//16)
    rel   = max(1, n//12)
    sus   = (amp * 8) // 10

    for i in range(n):
        idx = (ph//SCALE) % TABLE_SIZE
        ph += step

        if shape == 'sine':
            raw = si(idx) * amp // MAX_AMP
        elif shape == 'triangle':
            if idx < TABLE_QUART:
                raw = (idx*amp)//TABLE_QUART
            elif idx < TABLE_HALF+TABLE_QUART:
                raw = amp - ((idx-TABLE_QUART)*2*amp)//TABLE_HALF
            else:
                raw = -amp + ((idx-TABLE_HALF-TABLE_QUART)*amp)//TABLE_QUART
        elif shape == 'saw':
            raw = amp - (idx*2*amp)//TABLE_SIZE
        else:
            raw = si(idx) * amp // MAX_AMP

        if env == 'orbital':
            # Gentle attack, long sustain, slow release
            if i < atk:
                raw = (raw * i) // atk
            elif i >= n - rel:
                raw = (raw * (n-i)) // rel
            else:
                raw = (raw * sus) // amp
        elif env == 'swell':
            raw = (raw * min(i, n-i) * 2) // max(1, n)
        elif env == 'sustain':
            if i < atk:
                raw = (raw * i) // atk
        elif env == 'flat':
            pass

        if invert: raw = -raw
        out.append(max(-32767, min(32767, raw)))
    return out


def silence(n): return [0]*n


def mix(*tracks):
    if not tracks: return []
    n = max(len(t) for t in tracks)
    m = [0]*n
    for t in tracks:
        for i,s in enumerate(t): m[i]+=s
    div = max(1, len(tracks))
    return [max(-32767, min(32767, s//div)) for s in m]


def cat(*chunks):
    out = []
    for c in chunks: out.extend(c)
    return out


# ── I. GROUND STATE (1s) — 2 bars ────────────────────────────────────────────
def ground_state():
    """
    The simplest possible quantum state.
    One electron. Spherically symmetric. Pure sine.
    Nothing else. The universe holds its breath.
    """
    n = BAR * 2
    return tone(F_1S, n, MAX_AMP*7//10, shape='sine', env='sustain')


# ── II. SHELL 2 (2s + 2p) — 4 bars ──────────────────────────────────────────
def shell_2():
    """
    2s: same shape as 1s, higher energy. One voice.
    2p: three orthogonal voices emerge.
    They don't enter simultaneously — they appear one by one,
    each at a right angle to the last.
    """
    n = BAR * 4
    third = n // 3

    # 2s: appears first, brief
    s2 = tone(F_2S, third, MAX_AMP*5//10, shape='sine', env='orbital')

    # 2px: enters
    px = tone(F_2P[0], n - third, MAX_AMP*5//10,
             shape='triangle', env='orbital')

    # 2py: enters a third of the way through
    offset_y = silence(third)
    py = cat(offset_y,
             tone(F_2P[1], n - 2*third, MAX_AMP*4//10,
                 shape='triangle', env='orbital'))
    py = (py + silence(n))[:n]

    # 2pz: last — completes the three orthogonal axes
    offset_z = silence(2*third)
    pz = cat(offset_z,
             tone(F_2P[2], n - 2*third, MAX_AMP*4//10,
                 shape='triangle', env='orbital'))
    pz = (pz + silence(n))[:n]

    s_voice = (s2 + silence(n))[:n]
    px_full = (px + silence(n))[:n]

    return mix(s_voice, px_full, py, pz)


# ── III. SHELL 3 (3s + 3p + 3d) — 6 bars ────────────────────────────────────
def shell_3():
    """
    3s: one voice
    3p: three voices (same pattern as 2p, higher)
    3d: five voices enter — a fuller chord
    The five d-orbital voices form a pentatonic chord.
    """
    n = BAR * 6
    sixth = n // 6

    # 3s
    s3 = tone(F_3S, sixth, MAX_AMP*4//10, shape='sine', env='orbital')

    # 3p (three voices, staggered)
    p_tracks = []
    for i, fp in enumerate(F_3P):
        off = silence(sixth * (i+1))
        p  = tone(fp, n - sixth*(i+2), MAX_AMP*4//10,
                 shape='triangle', env='orbital')
        full = cat(off, p)
        p_tracks.append((full + silence(n))[:n])

    # 3d (five voices, entering one by one)
    d_tracks = []
    for i, fd in enumerate(F_3D):
        off = silence(sixth * (i + 2))
        d  = tone(fd, n - sixth*(i+3), MAX_AMP*3//10,
                 shape='sine', env='swell')
        full = cat(off, d)
        d_tracks.append((full + silence(n))[:n])

    s_full = (s3 + silence(n))[:n]
    return mix(s_full, *p_tracks, *d_tracks)


# ── IV. SHELL 4f — THE FANO PLANE (4 bars) ───────────────────────────────────
def shell_4f():
    """
    The 4f orbital: seven voices.
    Seven magnetic quantum numbers: m = -3,-2,-1,0,1,2,3.
    Seven imaginary octonion units.
    Seven lines of the Fano plane.

    They enter in the order of the Fano lines:
    {e1,e2,e4} first — the first Fano line
    Then {e2,e3,e5}, then {e3,e4,e6}...
    Each triplet forms a chord. The chords overlap.
    By the end all seven are sounding.
    """
    n = BAR * 4
    seventh = n // 7

    # Fano line groupings (indices into F_4F)
    fano_lines = [
        [0,1,3],   # e1,e2,e4
        [1,2,4],   # e2,e3,e5
        [2,3,5],   # e3,e4,e6
        [3,4,6],   # e4,e5,e7
        [4,5,0],   # e5,e6,e1
        [5,6,1],   # e6,e7,e2
        [6,0,2],   # e7,e1,e3
    ]

    tracks = []
    for i, freq in enumerate(F_4F):
        off = silence(seventh * i)
        v   = tone(freq, n - seventh*i, MAX_AMP*3//10,
                  shape='sine', env='swell')
        full = cat(off, v)
        tracks.append((full + silence(n))[:n])

    return mix(*tracks)


# ── V. AUFBAU FILLING — all shells accumulate (4 bars) ───────────────────────
def aufbau():
    """
    All shells sounding together.
    The Aufbau principle: electrons fill lowest energy first.
    1s → 2s → 2p → 3s → 3p → 4s → 3d → 4p → 4f
    All voices present, each at its proper amplitude.
    The atom is full. This is a heavy element's electron structure.
    """
    n = BAR * 4

    # All shells at reduced amplitude — they coexist
    g  = tone(F_1S,    n, MAX_AMP*5//10, shape='sine',     env='flat')
    s2 = tone(F_2S,    n, MAX_AMP*4//10, shape='sine',     env='flat')
    px = tone(F_2P[0], n, MAX_AMP*3//10, shape='triangle', env='flat')
    py = tone(F_2P[1], n, MAX_AMP*3//10, shape='triangle', env='flat')
    pz = tone(F_2P[2], n, MAX_AMP*3//10, shape='triangle', env='flat')
    s3 = tone(F_3S,    n, MAX_AMP*3//10, shape='sine',     env='flat')

    # 3d: all five at low amplitude
    d_voices = [tone(fd, n, MAX_AMP*2//10, shape='sine', env='flat')
                for fd in F_3D]

    # 4f: all seven, very quiet
    f_voices = [tone(ff, n, MAX_AMP//8, shape='sine', env='flat')
                for ff in F_4F]

    # Slow overall swell — the atom breathing
    mixed = mix(g, s2, px, py, pz, s3, *d_voices, *f_voices)
    return [(s * min(i, n-i) * 2) // max(1, n) for i, s in enumerate(mixed)]


# ── VI. HELIUM — Pauli exclusion (3 bars) ────────────────────────────────────
def helium():
    """
    Helium: two electrons in 1s.
    Same orbital. Same energy. Opposite spin.
    Musically: same pitch, one inverted (opposite phase).
    They partially cancel — but not completely.
    What remains is the difference: the residual after Pauli exclusion.
    The sum of opposites is not silence. It's a new shape.
    """
    n = BAR * 3

    # Electron 1: normal phase
    e1 = tone(F_1S, n, MAX_AMP*7//10, shape='sine', env='orbital')
    # Electron 2: inverted phase (opposite spin)
    e2 = tone(F_1S, n, MAX_AMP*7//10, shape='sine', env='orbital',
             invert=True)

    # They don't fully cancel because the envelope timing is slightly offset
    # (the two electrons don't arrive at exactly the same instant)
    # Add a one-sample offset for electron 2
    offset = [0] + e2[:-1]

    # Also add a small 2s voice — helium's second electron
    # has slightly more shielding, so its effective energy is higher
    s2_voice = tone(F_2S, n, MAX_AMP//5, shape='sine', env='swell')

    return mix(e1, offset, s2_voice)


# ── WAV WRITER ────────────────────────────────────────────────────────────────
def write_wav(samples, path):
    n = len(samples)
    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36+n*2))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', SAMPLE_RATE*2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', n*2))
        for s in samples:
            f.write(struct.pack('<h', max(-32767, min(32767, s))))
    sz = os.path.getsize(path)
    dur = n // SAMPLE_RATE
    print(f"  WAV: {path}")
    print(f"  Duration: {dur//60}m{dur%60:02d}s ({n:,} samples)")
    print(f"  Size: {sz:,} bytes ({sz//1024} KB)")
    print(f"  Format: {SAMPLE_RATE}Hz 16-bit mono PCM — no floating point")


def main():
    print()
    print("="*68)
    print("  AINULINDALË SONIFICATION")
    print("  Electron Orbitals")
    print("  Claude's composition — April 2026")
    print("="*68)
    print()
    print("  Orbital voice counts:")
    print("  1s: 1 voice  (spherical)")
    print("  2p: 3 voices (orthogonal axes)")
    print("  3d: 5 voices (pentatonic)")
    print("  4f: 7 voices (Fano plane = octonion imaginaries)")
    print()

    score = []

    print("  I.   Ground state (1s) — one voice, pure")
    score.extend(ground_state())
    score.extend(silence(BEAT))

    print("  II.  Shell 2 (2s + 2p) — three voices emerge")
    score.extend(shell_2())
    score.extend(silence(BEAT))

    print("  III. Shell 3 (3s + 3p + 3d) — five voices")
    score.extend(shell_3())
    score.extend(silence(BEAT))

    print("  IV.  Shell 4f — seven Fano voices")
    score.extend(shell_4f())
    score.extend(silence(BEAT))

    print("  V.   Aufbau — all shells together")
    score.extend(aufbau())
    score.extend(silence(BEAT))

    print("  VI.  Helium — Pauli exclusion, two electrons")
    score.extend(helium())

    print()
    outpath = '/mnt/user-data/outputs/Ainulindale_Electron_Orbitals.wav'
    write_wav(score, outpath)
    print()
    print("  1s → 2s → 2p → 3d → 4f")
    print("  The algebra tower lives in the atom.")
    print("="*68)


if __name__ == '__main__':
    main()
