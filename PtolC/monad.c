/*
 * PtolC/monad.c — C Monad: H_hat_RB field engine.
 *
 * learn()  deepens the beta field.
 * hear()   projects text onto the zero basis (internal, called by speak).
 * speak()  computes J^mu (Noether current) and returns ordered words.
 */

#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <stdio.h>

#include "ptolemy.h"
#include "monad.h"
#include "tokenizer.h"

/* ── Riemann zero generation (mirrors monad.py _generate_zeros) ───────────── */

static const double _EXACT_ZEROS[20] = {
    14.134725, 21.022040, 25.010858, 30.424876, 32.935062,
    37.586178, 40.918719, 43.327073, 48.005151, 49.773832,
    52.970321, 56.446248, 59.347044, 60.831779, 65.112544,
    67.079811, 69.546402, 72.067158, 75.704691, 77.144840,
};

static void generate_zeros(double *z, int N)
{
    int m = (N < 20) ? N : 20;
    for (int i = 0; i < m; i++) z[i] = _EXACT_ZEROS[i];
    if (N <= 20) return;

    double two_pi = 2.0 * M_PI;
    for (int n = 21; n <= N; n++) {
        double t = z[n-2] + (z[n-2] - z[n-3]);
        for (int iter = 0; iter < 30; iter++) {
            if (t < 2.0) t = (double)n * 3.0;
            double nt  = (t / two_pi) * (log(t / two_pi) - 1.0) + 0.875;
            double dnt = log(t / two_pi) / two_pi;
            if (fabs(dnt) < 1e-15) break;
            double dt  = (nt - n) / dnt;
            t -= dt;
            if (fabs(dt) < 1e-4) break;
        }
        z[n-1] = t;
    }
}

/* ── Word addressing (mirrors monad.py _word_coords) ─────────────────────── */

void monad_word_coords(const char *surface, int N, int *idx, double *E)
{
    /* Bijective base-95 Horner accumulation.
     * Chars 32..126 map to positions 1..95.  Result v in [0, inf).
     * Overflow of uint64_t gives consistent truncation for long words. */
    uint64_t v = 0;
    for (const char *p = surface; *p; p++) {
        unsigned char c = (unsigned char)*p;
        int ci = (c >= 32 && c < 127) ? (int)(c - 32 + 1) : 0;
        v = v * 95ULL + (uint64_t)ci;
    }
    if (v > 0) v--;

    /* Golden-ratio hash: seed = (v * phi) mod 1 */
    double seed = fmod((double)v * MONAD_PHI, 1.0);
    if (seed < 0.0) seed += 1.0;

    *idx = (int)(seed * N);
    if (*idx >= N) *idx = N - 1;
    if (*idx < 0)  *idx = 0;

    *E = MONAD_D_STAR + seed * (MONAD_OMEGA_ZS - MONAD_D_STAR);
}

/* ── FNV-1a hash for word strings ─────────────────────────────────────────── */

static uint32_t fnv1a(const char *s)
{
    uint32_t h = 2166136261u;
    while (*s) { h ^= (uint8_t)*s++; h *= 16777619u; }
    return h;
}

/* ── Word map (string → zero_idx) ────────────────────────────────────────── */

int monad_wm_get(const Monad *m, const char *word, int *idx, double *E)
{
    uint32_t h    = fnv1a(word);
    uint32_t mask = (uint32_t)(m->wm_cap - 1);
    uint32_t slot = h & mask;
    for (int i = 0; i < m->wm_cap; i++) {
        WMSlot *s = &m->wm[slot];
        if (!s->key) break;
        if (strcmp(s->key, word) == 0) {
            /* Use stored idx; recompute E from coords for accuracy */
            int   dummy_idx;
            monad_word_coords(word, m->N, &dummy_idx, E);
            *idx = (int)s->idx;
            return 1;
        }
        slot = (slot + 1) & mask;
    }
    monad_word_coords(word, m->N, idx, E);
    return 0;
}

