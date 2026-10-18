#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UrbanForestPark - India Green Jobs pipeline
============================================

Daily automation behind https://www.urbanforestpark.com/ (India's climate,
forestry, ESG and geospatial job board). It:

  1. SCRAPES India-focused green job boards with python-jobspy
     (LinkedIn + Indeed + Naukri, automatically falling back to
     LinkedIn + Indeed if any board errors mid-run) across six
     high-intent India search queries.
  2. RUNS a second zero-key sweep with organisation- and sector-targeted
     India queries (WWF / WRI / CEEW / TERI / ATREE / UNDP, government
     environment & forest bodies, remote-sensing / GIS forestry, ESG / CSR
     management, carbon and net-zero roles) so the whole climate and
     conservation economy is covered without extra API credentials.
  3. FETCHES ReliefWeb India vacancies: the v2 API is attempted first (it
     needs an appname approved by ReliefWeb; a 401/403 simply means "still
     pending"), and on any failure the pipeline falls back to ReliefWeb's
     public India jobs RSS feed, which needs no key or approval. Both routes
     feed the same Gemini humanizer as every other source.
  4. HUMANIZES every candidate with a Gemini Flash model (newest working
     version, with automatic fallback if one is retired). The model also runs
     a strict India + green-relevance check first: off-topic software/IT jobs
     that leaked through keyword search are marked is_relevant_green_job
     = false and never written to jobs.json.
  5. MERGES accepted listings into public/jobs.json (the file the job board
     reads at runtime; see js/jobs.js), stamps every listing with its
     lifecycle fields (status + valid_through) and MOVES listings whose
     30-day window has passed into public/archive.json - past mandates are
     preserved for institutional reference and never deleted.
  6. REGENERATES public/sitemap.xml (homepage, dashboard, archive view,
     category/state landing views, active and archived job URLs) and
     public/stats.json (weekly hiring telemetry: active / opened / passed
     counts plus per-category and per-state breakdowns).

Typical usage
-------------
    # Full daily run (requires GEMINI_API_KEY)
    python scripts/fetch_and_humanize.py

    # Rebuild sitemap.xml from jobs.json only (no API key needed)
    python scripts/fetch_and_humanize.py --sitemap-only

    # Maintenance-only run: expire listings into archive.json, refresh
    # stats.json and rewrite jobs.json / archive.json / stats.json /
    # sitemap.xml (no scraping, no Gemini calls)
    python scripts/fetch_and_humanize.py --sync-only

    # Full run without writing anything
    python scripts/fetch_and_humanize.py --dry-run

    # 7-day backfill sweep (bash; PowerShell: $env:LOOKBACK_HOURS="168")
    LOOKBACK_HOURS=168 python scripts/fetch_and_humanize.py

Environment
-----------
    GEMINI_API_KEY    Google AI Studio key with Gemini API access.
                      (GOOGLE_API_KEY is accepted as a fallback name.)
    GEMINI_MODEL      Optional. Force one specific Gemini model (e.g.
                      gemini-3.8-flash). By default the newest working
                      candidate in MODEL_CANDIDATES is used automatically.
    LOOKBACK_HOURS    Optional posting-age window in hours (default 24 for
                      daily runs; set 168 to cover a full week). Applies to
                      both the broad and targeted jobspy sweeps.
    RELIEFWEB_APPNAME Optional ReliefWeb API appname (default
                      "urbanforestpark-jobboard-7x9k"). ReliefWeb must
                      approve the appname before the v2 jobs API answers;
                      until then the public India jobs RSS feed is used
                      instead, so no action is required.
    A local .env file (git-ignored) is loaded automatically when present,
    so you can keep GEMINI_API_KEY=... next to your other dev secrets
    without exporting it in every terminal.
"""

from __future__ import annotations

import argparse
import html
import inspect
import json
import logging
import math
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urlparse
from xml.etree import ElementTree as ET

# ---------------------------------------------------------------------------
# Optional third-party dependencies.
# All imports are guarded so `--help` and `--sitemap-only` keep working in a
# bare Python environment (useful for regenerating the sitemap locally
# without installing the scrapers or the Gemini SDK).
# ---------------------------------------------------------------------------
try:
    from jobspy import scrape_jobs
except Exception:  # pragma: no cover
    scrape_jobs = None

_JOBSPY_PARAMS: Set[str] = set()
if scrape_jobs is not None:
    try:
        _JOBSPY_PARAMS = set(inspect.signature(scrape_jobs).parameters)
    except (TypeError, ValueError):  # pragma: no cover
        _JOBSPY_PARAMS = set()

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None

try:
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover
    BaseModel = None

_GENAI_MODE: Optional[str] = None
_genai_new = None       # google-genai           (pip install google-genai)
_genai_legacy = None    # google-generativeai    (legacy package name)
try:
    from google import genai as _genai_new
    _GENAI_MODE = "google-genai"
except Exception:  # pragma: no cover
    try:
        import google.generativeai as _genai_legacy
        _GENAI_MODE = "google-generativeai"
    except Exception:
        _GENAI_MODE = None

log = logging.getLogger("ufp-jobs")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SITE_BASE_URL = "https://www.urbanforestpark.com"

# Gemini model order: the first entry is tried first. The humanizer falls
# back to the next entry when a model is retired for this key ("404 ... no
# longer available") or keeps returning rate-limit/overload errors. The
# "latest" alias tracks the current recommended Flash model, and the lite
# model adds an independent quota bucket. GEMINI_MODEL (env or .env)
# overrides the order entirely.
MODEL_CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash",
]

DEFAULT_JOBS_PATH = Path("public/jobs.json")
DEFAULT_SITEMAP_PATH = Path("public/sitemap.xml")
DEFAULT_ARCHIVE_PATH = Path("public/archive.json")
DEFAULT_STATS_PATH = Path("public/stats.json")

# Job lifecycle: a listing stays "active" in jobs.json for VALID_DAYS after
# its date_added; once valid_through has passed it moves into archive.json
# (status "archived", date_archived stamped) and is never deleted.
VALID_DAYS = 30

RESULTS_PER_QUERY = 25          # jobspy results wanted per search query
REQUEST_TIMEOUT = 30            # seconds; HTTP timeout for ReliefWeb calls
DEFAULT_LOOKBACK_HOURS = 24     # posting-age window; LOOKBACK_HOURS env overrides
DEFAULT_MAX_NEW_PER_RUN = 12    # cap on Gemini calls per run (cost control)
GEMINI_SLEEP_SECONDS = 4.0      # gentle rate limit between model calls
GEMINI_RATE_LIMIT_SLEEP = 25.0  # longer pause when rate-limited/overloaded
GEMINI_RATE_LIMIT_ABORT_AFTER = 3  # consecutive rate-limited candidates -> stop run

# Board coverage: prefer all three; if any single board throws (upstream
# layout changes happen), retry the query with the stable pair so the
# pipeline never halts.
PRIMARY_SITES = ["linkedin", "indeed", "naukri"]
FALLBACK_SITES = ["linkedin", "indeed"]

# India-specific high-intent search queries.
SEARCH_QUERIES = [
    "Climate Change Sustainability India",
    "ESG BRSR Carbon Credits Sustainability",
    "Forestry Wildlife Afforestation Ecology CAMPA",
    "GIS Remote Sensing Earth Engine Environment",
    "Urban Heat Island Urban Planner Sustainability",
    "CSR Environment Sustainability Manager",
]

# Front-end vocabulary (must match index.html filters and jobs.json values).
CATEGORIES = [
    "Climate & Sustainability",
    "Environmental Policy & Fellowships",
    "ESG & Carbon Markets",
    "Forestry & Afforestation",
    "GIS, Remote Sensing & UHI",
]

# URL slugs for the crawlable category landing views (?category=<slug>).
# js/jobs.js maps the same slugs back to the display names above.
CATEGORY_SLUGS = {
    "Climate & Sustainability": "climate-sustainability",
    "Environmental Policy & Fellowships": "environmental-policy-fellowships",
    "ESG & Carbon Markets": "esg-carbon-markets",
    "Forestry & Afforestation": "forestry-afforestation",
    "GIS, Remote Sensing & UHI": "gis-remote-sensing-uhi",
}

# How many state landing views the sitemap lists (busiest states first).
SITEMAP_TOP_STATES = 25

EXPERIENCE_LEVELS = [
    "Entry Level / Fellowship",
    "1-3 Years",
    "Mid-Senior (3-6 Years)",
    "Senior",
]

EXPERIENCE_ALIASES = {
    "entry": "Entry Level / Fellowship",
    "entry level": "Entry Level / Fellowship",
    "entry-level": "Entry Level / Fellowship",
    "fresher": "Entry Level / Fellowship",
    "fellowship": "Entry Level / Fellowship",
    "junior": "Entry Level / Fellowship",
    "intern": "Entry Level / Fellowship",
    "mid": "1-3 Years",
    "mid level": "1-3 Years",
    "mid-level": "1-3 Years",
    "mid senior": "Mid-Senior (3-6 Years)",
    "mid-senior": "Mid-Senior (3-6 Years)",
    "lead": "Senior",
    "senior level": "Senior",
    "principal": "Senior",
    "head": "Senior",
}

# States / UTs the board recognises plus the Delhi NCR convenience value.
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Delhi NCR", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
    "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
    "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
    "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
    "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Jammu and Kashmir", "Ladakh",
    "Lakshadweep", "Puducherry", "Multiple States / Remote",
]

# Static pages seeded when no sitemap exists yet (existing entries are
# otherwise preserved verbatim on every regeneration).
STATIC_SITEMAP_PAGES = [
    ("/about.html", "monthly", "0.8"),
    ("/spatial-data.html", "weekly", "0.9"),
    ("/green-calculator.html", "monthly", "0.8"),
    ("/green-calculator-report.html", "monthly", "0.7"),
    ("/green-calculator-app.html", "monthly", "0.6"),
    ("/nagar-van-finder.html", "weekly", "0.8"),
    ("/public-survey.html", "monthly", "0.6"),
    ("/report.html", "monthly", "0.7"),
    ("/privacy.html", "yearly", "0.3"),
    ("/terms.html", "yearly", "0.3"),
    ("/cookies.html", "yearly", "0.3"),
    ("/accessibility.html", "yearly", "0.3"),
]

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

# ---------------------------------------------------------------------------
# Structured output schema (validated with pydantic before anything is
# written to jobs.json).
# ---------------------------------------------------------------------------
if BaseModel is not None:

    class GreenJob(BaseModel):
        """Publication-ready listing produced by Gemini for one candidate."""

        # Strict India + green relevance gate (Step 1 of the system prompt).
        is_relevant_green_job: bool = True
        rejection_reason: str = ""

        # jobs.json schema (must stay in sync with the front-end).
        id: str = ""
        date_added: str = ""
        clean_title: str = ""
        organization: str = ""
        state: str = ""
        city: str = ""
        category: str = ""
        experience_level: str = ""
        role_summary: str = ""
        key_responsibilities: List[str] = Field(default_factory=list)
        must_have_skills: List[str] = Field(default_factory=list)
        application_tip: str = ""
        apply_url: str = ""

else:  # pragma: no cover - only hit when pydantic is missing
    GreenJob = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Gemini prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are the editorial engine for UrbanForestPark \
(https://www.urbanforestpark.com), India's job board for climate, forestry, \
ESG and geospatial careers. You receive ONE raw job posting scraped from a \
job board (JSON). You return ONE JSON object.

STEP 1 - STRICT INDIA + GREEN RELEVANCE CHECK (always do this first):
A posting is acceptable ONLY when BOTH are true:
  (a) The role is genuinely about the environment, climate change, forestry, \
afforestation, wildlife/ecology, sustainability, ESG, CSR, carbon markets, \
clean/renewable energy, water, agriculture (sustainability angle), urban \
planning/green infrastructure, or geospatial / remote-sensing / GIS \
analysis of natural or built environments.
  (b) The role is located in India, or explicitly open to India-based or \
remote-India candidates.
If EITHER fails - for example a generic software, IT support, sales, \
marketing, finance or HR job that only matched search keywords - set \
"is_relevant_green_job" to false, give one sentence in "rejection_reason", \
and return empty strings/arrays for all other fields. When in doubt, \
reject. Never stretch the definition to keep a job.

STEP 2 - HUMANIZED FIELDS (only for accepted jobs). Return exactly:
- id: kebab-case slug (a-z, 0-9, hyphens only, max 60 chars) built from \
role + organisation (+ city only if needed to disambiguate).
- date_added: {today} (copy this exact value).
- clean_title: job title cleaned of noise (requisition codes, "urgent", \
city names glued on, company name repeats).
- organization: the employer's proper name.
- state: Indian state/UT from this vocabulary: {states}. Use \
"Multiple States / Remote" for multi-state or remote-India roles; use \
"Delhi NCR" for Delhi / Noida / Gurugram / Ghaziabad / Faridabad roles.
- city: city name, or a short descriptor such as "Remote (India)".
- category: EXACTLY ONE of: {categories}
- experience_level: EXACTLY ONE of: {experience}
- role_summary: exactly 3 sentences, 45-70 words, concrete and specific \
to THIS role (team, mandate, location, impact). No generic filler.
- key_responsibilities: 4-5 short bullets, each a plain sentence fragment \
starting with a verb. Only what the source posting supports.
- must_have_skills: 5-7 short skill tags (e.g. "ESG reporting (BRSR)", \
"QGIS", "carbon accounting"). Mix technical and domain skills.
- application_tip: 1-2 sentences of practical, editor-style advice for an \
Indian applicant (portfolio, GIS samples, BRSR familiarity, fieldwork \
experience, certifications). Never mention that this tip was AI-written.
- apply_url: copy the source URL EXACTLY as provided.

STYLE RULES: Write like a thoughtful human editor. Plain, concrete \
English; vary sentence length. Never use the words "delve", "leverage", \
"spearhead", "passionate", "vibrant", "landscape" (as metaphor) or \
"game-changer". Use at most one em dash in the entire output and no \
exclamation marks. Never invent facts (salaries, dates, requirements, \
benefits) that the source does not contain - you may only compress, \
clarify and humanize.

Return ONLY the JSON object - no markdown fences, no commentary."""


def build_system_prompt(today: str) -> str:
    """Fill the enum placeholders so the model can only echo valid values."""
    return (
        SYSTEM_PROMPT
        .replace("{today}", today)
        .replace("{states}", ", ".join(INDIAN_STATES))
        .replace("{categories}", " | ".join(CATEGORIES))
        .replace("{experience}", " | ".join(EXPERIENCE_LEVELS))
    )


def build_user_prompt(candidate: Dict[str, Any], today: str) -> str:
    payload = {
        "today": today,
        "source_board": candidate.get("source") or "job board",
        "raw_title": candidate.get("title") or "",
        "raw_company": candidate.get("organization") or "",
        "raw_location": candidate.get("location_raw") or "",
        "raw_date_posted": candidate.get("date_posted") or "",
        "raw_url": candidate.get("apply_url") or "",
        "raw_description": (candidate.get("description") or "")[:4000],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _clean_cell(value: Any) -> str:
    """Stringify a scraped cell, turning None/NaN/date objects into text."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    # pandas timestamps arrive as "YYYY-MM-DD 00:00:00" - keep the date part.
    if re.match(r"^\d{4}-\d{2}-\d{2} ", text):
        text = text[:10]
    return text


def strip_html(value: str) -> str:
    """Crude HTML-to-text for raw job descriptions."""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", value or "", flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def squash(value: Any) -> str:
    """Collapse whitespace in model output."""
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_key(text: str) -> str:
    """Normalise text for de-duplication comparisons."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def dedupe_key(candidate: Dict[str, Any]) -> str:
    url_key = normalize_key(candidate.get("apply_url") or "")
    title_key = normalize_key(candidate.get("title") or "")
    org_key = normalize_key(candidate.get("organization") or "")
    return url_key or (title_key + "@" + org_key)


def existing_keys(jobs: List[Dict[str, Any]]) -> Set[str]:
    keys: Set[str] = set()
    for job in jobs:
        keys.add(normalize_key(job.get("apply_url") or ""))
        keys.add(
            normalize_key(job.get("clean_title") or "")
            + "@"
            + normalize_key(job.get("organization") or "")
        )
    return keys


def unique_id(base_id: str, taken: Set[str]) -> str:
    """Return a URL-safe unique id, appending -2, -3 ... on collisions."""
    base = re.sub(r"[^a-z0-9]+", "-", (base_id or "").lower()).strip("-")[:60].strip("-")
    if not base:
        base = "green-job"
    candidate_id = base
    counter = 2
    while candidate_id in taken:
        suffix = "-" + str(counter)
        candidate_id = base[: 60 - len(suffix)].rstrip("-") + suffix
        counter += 1
    taken.add(candidate_id)
    return candidate_id


def match_enum(value: str, allowed: List[str], aliases: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Case-insensitive enum matcher with an optional alias map."""
    text = squash(value).lower()
    if not text:
        return None
    for option in allowed:
        if text == option.lower():
            return option
    if aliases and text in aliases:
        return aliases[text]
    return None


# ---------------------------------------------------------------------------
# Source 1: job boards via python-jobspy (LinkedIn / Indeed / Naukri)
# ---------------------------------------------------------------------------
def jobspy_row_to_candidate(row: Dict[str, Any], query: str) -> Dict[str, Any]:
    return {
        "source": _clean_cell(row.get("site")) or "job board",
        "title": _clean_cell(row.get("title")),
        "organization": _clean_cell(row.get("company")),
        "location_raw": _clean_cell(row.get("location")),
        "description": _clean_cell(row.get("description"))[:4000],
        "apply_url": _clean_cell(row.get("job_url")),
        "date_posted": _clean_cell(row.get("date_posted")),
        "matched_query": query,
    }


# ---------------------------------------------------------------------------
# Validation & configuration helpers
# ---------------------------------------------------------------------------
PLACEHOLDER_HOSTS = ("example.com", "example.org", "example.net")


def is_valid_apply_url(url: Optional[str]) -> bool:
    """Reject empty, malformed or placeholder apply URLs.

    A listing must always link to a real, clickable posting: anything with an
    empty URL, a non-http(s) scheme, a host without a dot or a reserved
    placeholder host (example.com/.org/.net) is refused before it can ever
    reach jobs.json or sitemap.xml.
    """
    raw = str(url or "").strip()
    if not raw.lower().startswith(("http://", "https://")):
        return False
    try:
        parsed = urlparse(raw)
    except ValueError:
        return False
    host = (parsed.netloc or "").split("@")[-1].split(":")[0].strip(".").lower()
    if not host or "." not in host:
        return False
    return not any(
        host == placeholder or host.endswith("." + placeholder)
        for placeholder in PLACEHOLDER_HOSTS
    )


def resolve_lookback_hours() -> int:
    """Posting-age window in hours: LOOKBACK_HOURS env var, else 24.

    Set LOOKBACK_HOURS=168 to sweep the last seven days (backfill); values
    are clamped to a sane 1..720-hour range.
    """
    raw = (os.environ.get("LOOKBACK_HOURS") or "").strip()
    if raw:
        try:
            value = int(float(raw))
        except ValueError:
            log.warning("Ignoring invalid LOOKBACK_HOURS=%r", raw)
        else:
            if value > 0:
                return min(value, 24 * 30)
    return DEFAULT_LOOKBACK_HOURS


def scrape_jobspy_queries(
    queries: List[str],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Run python-jobspy for every query over the India board set.

    Each query first tries the full three-board set; if that call raises
    (one board's page layout changed, rate limiting, etc.) it retries with
    the stable LinkedIn + Indeed pair so the pipeline never halts. Returns
    the raw candidates plus per-board counts for logging.
    """
    if scrape_jobs is None:
        log.warning("python-jobspy is not installed - skipping job-board scraping")
        return [], {}

    candidates: List[Dict[str, Any]] = []
    site_counts: Dict[str, int] = {}
    hours_old = resolve_lookback_hours()

    for query in queries:
        frame = None
        for site_list in (PRIMARY_SITES, FALLBACK_SITES):
            try:
                log.info("Scraping [%s] for %r", ", ".join(site_list), query)
                jobspy_kwargs: Dict[str, Any] = {
                    "site_name": site_list,
                    "search_term": query,
                    "location": "India",
                    "results_wanted": RESULTS_PER_QUERY,
                    "hours_old": hours_old,
                    "country_indeed": "India",
                }
                # The fetch-description option was renamed across jobspy
                # releases; pass whichever name this version accepts.
                if "fetch_description" in _JOBSPY_PARAMS:
                    jobspy_kwargs["fetch_description"] = True
                elif "linkedin_fetch_description" in _JOBSPY_PARAMS:
                    jobspy_kwargs["linkedin_fetch_description"] = True
                frame = scrape_jobs(**jobspy_kwargs)
                break
            except Exception as exc:
                log.warning(
                    "Scrape failed (sites=%s, query=%r): %s", site_list, query, exc
                )

        if frame is None or getattr(frame, "empty", True):
            continue
        try:
            rows = frame.to_dict(orient="records")
        except Exception as exc:  # pragma: no cover
            log.warning("Could not read results for %r: %s", query, exc)
            continue

        for row in rows:
            candidate = jobspy_row_to_candidate(row, query)
            if candidate["title"] and candidate["apply_url"]:
                candidates.append(candidate)
                source_name = candidate.get("source") or "unknown"
                site_counts[source_name] = site_counts.get(source_name, 0) + 1

        time.sleep(2)  # be polite between queries

    return candidates, site_counts


def format_source_counts(site_counts: Dict[str, int]) -> str:
    """Render per-board candidate counts as a single 'linkedin=12, ...' line."""
    return ", ".join(
        f"{name}={count}"
        for name, count in sorted(site_counts.items(), key=lambda item: -item[1])
    )


def scrape_board_candidates() -> List[Dict[str, Any]]:
    """Primary sweep across the six broad India green searches."""
    candidates, site_counts = scrape_jobspy_queries(SEARCH_QUERIES)
    if site_counts:
        log.info(
            "Job boards produced %d raw candidate(s) (%s)",
            len(candidates),
            format_source_counts(site_counts),
        )
    else:
        log.info("Job boards produced 0 raw candidate(s)")
    return candidates


# ---------------------------------------------------------------------------
# Source 2: targeted green-sector sweep (zero-key public job boards)
# ---------------------------------------------------------------------------
TARGETED_QUERIES = [
    "WWF WRI CEEW TERI ATREE UNDP India",
    "Ministry of Environment Forest Climate Change",
    "Remote Sensing GIS Forestry India",
    "Sustainability ESG CSR Manager India",
    "Carbon Footprinting Net Zero India",
]


def fetch_targeted_green_jobs() -> List[Dict[str, Any]]:
    """Second zero-key sweep with organisation- and sector-targeted queries.

    Covers conservation NGOs and climate think tanks (WWF, WRI, CEEW, TERI,
    ATREE, UNDP India), government environment / forest / climate bodies,
    remote-sensing and GIS forestry roles, ESG / CSR management and carbon /
    net-zero positions - all via public job boards, no credentials required.
    """
    candidates, site_counts = scrape_jobspy_queries(TARGETED_QUERIES)
    if site_counts:
        log.info(
            "Targeted sweep produced %d raw candidate(s) (%s)",
            len(candidates),
            format_source_counts(site_counts),
        )
    else:
        log.info("Targeted sweep produced 0 raw candidate(s)")
    return candidates


# ---------------------------------------------------------------------------
# Source 3: ReliefWeb India (v2 API first, public RSS feed as fallback)
# ---------------------------------------------------------------------------
RELIEFWEB_V2_JOBS_API = "https://api.reliefweb.int/v2/jobs"
RELIEFWEB_INDIA_RSS = "https://reliefweb.int/jobs/rss.xml?advanced-search=%28C119%29"
DEFAULT_RELIEFWEB_APPNAME = "urbanforestpark-jobboard-7x9k"

# Keyword scope for the API attempt (plain-text OR query).
RELIEFWEB_KEYWORDS = (
    "climate OR environment OR forestry OR wildlife OR conservation OR "
    "sustainability OR ESG OR carbon OR water OR agriculture OR disaster OR "
    "GIS OR geospatial OR \"remote sensing\""
)

# ReliefWeb's curated themes that overlap this board's categories; the API
# call first tries country+theme and then drops to country-only for safety.
RELIEFWEB_THEMES = (
    "climate change and environment",
    "disaster management",
    "agriculture",
    "water sanitation hygiene",
)


def fetch_reliefweb_v2_jobs(appname: str) -> Optional[List[Dict[str, Any]]]:
    """Try the ReliefWeb v2 jobs API for India vacancies.

    Returns the candidate list on success, or None whenever the API is not
    usable this run (401/403 while the appname is still pending approval,
    network trouble, or an unexpected payload) so the caller can fall back
    to the public RSS feed.
    """
    if requests is None:
        log.warning("`requests` is not installed - skipping the ReliefWeb v2 API")
        return None

    base_payload: Dict[str, Any] = {
        "limit": 60,
        "profile": "full",
        "query": {"value": RELIEFWEB_KEYWORDS, "fields": ["title", "body"]},
        "sort": ["date.created:desc"],
    }
    country_condition = {"field": "country", "value": "india"}
    theme_condition = {
        "operator": "OR",
        "conditions": [{"field": "theme", "value": theme} for theme in RELIEFWEB_THEMES],
    }
    filter_attempts = (
        {"operator": "AND", "conditions": [country_condition, theme_condition]},
        {"operator": "AND", "conditions": [country_condition]},
    )

    items: Optional[List[Dict[str, Any]]] = None
    for attempt, filter_obj in enumerate(filter_attempts, start=1):
        try:
            response = requests.post(
                RELIEFWEB_V2_JOBS_API,
                params={"appname": appname},
                json=dict(base_payload, filter=filter_obj),
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json().get("data")
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (401, 403):
                log.warning(
                    "ReliefWeb v2 rejected appname %r (HTTP %s; it may still be "
                    "pending approval) - falling back to the public RSS feed",
                    appname,
                    status,
                )
                return None
            log.warning(
                "ReliefWeb v2 query attempt %d failed (%s)",
                attempt,
                str(exc)[:160].replace("\n", " "),
            )
            continue
        if data is None:
            log.warning("ReliefWeb v2 returned an unexpected payload")
            return None
        items = data
        if items:
            break

    if items is None:
        log.warning(
            "ReliefWeb v2 was not usable this run - falling back to the public RSS feed"
        )
        return None

    candidates: List[Dict[str, Any]] = []
    for item in items:
        fields = item.get("fields") or {}
        title = _clean_cell(fields.get("title"))
        apply_url = _clean_cell(fields.get("url"))
        if not (title and apply_url):
            continue
        sources = fields.get("source") or []
        organization = (
            _clean_cell(sources[0].get("name"))
            if sources
            else "ReliefWeb partner organisation"
        )
        cities = fields.get("city") or []
        city = _clean_cell(cities[0].get("name")) if cities else ""
        created = _clean_cell((fields.get("date") or {}).get("created"))[:10]
        candidates.append(
            {
                "source": "reliefweb",
                "title": title,
                "organization": organization,
                "location_raw": city or "India",
                "description": strip_html(fields.get("body") or "")[:4000],
                "apply_url": apply_url,
                "date_posted": created,
                "matched_query": "reliefweb-v2-india",
            }
        )
    log.info("ReliefWeb v2 API produced %d India candidate(s)", len(candidates))
    return candidates


def _reliefweb_org_from_entry(entry: Dict[str, Any]) -> str:
    """Best-effort organization extraction from a ReliefWeb RSS entry."""
    raw = str(entry.get("summary") or entry.get("description") or "")
    match = re.search(
        r'class="tag source">\s*Organization:\s*(.*?)\s*</div>', raw, re.S | re.I
    )
    if match:
        return _clean_cell(html.unescape(match.group(1)))
    match = re.search(
        r"Organization:\s*(.+?)(?:\s+Closing date:|\s+Employment Type:|$)",
        strip_html(raw),
        re.I,
    )
    if match:
        return _clean_cell(match.group(1))
    return ""


def fetch_reliefweb_rss_jobs() -> List[Dict[str, Any]]:
    """Parse ReliefWeb's public India jobs RSS feed (no appname needed).

    The feed is fetched with `requests` keeping its default library
    user-agent, then parsed with feedparser. Every failure mode (WAF
    challenge page, HTTP error, missing dependency) is logged and skipped
    so the rest of the pipeline keeps running.
    """
    if requests is None and feedparser is None:
        log.warning(
            "Neither `requests` nor `feedparser` is installed - skipping the "
            "ReliefWeb RSS fallback (pip install -r scripts/requirements.txt)"
        )
        return []

    parsed = None
    if requests is not None:
        try:
            # IMPORTANT: keep requests' default library user-agent. The
            # reliefweb.int edge (AWS WAF) challenges browser-like and known
            # scraper user-agents (202 + challenge.js) but lets plain library
            # clients read the public feed.
            response = requests.get(
                RELIEFWEB_INDIA_RSS,
                headers={
                    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
                },
                timeout=REQUEST_TIMEOUT,
            )
        except Exception as exc:
            log.warning("ReliefWeb RSS request failed: %s", str(exc)[:160])
            return []
        waf_action = (response.headers.get("x-amzn-waf-action") or "").lower()
        if waf_action == "challenge" or response.status_code == 202:
            log.warning(
                "ReliefWeb RSS is behind an AWS WAF browser challenge (HTTP %s) - "
                "skipping this source this run",
                response.status_code,
            )
            return []
        if response.status_code != 200:
            log.warning(
                "ReliefWeb RSS returned HTTP %s - skipping", response.status_code
            )
            return []
        if feedparser is None:
            log.warning(
                "feedparser is not installed - cannot parse the ReliefWeb RSS "
                "feed (pip install -r scripts/requirements.txt)"
            )
            return []
        parsed = feedparser.parse(response.content)
    else:
        # No `requests` available: last-ditch direct fetch via feedparser.
        try:
            parsed = feedparser.parse(RELIEFWEB_INDIA_RSS)
        except Exception as exc:
            log.warning("ReliefWeb RSS fetch via feedparser failed: %s", str(exc)[:160])
            return []

    status = getattr(parsed, "status", None)
    entries = list(getattr(parsed, "entries", []) or [])
    if status not in (None, 200) and not entries:
        log.warning("ReliefWeb RSS feed returned HTTP %s - skipping", status)
        return []
    if not entries:
        if getattr(parsed, "bozo", False):
            log.warning(
                "ReliefWeb RSS could not be parsed (%s) - skipping",
                str(parsed.get("bozo_exception"))[:160],
            )
        else:
            log.info("ReliefWeb RSS returned no entries this run")
        return []

    candidates: List[Dict[str, Any]] = []
    for entry in entries:
        title = _clean_cell(entry.get("title"))
        apply_url = _clean_cell(entry.get("link"))
        if not (title and apply_url):
            continue
        organization = _clean_cell(entry.get("author")) or _reliefweb_org_from_entry(entry)
        date_posted = ""
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published is not None:
            try:
                date_posted = date(published[0], published[1], published[2]).isoformat()
            except (TypeError, ValueError, IndexError, AttributeError):
                date_posted = ""
        candidates.append(
            {
                "source": "reliefweb-rss",
                "title": title,
                "organization": organization or "ReliefWeb partner organisation",
                "location_raw": "India",
                "description": strip_html(
                    entry.get("summary") or entry.get("description") or ""
                )[:4000],
                "apply_url": apply_url,
                "date_posted": date_posted,
                "matched_query": "reliefweb-india-rss",
            }
        )
    log.info("ReliefWeb RSS produced %d India candidate(s)", len(candidates))
    return candidates


def fetch_reliefweb_jobs() -> List[Dict[str, Any]]:
    """ReliefWeb India source: v2 API first, public RSS feed as the fallback.

    RELIEFWEB_APPNAME (env or .env, default DEFAULT_RELIEFWEB_APPNAME) names
    this client to the API. Until ReliefWeb approves that appname every v2
    call returns 403 and the pipeline automatically continues with the
    public RSS feed, which needs no key or approval.
    """
    appname = (
        os.environ.get("RELIEFWEB_APPNAME") or DEFAULT_RELIEFWEB_APPNAME
    ).strip()
    log.info("ReliefWeb source: trying the v2 API first (appname=%r)", appname)
    jobs = fetch_reliefweb_v2_jobs(appname)
    if jobs is not None:
        return jobs
    return fetch_reliefweb_rss_jobs()


# ---------------------------------------------------------------------------
# Gemini humanizer
# ---------------------------------------------------------------------------
RETIRED_MARKERS = ("404", "not_found", "no longer available")
THROTTLE_MARKERS = (
    "429",
    "resource_exhausted",
    "rate limit",
    "rate_limit",
    "quota",
    "too many requests",
    "high demand",
    "overloaded",
    "unavailable",
    "503",
    "500",
    "deadline",
)


class GeminiRateLimited(RuntimeError):
    """Raised when every candidate Gemini model is rate-limited/overloaded."""


class GeminiHumanizer:
    """Thin adapter over either google-genai (new) or google-generativeai.

    Tries the models in MODEL_CANDIDATES in order and automatically moves to
    the next one when a model is retired ("404 ... no longer available") or
    keeps returning rate-limit/overload errors, so the daily pipeline
    survives both model deprecations and quota hiccups without edits.
    """

    def __init__(self, api_key: str, today: str) -> None:
        if _GENAI_MODE is None:
            raise RuntimeError(
                "No Gemini SDK found. Install with: pip install google-genai"
            )
        self.mode = _GENAI_MODE
        self.system_instruction = build_system_prompt(today)
        override = (os.environ.get("GEMINI_MODEL") or "").strip()
        ordered = ([override] if override else []) + list(MODEL_CANDIDATES)
        seen: Set[str] = set()
        self.model_candidates = [
            name for name in ordered if name and not (name in seen or seen.add(name))
        ]
        self.active_model: Optional[str] = None
        self.retired: Set[str] = set()
        if self.mode == "google-genai":
            self._client = _genai_new.Client(api_key=api_key)
        else:  # legacy google-generativeai
            _genai_legacy.configure(api_key=api_key)
            self._legacy_models: Dict[str, Any] = {}

    def _legacy_model(self, model_name: str):
        if model_name not in self._legacy_models:
            self._legacy_models[model_name] = _genai_legacy.GenerativeModel(
                model_name,
                system_instruction=self.system_instruction,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.4,
                },
            )
        return self._legacy_models[model_name]

    def _try_model(self, model_name: str, user_prompt: str) -> str:
        if self.mode == "google-genai":
            response = self._client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config={
                    "system_instruction": self.system_instruction,
                    "response_mime_type": "application/json",
                    "temperature": 0.4,
                },
            )
            return response.text or ""
        response = self._legacy_model(model_name).generate_content(user_prompt)
        return response.text or ""

    def complete(self, user_prompt: str) -> str:
        order = [name for name in self.model_candidates if name not in self.retired]
        if self.active_model and self.active_model in order:
            order.remove(self.active_model)
            order.insert(0, self.active_model)
        last_error: Optional[Exception] = None
        throttle_error: Optional[Exception] = None
        for index, model_name in enumerate(order):
            has_next = index < len(order) - 1
            for attempt in (1, 2):
                try:
                    text = self._try_model(model_name, user_prompt)
                    if self.active_model != model_name:
                        log.info("Using Gemini model: %s", model_name)
                        self.active_model = model_name
                    return text
                except Exception as exc:
                    last_error = exc
                    message = str(exc).lower()
                    if any(marker in message for marker in RETIRED_MARKERS):
                        self.retired.add(model_name)
                        if has_next:
                            log.warning(
                                "Gemini model %s is retired for this key; switching to the next candidate",
                                model_name,
                            )
                        break
                    if any(marker in message for marker in THROTTLE_MARKERS):
                        throttle_error = exc
                        if attempt == 1:
                            log.warning(
                                "%s is rate-limited or overloaded (%s); retrying in %.0fs | %s",
                                model_name,
                                type(exc).__name__,
                                GEMINI_RATE_LIMIT_SLEEP,
                                str(exc)[:140].replace("\n", " "),
                            )
                            time.sleep(GEMINI_RATE_LIMIT_SLEEP)
                            continue
                        if has_next:
                            log.warning(
                                "%s still rate-limited or overloaded; trying the next candidate",
                                model_name,
                            )
                        break
                    raise
        if throttle_error is not None and last_error is not None:
            raise GeminiRateLimited(str(throttle_error)[:300]) from last_error
        if last_error is not None:
            raise last_error
        raise RuntimeError("No Gemini model candidates configured")


def parse_model_json(text: str) -> Dict[str, Any]:
    """Parse the model reply, tolerating stray markdown fences."""
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("model did not return a JSON object")
    return data


def coerce_to_job_record(
    data: Dict[str, Any], candidate: Dict[str, Any], today: str
) -> (Optional[Dict[str, Any]], str):
    """Validate model output into a jobs.json record, or explain the reject."""
    if GreenJob is None:
        raise RuntimeError("pydantic is not installed")

    job = GreenJob.model_validate(data)

    if not job.is_relevant_green_job:
        return None, squash(job.rejection_reason) or "judged not a relevant Indian green job"

    category = match_enum(job.category, CATEGORIES)
    if category is None:
        return None, "unmapped category: " + squash(job.category)

    experience = match_enum(job.experience_level, EXPERIENCE_LEVELS, EXPERIENCE_ALIASES)
    if experience is None:
        return None, "unmapped experience level: " + squash(job.experience_level)

    responsibilities = [
        re.sub(r"^[\-\u2022\*\s]+", "", squash(item))
        for item in (job.key_responsibilities or [])
        if squash(item)
    ][:6]
    skills = [
        squash(item).strip(" .;")
        for item in (job.must_have_skills or [])
        if squash(item)
    ][:8]

    if len(responsibilities) < 3:
        return None, "fewer than 3 usable responsibilities"
    if len(skills) < 4:
        return None, "fewer than 4 usable skills"

    clean_title = squash(job.clean_title)
    organization = squash(job.organization)
    role_summary = squash(job.role_summary)
    application_tip = squash(job.application_tip)
    if not (clean_title and organization and role_summary and application_tip):
        return None, "missing required text fields"

    apply_url = squash(job.apply_url) or squash(candidate.get("apply_url"))
    if not apply_url.lower().startswith("http"):
        return None, "no usable apply URL"

    state = squash(job.state) or "Multiple States / Remote"
    record = {
        "id": squash(job.id),
        "date_added": today,
        "clean_title": clean_title,
        "organization": organization,
        "state": state,
        "city": squash(job.city),
        "category": category,
        "experience_level": experience,
        "role_summary": role_summary,
        "key_responsibilities": responsibilities,
        "must_have_skills": skills,
        "application_tip": application_tip,
        "apply_url": apply_url,
    }
    return record, ""


# ---------------------------------------------------------------------------
# jobs.json I/O
# ---------------------------------------------------------------------------
def resolve_default(default: Path) -> Path:
    """Find the working file from the repo root, public/ or scripts/ cwd."""
    candidates = [default, Path(default.name)]
    repo_root = Path(__file__).resolve().parent.parent
    candidates.append(repo_root / default)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def load_jobs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        log.warning("Could not read %s (%s); starting from an empty feed", path, exc)
        return []
    if not isinstance(data, list):
        log.warning("%s is not a JSON array; starting from an empty feed", path)
        return []
    return [row for row in data if isinstance(row, dict)]


def filter_valid_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Final gate: legacy/imported listings with invalid URLs never persist."""
    valid: List[Dict[str, Any]] = []
    dropped = 0
    for job in jobs:
        if is_valid_apply_url(job.get("apply_url")):
            valid.append(job)
        else:
            dropped += 1
    if dropped:
        log.warning(
            "Dropped %d listing(s) with empty/placeholder apply URLs", dropped
        )
    return valid


def write_jobs(jobs: List[Dict[str, Any]], path: Path) -> None:
    jobs = filter_valid_jobs(jobs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info("Wrote %d listing(s) to %s", len(jobs), path)


# ---------------------------------------------------------------------------
# Job lifecycle: active -> archived (records are never deleted) + stats.json
# ---------------------------------------------------------------------------
def parse_iso_date(value: Any) -> Optional[date]:
    """Parse an ISO ``YYYY-MM-DD`` date, returning None when unusable."""
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def apply_job_lifecycle(
    jobs: List[Dict[str, Any]],
    archive: List[Dict[str, Any]],
    today: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """Normalize lifecycle fields and move passed listings to the archive.

    Every active listing carries ``status: "active"`` and a ``valid_through``
    date exactly VALID_DAYS after ``date_added``. Once ``valid_through`` has
    passed, the listing moves into the archive (deduplicated by id) with
    ``status: "archived"`` and a ``date_archived`` stamp, and is never
    deleted from the registry. Returns ``(active, archive, newly_archived)``.
    """
    today_value = parse_iso_date(today) or date.today()

    archive_by_id: Dict[str, Dict[str, Any]] = {}
    for record in archive:
        record_id = str(record.get("id") or "").strip()
        if not record_id:
            continue
        record["status"] = "archived"
        record.setdefault("date_archived", today)
        added = parse_iso_date(record.get("date_added"))
        if added is not None and not record.get("valid_through"):
            record["valid_through"] = (added + timedelta(days=VALID_DAYS)).isoformat()
        archive_by_id.setdefault(record_id, record)  # dedupe by id

    active: List[Dict[str, Any]] = []
    newly_archived = 0
    for job in jobs:
        job_id = str(job.get("id") or "").strip()
        if not job_id:
            continue
        added = parse_iso_date(job.get("date_added")) or today_value
        job["date_added"] = added.isoformat()
        valid_through = added + timedelta(days=VALID_DAYS)
        job["valid_through"] = valid_through.isoformat()

        if valid_through < today_value:
            job["status"] = "archived"
            job.setdefault("date_archived", today)
            existing = archive_by_id.get(job_id)
            if existing is None:
                archive_by_id[job_id] = job
                newly_archived += 1
            else:
                existing.setdefault("date_archived", job.get("date_archived") or today)
        else:
            job["status"] = "active"
            active.append(job)

    archive_out = sorted(
        archive_by_id.values(),
        key=lambda record: (
            str(record.get("date_archived") or ""),
            str(record.get("id") or ""),
        ),
        reverse=True,
    )
    return active, archive_out, newly_archived


def compute_stats(
    active: List[Dict[str, Any]],
    archive: List[Dict[str, Any]],
    today: str,
) -> Dict[str, Any]:
    """Weekly hiring telemetry written to stats.json for the front-end."""
    today_value = parse_iso_date(today) or date.today()
    week_ago = (today_value - timedelta(days=7)).isoformat()

    by_category: Dict[str, Dict[str, int]] = {}
    for job in active:
        category = squash(job.get("category")) or "Uncategorised"
        by_category.setdefault(category, {"active": 0, "archived": 0})
        by_category[category]["active"] += 1
    for job in archive:
        category = squash(job.get("category")) or "Uncategorised"
        by_category.setdefault(category, {"active": 0, "archived": 0})
        by_category[category]["archived"] += 1

    by_state: Dict[str, int] = {}
    for job in active:
        state = squash(job.get("state"))
        if state and state != "Multiple States / Remote":
            by_state[state] = by_state.get(state, 0) + 1

    return {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "active_open_jobs": len(active),
        "opened_this_week": sum(
            1 for job in active if str(job.get("date_added") or "") >= week_ago
        ),
        "passed_this_week": sum(
            1 for job in archive if str(job.get("date_archived") or "") >= week_ago
        ),
        "total_archived_jobs": len(archive),
        "total_historical_indexed": len(active) + len(archive),
        "by_category": by_category,
        "by_state": dict(
            sorted(by_state.items(), key=lambda item: (-item[1], item[0]))
        ),
    }


def write_archive(jobs: List[Dict[str, Any]], path: Path) -> None:
    jobs = filter_valid_jobs(jobs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info("Wrote %d archived listing(s) to %s", len(jobs), path)


def write_stats(stats: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info(
        "Wrote weekly telemetry to %s (%d active, %d archived, %d passed this week)",
        path,
        stats.get("active_open_jobs", 0),
        stats.get("total_archived_jobs", 0),
        stats.get("passed_this_week", 0),
    )


# ---------------------------------------------------------------------------
# sitemap.xml generation
# ---------------------------------------------------------------------------
def write_sitemap(
    active_jobs: List[Dict[str, Any]],
    archive_jobs: List[Dict[str, Any]],
    path: Path,
) -> None:
    """Regenerate sitemap.xml for the registry.

    Includes the homepage, dashboard.html, the archive view
    (/?view=archive), the category landing views (/?category=<slug>), the
    busiest state landing views (/?state=<State>), every active listing
    (/?job=<id>, priority 0.8, lastmod = date_added) and every archived
    listing (priority 0.5, lastmod = date_archived). Any other pre-existing
    URLs (e.g. spatial-data.html?van=...) are preserved untouched.
    """
    jobs = filter_valid_jobs(active_jobs)
    archive = filter_valid_jobs(archive_jobs)
    today = date.today().isoformat()

    preserved: Dict[str, Dict[str, str]] = {}
    if path.exists():
        try:
            root = ET.parse(path).getroot()
            url_nodes = root.findall("{" + SITEMAP_NS + "}url") or root.findall("url")
            for node in url_nodes:
                loc = (node.findtext("{" + SITEMAP_NS + "}loc") or node.findtext("loc") or "").strip()
                if not loc:
                    continue
                preserved[loc] = {
                    "lastmod": (node.findtext("{" + SITEMAP_NS + "}lastmod") or node.findtext("lastmod") or "").strip(),
                    "changefreq": (node.findtext("{" + SITEMAP_NS + "}changefreq") or node.findtext("changefreq") or "").strip(),
                    "priority": (node.findtext("{" + SITEMAP_NS + "}priority") or node.findtext("priority") or "").strip(),
                }
        except Exception as exc:
            log.warning("Could not parse existing sitemap (%s); generating fresh", exc)

    entries: Dict[str, Dict[str, str]] = {}

    home_url = SITE_BASE_URL + "/"
    dash_url = SITE_BASE_URL + "/dashboard.html"
    archive_url = SITE_BASE_URL + "/?view=archive"
    home_prev = preserved.pop(home_url, {})
    dash_prev = preserved.pop(dash_url, {})
    archive_prev = preserved.pop(archive_url, {})
    entries[home_url] = {
        "lastmod": home_prev.get("lastmod") or today,
        "changefreq": "weekly",
        "priority": "1.0",
    }
    entries[dash_url] = {
        "lastmod": dash_prev.get("lastmod") or today,
        "changefreq": "weekly",
        "priority": "0.9",
    }
    latest_archived = max(
        (str(job.get("date_archived") or "") for job in archive), default=""
    )
    entries[archive_url] = {
        "lastmod": latest_archived or archive_prev.get("lastmod") or today,
        "changefreq": "weekly",
        "priority": "0.7",
    }

    # Preserve everything else that is not a generated registry URL.
    for loc, meta in preserved.items():
        if "?job=" in loc or "?category=" in loc or "?state=" in loc or "?view=" in loc:
            continue  # regenerated from the data below
        entries[loc] = {
            "lastmod": meta.get("lastmod") or today,
            "changefreq": meta.get("changefreq") or "monthly",
            "priority": meta.get("priority") or "0.6",
        }

    # Fresh checkout: seed the known static pages.
    if len(entries) <= 3:
        for page_path, changefreq, priority in STATIC_SITEMAP_PAGES:
            entries[SITE_BASE_URL + page_path] = {
                "lastmod": today,
                "changefreq": changefreq,
                "priority": priority,
            }

    # Crawlable category landing views (?category=<slug>).
    for slug in CATEGORY_SLUGS.values():
        entries[SITE_BASE_URL + "/?category=" + slug] = {
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.7",
        }

    # Busiest state landing views (?state=<State>), in rank order.
    state_counts: Dict[str, int] = {}
    for job in jobs:
        state = squash(job.get("state"))
        if state and state != "Multiple States / Remote":
            state_counts[state] = state_counts.get(state, 0) + 1
    ranked_states = sorted(state_counts.items(), key=lambda item: (-item[1], item[0]))
    for state, _count in ranked_states[:SITEMAP_TOP_STATES]:
        entries[SITE_BASE_URL + "/?state=" + quote(state)] = {
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.7",
        }

    # Every active listing, in feed order (feed order = newest first).
    for job in jobs:
        job_id = (job.get("id") or "").strip()
        if not job_id:
            continue
        entries[SITE_BASE_URL + "/?job=" + job_id] = {
            "lastmod": (job.get("date_added") or today),
            "changefreq": "daily",
            "priority": "0.8",
        }

    # Every archived listing stays in the registry as a historical record.
    for job in archive:
        job_id = (job.get("id") or "").strip()
        if not job_id:
            continue
        entries[SITE_BASE_URL + "/?job=" + job_id] = {
            "lastmod": (job.get("date_archived") or job.get("date_added") or today),
            "changefreq": "monthly",
            "priority": "0.5",
        }

    ET.register_namespace("", SITEMAP_NS)
    root = ET.Element("{" + SITEMAP_NS + "}urlset")
    for loc, meta in entries.items():
        url_node = ET.SubElement(root, "{" + SITEMAP_NS + "}url")
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}loc").text = loc
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}lastmod").text = meta["lastmod"]
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}changefreq").text = meta["changefreq"]
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}priority").text = meta["priority"]

    tree = ET.ElementTree(root)
    if hasattr(ET, "indent"):
        ET.indent(tree, space="  ")
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    log.info(
        "Wrote sitemap with %d URL(s) to %s (%d active, %d archived listing(s))",
        len(entries), path, len(jobs), len(archive),
    )


# ---------------------------------------------------------------------------
# Local .env support
# ---------------------------------------------------------------------------
def load_env_file() -> None:
    """Populate os.environ from a local .env file, if one exists.

    Existing environment variables always win, so GitHub Actions secrets and
    shell exports are never overridden. Looks in the current directory first,
    then next to the repository root (parent of scripts/).
    """
    candidates = [Path(".env"), Path(__file__).resolve().parent.parent / ".env"]
    for env_path in candidates:
        if not env_path.exists():
            continue
        loaded = 0
        try:
            for line in env_path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and value and key not in os.environ:
                    os.environ[key] = value
                    loaded += 1
        except Exception as exc:  # pragma: no cover
            log.warning("Could not read %s: %s", env_path, exc)
        log.debug("Loaded %d variable(s) from %s", loaded, env_path)
        return


def sanitize_ca_bundle_env() -> None:
    """Ignore stale CA-bundle env paths so TLS keeps working.

    Some Windows installs leave CURL_CA_BUNDLE / REQUESTS_CA_BUNDLE / 
    SSL_CERT_FILE pointing at a certificate file that no longer exists (e.g.
    an old PostgreSQL path), which makes every requests/urllib call fail TLS
    verification. When the configured path is missing, drop the variable and
    let certifi's default bundle apply.
    """
    for var in ("CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"):
        value = (os.environ.get(var) or "").strip()
        if value and not Path(value).exists():
            log.warning("%s points to a missing file (%s); ignoring it", var, value)
            os.environ.pop(var, None)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch India green jobs, humanize them with Gemini and publish "
            "jobs.json + archive.json + stats.json + sitemap.xml for "
            "urbanforestpark.com."
        )
    )
    parser.add_argument("--jobs", help="Path to jobs.json (default: public/jobs.json)")
    parser.add_argument(
        "--archive", help="Path to archive.json (default: public/archive.json)"
    )
    parser.add_argument(
        "--stats", help="Path to stats.json (default: public/stats.json)"
    )
    parser.add_argument(
        "--sitemap", help="Path to sitemap.xml (default: public/sitemap.xml)"
    )
    parser.add_argument(
        "--max-new",
        type=int,
        default=DEFAULT_MAX_NEW_PER_RUN,
        help="Maximum new listings to publish per run (default: %(default)s)",
    )
    parser.add_argument(
        "--sitemap-only",
        action="store_true",
        help="Only regenerate sitemap.xml from the current jobs.json + archive.json (no scraping, no API key needed)",
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help=(
            "Only apply lifecycle maintenance (expire passed listings into "
            "archive.json, refresh stats.json) and rewrite jobs.json / "
            "archive.json / stats.json / sitemap.xml (no scraping, no API key)"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full pipeline but do not write jobs.json, archive.json, stats.json or sitemap.xml",
    )
    parser.add_argument("--verbose", action="store_true", help="Debug logging")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # The Gemini SDK and HTTP clients chatter at INFO; keep run logs focused
    # (still fully visible with --verbose).
    noise_level = logging.DEBUG if args.verbose else logging.WARNING
    for noisy in ("httpx", "httpcore", "google_genai"):
        logging.getLogger(noisy).setLevel(noise_level)

    load_env_file()
    sanitize_ca_bundle_env()

    jobs_path = Path(args.jobs) if args.jobs else resolve_default(DEFAULT_JOBS_PATH)
    archive_path = (
        Path(args.archive) if args.archive else resolve_default(DEFAULT_ARCHIVE_PATH)
    )
    stats_path = Path(args.stats) if args.stats else resolve_default(DEFAULT_STATS_PATH)
    sitemap_path = (
        Path(args.sitemap) if args.sitemap else resolve_default(DEFAULT_SITEMAP_PATH)
    )

    existing = load_jobs(jobs_path)
    archive = load_jobs(archive_path)
    log.info(
        "Loaded %d active listing(s) from %s and %d archived listing(s) from %s",
        len(existing), jobs_path, len(archive), archive_path,
    )

    today = date.today().isoformat()

    if args.sitemap_only:
        write_sitemap(existing, archive, sitemap_path)
        return 0

    if args.sync_only:
        # Maintenance-only run: expire passed listings into the archive,
        # refresh the weekly telemetry and rewrite every published data file.
        # No scraping and no Gemini calls, so it works without an API key.
        active, archive, newly_archived = apply_job_lifecycle(existing, archive, today)
        stats = compute_stats(active, archive, today)
        write_jobs(active, jobs_path)
        write_archive(archive, archive_path)
        write_stats(stats, stats_path)
        write_sitemap(active, archive, sitemap_path)
        log.info(
            "Sync complete: %d active, %d archived (%d newly archived this run).",
            len(active), len(archive), newly_archived,
        )
        return 0

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        log.error(
            "GEMINI_API_KEY is not set. Add it to your .env file, export it as "
            "an environment variable, or use --sitemap-only / --sync-only / --dry-run."
        )
        return 1
    if GreenJob is None:
        log.error("pydantic is not installed. Run: pip install -r scripts/requirements.txt")
        return 1

    # 1. Gather raw candidates from all sources.
    log.info("Lookback window for this run: %d hour(s)", resolve_lookback_hours())
    candidates: List[Dict[str, Any]] = []
    candidates.extend(scrape_board_candidates())
    candidates.extend(fetch_targeted_green_jobs())
    candidates.extend(fetch_reliefweb_jobs())
    log.info("Collected %d raw candidate(s) from all sources", len(candidates))

    # 2. De-duplicate against the live feed and within this run.
    seen = existing_keys(existing)
    fresh: List[Dict[str, Any]] = []
    invalid_urls = 0
    for candidate in candidates:
        if not (candidate.get("title") and candidate.get("apply_url")):
            continue
        if not is_valid_apply_url(candidate.get("apply_url")):
            invalid_urls += 1
            continue
        key = dedupe_key(candidate)
        if not key or key in seen:
            continue
        seen.add(key)
        fresh.append(candidate)
    if invalid_urls:
        log.warning(
            "Skipped %d candidate(s) with empty/placeholder apply URLs", invalid_urls
        )
    total_fresh = len(fresh)
    fresh = fresh[: max(0, args.max_new)]
    log.info(
        "%d candidate(s) are new; humanizing %d (run cap=%d)",
        total_fresh, len(fresh), args.max_new,
    )

    # 3. Humanize + strict India green filter with Gemini.
    humanizer = GeminiHumanizer(api_key, today)
    taken_ids: Set[str] = {
        str(job.get("id") or "")
        for job in existing + archive
        if job.get("id")
    }
    accepted: List[Dict[str, Any]] = []
    rate_limit_streak = 0
    for index, candidate in enumerate(fresh, start=1):
        label = squash(candidate.get("title"))[:70]
        try:
            reply = humanizer.complete(build_user_prompt(candidate, today))
            data = parse_model_json(reply)
            record, reason = coerce_to_job_record(data, candidate, today)
            rate_limit_streak = 0
            if record is not None and not is_valid_apply_url(record.get("apply_url")):
                record, reason = None, "apply URL failed validation"
            if record is None:
                log.info("[%d/%d] skipped %r - %s", index, len(fresh), label, reason)
            else:
                record["id"] = unique_id(record["id"], taken_ids)
                accepted.append(record)
                log.info("[%d/%d] accepted %s", index, len(fresh), record["id"])
        except GeminiRateLimited as exc:
            rate_limit_streak += 1
            log.warning(
                "[%d/%d] Gemini rate-limited for %r (%d in a row) | %s",
                index, len(fresh), label, rate_limit_streak, str(exc)[:180],
            )
            if rate_limit_streak >= GEMINI_RATE_LIMIT_ABORT_AFTER:
                log.warning(
                    "Gemini rate limit persists after %d candidates in a row; "
                    "stopping this run early. Unprocessed candidates remain for "
                    "the next run.",
                    rate_limit_streak,
                )
                break
        except Exception as exc:
            rate_limit_streak = 0
            log.warning(
                "[%d/%d] humanizer failed for %r: %s | %s",
                index, len(fresh), label, type(exc).__name__, str(exc)[:180],
            )
        time.sleep(GEMINI_SLEEP_SECONDS)

    # 4. Merge (newest first), apply the lifecycle and persist everything.
    merged = accepted + existing
    merged.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )

    if args.dry_run:
        log.info("DRY RUN: %d new listing(s) accepted; nothing written.", len(accepted))
        return 0

    active, archive, newly_archived = apply_job_lifecycle(merged, archive, today)
    stats = compute_stats(active, archive, today)

    write_jobs(active, jobs_path)
    write_archive(archive, archive_path)
    write_stats(stats, stats_path)

    # 5. Regenerate the sitemap for Google Jobs indexing.
    write_sitemap(active, archive, sitemap_path)

    log.info(
        "Done: %d active listing(s) (%d new this run), %d archived (%d newly archived).",
        len(active), len(accepted), len(archive), newly_archived,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:  # pragma: no cover
        log.warning("Interrupted")
        sys.exit(130)
