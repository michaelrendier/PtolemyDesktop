#!/usr/bin/env bash
# ============================================================
#  Ptolemy + Ainulindalë — Surface Go System Setup
#  MODEL: apt_pip3
#
#  - No .env file — keys live in ~/.bashrc (already sourced)
#  - System-wide installs — no venv, no sandboxing
#  - Python packages: apt attempted first, pip3 fallback
#  - Node.js: NodeSource LTS via apt (only stable Ubuntu 24.04 path)
#  - Claude Code: npm install (apt-managed Node.js prerequisite)
#
#  This machine IS Ptolemy/Ainulindalë.
#  Local git server — laptop pulls from here over SSH.
#
#  Run from /home/rendier after clean OS install + updates.
#  Keys (ANTHROPIC_API_KEY, GEMINI_API_KEY, PTOL_TOKEN,
#        AINUR_TOKEN) must be exported in ~/.bashrc before
#        running, or repos will be cloned in a second pass.
#
#  Usage: chmod +x ptolemy_setup-apt_pip3.sh
#         ./ptolemy_setup-apt_pip3.sh
# ============================================================

set -eu
set -o pipefail

PTOLEMY_USER="rendier"
HOME_DIR="/home/${PTOLEMY_USER}"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Ptolemy + Ainulindalë — Surface Go Setup   ║"
echo "║   MODEL: apt_pip3 — Ubuntu 24.04 LTS         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ============================================================
# Helper: apt first, pip3 --break-system-packages fallback
# ============================================================
apt_or_pip3() {
    local pkg_apt="$1"
    local pkg_pip="$2"
    echo "    apt: python3-${pkg_apt}..."
    if sudo apt-get install -y "python3-${pkg_apt}" 2>/dev/null; then
        echo "    ok  apt: python3-${pkg_apt}"
    else
        echo "    apt failed — pip3 fallback: ${pkg_pip}..."
        pip3 install --break-system-packages "${pkg_pip}"
        echo "    ok  pip3: ${pkg_pip}"
    fi
}

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
# 2. Python packages — apt first, pip3 fallback
# ============================================================
echo "[2/6] Python packages (apt first, pip3 fallback)..."

apt_or_pip3 "lxml"     "lxml"
apt_or_pip3 "flask"    "flask"
apt_or_pip3 "requests" "requests"
apt_or_pip3 "numpy"    "numpy"
apt_or_pip3 "scipy"    "scipy"

# No reliable apt name — pip3 direct
echo "    pip3 direct: wikipedia-api PyGithub..."
pip3 install --break-system-packages wikipedia-api PyGithub

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
#    Reads tokens from ~/.bashrc exported environment
# ============================================================
echo "[5/6] Cloning repositories..."

if [ -z "${PTOL_TOKEN:-}" ]; then
    echo "  PTOL_TOKEN not set — skipping Ptolemy clone."
    echo "  After sourcing ~/.bashrc run:"
    echo "    git clone https://x-access-token:\${PTOL_TOKEN}@github.com/michaelrendier/Ptolemy ${HOME_DIR}/Ptolemy"
elif [ ! -d "${HOME_DIR}/Ptolemy" ]; then
    git clone "https://x-access-token:${PTOL_TOKEN}@github.com/michaelrendier/Ptolemy" "${HOME_DIR}/Ptolemy"
    echo "  Ptolemy cloned → ${HOME_DIR}/Ptolemy"
else
    echo "  Ptolemy already present — skipping."
fi

if [ -z "${AINUR_TOKEN:-}" ]; then
    echo "  AINUR_TOKEN not set — skipping Ainulindale clone."
    echo "  After sourcing ~/.bashrc run:"
    echo "    git clone https://\${AINUR_TOKEN}@github.com/michaelrendier/Ainulindale ${HOME_DIR}/Ainulindale"
elif [ ! -d "${HOME_DIR}/Ainulindale" ]; then
    git clone "https://${AINUR_TOKEN}@github.com/michaelrendier/Ainulindale" "${HOME_DIR}/Ainulindale"
    echo "  Ainulindale cloned → ${HOME_DIR}/Ainulindale"
else
    echo "  Ainulindale already present — skipping."
fi

# ============================================================
# 6. SSH server — enable for laptop pull access
# ============================================================
echo "[6/6] SSH server..."

sudo systemctl enable ssh
sudo systemctl start ssh
echo "  SSH running."

# ============================================================
# Done
# ============================================================
SURFACE_IP=$(ip addr show wlp1s0 2>/dev/null | grep 'inet ' | awk '{print $2}' | cut -d/ -f1 || echo "unavailable")

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  Done.                                       ║"
echo "╚══════════════════════════════════════════════╝"
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
