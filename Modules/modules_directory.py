#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy — Modules Directory
=============================
Modules/modules_directory.py

Run from the Modules/ directory. Discovers all available modules
(any subdirectory containing an install.py), manages installation,
and reports status.

Usage:
    python3 modules_directory.py               # interactive menu
    python3 modules_directory.py --list        # list all modules
    python3 modules_directory.py --status      # show install status
    python3 modules_directory.py --install <module_id>
    python3 modules_directory.py --install-all
    python3 modules_directory.py --verify <module_id>
    python3 modules_directory.py --verify-all

Module discovery:
    Scans Modules/ subdirectories for install.py.
    Each install.py must contain a class that subclasses PtolemyModuleInstall.
    The class is instantiated and its MODULE_ID, FACE, DISPLAY used for registry.

Tesla integration:
    modules_directory.py lives in Modules/ at PTOL_ROOT level.
    Tesla SensorStream can query it at runtime for module status.
    The directory is the single source of truth for what's installed.

Module directory layout:
    Modules/
      modules_directory.py          ← this file
      module_install.py             ← base class
      luthspell/
        install.py                  ← subclass of PtolemyModuleInstall
      cyclic_context_buffer/
        install.py
      luthspell_error_handler/
        install.py
      <new_module>/
        install.py                  ← drop in, auto-discovered
