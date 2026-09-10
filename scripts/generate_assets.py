"""One-off generator for app/assets/icon.ico and app/assets/splash.png.

Run manually with `python scripts\\generate_assets.py` whenever the icon or
splash design needs to change. The master icon design lives in
`app/assets/icon.svg` (hand-authored, matches the app's Fluent accent color)
and is rasterized here via Qt's own SVG renderer. Requires Pillow and PySide6
(both already dev/runtime dependencies of this project).
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter
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
        [0, 0, w - 1, h - 1], radius=radius, fill=(255, 255, 255, 26)
    )
    draw.rounded_rectangle(
        [0, 0, w - 1, h - 1], radius=radius, outline=(255, 255, 255, 60), width=1
    )
    return card


def generate_splash_background() -> None:
    """Background art only (aurora glow + grain + glass card) — the icon badge,
    title, subtitle and loading spinner are drawn live by app/splash.py so the
    splash window can actually animate and scale crisply on any DPI."""
    w, h = 480, 300
    canvas = _vertical_gradient(w, h, BG_TOP, BG_BOTTOM)
    canvas = ImageChops.screen(canvas, _aurora_layer(w, h))
    canvas = canvas.convert("RGBA")

    grain = _grain(w, h)
    canvas = Image.alpha_composite(canvas, grain)

    # glass card behind the text block — larger radius and stronger presence
    # than the first draft, so it reads as a deliberate rounded panel.
    card_w, card_h = 380, 150
    card = _glass_card(card_w, card_h, radius=28)
    canvas.alpha_composite(card, ((w - card_w) // 2, 128))

    # soft accent glow behind where the icon badge will sit
    glow = _glow_blob(w, h, w / 2, 88, 70, 70, ACCENT, 26)
    canvas = ImageChops.screen(canvas.convert("RGB"), glow).convert("RGBA")

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    canvas.save(ASSETS_DIR / "splash_bg.png")
    print(f"wrote {ASSETS_DIR / 'splash_bg.png'}")


if __name__ == "__main__":
    generate_icon()
    generate_splash_background()
