/* ptol_gpu_api.c — The Ptolemy GPU Assembler: one-shot C bootstrap
 * ─────────────────────────────────────────────────────────────────────────────
 * Expose the API. Use it once. The geometry is then in GPU memory.
 *
 * Build:
 *   gcc -O2 -o ptol_gpu  ptol_gpu_api.c  -lGL -lGLFW -ldl
 *
 * GLAD: drop glad.h + glad.c (generated, MIT) beside this file,
 *   then add glad.c to the build and -DGLAD=1 to the flags.
 *   Without GLAD, the raw dlsym loader below is used (Linux only).
 *
 * All open source:
 *   GLFW  — zlib licence
 *   GLAD  — MIT licence (generated)
 *   OpenGL — Khronos specification
 * ─────────────────────────────────────────────────────────────────────────────
 */

#include "ptol_gpu_api.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

/* ── OpenGL loader ────────────────────────────────────────────────────────── */
#ifdef GLAD
#  include "glad.h"
#else
#  define GL_GLEXT_PROTOTYPES
#  include <GL/gl.h>
#  include <GL/glext.h>
#  include <dlfcn.h>
typedef void (*PFNGLGENBUFFERSPROC)(GLsizei, GLuint *);
typedef void (*PFNGLBINDBUFFERPROC)(GLenum, GLuint);
typedef void (*PFNGLBUFFERDATAPROC)(GLenum, GLsizeiptr, const void *, GLenum);
typedef GLuint (*PFNGLCREATESHADERPROC)(GLenum);
typedef void (*PFNGLSHADERSOURCEPROC)(GLuint, GLsizei, const GLchar *const *, const GLint *);
typedef void (*PFNGLCOMPILESHADERPROC)(GLuint);
typedef GLuint (*PFNGLCREATEPROGRAMPROC)(void);
typedef void (*PFNGLATTACHSHADERPROC)(GLuint, GLuint);
typedef void (*PFNGLLINKPROGRAMPROC)(GLuint);
typedef void (*PFNGLUSEPROGRAMPROC)(GLuint);
typedef void (*PFNGLDISPATCHCOMPUTEPROC)(GLuint, GLuint, GLuint);
typedef void (*PFNGLMEMORYBARRIERPROC)(GLbitfield);
typedef void (*PFNGLGETSHADERIVPROC)(GLuint, GLenum, GLint *);
typedef void (*PFNGLGETPROGRAMIVPROC)(GLuint, GLenum, GLint *);
typedef void (*PFNGLGETSHADERINFOLOGPROC)(GLuint, GLsizei, GLsizei *, GLchar *);
typedef void (*PFNGLGETPROGRAMINFOLOGPROC)(GLuint, GLsizei, GLsizei *, GLchar *);
typedef void (*PFNGLUNIFORM1IPROC)(GLint, GLint);
typedef void (*PFNGLUNIFORM1FPROC)(GLint, GLfloat);
typedef void (*PFNGLUNIFORM1FVPROC)(GLint, GLsizei, const GLfloat *);
typedef GLint (*PFNGLGETUNIFORMLOCATIONPROC)(GLuint, const GLchar *);
typedef void (*PFNGLBINDBUFFERBASEPROC)(GLenum, GLuint, GLuint);
typedef void (*PFNGLBUFFERDATAPROC2)(GLenum, GLsizeiptr, const void *, GLenum);
typedef void (*PFNGLGETBUFFERSUBDATAPROC)(GLenum, GLintptr, GLsizeiptr, void *);
typedef void (*PFNGLDELETEPROGRAM)(GLuint);
typedef void (*PFNGLDELETEBUFFERS)(GLsizei, const GLuint *);
typedef void (*PFNGLDELETEVERTEXARRAYS)(GLsizei, const GLuint *);
typedef GLuint (*PFNGLGENVERTEXARRAYS)(GLsizei, GLuint *);
typedef void (*PFNGLDRAWARRAYS)(GLenum, GLint, GLsizei);
typedef void (*PFNGLBINDVERTEXARRAY)(GLuint);

