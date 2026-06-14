"""
Asset generator — creates the ScreenSeek logo, icon, and placeholder screenshots.
Run once: python assets/generate_assets.py
Requires Pillow.
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is required: pip install Pillow")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BG      = (26,  26,  46)    # #1a1a2e — dark navy
ACCENT  = (233, 69,  96)    # #e94560 — crimson red
NAVY    = (15,  52,  96)    # #0f3460
WHITE   = (224, 224, 224)


def draw_logo(size: int = 512) -> Image.Image:
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    pad = size // 10
    draw.ellipse([pad, pad, size - pad, size - pad], fill=BG)

    # Magnifying glass handle
    cx, cy = size // 2, size // 2 - size // 16
    r = size // 4
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=ACCENT,
        width=max(4, size // 32),
    )

    # "Screen" inside the glass — a tiny screenshot grid
    inner_r = r - size // 18
    ix, iy = cx - inner_r, cy - inner_r
    draw.rectangle(
        [ix, iy, cx + inner_r, cy + inner_r],
        fill=NAVY,
    )
    # Simulated screen lines
    line_color = WHITE
    lw = max(1, size // 128)
    for row in range(3):
        y = iy + (inner_r * 2 // 4) * (row + 1) - lw
        x_start = ix + size // 48
        x_end   = cx + inner_r - size // 48
        draw.rectangle([x_start, y, x_end, y + lw * 2], fill=line_color)

    # Handle
    angle = math.radians(45)
    hx1 = int(cx + r * 0.7 * math.cos(angle))
    hy1 = int(cy + r * 0.7 * math.sin(angle))
    hx2 = int(cx + r * 1.45 * math.cos(angle))
    hy2 = int(cy + r * 1.45 * math.sin(angle))
    handle_width = max(4, size // 26)
    draw.line([hx1, hy1, hx2, hy2], fill=ACCENT, width=handle_width)

    return img


def save_logo_variants(logo: Image.Image) -> None:
    logo_dir = ROOT / "logo"
    logo_dir.mkdir(parents=True, exist_ok=True)

    for sz in (512, 256, 128, 64, 32):
        resized = logo.resize((sz, sz), Image.LANCZOS)
        resized.save(logo_dir / f"logo_{sz}.png")
        print(f"  Saved logo_{sz}.png")

    # ICO for Windows
    ico_path = logo_dir / "screenseek.ico"
    logo.save(
        ico_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    print(f"  Saved screenseek.ico")

    # Also copy to assets root for buildbox
    logo.save(ROOT / "logo.png")
    print("  Saved assets/logo.png")


def make_screenshot_placeholder(name: str, label: str, size=(1280, 800)) -> None:
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)

    # Header bar
    draw.rectangle([0, 0, size[0], 56], fill=NAVY)
    # "Search bar"
    draw.rounded_rectangle([60, 10, size[0] - 60, 46], radius=8, fill=(22, 33, 62))

    # Fake result cards
    card_w, card_h = 180, 200
    cols = 5
    for i in range(10):
        col = i % cols
        row = i // cols
        x = 40 + col * (card_w + 16)
        y = 80 + row * (card_h + 16)
        draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=8, fill=NAVY)
        # Thumbnail placeholder
        draw.rectangle([x + 8, y + 8, x + card_w - 8, y + card_h - 50], fill=(15, 52, 96))
        # Text lines
        for li in range(2):
            draw.rectangle(
                [x + 8, y + card_h - 40 + li * 16, x + card_w - 8, y + card_h - 28 + li * 16],
                fill=(40, 60, 100),
            )

    shots_dir = ROOT / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)
    path = shots_dir / f"{name}.png"
    img.save(path)
    print(f"  Saved {path.name}")


if __name__ == "__main__":
    print("Generating ScreenSeek assets…")
    logo = draw_logo(512)
    save_logo_variants(logo)

    make_screenshot_placeholder("01_search_results",    "Search Results")
    make_screenshot_placeholder("02_preview",           "Preview Panel")
    make_screenshot_placeholder("03_settings",          "Settings Dialog")
    make_screenshot_placeholder("04_index_manager",     "Index Manager")
    make_screenshot_placeholder("05_empty_state",       "Empty State")

    print("\nAll assets generated successfully.")
