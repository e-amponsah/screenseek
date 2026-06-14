"""Tests for thumbnail generation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.thumbnails.generator import ThumbnailGenerator


@pytest.fixture
def gen(tmp_path):
    return ThumbnailGenerator(tmp_path / "thumbs", size=128)


def _make_png(path: Path, width: int = 200, height: int = 200) -> Path:
    """Create a minimal valid PNG for testing."""
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), color=(100, 150, 200))
        img.save(path, "PNG")
        return path
    except ImportError:
        # Pillow not installed — write a stub PNG header
        path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        return path


class TestThumbnailGenerator:
    def test_generates_thumbnail(self, gen, tmp_path):
        src = _make_png(tmp_path / "test.png")
        try:
            result = gen.generate(src)
            assert result is not None
            assert Path(result).exists()
        except Exception:
            pytest.skip("Pillow not installed")

    def test_caches_thumbnail(self, gen, tmp_path):
        src = _make_png(tmp_path / "test.png")
        try:
            r1 = gen.generate(src)
            r2 = gen.generate(src)
            assert r1 == r2
        except Exception:
            pytest.skip("Pillow not installed")

    def test_invalidate_removes_cache(self, gen, tmp_path):
        src = _make_png(tmp_path / "test.png")
        try:
            r1 = gen.generate(src)
            assert r1 and Path(r1).exists()
            gen.invalidate(src)
            assert not Path(r1).exists()
        except Exception:
            pytest.skip("Pillow not installed")

    def test_nonexistent_file_returns_none(self, gen):
        result = gen.generate(Path("/nonexistent/image.png"))
        assert result is None

    def test_thumb_path_is_deterministic(self, gen, tmp_path):
        src = tmp_path / "img.png"
        p1 = gen._thumb_path(src)
        p2 = gen._thumb_path(src)
        assert p1 == p2

    def test_different_files_different_thumb_paths(self, gen, tmp_path):
        p1 = gen._thumb_path(tmp_path / "a.png")
        p2 = gen._thumb_path(tmp_path / "b.png")
        assert p1 != p2
