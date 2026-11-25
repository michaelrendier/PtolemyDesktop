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
#include <math.h>
#include <ctype.h>
#include <stdint.h>
#include <complex.h>

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

/* ═══════════════════════════════════════════════════════════════════════════
 * THE HARNESS HEARS (2026-11-25) -- see monad_harness.h.  Ported from Python and tested against it.
 * ═══════════════════════════════════════════════════════════════════════════ */

/* BEGIN GENERATED harness_data */
static const char *const VS_STOP[] = {"a","about","above","after","again","against","ain","all","am","an","and","any","are","aren","aren't","as","at","be","because","been","before","being","below","between","both","but","by","can","can't","couldn","couldn't","d","did","didn","didn't","do","does","doesn","doesn't","doing","don","don't","down","during","each","few","for","from","further","had","hadn","hadn't","has","hasn","hasn't","have","haven","haven't","having","he","he'd","he'll","he's","her","here","hers","herself","him","himself","his","how","i","i'd","i'll","i'm","i've","if","in","into","is","isn","isn't","it","it'd","it'll","it's","its","itself","just","ll","m","ma","me","mightn","mightn't","more","most","mustn","mustn't","my","myself","needn","needn't","no","nor","not","now","o","of","off","on","once","only","or","other","our","ours","ourselves","out","over","own","re","s","same","shan","shan't","she","she'd","she'll","she's","should","should've","shouldn","shouldn't","so","some","such","t","than","that","that'll","that's","the","their","theirs","them","themselves","then","there","these","they","they'd","they'll","they're","they've","this","those","through","to","too","under","until","up","ve","very","was","wasn","wasn't","we","we'd","we'll","we're","we've","were","weren","weren't","what","when","where","which","while","who","whom","why","will","with","won","won't","wouldn","wouldn't","y","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"};
static const int N_VS_STOP = 200;
/* END GENERATED harness_data */

/* ── numbers are not words (numeric.py) ───────────────────────────────────── */
static int nw(int c)  { return isalnum(c) || c == '_' || c >= 0x80; }            /* regex \w (non-ASCII bytes count as letters) */
static int nd(int c)  { return c >= '0' && c <= '9'; }
static int a_alnum_(int c) { return isalnum(c) || c == '_'; }                      /* [A-Za-z0-9_] */

static int num_version(const char *s, int n, int i)              /* \b\d+(\.\d+){2,}\b */
{
    if (!nd((unsigned char)s[i]) || (i > 0 && nw((unsigned char)s[i - 1]))) return -1;
    int j = i, ends[40], g = 0;
    while (j < n && nd((unsigned char)s[j])) j++;
    while (j + 1 < n && s[j] == '.' && nd((unsigned char)s[j + 1]) && g < 40) {
        int k = j + 1; while (k < n && nd((unsigned char)s[k])) k++;
        ends[g++] = k; j = k;
    }
    for (; g >= 2; g--) { int e = ends[g - 1]; if (e >= n || !nw((unsigned char)s[e])) return e; }
    return -1;
}

static int num_code(const char *s, int n, int i)                 /* \b[A-Za-z]+\d[A-Za-z0-9]*\b | \b\d+[A-Za-z][A-Za-z0-9]*\b */
{
    if (i > 0 && nw((unsigned char)s[i - 1])) return -1;
    int j = i;
    if (isalpha((unsigned char)s[j])) {
        while (j < n && isalpha((unsigned char)s[j])) j++;
        if (j >= n || !nd((unsigned char)s[j])) return -1;
    } else if (nd((unsigned char)s[j])) {
        while (j < n && nd((unsigned char)s[j])) j++;
        if (j >= n || !isalpha((unsigned char)s[j])) return -1;
    } else return -1;
    j++;
    while (j < n && isalnum((unsigned char)s[j])) j++;
    return (j >= n || !nw((unsigned char)s[j])) ? j : -1;
}

static int suf_len(const char *s, int n, int d)                   /* (%|st|nd|rd|th) at d: its length, 0 if none */
{
    if (d < n && s[d] == '%') return 1;
    if (d + 1 < n && ((s[d] == 's' && s[d + 1] == 't') || (s[d] == 'n' && s[d + 1] == 'd') || (s[d] == 'r' && s[d + 1] == 'd') || (s[d] == 't' && s[d + 1] == 'h'))) return 2;
    return 0;
}

