#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
LorenzStirling.py — Lorenz-Stirling Basin Attractor
=====================================================
Archimedes Face — Mathematics

Combines two attractor systems into a unified output-layer classifier:

    Stirling V=10  →  defines BASIN BOUNDARIES (which basin)
    Lorenz         →  defines TRAJECTORY within a basin (where in basin)

Pipeline role
-------------
    Input waveform  →  ℝ→𝕊 encode  →  CWC at 𝕊 apex
                                          ↓
                              LorenzStirling.classify(z_sedenion)
                                          ↓
                        basin_id  +  lorenz_position  +  extinction_flag
                                          ↓
                              𝕊→ℝ decode on that basin's trajectory

Basin geometry (Stirling V=10)
------------------------------
    z_n+1 = p2 * log|S10(z_n)| ^ pow  +  p3

    where S10(z) is the inversion-step Stirling iteration:
        z' = fn(z)          # configurable: identity, sin, log
        x, y = Re(z'), Im(z')
        a = x² + y²
        x, y = x/a + p1_re, y/a + p1_im   # inversion + shift
        z = x + iy
        S10(z) = (15z⁹ - 45z⁸ - 270z⁷ + 182z⁶ + 1687z⁵
                  + 1395z⁴ - 1576z³ - 2684z² - 1008z) / 7680

    Bailout: |z| < bail  →  inside basin
    Escape:  |z| ≥ bail  →  EXTINCTION

Lorenz trajectory (within basin)
---------------------------------
    Standard Lorenz system, parameterized to basin geometry:

    dx/dt = σ(y − x)
    dy/dt = x(ρ − z) − y
    dz/dt = xy − βz

    Default params: σ=10, ρ=28, β=8/3
    These produce the classic butterfly — two focal lobes.
    Basin focal points map to Lorenz lobe centers.

Usage
-----
    from Archimedes.Maths.LorenzStirling import LorenzStirling

    ls = LorenzStirling()

    # Classify a complex point (post-CWC output)
    result = ls.classify(complex(0.3, -0.7))
    print(result.basin_id)        # int — which basin
    print(result.extinct)         # bool — outside all basins
    print(result.lorenz_pos)      # (x, y, z) — position in Lorenz space
    print(result.uncertainty)     # float — distance from basin center

    # Generate attractor trajectory for visualization
    traj = ls.lorenz_trajectory(steps=5000)   # list of (x,y,z)

    # Full basin map (for Alexandria visualization)
    bmap = ls.basin_map(resolution=400)
