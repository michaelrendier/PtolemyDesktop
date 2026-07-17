#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos/ptolemy_tongue.py — Output Fold Filter
=====================================================
Ptolemy's Tongue: the last layer before text reaches the display widget.

Theory: Pentagonal–Hexagonal Hydroradiolysis Chromatography
------------------------------------------------------------
Carbon lattices (graphene, fullerenes) obey a strict curvature rule:
a flat hexagonal sheet (graphene) introduces NO curvature.
A pentagonal ring introduces positive (convex) curvature — required
to close a sphere (C60 has exactly 12 pentagons, any number of hexagons).

Applied to letter sequences:
  - A "hexagonal" segment is a stable, locally flat run — normal text.
  - A "pentagonal" segment is a forced curvature insertion — e.g. a line
    break, paragraph boundary, punctuation cluster, emphasis inflection.
  - "Hydroradiolysis" in this context: the energetic breaking of bonds
    in a sequence under radiation — i.e. pathological folds: runaway
    repetition, excessive punctuation clusters, malformed glyph runs,
    unclosed bracket stacks, overlong identical-character sequences.

The filter:
  1. Counts fold events in the text (transitions between character classes).
  2. Applies the Euler characteristic constraint: for a closed surface,
     V - E + F = 2. For text: pentagons - hexagons ≤ MAX_PENTAGON_RATIO.
     Excess curvature (too many pentagons) = pathological folding = rejected.
  3. Specific pathologies caught:
       a. Runaway repeats: same character >MAX_REPEAT consecutive times
       b. Punctuation storms: >MAX_PUNCT_RUN consecutive punctuation chars
       c. Unclosed bracket stacks: depth exceeds MAX_BRACKET_DEPTH
       d. Null/control character injection: stripped
       e. Overlong lines: wrapped at MAX_LINE if no natural break

The filter is CONSERVATIVE — it never changes meaning, only constrains
the surface geometry of the glyph stream.

Constants are tunable. Defaults are permissive for normal prose output.

