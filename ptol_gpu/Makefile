# ptol_gpu Makefile — open source only (GLFW + OpenGL)
# ─────────────────────────────────────────────────────
# Install deps (Debian/Ubuntu):
#   sudo apt install libglfw3-dev libgl-dev
#
# Build:
#   make          — library only  (libptol_gpu.a)
#   make demo     — demo binary   (ptol_gpu_demo)
#   make clean    — remove outputs

CC      := gcc
CFLAGS  := -O2 -std=c11 -Wall -Wextra
LDFLAGS := -lGL -lglfw -ldl -lm

SRC     := ptol_gpu_api.c
OBJ     := ptol_gpu_api.o
LIB     := libptol_gpu.a
DEMO    := ptol_gpu_demo

.PHONY: all demo clean

all: $(LIB)

$(OBJ): $(SRC) ptol_gpu_api.h
	$(CC) $(CFLAGS) -fno-strict-aliasing -c -o $@ $<

$(LIB): $(OBJ)
	ar rcs $@ $^
	@echo "Built: $(LIB)"
	@echo "Sedenion geometry is in the shaders. The API is just the key."

demo: $(SRC) ptol_gpu_api.h
	$(CC) $(CFLAGS) -DPTOL_DEMO -fno-strict-aliasing -o $(DEMO) $(SRC) $(LDFLAGS)
	@echo "Built: $(DEMO)"
	@echo "Run:   ./$(DEMO)"
	@echo "Close the window when you have seen the geometry. Then discard."

clean:
	rm -f $(OBJ) $(LIB) $(DEMO)
