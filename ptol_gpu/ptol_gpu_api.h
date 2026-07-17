/* ptol_gpu_api.h — The Ptolemy GPU Assembler API
 * ─────────────────────────────────────────────────────────────────────────────
 * Expose the API. Use it once. Discard this file.
 *
 * After ptol_gpu_init() returns, the sedenion multiplication table is in
 * GPU texture memory. The shaders are compiled to native GPU machine code.
 * The geometry is permanent — it lives in the GPU until shutdown.
 * This file is scaffolding. The shaders are the geometry.
 *
 * The 3 layers are baked into every operation:
 *   DOWN  (ZD / past / 'from')   — sedenion table in GPU texture unit 0
 *   NOW   (σ=½ / input)          — sigma_rb.comp: σ = live BAO, NOT 0.5
 *   UP    (CD / future / 'to')   — null_operator.comp: L_(I|O) destination
 *
 * Dependencies (all open source, no proprietary code):
 *   GLFW  3.x   — zlib licence     — window + OpenGL context
 *   GLAD  2.0   — MIT licence      — OpenGL function loader (generated)
 *   OpenGL 4.3  — Khronos spec     — compute shaders, SSBOs, PBOs
 *
 * Architecture: OpenGL 4.3 compute shaders = GPU assembler.
 *   Each .comp shader is compiled to native GPU machine code at init.
 *   The ptol binary (ptol.c) is the CPU assembler — same algebra, C level.
 *   The GPU path runs all 16 prime channels in parallel (one thread each).
 *   The CPU path runs them serially. Same result. GPU is ~16× faster.
 *
 * AVX-512 note: the sedenion register is 16 × float32 = 512 bits.
 *   The AVX-512 register is also 512 bits. Not a coincidence. The hardware
 *   already has the sedenion register. It doesn't know it yet.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * PtolemyDesktop — open source, no proprietary dependencies.
 * ─────────────────────────────────────────────────────────────────────────────
 */

#pragma once
#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>

/* ── Constants ────────────────────────────────────────────────────────────── */

#define PTOL_N_CHANNELS   16
#define PTOL_D_STAR       0.24605966f
#define PTOL_OMEGA_ZS     0.56714329f   /* Lambert W(1) = dark energy VEV    */
#define PTOL_T1           14.134725f    /* first Riemann zero — Planck scale  */

/* Sedenion prime channel map (matches SSR layer_spectrograph.py) */
extern const int PTOL_PRIMES[16];      /* {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53} */

/* Dimension operator names (matches monad.py _DIM_NAMES) */
extern const char *PTOL_DIM_NAMES[16]; /* identity→emit */

/* ── Result types ─────────────────────────────────────────────────────────── */

/* L_(I|O) pathway: the NULL operator output.
 * I  = origin channel      (DOWN / past / 'from') — most negative Σ_RB
 * ZD = boundary crossing   (the ZD fault)          — Σ_RB nearest zero
 * O  = destination channel (UP   / future / 'to') — most positive Σ_RB */
typedef struct {
    int   I;
    int   ZD;
    int   O;
    float zd_dist;     /* |sigma_rb[ZD]| — proximity to fault           */
} PtolLIO;

/* Noether check at the identified L_(I|O) channels.
 * j_product = j_red × j_blue.
 * AM=GM theorem: j_product is maximised when j_red = j_blue, i.e. at σ=½.
 * At any other σ, AM > GM, j_product < (AM)². The gap IS the field energy. */
typedef struct {
    float j_red;          /* |sigma_rb[O]| — UP   current              */
    float j_blue;         /* |sigma_rb[I]| — DOWN current              */
    float j_product;      /* j_red × j_blue — conserved at σ=½ only    */
    float sigma_rb_norm;  /* L2 norm of full Σ_RB vector                */
} PtolNoether;