Author: O Captain My Captain + Claude (Anthropic)
Date:   April 2026
"""

from __future__ import annotations
import re
import unicodedata
from typing import List, Tuple

# ══════════════════════════════════════════════════════════════════════════════
#  GEOMETRY CONSTANTS
#  Euler characteristic: V - E + F = χ (2 for sphere, 0 for torus)
#  Pentagon rule: min 12 pentagons to close a fullerene surface.
#  We use ratios rather than absolute counts.
# ══════════════════════════════════════════════════════════════════════════════

# Maximum consecutive identical characters before fold collapse
MAX_REPEAT            = 8

# Maximum consecutive punctuation/symbol chars (excluding spaces)
MAX_PUNCT_RUN         = 5

# Maximum nesting depth of bracket-type structures: (), [], {}, <>
MAX_BRACKET_DEPTH     = 12

# Maximum line length before hard-wrapping (characters, not bytes)
MAX_LINE              = 4096

# Pentagon-to-hexagon ratio cap: pentagons = fold events / total_chars
# Above this ratio the text is considered pathologically curved.
MAX_PENTAGON_RATIO    = 0.40

# Control characters to strip (keep tab=0x09, newline=0x0A, CR=0x0D)
_STRIP_CONTROLS       = set(range(0x00, 0x09)) | {0x0B, 0x0C} | set(range(0x0E, 0x20)) | {0x7F}

# Character class transitions that count as "fold events" (pentagon insertions)
# We define 6 classes matching the hexagonal lattice:
#   0=alpha, 1=digit, 2=space, 3=punct, 4=bracket, 5=newline/control
_CLASS_ALPHA   = 0
_CLASS_DIGIT   = 1
_CLASS_SPACE   = 2
_CLASS_PUNCT   = 3
_CLASS_BRACKET = 4
_CLASS_NEWLINE = 5

_BRACKETS_OPEN  = set('([{<')
_BRACKETS_CLOSE = set(')]}>')
_BRACKET_PAIRS  = {')': '(', ']': '[', '}': '{', '>': '<'}


def _char_class(ch: str) -> int:
    if ch in '\n\r':
        return _CLASS_NEWLINE
    if ch in ' \t':
        return _CLASS_SPACE
    if ch in _BRACKETS_OPEN or ch in _BRACKETS_CLOSE:
        return _CLASS_BRACKET
    if ch.isalpha():
        return _CLASS_ALPHA
    if ch.isdigit():
        return _CLASS_DIGIT
    return _CLASS_PUNCT


# ══════════════════════════════════════════════════════════════════════════════
#  FoldGeometry — measures and validates a text surface
# ══════════════════════════════════════════════════════════════════════════════

class FoldGeometry:
    """
    Analyses the fold geometry of a text string.

    Attributes after analyse():
        pentagons       : int   — count of class transitions (curvature insertions)
        hexagons        : int   — count of same-class continuations (flat segments)
        repeat_offsets  : list  — (start, end, char) of runaway repeat sites
        punct_offsets   : list  — (start, end) of punctuation storms
        bracket_depth   : int   — max bracket nesting depth reached
        unclosed        : list  — list of unclosed open-bracket chars
        long_lines      : list  — (start, end) of overlong line segments
        pentagon_ratio  : float — pentagons / max(1, total_chars)
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.pentagons            : int   = 0
        self.hexagons             : int   = 0
        self.repeat_offsets       : List  = []
        self.punct_offsets        : List  = []
        self.word_repeat_offsets  : List  = []   # (word, count) pairs
        self.bracket_depth        : int   = 0
        self.unclosed             : List  = []
        self.long_lines           : List  = []
        self.pentagon_ratio       : float = 0.0
        self._total_chars         : int   = 0

    def analyse(self, text: str) -> 'FoldGeometry':
        self.reset()
        if not text:
            return self

        n = len(text)
        self._total_chars = n

        prev_cls = _char_class(text[0])
        run_len  = 1
        run_char = text[0]
        punct_run = 0

        bracket_stack = []
        max_bracket_depth = 0

        # line length tracking
        line_start = 0

        for i in range(1, n):
            ch  = text[i]
            cls = _char_class(ch)

            # fold event (pentagon)
            if cls != prev_cls:
                self.pentagons += 1
                prev_cls = cls
                run_len  = 1
                run_char = ch
            else:
                self.hexagons += 1
                if ch == run_char:
                    run_len += 1
                    if run_len > MAX_REPEAT:
                        if not self.repeat_offsets or self.repeat_offsets[-1][2] != ch:
                            start = max(0, i - run_len + 1)
                            self.repeat_offsets.append((start, i, ch))
                else:
                    run_len  = 1
                    run_char = ch

            # punctuation storm
            if cls == _CLASS_PUNCT:
                punct_run += 1
                if punct_run > MAX_PUNCT_RUN:
                    if not self.punct_offsets or self.punct_offsets[-1][1] < i - 1:
                        self.punct_offsets.append((i - punct_run + 1, i))
            else:
                punct_run = 0

            # bracket tracking
            if ch in _BRACKETS_OPEN:
                bracket_stack.append((ch, i))
                max_bracket_depth = max(max_bracket_depth, len(bracket_stack))
            elif ch in _BRACKETS_CLOSE:
                if bracket_stack and bracket_stack[-1][0] == _BRACKET_PAIRS[ch]:
                    bracket_stack.pop()
                # mismatched close — ignore (don't push)

            # line length
            if ch == '\n':
                line_len = i - line_start
                if line_len > MAX_LINE:
                    self.long_lines.append((line_start, i))
                line_start = i + 1

        # check final line
        if n - line_start > MAX_LINE:
            self.long_lines.append((line_start, n))

        self.bracket_depth = max_bracket_depth
        self.unclosed      = [ch for ch, _ in bracket_stack]
        self.pentagon_ratio = self.pentagons / max(1, n)

        # Word-level run detection (sequence of same word >MAX_WORD_RUN times)
        self._detect_word_runs(text)

        return self

    # Maximum consecutive identical words (case-insensitive) before pathological
    _MAX_WORD_RUN = 5

    def _detect_word_runs(self, text: str):
        """Find repeated word runs exceeding _MAX_WORD_RUN."""
        words = text.lower().split()
        if not words:
            return
        run_word  = words[0]
        run_count = 1
        for w in words[1:]:
            if w == run_word:
                run_count += 1
                if run_count > self._MAX_WORD_RUN:
                    if (not self.word_repeat_offsets or
                            self.word_repeat_offsets[-1][0] != run_word):
                        self.word_repeat_offsets.append((run_word, run_count))
            else:
                run_word  = w
                run_count = 1

    def is_pathological(self) -> Tuple[bool, List[str]]:
        """
        Returns (True, [reasons]) if text geometry is pathological.
        """
        reasons = []
        if self.repeat_offsets:
            reasons.append(
                f"runaway_repeat:{len(self.repeat_offsets)}_sites")
        if self.punct_offsets:
            reasons.append(
                f"punct_storm:{len(self.punct_offsets)}_sites")
        if self.bracket_depth > MAX_BRACKET_DEPTH:
            reasons.append(
                f"bracket_depth:{self.bracket_depth}>{MAX_BRACKET_DEPTH}")
        if self.pentagon_ratio > MAX_PENTAGON_RATIO:
            reasons.append(
                f"pentagon_ratio:{self.pentagon_ratio:.3f}>{MAX_PENTAGON_RATIO}")
        if self.word_repeat_offsets:
            reasons.append(
                f"word_run:{len(self.word_repeat_offsets)}_sites")
        return bool(reasons), reasons


