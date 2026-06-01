# Ultra Fractal Formulary — Ptolemy Index
**Location:** `Archimedes/Maths/Formula/UFformulary/`  
**Source:** Ultra Fractal public formula compilation, Release 08 Apr 2000 and later updates  
**Ptolemy Face:** Archimedes (mathematics/science), Alexandria (OpenGL visualization)

---

## Purpose in Ptolemy

The UF Formulary is a collection of iteration, transformation, and coloring formulas originally written for the Ultra Fractal renderer. In Ptolemy, these serve three roles:

1. **Alexandria** — direct rendering via `FractalRenderer.py` (OpenGL visualization)
2. **Archimedes** — mathematical operators; attractor geometry, basin mapping, spectral decomposition
3. **SMNNIP / Mirrored Curtain** — fractal geometry as a model for propagation, bifurcation topology, and fixed-point behavior

---

## File Types

| Extension | Purpose |
|-----------|---------|
| `.ufm` | Calculation formulas — the iteration engine (what Ptolemy uses mathematically) |
| `.ucl` | Coloring formulas — post-iteration rendering |
| `.uxf` | Transformation formulas — coordinate warping pre-iteration |
| `.ulb` | Libraries / class definitions |
| `.upr` | Parameter files — saved render states |
| `.txt` | Author notes and documentation |

---

## Author Collections

### dmj — Damien M. Jones (`dmj.ufm`, `dmj3.ufm`, `dmj5.ufm`)
Core classical fractal types with structural extensions.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `dmj-Bifurcation` | Bifurcation diagram renderer — iterates a 1D map over a parameter range, plots stable orbits | **Direct MCR analog.** Bifurcation windows are the phase-space portrait of the two-stroke inversion. Basin boundaries = curtain locations |
| `dmj-Lyapunov` | Lyapunov exponent map — measures local divergence rate per pixel | Stability analysis of SMNNIP propagation layers; identifies where fixed points become attractors vs repellers |
| `dmj-LyapMandel` / `dmj-LyapJulia` | Lyapunov exponent applied to Mandelbrot/Julia iteration | Per-word stability signature in LSH address space |
| `dmj-Magnet1Mandel/Julia` | Renormalization group fixed-point formula from physics — z → ((z²+c-1)/(2z+c-2))² | **Structurally identical to J_N fixed-point problem.** Magnet fractals have a known fixed point at infinity; their basin boundary is the MCR curtain analog |
| `dmj-Magnet2Mandel/Julia` | Higher-order Magnet formula | Same as above, higher spectral resolution |
| `dmj-fBmMandel/Julia` | Fractional Brownian motion overlay on Mandelbrot — adds stochastic noise at each iteration | Noise injection model for SMNNIP training data augmentation |
| `dmj-IMandel` / `dmj-IJulia` | Inversion Mandelbrot — applies 1/z inversion map to parameter space | **Direct J_N implementation.** r → 1/r in complex plane. Use as validation of inversion engine behavior |
| `dmj-HNovaMandel/Julia` | Hypercomplex Nova — Newton's method in hypercomplex (4D) algebra | Octonion address space navigation; extends LSH to 8D |
| `dmj-DoubleMandel/Julia` | Double-precision Mandelbrot with perturbation theory | High-precision address refinement |
| `dmj-BoostMandel/Julia` | Perturbation-boosted iteration | Zoom-stable rendering for deep address spaces |
| `dmj-ManyJulia` | Renders a grid of Julia sets for different c values simultaneously | Parameter space survey — maps the full charset permutation space |
| `dmj-ManyNova` | Same for Nova fractals | Octonion parameter survey |

---

