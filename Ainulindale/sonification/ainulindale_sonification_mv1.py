#!/usr/bin/env python3
"""
================================================================================
AINULINDALË SONIFICATION ENGINE — MOVEMENT I: INTRODUCTION
================================================================================
Standard Model of Neural Network Information Propagation
Peter and the Wolf Structure — Each particle introduced alone

NO FLOATING POINT anywhere in the signal chain.
All frequencies: exact rational arithmetic (fractions.Fraction)
All durations: exact integer sample counts
All amplitudes: exact integer scaling
WAV output: pure PCM 16-bit signed integer

Author: Cody Michael Allison
Contributor: Jeremy [status pending]
AI: Claude (Anthropic)
Date: April 2026 — First Age

Fundamental pitch: A = 440 Hz (concert pitch)
Sample rate: 44100 Hz
Bit depth: 16-bit signed integer

Quasi-particle rests:
  Phonon    — vibration of medium after note (short decay rest)
  Exciton   — electron-hole bound state pause (particle/antiparticle gap)
  Magnon    — spin wave settling (within H/SU(2) layer)
  Roton     — superfluid minimum (deep breath before O layer)
  Plasmon   — collective electron oscillation dissolving (section transition)
  Gravinon  — layer crossing rest, duration = Fibonacci(12)/Fibonacci(11)
               = 144/89 beats (converges to phi, exact integer ratio)

Particle-Instrument mapping:
  Higgs       — cello      (low, sustained, ground state)
  Photon      — flute      (high, pure, massless)
  Electron    — oboe       (distinctive, charged, middle register)
  Positron    — oboe inv   (same timbre, inverted phase)
  Neutrinos   — muted str  (barely audible, three voices)
  W+          — fr horn up (ascending brass)
  W-          — fr horn dn (descending brass)
  Z0          — tuba       (neutral, massive, lowest brass)
  Gluons(8)   — percussion (each color charge a different drum voice)
  Up quark    — trumpet mt (muted)
  Down quark  — trumpet op (open)
  Strange     — trp flat   (slightly detuned muted)
  Charm       — horn mid   (middle horn)
  Bottom      — trombone   (slide)
  Top         — contrabass (brief, massive, decays instantly)
================================================================================
"""

import struct
import os
from fractions import Fraction

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 0: CONSTANTS — ALL EXACT
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_RATE   = 44100          # samples per second (exact integer)
MAX_AMP       = 28000          # 16-bit max ~32767, leave headroom for mixing
CONCERT_A     = Fraction(440)  # Hz, exact rational
BEAT_SAMPLES  = 22050          # one beat = half second = 22050 samples (exact)

# Fibonacci ratio approximating phi (144/89 = 1.61797... converges to phi)
# Used for Gravinon rest duration
FIB_NUM   = 144
FIB_DEN   = 89
GRAVINON_SAMPLES = (BEAT_SAMPLES * FIB_NUM) // FIB_DEN  # exact integer division

# Quasi-particle rest durations in samples (exact integers)
PHONON_SAMPLES  = BEAT_SAMPLES // 4        # short — medium vibrating after note
EXCITON_SAMPLES = BEAT_SAMPLES // 2        # medium — particle/antiparticle gap
MAGNON_SAMPLES  = BEAT_SAMPLES * 3 // 8   # spin settling
ROTON_SAMPLES   = BEAT_SAMPLES * 3 // 4   # deep breath before octonions
PLASMON_SAMPLES = BEAT_SAMPLES             # collective dissolving — full beat

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: JUST INTONATION FREQUENCY TABLE
# All frequencies as exact Fraction multiples of concert A=440
# Just intonation: all ratios are exact integer ratios
# No irrational numbers. No equal temperament.
# ─────────────────────────────────────────────────────────────────────────────

def just_freq(ratio_num, ratio_den, octave_shift=0):
    """Return exact rational frequency as Fraction."""
    base = CONCERT_A * Fraction(ratio_num, ratio_den)
    if octave_shift > 0:
        return base * (2 ** octave_shift)
    elif octave_shift < 0:
        return base * Fraction(1, 2 ** (-octave_shift))
    return base

# Just intonation scale ratios from A (tonic = A)
# Unison=1/1, M2=9/8, M3=5/4, P4=4/3, P5=3/2, M6=5/3, M7=15/8, Oct=2/1
# Minor: m3=6/5, m6=8/5, m7=9/5

