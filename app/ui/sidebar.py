"""
Left sidebar — navigation, folder list, stat cards, maintenance controls.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.database.manager import DatabaseManager
from app.ui import icons as ic
from app.ui.widgets import HSeparator, SectionLabel, StatCard


# ---------------------------------------------------------------------------
# Navigation item — full-width, left-aligned, icon + label
# ---------------------------------------------------------------------------

class _NavItem(QPushButton):
    def __init__(self, icon_name: str, text: str, active: bool = False, parent=None) -> None:
        super().__init__(f"  {text}", parent)
        self._icon_name = icon_name
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(36)
        self._refresh(active)
        self.toggled.connect(self._refresh)

    def _refresh(self, checked: bool) -> None:
        self.setObjectName("navItemActive" if checked else "navItem")
        self.setStyle(self.style())
        color = ic.ACCENT2 if checked else ic.MUTED
        ic.set_icon(self, self._icon_name, color=color, size=14)
        self.setIconSize(QSize(14, 14))


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

class Sidebar(QWidget):
    folder_selected   = Signal(str)
    all_selected      = Signal()
    recent_selected   = Signal()
    reindex_requested = Signal(str)
    folder_added      = Signal(str)
    folder_removed    = Signal(str)

    def __init__(self, db: DatabaseManager, parent=None) -> None:
        super().__init__(parent)
        self._db = db
        self.setObjectName("sidebar")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self._build()
        self.refresh()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(10, 14, 10, 14)
        layout.setSpacing(2)

        # ---- Navigation
        layout.addWidget(SectionLabel("Library"))
        layout.addSpacing(4)

        self._nav_all    = _NavItem(ic.IMAGES, "All Screenshots", active=True)
        self._nav_recent = _NavItem(ic.CLOCK,  "Recent  (7 days)")
        self._nav_all.clicked.connect(self._on_all)
        self._nav_recent.clicked.connect(self._on_recent)
        layout.addWidget(self._nav_all)
        layout.addWidget(self._nav_recent)

        layout.addSpacing(10)
        layout.addWidget(HSeparator())
        layout.addSpacing(10)

        # ---- Folders header
        folders_hdr = QHBoxLayout()
        folders_hdr.setContentsMargins(4, 0, 0, 0)
        folders_hdr.setSpacing(4)
        folders_hdr.addWidget(SectionLabel("Folders"))
        folders_hdr.addStretch()

        self._add_btn = QPushButton()
        self._add_btn.setObjectName("iconBtn")
        self._add_btn.setFixedSize(24, 24)
        self._add_btn.setToolTip("Add folder  (Ctrl+O)")
        self._add_btn.setCursor(Qt.PointingHandCursor)
        ic.set_icon(self._add_btn, ic.PLUS, color=ic.ACCENT2, size=11)
        self._add_btn.clicked.connect(self._add_folder)
        folders_hdr.addWidget(self._add_btn)
        layout.addLayout(folders_hdr)

        layout.addSpacing(4)

        # ---- Folder list
        self._folder_list = QListWidget()
        self._folder_list.setFrameShape(QFrame.NoFrame)
        self._folder_list.setMaximumHeight(200)
        self._folder_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self._folder_list.itemClicked.connect(self._on_folder_clicked)
        layout.addWidget(self._folder_list)

        # Remove folder (compact, ghost style)
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setObjectName("dangerBtn")
        self._remove_btn.setFixedHeight(30)
        ic.set_icon(self._remove_btn, ic.TRASH, color=ic.DANGER, size=12)
        self._remove_btn.clicked.connect(self._remove_folder)
        layout.addWidget(self._remove_btn)

        layout.addSpacing(12)
        layout.addWidget(HSeparator())
        layout.addSpacing(12)

        # ---- Stat cards
        layout.addWidget(SectionLabel("Stats"))
        layout.addSpacing(6)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        self._card_count  = StatCard(ic.IMAGES,      "0", "Screenshots")
        self._card_folder = StatCard(ic.LAYER_GROUP,  "0", "Folders")
        stats_row.addWidget(self._card_count)
        stats_row.addWidget(self._card_folder)
        layout.addLayout(stats_row)

        layout.addSpacing(12)
        layout.addWidget(HSeparator())
        layout.addSpacing(12)

        # ---- Maintenance
        layout.addWidget(SectionLabel("Maintenance"))
        layout.addSpacing(6)

        reindex_btn = QPushButton("Reindex All")
        reindex_btn.setObjectName("primaryBtn")
        reindex_btn.setFixedHeight(34)
        ic.set_icon(reindex_btn, ic.SYNC, color=ic.WHITE, size=13)
        reindex_btn.clicked.connect(lambda: self.reindex_requested.emit(""))
        layout.addWidget(reindex_btn)

        layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        self._folder_list.clear()
        folders = self._db.get_all_folders()
        folder_icon = ic.icon(ic.FOLDER, color=ic.ACCENT)
        for f in folders:
            name = os.path.basename(f.path) or f.path
            item = QListWidgetItem(name)
            item.setIcon(folder_icon)
            item.setData(Qt.UserRole, f.path)
            item.setToolTip(f.path)
            self._folder_list.addItem(item)

        count = self._db.count_screenshots()
        self._card_count.setValue(f"{count:,}")
        self._card_folder.setValue(str(len(folders)))

    # ------------------------------------------------------------------

    def _on_all(self) -> None:
        self._nav_all.setChecked(True)
        self._nav_recent.setChecked(False)
        self._folder_list.clearSelection()
        self.all_selected.emit()

    def _on_recent(self) -> None:
        self._nav_all.setChecked(False)
        self._nav_recent.setChecked(True)
        self._folder_list.clearSelection()
        self.recent_selected.emit()

    def _on_folder_clicked(self, item: QListWidgetItem) -> None:
        self._nav_all.setChecked(False)
        self._nav_recent.setChecked(False)
        self.folder_selected.emit(item.data(Qt.UserRole))

    def _add_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Screenshot Folder")
        if path:
            self._db.add_folder(path)
            self.refresh()
            self.folder_added.emit(path)

    def _remove_folder(self) -> None:
        item = self._folder_list.currentItem()
        if not item:
            return
        path = item.data(Qt.UserRole)
        self._db.remove_folder(path)
        self.refresh()
        self.folder_removed.emit(path)