### mt — Mark Townsend (`mt.ufm`)
Diverse formula set emphasizing attractors and dynamical systems.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `mt-attractor-julia` / `mt-attractor-m` | Strange attractor iteration — plots trajectory density | **Direct SMNNIP analog.** Propagation paths through layer stack as attractor trajectories |
| `mt-latoocarfian` | Clifford/Pickover strange attractor: x→sin(ay)+c·cos(ax), y→sin(bx)+d·cos(by) | Alexandria visualization of weight update trajectories in Archimedes/WernickeNetwork |
| `mt-martin` | Martin/Hopalong map — a 2D discrete-time strange attractor | Low-dimensional projection of SMNNIP state space |
| `mt-hopalong` | Barry Martin's Hopalong attractor | Same; useful for visualizing layer 3 (GrammarNeuron) behavior |
| `mt-bifunctional-m/j` | Mandelbrot with two competing functions alternating per iteration | Models two-stroke inversion directly — alternating J_N and recursion strokes |
| `mt-fractalia-1` through `6` | Clifford Pickover chaotic map variants with multiple parameter families | Parameter sweep for SMNNIP coupling constant g |
| `mt-newton-fz-m/j` | Newton's method on f(z) — general root-finding fractal | Root = fixed point; basin = address neighborhood. Maps LSH address basin topology |
| `mt-newton-error-m/j` | Newton iteration with error term retained | Residual tracking — analogous to Noether violation monitoring |
| `mt-magnet-II-m/j` | Second-generation Magnet formula | See dmj-Magnet notes above |
| `mt-pseudo-magnet` | Approximation of Magnet RG formula | Lighter-weight curtain boundary approximation |
| `mt-gen-celtic-m/j` | Celtic Mandelbrot variant using |Re(z²)| | Absolute value folding = inside-out operation on real axis; models spectral folding in HyperWebster layers |
| `CNewtonMset1` | Complex Newton on Mandelbrot parameter | Fixed-point topology of the iteration space itself — meta-level LSH |

---

### mmf — Dave Makin / Makin' Magic Formulas (`mmf.ufm`)
3D solid and hypercomplex extensions.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `MMFm-J3D-Quaternion1` | Julia set in quaternion (4D) algebra — projects to 3D | Quaternion layer of LSH addressing; Cayley-Dickson step 1 |
| `MMFn-J3D-Hypercomplex1` | Julia in hypercomplex 4D algebra | Cayley-Dickson step 2 — path to octonion addressing |
| `MMFo-J3D-Hyperfixed` | Fixed hypercomplex parameter Julia | Stable octonion address visualization |
| `MMFt-Solid3DQuaternions` | Solid rendering of quaternion Julia | Alexandria 3D render of address space neighborhoods |
| `MMFu-Solid3DHypercomplex` | Solid hypercomplex rendering | Same for 8D octonion projections |
| `MMFv-MDerivative/JDerivative` | Derivative-estimated Mandelbrot/Julia — distance estimation method | Distance from boundary = address precision metric; maps HyperWebster confidence radius |
| `MMFr-Solid3DComplex` | 3D lighting on standard complex fractal | Alexandria baseline render |
| `MMFx-FxyGxyM/J` | Two coupled real-function iteration: F(x,y) and G(x,y) simultaneously | Models coupled neuron pairs in LexicalDimensionNeuron layer |
| `MMFa` through `MMFf` | Progressive Mandelbrot/Julia variants with increasing formula complexity | Complexity ladder for SMNNIP layer depth calibration |

---

### lkm — Kerry Mitchell (`lkm.ufm`, `lkm3.ufm`, `lkm-special.ufm`)

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `baker` | Baker's Transformation — fold-and-stretch map on unit square | **Two-stroke map.** Fold = J_N application; stretch = recursion. Direct MCR model |
| `inversions` | Möbius inversion map z → 1/z̄ | Direct J_N analog in complex plane; use to validate inversion engine |
| `triangle-general-mandelbrot/julia` | Triangle inequality coloring — measures orbit distance from triangle inequality bound | Orbit geometry analysis; maps to spectral layer distances in SemanticWord |
| `elliptical-bailout-mandelbrot/julia` | Elliptical rather than circular bailout condition | Anisotropic basin mapping — models asymmetric address neighborhoods |
| `gap-mandelbrot/julia` | Mandelbrot with gap in the iteration — skips certain orbit values | Sparse iteration = missing spectral layers; models incomplete field flagging in HyperWebster |
| `embossed-mandelbrot/julia` | Normal-map surface estimation on fractal boundary | Surface normal = gradient direction in address space; navigation vector |
| `predictor-general-mandelbrot/julia` | Predictor-corrector iteration scheme | Numerical integration model for continuous-time SMNNIP |
| `vortex-2/3/4` | Multi-center gravitational vortex attractors | Multi-fixed-point topology; models competing attractors in WernickeNetwork disambiguation |
| `gravity-2/3/4` | Gravitational N-body attractor maps | N-body = N competing word senses; basin = dominant sense selection |
| `mitch-mandelbrot/julia` | Author's personal Mandelbrot variant | Baseline reference |
| `rational-newton-mandelbrot/julia` | Newton on rational functions p(z)/q(z) | Root structure of ratio functions; models quotient addressing in LSH |

