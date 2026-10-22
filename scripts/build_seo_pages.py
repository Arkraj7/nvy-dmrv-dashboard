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
    # Never rewrite an external absolute URL, even when it ends in .html.
    if url.startswith(("http://", "https://")) and not url.startswith(SITE + "/"):
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
JOB_FEED_START = "<!-- JOB_FEED_START -->"
JOB_FEED_END = "<!-- JOB_FEED_END -->"

# Official social profiles. Keep these URLs in one place so the footer links,
# Organization JSON-LD sameAs array and the SEO auditor never drift apart.
LINKEDIN_GROUP_URL = "https://www.linkedin.com/groups/40965341/"
FACEBOOK_PAGE_URL = "https://www.facebook.com/share/1EwgtMnfcx/"
OFFICIAL_SOCIAL_URLS = (LINKEDIN_GROUP_URL, FACEBOOK_PAGE_URL)
CARD_STOP = '<span class="visually-hidden">.</span>'
PRERENDER_CARDS = 12
JOBS_DIRNAME = "jobs"

RECENT_ARCHIVE_DAYS = 180     # archived mandates shown on the index snapshot
HUB_ARCHIVE_LIMIT = 6         # archived mandates per hub page
ITEM_LIST_CAP = 60            # ItemList entries per hub page

# Hub streak gating (A2 duplicate-hub rule)
HUB_STREAK_STATE_PATH = REPO_ROOT / "scripts" / "hub_streak_state.json"
HUB_ON_THRESHOLD = 12         # minimum active roles to start counting streak_on
HUB_ON_STREAK_N = 3           # consecutive runs at/above threshold to flip ON
HUB_OFF_THRESHOLD = 8         # active roles below this to start counting streak_off
HUB_OFF_STREAK_N = 7          # consecutive runs below threshold to flip OFF

# A literal, crawlable separator between adjacent badge <span> elements. The
# spaces matter: tag-stripping crawlers otherwise concatenate the badges into
# one unreadable token.
BADGE_SEP = '<span class="badge-sep" aria-hidden="true"> · </span>'

# Boilerplate qualification / pay strings are deliberately suppressed on feed
# and hub cards. They describe no specific job, repeat across many records and
# create duplicate on-page text. The full dossier keeps the original fields.
_GENERIC_QUAL_RE = re.compile(
    r"relevant discipline|as per (?:the )?(?:institute|project|scheme|fellowship|advertisement|norms)|"
    r"recent graduate\s*/\s*postgraduate|as per institute norms|as per university norms|"
    r"as per funding agency norms",
    re.I,
)
_GENERIC_COMP_RE = re.compile(
    r"not disclosed|as per (?:institute|university|project|scheme|fellowship|un volunteer|ugc|icfre|"
    r"funding agency|organization|organisation) norms|as per norms",
    re.I,
)


def is_specific_qualification(value: Any) -> bool:
    text = plain(value)
    return bool(text) and not bool(_GENERIC_QUAL_RE.search(text))


def is_specific_compensation(value: Any) -> bool:
    text = plain(value)
    return bool(text) and not bool(_GENERIC_COMP_RE.search(text))


def anchor_text(value: Any, limit: int = 68) -> str:
    """Keep visible anchor text short; the full title stays in aria/title."""
    return trim(value, limit)

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


def sentence(value: Any, limit: Optional[int] = None) -> str:
    """Return one clean sentence for crawlable card metadata.

    Tag-stripping crawlers do not insert spaces at block boundaries.  Ending
    each card line with a terminal period prevents neighbouring titles,
    badges, locations and skills from collapsing into a run-on sentence.
    """
    text = trim(value, limit) if limit else plain(value)
    text = text.strip()
    if not text:
        return ""
    return text.rstrip(" .;:,\u2026") + "."


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


# --------------------------------------------------------------------------
# Hub streak gating (A2 duplicate-hub rule)
# --------------------------------------------------------------------------
HUB_STREAK_STATE_PATH = REPO_ROOT / "scripts" / "hub_streak_state.json"
HUB_ON_THRESHOLD = 12         # minimum active roles to start counting streak_on
HUB_ON_STREAK_N = 3           # consecutive runs at/above threshold to flip ON
HUB_OFF_THRESHOLD = 8         # active roles below this to start counting streak_off
HUB_OFF_STREAK_N = 7          # consecutive runs below threshold to flip OFF


def load_hub_streak_state() -> Dict[str, Any]:
    if HUB_STREAK_STATE_PATH.exists():
        try:
            return json.loads(HUB_STREAK_STATE_PATH.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not read hub streak state %s: %s", HUB_STREAK_STATE_PATH, exc)
    return {"hubs": {}, "last_run_date": None}


def save_hub_streak_state(state: Dict[str, Any]) -> None:
    HUB_STREAK_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def update_hub_streaks(hub_counts: Dict[str, int], hub_to_city: Dict[str, str]) -> Dict[str, bool]:
    """
    Update streak counters for each hub and return {hub_file: is_indexable}.
    Applies A2 duplicate-hub rule: a state hub is forced to noindex only when
    its overlapping city hub is currently indexable (or flips ON in this run).
    """
    state = load_hub_streak_state()
    hubs_state = state.setdefault("hubs", {})
    today = ist_today().isoformat()
    # Count once per calendar day, not once per build. Without this guard a
    # manual re-build (or a retried CI run) can satisfy a multi-day streak in
    # a single session.
    already_ran_today = state.get("last_run_date") == today

    # Initialize hubs not yet tracked
    for hub_file in hub_counts:
        if hub_file not in hubs_state:
            hubs_state[hub_file] = {
                "streak_on": 0,
                "streak_off": 0,
                "indexable": False,
                "last_flip": None,
                "flip_log": [],
            }

    indexable: Dict[str, bool] = {}
    for hub_file, count in hub_counts.items():
        h = hubs_state[hub_file]
        currently_indexable = h["indexable"]

        if not already_ran_today:
            if count >= HUB_ON_THRESHOLD:
                h["streak_on"] += 1
                h["streak_off"] = 0
            else:
                h["streak_on"] = 0
                h["streak_off"] += 1

        # Flip ON: 3 consecutive runs >= 12
        if not currently_indexable and h["streak_on"] >= HUB_ON_STREAK_N:
            h["indexable"] = True
            h["last_flip"] = today
            h["flip_log"].append(f"{today}: ON (count={count}, streak_on={h['streak_on']})")
            log.info("HUB FLIP ON: %s (count=%d, streak_on=%d)", hub_file, count, h["streak_on"])

        # Flip OFF: 7 consecutive runs < 8
        if currently_indexable and h["streak_off"] >= HUB_OFF_STREAK_N:
            h["indexable"] = False
            h["last_flip"] = today
            h["flip_log"].append(f"{today}: OFF (count={count}, streak_off={h['streak_off']})")
            log.warning("HUB FLIP OFF: %s (count=%d, streak_off=%d)", hub_file, count, h["streak_off"])

        indexable[hub_file] = h["indexable"]

    # A2 duplicate-hub rule: state hub forced noindex only if city hub is indexable or flipping ON
    DUPLICATE_PAIRS = [
        ("esg-sustainability-jobs-karnataka.html", "esg-jobs-bangalore.html"),
        ("esg-sustainability-jobs-maharashtra.html", "esg-jobs-mumbai.html"),
    ]

    for state_hub, city_hub in DUPLICATE_PAIRS:
        if state_hub not in indexable or city_hub not in indexable:
            continue
        state_idx = indexable[state_hub]
        city_idx = indexable[city_hub]
        city_flipping_on = (not hubs_state[city_hub]["indexable"]) and hubs_state[city_hub]["streak_on"] >= HUB_ON_STREAK_N

        if state_idx and (city_idx or city_flipping_on):
            # State hub is indexable but city hub is (or will be) indexable -> force state to noindex
            log.warning(
                "DUPLICATE RULE: %s forced noindex (city hub %s indexable=%s, flipping=%s)",
                state_hub, city_hub, city_idx, city_flipping_on
            )
            hubs_state[state_hub]["indexable"] = False
            hubs_state[state_hub]["flip_log"].append(f"{today}: DUPLICATE RULE OFF (city={city_hub})")
            indexable[state_hub] = False
        elif state_idx and not city_idx and not city_flipping_on:
            # State hub indexable, city hub scaffolded -> state hub allowed to stay indexable
            log.info(
                "DUPLICATE RULE: %s allowed (city hub %s scaffolded)",
                state_hub, city_hub
            )

    state["last_run_date"] = today
    save_hub_streak_state(state)
    return indexable


def ist_today() -> date:
    return datetime.now(IST).date()


def touch_stats_ist(public: Path) -> None:
    """Stamp stats.json with the current IST date on every SEO rebuild.

    The pipeline already writes these fields, but a maintenance-only build or
    a zero-new-jobs morning must still move the visible "last updated" date.
    Existing telemetry and broadcast rotation history are preserved verbatim.
    """
    path = public / "stats.json"
    if not path.exists():
        return
    try:
        stats = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(stats, dict):
        return
    now_ist = datetime.now(IST)
    stats["last_updated"] = now_ist.isoformat(timespec="seconds")
    stats["last_updated_ist"] = now_ist.isoformat(timespec="seconds")
    stats["last_pipeline_run_date_ist"] = now_ist.date().isoformat()
    path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info(
        "Stamped %s with IST date %s", path, stats["last_pipeline_run_date_ist"]
    )


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
                LINKEDIN_GROUP_URL,
                FACEBOOK_PAGE_URL,
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
    ("Email Job Alert Archive", "/newsletter_latest.html"),
    ("Email Alert Preferences", "/unsubscribe.html"),
    ("Report an Issue", "/report.html"),
]

