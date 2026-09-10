"""One-off generator for app/assets/icon.ico and app/assets/splash.png.

Run manually with `python scripts\\generate_assets.py` whenever the icon or
splash design needs to change. The master icon design lives in
`app/assets/icon.svg` (hand-authored, matches the app's Fluent accent color)
and is rasterized here via Qt's own SVG renderer. Requires Pillow and PySide6
(both already dev/runtime dependencies of this project).
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

ACCENT = (124, 111, 240)  # #7C6FF0
ACCENT_LIGHT = (156, 144, 255)  # #9C90FF
GLOW_TEAL = (95, 214, 200)  # secondary aurora accent
BG_TOP = (10, 10, 18)
BG_BOTTOM = (18, 15, 28)
WHITE = (255, 255, 255)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "app" / "assets"
ICON_SVG = ASSETS_DIR / "icon.svg"


def _rasterize_svg(svg_path: Path, size: int) -> Image.Image:
    if QApplication.instance() is None:
        QApplication(sys.argv[:1])

    renderer = QSvgRenderer(str(svg_path))
    qimg = QImage(size, size, QImage.Format_RGBA8888)
    qimg.fill(0)
    painter = QPainter(qimg)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter)
    painter.end()

    buf = bytes(qimg.constBits())
    return Image.frombuffer("RGBA", (size, size), buf, "raw", "RGBA", 0, 1).copy()


def generate_icon() -> None:
    base = _rasterize_svg(ICON_SVG, 256)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    base.save(
        ASSETS_DIR / "icon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"wrote {ASSETS_DIR / 'icon.ico'}")


def _vertical_gradient(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    base = Image.new("RGB", (1, h), 0)
    for y in range(h):
        t = y / max(h - 1, 1)
        base.putpixel(
            (0, y),
            tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return base.resize((w, h))


def _glow_blob(w: int, h: int, cx: float, cy: float, rx: float, ry: float, color: tuple, blur: float) -> Image.Image:
    """A soft radial blob, drawn and blurred on a full-size canvas so the glow
    fades to black smoothly with no hard edges when screen-blended later."""
    layer = Image.new("RGB", (w, h), 0)
    draw = ImageDraw.Draw(layer)
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
    return layer.filter(ImageFilter.GaussianBlur(blur))


def _aurora_layer(w: int, h: int) -> Image.Image:
    """Soft blurred color blobs, screen-blended for a glowing 2026-style backdrop."""
    layer = Image.new("RGB", (w, h), 0)
    layer = ImageChops.screen(
        layer, _glow_blob(w, h, w * 0.22, h * 0.05, w * 0.34, h * 0.34, ACCENT, 65)
    )
    layer = ImageChops.screen(
        layer, _glow_blob(w, h, w * 0.82, h * 0.55, w * 0.32, h * 0.32, GLOW_TEAL, 75)
    )
    layer = ImageChops.screen(
        layer, _glow_blob(w, h, w * 0.05, h * 0.8, w * 0.28, h * 0.28, ACCENT_LIGHT, 70)
    )
    return layer


def _grain(w: int, h: int, opacity: int = 14) -> Image.Image:
    noise = Image.effect_noise((w, h), 28)
    alpha = Image.new("L", (w, h), opacity)
    grain = Image.merge("RGBA", (noise, noise, noise, alpha))
    return grain


def _glass_card(w: int, h: int, radius: int) -> Image.Image:
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius, fill=(255, 255, 255, 18)
    )
    draw.rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius, outline=(255, 255, 255, 40), width=1
    )
    return card


def _gradient_text(
    draw_size: tuple, text: str, font: ImageFont.FreeTypeFont, colors: tuple
) -> Image.Image:
    """Render text filled with a horizontal gradient, for a premium accent title."""
    w, h = draw_size
    mask = Image.new("L", (w, h), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.text((0, 0), text, font=font, fill=255)

    gradient = _vertical_gradient(w, h, colors[0], colors[1])
    # horizontal gradient: rotate a vertical one
    gradient = _vertical_gradient(h, w, colors[0], colors[1]).rotate(-90, expand=True)
    gradient = gradient.resize((w, h))

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(gradient, (0, 0), mask)
    return out


def generate_splash() -> None:
    w, h = 480, 300
    canvas = _vertical_gradient(w, h, BG_TOP, BG_BOTTOM)
    canvas = ImageChops.screen(canvas, _aurora_layer(w, h))
    canvas = canvas.convert("RGBA")

    grain = _grain(w, h)
    canvas = Image.alpha_composite(canvas, grain)

    # glass card behind the text block
    card_w, card_h = 360, 108
    card = _glass_card(card_w, card_h, radius=20)
    canvas.alpha_composite(card, ((w - card_w) // 2, 168))

    # icon badge with a soft accent glow behind it
    badge_size = 108
    glow = _glow_blob(w, h, w / 2, 28 + badge_size / 2, badge_size * 0.75, badge_size * 0.75, ACCENT, 26)
    canvas = ImageChops.screen(canvas.convert("RGB"), glow).convert("RGBA")

    badge = _rasterize_svg(ICON_SVG, badge_size)
    canvas.alpha_composite(badge, (w // 2 - badge_size // 2, 30))

    draw = ImageDraw.Draw(canvas)

    try:
        title_font = ImageFont.truetype("segoeuib.ttf", 26)
    except OSError:
        title_font = ImageFont.load_default()

    title = "Insta Music Downloader"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w, title_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    title_img = _gradient_text(
        (title_w + 4, title_h + 20), title, title_font, (WHITE, ACCENT_LIGHT)
    )
    canvas.alpha_composite(title_img, ((w - title_w) // 2 - 2, 190))

    try:
        small_font = ImageFont.truetype("segoeui.ttf", 13)
    except OSError:
        small_font = ImageFont.load_default()

    subtitle = "Загрузка..."
    bbox2 = draw.textbbox((0, 0), subtitle, font=small_font)
    subtitle_w = bbox2[2] - bbox2[0]
    draw.text(
        ((w - subtitle_w) / 2, 232), subtitle, fill=(168, 166, 190, 255), font=small_font
    )

    # static three-dot loader accent beneath the subtitle
    dot_r = 3
    dot_gap = 16
    dot_y = 256
    start_x = w / 2 - dot_gap
    for i in range(3):
        cx = start_x + i * dot_gap
        opacity = 255 if i == 1 else 130
        draw.ellipse(
            [cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r],
            fill=(*ACCENT_LIGHT, opacity),
        )

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(ASSETS_DIR / "splash.png")
    print(f"wrote {ASSETS_DIR / 'splash.png'}")


if __name__ == "__main__":
    generate_icon()
    generate_splash()
