"""PySide6 + qfluentwidgets GUI: Fluent Design, Mica backdrop, light/dark themes."""

import itertools
import os
import queue
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from qfluentwidgets import (
    CardWidget,
    FluentIcon,
    FluentWidget,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    SingleDirectionScrollArea,
    Theme,
    TitleLabel,
    TransparentPushButton,
    TransparentToolButton,
    isDarkTheme,
    qconfig,
    setTheme,
    setThemeColor,
)
from qfluentwidgets import FluentIcon as FIF

from app import config as cfg
from app.downloader import download

STATUS_IDLE = "idle"
STATUS_QUEUED = "queued"
STATUS_DOWNLOADING = "downloading"
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

STATUS_TEXT = {
    STATUS_IDLE: "Готово к загрузке",
    STATUS_QUEUED: "В очереди",
    STATUS_DOWNLOADING: "Скачивается",
    STATUS_SUCCESS: "Готово ✓",
    STATUS_ERROR: "Ошибка",
}

# (light_bg, light_fg, dark_bg, dark_fg) per status
STATUS_TONES = {
    STATUS_IDLE: ("#E4E4EC", "#5A5A6E", "#33334A", "#B4B4C6"),
    STATUS_QUEUED: ("#E4E4EC", "#5A5A6E", "#33334A", "#B4B4C6"),
    STATUS_DOWNLOADING: ("#D9E9FC", "#2B6CB0", "#233A57", "#7FB4F5"),
    STATUS_SUCCESS: ("#DBF3E4", "#1F8A4C", "#1E3B2E", "#5FD68F"),
    STATUS_ERROR: ("#FBDEDA", "#C0392B", "#3B2222", "#F2867A"),
}

ACCENT_COLOR = "#7C6FF0"

_row_ids = itertools.count(1)


def _locate_icon() -> str | None:
    """Prefer the vector icon.svg (crisp at any titlebar/taskbar DPI); fall back
    to icon.ico, which is also what Windows requires for the .exe resource."""
    if getattr(sys, "frozen", False):
        icon_dir = Path(sys._MEIPASS) / "icon"
    else:
        icon_dir = Path(__file__).resolve().parent / "assets"

    for name in ("icon.svg", "icon.ico"):
        candidate = icon_dir / name
        if candidate.exists():
            return str(candidate)
    return None


