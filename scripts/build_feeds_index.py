#!/usr/bin/env python3
"""Build a small RSS feeds index page."""

from __future__ import annotations

from pathlib import Path

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
hero = beh.hero
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local

FEEDS = [
    ("All active jobs", "/feed.xml", "Every verified listing, updated daily."),
    ("ESG & carbon", "/feed-esg.xml", "ESG, carbon markets and corporate sustainability jobs."),
    ("Forestry & wildlife", "/feed-forestry.xml", "Forestry, wildlife and afforestation jobs."),
    ("Research & academic", "/feed-research.xml", "JRF, SRF, PhD and research associate jobs."),
    ("GIS & remote sensing", "/feed-gis.xml", "GIS, remote sensing and earth observation jobs."),
    ("Climate policy", "/feed-policy.xml", "Climate policy, think-tank and fellowship jobs."),
    ("Internships", "/feed-internships.xml", "Green internships and entry-level jobs."),
    ("Global", "/feed-global.xml", "Global climate and sustainability jobs."),
    ("JRF feed", "/jrf-feed.xml", "JRF and fellowship listings only."),
]


def main() -> None:
    feed_links = "\n".join(
        f'        <li><a href="{href}">{esc(name)}</a> &mdash; <span class="muted">{esc(desc)}</span></li>'
        for name, href, desc in FEEDS
    )
    body = "\n".join([
        hero("RSS feeds", "Green Jobs RSS Feeds", "Subscribe to verified green job listings by category. Paste any feed URL into your RSS reader, Slack, or college TPO dashboard.", [("Feeds", str(len(FEEDS))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Available feeds</h2>
        <p>Each feed is regenerated on every build and contains the latest verified listings with official application links.</p>
        <ul class="check-list">
{feed_links}
        </ul>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("How do I use these feeds?", "Paste the feed URL into any RSS reader (Feedly, Inoreader, etc.) or use it in a Slack/Teams channel."),
            ("How often are they updated?", "On every build, which runs daily in the pipeline."),
            ("Can I filter by city?", "Not yet. Use the city hubs for city-specific listings."),
        ]),
    ])
    write_sub(PUBLIC, "feeds", shell(
        title="Green Jobs RSS Feeds: ESG, Forestry, GIS & More",
        description="Subscribe to verified green job listings by category: ESG, forestry, research, GIS, climate policy, internships and global.",
        canonical=f"{SITE}/feeds",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("RSS Feeds", f"{SITE}/feeds")]),
    ))
    beh.update_sitemap(["/feeds"])
    print("Wrote /feeds index")


if __name__ == "__main__":
    main()
