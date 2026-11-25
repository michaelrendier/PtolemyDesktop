/* monad_harness.h — the seam ptol.c crosses to drive the Python tabbed
 * curses UI (PtolemyDesktop/ptolemy_console.py).
 *
 * Two inputs, unchanged from the PtolemyDesktop skeleton this is grown from:
 *   1. FRAMES  — newline-delimited JSON over a socketpair. `ptol -w` forks the
 *      console onto the tty (curses draws there) and keeps this end: it reads
 *      `say` / `cmd` / `mode` / `ping` / `quit` frames and answers `chat`.
 *   2. SUPPORT TEXT — the support harness never binds to C. It leaves
 *      regularly-structured lines in the Chat buffer; mh_parse_support_line()
 *      reads them back, Ptolemy's judgement lines included.
 *
 * Frame dispatch (mh_recv / mh_send_chat / mh_send_raw) is real, and so is
 * mh_pump()'s ingest: a "radio" frame's text is parsed as a support line and
 * folded into the Monad via mh_ingest_support(). This is the beginning of
 * the PtolemyDesktop Event Handler for the monad -- the bus function (a
 * general pub/sub beyond this one frame type) is deliberately deferred, not
 * built here.
 *
 * `Monad *` is passed through as `void *` so this header stays standalone
 * (no monad.h dependency) -- monad_harness.c includes monad.h itself and
 * casts back at the point of use.
 */
#ifndef MONAD_HARNESS_H
#define MONAD_HARNESS_H

#include <stddef.h>

/* ── frame kinds ──────────────────────────────────────────────────────────── */
typedef enum {
    MH_F_ATTACH = 0,   /* handshake / status request                          */
    MH_F_STATUS,       /* status reply                                        */
    MH_F_TOOL,         /* a tool-request:  {name, args}                       */
    MH_F_ENGINE,       /* an engine call:  {engine, fn, args}                 */
    MH_F_RENDER,       /* a render request                                    */
    MH_F_RADIO,        /* a passive line for the Chat Tab                     */
    MH_F_RESULT,       /* a reply to TOOL / ENGINE / RENDER                   */
    MH_F_ERROR
} mh_frame_kind;

/* ── support-line kinds (parsed from the Chat buffer) ─────────────────────── */
typedef enum {
    MH_S_UNKNOWN = 0,
    MH_S_FACE_POST,        /* « <face> » [<intrusion>] <text>                  */
    MH_S_PTOLEMY_JUDGEMENT /* « Ptolemy » judgement [<face>/<intrusion>]: ...  */
} mh_support_kind;

typedef struct {
    mh_support_kind kind;
    char face[32];
    char intrusion[32];
    char decision[16];     /* HOLD|THROTTLE|HARDEN|ESCALATE|DEFER, judgement only */
    char text[512];        /* the reason (judgement) or the post body (face)   */
} mh_support_line;

/* Parse one line from the Chat buffer. Returns kind; fills `out`. */
mh_support_kind mh_parse_support_line(const char *line, mh_support_line *out);

/* Fold an ingested support line into the core. `monad` is a `Monad *`
 * (monad.h), passed opaque so this header need not include monad.h.
 * HARDEN/THROTTLE and ESCALATE raise emote (positive = more irritated,
 * ESCALATE the larger step); DEFER/HOLD change nothing; a FACE_POST
 * carrying a non-empty intrusion tag is a warn (+small). Safe to call with
 * monad == NULL (classifies and logs only, same as before this was wired). */
int mh_ingest_support(void *monad, const mh_support_line *sl);

/* ── the frame link ──────────────────────────────────────────────────────── */
#define MH_FRAME_MAX 65536

typedef struct {
    char   t[24];              /* frame type: say|cmd|mode|ping|attach|quit    */
    char   text[MH_FRAME_MAX]; /* say/cmd body                                 */
    char   mode[16];           /* mode frames: "sentence" | "paragraph"        */
    long   id;                 /* correlation id, -1 if none                   */
} mh_frame;

typedef struct mh_harness mh_harness;

mh_harness *mh_open(int in_fd, int out_fd);   /* socketpair end (in==out ok)   */
void        mh_close(mh_harness *h);

/* Block for the next frame (timeout_ms < 0 = forever). Returns 1 = got one,
 * 0 = timed out, -1 = EOF / peer gone / hard error. */
int mh_recv(mh_harness *h, mh_frame *out, int timeout_ms);

/* Answer a say/cmd frame. `primes` is a pre-formatted "2 3 5 ..." string (may
 * be NULL/empty); sigma/gamma go out as numbers; `mode` echoes the current
 * construction mode. Returns 0 on success, -1 on write error. */
int mh_send_chat(mh_harness *h, long id, const char *text,
                 double sigma, double gamma,
                 const char *primes, const char *mode);

/* Write a raw pre-built JSON object line (no trailing newline needed). */
int mh_send_raw(mh_harness *h, const char *json_line);