"""

import os
import sys
import json
import importlib.util
import argparse
from typing import Optional

# ── Self-location ──────────────────────────────────────────────────────────────
_MODULES_DIR = os.path.dirname(os.path.abspath(__file__))
_PTOL_ROOT   = os.path.dirname(_MODULES_DIR)
sys.path.insert(0, _PTOL_ROOT)
sys.path.insert(0, _MODULES_DIR)

from module_install import PtolemyModuleInstall, _find_ptol_root

# ── Colors ─────────────────────────────────────────────────────────────────────
_G  = "\033[92m"   # green
_Y  = "\033[93m"   # yellow
_R  = "\033[91m"   # red
_D  = "\033[90m"   # dim
_B  = "\033[96m"   # cyan
_RS = "\033[0m"    # reset


def _clr(text, code): return f"{code}{text}{_RS}"


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

class ModuleEntry:
    def __init__(self, path: str, installer_class):
        self.path            = path
        self.installer_class = installer_class
        inst                 = installer_class()
        self.module_id       = inst.MODULE_ID
        self.face            = inst.FACE
        self.display         = inst.DISPLAY
        self.version         = inst.VERSION
        self._settings_path  = os.path.join(
            _PTOL_ROOT, inst.FACE, "settings", inst.MODULE_ID, "settings.json"
        )

    @property
    def installed(self) -> bool:
        return os.path.exists(self._settings_path)

    @property
    def installed_version(self) -> Optional[str]:
        if not self.installed:
            return None
        try:
            with open(self._settings_path) as f:
                return json.load(f).get("version", "?")
        except Exception:
            return "?"

    @property
    def needs_update(self) -> bool:
        iv = self.installed_version
        return iv is not None and iv != self.version


class ModulesDirectory:

    def __init__(self):
        self._modules: dict[str, ModuleEntry] = {}
        self._scan_errors: list[str] = []
        self._discover()

    def _discover(self):
        """Scan Modules/ subdirectories for install.py files."""
        for name in sorted(os.listdir(_MODULES_DIR)):
            subdir = os.path.join(_MODULES_DIR, name)
            if not os.path.isdir(subdir):
                continue
            install_py = os.path.join(subdir, "install.py")
            if not os.path.exists(install_py):
                continue
            try:
                cls = self._load_installer(install_py, name)
                if cls is None:
                    self._scan_errors.append(f"{name}: no PtolemyModuleInstall subclass found")
                    continue
                entry = ModuleEntry(subdir, cls)
                if not entry.module_id:
                    self._scan_errors.append(f"{name}: MODULE_ID not set")
                    continue
                self._modules[entry.module_id] = entry
            except Exception as e:
                self._scan_errors.append(f"{name}: {e}")

    def _load_installer(self, path: str, mod_name: str):
        """Load install.py, return first PtolemyModuleInstall subclass found."""
        spec   = importlib.util.spec_from_file_location(f"_ptol_install_{mod_name}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for attr in vars(module).values():
            if (isinstance(attr, type)
                    and issubclass(attr, PtolemyModuleInstall)
                    and attr is not PtolemyModuleInstall):
                return attr
        return None

    # ── Commands ──────────────────────────────────────────────────────────────

    def cmd_list(self):
        print(f"\n{_clr('Ptolemy Modules Directory', _B)}")
        print(f"{_clr(_MODULES_DIR, _D)}\n")
        if not self._modules:
            print("  No modules found.")
            return
        print(f"  {'ID':<30} {'Face':<16} {'Ver':<6} Status")
        print(f"  {'─'*30} {'─'*16} {'─'*6} {'─'*12}")
        for mid, entry in self._modules.items():
            if entry.installed:
                if entry.needs_update:
                    status = _clr(f"update → {entry.version}", _Y)
                else:
                    status = _clr("installed", _G)
            else:
                status = _clr("not installed", _D)
            print(f"  {mid:<30} {entry.face:<16} {entry.version:<6} {status}")
        if self._scan_errors:
            print(f"\n  {_clr('Scan errors:', _Y)}")
            for e in self._scan_errors:
                print(f"    {_clr('!', _R)} {e}")

    def cmd_status(self):
        """Detailed status — show settings.json fields for installed modules."""
        self.cmd_list()
        print(f"\n  {_clr('Settings paths:', _D)}")
        for mid, entry in self._modules.items():
            if entry.installed:
                print(f"    {_clr('●', _G)} {entry._settings_path}")
            else:
                print(f"    {_clr('○', _D)} {entry._settings_path}  (missing)")

    def cmd_install(self, module_id: str) -> bool:
        entry = self._modules.get(module_id)
        if entry is None:
            print(f"{_clr('ERROR', _R)}: module '{module_id}' not found in directory.")
            self._suggest(module_id)
            return False
        result = entry.installer_class().run()
        return result.success

    def cmd_install_all(self):
        ok = 0; fail = 0
        for mid in self._modules:
            success = self.cmd_install(mid)
            if success: ok += 1
            else: fail += 1
        print(f"\n{'─'*44}")
        print(f"  Installed: {_clr(ok, _G)}   Failed: {_clr(fail, _R) if fail else _clr(0, _D)}")

    def cmd_verify(self, module_id: str):
        entry = self._modules.get(module_id)
        if entry is None:
            print(f"{_clr('ERROR', _R)}: module '{module_id}' not found.")
            return
        inst = entry.installer_class()
        if not entry.installed:
            print(f"{_clr('WARN', _Y)}: {module_id} not installed. Run install first.")
            return
        if inst.MODULE_PATH:
            try:
                importlib.import_module(inst.MODULE_PATH)
                print(f"{_clr('✓', _G)}  {module_id}: import OK ({inst.MODULE_PATH})")
            except ImportError as e:
                print(f"{_clr('✗', _R)}  {module_id}: import FAILED — {e}")
        else:
            print(f"{_clr('-', _D)}  {module_id}: no MODULE_PATH set, skipping import check")

    def cmd_verify_all(self):
        for mid in self._modules:
            self.cmd_verify(mid)

    def _suggest(self, module_id: str):
        candidates = [mid for mid in self._modules
                      if module_id.lower() in mid.lower()]
        if candidates:
            print(f"  Did you mean: {', '.join(candidates)}")

    # ── Interactive menu ───────────────────────────────────────────────────────

    def interactive(self):
        while True:
            print(f"\n{_clr('Ptolemy Modules Directory', _B)}")
            print("  1. List modules")
            print("  2. Status")
            print("  3. Install module")
            print("  4. Install all")
            print("  5. Verify module")
            print("  6. Verify all")
            print("  q. Quit")
            choice = input("\n  > ").strip().lower()

            if choice == "1": self.cmd_list()
            elif choice == "2": self.cmd_status()
            elif choice == "3":
                mid = input("  Module ID: ").strip()
                self.cmd_install(mid)
            elif choice == "4": self.cmd_install_all()
            elif choice == "5":
                mid = input("  Module ID: ").strip()
                self.cmd_verify(mid)
            elif choice == "6": self.cmd_verify_all()
            elif choice in ("q", "quit", "exit"): break
            else: print("  Unknown choice.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Ptolemy Modules Directory",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--list",        action="store_true")
    parser.add_argument("--status",      action="store_true")
    parser.add_argument("--install",     metavar="MODULE_ID")
    parser.add_argument("--install-all", action="store_true", dest="install_all")
    parser.add_argument("--verify",      metavar="MODULE_ID")
    parser.add_argument("--verify-all",  action="store_true", dest="verify_all")
    args = parser.parse_args()

    directory = ModulesDirectory()

    if args.list:           directory.cmd_list()
    elif args.status:       directory.cmd_status()
    elif args.install:      directory.cmd_install(args.install)
    elif args.install_all:  directory.cmd_install_all()
    elif args.verify:       directory.cmd_verify(args.verify)
    elif args.verify_all:   directory.cmd_verify_all()
    else:                   directory.interactive()


if __name__ == "__main__":
    main()
