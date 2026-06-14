"""Tests for the indexing pipeline."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.manager import DatabaseManager
from app.indexer import IndexingPipeline
from app.ocr.engine import OCREngine, OCRResult
from app.thumbnails.generator import ThumbnailGenerator


@pytest.fixture
def db(tmp_path):
    manager = DatabaseManager(tmp_path / "idx.db")
    yield manager
    manager.close()


@pytest.fixture
def mock_ocr():
    ocr = MagicMock(spec=OCREngine)
    ocr.extract.return_value = OCRResult(
        text="sample ocr text",
        confidence=0.92,
        language="en",
        engine_used="easyocr",
    )
    return ocr


@pytest.fixture
def mock_thumbs(tmp_path):
    thumbs = MagicMock(spec=ThumbnailGenerator)
    thumbs.generate.return_value = str(tmp_path / "thumb.webp")
    return thumbs


@pytest.fixture
def pipeline(db, mock_ocr, mock_thumbs):
    return IndexingPipeline(db, mock_ocr, mock_thumbs)


def _make_png(directory: Path, name: str = "test.png") -> Path:
    p = directory / name
    try:
        from PIL import Image
        Image.new("RGB", (100, 100)).save(p, "PNG")
    except ImportError:
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return p


class TestIndexingPipeline:
    def test_index_single_image(self, pipeline, db, tmp_path):
        img = _make_png(tmp_path)
        result = pipeline.index_single(str(img))
        assert result == "indexed"
        assert db.screenshot_exists(str(img))

    def test_index_folder(self, pipeline, db, tmp_path):
        folder = tmp_path / "shots"
        folder.mkdir()
        _make_png(folder, "a.png")
        _make_png(folder, "b.png")
        summary = pipeline.index_folders([str(folder)])
        assert summary["indexed"] == 2

    def test_skip_unchanged_file(self, pipeline, db, tmp_path):
        img = _make_png(tmp_path)
        pipeline.index_single(str(img))
        # Second index without force should skip (same hash)
        result = pipeline._process_image(str(img), force_reindex=False)
        assert result == "skipped"

    def test_force_reindex(self, pipeline, db, tmp_path):
        img = _make_png(tmp_path)
        pipeline.index_single(str(img))
        result = pipeline._process_image(str(img), force_reindex=True)
        assert result == "indexed"

    def test_missing_file_returns_skipped(self, pipeline):
        result = pipeline.index_single("/nonexistent/path/img.png")
        assert result == "skipped"

    def test_purge_missing_removes_deleted(self, pipeline, db, tmp_path):
        folder = tmp_path / "shots"
        folder.mkdir()
        img = _make_png(folder)
        db.add_folder(str(folder))
        pipeline.index_single(str(img))
        assert db.screenshot_exists(str(img))

        # Delete the file
        img.unlink()
        deleted = pipeline._purge_missing([str(folder)])
        assert deleted == 1
        assert not db.screenshot_exists(str(img))
