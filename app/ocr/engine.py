"""
OCR engine with EasyOCR as primary and Tesseract as fallback.
Lazy-loads models on first use to keep startup fast.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# --- Result type ---------------------------------------------------------

@dataclass
class OCRResult:
    text: str
    confidence: float          # 0.0 – 1.0
    language: str
    engine_used: str           # "easyocr" | "tesseract" | "none"
    word_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.word_count = len(self.text.split()) if self.text else 0

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


EMPTY_RESULT = OCRResult(text="", confidence=0.0, language="unknown", engine_used="none")


# --- EasyOCR wrapper -----------------------------------------------------

class EasyOCREngine:
    """Thread-safe, lazily-initialised EasyOCR wrapper."""

    def __init__(self, languages: list[str] | None = None) -> None:
        self._languages = languages or ["en"]
        self._reader = None
        self._lock = threading.Lock()
        self._available: Optional[bool] = None

    def _get_reader(self):
        if self._reader is not None:
            return self._reader
        with self._lock:
            if self._reader is not None:
                return self._reader
            try:
                import easyocr  # type: ignore
                self._reader = easyocr.Reader(
                    self._languages,
                    gpu=False,          # safer default; GPU auto-detected at runtime
                    verbose=False,
                )
                self._available = True
                logger.info("EasyOCR initialised with languages: %s", self._languages)
            except ImportError as exc:
                logger.exception("EasyOCR import failed (missing package or DLL): %s", exc)
                self._available = False
            except Exception as exc:
                logger.exception("EasyOCR init failed: %s", exc)
                self._available = False
        return self._reader

    @property
    def available(self) -> bool:
        if self._available is None:
            self._get_reader()
        return bool(self._available)

    def extract(self, image_path: Path) -> OCRResult:
        reader = self._get_reader()
        if reader is None:
            return EMPTY_RESULT
        try:
            results = reader.readtext(str(image_path), detail=1, paragraph=False)
            if not results:
                return OCRResult(text="", confidence=0.0, language=self._languages[0], engine_used="easyocr")

            texts, confidences = [], []
            for _bbox, text, conf in results:
                if text.strip():
                    texts.append(text.strip())
                    confidences.append(conf)

            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return OCRResult(
                text=full_text,
                confidence=round(avg_confidence, 4),
                language=self._languages[0],
                engine_used="easyocr",
            )
        except Exception as exc:
            logger.error("EasyOCR extraction error on %s: %s", image_path, exc)
            return EMPTY_RESULT

    def set_languages(self, languages: list[str]) -> None:
        """Change OCR languages — forces re-initialisation on next call."""
        with self._lock:
            self._languages = languages
            self._reader = None
            self._available = None


# --- Tesseract wrapper ---------------------------------------------------

_TESSERACT_WIN_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


class TesseractEngine:
    """Thin pytesseract wrapper used as a fallback."""

    def __init__(self, language: str = "eng") -> None:
        self._language = language
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        if self._available is None:
            try:
                import os
                import sys
                import pytesseract  # type: ignore

                # On Windows the installer doesn't always add Tesseract to PATH.
                # Try the standard install locations before checking the version.
                if sys.platform == "win32":
                    for candidate in _TESSERACT_WIN_PATHS:
                        if os.path.exists(candidate):
                            pytesseract.pytesseract.tesseract_cmd = candidate
                            logger.info("Tesseract found at: %s", candidate)
                            break

                pytesseract.get_tesseract_version()
                self._available = True
            except Exception:
                self._available = False
        return self._available

    def extract(self, image_path: Path) -> OCRResult:
        try:
            import pytesseract  # type: ignore
            from PIL import Image

            img = Image.open(image_path)
            data = pytesseract.image_to_data(
                img,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
            )
            words, confs = [], []
            for word, conf in zip(data["text"], data["conf"]):
                if word.strip() and int(conf) > 0:
                    words.append(word.strip())
                    confs.append(int(conf) / 100.0)

            full_text = " ".join(words)
            avg_conf = sum(confs) / len(confs) if confs else 0.0
            return OCRResult(
                text=full_text,
                confidence=round(avg_conf, 4),
                language=self._language,
                engine_used="tesseract",
            )
        except Exception as exc:
            logger.error("Tesseract extraction error on %s: %s", image_path, exc)
            return EMPTY_RESULT


# --- Unified OCR facade --------------------------------------------------

class OCREngine:
    """
    Public facade that tries EasyOCR first, falls back to Tesseract,
    and returns a structured OCRResult regardless of outcome.
    """

    def __init__(
        self,
        languages: list[str] | None = None,
        tesseract_lang: str = "eng",
    ) -> None:
        self._easyocr = EasyOCREngine(languages or ["en"])
        self._tesseract = TesseractEngine(tesseract_lang)

    # ------------------------------------------------------------------
    def extract(self, image_path: Path | str) -> OCRResult:
        path = Path(image_path)
        if not path.exists():
            logger.warning("Image not found: %s", path)
            return EMPTY_RESULT

        # Try EasyOCR
        if self._easyocr.available:
            result = self._easyocr.extract(path)
            if not result.is_empty:
                return result
            logger.debug("EasyOCR returned empty result for %s; trying Tesseract.", path.name)

        # Try Tesseract
        if self._tesseract.available:
            result = self._tesseract.extract(path)
            if not result.is_empty:
                return result

        logger.warning("Both OCR engines returned empty for %s", path.name)
        return OCRResult(text="", confidence=0.0, language="unknown", engine_used="none")

    # ------------------------------------------------------------------
    def set_languages(self, languages: list[str], tesseract_lang: str = "eng") -> None:
        self._easyocr.set_languages(languages)
        self._tesseract._language = tesseract_lang

    @property
    def easyocr_available(self) -> bool:
        return self._easyocr.available

    @property
    def tesseract_available(self) -> bool:
        return self._tesseract.available
