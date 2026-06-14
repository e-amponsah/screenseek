"""
Font loader — registers Poppins from assets/fonts/, falls back to system fonts.
Call setup(app) once, after QApplication is created, before any UI is shown.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

_FAMILY: str = ""


def _fonts_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / "fonts"
    return Path(__file__).resolve().parent.parent.parent / "assets" / "fonts"


def load_poppins() -> str:
    """Register Poppins .ttf files and return the resolved font family name."""
    global _FAMILY
    if _FAMILY:
        return _FAMILY

    fonts_dir = _fonts_dir()
    registered = 0
    for variant in (
        "Poppins-Regular.ttf",
        "Poppins-Medium.ttf",
        "Poppins-SemiBold.ttf",
        "Poppins-Bold.ttf",
    ):
        path = fonts_dir / variant
        if path.exists():
            fid = QFontDatabase.addApplicationFont(str(path))
            if fid >= 0:
                registered += 1

    families = set(QFontDatabase.families())

    for candidate in ("Poppins", "Inter", "Segoe UI Variable", "Segoe UI", "Helvetica Neue", "Arial"):
        if candidate in families:
            _FAMILY = candidate
            return _FAMILY

    _FAMILY = "Arial"
    return _FAMILY


def family() -> str:
    """Return the resolved font family name (empty string before setup() is called)."""
    return _FAMILY if _FAMILY else "Segoe UI"


def setup(app) -> str:
    """Load fonts and set the application-wide font. Returns the family name used."""
    fam = load_poppins()
    f = QFont(fam, 10)
    f.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    app.setFont(f)
    return fam
