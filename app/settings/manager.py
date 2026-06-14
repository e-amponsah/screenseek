"""
Settings manager — thin wrapper that syncs app-level settings with the database.
Provides typed accessors for each setting key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.database.manager import DatabaseManager


class SettingsManager:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Typed accessors
    # ------------------------------------------------------------------

    @property
    def theme(self) -> str:
        return self._db.get_setting("theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        assert value in ("dark", "light", "system")
        self._db.set_setting("theme", value)

    @property
    def ocr_languages(self) -> list[str]:
        raw = self._db.get_setting("ocr_languages", "en")
        return [l.strip() for l in raw.split(",") if l.strip()]

    @ocr_languages.setter
    def ocr_languages(self, langs: list[str]) -> None:
        self._db.set_setting("ocr_languages", ",".join(langs))

    @property
    def thumbnail_size(self) -> int:
        return int(self._db.get_setting("thumbnail_size", "256"))

    @thumbnail_size.setter
    def thumbnail_size(self, size: int) -> None:
        self._db.set_setting("thumbnail_size", str(size))

    @property
    def monitor_enabled(self) -> bool:
        return self._db.get_setting("monitor_enabled", "true").lower() == "true"

    @monitor_enabled.setter
    def monitor_enabled(self, value: bool) -> None:
        self._db.set_setting("monitor_enabled", "true" if value else "false")

    @property
    def start_on_boot(self) -> bool:
        return self._db.get_setting("start_on_boot", "false").lower() == "true"

    @start_on_boot.setter
    def start_on_boot(self, value: bool) -> None:
        self._db.set_setting("start_on_boot", "true" if value else "false")

    # ------------------------------------------------------------------
    # Generic access for any key
    # ------------------------------------------------------------------

    def get(self, key: str, default: str = "") -> str:
        return self._db.get_setting(key, default)

    def set(self, key: str, value: str) -> None:
        self._db.set_setting(key, value)

    def all(self) -> dict[str, str]:
        return self._db.get_all_settings()
