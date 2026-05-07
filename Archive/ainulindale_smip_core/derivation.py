#!/usr/bin/env python3
"""
Ptolemy — SMNNIP Derivation Engine Console
============================================
Launch the curses proof engine GUI with live derivation engine + SymPy.

Usage:
    python3 derivation.py
    python3 -m Ainulindale.console.smnnip_proof_engine_console
"""
import sys
import os
import curses

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Ainulindale.console.smnnip_proof_engine_console import main

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nSMNNIP Proof Engine — session ended.")
