"""
DatabaseManager — all persistence operations for ScreenSeek.
Uses a single WAL-mode SQLite connection with thread safety via a lock.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from app.database.models import ALL_STATEMENTS, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data transfer objects
# ---------------------------------------------------------------------------

@dataclass
class ScreenshotRecord:
    id: int
    file_path: str
    file_name: str
    folder: str
    file_hash: str
    file_size: int
    created_at: float
    modified_at: float
    indexed_at: float
    ocr_text: str
    ocr_confidence: float
    language: str
    thumbnail_path: str
    engine_used: str

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ScreenshotRecord":
        return cls(**dict(row))


@dataclass
class FolderRecord:
    id: int
    path: str
    enabled: bool
    created_at: float

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "FolderRecord":
        d = dict(row)
        d["enabled"] = bool(d["enabled"])
        return cls(**d)


@dataclass
class SearchResult:
    record: ScreenshotRecord
    rank: float
    snippet: str = ""


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class DatabaseManager:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._initialise_schema()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._conn.execute("PRAGMA cache_size=-32000;")  # 32 MB page cache

    def _initialise_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            for stmt in ALL_STATEMENTS:
                cur.execute(stmt.strip())

            # Seed defaults only if the settings table is empty
            cur.execute("SELECT COUNT(*) FROM settings;")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?);",
                    DEFAULT_SETTINGS,
                )
            self._conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Screenshots CRUD
    # ------------------------------------------------------------------

    def upsert_screenshot(
        self,
        file_path: str,
        ocr_text: str,
        ocr_confidence: float,
        language: str,
        engine_used: str,
        thumbnail_path: str = "",
    ) -> int:
        """Insert or replace a screenshot record. Returns the row id."""
        p = Path(file_path)
        stat = p.stat() if p.exists() else None
        file_hash = _hash_file(p) if p.exists() else ""
        now = time.time()

        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO screenshots
                    (file_path, file_name, folder, file_hash, file_size,
                     created_at, modified_at, indexed_at,
                     ocr_text, ocr_confidence, language, thumbnail_path, engine_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_hash       = excluded.file_hash,
                    file_size       = excluded.file_size,
                    modified_at     = excluded.modified_at,
                    indexed_at      = excluded.indexed_at,
                    ocr_text        = excluded.ocr_text,
                    ocr_confidence  = excluded.ocr_confidence,
                    language        = excluded.language,
                    thumbnail_path  = excluded.thumbnail_path,
                    engine_used     = excluded.engine_used
                """,
                (
                    str(file_path),
                    p.name,
                    str(p.parent),
                    file_hash,
                    stat.st_size if stat else 0,
                    stat.st_ctime if stat else now,
                    stat.st_mtime if stat else now,
                    now,
                    ocr_text,
                    ocr_confidence,
                    language,
                    thumbnail_path,
                    engine_used,
                ),
            )
            self._conn.commit()
            return cur.lastrowid or self._get_id_by_path(file_path)

    def _get_id_by_path(self, file_path: str) -> int:
        cur = self._conn.execute(
            "SELECT id FROM screenshots WHERE file_path = ?;", (file_path,)
        )
        row = cur.fetchone()
        return row[0] if row else -1

    def delete_screenshot(self, file_path: str) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM screenshots WHERE file_path = ?;", (file_path,)
            )
            self._conn.commit()
            return cur.rowcount > 0

    def get_screenshot(self, file_path: str) -> Optional[ScreenshotRecord]:
        cur = self._conn.execute(
            "SELECT * FROM screenshots WHERE file_path = ?;", (file_path,)
        )
        row = cur.fetchone()
        return ScreenshotRecord.from_row(row) if row else None

    def get_screenshot_by_id(self, record_id: int) -> Optional[ScreenshotRecord]:
        cur = self._conn.execute(
            "SELECT * FROM screenshots WHERE id = ?;", (record_id,)
        )
        row = cur.fetchone()
        return ScreenshotRecord.from_row(row) if row else None

    def get_all_screenshots(self, folder: str | None = None) -> list[ScreenshotRecord]:
        if folder:
            cur = self._conn.execute(
                "SELECT * FROM screenshots WHERE folder = ? ORDER BY indexed_at DESC;",
                (folder,),
            )
        else:
            cur = self._conn.execute(
                "SELECT * FROM screenshots ORDER BY indexed_at DESC;"
            )
        return [ScreenshotRecord.from_row(r) for r in cur.fetchall()]

    def screenshot_exists(self, file_path: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM screenshots WHERE file_path = ?;", (file_path,)
        )
        return cur.fetchone() is not None

    def file_hash_for(self, file_path: str) -> Optional[str]:
        cur = self._conn.execute(
            "SELECT file_hash FROM screenshots WHERE file_path = ?;", (file_path,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def count_screenshots(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM screenshots;")
        return cur.fetchone()[0]

    def clear_all_screenshots(self) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM screenshots;")
            self._conn.execute(
                "INSERT INTO screenshots_fts(screenshots_fts) VALUES ('rebuild');"
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Folders CRUD
    # ------------------------------------------------------------------

    def add_folder(self, path: str) -> FolderRecord:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO folders(path, enabled, created_at) VALUES (?, 1, ?);",
                (path, now),
            )
            self._conn.commit()
        return self.get_folder(path)  # type: ignore[return-value]

    def remove_folder(self, path: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM folders WHERE path = ?;", (path,))
            self._conn.commit()
            return cur.rowcount > 0

    def get_folder(self, path: str) -> Optional[FolderRecord]:
        cur = self._conn.execute("SELECT * FROM folders WHERE path = ?;", (path,))
        row = cur.fetchone()
        return FolderRecord.from_row(row) if row else None

    def get_all_folders(self) -> list[FolderRecord]:
        cur = self._conn.execute("SELECT * FROM folders ORDER BY created_at;")
        return [FolderRecord.from_row(r) for r in cur.fetchall()]

    def set_folder_enabled(self, path: str, enabled: bool) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE folders SET enabled = ? WHERE path = ?;",
                (int(enabled), path),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def get_setting(self, key: str, default: str = "") -> str:
        cur = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?;", (key,)
        )
        row = cur.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value;",
                (key, value),
            )
            self._conn.commit()

    def get_all_settings(self) -> dict[str, str]:
        cur = self._conn.execute("SELECT key, value FROM settings;")
        return {row[0]: row[1] for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # Rebuild FTS index
    # ------------------------------------------------------------------

    def rebuild_fts(self) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO screenshots_fts(screenshots_fts) VALUES ('rebuild');"
            )
            self._conn.commit()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _hash_file(path: Path, chunk: int = 65536) -> str:
    """Fast file hash using first+last 64 KB + file size to avoid reading huge images fully."""
    h = hashlib.blake2b(digest_size=20)
    try:
        size = path.stat().st_size
        h.update(size.to_bytes(8, "little"))
        with path.open("rb") as f:
            h.update(f.read(chunk))
            if size > chunk * 2:
                f.seek(-chunk, 2)
                h.update(f.read(chunk))
    except Exception:
        pass
    return h.hexdigest()
