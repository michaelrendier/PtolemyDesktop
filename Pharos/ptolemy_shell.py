#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ptolemy_shell.py — Ptolemy pty process (curses UI).

Runs **inside** the QTermWidget pseudo-terminal started by
:class:`Pharos.PtolShell.PtolShell`.  No Qt code here.

Screen layout
-------------
Rows are allocated from the bottom upward; the output pad fills the rest::

    ┌──────────────────────────────┐
    │  out_pad  (SCROLLBACK lines) │  rows 0 .. h-inp_h-2
    ├──────────────────────────────┤
    │  separator  ─────────────    │  row  h-inp_h-1
    ├──────────────────────────────┤
    │  input  (1-3 growing rows)   │  rows h-inp_h .. h-1
    └──────────────────────────────┘

The input area grows automatically (up to 3 rows) as the line length
exceeds the terminal width, matching the behaviour of the Claude Code
input box.

Input routing
-------------
``$ cmd``
    Passed to ``/bin/sh`` via :func:`subprocess.run` with
    ``capture_output=True``.  Output is written to the pad.

``> expr``
    Passed to ``python3 -c`` (eval then exec fallback) with
    ``capture_output=True``.

plain text
    Forwarded to :meth:`Philadelphos.monad.Monad.shell_exchange`.
