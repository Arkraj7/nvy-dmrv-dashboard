#!/usr/bin/env python3
"""Build the five expansion hubs (Nov 2026).

1. /government-environment-jobs  - recruitment tracker for green public bodies
2. /green-internships            - internships and entry-level roles
3. /fellowship-deadlines         - deadline-sorted fellowships, grants, courses
4. /dmrv                         - institutional landing page for the dMRV tools
5. /green-careers                - career pathways and role intelligence

The pages reuse the registry design system (jobs.css + hub.css) and the shared
header/footer from build_seo_pages, so they stay visually consistent. Job lists
are generated from public/jobs.json and public/global_jobs.json; nothing is
hard-coded that the registry already knows.

Run after build_seo_pages.py:

    py scripts/build_expansion_hubs.py
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import build_seo_pages as bsp

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
JOBS_PATH = PUBLIC / "jobs.json"
GLOBAL_PATH = PUBLIC / "global_jobs.json"
SITEMAP = PUBLIC / "sitemap.xml"

SITE = bsp.SITE
TODAY = date.today()

HUB_CSS = (
    '<link rel="stylesheet" href="/styles/hub.css">\n'
    '    <link rel="stylesheet" href="/styles/expansion.css">\n'
    "    <script defer src=\"/js/toc2.js\"></script>"
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def esc(value: Any) -> str:
    return bsp.esc(value)


def plain(value: Any) -> str:
    return bsp.plain(value)


def load(path: Path) -> List[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return [record for record in data if isinstance(record, dict)]


def parse_date(value: Any) -> Optional[date]:
    text = str(value or "").strip()[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def active(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in records if str(r.get("status") or "active") == "active"]


def days_left(value: Any) -> Optional[int]:
    parsed = parse_date(value)
    if not parsed:
        return None
    return (parsed - TODAY).days


def deadline_label(job: Dict[str, Any]) -> str:
    left = days_left(job.get("valid_through"))
    raw = plain(job.get("deadline_or_window")) or "Rolling / Open"
    if left is None:
        return raw
    if left < 0:
        return raw
    if left == 0:
        return f"Closes today - {raw}"
    if left <= 14:
        return f"{raw} · {left} day{'s' if left != 1 else ''} left"
    return raw


def shell(
    *,
    title: str,
    description: str,
    canonical: str,
    body: str,
    jsonld: str,
    robots: str = "index, follow",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
    {bsp.GTM_SCRIPT}

    {bsp.GA_SCRIPT}

    {bsp.SWG_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{bsp.THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <meta name="robots" content="{robots}">
    <link rel="canonical" href="{canonical}">

    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park - India Career Registry">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{SITE}/assets/images/og-default.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(description)}">

    {jsonld}
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

{bsp.FAVICONS}

{bsp.FONTS}

    <link rel="stylesheet" href="/styles/jobs.css?v=20261104">
    {HUB_CSS}
    <style>
      .header-inner{{display:flex!important;flex-wrap:wrap!important;justify-content:center!important;align-items:flex-start!important;text-align:center;}}
      .brand{{flex-basis:100%!important;display:flex!important;align-items:center;justify-content:center;gap:10px;text-align:center;}}
      .site-nav{{flex:0 1 auto!important;justify-content:center!important;flex-wrap:wrap!important;max-width:calc(100% - 260px)!important;}}
      .header-actions{{margin-left:auto!important;justify-content:flex-end!important;align-self:flex-start!important;flex:0 0 auto!important;}}
    </style>
</head>
<body>
    {bsp.GTM_NOSCRIPT}
  <a class="skip-link" href="#main">Skip to content</a>

{bsp.header_html('registry')}

  <main id="main">
{body}
  </main>

{bsp.footer_html()}
</body>
</html>
"""


def hero(kicker: str, h1: str, sub: str, stats: List[tuple[str, str]]) -> str:
    stat_html = "\n".join(
        f"          <div><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>"
        for label, value in stats
    )
    return f"""    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">All opportunities</a><span aria-hidden="true">/</span><span>{esc(h1)}</span>
        </nav>
        <p class="eyebrow">{esc(kicker)}</p>
        <h1>{esc(h1)}</h1>
        <p class="hub-hero-sub">{esc(sub)}</p>
        <dl class="hub-stats">
{stat_html}
        </dl>
      </div>
    </section>"""


