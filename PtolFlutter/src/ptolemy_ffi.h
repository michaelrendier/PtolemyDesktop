/*
 * PtolFlutter/src/ptolemy_ffi.h — C FFI bridge for Flutter/Dart.
 *
 * Exposes the Monad engine through an opaque handle API.
 * All strings returned by ptolemy_speak() must be freed with ptolemy_free_string().
 * Thread safety: single-threaded. All calls from same Dart isolate.
 */

#ifndef PTOLEMY_FFI_H
#define PTOLEMY_FFI_H

#include <stdint.h>

#ifdef _WIN32
#  define PTOL_EXPORT __declspec(dllexport)
#else
#  define PTOL_EXPORT __attribute__((visibility("default"))) __attribute__((used))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Lifecycle */
PTOL_EXPORT void *ptolemy_create(int n);
PTOL_EXPORT void  ptolemy_destroy(void *handle);

/* Checkpoint */
PTOL_EXPORT int   ptolemy_load(void *handle, const char *path);
PTOL_EXPORT int   ptolemy_save(void *handle, const char *path);

/* Core API */
PTOL_EXPORT void  ptolemy_learn(void *handle, const char *text);
PTOL_EXPORT void  ptolemy_learn_identity(void *handle);
PTOL_EXPORT char *ptolemy_speak(void *handle, const char *query, int max_tokens);
PTOL_EXPORT void  ptolemy_free_string(char *s);

/* Status */
PTOL_EXPORT int    ptolemy_vocab_count(void *handle);
PTOL_EXPORT int    ptolemy_word_count(void *handle);
PTOL_EXPORT int    ptolemy_a_size(void *handle);
PTOL_EXPORT double ptolemy_deepest_beta(void *handle);

/* β field array — caller allocates out[n], n <= 25000 */
PTOL_EXPORT void ptolemy_get_beta_array(void *handle, double *out, int n);

/* Per-word lookup: writes zero_idx, gamma, E, beta to out[4] */
PTOL_EXPORT void ptolemy_lookup_word(void *handle, const char *word, double *out);

#ifdef __cplusplus
}
#endif

#endif /* PTOLEMY_FFI_H */
