# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ScreenSeek — onedir mode.
Build:   pyinstaller screenseek.spec --distpath release
Output:  release/ScreenSeek/ScreenSeek.exe  (+ all supporting files)
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH)

block_cipher = None

# Collect every package that EasyOCR depends on at runtime.
# collect_all() gathers Python source, native DLLs, and data files together.
torch_datas,       torch_binaries,       torch_hiddenimports       = collect_all("torch")
torchvision_datas, torchvision_binaries, torchvision_hiddenimports = collect_all("torchvision")
easyocr_datas,     easyocr_binaries,     easyocr_hiddenimports     = collect_all("easyocr")
cv2_datas,         cv2_binaries,         cv2_hiddenimports         = collect_all("cv2")
scipy_datas,       scipy_binaries,       scipy_hiddenimports       = collect_all("scipy")
skimage_datas,     skimage_binaries,     skimage_hiddenimports     = collect_all("skimage")
bidi_datas,        bidi_binaries,        bidi_hiddenimports        = collect_all("bidi")

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=(
        []
        + torch_binaries
        + torchvision_binaries
        + easyocr_binaries
        + cv2_binaries
        + scipy_binaries
        + skimage_binaries
        + bidi_binaries
    ),
    datas=(
        [
            (str(ROOT / "assets" / "logo"),        "assets/logo"),
            (str(ROOT / "assets" / "screenshots"), "assets/screenshots"),
            (str(ROOT / "assets" / "fonts"),       "assets/fonts"),
        ]
        + torch_datas
        + torchvision_datas
        + easyocr_datas
        + cv2_datas
        + scipy_datas
        + skimage_datas
        + bidi_datas
    ),
    hiddenimports=(
        [
            # PySide6
            "PySide6.QtCore",
            "PySide6.QtGui",
            "PySide6.QtWidgets",
            # qtawesome
            "qtawesome",
            "qtawesome.iconic_font",
            # EasyOCR & deps
            "easyocr",
            "easyocr.easyocr",
            "easyocr.utils",
            "easyocr.detection",
            "easyocr.recognition",
            "easyocr.model",
            "onnxruntime",
            "yaml",
            "six",
            "bidi",
            "bidi.algorithm",
            # Tesseract
            "pytesseract",
            # Image
            "PIL",
            "PIL.Image",
            "PIL.ImageDraw",
            "PIL.ImageFilter",
            "PIL.ImageEnhance",
            # Watchdog
            "watchdog",
            "watchdog.observers",
            "watchdog.events",
            # App modules
            "app",
            "app.ocr.engine",
            "app.ocr.processor",
            "app.database.manager",
            "app.database.models",
            "app.search.engine",
            "app.thumbnails.generator",
            "app.watcher.monitor",
            "app.indexer",
            "app.settings.manager",
            "app.ui.fonts",
            "app.ui.icons",
            "app.ui.styles",
            "app.ui.widgets",
            "app.ui.main_window",
            "app.ui.search_bar",
            "app.ui.sidebar",
            "app.ui.results_panel",
            "app.ui.preview_panel",
            "app.ui.settings_dialog",
        ]
        + torch_hiddenimports
        + torchvision_hiddenimports
        + easyocr_hiddenimports
        + cv2_hiddenimports
        + scipy_hiddenimports
        + skimage_hiddenimports
        + bidi_hiddenimports
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "pandas",
        "jupyter",
        "notebook",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ScreenSeek",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # UPX can corrupt torch / cv2 native DLLs — exclude them
        "torch_cpu.dll",
        "torch_cuda.dll",
        "cv2*.pyd",
        "*.pyd",
    ],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "logo" / "screenseek.ico"),
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        "torch_cpu.dll",
        "torch_cuda.dll",
        "cv2*.pyd",
        "*.pyd",
    ],
    name="ScreenSeek",
)
