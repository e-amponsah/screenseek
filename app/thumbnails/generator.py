"""
Thumbnail generator — creates fixed-size WEBP thumbnails for search results.
Thumbnails are stored in a dedicated cache directory alongside the database.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_SIZE = 256    # pixels (square bounding box)


class ThumbnailGenerator:
    def __init__(self, cache_dir: Path, size: int = DEFAULT_SIZE) -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._size = size

    # ------------------------------------------------------------------

    def generate(self, image_path: Path | str) -> Optional[str]:
        """
        Generate thumbnail for image_path if not already cached.
        Returns the thumbnail path string, or None on failure.
        """
        image_path = Path(image_path)
        thumb_path = self._thumb_path(image_path)

        if thumb_path.exists():
            return str(thumb_path)

        return self._create_thumbnail(image_path, thumb_path)

    def invalidate(self, image_path: Path | str) -> None:
        """Remove cached thumbnail for a given source image."""
        thumb_path = self._thumb_path(Path(image_path))
        if thumb_path.exists():
            thumb_path.unlink(missing_ok=True)

    def set_size(self, size: int) -> None:
        self._size = size

    # ------------------------------------------------------------------

    def _thumb_path(self, image_path: Path) -> Path:
        name_hash = hashlib.blake2b(str(image_path).encode(), digest_size=16).hexdigest()
        return self._cache_dir / f"{name_hash}_{self._size}.webp"

    def _create_thumbnail(self, src: Path, dest: Path) -> Optional[str]:
        try:
            from PIL import Image

            with Image.open(src) as img:
                img = img.convert("RGB")
                img.thumbnail((self._size, self._size), Image.LANCZOS)
                img.save(dest, "WEBP", quality=75, optimize=True)
            logger.debug("Thumbnail created: %s", dest.name)
            return str(dest)
        except Exception as exc:
            logger.error("Thumbnail generation failed for %s: %s", src, exc)
            return None
