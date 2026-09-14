"""One-time helper: fetch a platform-appropriate ffmpeg binary into
vendor/ffmpeg/, so it can be bundled into the app by scripts/build.ps1
(Windows) or scripts/build_macos.sh (macOS).

Usage: python scripts/fetch_ffmpeg.py
"""

import io
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = PROJECT_ROOT / "vendor" / "ffmpeg"


def _fetch_windows() -> None:
    dest_file = DEST_DIR / "ffmpeg.exe"
    if dest_file.exists():
        print(f"ffmpeg.exe уже есть: {dest_file}")
        return

    print(f"Скачиваю {FFMPEG_URL} ...")
    with urllib.request.urlopen(FFMPEG_URL) as response:
        data = response.read()

    print("Распаковываю...")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        exe_entries = [
            name for name in archive.namelist()
            if name.endswith("/bin/ffmpeg.exe")
        ]
        if not exe_entries:
            print("Не удалось найти ffmpeg.exe в архиве.", file=sys.stderr)
            sys.exit(1)

        with archive.open(exe_entries[0]) as src, open(dest_file, "wb") as dst:
            dst.write(src.read())

    print(f"Готово: {dest_file}")


def _fetch_macos() -> None:
    """Install ffmpeg via Homebrew and turn it into a self-contained binary
    with dylibbundler, so it doesn't depend on Homebrew being present on the
    end user's machine. There is no reliable static arm64 ffmpeg build to
    just download (evermeet.cx doesn't target Apple Silicon)."""
    dest_file = DEST_DIR / "ffmpeg"
    if dest_file.exists():
        print(f"ffmpeg уже есть: {dest_file}")
        return

    brew = shutil.which("brew")
    if brew is None:
        print(
            "Homebrew не найден. Установите его с https://brew.sh и запустите "
            "этот скрипт снова (либо вручную положите бинарник ffmpeg в "
            "vendor/ffmpeg/ffmpeg).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Устанавливаю ffmpeg и dylibbundler через Homebrew...")
    subprocess.run([brew, "install", "ffmpeg", "dylibbundler"], check=True)

    prefix = subprocess.run(
        [brew, "--prefix", "ffmpeg"], check=True, capture_output=True, text=True
    ).stdout.strip()
    src_file = Path(prefix) / "bin" / "ffmpeg"

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_file, dest_file)
    dest_file.chmod(0o755)

    libs_dir = DEST_DIR / "libs"
    libs_dir.mkdir(parents=True, exist_ok=True)

    print("Собираю зависимости в самодостаточный бандл (dylibbundler)...")
    subprocess.run(
        [
            "dylibbundler",
            "-od", "-b",
            "-x", str(dest_file),
            "-d", str(libs_dir),
            "-p", "@executable_path/libs/",
        ],
        check=True,
    )

    print(f"Готово: {dest_file}")


def main() -> None:
    if sys.platform == "darwin":
        _fetch_macos()
    else:
        _fetch_windows()


if __name__ == "__main__":
    main()
