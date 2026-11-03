#!/usr/bin/env python3
"""Build a career counselor toolkit page for TPOs and career counselors."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
hero = beh.hero
section = beh.section
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local


def main() -> None:
    body = "\n".join([
        hero("Career counselor toolkit", "Resources for Career Counselors & TPOs", "Tools, feeds and guides for placement officers, career counselors and academic advisors helping students enter green careers.", [("Updated", TODAY.strftime("%d %b %Y"))]),
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>RSS feeds for your dashboard</h2>
        <p>Subscribe to verified green job listings by category. Paste any feed URL into your TPO dashboard, Slack channel or college website.</p>
        <ul class="check-list">
          <li><a href="/feed.xml">All green jobs (RSS)</a> &mdash; every verified listing.</li>
          <li><a href="/feed-esg.xml">ESG & carbon jobs</a></li>
          <li><a href="/feed-forestry.xml">Forestry & wildlife jobs</a></li>
          <li><a href="/feed-research.xml">Research & academic jobs (JRF/SRF/PhD)</a></li>
          <li><a href="/feed-gis.xml">GIS & remote sensing jobs</a></li>
          <li><a href="/feed-policy.xml">Climate policy & think-tank jobs</a></li>
          <li><a href="/feed-internships.xml">Green internships</a></li>
          <li><a href="/feed-global.xml">Global climate & sustainability jobs</a></li>
          <li><a href="/jrf-feed.xml">JRF feed only</a></li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Search and filter</h2>
        <p>The <a href="/search">search page</a> lets students filter 220+ verified jobs by role, city, category, skill and experience level. Share the URL with filters pre-set: <code>/search?q=GIS&city=Bengaluru</code></p>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Guides for students</h2>
        <ul class="check-list">
          <li><a href="/guides/how-to-enter-esg-career">How to enter an ESG career</a></li>
          <li><a href="/guides/how-to-apply-for-jrf">How to apply for JRF</a></li>
          <li><a href="/guides/how-to-prepare-forest-guard-exam">Forest guard exam preparation</a></li>
          <li><a href="/guides/esg-interview-questions">ESG interview questions</a></li>
          <li><a href="/guides/jrf-interview-prep">JRF interview preparation</a></li>
          <li><a href="/guides/it-to-sustainability-career">IT to sustainability transition</a></li>
          <li><a href="/guides/engineering-to-esg-career">Engineering to ESG transition</a></li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Resume templates</h2>
        <ul class="check-list">
          <li><a href="/guides/esg-analyst-resume-template">ESG analyst resume template</a></li>
          <li><a href="/guides/jrf-cv-format">JRF CV format</a></li>
          <li><a href="/guides/forest-guard-application-format">Forest guard application format</a></li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Exam and eligibility guides</h2>
        <ul class="check-list">
          <li><a href="/exams">All exam guides</a></li>
          <li><a href="/exams/indian-forest-service">Indian Forest Service (IFS)</a></li>
          <li><a href="/exams/forest-guard">Forest guard</a></li>
          <li><a href="/exams/csir-jrf">CSIR JRF</a></li>
          <li><a href="/exams/ugc-net-environmental-science">UGC-NET Environmental Science</a></li>
          <li><a href="/exams/icar-jrf-srf">ICAR JRF/SRF</a></li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Salary data</h2>
        <p>Download the full salary dataset as CSV: <a href="/data/green-jobs-salary.csv" download>green-jobs-salary.csv</a> (235 rows). Use it for career counselling, placement reports and student guidance.</p>
        <p><a href="/salary-guide">Open the salary guide &rarr;</a></p>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Is this free for colleges?", "Yes. All content, feeds and data on Urban Forest Park are free."),
            ("Can I embed the job board on my college website?", "Yes. Use the RSS feeds or the search URL with filters. Contact us for custom integration."),
            ("How often is the data updated?", "The registry refreshes daily. Feeds and search update on every build."),
        ]),
    ])
    write_sub(PUBLIC, "counselor-toolkit", shell(
        title="Career Counselor Toolkit: Green Jobs Resources for TPOs",
        description="RSS feeds, search tools, guides, resume templates and salary data for career counselors and placement officers.",
        canonical=f"{SITE}/counselor-toolkit",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("Career Counselor Toolkit", f"{SITE}/counselor-toolkit")]),
    ))
    beh.update_sitemap(["/counselor-toolkit"])
    print("Wrote counselor toolkit")


if __name__ == "__main__":
    main()
