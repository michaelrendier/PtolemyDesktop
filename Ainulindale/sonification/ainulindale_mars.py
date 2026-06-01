#!/usr/bin/env python3
"""
================================================================================
AINULINDALË SONIFICATION — MOVEMENT I: MARS / THE STRONG FORCE
================================================================================
Claude's composition. Not a transcription. Not a mapping.

The Strong Force in one sentence:
  Color-charged quarks cannot be separated.
  The harder you pull, the stronger the bond.
  Pull far enough — the string snaps and makes new quarks.
  It never ends. It never resolves.

Compositional choices:
  Time: 5/4 — five beats per bar, never landing on 'one' the same way twice
  Tempo: BPM 40 — slow, grinding, inevitable
  Structure: Three-layer texture
    - Gluon pulse: the constant bond, 8 voices in rotation (percussion)
    - Quark melody: the trapped voices trying to separate
    - Color confinement: every time a quark phrase ends, it is pulled back

  The piece NEVER cadences cleanly.
  Every resolution attempt produces a new quark pair.
  It ends not with silence but with the bond still active.

  Duration target: ~2 minutes (matching Mars BPM 40 at 5/4)

Pure integer arithmetic. No floating point. No compromise.
================================================================================
"""

import struct, os
from fractions import Fraction

SAMPLE_RATE  = 44100
MAX_AMP      = 26000
CONCERT_A    = Fraction(440)

# Mars tempo: BPM 40 = 1.5 seconds per beat
# 5/4 time: bar = 5 beats = 7.5 seconds
BEAT_SAMPLES = (SAMPLE_RATE * 3) // 2   # 66150 samples = 1.5s per beat
BAR_SAMPLES  = BEAT_SAMPLES * 5          # 5/4 bar

# Target: ~2 minutes = 120 seconds
# At 1.5s/beat: 80 beats = 120 seconds = 16 bars of 5/4
TARGET_BARS  = 16

# Fibonacci Gravinon (phi beat)
GRAVINON = (BEAT_SAMPLES * 144) // 89

TABLE_SIZE  = 4096
TABLE_HALF  = TABLE_SIZE // 2
TABLE_QUART = TABLE_SIZE // 4