static int num_number(const char *s, int n, int i, mh_number *out)       /* the NUMBER pattern of numeric.py, with its backtracking order */
{
    if (i > 0) { unsigned char p = (unsigned char)s[i - 1]; if (isalnum(p) || p == '_' || p == '.') return -1; }
    int j = i; char sign = 0; int cur = 0;
    if (s[j] == '+' || s[j] == '-') sign = s[j++];
    if (s[j] == '$') { cur = 1; j++; }
    else if (!strncmp(s + j, "\xE2\x82\xAC", 3)) { cur = 1; j += 3; }
    else if (!strncmp(s + j, "\xC2\xA3", 2)) { cur = 1; j += 2; }
    if (j >= n || !nd((unsigned char)s[j])) return -1;
    int is = j, imax = j;
    while (imax < n && (nd((unsigned char)s[imax]) || s[imax] == ',')) imax++;
    for (int ie = imax; ie > is; ie--) {
        int hasdec = (ie + 1 < n && s[ie] == '.' && nd((unsigned char)s[ie + 1]));
        int dmax = ie; if (hasdec) { dmax = ie + 1; while (dmax < n && nd((unsigned char)s[dmax])) dmax++; }
        for (int cand = hasdec ? dmax : ie; cand >= ie; cand--) {          /* with a decimal part (longest first), then without */
            if (cand == ie + 1) continue;                                  /* '.' alone is not a decimal part */
            int de = cand, dec = (cand > ie);
            for (int withsuf = 1; withsuf >= 0; withsuf--) {
                int sl = withsuf ? suf_len(s, n, de) : 0;
                if (withsuf && !sl) continue;
                int e = de + sl;
                if (e < n && a_alnum_((unsigned char)s[e])) continue;
                if (out) {
                    char body[48]; int b = 0;
                    for (int k = is; k < ie && b < 40; k++) if (s[k] != ',') body[b++] = s[k];
                    for (int k = ie; k < de && b < 46; k++) body[b++] = s[k];
                    body[b] = 0;
                    out->value = atof(body); if (sign == '-') out->value = -out->value; out->has_value = 1;
                    snprintf(out->kind, sizeof out->kind, "%s",
                             (sl && s[de] == '%') ? "percent" : sl ? "ordinal" : cur ? "currency" : dec ? "decimal" : sign ? "signed" : "integer");
                    int L = e - i; if (L > 47) L = 47; memcpy(out->text, s + i, (size_t)L); out->text[L] = 0;
                }
                return e;
            }
        }
    }
    return -1;
}

int mh_split_numbers(const char *text, char *out, size_t outsz, mh_number *nums, int maxn)
{
    int n = (int)strlen(text), i = 0, found = 0; size_t o = 0;
    while (i < n && o + 1 < outsz) {
        int e = num_version(text, n, i); mh_number tmp; int isver = 0, iscode = 0;
        if (e >= 0) isver = 1;
        else { e = num_number(text, n, i, &tmp); if (e < 0) { e = num_code(text, n, i); if (e >= 0) iscode = 1; } }
        if (e >= 0) {
            if (found < maxn && nums) {
                mh_number *m = &nums[found];
                if (isver || iscode) { int L = e - i; if (L > 47) L = 47; memcpy(m->text, text + i, (size_t)L); m->text[L] = 0; strcpy(m->kind, "code"); m->value = 0; m->has_value = 0; }
                else *m = tmp;
            }
            found++; out[o++] = ' '; i = e;
        } else out[o++] = text[i++];
    }
    out[o] = 0;
    return found;
}

/* ── the drift (bw_drift.py) ──────────────────────────────────────────────── */
#define BW_ON  0.35
#define BW_OFF 0.15
double mh_bw_correction(double w_bits, double b_bits, int *active, double *delta_out, double *gamma_abs_out)
{
    double w = w_bits > 1e-9 ? w_bits : 1e-9, b = b_bits > 1e-9 ? b_bits : 1e-9;
    double d = log(b / w), corr = 0.0;
    double complex z = w + b * I, z0 = sqrt(w * b) * (1.0 + I), g = ctanh(clog(z / z0) / 2.0);
    int act = (fabs(d) > BW_ON) || (active && *active && fabs(d) > BW_OFF);
    if (act) { corr = copysign(1.0, d) * (fabs(d) - BW_OFF) / (1.0 - BW_OFF); if (corr > 1) corr = 1; if (corr < -1) corr = -1; }
    if (active) *active = act;
    if (delta_out) *delta_out = d;
    if (gamma_abs_out) *gamma_abs_out = cabs(g);
    return corr;
}