def cards(jobs: List[Dict[str, Any]]) -> str:
    if not jobs:
        return ('        <p class="hub-empty">No open listings in this section right now. '
                '<a href="/">Browse the full registry</a> - new roles are added daily.</p>')
    return "\n".join(bsp.hub_card_html(job) for job in jobs)


def section(title: str, intro: str, inner: str, anchor: str = "") -> str:
    anchor_attr = f' id="{anchor}"' if anchor else ""
    return f"""      <section class="hub-section"{anchor_attr}>
        <h2>{esc(title)}</h2>
        <p>{esc(intro)}</p>
{inner}
      </section>"""


def breadcrumb(name: str, url: str) -> str:
    return bsp.breadcrumb_jsonld(name, url)


def faq_jsonld(faqs: List[tuple[str, str]]) -> str:
    return bsp.faq_jsonld(faqs)


def write_page(name: str, html: str) -> None:
    (PUBLIC / f"{name}.html").write_text(html, encoding="utf-8")


# --------------------------------------------------------------------------
# 1. Government recruitment tracker
# --------------------------------------------------------------------------
BODIES = [
    {
        "name": "UPSC - Indian Forest Service (IFS)",
        "what": "Indian Forest Service selection through the Civil Services examination, plus other UPSC recruitments.",
        "cycle": "Annual UPSC cycle; check the exam calendar and notification on the portal.",
        "url": "https://upsc.gov.in",
        "host": "upsc.gov.in",
    },
    {
        "name": "MoEFCC - Ministry of Environment, Forest and Climate Change",
        "what": "Young Professionals, project staff and deputation posts across divisions, CAMPA and attached offices.",
        "cycle": "Notification-driven; vacancies are published on the recruitment page.",
        "url": "https://moef.gov.in/recruitment/update",
        "host": "moef.gov.in",
    },
    {
        "name": "CSIR - Council of Scientific and Industrial Research",
        "what": "Project Associate, JRF/SRF and Research Associate positions across CSIR laboratories.",
        "cycle": "Institute-wise walk-ins and advertised posts throughout the year.",
        "url": "https://www.csir.res.in",
        "host": "csir.res.in",
    },
    {
        "name": "ICAR - Indian Council of Agricultural Research",
        "what": "JRF/SRF, Young Professional and project staff roles at ICAR institutes and regional centres.",
        "cycle": "Institute-wise vacancies and walk-in interviews through the year.",
        "url": "https://icar.org.in/en/archive-vacancies",
        "host": "icar.org.in",
    },
    {
        "name": "Forest Survey of India (FSI)",
        "what": "Technical, project and mapping roles supporting national forest cover assessment.",
        "cycle": "Notification-driven; check the FSI recruitment section.",
        "url": "https://fsi.nic.in",
        "host": "fsi.nic.in",
    },
    {
        "name": "Wildlife Institute of India (WII)",
        "what": "Research posts, JRF/project staff and PG Diploma admissions in wildlife science.",
        "cycle": "Rolling vacancies plus annual academic admissions.",
        "url": "https://wii.gov.in",
        "host": "wii.gov.in",
    },
    {
        "name": "Central Pollution Control Board (CPCB)",
        "what": "Scientist, engineer and technical positions; state pollution control boards recruit separately.",
        "cycle": "Notification-driven; state boards publish their own cycles.",
        "url": "https://cpcb.nic.in",
        "host": "cpcb.nic.in",
    },
    {
        "name": "Madhya Pradesh Forest Department",
        "what": "Forest guard, ranger and field recruitment - representative of state forest department cycles.",
        "cycle": "State-specific; each state publishes its own notification and exam calendar.",
        "url": "https://www.mpforest.gov.in",
        "host": "mpforest.gov.in",
        "state_example": True,
    },
    {
        "name": "Odisha Forest Department",
        "what": "Forest guard, forester and field recruitment in Odisha.",
        "cycle": "State-specific; verify on the state portal.",
        "url": "https://forest.odisha.gov.in",
        "host": "forest.odisha.gov.in",
        "state_example": True,
    },
]