void monad_wm_set(Monad *m, const char *word, uint32_t idx)
{
    /* Rehash at 65% load */
    if (m->wm_size * 100 >= m->wm_cap * 65) {
        int      new_cap = m->wm_cap * 2;
        WMSlot  *new_wm  = calloc(new_cap, sizeof(WMSlot));
        uint32_t mask    = (uint32_t)(new_cap - 1);
        for (int i = 0; i < m->wm_cap; i++) {
            if (!m->wm[i].key) continue;
            uint32_t h = fnv1a(m->wm[i].key);
            uint32_t s = h & mask;
            while (new_wm[s].key) s = (s + 1) & mask;
            new_wm[s] = m->wm[i];
        }
        free(m->wm);
        m->wm     = new_wm;
        m->wm_cap = new_cap;
    }

    uint32_t h    = fnv1a(word);
    uint32_t mask = (uint32_t)(m->wm_cap - 1);
    uint32_t slot = h & mask;
    for (int i = 0; i < m->wm_cap; i++) {
        WMSlot *s = &m->wm[slot];
        if (!s->key) {
            s->key = strdup(word);
            s->idx = idx;
            m->wm_size++;
            return;
        }
        if (strcmp(s->key, word) == 0) {
            s->idx = idx;  /* update */
            return;
        }
        slot = (slot + 1) & mask;
    }
}

/* ── A matrix (sparse, open addressing) ──────────────────────────────────── */

static uint32_t a_key(int i, int j)
{
    /* Normalise i < j, encode as (i<<15)|j (both < 32768). */
    if (i > j) { int t = i; i = j; j = t; }
    return ((uint32_t)i << 15) | (uint32_t)j;
}

void monad_a_add(Monad *m, int i, int j, double delta)
{
    if (i == j) return;
    uint32_t key  = a_key(i, j);
    if (key == 0) return;  /* invalid */

    /* Rehash at 65% load */
    if (m->am_size * 100 >= m->am_cap * 65) {
        int    new_cap = m->am_cap * 2;
        ASlot *new_am  = calloc(new_cap, sizeof(ASlot));
        uint32_t mask  = (uint32_t)(new_cap - 1);
        for (int k = 0; k < m->am_cap; k++) {
            if (m->am[k].key == 0) continue;
            uint32_t s = m->am[k].key & mask;
            while (new_am[s].key) s = (s + 1) & mask;
            new_am[s] = m->am[k];
        }
        free(m->am);
        m->am     = new_am;
        m->am_cap = new_cap;
    }

    uint32_t mask = (uint32_t)(m->am_cap - 1);
    uint32_t slot = key & mask;
    for (int k = 0; k < m->am_cap; k++) {
        ASlot *s = &m->am[slot];
        if (s->key == 0) {
            s->key = key;
            s->val = delta;
            m->am_size++;
            return;
        }
        if (s->key == key) {
            s->val += delta;
            return;
        }
        slot = (slot + 1) & mask;
    }
}

double monad_a_get(const Monad *m, int i, int j)
{
    uint32_t key  = a_key(i, j);
    uint32_t mask = (uint32_t)(m->am_cap - 1);
    uint32_t slot = key & mask;
    for (int k = 0; k < m->am_cap; k++) {
        ASlot *s = &m->am[slot];
        if (s->key == 0) return 0.0;
        if (s->key == key) return s->val;
        slot = (slot + 1) & mask;
    }
    return 0.0;
}

/* ── Lifecycle ────────────────────────────────────────────────────────────── */

Monad *monad_create(int N)
{
    Monad *m = calloc(1, sizeof(Monad));
    m->N                 = N;
    m->ground            = fabs(MONAD_L_GROUND) / N;
    m->emission_threshold = fabs(MONAD_L_GROUND) * 2.0;

    m->zeros = malloc(N * sizeof(double));
    m->beta  = malloc(N * sizeof(double));
    m->age   = calloc(N, sizeof(int));
    m->vocab = calloc(N, sizeof(VocabEntry));

    m->wm_cap = 65536;  /* 64K — grows on demand */
    m->wm     = calloc(m->wm_cap, sizeof(WMSlot));

    m->am_cap = 131072;  /* 128K — grows on demand */
    m->am     = calloc(m->am_cap, sizeof(ASlot));

    return m;
}

void monad_destroy(Monad *m)
{
    if (!m) return;
    free(m->zeros);
    free(m->beta);
    free(m->age);
    free(m->vocab);
    for (int i = 0; i < m->wm_cap; i++)
        if (m->wm[i].key) free(m->wm[i].key);
    free(m->wm);
    free(m->am);
    free(m);
}