/* ── neuro_recipes constants (kite order) ─────────────────────────────────── */
const char *const MH_AXES[MH_NAX] = {"OPI", "GLU", "GABA", "DA", "5HT", "NE", "OXT"};
static const double NR_BASELINE[MH_NAX]  = {0.50, 0.45, 0.65, 0.50, 0.75, 0.30, 0.50};
static const double NR_RECEPTIVE[MH_NAX] = {0.60, 0.75, 0.70, 0.70, 0.65, 0.50, 0.50};   /* neuro_recipes.RECEPTIVE = V(DA .70, 5HT .65, NE .50, OXT .50, GLU .75, GABA .70, OPI .60), in kite order */
#define NR_K 0.6
#define NR_BAND 0.5

/* ── the usage store ──────────────────────────────────────────────────────── */
typedef struct { char *w; int n; } uslot;
struct mh_ear {
    char dir[512], ptol_dir[512];
    mh_known_fn known; mh_pgen_fn pgen; void *ctx;
    uslot *tab; size_t cap, used; long n_obs;
    long n_numbers, n_kinds[8];
    int bw_active; double bw_corr, bw_delta, bw_gamma; int bw_have;
    struct { char pair[40]; double bits; } pending[16]; int npend;
    /* the user meter */
    int ms_ok; uint32_t nf; double gain[14], base[14], spread[14], icpt[14];
    const char *blob; const float *idf, *coefT; const char **term; 
    double sol_c[14], sol_V; int sol_has;
};

static unsigned long hash_s(const char *s) { unsigned long h = 5381; while (*s) h = h * 33 + (unsigned char)*s++; return h; }

static uslot *u_find(mh_ear *e, const char *w, int create)
{
    if (e->cap == 0) { e->cap = 1024; e->tab = calloc(e->cap, sizeof(uslot)); }
    if (create && (e->used + 1) * 2 > e->cap) {
        size_t oc = e->cap; uslot *ot = e->tab; e->cap *= 2; e->tab = calloc(e->cap, sizeof(uslot)); e->used = 0;
        for (size_t i = 0; i < oc; i++) if (ot[i].w) { size_t k = hash_s(ot[i].w) & (e->cap - 1); while (e->tab[k].w) k = (k + 1) & (e->cap - 1); e->tab[k] = ot[i]; e->used++; }
        free(ot);
    }
    size_t k = hash_s(w) & (e->cap - 1);
    while (e->tab[k].w) { if (!strcmp(e->tab[k].w, w)) return &e->tab[k]; k = (k + 1) & (e->cap - 1); }
    if (!create) return NULL;
    e->tab[k].w = strdup(w); e->tab[k].n = 0; e->used++; return &e->tab[k];
}

static int is_stop(const char *w) { for (int i = 0; i < N_VS_STOP; i++) if (!strcmp(VS_STOP[i], w)) return 1; return 0; }

double mh_ear_lambda(const mh_ear *e) { return (double)e->n_obs / ((double)e->n_obs + 200.0); }
int mh_ear_n_obs(const mh_ear *e) { return (int)e->n_obs; }
int mh_ear_n_numbers(const mh_ear *e) { return (int)e->n_numbers; }
double mh_ear_bw_correction(const mh_ear *e) { return e->bw_corr; }

double mh_ear_p_word(const mh_ear *e, const char *w)
{
    char lw[96]; size_t j = 0; for (; w[j] && j < 95; j++) lw[j] = (char)tolower((unsigned char)w[j]); lw[j] = 0;
    double lam = mh_ear_lambda(e), pg = e->pgen ? e->pgen(lw, e->ctx) : 1e-6;
    uslot *s = u_find((mh_ear *)e, lw, 0); int n = s ? s->n : 0; double V = e->used > 0 ? (double)e->used : 1.0;
    double pu = ((double)n + 0.5) / ((double)e->n_obs + 0.5 * V);
    return lam * pu + (1.0 - lam) * pg;
}

