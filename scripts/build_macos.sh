#!/usr/bin/env bash
# Build a standalone InstaMusicDownloader.app (Apple Silicon / arm64) with
# ffmpeg bundled inside. Run from the project root: ./scripts/build_macos.sh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Build from a dedicated venv (not the system Python) for the same reason as
# build.ps1 on Windows: keep PyInstaller's import analysis from sweeping in
# unrelated packages and bloating the app.
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "Creating build venv at .venv ..."
    python3 -m venv "$VENV_DIR"
fi
"$VENV_PYTHON" -m pip install -q --upgrade pip
"$VENV_PYTHON" -m pip install -q -r requirements.txt

FFMPEG_BIN="$PROJECT_ROOT/vendor/ffmpeg/ffmpeg"
if [ ! -f "$FFMPEG_BIN" ]; then
    echo "ffmpeg not found, fetching it first..."
    "$VENV_PYTHON" scripts/fetch_ffmpeg.py
fi

ICON_ICNS="$PROJECT_ROOT/app/assets/icon.icns"
ICON_ICO="$PROJECT_ROOT/app/assets/icon.ico"
ICON_SVG="$PROJECT_ROOT/app/assets/icon.svg"
SPLASH_BG="$PROJECT_ROOT/app/assets/splash_bg.png"
if [ ! -f "$ICON_ICNS" ] || [ ! -f "$SPLASH_BG" ]; then
    echo "icon/splash assets not found, generating them first..."
    "$VENV_PYTHON" scripts/generate_assets.py
fi

VENV_PYINSTALLER="$VENV_DIR/bin/pyinstaller"
"$VENV_PYINSTALLER" --name InstaMusicDownloader \
    --onedir \
    --windowed \
    --icon "$ICON_ICNS" \
    --add-binary "$FFMPEG_BIN:ffmpeg" \
    --add-binary "$PROJECT_ROOT/vendor/ffmpeg/libs:ffmpeg/libs" \
    --add-data "$ICON_ICO:icon" \
    --add-data "$ICON_SVG:icon" \
    --add-data "$SPLASH_BG:icon" \
    --osx-bundle-identifier com.xqula.instamusicdownloader \
    app/main.py

APP_BUNDLE="dist/InstaMusicDownloader.app"

# Apple Silicon refuses to run unsigned code at all, so an ad-hoc signature
# (no Developer ID, just "-") is required even though we're not distributing
# this through notarization.
echo "Ad-hoc signing $APP_BUNDLE ..."
codesign --force --deep --sign - "$APP_BUNDLE"

echo "Build complete: $APP_BUNDLE"
