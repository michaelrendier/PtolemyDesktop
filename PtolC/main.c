/*
 * PtolC/main.c — ptolemy command-line binary.
 *
 * Usage:
 *   ptolemy -l <file>         learn from file (plain text)
 *   ptolemy -l <url>          learn from URL  (via curl)
 *   ptolemy -l -              learn from stdin
 *   ptolemy -h <prompt>       hear: query the field → speak
 *   ptolemy -s                status
 *   ptolemy -q <word>         lookup a single word
 *   ptolemy -c <checkpoint>   specify checkpoint path (default: see below)
 *   ptolemy -n                dry run: do not save checkpoint after -l
 *
 * Multiple -l and -h flags may be combined in one invocation.
 * Checkpoint is saved after all -l operations unless -n is set.
 *
 * Checkpoint search order:
 *   1. -c flag
 *   2. PTOLEMY_CHECKPOINT env var
 *   3. ./monad_wordnet.bin  (beside binary)
 *   4. ../Callimachus/data/monad_wordnet.bin  (from PtolC/ build dir)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

#include "ptolemy.h"
#include "monad.h"
#include "checkpoint.h"

/* ── Helpers ──────────────────────────────────────────────────────────────── */

static char *read_file(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "[ptolemy] cannot open %s: %s\n", path, strerror(errno));
        return NULL;
    }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    char *buf = malloc(sz + 1);
    if (!buf) { fclose(f); return NULL; }
    size_t got = fread(buf, 1, sz, f);
    buf[got] = '\0';
    fclose(f);
    return buf;
}

static char *read_stdin(void)
{
    size_t cap = 65536, len = 0;
    char  *buf = malloc(cap);
    int    c;
    while ((c = fgetc(stdin)) != EOF) {
        if (len + 2 >= cap) { cap *= 2; buf = realloc(buf, cap); }
        buf[len++] = (char)c;
    }
    buf[len] = '\0';
    return buf;
}

static char *read_url(const char *url)
{
    /* Validate URL has no single quotes to prevent shell injection */
    for (const char *p = url; *p; p++) {
        if (*p == '\'') {
            fprintf(stderr, "[ptolemy] URL contains single quote — refusing\n");
            return NULL;
        }
    }
    char cmd[4096];
    snprintf(cmd, sizeof(cmd), "curl -sf '%s'", url);
    FILE *pipe = popen(cmd, "r");
    if (!pipe) {
        fprintf(stderr, "[ptolemy] popen failed for URL %s\n", url);
        return NULL;
    }
    size_t cap = 131072, len = 0;
    char  *buf = malloc(cap);
    int    c;
    while ((c = fgetc(pipe)) != EOF) {
        if (len + 2 >= cap) { cap *= 2; buf = realloc(buf, cap); }
        buf[len++] = (char)c;
    }
    buf[len] = '\0';
    pclose(pipe);
    return buf;
}

static const char *find_checkpoint(const char *flag_path)
{
    static char found[4096];
    const char *env_path = getenv("PTOLEMY_CHECKPOINT");
    const char *candidates[] = {
        flag_path,
        env_path,
        "monad_wordnet.bin",
        "../Callimachus/data/monad_wordnet.bin",
    };
    int n = (int)(sizeof(candidates) / sizeof(candidates[0]));
    for (int i = 0; i < n; i++) {
        if (!candidates[i] || !candidates[i][0]) continue;
        FILE *t = fopen(candidates[i], "rb");
        if (t) {
            fclose(t);
            strncpy(found, candidates[i], sizeof(found) - 1);
            found[sizeof(found) - 1] = '\0';
            return found;
        }
    }
    return NULL;
}

/* ── Main ─────────────────────────────────────────────────────────────────── */

int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr,
            "ptolemy — H_hat_RB field engine\n\n"
            "  -l <file|url|->  learn from file, URL, or stdin\n"
            "  -h <prompt>      hear: query → Noether response\n"
            "  -q <word>        lookup word: zero, sigma, beta\n"
            "  -s               status\n"
            "  -c <path>        checkpoint path\n"
            "  -n               no-save (dry run for -l)\n"
            "\ncheckpoint search: -c flag → PTOLEMY_CHECKPOINT → "
            "./monad_wordnet.bin → ../Callimachus/data/monad_wordnet.bin\n");
        return 1;
    }

    const char *ckpt_flag = NULL;
    int         no_save   = 0;
    int         learned   = 0;

    /* Pre-scan for -c and -n */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-c") == 0 && i + 1 < argc)
            ckpt_flag = argv[++i];
        else if (strcmp(argv[i], "-n") == 0)
            no_save = 1;
    }

    const char *ckpt_path = find_checkpoint(ckpt_flag);

    /* Create and initialise monad */
    Monad *m = monad_create(MONAD_N_DEFAULT);
    monad_ground_init(m);

    if (ckpt_path) {
        if (checkpoint_load(m, ckpt_path) != 0) {
            fprintf(stderr, "[ptolemy] warning: checkpoint load failed; using ground state\n");
        }
    } else {
        fprintf(stderr, "[ptolemy] no checkpoint found; starting from σ=0 ground state\n"
                        "          run Callimachus/wordnet_init.py then checkpoint_export.py\n");
    }

    /* Process arguments in order */
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-c") == 0) { i++; continue; }
        if (strcmp(argv[i], "-n") == 0) continue;

        if (strcmp(argv[i], "-l") == 0 && i + 1 < argc) {
            const char *src = argv[++i];
            char *text = NULL;

            if (strcmp(src, "-") == 0) {
                text = read_stdin();
            } else if (strncmp(src, "http://", 7) == 0 ||
                       strncmp(src, "https://", 8) == 0) {
                fprintf(stderr, "[ptolemy] fetching %s ...\n", src);
                text = read_url(src);
            } else {
                text = read_file(src);
            }

            if (text) {
                size_t tlen = strlen(text);
                fprintf(stderr, "[ptolemy] learning from %s  (%zu bytes)\n", src, tlen);
                monad_learn(m, text);
                free(text);
                learned = 1;
                monad_status(m, stderr);
            }
            continue;
        }

        if (strcmp(argv[i], "-h") == 0 && i + 1 < argc) {
            const char *query = argv[++i];

            /* Print hear activations */
            fprintf(stderr, "\n[hear] %s\n", query);
            /* Re-implement a quick per-word breakdown */
            {
                int    ntok = 0;
                char **toks = NULL;
                /* Inline split for display */
                /* Use monad_lookup for each token found in query */
                char  query_copy[4096];
                strncpy(query_copy, query, sizeof(query_copy) - 1);
                char *tok = strtok(query_copy, " \t\r\n");
                while (tok) {
                    monad_lookup(m, tok, stderr);
                    tok = strtok(NULL, " \t\r\n");
                }
                (void)ntok; (void)toks;
            }

            char *response = monad_speak(m, query, 50);
            printf("[speak] %s\n", response);
            free(response);
            continue;
        }

        if (strcmp(argv[i], "-q") == 0 && i + 1 < argc) {
            monad_lookup(m, argv[++i], stdout);
            continue;
        }

        if (strcmp(argv[i], "-s") == 0) {
            monad_status(m, stdout);
            continue;
        }

        fprintf(stderr, "[ptolemy] unknown argument: %s\n", argv[i]);
    }

    /* Save checkpoint if we learned anything */
    if (learned && !no_save) {
        const char *save_path = ckpt_path ? ckpt_path : "monad_wordnet.bin";
        checkpoint_save(m, save_path, 0.0);
    }

    monad_destroy(m);
    return 0;
}
