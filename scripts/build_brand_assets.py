#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the Urban Forest Park brand assets (favicons, PWA icons, logo).

Design language ("soothing red + cream tree"):
  * background: warm terracotta-coral red gradient #C9544D -> #B8433E
  * tree silhouette: crisp cream #FFFDF9 (stands out on light and dark tabs)

Outputs (all inside public/, deployed verbatim by the Astro build):
  favicon.svg                  rounded-square icon (vector)
  favicon-96x96.png            classic raster icon
  favicon.ico                  multi-size (16/32/48/64) ICO
  apple-touch-icon.png         180x180 full-bleed touch icon
  web-app-manifest-192x192.png PWA icon (any + maskable safe zone)
  web-app-manifest-512x512.png PWA icon
  assets/images/Logo_UFF.png   circular header emblem (transparent corners)

The tree artwork is read from public/assets/images/tree-svgrepo-com.svg so the
silhouette stays the canonical one used across the site.

Rendering uses the Playwright Chromium binary (headless screenshot) because
Chrome renders SVG gradients crisply at every size; no Python SVG rasteriser
is required. Re-runnable and idempotent.

    py scripts/build_brand_assets.py
"""
from __future__ import annotations

import argparse
import glob
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from PIL import Image

log = logging.getLogger("ufp-brand")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PUBLIC = REPO_ROOT / "public"

RED_A = "#C9544D"   # soothing terracotta-coral red
RED_B = "#B8433E"   # warm deeper tone for the gradient
CREAM = "#FFFDF9"   # tree artwork / inner glow

CHROME_CANDIDATES = [
    r"C:\Users\arkra\AppData\Local\ms-playwright\chromium-*\chrome-win64\chrome.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> Optional[str]:
    import os

    env = (os.environ.get("UFP_CHROME") or "").strip()
    if env and Path(env).exists():
        return env
    for pattern in CHROME_CANDIDATES:
        hits = sorted(glob.glob(pattern), reverse=True)
        if hits:
            return hits[0]
    return None


def tree_paths(public: Path) -> List[str]:
    """The tree silhouette path data (canopy + trunk) from the canonical SVG."""
    tree_svg = public / "assets" / "images" / "tree-svgrepo-com.svg"
    text = tree_svg.read_text(encoding="utf-8", errors="ignore")
    paths = re.findall(r'<path\s+d="([^"]+)"', text)
    if len(paths) < 2:
        raise SystemExit(f"Could not extract tree paths from {tree_svg}")
    return paths[:2]


def _tree_group(paths: List[str], box: float, inset_ratio: float) -> str:
    """Tree paths scaled/centred inside a ``box`` x ``box`` square."""
    side = box * (1.0 - inset_ratio)
    scale = side / 1024.0
    offset = (box - side) / 2.0
    body = "\n".join(
        f'      <path d="{d}" fill="{CREAM}"/>' for d in paths
    )
    return (
        f'    <g transform="translate({offset:.1f} {offset:.1f}) scale({scale:.6f})">\n'
        f"{body}\n    </g>"
    )


def favicon_svg(paths: List[str], rounded: bool, size: int = 750) -> str:
    """The primary icon: soothing red tile + cream tree silhouette."""
    rx = size * 0.2 if rounded else 0
    rect = (
        f'    <rect x="0" y="0" width="{size}" height="{size}" '
        f'rx="{rx:.0f}" ry="{rx:.0f}" fill="url(#ufpRed)"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">\n'
        f"  <defs>\n"
        f'    <linearGradient id="ufpRed" x1="0" y1="0" x2="1" y2="1">\n'
        f'      <stop offset="0" stop-color="{RED_A}"/>\n'
        f'      <stop offset="1" stop-color="{RED_B}"/>\n'
        f"    </linearGradient>\n"
        f"  </defs>\n"
        f"{rect}\n"
        f"{_tree_group(paths, size, 0.28)}\n"
        f"</svg>\n"
    )


def circle_logo_svg(paths: List[str], size: int = 512) -> str:
    """Circular header emblem: red disc + cream tree, transparent corners."""
    r = size / 2.0
    tree_side = size * 0.58
    scale = tree_side / 1024.0
    offset = (size - tree_side) / 2.0
    body = "\n".join(f'      <path d="{d}" fill="{CREAM}"/>' for d in paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">\n'
        f"  <defs>\n"
        f'    <linearGradient id="ufpRed" x1="0" y1="0" x2="1" y2="1">\n'
        f'      <stop offset="0" stop-color="{RED_A}"/>\n'
        f'      <stop offset="1" stop-color="{RED_B}"/>\n'
        f"    </linearGradient>\n"
        f"  </defs>\n"
        f'  <circle cx="{r:.0f}" cy="{r:.0f}" r="{r:.0f}" fill="url(#ufpRed)"/>\n'
        f'  <circle cx="{r:.0f}" cy="{r:.0f}" r="{r * 0.90:.1f}" fill="none" '
        f'stroke="{CREAM}" stroke-opacity="0.35" stroke-width="{size * 0.02:.1f}"/>\n'
        f'    <g transform="translate({offset:.1f} {offset:.1f}) scale({scale:.6f})">\n'
        f"{body}\n    </g>\n"
        f"</svg>\n"
    )


def render_png(
    browser: str,
    workdir: Path,
    svg_markup: str,
    pixel_size: int,
    out_path: Path,
    transparent: bool = True,
) -> None:
    """Rasterise an SVG to PNG at an exact size via a headless screenshot."""
    svg_file = workdir / f"asset_{pixel_size}_{out_path.stem}.svg"
    html_file = workdir / f"asset_{pixel_size}_{out_path.stem}.html"
    svg_file.write_text(svg_markup, encoding="utf-8")
    css = (
        "html,body{margin:0;padding:0;background:transparent;}"
        f"img{{display:block;width:{pixel_size}px;height:{pixel_size}px;}}"
    )
    html_file.write_text(
        '<!DOCTYPE html><html><head><meta charset="utf-8"><style>'
        + css
        + "</style></head><body>"
        + f'<img src="{svg_file.as_uri()}" alt="">'
        + "</body></html>",
        encoding="utf-8",
    )
    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--force-device-scale-factor=1",
        f"--window-size={pixel_size},{pixel_size}",
        f"--screenshot={out_path}",
    ]
    if transparent:
        cmd.insert(4, "--default-background-color=00000000")
    cmd.append(html_file.as_uri())
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if not out_path.exists():
        raise SystemExit(
            f"Headless render failed for {out_path.name}: "
            f"{result.stderr[-400:] if result.stderr else 'no output'}"
        )


def build_ico(png_512: Path, out_ico: Path) -> None:
    img = Image.open(png_512).convert("RGBA")
    img.save(
        out_ico,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate brand assets (favicons + logo).")
    parser.add_argument("--public", type=Path, default=DEFAULT_PUBLIC)
    return parser.parse_args(argv)


def derive_header_emblem(images: Path) -> bool:
    """Prefer the official uploaded emblem (repo-root assets/images/Logo_UFF.png).

    The uploaded master is a white, heavily padded lockup (tree emblem above
    the "URBAN FOREST / JOB POINT" wordmark). The circular 38px
    .ufp-header-logo needs the emblem itself, so this crops the tree mark
    above the wordmark, keeps it square and writes a 512x512
    public/assets/images/Logo_UFF.png. Returns True when used.
    """
    source = REPO_ROOT / "assets" / "images" / "Logo_UFF.png"
    if not source.exists():
        return False
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow is a soft dependency
        log.warning("Pillow is not installed; keeping the generated emblem")
        return False

    master = Image.open(source).convert("RGB")
    width, height = master.size
    # Exclude the wordmark band (bottom ~45% of the padded master).
    top_band = master.crop((0, 0, width, int(height * 0.55)))
    mask = top_band.convert("L").point(lambda value: 255 if value < 235 else 0)
    bbox = mask.getbbox()
    if not bbox:
        log.warning("Uploaded master has no emblem ink; keeping the generated emblem")
        return False

    left, upper, right, lower = bbox
    cx, cy = (left + right) / 2.0, (upper + lower) / 2.0
    half = max(right - left, lower - upper) * 1.06 / 2.0
    crop = (
        int(max(0, cx - half)),
        int(max(0, cy - half)),
        int(min(width, cx + half)),
        int(min(height, cy + half)),
    )
    emblem = master.crop(crop).resize((512, 512), Image.LANCZOS)
    out = images / "Logo_UFF.png"
    emblem.save(out, "PNG", optimize=True)
    try:
        shown = out.relative_to(REPO_ROOT)
    except ValueError:
        shown = out.name
    log.info("Derived header emblem from the uploaded master -> %s (512px)", shown)
    return True


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args(argv)
    public: Path = args.public.resolve()
    images = public / "assets" / "images"
    images.mkdir(parents=True, exist_ok=True)

    browser = find_browser()
    if not browser:
        log.error("No Chromium/Chrome binary found; set UFP_CHROME to a chrome.exe path")
        return 1
    log.info("Rendering with %s", browser)

    paths = tree_paths(public)
    rounded_svg = favicon_svg(paths, rounded=True)
    square_svg = favicon_svg(paths, rounded=False)
    logo_svg = circle_logo_svg(paths)

    (public / "favicon.svg").write_text(rounded_svg, encoding="utf-8")
    log.info("Wrote public/favicon.svg")

    workdir = Path(tempfile.mkdtemp(prefix="ufp_brand_"))
    upload_master = REPO_ROOT / "assets" / "images" / "Logo_UFF.png"
    try:
        targets = [
            (square_svg, 96, public / "favicon-96x96.png"),
            (square_svg, 180, public / "apple-touch-icon.png"),
            (square_svg, 192, public / "web-app-manifest-192x192.png"),
            (square_svg, 512, public / "web-app-manifest-512x512.png"),
            (rounded_svg, 512, workdir / "favicon-base-512.png"),
        ]
        if not upload_master.exists():
            targets.append((logo_svg, 512, images / "Logo_UFF.png"))
        for svg_markup, size, out_path in targets:
            render_png(browser, workdir, svg_markup, size, out_path)
            try:
                shown = out_path.relative_to(REPO_ROOT)
            except ValueError:
                shown = out_path.name
            log.info("Wrote %s (%dpx)", shown, size)

        if not derive_header_emblem(images):
            log.info("Using the generated circular emblem at public/assets/images/Logo_UFF.png")

        build_ico(workdir / "favicon-base-512.png", public / "favicon.ico")
        log.info("Wrote public/favicon.ico (16/32/48/64)")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    log.info("Brand assets rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
