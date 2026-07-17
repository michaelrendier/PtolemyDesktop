#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.Ainur — Claude API feature module for Ptolemy
===========================================================
Claude (Anthropic) integrated as a Ptolemy component.
API key: environment variable AINUR_TOKEN

Usage:
    from Philadelphos.Ainur import Ainur
    ainur = Ainur()
    ainur.chat("What is the Lagrangian of the SMNNIP?")
"""

from .ainur import Ainur, AinurStatus

__all__ = ['Ainur', 'AinurStatus']
