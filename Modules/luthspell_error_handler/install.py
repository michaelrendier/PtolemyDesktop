#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LuthSpell Error Handler module installer.
Run from Modules/luthspell_error_handler/ or via modules_directory.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from module_install import PtolemyModuleInstall, InstallResult


class LuthSpellErrorHandlerInstall(PtolemyModuleInstall):

    MODULE_ID   = "luthspell_error_handler"
    FACE        = "Pharos"
    DISPLAY     = "Error Handler"
    VERSION     = "1.0"
    MODULE_PATH = "luthspell_error_handler"
    PIP_DEPS    = []

    SETTINGS = {
        "gc_on_fatal": {
            "value": True, "type": "bool",
            "label": "GC on FATAL", "stub": False
        },
        "gc_on_error": {
            "value": False, "type": "bool",
            "label": "GC on ERROR", "stub": False
        },
        "log_backend": {
            "value": "stdout", "type": "enum",
            "options": ["stdout", "file", "blockchain"],
            "label": "Log backend", "stub": True
        },
        "report_to_ptolemy_severity": {
            "value": "ERROR", "type": "enum",
            "options": ["INFO", "WARN", "ERROR", "FATAL"],
            "label": "Report to Ptolemy severity", "stub": False
        }
    }


if __name__ == "__main__":
    LuthSpellErrorHandlerInstall().run()
