"""Inject the floating "Back to top" control script into every HTML page under
public/ that does not already reference it.

The control itself lives in public/js/back-to-top.js (self-initialising: it
injects its own markup and styles), so each page only needs the deferred
script tag.  The generated SEO hubs / Hindi portals emit the tag from
scripts/build_seo_pages.py and scripts/seo_portals.py; this script keeps the
hand-maintained pages (index, legal pages, dashboards, tool pages) in sync.

Idempotent: pages that already reference /js/back-to-top.js are skipped;
pages without a </body> close are reported and left untouched.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("patch_back_to_top")

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC = REPO_ROOT / "public"

TAG = '<script defer src="/js/back-to-top.js"></script>'


def patch(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    if "/js/back-to-top.js" in html:
        return "skipped (already present)"
    idx = html.rfind("</body>")
    if idx == -1:
        return "SKIPPED (no </body>) - left untouched"
    path.write_text(html[:idx] + "  " + TAG + "\n" + html[idx:], encoding="utf-8")
    return "patched"


def main() -> int:
    pages = sorted(PUBLIC.glob("*.html"))
    if not pages:
        log.error("No HTML pages found in %s", PUBLIC)
        return 1
    for page in pages:
        log.info("%s: %s", page.name, patch(page))
    return 0


if __name__ == "__main__":
    sys.exit(main())
