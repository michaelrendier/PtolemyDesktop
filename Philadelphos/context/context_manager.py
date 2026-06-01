#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Philadelphos.context.context_manager
=====================================
Top-level Ptolemy HyperWebster context manager.

Aggregates:
  - claude_context.json   (Philadelphos.Ainur)
  - gemini_context.json   (Philadelphos.Gemini)
  - Runtime I/O: stdin / stdout / stderr capture

Usage:
    from Philadelphos.context.context_manager import PtolemyContext

    ctx = PtolemyContext()
    ctx.update_ai_status("claude", ready=True, model="claude-opus-4-6")
    ctx.log_event("session_start", detail="Ainur REPL launched")
    ctx.log_io(stdout="engine: Lagrangian total = -0.252365")
    ctx.save()
"""

import json
import datetime
from pathlib import Path
from typing import Optional

_CONTEXT_DIR  = Path(__file__).resolve().parent
_MASTER_FILE  = _CONTEXT_DIR / "ptolemy_context.json"
_CLAUDE_FILE  = _CONTEXT_DIR / "claude_context.json"
_GEMINI_FILE  = _CONTEXT_DIR / "gemini_context.json"


class PtolemyContext:
    """
    Read/write/aggregate the three Ptolemy HyperWebster context files.

    ptolemy_context.json  — master index (this class manages it)
    claude_context.json   — delegated to Ainur module
    gemini_context.json   — delegated to Gemini module

    The master context caches the last-known status of each AI feature
    and maintains a Ptolemy-level I/O log and event stream.
    """

    def __init__(self, auto_load: bool = True):
        self._data: dict = {}
        if auto_load:
            self.load()

    # ── Load / Save ───────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load ptolemy_context.json from disk."""
        try:
            with open(_MASTER_FILE, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def save(self) -> None:
        """Write current state back to ptolemy_context.json."""
        self._data.setdefault("metadata", {})
        self._data["metadata"]["last_updated"] = (
            datetime.datetime.utcnow().isoformat() + "Z"
        )
        with open(_MASTER_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ── AI feature status ─────────────────────────────────────────────────────

    def update_ai_status(
        self,
        ai_name: str,          # "claude" or "gemini"
        ready:   bool = False,
        model:   Optional[str] = None,
        error:   Optional[str] = None,
    ) -> None:
        """
        Update the last_status entry for an AI feature in the master context.
        Saves immediately.
        """
        self._data.setdefault("ai_features", {}).setdefault(ai_name, {})
        status = {
            "ready": ready,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }
        if model:
            status["model"] = model
        if error:
            status["error"] = error
        self._data["ai_features"][ai_name]["last_status"] = status

        active = self._data.setdefault("metadata", {}).setdefault("active_ai", [])
        if ready and ai_name not in active:
            active.append(ai_name)
        elif not ready and ai_name in active:
            active.remove(ai_name)

        self.save()

    # ── I/O logging ───────────────────────────────────────────────────────────

    def log_io(
        self,
        stdin:  Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        source: Optional[str] = None,   # e.g. "ainur", "gemini", "derivation"
    ) -> None:
        """
        Append I/O to the master ptolemy_context.json runtime streams.
        Also propagates to the correct child context file if source given.
        Saves immediately.
        """
        now  = datetime.datetime.utcnow().isoformat() + "Z"
        rt   = self._data.setdefault("runtime", {})
        ios  = rt.setdefault("io_streams", {})
        max_e = 200

        for key, val in [("stdin", stdin), ("stdout", stdout), ("stderr", stderr)]:
            if val is not None:
                stream = ios.setdefault(key, {"log": [], "max_entries": max_e})
                entry  = {"ts": now, "text": val}
                if source:
                    entry["source"] = source
                stream["log"].append(entry)
                if len(stream["log"]) > max_e:
                    stream["log"] = stream["log"][-max_e:]

        self.save()

    # ── Event log ─────────────────────────────────────────────────────────────

    def log_event(
        self,
        event:  str,
        detail: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        """
        Append a named event to the master event stream.
        Saves immediately.
        """
        entry = {
            "ts":    datetime.datetime.utcnow().isoformat() + "Z",
            "event": event,
        }
        if detail:
            entry["detail"] = detail
        if source:
            entry["source"] = source

        events = self._data.setdefault("runtime", {}).setdefault("events", [])
        events.append(entry)
        if len(events) > 500:
            self._data["runtime"]["events"] = events[-500:]

        self._data.setdefault("session_log", []).append(entry)
        self.save()

    # ── Child context snapshot ────────────────────────────────────────────────

    def snapshot_children(self) -> dict:
        """
        Read both child context files and return a summary dict.
        Does not modify any files.
        """
        result = {}
        for name, path in [("claude", _CLAUDE_FILE), ("gemini", _GEMINI_FILE)]:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    child = json.load(f)
                result[name] = {
                    "model":         child.get("identity", {}).get("model"),
                    "last_updated":  child.get("metadata", {}).get("last_updated"),
                    "session_count": child.get("metadata", {}).get("session_count", 0),
                    "engine":        child.get("smnnip_knowledge", {})
                                         .get("verified_results", {})
                                         .get("engine_available"),
                }
            except (FileNotFoundError, json.JSONDecodeError):
                result[name] = {"error": "context file unreadable"}
        return result

    def __repr__(self) -> str:
        snap = self.snapshot_children()
        return (
            f"PtolemyContext("
            f"claude={snap.get('claude', {}).get('model')}, "
            f"gemini={snap.get('gemini', {}).get('model')})"
        )