def state_slug(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", plain(label).lower()).strip("-")


# Contextual state gateways keep every major state within two clicks of the
# homepage. They point at stable anchors on the regional portal, never at a
# query-string filter.
TOP_STATE_LINKS: List[Tuple[str, str]] = [
    (label, f"/bharat-regional-green-jobs#state-{state_slug(label)}")
    for label in (
        "Uttar Pradesh",
        "Maharashtra",
        "Delhi NCR",
        "Karnataka",
        "Tamil Nadu",
        "Madhya Pradesh",
        "Rajasthan",
        "Gujarat",
        "Telangana",
        "Uttarakhand",
        "West Bengal",
        "Bihar",
        "Kerala",
        "Punjab",
        "Odisha",
        "Assam",
        "Himachal Pradesh",
        "Jharkhand",
        "Chhattisgarh",
        "Andhra Pradesh",
        "Goa",
        "Meghalaya",
        "Nagaland",
        "Tripura",
        "Manipur",
        "Arunachal Pradesh",
    )
]


def site_matrix_html(current_path: str = "", include_states: bool = True) -> str:
    """Compact crawlable portal directory used on the homepage and every hub."""
    portals = [
        ("India career registry", "/"),
        ("Global career opportunities", "/global-climate-sustainability-opportunities"),
        ("Hindi environment jobs", "/hindi-environment-forestry-jobs"),
        ("State &amp; language portals", "/bharat-regional-green-jobs"),
        ("About this registry", "/about"),
    ]
    items = []
    for label, href in portals:
        if href == current_path:
            items.append(f'<li><span aria-current="page">{label}</span></li>')
        else:
            items.append(f'<li><a href="{href}">{label}</a></li>')
    state_items = ""
    if include_states and current_path != "/bharat-regional-green-jobs":
        state_items = "".join(
            f'<li><a href="{href}">{esc(label)} jobs</a></li>'
            for label, href in TOP_STATE_LINKS[:4]
        )
    state_block = (
        f"""      <p class="site-matrix-sub">State gateways</p>
      <ul class="site-matrix-list site-matrix-states">
        {state_items}
      </ul>"""
        if state_items
        else ""
    )
    return f"""  <section class="site-matrix" aria-labelledby="site-matrix-title">
    <div class="site-matrix-inner">
      <p class="eyebrow">National &amp; Global Career Pathways</p>
      <h2 id="site-matrix-title">National &amp; Global Career Pathways &amp; Research Hubs</h2>
      <p class="site-matrix-sub">A short directory of the registry, language portals, state gateways and editorial pages.</p>
      <ul class="site-matrix-list">
        {''.join(items)}
      </ul>
{state_block}
    </div>
  </section>"""


def compact_site_matrix_html(current_path: str = "") -> str:
    """Footer-level fallback for legacy static pages outside the hub generator."""
    portals = [
        ("India career registry", "/"),
        ("Global career opportunities", "/global-climate-sustainability-opportunities"),
        ("Hindi environment jobs", "/hindi-environment-forestry-jobs"),
        ("State &amp; language portals", "/bharat-regional-green-jobs"),
        ("About this registry", "/about"),
    ]
    items = []
    for label, href in portals:
        if href == current_path:
            items.append(f'<li><span aria-current="page">{label}</span></li>')
        else:
            items.append(f'<li><a href="{href}">{label}</a></li>')
    state_items = "".join(
        f'<li><a href="{href}">{esc(label)} jobs</a></li>'
        for label, href in TOP_STATE_LINKS[:4]
    )
    return f"""<nav class="ufp-site-matrix" aria-labelledby="ufp-site-matrix-title" style="max-width:1240px;margin:0 auto;padding:22px 18px 28px;font-family:Inter,system-ui,sans-serif;color:#334155;border-top:1px solid #E2E8F0;background:#F8FAFC;">
  <h2 id="ufp-site-matrix-title" style="font-size:15px;margin:0 0 10px;color:#0F172A;">National &amp; Global Career Pathways &amp; Research Hubs</h2>
  <ul style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:6px 20px;list-style:none;padding:0;margin:0;font-size:12.5px;line-height:1.55;">
    {''.join(items)}
  </ul>
  <p style="font-size:13px;font-weight:700;margin:16px 0 6px;">State gateways</p>
  <ul style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:6px 20px;list-style:none;padding:0;margin:0;font-size:12.5px;line-height:1.55;">
    {state_items}
  </ul>
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


# --------------------------------------------------------------------------
# Additional hub matchers (sustainability, freshers, entry-level, remote, Delhi NCR, state/city)
# --------------------------------------------------------------------------
SUSTAINABILITY_CATEGORIES = {
    "ESG, Carbon Markets & Corporate Sustainability",
    "Climate Policy, Think-Tanks & Fellowships",
    "Forestry, Wildlife & Afforestation",
}


def is_job_listing(job: Dict[str, Any]) -> bool:
    """True for job/fellowship records, false for course and award portals."""
    return str(job.get("entry_type") or "posting") != "award_portal"


def is_entry_level(job: Dict[str, Any]) -> bool:
    return "entry level" in plain(job.get("experience_level")).lower()


def is_remote_job(job: Dict[str, Any]) -> bool:
    location = " ".join(
        plain(job.get(key)) for key in ("city", "state", "region", "country")
    ).lower()
    return "remote" in location


def matching_text(job: Dict[str, Any]) -> str:
    return " ".join(
        [
            searchable_text(job),
            plain(job.get("category")),
            plain(job.get("role_summary")),
        ]
    )


# Deny list for irrelevant roles (B2)
DENY_PATTERNS = re.compile(
    r"\b(mechanical|civil|process|design|structural|electrical|software)\s*engineer\b|"
    r"\bbuilding\s*automation\b|"
    r"\bsupplier\s*compliance\b|"
    r"\bai\s*training\b|\bdata\s*labelling\b|"
    r"\beditorial\s*review\b|"
    r"\bsales\b|\bbusiness\s*development\b|\bmarketing\b",
    re.I,
)


def is_relevant_sustainability(job: Dict[str, Any]) -> bool:
    """Check if job is plainly sustainability/climate/ESG/environment work."""
    text = matching_text(job)
    if DENY_PATTERNS.search(text):
        return False
    return plain(job.get("category")) in SUSTAINABILITY_CATEGORIES


def match_sustainability(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    return is_relevant_sustainability(job)


def match_esg_fresher(job: Dict[str, Any]) -> bool:
    if not (is_job_listing(job) and is_entry_level(job)):
        return False
    if plain(job.get("position_type")) in ("PhD / Doctoral Fellowship", "Postdoctoral Fellowship"):
        return False
    return (
        job.get("category") == "ESG, Carbon Markets & Corporate Sustainability"
        or bool(ESG_FRESH_RE.search(matching_text(job)))
    )


def match_entry_environment(job: Dict[str, Any]) -> bool:
    if not (is_job_listing(job) and is_entry_level(job)):
        return False
    if plain(job.get("position_type")) in ("PhD / Doctoral Fellowship", "Postdoctoral Fellowship"):
        return False
    return is_relevant_sustainability(job)


def match_remote_environment(job: Dict[str, Any]) -> bool:
    if not (is_job_listing(job) and is_remote_job(job)):
        return False
    return is_relevant_sustainability(job)


def match_delhi_ncr(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    state = plain(job.get("state")).lower()
    return "delhi" in state or "ncr" in state


def match_karnataka(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    state = plain(job.get("state")).lower()
    return "karnataka" in state


def match_maharashtra(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    state = plain(job.get("state")).lower()
    return "maharashtra" in state


def match_bangalore(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    city = plain(job.get("city")).lower()
    return "bengaluru" in city or "bangalore" in city


def match_mumbai(job: Dict[str, Any]) -> bool:
    if not is_job_listing(job):
        return False
    city = plain(job.get("city")).lower()
    return "mumbai" in city


ESG_FRESH_RE = re.compile(
    r"\besg\b|sustainab|carbon|brsr|climate finance|corporate social|"
    r"climate policy|renewable|energy transition",
    re.I,
)


HUBS: List[Dict[str, Any]] = [
    {
        "file": "jrf-srf-project-associate-jobs.html",
        "match": match_research,
        "kicker": "Academic & Research Track",
        "title": "Verified JRF / SRF & Project Associate Jobs in India 2026",
        "h1": "Verified JRF / SRF & Project Associate Jobs in India 2026",
        "desc": (
            "Verified Junior Research Fellow (JRF), Senior Research Fellow (SRF), Research "
            "Associate and Project Associate vacancies across Indian universities, IITs, IISc, "
            "CSIR institutes and government research bodies \u2014 updated daily with direct "
            "application links."
        ),
        "hero_sub": (
            "Every JRF, SRF, research associate and project associate job currently tracked "
            "by the Urban Forest Park registry \u2014 sourced from official university, institute "
            "and government portals across India."
        ),
        "list_copy": (
            "Junior Research Fellow (JRF), Senior Research Fellow (SRF), Research Associate and "
            "Project Associate positions in environmental science, forestry, ecology, climate "
            "change, sustainability, agriculture and allied disciplines. Each listing links "
            "straight to the official advertisement and application portal."
        ),
        "cta_href": "/#filter-bar",
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
        "title": "Verified PhD Climate & Ecology Fellowships in India 2026",
        "h1": "Verified PhD Climate & Ecology Fellowships in India 2026",
        "desc": (
            "Doctoral fellowships, PhD positions and postdoctoral vacancies in climate change, "
            "sustainability, ecology and environmental science at IITs, IISc, central universities "
            "and research institutes across India."
        ),
        "hero_sub": (
            "Doctoral programmes, PhD fellowships and postdoctoral positions in climate, ecology, "
            "sustainability and environmental science \u2014 every listing links to the official "
            "institute portal."
        ),
        "list_copy": (
            "PhD admissions with funding, doctoral fellowships and postdoctoral positions in "
            "climate dynamics, earth-system modelling, environmental sustainability, ecological "
            "sciences and allied fields at Indian institutes of national importance and research "
            "organisations."
        ),
        "cta_href": "/#filter-bar",
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
                "Postdoctoral positions at IITs, IISc and national institutes are added as they "
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
        "title": "Government Forestry, CAMPA, FSI & SPCB Jobs in India 2026",
        "h1": "Government Forestry, CAMPA, FSI & SPCB Jobs in India 2026",
        "desc": (
            "Forest guard, forester, RFO, ACF and IFS recruitment plus forest department, "
            "wildlife institute, ICFRE and environment ministry vacancies across India \u2014 "
            "research positions, young-professional jobs and contractual roles with "
            "direct application links."
        ),
        "hero_sub": (
            "Forest guard, forester, RFO, ACF and IFS recruitment, plus forestry, wildlife, "
            "conservation and environment-ministry jobs across Indian states. Filter "
            "state-wise links below for local forest department notices."
        ),
        "list_copy": (
            "Vacancies with state forest departments, the Wildlife Institute of India, ICFRE "
            "institutes, SACON, the environment ministry and conservation organisations \u2014 "
            "covering forest guard and forester recruitment, RFO / ACF / IFS notifications, "
            "afforestation, wildlife biology, ecology and habitat management. Use the "
            "state-wise filter to narrow the registry to your state."
        ),
        "cta_href": "/#filter-bar",
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
        "title": "GIS, Remote Sensing & Earth Observation Jobs in India 2026",
        "h1": "GIS, Remote Sensing & Earth Observation Jobs in India 2026",
        "desc": (
            "GIS analyst, remote sensing, geospatial and earth observation vacancies across ISRO "
            "centres, environmental institutes, urban planning bodies and consultancies in India "
            "\u2014 updated daily."
        ),
        "hero_sub": (
            "Geospatial analyst, remote sensing, earth observation and urban heat-island jobs "
            "with ISRO / NRSC, research institutes, urban bodies and consultancies across India."
        ),
        "list_copy": (
            "GIS, remote sensing and earth-observation positions spanning geospatial modelling, "
            "satellite data analysis, urban heat-island mapping, land-use change and spatial "
            "planning \u2014 each with a direct application link."
        ),
        "cta_href": "/#filter-bar",
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
                "climate-mapping jobs with institutes and municipal programmes appear under "
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
        "title": "ESG, Carbon Markets & Corporate Sustainability Jobs 2026",
        "h1": "ESG, Carbon Markets & Corporate Sustainability Jobs 2026",
        "desc": (
            "ESG analyst, sustainability manager, carbon market, climate finance and corporate "
            "sustainability vacancies across Indian companies, consultancies and NGOs \u2014 "
            "verified and updated daily."
        ),
        "hero_sub": (
            "ESG analyst, sustainability manager, carbon-market and climate-finance jobs "
            "across corporate India, consultancies and development organisations."
        ),
        "list_copy": (
            "Corporate sustainability and ESG positions \u2014 ESG analysis and reporting, BRSR "
            "disclosure, carbon accounting and markets, climate risk and climate finance "
            "\u2014 from companies, consultancies, rating agencies and NGOs. Every listing links "
            "to the official careers portal."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG and sustainability",
        "faqs": [
            (
                "What ESG and sustainability roles are in demand in India?",
                "ESG analyst and reporting roles, BRSR / sustainability disclosure specialists, "
                "carbon accounting and assurance, climate-risk modelling, climate finance and "
                "corporate sustainability manager positions are among the fastest-growing "
                "jobs \u2014 alongside environmental and social impact roles at development "
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
                "Yes \u2014 BRSR reporting, climate disclosure and assurance jobs are tracked "
                "under this pathway, alongside environmental compliance and EHS sustainability "
                "roles where they carry a climate / ESG remit.",
            ),
            (
                "How does the registry verify corporate ESG vacancies?",
                "Corporate roles are collected from official company career portals and verified "
                "job feeds, then normalised, de-duplicated and linked directly to the employer's "
                "application page. Closed jobs move to the Historical Archive for reference.",
            ),
        ],
    },
    {
        "file": "sustainability-jobs-india.html",
        "match": match_sustainability,
        "kicker": "Sustainability & Climate Track",
        "title": "Verified Sustainability Jobs in India 2026",
        "h1": "Verified Sustainability Jobs in India 2026 — Forestry, Climate Policy & ESG",
        "desc": (
            "Verified sustainability, forestry, climate policy and ESG jobs across India — "
            "from forest departments and research institutes to corporate ESG teams and climate consultancies."
        ),
        "hero_sub": (
            "India's broadest sustainability job hub: forestry & conservation, climate policy & research, "
            "corporate ESG & carbon — every listing links to the official source."
        ),
        "list_copy": (
            "Sustainability jobs across the full spectrum: forest departments, research institutes, "
            "climate think-tanks, corporate ESG teams, carbon consultancies and multilateral organisations. "
            "Each listing links to the official application page."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "sustainability and climate",
        "faqs": [
            (
                "What counts as a sustainability job?",
                "Any role that advances environmental, climate or sustainability outcomes — "
                "from forest rangers and conservation researchers to ESG analysts and carbon consultants."
            ),
            (
                "How does this differ from the ESG hub?",
                "The ESG hub covers corporate reporting, carbon markets and sustainability disclosure. "
                "This hub is broader: it adds forestry, conservation, climate policy and research roles. "
                "For purely corporate ESG roles, see the ESG hub."
            ),
            (
                "Are government forestry jobs included?",
                "Yes — forest guard, RFO, ACF and research roles from state forest departments, ICFRE and WII. "
                "For a pure government/forestry view, see the Government & Forestry hub."
            ),
            (
                "Can freshers find sustainability jobs here?",
                "Yes — JRF, project associate and research intern roles appear here. "
                "For a dedicated fresher view, see the ESG Jobs for Freshers hub."
            ),
        ],
    },
    {
        "file": "esg-jobs-for-freshers.html",
        "match": match_esg_fresher,
        "kicker": "Early-Career ESG Track",
        "title": "ESG Jobs for Freshers in India 2026",
        "h1": "ESG Jobs for Freshers in India 2026 — Entry-Level Roles",
        "desc": (
            "Verified entry-level ESG, carbon and sustainability roles for fresh graduates — "
            "analyst, reporting, research and associate positions with direct application links."
        ),
        "hero_sub": (
            "ESG jobs for freshers: analyst, reporting, carbon and research roles — "
            "no experience required, direct links to employer portals."
        ),
        "list_copy": (
            "Entry-level ESG and sustainability roles: analyst, reporting associate, carbon analyst, "
            "research intern. Each listing states the experience band and links to the official application page."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG fresher and entry-level",
        "faqs": [
            (
                "Can freshers apply for ESG jobs?",
                "Yes — many ESG analyst, reporting associate and carbon analyst roles accept fresh graduates. "
                "Internships, research projects and relevant coursework help."
            ),
            (
                "What skills do ESG freshers need?",
                "Basic sustainability literacy, Excel/data skills, research ability and clear writing. "
                "Coursework in environmental science, economics or engineering is a plus."
            ),
            (
                "Where are fresher ESG jobs posted?",
                "Corporate career pages, consultancy graduate programmes, think-tank internships "
                "and the ESG hub's fresher filter."
            ),
            (
                "How does this differ from the Entry-Level Environmental hub?",
                "This hub is ESG-only (corporate reporting, carbon, sustainability disclosure). "
                "The Entry-Level Environmental hub is broader: JRF, field research, GIS, forestry, etc."
            ),
        ],
    },
    {
        "file": "entry-level-environmental-jobs.html",
        "match": match_entry_environment,
        "kicker": "Entry-Level Environmental Track",
        "title": "Entry Level Environmental Jobs in India 2026",
        "h1": "Entry Level Environmental Jobs in India 2026 — JRF, Field & Research",
        "desc": (
            "Verified entry-level environmental, forestry, GIS and research jobs across India — "
            "JRF, project associate, field assistant, GIS intern roles with direct application links."
        ),
        "hero_sub": (
            "Entry-level environmental jobs: JRF, project associate, field assistant, GIS intern — "
            "zero to two years experience, direct links to official sources."
        ),
        "list_copy": (
            "Zero-to-two-year environmental roles: JRF, project associate, field assistant, "
            "GIS intern, research intern. Each listing links to the official application page."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "entry-level environmental",
        "faqs": [
            (
                "What entry-level environmental jobs exist?",
                "JRF, project associate, field assistant, GIS intern, research intern, "
                "young professional and conservation trainee roles."
            ),
            (
                "Do I need a Master's degree?",
                "JRF typically requires M.Sc. + NET/GATE. Project associate and field roles "
                "may accept B.Sc./B.Tech. Check each listing."
            ),
            (
                "Where are the field jobs?",
                "Forest departments, WII, SACON, ATREE, research institutes and NGOs "
                "post field roles across India — filter by state in the live registry."
            ),
            (
                "How does this differ from the ESG Freshers hub?",
                "This hub covers JRF, field research, GIS, forestry, conservation. "
                "The ESG Freshers hub is corporate-only: ESG analyst, carbon, reporting."
            ),
        ],
    },
    {
        "file": "remote-environmental-jobs.html",
        "match": match_remote_environment,
        "kicker": "Remote & Hybrid Track",
        "title": "Remote Environmental & Climate Jobs in India 2026",
        "h1": "Remote Environmental & Climate Jobs in India 2026 — Work from Anywhere",
        "desc": (
            "Verified remote and hybrid environmental, climate, ESG and GIS jobs — "
            "work from anywhere in India with direct application links."
        ),
        "hero_sub": (
            "Remote environmental jobs: research, ESG, climate policy, GIS — "
            "work from anywhere in India, direct links to employers."
        ),
        "list_copy": (
            "Remote and hybrid roles: research, ESG reporting, climate policy, GIS, "
            "carbon analysis — work from anywhere in India, direct employer links."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "remote environmental and climate",
        "faqs": [
            (
                "Are remote environmental jobs common?",
                "Yes — research, ESG reporting, climate policy and GIS roles often offer remote/hybrid. "
                "Field and lab roles typically require on-site presence."
            ),
            (
                "How do I verify a remote job?",
                "Check the employer's official career page. The registry links directly to the source. "
                "Beware of jobs asking for upfront fees — the registry never charges candidates."
            ),
            (
                "Can freshers get remote roles?",
                "Some research intern and ESG reporting roles offer remote options for freshers. "
                "Filter by experience level in the live registry."
            ),
        ],
    },
    {
        "file": "esg-sustainability-jobs-delhi-ncr.html",
        "match": match_delhi_ncr,
        "kicker": "Delhi NCR ESG & Sustainability Track",
        "title": "ESG & Sustainability Jobs in Delhi NCR 2026",
        "h1": "ESG & Sustainability Jobs in Delhi NCR 2026 — Gurugram, Noida, Faridabad",
        "desc": (
            "Verified ESG, sustainability and climate jobs across Delhi, Gurugram, Noida, "
            "Faridabad and Ghaziabad — corporate, consulting, multilateral and government roles."
        ),
        "hero_sub": (
            "Delhi NCR ESG jobs: Gurugram corporate hubs, Noida tech parks, "
            "Delhi multilateral hubs — direct links to official sources."
        ),
        "list_copy": (
            "ESG analyst, sustainability manager, climate finance, multilateral and government roles "
            "across Delhi, Gurugram, Noida, Faridabad, Ghaziabad. Direct links to official sources."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG and sustainability in Delhi NCR",
        "faqs": [
            (
                "Which NCR cities have the most ESG jobs?",
                "Gurugram leads (corporate HQs), followed by Noida (tech/consulting), "
                "Delhi (multilaterals/government), Faridabad/Ghaziabad (industrial)."
            ),
            (
                "Are there government ESG jobs in Delhi NCR?",
                "Yes — MoEFCC, CPCB, CAMPA and state bodies post Young Professional and "
                "consultant roles for climate finance and ESG."
            ),
            (
                "How does this differ from the national ESG hub?",
                "This hub is geography-filtered to Delhi NCR only. "
                "For all-India ESG roles, see the ESG & Carbon hub."
            ),
        ],
    },
    {
        "file": "esg-sustainability-jobs-karnataka.html",
        "match": match_karnataka,
        "kicker": "Karnataka ESG & Sustainability Track",
        "title": "Verified ESG & Sustainability Jobs in Karnataka 2026",
        "h1": "Verified ESG & Sustainability Jobs in Karnataka 2026 — Bengaluru & Beyond",
        "desc": (
            "Verified ESG, sustainability and climate jobs across Karnataka — "
            "Bengaluru's corporate hub, research institutes and emerging districts."
        ),
        "hero_sub": (
            "Karnataka ESG jobs: Bengaluru's corporate hub, IISc/IISc-adjacent research, "
            "emerging districts — direct links to official sources."
        ),
        "list_copy": (
            "ESG analyst, sustainability manager, climate researcher, carbon consultant "
            "across Bengaluru and Karnataka — direct links to official sources."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG and sustainability in Karnataka",
        "faqs": [
            (
                "Is this hub currently live?",
                "This hub is scaffolded and will publish when Karnataka reaches 12+ active roles "
                "for 3 consecutive pipeline runs. Current count is below threshold."
            ),
            (
                "How does this differ from the Bangalore city hub?",
                "This hub covers the entire state (Bengaluru + other districts). "
                "The Bangalore hub is city-specific."
            ),
        ],
    },
    {
        "file": "esg-jobs-bangalore.html",
        "match": match_bangalore,
        "kicker": "Bengaluru ESG Track",
        "title": "Verified ESG Jobs in Bengaluru 2026",
        "h1": "Verified ESG Jobs in Bengaluru 2026 — India's ESG Capital",
        "desc": (
            "Verified ESG jobs in Bengaluru — India's deepest corporate ESG hub "
            "with GCCs, climate tech startups and consultancies."
        ),
        "hero_sub": (
            "Bengaluru ESG jobs: GCCs, climate tech, consultancies — "
            "India's densest ESG market, direct links to official sources."
        ),
        "list_copy": (
            "ESG analyst, sustainability manager, carbon analyst, climate tech roles "
            "across Bengaluru's GCCs, startups and consultancies — direct official links."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG jobs in Bengaluru",
        "faqs": [
            (
                "Is this hub currently live?",
                "This hub is scaffolded and will publish when Bengaluru reaches 12+ active ESG roles "
                "for 3 consecutive pipeline runs. Current count is below threshold."
            ),
            (
                "How does this differ from the Karnataka hub?",
                "This hub is city-specific (Bengaluru only). "
                "The Karnataka hub covers the entire state."
            ),
        ],
    },
    {
        "file": "esg-sustainability-jobs-maharashtra.html",
        "match": match_maharashtra,
        "kicker": "Maharashtra ESG & Sustainability Track",
        "title": "Verified ESG & Sustainability Jobs in Maharashtra 2026",
        "h1": "Verified ESG & Sustainability Jobs in Maharashtra 2026 — Mumbai, Pune & Beyond",
        "desc": (
            "Verified ESG, sustainability and climate jobs across Maharashtra — "
            "Mumbai's finance hub, Pune's research/tech, Thane's industrial corridor."
        ),
        "hero_sub": (
            "Maharashtra ESG jobs: Mumbai finance, Pune research, Thane industry — "
            "direct links to official sources."
        ),
        "list_copy": (
            "ESG analyst, sustainability manager, climate finance, carbon consultant "
            "across Mumbai, Pune, Thane, Navi Mumbai — direct official links."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG and sustainability in Maharashtra",
        "faqs": [
            (
                "Is this hub currently live?",
                "This hub is scaffolded and will publish when Maharashtra reaches 12+ active roles "
                "for 3 consecutive pipeline runs. Current count is below threshold."
            ),
            (
                "How does this differ from the Mumbai city hub?",
                "This hub covers the entire state (Mumbai + Pune + Thane + other districts). "
                "The Mumbai hub is city-specific."
            ),
        ],
    },
    {
        "file": "esg-jobs-mumbai.html",
        "match": match_mumbai,
        "kicker": "Mumbai ESG Track",
        "title": "Verified ESG Jobs in Mumbai 2026",
        "h1": "Verified ESG Jobs in Mumbai 2026 — Finance, Corporate & Climate",
        "desc": (
            "Verified ESG jobs in Mumbai — India's financial capital with "
            "corporate HQs, consultancies and climate finance firms."
        ),
        "hero_sub": (
            "Mumbai ESG jobs: finance HQs, Big 4, climate finance, corporate HQs — "
            "direct links to official sources."
        ),
        "list_copy": (
            "ESG analyst, sustainability manager, climate finance, carbon consultant "
            "across Mumbai — direct links to official sources."
        ),
        "cta_href": "/#filter-bar",
        "matched_noun": "ESG jobs in Mumbai",
        "faqs": [
            (
                "Is this hub currently live?",
                "This hub is scaffolded and will publish when Mumbai reaches 12+ active ESG roles "
                "for 3 consecutive pipeline runs. Current count is below threshold."
            ),
            (
                "How does this differ from the Maharashtra hub?",
                "This hub is city-specific (Mumbai only). "
                "The Maharashtra hub covers the entire state."
            ),
        ]
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
        if not isinstance(entry, dict):
            continue
        # Quarantined records are kept in the data files but never rendered.
        # Records with no classifiable entry type are hidden by placement policy.
        if entry.get("status") == "quarantined":
            continue
        if str(entry.get("entry_type") or "posting") == "unknown":
            continue
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
        <span class="brand-sub">Green Jobs &amp; Research Registry</span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="Primary">
        <a class="{cls('registry')}" href="/">Career Registry</a>
        <a class="{cls('archive')}" href="/?view=archive" rel="nofollow">Historical Archive</a>
        <a class="{cls('global')}" href="/global-climate-sustainability-opportunities">Global Opportunities</a>
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


def footer_social_html() -> str:
    """Official social/community bar shared by every generated page."""
    return f"""    <div class="footer-social" aria-label="Official social and community profiles">
      <span class="footer-social-label">Official communities</span>
      <div class="footer-social-links">
        <a href="{LINKEDIN_GROUP_URL}" target="_blank" rel="noopener noreferrer"
           aria-label="Join the official Urban Forest Park LinkedIn Group (opens in a new tab)">LinkedIn Group <span aria-hidden="true">&nearr;</span></a>
        <a href="{FACEBOOK_PAGE_URL}" target="_blank" rel="noopener noreferrer"
           aria-label="Follow the official Urban Forest Park Facebook page (opens in a new tab)">Facebook <span aria-hidden="true">&nearr;</span></a>
      </div>
    </div>"""


def footer_html(current_hub: Optional[str] = None) -> str:
    return f"""  <footer class="site-footer">
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Urban Forest Park</h3>
        <p>
          Verified green jobs, research fellowships and climate careers in India and worldwide.
          Every listing links to the official application source.
        </p>
        <p style="margin-top:10px;">
          Also home of the <a href="/dashboard">Nagar Van dMRV Dashboard</a>.
        </p>
      </div>

      <div class="footer-col">
        <h3>Registry</h3>
        <ul>
          <li><a href="/">All active opportunities</a></li>
          <li><a href="/#pathway-title">Career pathway hubs</a></li>
          <li><a href="/?view=archive" rel="nofollow">Archived jobs</a></li>
          <li><a href="/global-climate-sustainability-opportunities">International opportunities</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>Institutional Tools</h3>
        <ul>
          <li><a href="/dashboard">Live dMRV dashboard</a></li>
          <li><a href="/green-calculator">Green Calculator</a></li>
          <li><a href="/nagar-van-finder">Nagar Van Finder</a></li>
          <li><a href="/green-calculator-app">Calculator app</a></li>
          <li><a href="/green-calculator-report">Impact report</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>Legal &amp; Contact</h3>
        <ul>
          <li><a href="/about">About Urban Forest Park</a></li>
          <li><a href="/privacy">Privacy policy</a></li>
          <li><a href="/terms">Terms of use</a></li>
          <li><a href="/report">Report an issue</a></li>
          <li><a href="mailto:urbanforestpark@gmail.com">Contact the registry</a></li>
          <li><button type="button" class="footer-link-btn" data-syndication-open title="Internal broadcast &amp; backlink workspace (Ctrl+Shift+U)">Syndication desk</button></li>
        </ul>
      </div>
    </div>

{footer_social_html()}

    <div class="footer-bottom">
      &copy; {ist_today().year} Urban Forest Park<span class="dot">&bull;</span>Green Jobs &amp; Research Registry (India)
      <span class="dot">&bull;</span>Verify details on the official application page.
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
    title = plain(job.get("clean_title")) or plain(job.get("organization")) or "Untitled job"
    org = plain(job.get("organization"))
    label = f"{title} \u2014 {org} ({state_label(job)} | {position_type_of(job)})"
    return f'            <li><a href="{job_url(job)}">{esc(label)}</a></li>'


def build_index_block(
    active: List[Dict[str, Any]],
    archived: List[Dict[str, Any]],
    today: date,
) -> str:
    """A compact, crawlable link bar to the five static career hubs.

    The old block dumped every active and recently archived job into the
    homepage. That produced thousands of words, duplicate anchor text and a
    large repeated job-card boilerplate. Crawlers now reach each job through
    its hub page and the sitemap instead.
    """
    hubs = [
        ("jrf-srf-project-associate-jobs", "JRF, SRF & project associate jobs"),
        ("phd-fellowships-climate-sustainability", "PhD & postdoctoral fellowships"),
        ("forestry-wildlife-government-jobs", "Forestry, wildlife & government jobs"),
        ("gis-remote-sensing-climate-jobs", "GIS, remote sensing & earth observation"),
        ("esg-carbon-sustainability-jobs", "ESG, carbon markets & sustainability"),
    ]
    hub_items = "\n".join(
        f'        <li><a href="/{href}">{esc(label)}</a></li>' for href, label in hubs
    )
    updated = long_date(today)
    return f"""{SNAPSHOT_START}
    <section class="seo-prerendered hub-summary" aria-labelledby="seo-pr-title">
      <div class="seo-pr-inner">
        <p class="eyebrow">Career Pathway Hubs</p>
        <h2 id="seo-pr-title">Browse Green Jobs by Career Pathway</h2>
        <p class="seo-pr-intro">Registry last refreshed on {updated} IST. New verified roles are added every morning at 7 AM IST.</p>
        <ul class="hub-summary-grid">
{hub_items}
        </ul>
      </div>
    </section>
    {SNAPSHOT_END}"""


def job_slug(job: Dict[str, Any]) -> str:
    """Stable, URL-safe slug. Registry ids are already editorial slugs."""
    raw = plain(job.get("id")).lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", raw).strip("-")
    return slug or "job"


def job_url(job: Dict[str, Any], absolute: bool = False) -> str:
    path = "/jobs/" + job_slug(job)
    return (SITE + path) if absolute else path


def _hostname(url: str) -> str:
    try:
        from urllib.parse import urlparse
        host = urlparse(str(url or "")).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:  # noqa: BLE001
        return "official portal"


def _valid_through(job: Dict[str, Any]) -> str:
    explicit = plain(job.get("valid_through"))
    if explicit:
        return explicit[:10]
    added = plain(job.get("date_added"))
    try:
        return (date.fromisoformat(added[:10]) + timedelta(days=30)).isoformat()
    except Exception:  # noqa: BLE001
        return ""


def feed_card_html(job: Dict[str, Any], archived: bool = False) -> str:
    """Match the JavaScript card structure closely enough that hydration is a
    no-op visually, while keeping a real crawlable link even without JS.

    Only the heading is an anchor. The card remains clickable through
    ``data-href`` and the JavaScript card handler.
    """
    cat = plain(job.get("category")) or "Environmental Jobs"
    title = plain(job.get("clean_title")) or "Untitled job"
    org = plain(job.get("organization")) or "Organisation not specified"
    city = plain(job.get("city"))
    state = state_label(job)
    ptype = position_type_of(job)
    exp = plain(job.get("experience_level"))
    href = job_url(job)
    deadline = plain(job.get("deadline_or_window")) or "Rolling / Open"
    quals = plain(job.get("qualification_summary"))
    comp = plain(job.get("compensation_or_fellowship"))
    skills = [plain(item) for item in (job.get("must_have_skills") or []) if plain(item)][:3]
    loc = ", ".join(part for part in (city, state) if part and part not in ("India", "Global / Remote"))
    loc = loc or state or "India / Global"
    date_label = plain(job.get("date_added"))
    badges = [
        f'<span class="badge {cat_class(cat)}">{esc(cat)}</span>',
        f'<span class="badge badge-type">{esc(ptype)}</span>',
        f'<span class="badge badge-state">{PIN_SVG}{esc(state)}</span>',
    ]
    if exp:
        badges.append(f'<span class="badge badge-exp">{esc(exp)}</span>')
    if archived:
        badges.append('<span class="badge badge-archived">Archived</span>')

    rows = []
    if is_specific_qualification(quals):
        rows.append(
            f'<span class="jc-elig-item"><strong>Qualification:</strong> {esc(sentence(quals, 120))}</span>'
        )
    elif skills:
        focus = sentence(", ".join(skills) + (f" \u00b7 {loc}" if loc else ""))
        rows.append(f'<span class="jc-elig-item"><strong>Focus:</strong> {esc(focus)}</span>')
    if is_specific_compensation(comp):
        rows.append(
            f'<span class="jc-elig-item"><strong>Pay / fellowship:</strong> {esc(sentence(comp, 100))}</span>'
        )
    elig = '<div class="jc-eligibility">' + "".join(rows) + "</div>" if rows else ""

    skill_html = ""
    if skills:
        skill_html = '<div class="jc-skills">' + "".join(
            f'<span class="skill-chip">{esc(skill)}</span>' for skill in skills
        ) + CARD_STOP + "</div>"
    return f"""        <article class="job-card{' is-archived' if archived else ''}" data-id="{esc(job_slug(job))}" data-href="{href}" tabindex="0" role="group" aria-label="View job details: {esc(title)} at {esc(org)}">
          <div class="jc-top">{BADGE_SEP.join(badges)}{CARD_STOP}</div>
          <div class="jc-main">
            <div class="jc-main-text">
              <h3 class="jc-title"><a class="jc-title-link" href="{href}" title="{esc(title)}">{esc(anchor_text(title))}</a>{CARD_STOP}</h3>
              <p class="jc-org">{esc(sentence(org))}</p>
              <div class="jc-meta">
                <span>{PIN_SVG}{esc(sentence(loc))}</span>
                <span><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M7.5 3v4M16.5 3v4M3.5 10h17"/></svg>{esc(sentence(deadline))}</span>
              </div>
              {elig}
              {skill_html}
            </div>
          </div>
          <div class="jc-foot">
            <span class="jc-date">Added {esc(sentence(date_label))}</span>
            <span class="jc-view">View details. <span aria-hidden="true">&nearr;</span></span>
          </div>
        </article>"""


def build_job_feed_block(active: List[Dict[str, Any]]) -> str:
    ordered = sort_recent_first(active)[:PRERENDER_CARDS]
    cards = "\n".join(feed_card_html(job) for job in ordered)
    return f"""{JOB_FEED_START}
{cards}
{JOB_FEED_END}"""


def inject_job_feed(index_path: Path, block: str) -> None:
    text = index_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(JOB_FEED_START) + r".*?" + re.escape(JOB_FEED_END), re.S
    )
    count = len(pattern.findall(text))
    if count != 1:
        raise SystemExit(
            f"ERROR: expected exactly one {JOB_FEED_START} ... {JOB_FEED_END} block "
            f"in {index_path} (found {count})."
        )
    index_path.write_text(pattern.sub(lambda _m: block, text, count=1), encoding="utf-8")


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
    org_line = sentence(org_line)

    badges = [
        f'<span class="badge {cat_class(cat)}">{esc(cat)}</span>',
        f'<span class="badge badge-type">{esc(pt)}</span>',
        f'<span class="badge badge-state">{PIN_SVG}{esc(state)}</span>',
    ]
    if archived:
        closed_on = plain(job.get("date_archived")) or plain(job.get("valid_through"))
        badges.append(f'<span class="badge badge-archived">Closed {esc(closed_on)}</span>')

    skills = [plain(item) for item in (job.get("must_have_skills") or []) if plain(item)][:3]
    loc = ", ".join(part for part in (city, state) if part and part not in ("India", "Global / Remote"))
    loc = loc or state
    elig_bits = []
    quals = plain(job.get("qualification_summary"))
    comp = plain(job.get("compensation_or_fellowship"))
    if is_specific_qualification(quals):
        elig_bits.append(f"<span><strong>Qualification:</strong> {esc(sentence(quals, 140))}</span>")
    elif skills:
        focus = sentence(", ".join(skills) + (f" \u00b7 {loc}" if loc else ""))
        elig_bits.append(f"<span><strong>Focus:</strong> {esc(focus)}</span>")
    if is_specific_compensation(comp):
        elig_bits.append(f"<span><strong>Compensation:</strong> {esc(sentence(comp, 120))}</span>")
    elig_html = (
        '<p class="hub-card-elig">' + " ".join(elig_bits) + "</p>" if elig_bits else ""
    )

    summary = trim(job.get("role_summary"), 240)
    summary_html = f'<p class="hub-card-sum">{esc(sentence(summary))}</p>' if summary else ""
    title = plain(job.get("clean_title")) or org

    return f"""        <article class="hub-card{' hub-card-archived' if archived else ''}">
          <div class="hub-card-top">
            {BADGE_SEP.join(badges)}{CARD_STOP}
          </div>
          <h3 class="hub-card-title"><a href="{job_url(job)}" title="{esc(title)}">{esc(anchor_text(title))}</a>{CARD_STOP}</h3>
          <p class="hub-card-org">{esc(org_line)}</p>
          {elig_html}
          {summary_html}
          <p class="hub-card-foot"><span>View details. <span aria-hidden="true">&nearr;</span></span></p>
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
                "url": job_url(job, absolute=True),
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
        '        <p class="hub-empty">No jobs in this pathway right now \u2014 new openings '
        'are added daily. <a href="/">Browse the full registry</a>.</p>'
    )

    archive_block = ""
    if matched_archived:
        arch_cards = "\n".join(hub_card_html(j, archived=True) for j in matched_archived)
        archive_block = f"""      <section class="hub-archive" aria-labelledby="hub-archive-title">
        <h2 id="hub-archive-title">Recently Closed {esc(hub['matched_noun'])} jobs</h2>
        <p class="hub-archive-sub">Preserved for reference \u2014 compensation, eligibility and institutional history.</p>
        <div class="hub-list">
{arch_cards}
        </div>
      </section>"""

    other_links = "\n".join(
        f'          <li><a href="/{h["file"]}"><span class="hub-other-name">{esc(h["h1"])}</span>'
        f'<span class="hub-other-cnt">{all_hubs_counts.get(h["file"], 0)} active</span></a></li>'
        for h in HUBS
        if h["file"] != hub["file"] and h.get("_indexable", True)
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
    <meta name="robots" content="{'index, follow' if hub.get('_indexable', True) else 'noindex, follow'}">
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
          <a href="/">All jobs</a><span aria-hidden="true">/</span><span>{esc(hub['h1'])}</span>
        </nav>
        <p class="eyebrow">{esc(hub['kicker'])}</p>
        <h1>{esc(hub['h1'])}</h1>
        <p class="hub-hero-sub">{esc(hub['hero_sub'])}</p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="{hub['cta_href']}">Open in the live registry &rarr;</a>
          <a class="btn btn-outline" href="/?view=archive" rel="nofollow">Past deadlines</a>
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
          <h2>Active {esc(hub['matched_noun'])} jobs ({len(matched_active)})</h2>
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
            <p>The live registry carries every active job with state, sector and career-track filters \u2014 updated daily at 7 AM IST.</p>
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
# Static /jobs/<slug> detail pages
# --------------------------------------------------------------------------
CATEGORY_HUB_PATHS = {
    "Academic, JRF, SRF & PhD Positions": "/jrf-srf-project-associate-jobs",
    "Research Associate & Project Staff (Contractual)": "/jrf-srf-project-associate-jobs",
    "Forestry, Wildlife & Afforestation": "/forestry-wildlife-government-jobs",
    "GIS, Remote Sensing & Earth Observation": "/gis-remote-sensing-climate-jobs",
    "ESG, Carbon Markets & Corporate Sustainability": "/esg-carbon-sustainability-jobs",
    "Climate Policy, Think-Tanks & Fellowships": "/jrf-srf-project-associate-jobs",
}


def category_hub_path(category: Any) -> str:
    return CATEGORY_HUB_PATHS.get(plain(category), "/")


def job_page_title(job: Dict[str, Any]) -> str:
    title = plain(job.get("clean_title")) or "Environmental Job"
    org = plain(job.get("organization"))
    state = state_label(job)
    suffix = f" | {state} Job" if state and state not in ("India", "Global / Remote") else " | India Job"
    base = f"{title} at {org}" if org else title
    candidate = base + suffix
    if len(candidate) <= 70:
        return candidate
    return trim(base, 60)


def job_page_description(job: Dict[str, Any]) -> str:
    summary = plain(job.get("role_summary")) or plain(job.get("summary")) or ""
    if not summary:
        bits = [
            plain(job.get("clean_title")),
            "at",
            plain(job.get("organization")),
            "in",
            state_label(job),
            ".",
            "Eligibility, stipend, deadline and official application link.",
        ]
        summary = " ".join(bit for bit in bits if bit)
    return trim(summary, 158)


def _bullets(values: Any) -> str:
    if isinstance(values, str):
        items = [line.strip(" -•") for line in values.splitlines() if line.strip()]
    elif isinstance(values, list):
        items = [plain(item) for item in values if plain(item)]
    else:
        items = []
    if not items:
        return "<p>Details are stated in the official notification.</p>"
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def _job_location_text(job: Dict[str, Any]) -> str:
    parts = [plain(job.get("city")), plain(job.get("state")), plain(job.get("country"))]
    return ", ".join(part for part in parts if part) or plain(job.get("region")) or "India"


def job_posting_jsonld(job: Dict[str, Any], today: date) -> str:
    title = plain(job.get("clean_title"))
    org = plain(job.get("organization"))
    url = job_url(job, absolute=True)
    apply_url = plain(job.get("apply_url"))
    summary = plain(job.get("role_summary")) or plain(job.get("summary"))
    responsibilities = job.get("key_responsibilities") or []
    requirements = job.get("qualification_summary") or ""
    description_html = ""
    if summary:
        description_html += f"<p>{esc(summary)}</p>"
    if responsibilities:
        description_html += "<h3>Key responsibilities</h3>" + _bullets(responsibilities)
    if requirements:
        description_html += f"<h3>Eligibility</h3><p>{esc(requirements)}</p>"
    if not description_html:
        description_html = f"<p>{esc(title)} at {esc(org)}. See the official notification for full details.</p>"

    country = plain(job.get("country"))
    region = plain(job.get("region"))
    address_country = country if len(country) == 2 else ("IN" if not job.get("global") else country or "Global")
    location: Dict[str, Any] = {
        "@type": "Place",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": plain(job.get("city")) or region or "India",
            "addressRegion": plain(job.get("state")),
            "addressCountry": address_country,
        },
    }
    data: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "JobPosting",
        "title": title,
        "description": description_html,
        "datePosted": plain(job.get("date_added")) or today.isoformat(),
        "validThrough": _valid_through(job),
        "employmentType": plain(job.get("employment_type")) or "FULL_TIME",
        "hiringOrganization": {
            "@type": "Organization",
            "name": org,
            "sameAs": plain(job.get("org_website")) or None,
        },
        "jobLocation": location,
        "url": url,
        "directApply": False,
        "identifier": {
            "@type": "PropertyValue",
            "name": org,
            "value": job_slug(job),
        },
        "inLanguage": "en-IN",
    }
    if job.get("global") and ("remote" in region.lower() or "global" in region.lower()):
        data["jobLocationType"] = "TELECOMMUTE"
        data["applicantLocationRequirements"] = {
            "@type": "Country",
            "name": country or "Worldwide",
        }
    if job.get("deadline_or_window"):
        data["jobBenefits"] = plain(job.get("compensation_or_fellowship")) or None
    if not data["hiringOrganization"]["sameAs"]:
        data["hiringOrganization"].pop("sameAs", None)
    data = {key: value for key, value in data.items() if value is not None}
    return jsonld_script(data)


def related_jobs_for(
    job: Dict[str, Any], pool: List[Dict[str, Any]], limit: int = 5
) -> List[Dict[str, Any]]:
    own_id = job_slug(job)
    own_cat = plain(job.get("category"))
    own_state = plain(job.get("state"))
    own_org = plain(job.get("organization")).casefold()
    scored: List[Tuple[int, str, Dict[str, Any]]] = []
    for candidate in pool:
        if job_slug(candidate) == own_id:
            continue
        score = 0
        if plain(candidate.get("category")) == own_cat:
            score += 4
        if own_state and plain(candidate.get("state")) == own_state:
            score += 3
        if own_org and plain(candidate.get("organization")).casefold() == own_org:
            score -= 1
        if bool(candidate.get("global")) == bool(job.get("global")):
            score += 2
        text = " ".join(
            str(candidate.get(key) or "") for key in ("clean_title", "position_type", "category")
        ).casefold()
        title_tokens = {
            token for token in re.findall(r"[a-z]{4,}", plain(job.get("clean_title")).casefold())
            if token not in {"research", "project", "associate", "senior", "junior", "india"}
        }
        score += min(3, sum(1 for token in title_tokens if token in text))
        scored.append((score, str(candidate.get("date_added") or ""), candidate))
    scored.sort(key=lambda item: (-item[0], item[1]), reverse=False)
    return [item[2] for item in scored[:limit]]


def related_jobs_html(related: List[Dict[str, Any]]) -> str:
    if not related:
        return '<p class="job-page-note">No related listings at present. <a href="/">Browse the full registry</a>.</p>'
    cards = []
    for job in related:
        title = plain(job.get("clean_title")) or "Untitled job"
        related_meta = sentence(
            f"{plain(job.get('organization'))} \u00b7 {state_label(job)}"
        )
        cards.append(f"""          <article class="related-card">
            <span class="related-kicker">{esc(sentence(plain(job.get("category"))))}</span>
            <strong><a href="{job_url(job)}" title="{esc(title)}">{esc(anchor_text(title))}</a>{CARD_STOP}</strong>
            <span class="related-meta">{esc(related_meta)}</span>
          </article>""")
    return "\n".join(cards)


def build_job_page(
    job: Dict[str, Any],
    active: List[Dict[str, Any]],
    archived: List[Dict[str, Any]],
    today: date,
) -> str:
    slug = job_slug(job)
    canonical = job_url(job, absolute=True)
    is_archived = bool(job.get("date_archived")) or str(job.get("status")) == "archived"
    title = job_page_title(job)
    desc = job_page_description(job)
    job_title = plain(job.get("clean_title")) or "Environmental Job"
    org = plain(job.get("organization")) or "Organisation not specified"
    location = _job_location_text(job)
    apply_url = plain(job.get("apply_url"))
    website = plain(job.get("org_website"))
    deadline = plain(job.get("deadline_or_window")) or "Rolling / Open"
    posted = plain(job.get("date_added"))
    compensation = plain(job.get("compensation_or_fellowship")) or "As per official notification"
    qualification = plain(job.get("qualification_summary")) or "See official notification"
    summary = plain(job.get("role_summary")) or plain(job.get("summary")) or desc
    skills = [plain(item) for item in (job.get("must_have_skills") or []) if plain(item)]
    apply_label = f"Apply on {_hostname(apply_url)}" if apply_url else "Official application page"

    if is_archived:
        apply_block = f"""        <div class="job-page-archive-note">
          <strong>This position is closed.</strong> The application window has ended.
          The record is preserved for stipend, eligibility and institutional reference.
        </div>"""
    else:
        apply_block = f"""        <div class="job-page-actions">
          <a class="btn btn-primary" href="{esc(apply_url)}" target="_blank" rel="noopener noreferrer">{esc(apply_label)} &nearr;</a>"""

    if website:
        apply_block += f"""
          <a class="btn btn-outline" href="{esc(website)}" target="_blank" rel="noopener noreferrer">Official website &nearr;</a>"""
    if not is_archived:
        apply_block += """
        </div>"""

    related_pool = [j for j in active if job_slug(j) != slug]
    if is_archived:
        related_pool = [j for j in archived if job_slug(j) != slug] or related_pool
    related = related_jobs_for(job, related_pool, 5)

    skills_html = ""
    if skills:
        skills_html = '<div class="job-page-skills">' + "".join(
            f'<span class="skill-chip">{esc(skill)}</span>' for skill in skills
        ) + CARD_STOP + "</div>"

    schema = job_posting_jsonld(job, today) if not is_archived else jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": desc,
            "url": canonical,
            "inLanguage": "en-IN",
            "isPartOf": {"@id": SITE + "/#website"},
            "breadcrumb": {"@id": canonical + "#breadcrumb"},
        }
    )
    breadcrumb = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": canonical + "#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Career Registry", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": job_title, "item": canonical},
            ],
        }
    )

    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
    {GA_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="en-IN" href="{canonical}">
    <link rel="alternate" hreflang="x-default" href="{canonical}">

    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Urban Forest Park — India Career Registry">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{LOGO_URL}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

{FAVICONS}

{FONTS}

    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">
    <link rel="stylesheet" href="/styles/job-page.css">

{schema}
{breadcrumb}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#job-content">Skip to job details</a>

{header_html('registry')}

  <main class="job-page" id="job-content">
    <section class="job-page-hero">
      <div class="job-page-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">All jobs</a><span aria-hidden="true">/</span><a href="{category_hub_path(job.get('category'))}">{esc(plain(job.get('category')) or 'Jobs')}</a><span aria-hidden="true">/</span><span>{esc(job_title)}</span>
        </nav>
        <p class="eyebrow">{esc(plain(job.get("category")) or "Environmental Job")}</p>
        <h1>{esc(job_title)}</h1>
        <p class="job-page-org"><strong>{esc(org)}</strong> &middot; {esc(location)}</p>
        <div class="job-page-badges">
          <span class="badge badge-type">{esc(position_type_of(job))}</span>
          <span class="badge badge-state">{PIN_SVG}{esc(state_label(job))}</span>
          <span class="badge">{esc(plain(job.get("experience_level")) or "Experience stated in notice")}</span>
        </div>
{apply_block}
      </div>
    </section>

    <div class="job-page-layout">
      <article class="job-page-main">
        <section>
          <h2>Role overview</h2>
          <p>{esc(summary)}</p>
        </section>
        <section>
          <h2>Key responsibilities</h2>
          {_bullets(job.get("key_responsibilities"))}
        </section>
        <section>
          <h2>Eligibility &amp; qualifications</h2>
          <p>{esc(qualification)}</p>
          {skills_html}
        </section>
        <section>
          <h2>Compensation / fellowship</h2>
          <p>{esc(compensation)}</p>
        </section>
        <section>
          <h2>How to apply</h2>
          <p>{'This job is closed. The original portal is retained for reference only.' if is_archived else 'Applications are submitted directly through the official employer portal. Urban Forest Park does not charge any fee and does not act as a recruitment intermediary.'}</p>
          <p><strong>Application deadline / window:</strong> {esc(deadline)}</p>
          {('<p><a class="btn btn-outline" href="' + esc(website) + '" target="_blank" rel="noopener noreferrer">Open official employer website &nearr;</a></p>') if website else ''}
        </section>
      </article>

      <aside class="job-page-side" aria-label="Job snapshot">
        <h2>Job snapshot</h2>
        <dl class="job-facts">
          <div><dt>Employer</dt><dd>{esc(org)}</dd></div>
          <div><dt>Location</dt><dd>{esc(location)}</dd></div>
          <div><dt>Position type</dt><dd>{esc(position_type_of(job))}</dd></div>
          <div><dt>Experience</dt><dd>{esc(plain(job.get("experience_level")) or "See notification")}</dd></div>
          <div><dt>Compensation</dt><dd>{esc(compensation)}</dd></div>
          <div><dt>Deadline</dt><dd>{esc(deadline)}</dd></div>
          <div><dt>Posted</dt><dd>{esc(posted or "Not stated")}</dd></div>
        </dl>
        <p class="job-page-note">Always verify eligibility, age limits, reservation and fees in the official notification before applying.</p>
      </aside>
    </div>

    <section class="job-page-related" aria-labelledby="related-title">
      <div class="job-page-inner">
        <h2 id="related-title">Five related jobs &amp; fellowships</h2>
        <div class="related-grid">
{related_jobs_html(related)}
        </div>
      </div>
    </section>
  </main>

{site_matrix_html(job_url(job))}

{footer_html('jobs/' + slug + '.html')}

  <script defer src="/js/consent.js"></script>
<script defer src="/js/back-to-top.js"></script>
<script defer src="/js/syndication-drawer.js"></script>
</body>
</html>
"""


