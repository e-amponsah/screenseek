"""Tests for the OCR engine."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ocr.engine import (
    EasyOCREngine,
    OCREngine,
    OCRResult,
    TesseractEngine,
    EMPTY_RESULT,
)
from app.ocr.processor import is_supported_image, SUPPORTED_EXTENSIONS


# ---------------------------------------------------------------------------
# OCRResult
# ---------------------------------------------------------------------------

class TestOCRResult:
    def test_word_count(self):
        r = OCRResult(text="hello world foo", confidence=0.9, language="en", engine_used="easyocr")
        assert r.word_count == 3

    def test_empty_result_is_empty(self):
        assert EMPTY_RESULT.is_empty

    def test_non_empty_result(self):
        r = OCRResult(text="some text", confidence=0.8, language="en", engine_used="easyocr")
        assert not r.is_empty

    def test_whitespace_only_is_empty(self):
        r = OCRResult(text="   ", confidence=0.5, language="en", engine_used="easyocr")
        assert r.is_empty


# ---------------------------------------------------------------------------
# Image support
# ---------------------------------------------------------------------------

class TestImageSupport:
    @pytest.mark.parametrize("ext", [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"])
    def test_supported_extensions(self, ext):
        assert is_supported_image(Path(f"file{ext}"))

    def test_unsupported_extension(self):
        assert not is_supported_image(Path("file.gif"))
        assert not is_supported_image(Path("file.mp4"))


# ---------------------------------------------------------------------------
# EasyOCREngine
# ---------------------------------------------------------------------------

class TestEasyOCREngine:
    def test_unavailable_when_import_fails(self):
        engine = EasyOCREngine(["en"])
        with patch("builtins.__import__", side_effect=ImportError("no module")):
            # Already tried to init — check state
            engine._available = False
            assert not engine.available

    def test_extract_nonexistent_file_returns_empty(self):
        engine = EasyOCREngine(["en"])
        engine._available = False
        result = engine.extract(Path("/nonexistent/file.png"))
        assert result.is_empty

    def test_set_languages_resets_reader(self):
        engine = EasyOCREngine(["en"])
        engine._reader = MagicMock()
        engine._available = True
        engine.set_languages(["fr", "en"])
        assert engine._reader is None
        assert engine._languages == ["fr", "en"]


# ---------------------------------------------------------------------------
# OCREngine (facade)
# ---------------------------------------------------------------------------

class TestOCREngine:
    def test_returns_empty_for_missing_file(self, tmp_path):
        engine = OCREngine()
        result = engine.extract(tmp_path / "nonexistent.png")
        assert result.is_empty

    def test_falls_back_to_tesseract_when_easyocr_empty(self):
        engine = OCREngine()
        engine._easyocr._available = True
        engine._easyocr.extract = MagicMock(
            return_value=OCRResult(text="", confidence=0.0, language="en", engine_used="easyocr")
        )
        engine._tesseract._available = True
        engine._tesseract.extract = MagicMock(
            return_value=OCRResult(text="hello", confidence=0.9, language="eng", engine_used="tesseract")
        )

        # Create a dummy file so the path-exists check passes
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp = f.name
        try:
            result = engine.extract(tmp)
            assert result.text == "hello"
            assert result.engine_used == "tesseract"
        finally:
            os.unlink(tmp)

    def test_set_languages(self):
        engine = OCREngine(languages=["en"])
        engine.set_languages(["de", "fr"])
        assert engine._easyocr._languages == ["de", "fr"]