class StatusPill(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        self._status = STATUS_IDLE
        self._message = ""
        self.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        qconfig.themeChanged.connect(self._refresh)
        self._refresh()

    def set_status(self, status: str, message: str = "") -> None:
        self._status = status
        self._message = message
        self._refresh()

    def _refresh(self) -> None:
        light_bg, light_fg, dark_bg, dark_fg = STATUS_TONES[self._status]
        bg, fg = (dark_bg, dark_fg) if isDarkTheme() else (light_bg, light_fg)
        self.setText(self._message or STATUS_TEXT[self._status])
        self.setStyleSheet(
            f"QLabel {{ background-color: {bg}; color: {fg}; "
            f"border-radius: 13px; padding: 0 10px; font-size: 12px; }}"
        )


class LinkCard(CardWidget):
    def __init__(self, parent, app: "MainWindow", row_id: int):
        super().__init__(parent)
        self.app = app
        self.row_id = row_id

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.url_edit = LineEdit(self)
        self.url_edit.setPlaceholderText("Вставьте ссылку на Reels")
        self.url_edit.setClearButtonEnabled(True)
        layout.addWidget(self.url_edit)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.status_pill = StatusPill(self)
        action_row.addWidget(self.status_pill, 0, Qt.AlignLeft)
        action_row.addStretch(1)

        self.download_btn = PrimaryPushButton(FIF.DOWNLOAD, "Скачать", self)
        self.download_btn.clicked.connect(self._on_download_clicked)
        action_row.addWidget(self.download_btn)

        self.remove_btn = TransparentToolButton(FIF.CLOSE, self)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        action_row.addWidget(self.remove_btn)

        layout.addLayout(action_row)

    def _on_download_clicked(self) -> None:
        self.app.submit_row(self.row_id)

    def _on_remove_clicked(self) -> None:
        self.app.remove_row(self.row_id)

    def set_status(self, status: str, message: str = "") -> None:
        self.status_pill.set_status(status, message)

    def get_url(self) -> str:
        return self.url_edit.text().strip()


class MainWindow(FluentWidget):
    def __init__(self, ffmpeg_path: str):
        super().__init__()
        self.ffmpeg_path = ffmpeg_path

        self.setWindowTitle("Insta Music Downloader")
        self.resize(680, 640)
        self.setMinimumSize(560, 440)

        icon_path = _locate_icon()
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))

        setTheme(Theme.AUTO)
        setThemeColor(ACCENT_COLOR)

        self.config_data = cfg.load_config()
        self.rows: dict[int, LinkCard] = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.update_queue: "queue.Queue[tuple[int, str, str]]" = queue.Queue()

        self._build_layout()
        self.add_row()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_queue)
        self.poll_timer.start(100)

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, self.titleBar.height() + 12, 24, 20)
        root.setSpacing(16)

        header_row = QHBoxLayout()
        title = TitleLabel("Insta Music Downloader", self)
        header_row.addWidget(title)
        header_row.addStretch(1)

        self.theme_btn = TransparentToolButton(FIF.CONSTRACT, self)
        self.theme_btn.setToolTip("Светлая / тёмная тема")
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_row.addWidget(self.theme_btn)
        root.addLayout(header_row)

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        self.folder_btn = PushButton(FIF.FOLDER, "Папка не выбрана", self)
        self.folder_btn.clicked.connect(self._on_browse_clicked)
        folder_row.addWidget(self.folder_btn, 1)

        self.open_folder_btn = TransparentToolButton(FIF.MUSIC_FOLDER, self)
        self.open_folder_btn.setToolTip("Открыть папку")
        self.open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        folder_row.addWidget(self.open_folder_btn)

        root.addLayout(folder_row)
        self._set_folder_text(self.config_data.get("last_dir", ""))

        self.scroll_area = SingleDirectionScrollArea(self, orient=Qt.Vertical)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.rows_container = QWidget(self)
        self.rows_container.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(12)
        self.rows_layout.addStretch(1)

        self.scroll_area.setWidget(self.rows_container)
        root.addWidget(self.scroll_area, 1)

        bottom_row = QHBoxLayout()
        add_btn = TransparentPushButton(FIF.LINK, "Добавить ссылку", self)
        add_btn.clicked.connect(self.add_row)
        bottom_row.addWidget(add_btn)
        bottom_row.addStretch(1)

        download_all_btn = PrimaryPushButton(FIF.CLOUD_DOWNLOAD, "Скачать все", self)
        download_all_btn.clicked.connect(self.submit_all)
        bottom_row.addWidget(download_all_btn)
        root.addLayout(bottom_row)

        self.titleBar.raise_()

    def _toggle_theme(self) -> None:
        setTheme(Theme.LIGHT if isDarkTheme() else Theme.DARK)

    def _set_folder_text(self, path: str) -> None:
        display = path if len(path) <= 60 else f"...{path[-57:]}"
        self.folder_btn.setText(display if path else "Папка не выбрана")

    def _on_browse_clicked(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения", self.config_data.get("last_dir", "")
        )
        if chosen:
            self._set_folder_text(chosen)
            self.config_data["last_dir"] = chosen
            cfg.save_config(self.config_data)

    def _on_open_folder_clicked(self) -> None:
        folder = self.config_data.get("last_dir", "").strip()
        if folder and os.path.isdir(folder):
            os.startfile(folder)

    def add_row(self) -> None:
        row_id = next(_row_ids)
        row = LinkCard(self.rows_container, self, row_id)
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        self.rows[row_id] = row

    def remove_row(self, row_id: int) -> None:
        row = self.rows.pop(row_id, None)
        if row is not None:
            row.setParent(None)
            row.deleteLater()
        if not self.rows:
            self.add_row()

    def submit_row(self, row_id: int) -> None:
        row = self.rows.get(row_id)
        if row is None:
            return
        url = row.get_url()
        if not url:
            return
        if "instagram.com" not in url.lower():
            row.set_status(STATUS_ERROR, "Не похоже на ссылку Instagram")
            return

        out_dir = self.config_data.get("last_dir", "").strip()
        if not out_dir:
            row.set_status(STATUS_ERROR, "Укажите папку для сохранения")
            return

        row.set_status(STATUS_QUEUED)
        self.executor.submit(self._run_download, row_id, url, out_dir)

    def submit_all(self) -> None:
        for row_id in list(self.rows.keys()):
            self.submit_row(row_id)

    def _run_download(self, row_id: int, url: str, out_dir: str) -> None:
        def progress_hook(status: dict) -> None:
            if status.get("status") == "downloading":
                pct = status.get("_percent_str", "").strip()
                self.update_queue.put((row_id, STATUS_DOWNLOADING, f"Скачивается {pct}"))
            elif status.get("status") == "finished":
                self.update_queue.put((row_id, STATUS_DOWNLOADING, "Обработка..."))

        result = download(url, out_dir, self.ffmpeg_path, progress_hook)
        if result.success:
            self.update_queue.put((row_id, STATUS_SUCCESS, "Готово ✓"))
            self.config_data["last_dir"] = out_dir
            cfg.save_config(self.config_data)
        else:
            self.update_queue.put((row_id, STATUS_ERROR, result.error or "Ошибка"))

    def _poll_queue(self) -> None:
        try:
            while True:
                row_id, status, message = self.update_queue.get_nowait()
                row = self.rows.get(row_id)
                if row is not None:
                    row.set_status(status, message)
        except queue.Empty:
            pass

    def closeEvent(self, event) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)