def _build_sine_table():
    table = [0] * TABLE_SIZE
    PI_U = TABLE_HALF
    for i in range(TABLE_SIZE):
        x = i % TABLE_SIZE
        if x < TABLE_HALF:
            theta = x
            numer = 4 * theta * (PI_U - theta)
            denom = PI_U * PI_U - theta * (PI_U - theta)
            val = (numer * MAX_AMP) // denom if denom else MAX_AMP
        else:
            theta = x - TABLE_HALF
            numer = 4 * theta * (PI_U - theta)
            denom = PI_U * PI_U - theta * (PI_U - theta)
            val = -((numer * MAX_AMP) // denom) if denom else -MAX_AMP
        table[i] = val
    return table

SINE_TABLE = _build_sine_table()

def sine_int(phase): return SINE_TABLE[phase % TABLE_SIZE]

def just_freq(n, d, octave=0):
    f = CONCERT_A * Fraction(n, d)
    if octave > 0:  return f * (2 ** octave)
    if octave < 0:  return f * Fraction(1, 2 ** (-octave))
    return f

# ── FREQUENCIES ──────────────────────────────────────────────────────────────
# Strong force palette: low, dark, grinding
# Root: A1 = 55 Hz (two octaves below concert A)
# Modal: Phrygian (flat 2nd) — the modal sound of inevitability

FREQS = {
    # Gluon pulse voices — 8 color charges
    # Each is a specific interval in the low register
    'g1': just_freq(1, 1, -3),       # A1 = 55 Hz  — root, bass drum
    'g2': just_freq(9, 8, -3),       # B1 = 61.9   — minor 2nd above root (Phrygian)
    'g3': just_freq(6, 5, -3),       # C2 = 66 Hz  — minor 3rd
    'g4': just_freq(4, 3, -3),       # D2 = 73.3   — fourth
    'g5': just_freq(3, 2, -3),       # E2 = 82.5   — fifth
    'g6': just_freq(8, 5, -3),       # F2 = 88     — minor 6th
    'g7': just_freq(9, 5, -3),       # G2 = 99     — minor 7th
    'g8': just_freq(2, 1, -3),       # A2 = 110    — octave

    # Quark voices — trying to separate, always pulled back
    'up':     just_freq(5, 4, 0),    # C#5 = 550   — muted trumpet
    'down':   just_freq(4, 3, 0),    # D5 = 586    — open trumpet
    'strange':just_freq(6, 5, 0),    # C5 = 528    — slightly darker

    # Confinement string — the force that pulls them back
    'string': just_freq(1, 1, -1),   # A3 = 220    — cello/viola low

    # The new pair — born when the string snaps
    'new1':   just_freq(3, 2, 0),    # E5 = 660    — new quark
    'new2':   just_freq(4, 3, 0),    # D5 = 586    — new antiquark
}


def tone(freq_frac, n_samples, amp=MAX_AMP, invert=False,
         shape='saw', env='mars'):
    """Generate tone with Mars-appropriate envelope."""
    SCALE = 1000000
    step = int(freq_frac * TABLE_SIZE * SCALE // SAMPLE_RATE)
    phase = 0
    out = []
    atk = max(1, n_samples // 16)
    rel = max(1, n_samples // 8)

    for i in range(n_samples):
        idx = (phase // SCALE) % TABLE_SIZE
        phase += step

        if shape == 'saw':
            raw = amp - (idx * 2 * amp) // TABLE_SIZE
        elif shape == 'square':
            raw = amp if idx < TABLE_HALF else -amp
        elif shape == 'sine':
            raw = sine_int(idx) * amp // MAX_AMP
        elif shape == 'triangle':
            if idx < TABLE_QUART:
                raw = (idx * amp) // TABLE_QUART
            elif idx < TABLE_HALF + TABLE_QUART:
                raw = amp - ((idx - TABLE_QUART) * 2 * amp) // TABLE_HALF
            else:
                raw = -amp + ((idx - TABLE_HALF - TABLE_QUART) * amp) // TABLE_QUART
        else:
            raw = sine_int(idx)

        if env == 'mars':
            # Hard attack, long sustain, abrupt cutoff
            if i < atk:
                raw = (raw * i) // atk
            elif i >= n_samples - rel:
                raw = (raw * (n_samples - i)) // rel
        elif env == 'slam':
            # Immediate full amplitude, sharp decay
            if i >= n_samples - rel:
                raw = (raw * (n_samples - i)) // rel
        elif env == 'swell':
            raw = (raw * min(i, n_samples - i) * 2) // max(1, n_samples)
        elif env == 'grind':
            # No envelope — constant, grinding
            pass

        if invert: raw = -raw
        out.append(max(-32767, min(32767, raw)))
    return out


def noise(n_samples, amp, seed=1):
    """Deterministic integer noise for gluon percussion."""
    a, c, m = 6364136223846793005, 1442695040888963407, 2**64
    s = seed
    out = []
    rel = max(1, n_samples // 4)
    for i in range(n_samples):
        s = (a * s + c) % m
        raw = int((s % (2 * amp)) - amp)
        if i >= n_samples - rel:
            raw = (raw * (n_samples - i)) // rel
        out.append(max(-32767, min(32767, raw)))
    return out


def silence(n): return [0] * n


def mix(*tracks):
    """Mix tracks by sum then normalize."""
    if not tracks: return []
    n = max(len(t) for t in tracks)
    m = [0] * n
    for t in tracks:
        for i, s in enumerate(t): m[i] += s
    div = max(1, len(tracks))
    return [max(-32767, min(32767, s // div)) for s in m]


def concat(*chunks):
    out = []
    for c in chunks: out.extend(c)
    return out


# ── COMPOSITIONAL ELEMENTS ────────────────────────────────────────────────────

def gluon_pulse(beat_count, phase_offset=0):
    """
    The gluon pulse — 8 voices in rotation.
    This runs THROUGHOUT the piece, never stopping.
    Each beat: one or two gluon voices strike.
    The pattern rotates through the 8 color charges.
    Never the same combination twice in a bar.
    """
    out = []
    gluon_keys = ['g1','g2','g3','g4','g5','g6','g7','g8']
    # 5/4 pattern: which gluons hit on each of 5 beats
    # Beat 1: g1+g5 (root+fifth — power chord of color)
    # Beat 2: g3 (minor third — color shift)
    # Beat 3: g2+g6 (Phrygian second + sixth — tension)
    # Beat 4: g4 (fourth — almost resolves, never does)
    # Beat 5: g7+g8 (minor 7th + octave — pulled back)
    patterns = [
        [0, 4],   # beat 1: g1, g5
        [2],      # beat 2: g3
        [1, 5],   # beat 3: g2, g6
        [3],      # beat 4: g4
        [6, 7],   # beat 5: g7, g8
    ]

    for beat in range(beat_count):
        beat_pos = (beat + phase_offset) % 5
        pattern = patterns[beat_pos]
        beat_tracks = []
        for gi in pattern:
            key = gluon_keys[gi]
            # Each gluon: short noise burst + tuned carrier
            n = BEAT_SAMPLES
            carrier = tone(FREQS[key], n, MAX_AMP * 5 // 8,
                          shape='square', env='slam')
            percuss = noise(n // 2, MAX_AMP * 3 // 8, seed=(gi+1)*17)
            percuss += silence(n - len(percuss))
            beat_tracks.append(mix(carrier, percuss))
        if beat_tracks:
            out.extend(mix(*beat_tracks))
        else:
            out.extend(silence(BEAT_SAMPLES))
    return out


def quark_phrase(quark_key, duration_beats, pull_back=True):
    """
    A quark voice trying to move away.
    Rises in pitch (ascending intervals = moving away from center).
    Then: the confinement string pulls it back.
    pull_back=True: add the string tension snap.
    """
    n = BEAT_SAMPLES * duration_beats
    # Ascending phrase: root → up a fifth → up an octave
    # Each note = duration_beats/3 beats
    third = n // 3
    f1 = FREQS[quark_key]
    f2 = f1 * Fraction(3, 2)   # fifth up
    f3 = f1 * Fraction(2, 1)   # octave up

    part1 = tone(f1, third, MAX_AMP * 7 // 10, shape='saw', env='mars')
    part2 = tone(f2, third, MAX_AMP * 8 // 10, shape='saw', env='mars')
    part3 = tone(f3, n - 2*third, MAX_AMP * 9 // 10, shape='saw', env='mars')

    phrase = concat(part1, part2, part3)

    if pull_back:
        # Confinement string — pulls back to root
        pull_n = BEAT_SAMPLES * 2
        pull = tone(FREQS['string'], pull_n,
                   MAX_AMP * 6 // 10, shape='triangle', env='swell')
        return concat(phrase, pull)
    return phrase


def string_snap(new_pair=False):
    """
    The moment the confinement string snaps.
    Produces a new quark-antiquark pair.
    Musically: sharp dissonance, then two new voices emerge.
    """
    snap_n = BEAT_SAMPLES // 4
    # The snap itself — sharp noise burst
    snap = noise(snap_n, MAX_AMP, seed=42)

    if new_pair:
        # New pair emerging — two voices ascending from the snap
        pair_n = BEAT_SAMPLES * 3
        new1 = tone(FREQS['new1'], pair_n,
                   MAX_AMP * 6 // 10, shape='saw', env='mars')
        new2 = tone(FREQS['new2'], pair_n,
                   MAX_AMP * 6 // 10, invert=True, shape='saw', env='mars')
        return concat(snap, mix(new1, new2))

    return snap


def confinement_grind(bars):
    """
    The underlying grind — the bond that never breaks (audibly).
    Low, constant, slightly detuned from everything else.
    This is the QCD vacuum.
    """
    n = BAR_SAMPLES * bars
    # Two slightly detuned low tones — beating against each other
    # Detuning: 1731/1730 ratio per cent, ~5 cents = 5 applications
    f1 = FREQS['g1']
    # Approximate 5-cent detuning with integer ratio
    # 5 cents ≈ (1731/1730)^5 ≈ 8659/8655 (close enough)
    f2 = f1 * Fraction(8659, 8655)
    t1 = tone(f1, n, MAX_AMP * 4 // 10, shape='sine', env='grind')
    t2 = tone(f2, n, MAX_AMP * 4 // 10, shape='sine', env='grind')
    return mix(t1, t2)


# ── FULL COMPOSITION: MARS / THE STRONG FORCE ────────────────────────────────

def compose_mars():
    """
    Structure (16 bars of 5/4 at BPM 40 = ~2 minutes):

    Bars 1-2:   The gluon pulse begins alone. No melody. Just the bond.
    Bars 3-4:   Up quark enters. Tries to ascend. String pulls back.
    Bars 5-6:   Down quark enters against up quark. They pull in opposition.
    Bar 7:      String snap. New pair born. Four voices briefly.
    Bars 8-9:   All quarks grinding. Gluon pulse thickens.
    Bar 10:     Moment of near-resolution — NEVER arrives. Back to grinding.
    Bars 11-12: Strange quark enters. Three flavors. More complex pull.
    Bar 13:     Second string snap. More pairs. The vacuum seethes.
    Bars 14-15: Everything at once. The bond at full strength.
    Bar 16:     Does not resolve. Ends mid-phrase. The bond is still active.
    """
    print("  Composing Mars / The Strong Force")
    print("  ────────────────────────────────────")
    print("  5/4 time | BPM 40 | 1.5s/beat | 16 bars | target ~2min")

    score = []

    # Underlying grind — runs the whole piece
    grind = confinement_grind(TARGET_BARS)

    # ── BARS 1-2: The pulse begins ────────────────────────────────────────
    print("  [Bars 1-2: Gluon pulse — the bond alone]")
    pulse_12 = gluon_pulse(10, phase_offset=0)  # 10 beats = 2 bars of 5/4
    section_12 = mix(pulse_12, grind[:len(pulse_12)])
    score.extend(section_12)

    # ── BARS 3-4: Up quark enters ─────────────────────────────────────────
    print("  [Bars 3-4: Up quark — ascending, pulled back]")
    pulse_34 = gluon_pulse(10, phase_offset=0)
    quark_34 = quark_phrase('up', 8, pull_back=True)
    quark_34 += silence(max(0, len(pulse_34) - len(quark_34)))
    quark_34 = quark_34[:len(pulse_34)]
    g_start = len(score)
    section_34 = mix(pulse_34,
                     quark_34,
                     grind[g_start:g_start+len(pulse_34)])
    score.extend(section_34)

    # ── BARS 5-6: Down quark enters in opposition ─────────────────────────
    print("  [Bars 5-6: Down quark — opposing pull]")
    pulse_56 = gluon_pulse(10, phase_offset=2)
    up_56   = quark_phrase('up', 5, pull_back=False)
    down_56 = quark_phrase('down', 5, pull_back=False)
    # Stagger them — they pull in opposite directions
    down_offset = silence(BEAT_SAMPLES * 2)
    down_56_delayed = concat(down_offset, down_56)
    n56 = len(pulse_56)
    up_56   = (up_56   + silence(n56))[:n56]
    down_56_delayed = (down_56_delayed + silence(n56))[:n56]
    g_start = len(score)
    section_56 = mix(pulse_56, up_56, down_56_delayed,
                     grind[g_start:g_start+n56])
    score.extend(section_56)

    # ── BAR 7: String snap — new pair born ────────────────────────────────
    print("  [Bar 7: String snap — new quark pair born]")
    pulse_7 = gluon_pulse(5, phase_offset=4)
    snap_7  = string_snap(new_pair=True)
    snap_7  = (snap_7 + silence(len(pulse_7)))[:len(pulse_7)]
    g_start = len(score)
    section_7 = mix(pulse_7, snap_7, grind[g_start:g_start+len(pulse_7)])
    score.extend(section_7)

    # ── BARS 8-9: All quarks grinding ────────────────────────────────────
    print("  [Bars 8-9: All quarks grinding — gluon pulse thickens]")
    # Double gluon density
    pulse_89a = gluon_pulse(10, phase_offset=0)
    pulse_89b = gluon_pulse(10, phase_offset=2)  # offset second pulse
    up_89    = quark_phrase('up', 4, pull_back=False)
    down_89  = quark_phrase('down', 4, pull_back=False)
    n89 = len(pulse_89a)
    up_89   = (up_89   + silence(n89))[:n89]
    down_89 = (down_89 + silence(n89))[:n89]
    g_start = len(score)
    thick_pulse = mix(pulse_89a, pulse_89b)
    section_89 = mix(thick_pulse, up_89, down_89,
                     grind[g_start:g_start+n89])
    score.extend(section_89)

    # ── BAR 10: Near-resolution — never arrives ───────────────────────────
    print("  [Bar 10: Near-resolution — always denied]")
    # A major chord approach — then pulled back to Phrygian
    # The 'almost' moment: rise toward A major, drop back
    n10 = BAR_SAMPLES
    # Approach: A major chord (A, C#, E)
    approach_a = tone(just_freq(1,1,0),  n10//2, MAX_AMP*7//10,
                     shape='triangle', env='swell')
    approach_b = tone(just_freq(5,4,0),  n10//2, MAX_AMP*6//10,
                     shape='triangle', env='swell')
    approach_c = tone(just_freq(3,2,0),  n10//2, MAX_AMP*5//10,
                     shape='triangle', env='swell')
    # Then: forced back to Phrygian grind
    return_grind = gluon_pulse(3, phase_offset=1)  # partial bar — asymmetric
    approach = mix(approach_a, approach_b, approach_c)
    approach_full = concat(approach, return_grind)
    approach_full = (approach_full + silence(n10))[:n10]
    g_start = len(score)
    section_10 = mix(approach_full, grind[g_start:g_start+n10])
    score.extend(section_10)

    # ── BARS 11-12: Strange quark enters ──────────────────────────────────
    print("  [Bars 11-12: Strange quark — three flavors in tension]")
    pulse_1112 = gluon_pulse(10, phase_offset=3)
    up_1112     = quark_phrase('up', 4, pull_back=False)
    down_1112   = quark_phrase('down', 4, pull_back=False)
    strange_off = silence(BEAT_SAMPLES * 3)
    strange_1112 = concat(strange_off,
                          quark_phrase('strange', 4, pull_back=True))
    n1112 = len(pulse_1112)
    up_1112     = (up_1112     + silence(n1112))[:n1112]
    down_1112   = (down_1112   + silence(n1112))[:n1112]
    strange_1112= (strange_1112+ silence(n1112))[:n1112]
    g_start = len(score)
    section_1112 = mix(pulse_1112, up_1112, down_1112, strange_1112,
                       grind[g_start:g_start+n1112])
    score.extend(section_1112)

    # ── BAR 13: Second string snap ────────────────────────────────────────
    print("  [Bar 13: Second snap — vacuum seethes]")
    pulse_13 = gluon_pulse(5, phase_offset=1)
    snap_13  = string_snap(new_pair=True)
    snap_13  = (snap_13 + silence(len(pulse_13)))[:len(pulse_13)]
    g_start = len(score)
    section_13 = mix(pulse_13, snap_13, grind[g_start:g_start+len(pulse_13)])
    score.extend(section_13)

    # ── BARS 14-15: Everything at full strength ───────────────────────────
    print("  [Bars 14-15: Full force — all voices, maximum tension]")
    pulse_1415a = gluon_pulse(10, phase_offset=0)
    pulse_1415b = gluon_pulse(10, phase_offset=2)
    pulse_1415c = gluon_pulse(10, phase_offset=4)
    up_1415    = quark_phrase('up', 3, pull_back=False)
    down_1415  = quark_phrase('down', 3, pull_back=False)
    strange_1415 = quark_phrase('strange', 3, pull_back=False)
    n1415 = len(pulse_1415a)
    up_1415     = (up_1415      + silence(n1415))[:n1415]
    down_1415   = (down_1415    + silence(n1415))[:n1415]
    strange_1415= (strange_1415 + silence(n1415))[:n1415]
    triple_pulse = mix(pulse_1415a, pulse_1415b, pulse_1415c)
    g_start = len(score)
    section_1415 = mix(triple_pulse, up_1415, down_1415, strange_1415,
                       grind[g_start:g_start+n1415])
    score.extend(section_1415)

    # ── BAR 16: Does not resolve ──────────────────────────────────────────
    print("  [Bar 16: No resolution — bond still active — piece ends mid-phrase]")
    # Start a resolution phrase — then cut it short
    # The music stops not because it's done but because we stopped listening
    # The Strong Force continues whether we hear it or not
    pulse_16 = gluon_pulse(5, phase_offset=0)
    unfinished = quark_phrase('up', 2, pull_back=False)
    unfinished = (unfinished + silence(len(pulse_16)))[:len(pulse_16)]
    g_start = len(score)
    section_16 = mix(pulse_16, unfinished,
                     grind[g_start:g_start+len(pulse_16)])
    # Fade the last bar — not to resolution, just to inaudibility
    # The bond persists. We just can't hear it anymore.
    fade_n = len(section_16)
    section_16 = [(s * (fade_n - i)) // fade_n for i, s in enumerate(section_16)]
    score.extend(section_16)

    return score


def write_wav(samples, path):
    n = len(samples)
    data_size = n * 2
    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<I', SAMPLE_RATE))
        f.write(struct.pack('<I', SAMPLE_RATE * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            f.write(struct.pack('<h', max(-32767, min(32767, s))))
    size = os.path.getsize(path)
    dur = n // SAMPLE_RATE
    print(f"\n  WAV: {path}")
    print(f"  Duration: {dur//60}m{dur%60:02d}s ({n:,} samples)")
    print(f"  Size: {size:,} bytes ({size//1024} KB)")
    print(f"  Format: {SAMPLE_RATE}Hz 16-bit mono PCM — no floating point")


def main():
    print()
    print("=" * 68)
    print("  AINULINDALË SONIFICATION")
    print("  Movement I: Mars / The Strong Force")
    print("  Claude's composition — April 2026")
    print("=" * 68)
    print()
    print("  The Strong Force never resolves.")
    print("  Pull a quark away: the bond strengthens.")
    print("  Snap the bond: it makes new quarks.")
    print("  It does not end. We just stop hearing it.")
    print()

    samples = compose_mars()
    outpath = '/mnt/user-data/outputs/Ainulindale_Mars_Strong_Force.wav'
    write_wav(samples, outpath)

    print()
    print("  The bond is still active.")
    print("=" * 68)


if __name__ == '__main__':
    main()
