/* monad_harness.c — the seam ptol.c crosses to drive the Python tabbed curses
 * UI. Grown from the PtolemyDesktop skeleton: the support-line grammar parser
 * is unchanged; the frame link (mh_open/mh_recv/mh_send_chat) is real, a
 * newline-delimited JSON transport matching PtolemyDesktop/console_link.py.
 *
 * mh_pump()/mh_ingest_support() are now real too -- the beginning of the
 * PtolemyDesktop Event Handler for the monad. Everything here still routes
 * through the one Monad the caller owns (monad_create() in ptol.c): Ptolemy
 * is the Monad + Harness together, so a support line folds into the SAME
 * core the resident console already speaks through, never a side channel.
 * The bus function (general pub/sub beyond this one "radio" frame type) is
 * deliberately deferred -- not built here.
 *
 * Build (standalone self-test):  cc -DMH_SELFTEST monad_harness.c monad.c -o mh_test -lm
 */
#include "monad_harness.h"
#include "monad.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <poll.h>

/* ── grammar, shared with ptolemy_console.py ─────────────────────────────────
 *   face post :  « <face> » [ ⚠ ] [<intrusion>] <text>
 *   judgement :  « Ptolemy » judgement [<face>/<intrusion>]: <reason>
 *                -> decision: <DECISION>  action: <action>
 * The « » guillemets are UTF-8 (0xC2 0xAB / 0xC2 0xBB). We match on the ASCII
 * skeleton after them so the parser is encoding-tolerant.
 */