def write_job_pages(
    public: Path,
    active: List[Dict[str, Any]],
    archived: List[Dict[str, Any]],
    global_active: List[Dict[str, Any]],
    global_archived: List[Dict[str, Any]],
    today: date,
) -> int:
    out_dir = public / JOBS_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    all_india = active + archived
    all_global = global_active + global_archived
    for job in all_india:
        slug = job_slug(job)
        (out_dir / f"{slug}.html").write_text(
            build_job_page(job, all_india, archived, today), encoding="utf-8"
        )
        written += 1
    for job in all_global:
        slug = job_slug(job)
        (out_dir / f"{slug}.html").write_text(
            build_job_page(job, all_global, global_archived, today), encoding="utf-8"
        )
        written += 1
    # Remove stale pages for records that no longer exist (purged, never
    # quarantined/rendered). Only files previously generated in this folder.
    keep = {job_slug(job) + ".html" for job in all_india + all_global}
    for path in out_dir.glob("*.html"):
        if path.name not in keep:
            path.unlink()
    return written


def sync_sitemap_jobs(
    public: Path,
    active: List[Dict[str, Any]],
    archived: List[Dict[str, Any]],
    global_active: List[Dict[str, Any]],
    global_archived: List[Dict[str, Any]],
    today: date,
) -> None:
    """Remove legacy ?job= entries and ensure every static page is listed."""
    path = public / "sitemap.xml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    # Remove every prior job URL (legacy query and static) before rebuilding
    # from the current registries, so purged records cannot leave stale locs.
    text = re.sub(r"\s*<url>\s*<loc>[^<]*\?job=[^<]*</loc>.*?</url>", "", text, flags=re.S)
    text = re.sub(r"\s*<url>\s*<loc>[^<]*/jobs/[^<]*</loc>.*?</url>", "", text, flags=re.S)
    additions: List[str] = []
    seen = set(re.findall(r"<loc>([^<]+)</loc>", text))
    for job in active + global_active:
        loc = job_url(job, absolute=True)
        if loc in seen:
            continue
        seen.add(loc)
        lastmod = plain(job.get("date_added")) or today.isoformat()
        additions.append(
            f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
            "<changefreq>daily</changefreq><priority>0.8</priority></url>"
        )
    for job in archived + global_archived:
        loc = job_url(job, absolute=True)
        if loc in seen:
            continue
        seen.add(loc)
        lastmod = plain(job.get("date_archived")) or plain(job.get("date_added")) or today.isoformat()
        additions.append(
            f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
            "<changefreq>monthly</changefreq><priority>0.5</priority></url>"
        )
    if additions:
        text = text.replace("</urlset>", "\n".join(additions) + "\n</urlset>")
    path.write_text(text, encoding="utf-8")


