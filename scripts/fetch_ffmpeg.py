"""One-time helper: download a static Windows ffmpeg build and extract
ffmpeg.exe into vendor/ffmpeg/, so it can be bundled into the .exe by
scripts/build.ps1.

Usage: python scripts/fetch_ffmpeg.py
"""

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = PROJECT_ROOT / "vendor" / "ffmpeg"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)
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


if __name__ == "__main__":
    main()