static void *gl_lib;
#  define LOAD(T, name) \
    static T name##_fn = NULL; \
    if (!name##_fn) { \
        void *(*gp)(const char *) = dlsym(gl_lib, "glfwGetProcAddress"); \
        if (gp) name##_fn = (T)gp(#name); \
        if (!name##_fn) name##_fn = (T)dlsym(gl_lib, #name); \
    } \
    T name = name##_fn
#endif /* GLAD */

#include <GLFW/glfw3.h>

/* memcpy-based type pun — avoids strict-aliasing UB */
static inline float int_as_float(int i) {
    float f; memcpy(&f, &i, sizeof(f)); return f;
}

/* ── Constants (see ptol_gpu_api.h) ──────────────────────────────────────── */
const int PTOL_PRIMES[16] = {2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53};
const char *PTOL_DIM_NAMES[16] = {
    "identity","name","reflect","iterate",
    "negate","conjugate","associate","deref",
    "compare","permute","mask","address",
    "hash","encode","project","emit"
};

/* ── Internal state ───────────────────────────────────────────────────────── */
static struct {
    GLFWwindow *window;

    GLuint prog_sed_table;   /* sedenion_table.comp  */
    GLuint prog_sigma_rb;    /* sigma_rb.comp        */
    GLuint prog_null_op;     /* null_operator.comp   */
    GLuint prog_display;     /* vert + frag          */

    GLuint ssbo_sed_sign;    /* table_sign[256]      */
    GLuint ssbo_sed_idx;     /* table_idx[256]       */
    GLuint ssbo_words_fwd;   /* UTF-8 forward bytes  */
    GLuint ssbo_words_bwd;   /* UTF-8 backward bytes */
    GLuint ssbo_sigma_rb;    /* sigma_rb[16]         */
    GLuint ssbo_lio;         /* {I,ZD,O,zd_dist}     */
    GLuint ssbo_noether;     /* {j_red,j_blue,j_product,norm} */

    GLuint vao_display;      /* empty VAO for full-screen triangle */
    int    width, height;
    double t_start;

    /* CPU sedenion table (cached after first use) */
    int   cpu_sed_idx[256];
    int   cpu_sed_sign[256];
    int   cpu_table_ready;
} G;

/* ── Shader loader ────────────────────────────────────────────────────────── */
static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "ptol_gpu: cannot open %s\n", path); return NULL; }
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    rewind(f);
    char *buf = malloc(len + 1);
    if (fread(buf, 1, len, f) != (size_t)len) { free(buf); fclose(f); return NULL; }
    buf[len] = '\0';
    fclose(f);
    return buf;
}

static GLuint compile_shader(GLenum type, const char *src, const char *name) {
    GLuint sh = glCreateShader(type);
    glShaderSource(sh, 1, &src, NULL);
    glCompileShader(sh);
    GLint ok;
    glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetShaderInfoLog(sh, sizeof(log), NULL, log);
        fprintf(stderr, "ptol_gpu: shader %s compile error:\n%s\n", name, log);
        return 0;
    }
    return sh;
}

static GLuint link_compute(const char *shader_dir, const char *comp_name) {
    char path[512];
    snprintf(path, sizeof(path), "%s/%s", shader_dir, comp_name);
    char *src = read_file(path);
    if (!src) return 0;

    GLuint sh = compile_shader(GL_COMPUTE_SHADER, src, comp_name);
    free(src);
    if (!sh) return 0;

    GLuint prog = glCreateProgram();
    glAttachShader(prog, sh);
    glLinkProgram(prog);
    GLint ok;
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetProgramInfoLog(prog, sizeof(log), NULL, log);
        fprintf(stderr, "ptol_gpu: program %s link error:\n%s\n", comp_name, log);
        return 0;
    }
    glDeleteShader(sh);
    return prog;
}

static GLuint link_display(const char *shader_dir) {
    char path_v[512], path_f[512];
    snprintf(path_v, sizeof(path_v), "%s/spectrograph.vert", shader_dir);
    snprintf(path_f, sizeof(path_f), "%s/spectrograph.frag", shader_dir);

    char *src_v = read_file(path_v);
    char *src_f = read_file(path_f);
    if (!src_v || !src_f) { free(src_v); free(src_f); return 0; }

    GLuint sv = compile_shader(GL_VERTEX_SHADER,   src_v, "spectrograph.vert");
    GLuint sf = compile_shader(GL_FRAGMENT_SHADER, src_f, "spectrograph.frag");
    free(src_v); free(src_f);
    if (!sv || !sf) return 0;

    GLuint prog = glCreateProgram();
    glAttachShader(prog, sv);
    glAttachShader(prog, sf);
    glLinkProgram(prog);
    GLint ok;
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[4096];
        glGetProgramInfoLog(prog, sizeof(log), NULL, log);
        fprintf(stderr, "ptol_gpu: display program link error:\n%s\n", log);
        return 0;
    }
    glDeleteShader(sv);
    glDeleteShader(sf);
    return prog;
}