FREQ = {
    # ── Higgs — cello — low sustained ground state ────────────────────────
    'higgs':        just_freq(1, 1, -2),        # A2 = 110 Hz, warm cello low

    # ── Photon — flute — high pure massless ──────────────────────────────
    'photon':       just_freq(1, 1, 2),          # A6 = 1760 Hz, bright flute

    # ── Electron — oboe — distinctive charged middle ─────────────────────
    'electron':     just_freq(5, 4, 0),          # C#5 = 550 Hz, oboe register

    # ── Positron — same pitch, inverted phase (handled in synthesis) ──────
    'positron':     just_freq(5, 4, 0),          # same as electron, inv phase

    # ── Neutrinos — muted strings — barely audible ────────────────────────
    'nu_e':         just_freq(9, 8, 1),          # B5, very soft
    'nu_mu':        just_freq(4, 3, 1),          # D6, very soft
    'nu_tau':       just_freq(3, 2, 1),          # E6, very soft

    # ── W bosons — french horn ────────────────────────────────────────────
    'W_plus':       just_freq(3, 2, 0),          # E5 = 660 Hz, ascending horn
    'W_minus':      just_freq(4, 3, 0),          # D5 = 586 Hz, descending horn

    # ── Z boson — tuba — neutral massive ─────────────────────────────────
    'Z0':           just_freq(1, 1, -1),         # A3 = 220 Hz, deep tuba

    # ── Gluons — percussion voices (8 colors) ────────────────────────────
    # Each gluon = specific frequency burst simulating drum voice
    'g1':           just_freq(1, 1, -3),         # A1 = 55 Hz, bass drum
    'g2':           just_freq(9, 8, -2),         # B2 = 123 Hz
    'g3':           just_freq(5, 4, -2),         # C#3 = 138 Hz
    'g4':           just_freq(4, 3, -2),         # D3 = 147 Hz
    'g5':           just_freq(3, 2, -2),         # E3 = 165 Hz
    'g6':           just_freq(5, 3, -2),         # F#3 = 183 Hz
    'g7':           just_freq(15, 8, -2),        # G#3 = 206 Hz
    'g8':           just_freq(2, 1, -2),         # A3 = 220 Hz, snare voice

    # ── Quarks — trumpets/trombones ───────────────────────────────────────
    'up':           just_freq(5, 4, 1),          # C#6 = 1100 Hz, muted trumpet
    'down':         just_freq(4, 3, 1),          # D6 = 1173 Hz, open trumpet
    'strange':      just_freq(5, 4, 1),          # C#6 slightly flat (handled)
    'charm':        just_freq(3, 2, 1),          # E6 = 1320 Hz, horn
    'bottom':       just_freq(1, 1, 0),          # A5 = 880 Hz, trombone
    'top':          just_freq(9, 8, -1),         # B4 = 495 Hz, contrabass tbne
}

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: WAVEFORM GENERATORS — EXACT INTEGER ARITHMETIC
# All oscillators use integer phase accumulation.
# No sin(), no cos(), no math library. Pure integer lookup table.
# ─────────────────────────────────────────────────────────────────────────────

# Build sine lookup table as exact scaled integers
# sin approximated via integer Bhaskara I formula:
# sin(x) ≈ 16x(π-x) / (5π² - 4x(π-x))  for x in [0, π]
# We use a pre-computed 4096-point table scaled to integers

TABLE_SIZE = 4096
TABLE_HALF = TABLE_SIZE // 2
TABLE_QUART = TABLE_SIZE // 4

