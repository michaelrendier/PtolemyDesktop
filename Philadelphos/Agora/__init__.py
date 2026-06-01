#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.Agora — Ptolemy dual-AI chat
==========================================
Routes queries to Claude and Gemini independently and in parallel.
Model independence is preserved for sigma valuation.

Usage:
    from Philadelphos.Agora import Agora
    agora = Agora()
    result = agora.query("What is the SMNNIP Noether current?")
    print(result["claude"])
    print(result["gemini"])
"""

from .agora import Agora, AgoraResult

__all__ = ['Agora', 'AgoraResult']
