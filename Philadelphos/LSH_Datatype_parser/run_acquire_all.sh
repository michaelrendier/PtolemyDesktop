#!/usr/bin/env bash
# run_acquire_all.sh — Run acquire.py on each of the 26 per-letter word pages.
#
# Usage:
#   ./run_acquire_all.sh              # all 26 letters
#   ./run_acquire_all.sh a b c        # specific letters only
#   ./run_acquire_all.sh --wikipedia  # include Wikipedia queries (slower)
#
# acquire.py skips words that already have a complete record (resume-safe).
# Each letter's run logs to logs/acquire_<letter>.log.
#
# Rough timing: ~3s/word × 370k words = weeks of wall time.
# Run a subset first: ./run_acquire_all.sh a
# Or run letters in parallel across tmux panes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAGES_DIR="$SCRIPT_DIR/word_pages"
ACQUIRE="$SCRIPT_DIR/acquire.py"
LOG_DIR="$SCRIPT_DIR/logs"

mkdir -p "$LOG_DIR"

WIKIPEDIA=""
LETTERS=()

for arg in "$@"; do
    case "$arg" in
        --wikipedia|-w) WIKIPEDIA="--wikipedia" ;;
        [a-z])          LETTERS+=("$arg") ;;
        *)              echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# Default: all 26 letters
if [ ${#LETTERS[@]} -eq 0 ]; then
    LETTERS=( a b c d e f g h i j k l m n o p q r s t u v w x y z )
fi

echo "Letters to process: ${LETTERS[*]}"
echo "Wikipedia: ${WIKIPEDIA:-off}"
echo "Logs: $LOG_DIR"
echo ""

for letter in "${LETTERS[@]}"; do
    page="$PAGES_DIR/words_${letter}.txt"
    log="$LOG_DIR/acquire_${letter}.log"

    if [ ! -f "$page" ]; then
        echo "[$letter] SKIP — $page not found"
        continue
    fi

    count=$(wc -l < "$page")
    echo "[$letter] Starting — $count words → $log"

    python3 "$ACQUIRE" --file "$page" $WIKIPEDIA 2>&1 | tee "$log"

    echo "[$letter] Done."
    echo ""
done

echo "All letters complete."