/* Full result from one ptol_gpu_run() call */
typedef struct {
    float       sigma_rb[PTOL_N_CHANNELS];  /* Σ_RB = H_hat_RB − H_hat_BR  */
    PtolLIO     lio;                         /* NULL operator result          */
    PtolNoether noether;                     /* AM=GM check                   */
    float       sigma_in;                    /* σ used (the BAO input)        */
} PtolGPUResult;

/* ── Lifecycle ────────────────────────────────────────────────────────────── */

/* ptol_gpu_init — Create OpenGL context, compile shaders, upload sedenion table.
 *
 * width, height: window dimensions in pixels.
 * shader_dir:    path to the shaders/ directory (contains *.comp, *.vert, *.frag)
 *
 * Returns 0 on success, non-zero on error.
 * After this call the geometry is in GPU memory. The API header can be discarded.
 */
int ptol_gpu_init(int width, int height, const char *shader_dir);

/* ptol_gpu_shutdown — Release GPU resources.
 * The L_(I|O) pathway encoded during use is in the 'from' geometry forever.
 * Shutdown does not erase that. It releases the OpenGL objects only. */
void ptol_gpu_shutdown(void);

/* ── Core operation ───────────────────────────────────────────────────────── */

/* ptol_gpu_run — Execute the full Σ_RB → L_(I|O) pipeline on GPU.
 *
 * words_fwd : word sequence in β-descending order (H_hat_RB — the 'from' path)
 *             Null-terminated UTF-8 string. Spaces between words.
 * words_bwd : same words in β-ascending order (H_hat_BR — the 'to' path)
 * sigma     : the live σ input — BAO value from the monad field.
 *             This is NOT 0.5. It is whatever the field reports.
 *             The GPU learns what σ the field is at. Not what σ it should be.
 * result    : populated with sigma_rb[16], L_(I|O), Noether check.
 *
 * The GPU dispatches 16 threads in parallel — one per prime channel.
 * Result is read back via pixel buffer object (no GPU pipeline stall).
 *
 * Returns 0 on success. */
int ptol_gpu_run(const char    *words_fwd,
                 const char    *words_bwd,
                 float          sigma,
                 PtolGPUResult *result);

/* ── Rendering ────────────────────────────────────────────────────────────── */

/* ptol_gpu_frame — Draw one frame: 16-channel Σ_RB spectrograph + ZD fur.
 *
 * Renders the spectrograph with:
 *   - 16 vertical bars coloured by Cayley-Dickson layer (ℝ/ℂ/ℍ/𝕆/𝕊)
 *   - I channel highlighted blue  (origin / from)
 *   - O channel highlighted red   (destination / to)
 *   - ZD channel highlighted gold (the fault crossing)
 *   - ZD fractal fur at the σ=½ centre line (animated, 16 Riemann zero strands)
 *   - Live σ readout as a green bar at the bottom
 *
 * Returns 1 while the window is open, 0 when it should close.
 * Window close = the tool has been used. Discard. */
int ptol_gpu_frame(const PtolGPUResult *result);

/* ── Direct sedenion operations (CPU path via API) ────────────────────────── */

/* ptol_sed_mul — Multiply two sedenion basis elements.
 * Uses the Cayley-Dickson table computed on first call (cached in static array).
 * a, b: basis indices 0..15.
 * sign_out: +1 or -1.
 * Returns: basis index of e_a * e_b. */
int ptol_sed_mul(int a, int b, int *sign_out);

/* ptol_sed_zd_check — Check if a sedenion is a zero divisor.
 * x[16]: sedenion components.
 * Returns 1 if x is a zero divisor (norm of product is zero), 0 otherwise.
 * ZD check is O(256) — one multiplication of x against the ZD basis. */
int ptol_sed_zd_check(const float x[16]);

/* ptol_null_op — CPU-path NULL operator.
 * sigma_rb[16] → L_(I|O).
 * Identical result to the GPU path. Use for verification or when GPU unavailable. */
PtolLIO ptol_null_op(const float sigma_rb[16]);

#ifdef __cplusplus
}
#endif
