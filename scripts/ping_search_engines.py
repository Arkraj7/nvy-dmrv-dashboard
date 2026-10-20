#!/usr/bin/env python3
"""Submit the public sitemap URLs to IndexNow (Bing / DuckDuckGo partners).

The key file lives in the web root and is served as
``https://www.urbanforestpark.com/<key>.txt``. IndexNow rejects submissions
when that file is missing or does not contain the exact key, so the script
checks the local copy first.

Usage:
    py scripts/ping_search_engines.py --dry-run
    py scripts/ping_search_engines.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List

import requests

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = "https://www.urbanforestpark.com"
KEY = "a9f3c2d7e8b14f60a2c5e9d3b7f14c68"
KEY_FILE = PUBLIC / (KEY + ".txt")
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls() -> List[str]:
    path = PUBLIC / "sitemap.xml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    urls = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", text)
    cleaned: List[str] = []
    for url in urls:
        url = url.replace("&amp;", "&").strip()
        if url.startswith(SITE) and url not in cleaned:
            cleaned.append(url)
    for extra in (
        SITE + "/",
        SITE + "/sitemap.xml",
        SITE + "/feed.xml",
        SITE + "/jrf-feed.xml",
        SITE + "/" + KEY + ".txt",
    ):
        if extra not in cleaned:
            cleaned.append(extra)
    return cleaned


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ping IndexNow with current URLs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args(argv)

    if not KEY_FILE.exists() or KEY_FILE.read_text(encoding="utf-8").strip() != KEY:
        print("IndexNow key file is missing or has the wrong content:", KEY_FILE)
        return 2
    urls = sitemap_urls()[: max(1, args.limit)]
    if not urls:
        print("No sitemap URLs found; run scripts/build_seo_pages.py first.")
        return 2

    payload = {
        "host": "www.urbanforestpark.com",
        "key": KEY,
        "keyLocation": SITE + "/" + KEY + ".txt",
        "urlList": urls,
    }
    print(f"IndexNow: {len(urls)} URL(s), key file OK")
    if args.dry_run:
        print(json.dumps(payload, indent=2)[:1200])
        return 0
    try:
        response = requests.post(ENDPOINT, json=payload, timeout=30)
        print(
            "IndexNow response: HTTP",
            response.status_code,
            (response.text or "")[:400],
        )
        return 0 if response.status_code in (200, 202) else 1
    except Exception as exc:
        print("IndexNow request failed:", str(exc)[:300])
        return 1


if __name__ == "__main__":
    sys.exit(main())
