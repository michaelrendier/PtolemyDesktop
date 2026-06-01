#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ptolemy — Module Install Base Class
=====================================
Modules/module_install.py

Every Ptolemy module ships an install.py that subclasses PtolemyModuleInstall.
Running install.py directly from the module's own directory performs the full
install sequence for that module.

Standard install sequence:
  1. check_dependencies()   — verify pip/apt packages present
  2. register_settings()    — write/validate settings.json into module's settings dir
  3. register_menu()        — write .menu file to Pharos/menus/ (optional)
  4. post_install()         — any module-specific wiring (optional override)
  5. verify()               — smoke test the module imports cleanly

Each step is idempotent — re-running install.py is always safe.

Usage (from module directory):
    python3 install.py

Usage (from Modules Directory):
    python3 modules_directory.py --install <module_id>
    python3 modules_directory.py --install-all
    python3 modules_directory.py --list
    python3 modules_directory.py --status
"""

import os
import sys
import json
import importlib
import subprocess
from typing import Optional

# ── Resolve PTOL_ROOT from any install.py location ────────────────────────────
def _find_ptol_root(start: str) -> str:
    """Walk up from start until we find Ptolemy3.py or __init__.py at root."""
    path = os.path.abspath(start)
    for _ in range(10):
        if os.path.exists(os.path.join(path, 'Ptolemy3.py')):
            return path
        if os.path.exists(os.path.join(path, 'Pharos')) and \
           os.path.exists(os.path.join(path, 'Callimachus')):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    raise RuntimeError(f"Cannot locate PTOL_ROOT from {start}")


# ── Result object ──────────────────────────────────────────────────────────────
class InstallResult:
    def __init__(self):
        self.steps:   list[tuple[str, bool, str]] = []  # (step, ok, message)
        self.success: bool = True

    def record(self, step: str, ok: bool, msg: str = ""):
        self.steps.append((step, ok, msg))
        if not ok:
            self.success = False

    def print_report(self):
        width = 44
        print(f"\n{'─'*width}")
        for step, ok, msg in self.steps:
            icon = "✓" if ok else "✗"
            tail = f"  {msg}" if msg else ""
            print(f"  {icon}  {step:<30}{tail}")
        print(f"{'─'*width}")
        status = "INSTALL OK" if self.success else "INSTALL FAILED"
        print(f"  {status}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  BASE CLASS
# ══════════════════════════════════════════════════════════════════════════════

class PtolemyModuleInstall:
    """
    Subclass this in your module's install.py.

    Minimum required overrides:
        MODULE_ID       = "my_module"
        FACE            = "MyFace"
        DISPLAY         = "My Module"
        VERSION         = "1.0"
        SETTINGS        = { ... }   # standard stack settings dict
        PIP_DEPS        = []        # pip packages required
        APT_DEPS        = []        # apt packages required (optional)
        MODULE_PATH     = "MyFace.my_module"  # importlib path for verify step

    Optional overrides:
        post_install(result)        — additional wiring after core steps
        generate_menu() -> str      # return menu file content if needed
    """

    MODULE_ID:   str = ""
    FACE:        str = ""
    DISPLAY:     str = ""
    VERSION:     str = "1.0"
    SETTINGS:    dict = {}
    PIP_DEPS:    list = []
    APT_DEPS:    list = []
    MODULE_PATH: str = ""

    def __init__(self):
        self._here     = os.path.dirname(os.path.abspath(__file__))
        self._ptol_root = _find_ptol_root(self._here)
        self._settings_dir = os.path.join(
            self._ptol_root, self.FACE, "settings", self.MODULE_ID
        )
        self._menu_dir = os.path.join(self._ptol_root, "Pharos", "menus")
        sys.path.insert(0, self._ptol_root)

    # ── Public entry point ────────────────────────────────────────────────────

    def run(self) -> InstallResult:
        result = InstallResult()
        print(f"\nInstalling: {self.DISPLAY}  [{self.MODULE_ID}]")
        print(f"  Face:     {self.FACE}")
        print(f"  Version:  {self.VERSION}")
        print(f"  Root:     {self._ptol_root}")

        self._step_deps(result)
        self._step_settings(result)
        self._step_menu(result)
        self.post_install(result)
        self._step_verify(result)

        result.print_report()
        return result

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _step_deps(self, result: InstallResult):
        # pip
        missing_pip = []
        for pkg in self.PIP_DEPS:
            try:
                importlib.import_module(pkg.replace("-", "_").split(">=")[0].split("==")[0])
            except ImportError:
                missing_pip.append(pkg)

        if missing_pip:
            cmd = [sys.executable, "-m", "pip", "install"] + missing_pip
            try:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
                result.record("pip dependencies", True, f"installed: {missing_pip}")
            except subprocess.CalledProcessError as e:
                result.record("pip dependencies", False, f"pip failed: {e}")
                return
        else:
            result.record("pip dependencies", True, "all present")

        # apt (non-fatal — just warn)
        for pkg in self.APT_DEPS:
            chk = subprocess.run(["dpkg", "-s", pkg],
                                  capture_output=True, text=True)
            if chk.returncode != 0:
                result.record(f"apt: {pkg}", False, "not installed — run: sudo apt install " + pkg)
            else:
                result.record(f"apt: {pkg}", True)

    def _step_settings(self, result: InstallResult):
        os.makedirs(self._settings_dir, exist_ok=True)
        path = os.path.join(self._settings_dir, "settings.json")

        payload = {
            "module":   self.MODULE_ID,
            "face":     self.FACE,
            "display":  self.DISPLAY,
            "version":  self.VERSION,
            "settings": self.SETTINGS,
        }

        # If exists, merge — preserve user-modified values
        if os.path.exists(path):
            try:
                with open(path) as f:
                    existing = json.load(f)
                for key, meta in existing.get("settings", {}).items():
                    if key in payload["settings"]:
                        payload["settings"][key]["value"] = meta.get("value",
                            payload["settings"][key]["value"])
                result.record("settings.json", True, "merged (user values preserved)")
            except (json.JSONDecodeError, KeyError):
                result.record("settings.json", True, "overwritten (corrupt existing)")
        else:
            result.record("settings.json", True, "created")

        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

    def _step_menu(self, result: InstallResult):
        content = self.generate_menu()
        if content is None:
            result.record("menu file", True, "skipped (no menu defined)")
            return
        os.makedirs(self._menu_dir, exist_ok=True)
        menu_name = f"{self.FACE.lower()}_{self.MODULE_ID}.menu"
        path = os.path.join(self._menu_dir, menu_name)
        with open(path, "w") as f:
            f.write(content)
        result.record("menu file", True, menu_name)

    def _step_verify(self, result: InstallResult):
        if not self.MODULE_PATH:
            result.record("verify import", True, "skipped (no MODULE_PATH)")
            return
        try:
            importlib.import_module(self.MODULE_PATH)
            result.record("verify import", True, self.MODULE_PATH)
        except ImportError as e:
            result.record("verify import", False, str(e))
        except Exception as e:
            result.record("verify import", False, f"runtime error: {e}")

    # ── Overridable hooks ─────────────────────────────────────────────────────

    def post_install(self, result: InstallResult):
        """Override for module-specific post-install wiring."""
        pass

    def generate_menu(self) -> Optional[str]:
        """Override to return .menu file content string. Return None to skip."""
        return None


# ── Standalone entry point ────────────────────────────────────────────────────
# When a module's install.py is run directly, it should end with:
#
#   if __name__ == "__main__":
#       MyModuleInstall().run()
#