/* ── SSBO helpers ─────────────────────────────────────────────────────────── */
static GLuint make_ssbo(GLsizeiptr size, GLenum usage) {
    GLuint buf;
    glGenBuffers(1, &buf);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf);
    glBufferData(GL_SHADER_STORAGE_BUFFER, size, NULL, usage);
    return buf;
}

/* ── Cayley-Dickson CPU table (for ptol_sed_mul / ptol_null_op) ────────── */

/* The doubling law: (a,b)(c,d) = (ac − d̄b, da + bc̄)
 * For basis elements, conjugate = sign flip on all but e₀.
 * We build the 2×2 → 4×4 → 8×8 → 16×16 table iteratively. */
static void build_cpu_table(void) {
    if (G.cpu_table_ready) return;
    /* Start with ℝ: just e₀ × e₀ = +e₀ */
    int sign[256], idx[256];
    memset(sign, 0, sizeof(sign));
    memset(idx,  0, sizeof(idx));
    sign[0] = 1; idx[0] = 0;   /* e₀ × e₀ = +e₀ */

    /* n = current algebra dimension (1, 2, 4, 8 → 16) */
    for (int n = 1; n <= 8; n <<= 1) {
        /* doubling: (n×n) → (2n)×(2n)
         * Basis layout: e₀..eₙ₋₁ in "left" half, eₙ..e₂ₙ₋₁ in "right" half.
         * Cayley-Dickson: for a,b in 0..n-1:
         *   ea × eb          = sign[a*n+b] * e[idx[a*n+b]]
         *   ea × e(b+n)      = conj-sign *  e(idx[...]+n)
         *   e(a+n) × eb      = sign[b*n+a] * e(idx[b*n+a]+n)
         *   e(a+n) × e(b+n)  = -conj-sign * e(idx[...])
         */
        int n2 = n * 2;
        /* We build into a temporary to avoid overwriting while reading */
        int ts[256], ti[256];
        memset(ts, 0, sizeof(ts)); memset(ti, 0, sizeof(ti));
        for (int a = 0; a < n; a++) {
            for (int b = 0; b < n; b++) {
                int s = sign[a * n + b];
                int i = idx [a * n + b];
                /* conjugate of eₙ basis: e₀ stays, eₖ (k>0) flips sign */
                int conj_s = (i == 0) ? s : -s;

                /* Block (0,0): ea × eb = same */
                ts[a * n2 + b]         = s;
                ti[a * n2 + b]         = i;

                /* Block (0,1): ea × e(b+n) = conj(eb_result) shifted */
                ts[a * n2 + (b + n)]   = conj_s;
                ti[a * n2 + (b + n)]   = (i == 0) ? n : i + n;

                /* Block (1,0): e(a+n) × eb = conj(ea)× eb, then shift */
                int s10 = sign[b * n + a];
                int i10 = idx [b * n + a];
                ts[(a + n) * n2 + b]   = s10;
                ti[(a + n) * n2 + b]   = (i10 == 0) ? n : i10 + n;

                /* Block (1,1): e(a+n) × e(b+n) = -(ēb × ea) */
                int s11 = sign[b * n + a];
                int i11 = idx [b * n + a];
                ts[(a + n) * n2 + (b + n)] = -s11;
                ti[(a + n) * n2 + (b + n)] = i11;
            }
        }
        /* Copy back the n2×n2 table into the 16×16 buffer */
        for (int a = 0; a < n2; a++)
            for (int b = 0; b < n2; b++) {
                sign[a * 16 + b] = ts[a * n2 + b];
                idx [a * 16 + b] = ti[a * n2 + b];
            }
    }
    memcpy(G.cpu_sed_sign, sign, sizeof(sign));
    memcpy(G.cpu_sed_idx,  idx,  sizeof(idx));
    G.cpu_table_ready = 1;
}

/* ── ptol_gpu_init ────────────────────────────────────────────────────────── */
int ptol_gpu_init(int width, int height, const char *shader_dir) {
    memset(&G, 0, sizeof(G));
    G.width  = width;
    G.height = height;

    /* ── GLFW context ─────────────────────────────────────────────────── */
    if (!glfwInit()) {
        fprintf(stderr, "ptol_gpu: glfwInit failed\n");
        return 1;
    }
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_VISIBLE, GLFW_TRUE);

    G.window = glfwCreateWindow(width, height,
                                "Ptolemy — Σ_RB Spectrograph", NULL, NULL);
    if (!G.window) {
        fprintf(stderr, "ptol_gpu: glfwCreateWindow failed\n");
        glfwTerminate();
        return 1;
    }
    glfwMakeContextCurrent(G.window);

