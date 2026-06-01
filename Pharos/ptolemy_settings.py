#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy — Settings Integration Engine
======================================
Pharos Face / Root Layer

Architecture:
  - Each module ships a settings.json alongside its .py
  - PtolemySettings scans PTOL_ROOT for settings.json files
  - Each discovered file gets a tab in the Modules space of SettingsWindow
  - Sensor inputs live separately under "Inputs" (not modules)

Settings JSON standard stack (every module settings.json MUST conform):
{
    "module":      "luthspell",           # unique module id (snake_case)
    "face":        "Pharos",              # which Face this belongs to
    "display":     "LuthSpell",           # human label for the tab
    "version":     "1.0",
    "settings": {
        "key": {
            "value":    <current_value>,
            "type":     "str|int|float|bool|enum",
            "options":  [...],            # only for enum
            "label":    "Human label",
            "stub":     true|false        # true = not yet wired
        },
        ...
    }
}

Module settings.json locations (auto-discovered):
  <PTOL_ROOT>/<Face>/<module>/settings.json
  <PTOL_ROOT>/<Face>/settings.json          (Face-level, rare)

Sensor settings live in:
  <PTOL_ROOT>/Tesla/sensor_inputs.json      (managed separately)
"""

import os
import json
import glob
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE      = os.path.dirname(os.path.abspath(__file__))
PTOL_ROOT  = os.path.dirname(_HERE)
SENSOR_CFG = os.path.join(PTOL_ROOT, 'Tesla', 'sensor_inputs.json')

# ── Standard stack keys every settings.json must have ─────────────────────────
REQUIRED_KEYS = {"module", "face", "display", "version", "settings"}

# ── Default sensor input registry (stub — wired when Tesla stream active) ─────
DEFAULT_SENSOR_INPUTS = {
    "gps":         {"label": "GPS",            "active": False, "stub": True},
    "kvm":         {"label": "KVM",            "active": False, "stub": False},
    "accelerometer":{"label": "Accelerometer", "active": False, "stub": True},
    "gyroscope":   {"label": "Gyroscope",      "active": False, "stub": True},
    "microphone":  {"label": "Microphone",     "active": False, "stub": True},
    "camera":      {"label": "Camera",         "active": False, "stub": True},
    "proximity":   {"label": "Proximity",      "active": False, "stub": True},
    "light":       {"label": "Light Sensor",   "active": False, "stub": True},
    "barometer":   {"label": "Barometer",      "active": False, "stub": True},
}


class SettingsValidationError(Exception):
    pass


class ModuleSettings:
    """
    Wrapper for one module's settings.json.
    Validates against the standard stack on load.
    """

    def __init__(self, path: str):
        self.path = path
        self._data = {}
        self.load()

    def load(self):
        with open(self.path, 'r', encoding='utf-8') as f:
            self._data = json.load(f)
        self._validate()

    def _validate(self):
        missing = REQUIRED_KEYS - set(self._data.keys())
        if missing:
            raise SettingsValidationError(
                f"{self.path}: missing required keys: {missing}"
            )

    def save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=2)

    @property
    def module_id(self) -> str:
        return self._data["module"]

    @property
    def face(self) -> str:
        return self._data["face"]

    @property
    def display(self) -> str:
        return self._data["display"]

    @property
    def version(self) -> str:
        return self._data["version"]

    @property
    def settings(self) -> dict:
        return self._data["settings"]

    def get(self, key: str):
        return self._data["settings"][key]["value"]

    def set(self, key: str, value):
        if key not in self._data["settings"]:
            raise KeyError(f"Unknown setting: {key}")
        self._data["settings"][key]["value"] = value
        self.save()

    def is_stub(self, key: str) -> bool:
        return self._data["settings"].get(key, {}).get("stub", False)


class PtolemySettings:
    """
    Settings integration engine.
    Scans PTOL_ROOT for settings.json files, validates each against
    the standard stack, and exposes them for the SettingsWindow to tab.

    Usage:
        settings = PtolemySettings()
        settings.scan()
        for mod in settings.modules:
            # mod is a ModuleSettings instance
            print(mod.display, mod.settings)
    """

    def __init__(self, root: str = PTOL_ROOT):
        self.root = root
        self._modules: dict[str, ModuleSettings] = {}   # module_id → ModuleSettings
        self._sensor_inputs: dict = {}
        self._errors: list[str] = []

    def scan(self):
        """
        Discover all settings.json files under PTOL_ROOT.
        Skips .git, __pycache__, node_modules, venv.
        """
        self._modules.clear()
        self._errors.clear()
        skip_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv'}

        for dirpath, dirnames, filenames in os.walk(self.root):
            # Prune skip dirs in-place
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            if 'settings.json' in filenames:
                path = os.path.join(dirpath, 'settings.json')
                try:
                    ms = ModuleSettings(path)
                    self._modules[ms.module_id] = ms
                except (SettingsValidationError, json.JSONDecodeError, KeyError) as e:
                    self._errors.append(f"[SKIP] {path}: {e}")

        self._load_sensor_inputs()

    def _load_sensor_inputs(self):
        if os.path.exists(SENSOR_CFG):
            with open(SENSOR_CFG, 'r') as f:
                self._sensor_inputs = json.load(f)
        else:
            self._sensor_inputs = dict(DEFAULT_SENSOR_INPUTS)

    def save_sensor_inputs(self):
        os.makedirs(os.path.dirname(SENSOR_CFG), exist_ok=True)
        with open(SENSOR_CFG, 'w') as f:
            json.dump(self._sensor_inputs, f, indent=2)

    def mark_sensor_active(self, sensor_id: str, active: bool):
        if sensor_id in self._sensor_inputs:
            self._sensor_inputs[sensor_id]["active"] = active
            self.save_sensor_inputs()

    @property
    def modules(self) -> list[ModuleSettings]:
        return list(self._modules.values())

    @property
    def sensor_inputs(self) -> dict:
        return self._sensor_inputs

    @property
    def errors(self) -> list[str]:
        return list(self._errors)

    def get_module(self, module_id: str) -> Optional[ModuleSettings]:
        return self._modules.get(module_id)

    def __repr__(self):
        return (f"PtolemySettings(modules={len(self._modules)}, "
                f"sensors={len(self._sensor_inputs)}, "
                f"errors={len(self._errors)})")
