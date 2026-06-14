"""
ScreenSeek — Search your screenshots like Google searches the web.
Entry point for both development and packaged (PyInstaller) execution.
"""

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

LOG_DIR = Path.home() / ".screenseek" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "screenseek.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger("screenseek")


# ---------------------------------------------------------------------------
# Startup diagnostic — runs before UI so errors land in the log file
# ---------------------------------------------------------------------------

def _log_env() -> None:
    """Log Python environment and all critical dependency imports."""
    import os
    frozen = getattr(sys, "frozen", False)
    meipass = getattr(sys, "_MEIPASS", None)
    logger.info("Python %s | frozen=%s | _MEIPASS=%s", sys.version, frozen, meipass)
    logger.info("Executable: %s", sys.executable)
    logger.info("Log file:   %s", LOG_DIR / "screenseek.log")

    checks = [
        "PySide6",
        "PySide6.QtWidgets",
        "qtawesome",
        "PIL",
        "cv2",
        "numpy",
        "torch",
        "torchvision",
        "easyocr",
        "pytesseract",
        "scipy",
        "skimage",
        "shapely",
        "bidi",
        "onnxruntime",
        "yaml",
        "watchdog",
    ]
    for mod in checks:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "?")
            logger.info("  [OK] %-16s %s", mod, ver)
        except Exception as exc:
            logger.error("  [FAIL] %-14s %s", mod, exc)

    # Tesseract binary detection
    try:
        import pytesseract, os as _os
        _WIN_PATHS = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        if sys.platform == "win32":
            for p in _WIN_PATHS:
                if _os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break
        v = pytesseract.get_tesseract_version()
        logger.info("  [OK] tesseract binary  %s", v)
    except Exception as exc:
        logger.warning("  [WARN] tesseract binary  %s", exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("Starting ScreenSeek…")
    _log_env()

    try:
        from PySide6.QtWidgets import QApplication
        from app.ui import fonts as app_fonts

        app = QApplication(sys.argv)
        app.setApplicationName("ScreenSeek")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("ScreenSeek")

        resolved = app_fonts.setup(app)
        logger.info("Font: %s", resolved)

        from app.ui.main_window import MainWindow
        window = MainWindow()
        window.show()

        sys.exit(app.exec())
    except ImportError as exc:
        logger.exception("Missing dependency: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.exception("Fatal error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
