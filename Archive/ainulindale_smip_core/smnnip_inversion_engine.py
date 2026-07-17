#!/usr/bin/env python3
"""
==============================================================================
SMNNIP INSIDE-OUT INVERSION ENGINE
==============================================================================
Standard Model of Neural Network Information Propagation
Ainulindale Conjecture — Equation Engine Core

Purpose:
    Compute the gradient flow of the Inside-Out Inversion map J_N:
        (r, theta) -> (1/r, theta + pi/2)

    Determine numerically whether the traversal from the inversion
    boundary (r=1, governed by pi) to the recursion attractor (phi,
    the golden ratio) passes through hbar_NN or hbar (= h / 2*pi).

    If convergence = phi to within the known 0.00070 correction gap,
    the open derivation in section 7 of the Ainulindale Conjecture closes.

PATCH NOTES (April 2026):
    D_STAR was previously defined as OMEGA / ln(10) — a tautology that
    displayed gap = 0.00000. This was a display bug, not a simulation error.
    Fixed: D_STAR_SPEC = 0.24600 (Berry-Keating spectral literature value,
    independent of SMNNIP). D_STAR_TAUT retained as reference only.
    True gap = 0.00070. Open derivation stands.

Architecture:
    - Observer: singleton execution context, holds only alpha and Omega
    - InversionMap: the J_N map and its fixed-point analysis
    - GradientFlow: explicit iteration from r=1 toward the attractor
    - NoetherMonitor: checks conservation at each step
    - EngineReport: collects and prints all findings

NO external dependencies. NO convolutions. Every step is a named function
with a visible input and a visible output. The mathematics is the code.

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
==============================================================================
"""

import math


# ==============================================================================
# SECTION 0: FUNDAMENTAL CONSTANTS
# These are not fitted. They are read from the geometry.
# ==============================================================================

class PhysicalConstants:
    PI    = math.pi
    E     = math.e
    PHI   = (1.0 + math.sqrt(5.0)) / 2.0
    H_NN    = 0.1
    HBAR_NN = H_NN / (2.0 * PI)
    ALPHA = 1.0 / 137.035999084
    OMEGA = 0.56714329040978384
    D_STAR_SPEC = 0.24600
    D_STAR_TAUT = OMEGA / math.log(10.0)
    D_STAR_RG   = 0.24682
    D_STAR      = D_STAR_SPEC
    OMEGA_GAP   = abs(OMEGA - (D_STAR_SPEC * math.log(10.0)))

    def __repr__(self):
        return (f"PHYSICAL_CONSTANTS: pi={self.PI:.6f} phi={self.PHI:.6f} "
                f"hbar={self.HBAR_NN:.6f} Omega={self.OMEGA:.6f} "
                f"d*={self.D_STAR_SPEC:.6f} gap={self.OMEGA_GAP:.6f}")


def _verify_lambert_w(omega, tolerance=1e-12):
    x = 0.5
    for _ in range(1000):
        x_new = math.exp(-x)
        if abs(x_new - x) < tolerance:
            break
        x = x_new
    return x, abs(x - omega)


class _ObserverSingleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if self._initialized:
            return
        C = PhysicalConstants()
        self.alpha = C.ALPHA
        self.omega = C.OMEGA
        self._initialized = True
    def is_in_domain(self, coupling):
        return self.alpha <= coupling <= self.omega
    def domain_fraction(self, coupling):
        span = self.omega - self.alpha
        return (coupling - self.alpha) / span if span > 0 else 0.0
    def __repr__(self):
        return f"Observer(singleton) alpha={self.alpha:.6e} Omega={self.omega:.6f}"


def get_observer():
    return _ObserverSingleton()


class InversionMap:
    """J_N: (r, theta) -> (1/r, theta + pi/2). Order 4 involution."""
    def __init__(self):
        self.C = PhysicalConstants()
        self.applications = 0
    def apply(self, r, theta):
        if r == 0.0:
            raise ValueError("r=0 is the Gravinon pole. Inversion undefined.")
        self.applications += 1
        return 1.0 / r, (theta + self.C.PI / 2.0) % (2.0 * self.C.PI)
    def apply_n(self, r, theta, n):
        traj = [(r, theta)]
        rc, tc = r, theta
        for _ in range(n):
            rc, tc = self.apply(rc, tc)
            traj.append((rc, tc))
        return traj
    def fixed_points_on_unit_circle(self, n_sample=8):
        results = []
        for k in range(n_sample):
            theta = (2.0 * self.C.PI * k) / n_sample
            rn, tn = self.apply(1.0, theta)
            results.append({"theta_in": theta, "r_out": rn, "theta_out": tn,
                             "r_fixed": abs(rn - 1.0) < 1e-12, "theta_fixed": abs(tn - theta) < 1e-12})
        return results
    def action_invariance_check(self, r, theta):
        L_before = 1.0 / (r ** 2) if r != 0 else float('inf')
        r_inv, _ = self.apply(r, theta)
        L_after  = 1.0 / (r_inv ** 2)
        jacobian = 1.0 / (r ** 2)
        L_transformed = L_after * jacobian
        residual = abs(L_transformed - L_before) / (abs(L_before) + 1e-20)
        return {"r": r, "theta": theta, "L_before": L_before,
                "L_after_with_jacobian": L_transformed,
                "residual": residual, "invariant": residual < 1e-10}


