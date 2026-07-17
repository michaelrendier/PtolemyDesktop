#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alexandria -- Engine Registry + Mouseion Pipe
"""
from __future__ import annotations
import threading
from typing import Any, Dict, Optional

_ENGINE_LOADERS: Dict[str, callable] = {}
_ENGINE_CACHE:   Dict[str, Any]      = {}
_LOCK = threading.Lock()

def register_engine(name: str, loader: callable):
    _ENGINE_LOADERS[name] = loader

def get_engine(name: str) -> Optional[Any]:
    with _LOCK:
        if name in _ENGINE_CACHE:
            return _ENGINE_CACHE[name]
        loader = _ENGINE_LOADERS.get(name)
        if loader is None:
            return None
        try:
            inst = loader()
            _ENGINE_CACHE[name] = inst
            return inst
        except Exception as e:
            print(f'[Alexandria] engine load failed: {name}: {e}')
            return None

def list_engines() -> list:
    return list(_ENGINE_LOADERS.keys())

def _load_lorenz_stirling():
    from Archimedes.Maths.LorenzStirling import LorenzStirling
    return LorenzStirling()
def _load_smnnip():
    from Ainulindale.core.smnnip_derivation_pure import SMNNIPPipeline
    return SMNNIPPipeline()
def _load_input():
    from Ainulindale.core.smnnip_derivation_pure import InputEngine
    return InputEngine
def _load_output():
    from Ainulindale.core.smnnip_derivation_pure import OutputEngine
    return OutputEngine
def _load_inversion():
    from Ainulindale.core.smnnip_derivation_pure import InversionEngine
    return InversionEngine
def _load_kcf():
    from Kryptos.kcf import KCFRegistry
    return KCFRegistry()
def _load_hyperwebster():
    from Callimachus.v09.core.hyperwebster import HyperWebster
    return HyperWebster()

register_engine('lorenz_stirling', _load_lorenz_stirling)
register_engine('smnnip',          _load_smnnip)
register_engine('input',           _load_input)
register_engine('output',          _load_output)
register_engine('inversion',       _load_inversion)
register_engine('kcf',             _load_kcf)
register_engine('hyperwebster',    _load_hyperwebster)

def _load_fractal():
    from Alexandria.FractalRenderer import FractalRenderer
    return FractalRenderer

def _load_fractal_view():
    from Alexandria.FractalRenderer import FractalView
    return FractalView

register_engine('fractal',      _load_fractal)
register_engine('fractal_view', _load_fractal_view)

_MOUSEION_PIPE: Optional[callable] = None

def set_mouseion_pipe(fn: callable):
    global _MOUSEION_PIPE
    _MOUSEION_PIPE = fn

def pipe_to_mouseion(view_name: str, data: dict):
    if _MOUSEION_PIPE is not None:
        try:
            _MOUSEION_PIPE(view_name, data)
            return
        except Exception as e:
            print(f'[Alexandria] Mouseion pipe error: {e}')
    try:
        from Pharos.PtolBus import BusMessage, CH_FACE_EVENT, Priority
        import sys
        for mod in sys.modules.values():
            if hasattr(mod, 'bus') and hasattr(mod, 'scene'):
                mod.bus.publish(BusMessage(CH_FACE_EVENT,
                    {'face': 'alexandria', 'view': view_name, 'data': data},
                    Priority.T1, sender='Alexandria'))
                break
    except Exception:
        pass
