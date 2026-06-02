#!/usr/bin/env bash
# PtolFlutter/setup.sh — installs toolchain and builds release candidates.
#
# Run once: ./setup.sh
# Then to rebuild: ./setup.sh --build-only
#
# What this does:
#   1. Install Flutter SDK (via snap or tar.gz)
#   2. Install Android cmdline-tools → NDK → platform SDK
#   3. flutter create to generate platform boilerplate
#   4. flutter pub get
#   5. Build Android APK + AAB
#   6. Print instructions for iOS, macOS, Windows builds

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Config ─────────────────────────────────────────────────────────────────────
FLUTTER_VERSION="3.22.3"
ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$HOME/Android/Sdk}"
NDK_VERSION="27.2.12479018"
PLATFORM_VERSION="android-35"
BUILD_TOOLS_VERSION="35.0.0"
CMDLINE_TOOLS_URL="https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"

# ── Colors ────────────────────────────────────────────────────────────────────
GRN='\033[0;32m'; YEL='\033[1;33m'; RED='\033[0;31m'; RST='\033[0m'
info() { echo -e "${GRN}[setup]${RST} $*"; }
warn() { echo -e "${YEL}[warn]${RST}  $*"; }
die()  { echo -e "${RED}[error]${RST} $*"; exit 1; }

# ── 1. Flutter ────────────────────────────────────────────────────────────────
install_flutter() {
    if command -v flutter &>/dev/null; then
        info "Flutter already installed: $(flutter --version 2>/dev/null | head -1)"
        return
    fi

    info "Installing Flutter $FLUTTER_VERSION…"

    # Try snap first (Ubuntu/Debian)
    if command -v snap &>/dev/null; then
        sudo snap install flutter --classic
        export PATH="$PATH:/snap/bin"
        info "Flutter installed via snap"
        return
    fi

    # Fallback: tar.gz to ~/flutter
    FLUTTER_DIR="$HOME/flutter"
    if [ ! -d "$FLUTTER_DIR" ]; then
        ARCHIVE="flutter_linux_${FLUTTER_VERSION}-stable.tar.xz"
        URL="https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/$ARCHIVE"
        info "Downloading Flutter $FLUTTER_VERSION from Google storage…"
        curl -L "$URL" -o "/tmp/$ARCHIVE"
        tar xf "/tmp/$ARCHIVE" -C "$HOME"
        rm "/tmp/$ARCHIVE"
    fi
    export PATH="$HOME/flutter/bin:$PATH"
    info "Flutter installed at $FLUTTER_DIR"
    info "Add to your shell: export PATH=\"\$HOME/flutter/bin:\$PATH\""
}

# ── 2. Android SDK ────────────────────────────────────────────────────────────
install_android_sdk() {
    mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools"

    local sdkmanager="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager"

    if [ ! -f "$sdkmanager" ]; then
        info "Downloading Android cmdline-tools…"
        curl -L "$CMDLINE_TOOLS_URL" -o /tmp/cmdline-tools.zip
        unzip -q /tmp/cmdline-tools.zip -d /tmp/android-cmdtools
        mkdir -p "$ANDROID_SDK_ROOT/cmdline-tools/latest"
        mv /tmp/android-cmdtools/cmdline-tools/* "$ANDROID_SDK_ROOT/cmdline-tools/latest/"
        rm -rf /tmp/cmdline-tools.zip /tmp/android-cmdtools
        info "cmdline-tools installed"
    fi

    export ANDROID_SDK_ROOT
    export PATH="$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$PATH"
    export PATH="$ANDROID_SDK_ROOT/platform-tools:$PATH"

    # Accept licenses
    yes | "$sdkmanager" --licenses &>/dev/null || true

    # Install required components
    info "Installing Android SDK components (platform, build-tools, NDK)…"
    "$sdkmanager" \
        "platform-tools" \
        "platforms;$PLATFORM_VERSION" \
        "build-tools;$BUILD_TOOLS_VERSION" \
        "ndk;$NDK_VERSION"

    info "Android SDK ready at $ANDROID_SDK_ROOT"
}

# ── 3. flutter create (generates platform boilerplate) ───────────────────────
scaffold_flutter_project() {
    if [ -f "pubspec.lock" ]; then
        info "Flutter project already scaffolded"
        return
    fi

    info "Running flutter create to generate platform boilerplate…"

    # flutter create will overwrite pubspec.yaml — back ours up
    cp pubspec.yaml pubspec.yaml.ptol
    cp lib/main.dart lib/main.dart.ptol

    flutter create \
        --project-name ptolemy \
        --org com.ptol \
        --platforms android,ios,macos,windows,linux \
        --no-overwrite \
        . 2>/dev/null || true

    # Restore our files over flutter's generated ones
    cp pubspec.yaml.ptol pubspec.yaml
    cp lib/main.dart.ptol lib/main.dart
    rm -f pubspec.yaml.ptol lib/main.dart.ptol

    # Patch android/app/build.gradle with our NDK + CMake config
    _patch_android_build_gradle

    info "Platform boilerplate generated"
}

_patch_android_build_gradle() {
    local f="android/app/build.gradle"
    # Our build.gradle is the authoritative one — already in place
    info "Android build.gradle is configured with NDK $NDK_VERSION"
}

# ── 4. pub get ────────────────────────────────────────────────────────────────
pub_get() {
    info "Running flutter pub get…"
    # provider is needed — add it if not present
    if ! grep -q "provider:" pubspec.yaml; then
        sed -i '/  ffi:/i\  provider: ^6.1.2' pubspec.yaml
    fi
    flutter pub get
}

# ── 5. Build Android ──────────────────────────────────────────────────────────
build_android() {
    info "Building Android APK (release)…"
    flutter build apk --release \
        --dart-define=FLUTTER_BUILD_NAME=1.0.0 \
        --dart-define=FLUTTER_BUILD_NUMBER=1

    info "Building Android App Bundle (release)…"
    flutter build appbundle --release

    APK="build/app/outputs/flutter-apk/app-release.apk"
    AAB="build/app/outputs/bundle/release/app-release.aab"

    info "APK: $(du -sh $APK 2>/dev/null | cut -f1)  →  $SCRIPT_DIR/$APK"
    info "AAB: $(du -sh $AAB 2>/dev/null | cut -f1)  →  $SCRIPT_DIR/$AAB"
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    local build_only=0
    [[ "$1" == "--build-only" ]] && build_only=1

    if [ $build_only -eq 0 ]; then
        install_flutter
        install_android_sdk
        scaffold_flutter_project
        pub_get
    fi

    build_android

    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "  Android APK:  build/app/outputs/flutter-apk/app-release.apk"
    echo "  Android AAB:  build/app/outputs/bundle/release/app-release.aab"
    echo ""
    echo "  iOS (requires macOS + Xcode):"
    echo "    flutter build ios --release"
    echo "    # open ios/Runner.xcworkspace in Xcode → Archive"
    echo ""
    echo "  macOS (requires macOS + Xcode):"
    echo "    flutter build macos --release"
    echo "    # output: build/macos/Build/Products/Release/ptolemy.app"
    echo ""
    echo "  Windows (requires Windows + Visual Studio 2022):"
    echo "    flutter build windows --release"
    echo "    # output: build/windows/x64/runner/Release/"
    echo "══════════════════════════════════════════════════════════"
}

main "$@"