double mh_ear_bits_per_word(const mh_ear *e, const char *prose)           /* tokens [A-Za-z][A-Za-z'-]* */
{
    double tot = 0; int cnt = 0; const char *p = prose;
    while (*p) {
        if (isalpha((unsigned char)*p) && (unsigned char)*p < 0x80) {
            char w[96]; int k = 0;
            while ((isalpha((unsigned char)*p) || *p == '\'' || *p == '-') && (unsigned char)*p < 0x80 && k < 95) { w[k++] = (char)tolower((unsigned char)*p); p++; }
            w[k] = 0; tot += -log2(mh_ear_p_word(e, w)); cnt++;
        } else p++;
    }
    return cnt ? tot / cnt : 0.0;
}

static void u_observe(mh_ear *e, const char *prose)             /* UsageStore.observe: per sentence, each content lemma the Monad knows */
{
    const char *p = prose;
    while (*p) {
        if (isalnum((unsigned char)*p) && (unsigned char)*p < 0x80) {          /* token [A-Za-z0-9][A-Za-z0-9'-]* */
            char w[96]; int k = 0, dig = 0;
            while ((isalnum((unsigned char)*p) || *p == '\'' || *p == '-') && (unsigned char)*p < 0x80 && k < 95) { if (isdigit((unsigned char)*p)) dig = 1; { w[k++] = (char)tolower((unsigned char)*p); p++; } }
            w[k] = 0;
            if (k < 3 || dig || is_stop(w)) continue;
            if (e->known && !e->known(w, e->ctx)) continue;                  /* a word with no sense is skipped, as in the Python store */
            uslot *s = u_find(e, w, 1); s->n++; e->n_obs++;
        } else p++;
    }
}

/* ── the user meter ──────────────────────────────────────────────────────── */
static void ms_open(mh_ear *e)
{
    char path[640]; snprintf(path, sizeof path, "%s/user_state.bin", e->ptol_dir);
    FILE *f = fopen(path, "rb"); if (!f) return;
    char magic[8]; uint32_t hd[3];
    if (fread(magic, 1, 8, f) != 8 || memcmp(magic, "USTATE1\0", 8) || fread(hd, 4, 3, f) != 3 || hd[1] != 14) { fclose(f); return; }
    e->nf = hd[0]; size_t blen = hd[2], pad = (8 - blen % 8) % 8;
    if (fread(e->gain, 8, 14, f) != 14 || fread(e->base, 8, 14, f) != 14 || fread(e->spread, 8, 14, f) != 14 || fread(e->icpt, 8, 14, f) != 14) { fclose(f); return; }
    char *blob = malloc(blen + 1); float *idf = malloc(sizeof(float) * e->nf), *cf = malloc(sizeof(float) * 14 * (size_t)e->nf); char padb[8];
    if (!blob || !idf || !cf || fread(blob, 1, blen, f) != blen || (pad && fread(padb, 1, pad, f) != pad) || fread(idf, 4, e->nf, f) != e->nf || fread(cf, 4, 14 * (size_t)e->nf, f) != 14 * (size_t)e->nf) { fclose(f); free(blob); free(idf); free(cf); return; }
    fclose(f); blob[blen] = 0;
    const char **term = malloc(sizeof(char *) * e->nf); size_t o = 0;
    for (uint32_t i = 0; i < e->nf; i++) { term[i] = blob + o; o += strlen(blob + o) + 1; }
    e->blob = blob; e->idf = idf; e->coefT = cf; e->term = term; e->ms_ok = 1;
}

static long ms_find(const mh_ear *e, const char *t)               /* bsearch the sorted vocabulary */
{
    long lo = 0, hi = (long)e->nf - 1;
    while (lo <= hi) { long mid = (lo + hi) / 2; int c = strcmp(e->term[mid], t); if (c == 0) return mid; if (c < 0) lo = mid + 1; else hi = mid - 1; }
    return -1;
}

