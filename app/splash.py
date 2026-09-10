"""Custom PySide6 splash screen shown at app startup.

Replaces PyInstaller's built-in --splash feature: that mechanism only shows a
single static image with (at best) text updates, and only after Python has
already started — the bulk of a onefile build's startup delay happens before
that. Building our own splash and switching the build to --onedir lets it
actually animate and gives real anti-aliased rounded corners via a translucent
Qt window instead of a color-keyed one.
"""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor, QGuiApplication, QIcon, QPainter, QPainterPath, QPixmap, QScreen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from qfluentwidgets import IndeterminateProgressRing

WIDTH, HEIGHT = 480, 300
CORNER_RADIUS = 28


def _asset_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "icon"
    return Path(__file__).resolve().parent / "assets"


def target_screen() -> QScreen:
    """The screen the user is currently on, so the splash and the main window
    both land on the same monitor instead of drifting to whichever one Qt's
    default top-level window placement happens to pick."""
    screen = QGuiApplication.screenAt(QCursor.pos())
    return screen if screen is not None else QGuiApplication.primaryScreen()


class SplashScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIDTH, HEIGHT)
        self._center_on_screen()

        assets = _asset_dir()
        bg_path = assets / "splash_bg.png"
        self._background = QPixmap(str(bg_path)) if bg_path.exists() else QPixmap()

        icon_path = assets / "icon.svg"
        if not icon_path.exists():
            icon_path = assets / "icon.ico"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 34, 0, 24)
        layout.setSpacing(6)

        badge = QLabel(self)
        badge.setFixedSize(96, 96)
        badge.setAlignment(Qt.AlignCenter)
        if icon_path.exists():
            badge.setPixmap(QIcon(str(icon_path)).pixmap(96, 96))
        layout.addWidget(badge, 0, Qt.AlignHCenter)

        layout.addSpacing(16)

        title = QLabel("Insta Music Downloader", self)
        title.setStyleSheet('color: white; font: 600 18pt "Segoe UI";')
        layout.addWidget(title, 0, Qt.AlignHCenter)

        subtitle = QLabel("Загрузка...", self)
        subtitle.setStyleSheet('color: #A8A6BE; font: 10pt "Segoe UI";')
        layout.addWidget(subtitle, 0, Qt.AlignHCenter)

        layout.addSpacing(10)

        ring = IndeterminateProgressRing(self)
        ring.setFixedSize(26, 26)
        ring.setStrokeWidth(3)
        layout.addWidget(ring, 0, Qt.AlignHCenter)

        layout.addStretch(1)

    def _center_on_screen(self) -> None:
        screen_center = target_screen().geometry().center()
        self.move(screen_center.x() - WIDTH // 2, screen_center.y() - HEIGHT // 2)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), CORNER_RADIUS, CORNER_RADIUS)
        painter.setClipPath(path)
        if not self._background.isNull():
            painter.drawPixmap(self.rect(), self._background)
