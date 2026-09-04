#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
The Enigma visualiser is nes-viewport's SCREEN-LOCKED archetype: the map (the
subdued photo) and the viewport are the same size, so there is no scrolling.
This test is the matching acceptance gate: no offset ever moves, no scrollbar,
nothing clips, and the SVG overlay stays registered inside the map rectangle.
"""

import os
import sys
import importlib.util

import pytest

_SKILL = os.path.expanduser('~/.claude/skills/nes-viewport/assets/viewport.py')


def _load_viewport():
    spec = importlib.util.spec_from_file_location('nes_viewport', _SKILL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['nes_viewport'] = mod          # dataclass needs this resolvable
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.skipif(not os.path.isfile(_SKILL), reason='nes-viewport skill not installed')
def test_screen_locked_no_scroll():
    vp_mod = _load_viewport()
    W, H = 918, 1062                      # enigma_map.png size
    vp = vp_mod.Viewport(cw=W, ch=H, vw=W, vh=H)

    # CLAMP: content == viewport → no room to move in either axis
    assert vp.max_ox == 0 and vp.max_oy == 0
    assert vp.max_oy == max(0, vp.ch - vp.vh)

    # every navigation command is an offset no-op
    for move in ('up', 'down', 'left', 'right', 'page_up', 'page_down',
                 'move_to_top', 'move_to_bottom', 'move_to_left', 'move_to_right'):
        getattr(vp, move)()
        assert (vp.ox, vp.oy) == (0, 0), move
    vp.set_offset(x=-10 ** 9, y=10 ** 9)
    assert (vp.ox, vp.oy) == (0, 0)

    # FLUSH: the whole map is visible, top row to bottom row, nothing clipped
    assert vp.first_visible_row() == 0
    assert vp.last_visible_row() == H - 1

    # THUMB: a screen-locked pane hides its bar (thumb fills the track)
    bar = vp.vbar(track_len=100)
    assert bar.visible is False
    assert bar.length == 100 and bar.pos == 0


@pytest.mark.skipif('PyQt6' not in sys.modules and importlib.util.find_spec('PyQt6') is None,
                    reason='PyQt6 not available')
def test_overlay_registered_inside_map():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ.setdefault('PTOLEMY_PHAROS', '0')
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from Kryptos.enigma_view import EnigmaVisualiser
    from Kryptos.Ciphers.common import ALPHABET

    v = EnigmaVisualiser()
    W, H = v.W, v.H
    assert v.size().width() == W and v.size().height() == H     # fixed == map

    # every overlay contact point lands inside the map rectangle
    pts = list(v._lamp_xy.values()) + list(v._key_xy.values())
    pts += [v._plug_pt(c) for c in range(26)]
    for name in ('reflector', 'III', 'II', 'I', 'ETW'):
        pts += [v._ladder_pt(name, c) for c in range(26)]
    for p in pts:
        assert 0 <= p.x() <= W and 0 <= p.y() <= H

    # the drawn path is exactly the engine's trace_path hop chain
    v.set_text('AAAAA')
    for _ in range(5):
        v.type_next()
    line_pts, legs = v._polyline()
    assert len(line_pts) == 14                # 13 hops + final out
    assert legs[0] == 'forward' and legs[-1] == 'return'
    assert ''.join(p.lamp for p in v._paths) == 'BDZGO'