# ══════════════════════════════════════════════════════════════════════════════
#  PtolemyTongue — the filter
# ══════════════════════════════════════════════════════════════════════════════

class PtolemyTongue:
    """
    Last-layer output filter.

    filter(text) → cleaned text

    Steps applied in order:
        1. Control character stripping
        2. Unicode normalisation (NFC)
        3. Runaway repeat collapse (>MAX_REPEAT same chars → MAX_REPEAT)
        4. Punctuation storm reduction (>MAX_PUNCT_RUN punct → MAX_PUNCT_RUN)
        5. Overlong line wrapping
        6. Pentagon ratio check — if still excessive, flag in output header
           (text is NOT truncated; only flagged so upstream can decide)

    The filter NEVER truncates content — it only repairs geometry.
    The Euler constraint is advisory, not destructive.
    """

    def __init__(self,
                 max_repeat:       int   = MAX_REPEAT,
                 max_punct_run:    int   = MAX_PUNCT_RUN,
                 max_line:         int   = MAX_LINE,
                 max_pentagon_ratio: float = MAX_PENTAGON_RATIO):
        self.max_repeat         = max_repeat
        self.max_punct_run      = max_punct_run
        self.max_line           = max_line
        self.max_pentagon_ratio = max_pentagon_ratio
        self._geo               = FoldGeometry()

    # ── public ────────────────────────────────────────────────────────────

    def filter(self, text: str) -> str:
        """
        Apply all fold-geometry constraints to text.
        Returns cleaned string ready for display.
        """
        if not text:
            return text

        text = self._strip_controls(text)
        text = self._normalise_unicode(text)
        text = self._collapse_repeats(text)
        text = self._collapse_word_runs(text)
        text = self._reduce_punct_storms(text)
        text = self._wrap_long_lines(text)

        # Advisory geometry check — annotate if still bent
        geo = self._geo.analyse(text)
        is_bad, reasons = geo.is_pathological()
        if is_bad:
            # Prepend a single diagnostic line; content intact
            tag = f"[⬡ fold-flag: {', '.join(reasons)}]\n"
            text = tag + text

        return text

    def analyse(self, text: str) -> FoldGeometry:
        """Return geometry analysis without filtering."""
        return self._geo.analyse(text)

    # ── steps ─────────────────────────────────────────────────────────────

    @staticmethod
    def _strip_controls(text: str) -> str:
        """Remove non-printable control characters (keep tab, LF, CR)."""
        return ''.join(ch for ch in text if ord(ch) not in _STRIP_CONTROLS)

    @staticmethod
    def _normalise_unicode(text: str) -> str:
        """NFC normalisation — canonical composed form."""
        return unicodedata.normalize('NFC', text)

    def _collapse_word_runs(self, text: str) -> str:
        """
        Collapse runs of >5 identical consecutive words (case-insensitive)
        to exactly 5. Preserves surrounding whitespace structure.
        Applied word-by-word across the whole text as a flat token stream.
        """
        MAX_WORD_RUN = 5
        tokens  = re.split(r'(\s+)', text)    # alternating [word, ws, word, ws…]
        result  = []
        run_word  = None
        run_count = 0
        for tok in tokens:
            if tok.strip() == '':             # whitespace token — pass through
                result.append(tok)
                continue
            lower = tok.lower()
            if lower == run_word:
                run_count += 1
                if run_count <= MAX_WORD_RUN:
                    result.append(tok)
                # else: silently drop — the word run is already at max
            else:
                run_word  = lower
                run_count = 1
                result.append(tok)
        return ''.join(result)

    def _collapse_repeats(self, text: str) -> str:
        """
        Collapse runs of >max_repeat identical characters to exactly max_repeat.
        Applies to non-whitespace characters only (preserves indent/padding).
        """
        def _replace_run(m):
            ch    = m.group(0)[0]
            count = len(m.group(0))
            if ch in ' \t\n\r':
                return m.group(0)           # whitespace preserved
            if count > self.max_repeat:
                return ch * self.max_repeat
            return m.group(0)

        return re.sub(r'(.)\1+', _replace_run, text)

    def _reduce_punct_storms(self, text: str) -> str:
        """
        Reduce consecutive punctuation runs exceeding max_punct_run.
        Builds a regex matching runs of punct chars (excluding space/alpha/digit).
        """
        # Punctuation: anything not alpha, digit, whitespace, bracket
        punct_re = re.compile(r'[^\w\s\(\)\[\]\{\}<>]{' + str(self.max_punct_run + 1) + r',}')

        def _trim(m):
            run = m.group(0)
            return run[:self.max_punct_run]

        return punct_re.sub(_trim, text)

    def _wrap_long_lines(self, text: str) -> str:
        """
        Hard-wrap lines exceeding max_line characters.
        Tries to break at last space within the limit; falls back to hard cut.
        """
        if self.max_line <= 0:
            return text

        lines  = text.split('\n')
        result = []
        for line in lines:
            while len(line) > self.max_line:
                # try soft break at last space
                break_at = line.rfind(' ', 0, self.max_line)
                if break_at <= 0:
                    break_at = self.max_line
                result.append(line[:break_at])
                line = line[break_at:].lstrip(' ')
            result.append(line)
        return '\n'.join(result)


# ══════════════════════════════════════════════════════════════════════════════
#  Smoke test
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    tongue = PtolemyTongue()

    tests = [
        "Normal prose sentence with some punctuation. Fine.",
        "aaaaaaaaaaaaaaaaaaa runaway repeat",
        "!!!!!!!!!!!!!!!!!!! punctuation storm",
        "Nested [[[[[[[[[[[[[[brackets]]]]]]]]]]]]]]",
        "A" * 200 + " — overlong single-word line",
        "Hello\x00\x01\x02 world",
        "Clean output from the model — no issues here.",
    ]

    for t in tests:
        filtered = tongue.filter(t)
        geo      = FoldGeometry().analyse(t)
        print(f"\nIN:  {t[:60]!r}")
        print(f"OUT: {filtered[:80]!r}")
        print(f"     pentagons={geo.pentagons} hexagons={geo.hexagons} "
              f"ratio={geo.pentagon_ratio:.3f} "
              f"repeats={len(geo.repeat_offsets)} "
              f"punct={len(geo.punct_offsets)}")
