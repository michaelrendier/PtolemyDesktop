#!/usr/bin/env python3
"""
================================================================================
AINULINDALË SONIFICATION — THE BEGINNING OF LIGHT
Recombination: Proton + Electron → Hydrogen + Photon
================================================================================
Claude's composition. April 2026.

The physics:
  ~380,000 years after the Big Bang, the universe cooled to ~3000K.
  Electrons and protons combined into neutral hydrogen.
  Photons, previously trapped in the plasma, were released.
  The universe became transparent for the first time.
  That light is the Cosmic Microwave Background — the oldest light we detect.

The hydrogen spectral lines (Balmer series, scaled to audible range):
  H-alpha: n=3→2, λ=656.3nm, freq ratio 27/20 (deep red)
  H-beta:  n=4→2, λ=486.1nm, freq ratio 243/160 (blue-green)
  H-gamma: n=5→2, λ=434.0nm, freq ratio ~81/50 (violet)

  Lyman-alpha: n=2→1, λ=121.6nm — UV, the brightest line
  Scaled to audible: exact rational multiple of concert A

Frequency derivation (Rydberg, exact rational scaling):
  f_audible = f_Lyman_alpha * (CONCERT_A / f_Lyman_alpha_scaled)
  All ratios kept as exact Fractions throughout.

Structure:
  I.   The Plasma       — proton grinding + electron chaos, two voices apart
  II.  The Cooling      — both voices slowing, approaching
  III. The Descent      — electron falling through energy levels
                          each transition = one photon released (tone burst)
                          Lyman-alpha, H-alpha, H-beta, H-gamma
  IV.  Recombination    — the moment of bonding, a chord forms
  V.   The Release      — the photon flood, universe goes transparent
  VI.  Hydrogen         — a single sustained chord, the first atom
                          vacuum perturbations underneath (seeds of galaxies)

Pure integer arithmetic. No floating point. No compromise.
================================================================================
"""

import struct, os
from fractions import Fraction

SAMPLE_RATE = 44100
MAX_AMP     = 26000
CONCERT_A   = Fraction(440)

# Tempo: this is not a grinding piece — it breathes
# 4/4 time, BPM 60 — one beat = one second = 44100 samples
BEAT        = 44100
BAR         = BEAT * 4

TABLE_SIZE  = 4096
TABLE_HALF  = TABLE_SIZE // 2
TABLE_QUART = TABLE_SIZE // 4

