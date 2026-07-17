/*
 * PtolC/checkpoint.h — Binary checkpoint loader/saver for the C Monad.
 */

#ifndef CHECKPOINT_H
#define CHECKPOINT_H

#include "monad.h"

/* Load binary checkpoint produced by Callimachus/checkpoint_export.py.
 * Returns 0 on success, -1 on error (prints reason to stderr). */
int checkpoint_load(Monad *m, const char *path);

/* Save current Monad state to binary checkpoint.
 * Skips A entries below min_weight to cap file size.
 * Returns 0 on success, -1 on error. */
int checkpoint_save(const Monad *m, const char *path, double min_weight);

#endif /* CHECKPOINT_H */
