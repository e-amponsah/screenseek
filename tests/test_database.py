"""Tests for the database manager."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.manager import DatabaseManager


@pytest.fixture
def db(tmp_path):
    manager = DatabaseManager(tmp_path / "test.db")
    yield manager
    manager.close()


class TestDatabaseInit:
    def test_creates_file(self, tmp_path):
        db = DatabaseManager(tmp_path / "sub" / "new.db")
        assert (tmp_path / "sub" / "new.db").exists()
        db.close()

    def test_default_settings_seeded(self, db):
        assert db.get_setting("theme") in ("dark", "light", "system")


class TestScreenshots:
    def _make_image(self, tmp_path, name="test.png") -> str:
        p = tmp_path / name
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        return str(p)

    def test_upsert_and_retrieve(self, db, tmp_path):
        img = self._make_image(tmp_path)
        db.upsert_screenshot(img, "hello world", 0.9, "en", "easyocr", "")
        rec = db.get_screenshot(img)
        assert rec is not None
        assert rec.ocr_text == "hello world"
        assert rec.file_name == "test.png"

    def test_upsert_updates_existing(self, db, tmp_path):
        img = self._make_image(tmp_path)
        db.upsert_screenshot(img, "first text", 0.8, "en", "easyocr", "")
        db.upsert_screenshot(img, "updated text", 0.95, "en", "easyocr", "")
        rec = db.get_screenshot(img)
        assert rec.ocr_text == "updated text"

    def test_screenshot_exists(self, db, tmp_path):
        img = self._make_image(tmp_path)
        assert not db.screenshot_exists(img)
        db.upsert_screenshot(img, "text", 0.9, "en", "easyocr", "")
        assert db.screenshot_exists(img)

    def test_delete_screenshot(self, db, tmp_path):
        img = self._make_image(tmp_path)
        db.upsert_screenshot(img, "text", 0.9, "en", "easyocr", "")
        assert db.delete_screenshot(img)
        assert not db.screenshot_exists(img)

    def test_count(self, db, tmp_path):
        assert db.count_screenshots() == 0
        db.upsert_screenshot(self._make_image(tmp_path, "a.png"), "a", 0.9, "en", "easyocr")
        db.upsert_screenshot(self._make_image(tmp_path, "b.png"), "b", 0.9, "en", "easyocr")
        assert db.count_screenshots() == 2

    def test_clear_all(self, db, tmp_path):
        db.upsert_screenshot(self._make_image(tmp_path), "text", 0.9, "en", "easyocr")
        db.clear_all_screenshots()
        assert db.count_screenshots() == 0


class TestFolders:
    def test_add_and_retrieve(self, db, tmp_path):
        folder = str(tmp_path / "shots")
        db.add_folder(folder)
        rec = db.get_folder(folder)
        assert rec is not None
        assert rec.enabled

    def test_remove_folder(self, db, tmp_path):
        folder = str(tmp_path / "shots")
        db.add_folder(folder)
        assert db.remove_folder(folder)
        assert db.get_folder(folder) is None

    def test_get_all_folders(self, db, tmp_path):
        db.add_folder(str(tmp_path / "a"))
        db.add_folder(str(tmp_path / "b"))
        folders = db.get_all_folders()
        assert len(folders) == 2

    def test_set_folder_enabled(self, db, tmp_path):
        folder = str(tmp_path / "shots")
        db.add_folder(folder)
        db.set_folder_enabled(folder, False)
        rec = db.get_folder(folder)
        assert not rec.enabled


class TestSettings:
    def test_get_and_set(self, db):
        db.set_setting("my_key", "my_value")
        assert db.get_setting("my_key") == "my_value"

    def test_default_value(self, db):
        assert db.get_setting("nonexistent_key", "default") == "default"

    def test_get_all_settings(self, db):
        settings = db.get_all_settings()
        assert "theme" in settings
