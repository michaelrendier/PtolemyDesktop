#!/usr/bin/python3
"""
extract_menus.py — regenerate all Pharos menu files from source.

Run from Ptolemy root:
    python3 Pharos/extract_menus.py

Scans every .py file in every Face directory and writes a .menu file
into Pharos/menus/ for each module that contains public classes.
Add new faces to FACE_DIRS to include them automatically.
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Pharos.PGui import extract_module_menu, _MENU_DIR

FACE_DIRS = [
    'Alexandria',
    'Anaximander',
    'Archimedes/Maths',
    'Callimachus',
    'Kryptos',
    'Mouseion',
    'Phaleron/TreasureHunt',
    'Phaleron/APISniff',
    'Pharos',
    'Tesla',
    'Philadelphos',
]

SKIP = {'__init__.py', 'extract_menus.py'}

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total = 0
    for face_dir in FACE_DIRS:
        dirpath = os.path.join(root, face_dir)
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith('.py') or fname in SKIP:
                continue
            fpath = os.path.join(dirpath, fname)
            stem  = face_dir.replace('/', '_').lower() + '_' + fname[:-3]
            try:
                out = extract_module_menu(fpath, stem)
                # only keep non-trivial files (more than header line)
                lines = open(out).readlines()
                if len(lines) <= 2:
                    os.remove(out)
                else:
                    print(f'  OK  {stem}.menu  ({len(lines)} lines)')
                    total += 1
            except SyntaxError:
                pass  # skip files with syntax errors
            except Exception as e:
                print(f'  --  {stem}: {e}')
    print(f'\n{total} menu files written to {_MENU_DIR}')

if __name__ == '__main__':
    main()