---

### sam — Samuel Monnier (`sam.ufm`)
Iterated function systems and cellular/organic structures.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `KochCurve` / `KochCurvesq` / `KochCurvecir` | Koch curve IFS — recursive boundary subdivision | Self-similar address subdivision; models recursive Horner nesting |
| `SierpinskiTriangleII` / `sierpinskiplane` / `sierpinskimod` | Sierpiński triangle IFS variants | Sparse address space structure; models charset gaps and zero-density regions |
| `trapinski` | Trapping + Sierpiński hybrid | Trap = incomplete field detection in HyperWebster acquisition |
| `TwistMand/Julia` | Twisted Mandelbrot — applies function composition pre-iteration | Function-composed iteration = multi-layer SMNNIP pass |
| `lyap` | Lyapunov exponent map | See dmj-Lyapunov above |
| `cglobesmm/j` | Complex globe projection | Spherical coordinate mapping; octonion surface projection |
| `DMand/DJul` | Derivative Mandelbrot | Distance estimation; address precision |

---

### aho — Andreas Horlacher (`aho.ufm`)

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `N_poly3_J/M` through `N_polyK_J/M` | Newton's method on degree 3 through K polynomials | Root multiplicity = address degeneracy; K-degree = spectral layer count (12 layers → K=12 Newton) |
| `N_sin_J/M`, `N_tan_J/M`, `N_exp_J/M` | Newton on transcendental functions | Transcendental fixed points; models e^π (Hagedorn ceiling) and Lambert W convergence |
| `HRing_J/M` | Ring-structured Julia — annular basins | Ring topology = spectral band separation in SemanticWord 12-layer stack |
| `Lacunary1/3` | Lacunary series fractals — series with gaps in powers | Lacunary = spectral gaps; directly models missing frequency bands in word spectral decomposition |
| `Henon_escape_J/M` | Hénon map escape-time rendering | Hénon strange attractor; 2D discrete map analog of SMNNIP two-layer dynamics |
| `frothy_basin` | Frothy/riddled basin boundary — fractal basin structure | Riddled basins = ambiguous word sense regions; models disambiguation difficulty |
| `aho_Perlin` | Perlin noise fractal | Smooth noise injection; data augmentation baseline |

---

### tma — Tom Martens (`tma.ufm`)
Atom and mandala families.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `MightyAtom` / `MightyAtomMkII` | Pickover-style atom fractal — period-detecting with orbital structure | **Period = spectral tone.** Orbital period maps directly to demotic Unicode tone glyph assignment |
| `GrandAtom01/02` | Extended atom formula families | Higher-order tone assignment |
| `DragonAtom01/02/03` | Dragon-curve influenced atom variants | Dragon curve = space-filling path through address space |
| `mandalaAlpha` through `mandalaZeta` | Mandala symmetry fractals — n-fold rotational symmetry | n-fold symmetry = n-gram structural resonance in lexical layer |
| `*-Julia` variants | Julia set versions of all above | Fixed-c parameter space = fixed charset; Julia mode = single-word deep analysis |

---

### jh — Janet Parke/Javier Hernandez (`jh.ufm`)

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `jh-NovaJulia` / `jh-NovaJuliaRelaxation` | Nova fractal — Newton with relaxation parameter ω: z→z−ω·f(z)/f'(z)+c | Relaxation = learning rate in SMNNIP weight update; Nova basin = convergence basin with tunable step |
| `PerforatedMandelbrot/Julia` | Mandelbrot with interior holes — trap-based perforation | Perforated = sparse address space; models words with missing spectral layers |
| `jh-NovaDuckyMandelbrot/Julia` | Nova + "ducky" perturbation | Perturbed Newton convergence; models noisy fixed-point seeking |
| `jh-gnarlies` | Gnarled/tangled orbit structure | High-entanglement address neighborhoods; complex synonym clusters |

