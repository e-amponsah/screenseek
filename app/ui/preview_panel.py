"""
Right-side preview panel — full image, metadata grid, OCR text, icon-based actions.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.manager import ScreenshotRecord
from app.ui import icons as ic
from app.ui.widgets import HSeparator


class _MetaRow(QWidget):
    def __init__(self, key: str, value: str, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        key_lbl = QLabel(key)
        key_lbl.setObjectName("metaKey")
        key_lbl.setFixedWidth(82)
        key_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(key_lbl)

        self._val = QLabel(value)
        self._val.setObjectName("metaValue")
        self._val.setWordWrap(True)
        self._val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self._val, 1)

    def setValue(self, v: str) -> None:
        self._val.setText(v)


def _primary_btn(icon_name: str, text: str) -> QPushButton:
    btn = QPushButton(f"  {text}")
    btn.setObjectName("primaryBtn")
    btn.setFixedHeight(32)
    ic.set_icon(btn, icon_name, color=ic.WHITE, size=13)
    return btn


def _icon_action_btn(icon_name: str, tooltip: str) -> QPushButton:
    """Compact square icon-only action button."""
    btn = QPushButton()
    btn.setObjectName("iconBtn")
    btn.setFixedSize(32, 32)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    ic.set_icon(btn, icon_name, color=ic.MUTED, size=14)
    return btn


class PreviewPanel(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("previewPanel")
        self._current: ScreenshotRecord | None = None
        self._build()

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
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 14, 14, 14)
        body_layout.setSpacing(12)

        # --- Header
        hdr = QHBoxLayout()
        title = QLabel("Preview")
        title.setObjectName("previewTitle")
        hdr.addWidget(title)
        hdr.addStretch()
        body_layout.addLayout(hdr)

        # --- Image area
        self._img_frame = QWidget()
        self._img_frame.setObjectName("previewImageArea")
        self._img_frame.setMinimumHeight(180)
        self._img_frame.setMaximumHeight(220)
        img_layout = QVBoxLayout(self._img_frame)
        img_layout.setContentsMargins(4, 4, 4, 4)

        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignCenter)
        self._img_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Default placeholder — vector icon instead of text
        self._show_placeholder()
        img_layout.addWidget(self._img_lbl)
        body_layout.addWidget(self._img_frame)

        # --- Action buttons  (Open gets text; Reveal / Copy Path are icon-only)
        actions = QHBoxLayout()
        actions.setSpacing(6)

        self._open_btn = _primary_btn(ic.EXTERNAL, "Open")
        self._open_btn.clicked.connect(self._open_image)
        self._open_btn.setEnabled(False)
        actions.addWidget(self._open_btn, 1)   # stretch so it fills remaining space

        self._reveal_btn = _icon_action_btn(ic.FOLDER_OPEN, "Reveal in Explorer")
        self._reveal_btn.clicked.connect(self._reveal)
        self._reveal_btn.setEnabled(False)
        actions.addWidget(self._reveal_btn)

        self._copy_path_btn = _icon_action_btn(ic.LINK, "Copy file path")
        self._copy_path_btn.clicked.connect(self._copy_path)
        self._copy_path_btn.setEnabled(False)
        actions.addWidget(self._copy_path_btn)

        body_layout.addLayout(actions)
        body_layout.addWidget(HSeparator())

        # --- File info
        info_hdr = QHBoxLayout()
        info_icon = QLabel()
        info_icon.setPixmap(ic.px(ic.INFO, color=ic.MUTED, size=13))
        info_icon.setFixedSize(16, 16)
        info_hdr.addWidget(info_icon)
        info_lbl = QLabel("File Info")
        info_lbl.setObjectName("sectionTitle")
        info_hdr.addWidget(info_lbl)
        info_hdr.addStretch()
        body_layout.addLayout(info_hdr)

        self._meta_name  = _MetaRow("Name",       "—")
        self._meta_size  = _MetaRow("Size",        "—")
        self._meta_date  = _MetaRow("Indexed",     "—")
        self._meta_conf  = _MetaRow("Confidence",  "—")
        self._meta_lang  = _MetaRow("Language",    "—")
        self._meta_eng   = _MetaRow("Engine",      "—")
        for row in (self._meta_name, self._meta_size, self._meta_date,
                    self._meta_conf, self._meta_lang, self._meta_eng):
            body_layout.addWidget(row)

        body_layout.addSpacing(4)
        body_layout.addWidget(HSeparator())

        # --- OCR text
        ocr_hdr = QHBoxLayout()
        ocr_icon = QLabel()
        ocr_icon.setPixmap(ic.px(ic.ALIGN_LEFT, color=ic.MUTED, size=13))
        ocr_icon.setFixedSize(16, 16)
        ocr_hdr.addWidget(ocr_icon)
        ocr_title = QLabel("Extracted Text")
        ocr_title.setObjectName("sectionTitle")
        ocr_hdr.addWidget(ocr_title)
        ocr_hdr.addStretch()

        self._copy_text_btn = _icon_action_btn(ic.COPY, "Copy extracted text")
        self._copy_text_btn.clicked.connect(self._copy_text)
        self._copy_text_btn.setEnabled(False)
        ocr_hdr.addWidget(self._copy_text_btn)
        body_layout.addLayout(ocr_hdr)

        self._ocr_box = QTextEdit()
        self._ocr_box.setObjectName("ocrBox")
        self._ocr_box.setReadOnly(True)
        self._ocr_box.setMinimumHeight(120)
        self._ocr_box.setMaximumHeight(260)
        self._ocr_box.setPlaceholderText("Extracted text will appear here…")
        body_layout.addWidget(self._ocr_box)

        body_layout.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)

    # ------------------------------------------------------------------

    def show_record(self, record: ScreenshotRecord) -> None:
        self._current = record
        path = Path(record.file_path)

        if path.exists():
            px = QPixmap(str(path))
            if not px.isNull():
                w = max(self._img_frame.width() - 8, 100)
                h = max(self._img_frame.height() - 8, 80)
                self._img_lbl.setPixmap(px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self._show_placeholder()
        else:
            self._show_placeholder()

        size_kb  = record.file_size // 1024
        size_str = f"{size_kb:,} KB" if size_kb < 1024 else f"{size_kb / 1024:.1f} MB"
        date_str = datetime.fromtimestamp(record.indexed_at).strftime("%d %b %Y, %H:%M")

        self._meta_name.setValue(record.file_name)
        self._meta_size.setValue(size_str)
        self._meta_date.setValue(date_str)
        self._meta_conf.setValue(f"{record.ocr_confidence:.0%}")
        self._meta_lang.setValue(record.language)
        self._meta_eng.setValue(record.engine_used)

        self._ocr_box.setPlainText(record.ocr_text or "No text extracted from this image.")

        exists = path.exists()
        self._open_btn.setEnabled(exists)
        self._reveal_btn.setEnabled(exists)
        self._copy_path_btn.setEnabled(True)
        self._copy_text_btn.setEnabled(bool(record.ocr_text))

        QTimer.singleShot(10, lambda: self._refit(record.file_path))

    def _refit(self, file_path: str) -> None:
        if not self._current or self._current.file_path != file_path:
            return
        p = Path(file_path)
        if not p.exists():
            return
        px = QPixmap(str(p))
        if px.isNull():
            return
        w = max(self._img_frame.width() - 8, 100)
        h = max(self._img_frame.height() - 8, 80)
        self._img_lbl.setPixmap(px.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def clear(self) -> None:
        self._current = None
        self._show_placeholder()
        for row in (self._meta_name, self._meta_size, self._meta_date,
                    self._meta_conf, self._meta_lang, self._meta_eng):
            row.setValue("—")
        self._ocr_box.clear()
        for btn in (self._open_btn, self._reveal_btn, self._copy_path_btn, self._copy_text_btn):
            btn.setEnabled(False)

    def _show_placeholder(self) -> None:
        ph_px = ic.px(ic.IMAGE, color="#2D2860", size=48)
        if not ph_px.isNull():
            self._img_lbl.setPixmap(ph_px)
            self._img_lbl.setText("")
        else:
            self._img_lbl.setText("Select a screenshot")
        self._img_lbl.setStyleSheet("background: transparent;")

    # ------------------------------------------------------------------

    def _open_image(self) -> None:
        if not self._current:
            return
        p = self._current.file_path
        if sys.platform == "win32":
            os.startfile(p)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])

    def _reveal(self) -> None:
        if not self._current:
            return
        p = Path(self._current.file_path)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(p)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])

    def _copy_path(self) -> None:
        if self._current:
            QApplication.clipboard().setText(self._current.file_path)

    def _copy_text(self) -> None:
        QApplication.clipboard().setText(self._ocr_box.toPlainText())