/* sklearn TfidfVectorizer(ngram (1,2), lowercase, sublinear_tf, l2) with token_pattern (?u)\b\w[\w']*\b|[!?] */
int mh_meter_raw(const mh_ear *e, const char *text, double dose[14])
{
    if (!e->ms_ok) return 0;
    int n = (int)strlen(text); char *lo = malloc((size_t)n + 1); for (int i = 0; i <= n; i++) lo[i] = (char)tolower((unsigned char)text[i]);
    int nt = 0, cap = 64; char **tok = malloc(sizeof(char *) * (size_t)cap);
    for (int i = 0; i < n; ) {
        if (nw((unsigned char)lo[i]) && (i == 0 || !nw((unsigned char)lo[i - 1]))) {
            int j = i + 1; while (j < n && (nw((unsigned char)lo[j]) || lo[j] == '\'')) j++;
            while (j > i + 1 && lo[j - 1] == '\'') j--;
            if (nt == cap) { cap *= 2; tok = realloc(tok, sizeof(char *) * (size_t)cap); }
            tok[nt] = strndup(lo + i, (size_t)(j - i)); nt++; i = j;
        } else if (lo[i] == '!' || lo[i] == '?') {
            if (nt == cap) { cap *= 2; tok = realloc(tok, sizeof(char *) * (size_t)cap); }
            tok[nt++] = strndup(lo + i, 1); i++;
        } else i++;
    }
    long *fid = malloc(sizeof(long) * (size_t)(2 * nt + 1)); int nf = 0;
    for (int i = 0; i < nt; i++) {
        long f = ms_find(e, tok[i]); if (f >= 0) fid[nf++] = f;
        if (i + 1 < nt) { char bg[256]; snprintf(bg, sizeof bg, "%s %s", tok[i], tok[i + 1]); f = ms_find(e, bg); if (f >= 0) fid[nf++] = f; }
    }
    /* count per feature */
    double x[14]; for (int p = 0; p < 14; p++) x[p] = e->icpt[p];
    double *wv = malloc(sizeof(double) * (size_t)(nf + 1)); long *uf = malloc(sizeof(long) * (size_t)(nf + 1)); int nu = 0; double nrm = 0;
    for (int i = 0; i < nf; i++) {
        int seen = -1; for (int u = 0; u < nu; u++) if (uf[u] == fid[i]) { seen = u; break; }
        if (seen >= 0) wv[seen] += 1.0; else { uf[nu] = fid[i]; wv[nu] = 1.0; nu++; }
    }
    for (int u = 0; u < nu; u++) { wv[u] = (1.0 + log(wv[u])) * (double)e->idf[uf[u]]; nrm += wv[u] * wv[u]; }
    nrm = sqrt(nrm);
    if (nrm > 0) for (int u = 0; u < nu; u++) { double v = wv[u] / nrm; for (int p = 0; p < 14; p++) x[p] += v * (double)e->coefT[uf[u] * 14 + p]; }
    for (int p = 0; p < 14; p++) { double b = x[p] < 0 ? 0 : x[p] > 1 ? 1 : x[p]; dose[p] = 4.5 * b; }   /* 9*(lexical 0 + usage b)/2 */
    for (int i = 0; i < nt; i++) free(tok[i]);
    free(tok); free(lo); free(fid); free(wv); free(uf);
    return 1;
}

/* PromptToState.dose: a text of more than 3 sentences is read sentence by sentence and averaged by length; then the calibration gain, capped at 9 */
static void ms_dose(const mh_ear *e, const char *text, double d[14])
{
    char *cp = strdup(text); int ns = 0, cap = 16; char **ss = malloc(sizeof(char *) * (size_t)cap); int n = (int)strlen(cp), st = 0;
    for (int q = 0; q <= n; q++) {                                       /* re.split(r'(?<=[.?!])\s+|\.\.\.+') then keep len(strip) > 3 */
        int cut = 0, next = q;
        if (q == n) { cut = 1; next = n; }
        else if (isspace((unsigned char)cp[q]) && q > 0 && strchr(".?!", cp[q - 1])) { cut = 1; next = q; while (next < n && isspace((unsigned char)cp[next])) next++; }
        else if (cp[q] == '.' && q + 2 < n + 0 && cp[q + 1] == '.' && cp[q + 2] == '.') { cut = 1; next = q; while (next < n && cp[next] == '.') next++; }
        if (!cut) continue;
        int a0 = st, a1 = q; while (a0 < a1 && isspace((unsigned char)cp[a0])) a0++; while (a1 > a0 && isspace((unsigned char)cp[a1 - 1])) a1--;
        if (a1 - a0 > 3) { if (ns == cap) { cap *= 2; ss = realloc(ss, sizeof(char *) * (size_t)cap); } ss[ns++] = strndup(cp + a0, (size_t)(a1 - a0)); }
        st = next; q = next - 1; if (next >= n) break;
    }
    double acc[14] = {0};
    if (ns > 3) {
        double wsum = 0; double w[256]; int nn = ns > 256 ? 256 : ns;
        for (int i = 0; i < nn; i++) { int c = 0, in = 0; for (const char *t = ss[i]; *t; t++) { if (!isspace((unsigned char)*t)) { if (!in) c++; in = 1; } else in = 0; } w[i] = c > 1 ? c : 1; wsum += w[i]; }
        for (int i = 0; i < nn; i++) { double r[14]; mh_meter_raw(e, ss[i], r); for (int p = 0; p < 14; p++) acc[p] += (w[i] / wsum) * r[p]; }
    } else mh_meter_raw(e, text, acc);
    for (int p = 0; p < 14; p++) { double v = acc[p] * e->gain[p]; d[p] = v > 9 ? 9 : v; }
    for (int i = 0; i < ns; i++) free(ss[i]);
    free(ss); free(cp);
}

