#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the static SEO surface for the Urban Forest Park career registry.

Two outputs, both regenerated after every pipeline run (see the GitHub
Actions workflow and scripts/fetch_and_humanize.py):

1. A pre-rendered registry snapshot injected into ``public/index.html``
   between the ``<!-- SEO_DIRECTORY_START -->`` / ``<!-- SEO_DIRECTORY_END -->``
   markers: crawlable links to every active and recently archived mandate
   and keyword-dense structured copy. The homepage's executive FAQ block and
   its FAQPage JSON-LD are maintained by hand in index.html, outside the
   markers, so this script never rewrites or duplicates them.

2. Five career-pathway hub pages (listed in ``SEO_HUB_PAGES`` inside
   ``fetch_and_humanize.py`` and emitted into the sitemap at priority 0.9),
   each pre-rendering its matching mandates with unique title / description /
   canonical and CollectionPage + ItemList + FAQPage JSON-LD.

The script is read-only with respect to the pipeline data: it never rewrites
jobs.json / archive.json / sitemap.xml. Run it *after* the pipeline so the
snapshot reflects the latest registry state:

    py scripts/build_seo_pages.py
"""
from __future__ import annotations

import argparse
import html
import json
import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Shared constants and normalisation helpers are imported from the pipeline
# module so the two never drift apart (categories, slugs, position types).
# --------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_and_humanize as fh  # noqa: E402

log = logging.getLogger("ufp-seo")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PUBLIC = REPO_ROOT / "public"

SITE = "https://www.urbanforestpark.com"
LOGO_URL = SITE + "/assets/images/Logo_UFF.png"
LOGO_PATH = "assets/images/Logo_UFF.png"
BRAND_ALT = "Urban Forest Park — India Climate, Forestry, ESG & Research Jobs Registry Logo"
BRAND_ALT_HTML = html.escape(BRAND_ALT, quote=True)
BRAND_TITLE = "Urban Forest Park Official Emblem"

# Bump when an immutable /assets image changes so existing edge and browser
# caches fetch the new bytes (the URL is the cache key).
ASSET_VERSION = "20261019"


def pretty_url(url: str) -> str:
    """Return the URL form Cloudflare Pages serves with HTTP 200.

    The host normalises ``/about.html`` to ``/about`` with a 308, so every
    canonical, sitemap entry and internal link must use the pretty form to
    keep the crawl path redirect-free.
    """
    if not url:
        return url
    if url.startswith(("mailto:", "tel:", "javascript:", "data:", "#", "//")):
        return url

    prefix = ""
    rest = url
    if url.startswith(SITE + "/"):
        prefix, rest = SITE, url[len(SITE):]
    elif url.startswith("/"):
        prefix, rest = "", url
    else:
        # Relative page links such as "explore-dashboard.html#map-section".
        if ".html" not in url.split("#", 1)[0].split("?", 1)[0]:
            return url
        rest = "/" + url

    path, has_fragment, fragment = rest.partition("#")
    page, has_query, query = path.partition("?")
    if not page.endswith(".html"):
        return url
    page = "/" if page == "/index.html" else page[:-5]
    rebuilt = prefix + page
    if has_query:
        rebuilt += "?" + query
    if has_fragment:
        rebuilt += "#" + fragment
    return rebuilt


_ATTR_URL_RE = re.compile(
    r"(\b(?:href|content|item|url)=)(?:\"([^\"]+)\"|'([^']+)')", re.I
)
_JSON_URL_RE = re.compile(r'("(?:url|item|@id|image)"\s*:\s*")([^"]+)(")', re.I)


def prettify_internal_urls(text: str) -> str:
    """Rewrite same-site .html URLs to their extensionless canonical form."""

    def attr_repl(match: re.Match[str]) -> str:
        quote = '"' if match.group(2) is not None else "'"
        value = match.group(2) if match.group(2) is not None else match.group(3)
        return f"{match.group(1)}{quote}{pretty_url(value)}{quote}"

    def json_repl(match: re.Match[str]) -> str:
        return match.group(1) + pretty_url(match.group(2)) + match.group(3)

    text = _ATTR_URL_RE.sub(attr_repl, text)
    return _JSON_URL_RE.sub(json_repl, text)
IST = timezone(timedelta(hours=5, minutes=30))

KEYWORD_MAP_PATH = REPO_ROOT / "scripts" / "seo_keyword_map.json"
PUBLIC_KEYWORD_MAP = DEFAULT_PUBLIC / "seo_keyword_map.json"

SNAPSHOT_START = "<!-- SEO_DIRECTORY_START -->"
SNAPSHOT_END = "<!-- SEO_DIRECTORY_END -->"

RECENT_ARCHIVE_DAYS = 180     # archived mandates shown on the index snapshot
HUB_ARCHIVE_LIMIT = 6         # archived mandates per hub page
ITEM_LIST_CAP = 60            # ItemList entries per hub page

GA_SCRIPT = """    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-4E7BLPFWP7"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-4E7BLPFWP7');
    </script>"""

THEME_BOOTSTRAP = """    <!-- Theme bootstrap: applied before stylesheets to prevent flicker. -->
    <script>
      (function () {
        try {
          var t = localStorage.getItem('ufp_theme');
          if (t !== 'dark' && t !== 'light') {
            t = (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
          }
          document.documentElement.setAttribute('data-theme', t);
        } catch (e) { /* default rendering: light */ }
      })();
    </script>"""

FAVICONS = """    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
    <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="shortcut icon" href="/favicon.ico" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    <meta name="apple-mobile-web-app-title" content="UrbanPark" />
    <link rel="manifest" href="/manifest.json" />"""

FONTS = """    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&family=Spectral:wght@500;600;700&display=swap">"""

PIN_SVG = ('<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
           'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
           '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 1116 0z"/><circle cx="12" cy="10" r="2.6"/></svg>')


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def plain(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def trim(value: Any, limit: int) -> str:
    text = plain(value)
    if len(text) <= limit:
        return text
    cut = text[: limit + 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:") + "\u2026"


def load_keyword_map(path: Path = KEYWORD_MAP_PATH) -> Dict[str, Dict[str, Any]]:
    """Load the single source of truth for page titles, descriptions and H1s."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"ERROR: could not read keyword map {path}: {exc}") from exc
    pages = payload.get("pages") if isinstance(payload, dict) else payload
    if not isinstance(pages, list):
        raise SystemExit(f"ERROR: {path} must contain a 'pages' array")
    result: Dict[str, Dict[str, Any]] = {}
    for entry in pages:
        if not isinstance(entry, dict):
            continue
        file_name = str(entry.get("file") or "").strip()
        if not file_name:
            raise SystemExit(f"ERROR: keyword-map entry without a file name in {path}")
        result[file_name] = entry
    if not result:
        raise SystemExit(f"ERROR: keyword map {path} is empty")
    return result


def validate_keyword_map(pages: Dict[str, Dict[str, Any]]) -> None:
    titles: Dict[str, str] = {}
    descriptions: Dict[str, str] = {}
    primaries: Dict[str, str] = {}
    for file_name, entry in pages.items():
        title = plain(entry.get("title"))
        desc = plain(entry.get("description"))
        primary = plain(entry.get("primary_keyword"))
        if not (55 <= len(title) <= 60):
            raise SystemExit(f"ERROR: {file_name} title is {len(title)} chars (expected 55-60)")
        if not (155 <= len(desc) <= 160):
            raise SystemExit(f"ERROR: {file_name} description is {len(desc)} chars (expected 155-160)")
        if title in titles:
            raise SystemExit(f"ERROR: duplicate title for {file_name} and {titles[title]}")
        if desc in descriptions:
            raise SystemExit(f"ERROR: duplicate description for {file_name} and {descriptions[desc]}")
        if primary in primaries:
            raise SystemExit(f"ERROR: duplicate primary keyword for {file_name} and {primaries[primary]}")
        titles[title] = file_name
        descriptions[desc] = file_name
        primaries[primary] = file_name


KEYWORD_MAP: Dict[str, Dict[str, Any]] = load_keyword_map()
validate_keyword_map(KEYWORD_MAP)


def page_meta(file_name: str) -> Dict[str, Any]:
    try:
        return KEYWORD_MAP[file_name]
    except KeyError as exc:
        raise SystemExit(f"ERROR: missing keyword-map entry for {file_name}") from exc


def ist_today() -> date:
    return datetime.now(IST).date()


def long_date(value: date) -> str:
    return value.strftime("%d %B %Y")


def cat_class(category: Any) -> str:
    return {
        "Academic, JRF, SRF & PhD Positions": "cat-academic",
        "Research Associate & Project Staff (Contractual)": "cat-research",
        "Forestry, Wildlife & Afforestation": "cat-forestry",
        "GIS, Remote Sensing & Earth Observation": "cat-gis",
        "ESG, Carbon Markets & Corporate Sustainability": "cat-esg",
        "Climate Policy, Think-Tanks & Fellowships": "cat-policy",
    }.get(str(category or ""), "cat-policy")


def position_type_of(job: Dict[str, Any]) -> str:
    pt = plain(job.get("position_type"))
    if pt in fh.POSITION_TYPES:
        return pt
    return fh.infer_position_type(plain(job.get("clean_title")), str(job.get("category") or ""))


def track_of(job: Dict[str, Any]) -> str:
    """Exactly one career track per record (mirrors jobs.js trackOf())."""
    pt = position_type_of(job)
    cat = str(job.get("category") or "")
    if pt in ("JRF / SRF", "Project Associate / Research Associate", "Faculty / Academic"):
        return "research"
    if pt == "PhD / Doctoral Fellowship":
        return "phd"
    if pt == "Young Professional / Consultant (Contractual)":
        return "contractual"
    if cat == "Climate Policy, Think-Tanks & Fellowships" or pt == "Fellowship / Internship":
        return "thinktank"
    return "corporate"


def state_label(job: Dict[str, Any]) -> str:
    state = plain(job.get("state"))
    return state or "India"


def searchable_text(job: Dict[str, Any]) -> str:
    return " ".join(
        [
            plain(job.get("clean_title")),
            plain(job.get("organization")),
            plain(job.get("qualification_summary")),
            " ".join(job.get("must_have_skills") or []),
        ]
    )


def jsonld_script(payload: Any) -> str:
    body = json.dumps(payload, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + body + "\n</script>"


def organization_jsonld() -> str:
    """Institutional publisher identity, reused by every indexable surface."""
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": SITE + "/#organization",
            "name": "Urban Forest Park",
            "url": SITE + "/",
            "logo": {
                "@type": "ImageObject",
                "url": LOGO_URL,
                "width": 512,
                "height": 512,
            },
            "email": "urbanforestpark@gmail.com",
            "contactPoint": [
                {
                    "@type": "ContactPoint",
                    "contactType": "editorial support",
                    "email": "urbanforestpark@gmail.com",
                    "availableLanguage": ["en", "hi"],
                    "areaServed": "IN",
                }
            ],
            "description": (
                "National Climate, Forestry, ESG and Geospatial Career Registry (India), "
                "and home of the Nagar Van dMRV Dashboard and Green Calculator."
            ),
            "areaServed": ["IN", "Global"],
            "sameAs": [
                "https://t.me/urbanforestpark",
                "https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw",
            ],
        }
    )


def website_jsonld() -> str:
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": SITE + "/#website",
            "name": "Urban Forest Park — National Climate, Forestry, ESG & Geospatial Career Registry (India)",
            "url": SITE + "/",
            "inLanguage": "en-IN",
            "publisher": {"@id": SITE + "/#organization"},
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": SITE + "/?q={search_term_string}",
                },
                "query-input": "required name=search_term_string",
            },
        }
    )


def breadcrumb_jsonld(name: str, url: str) -> str:
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Career Registry", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": name, "item": url},
            ],
        }
    )


SITE_MATRIX_LINKS: List[Tuple[str, str]] = [
    ("India Climate, Forestry, ESG & Academic Job Registry", "/"),
    ("Global Climate Jobs, Grants & Fellowships", "/global-climate-sustainability-opportunities.html"),
    ("JRF, SRF & Project Associate Environmental Science Jobs", "/jrf-srf-project-associate-jobs.html"),
    ("PhD Fellowships & Postdoctoral Positions in Climate", "/phd-fellowships-climate-sustainability.html"),
    ("Forestry, Wildlife, ICFRE, WII & MoEFCC Jobs", "/forestry-wildlife-government-jobs.html"),
    ("GIS, Remote Sensing & Earth Observation Jobs", "/gis-remote-sensing-climate-jobs.html"),
    ("ESG, BRSR, Carbon Credits & Sustainability Jobs", "/esg-carbon-sustainability-jobs.html"),
    ("Hindi Environment, Forestry & Climate Jobs Portal", "/hindi-environment-forestry-jobs.html"),
    ("State-Wise Environmental & Research Jobs in India", "/bharat-regional-green-jobs.html"),
    ("Nagar Van Yojana dMRV Dashboard & Green Calculator", "/dashboard.html"),
    ("Live Nagar Van dMRV Site Insights Dashboard", "/explore-dashboard.html"),
    ("Urban Forest Green Calculator", "/green-calculator.html"),
    ("Green Calculator Web App", "/green-calculator-app.html"),
    ("Green Calculator Environmental Impact Report", "/green-calculator-report.html"),
    ("Find Nagar Van Sites Near You", "/nagar-van-finder.html"),
    ("Nagar Van Spatial Data Explorer", "/spatial-data.html"),
    ("Nagar Van Public Survey", "/public-survey.html"),
    ("About Urban Forest Park & Editorial Governance", "/about.html"),
    ("Privacy Policy", "/privacy.html"),
    ("Terms of Use", "/terms.html"),
    ("Cookie Policy", "/cookies.html"),
    ("Accessibility Statement", "/accessibility.html"),
    ("Mandate Dispatch Archive", "/newsletter_latest.html"),
    ("Dispatch Subscription Preferences", "/unsubscribe.html"),
    ("Report an Issue", "/report.html"),
]

# Contextual state gateways keep every major state within two clicks of the
# homepage and give crawlers a path to the live ?state= filtered views.
TOP_STATE_LINKS: List[Tuple[str, str]] = [
    ("Uttar Pradesh", "/?state=Uttar%20Pradesh"),
    ("Maharashtra", "/?state=Maharashtra"),
    ("Delhi NCR", "/?state=Delhi%20NCR"),
    ("Karnataka", "/?state=Karnataka"),
    ("Tamil Nadu", "/?state=Tamil%20Nadu"),
    ("Madhya Pradesh", "/?state=Madhya%20Pradesh"),
    ("Rajasthan", "/?state=Rajasthan"),
    ("Gujarat", "/?state=Gujarat"),
    ("Telangana", "/?state=Telangana"),
    ("Uttarakhand", "/?state=Uttarakhand"),
    ("West Bengal", "/?state=West%20Bengal"),
    ("Bihar", "/?state=Bihar"),
    ("Kerala", "/?state=Kerala"),
    ("Punjab", "/?state=Punjab"),
    ("Odisha", "/?state=Odisha"),
    ("Assam", "/?state=Assam"),
]


def site_matrix_html(current_path: str = "", include_states: bool = True) -> str:
    """The unified crawlable hub matrix used by the homepage and every hub."""
    items = []
    for label, href in SITE_MATRIX_LINKS:
        if href == current_path:
            items.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
        else:
            items.append(f'<li><a href="{href}">{esc(label)}</a></li>')
    state_items = "".join(
        f'<li><a href="{href}">{esc(label)} state jobs</a></li>' for label, href in TOP_STATE_LINKS
    )
    state_block = ""
    if include_states:
        state_block = f"""      <p class="site-matrix-sub" style="margin:18px 0 6px;font-weight:700;">Browse live state gateways</p>
      <ul class="site-matrix-list">
        {state_items}
      </ul>"""
    return f"""  <section class="site-matrix" aria-labelledby="site-matrix-title">
    <div class="site-matrix-inner">
      <p class="eyebrow">National &amp; Global Career Pathways</p>
      <h2 id="site-matrix-title">National &amp; Global Career Pathways &amp; Research Hubs</h2>
      <p class="site-matrix-sub">Every career pathway, language portal, institutional research tool, governance page and statutory policy in one crawlable directory.</p>
      <ul class="site-matrix-list">
        {''.join(items)}
      </ul>
{state_block}
    </div>
  </section>"""


def compact_site_matrix_html(current_path: str = "") -> str:
    """Footer-level fallback for legacy static pages outside the hub generator."""
    items = []
    for label, href in SITE_MATRIX_LINKS:
        if href == current_path:
            items.append(f'<li><span aria-current="page">{esc(label)}</span></li>')
        else:
            items.append(f'<li><a href="{href}">{esc(label)}</a></li>')
    state_items = "".join(
        f'<li><a href="{href}">{esc(label)} state jobs</a></li>' for label, href in TOP_STATE_LINKS
    )
    return f"""<nav class="ufp-site-matrix" aria-labelledby="ufp-site-matrix-title" style="max-width:1240px;margin:0 auto;padding:22px 18px 28px;font-family:Inter,system-ui,sans-serif;color:#334155;border-top:1px solid #E2E8F0;background:#F8FAFC;">
  <h2 id="ufp-site-matrix-title" style="font-size:15px;margin:0 0 10px;color:#0F172A;">National &amp; Global Career Pathways &amp; Research Hubs</h2>
  <ul style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:6px 20px;list-style:none;padding:0;margin:0;font-size:12.5px;line-height:1.55;">
    {''.join(items)}
  </ul>
  <p style="font-size:13px;font-weight:700;margin:16px 0 6px;">Browse live state gateways</p>
  <ul style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:6px 20px;list-style:none;padding:0;margin:0;font-size:12.5px;line-height:1.55;">
    {state_items}
  </ul>
  <p style="font-size:12px;line-height:1.6;margin:16px 0 0;color:#475569;">Cite this registry:
    <a href="/about.html#cite">citation &amp; embed widget</a> &middot;
    <a href="https://t.me/urbanforestpark" rel="noopener">Telegram</a> &middot;
    <a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a>
  </p>
</nav>"""


FAQS_PAGE_RE = re.compile(r"\n{3,}")


# --------------------------------------------------------------------------
# Hub definitions
# --------------------------------------------------------------------------
FORESTRY_RE = re.compile(
    r"forest|wildlife|afforest|conservation|biodiversity|tiger|elephant|"
    r"ecology|habitat|sanctuary|national park|moefcc|icfre|wii\b",
    re.I,
)
GIS_RE = re.compile(
    r"\bgis\b|geographic information|remote sensing|geospatial|earth observation|"
    r"satellite|urban heat|spatial|land use|land cover|earth engine|"
    r"photogrammetr|cartograph|geoinformatic",
    re.I,
)


def match_research(job: Dict[str, Any]) -> bool:
    return track_of(job) == "research"


def match_phd(job: Dict[str, Any]) -> bool:
    return track_of(job) == "phd"


def match_forestry(job: Dict[str, Any]) -> bool:
    if job.get("category") == "Forestry, Wildlife & Afforestation":
        return True
    if position_type_of(job) == "Full-Time Corporate / NGO":
        return False
    return bool(FORESTRY_RE.search(searchable_text(job)))


def match_gis(job: Dict[str, Any]) -> bool:
    if job.get("category") == "GIS, Remote Sensing & Earth Observation":
        return True
    return bool(GIS_RE.search(searchable_text(job)))


def match_esg(job: Dict[str, Any]) -> bool:
    return job.get("category") == "ESG, Carbon Markets & Corporate Sustainability"


HUBS: List[Dict[str, Any]] = [
    {
        "file": "jrf-srf-project-associate-jobs.html",
        "match": match_research,
        "kicker": "Academic & Research Track",
        "title": "JRF, SRF & Project Associate Jobs in India | Urban Forest Park",
        "h1": "JRF / SRF & Project Associate Jobs in India",
        "desc": (
            "Verified Junior Research Fellow (JRF), Senior Research Fellow (SRF), Research "
            "Associate and Project Associate vacancies across Indian universities, IITs, IISc, "
            "CSIR institutes and government research bodies \u2014 updated daily with direct "
            "application links."
        ),
        "hero_sub": (
            "Every JRF, SRF, research associate and project associate mandate currently tracked "
            "by the Urban Forest Park registry \u2014 sourced from official university, institute "
            "and government portals across India."
        ),
        "list_copy": (
            "Junior Research Fellow (JRF), Senior Research Fellow (SRF), Research Associate and "
            "Project Associate positions in environmental science, forestry, ecology, climate "
            "change, sustainability, agriculture and allied disciplines. Each listing links "
            "straight to the official advertisement and application portal."
        ),
        "cta_href": "/?track=research",
        "matched_noun": "research fellowship and project-staff",
        "faqs": [
            (
                "Which organisations advertise JRF and SRF positions in India?",
                "JRF and SRF positions in environment, forestry, ecology and climate disciplines "
                "are advertised by Central, State and Agricultural universities, IITs, IISc, CSIR "
                "and ICAR laboratories, ICFRE institutes, the Wildlife Institute of India, IIFM, "
                "ATREE and project-mode research programmes funded by DST, DBT, MoEFCC and "
                "similar agencies.",
            ),
            (
                "What is the eligibility for JRF and SRF roles?",
                "A JRF typically requires an M.Sc. / M.Tech. in a relevant discipline with "
                "UGC-NET or GATE qualification, while an SRF requires the same plus roughly two "
                "years of research experience. Individual advertisements specify exact subject "
                "requirements \u2014 always check the official notification linked from each "
                "listing.",
            ),
            (
                "What stipend do JRF / SRF and project associate positions pay?",
                "Stipends follow funding-agency norms \u2014 commonly around Rs 37,000\u201342,000 "
                "per month for JRF and Rs 42,000\u201346,000 for SRF under national fellowship "
                "schemes \u2014 while project associate positions at institutes and IITs follow "
                "the DST pay matrix (about Rs 25,000\u201356,000 depending on level). The registry "
                "records the compensation stated in each advertisement.",
            ),
            (
                "How often are new research vacancies added?",
                "The registry refreshes every day at 7 AM IST: official institute portals, "
                "verified job feeds and news alerts for JRF, SRF and project associate "
                "advertisements are scanned automatically, so new openings usually appear within "
                "24 hours of publication.",
            ),
        ],
    },
    {
        "file": "phd-fellowships-climate-sustainability.html",
        "match": match_phd,
        "kicker": "Doctoral & Postdoctoral Track",
        "title": "PhD & Postdoctoral Fellowships \u2014 Climate & Sustainability, India | Urban Forest Park",
        "h1": "PhD & Postdoctoral Fellowships \u2014 Climate, Sustainability & Environment",
        "desc": (
            "Doctoral fellowships, PhD positions and postdoctoral vacancies in climate change, "
            "sustainability, ecology and environmental science at IITs, IISc, central universities "
            "and research institutes across India."
        ),
        "hero_sub": (
            "Doctoral programmes, PhD fellowships and postdoctoral mandates in climate, ecology, "
            "sustainability and environmental science \u2014 every listing links to the official "
            "institute portal."
        ),
        "list_copy": (
            "PhD admissions with funding, doctoral fellowships and postdoctoral positions in "
            "climate dynamics, earth-system modelling, environmental sustainability, ecological "
            "sciences and allied fields at Indian institutes of national importance and research "
            "organisations."
        ),
        "cta_href": "/?track=phd",
        "matched_noun": "doctoral and postdoctoral",
        "faqs": [
            (
                "Where are PhD and postdoctoral positions in climate and sustainability advertised in India?",
                "IITs, IISc, IIMs, central and state universities, TERI and TERI SAS, the Indian "
                "Institute of Forest Management, NRSC / ISRO centres and national research "
                "institutes advertise doctoral and postdoctoral openings on their official "
                "portals. The registry aggregates these advertisements daily and links to the "
                "source.",
            ),
            (
                "What funding supports PhD research in climate and sustainability in India?",
                "Common funding routes include UGC-JRF, CSIR-JRF, DST-INSPIRE fellowships, "
                "institute assistantships and project-linked fellowships funded by DST, DBT, "
                "MoEFCC and international programmes. Individual listings state the fellowship "
                "amount and duration where advertised.",
            ),
            (
                "Can I find postdoctoral positions in this registry?",
                "Yes \u2014 postdoctoral fellow and research associate (post-PhD) positions are "
                "tracked under this pathway and in the JRF / SRF & Project Associate hub. "
                "Postdoctoral mandates at IITs, IISc and national institutes are added as they "
                "are published.",
            ),
            (
                "How are PhD and fellowship listings verified?",
                "Every listing is sourced from an official institute portal, a verified job feed "
                "or a reputable news announcement, then normalised and de-duplicated by the "
                "registry pipeline. Each dossier links straight to the official application "
                "page \u2014 the registry never charges fees.",
            ),
        ],
    },
    {
        "file": "forestry-wildlife-government-jobs.html",
        "match": match_forestry,
        "kicker": "Government & Forestry Track",
        "title": "Forestry & Wildlife Jobs in India \u2014 Government Vacancies | Urban Forest Park",
        "h1": "Forestry, Wildlife & Government Jobs in India",
        "desc": (
            "Forest department, wildlife institute, ICFRE and environment ministry vacancies "
            "across India \u2014 research positions, young-professional mandates and contractual "
            "roles with direct application links."
        ),
        "hero_sub": (
            "Forestry, wildlife, conservation and environment-ministry mandates \u2014 research "
            "and project positions, young professionals and contractual government roles across "
            "Indian states."
        ),
        "list_copy": (
            "Vacancies with state forest departments, the Wildlife Institute of India, ICFRE "
            "institutes, SACON, the environment ministry and conservation organisations \u2014 "
            "covering forestry, afforestation, wildlife biology, ecology and habitat "
            "management."
        ),
        "cta_href": "/?category=forestry-wildlife-afforestation",
        "matched_noun": "forestry, wildlife and government",
        "faqs": [
            (
                "Which government bodies hire in forestry and wildlife in India?",
                "State forest departments, the Ministry of Environment, Forest and Climate Change "
                "(MoEFCC), ICFRE institutes, the Wildlife Institute of India, state biodiversity "
                "and wildlife boards, SACON and national parks authorities regularly advertise "
                "research, project and contractual positions. The registry tracks these official "
                "portals daily.",
            ),
            (
                "What is a Young Professional role in the environment sector?",
                "Young Professional (YP) positions are contractual scheme roles \u2014 commonly "
                "in the 0\u20133 year experience band \u2014 with ministries, forest departments "
                "and research institutes. They typically run for one to three years, may be "
                "renewable, and follow institute or scheme pay norms.",
            ),
            (
                "Are these permanent government jobs?",
                "The registry covers both permanent recruitments and contractual or project-mode "
                "engagements. Each listing states the nature of the role, the application window "
                "and the official portal where the recruitment is administered \u2014 always "
                "verify details in the original notification.",
            ),
            (
                "How do I apply for forest department vacancies?",
                "Open the position dossier and follow the official application link \u2014 forest "
                "department and institute recruitments are administered through their own "
                "portals, walk-in interviews or email applications as stated in the "
                "advertisement. The registry never charges fees for listings.",
            ),
        ],
    },
    {
        "file": "gis-remote-sensing-climate-jobs.html",
        "match": match_gis,
        "kicker": "Geospatial Track",
        "title": "GIS & Remote Sensing Jobs in India \u2014 Geospatial & Earth Observation | Urban Forest Park",
        "h1": "GIS, Remote Sensing & Earth Observation Jobs in India",
        "desc": (
            "GIS analyst, remote sensing, geospatial and earth observation vacancies across ISRO "
            "centres, environmental institutes, urban planning bodies and consultancies in India "
            "\u2014 updated daily."
        ),
        "hero_sub": (
            "Geospatial analyst, remote sensing, earth observation and urban heat-island mandates "
            "with ISRO / NRSC, research institutes, urban bodies and consultancies across India."
        ),
        "list_copy": (
            "GIS, remote sensing and earth-observation positions spanning geospatial modelling, "
            "satellite data analysis, urban heat-island mapping, land-use change and spatial "
            "planning \u2014 each with a direct link to the official application portal."
        ),
        "cta_href": "/?category=gis-remote-sensing-earth-observation",
        "matched_noun": "GIS, remote sensing and geospatial",
        "faqs": [
            (
                "Which organisations hire GIS and remote sensing specialists in India?",
                "ISRO / NRSC and regional remote sensing centres, state remote sensing "
                "application centres, IITs and central universities, environmental research "
                "institutes such as TERI and ATREE, urban development authorities and private "
                "geospatial consultancies all advertise geospatial roles \u2014 tracked daily by "
                "the registry.",
            ),
            (
                "What qualifications do GIS jobs require?",
                "Most positions ask for an M.Sc. / M.Tech. in geoinformatics, remote sensing, "
                "geography or a related discipline, with hands-on skills in QGIS / ArcGIS, "
                "Google Earth Engine, Python or R and satellite-image processing. Project "
                "associate and young-professional roles may accept strong B.Tech. or fresh "
                "postgraduate candidates.",
            ),
            (
                "Are there urban heat island and climate-mapping roles in the registry?",
                "Yes \u2014 urban heat-island modelling, land-surface temperature analysis and "
                "climate-mapping mandates with institutes and municipal programmes appear under "
                "this pathway as they are advertised.",
            ),
            (
                "Can freshers find geospatial jobs here?",
                "Entry-level project associate, project assistant and fellowship positions in "
                "geospatial projects are tracked along with experienced roles. Use the experience "
                "filter in the live registry to see Entry Level / Fellowship openings.",
            ),
        ],
    },
    {
        "file": "esg-carbon-sustainability-jobs.html",
        "match": match_esg,
        "kicker": "Corporate & Carbon Track",
        "title": "ESG, Carbon Market & Sustainability Jobs in India | Urban Forest Park",
        "h1": "ESG, Carbon Markets & Corporate Sustainability Jobs",
        "desc": (
            "ESG analyst, sustainability manager, carbon market, climate finance and corporate "
            "sustainability vacancies across Indian companies, consultancies and NGOs \u2014 "
            "verified and updated daily."
        ),
        "hero_sub": (
            "ESG analyst, sustainability manager, carbon-market and climate-finance mandates "
            "across corporate India, consultancies and development organisations."
        ),
        "list_copy": (
            "Corporate sustainability and ESG positions \u2014 ESG analysis and reporting, BRSR "
            "disclosure, carbon accounting and markets, climate risk and climate finance "
            "\u2014 from companies, consultancies, rating agencies and NGOs. Every listing links "
            "to the official careers portal."
        ),
        "cta_href": "/?category=esg-carbon-sustainability",
        "matched_noun": "ESG and sustainability",
        "faqs": [
            (
                "What ESG and sustainability roles are in demand in India?",
                "ESG analyst and reporting roles, BRSR / sustainability disclosure specialists, "
                "carbon accounting and assurance, climate-risk modelling, climate finance and "
                "corporate sustainability manager positions are among the fastest-growing "
                "mandates \u2014 alongside environmental and social impact roles at development "
                "organisations.",
            ),
            (
                "What skills do carbon market jobs require?",
                "Employers typically look for GHG accounting (GHG Protocol), familiarity with "
                "carbon-market mechanisms (India CCTS, voluntary markets), MRV, ISO 14064 / 14067 "
                "and sustainability-reporting standards, plus data and reporting tooling. Skill "
                "chips on each listing summarise the stated requirements.",
            ),
            (
                "Do these listings include BRSR and climate-disclosure roles?",
                "Yes \u2014 BRSR reporting, climate disclosure and assurance mandates are tracked "
                "under this pathway, alongside environmental compliance and EHS sustainability "
                "roles where they carry a climate / ESG remit.",
            ),
            (
                "How does the registry verify corporate ESG vacancies?",
                "Corporate roles are collected from official company career portals and verified "
                "job feeds, then normalised, de-duplicated and linked directly to the employer's "
                "application page. Closed mandates move to the Historical Archive for reference.",
            ),
        ],
    },
]

for _hub in HUBS:
    _meta = page_meta(_hub["file"])
    _hub["title"] = plain(_meta["title"])
    _hub["desc"] = plain(_meta["description"])
    _hub["h1"] = plain(_meta["h1"])
    _hub["canonical"] = SITE + "/" + _hub["file"]
    _hub["primary_keyword"] = plain(_meta["primary_keyword"])


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------
def load_records(public: Path, filename: str) -> List[Dict[str, Any]]:
    path = public / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not read %s (%s); treating as empty.", path, exc)
        return []
    if isinstance(data, dict):
        data = data.get("jobs", [])
    if not isinstance(data, list):
        return []
    records: List[Dict[str, Any]] = []
    for entry in data:
        if isinstance(entry, dict):
            records.append(fh.normalize_job_fields(entry))
    return records


def sort_recent_first(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        jobs,
        key=lambda j: (str(j.get("date_added") or ""), str(j.get("clean_title") or "")),
        reverse=True,
    )


def recent_archive(archived: List[Dict[str, Any]], today: date, days: int) -> List[Dict[str, Any]]:
    cutoff = (today - timedelta(days=days)).isoformat()
    pool = [j for j in archived if str(j.get("date_archived") or "") >= cutoff]
    if not pool:
        pool = archived
    return sorted(pool, key=lambda j: str(j.get("date_archived") or ""), reverse=True)


# --------------------------------------------------------------------------
# Shared fragments
# --------------------------------------------------------------------------
def header_html(active: Optional[str] = None) -> str:
    def cls(name: str) -> str:
        return "nav-link active" if active == name else "nav-link"

    return f"""  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="/" aria-label="Urban Forest Park - National Career Registry, India">
        <img src="/assets/images/Logo_UFF.png" alt="{BRAND_ALT_HTML}" title="{BRAND_TITLE}" class="ufp-header-logo" width="48" height="48" loading="eager" decoding="async" fetchpriority="high" />
        <span class="brand-word">Urban Forest Park</span>
        <span class="brand-sub">National Climate, Forestry, ESG &amp; Geospatial Career Registry (India)</span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="Primary">
        <a class="{cls('registry')}" href="/">Career Registry</a>
        <a class="{cls('archive')}" href="/?view=archive">Historical Archive</a>
        <a class="{cls('global')}" href="/global-climate-sustainability-opportunities.html">Global Opportunities</a>
      </nav>
      <div class="header-actions">
        <a class="btn btn-outline nav-cta" href="/#filter-bar">Browse Registry</a>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false" aria-label="Switch to night mode">
          <svg class="theme-icon icon-sun" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.4"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.3 5.3l1.7 1.7M17 17l1.7 1.7M18.7 5.3 17 7M7 17l-1.7 1.7"/></svg>
          <svg class="theme-icon icon-moon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.4 14.2A8.5 8.5 0 1 1 9.8 3.6a7 7 0 0 0 10.6 10.6z"/></svg>
          <span class="theme-label" id="theme-label">Night</span>
        </button>
        <button class="nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Toggle navigation menu">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
      </div>
    </div>
  </header>"""


def footer_html(current_hub: Optional[str] = None) -> str:
    hub_links = []
    for hub in HUBS:
        if hub["file"] == current_hub:
            hub_links.append(f'          <li><span class="footer-current">{esc(hub["h1"])}</span></li>')
        else:
            hub_links.append(f'          <li><a href="/{hub["file"]}">{esc(hub["h1"])}</a></li>')
    hubs_block = "\n".join(hub_links)

    return f"""  <footer class="site-footer">
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Urban Forest Park</h3>
        <p>
          National Climate, Forestry, ESG &amp; Geospatial Career Registry (India). We monitor
          official portals, universities, research institutions, consultancies and development
          organisations &mdash; and publish verified mandates that link straight to the source.
        </p>
        <p style="margin-top:10px;">
          Also home of the <a href="/dashboard.html">Nagar Van dMRV Dashboard &amp; Green Calculator</a>.
        </p>
      </div>

      <div class="footer-col">
        <h3>Career Pathways</h3>
        <ul>
{hubs_block}
        </ul>
        <h3 style="margin-top:16px;">Regional &amp; Multilingual Portals (भारत / हिंदी)</h3>
        <ul>
          <li><a href="/hindi-environment-forestry-jobs.html">हिंदी करियर पोर्टल — पर्यावरण एवं वानिकी भर्तियाँ</a></li>
          <li><a href="/bharat-regional-green-jobs.html">Bharat Regional &amp; State-Wise Green Jobs</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>Registry</h3>
        <ul>
          <li><a href="/">Active Opportunities</a></li>
          <li><a href="/?view=archive">Historical Mandate Archive</a></li>
          <li><a href="/global-climate-sustainability-opportunities.html">&#127757; Global Opportunities (International)</a></li>
          <li><a href="/#filter-bar">Browse by State</a></li>
          <li><a href="/#seo-dir-title">Browse by Sector</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>Institutional Tools</h3>
        <ul>
          <li><a href="/dashboard.html">Live dMRV Dashboard</a></li>
          <li><a href="/green-calculator.html">Green Calculator</a></li>
          <li><a href="/nagar-van-finder.html">Nagar Van Finder</a></li>
          <li><a href="/spatial-data.html">Spatial Data Explorer</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>Legal &amp; Contact</h3>
        <ul>
          <li><a href="/about.html">About</a></li>
          <li><a href="/privacy.html">Privacy Policy</a></li>
          <li><a href="/terms.html">Terms of Use</a></li>
          <li><a href="/cookies.html">Cookie Policy</a></li>
          <li><a href="/accessibility.html">Accessibility</a></li>
          <li><a href="/unsubscribe.html">Dispatch Preferences</a></li>
          <li><a href="/cookies.html" data-ufp-cookie-settings>Cookie Preferences</a></li>
          <li><a href="/report.html">Report an Issue</a></li>
          <li><a href="mailto:urbanforestpark@gmail.com">Contact the Registry</a></li>
          <li><a href="https://t.me/urbanforestpark" target="_blank" rel="noopener">Telegram Channel</a></li>
          <li><a href="https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw" target="_blank" rel="noopener">WhatsApp Job Group</a></li>
          <li><button type="button" class="footer-link-btn" data-syndication-open title="Internal broadcast &amp; backlink workspace (Ctrl+Shift+U)">Syndication Desk</button></li>
        </ul>
      </div>
    </div>

    <div class="footer-bottom">
      &copy; {ist_today().year} Urban Forest Park<span class="dot">&bull;</span>National Climate, Forestry, ESG &amp; Geospatial Career Registry (India)
      <span class="dot">&bull;</span>All listings link to official application portals &mdash; please verify details before applying.
      <span class="dot">&bull;</span><a href="/about.html#cite">Cite this registry &amp; embed a link</a>
    </div>
  </footer>"""


# --------------------------------------------------------------------------
# Index snapshot
# --------------------------------------------------------------------------
# NOTE: The homepage FAQ block (executive accordion + FAQPage JSON-LD) is
# maintained by hand in public/index.html, outside the snapshot markers.
# Historically this script injected a second, generated FAQ block here; it
# was retired so the page carries exactly one FAQPage entity, synchronised
# with the visible accordion content.



def snapshot_link(job: Dict[str, Any]) -> str:
    title = plain(job.get("clean_title")) or plain(job.get("organization")) or "Untitled mandate"
    org = plain(job.get("organization"))
    label = f"{title} \u2014 {org} ({state_label(job)} | {position_type_of(job)})"
    return f'            <li><a href="/?job={esc(job.get("id"))}">{esc(label)}</a></li>'


def build_index_block(
    active: List[Dict[str, Any]],
    archived: List[Dict[str, Any]],
    today: date,
) -> str:
    active_sorted = sort_recent_first(active)
    archived_sorted = recent_archive(archived, today, RECENT_ARCHIVE_DAYS)[:24]

    active_links = "\n".join(snapshot_link(j) for j in active_sorted)
    archived_links = "\n".join(snapshot_link(j) for j in archived_sorted) or (
        '            <li class="seo-pr-empty">No recently archived mandates.</li>'
    )

    hub_links = "\n".join(
        f'            <li><a href="/{h["file"]}">{esc(h["h1"])}</a></li>' for h in HUBS
    )
    hub_links += (
        '\n            <li><a href="/global-climate-sustainability-opportunities.html">'
        '&#127757; Global Opportunities (International Jobs, Grants &amp; Scholarships)</a></li>'
    )

    intro = (
        f"The complete static index of active environmental, forestry, geospatial and academic "
        f"research mandates tracked by Urban Forest Park \u2014 climate, forestry, wildlife, ESG, "
        f"carbon market, GIS, remote sensing, earth observation, JRF, SRF, PhD, postdoctoral, "
        f"project associate, young professional and faculty vacancies across Indian states and "
        f"cities. Every entry links to the live position dossier with the official application "
        f"portal. Snapshot updated {long_date(today)} (IST) \u2014 {len(active_sorted)} active "
        f"and {len(archived_sorted)} recently archived mandates."
    )

    block = f"""{SNAPSHOT_START}
    <section class="seo-prerendered" aria-labelledby="seo-pr-title">
      <div class="seo-pr-inner">
        <p class="eyebrow">Pre-Rendered Registry Snapshot</p>
        <h2 id="seo-pr-title">Complete List of Active Environmental &amp; Academic Mandates in India</h2>
        <p class="seo-pr-intro">{esc(intro)}</p>
        <div class="seo-pr-grid">
          <div class="seo-pr-col">
            <h3>Active Opportunities ({len(active_sorted)})</h3>
            <ul class="seo-pr-list">
{active_links}
            </ul>
          </div>
          <div class="seo-pr-col">
            <h3>Recently Archived Mandates ({len(archived_sorted)})</h3>
            <ul class="seo-pr-list">
{archived_links}
            </ul>
            <h3 style="margin-top:22px;">Career Pathway Hubs</h3>
            <ul class="seo-pr-list">
{hub_links}
            </ul>
          </div>
        </div>
      </div>
    </section>
    {SNAPSHOT_END}"""
    return block


def inject_snapshot(index_path: Path, block: str) -> None:
    text = index_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(SNAPSHOT_START) + r".*?" + re.escape(SNAPSHOT_END), re.S
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise SystemExit(
            f"ERROR: expected exactly one {SNAPSHOT_START} ... {SNAPSHOT_END} block in "
            f"{index_path} (found {len(matches)}). Aborting without changes."
        )
    text = pattern.sub(lambda _m: block, text, count=1)
    index_path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------
# Hub pages
# --------------------------------------------------------------------------
def hub_card_html(job: Dict[str, Any], archived: bool = False) -> str:
    cat = plain(job.get("category"))
    pt = position_type_of(job)
    state = state_label(job)
    org = plain(job.get("organization")) or "Organisation not specified"
    city = plain(job.get("city"))
    org_line = org + (f" \u00b7 {city}" if city and city.lower() != org.lower() else "")

    badges = [
        f'<span class="badge {cat_class(cat)}">{esc(cat)}</span>',
        f'<span class="badge badge-type">{esc(pt)}</span>',
        f'<span class="badge badge-state">{PIN_SVG}{esc(state)}</span>',
    ]
    if archived:
        closed_on = plain(job.get("date_archived")) or plain(job.get("valid_through"))
        badges.append(f'<span class="badge badge-archived">Closed {esc(closed_on)}</span>')

    elig_bits = []
    if plain(job.get("qualification_summary")):
        elig_bits.append(f"<span><strong>Qualification:</strong> {esc(job['qualification_summary'])}</span>")
    if plain(job.get("compensation_or_fellowship")):
        elig_bits.append(f"<span><strong>Compensation:</strong> {esc(job['compensation_or_fellowship'])}</span>")
    elig_html = (
        '<p class="hub-card-elig">' + " ".join(elig_bits) + "</p>" if elig_bits else ""
    )

    summary = trim(job.get("role_summary"), 240)
    summary_html = f'<p class="hub-card-sum">{esc(summary)}</p>' if summary else ""

    return f"""        <article class="hub-card{' hub-card-archived' if archived else ''}">
          <div class="hub-card-top">
            {''.join(badges)}
          </div>
          <h3 class="hub-card-title"><a href="/?job={esc(job.get('id'))}">{esc(plain(job.get('clean_title')) or org)}</a></h3>
          <p class="hub-card-org">{esc(org_line)}</p>
          {elig_html}
          {summary_html}
          <p class="hub-card-foot"><a href="/?job={esc(job.get('id'))}">View dossier &amp; application link &rarr;</a></p>
        </article>"""


def faq_section_html(faqs: List[Tuple[str, str]], heading: str = "Frequently Asked Questions") -> str:
    items = "\n".join(
        f"          <dt>{esc(q)}</dt>\n          <dd>{esc(a)}</dd>" for q, a in faqs
    )
    return f"""      <section class="hub-faq" aria-labelledby="hub-faq-title">
        <h2 id="hub-faq-title">{esc(heading)}</h2>
        <dl>
{items}
        </dl>
      </section>"""


def collection_jsonld(hub: Dict[str, Any], today: date) -> str:
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": hub["title"],
            "description": hub["desc"],
            "url": hub["canonical"],
            "inLanguage": "en-IN",
            "dateModified": today.isoformat(),
            "isPartOf": {"@id": SITE + "/#website"},
            "publisher": {"@id": SITE + "/#organization"},
            "about": {"@type": "Thing", "name": hub["h1"]},
        }
    )


def item_list_jsonld(hub: Dict[str, Any], jobs: List[Dict[str, Any]]) -> str:
    items = []
    for index, job in enumerate(jobs[:ITEM_LIST_CAP], start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": index,
                "url": SITE + "/?job=" + str(job.get("id") or ""),
                "name": plain(job.get("clean_title")) or plain(job.get("organization")),
            }
        )
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": hub["h1"],
            "numberOfItems": len(items),
            "itemListElement": items,
        }
    )


def faq_jsonld(faqs: List[Tuple[str, str]]) -> str:
    return jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in faqs
            ],
        }
    )


def build_hub_page(
    hub: Dict[str, Any],
    active_jobs: List[Dict[str, Any]],
    archived_jobs: List[Dict[str, Any]],
    all_hubs_counts: Dict[str, int],
    today: date,
) -> str:
    matched_active = sort_recent_first([j for j in active_jobs if hub["match"](j)])
    matched_archived = recent_archive(
        [j for j in archived_jobs if hub["match"](j)], today, RECENT_ARCHIVE_DAYS
    )[:HUB_ARCHIVE_LIMIT]

    cards = "\n".join(hub_card_html(j) for j in matched_active) or (
        '        <p class="hub-empty">No mandates in this pathway right now \u2014 new openings '
        'are added daily. <a href="/">Browse the full registry</a>.</p>'
    )

    archive_block = ""
    if matched_archived:
        arch_cards = "\n".join(hub_card_html(j, archived=True) for j in matched_archived)
        archive_block = f"""      <section class="hub-archive" aria-labelledby="hub-archive-title">
        <h2 id="hub-archive-title">Recently Closed {esc(hub['matched_noun'])} mandates</h2>
        <p class="hub-archive-sub">Preserved for reference \u2014 compensation, eligibility and institutional history.</p>
        <div class="hub-list">
{arch_cards}
        </div>
      </section>"""

    other_links = "\n".join(
        f'          <li><a href="/{h["file"]}"><span class="hub-other-name">{esc(h["h1"])}</span>'
        f'<span class="hub-other-cnt">{all_hubs_counts.get(h["file"], 0)} active</span></a></li>'
        for h in HUBS
        if h["file"] != hub["file"]
    )

    states = sorted({state_label(j) for j in matched_active})
    states_note = (
        f"{len(states)} states / regions"
        if len(states) > 1
        else (states[0] if states else "All India")
    )

    jsonld_blocks = "\n".join(
        [
            organization_jsonld(),
            website_jsonld(),
            collection_jsonld(hub, today),
            item_list_jsonld(hub, matched_active),
            breadcrumb_jsonld(hub["h1"], hub["canonical"]),
            faq_jsonld(hub["faqs"]),
        ]
    )

    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
    {GA_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{THEME_BOOTSTRAP}

    <title>{esc(hub['title'])}</title>
    <meta name="description" content="{esc(hub['desc'])}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{hub['canonical']}">
    <link rel="alternate" hreflang="en-IN" href="{hub['canonical']}">
    <link rel="alternate" hreflang="hi-IN" href="https://www.urbanforestpark.com/hindi-environment-forestry-jobs.html">
    <link rel="alternate" hreflang="en" href="https://www.urbanforestpark.com/global-climate-sustainability-opportunities.html">
    <link rel="alternate" hreflang="x-default" href="{hub['canonical']}">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park \u2014 India Career Registry">
    <meta property="og:title" content="{esc(hub['title'])}">
    <meta property="og:description" content="{esc(hub['desc'])}">
    <meta property="og:url" content="{hub['canonical']}">
    <meta property="og:image" content="{LOGO_URL}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{esc(hub['title'])}">
    <meta name="twitter:description" content="{esc(hub['desc'])}">
    <meta name="twitter:image" content="{LOGO_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{FAVICONS}

    <!-- Typography -->
{FONTS}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{jsonld_blocks}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#hub-list">Skip to listings</a>

{header_html('registry')}

  <main>
    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">Career Registry</a><span aria-hidden="true">/</span><span>{esc(hub['h1'])}</span>
        </nav>
        <p class="eyebrow">{esc(hub['kicker'])}</p>
        <h1>{esc(hub['h1'])}</h1>
        <p class="hub-hero-sub">{esc(hub['hero_sub'])}</p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="{hub['cta_href']}">Open in the live registry &rarr;</a>
          <a class="btn btn-outline" href="/?view=archive">Historical Archive</a>
        </div>
        <dl class="hub-stats">
          <div><dt>Active listings</dt><dd>{len(matched_active)}</dd></div>
          <div><dt>Coverage</dt><dd>{esc(states_note)}</dd></div>
          <div><dt>Updated</dt><dd>{esc(long_date(today))}</dd></div>
        </dl>
      </div>
    </section>

    <section class="hub-main" id="hub-list">
      <div class="hub-main-inner">
        <div class="hub-main-head">
          <h2>Active {esc(hub['matched_noun'])} mandates ({len(matched_active)})</h2>
          <p>{esc(hub['list_copy'])}</p>
        </div>
        <div class="hub-list">
{cards}
        </div>

{archive_block}

{faq_section_html(hub['faqs'])}

        <section class="hub-cta" aria-label="Open the live registry">
          <div>
            <h2>Looking for something else?</h2>
            <p>The live registry carries every active mandate with state, sector and career-track filters \u2014 updated daily at 7 AM IST.</p>
          </div>
          <a class="btn btn-primary" href="{hub['cta_href']}">Browse on urbanforestpark.com &rarr;</a>
        </section>

        <section class="hub-others" aria-labelledby="hub-others-title">
          <h2 id="hub-others-title">Explore other career pathways</h2>
          <ul class="hub-other-grid">
{other_links}
          </ul>
        </section>
      </div>
    </section>
  </main>

{site_matrix_html('/' + hub['file'])}

{footer_html(hub['file'])}

  <script defer src="/js/consent.js"></script>
<script defer src="/js/back-to-top.js"></script>
<script defer src="/js/syndication-drawer.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the static SEO pages for the registry.")
    parser.add_argument(
        "--public",
        type=Path,
        default=DEFAULT_PUBLIC,
        help="Path to the public/ directory (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    args = parse_args(argv)
    public: Path = args.public.resolve()
    today = ist_today()

    index_path = public / "index.html"
    if not index_path.exists():
        log.error("index.html not found at %s", index_path)
        return 1

    active = load_records(public, "jobs.json")
    archived = load_records(public, "archive.json")
    log.info("Loaded %d active and %d archived mandate(s)", len(active), len(archived))

    # ---- index snapshot -------------------------------------------------
    block = build_index_block(active, archived, today)
    inject_snapshot(index_path, block)
    log.info("Injected registry snapshot into %s", index_path.name)

    # ---- hub pages ------------------------------------------------------
    hub_counts: Dict[str, int] = {}
    for hub in HUBS:
        matched = [j for j in active if hub["match"](j)]
        hub_counts[hub["file"]] = len(matched)

    for hub in HUBS:
        page = build_hub_page(hub, active, archived, hub_counts, today)
        out_path = public / hub["file"]
        out_path.write_text(page, encoding="utf-8")
        log.info("Wrote %s (%d active match(es))", hub["file"], hub_counts[hub["file"]])

    # ---- multilingual & regional portals --------------------------------
    import seo_portals  # lazy import: reuses this module's helpers/constants

    hindi_page = seo_portals.build_hindi_hub_page(active, archived, hub_counts, today)
    (public / seo_portals.HINDI_HUB_FILE).write_text(hindi_page, encoding="utf-8")
    log.info("Wrote %s", seo_portals.HINDI_HUB_FILE)

    regional_page = seo_portals.build_regional_hub_page(active, today)
    (public / seo_portals.REGIONAL_HUB_FILE).write_text(regional_page, encoding="utf-8")
    log.info("Wrote %s", seo_portals.REGIONAL_HUB_FILE)

    # ---- global opportunities hub (strictly separate registry) -----------
    global_active = load_records(public, "global_jobs.json")
    if not global_active:
        log.warning("global_jobs.json missing or empty - global hub built with placeholder content")
    global_page = seo_portals.build_global_hub_page(global_active, today)
    (public / seo_portals.GLOBAL_HUB_FILE).write_text(global_page, encoding="utf-8")
    log.info(
        "Wrote %s (%d global listing(s))",
        seo_portals.GLOBAL_HUB_FILE,
        len(global_active),
    )

    # ---- institutional pages + keyword-map metadata -----------------------
    import seo_static_pages  # lazy import: reuses this module's helpers

    seo_static_pages.write_keyword_map(public)
    seo_static_pages.write_institutional_pages(public, today)
    seo_static_pages.normalise_static_pages(public)
    log.info("Wrote institutional pages and normalised static SEO metadata")

    # ---- pretty-URL normalisation ----------------------------------------
    # Cloudflare Pages serves /about and 308s /about.html. Everything the
    # crawler sees must use the 200 form: internal links, canonical/OG tags,
    # JSON-LD URLs and the sitemap.
    rewritten = 0
    for path in sorted(public.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        updated = prettify_internal_urls(text)
        updated = re.sub(
            r"(/assets/images/Logo_UFF\.png)(?!\?)",
            r"\1?v=" + ASSET_VERSION,
            updated,
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            rewritten += 1
    log.info("Normalised internal URLs on %d page(s)", rewritten)

    sitemap_path = public / "sitemap.xml"
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text(encoding="utf-8")
        updated = re.sub(
            r"<loc>([^<]+)</loc>",
            lambda m: "<loc>" + pretty_url(m.group(1)) + "</loc>",
            sitemap,
        )
        if updated != sitemap:
            sitemap_path.write_text(updated, encoding="utf-8")
            log.info("Normalised sitemap locations to extensionless canonicals")

    log.info(
        "SEO surface rebuilt: 1 snapshot + %d hub page(s) + 2 multilingual portal(s) + 1 global hub + 3 institutional pages",
        len(HUBS),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
