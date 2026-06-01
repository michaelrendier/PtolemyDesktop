#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CyclicContextBuffer module installer.
Run from Modules/cyclic_context_buffer/ or via modules_directory.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from module_install import PtolemyModuleInstall, InstallResult


class CyclicContextBufferInstall(PtolemyModuleInstall):

    MODULE_ID   = "cyclic_context_buffer"
    FACE        = "Philadelphos"
    DISPLAY     = "Cyclic Context Buffer"
    VERSION     = "1.0"
    MODULE_PATH = "Philadelphos.cyclic_context_buffer"
    PIP_DEPS    = []

    SETTINGS = {
        "buffer_size_lines": {
            "value": 100, "type": "int",
            "label": "Buffer size (lines)", "stub": False
        },
        "compression_model": {
            "value": "stub", "type": "enum",
            "options": ["stub", "ainur"],
            "label": "Compression model", "stub": True
        },
        "hyperindex_method": {
            "value": "octonion", "type": "enum",
            "options": ["octonion"],
            "label": "Hyperindex method", "stub": True
        },
        "blockchain_backend": {
            "value": "branch", "type": "enum",
            "options": ["branch", "stub"],
            "label": "Blockchain backend", "stub": True
        }
    }


if __name__ == "__main__":
    CyclicContextBufferInstall().run()