static double clamp01(double x) { return x < 0 ? 0 : x > 1 ? 1 : x; }
static double rnd2(double x) { return nearbyint(x * 100.0) / 100.0; }
static double nr_dist(const double *a, const double *b) { double s = 0; for (int i = 0; i < MH_NAX; i++) s += (a[i] - b[i]) * (a[i] - b[i]); return sqrt(s); }

void mh_ear_user_turn(mh_ear *e, const char *text, int fill, mh_state *o)
{
    memset(o, 0, sizeof *o);
    for (int a = 0; a < MH_NAX; a++) { o->mix[a] = NR_BASELINE[a]; o->target[a] = NR_BASELINE[a]; }
    o->held = 1; o->k_eff = NR_K;
    if (!e->ms_ok) return;
    o->ready = 1; double d[14]; ms_dose(e, text, d);
    int words = 0, in = 0; for (const char *t = text; *t; t++) { if (isalpha((unsigned char)*t) || *t == '\'') { if (!in) words++; in = 1; } else in = 0; }
    double v = words / 25.0; v = v < 0.5 ? 0.5 : v > 3.0 ? 3.0 : v;
    if (!e->sol_has) { memcpy(e->sol_c, d, sizeof d); e->sol_V = v; e->sol_has = 1; }
    else { for (int p = 0; p < 14; p++) e->sol_c[p] = (e->sol_V * e->sol_c[p] + v * d[p]) / (e->sol_V + v); e->sol_V += v; }
    if (e->sol_V > 8.0) e->sol_V = 8.0;
    double dev14[14];
    for (int p = 0; p < 14; p++) {
        o->conc[p] = e->sol_c[p]; o->spread[p] = e->spread[p];
        double dev = o->conc[p] - e->base[p]; int heal = fabs(dev) <= o->spread[p]; o->healed += heal; dev14[p] = heal ? 0.0 : dev;
    }
    for (int a = 0; a < MH_NAX; a++) o->mix[a] = clamp01(NR_BASELINE[a] + (dev14[2 * a + 1] - dev14[2 * a]) / 9.0);
    int f = fill < 1 ? 1 : fill > 16 ? 16 : fill; o->k_eff = NR_K * sqrt(f / 16.0);
    o->held = nr_dist(o->mix, NR_RECEPTIVE) < NR_BAND;
    if (o->held) for (int a = 0; a < MH_NAX; a++) o->target[a] = rnd2(o->mix[a]);
    else for (int a = 0; a < MH_NAX; a++) o->target[a] = rnd2(clamp01(NR_RECEPTIVE[a] - o->k_eff * (o->mix[a] - NR_RECEPTIVE[a])));
}

static int farthest(const double *s) { int b = 0; double bd = -1; for (int a = 0; a < MH_NAX; a++) { double d = fabs(s[a] - NR_RECEPTIVE[a]); if (d > bd) { bd = d; b = a; } } return b; }

void mh_state_heard(const mh_state *s, int *axis, int *level) { int a = farthest(s->mix); *axis = a; *level = (int)lrint(6 * s->mix[a]); }

void mh_state_trajectory(const mh_state *s, int n, int *axis, int *level)
{
    int steps = n < 1 ? 1 : n;
    for (int i = 0; i < steps; i++) {
        double st[MH_NAX]; for (int a = 0; a < MH_NAX; a++) st[a] = rnd2(0) + nearbyint((s->mix[a] + (s->target[a] - s->mix[a]) * i / (steps > 1 ? steps - 1 : 1)) * 1000.0) / 1000.0;
        int a = farthest(st); axis[i] = a; level[i] = (int)lrint(6 * st[a]);
    }
}