def sync_sitemap_hubs(
    public: Path,
    today: date,
    hub_indexable: Dict[str, bool],
) -> int:
    """Ensure only indexable hubs are in the sitemap; remove non-indexable ones."""
    path = public / "sitemap.xml"
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")

    removals = 0
    for hub in HUBS:
        if hub_indexable.get(hub["file"], True):
            continue
        loc = pretty_url(SITE + "/" + hub["file"])
        pattern = rf"\s*<url>\s*<loc>{re.escape(loc)}</loc>.*?</url>"
        text, count = re.subn(pattern, "", text, flags=re.S)
        removals += count
    if removals:
        log.info("Removed %d non-indexable hub URL(s) from sitemap", removals)

    # Add missing indexable hubs
    seen = set(re.findall(r"<loc>([^<]+)</loc>", text))
    additions: List[str] = []
    for hub in HUBS:
        if not hub_indexable.get(hub["file"], False):
            continue
        loc = pretty_url(SITE + "/" + hub["file"])
        if loc in seen:
            continue
        seen.add(loc)
        additions.append(
            f"  <url><loc>{loc}</loc><lastmod>{today.isoformat()}</lastmod>"
            "<changefreq>weekly</changefreq><priority>0.9</priority></url>"
        )
    if additions or removals:
        if additions:
            text = text.replace("</urlset>", "\n".join(additions) + "\n</urlset>")
        path.write_text(text, encoding="utf-8")
    return len(additions)


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


