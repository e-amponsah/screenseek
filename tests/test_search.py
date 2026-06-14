"""Tests for the search engine."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.manager import DatabaseManager
from app.search.engine import SearchEngine, SearchFilters


@pytest.fixture
def db_with_data(tmp_path):
    db = DatabaseManager(tmp_path / "search_test.db")

    # Seed some records
    images = [
        ("img1.png", "Flight confirmation AF1234 Paris Geneva departure 10:30"),
        ("img2.png", "Hotel booking confirmation Geneva Marriott check-in July 15"),
        ("img3.png", "Visa approval letter embassy France"),
        ("img4.png", "Receipt Apple Store MacBook Pro invoice"),
        ("img5.png", "OTP code 847291 expires in 5 minutes"),
    ]
    for name, text in images:
        p = tmp_path / name
        p.write_bytes(b"\x89PNG" + b"\x00" * 50)
        db.upsert_screenshot(str(p), text, 0.9, "en", "easyocr", "")
    db.rebuild_fts()
    yield db
    db.close()


@pytest.fixture
def engine(db_with_data):
    return SearchEngine(db_with_data)


class TestSearchBasics:
    def test_empty_query_returns_results(self, engine):
        results = engine.search("")
        assert len(results) > 0

    def test_single_word_match(self, engine):
        results = engine.search("Geneva")
        paths = [r.record.file_name for r in results]
        assert any("img1" in p or "img2" in p for p in paths)

    def test_no_match_returns_empty(self, engine):
        results = engine.search("xyzqwerty12345nonexistent")
        assert len(results) == 0

    def test_multi_word_match(self, engine):
        results = engine.search("hotel booking")
        assert len(results) >= 1
        assert any("img2" in r.record.file_name for r in results)

    def test_partial_match(self, engine):
        results = engine.search("conf")   # matches "confirmation"
        assert len(results) >= 1

    def test_case_insensitive(self, engine):
        upper = engine.search("FLIGHT")
        lower = engine.search("flight")
        assert len(upper) == len(lower)

    def test_otp_search(self, engine):
        results = engine.search("OTP")
        assert any("img5" in r.record.file_name for r in results)


class TestSearchFilters:
    def test_folder_filter(self, engine, tmp_path):
        filters = SearchFilters(folder=str(tmp_path))
        results = engine.search("Geneva", filters)
        assert all(r.record.folder == str(tmp_path) for r in results)

    def test_nonexistent_folder_returns_empty(self, engine):
        filters = SearchFilters(folder="/nonexistent/folder")
        results = engine.search("Geneva", filters)
        assert len(results) == 0


class TestFTSQueryBuilder:
    def test_quoted_phrase(self, engine):
        fts = engine._build_fts_query('"exact phrase"')
        assert '"exact phrase"' in fts

    def test_prefix_wildcard_added(self, engine):
        fts = engine._build_fts_query("flight")
        assert "flight*" in fts

    def test_multi_word_prefix(self, engine):
        fts = engine._build_fts_query("hotel booking")
        assert "hotel*" in fts
        assert "booking*" in fts
