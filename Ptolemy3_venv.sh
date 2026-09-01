#!/usr/bin/env bash
# Ptolemy3_venv.sh — build PtolemyDesktop/.venv, LAYERED ON the ValaQuenta venv.
#
# The derivation-engine UI (ValaQuenta --curses) is the maths manual/settings
# face that runs alongside the Ptolemy chat window; both need the ValaQuenta
# engines. This venv "necessarily requires the ValaQuenta venv": a .pth file
# makes every ValaQuenta-venv package + the ValaQuenta package itself visible
# here, then PyQt6 / vispy (desktop-only) are installed on top.
set -eu
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEPLACE="$(cd "$HERE/.." && pwd)"
VQ_SP="$THEPLACE/ValaQuenta/.venv/lib/python3.12/site-packages"

[ -d "$VQ_SP" ] || { echo "ValaQuenta venv not found at $VQ_SP — build it first (ValaQuenta/env.sh)"; exit 1; }

python3 -m venv "$HERE/.venv"
PD_SP="$HERE/.venv/lib/python3.12/site-packages"
printf '%s\n%s\n%s\n' "$VQ_SP" "$THEPLACE" "$HERE" > "$PD_SP/_valaquenta_layer.pth"

"$HERE/.venv/bin/pip" install --quiet PyQt6 vispy

"$HERE/.venv/bin/python3" - <<'PY'
import sys
from ValaQuenta.__main__ import _register_all
from ValaQuenta.engine.console_curses import DerivationBrowser
import PyQt6, vispy, numpy, sympy
reg = _register_all()
print(f"OK  py{sys.version.split()[0]}  ValaQuenta {len(reg.list_modules())} engines  "
      f"PyQt6 {PyQt6.QtCore.PYQT_VERSION_STR if hasattr(PyQt6,'QtCore') else 'ok'}  "
      f"vispy {vispy.__version__}  numpy {numpy.__version__}")
PY
