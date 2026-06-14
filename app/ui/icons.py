"""
Centralized icon factory backed by qtawesome (Font Awesome 5).
All icon calls go through here so the rest of the codebase stays clean.
Falls back to empty QIcon gracefully if qtawesome is unavailable.
"""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QPixmap

# ---------------------------------------------------------------------------
# qtawesome import — lazy, safe
# ---------------------------------------------------------------------------

_qta = None

def _get_qta():
    global _qta
    if _qta is None:
        try:
            import qtawesome as q
            _qta = q
        except Exception:
            _qta = False
    return _qta if _qta else None


# ---------------------------------------------------------------------------
# Palette-aware color helpers
# ---------------------------------------------------------------------------

# Colors used across both themes — callers can pass these constants or custom hex strings.
# Dark-theme defaults; callers supply overrides when in light mode.
MUTED   = "#9095C0"
PRIMARY = "#E4E6FF"
ACCENT  = "#6C5CE7"
ACCENT2 = "#A29BFE"
WHITE   = "#FFFFFF"
DANGER  = "#FF6B6B"
SUCCESS = "#00B894"
WARN    = "#FDCB6E"

# Light-mode overrides — pass these when on the light theme
L_MUTED   = "#6B6F9A"
L_PRIMARY = "#1A1B3A"
L_ACCENT  = "#6C5CE7"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def icon(name: str, color: str = MUTED, **opts) -> QIcon:
    """Return a QIcon for the given qtawesome icon name."""
    q = _get_qta()
    if q is None:
        return QIcon()
    try:
        return q.icon(name, color=color, **opts)
    except Exception:
        return QIcon()


def px(name: str, color: str = MUTED, size: int = 16) -> QPixmap:
    """Return a QPixmap for the given icon name at the given pixel size."""
    return icon(name, color).pixmap(QSize(size, size))


def set_icon(widget, name: str, color: str = MUTED, size: int = 16) -> None:
    """Convenience: set icon + icon-size on any QAbstractButton."""
    ic = icon(name, color)
    if not ic.isNull():
        widget.setIcon(ic)
        widget.setIconSize(QSize(size, size))


# ---------------------------------------------------------------------------
# Named icon constants (used throughout the app for consistency)
# ---------------------------------------------------------------------------

# Search / navigation
SEARCH      = "fa5s.search"
TIMES       = "fa5s.times"
TIMES_CIRCLE = "fa5s.times-circle"

# File system
FOLDER      = "fa5s.folder"
FOLDER_OPEN = "fa5s.folder-open"
IMAGE       = "fa5s.image"
IMAGES      = "fa5s.images"
FILE_IMAGE  = "far.file-image"

# Actions
PLUS        = "fa5s.plus"
MINUS       = "fa5s.minus"
TRASH       = "fa5s.trash-alt"
SYNC        = "fa5s.sync-alt"
COPY        = "fa5s.copy"
LINK        = "fa5s.link"
EXTERNAL    = "fa5s.external-link-alt"
DOWNLOAD    = "fa5s.download"

# UI chrome
COG         = "fa5s.cog"
MOON        = "fa5s.moon"
SUN         = "fa5s.sun"
EYE         = "fa5s.eye"
INFO        = "fa5s.info-circle"
ALIGN_LEFT  = "fa5s.align-left"
LAYER_GROUP = "fa5s.layer-group"
DATABASE    = "fa5s.database"
CLOCK       = "fa5s.clock"
CHEVRON_R   = "fa5s.chevron-right"
ELLIPSIS    = "fa5s.ellipsis-h"
CHECK       = "fa5s.check"
CHECK_CIRCLE = "fa5s.check-circle"
EXCLAMATION = "fa5s.exclamation-circle"
