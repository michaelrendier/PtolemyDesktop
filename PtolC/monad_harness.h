/* monad_harness.h — the ACTIVE harness: the one seam every Python caller and
 * the curses UI cross to reach the Monad core (monad.c / monad.h).
 *
 * Two inputs:
 *   1. FRAMES  — request/response over a pipe (stdio here, a pty when the
 *      console is spawned by PtolemyDesktop). Tool calls, renders, engine
 *      dispatch, state writes.
 *   2. SUPPORT TEXT — the support harness never binds to C. It leaves
 *      regularly-structured lines in the Chat buffer; this harness tails that
 *      buffer and ingests them, including Ptolemy's judgement lines.
 *
 * SKELETON: interfaces + the text ingest are real; frame dispatch and the
 * monad.h calls are marked TODO against the existing core.
 */
#ifndef MONAD_HARNESS_H
#define MONAD_HARNESS_H

#include <stddef.h>

/* the core, from monad.h — forward-declared so this header stands alone */
struct Monad_;

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

/* Fold an ingested support line into the core. TODO: wire to monad.h. */
int mh_ingest_support(struct Monad_ *m, const mh_support_line *sl);

/* ── the run loop (frames) ───────────────────────────────────────────────── */
typedef struct mh_harness mh_harness;

mh_harness *mh_open(int in_fd, int out_fd);   /* stdio: 0,1 ; pty otherwise    */
void        mh_close(mh_harness *h);
int         mh_pump(mh_harness *h, int timeout_ms);  /* one frame + drain chat */

#endif /* MONAD_HARNESS_H */
