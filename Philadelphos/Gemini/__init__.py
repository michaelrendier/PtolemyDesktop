#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.Gemini — Google Gemini feature module for Ptolemy
==============================================================
Gemini integrated as a Ptolemy component.
API key: environment variable GEMINI_API_KEY

Usage:
    from Philadelphos.Gemini import Gemini
    gemini = Gemini()
    gemini.chat("What is the SMNNIP Lagrangian?")
"""

from .gemini import Gemini, GeminiStatus

__all__ = ['Gemini', 'GeminiStatus']
