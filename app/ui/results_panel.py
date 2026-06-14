"""
Results panel — responsive grid of thumbnail cards, re-layouts on every resize.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.database.manager import ScreenshotRecord
from app.search.engine import SearchResultItem
from app.ui import icons as ic
from app.ui.widgets import EmptyState

THUMB_H = 145
CARD_W  = 188


# ---------------------------------------------------------------------------
# Single result card
# ---------------------------------------------------------------------------

class ResultCard(QFrame):
    clicked = Signal(object)   # ScreenshotRecord

    def __init__(self, result: SearchResultItem, selected: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.result    = result
        self._selected = selected
        self.setObjectName("resultCardSelected" if selected else "resultCard")
        self.setFixedWidth(CARD_W)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(0)

        # Thumbnail area
        thumb_wrap = QWidget()
        thumb_wrap.setObjectName("resultThumb")
        thumb_wrap.setFixedHeight(THUMB_H)
        tw_layout = QVBoxLayout(thumb_wrap)
        tw_layout.setContentsMargins(0, 0, 0, 0)

        self._thumb_lbl = QLabel()
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._thumb_lbl.setFixedHeight(THUMB_H)

        rec = self.result.record
        thumb_path = rec.thumbnail_path
        if thumb_path and Path(thumb_path).exists():
            px = QPixmap(thumb_path).scaled(
                CARD_W, THUMB_H,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            if px.width() > CARD_W:
                offset = (px.width() - CARD_W) // 2
                px = px.copy(offset, 0, CARD_W, THUMB_H)
            self._thumb_lbl.setPixmap(px)
        else:
            icon_px = ic.px(ic.IMAGE, color="#2D2860", size=36)
            self._thumb_lbl.setPixmap(icon_px)
            self._thumb_lbl.setStyleSheet(
                "background: rgba(108,92,231,0.07); border-radius: 10px 10px 0 0;"
            )

        tw_layout.addWidget(self._thumb_lbl)
        layout.addWidget(thumb_wrap)

        # Text area
        meta_widget = QWidget()
        meta_layout = QVBoxLayout(meta_widget)
        meta_layout.setContentsMargins(10, 8, 10, 0)
        meta_layout.setSpacing(2)

        name_lbl = QLabel(self._truncate(rec.file_name, 24))
        name_lbl.setObjectName("resultTitle")
        name_lbl.setToolTip(rec.file_path)
        meta_layout.addWidget(name_lbl)

        folder_name = Path(rec.folder).name or rec.folder
        date_str    = datetime.fromtimestamp(rec.indexed_at).strftime("%b %d")
        meta_lbl    = QLabel(f"{self._truncate(folder_name, 16)}  ·  {date_str}")
        meta_lbl.setObjectName("resultMeta")
        meta_layout.addWidget(meta_lbl)

        if self.result.snippet:
            clean = self.result.snippet.replace("<b>", "").replace("</b>", "")
            snip = QLabel(self._truncate(clean, 52))
            snip.setObjectName("resultSnippet")
            snip.setWordWrap(True)
            meta_layout.addWidget(snip)

        layout.addWidget(meta_widget)
        layout.addStretch()

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        return text if len(text) <= max_len else text[:max_len - 1] + "…"

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result.record)

    def set_selected(self, val: bool) -> None:
        if self._selected != val:
            self._selected = val
            self.setObjectName("resultCardSelected" if val else "resultCard")
            self.setStyle(self.style())


# ---------------------------------------------------------------------------
# Results panel
# ---------------------------------------------------------------------------

class ResultsPanel(QWidget):
    result_selected = Signal(object)   # ScreenshotRecord
    open_file       = Signal(str)
    open_dir        = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._cards: list[ResultCard] = []
        self._selected_card: Optional[ResultCard] = None
        # Debounce resize so we don't re-layout on every pixel
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(80)
        self._resize_timer.timeout.connect(self._re_layout)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setObjectName("resultsHeader")
        header.setFixedHeight(48)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 16, 0)
        h_layout.setSpacing(10)

        self._title_lbl = QLabel("All Screenshots")
        self._title_lbl.setObjectName("resultsTitle")
        h_layout.addWidget(self._title_lbl)

        self._count_lbl = QLabel()
        self._count_lbl.setObjectName("badgeCount")
        self._count_lbl.setVisible(False)
        h_layout.addWidget(self._count_lbl)

        h_layout.addStretch()
        root.addWidget(header)

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(self._scroll)

        self._container = QWidget()
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(16, 16, 16, 16)
        self._grid.setSpacing(12)
        self._scroll.setWidget(self._container)

    # ------------------------------------------------------------------

    def display(self, results: list[SearchResultItem], title: str = "") -> None:
        self._clear_grid()
        self._selected_card = None

        n = len(results)
        self._count_lbl.setText(f"  {n:,}  ")
        self._count_lbl.setVisible(n > 0)
        self._title_lbl.setText(title or ("All Screenshots" if n > 0 else "No results"))

        if not results:
            empty = EmptyState(
                ic.SEARCH,
                "No screenshots found",
                "Try a different search term, or add folders and reindex.",
                icon_color="#2D2860",
            )
            self._grid.addWidget(empty, 0, 0)
            return

        for result in results:
            card = ResultCard(result)
            card.clicked.connect(self._on_card_clicked)
            self._cards.append(card)

        self._re_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._cards:
            self._resize_timer.start()

    def _re_layout(self) -> None:
        """Reposition cards at the current panel width without recreating them."""
        if not self._cards:
            return

        # Pull everything out of the grid; delete spacers, keep cards
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w and w not in self._cards:
                w.deleteLater()

        vp_w = self._scroll.viewport().width()
        cols = max(2, (vp_w - 32) // (CARD_W + 12))
        n = len(self._cards)

        for i, card in enumerate(self._cards):
            self._grid.addWidget(card, i // cols, i % cols)

        # Spacer widgets to pad the last incomplete row
        remainder = n % cols
        if remainder:
            for j in range(cols - remainder):
                spacer = QWidget()
                spacer.setFixedWidth(CARD_W)
                self._grid.addWidget(spacer, (n - 1) // cols, remainder + j)

    def _on_card_clicked(self, record: ScreenshotRecord) -> None:
        if self._selected_card:
            self._selected_card.set_selected(False)
        for card in self._cards:
            if card.result.record.id == record.id:
                card.set_selected(True)
                self._selected_card = card
                break
        self.result_selected.emit(record)

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