RSS_ALTERNATE = (
    '<link rel="alternate" type="application/rss+xml" '
    'title="Urban Forest Park — Climate, Forestry, ESG &amp; JRF Jobs RSS" '
    'href="https://www.urbanforestpark.com/feed.xml" />'
)
JRF_ALTERNATE = (
    '<link rel="alternate" type="application/rss+xml" '
    'title="Urban Forest Park — JRF, SRF, PhD &amp; Fellowship Feed" '
    'href="https://www.urbanforestpark.com/jrf-feed.xml" />'
)
RSS_FOOTER = (
    '<div class="footer-rss" style="margin-top:10px;font-size:12px;">'
    '<a href="/feed.xml">RSS: all jobs</a> &middot; '
    '<a href="/jrf-feed.xml">RSS: JRF, SRF &amp; fellowships</a></div>'
)


def _rss_date(value: Any, fallback: datetime) -> str:
    from email.utils import format_datetime
    text = str(value or "").strip()
    parsed: Optional[datetime] = None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(text[:19], fmt).replace(tzinfo=timezone.utc)
            break
        except ValueError:
            continue
    return format_datetime(parsed or fallback)


def _rss_item(job: Dict[str, Any], fallback: datetime) -> str:
    job_id = str(job.get("id") or "")
    title = str(job.get("clean_title") or "Untitled job")
    org = str(job.get("organization") or "")
    location = " · ".join(
        part for part in (job.get("city"), job.get("state"), job.get("country")) if part
    ) or str(job.get("region") or "India")
    deadline = str(job.get("deadline_or_window") or job.get("valid_through") or "")
    qualification = str(job.get("qualification_summary") or "")
    comp = str(job.get("compensation_or_fellowship") or "")
    desc_parts = [org, location]
    if deadline:
        desc_parts.append("Deadline: " + deadline)
    if qualification:
        desc_parts.append("Eligibility: " + qualification)
    if comp:
        desc_parts.append("Pay: " + comp)
    link = job_url(job, absolute=True)
    category = html.escape(str(job.get("category") or "Climate / Forestry / ESG"))
    return (
        "<item>"
        f"<title>{html.escape(title)}</title>"
        f"<link>{link}</link>"
        f"<guid isPermaLink=\"true\">{link}</guid>"
        f"<pubDate>{_rss_date(job.get('date_added'), fallback)}</pubDate>"
        f"<category>{category}</category>"
        f"<description>{html.escape(' | '.join(desc_parts))}</description>"
        "</item>"
    )


