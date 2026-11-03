#!/usr/bin/env python3
"""Generate per-category RSS feeds from the verified job registry.

Feeds
-----
- /feed.xml            (all active, already built by build_seo_pages)
- /feed-esg.xml        ESG, Carbon Markets & Corporate Sustainability
- /feed-forestry.xml   Forestry, Wildlife & Afforestation
- /feed-research.xml   Academic, JRF, SRF & PhD + Research Associate
- /feed-gis.xml        GIS, Remote Sensing & Earth Observation
- /feed-policy.xml     Climate Policy, Think-Tanks & Fellowships
- /feed-internships.xml Internships & Student Traineeships
- /feed-global.xml     Global listings
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from xml.sax.saxutils import escape

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

FEEDS = [
    ("esg", "ESG, Carbon Markets & Corporate Sustainability", "ESG, Carbon & Sustainability Jobs", "ESG, carbon markets and corporate sustainability jobs in India."),
    ("forestry", "Forestry, Wildlife & Afforestation", "Forestry & Wildlife Jobs", "Forestry, wildlife and afforestation jobs in India."),
    ("research", None, "Research & Academic Jobs", "JRF, SRF, PhD and research associate jobs in environment and climate."),
    ("gis", "GIS, Remote Sensing & Earth Observation", "GIS & Remote Sensing Jobs", "GIS, remote sensing and earth observation jobs in India."),
    ("policy", "Climate Policy, Think-Tanks & Fellowships", "Climate Policy & Think-Tank Jobs", "Climate policy, think-tank and fellowship jobs in India."),
    ("internships", "Internships & Student Traineeships", "Green Internships", "Green internships and entry-level environmental jobs in India."),
]


def load_jobs(path: Path) -> List[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []
    except Exception:
        return []


def rfc822(value: Any) -> str:
    text = str(value or "")[:10].strip()
    try:
        dt = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def build_feed(slug: str, category: str | None, title: str, desc: str, jobs: List[Dict[str, Any]]) -> str:
    items = []
    for job in jobs[:50]:
        jid = str(job.get("id") or "")
        jtitle = str(job.get("clean_title") or job.get("title") or "Untitled")
        org = str(job.get("organization") or "")
        city = str(job.get("city") or job.get("state") or "India")
        link = f"{SITE}/jobs/{jid}" if jid else SITE
        desc_text = str(job.get("role_summary") or job.get("summary") or desc)
        pub = rfc822(job.get("date_added") or job.get("date_posted"))
        items.append(f"""    <item>
      <title>{escape(jtitle)}</title>
      <link>{escape(link)}</link>
      <guid isPermaLink="true">{escape(link)}</guid>
      <description>{escape(desc_text[:500])}</description>
      <pubDate>{pub}</pubDate>
      <category>{escape(str(job.get("category") or ""))}</category>
      <author>{escape(org)} ({escape(city)})</author>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(title)} | Urban Forest Park</title>
    <link>{SITE}</link>
    <description>{escape(desc)}</description>
    <language>en-in</language>
    <lastBuildDate>{datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
    <atom:link href="{SITE}/feed-{slug}.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
"""


def main() -> None:
    india = beh.active(beh.load(beh.JOBS_PATH))
    global_jobs = beh.active(beh.load(beh.GLOBAL_PATH))

    for slug, category, title, desc in FEEDS:
        if category:
            filtered = [j for j in india if str(j.get("category") or "") == category]
        elif slug == "research":
            filtered = [j for j in india if str(j.get("category") or "") in ("Academic, JRF, SRF & PhD Positions", "Research Associate & Project Staff (Contractual)")]
        elif slug == "internships":
            filtered = [j for j in india if str(j.get("category") or "") == "Internships & Student Traineeships"]
        else:
            filtered = india
        (PUBLIC / f"feed-{slug}.xml").write_text(build_feed(slug, category, title, desc, filtered), encoding="utf-8")
        print(f"Wrote feed-{slug}.xml ({len(filtered)} items)")

    # Global feed
    (PUBLIC / "feed-global.xml").write_text(build_feed("global", None, "Global Climate & Sustainability Jobs", "Global climate, sustainability and green jobs.", global_jobs), encoding="utf-8")
    print(f"Wrote feed-global.xml ({len(global_jobs)} items)")


if __name__ == "__main__":
    main()
