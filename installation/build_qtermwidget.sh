#!/usr/bin/env bash
# ============================================================
#  QTermWidget — CMake build from source
#  Target: Linux Mint Xia / Ubuntu Studio (Ubuntu 24.04 base)
#
#  Builds:
#    1. qtermwidget C++ library  (libqtermwidget5)
#    2. Python3 bindings         (via SIP — kept for Ptolemy SIP pipeline)
#
#  SIP note: SIP bindings are fully reversible — the .sip spec files
#  are interface definitions only. The C++ library is unaffected by
#  removing or regenerating bindings. Safe to use as the model for
#  all future PtolCPP SIP bindings.
#
#  Usage:
#    chmod +x build_qtermwidget.sh
#    ./build_qtermwidget.sh
#
#  After build, Python usage:
#    import QTermWidget
#    term = QTermWidget.QTermWidget()
# ============================================================

set -eu
set -o pipefail

BUILD_DIR="${HOME}/builds"
QTERMWIDGET_SRC="${BUILD_DIR}/qtermwidget"
QTERMWIDGET_BUILD="${BUILD_DIR}/qtermwidget-build"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   QTermWidget — CMake + SIP Build            ║"
echo "║   Target: Linux Mint Xia / Ubuntu Studio     ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ============================================================
# 1. System dependencies
# ============================================================
echo "[1/5] System dependencies..."

sudo apt-get update -qq
sudo apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    pkg-config \
    git \
    qtbase5-dev \
    qtbase5-dev-tools \
    libqt5opengl5-dev \
    qt5-qmake \
    libqt5x11extras5-dev \
    libkf5pty-dev \
    libkf5config-dev \
    libkf5coreaddons-dev \
    libleptonica-dev \
    python3-dev \
    python3-sip \
    python3-sip-dev \
    sip-tools \
    pyqt5-dev \
    pyqt5-dev-tools \
    python3-pyqt5

echo "  Done."

# ============================================================
# 2. Clone qtermwidget
# ============================================================
echo "[2/5] Cloning qtermwidget..."

mkdir -p "${BUILD_DIR}"

if [ -d "${QTERMWIDGET_SRC}" ]; then
    echo "  Already cloned — pulling latest..."
    git -C "${QTERMWIDGET_SRC}" pull
else
    git clone https://github.com/lxqt/qtermwidget.git "${QTERMWIDGET_SRC}"
    echo "  Cloned → ${QTERMWIDGET_SRC}"
fi

echo "  Done."

# ============================================================
# 3. Build C++ library
# ============================================================
echo "[3/5] Building C++ library..."

mkdir -p "${QTERMWIDGET_BUILD}"
cd "${QTERMWIDGET_BUILD}"

cmake "${QTERMWIDGET_SRC}" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DBUILD_PYTHON_BINDINGS=ON \
    -DPYTHON_EXECUTABLE=$(which python3)

ninja
sudo ninja install
sudo ldconfig

echo "  Library installed → /usr/local/lib"
echo "  Done."

# ============================================================
# 4. SIP Python bindings
#    BUILD_PYTHON_BINDINGS=ON in CMake handles this for
#    qtermwidget >= 1.0 which ships its own SIP spec.
#    If the version predates that flag, fall back to manual SIP.
# ============================================================
echo "[4/5] Verifying Python bindings..."

if python3 -c "import QTermWidget; print('QTermWidget:', QTermWidget.__file__)" 2>/dev/null; then
    echo "  Python bindings: OK (CMake BUILD_PYTHON_BINDINGS)"
else
    echo "  CMake bindings not found — attempting manual SIP build..."

    SIP_BUILD_DIR="${BUILD_DIR}/qtermwidget-sip"
    mkdir -p "${SIP_BUILD_DIR}"

    # Generate SIP project from the spec files shipped with qtermwidget
    SIP_SPEC="${QTERMWIDGET_SRC}/python"

    if [ ! -d "${SIP_SPEC}" ]; then
        echo "  No python/ SIP spec dir found in source. Manual SIP not possible."
        echo "  Check qtermwidget version — may need a specific tag."
        echo ""
        echo "  Suggested: try cloning a tagged release:"
        echo "    git -C ${QTERMWIDGET_SRC} checkout \$(git -C ${QTERMWIDGET_SRC} tag | sort -V | tail -1)"
        echo "  Then re-run this script."
        exit 1
    fi

    cd "${SIP_SPEC}"
    python3 -m sipbuild.tools build
    sudo python3 -m sipbuild.tools install

    echo "  Manual SIP build complete."
fi

# ============================================================
# 5. Smoke test
# ============================================================
echo "[5/5] Smoke test..."

python3 - <<'PYEOF'
try:
    import QTermWidget
    # Instantiation requires a QApplication — just check import + attr
    assert hasattr(QTermWidget, 'QTermWidget'), "QTermWidget class not found"
    print("  QTermWidget import: OK")
    print("  File:", QTermWidget.__file__)
except ImportError as e:
    print("  FAIL:", e)
    print("  QTermWidget is not importable.")
    print("  Check that /usr/local/lib is in ldconfig and")
    print("  that the .so is in a Python path directory.")
    raise SystemExit(1)
PYEOF

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Build complete.                             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Usage in Ptolemy:"
echo "    import QTermWidget"
echo "    term = QTermWidget.QTermWidget()"
echo "    scene.addWidget(term)"
echo ""
echo "  SIP spec files: ${QTERMWIDGET_SRC}/python/"
echo "  These are the model for all future PtolCPP SIP bindings."
echo ""
