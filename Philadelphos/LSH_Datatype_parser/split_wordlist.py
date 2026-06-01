#!/usr/bin/env python3
"""
split_wordlist.py — Split words_alpha.txt into 26 per-letter page files.

Output: word_pages/words_a.txt … words_z.txt
Each file contains one word per line, all starting with that letter.

Usage:
    python3 split_wordlist.py
    python3 split_wordlist.py --src /path/to/wordlist.txt --out ./word_pages
"""

import argparse
import os
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR  = Path(__file__).resolve().parent
DEFAULT_SRC = SCRIPT_DIR / '../../../working/dictionary/words_alpha.txt'
DEFAULT_OUT = SCRIPT_DIR / 'word_pages'


def split(src: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    buckets = defaultdict(list)
    skipped = 0

    with open(src, encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if not word:
                continue
            first = word[0]
            if first.isalpha():
                buckets[first].append(word)
            else:
                skipped += 1

    for letter in sorted(buckets):
        out_path = out_dir / f'words_{letter}.txt'
        out_path.write_text('\n'.join(buckets[letter]) + '\n', encoding='utf-8')
        print(f'  {letter}  {len(buckets[letter]):>6} words  →  {out_path.name}')

    total = sum(len(v) for v in buckets.values())
    print(f'\nTotal: {total} words across {len(buckets)} letters. Skipped: {skipped}')
    print(f'Output: {out_dir}')


def main():
    parser = argparse.ArgumentParser(description='Split word list into 26 per-letter files')
    parser.add_argument('--src', default=str(DEFAULT_SRC),
                        help='Source word list (newline-delimited)')
    parser.add_argument('--out', default=str(DEFAULT_OUT),
                        help='Output directory for word_pages/')
    args = parser.parse_args()

    src = Path(args.src).resolve()
    out = Path(args.out).resolve()

    if not src.exists():
        print(f'ERROR: source not found: {src}')
        raise SystemExit(1)

    print(f'Source: {src}')
    split(src, out)


if __name__ == '__main__':
    main()
