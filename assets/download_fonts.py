"""
One-time helper — downloads Poppins font variants from Google Fonts (GitHub).
Run before first launch or before building: python assets/download_fonts.py
"""
import urllib.request
from pathlib import Path

FONTS_DIR = Path(__file__).parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

VARIANTS = [
    "Poppins-Regular.ttf",
    "Poppins-Medium.ttf",
    "Poppins-SemiBold.ttf",
    "Poppins-Bold.ttf",
]
BASE = "https://github.com/google/fonts/raw/main/ofl/poppins/"

print(f"Target: {FONTS_DIR}\n")
for name in VARIANTS:
    dest = FONTS_DIR / name
    if dest.exists():
        print(f"  skip   {name}")
        continue
    print(f"  fetch  {name} ... ", end="", flush=True)
    try:
        urllib.request.urlretrieve(BASE + name, dest)
        print("ok")
    except Exception as exc:
        print(f"FAILED ({exc})")

print("\nDone. Run the app or build with PyInstaller.")
