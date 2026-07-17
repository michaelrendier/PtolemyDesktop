#!/usr/bin/env bash
# ============================================================
#  Ptolemy + Ainulindalë — Surface Go System Setup
#  MODEL: venv
#
#  - Python packages isolated in /home/rendier/.ptolemy_venv
#  - Activate: source ~/.ptolemy_venv/bin/activate
#  - Node.js: NodeSource LTS via apt
#  - Claude Code: npm install (user-level)
#  - Keys in ~/.bashrc — no .env file
#
#  Use this model if you need dependency isolation or are
#  running multiple Python projects with conflicting packages.
#  For a machine that IS Ptolemy, apt_pip3 is preferred.
#
#  Usage: chmod +x ptolemy_setup-venv.sh
#         ./ptolemy_setup-venv.sh
# ============================================================

set -eu
set -o pipefail

PTOLEMY_USER="rendier"
HOME_DIR="/home/${PTOLEMY_USER}"
VENV_DIR="${HOME_DIR}/.ptolemy_venv"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Ptolemy + Ainulindalë — Surface Go Setup   ║"
echo "║   MODEL: venv — Ubuntu 24.04 LTS             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ============================================================
# 1. Core system packages
# ============================================================
echo "[1/6] Core system packages..."

sudo apt-get update -qq
sudo apt-get install -y \
    git \
    curl \
    wget \
    ripgrep \
    build-essential \
    cmake \
    pkg-config \
    openssh-server \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    sqlite3 \
    libsqlite3-dev \
    openssl \
    libssl-dev \
    ca-certificates \
    gnupg \
    unzip \
    htop \
    tree \
    barrier

echo "  Done."

# ============================================================
# 2. Create venv + install Python packages inside it
# ============================================================
echo "[2/6] Python venv + packages..."

if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
    echo "  Venv created: ${VENV_DIR}"
fi

"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install \
    requests \
    lxml \
    flask \
    wikipedia-api \
    PyGithub \
    numpy \
    scipy

echo "  Done."

# ============================================================
# 3. Node.js + npm via apt (NodeSource LTS)
# ============================================================
echo "[3/6] Node.js + npm (NodeSource LTS via apt)..."

if command -v node &>/dev/null; then
    echo "  Already installed: $(node --version)"
else
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
    echo "  Node.js: $(node --version)"
    echo "  npm:     $(npm --version)"
fi

# ============================================================
# 4. Claude Code via npm (user-level, no sudo)
# ============================================================
echo "[4/6] Claude Code..."

mkdir -p "${HOME_DIR}/.npm-global"
npm config set prefix "${HOME_DIR}/.npm-global"
export PATH="${HOME_DIR}/.npm-global/bin:$PATH"

if command -v claude &>/dev/null; then
    echo "  Already installed: $(claude --version)"
else
    npm install -g @anthropic-ai/claude-code
    echo "  Installed: $(claude --version)"
fi

# ============================================================
# 5. Clone Ptolemy + Ainulindalë
# ============================================================
echo "[5/6] Cloning repositories..."

if [ -z "${PTOL_TOKEN:-}" ]; then
    echo "  PTOL_TOKEN not set — skipping Ptolemy clone."
elif [ ! -d "${HOME_DIR}/Ptolemy" ]; then
    git clone "https://x-access-token:${PTOL_TOKEN}@github.com/michaelrendier/Ptolemy" "${HOME_DIR}/Ptolemy"
    echo "  Ptolemy cloned → ${HOME_DIR}/Ptolemy"
else
    echo "  Ptolemy already present — skipping."
fi

if [ -z "${AINUR_TOKEN:-}" ]; then
    echo "  AINUR_TOKEN not set — skipping Ainulindale clone."
elif [ ! -d "${HOME_DIR}/Ainulindale" ]; then
    git clone "https://${AINUR_TOKEN}@github.com/michaelrendier/Ainulindale" "${HOME_DIR}/Ainulindale"
    echo "  Ainulindale cloned → ${HOME_DIR}/Ainulindale"
else
    echo "  Ainulindale already present — skipping."
fi

# ============================================================
# 6. SSH server + venv activation in ~/.bashrc
# ============================================================
echo "[6/6] SSH server + venv activation..."

sudo systemctl enable ssh
sudo systemctl start ssh

if ! grep -q "ptolemy_venv" "${HOME_DIR}/.bashrc"; then
    cat >> "${HOME_DIR}/.bashrc" << 'EOF'

# Ptolemy venv — activate on shell start
source "$HOME/.ptolemy_venv/bin/activate"
EOF
    echo "  Venv activation added to ~/.bashrc"
fi

# ============================================================
# Done
# ============================================================
SURFACE_IP=$(ip addr show wlp1s0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 || echo "unavailable")

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Done.                                       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Venv: ${VENV_DIR}"
echo "  Activate manually: source ${VENV_DIR}/bin/activate"
echo ""
echo "  Surface Go IP: ${SURFACE_IP}"
echo ""
echo "  Laptop pulls via SSH:"
echo "    git clone ssh://${PTOLEMY_USER}@${SURFACE_IP}/home/${PTOLEMY_USER}/Ptolemy"
echo "    git clone ssh://${PTOLEMY_USER}@${SURFACE_IP}/home/${PTOLEMY_USER}/Ainulindale"
echo ""
echo "  Authenticate Claude Code:"
echo "    claude login"
echo ""
