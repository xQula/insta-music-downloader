"""One-off generator for app/assets/icon.ico and app/assets/splash.png.

Run manually with `python scripts\\generate_assets.py` whenever the icon design
needs to change. Requires Pillow (dev-only, not a runtime dependency of the app).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ACCENT = (124, 111, 240)  # #7C6FF0
DARK_BG = (26, 26, 36)  # near-black, matches Fluent dark theme background
WHITE = (255, 255, 255)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "assets"


def _rounded_square(size: int, radius_ratio: float = 0.22) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    radius = int(size * radius_ratio)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=ACCENT)
    return img


def _draw_glyph(img: Image.Image) -> None:
    """Download arrow into a music note head, in white, centered."""
    size = img.width
    draw = ImageDraw.Draw(img)
    cx = size / 2
    stem_w = size * 0.10

    # Arrow shaft
    top = size * 0.22
    bottom = size * 0.58
    draw.rounded_rectangle(
        [cx - stem_w / 2, top, cx + stem_w / 2, bottom],
        radius=stem_w / 2,
        fill=WHITE,
    )
    # Arrow head
    head_w = size * 0.34
    head_top = bottom - size * 0.04
    head_bottom = bottom + size * 0.16
    draw.polygon(
        [
            (cx - head_w / 2, head_top),
            (cx + head_w / 2, head_top),
            (cx, head_bottom),
        ],
        fill=WHITE,
    )
    # Note head (small filled circle, bottom-right accent) representing music
    note_r = size * 0.09
    note_cx = cx + size * 0.20
    note_cy = size * 0.78
    draw.ellipse(
        [note_cx - note_r, note_cy - note_r, note_cx + note_r, note_cy + note_r],
        fill=WHITE,
    )


def generate_icon() -> None:
    base = _rounded_square(256)
    _draw_glyph(base)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    base.save(
        ASSETS_DIR / "icon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"wrote {ASSETS_DIR / 'icon.ico'}")


def generate_splash() -> None:
    w, h = 420, 260
    img = Image.new("RGB", (w, h), DARK_BG)
    draw = ImageDraw.Draw(img)

    badge = _rounded_square(96)
    _draw_glyph(badge)
    img.paste(badge, (w // 2 - 48, 40), badge)

    try:
        font = ImageFont.truetype("segoeuib.ttf", 22)
    except OSError:
        font = ImageFont.load_default()

    text = "Insta Music Downloader"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((w - text_w) / 2, 160), text, fill=WHITE, font=font)

    try:
        small_font = ImageFont.truetype("segoeui.ttf", 13)
    except OSError:
        small_font = ImageFont.load_default()
    loading = "Загрузка..."
    bbox2 = draw.textbbox((0, 0), loading, font=small_font)
    loading_w = bbox2[2] - bbox2[0]
    draw.text(((w - loading_w) / 2, 200), loading, fill=(180, 180, 196), font=small_font)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    img.save(ASSETS_DIR / "splash.png")
    print(f"wrote {ASSETS_DIR / 'splash.png'}")


if __name__ == "__main__":
    generate_icon()
    generate_splash()
