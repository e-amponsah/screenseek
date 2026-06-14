"""
Main application window — clean toolbar, splitter layout, no in-app branding.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.database.manager import DatabaseManager, ScreenshotRecord
from app.indexer import IndexingPipeline
from app.ocr.engine import OCREngine
from app.search.engine import SearchEngine, SearchFilters
from app.settings.manager import SettingsManager
from app.thumbnails.generator import ThumbnailGenerator
from app.ui import icons as ic
from app.ui.preview_panel import PreviewPanel
from app.ui.results_panel import ResultsPanel
from app.ui.search_bar import SearchBar
from app.ui.settings_dialog import SettingsDialog
from app.ui.sidebar import Sidebar
from app.ui.styles import get_palette, get_stylesheet
from app.ui.widgets import IconButton, ToggleSwitch
from app.watcher.monitor import FolderMonitor

logger = logging.getLogger(__name__)

APP_DATA_DIR = Path.home() / ".screenseek"


# ---------------------------------------------------------------------------
# Background indexing worker
# ---------------------------------------------------------------------------

class _WorkerSignals(QObject):
    progress = Signal(int, int, str)
    status   = Signal(str)
    finished = Signal(dict)


class _IndexWorker(QThread):
    def __init__(self, pipeline: IndexingPipeline, folders: list[str], force: bool = False) -> None:
        super().__init__()
        self._pipeline = pipeline
        self._folders  = folders
        self._force    = force
        self.signals   = _WorkerSignals()

    def run(self) -> None:
        summary = self._pipeline.index_folders(
            self._folders,
            progress_cb=self.signals.progress.emit,
            status_cb=self.signals.status.emit,
            force_reindex=self._force,
        )
        self.signals.finished.emit(summary)


# ---------------------------------------------------------------------------
# App toolbar — search bar + theme toggle + settings (no in-app logo)
# ---------------------------------------------------------------------------

class _ToolBar(QWidget):
    search_triggered = Signal(str)
    theme_changed    = Signal(str)
    settings_clicked = Signal()

    def __init__(self, current_theme: str = "dark", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("appToolBar")
        self.setFixedHeight(52)
        self._theme = current_theme
        self._build()

    def _build(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 12, 0)
        layout.setSpacing(10)

        # Search bar — takes all available space
        self._search = SearchBar()
        layout.addWidget(self._search, 1)
        self._search.search_triggered.connect(self.search_triggered)

        # Vertical separator
        sep = QFrame()
        sep.setObjectName("toolbarSep")
        sep.setFrameShape(QFrame.VLine)
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        # Moon icon
        self._moon_lbl = QLabel()
        self._moon_lbl.setFixedSize(16, 16)
        self._moon_lbl.setPixmap(ic.px(ic.MOON, color=ic.MUTED, size=13))
        self._moon_lbl.setToolTip("Dark mode")
        layout.addWidget(self._moon_lbl)

        # Toggle switch
        self._theme_switch = ToggleSwitch(checked=(self._theme == "light"))
        self._theme_switch.setTheme(self._theme)
        self._theme_switch.toggled.connect(self._on_toggle)
        layout.addWidget(self._theme_switch)

        # Sun icon
        self._sun_lbl = QLabel()
        self._sun_lbl.setFixedSize(16, 16)
        self._sun_lbl.setPixmap(ic.px(ic.SUN, color=ic.MUTED, size=13))
        self._sun_lbl.setToolTip("Light mode")
        layout.addWidget(self._sun_lbl)

        layout.addSpacing(2)

        # Settings button
        self._settings_btn = IconButton(ic.COG, "Settings  (Ctrl+,)", color=ic.MUTED)
        self._settings_btn.clicked.connect(self.settings_clicked)
        layout.addWidget(self._settings_btn)

    def _on_toggle(self, is_light: bool) -> None:
        self._theme = "light" if is_light else "dark"
        self._theme_switch.setTheme(self._theme)
        self.theme_changed.emit(self._theme)

    def set_theme(self, theme: str) -> None:
        self._theme = theme
        self._theme_switch.setChecked(theme == "light")
        self._theme_switch.setTheme(theme)

    def search_bar(self) -> SearchBar:
        return self._search


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ScreenSeek")
        self.setMinimumSize(1100, 680)

        # --- Infrastructure
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        db_path   = APP_DATA_DIR / "screenseek.db"
        thumb_dir = APP_DATA_DIR / "thumbnails"

        self._db       = DatabaseManager(db_path)
        self._settings = SettingsManager(self._db)
        self._ocr      = OCREngine(self._settings.ocr_languages)
        self._thumbs   = ThumbnailGenerator(thumb_dir, self._settings.thumbnail_size)
        self._monitor  = FolderMonitor(self._on_file_event)
        self._pipeline = IndexingPipeline(self._db, self._ocr, self._thumbs, self._monitor)
        self._search   = SearchEngine(self._db)

        self._worker: Optional[_IndexWorker] = None
        self._active_filters = SearchFilters()
        self._current_theme  = self._settings.theme

        # --- Build
        self._apply_theme()
        self._build_ui()
        self._build_status_bar()
        self._build_menu()

        # --- Start monitoring
        if self._settings.monitor_enabled:
            folders = [f.path for f in self._db.get_all_folders() if f.enabled]
            if folders:
                self._pipeline.start_monitoring(folders)

        QTimer.singleShot(150, lambda: self._on_search(""))

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root_widget = QWidget()
        self.setCentralWidget(root_widget)
        root = QVBoxLayout(root_widget)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._toolbar = _ToolBar(current_theme=self._current_theme)
        self._toolbar.search_triggered.connect(self._on_search)
        self._toolbar.theme_changed.connect(self._on_theme_changed)
        self._toolbar.settings_clicked.connect(self._open_settings)
        root.addWidget(self._toolbar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)

        self._sidebar = Sidebar(self._db)
        self._sidebar.all_selected.connect(self._on_show_all)
        self._sidebar.recent_selected.connect(self._on_show_recent)
        self._sidebar.folder_selected.connect(self._on_folder_filter)
        self._sidebar.folder_added.connect(self._on_folder_added)
        self._sidebar.folder_removed.connect(self._on_folder_removed)
        self._sidebar.reindex_requested.connect(lambda _: self._start_indexing())
        splitter.addWidget(self._sidebar)

        self._results = ResultsPanel()
        self._results.result_selected.connect(self._on_result_selected)
        splitter.addWidget(self._results)

        self._preview = PreviewPanel()
        splitter.addWidget(self._preview)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([256, 524, 320])
        root.addWidget(splitter)

    def _build_status_bar(self) -> None:
        bar = QStatusBar()
        self.setStatusBar(bar)

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setContentsMargins(4, 0, 0, 0)
        bar.addWidget(self._status_lbl, 1)

        self._progress = QProgressBar()
        self._progress.setMaximumWidth(160)
        self._progress.setMaximumHeight(4)
        self._progress.setVisible(False)
        bar.addPermanentWidget(self._progress)

        self._count_lbl = QLabel()
        self._count_lbl.setObjectName("badgeCount")
        bar.addPermanentWidget(self._count_lbl)
        self._refresh_count()

        self._ocr_status_lbl = QLabel()
        bar.addPermanentWidget(self._ocr_status_lbl)
        QTimer.singleShot(600, self._update_ocr_status)

    def _build_menu(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu("File")
        add_action = QAction("Add Folder…", self)
        add_action.setShortcut(QKeySequence("Ctrl+O"))
        add_action.triggered.connect(self._sidebar._add_folder)
        file_menu.addAction(add_action)
        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(quit_action)

        index_menu = bar.addMenu("Index")
        reindex_action = QAction("Reindex All", self)
        reindex_action.setShortcut(QKeySequence("Ctrl+R"))
        reindex_action.triggered.connect(lambda: self._start_indexing())
        index_menu.addAction(reindex_action)
        cancel_action = QAction("Cancel Indexing", self)
        cancel_action.triggered.connect(self._cancel_indexing)
        index_menu.addAction(cancel_action)
        index_menu.addSeparator()
        clear_action = QAction("Clear Index…", self)
        clear_action.triggered.connect(self._clear_index)
        index_menu.addAction(clear_action)

        view_menu = bar.addMenu("View")
        toggle_theme = QAction("Toggle Dark / Light", self)
        toggle_theme.setShortcut(QKeySequence("Ctrl+T"))
        toggle_theme.triggered.connect(self._toggle_theme_shortcut)
        view_menu.addAction(toggle_theme)

        tools_menu = bar.addMenu("Tools")
        settings_action = QAction("Settings…", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _on_search(self, query: str) -> None:
        results = self._search.search(query, self._active_filters, limit=5000)
        title = f'"{query}"' if query else "All Screenshots"
        self._results.display(results, title)
        self._preview.clear()

    def _on_show_all(self) -> None:
        self._active_filters = SearchFilters()
        self._on_search(self._toolbar.search_bar().text())

    def _on_show_recent(self) -> None:
        import time
        self._active_filters = SearchFilters(date_from=time.time() - 7 * 86400)
        self._on_search(self._toolbar.search_bar().text())

    def _on_folder_filter(self, folder: str) -> None:
        self._active_filters = SearchFilters(folder=folder)
        self._on_search(self._toolbar.search_bar().text())

    def _on_result_selected(self, record: ScreenshotRecord) -> None:
        self._preview.show_record(record)

    # ------------------------------------------------------------------
    # Folder management
    # ------------------------------------------------------------------

    def _on_folder_added(self, path: str) -> None:
        self._sidebar.refresh()
        if self._settings.monitor_enabled:
            self._monitor.watch(path)
        self._start_indexing(folders=[path])

    def _on_folder_removed(self, path: str) -> None:
        self._sidebar.refresh()
        self._monitor.unwatch(path)
        self._active_filters = SearchFilters()
        self._on_search(self._toolbar.search_bar().text())

    def _on_file_event(self, event_type: str, file_path: str) -> None:
        self._pipeline.on_file_event(event_type, file_path)
        QTimer.singleShot(600, lambda: self._on_search(self._toolbar.search_bar().text()))
        QTimer.singleShot(600, self._refresh_count)
        QTimer.singleShot(600, self._sidebar.refresh)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def _start_indexing(self, folders: list[str] | None = None, force: bool = False) -> None:
        if self._worker and self._worker.isRunning():
            return
        if folders is None:
            folders = [f.path for f in self._db.get_all_folders() if f.enabled]
        if not folders:
            QMessageBox.information(
                self, "No Folders",
                "Add at least one folder first via File > Add Folder…",
            )
            return

        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._set_status("Indexing…")

        self._worker = _IndexWorker(self._pipeline, folders, force)
        self._worker.signals.progress.connect(self._on_index_progress)
        self._worker.signals.status.connect(self._set_status)
        self._worker.signals.finished.connect(self._on_index_finished)
        self._worker.start()

    def _cancel_indexing(self) -> None:
        self._pipeline.cancel()
        self._set_status("Cancelling…")

    def _on_index_progress(self, current: int, total: int, filename: str) -> None:
        self._progress.setRange(0, total)
        self._progress.setValue(current)
        self._set_status(f"Indexing {current:,} / {total:,}  ·  {filename}")

    def _on_index_finished(self, summary: dict) -> None:
        self._progress.setVisible(False)
        self._set_status(
            f"Done  ·  {summary.get('indexed',0):,} indexed  "
            f"·  {summary.get('skipped',0):,} skipped  "
            f"·  {summary.get('failed',0):,} failed"
        )
        self._refresh_count()
        self._sidebar.refresh()
        self._on_search(self._toolbar.search_bar().text())

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _on_theme_changed(self, theme: str) -> None:
        self._current_theme = theme
        self._settings.theme = theme
        self._apply_theme()
        self._update_ocr_status()

    def _toggle_theme_shortcut(self) -> None:
        new = "light" if self._current_theme == "dark" else "dark"
        self._toolbar.set_theme(new)
        self._on_theme_changed(new)

    def _apply_theme(self) -> None:
        QApplication.instance().setStyleSheet(get_stylesheet(self._current_theme))

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self._settings, self._current_theme, self)
        dlg.settings_changed.connect(self._on_settings_saved)
        dlg.theme_changed.connect(self._on_theme_changed)
        dlg.exec()

    def _on_settings_saved(self) -> None:
        self._on_theme_changed(self._settings.theme)
        self._toolbar.set_theme(self._settings.theme)
        self._ocr.set_languages(self._settings.ocr_languages)
        self._thumbs.set_size(self._settings.thumbnail_size)

    def _clear_index(self) -> None:
        if QMessageBox.warning(
            self, "Clear Index",
            "Remove all indexed data?\n\nOriginal files will NOT be deleted.",
            QMessageBox.Yes | QMessageBox.No,
        ) == QMessageBox.Yes:
            self._db.clear_all_screenshots()
            self._results.display([], "All Screenshots")
            self._preview.clear()
            self._sidebar.refresh()
            self._refresh_count()
            self._set_status("Index cleared.")

    def _set_status(self, msg: str) -> None:
        self._status_lbl.setText(msg)

    def _refresh_count(self) -> None:
        n = self._db.count_screenshots()
        self._count_lbl.setText(f"  {n:,} screenshots  ")

    def _update_ocr_status(self) -> None:
        if self._ocr.easyocr_available:
            self._ocr_status_lbl.setPixmap(ic.px(ic.CHECK_CIRCLE, color=ic.SUCCESS, size=12))
            self._ocr_status_lbl.setToolTip("EasyOCR is ready")
        elif self._ocr.tesseract_available:
            self._ocr_status_lbl.setPixmap(ic.px(ic.EXCLAMATION, color=ic.WARN, size=12))
            self._ocr_status_lbl.setToolTip("Tesseract (fallback) is ready")
        else:
            self._ocr_status_lbl.setPixmap(ic.px(ic.TIMES_CIRCLE, color=ic.DANGER, size=12))
            self._ocr_status_lbl.setToolTip("No OCR engine found")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._pipeline.cancel()
        self._pipeline.stop_monitoring()
        if self._worker:
            self._worker.quit()
            self._worker.wait(3000)
        self._db.close()
        event.accept()