"""

import sys
import os
import signal
import curses
import subprocess

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

_CHECKPOINT = os.path.join(_ROOT, 'Callimachus', 'data', 'monad_wordnet.json')
SCROLLBACK   = 5000
PROMPT       = 'Ptolemy > '
PROMPT_LEN   = len(PROMPT)

PTOLEMY_COLOR = 1   # blue  — Ptolemy exchange
SHELL_COLOR   = 2   # cyan  — shell / REPL output
ERROR_COLOR   = 3   # red   — errors
DIM_COLOR     = 4   # white dim — system messages


def _load_monad():
    """Import and initialise the Monad, loading the wordnet checkpoint if present.

    :returns: A ready :class:`Philadelphos.monad.Monad` instance, or ``None``
              if the import or load fails.
    """
    try:
        from Philadelphos.monad import Monad
        m = Monad(N=25000)
        m.load(_CHECKPOINT if os.path.exists(_CHECKPOINT) else None)
        return m
    except Exception:
        return None


def _inp_h(buf, w):
    """Return the number of input rows needed for *buf* at terminal width *w*.

    :param buf: Current input character buffer.
    :type buf: list[str]
    :param w: Terminal width in columns.
    :type w: int
    :returns: Row count clamped to ``[1, 3]``.
    :rtype: int
    """
    total = PROMPT_LEN + len(buf)
    return min(3, max(1, -(-(total) // max(w, 1))))


def run(stdscr):
    """Main curses entry point — called by :func:`curses.wrapper`.

    Owns the full curses session: colour pairs, the output pad, the separator
    row, the growing input rows, SIGWINCH handling, and the main event loop.

    :param stdscr: The curses standard screen supplied by ``curses.wrapper``.
    """
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(PTOLEMY_COLOR, curses.COLOR_BLUE,  -1)
    curses.init_pair(SHELL_COLOR,   curses.COLOR_CYAN,  -1)
    curses.init_pair(ERROR_COLOR,   curses.COLOR_RED,   -1)
    curses.init_pair(DIM_COLOR,     curses.COLOR_WHITE, -1)
    curses.noecho()
    stdscr.keypad(True)

    h, w = stdscr.getmaxyx()
    w = max(w, 1)

    out_pad = curses.newpad(SCROLLBACK, max(w, 1))
    out_pos = [0]

    resize_flag = [False]

    def _sigwinch(signum, frame):
        """Set resize_flag so the main loop rebuilds the layout."""
        resize_flag[0] = True

    signal.signal(signal.SIGWINCH, _sigwinch)

    def _refresh_pad(ih):
        """Repaint the output pad, leaving *ih* input rows + 1 sep row clear."""
        try:
            display_rows = max(h - ih - 1, 1)
            top = max(0, out_pos[0] - display_rows)
            out_pad.refresh(top, 0, 0, 0, max(h - ih - 2, 0), max(w - 1, 1))
        except curses.error:
            pass

    def _write(text: str, color: int = PTOLEMY_COLOR):
        """Append *text* to the next line of out_pad in the given colour pair."""
        try:
            out_pad.addstr(
                out_pos[0], 0,
                text[:max(w - 1, 1)],
                curses.color_pair(color),
            )
            out_pos[0] = min(out_pos[0] + 1, SCROLLBACK - 1)
        except curses.error:
            pass

    def _draw_sep(ih):
        """Draw the '─' separator directly on stdscr above the input rows."""
        row = max(h - ih - 1, 0)
        try:
            stdscr.addstr(row, 0, '─' * max(w - 1, 0),
                          curses.color_pair(DIM_COLOR))
            stdscr.clrtoeol()
        except curses.error:
            pass

    def _draw_input(buf, ih):
        """Render PROMPT + *buf* across *ih* rows directly on stdscr."""
        text = PROMPT + ''.join(buf)
        for i in range(ih):
            row = h - ih + i
            if not (0 <= row < h):
                continue
            chunk = text[i * w: (i + 1) * w]
            try:
                stdscr.move(row, 0)
                stdscr.clrtoeol()
                if i == 0:
                    p = min(PROMPT_LEN, len(chunk))
                    stdscr.addstr(row, 0, chunk[:p],
                                  curses.color_pair(PTOLEMY_COLOR))
                    if len(chunk) > PROMPT_LEN:
                        stdscr.addstr(row, PROMPT_LEN, chunk[PROMPT_LEN:])
                else:
                    stdscr.addstr(row, 0, chunk)
            except curses.error:
                pass
        stdscr.refresh()

    def _redraw(buf):
        """Full repaint: sep + input + pad, computing inp_h from *buf*."""
        ih = _inp_h(buf, w)
        _draw_sep(ih)
        _draw_input(buf, ih)
        _refresh_pad(ih)

    def _do_resize(buf):
        """Re-query terminal dimensions after SIGWINCH and repaint."""
        nonlocal h, w
        try:
            curses.update_lines_cols()
        except AttributeError:
            pass
        h, w = stdscr.getmaxyx()
        w = max(w, 1)
        stdscr.clear()
        stdscr.refresh()
        _redraw(buf)

    def _run_shell(cmd):
        """Run *cmd* in a subshell and write captured stdout/stderr to the pad."""
        if not cmd:
            return
        try:
            r = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30)
            out = r.stdout + r.stderr
            color = ERROR_COLOR if r.returncode != 0 else SHELL_COLOR
            for line in (out.splitlines() or ['(no output)']):
                _write(line, color)
        except subprocess.TimeoutExpired:
            _write('[$ timeout after 30s]', ERROR_COLOR)
        except Exception as exc:
            _write(f'[$ {exc}]', ERROR_COLOR)

    def _run_repl(expr):
        """Evaluate *expr* via ``python3 -c`` (eval then exec) and write output to the pad."""
        if not expr:
            return
        wrap = (
            'import sys\n'
            'try:\n'
            f'    _r = eval({repr(expr)})\n'
            '    if _r is not None: print(_r)\n'
            'except SyntaxError:\n'
            f'    exec({repr(expr)})\n'
        )
        try:
            r = subprocess.run(
                [sys.executable, '-c', wrap],
                capture_output=True, text=True, timeout=30)
            out = r.stdout + r.stderr
            color = ERROR_COLOR if r.returncode != 0 else SHELL_COLOR
            for line in (out.splitlines() or ['(no output)']):
                _write(line, color)
        except subprocess.TimeoutExpired:
            _write('[> timeout after 30s]', ERROR_COLOR)
        except Exception as exc:
            _write(f'[> {exc}]', ERROR_COLOR)

    # ── boot ──────────────────────────────────────────────────────────────────
    _write('Ptolemy II Philadelphos', PTOLEMY_COLOR)
    _write('  $ cmd → shell   > expr → python   text → Monad', DIM_COLOR)

    monad = _load_monad()
    if monad is None:
        _write('[Monad] offline — run: python3 Callimachus/wordnet_init.py',
               ERROR_COLOR)
    else:
        _write('[Monad] ready', DIM_COLOR)

    inp_buf: list[str] = []
    history:  list[str] = []
    hist_idx  = [0]

    curses.halfdelay(1)
    _redraw(inp_buf)

    def _handle_enter():
        line = ''.join(inp_buf).strip()
        inp_buf.clear()
        if not line:
            return
        history.append(line)
        hist_idx[0] = len(history)
        _write(f'Ptolemy > {line}', PTOLEMY_COLOR)

        if line[0] == '$':
            _run_shell(line[1:].lstrip())
        elif line[0] == '>':
            _run_repl(line[1:].lstrip())
        elif monad is not None:
            try:
                result = monad.shell_exchange(line)
                if result and str(result).strip():
                    _write(f'Ptolemy › {result}', PTOLEMY_COLOR)
                else:
                    _write('(σ=½ — field perturbed, no emission)',
                           DIM_COLOR)
            except Exception as exc:
                _write(f'[Monad error: {exc}]', ERROR_COLOR)
        else:
            _write('[Ptolemy] Monad not available.', ERROR_COLOR)

    # ── main loop ─────────────────────────────────────────────────────────────
    while True:
        if resize_flag[0]:
            resize_flag[0] = False
            _do_resize(inp_buf)

        _redraw(inp_buf)

        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1

        if ch == -1:
            continue
        elif ch in (curses.KEY_ENTER, ord('\n'), ord('\r')):
            _handle_enter()
        elif ch == curses.KEY_UP:
            if history and hist_idx[0] > 0:
                hist_idx[0] -= 1
                inp_buf.clear()
                inp_buf.extend(list(history[hist_idx[0]]))
        elif ch == curses.KEY_DOWN:
            if hist_idx[0] < len(history) - 1:
                hist_idx[0] += 1
                inp_buf.clear()
                inp_buf.extend(list(history[hist_idx[0]]))
            elif hist_idx[0] == len(history) - 1:
                hist_idx[0] = len(history)
                inp_buf.clear()
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if inp_buf:
                inp_buf.pop()
        elif ch in (3, 4):   # Ctrl+C / Ctrl+D
            break
        elif 32 <= ch <= 126:
            inp_buf.append(chr(ch))


if __name__ == '__main__':
    curses.wrapper(run)
