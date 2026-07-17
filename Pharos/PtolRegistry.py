#!/usr/bin/python3
# -*- coding: utf-8 -*-
__author__ = 'rendier'

"""
Pharos/PtolRegistry.py — Face Lifecycle Registry
=================================================
Extracted from Ptolemy3.py v0.9 (was embedded class PtolBus — renamed to
FaceRegistry to avoid collision with Pharos/PtolBus.py message bus).

self.bus     = FaceRegistry   (launch / suspend / terminate faces)
self.msg_bus = PtolBus        (pub-sub message bus, priority queue)
"""

import os
import importlib
from subprocess import Popen, PIPE

from PyQt6.QtCore import QObject, pyqtSignal


class FaceRegistry(QObject):
    """
    Central face registry.  Owns the face lifecycle and enforces the
    threading contract: faces not on screen are not processing.

    Usage:
        window = self.bus.launch(TreasureHunt)
        self.bus.suspend(window.face_id)
        self.bus.resume(window.face_id)
        self.bus.terminate(window.face_id)
    """

    face_launched   = pyqtSignal(str)
    face_suspended  = pyqtSignal(str)
    face_resumed    = pyqtSignal(str)
    face_terminated = pyqtSignal(str)

    def __init__(self, ptolemy):
        super().__init__(ptolemy)
        self.Ptolemy   = ptolemy
        self._registry = {}
        self._counter  = 0

    # ── Launch ────────────────────────────────────────────────────────────────

    def launch(self, face_cls, *args, use_vispy=False, **kwargs):
        from Pharos.PGui import PWindow

        face_id = f"{face_cls.__name__}_{self._counter}"
        self._counter += 1

        face = face_cls(*args, parent=self.Ptolemy, **kwargs)

        if hasattr(face, '_ptol_id'):
            face._ptol_id  = face_id
            face._ptol_bus = self
            if hasattr(face, 'ptol_start'):
                face.ptol_start()

        timers = getattr(face, '_ptol_timers', [])
        thread = getattr(face, '_ptol_thread', None)

        if use_vispy:
            native = face.native
            pwin = PWindow(native, title=face_cls.__name__,
                           face_id=face_id, bus=self,
                           ptolemy=self.Ptolemy)
        else:
            pwin = PWindow(face, title=face_cls.__name__,
                           face_id=face_id, bus=self,
                           ptolemy=self.Ptolemy)

        self.Ptolemy.scene.addItem(pwin)

        self._registry[face_id] = {
            'face':   face,
            'pwin':   pwin,
            'thread': thread,
            'timers': timers,
            'state':  'running',
            'cls':    face_cls.__name__,
        }

        self.face_launched.emit(face_id)
        return pwin

    # ── Subprocess ────────────────────────────────────────────────────────────

    def launch_subprocess(self, script_path, *args):
        cmd = ['python3', script_path] + list(args)
        proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
        face_id = f"subprocess_{os.path.basename(script_path)}_{self._counter}"
        self._counter += 1
        self._registry[face_id] = {
            'face':   None,
            'pwin':   None,
            'thread': None,
            'timers': [],
            'state':  'subprocess',
            'proc':   proc,
            'cls':    script_path,
        }
        return proc

    # ── Dynamic import ────────────────────────────────────────────────────────

    def import_face(self, module_path, class_name):
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name)

    # ── Suspend / Resume / Terminate ─────────────────────────────────────────

    def suspend(self, face_id):
        rec = self._registry.get(face_id)
        if not rec or rec['state'] != 'running':
            return
        face = rec.get('face')
        if face and hasattr(face, 'ptol_stop'):
            face.ptol_stop()
        if rec['thread']:
            rec['thread'].quit()
        for timer in rec['timers']:
            timer.stop()
        rec['state'] = 'suspended'
        self.face_suspended.emit(face_id)

    def resume(self, face_id):
        rec = self._registry.get(face_id)
        if not rec or rec['state'] != 'suspended':
            return
        if rec['thread']:
            rec['thread'].start()
        for timer in rec['timers']:
            timer.start()
        rec['state'] = 'running'
        face = rec.get('face')
        if face and hasattr(face, 'ptol_start'):
            face.ptol_start()
        self.face_resumed.emit(face_id)

    def terminate(self, face_id):
        rec = self._registry.get(face_id)
        if not rec:
            return

        if rec['state'] == 'subprocess':
            proc = rec.get('proc')
            if proc:
                proc.terminate()
            del self._registry[face_id]
            return

        self.suspend(face_id)
        if rec['thread']:
            rec['thread'].wait(2000)

        pwin = rec.get('pwin')
        if pwin and pwin.scene():
            self.Ptolemy.scene.removeItem(pwin)

        face = rec.get('face')
        if face:
            if hasattr(face, 'ptol_close'):
                face.ptol_close()
            try:
                face.deleteLater()
            except Exception:
                pass

        del self._registry[face_id]
        self.face_terminated.emit(face_id)

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self):
        return {fid: {'cls': r['cls'], 'state': r['state']}
                for fid, r in self._registry.items()}
