# Ptolemy + Ainulindalë — Installation Guide

> **Living document.** Each supported architecture and install model has its own section.
> When a new branch or platform is added, its `inxi` output and setup requirements belong here.

---

## Table of Contents

- [Philosophy](#philosophy)
- [Environment Variables](#environment-variables)
- [Supported Platforms](#supported-platforms)
- [Ubuntu 24.04 LTS — Surface Go (Current Reference Node)](#ubuntu-2404-lts--surface-go-current-reference-node)
- [Ubuntu 24.04 LTS — Generic x86_64](#ubuntu-2404-lts--generic-x86_64)
- [Arch Linux](#arch-linux)
- [Gentoo](#gentoo)
- [CentOS / RHEL Stream (Server)](#centos--rhel-stream-server)
- [Install Models](#install-models)
- [Claude Code](#claude-code)
- [Post-Install](#post-install)

---

## Philosophy

This machine **is** Ptolemy/Ainulindalë. There is no sandboxing, no virtual environment by default, no separation between the OS and the project. The system packages **are** the project dependencies. The install model reflects this.

Venv and container variants exist as documented alternatives — not defaults.

---

## Environment Variables

Ptolemy and Ainulindalë authenticate to external services exclusively through shell environment variables. There is no `.env` file, no secrets manager, no credential store. Keys and tokens are owned by the user, declared once in the user's console environment, and are never committed to any repository.

The console environment on Ubuntu is established by `~/.bashrc` — the script that runs every time a new terminal session opens. Any variable exported there is immediately available to every process launched from that shell, including Python scripts, Claude Code, git, and Flask.

### Step 1 — Open ~/.bashrc

```bash
nano ~/.bashrc
```

### Step 2 — Add the Ptolemy block at the bottom

```bash
# ── Ptolemy/Ainulindalë ──────────────────────────────────────
# Service                          Variable
# ─────────────────────────────────────────────────────────────
# Anthropic API                    ANTHROPIC_API_KEY
# Google Gemini API                GEMINI_API_KEY
# GitHub fine-scoped (repo mgmt)   PTOL_TOKEN
# GitHub classic (push/pull)       AINUR_TOKEN
# ─────────────────────────────────────────────────────────────
export PATH="$HOME/.npm-global/bin:$PATH"

export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
export PTOL_TOKEN="your_ptol_token_here"
export AINUR_TOKEN="your_ainur_token_here"
# ─────────────────────────────────────────────────────────────
```

Save and close: `Ctrl+O` → `Enter` → `Ctrl+X`

### Step 3 — Load the environment into the current session

Writing to `~/.bashrc` does not affect the terminal you have open right now. Source it to apply immediately without opening a new terminal:

```bash
source ~/.bashrc
```

### Step 4 — Verify all four variables are live

```bash
echo $ANTHROPIC_API_KEY
echo $GEMINI_API_KEY
echo $PTOL_TOKEN
echo $AINUR_TOKEN
```

Each line should print its value. A blank line means that variable is not set — go back to `~/.bashrc` and check for typos or missing `export`.

### Variable reference

| Variable | Service | Type | Used by |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API | API key | Claude Code, direct API calls |
| `GEMINI_API_KEY` | Google Gemini API | API key | Gemini model experiments |
| `PTOL_TOKEN` | GitHub Ptolemy | Fine-scoped PAT | Repo management, CI |
| `AINUR_TOKEN` | GitHub Ainulindalë | Classic PAT | Push / pull |

### Security note

`~/.bashrc` is a plaintext file in your home directory. It is readable only by your user account (mode 644 by default — consider `chmod 600 ~/.bashrc`). It is never sourced by system processes or other users. Do not add these variables to `/etc/environment`, `/etc/profile`, or any system-wide location.

---

## Supported Platforms

| Platform | Arch | Status | Script | inxi |
|---|---|---|---|---|
| Ubuntu 24.04 LTS | x86_64 | ✅ Reference | `ptolemy_setup-apt_pip3.sh` | [Surface Go](#ubuntu-2404-lts--surface-go-current-reference-node) |
| Ubuntu 24.04 LTS | x86_64 | ✅ Generic | `ptolemy_setup-apt_pip3.sh` | — |
| Arch Linux | x86_64 | 🔲 Planned | — | — |
| Gentoo | x86_64 | 🔲 Planned | — | — |
| CentOS Stream / RHEL | x86_64 | 🔲 Planned | — | — |

---

## Ubuntu 24.04 LTS — Surface Go (Current Reference Node)

**Role:** Primary Ptolemy/Ainulindalë development node. Local git server. Barrier KVM client. Claude Code + all AI interfaces. Laptop pulls from this machine over SSH.

**Hardware:** Microsoft Surface Go Gen 1

```
System:
  Kernel: 6.18.7-surface-1 arch: x86_64  Distro: Ubuntu 24.04.4 LTS (Noble Numbat)
Machine:
  Type: Laptop  System: Microsoft  product: Surface Go  v: 1
  UEFI: Microsoft  v: 1.0.38  date: 09/20/2022
CPU:
  model: Intel Pentium 4415Y  bits: 64  type: MT MCP  arch: Amber/Kaby Lake
  cores: 2  threads: 4  max: 1600 MHz  bogomips: 12799
Memory:
  RAM: total: 8 GiB  available: 7.65 GiB
Graphics:
  Device-1: Intel HD Graphics 615  driver: i915  arch: Gen-9.5
  OpenGL: v: 4.6  renderer: Mesa Intel HD Graphics 615 (KBL GT2)
Storage:
  ID-1: /dev/nvme0n1  vendor: Toshiba  size: 119.24 GiB  speed: 15.8 Gb/s
Network:
  Device-1: Qualcomm Atheros QCA6174 802.11ac  driver: ath10k_pci
Audio:
  Device-1: Intel Sunrise Point-LP HD Audio  driver: snd_hda_intel
```

**Install script:** `ptolemy_setup-apt_pip3.sh`

**Model:** `apt_pip3` — see [Install Models](#install-models)

**Notes:**
- Kernel is `linux-surface` fork for Surface hardware support
- WiFi adapter (QCA6174) runs warm — monitor temps under sustained network load
- CPU governor defaults to `powersave` — switch to `performance` for benchmark runs:
  ```bash
  echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
  ```
- Barrier runs as KVM client (server is the laptop)
- SSH server enabled — laptop clones/pulls via:
  ```bash
  git clone ssh://rendier@<surface-ip>/home/rendier/Ptolemy
  git clone ssh://rendier@<surface-ip>/home/rendier/Ainulindale
  ```

---

## Ubuntu 24.04 LTS — Generic x86_64

Same script as the Surface Go reference node. No Surface-specific kernel required.

**Prerequisites:**
- Ubuntu 24.04 LTS clean install, fully updated
- `~/.bashrc` environment variables set (see [Environment Variables](#environment-variables))

**Run:**
```bash
chmod +x ptolemy_setup-apt_pip3.sh
./ptolemy_setup-apt_pip3.sh
```

---

## Arch Linux

> 🔲 **Not yet implemented.** Section reserved for when an Arch branch is established.

**Expected differences from Ubuntu model:**
- `pacman -S` replaces `apt-get install`
- No NodeSource repo needed — Node.js LTS available directly: `pacman -S nodejs npm`
- Python packages via `pacman` where available (`python-lxml`, `python-flask`, `python-numpy`, `python-scipy`), AUR or pip for remainder
- No `--break-system-packages` flag needed — Arch pip installs system-wide by default
- `systemctl enable sshd` (not `ssh`)
- Barrier available in AUR: `yay -S barrier`

**inxi output:** *(add when Arch node is established)*

**Install script:** *(to be written — `ptolemy_setup-arch.sh`)*

---

## Gentoo

> 🔲 **Not yet implemented.** Section reserved for when a Gentoo branch is established.

**Expected differences from Ubuntu model:**
- `emerge` replaces `apt-get`
- USE flags will need to be documented per package
- Node.js via `net-libs/nodejs` — verify LTS version in portage
- Python packages via `dev-python/*` where available, pip for remainder
- Compilation times significant on low-power hardware — document `MAKEOPTS` and cross-compile options
- `rc-update add sshd default` (OpenRC) or `systemctl enable sshd` (systemd profile)

**inxi output:** *(add when Gentoo node is established)*

**Install script:** *(to be written — `ptolemy_setup-gentoo.sh`)*

---

## CentOS / RHEL Stream (Server)

> 🔲 **Not yet implemented.** Section reserved for server deployment.

**Expected differences from Ubuntu model:**
- `dnf` replaces `apt-get`
- NodeSource repo URL differs: `https://rpm.nodesource.com/setup_lts.x`
- Python packages via `dnf` where available (`python3-lxml`, `python3-numpy`), pip for remainder
- `firewall-cmd` needed to open SSH port if firewalld is active
- `setenforce 0` or proper SELinux policy may be required
- `systemctl enable sshd` (service name `sshd` not `ssh`)
- `ripgrep` available via `dnf` on RHEL 9+ / CentOS Stream 9+

**Intended role:** Mouseion (Flask) server deployment, Callimachus database node

**inxi output:** *(add when server node is established)*

**Install script:** *(to be written — `ptolemy_setup-centos.sh`)*

---

## Install Models

Scripts follow the naming convention `ptolemy_setup-{MODEL}.sh`.

| Model | Description | Venv | System packages | Script |
|---|---|---|---|---|
| `apt_pip3` | apt first, pip3 fallback. No .env. System-wide. | No | Yes | `ptolemy_setup-apt_pip3.sh` |
| `apt_pip3_prefilled` | Same as apt_pip3, tokens pre-filled. Keep local. | No | Yes | `ptolemy_setup-apt_pip3_prefilled.sh` |
| `venv` | Python isolated in `~/.ptolemy_venv`. Reference only. | Yes | Partial | `ptolemy_setup-venv.sh` |

### apt_pip3 (current model)

Python packages are installed using apt first. If apt fails for a given package, pip3 with `--break-system-packages` is used as fallback. Node.js is installed via NodeSource LTS apt repository — this is the only stable path on Ubuntu 24.04. Claude Code is installed via npm into a user-level prefix (`~/.npm-global`) without sudo.

```bash
# apt first
sudo apt-get install -y python3-lxml

# pip3 fallback if apt fails
pip3 install --break-system-packages lxml
```

---

## Claude Code

Claude Code requires Node.js 18+ and is installed via npm. The apt-managed NodeSource LTS Node.js is the prerequisite.

```bash
# Install Node.js via NodeSource (handled by setup script)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude Code user-level (no sudo)
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global
npm install -g @anthropic-ai/claude-code

# Add to PATH in ~/.bashrc
export PATH="$HOME/.npm-global/bin:$PATH"

# Authenticate
claude login
```

**Note:** The native Claude Code installer (`curl https://claude.ai/install.sh | sh`) is Anthropic's current recommended method but has shown inconsistent behavior on Ubuntu 24.04. The npm + NodeSource apt path is the verified stable method for this platform.

---

## Post-Install

After any setup script completes:

```bash
# 1. Verify environment
source ~/.bashrc
echo $ANTHROPIC_API_KEY
echo $PTOL_TOKEN

# 2. Verify Claude Code
claude --version

# 3. Clone repos (if tokens were set before running script)
git clone https://x-access-token:${PTOL_TOKEN}@github.com/michaelrendier/Ptolemy ~/Ptolemy
git clone https://${AINUR_TOKEN}@github.com/michaelrendier/Ainulindale ~/Ainulindale

# 4. Get Surface Go IP for laptop SSH access
ip addr show wlp1s0 | grep 'inet '

# 5. Authenticate Claude Code
claude login
```

---

## Third-Party Build Dependencies

These packages cannot be installed via apt or pip — they require building from source.
Build scripts are in `installation/`. Run them after the main setup script.

| Package | Repository | Build Script | Role |
|---|---|---|---|
| **QTermWidget** | https://github.com/lxqt/qtermwidget | `installation/build_qtermwidget.sh` | **The Shell** — PtolShell pty backend. Required for all Face subshells. |
| **vispy** | https://github.com/vispy/vispy | `pip install vispy --break-system-packages` | OpenGL canvas — Alexandria Face, 320k-vertex renders verified |

### QTermWidget — Quick Build

```bash
chmod +x installation/build_qtermwidget.sh
./installation/build_qtermwidget.sh
```

Verify:
```bash
python3 -c "import QTermWidget; print('OK:', QTermWidget.__file__)"
```

If the CMake `BUILD_PYTHON_BINDINGS=ON` path fails (older qtermwidget versions),
the script falls back to manual SIP binding. See script for details.

### vispy — Quick Install

```bash
pip install vispy --break-system-packages
python3 -c "import vispy; print('vispy', vispy.__version__)"
```

vispy requires PyQt5 as the Qt backend — already in the main setup script.