def government_rows() -> str:
    rows = []
    for body in BODIES:
        tag = "State example" if body.get("state_example") else "National"
        rows.append(
            f"""          <tr>
            <td><strong>{esc(body['name'])}</strong><br><span class="muted">{esc(tag)}</span></td>
            <td>{esc(body['what'])}</td>
            <td>{esc(body['cycle'])}</td>
            <td><a href="{esc(body['url'])}" target="_blank" rel="noopener noreferrer">Official portal &nearr;</a><br>
                <span class="muted">{esc(body['host'])}</span></td>
          </tr>"""
        )
    return f"""        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Recruiting body</th><th>What they recruit</th><th>Cycle</th><th>Official portal</th></tr></thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
          </table>
        </div>"""


PUBLIC_ORG_TOKENS = (
    "ministry of", "moef", "moefcc", "csir", "icar", "icfre", "forest survey",
    "wildlife institute", "cpcb", "pollution control", "forest department",
    "forest development", "campa", "zoological survey", "botanical survey",
    "indian council of forestry", "national tiger", "central zoo",
)


def match_government(job: Dict[str, Any]) -> bool:
    """Public-sector and forestry/wildlife pathway, not any mention of 'forest'.

    Matching on the words 'forest' or 'wildlife' anywhere in a summary pulled in
    ESG and consulting roles that merely mention deforestation, so the pathway
    filter is limited to the category and to recognisable public bodies.
    """

    org = str(job.get("organization") or "").lower()
    category = str(job.get("category") or "").lower()
    if "forestry" in category or "wildlife" in category:
        return True
    return any(token in org for token in PUBLIC_ORG_TOKENS)