"""

import cmath
import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional


# ── Stirling V=10 polynomial ──────────────────────────────────────────────────

def stirling_poly_10(z: complex) -> complex:
    """
    Stirling polynomial degree 9 (V=10 in UF om.ufm).
    S10(z) = (15z⁹ - 45z⁸ - 270z⁷ + 182z⁶ + 1687z⁵
              + 1395z⁴ - 1576z³ - 2684z² - 1008z) / 7680
    """
    return (
        15*z**9 - 45*z**8 - 270*z**7 + 182*z**6 + 1687*z**5
        + 1395*z**4 - 1576*z**3 - 2684*z**2 - 1008*z
    ) / 7680


def stirling_inversion_step(z: complex, p1: complex = complex(0.001, 0.001)) -> complex:
    """
    Inversion step from UF formula before Stirling poly.
    Mirrors: a = |z|², z → z/a + p1
    """
    a = z.real**2 + z.imag**2
    if a < 1e-12:
        return p1
    return complex(z.real / a + p1.real, z.imag / a + p1.imag)


# ── Stirling basin iterator ───────────────────────────────────────────────────

@dataclass
class BasinResult:
    basin_id:    int            # which basin (by escape iteration count)
    extinct:     bool           # True if escaped all basins
    iterations:  int            # iterations before escape/bailout
    z_final:     complex        # final z value
    uncertainty: float          # |z_final| — proximity to basin center
    lorenz_pos:  tuple          = field(default_factory=lambda: (0.0, 0.0, 0.0))


class StirlingBasin:
    """
    Iterates the Stirling V=10 formula and classifies complex points
    into basins by escape behavior.
    """

    def __init__(self,
                 p1:      complex = complex(0.001, 0.001),
                 p2:      complex = complex(1.0,   0.0),
                 p3:      complex = complex(0.0,   0.0),
                 pow_exp: float   = 1.0,
                 bail:    float   = 4.0,
                 maxiter: int     = 500):
        self.p1      = p1
        self.p2      = p2
        self.p3      = p3
        self.pow_exp = pow_exp
        self.bail    = bail
        self.maxiter = maxiter

    def iterate(self, z0: complex) -> BasinResult:
        z = z0
        for i in range(self.maxiter):
            # Inversion step
            z = stirling_inversion_step(z, self.p1)
            # Stirling V=10
            try:
                s = stirling_poly_10(z)
                if s == 0:
                    break
                val = cmath.log(abs(s))
                z = self.p2 * (val ** self.pow_exp) + self.p3
            except (ValueError, ZeroDivisionError, OverflowError):
                return BasinResult(
                    basin_id=0, extinct=True, iterations=i,
                    z_final=z, uncertainty=float('inf')
                )
            # Bailout check
            if abs(z) >= self.bail:
                return BasinResult(
                    basin_id=0, extinct=True, iterations=i,
                    z_final=z, uncertainty=abs(z)
                )
        # Stayed inside — basin capture
        basin_id = int(abs(z) * 7) % 8 + 1   # 8 basins, 1-indexed
        return BasinResult(
            basin_id=basin_id,
            extinct=False,
            iterations=self.maxiter,
            z_final=z,
            uncertainty=abs(z)
        )


# ── Lorenz system ─────────────────────────────────────────────────────────────

class LorenzSystem:
    """
    Classic Lorenz attractor. Parameterized to run inside a Stirling basin.
    σ=10, ρ=28, β=8/3 produce the butterfly with two focal lobes.
    """

    def __init__(self, sigma: float = 10.0, rho: float = 28.0, beta: float = 8/3):
        self.sigma = sigma
        self.rho   = rho
        self.beta  = beta

    def step(self, x: float, y: float, z: float, dt: float = 0.005) -> tuple:
        dx = self.sigma * (y - x)
        dy = x * (self.rho - z) - y
        dz = x * y - self.beta * z
        return x + dx*dt, y + dy*dt, z + dz*dt

    def trajectory(self, x0: float = 0.1, y0: float = 0.0, z0: float = 0.0,
                   steps: int = 5000, dt: float = 0.005) -> list[tuple]:
        pts = []
        x, y, z = x0, y0, z0
        for _ in range(steps):
            x, y, z = self.step(x, y, z, dt)
            pts.append((x, y, z))
        return pts

    def seed_from_basin(self, basin_result: BasinResult) -> tuple:
        """Map basin capture point to Lorenz initial condition."""
        z = basin_result.z_final
        x0 =  z.real * 5.0
        y0 =  z.imag * 5.0
        z0 =  basin_result.uncertainty * 10.0
        return x0, y0, z0


# ── LorenzStirling — unified classifier ──────────────────────────────────────

@dataclass
class ClassifyResult:
    basin_id:    int
    extinct:     bool
    lorenz_pos:  tuple          # (x, y, z) in Lorenz space
    uncertainty: float          # distance from basin center
    iterations:  int
    z_final:     complex


class LorenzStirling:
    """
    Unified Lorenz-Stirling basin attractor.

    Stirling V=10 defines basin boundaries.
    Lorenz defines trajectory within each basin.
    Points outside all basins → extinction (no output on that path).
    """

    def __init__(self,
                 stirling_params: Optional[dict] = None,
                 lorenz_params:   Optional[dict] = None):

        sp = stirling_params or {}
        lp = lorenz_params   or {}

        self.stirling = StirlingBasin(**sp)
        self.lorenz   = LorenzSystem(**lp)

    def classify(self, z: complex, lorenz_steps: int = 200) -> ClassifyResult:
        """
        Classify a complex point.
        Returns basin ID, extinction flag, Lorenz position, uncertainty.
        """
        basin = self.stirling.iterate(z)

        if basin.extinct:
            return ClassifyResult(
                basin_id=0, extinct=True,
                lorenz_pos=(0.0, 0.0, 0.0),
                uncertainty=float('inf'),
                iterations=basin.iterations,
                z_final=basin.z_final
            )

        # Seed Lorenz from basin capture point
        x0, y0, z0 = self.lorenz.seed_from_basin(basin)
        traj = self.lorenz.trajectory(x0, y0, z0, steps=lorenz_steps)
        lx, ly, lz = traj[-1] if traj else (0.0, 0.0, 0.0)

        return ClassifyResult(
            basin_id=basin.basin_id,
            extinct=False,
            lorenz_pos=(lx, ly, lz),
            uncertainty=basin.uncertainty,
            iterations=basin.iterations,
            z_final=basin.z_final
        )

    def lorenz_trajectory(self, steps: int = 5000) -> list[tuple]:
        """Full Lorenz trajectory for visualization."""
        return self.lorenz.trajectory(steps=steps)

    def basin_map(self, resolution: int = 300,
                  x_range: tuple = (-3, 3),
                  y_range: tuple = (-3, 3)) -> np.ndarray:
        """
        Compute basin map over complex plane.
        Returns 2D array of basin_ids (0 = extinct).
        For Alexandria visualization.
        """
        xs = np.linspace(x_range[0], x_range[1], resolution)
        ys = np.linspace(y_range[0], y_range[1], resolution)
        grid = np.zeros((resolution, resolution), dtype=int)

        for i, y in enumerate(ys):
            for j, x in enumerate(xs):
                r = self.stirling.iterate(complex(x, y))
                grid[i, j] = 0 if r.extinct else r.basin_id

        return grid


# ── Module-level default instance ────────────────────────────────────────────

lorenz_stirling = LorenzStirling()


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    ls = LorenzStirling()

    print('LorenzStirling Basin Attractor — test')
    print('=' * 42)

    test_points = [
        complex(0.1,  0.1),
        complex(0.5, -0.3),
        complex(2.0,  1.5),
        complex(0.0,  0.0),
        complex(-0.4, 0.8),
    ]

    for pt in test_points:
        r = ls.classify(pt)
        status = 'EXTINCT' if r.extinct else f'basin={r.basin_id}'
        print(f'  z={pt:+.2f}  →  {status:12s}  '
              f'uncertainty={r.uncertainty:.4f}  '
              f'lorenz=({r.lorenz_pos[0]:.2f}, {r.lorenz_pos[1]:.2f}, {r.lorenz_pos[2]:.2f})')
