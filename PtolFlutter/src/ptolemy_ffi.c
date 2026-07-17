/*
 * PtolFlutter/src/ptolemy_ffi.c — C FFI bridge implementation.
 *
 * Wraps the Monad API in an opaque handle for Dart/Flutter FFI.
 * g_color and g_self_ref are always 0 in the app context.
 */

#include <stdlib.h>
#include <string.h>
#include "ptolemy_ffi.h"
#include "monad.h"
#include "checkpoint.h"

/* g_color and g_self_ref defined in monad.c — always 0 in app context */

typedef struct { Monad *m; } Handle;

PTOL_EXPORT void *ptolemy_create(int n)
{
    Handle *h = malloc(sizeof(Handle));
    if (!h) return NULL;
    h->m = monad_create(n);
    if (!h->m) { free(h); return NULL; }
    monad_ground_init(h->m);
    return h;
}

PTOL_EXPORT void ptolemy_destroy(void *handle)
{
    if (!handle) return;
    Handle *h = handle;
    monad_destroy(h->m);
    free(h);
}

PTOL_EXPORT int ptolemy_load(void *handle, const char *path)
{
    if (!handle || !path) return -1;
    return checkpoint_load(((Handle *)handle)->m, path);
}

PTOL_EXPORT int ptolemy_save(void *handle, const char *path)
{
    if (!handle || !path) return -1;
    return checkpoint_save(((Handle *)handle)->m, path, 0.0);
}

PTOL_EXPORT void ptolemy_learn(void *handle, const char *text)
{
    if (!handle || !text) return;
    Handle *h = handle;
    monad_learn(h->m, text, 0);
    monad_self_flush(h->m);
}

PTOL_EXPORT void ptolemy_learn_identity(void *handle)
{
    if (!handle) return;
    Handle *h = handle;
    monad_learn_identity(h->m);
    monad_self_flush(h->m);
}

PTOL_EXPORT char *ptolemy_speak(void *handle, const char *query, int max_tokens)
{
    if (!handle) return NULL;
    return monad_speak(((Handle *)handle)->m, query, max_tokens, 0);
}

PTOL_EXPORT void ptolemy_free_string(char *s)
{
    free(s);
}

PTOL_EXPORT int ptolemy_vocab_count(void *handle)
{
    if (!handle) return 0;
    Monad *m = ((Handle *)handle)->m;
    int count = 0;
    for (int i = 0; i < m->N; i++)
        if (m->vocab[i].present) count++;
    return count;
}

PTOL_EXPORT int ptolemy_word_count(void *handle)
{
    if (!handle) return 0;
    return ((Handle *)handle)->m->word_count;
}

PTOL_EXPORT int ptolemy_a_size(void *handle)
{
    if (!handle) return 0;
    return ((Handle *)handle)->m->am_size;
}

PTOL_EXPORT double ptolemy_deepest_beta(void *handle)
{
    if (!handle) return 0.0;
    Monad *m = ((Handle *)handle)->m;
    double max = 0.0;
    for (int i = 0; i < m->N; i++)
        if (m->beta[i] > max) max = m->beta[i];
    return max;
}

PTOL_EXPORT void ptolemy_get_beta_array(void *handle, double *out, int n)
{
    if (!handle || !out || n <= 0) return;
    Monad *m = ((Handle *)handle)->m;
    int count = (n < m->N) ? n : m->N;
    memcpy(out, m->beta, (size_t)count * sizeof(double));
}

PTOL_EXPORT void ptolemy_lookup_word(void *handle, const char *word, double *out)
{
    if (!handle || !word || !out) return;
    Monad *m = ((Handle *)handle)->m;
    int   idx = 0;
    double E  = 0.0;
    monad_word_coords(word, m->N, &idx, &E);
    out[0] = (double)idx;
    out[1] = m->zeros[idx];     /* gamma */
    out[2] = E;
    out[3] = m->beta[idx];
}