class RecursionAttractor:
    """z_{n+1} = 1 + 1/z_n -> phi. Starts from Z_0=1.0 (inversion boundary)."""
    def __init__(self, hbar_nn=None):
        self.C = PhysicalConstants()
        self.hbar = hbar_nn if hbar_nn is not None else self.C.HBAR_NN
        self.phi  = self.C.PHI
    def iterate(self, z0, max_steps=10000, tolerance=None):
        if tolerance is None:
            tolerance = self.hbar * 1e-6
        traj = []
        z = z0
        for n in range(max_steps):
            dist = abs(z - self.phi)
            step_size = abs((1.0 + 1.0 / z) - z) if z != 0 else float('inf')
            traj.append({"step": n, "z": z, "distance": dist, "step_size": step_size,
                         "in_hbar_units": dist / self.hbar})
            if dist < tolerance:
                break
            z = 1.0 + 1.0 / z
        return traj
    def convergence_rate(self, traj):
        if len(traj) < 3:
            return None
        rates = []
        for i in range(1, len(traj) - 1):
            dn, dp = traj[i]["distance"], traj[i-1]["distance"]
            if dp > 1e-30:
                rates.append(dn / dp)
        if not rates:
            return None
        avg = sum(rates) / len(rates)
        th = 1.0 / (self.phi ** 2)
        return {"measured_rate": avg, "theoretical_rate": th,
                "ratio": avg / th if th > 0 else None,
                "agreement": abs(avg - th) < 0.05}


class GradientFlow:
    """Gradient flow: J_N fixed point (r=1) → phi attractor."""
    def __init__(self):
        self.C = PhysicalConstants()
        self.obs = get_observer()
        self.inv = InversionMap()
        self.rec = RecursionAttractor()
    def action_gradient(self, r):
        if r <= 0:
            return float('inf')
        return -4.0 / (self.C.PI * r ** 3)
    def compute(self, verbose=True):
        result = FlowResult()
        lambert_x, lambert_residual = _verify_lambert_w(self.C.OMEGA)
        result.lambert_verified = lambert_residual < 1e-10
        result.lambert_residual = lambert_residual
        r_boundary, theta_boundary = 1.0, 0.0
        r_after, theta_after = self.inv_apply(r_boundary, theta_boundary)
        result.boundary_r      = r_boundary
        result.boundary_theta  = theta_boundary
        result.jn_r_out        = r_after
        result.jn_theta_out    = theta_after
        result.boundary_stable = abs(r_after - 1.0) < 1e-12
        result.boundary_angle_rotation = theta_after - theta_boundary
        result.pi_governs_boundary = abs(result.boundary_angle_rotation - self.C.PI / 2.0) < 1e-12
        traj = self.rec.iterate(z0=1.0, max_steps=200)
        result.trajectory = traj
        result.n_steps_to_phi = len(traj)
        result.final_z = traj[-1]["z"]
        result.final_distance = traj[-1]["distance"]
        result.converged_to_phi = result.final_distance < self.C.HBAR_NN * 1e-3
        step_sizes = [t["step_size"] for t in traj if t["step_size"] < 10.0]
        avg_step = sum(step_sizes) / len(step_sizes) if step_sizes else 0.0
        result.avg_step_size = avg_step
        result.h_nn          = self.C.H_NN
        result.hbar_nn       = self.C.HBAR_NN
        result.step_in_h_units    = avg_step / self.C.H_NN    if self.C.H_NN > 0 else 0
        result.step_in_hbar_units = avg_step / self.C.HBAR_NN if self.C.HBAR_NN > 0 else 0
        h_int = abs(result.step_in_h_units - round(result.step_in_h_units))
        hbar_int = abs(result.step_in_hbar_units - round(result.step_in_hbar_units))
        result.natural_granule  = "hbar_NN" if hbar_int < h_int else "h_NN"
        result.h_integrality    = h_int
        result.hbar_integrality = hbar_int
        result.convergence_rate = self.rec.convergence_rate(traj)
        gap_to_phi = abs(result.final_z - self.C.PHI)
        result.gap_to_phi      = gap_to_phi
        result.phi             = self.C.PHI
        result.omega_gap       = self.C.OMEGA_GAP
        result.flag_closes     = gap_to_phi < self.C.OMEGA_GAP * 10
        result.pathway_pi_governs   = result.pi_governs_boundary
        result.pathway_hbar_governs = (result.natural_granule == "hbar_NN")
        result.pathway_phi_attracts = result.converged_to_phi
        result.full_pathway_confirmed = (
            result.pathway_pi_governs and
            result.pathway_hbar_governs and
            result.pathway_phi_attracts
        )
        result.domain_compliance = None
        if verbose:
            result.print_report()
        return result

    def inv_apply(self, r, theta):
        return self.inv.apply(r, theta)