#ifdef GLAD
    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        fprintf(stderr, "ptol_gpu: GLAD init failed\n");
        return 1;
    }
#else
    gl_lib = dlopen("libGL.so.1", RTLD_LAZY | RTLD_GLOBAL);
    if (!gl_lib) gl_lib = dlopen("libGL.so", RTLD_LAZY | RTLD_GLOBAL);
#endif

    /* ── Compile shaders ──────────────────────────────────────────────── */
    G.prog_sed_table = link_compute(shader_dir, "sedenion_table.comp");
    G.prog_sigma_rb  = link_compute(shader_dir, "sigma_rb.comp");
    G.prog_null_op   = link_compute(shader_dir, "null_operator.comp");
    G.prog_display   = link_display(shader_dir);

    if (!G.prog_sed_table || !G.prog_sigma_rb ||
        !G.prog_null_op   || !G.prog_display) {
        fprintf(stderr, "ptol_gpu: shader compilation failed\n");
        return 1;
    }

    /* ── Allocate SSBOs ───────────────────────────────────────────────── */
    G.ssbo_sed_sign  = make_ssbo(256 * sizeof(int),   GL_STATIC_DRAW);
    G.ssbo_sed_idx   = make_ssbo(256 * sizeof(int),   GL_STATIC_DRAW);
    G.ssbo_words_fwd = make_ssbo(4096,                GL_DYNAMIC_DRAW);
    G.ssbo_words_bwd = make_ssbo(4096,                GL_DYNAMIC_DRAW);
    G.ssbo_sigma_rb  = make_ssbo(16 * sizeof(float),  GL_DYNAMIC_READ);
    G.ssbo_lio       = make_ssbo(4  * sizeof(float),  GL_DYNAMIC_READ);
    G.ssbo_noether   = make_ssbo(4  * sizeof(float),  GL_DYNAMIC_READ);

    /* ── Generate sedenion multiplication table on GPU ────────────────── */
    /* Run sedenion_table.comp once — 16×16 workgroup, writes table to SSBOs */
    glUseProgram(G.prog_sed_table);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, G.ssbo_sed_sign);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, G.ssbo_sed_idx);
    glDispatchCompute(1, 1, 1);
    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);
    /* The sedenion table is now in GPU SSBO memory. Permanent until shutdown. */

    /* ── Empty VAO for display ────────────────────────────────────────── */
    glGenVertexArrays(1, &G.vao_display);

    /* ── Build CPU table (for ptol_sed_mul / ptol_null_op) ───────────── */
    build_cpu_table();

    G.t_start = glfwGetTime();
    fprintf(stdout, "ptol_gpu: init complete. Sedenion table in GPU memory.\n");
    fprintf(stdout, "ptol_gpu: The geometry is encoded. This file can be discarded.\n");
    return 0;
}

/* ── ptol_gpu_shutdown ────────────────────────────────────────────────────── */
void ptol_gpu_shutdown(void) {
    if (!G.window) return;
    glDeleteProgram(G.prog_sed_table);
    glDeleteProgram(G.prog_sigma_rb);
    glDeleteProgram(G.prog_null_op);
    glDeleteProgram(G.prog_display);
    GLuint bufs[7] = {
        G.ssbo_sed_sign, G.ssbo_sed_idx,
        G.ssbo_words_fwd, G.ssbo_words_bwd,
        G.ssbo_sigma_rb, G.ssbo_lio, G.ssbo_noether
    };
    glDeleteBuffers(7, bufs);
    glDeleteVertexArrays(1, &G.vao_display);
    glfwDestroyWindow(G.window);
    glfwTerminate();
    memset(&G, 0, sizeof(G));
}

/* ── Pack UTF-8 string into uint SSBO (4 bytes per uint) ─────────────────── */
static void upload_words(GLuint ssbo, const char *str, int *n_out) {
    int len = (int)strlen(str);
    *n_out = len;
    /* Pad to next multiple of 4 */
    int padded = (len + 3) & ~3;
    uint8_t *buf = calloc(padded, 1);
    memcpy(buf, str, len);
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo);
    glBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, padded, buf);
    free(buf);
}

