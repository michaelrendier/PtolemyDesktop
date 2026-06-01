# Archimedes Maths Implementation Guide

`Archimedes/Maths/`

Full plan of attack for completing the Archimedes mathematics library. See also: `/home/rendier/Projects/Ptol/All_The_Maths.txt` (full context primer with all method signatures).

---

## Style Rules (apply to every file)

- `@staticmethod` decorator on every equation method (no `self`/`cls`)
- Module-level constants block at the top of each file (only that file's constants)
- Optional-parameter solver style: `def foo(p=None, V=None): ...` — solve for whichever is `None`
- No import-time side effects (no loops, no prints outside `if __name__ == '__main__'`)
- No multi-paragraph docstrings — one line max

---

## Tier A — Fix Existing Stubs (8 files)

### A1. `Constants.py`
Add SMMIP constants block. Missing: `A_pi` (fine-structure = domain floor), `OMEGA`, `R_CRIT`, `GROUND`, `PHI`, `E_EULER`, physical constants (HBAR, C_LIGHT, MU_0, EPS_0, G_NEWTON, K_B, N_A). Note: `A_pi` = capital Latin A with subscript π, NOT Greek α.

### A2. `Trigonometry.py` — CRITICAL BUG
**degRad and radDeg are swapped.** `degRad(deg)` currently computes `(180/π)*deg` (converts radians to degrees — backwards). Fix direction, then expand: `deg_to_rad`, `rad_to_deg`, `sin_deg`, `cos_deg`, `tan_deg`, `law_of_cosines`, `law_of_sines`, `haversine`.

### A3. `Electromagnetism.py`
Empty class body. Add constants (C, MU_0, EPS_0, K_E) and methods: `coulombs_law`, `electric_field`, `gauss_law`, `biot_savart`, `faraday`, `ohms_law`, `power_dissipation`, `wave_speed`.

### A4. `Calculus.py`
Remove broken string-parsing derivative. Keep any working sympy stubs. Add full sympy-backed methods: `derivative`, `partial_derivative`, `integral`, `limit`, `taylor_series`, `gradient`, `laplacian`, `chain_rule`.

### A5. `LinearAlgebra.py`
3 lines (header only). Full numpy implementation: `dot`, `cross`, `norm`, `mat_mul`, `transpose`, `inverse`, `determinant`, `eigenvalues`, `eigenvectors`, `svd`, `rank`, `solve_linear`.

### A6. `Combinatorics.py`
Audit and fill: `factorial`, `permutations`, `combinations`, `binomial_coeff`, `multinomial`, `catalan`, `stirling_second`, `bell_number`, `derangements`, `partition_count`.

### A7. `Factorial.py`
Audit and fill: `factorial`, `double_factorial`, `rising_factorial`, `falling_factorial`, `gamma_approx` (Lanczos), `log_factorial` (Stirling), `subfactorial`.

### A8. `FibonacciSequence.py` — CRITICAL BUG
**`for i in range(10000): print(...)` runs on module import.** Wrap in `if __name__ == '__main__'`. Add constants (PHI) and methods: `fibonacci` (Binet closed-form), `fibonacci_seq`, `fibonacci_ratio`, `is_fibonacci`, `lucas_number`, `pisano_period`, `zeckendorf`.

---

## Tier B — Fill Subdirectory Stubs (7 files)

### B1. `Series/Maclaurin.py`
**Rewrite from scratch** — current file contains raw pseudocode comments, not valid Python. Add: `exp_series`, `sin_series`, `cos_series`, `ln_series`, `arctan_series`, `sinh_series`, `cosh_series`, `binomial_series`, `geometric_series`.

### B2. `Series/InfiniteSeries.py`
7 lines, comments only. Add: `harmonic`, `harmonic_limit`, `riemann_zeta_approx`, `basel_problem`, `leibniz_pi`, `euler_product`, `alternating_harmonic`, `kempner`.

### B3. `Sequences/SternBrocotSequence.py`
Empty after header. Add: `stern_brocot_tree`, `mediant`, `encode_fraction`, `decode_path`, `farey_sequence`, `rank_in_farey`.

### B4. `Sequences/MersennePrimes.py`
Check if file exists (may already be present — see actual Sequences/ contents). Constants: `KNOWN_MERSENNE_EXPONENTS`. Add: `mersenne`, `is_mersenne_prime`, `mersenne_seq`, `perfect_number`, `lucas_lehmer`.

### B5. `PtolWrote/JN_FixedSet.py`
J_N anti-Möbius involution — `J_N(z) = i/z̄`. Fixed set = unit circle = critical line Re(s)=1/2. Methods: `j_n`, `is_fixed`, `fixed_set_sample`, `j_n_orbit`, `maps_to_critical`, `verify_four_cycle`.

### B6. `PtolWrote/NodeTheorem.py`
SMMIP node structure — sedenion information nodes. Methods: `node_energy`, `propagation_speed`, `node_interference`, `noether_current`, `information_density`, `tower_map`.

### B7. `Tests/isDivisible.py`
Audit and fill: `is_divisible`, `is_prime` (Miller-Rabin), `prime_factors`, `gcd`, `lcm`, `euler_totient`, `is_perfect`, `is_abundant`, `is_deficient`, `digit_sum`, `is_divisible_by_11`.

---

## Tier C — New SMMIP Directory (7 files)

Create `Maths/SMMIP/` with `__init__.py` + 6 modules.

### C1. `SMMIP/__init__.py`
Export all 6 modules. One-line docstring: `"SMMIP mathematical engine — Cayley-Dickson tower"`.

### C2. `SMMIP/CayleyDickson.py`
Cayley-Dickson construction ℝ→ℂ→ℍ→𝕆→𝕊. Constants: `LAYER_DIMS`, `LAYER_NAMES`. Methods: `construct`, `conjugate`, `norm_sq`, `layer_dim`, `embed`, `is_associative`, `is_commutative`, `zero_divisors_exist`, `tower_product`.

### C3. `SMMIP/Lagrangian.py`
Four-layer SMMIP Lagrangian (`L_SMIP = L0 + L1 + L2 + L3`). Constants: `LAYER_COUPLING`. Methods: `L0_kinetic`, `L1_phase`, `L2_spin`, `L3_gauge`, `total`, `density`, `action`.

### C4. `SMMIP/EulerLagrange.py`
Symbolic Euler-Lagrange equations via sympy. Methods: `euler_lagrange`, `field_equation`, `equation_of_motion`, `conserved_quantity`, `canonical_momentum`, `hamiltonian`.

### C5. `SMMIP/FieldStrength.py`
Field strength tensor `F_μν = ∂_μA_ν - ∂_νA_μ + [A_μ, A_ν]`. Constants: `G_STRONG`, `G_WEAK`, `G_EM`. Methods: `field_tensor`, `commutator`, `self_dual`, `yang_mills`, `maxwell_tensor`, `lorentz_invariant`, `curvature_scalar`.

### C6. `SMMIP/NoetherCurrents.py`
Noether's theorem applied to SMMIP symmetries. Constants: `CURRENT_LAYERS = 4`. Methods: `noether_current`, `conservation_check`, `charge`, `energy_momentum`, `angular_momentum`, `topological_charge`, `current_algebra`.

### C7. `SMMIP/RenormalizationGroup.py`
RG flow of SMMIP couplings across tower layers. Constants: `M_Z`, `LAMBDA_QCD`. Methods: `beta_function`, `run_coupling`, `fixed_point`, `asymptotic_freedom`, `tower_flow`, `anomalous_dimension`, `callan_symanzik`.

---

## Tier D — Mathematical Foundations (5 files)

### D1. `SphericalHarmonics.py`
Angular basis for SMMIP wave modes. Methods: `legendre_p`, `spherical_harmonic`, `real_harmonic`, `solid_harmonic`, `normalization`, `addition_theorem`, `clebsch_gordan`.

### D2. `RiemannZeta.py`
ζ(s) and connection to BK/RH proof path. Constants: `R_CRIT`, `OMEGA`, `GROUND`, `KNOWN_ZEROS`. Methods: `zeta`, `zeta_euler_maclaurin`, `eta` (Dirichlet), `xi` (completed), `critical_strip`, `zero_count`, `functional_equation_check`, `gram_point`.

### D3. `InversionGeometry.py`
Circle inversion, anti-Möbius maps, J_N geometry. Constants: `UNIT_RADIUS`. Methods: `invert`, `mobius`, `anti_mobius`, `j_n`, `fixed_points`, `cross_ratio`, `inversion_circle`, `maps_unit_disk_to_half_plane`.

### D4. `BerryKeating.py`
BK conjecture — ζ zeros = quantum eigenvalues of H = xp. Constants: `A_pi` (domain floor, capital A subscript π), `OMEGA`, `R_CRIT`, `GROUND`. Methods: `bk_hamiltonian_eigenvalue`, `semiclassical_counting`, `gutzwiller_trace`, `level_spacing`, `pair_correlation`, `spectral_form_factor`, `omega_bound`, `ground_state_energy`.

### D5. `Schumann.py`
Schumann resonances — Earth-ionosphere cavity modes. Constants: `C_LIGHT`, `R_EARTH`, `H_IONO`, `F1`–`F5` (measured values). Methods: `frequency`, `wavelength`, `quality_factor`, `resonance_seq`, `cavity_mode`, `power_spectrum`, `smmip_coupling`.

---

## File Count Summary

| Tier | Files | Status |
|---|---|---|
| A | 8 | Fix existing — bugs + stubs |
| B | 7 | Fill subdirectory stubs |
| C | 7 | New SMMIP/ directory |
| D | 5 | New mathematical foundations |
| **Total** | **27** | |

---

## Directory Tree After Completion

```
Maths/
├── Constants.py          [A1]
├── Trigonometry.py       [A2]  ← bug fix
├── Electromagnetism.py   [A3]
├── Calculus.py           [A4]
├── LinearAlgebra.py      [A5]
├── Combinatorics.py      [A6]
├── Factorial.py          [A7]
├── FibonacciSequence.py  [A8]  ← bug fix
├── SphericalHarmonics.py [D1]
├── RiemannZeta.py        [D2]
├── InversionGeometry.py  [D3]
├── BerryKeating.py       [D4]
├── Schumann.py           [D5]
├── SMMIP/
│   ├── __init__.py       [C1]
│   ├── CayleyDickson.py  [C2]
│   ├── Lagrangian.py     [C3]
│   ├── EulerLagrange.py  [C4]
│   ├── FieldStrength.py  [C5]
│   ├── NoetherCurrents.py[C6]
│   └── RenormalizationGroup.py [C7]
├── Series/
│   ├── Maclaurin.py      [B1]  ← rewrite
│   └── InfiniteSeries.py [B2]
├── Sequences/
│   ├── SternBrocotSequence.py [B3]
│   └── MersennePrimes.py      [B4]
├── PtolWrote/
│   ├── JN_FixedSet.py    [B5]
│   └── NodeTheorem.py    [B6]
└── Tests/
    └── isDivisible.py    [B7]
```

---

## Full Method Signatures

See `/home/rendier/Projects/Ptol/All_The_Maths.txt` for the complete primer with all method signatures, constant values, and equations for every file in Tiers A–D.