def build_rss_feed(
    jobs: List[Dict[str, Any]], title: str, description: str, self_path: str
) -> str:
    fallback = datetime.now(timezone.utc)
    ordered = sorted(jobs, key=lambda job: str(job.get("date_added") or ""), reverse=True)
    items = "\n".join(_rss_item(job, fallback) for job in ordered)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "<channel>\n"
        f"<title>{html.escape(title)}</title>\n"
        f"<link>{SITE}/</link>\n"
        f"<description>{html.escape(description)}</description>\n"
        "<language>en-in</language>\n"
        f"<lastBuildDate>{_rss_date(fallback, fallback)}</lastBuildDate>\n"
        f'<atom:link href="{SITE}{self_path}" rel="self" type="application/rss+xml" />\n'
        f"{items}\n"
        "</channel>\n"
        "</rss>\n"
    )


def write_feeds(public: Path, active: List[Dict[str, Any]], global_active: List[Dict[str, Any]]) -> None:
    all_jobs = active + global_active
    (public / "feed.xml").write_text(
        build_rss_feed(
            all_jobs,
            "Urban Forest Park — Climate, Forestry, ESG & Research Jobs",
            "Verified climate, forestry, wildlife, ESG, geospatial, academic and clean-energy jobs in India and worldwide.",
            "/feed.xml",
        ),
        encoding="utf-8",
    )
    academic = [
        job for job in all_jobs
        if re.search(
            r"\b(jrf|junior research fellow|srf|senior research fellow|project associate|"
            r"research associate|research fellow|young professional|phd|doctoral|"
            r"postdoc|post-?doctoral|fellowship|research intern)\b",
            " ".join(str(job.get(key) or "") for key in ("clean_title", "position_type")),
            re.I,
        )
    ]
    (public / "jrf-feed.xml").write_text(
        build_rss_feed(
            academic,
            "Urban Forest Park — JRF, SRF, PhD & Fellowship Feed",
            "Current JRF, SRF, Project Associate, Research Associate, PhD and postdoctoral opportunities in India.",
            "/jrf-feed.xml",
        ),
        encoding="utf-8",
    )
    log.info("Wrote feed.xml (%d items) and jrf-feed.xml (%d items)", len(all_jobs), len(academic))


