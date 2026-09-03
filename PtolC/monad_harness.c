/* monad_harness.c — the ACTIVE harness. SKELETON.
 *
 * What is real here: the support-line grammar parser and its self-test. Every
 * Python engine and the curses UI reach the Monad core through this file; the
 * SUPPORT harness does not — it leaves structured text in the Chat buffer and
 * mh_parse_support_line() reads it back, Ptolemy's judgement lines included.
 *
 * TODO (next build): frame dispatch (mh_pump), and mh_ingest_support() wired to
 * monad.h (monad_emote / monad_a_add / a priority hook). ptol.c is untouched.
 *
 * Build (standalone self-test):  cc -DMH_SELFTEST monad_harness.c -o mh_test
 */
#include "monad_harness.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ── grammar, shared with ptolemy_console.py ─────────────────────────────────
 *   face post :  « <face> » [ ⚠ ] [<intrusion>] <text>
 *   judgement :  « Ptolemy » judgement [<face>/<intrusion>]: <reason>
 *                -> decision: <DECISION>  action: <action>
 * The « » guillemets are UTF-8 (0xC2 0xAB / 0xC2 0xBB). We match on the ASCII
 * skeleton after them so the parser is encoding-tolerant.
 */

static const char *skip_guillemet(const char *s)
{
    /* step past a leading «  (0xC2 0xAB) and its spaces */
    if ((unsigned char)s[0] == 0xC2 && (unsigned char)s[1] == 0xAB)
        s += 2;
    while (*s == ' ') s++;
    return s;
}

static void copy_field(char *dst, size_t cap, const char *src, size_t n)
{
    if (n >= cap) n = cap - 1;
    memcpy(dst, src, n);
    dst[n] = '\0';
    /* trim trailing spaces */
    while (n && dst[n - 1] == ' ') dst[--n] = '\0';
}

mh_support_kind mh_parse_support_line(const char *line, mh_support_line *out)
{
    memset(out, 0, sizeof(*out));
    out->kind = MH_S_UNKNOWN;
    if (!line) return MH_S_UNKNOWN;

    const char *p = skip_guillemet(line);

    /* PTOLEMY JUDGEMENT ---------------------------------------------------- */
    if (strncmp(p, "Ptolemy", 7) == 0) {
        const char *j = strstr(p, "judgement [");
        if (!j) return MH_S_UNKNOWN;
        j += strlen("judgement [");
        const char *slash = strchr(j, '/');
        const char *rb    = strchr(j, ']');
        if (!slash || !rb || slash > rb) return MH_S_UNKNOWN;
        copy_field(out->face, sizeof(out->face), j, (size_t)(slash - j));
        copy_field(out->intrusion, sizeof(out->intrusion),
                   slash + 1, (size_t)(rb - slash - 1));

        const char *reason = rb + 1;
        while (*reason == ':' || *reason == ' ') reason++;
        const char *arrow = strstr(reason, "-> decision:");
        if (arrow) {
            copy_field(out->text, sizeof(out->text), reason,
                       (size_t)(arrow - reason));
            const char *d = arrow + strlen("-> decision:");
            while (*d == ' ') d++;
            size_t k = 0;
            while (d[k] && d[k] != ' ' && k < sizeof(out->decision) - 1) k++;
            copy_field(out->decision, sizeof(out->decision), d, k);
        } else {
            copy_field(out->text, sizeof(out->text), reason, strlen(reason));
        }
        out->kind = MH_S_PTOLEMY_JUDGEMENT;
        return out->kind;
    }

    /* FACE POST ---------------------------------------------------------------
     * « <face> »  [optional ⚠ / HARDENING]  [<intrusion>]  <text>
     */
    {
        /* face name runs up to the closing »  (0xC2 0xBB) */
        const char *close = p;
        while (*close &&
               !((unsigned char)close[0] == 0xC2 && (unsigned char)close[1] == 0xBB))
            close++;
        if (!*close) return MH_S_UNKNOWN;
        copy_field(out->face, sizeof(out->face), p, (size_t)(close - p));

        const char *rest = close + 2;
        while (*rest == ' ') rest++;
        /* an optional [<intrusion>] tag */
        if (*rest == '[') {
            const char *rb = strchr(rest, ']');
            if (rb) {
                copy_field(out->intrusion, sizeof(out->intrusion),
                           rest + 1, (size_t)(rb - rest - 1));
                rest = rb + 1;
                while (*rest == ' ') rest++;
            }
        }
        copy_field(out->text, sizeof(out->text), rest, strlen(rest));
        out->kind = MH_S_FACE_POST;
        return out->kind;
    }
}

