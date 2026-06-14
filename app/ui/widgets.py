"""
Shared UI widget components — ToggleSwitch, StatCard, FilterPill, IconButton, EmptyState.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QSize,
    Qt,
    Signal,
    Property,
)
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.ui.styles import get_palette


# ---------------------------------------------------------------------------
# ToggleSwitch
# ---------------------------------------------------------------------------

class ToggleSwitch(QWidget):
    """Animated pill toggle switch."""

    toggled = Signal(bool)

    _W, _H, _D = 44, 24, 18

    def __init__(self, checked: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(self._W, self._H)
        self.setCursor(Qt.PointingHandCursor)
        self._checked = checked
        self._handle_x = float(self._W - self._D - 3) if checked else 3.0
        self._theme = "dark"

        self._anim = QPropertyAnimation(self, b"handle_x", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def _get_hx(self) -> float:
        return self._handle_x

    def _set_hx(self, val: float) -> None:
        self._handle_x = val
        self.update()

    handle_x = Property(float, _get_hx, _set_hx)

    def setTheme(self, theme: str) -> None:
        self._theme = theme
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool) -> None:
        if self._checked != val:
            self._checked = val
            self._animate()

    def _animate(self) -> None:
        end = float(self._W - self._D - 3) if self._checked else 3.0
        self._anim.stop()
        self._anim.setStartValue(self._handle_x)
        self._anim.setEndValue(end)
        self._anim.start()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._checked = not self._checked
            self._animate()
            self.toggled.emit(self._checked)

    def paintEvent(self, event) -> None:
        p = get_palette(self._theme)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Track
        track_color = QColor(p["accent"]) if self._checked else QColor(p["border_hover"])
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        r = self._H / 2
        painter.drawRoundedRect(0, 0, self._W, self._H, r, r)

        # Handle
        painter.setBrush(QColor("#FFFFFF"))
        hy = (self._H - self._D) // 2
        painter.drawEllipse(int(self._handle_x), hy, self._D, self._D)
        painter.end()

    def sizeHint(self) -> QSize:
        return QSize(self._W, self._H)


# ---------------------------------------------------------------------------
# StatCard
# ---------------------------------------------------------------------------

class StatCard(QWidget):
    """Icon + large number + label card for the sidebar stat section."""

    def __init__(self, icon_name: str, value: str, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("statCard")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        from app.ui import icons as ic
        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(26, 26)
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setPixmap(ic.px(icon_name, color=ic.ACCENT, size=20))
        layout.addWidget(self._icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        self._value_lbl = QLabel(value)
        self._value_lbl.setObjectName("statValue")
        self._label_lbl = QLabel(label)
        self._label_lbl.setObjectName("statLabel")
        text_col.addWidget(self._value_lbl)
        text_col.addWidget(self._label_lbl)
        layout.addLayout(text_col)
        layout.addStretch()

    def setValue(self, val: str) -> None:
        self._value_lbl.setText(val)

    def setLabel(self, lbl: str) -> None:
        self._label_lbl.setText(lbl)


# ---------------------------------------------------------------------------
# FilterPill
# ---------------------------------------------------------------------------

class FilterPill(QPushButton):
    def __init__(self, text: str, active: bool = False, parent=None) -> None:
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(active)
        self.setCursor(Qt.PointingHandCursor)
        self._refresh_style()
        self.toggled.connect(lambda _: self._refresh_style())

    def _refresh_style(self) -> None:
        self.setObjectName("filterPillActive" if self.isChecked() else "filterPill")
        self.setStyle(self.style())

    def sizeHint(self) -> QSize:
        sh = super().sizeHint()
        return QSize(max(sh.width(), 64), 28)


# ---------------------------------------------------------------------------
# IconButton
# ---------------------------------------------------------------------------

class IconButton(QPushButton):
    """Square ghost button showing a single vector icon (no text)."""

    def __init__(
        self,
        icon_name: str,
        tooltip: str = "",
        color: str = "#9095C0",
        size: int = 18,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("iconBtn")
        self.setFixedSize(34, 34)
        self.setCursor(Qt.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

        from app.ui import icons as ic
        ico = ic.icon(icon_name, color=color)
        if not ico.isNull():
            self.setIcon(ico)
            self.setIconSize(QSize(size, size))


# ---------------------------------------------------------------------------
# Separator / SectionLabel
# ---------------------------------------------------------------------------

class HSeparator(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class SectionLabel(QLabel):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text.upper(), parent)
        self.setObjectName("sidebarSection")


# ---------------------------------------------------------------------------
# EmptyState
# ---------------------------------------------------------------------------

class EmptyState(QWidget):
    """Centered placeholder shown when there are no results."""

    def __init__(
        self,
        icon_name: str,
        title: str,
        subtitle: str,
        icon_color: str = "#2D2860",
        parent=None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(14)

        from app.ui import icons as ic
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        px = ic.px(icon_name, color=icon_color, size=56)
        if not px.isNull():
            icon_lbl.setPixmap(px)
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("emptyTitle")
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setObjectName("emptySubtitle")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setWordWrap(True)
        sub_lbl.setMaximumWidth(300)
        layout.addWidget(sub_lbl)


# ---------------------------------------------------------------------------
# Drop-shadow helper
# ---------------------------------------------------------------------------

def add_card_shadow(widget: QWidget, blur: int = 18, opacity: float = 0.35) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 4)
    effect.setColor(QColor(0, 0, 0, int(255 * opacity)))
    widget.setGraphicsEffect(effect)
