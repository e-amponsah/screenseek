"""
Modern search bar with vector icon, debounced emission, and clear button.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget

from app.ui import icons as ic


class SearchBar(QWidget):
    search_triggered = Signal(str)
    DEBOUNCE_MS = 280

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("searchContainer")
        self.setMinimumHeight(44)
        self.setMaximumHeight(44)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        # Search icon
        self._icon_lbl = QLabel()
        self._icon_lbl.setObjectName("searchIcon")
        self._icon_lbl.setFixedSize(18, 18)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setPixmap(ic.px(ic.SEARCH, color=ic.MUTED, size=15))
        layout.addWidget(self._icon_lbl)

        # Text input
        self._input = QLineEdit()
        self._input.setObjectName("searchInput")
        self._input.setPlaceholderText("Search inside your screenshots…")
        self._input.setClearButtonEnabled(False)
        self._input.textChanged.connect(self._on_changed)
        self._input.returnPressed.connect(self._emit_now)
        layout.addWidget(self._input)

        # Clear button — hidden when field is empty
        self._clear_btn = QPushButton()
        self._clear_btn.setObjectName("searchClear")
        self._clear_btn.setFixedSize(22, 22)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        ic.set_icon(self._clear_btn, ic.TIMES, color=ic.MUTED, size=12)
        self._clear_btn.clicked.connect(self._input.clear)
        self._clear_btn.setVisible(False)
        layout.addWidget(self._clear_btn)

        self._input.textChanged.connect(lambda t: self._clear_btn.setVisible(bool(t)))

    # ------------------------------------------------------------------

    def _on_changed(self, _: str) -> None:
        self._timer.start(self.DEBOUNCE_MS)

    def _emit(self) -> None:
        self.search_triggered.emit(self._input.text().strip())

    def _emit_now(self) -> None:
        self._timer.stop()
        self._emit()

    def text(self) -> str:
        return self._input.text()

    def clear(self) -> None:
        self._input.clear()

    def set_focus(self) -> None:
        self._input.setFocus()