/* ── ptol_gpu_run ─────────────────────────────────────────────────────────── */
int ptol_gpu_run(const char    *words_fwd,
                 const char    *words_bwd,
                 float          sigma,
                 PtolGPUResult *result) {
    int n_fwd, n_bwd;
    upload_words(G.ssbo_words_fwd, words_fwd, &n_fwd);
    upload_words(G.ssbo_words_bwd, words_bwd, &n_bwd);
    int n = (n_fwd < n_bwd) ? n_fwd : n_bwd;   /* use shorter length */

    /* ── Σ_RB compute ────────────────────────────────────────────────── */
    glUseProgram(G.prog_sigma_rb);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, G.ssbo_words_fwd);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, G.ssbo_words_bwd);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, G.ssbo_sigma_rb);
    GLint loc_n     = glGetUniformLocation(G.prog_sigma_rb, "u_n");
    GLint loc_sigma = glGetUniformLocation(G.prog_sigma_rb, "u_sigma");
    glUniform1i(loc_n,     n);
    glUniform1f(loc_sigma, sigma);
    glDispatchCompute(1, 1, 1);          /* 16 threads in local group */
    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);

    /* ── NULL operator ────────────────────────────────────────────────── */
    glUseProgram(G.prog_null_op);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, G.ssbo_sigma_rb);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, G.ssbo_lio);
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, G.ssbo_noether);
    glDispatchCompute(1, 1, 1);
    glMemoryBarrier(GL_SHADER_STORAGE_BARRIER_BIT);

    /* ── Readback (non-stalling PBO not needed at this size: just glGetBuffer) */
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, G.ssbo_sigma_rb);
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0,
                       16 * sizeof(float), result->sigma_rb);

    int lio_raw[4];
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, G.ssbo_lio);
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, 4 * sizeof(int), lio_raw);
    result->lio.I       = lio_raw[0];
    result->lio.ZD      = lio_raw[1];
    result->lio.O       = lio_raw[2];
    result->lio.zd_dist = int_as_float(lio_raw[3]);

    float noether_raw[4];
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, G.ssbo_noether);
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, 4 * sizeof(float), noether_raw);
    result->noether.j_red        = noether_raw[0];
    result->noether.j_blue       = noether_raw[1];
    result->noether.j_product    = noether_raw[2];
    result->noether.sigma_rb_norm = noether_raw[3];

    result->sigma_in = sigma;
    return 0;
}

/* ── ptol_gpu_frame ───────────────────────────────────────────────────────── */
int ptol_gpu_frame(const PtolGPUResult *r) {
    if (!G.window || glfwWindowShouldClose(G.window)) return 0;

    glfwPollEvents();
    if (glfwWindowShouldClose(G.window)) return 0;

    double t = glfwGetTime() - G.t_start;

    glViewport(0, 0, G.width, G.height);
    glClear(GL_COLOR_BUFFER_BIT);

    glUseProgram(G.prog_display);

    /* Upload all uniforms */
    glUniform1fv(glGetUniformLocation(G.prog_display, "u_sigma_rb"),
                 16, r->sigma_rb);
    glUniform1i(glGetUniformLocation(G.prog_display, "u_I"),       r->lio.I);
    glUniform1i(glGetUniformLocation(G.prog_display, "u_ZD"),      r->lio.ZD);
    glUniform1i(glGetUniformLocation(G.prog_display, "u_O"),       r->lio.O);
    glUniform1f(glGetUniformLocation(G.prog_display, "u_sigma"),   r->sigma_in);
    glUniform1f(glGetUniformLocation(G.prog_display, "u_time"),    (float)t);
    glUniform1f(glGetUniformLocation(G.prog_display, "u_zd_dist"), r->lio.zd_dist);

    glBindVertexArray(G.vao_display);
    glDrawArrays(GL_TRIANGLES, 0, 3);   /* full-screen triangle */

    glfwSwapBuffers(G.window);
    return 1;
}

/* ── ptol_sed_mul (CPU path) ──────────────────────────────────────────────── */
int ptol_sed_mul(int a, int b, int *sign_out) {
    build_cpu_table();
    *sign_out = G.cpu_sed_sign[a * 16 + b];
    return      G.cpu_sed_idx [a * 16 + b];
}

