"""Entry point: verify ffmpeg is available, then launch the GUI."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.ffmpeg_locator import locate_ffmpeg
from app.gui import MainWindow


def _close_splash() -> None:
    """Close the PyInstaller onefile splash screen, if this is a frozen build with one."""
    try:
        import pyi_splash  # type: ignore[import-not-found]
    except ImportError:
        return
    pyi_splash.close()


def main() -> None:
    app = QApplication(sys.argv)

    ffmpeg_path = locate_ffmpeg()
    if ffmpeg_path is None:
        _close_splash()
        QMessageBox.critical(
            None,
            "Insta Music Downloader",
            "ffmpeg не найден. Переустановите приложение или (при запуске из "
            "исходников) выполните scripts/fetch_ffmpeg.py.",
        )
        sys.exit(1)

    window = MainWindow(ffmpeg_path)
    window.show()
    _close_splash()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
