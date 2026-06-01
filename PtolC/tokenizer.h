/*
 * PtolC/tokenizer.h — Text tokeniser for the C Monad.
 */

#ifndef TOKENIZER_H
#define TOKENIZER_H

/* Tokenise text: lowercase, split on non-alpha (apostrophe kept), filter len<2.
 * Returns malloc'd array of malloc'd strings.  Caller owns both.
 * *count set to number of tokens. */
char **tok_split(const char *text, int *count);

/* Free token array returned by tok_split. */
void   tok_free(char **tokens, int count);

#endif /* TOKENIZER_H */