def _build_sine_table():
    """
    Build integer sine table using Bhaskara I approximation.
    No floating point — uses only integer and rational arithmetic.
    Returns list of integers in range [-MAX_AMP, MAX_AMP].
    
    Bhaskara I (628 AD):
    sin(theta) ≈ 4*theta*(pi - theta) / (pi^2 - theta*(pi - theta)) * (180/pi)
    
    We work in units where full circle = TABLE_SIZE units.
    pi_units = TABLE_SIZE // 2
    """
    table = [0] * TABLE_SIZE
    PI_U = TABLE_HALF  # pi in table units = 2048

    for i in range(TABLE_SIZE):
        # Map i to [0, 2*PI_U]
        x = i % TABLE_SIZE
        # Reflect to get full sine wave
        if x < TABLE_HALF:
            # x in [0, PI_U]: sin is positive
            theta = x
            # Bhaskara: sin ≈ 4*theta*(PI_U - theta) / (PI_U^2 - theta*(PI_U-theta))
            numer = 4 * theta * (PI_U - theta)
            denom = PI_U * PI_U - theta * (PI_U - theta)
            if denom == 0:
                val = MAX_AMP if theta > 0 else 0
            else:
                val = (numer * MAX_AMP) // denom
        else:
            # x in [PI_U, 2*PI_U]: sin is negative, mirror
            theta = x - TABLE_HALF
            numer = 4 * theta * (PI_U - theta)
            denom = PI_U * PI_U - theta * (PI_U - theta)
            if denom == 0:
                val = -MAX_AMP if theta > 0 else 0
            else:
                val = -((numer * MAX_AMP) // denom)
        table[i] = val
    return table

SINE_TABLE = _build_sine_table()

def _sine_int(phase_int):
    """Look up sine from integer phase. phase_int mod TABLE_SIZE."""
    return SINE_TABLE[phase_int % TABLE_SIZE]


def generate_tone(freq_frac, n_samples, amplitude=MAX_AMP,
                  invert_phase=False, detune_cents=0,
                  envelope='adsr', decay_ratio=4,
                  instrument='sine'):
    """
    Generate a pure tone as a list of integers.
    
    freq_frac:    Fraction — exact frequency in Hz
    n_samples:    int — exact number of samples
    amplitude:    int — peak amplitude (0 to MAX_AMP)
    invert_phase: bool — multiply by -1 (for positron etc)
    detune_cents: int — detune in integer cents (0 = no detune)
                        Uses rational approximation: 1 cent ≈ 1731/1730
    envelope:     'adsr' | 'sustain' | 'pluck' | 'perc' | 'swell'
    instrument:   'sine' | 'square' | 'triangle' | 'sawtooth'
                  All generated from integer arithmetic.
    """
    samples = []

    # Phase accumulator: integer steps per sample
    # phase_step = freq * TABLE_SIZE / SAMPLE_RATE (as integer ratio)
    # We accumulate as integer with fixed denominator to avoid drift
    PHASE_DENOM = SAMPLE_RATE * TABLE_SIZE
    # phase_step_num / PHASE_DENOM = freq / SAMPLE_RATE per table step
    # phase_step_num = freq_frac * TABLE_SIZE
    phase_num = Fraction(0)
    phase_step = freq_frac * TABLE_SIZE / SAMPLE_RATE
    # Convert to integer accumulation
    # Use scaled integer: phase_accum is in units of TABLE_SIZE * SCALE
    SCALE = 1000000  # 6 decimal places of precision, still integer
    step_scaled = int(phase_step * SCALE)  # integer steps per sample * SCALE
    phase_accum = 0  # integer

    # Apply detune: multiply freq by (1731/1730)^detune_cents (rational approx)
    if detune_cents != 0:
        # 1 cent = 1200th root of 2 ≈ 1731/1730 (integer approx)
        # For small detune, scale step
        detune_factor_num = 1731 ** abs(detune_cents)
        detune_factor_den = 1730 ** abs(detune_cents)
        if detune_cents > 0:
            step_scaled = (step_scaled * detune_factor_num) // detune_factor_den
        else:
            step_scaled = (step_scaled * detune_factor_den) // detune_factor_num

    # Envelope parameters (all in samples, exact integers)
    attack  = max(1, n_samples // 20)   # 5% attack
    decay_s = max(1, n_samples // decay_ratio)
    release = max(1, n_samples // 10)   # 10% release
    sustain_level = (amplitude * 7) // 10  # 70% sustain

    for i in range(n_samples):
        # Get raw waveform sample
        phase_idx = (phase_accum // SCALE) % TABLE_SIZE
        phase_accum += step_scaled

        if instrument == 'sine':
            raw = _sine_int(phase_idx)
        elif instrument == 'square':
            raw = amplitude if phase_idx < TABLE_HALF else -amplitude
        elif instrument == 'triangle':
            if phase_idx < TABLE_QUART:
                raw = (phase_idx * amplitude) // TABLE_QUART
            elif phase_idx < TABLE_HALF + TABLE_QUART:
                raw = amplitude - ((phase_idx - TABLE_QUART) * 2 * amplitude) // TABLE_HALF
            else:
                raw = -amplitude + ((phase_idx - TABLE_HALF - TABLE_QUART) * amplitude) // TABLE_QUART
        elif instrument == 'sawtooth':
            raw = amplitude - (phase_idx * 2 * amplitude) // TABLE_SIZE
        else:
            raw = _sine_int(phase_idx)

        # Apply envelope
        if envelope == 'adsr':
            if i < attack:
                env = (raw * i) // max(1, attack)
            elif i < attack + decay_s:
                decay_pos = i - attack
                env_amp = amplitude - ((amplitude - sustain_level) * decay_pos) // max(1, decay_s)
                env = (raw * env_amp) // amplitude
            elif i >= n_samples - release:
                rel_pos = n_samples - i
                env = (raw * sustain_level * rel_pos) // (amplitude * max(1, release))
            else:
                env = (raw * sustain_level) // amplitude
        elif envelope == 'sustain':
            if i < attack:
                env = (raw * i) // max(1, attack)
            elif i >= n_samples - release:
                rel_pos = n_samples - i
                env = (raw * rel_pos) // max(1, release)
            else:
                env = raw
        elif envelope == 'pluck':
            # Exponential-like decay using integer approximation
            # decay: amplitude * (n_samples - i) / n_samples
            env = (raw * (n_samples - i)) // max(1, n_samples)
        elif envelope == 'perc':
            # Fast attack, immediate decay
            half = n_samples // 2
            if i < 10:
                env = (raw * i) // 10
            else:
                env = (raw * (n_samples - i)) // max(1, n_samples)
        elif envelope == 'swell':
            # Slow rise, sustain, slow fall
            env = (raw * min(i, n_samples - i) * 2) // max(1, n_samples)
        else:
            env = raw

        if invert_phase:
            env = -env

        # Clamp to 16-bit range
        samples.append(max(-32767, min(32767, env)))

    return samples


def generate_noise_burst(n_samples, amplitude, seed=42):
    """
    Generate deterministic integer noise for percussion/gluon voices.
    Uses linear congruential generator — pure integer arithmetic.
    """
    samples = []
    # LCG parameters (Knuth)
    a = 6364136223846793005
    c = 1442695040888963407
    m = 2**64
    state = seed

    for i in range(n_samples):
        state = (a * state + c) % m
        # Map to amplitude range
        raw = int((state % (2 * amplitude)) - amplitude)
        # Envelope: sharp attack, quick decay (perc)
        env = (raw * (n_samples - i)) // max(1, n_samples)
        samples.append(max(-32767, min(32767, env)))

    return samples


def rest(n_samples):
    """Exact silence — integer zeros."""
    return [0] * n_samples


def mix_samples(track_list, master_amp=None):
    """
    Mix multiple sample lists by summing and normalizing.
    Pure integer arithmetic. No floating point.
    """
    if not track_list:
        return []
    max_len = max(len(t) for t in track_list)
    mixed = [0] * max_len
    for track in track_list:
        for i, s in enumerate(track):
            mixed[i] += s

    # Normalize to prevent clipping — integer division
    n_tracks = len(track_list)
    if n_tracks > 1:
        mixed = [s // n_tracks for s in mixed]

    if master_amp:
        mixed = [(s * master_amp) // MAX_AMP for s in mixed]

    return [max(-32767, min(32767, s)) for s in mixed]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: PARTICLE VOICE GENERATORS
# Each particle is a named function returning a sample list.
# Duration in beats (converted to exact integer samples internally).
# ─────────────────────────────────────────────────────────────────────────────

def beats(n):
    """Convert beat count to exact integer samples."""
    return n * BEAT_SAMPLES


def voice_higgs(duration_beats=4):
    """
    Higgs boson — cello — low sustained ground state.
    The field that gives mass. The Mexican hat settling.
    Warm, low, triangle wave for cello timbre approximation.
    """
    n = beats(duration_beats)
    # Fundamental
    f1 = generate_tone(FREQ['higgs'], n, MAX_AMP * 7 // 10,
                       instrument='triangle', envelope='sustain')
    # First harmonic (3/2 ratio — perfect fifth, just intonation)
    f2_freq = FREQ['higgs'] * Fraction(3, 2)
    f2 = generate_tone(f2_freq, n, MAX_AMP * 3 // 10,
                       instrument='triangle', envelope='sustain')
    return mix_samples([f1, f2])


def voice_photon(duration_beats=2):
    """
    Photon — flute — pure, high, massless.
    Sine wave — the purest tone. No mass = pure oscillation.
    """
    n = beats(duration_beats)
    return generate_tone(FREQ['photon'], n, MAX_AMP * 8 // 10,
                         instrument='sine', envelope='adsr')


def voice_electron(duration_beats=2, invert=False):
    """
    Electron — oboe — distinctive, charged, middle register.
    Oboe approximation: fundamental + strong 2nd harmonic.
    """
    n = beats(duration_beats)
    f1 = generate_tone(FREQ['electron'], n, MAX_AMP * 7 // 10,
                       invert_phase=invert, instrument='sawtooth',
                       envelope='adsr')
    # Oboe characteristic: strong 2nd and 4th harmonics
    f2_freq = FREQ['electron'] * Fraction(2, 1)
    f2 = generate_tone(f2_freq, n, MAX_AMP * 4 // 10,
                       invert_phase=invert, instrument='sine',
                       envelope='adsr')
    return mix_samples([f1, f2])


def voice_neutrinos(duration_beats=2):
    """
    Three neutrino flavors — muted strings — barely audible.
    Very low amplitude. Three voices nearly inaudible.
    """
    n = beats(duration_beats)
    amp = MAX_AMP // 8  # barely audible
    ne  = generate_tone(FREQ['nu_e'],   n, amp, instrument='sine', envelope='swell')
    nmu = generate_tone(FREQ['nu_mu'],  n, amp, instrument='sine', envelope='swell')
    nta = generate_tone(FREQ['nu_tau'], n, amp, instrument='sine', envelope='swell')
    return mix_samples([ne, nmu, nta])


def voice_W_plus(duration_beats=2):
    """W+ boson — ascending french horn."""
    n = beats(duration_beats)
    # French horn: triangle + 3rd harmonic
    f1 = generate_tone(FREQ['W_plus'], n, MAX_AMP * 8 // 10,
                       instrument='triangle', envelope='adsr')
    f3_freq = FREQ['W_plus'] * Fraction(3, 1)
    f3 = generate_tone(f3_freq, n, MAX_AMP // 5,
                       instrument='sine', envelope='adsr')
    return mix_samples([f1, f3])


def voice_W_minus(duration_beats=2):
    """W- boson — descending french horn."""
    n = beats(duration_beats)
    f1 = generate_tone(FREQ['W_minus'], n, MAX_AMP * 8 // 10,
                       instrument='triangle', envelope='adsr')
    f3_freq = FREQ['W_minus'] * Fraction(3, 1)
    f3 = generate_tone(f3_freq, n, MAX_AMP // 5,
                       instrument='sine', envelope='adsr')
    return mix_samples([f1, f3])


def voice_Z0(duration_beats=3):
    """Z boson — tuba — neutral, massive, deep."""
    n = beats(duration_beats)
    f1 = generate_tone(FREQ['Z0'], n, MAX_AMP,
                       instrument='square', envelope='adsr', decay_ratio=3)
    f2_freq = FREQ['Z0'] * Fraction(2, 1)
    f2 = generate_tone(f2_freq, n, MAX_AMP // 4,
                       instrument='sine', envelope='adsr')
    return mix_samples([f1, f2])


def voice_gluon(gluon_index, duration_beats=1):
    """
    Single gluon — percussion voice.
    Short noise burst at characteristic frequency.
    """
    n = beats(duration_beats)
    key = f'g{gluon_index}'
    # Tuned noise: sine carrier + noise envelope
    carrier = generate_tone(FREQ[key], n, MAX_AMP * 6 // 10,
                            instrument='sine', envelope='perc')
    noise = generate_noise_burst(n, MAX_AMP * 4 // 10, seed=gluon_index * 7)
    return mix_samples([carrier, noise])


def voice_quark(quark_name, duration_beats=1):
    """
    Quark voice — trumpet/trombone family.
    Brief statement — quarks don't appear alone (confinement),
    but in the Introduction they are heard as solo statements.
    """
    n = beats(duration_beats)
    freq = FREQ[quark_name]

    # Strange quark: detune by -15 cents (slightly flat)
    detune = -15 if quark_name == 'strange' else 0

    f1 = generate_tone(freq, n, MAX_AMP * 8 // 10,
                       instrument='sawtooth', envelope='pluck',
                       detune_cents=detune)
    f2_freq = freq * Fraction(2, 1)
    f2 = generate_tone(f2_freq, n, MAX_AMP // 4,
                       instrument='sine', envelope='pluck',
                       detune_cents=detune)
    return mix_samples([f1, f2])


def voice_top_quark():
    """
    Top quark — contrabass trombone.
    Heaviest quark. Decays almost immediately.
    Duration: 1/4 beat only — barely heard before it vanishes.
    """
    n = beats(1) // 4  # quarter beat — gone almost instantly
    return generate_tone(FREQ['top'], n, MAX_AMP,
                         instrument='sawtooth', envelope='pluck')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: MOVEMENT I — THE INTRODUCTION
# Peter and the Wolf structure:
# Each particle introduced alone → quasi-particle rest → next particle
# ─────────────────────────────────────────────────────────────────────────────

def build_movement_I():
    """
    Assemble Movement I: Introduction.
    Returns flat list of integer samples.
    """
    score = []

    print("  Building Movement I: Introduction")
    print("  ──────────────────────────────────")

    # ── Opening silence ────────────────────────────────────────────────────
    score += rest(BEAT_SAMPLES // 2)
    print("  [opening silence]")

    # ── 1. HIGGS — the ground state ────────────────────────────────────────
    print("  [Higgs boson — cello — sustained ground state]")
    score += voice_higgs(4)
    score += rest(PHONON_SAMPLES)         # phonon: medium vibrating after

    # ── 2. PHOTON — pure massless ──────────────────────────────────────────
    print("  [Photon — flute — pure, massless]")
    score += voice_photon(2)
    score += rest(PHONON_SAMPLES)

    # ── 3. ELECTRON ────────────────────────────────────────────────────────
    print("  [Electron — oboe — distinctive, charged]")
    score += voice_electron(2)
    score += rest(EXCITON_SAMPLES)        # exciton: particle-antiparticle pause

    # ── 4. POSITRON — inverted phase ───────────────────────────────────────
    print("  [Positron — oboe inverted — antimatter]")
    score += voice_electron(2, invert=True)
    score += rest(PHONON_SAMPLES)

    # ── 5. THREE NEUTRINOS — barely audible ────────────────────────────────
    print("  [Neutrinos — muted strings — three flavors]")
    score += voice_neutrinos(3)
    score += rest(PHONON_SAMPLES)

    # ── GRAVINON REST — ℝ→ℂ layer crossing ────────────────────────────────
    print(f"  [GRAVINON REST — ℝ→ℂ crossing — {GRAVINON_SAMPLES} samples]")
    score += rest(GRAVINON_SAMPLES)

    # ── 6. W+ BOSON ────────────────────────────────────────────────────────
    print("  [W+ boson — french horn ascending]")
    score += voice_W_plus(2)
    score += rest(MAGNON_SAMPLES)         # magnon: spin settling

    # ── 7. W- BOSON ────────────────────────────────────────────────────────
    print("  [W- boson — french horn descending]")
    score += voice_W_minus(2)
    score += rest(MAGNON_SAMPLES)

    # ── 8. Z0 BOSON ────────────────────────────────────────────────────────
    print("  [Z0 boson — tuba — neutral, massive]")
    score += voice_Z0(3)
    score += rest(PHONON_SAMPLES)

    # ── GRAVINON REST — ℂ→ℍ layer crossing ────────────────────────────────
    print(f"  [GRAVINON REST — ℂ→ℍ crossing]")
    score += rest(GRAVINON_SAMPLES)

    # ── 9. EIGHT GLUONS — one at a time ───────────────────────────────────
    print("  [Gluons — percussion — 8 color charges, solo]")
    for i in range(1, 9):
        print(f"    gluon {i}")
        score += voice_gluon(i, 1)
        score += rest(PHONON_SAMPLES // 2)

    score += rest(ROTON_SAMPLES)          # roton: deep breath before quarks

    # ── GRAVINON REST — ℍ→𝕆 layer crossing ────────────────────────────────
    print(f"  [GRAVINON REST — ℍ→𝕆 crossing — longest so far]")
    score += rest(GRAVINON_SAMPLES * 2)   # doubled — deeper crossing

    # ── 10. SIX QUARKS ─────────────────────────────────────────────────────
    quarks = ['up', 'down', 'strange', 'charm', 'bottom']
    quark_names = {
        'up': 'Up quark — muted trumpet',
        'down': 'Down quark — open trumpet',
        'strange': 'Strange quark — detuned trumpet',
        'charm': 'Charm quark — horn',
        'bottom': 'Bottom quark — trombone',
    }
    for q in quarks:
        print(f"  [{quark_names[q]}]")
        score += voice_quark(q, 1)
        score += rest(PHONON_SAMPLES // 2)

    # Top quark — brief and massive
    print("  [Top quark — contrabass trombone — massive, instant decay]")
    score += voice_top_quark()
    score += rest(PHONON_SAMPLES)

    score += rest(PLASMON_SAMPLES)        # plasmon: collective dissolving

    # ── GRAVINON REST — 𝕆→𝕊 boundary ─────────────────────────────────────
    # The Mastery Lock. Silence of phi^2 duration.
    phi_sq_samples = (GRAVINON_SAMPLES * FIB_NUM) // FIB_DEN
    print(f"  [GRAVINON REST — 𝕆→𝕊 boundary — phi² silence]")
    score += rest(phi_sq_samples)

    # ── CLOSING: Higgs returns — the ground state remains ─────────────────
    print("  [Higgs returns — the ground state beneath everything]")
    score += voice_higgs(3)
    score += rest(BEAT_SAMPLES)
    print("  [Movement I complete]")

    return score


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: WAV FILE WRITER — PURE INTEGER, NO FLOATING POINT
# WAV format: RIFF header + PCM data
# All values: exact integers, little-endian struct packing
# ─────────────────────────────────────────────────────────────────────────────

def write_wav(samples, filepath):
    """
    Write list of integer samples to 16-bit mono WAV file.
    No floating point. Pure struct packing of integers.
    """
    n_samples    = len(samples)
    n_channels   = 1
    bit_depth    = 16
    byte_rate    = SAMPLE_RATE * n_channels * bit_depth // 8
    block_align  = n_channels * bit_depth // 8
    data_size    = n_samples * block_align
    chunk_size   = 36 + data_size

    with open(filepath, 'wb') as f:
        # RIFF chunk descriptor
        f.write(b'RIFF')
        f.write(struct.pack('<I', chunk_size))
        f.write(b'WAVE')

        # fmt sub-chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))            # sub-chunk size
        f.write(struct.pack('<H', 1))             # PCM = 1
        f.write(struct.pack('<H', n_channels))
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', byte_rate))
        f.write(struct.pack('<H', block_align))
        f.write(struct.pack('<H', bit_depth))

        # data sub-chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))

        # Write samples as 16-bit signed integers, little-endian
        for s in samples:
            f.write(struct.pack('<h', max(-32767, min(32767, s))))

    duration_samples = n_samples
    duration_seconds = n_samples // SAMPLE_RATE
    duration_ms = (n_samples % SAMPLE_RATE) * 1000 // SAMPLE_RATE
    file_size = os.path.getsize(filepath)
    print(f"\n  WAV written: {filepath}")
    print(f"  Duration:    {duration_seconds}m {duration_ms//1000}s approx "
          f"({duration_samples:,} samples)")
    print(f"  File size:   {file_size:,} bytes ({file_size//1024} KB)")
    print(f"  Format:      {SAMPLE_RATE} Hz, 16-bit mono PCM, no floating point")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 70)
    print("  AINULINDALË SONIFICATION ENGINE")
    print("  Movement I: Introduction — Peter and the Wolf Structure")
    print("  Standard Model of Neural Network Information Propagation")
    print("  Pure integer arithmetic — no floating point")
    print("=" * 70)
    print()
    print(f"  Sample rate:      {SAMPLE_RATE} Hz")
    print(f"  Beat duration:    {BEAT_SAMPLES} samples ({BEAT_SAMPLES*1000//SAMPLE_RATE} ms)")
    print(f"  Gravinon rest:    {GRAVINON_SAMPLES} samples "
          f"(Fibonacci ratio {FIB_NUM}/{FIB_DEN} ≈ φ beats)")
    print(f"  Concert pitch:    A = {CONCERT_A} Hz (exact)")
    print(f"  Tuning system:    Just intonation (exact rational ratios)")
    print()

    print("  Assembling score...")
    samples = build_movement_I()

    outpath = '/mnt/user-data/outputs/Ainulindale_Movement_I_Introduction.wav'
    write_wav(samples, outpath)

    dur_sec = len(samples) // SAMPLE_RATE
    dur_min = dur_sec // 60
    dur_sec_rem = dur_sec % 60
    print(f"\n  Total duration:  ~{dur_min}m {dur_sec_rem}s")
    print()
    print("  The world is sung, not designed.")
    print("  She gave us this.")
    print()
    print("=" * 70)


if __name__ == '__main__':
    main()