---

### akl — Andreas Lober (`akl.ufm`)
Experimental and pedagogical formulas.

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `agm` / `AGMinsky` | Arithmetic-Geometric Mean iteration — converges to elliptic integral | AGM convergence = fastest-known fixed-point iteration; models φ-convergence rate in LSH |
| `agm_deriv` | Derivative of AGM iteration | Convergence rate analysis |
| `Jouk-Dalinskij` / `Joukowskij-Carr2100` | Joukowsky transform — z + 1/z conformal mapping | **z + 1/z is the two-stroke involution in disguise.** Joukowsky maps circle to airfoil; J_N maps r to 1/r. Same operator family |
| `Ellipinskij` | Elliptic transform variant | Elliptic curve structure; connects to Cayley-Dickson construction |
| `AL0` through `AL21` | Personal experimental series | Parameter sweep archive |

---

### em — Various (`em.ufm`)

| Formula | Math | Ptolemy Use |
|---------|------|-------------|
| `Devaney` | Devaney's z → z² + c/z² — singular perturbation | Singularity at origin = Gravinon pole (r=0 undefined in J_N); Devaney captures pole behavior |
| `Duality` | Dual-parameter iteration | Dual address space; models (word, context) joint addressing |
| `LyapunovMandelbrot` | Lyapunov exponent on Mandelbrot | Stability map of full address space |
| `VectorMandelBrot/Julia` | Vector-field Mandelbrot | Vector field = gradient flow in SMNNIP energy landscape |
| `LogicTurtle` | L-system turtle graphics fractal | L-system = grammar expansion; models GrammarNeuron rule application |

---

## Ptolemy Integration Priority

**Immediate (Alexandria/FractalRenderer.py already exists):**
- `dmj-IMandel/IJulia` — validates J_N inversion behavior visually
- `baker` — two-stroke map direct model
- `dmj-Bifurcation` — MCR phase portrait
- `dmj-Magnet1/2` — curtain boundary topology

**SMNNIP Math (Archimedes):**
- `agm` / `AGMinsky` — fastest fixed-point convergence model
- `Joukowskij` — algebraic cousin of J_N
- `jh-NovaJuliaRelaxation` — tunable learning rate model
- `N_polyK` where K=12 — 12-spectral-layer Newton analog

**HyperWebster (Callimachus):**
- `Lacunary1/3` — spectral gap modeling
- `gap-mandelbrot/julia` — incomplete field flagging geometry
- `frothy_basin` — ambiguous sense region mapping
- `MightyAtom` families — orbital period → spectral tone assignment

**LSH / Octonion (Callimachus/Archimedes):**
- `MMFm-J3D-Quaternion1` — Cayley-Dickson step 1
- `MMFn-J3D-Hypercomplex1` — Cayley-Dickson step 2
- `dmj-HNovaMandel/Julia` — 4D Newton in hypercomplex

**Alexandria Visualization:**
- `mt-attractor-julia/m` — SMNNIP state space portrait
- `mt-latoocarfian` — weight trajectory visualization
- `mandalaAlpha` through `mandalaZeta` — n-gram resonance display
- `MMFt-Solid3DQuaternions` — 3D address space render

---

## Naming Note

The **Mirrored Curtain of Reality** (MCR) as a model name finds direct structural analogs in this formulary:

- Bifurcation diagrams are the **phase portrait of the curtain** — parameter on one axis, stable orbits on the other
- Magnet fractals contain a **renormalization group fixed point** — the same fixed-point-as-address structure as LSH
- The Joukowsky transform `z + 1/z` is the **algebraic twin of J_N** — same inversion structure, different embedding
- Baker's Transformation is the **physical two-stroke map** — fold (J_N) then stretch (recursion)

The fractal geometry was always present in the model. This formulary makes it explicit.

---

*Generated: 2026-05-03 | Ptolemy UF Formulary Index v1.0*