int mh_ingest_support(struct Monad_ *m, const mh_support_line *sl)
{
    (void)m;
    /* TODO: wire to monad.h —
     *   HARDEN / THROTTLE  -> a supervisor-priority / intake-throttle hook
     *   ESCALATE           -> raise the diagnostic weight
     *   DEFER              -> no core change (Archimedes handled it)
     *   FACE_POST warn     -> monad_emote(m, +small) on repeated territory
     * For now: classify and log.
     */
    if (!sl) return -1;
    fprintf(stderr, "[mh] ingest %s face=%s intr=%s dec=%s\n",
            sl->kind == MH_S_PTOLEMY_JUDGEMENT ? "judgement"
            : sl->kind == MH_S_FACE_POST       ? "face-post" : "unknown",
            sl->face, sl->intrusion, sl->decision);
    return 0;
}

/* ── frame loop — TODO ──────────────────────────────────────────────────── */
struct mh_harness { int in_fd, out_fd; };

mh_harness *mh_open(int in_fd, int out_fd)
{
    mh_harness *h = calloc(1, sizeof *h);
    if (h) { h->in_fd = in_fd; h->out_fd = out_fd; }
    return h;
}
void mh_close(mh_harness *h) { free(h); }

int mh_pump(mh_harness *h, int timeout_ms)
{
    (void)h; (void)timeout_ms;
    /* TODO: read one frame, dispatch (TOOL/ENGINE/RENDER), write RESULT;
     * then drain the Chat buffer through mh_parse_support_line +
     * mh_ingest_support. */
    return 0;
}

#ifdef MH_SELFTEST
int main(void)
{
    const char *samples[] = {
        "\xC2\xAB Ptolemy \xC2\xBB judgement [Aule/backlog]: drift 0.72 >= 0.60,"
        " hardening from Aule -> decision: HARDEN  action: apply the proposed"
        " adjustment",
        "\xC2\xAB Aule \xC2\xBB [backlog] the Forge is throttling intake until"
        " backlog clears",
        "\xC2\xAB Mandos \xC2\xBB nominal (drift 0.10)",
    };
    int ok = 1;
    mh_support_line sl;
    mh_support_kind k;

    k = mh_parse_support_line(samples[0], &sl);
    ok &= (k == MH_S_PTOLEMY_JUDGEMENT);
    ok &= (strcmp(sl.face, "Aule") == 0);
    ok &= (strcmp(sl.intrusion, "backlog") == 0);
    ok &= (strcmp(sl.decision, "HARDEN") == 0);
    printf("judgement: face=%s intr=%s dec=%s  reason=\"%.40s...\"\n",
           sl.face, sl.intrusion, sl.decision, sl.text);

    k = mh_parse_support_line(samples[1], &sl);
    ok &= (k == MH_S_FACE_POST);
    ok &= (strcmp(sl.face, "Aule") == 0);
    ok &= (strcmp(sl.intrusion, "backlog") == 0);
    printf("face-post: face=%s intr=%s  text=\"%.40s...\"\n",
           sl.face, sl.intrusion, sl.text);

    k = mh_parse_support_line(samples[2], &sl);
    ok &= (k == MH_S_FACE_POST) && (strcmp(sl.face, "Mandos") == 0);
    printf("face-post: face=%s (no intrusion)\n", sl.face);

    printf("%s\n", ok ? "mh selftest: HOLDS" : "mh selftest: FAIL");
    return ok ? 0 : 1;
}
#endif