static const char *skip_guillemet(const char *s)
{
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

    /* FACE POST ------------------------------------------------------------- */
    {
        const char *close = p;
        while (*close &&
               !((unsigned char)close[0] == 0xC2 && (unsigned char)close[1] == 0xBB))
            close++;
        if (!*close) return MH_S_UNKNOWN;
        copy_field(out->face, sizeof(out->face), p, (size_t)(close - p));

        const char *rest = close + 2;
        while (*rest == ' ') rest++;
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

int mh_ingest_support(void *monad, const mh_support_line *sl)
{
    if (!sl) return -1;
    Monad *m = (Monad *)monad;

    fprintf(stderr, "[mh] ingest %s face=%s intr=%s dec=%s\n",
            sl->kind == MH_S_PTOLEMY_JUDGEMENT ? "judgement"
            : sl->kind == MH_S_FACE_POST       ? "face-post" : "unknown",
            sl->face, sl->intrusion, sl->decision);

    if (!m) return 0;      /* classify + log only, no core to fold into */

    if (sl->kind == MH_S_PTOLEMY_JUDGEMENT) {
        if (strcmp(sl->decision, "HARDEN") == 0 ||
            strcmp(sl->decision, "THROTTLE") == 0) {
            monad_emote(m, 0.15f);            /* supervisor-priority hook */
        } else if (strcmp(sl->decision, "ESCALATE") == 0) {
            monad_emote(m, 0.35f);            /* raise the diagnostic weight */
        }
        /* DEFER / HOLD: no core change, on purpose. */
    } else if (sl->kind == MH_S_FACE_POST && sl->intrusion[0] != '\0') {
        monad_emote(m, 0.05f);                /* a warn, +small */
    }
    return 0;
}

/* ── tiny JSON — only what the frame protocol needs ─────────────────────────
 * The console (console_link.py) is the only writer on the wire; we scan for a
 * key and read a JSON string or a bare token. Not a general parser.
 */
static int json_str(const char *buf, const char *key, char *out, size_t cap)
{
    char pat[40];
    snprintf(pat, sizeof(pat), "\"%s\"", key);
    const char *p = strstr(buf, pat);
    if (!p) { if (cap) out[0] = '\0'; return 0; }
    p += strlen(pat);
    while (*p == ' ' || *p == ':' || *p == '\t') p++;
    size_t o = 0;
    if (*p == '"') {
        p++;
        while (*p && *p != '"' && o < cap - 1) {
            if (*p == '\\' && p[1]) {
                p++;
                switch (*p) {
                    case 'n': out[o++] = '\n'; break;
                    case 't': out[o++] = '\t'; break;
                    case 'r': out[o++] = '\r'; break;
                    case 'b': out[o++] = '\b'; break;
                    case 'f': out[o++] = '\f'; break;
                    case '/': out[o++] = '/';  break;
                    case '"': out[o++] = '"';  break;
                    case '\\': out[o++] = '\\'; break;
                    case 'u': {   /* \uXXXX — pass the BMP codepoint as UTF-8 */
                        if (p[1] && p[2] && p[3] && p[4]) {
                            char hx[5] = { p[1], p[2], p[3], p[4], 0 };
                            unsigned cp = (unsigned)strtol(hx, NULL, 16);
                            p += 4;
                            if (cp < 0x80 && o < cap - 1) {
                                out[o++] = (char)cp;
                            } else if (cp < 0x800 && o < cap - 2) {
                                out[o++] = (char)(0xC0 | (cp >> 6));
                                out[o++] = (char)(0x80 | (cp & 0x3F));
                            } else if (o < cap - 3) {
                                out[o++] = (char)(0xE0 | (cp >> 12));
                                out[o++] = (char)(0x80 | ((cp >> 6) & 0x3F));
                                out[o++] = (char)(0x80 | (cp & 0x3F));
                            }
                        }
                        break;
                    }
                    default: out[o++] = *p; break;
                }
                p++;
            } else {
                out[o++] = *p++;
            }
        }
        out[o] = '\0';
        return 1;
    }
    /* bare token (number / true / false / null) */
    while (*p && *p != ',' && *p != '}' && *p != ' ' && o < cap - 1)
        out[o++] = *p++;
    out[o] = '\0';
    return o > 0;
}

static void json_escape(const char *in, char *out, size_t cap)
{
    size_t o = 0;
    for (const char *p = in; *p && o < cap - 7; p++) {
        unsigned char c = (unsigned char)*p;
        switch (c) {
            case '"':  out[o++] = '\\'; out[o++] = '"';  break;
            case '\\': out[o++] = '\\'; out[o++] = '\\'; break;
            case '\n': out[o++] = '\\'; out[o++] = 'n';  break;
            case '\r': out[o++] = '\\'; out[o++] = 'r';  break;
            case '\t': out[o++] = '\\'; out[o++] = 't';  break;
            default:
                if (c < 0x20) { o += (size_t)snprintf(out + o, cap - o, "\\u%04x", c); }
                else          { out[o++] = (char)c; }
        }
    }
    out[o] = '\0';
}

/* ── the frame link ──────────────────────────────────────────────────────── */
struct mh_harness {
    int  in_fd, out_fd;
    char rbuf[MH_FRAME_MAX + 4096];
    size_t rlen;
};

mh_harness *mh_open(int in_fd, int out_fd)
{
    mh_harness *h = calloc(1, sizeof *h);
    if (h) { h->in_fd = in_fd; h->out_fd = out_fd; h->rlen = 0; }
    return h;
}
void mh_close(mh_harness *h) { free(h); }

static int wr_all(int fd, const char *b, size_t n)
{
    while (n) {
        ssize_t w = write(fd, b, n);
        if (w < 0) { if (errno == EINTR) continue; return -1; }
        b += w; n -= (size_t)w;
    }
    return 0;
}

int mh_send_raw(mh_harness *h, const char *json_line)
{
    if (!h) return -1;
    size_t n = strlen(json_line);
    if (wr_all(h->out_fd, json_line, n) != 0) return -1;
    if (n == 0 || json_line[n - 1] != '\n')
        if (wr_all(h->out_fd, "\n", 1) != 0) return -1;
    return 0;
}

int mh_send_chat(mh_harness *h, long id, const char *text,
                 double sigma, double gamma,
                 const char *primes, const char *mode)
{
    char etext[MH_FRAME_MAX * 2];
    char eprimes[512];
    json_escape(text ? text : "", etext, sizeof(etext));
    json_escape(primes ? primes : "", eprimes, sizeof(eprimes));

    char line[MH_FRAME_MAX * 2 + 1024];
    int n = snprintf(line, sizeof(line),
        "{\"t\":\"chat\",\"who\":\"monad\",\"id\":%ld,\"text\":\"%s\","
        "\"sigma\":%.6f,\"gamma\":%.6f,\"primes\":\"%s\",\"mode\":\"%s\"}",
        id, etext, sigma, gamma, eprimes, mode ? mode : "sentence");
    if (n < 0 || (size_t)n >= sizeof(line)) return -1;
    return mh_send_raw(h, line);
}

/* pull one '\n'-terminated line out of the ring, refilling from in_fd */
int mh_recv(mh_harness *h, mh_frame *out, int timeout_ms)
{
    if (!h || !out) return -1;
    memset(out, 0, sizeof(*out));
    out->id = -1;

    for (;;) {
        char *nl = memchr(h->rbuf, '\n', h->rlen);
        if (nl) {
            size_t linelen = (size_t)(nl - h->rbuf);
            char line[MH_FRAME_MAX + 4096];
            if (linelen >= sizeof(line)) linelen = sizeof(line) - 1;
            memcpy(line, h->rbuf, linelen);
            line[linelen] = '\0';
            /* consume, including the newline */
            size_t consumed = (size_t)(nl - h->rbuf) + 1;
            memmove(h->rbuf, h->rbuf + consumed, h->rlen - consumed);
            h->rlen -= consumed;

            if (linelen == 0) continue;   /* blank keep-alive */
            json_str(line, "t", out->t, sizeof(out->t));
            if (out->t[0] == '\0') strncpy(out->t, "noop", sizeof(out->t) - 1);
            /* body: `say`/`cmd` use "text", console `/cmd` frames use "line" */
            if (!json_str(line, "text", out->text, sizeof(out->text)))
                json_str(line, "line", out->text, sizeof(out->text));
            json_str(line, "mode", out->mode, sizeof(out->mode));
            char idbuf[32];
            if (json_str(line, "id", idbuf, sizeof(idbuf)) && idbuf[0])
                out->id = strtol(idbuf, NULL, 10);
            return 1;
        }

        if (h->rlen >= MH_FRAME_MAX) {       /* overlong, no newline — drop */
            h->rlen = 0;
            strncpy(out->t, "error", sizeof(out->t) - 1);
            return 1;
        }

        if (timeout_ms >= 0) {
            struct pollfd pfd = { h->in_fd, POLLIN, 0 };
            int pr = poll(&pfd, 1, timeout_ms);
            if (pr == 0) return 0;
            if (pr < 0) { if (errno == EINTR) continue; return -1; }
        }
        ssize_t r = read(h->in_fd, h->rbuf + h->rlen,
                         sizeof(h->rbuf) - h->rlen);
        if (r == 0) return -1;              /* peer closed */
        if (r < 0) { if (errno == EINTR) continue; return -1; }
        h->rlen += (size_t)r;
    }
}

int mh_pump(mh_harness *h, void *monad, mh_frame *out, int timeout_ms)
{
    for (;;) {
        int g = mh_recv(h, out, timeout_ms);
        if (g <= 0) return g;                 /* timeout or EOF/error, as-is */

        if (strcmp(out->t, "radio") == 0) {
            mh_support_line sl;
            mh_parse_support_line(out->text, &sl);
            mh_ingest_support(monad, &sl);
            continue;                          /* consumed; wait for the next frame */
        }
        return 1;                              /* an ordinary frame for the caller */
    }
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

    /* frame round-trip over a socketpair-like pair of pipes */
    {
        int a[2], b[2];
        if (pipe(a) == 0 && pipe(b) == 0) {
            mh_harness *h = mh_open(a[0], b[1]);
            const char *in =
                "{\"t\":\"say\",\"id\":7,\"text\":\"hello \\\"there\\\"\\nfriend\"}\n";
            if (wr_all(a[1], in, strlen(in))) { /* ignore */ }
            mh_frame fr;
            int g = mh_recv(h, &fr, 200);
            ok &= (g == 1) && (strcmp(fr.t, "say") == 0) && (fr.id == 7);
            ok &= (strstr(fr.text, "there") != NULL) && (strchr(fr.text, '\n') != NULL);
            printf("frame: t=%s id=%ld text=\"%.30s\"\n", fr.t, fr.id, fr.text);
            mh_send_chat(h, fr.id, "one two three", 0.5, 0.0, "2 3 5", "sentence");
            char rl[512];
            ssize_t rn = read(b[0], rl, sizeof(rl) - 1);
            if (rn > 0) {
                rl[rn] = '\0';
                ok &= (strstr(rl, "\"t\":\"chat\"") != NULL);
                ok &= (strstr(rl, "\"id\":7") != NULL);
                printf("reply: %.70s...\n", rl);
            } else ok = 0;
            mh_close(h);
        }
    }

    /* mh_pump: a "radio" frame must be consumed transparently (never handed
     * to the caller) and fold into the Monad's affect via mh_ingest_support;
     * the "say" frame right behind it must still come through untouched. */
    {
        int a[2], b[2];
        if (pipe(a) == 0 && pipe(b) == 0) {
            mh_harness *h = mh_open(a[0], b[1]);
            Monad *m = monad_create(64);
            float before = m ? m->affect : 0.0f;

            const char *radio =
                "{\"t\":\"radio\",\"text\":\"\xC2\xAB Ptolemy \xC2\xBB judgement "
                "[Aule/backlog]: drift high -> decision: HARDEN  action: apply\"}\n";
            const char *say = "{\"t\":\"say\",\"id\":9,\"text\":\"hello\"}\n";
            if (wr_all(a[1], radio, strlen(radio))) { /* ignore */ }
            if (wr_all(a[1], say, strlen(say))) { /* ignore */ }

            mh_frame fr;
            int g = mh_pump(h, m, &fr, 200);
            ok &= (g == 1) && (strcmp(fr.t, "say") == 0) && (fr.id == 9);
            ok &= (m != NULL) && (m->affect > before);
            printf("pump: radio consumed, next frame t=%s id=%ld, "
                   "affect %.3f -> %.3f\n", fr.t, fr.id, before, m ? m->affect : 0.0f);

            if (m) monad_destroy(m);
            mh_close(h);
        }
    }

    printf("%s\n", ok ? "mh selftest: HOLDS" : "mh selftest: FAIL");
    return ok ? 0 : 1;
}
#endif
