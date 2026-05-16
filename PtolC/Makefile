# PtolC/Makefile — C Monad build

CC      = gcc
CFLAGS  = -O2 -Wall -Wextra -std=c11 -D_POSIX_C_SOURCE=200809L
LDFLAGS = -lm

TARGET  = ptolemy
SRCS    = main.c monad.c checkpoint.c tokenizer.c
OBJS    = $(SRCS:.c=.o)

.PHONY: all clean export

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

# Export Python checkpoint to binary (run from Ptolemy3/ root)
export:
	python3 ../Callimachus/checkpoint_export.py

# Remove build artifacts
clean:
	rm -f $(OBJS) $(TARGET)

# ── Dependencies ────────────────────────────────────────────────────────────
main.o:        main.c ptolemy.h monad.h checkpoint.h tokenizer.h
monad.o:       monad.c ptolemy.h monad.h tokenizer.h
checkpoint.o:  checkpoint.c ptolemy.h checkpoint.h monad.h
tokenizer.o:   tokenizer.c tokenizer.h
