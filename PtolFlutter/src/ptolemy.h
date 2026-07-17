/*
 * PtolC/ptolemy.h — Shared constants for the C Monad.
 *
 * All values mirror Philadelphos/monad.py exactly.
 * Do not change these without changing the Python source.
 */

#ifndef PTOLEMY_H
#define PTOLEMY_H

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define MONAD_N_DEFAULT      25000
#define MONAD_L_GROUND      (-1.888)
#define MONAD_D_STAR         0.24600
#define MONAD_OMEGA_ZS       0.56714
#define MONAD_PHI            1.6180339887498948482
#define MONAD_ALPHA_LEARN    0.01
#define MONAD_LAMBDA         0.05
#define MONAD_TAU            5.0

/* β_sat = |L_GROUND| * 4 */
#define MONAD_BETA_SAT       7.552

/* Emission threshold = |L_GROUND| * 2 */
#define MONAD_EMIT_THRESH    3.776

/* Max word/token byte length stored in vocab */
#define MAX_WORD_LEN         256

/* Binary checkpoint magic and version */
#define CKPT_MAGIC           "PTOL"
#define CKPT_VERSION         1

/* ANSI colour codes — used when stderr/stdout is a tty */
#define C_RESET    "\033[0m"
#define C_BOLD     "\033[1m"
#define C_DIM      "\033[2m"
#define C_YELLOW   "\033[33m"   /* learn()  */
#define C_CYAN     "\033[36m"   /* hear()   */
#define C_GREEN    "\033[32m"   /* speak()  */
#define C_MAGENTA  "\033[35m"   /* J^mu propagation */
#define C_WHITE    "\033[97m"   /* numbers  */

#endif /* PTOLEMY_H */
