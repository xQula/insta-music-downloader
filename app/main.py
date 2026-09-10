"""Entry point: show a splash, verify ffmpeg is available, then launch the GUI."""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox
from qfluentwidgets import Theme, setTheme, setThemeColor

from app.ffmpeg_locator import locate_ffmpeg
from app.gui import ACCENT_COLOR, MainWindow
from app.splash import SplashScreen, target_screen

# Keep a module-level reference so the window isn't garbage-collected once
# _start()'s local variable goes out of scope.
_window = None


def _start(app: QApplication, splash: SplashScreen, screen) -> None:
    global _window

    ffmpeg_path = locate_ffmpeg()
    if ffmpeg_path is None:
        splash.close()
        QMessageBox.critical(
            None,
            "Insta Music Downloader",
            "ffmpeg не найден. Переустановите приложение или (при запуске из "
            "исходников) выполните scripts/fetch_ffmpeg.py.",
        )
        app.exit(1)
        return

    _window = MainWindow(ffmpeg_path)
    screen_center = screen.availableGeometry().center()
    frame = _window.frameGeometry()
    frame.moveCenter(screen_center)
    _window.move(frame.topLeft())
    _window.show()
    splash.close()


def main() -> None:
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)
    setThemeColor(ACCENT_COLOR)

    screen = target_screen()
    splash = SplashScreen(screen)
    splash.show()
    app.processEvents()

    QTimer.singleShot(50, lambda: _start(app, splash, screen))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