/* ── open / hear / close ─────────────────────────────────────────────────── */
mh_ear *mh_ear_open(const char *state_dir, const char *ptol_dir, mh_known_fn known, mh_pgen_fn pgen, void *ctx)
{
    mh_ear *e = calloc(1, sizeof *e);
    snprintf(e->dir, sizeof e->dir, "%s", state_dir ? state_dir : "."); snprintf(e->ptol_dir, sizeof e->ptol_dir, "%s", ptol_dir ? ptol_dir : ".");
    e->known = known; e->pgen = pgen; e->ctx = ctx;
    char path[640]; snprintf(path, sizeof path, "%s/usage_c.txt", e->dir);
    FILE *f = fopen(path, "r");
    if (f) {
        char w[128]; int n; long nobs = 0;
        if (fscanf(f, "n_obs %ld\n", &nobs) == 1) e->n_obs = nobs;
        while (fscanf(f, "%127s %d\n", w, &n) == 2) { uslot *s = u_find(e, w, 1); s->n = n; }
        fclose(f);
    }
    snprintf(path, sizeof path, "%s/numbers_c.txt", e->dir);
    if ((f = fopen(path, "r"))) { if (fscanf(f, "%ld", &e->n_numbers) != 1) e->n_numbers = 0; fclose(f); }
    ms_open(e); return e;
}

void mh_ear_close(mh_ear *e)
{
    if (!e) return;
    char path[640], tmp[660]; snprintf(path, sizeof path, "%s/usage_c.txt", e->dir); snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = fopen(tmp, "w");
    if (f) { fprintf(f, "n_obs %ld\n", e->n_obs); for (size_t i = 0; i < e->cap; i++) if (e->tab && e->tab[i].w) fprintf(f, "%s %d\n", e->tab[i].w, e->tab[i].n); fclose(f); rename(tmp, path); }
    snprintf(path, sizeof path, "%s/numbers_c.txt", e->dir);
    if ((f = fopen(path, "w"))) { fprintf(f, "%ld\n", e->n_numbers); fclose(f); }
    for (size_t i = 0; i < e->cap; i++) free(e->tab ? e->tab[i].w : NULL);
    free(e->tab); free((void *)e->blob); free((void *)e->idf); free((void *)e->coefT); free((void *)e->term); free(e);
}

int mh_ear_hear(mh_ear *e, const char *text, int cls, const char *pair)
{
    size_t L = strlen(text) + 1; char *prose = malloc(L); mh_number nums[64];
    int nn = mh_split_numbers(text, prose, L, nums, 64);
    if (nn && cls != MH_DOCUMENT) { e->n_numbers += nn; }
    if (cls == MH_EXTERNAL) {
        double bits = mh_ear_bits_per_word(e, prose);                 /* priced BEFORE it is counted */
        u_observe(e, prose);
        if (pair && *pair) { int k = e->npend < 16 ? e->npend++ : 15; if (e->npend == 16 && k == 15) memmove(&e->pending[0], &e->pending[1], 15 * sizeof e->pending[0]); snprintf(e->pending[k].pair, 40, "%s", pair); e->pending[k].bits = bits; }
    } else if (cls == MH_INTERNAL) {
        double bits = mh_ear_bits_per_word(e, prose);
        for (int i = 0; i < e->npend && pair && *pair; i++) if (!strcmp(e->pending[i].pair, pair)) {
            double w = e->pending[i].bits; memmove(&e->pending[i], &e->pending[i + 1], (size_t)(e->npend - i - 1) * sizeof e->pending[0]); e->npend--;
            if (bits > 0 && w > 0) { e->bw_corr = mh_bw_correction(w, bits, &e->bw_active, &e->bw_delta, &e->bw_gamma); e->bw_have = 1; }
            break;
        }
    }
    free(prose); return nn;
}

void mh_ear_report(const mh_ear *e, char *out, size_t sz)
{
    snprintf(out, sz, "usage: %ld words counted, %zu lemmas, lambda %.3f | drift: %s delta %+.3f |Gamma| %.3f active %d correction %+.3f | numbers heard: %ld | state meter: %s",
             e->n_obs, e->used, mh_ear_lambda(e), e->bw_have ? "measured" : "no pair yet", e->bw_delta, e->bw_gamma, e->bw_active, e->bw_corr, e->n_numbers, e->ms_ok ? "loaded" : "user_state.bin absent");
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
