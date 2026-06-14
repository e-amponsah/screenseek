"""
Image pre-processing helpers to improve OCR accuracy.
Applies contrast enhancement and noise reduction before OCR.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif", ".heic"}


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def preprocess_image(image_path: Path) -> Optional["PIL.Image.Image"]:
    """
    Load and optionally enhance an image for OCR.
    Returns a PIL Image, or None if loading fails.
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter

        img = Image.open(image_path).convert("RGB")

        # Upscale small images — OCR accuracy improves significantly above 300 DPI equivalent
        MIN_DIM = 1000
        w, h = img.size
        if min(w, h) < MIN_DIM:
            scale = MIN_DIM / min(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # Mild contrast boost
        img = ImageEnhance.Contrast(img).enhance(1.5)

        # Mild sharpening
        img = img.filter(ImageFilter.SHARPEN)

        return img
    except Exception as exc:
        logger.error("Preprocessing failed for %s: %s", image_path, exc)
        return None


def image_to_grayscale(image_path: Path) -> Optional["PIL.Image.Image"]:
    """Return a grayscale version of the image (used by Tesseract path)."""
    try:
        from PIL import Image
        return Image.open(image_path).convert("L")
    except Exception as exc:
        logger.error("Grayscale conversion failed for %s: %s", image_path, exc)
        return None


def get_image_metadata(image_path: Path) -> dict:
    """Return basic image metadata without full OCR."""
    try:
        from PIL import Image
        img = Image.open(image_path)
        return {
            "width": img.width,
            "height": img.height,
            "mode": img.mode,
            "format": img.format or image_path.suffix.lstrip(".").upper(),
        }
    except Exception:
        return {}
