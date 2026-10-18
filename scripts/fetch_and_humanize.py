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
  3. HUMANIZES every candidate with a Gemini Flash model (newest working
     version, with automatic fallback if one is retired). The model also runs
     a strict India + green-relevance check first: off-topic software/IT jobs
     that leaked through keyword search are marked is_relevant_green_job
     = false and never written to jobs.json.
  4. MERGES accepted listings into public/jobs.json (the file the job board
     reads at runtime; see js/jobs.js).
  5. REGENERATES public/sitemap.xml, listing the homepage, dashboard.html
     and every active job as https://www.urbanforestpark.com/?job=<id>
     with <lastmod> set to the job's date_added (plus any pre-existing
     non-job URLs are preserved).

Typical usage
-------------
    # Full daily run (requires GEMINI_API_KEY)
    python scripts/fetch_and_humanize.py

    # Rebuild sitemap.xml from jobs.json only (no API key needed)
    python scripts/fetch_and_humanize.py --sitemap-only

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
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
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

RESULTS_PER_QUERY = 25          # jobspy results wanted per search query
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
# sitemap.xml generation
# ---------------------------------------------------------------------------
def write_sitemap(jobs: List[Dict[str, Any]], path: Path) -> None:
    """Regenerate sitemap.xml: homepage + dashboard + every job as
    /?job=<id> (lastmod = date_added). Any other pre-existing URLs (e.g.
    spatial-data.html?van=...) are preserved untouched."""
    jobs = filter_valid_jobs(jobs)
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
    home_prev = preserved.pop(home_url, {})
    dash_prev = preserved.pop(dash_url, {})
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

    # Preserve everything else that is not a job URL.
    for loc, meta in preserved.items():
        if "?job=" in loc:
            continue  # regenerated from jobs.json below
        entries[loc] = {
            "lastmod": meta.get("lastmod") or today,
            "changefreq": meta.get("changefreq") or "monthly",
            "priority": meta.get("priority") or "0.6",
        }

    # Fresh checkout: seed the known static pages.
    if len(entries) <= 2:
        for page_path, changefreq, priority in STATIC_SITEMAP_PAGES:
            entries[SITE_BASE_URL + page_path] = {
                "lastmod": today,
                "changefreq": changefreq,
                "priority": priority,
            }

    # Every active listing, in feed order.
    for job in jobs:
        job_id = (job.get("id") or "").strip()
        if not job_id:
            continue
        entries[SITE_BASE_URL + "/?job=" + job_id] = {
            "lastmod": (job.get("date_added") or today),
            "changefreq": "daily",
            "priority": "0.8",
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
        "Wrote sitemap with %d URL(s) to %s (%d job listing(s))",
        len(entries), path, len(jobs),
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


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fetch India green jobs, humanize them with Gemini and publish "
            "jobs.json + sitemap.xml for urbanforestpark.com."
        )
    )
    parser.add_argument("--jobs", help="Path to jobs.json (default: public/jobs.json)")
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
        help="Only regenerate sitemap.xml from the current jobs.json (no scraping, no API key needed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full pipeline but do not write jobs.json or sitemap.xml",
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

    jobs_path = Path(args.jobs) if args.jobs else resolve_default(DEFAULT_JOBS_PATH)
    sitemap_path = (
        Path(args.sitemap) if args.sitemap else resolve_default(DEFAULT_SITEMAP_PATH)
    )

    existing = load_jobs(jobs_path)
    log.info("Loaded %d existing listing(s) from %s", len(existing), jobs_path)

    if args.sitemap_only:
        write_sitemap(existing, sitemap_path)
        return 0

    today = date.today().isoformat()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        log.error(
            "GEMINI_API_KEY is not set. Add it to your .env file, export it as "
            "an environment variable, or use --sitemap-only / --dry-run."
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
    taken_ids: Set[str] = {str(job.get("id") or "") for job in existing}
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

    # 4. Merge (newest first) and persist.
    merged = accepted + existing
    merged.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )

    if args.dry_run:
        log.info("DRY RUN: %d new listing(s) accepted; nothing written.", len(accepted))
        return 0

    if not accepted:
        log.info(
            "No new listings accepted this run - jobs.json and sitemap.xml unchanged."
        )
        return 0

    write_jobs(merged, jobs_path)

    # 5. Regenerate the sitemap for Google Jobs indexing.
    write_sitemap(merged, sitemap_path)

    log.info(
        "Done: %d listing(s) in the feed (%d new this run).",
        len(merged), len(accepted),
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:  # pragma: no cover
        log.warning("Interrupted")
        sys.exit(130)
