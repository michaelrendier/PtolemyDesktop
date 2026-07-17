#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier@thewanderinggod.tech'

"""
SystemTrayIcon.py — Ptolemy System Tray
=========================================
Pharos Face

Delegates to PtolDesktop.DualTrayMenu for dual-menu behaviour:
  Left click  → User Input Menu  (shell, Face quick-launch)
  Right click → System Menu      (sensors, settings, exit)

Icon: ptol_button.svg (PTOL power symbol)
"""

from Pharos.PtolDesktop import DualTrayMenu as _DualTrayMenu
from PyQt6.QtWidgets import QSystemTrayIcon

class SystemTrayIcon(_DualTrayMenu):
    """
    Ptolemy system tray icon.
    Thin subclass of DualTrayMenu — all logic lives there.
    Legacy API maintained: SystemTrayIcon(icon, parent) still works,
    icon arg is accepted but ignored (resolved internally from SVG files).
    """
    def __init__(self, icon=None, parent=None):
        super().__init__(ptolemy=parent, parent=parent)