def build_government(jobs: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]) -> None:
    live = [j for j in jobs if match_government(j)]
    live.sort(key=lambda j: str(j.get("valid_through") or "9999"))
    faqs = [
        ("Does Urban Forest Park conduct these recruitments?",
         "No. Urban Forest Park only tracks publicly advertised openings. Every application goes through the official portal linked on this page."),
        ("Why are some bodies missing a deadline?",
         "Several recruitments run on institute-wise or state-wise cycles. When no single notification is open, the tracker links to the portal where the next cycle appears."),
        ("Are walk-in interviews included?",
         "Yes. Walk-ins published by CSIR, ICAR and state departments are added to the registry with their venue and reporting time."),
    ]
    body = "\n".join(
        [
            hero(
                "Government & public-sector pathway",
                "Government Environment, Forestry & Wildlife Recruitment",
                "A tracker of the public bodies that recruit environmental scientists, foresters and wildlife researchers in India - with the official portal for each, plus live openings across the public, forestry and wildlife pathway.",
                [
                    ("Bodies tracked", str(len(BODIES))),
                    ("Live openings", str(len(live))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main" id="tracker">
      <div class="hub-main-inner">
        <h2>Recruitment tracker</h2>
        <p>Status is not guessed. Each row points to the official portal, because notification dates move every cycle.</p>
{government_rows()}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live forestry, wildlife and public-sector openings ({len(live)})</h2>
        <p>Public institutions and forestry/wildlife employers, pulled from the registry and sorted by closing date.</p>
        <div class="hub-list">
{cards(live)}
        </div>
      </div>
    </section>""",
            "<!-- EXAM_GUIDES_BLOCK -->",
            bsp.faq_section_html(faqs),
        ]
    )
    jsonld = "\n".join(
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            breadcrumb("Government Environment, Forestry & Wildlife Recruitment", SITE + "/government-environment-jobs"),
            faq_jsonld(faqs),
        ]
    )
    write_page(
        "government-environment-jobs",
        shell(
            title="Government Environment, Forestry & Wildlife Recruitment 2026",
            description=(
                "Track Indian Forest Service, MoEFCC, CSIR, ICAR, FSI, WII, CPCB and state forest "
                "department recruitment on the official portals, with live green openings from the registry."
            ),
            canonical=SITE + "/government-environment-jobs",
            body=body,
            jsonld=jsonld,
        ),
    )


# --------------------------------------------------------------------------
# 2. Internships and entry-level
# --------------------------------------------------------------------------
def is_internship(job: Dict[str, Any]) -> bool:
    """Word-boundary match so 'Internal Audit' is not read as an internship."""

    text = " ".join(
        str(job.get(key) or "")
        for key in ("category", "clean_title", "opportunity_kind", "position_type")
    ).lower()
    return bool(re.search(r"\b(intern|internship|internships|trainee|traineeship)\b", text))


NON_JOB_KINDS = {"Fellowship", "Scholarship", "Grant / Funding", "Competition / Award"}

# The registry files every record under one of these categories; anything else
# (workshops, conferences, grants, scholarships) is a programme, not a job.
JOB_CATEGORIES = {
    "Academic, JRF, SRF & PhD Positions",
    "Forestry, Wildlife & Afforestation",
    "ESG, Carbon Markets & Corporate Sustainability",
    "Research Associate & Project Staff (Contractual)",
    "GIS, Remote Sensing & Earth Observation",
    "Internships & Student Traineeships",
    "Climate Policy, Think-Tanks & Fellowships",
}


def is_entry(job: Dict[str, Any]) -> bool:
    if plain(job.get("opportunity_kind")) in NON_JOB_KINDS:
        return False
    if plain(job.get("category")) not in JOB_CATEGORIES:
        return False
    title = plain(job.get("clean_title")).lower()
    if re.search(r"\b(course|workshop|webinar|conclave|summit|training programme|bootcamp)\b", title):
        return False
    text = " ".join(
        str(job.get(key) or "")
        for key in ("experience_level", "clean_title")
    ).lower()
    return any(
        token in text
        for token in ("entry", "fresher", "graduate", "junior", "trainee", "assistant")
    )


def build_internships(jobs: List[Dict[str, Any]]) -> None:
    interns = [j for j in jobs if is_internship(j)]
    entry = [j for j in jobs if is_entry(j) and j not in interns]
    interns.sort(key=lambda j: str(j.get("valid_through") or "9999"))
    entry.sort(key=lambda j: str(j.get("valid_through") or "9999"))
    body = "\n".join(
        [
            hero(
                "Students & early careers",
                "Green Internships & Entry-Level Environmental Jobs",
                "Verified internships, traineeships and first-job roles in environment, forestry, GIS, ESG and climate - each linking to the official application page.",
                [
                    ("Internships", str(len(interns))),
                    ("Entry-level roles", str(len(entry))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Internships & traineeships ({len(interns)})</h2>
        <p>Short-term roles that build a portfolio. Deadlines are shown where the organiser publishes one.</p>
        <div class="hub-list">
{cards(interns)}
        </div>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Entry-level and junior roles ({len(entry)})</h2>
        <p>Assistant, associate and fresher-friendly positions across the registry.</p>
        <div class="hub-list">
{cards(entry[:40])}
        </div>
        <p><a href="/entry-level-environmental-jobs">See the full entry-level hub &rarr;</a></p>
      </div>
    </section>""",
            section(
                "How to apply with a thin CV",
                "Most early-career applications fail on evidence, not enthusiasm.",
                """        <ul class="check-list">
          <li><strong>One page, one direction.</strong> Lead with coursework, field work, tools and one concrete output per project.</li>
          <li><strong>Name your tools.</strong> QGIS, R, Python, Google Earth Engine, Excel, remote-sensing platforms - list what you can actually use.</li>
          <li><strong>Show a deliverable.</strong> A map, a report, a dataset or a field note is stronger than a claim of interest.</li>
          <li><strong>Match the notice.</strong> Mirror the qualification and experience wording from the official advertisement.</li>
          <li><strong>Check the mode.</strong> Walk-ins need documents and a reporting time; email applications need a single PDF.</li>
        </ul>""",
            ),
        ]
    )
    jsonld = "\n".join(
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            breadcrumb("Green Internships & Entry-Level Environmental Jobs", SITE + "/green-internships"),
        ]
    )
    write_page(
        "green-internships",
        shell(
            title="Green Internships & Entry-Level Environmental Jobs India 2026",
            description=(
                "Verified environmental internships, traineeships and entry-level green jobs in India - "
                "forestry, GIS, ESG, climate and research roles with official application links."
            ),
            canonical=SITE + "/green-internships",
            body=body,
            jsonld=jsonld,
        ),
    )


# --------------------------------------------------------------------------
# 3. Fellowship, grant and course deadlines
# --------------------------------------------------------------------------
FUNDING_CATEGORIES = {
    "Fellowships & Leadership Programs",
    "Scholarships & Doctoral Support",
    "Grants & Research Funding",
    "Workshops, Training & Capacity Building",
    "Competitions, Hackathons & Awards",
    "Ambassador & Fellowship Programs",
    "Conferences, Summits & Events",
    "Visiting Fellowships & Short-Term Research",
}


def is_funding(job: Dict[str, Any]) -> bool:
    kind = plain(job.get("opportunity_kind"))
    category = plain(job.get("category"))
    return (
        kind in {"Fellowship", "Scholarship", "Grant / Funding", "Competition / Award"}
        or category in FUNDING_CATEGORIES
    )


def build_fellowship_deadlines(jobs: List[Dict[str, Any]], global_jobs: List[Dict[str, Any]]) -> None:
    pool = active(jobs) + active(global_jobs)
    funding = [j for j in pool if is_funding(j)]

    dated: List[tuple[date, Dict[str, Any]]] = []
    rolling: List[Dict[str, Any]] = []
    for job in funding:
        parsed = parse_date(job.get("valid_through"))
        if parsed and parsed >= TODAY:
            dated.append((parsed, job))
        elif not parsed or parsed >= TODAY:
            rolling.append(job)
    dated.sort(key=lambda pair: pair[0])
    rolling.sort(key=lambda j: plain(j.get("clean_title")).lower())

    rows = []
    for parsed, job in dated[:120]:
        left = (parsed - TODAY).days
        urgent = " class=\"urgent\"" if left <= 14 else ""
        rows.append(
            f"""          <tr{urgent}>
            <td><time datetime="{parsed.isoformat()}">{parsed.strftime('%d %b %Y')}</time><br>
                <span class="muted">{left} day{'s' if left != 1 else ''} left</span></td>
            <td><a href="{bsp.job_url(job)}"><strong>{esc(plain(job.get('clean_title')))}</strong></a><br>
                <span class="muted">{esc(plain(job.get('organization')))}</span></td>
            <td>{esc(plain(job.get('category')))}</td>
            <td>{esc(plain(job.get('city')) or plain(job.get('country')))}</td>
          </tr>"""
        )
    table = f"""        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Deadline</th><th>Opportunity</th><th>Type</th><th>Location</th></tr></thead>
            <tbody>
{chr(10).join(rows) or '<tr><td colspan="4">No dated deadlines right now.</td></tr>'}
            </tbody>
          </table>
        </div>"""

    faqs = [
        ("What counts as rolling?",
         "Rolling or open calls accept applications until seats or funds are exhausted. They are listed separately because there is no single closing date to sort by."),
        ("Are these only fellowships?",
         "No. This calendar also carries scholarships, research grants, competitions, conferences and paid training courses, because they compete for the same early-career time."),
        ("How often is the calendar refreshed?",
         "It is regenerated from the registry on every build. Each opportunity links to the official page, which remains the final authority on the deadline."),
    ]
    body = "\n".join(
        [
            hero(
                "Funding & training calendar",
                "Fellowship, Scholarship & Grant Deadlines",
                "A single deadline calendar for fellowships, scholarships, grants, competitions and paid training in climate, environment and sustainability - sorted by what closes next.",
                [
                    ("Dated deadlines", str(len(dated))),
                    ("Funding tracked", str(len(funding))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Closing next</h2>
        <p>Ordered by closing date. Deadlines inside two weeks are marked.</p>
{table}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Rolling and open calls ({len(rolling)})</h2>
        <p>No fixed closing date - apply early, seats and funds are finite.</p>
        <div class="hub-list">
{cards(rolling[:30])}
        </div>
      </div>
    </section>""" if rolling else "",
            bsp.faq_section_html(faqs),
        ]
    )
    jsonld = "\n".join(
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            breadcrumb("Fellowship, Scholarship & Grant Deadlines", SITE + "/fellowship-deadlines"),
            faq_jsonld(faqs),
        ]
    )
    write_page(
        "fellowship-deadlines",
        shell(
            title="Fellowship, Scholarship & Grant Deadlines 2026-27",
            description=(
                "Climate and environment fellowship, scholarship, grant and training deadlines in one "
                "calendar, sorted by closing date, with official application links."
            ),
            canonical=SITE + "/fellowship-deadlines",
            body=body,
            jsonld=jsonld,
        ),
    )


# --------------------------------------------------------------------------
# 4. dMRV institutional landing page
# --------------------------------------------------------------------------
TOOLS = [
    {
        "name": "Nagar Van dMRV Dashboard",
        "href": "/dashboard",
        "copy": "Site-level monitoring view for urban forest plots: canopy, carbon, biodiversity and cooling indicators in one place.",
    },
    {
        "name": "Live site insights",
        "href": "/explore-dashboard",
        "copy": "Thematic maps, weather context and regional profiles for the Nagar Van sites tracked on the platform.",
    },
    {
        "name": "Urban Forest Green Calculator",
        "href": "/green-calculator",
        "copy": "Estimates carbon sequestration, biodiversity, cooling, air-quality and stormwater benefits for a site.",
    },
    {
        "name": "Nagar Van Finder",
        "href": "/nagar-van-finder",
        "copy": "Locates Nagar Van sites by state so field teams, students and researchers can find a site near them.",
    },
    {
        "name": "Spatial data explorer",
        "href": "/spatial-data",
        "copy": "Environmental impact profiles for 30 featured sites, covering climate, ecology, air quality and cooling.",
    },
    {
        "name": "Public survey",
        "href": "/public-survey",
        "copy": "Community feedback channel for the condition and use of urban forest sites.",
    },
]


def build_dmrv() -> None:
    tool_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="{tool['href']}">{esc(tool['name'])}</a></h3>
          <p class="hub-card-sum">{esc(tool['copy'])}</p>
          <p class="hub-card-foot"><a href="{tool['href']}">Open tool &rarr;</a></p>
        </article>"""
        for tool in TOOLS
    )
    faqs = [
        ("Who is this for?",
         "Urban local bodies, forest and horticulture departments, consultancies, CSR teams, researchers and students working on urban forest monitoring and reporting."),
        ("Is the calculator a substitute for field measurement?",
         "No. It produces first-pass estimates from site inputs so teams can compare options and plan monitoring. Field measurement and official protocols remain the reference."),
        ("Can a site be added?",
         "Use the public survey or the issue-report form to share a site or a correction. Each site profile is reviewed before it appears in the explorer."),
    ]
    body = "\n".join(
        [
            hero(
                "Institutional tools",
                "Nagar Van dMRV, Green Calculator & Urban Forest Data",
                "Monitoring, reporting and verification tooling for urban forests - built for the teams that plant, fund and inspect Nagar Van sites.",
                [
                    ("Tools", str(len(TOOLS))),
                    ("Featured sites", "30"),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>The toolkit</h2>
        <p>Each tool answers a different question in the urban forest cycle: where is the site, what does it deliver, and how is it changing.</p>
        <div class="hub-list">
{tool_cards}
        </div>
      </div>
    </section>""",
            section(
                "What dMRV means here",
                "Digital monitoring, reporting and verification for urban forests, not a certification scheme.",
                """        <ul class="check-list">
          <li><strong>Monitor:</strong> track site condition and benefit indicators over time instead of one-off plantation counts.</li>
          <li><strong>Report:</strong> turn field and spatial inputs into a consistent profile that can be shared with funders and reviewers.</li>
          <li><strong>Verify:</strong> keep the method visible - inputs, assumptions and calculations - so a third party can check the numbers.</li>
          <li><strong>Compare:</strong> use the same indicators across sites to prioritise where maintenance and investment go next.</li>
        </ul>""",
            ),
            section(
                "How the indicators are built",
                "The dashboard and calculator use transparent, documented inputs rather than opaque scores.",
                """        <ul class="check-list">
          <li>Site area, species mix and canopy cover feed the carbon and cooling estimates.</li>
          <li>Biodiversity and air-quality indicators are derived from site characteristics and published factors.</li>
          <li>Stormwater and ecosystem-benefit figures are estimates for planning, clearly separated from measured data.</li>
          <li>Every profile states what is estimated and what needs field verification.</li>
        </ul>""",
            ),
            bsp.faq_section_html(faqs),
        ]
    )
    jsonld = "\n".join(
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            breadcrumb("Nagar Van dMRV & Urban Forest Data", SITE + "/dmrv"),
            faq_jsonld(faqs),
        ]
    )
    write_page(
        "dmrv",
        shell(
            title="Nagar Van dMRV, Green Calculator & Urban Forest Data",
            description=(
                "Digital monitoring, reporting and verification for Nagar Van urban forests: site dashboards, "
                "green calculator, spatial data and community survey tools."
            ),
            canonical=SITE + "/dmrv",
            body=body,
            jsonld=jsonld,
        ),
    )


# --------------------------------------------------------------------------
# 5. Career pathways
# --------------------------------------------------------------------------
def build_careers(jobs: List[Dict[str, Any]]) -> None:
    paths = [
        {
            "name": "Research & academia",
            "href": "/jrf-srf-project-associate-jobs",
            "copy": "JRF/SRF and project associate roles are the standard entry point, followed by PhD registration and research associate posts.",
            "match": lambda j: "JRF" in plain(j.get("category")) or "Academic" in plain(j.get("category")),
        },
        {
            "name": "Forestry & wildlife",
            "href": "/forestry-wildlife-government-jobs",
            "copy": "Field and government pathways: forest guard and ranger recruitment, wildlife biology, conservation and CAMPA-funded posts.",
            "match": lambda j: "Forestry" in plain(j.get("category")) or "Wildlife" in plain(j.get("category")),
        },
        {
            "name": "ESG, carbon & sustainability",
            "href": "/esg-carbon-sustainability-jobs",
            "copy": "Corporate and consulting route: BRSR and ESG reporting, carbon accounting, climate risk and assurance.",
            "match": lambda j: "ESG" in plain(j.get("category")),
        },
        {
            "name": "GIS & remote sensing",
            "href": "/gis-remote-sensing-climate-jobs",
            "copy": "Spatial analyst to earth-observation specialist, across ISRO centres, institutes and consultancies.",
            "match": lambda j: "GIS" in plain(j.get("category")),
        },
        {
            "name": "Climate policy & think tanks",
            "href": "/sustainability-jobs-india",
            "copy": "Research, programme and policy roles in think tanks, multilaterals and climate finance.",
            "match": lambda j: "Climate Policy" in plain(j.get("category")),
        },
        {
            "name": "Internships & entry level",
            "href": "/green-internships",
            "copy": "Short-term and first-job roles that build a portfolio before a specialist track.",
            "match": lambda j: is_internship(j) or is_entry(j),
        },
    ]
    active_jobs = active(jobs)
    cards_html = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="{path['href']}">{esc(path['name'])}</a></h3>
          <p class="hub-card-sum">{esc(path['copy'])}</p>
          <p class="hub-card-foot"><span>{sum(1 for j in active_jobs if path['match'](j))} open now</span>
            <a href="{path['href']}">Explore &rarr;</a></p>
        </article>"""
        for path in paths
    )
    faqs = [
        ("Where do salaries come from?",
         "The salary guide aggregates bands from live and recently listed roles. It is indicative, not an offer, and is regenerated as the registry changes."),
        ("Do I need a master's degree?",
         "For JRF and research posts, usually yes. Field, GIS operations and internship routes often accept a bachelor's degree or a strong portfolio."),
        ("Which pathway grows fastest?",
         "ESG and climate-risk roles currently dominate the registry. GIS is the thinnest supply relative to demand, which usually means less competition per opening."),
    ]
    body = "\n".join(
        [
            hero(
                "Career intelligence",
                "Green Careers in India: Pathways, Roles & Pay",
                "How the green economy actually hires - the entry points, the transitions and the pay bands behind the listings.",
                [
                    ("Pathways", str(len(paths))),
                    ("Active roles", str(len(active_jobs))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a pathway</h2>
        <p>Each route has its own entry credential, hiring cycle and ceiling.</p>
        <div class="hub-list">
{cards_html}
        </div>
      </div>
    </section>""",
            "<!-- ROLE_PROFILES_BLOCK -->",
            section(
                "How the routes connect",
                "Most green careers are built in two moves, not one.",
                """        <ul class="check-list">
          <li><strong>Research route:</strong> JRF/SRF &rarr; PhD registration &rarr; research associate &rarr; scientist or faculty.</li>
          <li><strong>Corporate route:</strong> analyst or intern &rarr; ESG/carbon associate &rarr; manager &rarr; head of sustainability.</li>
          <li><strong>Geospatial route:</strong> GIS executive &rarr; analyst &rarr; remote-sensing specialist &rarr; earth-observation lead.</li>
          <li><strong>Public route:</strong> forest guard or field assistant &rarr; ranger/RFO &rarr; state forest service &rarr; IFS.</li>
        </ul>""",
            ),
            section(
                "Pay and progression",
                "Use the salary guide for bands, and the notice for the actual offer.",
                """        <p>The <a href="/salary-guide">salary guide</a> aggregates bands by role, city and experience from verified listings.
        Government posts follow pay-matrix rules, contractual research posts follow funding norms, and corporate roles vary most by city and firm.</p>
        <p><a class="btn btn-primary" href="/salary-guide">Open the salary guide &rarr;</a></p>""",
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Career comparisons</h2>
        <p>Side-by-side answers to the choices green-job seekers actually face.</p>
        <ul class="check-list">
          <li><a href="/compare/jrf-vs-srf-fellowship">JRF vs SRF</a> &mdash; fellowship stages and stipend.</li>
          <li><a href="/compare/forest-guard-vs-ranger">Forest guard vs ranger</a> &mdash; qualification and pay basis.</li>
          <li><a href="/compare/esg-vs-csr">ESG vs CSR</a> &mdash; regulation and jobs.</li>
          <li><a href="/compare/ifs-vs-ias">IFS vs IAS</a> &mdash; same exam, different service.</li>
          <li><a href="/compare/gis-vs-remote-sensing">GIS vs remote sensing</a> &mdash; tools and roles.</li>
          <li><a href="/compare/internship-vs-fellowship">Internship vs fellowship</a> &mdash; early career.</li>
        </ul>
        <p style="margin-top:16px;"><a class="btn btn-primary" href="/compare">Open all comparisons &rarr;</a></p>
      </div>
    </section>""",
            bsp.faq_section_html(faqs),
        ]
    )
    jsonld = "\n".join(
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            breadcrumb("Green Careers in India: Pathways, Roles & Pay", SITE + "/green-careers"),
            faq_jsonld(faqs),
        ]
    )
    write_page(
        "green-careers",
        shell(
            title="Green Careers in India 2026: Pathways, Roles & Salary Guide",
            description=(
                "Green career pathways in India - research, forestry, ESG, GIS, climate policy and internships - "
                "with live role counts, progression routes and a salary guide."
            ),
            canonical=SITE + "/green-careers",
            body=body,
            jsonld=jsonld,
        ),
    )


# --------------------------------------------------------------------------
# sitemap
# --------------------------------------------------------------------------
def update_sitemap(paths: List[str]) -> int:
    text = SITEMAP.read_text(encoding="utf-8")
    added = 0
    for path in paths:
        loc = SITE + path
        if f"<loc>{loc}</loc>" in text:
            continue
        entry = (
            f"  <url><loc>{loc}</loc><lastmod>{TODAY.isoformat()}</lastmod>"
            "<changefreq>daily</changefreq><priority>0.9</priority></url>"
        )
        text = text.replace("</urlset>", entry + "\n</urlset>")
        added += 1
    if added:
        SITEMAP.write_text(text, encoding="utf-8")
    return added


def main() -> None:
    jobs = active(load(JOBS_PATH))
    global_jobs = active(load(GLOBAL_PATH))

    build_government(jobs, global_jobs)
    build_internships(jobs)
    build_fellowship_deadlines(jobs, global_jobs)
    build_dmrv()
    build_careers(jobs)
    added = update_sitemap(
        [
            "/government-environment-jobs",
            "/green-internships",
            "/fellowship-deadlines",
            "/dmrv",
            "/green-careers",
        ]
    )
    print(f"Wrote 5 expansion hubs; sitemap +{added}")


if __name__ == "__main__":
    main()
