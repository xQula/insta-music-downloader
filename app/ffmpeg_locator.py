"""Resolve the path to the bundled (or dev-local) ffmpeg.exe binary."""

import shutil
import sys
from pathlib import Path

_FFMPEG_NAME = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def locate_ffmpeg() -> str | None:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "ffmpeg" / _FFMPEG_NAME
        if bundled.exists():
            return str(bundled)
        return None

    project_root = Path(__file__).resolve().parent.parent
    dev_local = project_root / "vendor" / "ffmpeg" / _FFMPEG_NAME
    if dev_local.exists():
        return str(dev_local)

    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path

    return None