/* ── ptol_sed_zd_check (CPU path) ────────────────────────────────────────── */
int ptol_sed_zd_check(const float x[16]) {
    /* A sedenion x is a zero divisor if ∃ y≠0 such that xy=0.
     * Quick check: compute |x|² and test if x lies in a known ZD family.
     * The canonical ZD basis pairs: (e₁₀−e₁₂)×(e₄+e₁₃) = 0, etc.
     * For a full production check, test multiplication against a ZD probe.
     * Here we use the norm-and-product test: if |x|=0 trivially, skip. */
    float norm2 = 0.0f;
    for (int k = 0; k < 16; k++) norm2 += x[k] * x[k];
    if (norm2 < 1e-12f) return 1;  /* zero is trivially a ZD */

    /* Test against the canonical first ZD probe:
     * y = (e₁₀ - e₁₂) / √2 — the simplest non-trivial ZD partner */
    float y[16] = {0};
    y[10] =  0.70710678f;
    y[12] = -0.70710678f;

    /* Compute product z = x*y using CPU table */
    build_cpu_table();
    float z[16] = {0};
    for (int a = 0; a < 16; a++) {
        if (fabsf(x[a]) < 1e-12f) continue;
        for (int b = 0; b < 16; b++) {
            if (fabsf(y[b]) < 1e-12f) continue;
            int sgn  = G.cpu_sed_sign[a * 16 + b];
            int ridx = G.cpu_sed_idx [a * 16 + b];
            z[ridx] += (float)sgn * x[a] * y[b];
        }
    }
    float znorm2 = 0.0f;
    for (int k = 0; k < 16; k++) znorm2 += z[k] * z[k];
    return (znorm2 < 1e-10f * norm2) ? 1 : 0;
}

/* ── ptol_null_op (CPU path) ──────────────────────────────────────────────── */
PtolLIO ptol_null_op(const float sigma_rb[16]) {
    PtolLIO lio;
    float min_v   = sigma_rb[0];
    float max_v   = sigma_rb[0];
    float min_abs = fabsf(sigma_rb[0]);
    lio.I = lio.ZD = lio.O = 0;
    for (int k = 0; k < 16; k++) {
        float v  = sigma_rb[k];
        float av = fabsf(v);
        if (v  < min_v)   { min_v   = v;  lio.I  = k; }
        if (v  > max_v)   { max_v   = v;  lio.O  = k; }
        if (av < min_abs) { min_abs = av; lio.ZD = k; }
    }
    lio.zd_dist = min_abs;
    return lio;
}

/* ── Standalone demo (compiled with -DPTOL_DEMO) ──────────────────────────── */
#ifdef PTOL_DEMO
int main(void) {
    if (ptol_gpu_init(960, 540, "shaders") != 0) return 1;

    /* The Method: use the API once. */
    PtolGPUResult result;
    /* words_fwd = top-β order; words_bwd = reverse */
    const char *fwd = "from boundary to";
    const char *bwd = "to boundary from";
    float sigma = 0.49985f;    /* live BAO value — NOT hardcoded 0.5 */

    ptol_gpu_run(fwd, bwd, sigma, &result);

    printf("\nΣ_RB channels:\n");
    for (int k = 0; k < 16; k++)
        printf("  e%-2d (p=%-2d): %+.6f\n", k, PTOL_PRIMES[k], result.sigma_rb[k]);

    printf("\nL_(I|O) pathway:\n");
    printf("  I  = e%-2d (%s) — DOWN / past / from\n",
           result.lio.I, PTOL_DIM_NAMES[result.lio.I]);
    printf("  ZD = e%-2d (%s) — boundary / crossing  zd_dist=%.6f\n",
           result.lio.ZD, PTOL_DIM_NAMES[result.lio.ZD], result.lio.zd_dist);
    printf("  O  = e%-2d (%s) — UP / future / to\n",
           result.lio.O, PTOL_DIM_NAMES[result.lio.O]);

    printf("\nNoether check (AM=GM at σ=½):\n");
    printf("  J_red   = %.6f\n", result.noether.j_red);
    printf("  J_blue  = %.6f\n", result.noether.j_blue);
    printf("  product = %.6f\n", result.noether.j_product);
    float am = (result.noether.j_red + result.noether.j_blue) * 0.5f;
    printf("  AM-GM gap = %.6f  (zero at σ=½)\n",
           am * am - result.noether.j_product);

    /* Display loop — closes when window is closed */
    printf("\nSpectrograph window open. Close it when you have seen the geometry.\n");
    printf("The geometry is encoded. This file can then be discarded.\n\n");
    while (ptol_gpu_frame(&result)) { /* empty — the window IS the output */ }

    ptol_gpu_shutdown();
    return 0;
}
#endif /* PTOL_DEMO */