void monad_ground_init(Monad *m)
{
    generate_zeros(m->zeros, m->N);
    for (int i = 0; i < m->N; i++) {
        m->beta[i] = m->ground;
        m->age[i]  = 0;
    }
}

/* ── learn() ──────────────────────────────────────────────────────────────── */

void monad_learn(Monad *m, const char *text)
{
    /* Split on sentence boundaries, then tokenise each sentence.
     * Co-activating adjacent tokens couple through A. */

    /* We work sentence by sentence: scan for '.', '!', '?', '\n' */
    const char *p   = text;
    int         len = strlen(text);
    char       *sbuf = malloc(len + 2);

    while (*p) {
        /* collect sentence */
        int slen = 0;
        while (*p && *p != '.' && *p != '!' && *p != '?' && *p != '\n') {
            sbuf[slen++] = *p++;
        }
        if (*p) p++;  /* skip delimiter */
        sbuf[slen] = '\0';
        if (slen == 0) continue;

        int    ntok = 0;
        char **toks = tok_split(sbuf, &ntok);

        /* Parallel arrays for this sentence's activations */
        int    *sidx = malloc(ntok * sizeof(int));
        double *sE   = malloc(ntok * sizeof(double));
        int     nact = 0;

        for (int t = 0; t < ntok; t++) {
            const char *word = toks[t];
            int    idx; double E;

            /* Look up in word map; if absent, compute and insert */
            monad_wm_get(m, word, &idx, &E);  /* sets idx/E via coords if not found */
            monad_wm_set(m, word, (uint32_t)idx);

            /* Deepen beta */
            double nb = m->beta[idx] + E * MONAD_ALPHA_LEARN;
            if (nb > MONAD_BETA_SAT) nb = MONAD_BETA_SAT;
            m->beta[idx] = nb;

            /* Update vocab: highest-E representative per zero wins */
            if (!m->vocab[idx].present || E > m->vocab[idx].E) {
                strncpy(m->vocab[idx].word, word, MAX_WORD_LEN - 1);
                m->vocab[idx].word[MAX_WORD_LEN - 1] = '\0';
                m->vocab[idx].E       = E;
                m->vocab[idx].present = 1;
            }

            sidx[nact] = idx;
            sE[nact]   = E;
            nact++;
            m->word_count++;
        }

        /* Gauge connections: w = E_i*E_j / |gamma_i - gamma_j| */
        for (int i = 0; i < nact; i++) {
            for (int j = i + 1; j < nact; j++) {
                if (sidx[i] == sidx[j]) continue;
                double dist = fabs(m->zeros[sidx[i]] - m->zeros[sidx[j]]);
                if (dist < 1e-4) dist = 1e-4;
                double w = sE[i] * sE[j] / dist;
                monad_a_add(m, sidx[i], sidx[j], w);
            }
        }

        free(sidx);
        free(sE);
        tok_free(toks, ntok);
    }

    free(sbuf);
}

/* ── hear() (internal) ────────────────────────────────────────────────────── */

typedef struct { int idx; double E; } Activation;

static Activation *monad_hear_raw(Monad *m, const char *query, int *n_out)
{
    int    ntok = 0;
    char **toks = tok_split(query, &ntok);
    Activation *act = malloc((ntok + 1) * sizeof(Activation));
    *n_out = 0;
    for (int t = 0; t < ntok; t++) {
        int idx; double E;
        monad_wm_get(m, toks[t], &idx, &E);
        act[(*n_out)].idx = idx;
        act[(*n_out)].E   = E;
        (*n_out)++;
    }
    tok_free(toks, ntok);
    return act;
}

/* ── speak() ──────────────────────────────────────────────────────────────── */

typedef struct { int idx; double J; } JEntry;
static int jcmp(const void *a, const void *b)
{
    double da = ((JEntry *)a)->J;
    double db = ((JEntry *)b)->J;
    return (da < db) ? 1 : (da > db) ? -1 : 0;
}

