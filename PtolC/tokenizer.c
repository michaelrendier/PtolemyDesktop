/*
 * PtolC/tokenizer.c — Text tokeniser for the C Monad.
 */

#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include "tokenizer.h"

char **tok_split(const char *text, int *count)
{
    int   cap  = 512;
    char **out = malloc(cap * sizeof(char *));
    *count = 0;
    if (!out || !text) return out;

    int   tlen = strlen(text);
    char *buf  = malloc(tlen + 2);
    if (!buf) return out;
    int blen = 0;

    for (int i = 0; i <= tlen; i++) {
        unsigned char c = (unsigned char)text[i];
        int word_char = isalpha(c) || c == '\'';

        if (word_char) {
            buf[blen++] = (char)tolower(c);
        } else if (blen > 0) {
            buf[blen] = '\0';
            /* filter: len >= 2, not pure apostrophe */
            if (blen >= 2 && buf[0] != '\'') {
                if (*count >= cap) {
                    cap *= 2;
                    out = realloc(out, cap * sizeof(char *));
                }
                out[(*count)++] = strdup(buf);
            }
            blen = 0;
        }
    }

    free(buf);
    return out;
}

void tok_free(char **tokens, int count)
{
    if (!tokens) return;
    for (int i = 0; i < count; i++) free(tokens[i]);
    free(tokens);
}
