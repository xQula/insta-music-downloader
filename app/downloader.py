"""Thin wrapper around yt-dlp for extracting audio from a single URL."""

import os
from dataclasses import dataclass
from typing import Callable, Optional

import yt_dlp


@dataclass
class DownloadResult:
    success: bool
    filepath: Optional[str] = None
    error: Optional[str] = None


def _friendly_error(exc: Exception) -> str:
    message = str(exc)
    lowered = message.lower()
    if "unsupported url" in lowered or "no video formats" in lowered:
        return "Ссылка не поддерживается или контент недоступен"
    if "private" in lowered or "login" in lowered:
        return "Пост приватный или требует входа в аккаунт"
    if "404" in message or "not found" in lowered:
        return "Пост не найден — проверьте ссылку"
    if isinstance(exc, yt_dlp.utils.DownloadError):
        return "Не удалось скачать: пост недоступен или ссылка неверна"
    return f"Ошибка: {message[:200]}"


def download(
    url: str,
    out_dir: str,
    ffmpeg_location: str,
    progress_hook: Callable[[dict], None],
) -> DownloadResult:
    os.makedirs(out_dir, exist_ok=True)

    downloaded_path: dict[str, str] = {}

    def hook(status: dict) -> None:
        if status.get("status") == "finished":
            downloaded_path["path"] = status.get("filename", "")
        progress_hook(status)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "ffmpeg_location": ffmpeg_location,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # yt-dlp raises many different exception types
        return DownloadResult(success=False, error=_friendly_error(exc))

    raw_path = downloaded_path.get("path")
    mp3_path = os.path.splitext(raw_path)[0] + ".mp3" if raw_path else None
    return DownloadResult(success=True, filepath=mp3_path)