char *monad_speak(Monad *m, const char *query, int max_tokens)
{
    int n_act = 0;
    Activation *psi;

    if (query && query[0]) {
        psi = monad_hear_raw(m, query, &n_act);
    } else {
        /* Spontaneous emission: top beta zeros */
        int cap = m->N < 200 ? m->N : 200;
        psi = malloc(cap * sizeof(Activation));
        for (int i = 0; i < cap; i++) {
            psi[i].idx = i;
            psi[i].E   = m->vocab[i].present ? m->vocab[i].E : MONAD_D_STAR;
        }
        n_act = cap;
    }

    /* Dense J field */
    double *J = malloc((size_t)m->N * sizeof(double));
    memset(J, 0, (size_t)m->N * sizeof(double));

    /* Primary: J[idx] = beta[idx] * E^2 * recency */
    for (int k = 0; k < n_act; k++) {
        int    idx = psi[k].idx;
        double E   = psi[k].E;
        double w   = exp(-MONAD_LAMBDA * m->age[idx]);
        J[idx] += m->beta[idx] * E * E * w;
    }

    /* Propagate through A (one step, in-place — mirrors Python) */
    for (int k = 0; k < m->am_cap; k++) {
        if (m->am[k].key == 0) continue;
        int    i   = (int)(m->am[k].key >> 15);
        int    j   = (int)(m->am[k].key & 0x7FFF);
        double aw  = m->am[k].val;
        double wi  = exp(-MONAD_LAMBDA * m->age[i]);
        double wj  = exp(-MONAD_LAMBDA * m->age[j]);
        if (J[i] > 0.0)
            J[j] += J[i] * aw * m->beta[j] * wj;
        if (J[j] > 0.0)
            J[i] += J[j] * aw * m->beta[i] * wi;
    }

    /* Collect (idx, J) pairs that have vocab entries */
    int     njv  = 0;
    JEntry *jv   = malloc(m->N * sizeof(JEntry));
    for (int i = 0; i < m->N; i++) {
        if (J[i] > 0.0 && m->vocab[i].present) {
            jv[njv].idx = i;
            jv[njv].J   = J[i];
            njv++;
        }
    }
    qsort(jv, njv, sizeof(JEntry), jcmp);

    /* Build response string */
    int   out_cap = max_tokens * (MAX_WORD_LEN + 1) + 4;
    char *out     = malloc(out_cap);
    out[0] = '\0';
    int written = 0;
    for (int i = 0; i < njv && written < max_tokens; i++) {
        const char *w = m->vocab[jv[i].idx].word;
        if (out[0]) strncat(out, " ", out_cap - strlen(out) - 1);
        strncat(out, w, out_cap - strlen(out) - 1);
        written++;
    }

    /* Advance all ages, reset activated zeros — mirrors _advance_age() */
    for (int i = 0; i < m->N; i++) m->age[i]++;
    for (int k = 0; k < n_act; k++) m->age[psi[k].idx] = 0;

    free(J);
    free(jv);
    free(psi);

    return out;
}

/* ── Diagnostics ──────────────────────────────────────────────────────────── */

void monad_status(const Monad *m, FILE *out)
{
    int vocab_count = 0;
    double deepest = 0.0;
    int    deepest_idx = 0;
    for (int i = 0; i < m->N; i++) {
        if (m->vocab[i].present) vocab_count++;
        if (m->beta[i] > deepest) { deepest = m->beta[i]; deepest_idx = i; }
    }
    fprintf(out,
        "[monad] N=%d  vocab=%d  A_edges=%d  word_count=%d\n"
        "        ground=%.8f  deepest_beta=%.4f (zero #%d γ=%.4f)\n"
        "        wm_load=%d/%d  am_load=%d/%d\n",
        m->N, vocab_count, m->am_size, m->word_count,
        m->ground, deepest, deepest_idx,
        (deepest_idx < m->N) ? m->zeros[deepest_idx] : 0.0,
        m->wm_size, m->wm_cap, m->am_size, m->am_cap);
}

void monad_lookup(const Monad *m, const char *word, FILE *out)
{
    int    idx; double E;
    int    known = monad_wm_get(m, word, &idx, &E);
    double beta  = m->beta[idx];
    double gamma = (idx < m->N) ? m->zeros[idx] : 0.0;
    /* sigma is always 0.5 by Noether forcing */
    fprintf(out,
        "  %-24s → zero #%-6d  γ=%-10.4f  σ=0.5  E=%.4f  β=%.4f  %s\n",
        word, idx, gamma, E, beta, known ? "[known]" : "[new]");
}