/* mh_recv, but "radio" frames (a passive support-line for the Chat Tab) are
 * intercepted, parsed, and folded into `monad` via mh_ingest_support before
 * looping for the next frame -- the caller never sees a radio frame, only
 * say/cmd/mode/ping/attach/quit, same as calling mh_recv() directly. `monad`
 * may be NULL (radio frames are still classified and logged, just not
 * folded into any core state). Same 1/0/-1 return contract as mh_recv. */
int mh_pump(mh_harness *h, void *monad, mh_frame *out, int timeout_ms);


/* ═══════════════════════════════════════════════════════════════════════════
 * 2026-11-25: THE HARNESS HEARS.  The C port of the Python harness path tested the same day
 * (numeric.py, state_repass.py, bw_drift.py, conversation_usage.py, prompt_to_state.py's usage meter).
 * Ptolemy is the Monad + Harness together: ptol.c is the Monad (the voice), this is the Harness (the ears).
 * Python is the test bench; every number here is checked against it (tests/test_c_parity.py).
 * ═══════════════════════════════════════════════════════════════════════════ */

/* ── numbers are not words (numeric.py) ─────────────────────────────────────── */
typedef struct {
    char   text[48];
    char   kind[12];      /* integer decimal percent ordinal currency signed code */
    double value;
    int    has_value;     /* 0 for codes (x2, h264, 3.10.3) */
} mh_number;

/* Copy `text` to `out` with every numeral/code/version replaced by one space; fill `nums` (up to maxn). Returns how many were found. */
int mh_split_numbers(const char *text, char *out, size_t outsz, mh_number *nums, int maxn);

/* ── the ears ───────────────────────────────────────────────────────────────── */
enum { MH_EXTERNAL = 0, MH_INTERNAL = 1, MH_DOCUMENT = 2 };
typedef int    (*mh_known_fn)(const char *word, void *ctx);   /* does the Monad know this word (has a WordNet entry)? */
typedef double (*mh_pgen_fn)(const char *word, void *ctx);   /* general-English probability of the word (the prior the user's usage mixes into) */

typedef struct mh_ear mh_ear;
mh_ear *mh_ear_open(const char *state_dir, const char *ptol_dir, mh_known_fn known, mh_pgen_fn pgen, void *ctx);
void    mh_ear_close(mh_ear *e);                 /* saves the usage store and the number counts */

/* Hear one turn (numbers leave first; MH_EXTERNAL = the user, counted and priced; MH_INTERNAL = the monad's own reply, priced, completes the pair and moves
 * the Broca-Wernicke drift; MH_DOCUMENT = nothing counted).  Returns the number of numbers found. */
int     mh_ear_hear(mh_ear *e, const char *text, int cls, const char *pair);

double  mh_ear_lambda(const mh_ear *e);          /* usage confidence N/(N+200) */
double  mh_ear_p_word(const mh_ear *e, const char *w);   /* lambda*(user usage) + (1-lambda)*general */
double  mh_ear_bits_per_word(const mh_ear *e, const char *prose);
double  mh_ear_bw_correction(const mh_ear *e);   /* in [-1, 1]: >0 favour probable words, <0 flatten */
int     mh_ear_n_obs(const mh_ear *e);
int     mh_ear_n_numbers(const mh_ear *e);
void    mh_ear_report(const mh_ear *e, char *out, size_t sz);   /* straight text: the usage, drift and number channels */

/* Pure functions (tested against bw_drift.py): the drift step. state = 0/1 hysteresis flag in/out. */
double  mh_bw_correction(double w_bits, double b_bits, int *active, double *delta_out, double *gamma_abs_out);

/* ── the user's state: the usage meter (a ridge on TF-IDF 1-2 grams, exported by tools/export_c_monad_data.py), the running solution, the repass ── */
#define MH_NAX 7                                  /* OPI GLU GABA DA 5HT NE OXT: the neuro_recipes kite order */
extern const char *const MH_AXES[MH_NAX];
typedef struct {
    double conc[14], spread[14];                  /* the 14 poles, dark then light per axis */
    double mix[MH_NAX], target[MH_NAX];
    int    held, healed, ready;
    double k_eff;
} mh_state;

/* Read one user turn: meter -> solution (C1V1 + C2V2 = C3(V1+V2), Vmax 8) -> heal -> mix -> cancel.  `fill` = how many of the 16 window slots hold a word.
 * ready = 0 when user_state.bin is absent (the state then stays at baseline and is held). */
void    mh_ear_user_turn(mh_ear *e, const char *text, int fill, mh_state *out);
/* The meter alone on one text (no solution, no state change): conc = clip(ridge)*4.5*gain, as ptol's usage-only reading. Returns 0 if no model. */
int     mh_meter_raw(const mh_ear *e, const char *text, double dose[14]);
void    mh_state_heard(const mh_state *s, int *axis, int *level);                 /* the axis farthest from RECEPTIVE and its level 0..6 */
void    mh_state_trajectory(const mh_state *s, int n, int *axis, int *level);     /* meet_then_lead: n (axis, level) steps, user's mix -> target */

#endif /* MONAD_HARNESS_H */
