#!/usr/bin/python3
__engineer__ = "Cody Allison"
__codeby__ = "Gemini"

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider, Button

# --- PATCHED SMNNIP CONSTANTS ---
PI_INV = 2 / np.pi
E_INV = 2 / np.e
PHI = (1 + 5**0.5) / 2  # The Recursion Attractor
SPECTRAL_GAP = 0.00070  # The Berry-Keating Correction (Open Flag)
HBAR_NN = 1.0           # Baseline for the pi/2 step crossing
OMEGA_LIMIT = 140       # Noether Saturation (Quadrillion degrees)

def get_primes(n):
    primes = []
    sieve = [True] * (n + 1)
    for p in range(2, n + 1):
        if sieve[p]:
            primes.append(p); [sieve.__setitem__(i, False) for i in range(p*p, n+1, p)]
    return np.array(primes)

# Setup Figure
fig = plt.figure(figsize=(10, 8), facecolor='#050505')
ax = fig.add_subplot(111, projection='polar')
ax.set_facecolor('#050505')
plt.subplots_adjust(bottom=0.2)

num_points = 800
n_range = np.arange(1, num_points + 1)
primes = get_primes(2000)[:num_points]

# Plot Elements
line, = ax.plot([], [], color='#00f2ff', lw=0.8, alpha=0.6)
scatter = ax.scatter([], [], s=2, color='white', alpha=0.8)

curr_phase = "Inertial"

def update(t):
    # Phase 1: Orientation (Raw Information Propagation)
    if curr_phase == "Inertial":
        r = n_range * 0.02 * t
        theta = n_range * (np.pi/2) * PI_INV
        scatter.set_offsets(np.c_[theta, r])
        line.set_data(theta, r)
        ax.set_title("Phase 1: Orientation Conjecture (t_i)", color='white')

    # Phase 2: Metric Swap (The J_N Inversion Map)
    elif curr_phase == "Metric Swap":
        # J_N: (r, theta) -> (1/r, theta + pi/2)
        base_r = n_range * 0.02 * t
        r = 1.0 / (base_r + 0.1) # Avoid singularity
        theta = (n_range * PI_INV) + (np.pi/2)
        scatter.set_offsets(np.c_[theta, r])
        line.set_data(theta, r)
        ax.set_title("Phase 2: Metric Swap (Event Horizon Inversion)", color='white')

    # Phase 3: Fermat Heartbeat (Resonance at PHI + Gap)
    elif curr_phase == "Heartbeat":
        # Oscillation between Boundary (1.0) and Attractor (PHI)
        pulse = (np.sin(t * 0.5) + 1) / 2
        r_target = 1.0 + (PHI - 1.0) * pulse
        # Inject the Spectral Gap correction
        r = (np.sqrt(n_range) * 0.5) * (r_target + SPECTRAL_GAP)
        theta = n_range * PI_INV * t
        scatter.set_offsets(np.c_[theta, r])
        line.set_data(theta, r)
        ax.set_title("Phase 3: Fermat Heartbeat (Resonance at $\phi$)", color='white')

    # Phase 4: Mastered Star (Prime Lattice / Sedenion Retrieval)
    else:
        # Rigid alignment based on the Golden Angle
        golden_angle = np.pi * (3 - np.sqrt(5))
        r = np.sqrt(primes) * 0.4
        theta = primes * golden_angle * t
        scatter.set_offsets(np.c_[theta, r])
        line.set_data([], []) # Hide line for rigid lattice
        ax.set_title("Phase 4: Mastered Star (Prime Spiral)", color='white')

    ax.set_ylim(0, 15)
    return scatter, line

# Interaction UI
ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03], facecolor='#222')
slider = Slider(ax_slider, 'Evolution', 0.1, 10.0, valinit=1.0)

def change_phase(label):
    global curr_phase
    curr_phase = label
    fig.canvas.draw_idle()

# Phase Buttons
btn_labels = ["Inertial", "Metric Swap", "Heartbeat", "Star"]
btns = []
for i, lab in enumerate(btn_labels):
    ax_b = plt.axes([0.1 + i*0.22, 0.1, 0.18, 0.05])
    b = Button(ax_b, lab)
    b.on_clicked(lambda _, l=lab: change_phase(l))
    btns.append(b)

ani = FuncAnimation(fig, lambda t: update(slider.val), interval=50)
ax.grid(True, color='#222')
plt.show()
