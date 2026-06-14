"""
Settings dialog — tabbed layout with toggle switches and clean section headers.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.settings.manager import SettingsManager
from app.ui import icons as ic
from app.ui.widgets import HSeparator, ToggleSwitch


def _section(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("settingsSectionHeader")
    return lbl


class _SettingRow(QWidget):
    """Label + optional description on left, control on right."""

    def __init__(
        self,
        label: str,
        control: QWidget,
        description: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(16)

        left = QVBoxLayout()
        title = QLabel(label)
        title.setObjectName("sectionTitle")
        left.addWidget(title)
        if description:
            desc = QLabel(description)
            desc.setObjectName("helpText")
            desc.setWordWrap(True)
            left.addWidget(desc)
        layout.addLayout(left, 1)

        layout.addWidget(control, 0, Qt.AlignRight | Qt.AlignVCenter)


class SettingsDialog(QDialog):
    settings_changed = Signal()
    theme_changed    = Signal(str)

    def __init__(self, settings: SettingsManager, current_theme: str = "dark", parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._theme    = current_theme
        self.setWindowTitle("Settings — ScreenSeek")
        self.setMinimumSize(520, 480)
        self.setMaximumWidth(620)
        self._build()
        self._load()

    # ------------------------------------------------------------------

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        root.addWidget(tabs, 1)

        # ----------------------------------------------------------------
        # General tab
        # ----------------------------------------------------------------
        general = QWidget()
        gl = QVBoxLayout(general)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(4)

        gl.addWidget(_section("Appearance"))
        gl.addWidget(HSeparator())
        gl.addSpacing(8)

        self._theme_toggle = ToggleSwitch(checked=(self._theme == "light"))
        self._theme_toggle.toggled.connect(self._on_theme_toggle)
        gl.addWidget(_SettingRow(
            "Theme",
            self._theme_toggle,
            "Switch between dark and light appearance.",
        ))

        self._theme_lbl = QLabel("Light Mode" if self._theme == "light" else "Dark Mode")
        self._theme_lbl.setObjectName("helpText")
        self._theme_lbl.setAlignment(Qt.AlignRight)
        gl.addWidget(self._theme_lbl)

        gl.addSpacing(16)
        gl.addWidget(_section("Startup & Monitoring"))
        gl.addWidget(HSeparator())
        gl.addSpacing(8)

        self._boot_toggle = ToggleSwitch()
        gl.addWidget(_SettingRow(
            "Start on boot",
            self._boot_toggle,
            "Launch ScreenSeek automatically when Windows starts.",
        ))

        self._monitor_toggle = ToggleSwitch()
        gl.addWidget(_SettingRow(
            "Auto-monitor folders",
            self._monitor_toggle,
            "Index new screenshots automatically as they appear.",
        ))

        gl.addStretch()
        tabs.addTab(general, "General")

        # ----------------------------------------------------------------
        # OCR tab
        # ----------------------------------------------------------------
        ocr_tab = QWidget()
        ol = QVBoxLayout(ocr_tab)
        ol.setContentsMargins(24, 20, 24, 20)
        ol.setSpacing(8)

        ol.addWidget(_section("OCR Engine"))
        ol.addWidget(HSeparator())
        ol.addSpacing(8)

        lang_label = QLabel("Languages")
        lang_label.setObjectName("sectionTitle")
        ol.addWidget(lang_label)

        self._lang_edit = QLineEdit()
        self._lang_edit.setPlaceholderText("e.g.  en, fr, de, es, zh, ar, hi")
        ol.addWidget(self._lang_edit)

        help_text = QLabel(
            "Comma-separated EasyOCR codes. Common codes: en (English), "
            "fr (French), de (German), es (Spanish), zh (Chinese), "
            "ar (Arabic), hi (Hindi), pt (Portuguese), ja (Japanese)."
        )
        help_text.setObjectName("helpText")
        help_text.setWordWrap(True)
        ol.addWidget(help_text)

        ol.addStretch()
        tabs.addTab(ocr_tab, "OCR")

        # ----------------------------------------------------------------
        # Thumbnails tab
        # ----------------------------------------------------------------
        thumb_tab = QWidget()
        tl = QVBoxLayout(thumb_tab)
        tl.setContentsMargins(24, 20, 24, 20)
        tl.setSpacing(8)

        tl.addWidget(_section("Thumbnail Cache"))
        tl.addWidget(HSeparator())
        tl.addSpacing(8)

        size_lbl = QLabel("Thumbnail size")
        size_lbl.setObjectName("sectionTitle")
        tl.addWidget(size_lbl)

        slider_row = QHBoxLayout()
        self._thumb_slider = QSlider(Qt.Horizontal)
        self._thumb_slider.setRange(64, 512)
        self._thumb_slider.setSingleStep(32)
        self._thumb_slider.setPageStep(64)
        slider_row.addWidget(self._thumb_slider)

        self._thumb_val_lbl = QLabel("256 px")
        self._thumb_val_lbl.setObjectName("badgeCount")
        self._thumb_val_lbl.setFixedWidth(54)
        self._thumb_val_lbl.setAlignment(Qt.AlignCenter)
        slider_row.addWidget(self._thumb_val_lbl)
        tl.addLayout(slider_row)

        self._thumb_slider.valueChanged.connect(
            lambda v: self._thumb_val_lbl.setText(f"{v} px")
        )

        tl.addWidget(QLabel("Larger thumbnails look sharper but use more disk space."))

        tl.addStretch()
        tabs.addTab(thumb_tab, "Thumbnails")

        # ----------------------------------------------------------------
        # About tab
        # ----------------------------------------------------------------
        about_tab = QWidget()
        al = QVBoxLayout(about_tab)
        al.setContentsMargins(24, 24, 24, 24)
        al.setSpacing(10)
        al.setAlignment(Qt.AlignTop)

        name_lbl = QLabel("ScreenSeek")
        nf = name_lbl.font()
        nf.setPointSize(20)
        nf.setBold(True)
        name_lbl.setFont(nf)
        name_lbl.setStyleSheet("color: #A29BFE;")
        al.addWidget(name_lbl)

        al.addWidget(QLabel("Version 1.0.0  ·  June 2026"))
        al.addWidget(HSeparator())
        al.addWidget(QLabel("Search your screenshots like Google searches the web."))
        al.addWidget(QLabel(
            "ScreenSeek uses EasyOCR and Tesseract to extract text from\n"
            "every screenshot in your chosen folders, then stores everything\n"
            "in a local SQLite database with full-text search."
        ))
        al.addSpacing(4)
        al.addWidget(HSeparator())
        al.addSpacing(4)

        # Privacy badge — icon instead of emoji
        privacy_row = QHBoxLayout()
        privacy_row.setSpacing(8)
        privacy_icon = QLabel()
        privacy_icon.setFixedSize(16, 16)
        privacy_icon.setPixmap(ic.px(ic.CHECK_CIRCLE, color=ic.SUCCESS, size=14))
        privacy_row.addWidget(privacy_icon)
        privacy_lbl = QLabel("100% offline — no internet, no telemetry, no data collection.")
        privacy_lbl.setObjectName("privacyBadge")
        privacy_row.addWidget(privacy_lbl, 1)
        al.addLayout(privacy_row)

        al.addStretch()
        tabs.addTab(about_tab, "About")

        # ----------------------------------------------------------------
        # Dialog button bar
        # ----------------------------------------------------------------
        btn_bar = QWidget()
        btn_bar.setObjectName("resultsHeader")
        bb = QHBoxLayout(btn_bar)
        bb.setContentsMargins(16, 8, 16, 8)
        bb.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bb.addWidget(cancel_btn)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        bb.addWidget(save_btn)

        root.addWidget(btn_bar)

    # ------------------------------------------------------------------

    def _load(self) -> None:
        s = self._settings
        self._theme_toggle.setChecked(s.theme == "light")
        self._boot_toggle.setChecked(s.start_on_boot)
        self._monitor_toggle.setChecked(s.monitor_enabled)
        self._lang_edit.setText(", ".join(s.ocr_languages))
        self._thumb_slider.setValue(s.thumbnail_size)

        for tog in (self._theme_toggle, self._boot_toggle, self._monitor_toggle):
            tog.setTheme(self._theme)

    def _on_theme_toggle(self, is_light: bool) -> None:
        new_theme = "light" if is_light else "dark"
        self._theme = new_theme
        self._theme_lbl.setText("Light Mode" if is_light else "Dark Mode")
        for tog in (self._theme_toggle, self._boot_toggle, self._monitor_toggle):
            tog.setTheme(new_theme)
        self.theme_changed.emit(new_theme)

    def _save(self) -> None:
        s = self._settings
        s.theme            = self._theme
        s.start_on_boot    = self._boot_toggle.isChecked()
        s.monitor_enabled  = self._monitor_toggle.isChecked()
        langs = [lang.strip() for lang in self._lang_edit.text().split(",") if lang.strip()]
        s.ocr_languages    = langs or ["en"]
        s.thumbnail_size   = self._thumb_slider.value()
        self.settings_changed.emit()
        self.accept()
