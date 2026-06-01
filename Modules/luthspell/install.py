#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LuthSpell module installer.
Run from Modules/luthspell/ or via modules_directory.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from module_install import PtolemyModuleInstall, InstallResult


class LuthSpellInstall(PtolemyModuleInstall):

    MODULE_ID   = "luthspell"
    FACE        = "Pharos"
    DISPLAY     = "LuthSpell"
    VERSION     = "1.0"
    MODULE_PATH = "luthspell"
    PIP_DEPS    = []

    SETTINGS = {
        "channel_prompt": {
            "value": "PROMPT", "type": "str",
            "label": "Prompt channel", "stub": False
        },
        "channel_inference": {
            "value": "INFERENCE_COORDS", "type": "str",
            "label": "Inference channel", "stub": False
        },
        "blockchain_backend": {
            "value": "branch", "type": "enum",
            "options": ["branch", "stub"],
            "label": "Blockchain backend", "stub": True
        },
        "priority_scheme": {
            "value": "rotary", "type": "enum",
            "options": ["rotary"],
            "label": "Priority scheme", "stub": True
        }
    }

    def generate_menu(self):
        return (
            "# LuthSpell — BUS Controller\n\n"
            "# LuthSpell\n"
            "wire | Wire LuthSpell to PtolBus\n"
            "set_boundary | Set halting boundary\n"
            "check | Check inference coord\n"
            "---\n"
            "# HaltingMonitor\n"
            "boundary_hash | Get current boundary hash\n"
            "halt_records | List halt records\n"
            "---\n"
        )


if __name__ == "__main__":
    LuthSpellInstall().run()