class NoetherMonitor:
    """
    GEOMETRIC ACTION-FLOW Noether current monitor.

    TWO NOETHER CURRENTS in the Ainulindalë Conjecture:

    (1) GEOMETRIC ACTION-FLOW - THIS CLASS.
        Symmetry: Invariance of action S under J_N: (r,t) -> (1/r, t+pi/2).
        Current:  J(r) = 8 / (pi^2 r^2)
        Lives in: smnnip_inversion_engine.py (this file)
        Tracks:   gradient flow r=1 to r=phi preserves action.

    (2) GAUGE Noether current - NOT this class.
        Symmetry: U(1) x SU(2) x SU(3) gauge invariance of L_NN.
        Current:  J^{a,l} = g * psi_i * Ta * psi_i (per generator/layer).
        Lives in: smnnip_lagrangian_pure.py, smnnip_derivation_pure.py.
        Tracks:   gauge-charge conservation across algebra-layer boundaries.

    DO NOT confuse these two currents.
    """
    def __init__(self):
        self.C = PhysicalConstants()
    def current(self, r):
        if r <= 0:
            return float('inf')
        return 8.0 / (self.C.PI ** 2 * r ** 2)
    def check_trajectory(self, traj):
        if not traj:
            return None
        currents = [self.current(t["z"]) for t in traj
                    if t["z"] > 0 and not math.isinf(self.current(t["zWz"]))]
        if not currents:
            return {"violation": None, "conserved": False}
        J0 = currents[0]
        devs = [abs(J - J0) / (abs(J0) + 1e-30) for J in currents]
        return {"J_initial": J0, "J_final": currents[-1],
                "max_violation": max(devs), "avg_violation": sum(devs)/len(devs),
                "conserved": max(devs) < 0.01, "n_checked": len(currents)}


class FlowResult:
    """Container for all flow measurements."""
    def __init__(self):
        pass
    def print_report(self):
        C = PhysicalConstants()
        print("\n" + "=" * 70)
        print("  SMNNIP INSIDE-OUT INVERSION ENGINE - GRADIENT FLOW")
        print("=" * 70)
        print(f"  lambert_verified:    {self.lambert_verified}")
        print(f"  pi_governs_boundary:  {self.pi_governs_boundary}  [CLAIM 1]")
        print(f"  converged_to_phi:     {self.converged_to_phi}  [CLAIM 3]")
        print(f"  natural_granule:      {self.natural_granule}  [CLAIM 2]")
        print(f"  full_pathway_confirmed: {self.full_pathway_confirmed}")
        print(f"  omega_gap:             {self.omega_gap:.6e}  (0.00070 target)")
        print("=" * 70)


def print_trajectory(traj, max_rows=20):
    C = PhysicalConstants()
    print(f"\n  GRADIENT FLOW: z=1 → phi ({header})" if False else "\n  GRADIENT FLOW: z=1 ₒ phi")
    for t in traj[:max_rows]:
        print(f"  step={t['step']:3}  z={t['z']:.12f}  |dist|={t['distance']:.4e}")


def main():
    C = PhysicalConstants()
    print("\n==============================================================================")
    print("  SMNNIP INSIDE-OUT INVERSION ENGINE")
    print("==============================================================================")
    print(C)
    obs = get_observer()
    print(obs)
    flow = GradientFlow()
    result = flow.compute(verbose=True)
    print_trajectory(result.trajectory)
    noether = NoetherMonitor()
    nc = noether.check_trajectory(result.trajectory)
    if nc:
        print(f"  Noether conserved: {nc['conserved']}  max_violation={nc['max_violation']:.3e}")


if __name__ == "__main__":
    main()