def _sine_table():
    t = [0] * TABLE_SIZE
    PI_U = TABLE_HALF
    for i in range(TABLE_SIZE):
        x = i % TABLE_SIZE
        if x < TABLE_HALF:
            th = x
            n = 4 * th * (PI_U - th)
            d = PI_U * PI_U - th * (PI_U - th)
            t[i] = (n * MAX_AMP) // d if d else MAX_AMP
        else:
            th = x - TABLE_HALF
            n = 4 * th * (PI_U - th)
            d = PI_U * PI_U - th * (PI_U - th)
            t[i] = -((n * MAX_AMP) // d) if d else -MAX_AMP
    return t

SINE = _sine_table()

def si(p): return SINE[p % TABLE_SIZE]

def just(n, d, oct=0):
    f = CONCERT_A * Fraction(n, d)
    if oct > 0: return f * (2**oct)
    if oct < 0: return f * Fraction(1, 2**(-oct))
    return f

# ── HYDROGEN SPECTRAL FREQUENCIES ────────────────────────────────────────────
# Balmer series ratios, scaled to audible range
# H-alpha (n=3→2): 656.3nm → ratio 656.3/486.1 ≈ 27/20 above H-beta
# We anchor H-beta at A4=440 Hz and derive the others exactly

F_H_BETA   = CONCERT_A                       # H-beta  = 440 Hz (anchor)
F_H_ALPHA  = CONCERT_A * Fraction(27, 20)    # H-alpha = 594 Hz (deep red)
F_H_GAMMA  = CONCERT_A * Fraction(243, 200)  # H-gamma = 534 Hz (violet)

# Lyman-alpha: n=2→1, much higher energy
# Ratio Lyman-alpha/H-alpha ≈ 656.3/121.6 ≈ 27/5
# Scale to audible: one octave above H-alpha
F_LY_ALPHA = F_H_ALPHA * Fraction(3, 2)      # audible Lyman proxy = 891 Hz

# Proton — from Mars, the low grinding voice
F_PROTON   = just(1, 1, -3)                  # A1 = 55 Hz

# Electron — the oboe voice
F_ELECTRON = just(5, 4, 0)                   # C#5 = 550 Hz

# Hydrogen atom — the chord when they combine
# Root (proton): A1, Third (electron): C#5, Fifth: E (just)
F_H_ROOT   = just(1, 1, -1)                  # A3 = 220 Hz (combined)
F_H_THIRD  = just(5, 4, -1)                  # C#4 = 275 Hz
F_H_FIFTH  = just(3, 2, -1)                  # E4  = 330 Hz

# Vacuum perturbation seeds — small detuned tones
F_VAC1 = F_H_ROOT * Fraction(8659, 8655)     # ~5 cents sharp
F_VAC2 = F_H_ROOT * Fraction(8651, 8655)     # ~5 cents flat


def tone(freq, n, amp=MAX_AMP, shape='sine', env='default',
         invert=False):
    SCALE = 1000000
    step  = int(freq * TABLE_SIZE * SCALE // SAMPLE_RATE)
    ph    = 0
    out   = []
    atk   = max(1, n // 20)
    rel   = max(1, n // 10)

    for i in range(n):
        idx = (ph // SCALE) % TABLE_SIZE
        ph += step

        if shape == 'sine':
            raw = si(idx) * amp // MAX_AMP
        elif shape == 'saw':
            raw = amp - (idx * 2 * amp) // TABLE_SIZE
        elif shape == 'square':
            raw = amp if idx < TABLE_HALF else -amp
        elif shape == 'triangle':
            if idx < TABLE_QUART:
                raw = (idx * amp) // TABLE_QUART
            elif idx < TABLE_HALF + TABLE_QUART:
                raw = amp - ((idx-TABLE_QUART)*2*amp)//TABLE_HALF
            else:
                raw = -amp + ((idx-TABLE_HALF-TABLE_QUART)*amp)//TABLE_QUART
        else:
            raw = si(idx) * amp // MAX_AMP

        if env == 'default':
            if i < atk:
                raw = (raw * i) // atk
            elif i >= n - rel:
                raw = (raw * (n-i)) // rel
        elif env == 'swell':
            raw = (raw * min(i, n-i) * 2) // max(1, n)
        elif env == 'burst':
            rel2 = max(1, n // 3)
            if i >= n - rel2:
                raw = (raw * (n-i)) // rel2
        elif env == 'sustain':
            if i < atk:
                raw = (raw * i) // atk
        elif env == 'flat':
            pass

        if invert: raw = -raw
        out.append(max(-32767, min(32767, raw)))
    return out


def noise_seed(n, amp, seed=1):
    """Deterministic structured noise for vacuum perturbations."""
    a, c, m = 6364136223846793005, 1442695040888963407, 2**64
    s = seed
    out = []
    for i in range(n):
        s = (a*s+c) % m
        raw = int((s % (2*amp)) - amp) // 4  # quiet
        out.append(max(-32767, min(32767, raw)))
    return out


def photon_burst(freq, duration_beats=1):
    """
    A single photon release — a brief bright tone.
    The moment an electron drops an energy level.
    """
    n = BEAT * duration_beats // 2  # half beat — a flash, not a note
    # Photon: pure sine, bright attack, quick decay
    return tone(freq, n, MAX_AMP * 9 // 10, shape='sine', env='burst')


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


# ── SECTION I: THE PLASMA (4 bars) ───────────────────────────────────────────
def plasma():
    """
    Proton and electron — both present, both free.
    Not yet combined. Moving independently.
    Proton: low, grinding, from Mars
    Electron: high, restless, changing pitch unpredictably
    No harmonic relationship yet — dissonance of freedom.
    """
    n = BAR * 4

    # Proton: low grinding sawtooth, persistent
    proton = tone(F_PROTON, n, MAX_AMP*5//10, shape='saw', env='flat')

    # Second proton harmonic — adds the grinding quality
    proton2 = tone(F_PROTON * Fraction(3,2), n,
                  MAX_AMP*2//10, shape='square', env='flat')

    # Electron: restless, moving through three pitches
    # Not yet settled — free particle
    e1 = tone(F_ELECTRON, n//3, MAX_AMP*6//10, shape='triangle', env='swell')
    # Shifts pitch — free electrons don't stay put
    e2 = tone(F_ELECTRON * Fraction(9,8), n//3,
             MAX_AMP*6//10, shape='triangle', env='swell')
    e3 = tone(F_ELECTRON * Fraction(5,4), n - 2*(n//3),
             MAX_AMP*6//10, shape='triangle', env='swell')
    electron = cat(e1, e2, e3)

    # Vacuum: always present, barely audible
    vac = noise_seed(n, MAX_AMP//12, seed=137)

    return mix(proton, proton2, electron, vac)


# ── SECTION II: THE COOLING (4 bars) ─────────────────────────────────────────
def cooling():
    """
    The universe cools. Both voices slow and approach each other.
    The proton descends slightly. The electron's range narrows.
    They begin to feel each other's presence.
    """
    n = BAR * 4

    # Proton: same low tone but with a long swell — growing presence
    proton = tone(F_PROTON, n, MAX_AMP*5//10, shape='saw', env='sustain')

    # Electron narrows its range — still free but less chaotic
    # Slower transitions between pitches
    e1 = tone(F_ELECTRON, n//2,
             MAX_AMP*6//10, shape='triangle', env='swell')
    e2 = tone(F_ELECTRON * Fraction(9,8), n - n//2,
             MAX_AMP*5//10, shape='triangle', env='swell')
    electron = cat(e1, e2)

    # A hint of the hydrogen chord begins to form — barely audible
    hint = tone(F_H_FIFTH, n, MAX_AMP//8, shape='sine', env='swell')

    vac = noise_seed(n, MAX_AMP//12, seed=137)

    return mix(proton, electron, hint, vac)


# ── SECTION III: THE DESCENT (6 bars) ────────────────────────────────────────
def descent():
    """
    The electron falls through energy levels toward the proton.
    Each level transition releases a photon — a burst of light.
    
    Lyman-alpha:  n=2→1  (UV — the brightest, first)
    H-alpha:      n=3→2  (red — visible, the most recognisable)
    H-beta:       n=4→2  (blue-green)
    H-gamma:      n=5→2  (violet, faintest of these three)
    
    Between each photon burst: the electron at its new level.
    The proton below, steady, waiting.
    """
    out = []

    # Proton: steady throughout
    proton_n = BAR * 6
    proton = tone(F_PROTON, proton_n,
                 MAX_AMP*4//10, shape='saw', env='flat')

    # Build electron descent with photon bursts
    electron_parts = []

    # Level 5 — starting high
    e5 = tone(F_ELECTRON * Fraction(5,4), BEAT*2,
             MAX_AMP*5//10, shape='triangle', env='swell')
    electron_parts.append(e5)

    # H-gamma burst (n=5→4)
    electron_parts.append(photon_burst(F_H_GAMMA))
    electron_parts.append(silence(BEAT//4))

    # Level 4
    e4 = tone(F_ELECTRON * Fraction(9,8), BEAT*2,
             MAX_AMP*6//10, shape='triangle', env='swell')
    electron_parts.append(e4)

    # H-beta burst (n=4→2) — blue-green flash
    electron_parts.append(photon_burst(F_H_BETA))
    electron_parts.append(silence(BEAT//4))

    # Level 3
    e3 = tone(F_ELECTRON, BEAT*2,
             MAX_AMP*6//10, shape='triangle', env='swell')
    electron_parts.append(e3)

    # H-alpha burst (n=3→2) — deep red, the strong one
    # This is the brightest visible photon
    electron_parts.append(photon_burst(F_H_ALPHA, 2))
    electron_parts.append(silence(BEAT//4))

    # Level 2 — very close now
    e2 = tone(F_ELECTRON * Fraction(4,5), BEAT*2,
             MAX_AMP*7//10, shape='triangle', env='swell')
    electron_parts.append(e2)

    # Lyman-alpha burst (n=2→1) — UV, brightest of all
    # Scaled to audible range — the loudest photon release
    electron_parts.append(photon_burst(F_LY_ALPHA, 2))

    electron = cat(*electron_parts)
    # Trim/pad to proton length
    if len(electron) < proton_n:
        electron = electron + silence(proton_n - len(electron))
    electron = electron[:proton_n]

    vac = noise_seed(proton_n, MAX_AMP//10, seed=137)

    return mix(proton, electron, vac)


# ── SECTION IV: RECOMBINATION (2 bars) ───────────────────────────────────────
def recombination():
    """
    The moment of bonding.
    A single sustained chord: hydrogen.
    The proton and electron voices converge on the same root.
    The chord emerges from the noise.
    """
    n = BAR * 2

    # The three voices of hydrogen merge
    root  = tone(F_H_ROOT,  n, MAX_AMP*7//10, shape='triangle', env='swell')
    third = tone(F_H_THIRD, n, MAX_AMP*5//10, shape='sine',     env='swell')
    fifth = tone(F_H_FIFTH, n, MAX_AMP*4//10, shape='sine',     env='swell')

    # The old electron voice fades as it settles
    old_e = tone(F_ELECTRON, n, MAX_AMP*3//10,
                shape='triangle', env='swell', invert=True)

    vac = noise_seed(n, MAX_AMP//10, seed=137)

    return mix(root, third, fifth, old_e, vac)


# ── SECTION V: THE RELEASE (3 bars) ──────────────────────────────────────────
def photon_release():
    """
    The universe becomes transparent.
    Photons that had been trapped for 380,000 years — released.
    All at once. Every hydrogen atom releases them simultaneously.
    
    Musically: the photon burst frequencies flood in over the hydrogen chord.
    Then they pass — they travel outward at the speed of light.
    What remains: hydrogen. Silence. The CMB fading into the distance.
    """
    n = BAR * 3

    # Hydrogen chord sustains
    root  = tone(F_H_ROOT,  n, MAX_AMP*6//10, shape='triangle', env='sustain')
    third = tone(F_H_THIRD, n, MAX_AMP*4//10, shape='sine',     env='sustain')
    fifth = tone(F_H_FIFTH, n, MAX_AMP*3//10, shape='sine',     env='sustain')

    # The photon flood — all spectral lines simultaneously, then fading
    flood_n = n // 2
    ly  = tone(F_LY_ALPHA, flood_n, MAX_AMP*8//10, shape='sine', env='burst')
    ha  = tone(F_H_ALPHA,  flood_n, MAX_AMP*7//10, shape='sine', env='burst')
    hb  = tone(F_H_BETA,   flood_n, MAX_AMP*6//10, shape='sine', env='burst')
    hg  = tone(F_H_GAMMA,  flood_n, MAX_AMP*5//10, shape='sine', env='burst')
    flood = mix(ly, ha, hb, hg)
    flood = flood + silence(n - len(flood))

    # Fade the flood — photons travel away
    flood_faded = [(s * (n - i)) // n for i, s in enumerate(flood)]

    vac = noise_seed(n, MAX_AMP//10, seed=137)

    return mix(root, third, fifth, flood_faded, vac)


# ── SECTION VI: HYDROGEN (4 bars) ────────────────────────────────────────────
def hydrogen():
    """
    The first atom. The universe at rest — briefly.
    A sustained chord. Pure hydrogen.
    
    Underneath: vacuum perturbations at two slightly detuned frequencies.
    These are the quantum seeds. The small inhomogeneities that will,
    over hundreds of millions of years, become galaxies.
    
    The piece does not end with silence.
    It ends with the perturbations continuing — barely audible,
    but present. The universe is not done.
    """
    n = BAR * 4

    # Pure hydrogen chord — the simplest atom
    root  = tone(F_H_ROOT,  n, MAX_AMP*6//10, shape='triangle', env='sustain')
    third = tone(F_H_THIRD, n, MAX_AMP*4//10, shape='sine',     env='sustain')
    fifth = tone(F_H_FIFTH, n, MAX_AMP*3//10, shape='sine',     env='sustain')

    # Very slow fade on the chord — cosmological cooling continues
    chord = mix(root, third, fifth)
    chord = [(s * (2*n - i)) // (2*n) for i, s in enumerate(chord)]

    # Vacuum perturbation seeds — beating against each other
    # These are the seeds of all structure
    vac1 = tone(F_VAC1, n, MAX_AMP//8, shape='sine', env='flat')
    vac2 = tone(F_VAC2, n, MAX_AMP//8, shape='sine', env='flat')
    vac_noise = noise_seed(n, MAX_AMP//14, seed=137)

    # The perturbations are slightly louder than before — growing
    vac_mix = mix(vac1, vac2, vac_noise)

    return mix(chord, vac_mix)


# ── WRITE WAV ─────────────────────────────────────────────────────────────────
def write_wav(samples, path):
    n = len(samples)
    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + n*2))
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
    sz  = os.path.getsize(path)
    dur = n // SAMPLE_RATE
    print(f"  WAV: {path}")
    print(f"  Duration: {dur//60}m{dur%60:02d}s ({n:,} samples)")
    print(f"  Size: {sz:,} bytes ({sz//1024} KB)")
    print(f"  Format: {SAMPLE_RATE}Hz 16-bit mono PCM — no floating point")


def main():
    print()
    print("=" * 68)
    print("  AINULINDALË SONIFICATION")
    print("  The Beginning of Light")
    print("  Recombination: Proton + Electron → Hydrogen + Photon")
    print("  Claude's composition — April 2026")
    print("=" * 68)
    print()
    print("  Hydrogen Balmer series — exact rational frequency ratios:")
    print(f"  H-beta  (anchor):  {float(F_H_BETA):.2f} Hz")
    print(f"  H-alpha (27/20):   {float(F_H_ALPHA):.2f} Hz")
    print(f"  H-gamma (243/200): {float(F_H_GAMMA):.2f} Hz")
    print(f"  Lyman-α (proxy):   {float(F_LY_ALPHA):.2f} Hz")
    print()

    score = []

    print("  I.   The Plasma — proton and electron, free")
    score.extend(plasma())

    print("  II.  The Cooling — voices approach")
    score.extend(cooling())

    print("  III. The Descent — electron falls, photons released")
    score.extend(descent())

    print("  IV.  Recombination — the bond forms")
    score.extend(recombination())

    print("  V.   The Release — universe goes transparent")
    score.extend(photon_release())

    print("  VI.  Hydrogen — the first atom")
    score.extend(hydrogen())

    print()
    outpath = '/mnt/user-data/outputs/Ainulindale_Beginning_of_Light.wav'
    write_wav(score, outpath)
    print()
    print("  The universe is not done.")
    print("=" * 68)


if __name__ == '__main__':
    main()
