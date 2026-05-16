/*
 * PtolC/monad.h — C Monad struct and API.
 *
 * Implements H_hat_RB field engine: learn(), hear(), speak().
 * speak() is Ptolemy's prerogative — called internally by hear output.
 * External CLI exposes: -l (learn) and -h (hear→speak).
 *
 * Word → zero mapping is identical to Philadelphos/monad.py:
 *   surface → bijective base-95 Horner int n
 *   seed    = fmod(n * φ, 1.0)
 *   idx     = (int)(seed * N)
 *   E       = D_STAR + seed * (OMEGA_ZS - D_STAR)
 */

#ifndef MONAD_H
#define MONAD_H

#include <stdint.h>
#include <stdio.h>
#include "ptolemy.h"

/* ── Data structures ──────────────────────────────────────────────────────── */

/* One entry in the vocab table (one per Riemann zero). */
typedef struct {
    char   word[MAX_WORD_LEN];
    double E;
    int    present;   /* 1 if this zero has been assigned a word */
} VocabEntry;

/* Open-addressing slot for word → zero_idx hash map. */
typedef struct {
    char    *key;     /* malloc'd, NULL = empty */
    uint32_t idx;
} WMSlot;

/* Open-addressing slot for A matrix (i,j) → weight.
 * Key encoding: (i << 15) | j  (both < 25000 < 32768 = 2^15).
 * key == 0 signals empty (impossible for valid i < j pair). */
typedef struct {
    uint32_t key;
    double   val;
} ASlot;

/* The Monad. */
typedef struct {
    int    N;
    double ground;             /* |L_GROUND| / N — pre-linguistic floor */
    double emission_threshold;
    int    word_count;

    double    *zeros;          /* N Riemann zero imaginary parts (γ_k) */
    double    *beta;           /* N β-field values */
    int       *age;            /* N recency counters */
    VocabEntry *vocab;         /* N vocab entries, indexed by zero_idx */

    /* word → zero_idx map */
    WMSlot *wm;
    int     wm_cap;            /* power of 2 */
    int     wm_size;

    /* A matrix: sparse gauge connections */
    ASlot  *am;
    int     am_cap;            /* power of 2 */
    int     am_size;
} Monad;

/* ── Lifecycle ────────────────────────────────────────────────────────────── */

/* Allocate and zero-initialise a Monad for N zeros. */
Monad *monad_create(int N);

/* Release all memory. */
void   monad_destroy(Monad *m);

/* Set β to ground state and generate Riemann zeros. */
void   monad_ground_init(Monad *m);

/* ── Core API ─────────────────────────────────────────────────────────────── */

/* Deepen the β field from text.  Text is discarded after processing. */
void   monad_learn(Monad *m, const char *text);

/* Return malloc'd string of top Noether-current words for query.
 * max_tokens: maximum words in response.
 * Caller owns returned string.  Returns "" (not NULL) on empty field. */
char  *monad_speak(Monad *m, const char *query, int max_tokens);

/* ── Word addressing ──────────────────────────────────────────────────────── */

/* Compute (idx, E) for a surface form.  Pure function, no side effects. */
void   monad_word_coords(const char *surface, int N, int *idx, double *E);

/* Look up word in wm.  Returns 1 and sets idx, E if found.
 * Returns 0 if not found (idx/E set via word_coords). */
int    monad_wm_get(const Monad *m, const char *word, int *idx, double *E);

/* Insert or update word → idx in wm (rehashes if load > 0.65). */
void   monad_wm_set(Monad *m, const char *word, uint32_t idx);

/* ── A matrix ─────────────────────────────────────────────────────────────── */

/* Add delta to A[(i,j)].  i and j are normalised to i<j internally. */
void   monad_a_add(Monad *m, int i, int j, double delta);

/* Get A[(i,j)], 0.0 if absent. */
double monad_a_get(const Monad *m, int i, int j);

/* ── Diagnostics ──────────────────────────────────────────────────────────── */

/* Print status to out. */
void   monad_status(const Monad *m, FILE *out);

/* Print per-word field info for a single surface form. */
void   monad_lookup(const Monad *m, const char *word, FILE *out);

#endif /* MONAD_H */
