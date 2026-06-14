"""
Search engine built on SQLite FTS5.
Supports: single-word, multi-word, phrase (quoted), and partial matching.
Returns results ranked by relevance (FTS5 BM25 rank).
"""

from __future__ import annotations

import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.database.manager import DatabaseManager, ScreenshotRecord

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    folder: Optional[str] = None
    date_from: Optional[float] = None     # Unix timestamp
    date_to: Optional[float] = None
    file_extension: Optional[str] = None


@dataclass
class SearchResultItem:
    record: ScreenshotRecord
    rank: float
    snippet: str


class SearchEngine:
    """
    Wraps DatabaseManager to provide ranked full-text search.

    Query semantics:
      - "word"              → partial token match (word*)
      - "word1 word2"       → both words must appear
      - '"exact phrase"'    → phrase match
    """

    SNIPPET_TOKENS = 30

    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        limit: int = 5000,
    ) -> list[SearchResultItem]:
        query = query.strip()
        if not query:
            return self._recent_screenshots(filters, limit)

        fts_query = self._build_fts_query(query)
        return self._run_fts_search(fts_query, query, filters, limit)

    def recent_screenshots(self, limit: int = 50) -> list[ScreenshotRecord]:
        """Return the most recently indexed screenshots."""
        conn = self._db._conn
        cur = conn.execute(
            "SELECT * FROM screenshots ORDER BY indexed_at DESC LIMIT ?;", (limit,)
        )
        return [ScreenshotRecord.from_row(r) for r in cur.fetchall()]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _recent_screenshots(
        self,
        filters: Optional[SearchFilters],
        limit: int,
    ) -> list[SearchResultItem]:
        """Return all screenshots ordered by most-recently-indexed."""
        where, params = self._build_where(filters)
        # _build_where uses the `s` alias, so give the table that alias here too
        sql = f"SELECT s.* FROM screenshots s{where} ORDER BY s.indexed_at DESC LIMIT ?;"
        params.append(limit)
        try:
            cur = self._db._conn.execute(sql, params)
            return [
                SearchResultItem(record=ScreenshotRecord.from_row(r), rank=0.0, snippet="")
                for r in cur.fetchall()
            ]
        except sqlite3.OperationalError as exc:
            logger.error("Recent-screenshots query failed: %s", exc)
            return []

    def _build_fts_query(self, raw: str) -> str:
        """Convert a natural-language query into an FTS5 query string."""
        quoted   = re.findall(r'"[^"]+"', raw)
        unquoted = re.sub(r'"[^"]+"', "", raw).split()

        parts = list(quoted)
        for word in unquoted:
            clean = re.sub(r'[^\w\s]', '', word)
            if clean:
                parts.append(f"{clean}*")

        return " ".join(parts) if parts else raw

    def _run_fts_search(
        self,
        fts_query: str,
        original_query: str,
        filters: Optional[SearchFilters],
        limit: int,
    ) -> list[SearchResultItem]:
        conn = self._db._conn

        filter_where, filter_params = self._build_where(filters)
        join_filter = filter_where.replace("WHERE", "AND") if filter_where else ""

        sql = f"""
            SELECT
                s.*,
                fts.rank,
                snippet(screenshots_fts, 1, '<b>', '</b>', '…', {self.SNIPPET_TOKENS}) AS snip
            FROM screenshots_fts fts
            JOIN screenshots s ON s.id = fts.rowid
            WHERE screenshots_fts MATCH ?
            {join_filter}
            ORDER BY fts.rank
            LIMIT ?;
        """
        params = [fts_query] + filter_params + [limit]

        try:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()
        except sqlite3.OperationalError as exc:
            logger.warning("FTS query error (%s), falling back to LIKE search.", exc)
            return self._like_fallback(original_query, filters, limit)

        results = []
        for row in rows:
            d = dict(row)
            snip = d.pop("snip", "")
            rank = d.pop("rank", 0.0)
            record = ScreenshotRecord(**{k: d[k] for k in ScreenshotRecord.__dataclass_fields__})
            results.append(SearchResultItem(record=record, rank=float(rank), snippet=snip))
        return results

    def _like_fallback(
        self,
        query: str,
        filters: Optional[SearchFilters],
        limit: int,
    ) -> list[SearchResultItem]:
        """Simple LIKE-based fallback for when FTS query is malformed."""
        pattern = f"%{query}%"
        where, params = self._build_where(filters)
        # _like_fallback query also uses the s alias
        connector = "AND" if where else "WHERE"
        sql = (
            f"SELECT s.* FROM screenshots s{where} "
            f"{connector} (s.ocr_text LIKE ? OR s.file_name LIKE ?) "
            f"ORDER BY s.indexed_at DESC LIMIT ?;"
        )
        params.extend([pattern, pattern, limit])
        try:
            cur = self._db._conn.execute(sql, params)
            return [
                SearchResultItem(record=ScreenshotRecord.from_row(r), rank=0.0, snippet="")
                for r in cur.fetchall()
            ]
        except sqlite3.OperationalError as exc:
            logger.error("LIKE fallback failed: %s", exc)
            return []

    def _build_where(
        self, filters: Optional[SearchFilters]
    ) -> tuple[str, list]:
        if not filters:
            return "", []
        clauses, params = [], []
        if filters.folder:
            clauses.append("s.folder = ?")
            params.append(filters.folder)
        if filters.date_from is not None:
            clauses.append("s.indexed_at >= ?")
            params.append(filters.date_from)
        if filters.date_to is not None:
            clauses.append("s.indexed_at <= ?")
            params.append(filters.date_to)
        if filters.file_extension:
            ext = filters.file_extension.lower().lstrip(".")
            clauses.append("lower(s.file_name) LIKE ?")
            params.append(f"%.{ext}")

        if not clauses:
            return "", []
        return " WHERE " + " AND ".join(clauses), params
