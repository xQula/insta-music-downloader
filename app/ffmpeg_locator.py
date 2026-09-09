"""Resolve the path to the bundled (or dev-local) ffmpeg.exe binary."""

import shutil
import sys
from pathlib import Path


def locate_ffmpeg() -> str | None:
    if getattr(sys, "frozen", False):
        bundled = Path(sys._MEIPASS) / "ffmpeg" / "ffmpeg.exe"
        if bundled.exists():
            return str(bundled)
        return None

    project_root = Path(__file__).resolve().parent.parent
    dev_local = project_root / "vendor" / "ffmpeg" / "ffmpeg.exe"
    if dev_local.exists():
        return str(dev_local)

    on_path = shutil.which("ffmpeg")
    if on_path:
        return on_path

    return None