def inject_feed_links(public: Path) -> int:
    changed = 0
    for path in sorted(public.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        updated = text
        if "application/rss+xml" not in updated and "</head>" in updated:
            updated = updated.replace("</head>", "    " + RSS_ALTERNATE + "\n    " + JRF_ALTERNATE + "\n</head>", 1)
        if "footer-rss" not in updated and "</footer>" in updated:
            updated = updated.replace("</footer>", "  " + RSS_FOOTER + "\n</footer>", 1)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


ANCHOR_TAG_RE = re.compile(r"<a\b([^>]*)>", re.I)


def _add_nofollow_to_anchor(match: re.Match[str]) -> str:
    attrs = match.group(1)
    href_match = re.search(r'href\s*=\s*"([^"]*)"', attrs, re.I)
    if not href_match:
        return match.group(0)
    url = href_match.group(1)
    if "?" not in url:
        return match.group(0)
    if not (url.startswith("/") or url.startswith("?") or url.startswith(SITE)):
        return match.group(0)
    if re.search(r'rel\s*=\s*"[^"]*nofollow', attrs, re.I):
        return match.group(0)
    if re.search(r"rel\s*=", attrs, re.I):
        return re.sub(
            r'rel\s*=\s*"([^"]*)"',
            lambda m: 'rel="' + m.group(1).strip() + ' nofollow"',
            match.group(0),
            count=1,
            flags=re.I,
        )
    return match.group(0).replace("<a", '<a rel="nofollow"', 1)


def harden_query_links(public: Path) -> int:
    """Safety net: every internal query-string anchor is nofollow.

    Interactive registry filters (archive, global region/kind, language) still
    work, but crawlers are not asked to index an infinite query surface. State
    and category links are already rewritten to static hubs at source.
    """
    changed = 0
    for path in list(sorted(public.glob("*.html"))) + list(sorted((public / JOBS_DIRNAME).glob("*.html"))):
        text = path.read_text(encoding="utf-8")
        updated = ANCHOR_TAG_RE.sub(_add_nofollow_to_anchor, text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


BRAND_SUB_RE = re.compile(r'(<span class="brand-sub"[^>]*>).*?(</span>)', re.S)
LW_SUB_RE = re.compile(r'(<span class="lw-sub">).*?(</span>)', re.S)


def shorten_brand_labels(public: Path) -> int:
    """Keep the header brand anchor short enough for link-text guidelines."""
    changed = 0
    for path in list(sorted(public.glob("*.html"))) + list(sorted((public / JOBS_DIRNAME).glob("*.html"))):
        text = path.read_text(encoding="utf-8")
        is_hindi = 'lang="hi"' in text[:300]
        short = "हरित करियर रजिस्ट्री" if is_hindi else "Green Jobs &amp; Research Registry"
        updated = BRAND_SUB_RE.sub(lambda m: m.group(1) + short + m.group(2), text)
        updated = LW_SUB_RE.sub(lambda m: m.group(1) + short + m.group(2), updated)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def strip_trailing_whitespace(public: Path) -> int:
    """Keep generated HTML clean for diff review and CI whitespace checks."""
    changed = 0
    for path in list(sorted(public.glob("*.html"))) + list(sorted((public / JOBS_DIRNAME).glob("*.html"))):
        text = path.read_text(encoding="utf-8")
        cleaned = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            changed += 1
    return changed


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
    global_active = load_records(public, "global_jobs.json")
    global_archived = load_records(public, "global_archive.json")
    log.info(
        "Loaded %d active + %d archived India record(s); %d + %d global record(s)",
        len(active), len(archived), len(global_active), len(global_archived),
    )
    touch_stats_ist(public)

    # ---- index snapshot + crawlable first-screen cards ------------------
    block = build_index_block(active, archived, today)
    inject_snapshot(index_path, block)
    inject_job_feed(index_path, build_job_feed_block(active))
    log.info("Injected registry snapshot and %d pre-rendered job cards", min(PRERENDER_CARDS, len(active)))

    # ---- hub pages ------------------------------------------------------
    hub_counts: Dict[str, int] = {}
    for hub in HUBS:
        matched = [j for j in active if hub["match"](j)]
        hub_counts[hub["file"]] = len(matched)

    # Hub-to-city mapping for A2 duplicate-hub rule
    HUB_TO_CITY: Dict[str, str] = {
        "esg-sustainability-jobs-karnataka.html": "esg-jobs-bangalore.html",
        "esg-sustainability-jobs-maharashtra.html": "esg-jobs-mumbai.html",
    }

    # Update streak counters and determine indexability
    hub_indexable = update_hub_streaks(hub_counts, HUB_TO_CITY)

    # Update keyword map with indexability
    for hub_file, is_indexable in hub_indexable.items():
        if hub_file in KEYWORD_MAP:
            KEYWORD_MAP[hub_file]["indexable"] = is_indexable

    # Save updated keyword map
    KEYWORD_MAP_PATH.write_text(
        json.dumps({"site": SITE, "pages": list(KEYWORD_MAP.values())}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (public / "seo_keyword_map.json").write_text(
        json.dumps({"site": SITE, "pages": list(KEYWORD_MAP.values())}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    for hub in HUBS:
        hub["_indexable"] = hub_indexable.get(hub["file"], False)
        page = build_hub_page(hub, active, archived, hub_counts, today)
        out_path = public / hub["file"]
        out_path.write_text(page, encoding="utf-8")
        status = "indexable" if hub["_indexable"] else "noindex (scaffolded)"
        log.info("Wrote %s (%d active match(es)) [%s]", hub["file"], hub_counts[hub["file"]], status)

    # ---- multilingual & regional portals --------------------------------
    import seo_portals  # lazy import: reuses this module's helpers/constants

    hindi_page = seo_portals.build_hindi_hub_page(active, archived, hub_counts, today)
    (public / seo_portals.HINDI_HUB_FILE).write_text(hindi_page, encoding="utf-8")
    log.info("Wrote %s", seo_portals.HINDI_HUB_FILE)

    regional_page = seo_portals.build_regional_hub_page(active, today)
    (public / seo_portals.REGIONAL_HUB_FILE).write_text(regional_page, encoding="utf-8")
    log.info("Wrote %s", seo_portals.REGIONAL_HUB_FILE)

    # ---- global opportunities hub (strictly separate registry) -----------
    if not global_active:
        log.warning("global_jobs.json missing or empty - global hub built with placeholder content")
    global_page = seo_portals.build_global_hub_page(global_active, today)
    (public / seo_portals.GLOBAL_HUB_FILE).write_text(global_page, encoding="utf-8")
    log.info(
        "Wrote %s (%d global listing(s))",
        seo_portals.GLOBAL_HUB_FILE,
        len(global_active),
    )

    # ---- static /jobs/<slug> pages (one per active and archived record) ---
    job_pages = write_job_pages(
        public, active, archived, global_active, global_archived, today
    )
    log.info("Wrote %d static job detail page(s) under /jobs/", job_pages)

    # ---- institutional pages + keyword-map metadata -----------------------
    import seo_static_pages  # lazy import: reuses this module's helpers

    seo_static_pages.write_keyword_map(public)
    seo_static_pages.write_institutional_pages(public, today)
    seo_static_pages.normalise_static_pages(public)
    log.info("Wrote institutional pages and normalised static SEO metadata")

    # ---- RSS 2.0 feeds + discovery links ---------------------------------
    write_feeds(public, active, global_active)
    feed_pages = inject_feed_links(public)
    log.info("Injected RSS discovery/footer links on %d page(s)", feed_pages)

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
    job_rewritten = 0
    for path in sorted((public / JOBS_DIRNAME).glob("*.html")):
        text = path.read_text(encoding="utf-8")
        updated = prettify_internal_urls(text)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            job_rewritten += 1
    log.info(
        "Normalised internal URLs on %d top-level and %d job page(s)",
        rewritten, job_rewritten,
    )

    nofollow_pages = harden_query_links(public)
    brand_pages = shorten_brand_labels(public)
    whitespace_pages = strip_trailing_whitespace(public)
    log.info(
        "Hardened query links on %d page(s); shortened brand labels on %d page(s); cleaned whitespace on %d page(s)",
        nofollow_pages, brand_pages, whitespace_pages,
    )

    sync_sitemap_jobs(public, active, archived, global_active, global_archived, today)
    hub_sitemap_additions = sync_sitemap_hubs(public, today, hub_indexable)
    log.info("Added/removed %d hub URL(s) in sitemap", hub_sitemap_additions)
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
