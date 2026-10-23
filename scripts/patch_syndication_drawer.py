#!/usr/bin/env python3
"""Inject the internal Syndication Desk script into every public HTML page.

The drawer (public/js/syndication-drawer.js) is intentionally loaded on every
surface - index, hubs, regional portals, legal pages, dashboards and the
secret /admin-syndication route - so the operator can summon it anywhere via
Ctrl+Shift+U, #syndication, ?syndication=1 or the subtle footer link.

Idempotent: files that already reference /js/syndication-drawer.js are skipped.

Usage:
    py scripts/patch_syndication_drawer.py
"""
from __future__ import annotations

import pathlib
import sys

TAG = '<script defer src="/js/syndication-drawer.js?v=20261023-1"></script>'
MARKER = "/js/syndication-drawer.js"

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def patch_file(path: pathlib.Path) -> str:
    """Return 'updated', 'skipped' or 'no-body'."""
    text = path.read_text(encoding="utf-8")
    if MARKER in text:
        return "skipped"
    idx = text.rfind("</body>")
    if idx == -1:
        return "no-body"

    # Preserve the existing indentation of the closing body tag.
    line_start = text.rfind("\n", 0, idx) + 1
    indent = text[line_start:idx]
    indent = indent if indent.strip() == "" else ""

    insertion = f"{indent}{TAG}\n"
    text = text[:line_start] + insertion + text[line_start:]
    path.write_text(text, encoding="utf-8")
    return "updated"


def main() -> int:
    counts = {"updated": 0, "skipped": 0, "no-body": 0}
    for path in sorted(PUBLIC.rglob("*.html")):
        result = patch_file(path)
        counts[result] += 1
        if result == "updated":
            print(f"updated  {path.relative_to(ROOT)}")
        elif result == "no-body":
            print(f"NO BODY  {path.relative_to(ROOT)}")

    print(
        f"\nSyndication drawer script: {counts['updated']} updated, "
        f"{counts['skipped']} already present, {counts['no-body']} without </body>."
    )
    return 0 if counts["no-body"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
