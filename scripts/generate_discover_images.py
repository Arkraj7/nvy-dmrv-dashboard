"""Generate 1200x675 (16:9) category banners for Google Discover / Open Graph.

Run from the repository root:

    py scripts/generate_discover_images.py

The banners are derived from the in-repo park photograph so no external
licences or downloads are involved. Each category gets its own crop, colour
grade, icon and headline so a Discover card is visually tied to the listing.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "public" / "assets" / "images" / (
    "Men and women walking, having picnic and doing exercises in park.jpg"
)
OUT_DIR = ROOT / "public" / "assets" / "images" / "discover"

W, H = 1200, 675

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_SEMI = r"C:\Windows\Fonts\seguisb.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"

INK = (255, 255, 255)
MUTED = (214, 232, 224)
ACCENT = (110, 231, 183)
DEEP = (7, 38, 30)

# name -> (crop box on the 5000x5000 source, title lines, subtitle, icon)
CATEGORIES = {
    "forestry": (
        (0, 0, 5000, 2812),
        ["Forestry, Wildlife", "& Afforestation"],
        "Field, government and NGO roles across India",
        "tree",
    ),
    "esg": (
        (0, 760, 5000, 3572),
        ["ESG, Carbon Markets", "& Sustainability"],
        "Corporate climate, reporting and carbon roles",
        "bars",
    ),
    "research": (
        (0, 1420, 5000, 4232),
        ["Research, JRF, SRF", "& PhD Positions"],
        "Academic and project-staff openings",
        "lens",
    ),
    "gis": (
        (0, 2188, 5000, 5000),
        ["GIS, Remote Sensing", "& Earth Observation"],
        "Geospatial and satellite-data careers",
        "globe",
    ),
    "policy": (
        (420, 360, 4580, 2700),
        ["Climate Policy", "& Fellowships"],
        "Think-tanks, fellowships and leadership programs",
        "columns",
    ),
    "events": (
        (0, 980, 4100, 3286),
        ["Workshops, Events", "& Capacity Building"],
        "Trainings, summits, webinars and live meet-ups",
        "calendar",
    ),
    "default": (
        (0, 620, 5000, 3432),
        ["Verified Green Jobs", "in India"],
        "Forestry, climate, ESG and geospatial opportunities",
        "check",
    ),
}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def horizontal_gradient(width: int, height: int, left_a: int, right_a: int) -> Image.Image:
    grad = Image.new("L", (width, 1))
    px = grad.load()
    for x in range(width):
        t = x / max(width - 1, 1)
        px[x, 0] = int(left_a + (right_a - left_a) * t)
    return grad.resize((width, height))


def vertical_gradient(width: int, height: int, top_a: int, bottom_a: int) -> Image.Image:
    grad = Image.new("L", (1, height))
    px = grad.load()
    for y in range(height):
        t = y / max(height - 1, 1)
        px[0, y] = int(top_a + (bottom_a - top_a) * t)
    return grad.resize((width, height))


def draw_icon(draw: ImageDraw.ImageDraw, kind: str, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    c = ACCENT
    lw = max(4, w // 16)

    if kind == "tree":
        draw.polygon([(x0 + w * 0.5, y0 + h * 0.06), (x0 + w * 0.12, y0 + h * 0.58), (x0 + w * 0.88, y0 + h * 0.58)], fill=c)
        draw.polygon([(x0 + w * 0.5, y0 + h * 0.34), (x0 + w * 0.06, y0 + h * 0.9), (x0 + w * 0.94, y0 + h * 0.9)], fill=c)
        draw.rectangle([x0 + w * 0.42, y0 + h * 0.86, x0 + w * 0.58, y1], fill=c)
    elif kind == "bars":
        for i, frac in enumerate((0.42, 0.66, 0.9)):
            bx = x0 + w * (0.08 + i * 0.31)
            draw.rounded_rectangle([bx, y0 + h * (1 - frac), bx + w * 0.22, y1], radius=int(w * 0.05), fill=c)
    elif kind == "lens":
        draw.ellipse([x0 + w * 0.04, y0 + h * 0.04, x0 + w * 0.72, y0 + h * 0.72], outline=c, width=lw)
        draw.line([(x0 + w * 0.64, y0 + h * 0.64), (x0 + w * 0.96, y0 + h * 0.96)], fill=c, width=lw)
    elif kind == "globe":
        draw.ellipse([x0 + w * 0.04, y0 + h * 0.04, x0 + w * 0.96, y0 + h * 0.96], outline=c, width=lw)
        draw.ellipse([x0 + w * 0.28, y0 + h * 0.04, x0 + w * 0.72, y0 + h * 0.96], outline=c, width=max(3, lw // 2))
        draw.line([(x0 + w * 0.04, y0 + h * 0.5), (x0 + w * 0.96, y0 + h * 0.5)], fill=c, width=max(3, lw // 2))
    elif kind == "columns":
        draw.polygon([(x0 + w * 0.5, y0 + h * 0.02), (x0 + w * 0.02, y0 + h * 0.26), (x0 + w * 0.98, y0 + h * 0.26)], fill=c)
        for i in range(3):
            bx = x0 + w * (0.12 + i * 0.3)
            draw.rectangle([bx, y0 + h * 0.36, bx + w * 0.16, y0 + h * 0.82], fill=c)
        draw.rectangle([x0 + w * 0.04, y0 + h * 0.86, x0 + w * 0.96, y0 + h * 0.96], fill=c)
    elif kind == "calendar":
        draw.rounded_rectangle([x0 + w * 0.04, y0 + h * 0.12, x0 + w * 0.96, y0 + h * 0.96], radius=int(w * 0.1), outline=c, width=lw)
        draw.rectangle([x0 + w * 0.04, y0 + h * 0.12, x0 + w * 0.96, y0 + h * 0.3], fill=c)
        for r in range(2):
            for col in range(3):
                cx = x0 + w * (0.24 + col * 0.26)
                cy = y0 + h * (0.5 + r * 0.24)
                draw.ellipse([cx - w * 0.045, cy - h * 0.045, cx + w * 0.045, cy + h * 0.045], fill=c)
    else:  # check
        draw.ellipse([x0 + w * 0.04, y0 + h * 0.04, x0 + w * 0.96, y0 + h * 0.96], outline=c, width=lw)
        draw.line(
            [(x0 + w * 0.26, y0 + h * 0.52), (x0 + w * 0.44, y0 + h * 0.7), (x0 + w * 0.76, y0 + h * 0.32)],
            fill=c,
            width=lw,
            joint="curve",
        )


def build(name: str) -> Path:
    crop, lines, subtitle, icon = CATEGORIES[name]
    src = Image.open(SOURCE).convert("RGB").crop(crop).resize((W, H), Image.LANCZOS)
    src = src.filter(ImageFilter.GaussianBlur(1.2))

    # Cool green grade so all banners share a family look.
    tint = Image.new("RGB", (W, H), (18, 74, 58))
    src = Image.blend(src, tint, 0.16)

    canvas = src.convert("RGBA")
    dark = Image.new("RGBA", (W, H), DEEP + (0,))
    dark.putalpha(horizontal_gradient(W, H, 236, 46))
    canvas = Image.alpha_composite(canvas, dark)
    bottom = Image.new("RGBA", (W, H), (4, 22, 18, 0))
    bottom.putalpha(vertical_gradient(W, H, 0, 150))
    canvas = Image.alpha_composite(canvas, bottom)

    draw = ImageDraw.Draw(canvas)

    # Icon badge
    badge = (80, 86, 176, 182)
    draw.rounded_rectangle(badge, radius=24, fill=(9, 48, 38), outline=(110, 231, 183), width=2)
    draw_icon(draw, icon, (106, 112, 150, 156))

    # Kicker
    draw.text((200, 112), "URBAN FOREST PARK  ·  INDIA", font=font(FONT_SEMI, 24), fill=ACCENT)

    # Accent rule
    draw.rounded_rectangle([80, 216, 200, 222], radius=3, fill=ACCENT)

    # Headline
    title_font = font(FONT_BOLD, 66)
    y = 254
    for line in lines:
        draw.text((80, y), line, font=title_font, fill=INK)
        y += 82

    # Subtitle
    draw.text((80, 470), subtitle, font=font(FONT_REG, 27), fill=MUTED)

    # Domain
    domain_font = font(FONT_SEMI, 24)
    domain = "urbanforestpark.com"
    dw = draw.textlength(domain, font=domain_font)
    draw.text((W - 80 - dw, H - 82), domain, font=domain_font, fill=(235, 245, 240))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{name}.jpg"
    canvas.convert("RGB").save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return out


def main() -> None:
    for name in CATEGORIES:
        out = build(name)
        size_kb = os.path.getsize(out) / 1024
        print(f"{out.relative_to(ROOT)}  {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
