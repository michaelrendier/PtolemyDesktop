#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
CommandInput — redirects to Ainulindale curses console.

The Qt widget command window (PyQt5/WebKit/OpenGL/espeak stack)
has been superseded by the Python3 built-in curses console in:

    Philadelphos/Ainulindale/console/smnnip_proof_engine_console.py

Previous implementation archived as CommandInput.py.bak
"""

import curses
from Ainulindale.console.smnnip_proof_engine_console import main

def launch():
    curses.wrapper(main)

if __name__ == '__main__':
    launch()
