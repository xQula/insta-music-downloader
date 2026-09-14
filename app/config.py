"""Persist user preferences (currently just the last-used save folder)."""

import json
import os
import sys
from pathlib import Path

APP_DIR_NAME = "InstaMusicDownloader"
CONFIG_FILENAME = "config.json"


def _config_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    return base / APP_DIR_NAME / CONFIG_FILENAME


def load_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
