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
  4. HARVESTS Indian academic, JRF/SRF, PhD and contractual institute
     vacancies through public Google News RSS searches (WII, ICFRE, IIFM,
     IIRS, NRSC, ATREE, CEEW, TERI, GBPNIHE, ICAR, MoEFCC and similar
     bodies advertise contractual roles outside the big job boards). Every
     headline is screened for job-ad phrasing before humanizing, and the
     links route through Google News to the underlying announcement.
  5. HUMANIZES every candidate with a Gemini Flash model (newest working
     version, with automatic fallback if one is retired). The model also runs
     a strict India + green-relevance check first: off-topic software/IT jobs
     that leaked through keyword search are marked is_relevant_green_job
     = false and never written to jobs.json.
  6. MERGES accepted listings into public/jobs.json (the file the job board
     reads at runtime; see js/jobs.js), stamps every listing with its
     lifecycle fields (status + valid_through) and MOVES listings whose
     30-day window has passed into public/archive.json - past mandates are
     preserved for institutional reference and never deleted.
  7. REGENERATES public/sitemap.xml (homepage, dashboard, archive view,
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

    # Pre-render the static SEO directory inside index.html plus the five
    # career-pathway hub pages (run after the pipeline; no API key needed)
    python scripts/build_seo_pages.py

    # One-time bootstrap of Indian academic / JRF / PhD seed listings
    python scripts/seed_academic_jobs.py

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
import base64
import html
import inspect
import json
import logging
import math
import os
import re
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote, urlencode, urljoin, urlparse
from xml.etree import ElementTree as ET

# Official-link gate (Phase 3): every candidate is verified at its source
# before anything is written. Kept in its own module so pytest exercises the
# exact code path used by the daily pipeline.
from ingestion_gate import (
    deadline_date,
    dedupe_hash,
    find_employer,
    gate_candidate,
    load_registry,
    quarantine_record,
)
from source_expansion import (
    SOURCE_LIMITS,
    STATE_QUERIES,
    fetch_ats_feeds,
    fetch_freejobalert,
    fetch_official_pages,
    write_source_report,
)

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
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

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
DEFAULT_DIGEST_JSON_PATH = Path("public/daily_digest.json")
DEFAULT_WHATSAPP_DIGEST_PATH = Path("public/whatsapp_digest.txt")

# Community channels printed inside every digest (override via env or .env).
WHATSAPP_GROUP_URL = "https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw"
TELEGRAM_CHANNEL_URL = "https://t.me/urbanforestpark"

# Job lifecycle: a listing stays "active" in jobs.json for VALID_DAYS after
# its date_added; once valid_through has passed it moves into archive.json
# (status "archived", date_archived stamped) and is never deleted.
VALID_DAYS = 30

RESULTS_PER_QUERY = 50          # jobspy results wanted per search query (was 15)
REQUEST_TIMEOUT = 30            # seconds; HTTP timeout for ReliefWeb calls
DEFAULT_LOOKBACK_HOURS = 72     # posting-age window; LOOKBACK_HOURS env overrides
DEFAULT_MAX_NEW_PER_RUN = 60    # cap on Gemini calls per run (was 12)
GEMINI_SLEEP_SECONDS = 4.0      # gentle rate limit between model calls
GEMINI_RATE_LIMIT_SLEEP = 25.0  # longer pause when rate-limited/overloaded
GEMINI_RATE_LIMIT_ABORT_AFTER = 3  # consecutive rate-limited candidates -> stop run

# Board coverage: prefer all three; if any single board throws (upstream
# layout changes happen), retry the query with the stable pair so the
# pipeline never halts.
PRIMARY_SITES = ["linkedin", "indeed", "naukri"]
FALLBACK_SITES = ["linkedin", "indeed"]

# India-specific high-intent search queries covering every pillar of the
# registry: climate/ESG/carbon, forestry & wildlife, GIS & remote sensing,
# JRF/SRF project staff, research fellowships, PhD/postdoc, environmental
# engineering/EHS, CSR & livelihoods, and urban planning/green building.
SEARCH_QUERIES = [
    "Climate Change Sustainability India",
    "ESG BRSR Carbon Credits Net Zero India",
    "Forestry Wildlife Afforestation Ecology Conservation India",
    "GIS Remote Sensing Earth Engine Geoinformatics India",
    "JRF SRF Project Associate Environmental Science Forestry",
    "Research Associate Fellow Climate Ecology Agriculture India",
    "PhD Postdoctoral Fellowship Environmental Climate Sustainability",
    "Environmental Engineer EHS Sustainability Manager India",
    "CSR Development Sector Environment Livelihoods India",
    "Urban Planner Green Building Urban Heat Island Sustainability",
    "Walk in Interview Project Associate GIS Remote Sensing Forestry",
    "Faculty Assistant Professor Environmental Science Sustainability India",
    # Grants, funding calls & research fellowships (India + open-to-India).
    "Research Grant Funding Call Proposal Climate Environment India",
    "DST SERB ANRF Project Grant Call Environment Climate",
    "Conservation Seed Grant Innovation Funding India Biodiversity",
    # Scholarships & doctoral support.
    "Scholarship PhD Fellowship Climate Environment Sustainability India",
    "International Scholarship Master Climate Sustainability India eligible",
    "Travel Grant Conference Scholarship Environment Research India",
    # Fellowships & leadership programmes.
    "Climate Fellowship Leadership Programme India",
    "Policy Fellowship Environment Think Tank India",
    "Postdoctoral Fellowship Climate Sustainability India",
    # Internships & student traineeships.
    "Internship Environment Climate Sustainability Student India",
    "Summer Internship Forestry Ecology Research India",
    "ESG Sustainability Internship Corporate India",
    # Competitions, hackathons & awards.
    "Sustainability Challenge Climate Hackathon Competition India",
    "Youth Innovation Prize Environment Climate India",
    "Green Tech Competition Award Students India",
    # Adjacent sustainability domains (water, energy, agriculture, waste...).
    "Water Resources WASH Climate India Jobs",
    "Sustainable Agriculture Agroforestry Remote Sensing India",
    "Renewable Energy Solar Wind Green Hydrogen Jobs India",
    "Biodiversity Marine Conservation Ecology Jobs India",
    "Circular Economy Waste Management Sustainability India",
    "Rural Livelihoods Natural Resource Management India",
    "Disaster Resilience Climate Adaptation Jobs India",
]

# Policy v2: cover the 15 states/regions that previously had few or no
# listings. One combined high-intent query per state keeps the sweep bounded.
SEARCH_QUERIES.extend(STATE_QUERIES)

# Front-end vocabulary (must match index.html filters, js/jobs.js and the
# values inside jobs.json / archive.json).
CATEGORIES = [
    "Academic, JRF, SRF & PhD Positions",
    "Research Associate & Project Staff (Contractual)",
    "Forestry, Wildlife & Afforestation",
    "GIS, Remote Sensing & Earth Observation",
    "ESG, Carbon Markets & Corporate Sustainability",
    "Climate Policy, Think-Tanks & Fellowships",
    "Grants & Research Funding",
    "Scholarships & Doctoral Support",
    "Fellowships & Leadership Programs",
    "Internships & Student Traineeships",
    "Competitions, Hackathons & Awards",
]

# Pre-upgrade category names still present in published data (jobs.json /
# archive.json written before this schema expansion). normalize_job_fields()
# maps them onto the list above so historical records stay filterable.
LEGACY_CATEGORY_MAP = {
    "Climate & Sustainability": "ESG, Carbon Markets & Corporate Sustainability",
    "ESG & Carbon Markets": "ESG, Carbon Markets & Corporate Sustainability",
    "Forestry & Afforestation": "Forestry, Wildlife & Afforestation",
    "GIS, Remote Sensing & UHI": "GIS, Remote Sensing & Earth Observation",
    "Environmental Policy & Fellowships": "Climate Policy, Think-Tanks & Fellowships",
}

# URL slugs for the crawlable category landing views (?category=<slug>).
# js/jobs.js maps the same slugs back to the display names above and keeps
# accepting the pre-upgrade slugs as aliases.
CATEGORY_SLUGS = {
    "Academic, JRF, SRF & PhD Positions": "academic-jrf-srf-phd",
    "Research Associate & Project Staff (Contractual)": "research-associate-project-staff",
    "Forestry, Wildlife & Afforestation": "forestry-wildlife-afforestation",
    "GIS, Remote Sensing & Earth Observation": "gis-remote-sensing-earth-observation",
    "ESG, Carbon Markets & Corporate Sustainability": "esg-carbon-sustainability",
    "Climate Policy, Think-Tanks & Fellowships": "climate-policy-think-tanks-fellowships",
    "Grants & Research Funding": "grants-research-funding",
    "Scholarships & Doctoral Support": "scholarships-doctoral-support",
    "Fellowships & Leadership Programs": "fellowships-leadership-programs",
    "Internships & Student Traineeships": "internships-student-traineeships",
    "Competitions, Hackathons & Awards": "competitions-hackathons-awards",
}

# Opportunity kinds carried by every record (badges + the Opportunity Type
# filter). "Job / Career" is the default for employment records; the other
# values cover grants, scholarships, fellowships, internships and
# competitions & awards.
OPPORTUNITY_KINDS = [
    "Job / Career",
    "Fellowship",
    "Scholarship",
    "Grant / Funding",
    "Internship",
    "Competition / Award",
]

# Region vocabulary for the strictly separated Global opportunities registry
# (global_jobs.json / global_archive.json). India records never carry these
# values; global records always carry exactly one.
GLOBAL_REGIONS = [
    "Global / Remote",
    "Europe",
    "North America",
    "Asia-Pacific",
    "Africa & Middle East",
    "Latin America",
    "UN / Multilateral",
]

# Position types carried by every record (badges on cards + dossiers, the
# career-track quick filters, and the JobPosting JSON-LD employmentType).
POSITION_TYPES = [
    "JRF / SRF",
    "PhD / Doctoral Fellowship",
    "Project Associate / Research Associate",
    "Young Professional / Consultant (Contractual)",
    "Faculty / Academic",
    "Full-Time Corporate / NGO",
    "Fellowship / Internship",
]

# Static career-pathway hub pages (regenerated by scripts/build_seo_pages.py
# after every pipeline run and listed in the sitemap at priority 0.9).
SEO_HUB_PAGES = [
    "/jrf-srf-project-associate-jobs.html",
    "/phd-fellowships-climate-sustainability.html",
    "/forestry-wildlife-government-jobs.html",
    "/gis-remote-sensing-climate-jobs.html",
    "/esg-carbon-sustainability-jobs.html",
]

# Multilingual & regional portals (Hindi + pan-India regional hubs),
# pre-rendered by scripts/build_seo_pages.py on every pipeline run.
MULTILINGUAL_PORTAL_PAGES = [
    "/hindi-environment-forestry-jobs.html",
    "/bharat-regional-green-jobs.html",
]

# Global opportunities portal (strictly separated from the India registry),
# pre-rendered by scripts/build_seo_pages.py from global_jobs.json.
GLOBAL_PORTAL_PAGES = [
    "/global-climate-sustainability-opportunities.html",
]

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
    ("/explore-dashboard.html", "monthly", "0.7"),
    ("/spatial-data.html", "weekly", "0.9"),
    ("/green-calculator.html", "monthly", "0.8"),
    ("/green-calculator-report.html", "monthly", "0.7"),
    ("/green-calculator-app.html", "monthly", "0.6"),
    ("/nagar-van-finder.html", "weekly", "0.8"),
    ("/global-climate-sustainability-opportunities.html", "weekly", "0.9"),
    ("/public-survey.html", "monthly", "0.6"),
    ("/report.html", "monthly", "0.7"),
    ("/privacy.html", "yearly", "0.3"),
    ("/terms.html", "yearly", "0.3"),
    ("/cookies.html", "yearly", "0.3"),
    ("/accessibility.html", "yearly", "0.3"),
]

SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

# ---------------------------------------------------------------------------
# Indian institution & company domain directory.
#
# Maps the organisations this board publishes most often onto their exact
# official website + clean root domain. Records matched here always carry a
# verified org_website/org_domain, which powers the "Visit Official Website"
# button, the readable link pills and the official institution logo lookup.
# Entries are `(alias, website, domain)`; the alias is matched against the
# lowercased organisation name on word boundaries. Longer aliases win.
# ---------------------------------------------------------------------------
KNOWN_INDIAN_ORGS: List[Tuple[str, str, str]] = [
    # Forests, wildlife & environment (institutes and regulators)
    ("wildlife institute of india", "https://wii.gov.in", "wii.gov.in"),
    ("wii dehradun", "https://wii.gov.in", "wii.gov.in"),
    ("wii", "https://wii.gov.in", "wii.gov.in"),
    ("indian council of forestry research and education", "https://icfre.gov.in", "icfre.gov.in"),
    ("indian council of forestry research & education", "https://icfre.gov.in", "icfre.gov.in"),
    ("icfre", "https://icfre.gov.in", "icfre.gov.in"),
    ("forest research institute", "https://fridu.edu.in", "fridu.edu.in"),
    ("indian institute of forest management", "https://www.iifm.ac.in", "iifm.ac.in"),
    ("iifm", "https://www.iifm.ac.in", "iifm.ac.in"),
    ("forest survey of india", "https://fsi.nic.in", "fsi.nic.in"),
    ("ministry of environment, forest and climate change", "https://moef.gov.in", "moef.gov.in"),
    ("ministry of environment forest and climate change", "https://moef.gov.in", "moef.gov.in"),
    ("moefcc", "https://moef.gov.in", "moef.gov.in"),
    ("central pollution control board", "https://cpcb.nic.in", "cpcb.nic.in"),
    ("cpcb", "https://cpcb.nic.in", "cpcb.nic.in"),
    ("g.b. pant", "https://gbpihed.gov.in", "gbpihed.gov.in"),
    ("gbpnihe", "https://gbpihed.gov.in", "gbpihed.gov.in"),
    ("gbpihed", "https://gbpihed.gov.in", "gbpihed.gov.in"),
    ("salim ali centre", "https://sacon.in", "sacon.in"),
    ("sacon", "https://sacon.in", "sacon.in"),
    ("wildlife trust of india", "https://www.wti.org.in", "wti.org.in"),
    ("wildlife conservation society", "https://india.wcs.org", "wcs.org"),
    ("bombay natural history society", "https://www.bnhs.org", "bnhs.org"),
    ("bnhs", "https://www.bnhs.org", "bnhs.org"),
    ("nature conservation foundation", "https://www.ncf-india.org", "ncf-india.org"),
    ("foundation for ecological security", "https://fes.org.in", "fes.org.in"),
    ("centre for wildlife studies", "https://cwsindia.org", "cwsindia.org"),
    ("centre for science and environment", "https://www.cseindia.org", "cseindia.org"),
    ("cse india", "https://www.cseindia.org", "cseindia.org"),
    # Geospatial & earth observation
    ("indian institute of remote sensing", "https://www.iirs.gov.in", "iirs.gov.in"),
    ("iirs", "https://www.iirs.gov.in", "iirs.gov.in"),
    ("national remote sensing cent", "https://www.nrsc.gov.in", "nrsc.gov.in"),
    ("nrsc", "https://www.nrsc.gov.in", "nrsc.gov.in"),
    ("indian space research organisation", "https://www.isro.gov.in", "isro.gov.in"),
    ("isro", "https://www.isro.gov.in", "isro.gov.in"),
    ("indian institute of tropical meteorology", "https://www.tropmet.res.in", "tropmet.res.in"),
    ("national institute of oceanography", "https://www.nio.org", "nio.org"),
    ("wadia institute", "https://www.wihg.res.in", "wihg.res.in"),
    ("birbal sahni", "https://bsip.res.in", "bsip.res.in"),
    # Research councils & funders
    ("indian council of agricultural research", "https://icar.org.in", "icar.org.in"),
    ("icar", "https://icar.org.in", "icar.org.in"),
    ("council of scientific and industrial research", "https://www.csir.res.in", "csir.res.in"),
    ("csir", "https://www.csir.res.in", "csir.res.in"),
    ("department of biotechnology", "https://dbtindia.gov.in", "dbtindia.gov.in"),
    ("department of science and technology", "https://dst.gov.in", "dst.gov.in"),
    ("niti aayog", "https://niti.gov.in", "niti.gov.in"),
    # Universities & academia
    ("indian institute of science", "https://iisc.ac.in", "iisc.ac.in"),
    ("iisc", "https://iisc.ac.in", "iisc.ac.in"),
    ("iit delhi", "https://home.iitd.ac.in", "iitd.ac.in"),
    ("iit bombay", "https://www.iitb.ac.in", "iitb.ac.in"),
    ("iit madras", "https://www.iitm.ac.in", "iitm.ac.in"),
    ("iit kharagpur", "https://www.iitkgp.ac.in", "iitkgp.ac.in"),
    ("iit roorkee", "https://www.iitr.ac.in", "iitr.ac.in"),
    ("iit kanpur", "https://www.iitk.ac.in", "iitk.ac.in"),
    ("iit guwahati", "https://www.iitg.ac.in", "iitg.ac.in"),
    ("banaras hindu university", "https://www.bhu.ac.in", "bhu.ac.in"),
    ("bhu", "https://www.bhu.ac.in", "bhu.ac.in"),
    ("tata institute of social sciences", "https://www.tiss.edu", "tiss.edu"),
    ("tiss", "https://www.tiss.edu", "tiss.edu"),
    ("azim premji university", "https://azimpremjiuniversity.edu.in", "azimpremjiuniversity.edu.in"),
    ("azim premji foundation", "https://azimpremjifoundation.org", "azimpremjifoundation.org"),
    ("jawaharlal nehru university", "https://www.jnu.ac.in", "jnu.ac.in"),
    ("jnu", "https://www.jnu.ac.in", "jnu.ac.in"),
    ("university of delhi", "https://www.du.ac.in", "du.ac.in"),
    ("delhi university", "https://www.du.ac.in", "du.ac.in"),
    ("jamia millia islamia", "https://jmi.ac.in", "jmi.ac.in"),
    ("aligarh muslim university", "https://www.amu.ac.in", "amu.ac.in"),
    ("indira gandhi national open university", "https://ignou.ac.in", "ignou.ac.in"),
    ("ignou", "https://ignou.ac.in", "ignou.ac.in"),
    ("national centre for biological sciences", "https://www.ncbs.res.in", "ncbs.res.in"),
    ("ncbs", "https://www.ncbs.res.in", "ncbs.res.in"),
    ("teri school", "https://www.terisas.ac.in", "terisas.ac.in"),
    ("terisas", "https://www.terisas.ac.in", "terisas.ac.in"),
    # Think tanks, NGOs & foundations
    ("council on energy, environment and water", "https://www.ceew.in", "ceew.in"),
    ("ceew", "https://www.ceew.in", "ceew.in"),
    ("wri india", "https://wri-india.org", "wri-india.org"),
    ("world resources institute", "https://wri-india.org", "wri-india.org"),
    ("the energy and resources institute", "https://www.teriin.org", "teriin.org"),
    ("teri", "https://www.teriin.org", "teriin.org"),
    ("wwf-india", "https://www.wwfindia.org", "wwfindia.org"),
    ("wwf india", "https://www.wwfindia.org", "wwfindia.org"),
    ("atree", "https://www.atree.org", "atree.org"),
    ("ashoka trust for research in ecology", "https://www.atree.org", "atree.org"),
    ("cstep", "https://cstep.in", "cstep.in"),
    ("development alternatives", "https://www.devalt.org", "devalt.org"),
    ("vasudha foundation", "https://www.vasudhafoundation.in", "vasudhafoundation.in"),
    ("shakti sustainable energy foundation", "https://shaktifoundation.in", "shaktifoundation.in"),
    ("centre for policy research", "https://cprindia.org", "cprindia.org"),
    ("observer research foundation", "https://www.orfonline.org", "orfonline.org"),
    ("india climate collaborative", "https://indiaclimatecollaborative.org", "indiaclimatecollaborative.org"),
    ("nrdc india", "https://www.nrdc.org", "nrdc.org"),
    # International agencies
    ("united nations development programme", "https://www.undp.org/india", "undp.org"),
    ("undp", "https://www.undp.org/india", "undp.org"),
    ("united nations environment programme", "https://www.unep.org", "unep.org"),
    ("unep", "https://www.unep.org", "unep.org"),
    ("iucn", "https://www.iucn.org", "iucn.org"),
    ("world bank", "https://www.worldbank.org", "worldbank.org"),
    ("international finance corporation", "https://www.ifc.org", "ifc.org"),
    ("asian development bank", "https://www.adb.org", "adb.org"),
    ("global environment facility", "https://www.thegef.org", "thegef.org"),
    ("international water management institute", "https://www.iwmi.cgiar.org", "iwmi.cgiar.org"),
    ("iwmi", "https://www.iwmi.cgiar.org", "iwmi.cgiar.org"),
    ("icrisat", "https://www.icrisat.org", "icrisat.org"),
    ("cgiar", "https://www.cgiar.org", "cgiar.org"),
    # Corporate sustainability, ESG & consultancy
    ("ernst & young", "https://www.ey.com/en_in", "ey.com"),
    ("ernst and young", "https://www.ey.com/en_in", "ey.com"),
    ("ey india", "https://www.ey.com/en_in", "ey.com"),
    ("kpmg", "https://kpmg.com/in", "kpmg.com"),
    ("deloitte", "https://www2.deloitte.com/in", "deloitte.com"),
    ("pricewaterhousecoopers", "https://www.pwc.in", "pwc.in"),
    ("pwc", "https://www.pwc.in", "pwc.in"),
    ("jpmorgan", "https://www.jpmorganchase.com", "jpmorganchase.com"),
    ("j.p. morgan", "https://www.jpmorganchase.com", "jpmorganchase.com"),
    ("larsen & toubro", "https://www.larsentoubro.com", "larsentoubro.com"),
    ("larsen and toubro", "https://www.larsentoubro.com", "larsentoubro.com"),
    ("l&t", "https://www.larsentoubro.com", "larsentoubro.com"),
    ("jsw", "https://www.jsw.in", "jsw.in"),
    ("tata steel", "https://www.tatasteel.com", "tatasteel.com"),
    ("tata power", "https://www.tatapower.com", "tatapower.com"),
    ("itc limited", "https://www.itcportal.com", "itcportal.com"),
    ("itc", "https://www.itcportal.com", "itcportal.com"),
    ("godrej", "https://www.godrej.com", "godrej.com"),
    ("hindustan unilever", "https://www.hul.co.in", "hul.co.in"),
    ("schneider electric", "https://www.se.com/in", "se.com"),
    ("siemens", "https://www.siemens.com", "siemens.com"),
    ("arcadis", "https://www.arcadis.com", "arcadis.com"),
    ("arup", "https://www.arup.com", "arup.com"),
    ("ramboll", "https://www.ramboll.com", "ramboll.com"),
    ("erm", "https://www.erm.com", "erm.com"),
    ("wsp", "https://www.wsp.com", "wsp.com"),
    # Energy & PSUs
    ("ntpc", "https://www.ntpc.co.in", "ntpc.co.in"),
    ("nhpc", "https://www.nhpcindia.com", "nhpcindia.com"),
    ("ongc", "https://ongcindia.com", "ongcindia.com"),
    ("gail", "https://gailonline.com", "gailonline.com"),
    ("indian oil", "https://iocl.com", "iocl.com"),
    ("bharat petroleum", "https://www.bharatpetroleum.in", "bharatpetroleum.in"),
    ("steel authority of india", "https://sail.co.in", "sail.co.in"),
    ("power grid corporation", "https://www.powergrid.in", "powergrid.in"),
    # Additional employers observed in the live registry (verified domains)
    ("indian institute of technology guwahati", "https://www.iitg.ac.in", "iitg.ac.in"),
    ("indian institute of technology delhi", "https://home.iitd.ac.in", "iitd.ac.in"),
    ("indian institute of technology bombay", "https://www.iitb.ac.in", "iitb.ac.in"),
    ("indian institute of technology madras", "https://www.iitm.ac.in", "iitm.ac.in"),
    ("indian institute of technology kharagpur", "https://www.iitkgp.ac.in", "iitkgp.ac.in"),
    ("indian institute of technology roorkee", "https://www.iitr.ac.in", "iitr.ac.in"),
    ("indian institute of technology kanpur", "https://www.iitk.ac.in", "iitk.ac.in"),
    ("indian institute for human settlements", "https://iihs.co.in", "iihs.co.in"),
    ("international crops research institute", "https://www.icrisat.org", "icrisat.org"),
    ("international forum for environment, sustainability & technology", "https://iforest.in", "iforest.in"),
    ("iforest", "https://iforest.in", "iforest.in"),
    ("tüv süd", "https://www.tuvsud.com", "tuvsud.com"),
    ("tuv sud", "https://www.tuvsud.com", "tuvsud.com"),
    ("colgate-palmolive", "https://www.colgatepalmolive.com", "colgatepalmolive.com"),
    ("colgate", "https://www.colgatepalmolive.com", "colgatepalmolive.com"),
    ("avantor", "https://www.avantorsciences.com", "avantorsciences.com"),
    ("ecolab", "https://www.ecolab.com", "ecolab.com"),
    ("intertek", "https://www.intertek.com", "intertek.com"),
    ("amazon", "https://www.amazon.in", "amazon.in"),
    ("castrol", "https://www.castrol.com", "castrol.com"),
    ("ntt data", "https://www.nttdata.com", "nttdata.com"),
    ("redington", "https://www.redingtongroup.com", "redingtongroup.com"),
    ("accelleron", "https://www.accelleron.com", "accelleron.com"),
    ("quest global", "https://www.quest-global.com", "quest-global.com"),
    ("aditya birla fashion", "https://www.abfrl.com", "abfrl.com"),
    ("yulu", "https://www.yulu.bike", "yulu.bike"),
    ("selco foundation", "https://selcofoundation.org", "selcofoundation.org"),
    ("global energy alliance for people and planet", "https://energyalliance.org", "energyalliance.org"),
    ("sambodhi research", "https://sambodhi.co.in", "sambodhi.co.in"),
    ("anant national university", "https://anu.edu.in", "anu.edu.in"),
    ("administrative staff college", "https://www.asci.org.in", "asci.org.in"),
    ("access development services", "https://www.accessdev.org", "accessdev.org"),
    ("liter of light", "https://literoflight.org", "literoflight.org"),
    ("jpmorganchase", "https://www.jpmorganchase.com", "jpmorganchase.com"),
    ("jpmorgan chase", "https://www.jpmorganchase.com", "jpmorganchase.com"),
    ("metro global solution center", "https://www.metro.co.in", "metro.co.in"),
    ("lic housing", "https://www.lichousing.com", "lichousing.com"),
    ("loom solar", "https://www.loomsolar.com", "loomsolar.com"),
    ("cundall", "https://www.cundall.com", "cundall.com"),
    ("cotecna", "https://www.cotecna.com", "cotecna.com"),
    ("deif", "https://www.deif.com", "deif.com"),
    ("desri", "https://www.desri.com", "desri.com"),
    ("naandi", "https://www.naandi.org", "naandi.org"),
]

# Aliases too short/ambiguous for substring matching: the organisation name
# must match the full normalized string exactly.
EXACT_ORG_NAMES: Dict[str, Tuple[str, str]] = {
    "path": ("https://www.path.org", "path.org"),
    "asci": ("https://www.asci.org.in", "asci.org.in"),
    "ey": ("https://www.ey.com/en_in", "ey.com"),
}

# Hosts that are job boards / aggregators / social platforms - never used as
# an organisation's own website, and matched for readable source labels.
JOB_BOARD_HOSTS = (
    "linkedin.com", "indeed.com", "naukri.com", "news.google.com", "google.com",
    "reliefweb.int", "glassdoor.com", "glassdoor.co.in", "monsterindia.com",
    "foundit.in", "shine.com", "timesjobs.com", "internshala.com", "unstop.com",
    "freshersworld.com", "hirist.com", "cutshort.io", "upwork.com",
    "facebook.com", "twitter.com", "x.com", "t.me", "instagram.com",
    "youtube.com", "indeed.co.in",
)

# Readable portal names keyed by host suffix for the "Apply on ..." button.
SOURCE_PORTAL_BY_HOST = (
    ("linkedin.com", "LinkedIn"),
    ("indeed.com", "Indeed"),
    ("naukri.com", "Naukri"),
    ("news.google.com", "News Announcement"),
    ("reliefweb.int", "ReliefWeb"),
    ("indiabioscience.org", "IndiaBioscience"),
    ("unstop.com", "Unstop"),
    ("internshala.com", "Internshala"),
    ("glassdoor.com", "Glassdoor"),
    ("foundit.in", "Foundit"),
    ("shine.com", "Shine"),
    ("timesjobs.com", "TimesJobs"),
)

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
        position_type: str = ""
        # Opportunity kind spans jobs, fellowships, scholarships, grants,
        # internships and competitions; deadline_or_window carries the
        # application window when the source states one.
        opportunity_kind: str = ""
        deadline_or_window: str = ""
        # Global-registry fields (empty for India records).
        region: str = ""
        country: str = ""
        qualification_summary: str = ""
        compensation_or_fellowship: str = ""
        role_summary: str = ""
        # Bilingual (Hindi) metadata: shown when the interface is switched
        # to हिंदी and on the Hindi SEO hub page. Acronyms (JRF, SRF, GIS,
        # ESG, PhD, BRSR ...) and organisation names stay in Latin script.
        title_hi: str = ""
        summary_hi: str = ""
        key_responsibilities: List[str] = Field(default_factory=list)
        must_have_skills: List[str] = Field(default_factory=list)
        application_tip: str = ""
        apply_url: str = ""
        org_website: str = ""
        org_domain: str = ""
        source_portal: str = ""

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
  (a) The opportunity is genuinely about the environment, climate change, \
forestry, afforestation, wildlife/ecology, sustainability, ESG, CSR, carbon \
markets, clean/renewable energy, water, agriculture (sustainability angle), \
urban planning/green infrastructure, or geospatial / remote-sensing / GIS \
analysis of natural or built environments. All CORE domains are in scope, and \
these closely connected ADJACENT domains are equally in scope: water resources \
& WASH, sustainable agriculture & agroforestry, clean/renewable energy \
(solar, wind, green hydrogen, energy transition), biodiversity & marine \
conservation, circular economy & waste management, rural livelihoods & \
natural-resource management, disaster resilience & climate adaptation, and \
green urban planning & sustainable mobility. Every opportunity KIND is in \
scope: jobs, grants & research funding calls, scholarships & doctoral \
support, fellowships & leadership programmes, internships & traineeships, \
and competitions / hackathons / awards. Academic, JRF/SRF, doctoral, \
postdoctoral, faculty and project-staff positions in these fields are fully \
in scope. Generic software, IT support, sales, marketing, finance, HR or QA \
postings, pure mechanical or civil design roles with no environmental scope, \
and any listing that asks the candidate to pay a fee, deposit or investment \
are out of scope even in green companies, unless the role itself works on \
the domains above.
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
- opportunity_kind: EXACTLY ONE of: {kinds}. Use "Job / Career" for \
employment; "Fellowship" for research/leadership fellowships (JRF, SRF, \
postdoctoral and similar); "Scholarship" for funded study or doctoral \
support; "Grant / Funding" for project, seed, innovation or travel funding \
calls; "Internship" for internships and traineeships; "Competition / Award" \
for challenges, hackathons, prizes and awards.
- deadline_or_window: the application deadline or window ONLY when the \
source states one (e.g. "Apply by 15 Nov 2026" or "Open until filled"); \
otherwise the exact string "Rolling / Open". Never invent dates.
- experience_level: EXACTLY ONE of: {experience}
- position_type: EXACTLY ONE of: {position_types}. Use "JRF / SRF" and \
"Project Associate / Research Associate" for funded research-project posts, \
"Young Professional / Consultant (Contractual)" for scheme-based government \
contract roles, "PhD / Doctoral Fellowship" for doctoral and postdoctoral \
positions, "Faculty / Academic" for teaching posts, "Fellowship / Internship" \
for entry fellowships and internships, and "Full-Time Corporate / NGO" for \
permanent staff roles.
- qualification_summary: one short line with the degree / exam requirements \
(e.g. "M.Sc. Environmental Science / Forestry / Geoinformatics (NET/GATE \
preferred or exempted)", "Master's in Sustainability / Management", "PhD in \
Ecology / Atmospheric Science"). When the source does not state them, write \
the standard requirement for that position_type.
- compensation_or_fellowship: the stipend or salary ONLY when the source \
states one (e.g. "₹37,000 - ₹42,000/month + HRA (DST/CSIR norms)"). \
Otherwise write "As per institute norms" for academic / contractual roles, or \
"Not disclosed - see official portal" for corporate roles. Never invent \
figures.
- role_summary: exactly 3 sentences, 45-70 words, concrete and specific \
to THIS role (team, mandate, location, impact). No generic filler.
- title_hi: the job title written in formal Hindi (Devanagari script), \
keeping the organisation name in its original Latin form and keeping \
acronyms (JRF, SRF, GIS, ESG, PhD, BRSR, IIT, IISc, IIFM, WII ...) in Latin \
script. Example: "जूनियर रिसर्च फेलो (JRF) - बाघ पारिस्थितिकी एवं परिदृश्य कनेक्टिविटी - Wildlife Institute of India (WII)". Use natural formal Hindi as \
printed in Indian government recruitment notices - never romanised English.
- summary_hi: exactly 2 formal Hindi sentences (Devanagari) summarising the \
role and its eligibility for Hindi-speaking candidates. Keep technical \
terms and acronyms in Latin script and organisation names in English.
- key_responsibilities: 4-5 short bullets, each a plain sentence fragment \
starting with a verb. Only what the source posting supports.
- must_have_skills: 5-7 short skill tags (e.g. "ESG reporting (BRSR)", \
"QGIS", "carbon accounting"). Mix technical and domain skills.
- application_tip: 1-2 sentences of practical, editor-style advice for an \
Indian applicant (portfolio, GIS samples, BRSR familiarity, fieldwork \
experience, certifications). Never mention that this tip was AI-written.
- apply_url: copy the source URL EXACTLY as provided.
- org_website: the hiring organisation's official website or careers page, \
ONLY when you are genuinely confident it is theirs (e.g. "https://wii.gov.in" \
for Wildlife Institute of India, "https://www.ceew.in", "https://icfre.gov.in"). \
Use an empty string when unsure - never guess a domain.
- org_domain: the root domain of org_website without "https://" or "www." \
(e.g. "wii.gov.in", "ceew.in", "ey.com"). Empty string when org_website is empty.
- source_portal: where apply_url points; exactly one of "LinkedIn", "Indeed", \
"Naukri", "ReliefWeb", "IndiaBioscience", "Official Institute Portal", \
"Official Organization Website", "News Announcement", or the bare domain \
(e.g. "careers.example.org") when it is none of those.

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
        .replace("{kinds}", " | ".join(OPPORTUNITY_KINDS))
        .replace("{experience}", " | ".join(EXPERIENCE_LEVELS))
        .replace("{position_types}", " | ".join(POSITION_TYPES))
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


_REGISTRY_CACHE: Optional[Dict[str, Any]] = None


def _employer_registry() -> Dict[str, Any]:
    """Load public/employers.json once per process (source of truth)."""
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        try:
            _REGISTRY_CACHE = load_registry(
                str(Path(__file__).resolve().parent.parent / "public" / "employers.json")
            )
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("Could not load employer registry: %s", exc)
            _REGISTRY_CACHE = {"employers": []}
    return _REGISTRY_CACHE


def _employer_id_for(organization: str) -> str:
    employer = find_employer(organization, _employer_registry())
    return str(employer.get("id") or "") if employer else ""


def dedupe_key(candidate: Dict[str, Any]) -> str:
    """employer_id + normalised title + location + deadline (tracking-free)."""
    organization = (
        candidate.get("organization")
        or candidate.get("company")
        or ""
    )
    return dedupe_hash(
        {
            "clean_title": candidate.get("title") or candidate.get("clean_title") or "",
            "organization": organization,
            "city": candidate.get("city") or candidate.get("location") or "",
            "state": candidate.get("state") or "",
            "deadline_or_window": candidate.get("deadline_or_window") or "",
        },
        _employer_id_for(str(organization)),
    )


def existing_keys(jobs: List[Dict[str, Any]]) -> Set[str]:
    keys: Set[str] = set()
    registry = _employer_registry()
    for job in jobs:
        employer = find_employer(job.get("organization"), registry)
        keys.add(
            dedupe_hash(
                job,
                str(employer.get("id") or "") if employer else "",
            )
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


# Ordered title patterns -> position_type, most specific first.
POSITION_TYPE_PATTERNS = (
    (
        re.compile(r"\b(jrf|junior research fellow|srf|senior research fellow)\b", re.I),
        "JRF / SRF",
    ),
    (
        re.compile(r"\b(ph\.?\s?d|doctoral|doctorate|post-?doctoral|postdoc)\b", re.I),
        "PhD / Doctoral Fellowship",
    ),
    (
        re.compile(
            r"\b(project associate|research associate|project assistant|"
            r"research assistant|project scientist|research scientist)\b",
            re.I,
        ),
        "Project Associate / Research Associate",
    ),
    (
        re.compile(r"\b(young professional|consultant|advisor|adviser)\b", re.I),
        "Young Professional / Consultant (Contractual)",
    ),
    (
        re.compile(r"\b(professor|faculty|lecturer|dean)\b", re.I),
        "Faculty / Academic",
    ),
    (
        re.compile(r"\b(fellow|fellowship|intern|internship|trainee)\b", re.I),
        "Fellowship / Internship",
    ),
)

# Fallback position_type per category when the title carries no signal.
POSITION_TYPE_BY_CATEGORY = {
    "Academic, JRF, SRF & PhD Positions": "JRF / SRF",
    "Research Associate & Project Staff (Contractual)": "Project Associate / Research Associate",
    "Grants & Research Funding": "Young Professional / Consultant (Contractual)",
    "Scholarships & Doctoral Support": "PhD / Doctoral Fellowship",
    "Fellowships & Leadership Programs": "Fellowship / Internship",
    "Internships & Student Traineeships": "Fellowship / Internship",
    "Competitions, Hackathons & Awards": "Fellowship / Internship",
}

DEFAULT_POSITION_TYPE = "Full-Time Corporate / NGO"

ACADEMIC_POSITION_TYPES = (
    "JRF / SRF",
    "PhD / Doctoral Fellowship",
    "Project Associate / Research Associate",
    "Young Professional / Consultant (Contractual)",
    "Faculty / Academic",
    "Fellowship / Internship",
)


def infer_position_type(title: str, category: str = "") -> str:
    """Guess a position_type from the title first, then the category."""
    text = squash(title)
    for pattern, position_type in POSITION_TYPE_PATTERNS:
        if pattern.search(text):
            return position_type
    return POSITION_TYPE_BY_CATEGORY.get(squash(category), DEFAULT_POSITION_TYPE)


def default_qualification_summary(position_type: str) -> str:
    """Standard Indian eligibility line used when a source omits requirements."""
    return {
        "JRF / SRF": (
            "M.Sc. / M.Tech. in the relevant discipline "
            "(UGC-NET / GATE preferred, as per funding-agency norms)"
        ),
        "PhD / Doctoral Fellowship": (
            "Master's degree in the relevant discipline; doctoral registration "
            "as per institute / fellowship norms (UGC-NET / GATE preferred)"
        ),
        "Project Associate / Research Associate": (
            "M.Sc. / M.Tech. / B.Tech. in the relevant discipline, "
            "as per the project advertisement"
        ),
        "Young Professional / Consultant (Contractual)": (
            "Master's degree in the relevant discipline with 0-3 years of "
            "experience, as per the scheme norms"
        ),
        "Faculty / Academic": (
            "Ph.D. in the relevant discipline with teaching / research "
            "experience, as per UGC norms"
        ),
        "Fellowship / Internship": (
            "Recent graduate / postgraduate in the relevant discipline, "
            "as per the fellowship norms"
        ),
    }.get(
        position_type,
        "Bachelor's / Master's degree in the relevant discipline or equivalent experience",
    )


def default_compensation(position_type: str) -> str:
    """Standard compensation note used when a source omits the figure."""
    if position_type in ACADEMIC_POSITION_TYPES:
        return "As per institute norms"
    return "Not disclosed - see official portal"


def infer_opportunity_kind(job: Dict[str, Any]) -> str:
    """Derive the opportunity kind for records written before the field existed."""
    category = squash(job.get("category"))
    position_type = squash(job.get("position_type"))
    title = squash(job.get("clean_title") or job.get("title"))
    if category == "Grants & Research Funding":
        return "Grant / Funding"
    if category == "Scholarships & Doctoral Support":
        return "Scholarship"
    if category == "Competitions, Hackathons & Awards":
        return "Competition / Award"
    if category == "Internships & Student Traineeships":
        return "Internship"
    if category == "Fellowships & Leadership Programs":
        return "Fellowship"
    if re.search(r"\b(grant|funding call|call for proposals?|seed fund)\b", title, re.I):
        return "Grant / Funding"
    if re.search(r"\b(scholarship|studentship)\b", title, re.I):
        return "Scholarship"
    if re.search(r"\b(competition|hackathon|challenge|award|prize)\b", title, re.I):
        return "Competition / Award"
    if re.search(r"\b(intern|internship|trainee|traineeship)\b", title, re.I):
        return "Internship"
    if position_type in ("JRF / SRF", "PhD / Doctoral Fellowship") or re.search(
        r"\b(fellow|fellowship)\b", title, re.I
    ):
        return "Fellowship"
    return "Job / Career"


def normalize_job_fields(job: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade a stored record to the current schema, in place.

    Maps pre-upgrade category names onto the current category list and
    backfills position_type / opportunity_kind / deadline_or_window /
    qualification_summary / compensation_or_fellowship / org_website /
    org_domain / source_portal so that every record - including historical
    archive entries - carries the fields the front-end filters, badges,
    readable links, official-logo figures and JSON-LD builders expect.
    """
    category = squash(job.get("category"))
    if category in LEGACY_CATEGORY_MAP:
        job["category"] = LEGACY_CATEGORY_MAP[category]
    position_type = squash(job.get("position_type"))
    if position_type not in POSITION_TYPES:
        position_type = infer_position_type(
            squash(job.get("clean_title")), str(job.get("category") or "")
        )
    job["position_type"] = position_type
    kind = squash(job.get("opportunity_kind"))
    if kind not in OPPORTUNITY_KINDS:
        job["opportunity_kind"] = infer_opportunity_kind(job)
    if not squash(job.get("deadline_or_window")):
        job["deadline_or_window"] = "Rolling / Open"
    if not squash(job.get("qualification_summary")):
        job["qualification_summary"] = default_qualification_summary(position_type)
    if not squash(job.get("compensation_or_fellowship")):
        job["compensation_or_fellowship"] = default_compensation(position_type)

    # Official institution website + readable link identity. Best-effort and
    # non-destructive: verified directory hits always win, existing valid
    # values are preserved, and nothing is ever dropped for missing identity.
    # Records that passed the Phase 3 gate keep the identity captured from the
    # verified page + registry; normalization must never overwrite it.
    if not job.get("verification"):
        website, domain = finalize_org_identity(
            squash(job.get("organization")),
            squash(job.get("apply_url")),
            squash(job.get("org_website")),
            squash(job.get("org_domain")),
        )
        job["org_website"] = website
        job["org_domain"] = domain
    domain = squash(job.get("org_domain"))
    if not squash(job.get("source_portal")):
        job["source_portal"] = infer_source_portal(
            squash(job.get("apply_url")), domain
        )
    return job


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


# ---------------------------------------------------------------------------
# Organisation identity, readable links & URL verification
# ---------------------------------------------------------------------------
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HTTP_SIMPLE_HEADERS = {
    "User-Agent": BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.8",
}

_KNOWN_ORGS_SORTED = sorted(KNOWN_INDIAN_ORGS, key=lambda item: -len(item[0]))


def host_of(url: str) -> str:
    """Lowercase hostname of a URL (empty string when unusable)."""
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw if "://" in raw else "https://" + raw)
    except ValueError:
        return ""
    return (parsed.netloc or "").split("@")[-1].split(":")[0].strip(".").lower()


def strip_www(host: str) -> str:
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_board_host(host: str) -> bool:
    """True when the host belongs to a job board / aggregator / social site."""
    host = (host or "").lower()
    return any(host == board or host.endswith("." + board) for board in JOB_BOARD_HOSTS)


def is_google_news_url(url: str) -> bool:
    return host_of(url) == "news.google.com"


def decode_google_news_link(url: str) -> Optional[str]:
    """Best-effort offline unwrap of a news.google.com/rss/articles/... link.

    Google News item ids embed the target URL inside a base64 protobuf
    payload. Decoding happens locally (no network call) and frequently
    recovers the publisher's real article URL.
    """
    match = re.search(r"/articles/([A-Za-z0-9_\-]+)", str(url or ""))
    if not match:
        return None
    token = match.group(1)
    padded = token + "=" * (-len(token) % 4)
    try:
        raw = base64.urlsafe_b64decode(padded)
    except Exception:
        return None
    for candidate_match in re.finditer(rb"https?://[\x21-\x7e]{8,}", raw):
        candidate = candidate_match.group(0).decode("ascii", "ignore")
        candidate = candidate.rstrip("\\\"'.,);]")
        if is_valid_apply_url(candidate) and not is_google_news_url(candidate):
            return candidate
    return None


def _unwrap_google_news_via_http(url: str, timeout: int = 12) -> Optional[str]:
    """Follow a Google News link once and mine the destination URL from HTML."""
    if requests is None:
        return None
    try:
        response = requests.get(
            url, headers=HTTP_SIMPLE_HEADERS, timeout=timeout, allow_redirects=True
        )
    except Exception:
        return None
    text = (response.text or "")[:400000]
    for pattern in (r'data-n-au="(https?://[^"]+)"', r'<a[^>]+href="(https?://[^"]+)"'):
        for match in re.finditer(pattern, text):
            href = html.unescape(match.group(1)).strip()
            if is_valid_apply_url(href) and not is_google_news_url(href):
                return href
    return None


GOOGLE_NEWS_BATCHEXECUTE = "https://news.google.com/_/DotsSplashUi/data/batchexecute"


def _resolve_google_news_via_batchexecute(
    article_id: str, timeout: int = 15
) -> Optional[str]:
    """Resolve an opaque Google News article id to the publisher URL.

    Newer Google News ids (AU_yqL... style) no longer embed the destination
    inside the base64 payload. The article shell page carries a signature +
    timestamp pair that the public DotsSplashUi batchexecute endpoint (the
    same RPC the Google News web app uses) exchanges for the real URL.
    """
    if requests is None or not article_id:
        return None
    try:
        shell = requests.get(
            "https://news.google.com/rss/articles/" + article_id,
            headers=HTTP_SIMPLE_HEADERS,
            timeout=timeout,
        )
    except Exception:
        return None
    shell_text = shell.text or ""
    signature = re.search(r'data-n-a-sg="([^"]+)"', shell_text)
    timestamp = re.search(r'data-n-a-ts="([^"]+)"', shell_text)
    if not signature or not timestamp:
        return None
    request_body = [
        "Fbv4je",
        json.dumps(
            [
                "garturlreq",
                [
                    [
                        "X",
                        "X",
                        ["X", "X"],
                        None,
                        None,
                        1,
                        1,
                        "US:en",
                        1,
                        1,
                        None,
                        None,
                        None,
                        None,
                        None,
                        0,
                        1,
                    ],
                    "X",
                    "X",
                    1,
                    [1, 1, 1],
                    1,
                    1,
                    None,
                    0,
                    0,
                    None,
                    0,
                ],
                article_id,
                timestamp.group(1),
                signature.group(1),
            ]
        ),
    ]
    payload = "f.req=" + quote(json.dumps([[request_body]]))
    try:
        response = requests.post(
            GOOGLE_NEWS_BATCHEXECUTE,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": HTTP_SIMPLE_HEADERS["User-Agent"],
                "Referer": "https://news.google.com/",
            },
            timeout=timeout,
        )
    except Exception:
        return None
    for part in (response.text or "").split("\n\n"):
        try:
            data = json.loads(part)
            inner = json.loads(data[0][2])
            url = inner[1]
        except Exception:
            continue
        if (
            isinstance(url, str)
            and is_valid_apply_url(url)
            and not is_google_news_url(url)
        ):
            return url
    return None


def resolve_google_news_link(url: str, timeout: int = 12) -> Optional[str]:
    """Best-effort unwrap of a news.google.com link to the publisher URL.

    Tries the free offline base64 decode first, then the batchexecute
    resolver for opaque ids, then a single HTTP pass over the article shell.
    """
    raw = squash(url)
    if not is_google_news_url(raw):
        return raw if is_valid_apply_url(raw) else None
    decoded = decode_google_news_link(raw)
    if decoded:
        return decoded
    match = re.search(r"/articles/([A-Za-z0-9_\-]+)", raw)
    if match:
        resolved = _resolve_google_news_via_batchexecute(match.group(1), timeout=timeout)
        if resolved:
            return resolved
    return _unwrap_google_news_via_http(raw, timeout=timeout)


def verify_and_resolve_url(url: str, timeout: int = 12) -> Optional[str]:
    """Resolve a URL to its final destination, or None when conclusively dead.

    Follows redirects (including unwrapping news.google.com wrappers) and
    rejects HTTP 404/410 destinations. Timeouts, TLS quirks and bot-blocks on
    government portals are deliberately NOT treated as dead - the listing is
    kept with the original URL so slow official servers never erase a vacancy.
    """
    raw = squash(url)
    if not is_valid_apply_url(raw):
        return None
    if is_google_news_url(raw):
        resolved = resolve_google_news_link(raw, timeout=timeout)
        if resolved:
            raw = resolved
    if requests is None:
        return raw
    try:
        response = requests.get(
            raw,
            headers=HTTP_SIMPLE_HEADERS,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        status = response.status_code
        final = response.url or raw
        response.close()
    except requests.exceptions.SSLError:
        return raw
    except Exception:
        # Unreachable / timed out / DNS flake: keep the listing, cannot
        # confirm it is dead.
        return raw
    if status in (404, 410):
        return None
    if not is_valid_apply_url(final):
        return raw
    if is_google_news_url(final):
        return raw
    return final


def known_org_identity(organization: str) -> Optional[Tuple[str, str]]:
    """Verified (website, domain) for a known Indian organisation, if any."""
    name = squash(organization).lower()
    if not name:
        return None
    name = re.sub(r"[^\w&\s]", " ", name, flags=re.UNICODE)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        return None
    exact = EXACT_ORG_NAMES.get(name)
    if exact is not None:
        return exact
    for alias, website, domain in _KNOWN_ORGS_SORTED:
        pattern = r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])"
        if re.search(pattern, name):
            return website, domain
    return None


def derive_org_site_from_apply_url(apply_url: str) -> Optional[str]:
    """When the apply link already lives on the organisation's own domain,
    that domain is its official website."""
    host = host_of(apply_url)
    if not host or is_board_host(host):
        return None
    site = "https://" + strip_www(host)
    return site if is_valid_apply_url(site) else None


def finalize_org_identity(
    organization: str,
    apply_url: str = "",
    current_website: str = "",
    current_domain: str = "",
) -> Tuple[str, str]:
    """Return the best known (org_website, org_domain) for a record.

    Priority: the verified directory -> a model-provided website on the same
    official domain -> the model-provided website -> the apply link's own
    domain (when it is not a job board) -> the model-provided bare domain.
    """
    website = squash(current_website)
    domain = squash(current_domain).strip(".").lower()
    if website and not is_valid_apply_url(website):
        website = ""

    known = known_org_identity(organization)
    if known is not None:
        known_site, known_domain = known
        if website:
            host = host_of(website)
            if host == known_domain or host.endswith("." + known_domain):
                return website, known_domain  # deeper page on the official domain
        return known_site, known_domain

    if website:
        host = strip_www(host_of(website))
        if host and not is_board_host(host):
            return website, host

    derived = derive_org_site_from_apply_url(apply_url)
    if derived:
        return derived, strip_www(host_of(derived))

    if domain and "." in domain and is_valid_apply_url("https://" + domain):
        return "https://" + domain, domain
    return "", ""


def infer_source_portal(apply_url: str, org_domain: str = "") -> str:
    """Readable label for wherever the apply link points."""
    host = strip_www(host_of(apply_url))
    if not host:
        return ""
    for board, label in SOURCE_PORTAL_BY_HOST:
        if host == board or host.endswith("." + board):
            return label
    if org_domain and (host == org_domain or host.endswith("." + org_domain)):
        return "Official Organization Website"
    if re.search(r"\.(gov\.in|nic\.in|ac\.in|res\.in|edu\.in|ernet\.in|gov)$", host):
        return "Official Institute Portal"
    if host.endswith((".org", ".org.in", ".ngo", ".int")):
        return "Official Organisation Website"
    return host


BAD_ORG_MARKERS = (
    "unknown", "confidential", "see announcement", "recruiter",
    "not disclosed", "undisclosed", "employer", "various",
)

# Anonymous-employer labels that are never publishable, even if a job board
# supplies a working apply link. Kept separate from the broader markers above
# so the final write gate can enforce this class unconditionally.
BLOCKED_ORG_TERMS = (
    "confidential", "undisclosed", "unknown",
    "leading client", "not disclosed",
)


def has_blocked_organization(job: Dict[str, Any]) -> bool:
    """True when the employer name is an anonymous placeholder."""
    org = squash(job.get("organization")).casefold()
    return any(term in org for term in BLOCKED_ORG_TERMS)


def is_verifiable_job(job: Dict[str, Any]) -> Tuple[bool, str]:
    """Strict publish gate: real apply link, real employer, official website."""
    apply_url = squash(job.get("apply_url"))
    if not is_valid_apply_url(apply_url):
        return False, "apply URL missing or invalid"
    if is_google_news_url(apply_url):
        return False, "apply link is still an unresolved news redirect"
    org = squash(job.get("organization")).lower().strip(" .,-")
    if len(org) < 3 or re.fullmatch(r"[^a-z0-9]+", org):
        return False, "organization is not a named entity"
    if has_blocked_organization(job):
        return False, "organization is an anonymous placeholder"
    if any(marker in org for marker in BAD_ORG_MARKERS):
        return False, "organization is not a named entity"
    if not is_valid_apply_url(squash(job.get("org_website"))):
        return False, "org_website missing or invalid"
    return True, ""


def resolve_and_verify_record(
    record: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], str]:
    """Resolve the apply link, fill org identity fields, then gate the record."""
    resolved = verify_and_resolve_url(squash(record.get("apply_url")))
    if resolved is None:
        return None, "apply URL is dead (HTTP 404/410 or invalid)"
    record["apply_url"] = resolved

    website, domain = finalize_org_identity(
        squash(record.get("organization")),
        resolved,
        squash(record.get("org_website")),
        squash(record.get("org_domain")),
    )
    # A model-guessed website that no longer resolves is dropped in favour of
    # the deterministic derivation; directory-matched sites are trusted.
    known = known_org_identity(squash(record.get("organization")))
    trusted = known is not None and domain == known[1]
    if website and not trusted and verify_and_resolve_url(website, timeout=8) is None:
        website, domain = finalize_org_identity(
            squash(record.get("organization")), resolved, "", ""
        )
    record["org_website"] = website
    record["org_domain"] = domain
    record["source_portal"] = (
        infer_source_portal(resolved, domain)
        or squash(record.get("source_portal"))
    )
    ok, why = is_verifiable_job(record)
    if not ok:
        return None, why
    return record, ""


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


def interleave_candidates(
    groups: List[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    """Round-robin merge several candidate lists, preserving group order.

    The run cap (--max-new) limits how many candidates reach the Gemini
    humanizer each day. Plain concatenation lets a single noisy source fill
    the entire budget; interleaving guarantees every source - job boards,
    targeted sweeps, ReliefWeb and the institute news harvest - contributes
    to each run.
    """
    merged: List[Dict[str, Any]] = []
    index = 0
    remaining = True
    while remaining:
        remaining = False
        for group in groups:
            if index < len(group):
                merged.append(group[index])
                remaining = True
        index += 1
    return merged


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
# Source 3: Indian academic & institute recruitment (Google News RSS, zero key)
# ---------------------------------------------------------------------------
GOOGLE_NEWS_RSS_SEARCH = "https://news.google.com/rss/search"
GOOGLE_NEWS_RESULTS_PER_QUERY = 50
# Google News happily resurfaces years-old announcements; anything older than
# this window is almost certainly an expired advertisement and is dropped at
# harvest time so only genuinely current vacancies reach the humanizer.
GOOGLE_NEWS_MAX_AGE_DAYS = 21

# High-intent Indian recruitment queries for institutes that advertise
# JRF / SRF / project-staff / PhD / contractual roles outside the big boards.
INDIAN_ACADEMIC_NEWS_QUERIES = [
    '("Junior Research Fellow" OR "JRF" OR "Project Associate" OR "Research Associate")'
    ' AND ("Environmental" OR "Forestry" OR "Climate" OR "Remote Sensing" OR "GIS"'
    ' OR "Ecology") India',
    '(JRF OR "Project Associate" OR "Research Fellow" OR "Field Assistant")'
    ' recruitment when:7d',
    '("WII Dehradun" OR "ICFRE" OR "IIFM Bhopal" OR "IIRS" OR "NRSC" OR "ATREE"'
    ' OR "CEEW" OR "TERI" OR "GBPNIHE" OR "ICAR") AND ("Recruitment" OR "Vacancy"'
    ' OR "Position" OR "Fellow" OR "Associate")',
    '("Young Professional" OR "Contractual" OR "Consultant") AND ("MoEFCC" OR "Forest"'
    ' OR "Climate Change" OR "Sustainability" OR "CAMPA" OR "Pollution Control") India',
    '("PhD Fellowship" OR "Postdoctoral" OR "PhD Position")'
    ' (Climate OR Forestry OR Environment OR Ecology OR "Earth Sciences") when:7d',
]

# Optional extra academic-job RSS feeds (labelled). Best-effort: unreachable
# feeds are logged and skipped, and an empty list simply means Google News
# is the only institute-news source (IndiaBioscience currently serves no
# public RSS, and its job pages block automated reads).
EXTRA_ACADEMIC_JOB_FEEDS: List[Tuple[str, str]] = []

# A harvested headline only counts as a vacancy announcement when it reads
# like a recruitment ad rather than a news story.
JOB_AD_TITLE_RE = re.compile(
    r"(jrf|srf|junior research fellow|senior research fellow|research fellow|"
    r"project associate|research associate|project assistant|research assistant|"
    r"young professional|consultant|fellow|fellowship|phd|doctoral|postdoc|"
    r"post-?doctoral|recruit|vacanc|walk-?in|opening|hiring|"
    r"assistant professor|faculty|(?:research|project|principal|chief)\s+scientist)",
    re.I,
)

# News headlines that merely mention fellowships/scientists (recipient lists,
# launches, explainers) are not vacancies and are dropped at harvest time.
NEWS_NOISE_TITLE_RE = re.compile(
    r"(recipients?|winners?|awardees?|felicitat|set out|observes|launches|"
    r"to prepare for)",
    re.I,
)

# Google News wrappers are unwrapped offline; the recovered destination must
# land on a verifiable Indian institutional / academic / organisation domain
# (or an official job board) or the headline is not publishable.
NEWS_VERIFIABLE_HOST_RE = re.compile(
    r"\.(gov\.in|ac\.in|res\.in|edu\.in|nic\.in|ernet\.in|org|in)$", re.I
)
NEWS_VERIFIABLE_DOMAINS = ("linkedin.com", "naukri.com", "indeed.com")


def _is_verifiable_news_host(url: str) -> bool:
    host = host_of(url)
    if not host:
        return False
    if any(host == d or host.endswith("." + d) for d in NEWS_VERIFIABLE_DOMAINS):
        return True
    return bool(NEWS_VERIFIABLE_HOST_RE.search(host))


def _google_news_query_url(query: str) -> str:
    # The when:30d operator makes Google News sort by recency, which is what a
    # daily pipeline needs (the default relevance order resurfaces old ads).
    return GOOGLE_NEWS_RSS_SEARCH + "?" + urlencode(
        {"q": query + " when:30d", "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}
    )


def _news_entry_to_candidate(entry: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
    """Convert one feed entry into a candidate, or None when it is not an ad."""
    title = squash(strip_html(entry.get("title") or ""))
    link = str(entry.get("link") or "").strip()
    if not title or not link.lower().startswith("http"):
        return None
    publisher = ""
    source = entry.get("source")
    if isinstance(source, dict):
        publisher = squash(source.get("title") or "")
    # Google News headlines end with " - Publisher"; drop the suffix when the
    # feed exposes the publisher name separately.
    if publisher and title.endswith(" - " + publisher):
        title = title[: -(len(publisher) + 3)].strip()
    if not JOB_AD_TITLE_RE.search(title):
        return None
    if NEWS_NOISE_TITLE_RE.search(title):
        return None
    summary = strip_html(entry.get("summary") or entry.get("description") or "")[:4000]
    date_posted = ""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published is not None:
        try:
            date_posted = date(published[0], published[1], published[2]).isoformat()
        except (TypeError, ValueError, IndexError, AttributeError):
            date_posted = ""
    if date_posted:
        age_cutoff = (date.today() - timedelta(days=GOOGLE_NEWS_MAX_AGE_DAYS)).isoformat()
        if date_posted < age_cutoff:
            return None
    # Strict verifiability (last, so resolution cost only hits real ads):
    # unwrap the Google News shell - offline base64, then the batchexecute
    # resolver for opaque ids, then one HTTP pass - and keep the announcement
    # only when it lands on a verifiable institution / academic / organisation
    # domain (or an official job board).
    if is_google_news_url(link):
        resolved = resolve_google_news_link(link)
        if not resolved:
            return None
        link = resolved
    if not _is_verifiable_news_host(link):
        return None
    return {
        "source": "google-news",
        "title": title,
        "organization": publisher or "Institute / Recruiter (see announcement)",
        "location_raw": "India",
        "description": summary,
        "apply_url": link,
        "date_posted": date_posted,
        "matched_query": query,
    }


def fetch_indian_academic_and_institute_jobs() -> List[Dict[str, Any]]:
    """Zero-key harvest of Indian institute JRF / PhD / contractual ads.

    Indian research institutes (WII, ICFRE, IIFM, IIRS, NRSC, ICAR, IITs,
    IISc, MoEFCC, GBPNIHE, ATREE, TERI and others) frequently post JRF, PhD
    and contractual advertisements outside the major job boards. Public
    Google News RSS searches surface those announcements; each headline is
    screened for job-ad phrasing, then flows through the same Gemini
    humanizer and strict India + green relevance filter as every other
    source. Feed entries link through Google News to the announcement page.
    """
    if feedparser is None:
        log.warning(
            "feedparser is not installed - skipping the institute news harvest "
            "(pip install -r scripts/requirements.txt)"
        )
        return []

    candidates: List[Dict[str, Any]] = []
    seen_links: Set[str] = set()

    def harvest(feed_url: str, label: str, query: str) -> None:
        parsed = None
        if requests is not None:
            try:
                # Keep requests' default library user-agent; Google News RSS
                # is a public feed and does not need browser spoofing.
                response = requests.get(
                    feed_url,
                    headers={"Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"},
                    timeout=REQUEST_TIMEOUT,
                )
                if response.status_code != 200:
                    log.warning(
                        "%s feed returned HTTP %s for %r - skipping",
                        label, response.status_code, query[:60],
                    )
                    return
                parsed = feedparser.parse(response.content)
            except Exception as exc:
                log.warning(
                    "%s feed request failed for %r: %s",
                    label, query[:60], str(exc)[:140],
                )
                return
        else:
            try:
                parsed = feedparser.parse(feed_url)
            except Exception as exc:
                log.warning(
                    "%s feed fetch via feedparser failed for %r: %s",
                    label, query[:60], str(exc)[:140],
                )
                return

        entries = list(getattr(parsed, "entries", []) or [])[:GOOGLE_NEWS_RESULTS_PER_QUERY]
        if not entries:
            if getattr(parsed, "bozo", False):
                log.warning(
                    "%s feed could not be parsed (%s) - skipping",
                    label, str(parsed.get("bozo_exception"))[:140],
                )
            return
        kept = 0
        for entry in entries:
            candidate = _news_entry_to_candidate(entry, query)
            if candidate is None:
                continue
            link_key = normalize_key(candidate["apply_url"])
            if link_key in seen_links:
                continue
            seen_links.add(link_key)
            candidates.append(candidate)
            kept += 1
        log.info(
            "%s: %d recruitment headline(s) kept from %d feed entr(y/ies) for %r",
            label, kept, len(entries), query[:70],
        )

    for query in INDIAN_ACADEMIC_NEWS_QUERIES:
        harvest(_google_news_query_url(query), "Google News (India)", query)

    for feed_label, feed_url in EXTRA_ACADEMIC_JOB_FEEDS:
        harvest(feed_url, feed_label, feed_label)

    log.info("Institute news harvest produced %d candidate(s)", len(candidates))
    return candidates


# ---------------------------------------------------------------------------
# Source 3b: direct verifiable Indian environmental & academic career portals
# ---------------------------------------------------------------------------
INDIABIOSCIENCE_FEED = "https://indiabioscience.org/feed"

# Direct careers pages of flagship Indian climate / conservation
# organisations. Listings are discovered as links on the page, then flow
# through the same Gemini humanizer + strict verifiability gate as every
# other source.
VERIFIED_PORTAL_PAGES: List[Dict[str, str]] = [
    # wri-india.org/careers sits behind a bot wall; the global WRI careers
    # board is public and carries the India postings with location = India.
    {
        "name": "WRI India",
        "organization": "WRI India",
        "url": "https://www.wri.org/careers",
        "slug": "wri-india",
    },
    {
        "name": "CEEW",
        "organization": "Council on Energy, Environment and Water (CEEW)",
        "url": "https://www.ceew.in/careers",
        "slug": "ceew",
    },
    {
        "name": "ATREE",
        "organization": "ATREE",
        "url": "https://www.atree.org/careers/",
        "slug": "atree",
    },
    {
        "name": "WWF-India",
        "organization": "WWF-India",
        "url": "https://www.wwfindia.org/engage_with_us/get_involved/jobs/",
        "slug": "wwf-india",
    },
]

INDIABIOSCIENCE_JOB_TITLE_RE = re.compile(
    r"(job|vacanc|career|position|opening|fellow|fellowship|postdoc|phd|"
    r"jrf|srf|research associate|project associate|recruit|intern|hiring|"
    r"walk-?in|scientist)",
    re.I,
)
GREEN_FIELD_RE = re.compile(
    r"(environment|ecolog|climate|forest|wildlife|sustainab|conservation|"
    r"biodiversity|earth|water|agricultur|geospatial|remote sensing|gis|"
    r"natural resource|planetary|green)",
    re.I,
)
PORTAL_LINK_TEXT_RE = re.compile(
    r"(\bjobs?\b|vacanc|\bpositions?\b|\bopenings?\b|fellowship|"
    r"\bassociates?\b|\banalysts?\b|\bofficers?\b|\bcoordinators?\b|"
    r"\bconsultants?\b|\bmanagers?\b|\bspecialists?\b|\binterns?\b|"
    r"\bresearch\b|\bscientists?\b|\badvis[eo]rs?\b|\bdirectors?\b|"
    r"\bengineers?\b|\bassistants?\b|\blead\b|\bhiring\b|\bcareers?\b|"
    r"\bfellows?\b|\bexecutives?\b|\btrainees?\b)",
    re.I,
)
PORTAL_LINK_SKIP_RE = re.compile(
    r"(read more|learn more|view all|see all|sign in|log ?in|donate|subscribe|"
    r"newsletter|privacy|terms|cookie|sitemap|contact|about|facebook|twitter|"
    r"instagram|linkedin\.com|youtube|mailto:|/tag/|/category/)",
    re.I,
)


def _fetch_rss_entries(feed_url: str, label: str, browser_ua: bool = False) -> List[Any]:
    """Fetch + parse a public RSS/Atom feed with graceful failure."""
    if feedparser is None:
        log.warning("feedparser is not installed - skipping %s", label)
        return []
    parsed = None
    if requests is not None:
        try:
            headers = dict(HTTP_SIMPLE_HEADERS) if browser_ua else {
                "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8"
            }
            if not browser_ua:
                headers["User-Agent"] = requests.utils.default_headers().get(
                    "User-Agent", ""
                )
            response = requests.get(feed_url, headers=headers, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                log.warning("%s feed returned HTTP %s - skipping", label, response.status_code)
                return []
            parsed = feedparser.parse(response.content)
        except Exception as exc:
            log.warning("%s feed request failed: %s", label, str(exc)[:160])
            return []
    else:
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            log.warning("%s feed fetch via feedparser failed: %s", label, str(exc)[:160])
            return []
    entries = list(getattr(parsed, "entries", []) or [])
    if not entries and getattr(parsed, "bozo", False):
        log.warning(
            "%s feed could not be parsed (%s) - skipping",
            label, str(parsed.get("bozo_exception"))[:140],
        )
    return entries


def _entry_date_iso(entry: Dict[str, Any]) -> str:
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published is None:
        return ""
    try:
        return date(published[0], published[1], published[2]).isoformat()
    except (TypeError, ValueError, IndexError, AttributeError):
        return ""


def fetch_indiabioscience_jobs() -> List[Dict[str, Any]]:
    """IndiaBioscience jobs & announcement feed filtered for green roles."""
    entries = _fetch_rss_entries(INDIABIOSCIENCE_FEED, "IndiaBioscience")
    candidates: List[Dict[str, Any]] = []
    for entry in entries[:GOOGLE_NEWS_RESULTS_PER_QUERY]:
        title = squash(strip_html(entry.get("title") or ""))
        link = str(entry.get("link") or "").strip()
        if not title or not link.lower().startswith("http"):
            continue
        if not INDIABIOSCIENCE_JOB_TITLE_RE.search(title):
            continue
        summary = strip_html(entry.get("summary") or entry.get("description") or "")
        if not GREEN_FIELD_RE.search(title + " " + summary[:600]):
            continue
        candidates.append(
            {
                "source": "portal:indiabioscience",
                "title": title,
                "organization": "IndiaBioscience partner institute",
                "location_raw": "India",
                "description": (summary or "")[:4000],
                "apply_url": link,
                "date_posted": _entry_date_iso(entry),
                "matched_query": "indiabioscience-feed",
            }
        )
    log.info("IndiaBioscience produced %d candidate(s)", len(candidates))
    return candidates


def _extract_portal_links(
    page_url: str, html_text: str, limit: int = 20
) -> List[Tuple[str, str]]:
    """Pull job-looking same-site links off a careers page."""
    anchors: List[Tuple[str, str]] = []
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html_text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            anchors.append((squash(anchor.get_text(" ")), str(anchor.get("href") or "")))
    else:  # pragma: no cover - regex fallback when bs4 is missing
        for match in re.finditer(
            r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html_text, re.I | re.S
        ):
            anchors.append((squash(strip_html(match.group(2))), html.unescape(match.group(1))))

    page_host = host_of(page_url)
    kept: List[Tuple[str, str]] = []
    seen: Set[str] = set()
    for text, href in anchors:
        if not text or len(text) < 8 or len(text) > 140:
            continue
        if not PORTAL_LINK_TEXT_RE.search(text):
            continue
        if PORTAL_LINK_SKIP_RE.search(text) or PORTAL_LINK_SKIP_RE.search(href):
            continue
        absolute = urljoin(page_url, href.strip())
        if not is_valid_apply_url(absolute):
            continue
        target_host = host_of(absolute)
        if target_host != page_host and not target_host.endswith("." + page_host):
            continue
        if absolute.rstrip("/") == page_url.rstrip("/"):
            continue
        key = normalize_key(absolute)
        if key in seen:
            continue
        seen.add(key)
        kept.append((text, absolute))
        if len(kept) >= limit:
            break
    return kept


def fetch_portal_page_candidates(page: Dict[str, str]) -> List[Dict[str, Any]]:
    """Scrape one official careers page for job-looking links."""
    if requests is None:
        return []
    try:
        response = requests.get(
            page["url"], headers=HTTP_SIMPLE_HEADERS, timeout=REQUEST_TIMEOUT
        )
    except Exception as exc:
        log.warning("%s careers page request failed: %s", page["name"], str(exc)[:140])
        return []
    if response.status_code != 200:
        log.warning(
            "%s careers page returned HTTP %s - skipping", page["name"], response.status_code
        )
        return []
    html_text = response.text or ""
    if len(html_text) < 500:
        log.warning("%s careers page returned too little content - skipping", page["name"])
        return []
    rows = _extract_portal_links(page["url"], html_text)
    candidates = [
        {
            "source": "portal:" + page["slug"],
            "title": text,
            "organization": page["organization"],
            "location_raw": "India",
            "description": (
                f"Live listing discovered on the official {page['name']} careers page. "
                "Confirm eligibility and deadlines on the destination page."
            ),
            "apply_url": href,
            "date_posted": "",
            "matched_query": page["slug"] + "-careers",
        }
        for text, href in rows
    ]
    log.info("%s careers page produced %d candidate(s)", page["name"], len(candidates))
    return candidates


def fetch_verified_indian_portals() -> List[Dict[str, Any]]:
    """Aggregate the direct verifiable Indian environmental career portals."""
    candidates: List[Dict[str, Any]] = []
    candidates.extend(fetch_indiabioscience_jobs())
    for page in VERIFIED_PORTAL_PAGES:
        candidates.extend(fetch_portal_page_candidates(page))
    log.info("Direct Indian portals produced %d candidate(s)", len(candidates))
    return candidates


# ---------------------------------------------------------------------------
# Source 4: ReliefWeb India (v2 API first, public RSS feed as fallback)
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
        "limit": 100,
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
# Global opportunities registry (global_jobs.json / global_archive.json).
#
# STRICTLY SEPARATED from the India registry: nothing in this section ever
# writes into jobs.json / archive.json, and the India pipeline never writes
# into the global files. Global records carry region / country instead of
# Indian state / city values and are flagged with "global": true.
# ---------------------------------------------------------------------------
DEFAULT_GLOBAL_JOBS_PATH = Path("public/global_jobs.json")
DEFAULT_GLOBAL_ARCHIVE_PATH = Path("public/global_archive.json")
GLOBAL_MAX_NEW_PER_RUN = 12       # cap on Gemini calls per run for the global stage (was 4)
GLOBAL_NEWS_MAX_AGE_DAYS = 21     # same freshness discipline as the India stage

GLOBAL_SYSTEM_PROMPT = """You are the editorial engine for UrbanForestPark \
(https://www.urbanforestpark.com), which maintains a Global Opportunities \
registry strictly separated from its India registry: international climate, \
environment, sustainability, conservation, energy-transition and ESG jobs, \
grants, scholarships, fellowships, internships and competitions that are \
open to candidates worldwide (including India-based applicants). You receive \
ONE raw opportunity posting scraped from a board or news feed (JSON). You \
return ONE JSON object.

STEP 1 - STRICT GLOBAL + GREEN RELEVANCE CHECK (always do this first):
A posting is acceptable ONLY when BOTH are true:
  (a) The opportunity is genuinely about the environment, climate change, \
forestry, conservation, biodiversity, sustainability, ESG, carbon markets, \
clean/renewable energy, water, sustainable agriculture, circular economy, \
disaster resilience or geospatial / earth-observation analysis - including \
adjacent domains such as WASH, agroforestry, marine conservation and green \
urban planning. Every opportunity kind counts: jobs, grants, scholarships, \
fellowships, internships and competitions / awards.
  (b) The opportunity is international: based outside India, remote/global, \
or hosted by a multilateral body (UN agencies, development banks, IUCN, \
CGIAR, international NGOs) or a foreign university or government, and open \
to applicants worldwide or to international applicants, including Indians. \
Positions restricted to India belong to the separate India registry and are \
NOT acceptable here.
If EITHER fails, set "is_relevant_green_job" to false, give one sentence in \
"rejection_reason", and return empty strings/arrays for all other fields. \
When in doubt, reject.

STEP 2 - HUMANIZED FIELDS (only for accepted opportunities). Return exactly:
- id: kebab-case slug (a-z, 0-9, hyphens only, max 60 chars) built from the \
opportunity title + organisation.
- date_added: {today} (copy this exact value).
- clean_title: opportunity title cleaned of noise.
- organization: the institution's proper name.
- region: EXACTLY ONE of: {regions}
- country: the host country of the institution or programme (plain English; \
use "Global" when the opportunity is worldwide and remote).
- city: city / location descriptor (e.g. "Bonn, Germany", "Remote (Global)").
- category: EXACTLY ONE of: {categories}
- opportunity_kind: EXACTLY ONE of: {kinds}
- deadline_or_window: the deadline or window ONLY when the source states one \
(e.g. "Apply by 15 Nov 2026"); otherwise the exact string "Rolling / Open". \
Never invent dates.
- experience_level: EXACTLY ONE of: {experience}
- position_type: EXACTLY ONE of: {position_types}
- qualification_summary: one short line with the degree / experience \
requirements; write the standard requirement for that kind when the source \
omits them.
- compensation_or_fellowship: stipend / salary / funding amount ONLY when the \
source states one; otherwise "Not disclosed - see official portal" (or \
"See official call" for grants). Never invent figures.
- role_summary: exactly 3 sentences, 45-70 words, concrete and specific to \
THIS opportunity.
- title_hi: the opportunity title written in formal Hindi (Devanagari), \
keeping organisation names in Latin script and keeping acronyms (UNFCCC, \
IUCN, GIS, ESG, PhD, dMRV ...) in Latin script.
- summary_hi: exactly 2 formal Hindi sentences summarising the opportunity \
and its eligibility for Hindi-speaking candidates.
- key_responsibilities: 4-5 short bullets, each supported by the source.
- must_have_skills: 5-7 short skill tags (mix technical and domain skills).
- application_tip: 1-2 sentences of practical, editor-style advice. Never \
mention that this tip was AI-written.
- apply_url: copy the source URL EXACTLY as provided.
- org_website: the institution's official website ONLY when genuinely \
confident; otherwise an empty string.
- org_domain: root domain of org_website without "https://" or "www."; empty \
when org_website is empty.
- source_portal: where apply_url points ("LinkedIn", "ReliefWeb", "Official \
Organization Website", or the bare domain when none of those).

STYLE RULES: Write like a thoughtful human editor. Plain, concrete English; \
vary sentence length. Never use the words "delve", "leverage", "spearhead", \
"passionate", "vibrant", "landscape" (as metaphor) or "game-changer". Use at \
most one em dash in the entire output and no exclamation marks. Never invent \
facts (salaries, dates, requirements, benefits) that the source does not \
contain - you may only compress, clarify and humanize.

Return ONLY the JSON object - no markdown fences, no commentary."""


def build_global_system_prompt(today: str) -> str:
    """Fill the global prompt's enum placeholders."""
    return (
        GLOBAL_SYSTEM_PROMPT
        .replace("{today}", today)
        .replace("{regions}", " | ".join(GLOBAL_REGIONS))
        .replace("{categories}", " | ".join(CATEGORIES))
        .replace("{kinds}", " | ".join(OPPORTUNITY_KINDS))
        .replace("{experience}", " | ".join(EXPERIENCE_LEVELS))
        .replace("{position_types}", " | ".join(POSITION_TYPES))
    )


# ---------------------------------------------------------------------------
# Verified evergreen global opportunities.
#
# These are real, long-standing international portals and programmes run by
# the institutions themselves - no fabricated vacancies. They guarantee the
# Global registry is rich and live today; freshly scraped opportunities are
# merged on top by run_global_stage() and expire through the normal
# lifecycle, while evergreen records stay active indefinitely.
# ---------------------------------------------------------------------------
_GLOBAL_SEED_BASE: Dict[str, Any] = {
    "state": "",
    "global": True,
    "evergreen": True,
    "status": "active",
    "source_portal": "Official Organization Website",
}

GLOBAL_SEED_OPPORTUNITIES: List[Dict[str, Any]] = [
    {
        **_GLOBAL_SEED_BASE,
        "id": "unfccc-secretariat-climate-careers",
        "clean_title": "Climate Change Careers - UNFCCC Secretariat (Professional & Programme Roles)",
        "organization": "United Nations Framework Convention on Climate Change (UNFCCC)",
        "region": "UN / Multilateral",
        "country": "Germany",
        "city": "Bonn, Germany",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Advanced university degree (Master's or above) in climate, environment, economics, law, engineering or a related field, with professional experience as specified per vacancy.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "The UNFCCC secretariat in Bonn runs the international climate process: COP sessions, the Paris Agreement work programme and the transparency regime. It recruits policy, finance, adaptation, mitigation and data professionals on a rolling basis, and professional posts are open to all nationalities, including Indian candidates. Apply through the official UN careers system.",
        "title_hi": "जलवायु परिवर्तन भर्तियाँ — UNFCCC सचिवालय (पेशेवर एवं कार्यक्रम पद)",
        "summary_hi": "जर्मनी के बॉन स्थित UNFCCC सचिवालय अंतर्राष्ट्रीय जलवायु प्रक्रिया का संचालन करता है और जलवायु वित्त, अनुकूलन, नीति एवं पारदर्शिता से जुड़े पदों पर योग्य पेशेवरों की निरंतर भर्ती करता है। भारतीय आवेदक इन पदों के लिए पूर्णतः पात्र हैं; नवीनतम रिक्तियाँ आधिकारिक भर्ती पोर्टल पर देखें।",
        "key_responsibilities": [
            "Support intergovernmental climate negotiations and work-programme delivery",
            "Draft policy, finance or transparency analysis for Parties and the secretariat",
            "Coordinate with UN agencies, observers and national focal points",
            "Maintain data, reporting and knowledge products for the climate regime",
        ],
        "must_have_skills": [
            "Climate policy",
            "International negotiations",
            "Climate finance",
            "MRV / transparency",
            "Data analysis",
            "Report writing",
        ],
        "application_tip": "Create a profile in the UNFCCC e-recruitment system before applying, and tailor each application to the specific vacancy requirements, since posts are competitive and reviewed against exact criteria.",
        "apply_url": "https://unfccc.int/about-us/vacancies",
        "org_website": "https://unfccc.int",
        "org_domain": "unfccc.int",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "green-climate-fund-careers",
        "clean_title": "Climate Finance Careers - Green Climate Fund (GCF)",
        "organization": "Green Climate Fund (GCF)",
        "region": "UN / Multilateral",
        "country": "Republic of Korea",
        "city": "Songdo, Incheon, Republic of Korea",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Master's degree in finance, economics, environment, engineering or a related field with relevant multilateral or banking experience as specified per vacancy.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "The Green Climate Fund is the world's largest dedicated climate finance institution, headquartered in Songdo, Republic of Korea. GCF recruits investment, safeguards, adaptation and programming professionals who structure and oversee climate projects in developing countries. Vacancies are open internationally, and Indian professionals are well represented in the Fund's portfolio and partner networks.",
        "title_hi": "जलवायु वित्त करियर — Green Climate Fund (GCF)",
        "summary_hi": "GCF विश्व का सबसे बड़ा समर्पित जलवायु वित्त संस्थान है, जिसका मुख्यालय दक्षिण कोरिया के सॉन्गदो में है और जो विकासशील देशों में जलवायु परियोजनाओं का वित्तपोषण करता है। वित्त, परियोजना, सुरक्षा-मानक एवं अनुकूलन से जुड़े पदों हेतु अंतर्राष्ट्रीय आवेदन आमंत्रित रहते हैं, जिनके लिए भारतीय पेशेवर भी पात्र हैं।",
        "key_responsibilities": [
            "Appraise and structure climate finance proposals from accredited entities",
            "Monitor funded projects against results and safeguards frameworks",
            "Prepare investment, risk and portfolio analysis",
            "Engage with national designated authorities and delivery partners",
        ],
        "must_have_skills": [
            "Climate finance",
            "Project appraisal",
            "Environmental & social safeguards",
            "Portfolio analysis",
            "Stakeholder engagement",
        ],
        "application_tip": "Study GCF's accreditation and funding frameworks before applying, and highlight any experience with multilateral funds, development banks or climate project pipelines in your application.",
        "apply_url": "https://www.greenclimate.fund/about/careers",
        "org_website": "https://www.greenclimate.fund",
        "org_domain": "greenclimate.fund",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "undp-climate-environment-jobs",
        "clean_title": "Nature, Climate & Energy Roles - UNDP (Global Recruitment)",
        "organization": "United Nations Development Programme (UNDP)",
        "region": "UN / Multilateral",
        "country": "United States",
        "city": "New York / Country Offices (Global)",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Young Professional / Consultant (Contractual)",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Master's degree in environmental science, climate policy, energy, economics or a related field, with experience matching the specific consultancy, NPSA or staff post advertised.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "UNDP's Nature, Climate and Energy practice supports countries on climate action, biodiversity finance, energy transition and resilience across its global network of country offices. Opportunities span staff positions, National Personnel Service Agreement posts and consultancies in more than 170 countries. Indian applicants can apply to both headquarters roles and the large India country-office portfolio.",
        "title_hi": "प्रकृति, जलवायु एवं ऊर्जा पद — UNDP (वैश्विक भर्ती)",
        "summary_hi": "UNDP की प्रकृति, जलवायु एवं ऊर्जा टीम जलवायु कार्रवाई, जैव विविधता वित्त, ऊर्जा संक्रमण एवं अनुकूलन क्षमता पर 170 से अधिक देशों में कार्यरत है। स्टाफ पदों, राष्ट्रीय अनुबंध पदों (NPSA) एवं परामर्शदाता भूमिकाओं हेतु भारतीय पेशेवर सीधे आवेदन कर सकते हैं।",
        "key_responsibilities": [
            "Design and backstop national climate, nature and energy programmes",
            "Prepare project documents, results frameworks and donor reports",
            "Support climate finance and biodiversity finance initiatives",
            "Advise country offices on resilience and energy transition policy",
        ],
        "must_have_skills": [
            "Climate policy",
            "Project management",
            "Climate / biodiversity finance",
            "Monitoring & evaluation",
            "English report writing",
        ],
        "application_tip": "UNDP advertises on its own careers portal; register once and enable job alerts, since many consultancies stay open for only one to two weeks.",
        "apply_url": "https://jobs.undp.org/cj_view_jobs.cfm",
        "org_website": "https://www.undp.org",
        "org_domain": "undp.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "world-bank-group-climate-careers",
        "clean_title": "Climate & Environment Careers - World Bank Group (Washington DC & Global)",
        "organization": "World Bank Group",
        "region": "UN / Multilateral",
        "country": "United States",
        "city": "Washington DC / Country Offices (Global)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "experience_level": "Senior",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Advanced degree in economics, environmental science, engineering, finance or a related field with significant relevant experience; the Young Professionals Program has its own annual criteria.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "The World Bank Group is one of the largest financiers of climate and environment operations in developing countries, covering adaptation, carbon markets, blue economy and environmental safeguards. It recruits economists, engineers and environmental specialists across Washington DC and country offices. Indian nationals work across the institution, and the annual Young Professionals Program is open to candidates worldwide.",
        "title_hi": "जलवायु एवं पर्यावरण करियर — World Bank Group (वॉशिंगटन DC एवं वैश्विक)",
        "summary_hi": "World Bank Group विकासशील देशों में जलवायु एवं पर्यावरण परियोजनाओं का विश्व का सबसे बड़ा वित्तपोषक संस्थान है, जो अनुकूलन, कार्बन बाज़ार एवं पर्यावरणीय सुरक्षा पर कार्य करता है। अर्थशास्त्रियों, इंजीनियरों एवं पर्यावरण विशेषज्ञों के लिए नियुक्तियाँ निरंतर होती हैं और युवा पेशेवर कार्यक्रम (YPP) हेतु भारतीय आवेदक पात्र हैं।",
        "key_responsibilities": [
            "Prepare climate and environment investment operations",
            "Run analytical work on adaptation, carbon markets and safeguards",
            "Supervise project implementation with client governments",
            "Contribute to country climate diagnostics and lending strategy",
        ],
        "must_have_skills": [
            "Development finance",
            "Climate economics",
            "Carbon markets",
            "Environmental safeguards",
            "Client engagement",
        ],
        "application_tip": "Watch the annual Young Professionals Program window (typically mid-year) and prepare a strong statement of interest early, since the process is highly competitive.",
        "apply_url": "https://www.worldbank.org/en/about/careers",
        "org_website": "https://www.worldbank.org",
        "org_domain": "worldbank.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "iucn-south-america-conservation-careers",
        "clean_title": "Conservation & Biodiversity Careers - IUCN South America Regional Office (Quito / Brasilia)",
        "organization": "International Union for Conservation of Nature (IUCN) - South America",
        "region": "Latin America",
        "country": "Ecuador",
        "city": "Quito, Ecuador / Brasilia, Brazil",
        "category": "Forestry, Wildlife & Afforestation",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Degree in conservation biology, environmental science, natural-resource management or a related field, with experience as specified per regional vacancy.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "IUCN's Regional Office for South America has been based in Quito, Ecuador since 1991, supported by an office in Brasilia, Brazil, and leads conservation work across the Amazon, the Andes and the páramos - species and ecosystem conservation, protected-area management, landscape restoration, ecosystem-based adaptation to climate change and bioeconomy. It recruits conservation, restoration and programme professionals on a rolling basis, and international candidates, including Indians, apply directly through the official IUCN portal.",
        "title_hi": "संरक्षण एवं जैव विविधता करियर — IUCN दक्षिण अमेरिका क्षेत्रीय कार्यालय (क्विटो / ब्रासीलिया)",
        "summary_hi": "IUCN का दक्षिण अमेरिका क्षेत्रीय कार्यालय 1991 से क्विटो (इक्वाडोर) में स्थित है और ब्रासीलिया (ब्राज़ील) कार्यालय के साथ अमेज़न, एंडीज़ एवं पैरामो क्षेत्रों में प्रजाति संरक्षण, संरक्षित क्षेत्र प्रबंधन, परिदृश्य पुनर्स्थापन एवं जलवायु अनुकूलन परियोजनाओं का संचालन करता है। संरक्षण एवं पुनर्स्थापन पेशेवरों की निरंतर भर्ती होती है, जिसके लिए भारतीय आवेदक भी पात्र हैं।",
        "key_responsibilities": [
            "Run species, forest or marine conservation programmes",
            "Prepare Red List assessments and biodiversity guidance",
            "Work with members, commissions and partner governments",
            "Support ecosystem-based adaptation planning across the region",
        ],
        "must_have_skills": [
            "Biodiversity conservation",
            "Red List / IUCN standards",
            "Protected area management",
            "Project coordination",
            "Scientific writing",
        ],
        "application_tip": "Register in IUCN's careers portal and consider joining an IUCN commission (for example the Species Survival or Ecosystem Management Commission) to build visibility before applying for staff roles at the regional offices.",
        "apply_url": "https://www.iucn.org/regions/south-america",
        "org_website": "https://www.iucn.org/regions/south-america",
        "org_domain": "iucn.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "wri-global-climate-research-jobs",
        "clean_title": "Climate Research & ESG Careers - World Resources Institute (WRI)",
        "organization": "World Resources Institute (WRI)",
        "region": "North America",
        "country": "United States",
        "city": "Washington DC / Global Offices",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Master's degree in environmental policy, economics, urban planning, geography or a related field, with research or programme experience matching the advertised role.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "WRI is a global research organisation working on climate, cities, energy, food, forests and water, with offices in Washington DC, India, Africa, Latin America and beyond. Its research analyst, programme and communications roles shape climate policy in dozens of countries. WRI India operates one of the network's largest programmes, and staff frequently move between global and India teams.",
        "title_hi": "जलवायु अनुसंधान एवं ESG करियर — World Resources Institute (WRI)",
        "summary_hi": "WRI एक वैश्विक अनुसंधान संस्था है जो जलवायु, शहर, ऊर्जा, खाद्य, वन एवं जल क्षेत्रों पर कार्य करती है तथा वॉशिंगटन DC, भारत, अफ्रीका एवं लैटिन अमेरिका में कार्यालयों से संचालित होती है। शोध विश्लेषक एवं कार्यक्रम पदों हेतु अंतर्राष्ट्रीय आवेदन आमंत्रित रहते हैं और WRI India के माध्यम से भारतीय पेशेवर वैश्विक टीमों से जुड़ते हैं।",
        "key_responsibilities": [
            "Produce policy-relevant climate, energy or urban research",
            "Translate research into actionable recommendations for governments",
            "Support country programmes with data and toolkits",
            "Communicate findings through reports and briefs",
        ],
        "must_have_skills": [
            "Climate policy research",
            "Quantitative analysis",
            "Data visualisation",
            "Policy writing",
            "Stakeholder workshops",
        ],
        "application_tip": "WRI values demonstrable analytical writing; attach or reference published reports and data work in your application materials.",
        "apply_url": "https://www.wri.org/careers",
        "org_website": "https://www.wri.org",
        "org_domain": "wri.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "esa-climate-change-initiative-opportunities",
        "clean_title": "Earth Observation & Climate Data - ESA Climate Change Initiative",
        "organization": "European Space Agency (ESA) Climate Office",
        "region": "Europe",
        "country": "United Kingdom",
        "city": "Harwell, United Kingdom / European Research Partners",
        "category": "GIS, Remote Sensing & Earth Observation",
        "experience_level": "1-3 Years",
        "position_type": "Project Associate / Research Associate",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Degree in remote sensing, geoinformatics, atmospheric or climate science, or a related field, with EO data-processing skills as specified per research call or vacancy.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "The ESA Climate Change Initiative generates Essential Climate Variables from European and international satellite missions, supported by a network of research teams across Europe. Opportunities include research fellowships, living-planet and CCI project positions for remote-sensing and climate-data specialists. These roles suit Indian geospatial scientists seeking international EO experience; individual project pages list their own openings and calls.",
        "title_hi": "पृथ्वी अवलोकन एवं जलवायु डेटा — ESA Climate Change Initiative",
        "summary_hi": "ESA की Climate Change Initiative यूरोपीय एवं अंतर्राष्ट्रीय उपग्रह मिशनों से आवश्यक जलवायु चर (ECV) तैयार करती है और यूरोप भर के शोध समूहों के साथ रिमोट सेंसिंग विशेषज्ञों की नियुक्ति करती है। भारतीय भू-स्थानिक वैज्ञानिक इन परियोजनाओं एवं शोध अवसरों हेतु आवेदन कर सकते हैं; प्रत्येक परियोजना पृष्ठ पर नवीनतम अवसर सूचीबद्ध होते हैं।",
        "key_responsibilities": [
            "Process satellite data into Essential Climate Variables",
            "Validate EO products against in-situ reference data",
            "Develop and document reproducible processing chains",
            "Coordinate with international CCI project teams",
        ],
        "must_have_skills": [
            "Remote sensing",
            "Python / ESA toolboxes",
            "Climate data formats (NetCDF)",
            "Earth observation validation",
            "Scientific documentation",
        ],
        "application_tip": "Build a portfolio of reproducible EO analysis (Sentinel or MODIS based) with public code, since CCI teams value verifiable processing experience over credentials alone.",
        "apply_url": "https://climate.esa.int/en/",
        "org_website": "https://www.esa.int",
        "org_domain": "esa.int",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "future-earth-global-opportunities",
        "clean_title": "Global Sustainability Opportunities - Future Earth Network",
        "organization": "Future Earth",
        "region": "Global / Remote",
        "country": "Global",
        "city": "Remote (Global) / Stockholm Secretariat",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "1-3 Years",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "Rolling / Open",
        "qualification_summary": "Varies by listing: research, programme and communications roles in sustainability science typically require a relevant master's degree or equivalent experience.",
        "compensation_or_fellowship": "Not disclosed - see official portal",
        "role_summary": "Future Earth is a global research network advancing sustainability science, linking thousands of researchers through programmes such as the Global Land Programme and Sustainability Transitions. Its opportunities desk circulates jobs, fellowships and calls from network members and partner institutions worldwide. India has one of the network's largest research communities, so many listed roles are open to Indian applicants or offer remote participation.",
        "title_hi": "वैश्विक सतत विकास अवसर — Future Earth नेटवर्क",
        "summary_hi": "Future Earth एक वैश्विक शोध नेटवर्क है जो सतत विकास विज्ञान को आगे बढ़ाता है और अपने सदस्यों तथा साझेदार संस्थानों की नौकरियों, फेलोशिप एवं कॉल को प्रकाशित करता है। इसके अवसर पृष्ठ पर भारतीय शोधकर्ताओं हेतु उपयुक्त दूरस्थ एवं अंतर्राष्ट्रीय भूमिकाएँ नियमित रूप से सूचीबद्ध होती हैं।",
        "key_responsibilities": [
            "Track global sustainability-science opportunities and calls",
            "Support network research programmes and working groups",
            "Assist with events, synthesis products and communications",
            "Connect regional communities with global initiatives",
        ],
        "must_have_skills": [
            "Sustainability science",
            "Research programme support",
            "Science communication",
            "International collaboration",
            "English writing",
        ],
        "application_tip": "Follow Future Earth's opportunities desk and subscribe to its newsletters, since listings from member institutes often appear there before they circulate on job boards.",
        "apply_url": "https://futureearth.org/opportunities/",
        "org_website": "https://futureearth.org",
        "org_domain": "futureearth.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "undp-gef-small-grants-programme",
        "clean_title": "GEF Small Grants Programme - Community Climate & Biodiversity Grants (UNDP)",
        "organization": "Global Environment Facility Small Grants Programme (SGP), implemented by UNDP",
        "region": "Global / Remote",
        "country": "Global",
        "city": "Country Programmes in 125+ Countries",
        "category": "Grants & Research Funding",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Young Professional / Consultant (Contractual)",
        "opportunity_kind": "Grant / Funding",
        "deadline_or_window": "Annual national calls - check the country page",
        "qualification_summary": "Open to civil-society organisations, community groups and indigenous organisations; grants up to USD 50,000 for community-led projects in biodiversity, climate change mitigation/adaptation, land degradation and chemicals management.",
        "compensation_or_fellowship": "Grants up to USD 50,000 - see official call",
        "role_summary": "The GEF Small Grants Programme, implemented by UNDP, provides financial and technical support to community organisations for climate, biodiversity and land projects in more than 125 countries, including a large India portfolio. National coordination teams issue annual calls for proposals that fund grassroots conservation, renewable energy and adaptation work. It is one of the most accessible international funding routes for Indian community organisations and field researchers.",
        "title_hi": "GEF Small Grants Programme — सामुदायिक जलवायु एवं जैव विविधता अनुदान (UNDP)",
        "summary_hi": "UNDP द्वारा संचालित Global Environment Facility Small Grants Programme 125 से अधिक देशों में सामुदायिक संगठनों को जलवायु, जैव विविधता एवं भूमि क्षरण से जुड़े परियोजनाओं हेतु USD 50,000 तक अनुदान देता है। भारत में राष्ट्रीय समन्वय टीम वार्षिक प्रस्ताव आह्वान जारी करती है, जिसके लिए स्थानीय संगठन सीधे आवेदन कर सकते हैं।",
        "key_responsibilities": [
            "Apply through the national SGP call for proposals",
            "Deliver community-led biodiversity or climate projects",
            "Maintain grant reporting and documentation standards",
            "Engage local stakeholders and co-financing partners",
        ],
        "must_have_skills": [
            "Community mobilisation",
            "Project proposal writing",
            "Grant management",
            "Biodiversity / climate field work",
            "Reporting",
        ],
        "application_tip": "Contact your national SGP office before drafting, since each country page lists its current call window, thematic priorities and required templates.",
        "apply_url": "https://sgp.undp.org/",
        "org_website": "https://sgp.undp.org",
        "org_domain": "sgp.undp.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "chevening-scholarships-masters",
        "clean_title": "Chevening Scholarships - Fully Funded Master's in the UK (Climate & Sustainability Tracks)",
        "organization": "Chevening Scholarships - UK Government (FCDO)",
        "region": "Europe",
        "country": "United Kingdom",
        "city": "UK Universities",
        "category": "Scholarships & Doctoral Support",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Scholarship",
        "deadline_or_window": "Annual cycle - applications typically open August to October",
        "qualification_summary": "Bachelor's degree (for master's entry), at least two years of work or leadership experience, and an unconditional offer from a UK course by the reference deadline; open to Indian citizens.",
        "compensation_or_fellowship": "Tuition fully funded + monthly living stipend + travel - see official portal",
        "role_summary": "Chevening is the UK government's fully funded international scholarship, covering tuition, living costs and travel for one-year master's degrees at UK universities. Indian applicants regularly win places in climate policy, environment, sustainability and energy programmes. The scholarship selects on leadership, networking and career-plan potential rather than academic scores alone.",
        "title_hi": "Chevening छात्रवृत्ति — ब्रिटेन में पूर्णतः वित्तपोषित मास्टर्स (जलवायु एवं सतत विकास)",
        "summary_hi": "Chevening ब्रिटेन सरकार की पूर्णतः वित्तपोषित अंतर्राष्ट्रीय छात्रवृत्ति है जो जलवायु नीति, पर्यावरण एवं सतत विकास जैसे विषयों में एक वर्षीय मास्टर्स हेतु ट्यूशन, रहने का खर्च एवं यात्रा प्रदान करती है। भारतीय नागरिक प्रत्येक वर्ष आवेदन कर सकते हैं; चयन नेतृत्व क्षमता एवं करियर योजना पर आधारित होता है।",
        "key_responsibilities": [
            "Secure admission to an eligible UK master's programme",
            "Submit the online Chevening application within the annual window",
            "Demonstrate leadership and career plan in interviews",
            "Complete the degree and join the global Chevening network",
        ],
        "must_have_skills": [
            "Leadership",
            "Climate / sustainability subject knowledge",
            "Academic writing",
            "Networking",
            "English proficiency (IELTS as required by the course)",
        ],
        "application_tip": "Draft your essays around concrete leadership stories and a clear return-home plan, and apply to UK courses in parallel so you can meet the offer deadline.",
        "apply_url": "https://www.chevening.org/scholarships/",
        "org_website": "https://www.chevening.org",
        "org_domain": "chevening.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "erasmus-mundus-joint-masters",
        "clean_title": "Erasmus Mundus Joint Masters - Climate, Environment & Sustainability Programmes (EU)",
        "organization": "European Commission - Erasmus+ (EACEA)",
        "region": "Europe",
        "country": "European Union",
        "city": "Multiple European Universities",
        "category": "Scholarships & Doctoral Support",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Scholarship",
        "deadline_or_window": "Annual cycle - most consortia close December to January",
        "qualification_summary": "Bachelor's degree for master's entry; each consortium sets its own discipline requirements. Scholarship applications are open to candidates worldwide, including India.",
        "compensation_or_fellowship": "Scholarships cover tuition, travel and living costs - see official catalogue",
        "role_summary": "Erasmus Mundus Joint Masters are prestigious two-year degrees delivered by consortia of European universities, with fully funded scholarships for excellent candidates worldwide. Catalogue entries include climate change, environmental sciences, sustainability, forestry and geospatial specialisations. Indian graduates receive a large share of these scholarships each year, and the catalogue lists every programme with its own application portal.",
        "title_hi": "Erasmus Mundus संयुक्त मास्टर्स — जलवायु, पर्यावरण एवं सतत विकास कार्यक्रम (यूरोपीय संघ)",
        "summary_hi": "Erasmus Mundus संयुक्त मास्टर्स यूरोपीय विश्वविद्यालयों के समूहों द्वारा संचालित दो-वर्षीय प्रतिष्ठित डिग्री कार्यक्रम हैं, जिनमें जलवायु, पर्यावरण विज्ञान, वानिकी एवं भू-स्थानिक विशेषज्ञता शामिल है। विश्व भर के उत्कृष्ट अभ्यर्थियों हेतु छात्रवृत्तियाँ उपलब्ध हैं और भारतीय स्नातक प्रत्येक वर्ष बड़ी संख्या में चयनित होते हैं।",
        "key_responsibilities": [
            "Choose consortia matching your climate / environment goals",
            "Apply directly through each programme's portal",
            "Prepare motivation letters and references early",
            "Plan mobility between the consortium universities",
        ],
        "must_have_skills": [
            "Subject expertise (environment / climate)",
            "English or consortium language proficiency",
            "Motivation letter writing",
            "Academic references",
            "Intercultural adaptability",
        ],
        "application_tip": "Filter the official catalogue by climate and environment fields, and shortlist three to four programmes: applications are free and deadlines cluster around January.",
        "apply_url": "https://www.eacea.ec.europa.eu/scholarships/erasmus-mundus-catalogue_en",
        "org_website": "https://www.eacea.ec.europa.eu",
        "org_domain": "eacea.ec.europa.eu",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "unu-ias-postdoctoral-fellowships",
        "clean_title": "Postdoctoral & Research Fellowships - UNU-IAS, Tokyo (Sustainability)",
        "organization": "United Nations University - Institute for the Advanced Study of Sustainability (UNU-IAS)",
        "region": "Asia-Pacific",
        "country": "Japan",
        "city": "Tokyo, Japan",
        "category": "Fellowships & Leadership Programs",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "PhD / Doctoral Fellowship",
        "opportunity_kind": "Fellowship",
        "deadline_or_window": "Annual calls - check the opportunities page",
        "qualification_summary": "PhD completed (or near completion) in sustainability-related fields for postdoctoral fellows; specific JSPS and project fellowships list their own eligibility.",
        "compensation_or_fellowship": "Monthly fellowship stipend + research allowance - see official call",
        "role_summary": "UNU-IAS in Tokyo advances sustainability research and education, hosting postdoctoral fellows, JSPS research fellows and visiting scholars working on biodiversity, climate, water and governance themes. Fellowships run for defined terms with stipends and research support in Japan. Calls are open internationally, and Indian researchers have strong representation in UNU-IAS programmes.",
        "title_hi": "पोस्टडॉक्टोरल एवं शोध फेलोशिप — UNU-IAS, टोक्यो (सतत विकास)",
        "summary_hi": "UNU-IAS टोक्यो में सतत विकास पर केंद्रित शोध एवं शिक्षण संचालित होता है, जहाँ पोस्टडॉक्टोरल, JSPS एवं परियोजना फेलोशिप हेतु प्रतिवर्ष आवेदन आमंत्रित किए जाते हैं। जैव विविधता, जलवायु, जल एवं शासन विषयों पर कार्यरत भारतीय शोधकर्ता इन अंतर्राष्ट्रीय फेलोशिप हेतु पात्र हैं।",
        "key_responsibilities": [
            "Conduct independent sustainability research with UNU-IAS faculty",
            "Publish peer-reviewed and policy outputs",
            "Participate in capacity-development programmes",
            "Contribute to international research networks",
        ],
        "must_have_skills": [
            "Research methods",
            "Peer-reviewed publishing",
            "Sustainability / climate expertise",
            "Interdisciplinary collaboration",
            "English academic writing",
        ],
        "application_tip": "Frame your research proposal around UNU-IAS thematic priorities and contact potential supervisors before the call closes; reference lists are competitive.",
        "apply_url": "https://ias.unu.edu/en/opportunities",
        "org_website": "https://ias.unu.edu",
        "org_domain": "ias.unu.edu",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "unfccc-internship-programme",
        "clean_title": "Internship Programme - UNFCCC Secretariat (Climate Policy, Bonn)",
        "organization": "United Nations Framework Convention on Climate Change (UNFCCC)",
        "region": "UN / Multilateral",
        "country": "Germany",
        "city": "Bonn, Germany (some teams support remote interns)",
        "category": "Internships & Student Traineeships",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Internship",
        "deadline_or_window": "Rolling / Open - internship calls posted continuously",
        "qualification_summary": "Enrolled in or recently completed a bachelor's / master's degree in climate, environment, economics, law, communications or a related field; strong English writing skills.",
        "compensation_or_fellowship": "Monthly internship stipend (varies) - see official portal",
        "role_summary": "The UNFCCC internship programme places students and recent graduates in the secretariat's divisions in Bonn, working alongside negotiators, analysts and communications teams on the international climate process. Internships run for up to six months and are open to applicants of all nationalities. It is a recognised entry route into multilateral climate work for young Indian graduates.",
        "title_hi": "इंटर्नशिप कार्यक्रम — UNFCCC सचिवालय (जलवायु नीति, बॉन)",
        "summary_hi": "UNFCCC इंटर्नशिप कार्यक्रम विद्यार्थियों एवं नए स्नातकों को बॉन स्थित सचिवालय के विभागों में वार्ताकारों एवं विश्लेषकों के साथ कार्य करने का अवसर देता है। यह अंतर्राष्ट्रीय जलवायु क्षेत्र में प्रवेश का मान्य मार्ग है, जिसके लिए सभी राष्ट्रीयताओं के आवेदक, जिनमें भारतीय स्नातक भी शामिल हैं, पात्र हैं।",
        "key_responsibilities": [
            "Support negotiation sessions and inter-sessional work",
            "Draft briefings, summaries and communication products",
            "Maintain databases and knowledge platforms",
            "Assist project teams across secretariat divisions",
        ],
        "must_have_skills": [
            "Climate policy literacy",
            "Research and drafting",
            "English writing",
            "MS Office / data tools",
            "Teamwork in multicultural settings",
        ],
        "application_tip": "Internship calls appear and close within weeks; set up alerts on the UNFCCC vacancies page and prepare a precise cover letter mapped to the division you target.",
        "apply_url": "https://unfccc.int/about-us/internships",
        "org_website": "https://unfccc.int",
        "org_domain": "unfccc.int",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "zayed-sustainability-prize",
        "clean_title": "Zayed Sustainability Prize - Global Awards for Climate, Energy, Water & Food Innovators",
        "organization": "Zayed Sustainability Prize (UAE)",
        "region": "Africa & Middle East",
        "country": "United Arab Emirates",
        "city": "Abu Dhabi, UAE",
        "category": "Competitions, Hackathons & Awards",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Competition / Award",
        "deadline_or_window": "Annual cycle - submissions typically close in spring",
        "qualification_summary": "Open to small and medium enterprises, non-profit organisations and high schools worldwide with sustainability solutions in health, food, energy, water or climate action categories.",
        "compensation_or_fellowship": "Prize funds per category - see official portal",
        "role_summary": "The Zayed Sustainability Prize honours organisations and schools delivering impactful, innovative and inspiring sustainability solutions across energy, water, food, health and climate action. Winners share a multi-million-dollar prize fund awarded at the UAE Sustainability Week in Abu Dhabi. Indian social enterprises and schools have been among the winners in past cycles.",
        "title_hi": "Zayed Sustainability Prize — जलवायु, ऊर्जा, जल एवं खाद्य नवाचार हेतु वैश्विक पुरस्कार",
        "summary_hi": "Zayed Sustainability Prize ऊर्जा, जल, खाद्य, स्वास्थ्य एवं जलवायु कार्रवाई के क्षेत्र में प्रभावी एवं नवाचारी समाधान प्रस्तुत करने वाले संगठनों तथा विद्यालयों को सम्मानित करता है। भारतीय सामाजिक उद्यम एवं विद्यालय भी प्रत्येक वर्ष इस वैश्विक पुरस्कार हेतु आवेदन कर सकते हैं, जिसका वितरण अबू धाबी में होता है।",
        "key_responsibilities": [
            "Submit an impact-driven entry in the relevant category",
            "Document measurable sustainability outcomes",
            "Provide references and verification evidence",
            "Engage with the global winners network",
        ],
        "must_have_skills": [
            "Impact measurement",
            "Sustainability innovation",
            "Project documentation",
            "Pitching",
            "Partnership building",
        ],
        "application_tip": "Quantify your impact with verifiable numbers in the entry form, since the jury scores measurable outcomes above narrative.",
        "apply_url": "https://zayedsustainabilityprize.org/",
        "org_website": "https://zayedsustainabilityprize.org",
        "org_domain": "zayedsustainabilityprize.org",
    },
    {
        **_GLOBAL_SEED_BASE,
        "id": "earthshot-prize",
        "clean_title": "The Earthshot Prize - GBP 1 Million Awards for Environmental Solutions",
        "organization": "The Earthshot Prize (Royal Foundation)",
        "region": "Global / Remote",
        "country": "United Kingdom",
        "city": "London, United Kingdom / Global",
        "category": "Competitions, Hackathons & Awards",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Competition / Award",
        "deadline_or_window": "Annual cycle - nominations open each year",
        "qualification_summary": "Open to innovators, communities, businesses and organisations worldwide with solutions across the five Earthshots: climate, biodiversity, nature protection, air and ocean.",
        "compensation_or_fellowship": "GBP 1 million per winner - see official portal",
        "role_summary": "The Earthshot Prize awards five one-million-pound prizes each year to the most inspiring and impactful environmental solutions, spanning climate, nature, oceans, air and waste. Finalists and winners receive global visibility and a fellowship of support, and entries from South Asia have featured strongly. Indian innovators working on clean air, restoration or circular economy solutions can be nominated or apply through the open process.",
        "title_hi": "The Earthshot Prize — पर्यावरणीय समाधानों हेतु 1 मिलियन पाउंड के वैश्विक पुरस्कार",
        "summary_hi": "Earthshot Prize प्रत्येक वर्ष जलवायु, प्रकृति, महासागर, वायु एवं अपशिष्ट क्षेत्रों के पाँच सर्वाधिक प्रभावी पर्यावरणीय समाधानों को 1 मिलियन पाउंड का पुरस्कार एवं वैश्विक पहचान प्रदान करता है। दक्षिण एशियाई परियोजनाएँ पहले भी फाइनलिस्ट रही हैं, और भारतीय नवप्रवर्तक खुले नामांकन माध्यम से आवेदन कर सकते हैं।",
        "key_responsibilities": [
            "Submit a scalable environmental solution to the annual cycle",
            "Evidence community and ecological impact",
            "Prepare for the global awards process",
            "Scale with fellowship support if shortlisted",
        ],
        "must_have_skills": [
            "Environmental innovation",
            "Scalable business model",
            "Impact evidence",
            "Storytelling",
            "International partnerships",
        ],
        "application_tip": "Nominations can be routed through official nominators; large organisations and past finalists publish the path, so contact a nominator early if you cannot apply directly.",
        "apply_url": "https://earthshotprize.org/",
        "org_website": "https://earthshotprize.org",
        "org_domain": "earthshotprize.org",
    },
]

_GLOBAL_NEWS_QUERIES = [
    '("Climate" OR "Environment" OR "Sustainability") ("vacancy" OR "careers" OR "jobs") '
    '("UN" OR "UNFCCC" OR "UNDP" OR "UNEP" OR "World Bank" OR "IUCN" OR "WRI" OR "CGIAR")',
    '("PhD" OR "postdoctoral" OR "fellowship") ("climate" OR "ecology" OR "conservation") '
    '("fully funded" OR "scholarship" OR "apply")',
    '("climate" OR "conservation" OR "biodiversity") ("grant" OR "call for proposals" OR "funding") '
    '("apply by" OR "deadline" OR "open call")',
    '("climate" OR "sustainability") ("internship" OR "traineeship") '
    '("United Nations" OR "UNEP" OR "UNDP" OR "World Bank" OR "IUCN")',
    '("climate" OR "sustainability") ("competition" OR "hackathon" OR "prize" OR "award") '
    '("youth" OR "students" OR "innovators")',
]

# A global headline must resolve to an institutional / academic / organisation
# domain before it can become a global candidate.
GLOBAL_VERIFIABLE_HOST_RE = re.compile(
    r"\.(int|org|edu|gov|eu|un\.org|ac\.[a-z]{2,3}|edu\.[a-z]{2,3}|org\.[a-z]{2,3})$",
    re.I,
)
GLOBAL_VERIFIABLE_DOMAINS = (
    "linkedin.com",
    "reliefweb.int",
    "un.org",
    "undp.org",
    "iucn.org",
    "wri.org",
    "worldbank.org",
    "greenclimate.fund",
    "unfccc.int",
    "cgiar.org",
    "cifor-icraf.org",
    "futureearth.org",
)


def _is_global_verifiable_host(url: str) -> bool:
    host = host_of(url)
    if not host:
        return False
    if any(host == d or host.endswith("." + d) for d in GLOBAL_VERIFIABLE_DOMAINS):
        return True
    return bool(GLOBAL_VERIFIABLE_HOST_RE.search(host))


def _google_news_query_url_global(query: str) -> str:
    return GOOGLE_NEWS_RSS_SEARCH + "?" + urlencode(
        {"q": query + " when:14d", "hl": "en", "gl": "US", "ceid": "US:en"}
    )


def _global_news_entry_to_candidate(
    entry: Dict[str, Any], query: str
) -> Optional[Dict[str, Any]]:
    """Convert one global news entry into a candidate, or None when unusable."""
    title = squash(strip_html(entry.get("title") or ""))
    link = str(entry.get("link") or "").strip()
    if not title or not link.lower().startswith("http"):
        return None
    publisher = ""
    source = entry.get("source")
    if isinstance(source, dict):
        publisher = squash(source.get("title") or "")
    if publisher and title.endswith(" - " + publisher):
        title = title[: -(len(publisher) + 3)].strip()
    if not JOB_AD_TITLE_RE.search(title):
        return None
    if NEWS_NOISE_TITLE_RE.search(title):
        return None
    summary = strip_html(entry.get("summary") or entry.get("description") or "")[:4000]
    date_posted = ""
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published is not None:
        try:
            date_posted = date(published[0], published[1], published[2]).isoformat()
        except (TypeError, ValueError, IndexError, AttributeError):
            date_posted = ""
    if date_posted:
        age_cutoff = (date.today() - timedelta(days=GLOBAL_NEWS_MAX_AGE_DAYS)).isoformat()
        if date_posted < age_cutoff:
            return None
    if is_google_news_url(link):
        resolved = resolve_google_news_link(link)
        if not resolved:
            return None
        link = resolved
    if not _is_global_verifiable_host(link):
        return None
    return {
        "source": "google-news-global",
        "title": title,
        "organization": publisher or "International organisation (see announcement)",
        "location_raw": "International",
        "description": summary,
        "apply_url": link,
        "date_posted": date_posted,
        "matched_query": query,
        "global": True,
    }


def fetch_global_opportunities() -> List[Dict[str, Any]]:
    """Zero-key harvest of global climate / sustainability opportunities.

    Public Google News RSS searches surface international vacancies, grants,
    scholarships, fellowships, internships and competitions; each headline is
    screened for opportunity phrasing and must resolve to an institutional
    domain. Every candidate then passes the same Gemini humanizer (global
    prompt) and verifiability gate as the India pipeline, but is written
    ONLY to the global registry files.
    """
    if feedparser is None or requests is None:
        log.warning("feedparser/requests unavailable - skipping global harvest")
        return []

    candidates: List[Dict[str, Any]] = []
    seen_links: Set[str] = set()
    for query in _GLOBAL_NEWS_QUERIES:
        url = _google_news_query_url_global(query)
        try:
            response = requests.get(
                url, headers=HTTP_SIMPLE_HEADERS, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as exc:
            log.warning("Global Google News query failed (%s): %s", query[:60], exc)
            continue
        added = 0
        for entry in (feed.entries or [])[:GOOGLE_NEWS_RESULTS_PER_QUERY]:
            candidate = _global_news_entry_to_candidate(entry, query)
            if candidate is None:
                continue
            key = normalize_key(candidate.get("apply_url") or "")
            if key in seen_links:
                continue
            seen_links.add(key)
            candidates.append(candidate)
            added += 1
        log.info("Global news query returned %d usable candidate(s): %s", added, query[:60])
    return candidates


def normalize_global_record(job: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a stored global record: base schema + region discipline."""
    job = normalize_job_fields(job)
    job["global"] = True
    region = squash(job.get("region"))
    job["region"] = region if region in GLOBAL_REGIONS else "Global / Remote"
    if job.get("state") and job.get("state") not in ("", "Multiple States / Remote"):
        # Global records never masquerade as Indian states.
        job["state"] = ""
    return job


def ensure_global_seed(jobs: List[Dict[str, Any]], today: str) -> int:
    """Merge the verified evergreen global seed into the active list.

    Idempotent: seed ids already present (active or archived) are left
    untouched, so manual edits and archive history are never overwritten.
    """
    taken_ids = {str(job.get("id") or "") for job in jobs}
    added = 0
    for seed in GLOBAL_SEED_OPPORTUNITIES:
        seed_id = str(seed.get("id") or "")
        if not seed_id or seed_id in taken_ids:
            continue
        record = dict(seed)
        record.setdefault("date_added", today)
        record.setdefault("deadline_or_window", "Rolling / Open")
        record.setdefault("status", "active")
        jobs.append(record)
        taken_ids.add(seed_id)
        added += 1
    if added:
        log.info("Seeded %d evergreen global opportunit(ies)", added)
    return added


def apply_global_lifecycle(
    jobs: List[Dict[str, Any]],
    archive: List[Dict[str, Any]],
    today: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """Global lifecycle: normal expiry rules, evergreen records never expire."""
    evergreen = [job for job in jobs if job.get("evergreen")]
    decayable = [job for job in jobs if not job.get("evergreen")]
    active, archive_out, newly_archived = apply_job_lifecycle(decayable, archive, today)

    today_value = parse_iso_date(today) or date.today()
    for job in evergreen:
        # Evergreen never expires -- but it can still be quarantined. A
        # quarantine block always wins over the evergreen status reset.
        if job.get("status") == "quarantined" or job.get("quarantine"):
            job["status"] = "quarantined"
            job.setdefault("status_before_quarantine", "active")
            active.append(job)
            continue
        job["status"] = "active"
        added = parse_iso_date(job.get("date_added")) or today_value
        job["date_added"] = added.isoformat()
        if not job.get("valid_through"):
            job["valid_through"] = (added + timedelta(days=3650)).isoformat()
        active.append(job)

    active_ids = {str(job.get("id") or "") for job in active}
    archive_out = [
        record for record in archive_out if str(record.get("id") or "") not in active_ids
    ]
    active.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )
    return active, archive_out, newly_archived


def run_global_stage(
    jobs_path: Path,
    archive_path: Path,
    today: str,
    api_key: Optional[str] = None,
    max_new: int = GLOBAL_MAX_NEW_PER_RUN,
) -> Tuple[int, int]:
    """Refresh the strictly separated global registry.

    Always: load + normalize both global files, merge the evergreen seed and
    apply the global lifecycle. When a Gemini key is available: additionally
    harvest a handful of fresh international opportunities and humanize them
    through the dedicated global prompt. Returns (active_count, new_count).
    """
    existing = [normalize_global_record(job) for job in load_jobs(jobs_path)]
    archive = [normalize_global_record(job) for job in load_jobs(archive_path)]
    log.info(
        "Global registry: %d active, %d archived before this run",
        len(existing), len(archive),
    )
    ensure_global_seed(existing, today)

    accepted: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []
    if api_key and GreenJob is not None:
        candidates = fetch_global_opportunities()
        seen = existing_keys(existing + archive)
        fresh: List[Dict[str, Any]] = []
        for candidate in candidates:
            if not (candidate.get("title") and candidate.get("apply_url")):
                continue
            if not is_valid_apply_url(candidate.get("apply_url")):
                continue
            key = dedupe_key(candidate)
            if not key or key in seen:
                continue
            seen.add(key)
            fresh.append(candidate)
        fresh = fresh[: max(0, max_new)]
        log.info(
            "Global registry: %d new candidate(s) to humanize (cap=%d)",
            len(fresh), max_new,
        )

        if fresh:
            humanizer = GeminiHumanizer(api_key, today, mode="global")
            taken_ids = {
                str(job.get("id") or "")
                for job in existing + archive
                if job.get("id")
            }
            rate_limited = False
            for index, candidate in enumerate(fresh, start=1):
                label = squash(candidate.get("title"))[:70]
                try:
                    reply = humanizer.complete(build_user_prompt(candidate, today))
                    data = parse_model_json(reply)
                    record, reason = coerce_to_job_record(data, candidate, today)
                    if record is not None and not is_valid_apply_url(record.get("apply_url")):
                        record, reason = None, "apply URL failed validation"
                    if record is not None:
                        record = normalize_global_record(record)
                        record["global"] = True
                        record["evergreen"] = False
                        record, reason = gate_candidate(
                            record,
                            _employer_registry(),
                            today,
                            resolve_news_url=resolve_google_news_link,
                        )
                        if record is not None:
                            record = normalize_global_record(record)
                    if record is None:
                        log.info(
                            "[global %d/%d] skipped %r - %s",
                            index, len(fresh), label, reason,
                        )
                    else:
                        record["id"] = unique_id(record["id"], taken_ids)
                        if record.get("status") == "quarantined":
                            quarantined.append(record)
                            log.warning(
                                "[global %d/%d] quarantined %s - %s",
                                index, len(fresh), record["id"],
                                (record.get("quarantine") or {}).get(
                                    "reason_code", reason
                                ),
                            )
                        else:
                            accepted.append(record)
                            log.info(
                                "[global %d/%d] accepted %s", index, len(fresh), record["id"]
                            )
                except GeminiRateLimited as exc:
                    rate_limited = True
                    log.warning(
                        "[global %d/%d] Gemini rate-limited for %r | %s",
                        index, len(fresh), label, str(exc)[:160],
                    )
                    break
                except Exception as exc:
                    log.warning(
                        "[global %d/%d] humanizer failed for %r: %s | %s",
                        index, len(fresh), label, type(exc).__name__, str(exc)[:160],
                    )
                time.sleep(GEMINI_SLEEP_SECONDS)

    merged = accepted + quarantined + existing
    merged.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )
    active, archive_out, newly_archived = apply_global_lifecycle(merged, archive, today)
    write_jobs(active, jobs_path)
    write_archive(archive_out, archive_path)
    log.info(
        "Global registry done: %d active (%d new this run), %d archived (%d newly archived).",
        len(active), len(accepted), len(archive_out), newly_archived,
    )
    return len(active), len(accepted)


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

    def __init__(self, api_key: str, today: str, mode: str = "india") -> None:
        if _GENAI_MODE is None:
            raise RuntimeError(
                "No Gemini SDK found. Install with: pip install google-genai"
            )
        self.mode = _GENAI_MODE
        self.system_instruction = (
            build_global_system_prompt(today)
            if mode == "global"
            else build_system_prompt(today)
        )
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

    position_type = match_enum(job.position_type, POSITION_TYPES) or infer_position_type(
        squash(job.clean_title), category
    )
    qualification_source = squash(job.qualification_summary)
    compensation_source = squash(job.compensation_or_fellowship)
    deadline_source = squash(job.deadline_or_window)
    qualification_summary = qualification_source or default_qualification_summary(position_type)
    compensation_or_fellowship = compensation_source or default_compensation(position_type)

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
    opportunity_kind = match_enum(job.opportunity_kind, OPPORTUNITY_KINDS) or ""
    deadline_or_window = deadline_source or "Rolling / Open"
    record = {
        "id": squash(job.id),
        "date_added": today,
        "clean_title": clean_title,
        "organization": organization,
        "state": state,
        "city": squash(job.city),
        "category": category,
        "experience_level": experience,
        "position_type": position_type,
        "opportunity_kind": opportunity_kind,
        "deadline_or_window": deadline_or_window,
        "region": squash(job.region),
        "country": squash(job.country),
        "qualification_summary": qualification_summary,
        "compensation_or_fellowship": compensation_or_fellowship,
        "role_summary": role_summary,
        "key_responsibilities": responsibilities,
        "must_have_skills": skills,
        "application_tip": application_tip,
        "apply_url": apply_url,
        "org_website": squash(job.org_website),
        "org_domain": squash(job.org_domain).strip(".").lower(),
        "source_portal": squash(job.source_portal),
        # Internal gate flags: placeholders are not LLM claims and must not be
        # demanded on the fetched page. Removed before publication.
        "_qualification_is_default": not qualification_source,
        "_compensation_is_default": not compensation_source,
        "_deadline_is_default": not deadline_source,
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
    """Final gate: invalid URLs and anonymous employers never persist."""
    valid: List[Dict[str, Any]] = []
    dropped = 0
    blocked = 0
    for job in jobs:
        # Quarantined records are the review queue: never deleted, never
        # published. Their apply_url may be temporarily broken; keep them.
        if job.get("status") == "quarantined":
            valid.append(job)
            continue
        if has_blocked_organization(job):
            blocked += 1
            continue
        if is_valid_apply_url(job.get("apply_url")):
            valid.append(job)
        else:
            dropped += 1
    if dropped:
        log.warning(
            "Dropped %d listing(s) with empty/placeholder apply URLs", dropped
        )
    if blocked:
        log.warning(
            "Dropped %d listing(s) with anonymous employer names", blocked
        )
    return valid


def write_jobs(jobs: List[Dict[str, Any]], path: Path) -> None:
    jobs = filter_valid_jobs([normalize_job_fields(job) for job in jobs])
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
        if record.get("status") != "quarantined" and not record.get("quarantine"):
            record["status"] = "archived"
            record.setdefault("date_archived", today)
        else:
            # Quarantine wins over archive: keep it hidden and unreachable.
            record["status"] = "quarantined"
            record.setdefault("status_before_quarantine", "archived")
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
        # Quarantined listings stay in the review queue: hidden from the site,
        # never aged into the archive and never reactivated automatically.
        # A stale quarantine block (status flipped by an older bug) still wins.
        if job.get("status") == "quarantined" or job.get("quarantine"):
            job["status"] = "quarantined"
            job.setdefault("status_before_quarantine", "active")
            active.append(job)
            continue
        added = parse_iso_date(job.get("date_added")) or today_value
        job["date_added"] = added.isoformat()
        # Expiry: archive on the stated deadline. With no deadline, cap the
        # listing at VALID_DAYS and schedule the day-15 re-verification.
        deadline = deadline_date(job)
        if deadline is not None:
            valid_through = deadline
            job.pop("reverify_after", None)
        else:
            valid_through = added + timedelta(days=VALID_DAYS)
            job["reverify_after"] = (
                added + timedelta(days=max(1, VALID_DAYS // 2))
            ).isoformat()
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


def published_records(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Records that are publicly visible: not quarantined, not hidden.

    ``entry_type == "unknown"`` is hidden by placement policy; legacy records
    without the field are treated as postings for backward compatibility.
    """
    return [
        job
        for job in jobs
        if job.get("status") != "quarantined"
        and not job.get("quarantine")
        and str(job.get("entry_type") or "posting") != "unknown"
    ]


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
    jobs = filter_valid_jobs([normalize_job_fields(job) for job in jobs])
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
# Community broadcasting: daily WhatsApp bulletin + Telegram channel post
# ---------------------------------------------------------------------------
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_MESSAGE_LIMIT = 3900   # Telegram hard limit is 4096; keep headroom
DIGEST_MAX_JOBS = 10            # jobs listed per digest / broadcast


def _community_links() -> Tuple[str, str]:
    whatsapp = (os.environ.get("WHATSAPP_GROUP_URL") or "").strip() or WHATSAPP_GROUP_URL
    telegram = (os.environ.get("TELEGRAM_CHANNEL_URL") or "").strip() or TELEGRAM_CHANNEL_URL
    return whatsapp, telegram


def _html_escape_text(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _location_line(job: Dict[str, Any]) -> str:
    city = squash(job.get("city"))
    state = squash(job.get("state"))
    if city and state:
        return f"{city}, {state}"
    return city or state or "India"


def build_whatsapp_job_block(job: Dict[str, Any], index: Optional[int] = None) -> str:
    """One rich, forward-ready WhatsApp alert block for a single job."""
    share_url = f"{SITE_BASE_URL}/?job={quote(str(job.get('id') or ''))}"
    lines = []
    if index is not None:
        lines.append(f"{index}. *{squash(job.get('clean_title'))}*")
    else:
        lines += ["🌱 *NEW GREEN / RESEARCH JOB ALERT*", ""]
        lines.append(f"📌 *Role:* {squash(job.get('clean_title'))}")
    lines.append(f"🏛️ *Organization:* {squash(job.get('organization'))}")
    lines.append(f"📍 *Location:* {_location_line(job)}")
    lines.append(f"🎓 *Eligibility:* {squash(job.get('qualification_summary')) or 'As per institute norms'}")
    lines.append(f"💰 *Fellowship/Pay:* {squash(job.get('compensation_or_fellowship')) or 'As per institute norms'}")
    valid_through = squash(job.get("valid_through"))[:10]
    if valid_through:
        lines.append(f"🕒 *Apply before:* {valid_through}")
    lines.append("")
    lines.append(f"🔗 *Full Details & Apply:* {share_url}")
    return "\n".join(lines)


def build_whatsapp_digest_text(
    jobs: List[Dict[str, Any]], today: str, heading: str
) -> str:
    """Ready-to-paste WhatsApp/Telegram bulletin covering the listed jobs."""
    whatsapp, telegram = _community_links()
    parts = [
        "🌱 *India Green, Forestry, JRF & ESG Jobs | पर्यावरण एवं अनुसंधान भर्ती अपडेट*",
        f"🗓️ {today} · {len(jobs)} mandate(s) · {len(jobs)} भर्तियाँ",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
    ]
    parts.append(f"*{heading}*")
    parts.append("")
    for position, job in enumerate(jobs, start=1):
        parts.append(build_whatsapp_job_block(job, index=position))
        parts.append("")
    parts += [
        "━━━━━━━━━━━━━━━━━━━━",
        "📡 *Never miss a verified green job:*",
        f"• WhatsApp group: {whatsapp}",
        f"• Telegram channel: {telegram}",
        f"• Full registry: {SITE_BASE_URL}",
    ]
    return "\n".join(parts).strip() + "\n"


def build_telegram_digest_html(
    jobs: List[Dict[str, Any]], today: str, heading: str
) -> str:
    """Telegram-flavoured (HTML parse_mode) version of the same digest."""
    whatsapp, telegram = _community_links()
    lines = [
        "🌱 <b>India Green, Forestry, JRF &amp; ESG Jobs</b> | पर्यावरण एवं अनुसंधान भर्ती अपडेट",
        f"<i>{_html_escape_text(today)} · {len(jobs)} mandate(s) · {len(jobs)} भर्तियाँ</i>",
        "",
        f"<b>{_html_escape_text(heading)}</b>",
        "",
    ]
    for position, job in enumerate(jobs, start=1):
        share_url = f"{SITE_BASE_URL}/?job={quote(str(job.get('id') or ''))}"
        links = f'<a href="{_html_escape_text(share_url)}">Full details &amp; apply</a>'
        lines += [
            f"<b>{position}. {_html_escape_text(squash(job.get('clean_title')))}</b> — "
            f"{_html_escape_text(squash(job.get('organization')))} "
            f"({_html_escape_text(_location_line(job))})",
            f"🎓 {_html_escape_text(squash(job.get('qualification_summary')))}",
            f"💰 {_html_escape_text(squash(job.get('compensation_or_fellowship')))}",
            f"🔗 {links}",
            "",
        ]
    lines += [
        "📡 <b>Never miss an alert:</b>",
        f'• <a href="{_html_escape_text(whatsapp)}">WhatsApp group</a>',
        f'• <a href="{_html_escape_text(telegram)}">Telegram channel</a>',
        f'• <a href="{SITE_BASE_URL}/">{SITE_BASE_URL.replace("https://", "")}</a>',
    ]
    return "\n".join(lines)


def _chunk_text(text: str, limit: int) -> List[str]:
    """Split a message into Telegram-safe chunks on line boundaries."""
    chunks: List[str] = []
    current = ""
    for line in text.splitlines(True):
        if current and len(current) + len(line) > limit:
            chunks.append(current.rstrip("\n"))
            current = ""
        current += line
    if current.strip():
        chunks.append(current.rstrip("\n"))
    return chunks


def write_digests(
    active: List[Dict[str, Any]],
    new_jobs: List[Dict[str, Any]],
    today: str,
    digest_path: Path,
    whatsapp_path: Path,
) -> Dict[str, Any]:
    """Generate daily_digest.json + whatsapp_digest.txt for the site owner.

    `new_jobs` are the listings accepted by this run; on maintenance-only
    runs the digest falls back to the freshest active mandates so the files
    (and the footer copy button) are refreshed on every run.

    Quarantined records and records hidden by placement policy never appear
    in a digest, even if a caller passes the raw active list.
    """
    def publishable(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            job
            for job in rows
            if job.get("status") != "quarantined"
            and str(job.get("entry_type") or "posting") != "unknown"
        ]

    new_jobs = publishable(new_jobs)
    active = publishable(active)

    if new_jobs:
        listed = new_jobs[:DIGEST_MAX_JOBS]
        heading = f"{len(new_jobs)} new verified mandate(s) added today"
    else:
        listed = sorted(
            active,
            key=lambda job: (
                str(job.get("date_added") or ""),
                str(job.get("id") or ""),
            ),
            reverse=True,
        )[:DIGEST_MAX_JOBS]
        heading = "Latest verified mandates on the registry"

    jobs_payload = []
    for job in listed:
        jobs_payload.append(
            {
                "id": squash(job.get("id")),
                "clean_title": squash(job.get("clean_title")),
                "organization": squash(job.get("organization")),
                "city": squash(job.get("city")),
                "state": squash(job.get("state")),
                "category": squash(job.get("category")),
                "position_type": squash(job.get("position_type")),
                "qualification_summary": squash(job.get("qualification_summary")),
                "compensation_or_fellowship": squash(job.get("compensation_or_fellowship")),
                "valid_through": squash(job.get("valid_through"))[:10],
                # Broadcasts and the public digest carry dossier URLs only.
                # apply_url / org_website / org_domain are never included.
                "source_portal": squash(job.get("source_portal")),
                "url": f"{SITE_BASE_URL}/?job={quote(str(job.get('id') or ''))}",
            }
        )

    whatsapp_text = build_whatsapp_digest_text(listed, today, heading)
    telegram_html = build_telegram_digest_html(listed, today, heading)
    digest = {
        "generated_at": today,
        "new_count": len(new_jobs),
        "count": len(jobs_payload),
        "heading": heading,
        "site": SITE_BASE_URL,
        "jobs": jobs_payload,
        "whatsapp_text": whatsapp_text,
        "telegram_html": telegram_html,
    }

    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(
        json.dumps(digest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    whatsapp_path.parent.mkdir(parents=True, exist_ok=True)
    whatsapp_path.write_text(whatsapp_text, encoding="utf-8")
    log.info(
        "Wrote daily digest (%d job(s)) to %s + %s",
        len(jobs_payload), digest_path, whatsapp_path,
    )
    return digest


def send_telegram_digest(telegram_html: str) -> bool:
    """Post the digest to the configured Telegram channel (no-op without env)."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not token or not chat_id:
        log.info(
            "Telegram broadcast skipped (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set)"
        )
        return False
    if requests is None:
        log.warning("requests is not installed - cannot broadcast to Telegram")
        return False
    delivered = 0
    for chunk in _chunk_text(telegram_html, TELEGRAM_MESSAGE_LIMIT):
        try:
            response = requests.post(
                TELEGRAM_API_URL.format(token=token),
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": False,
                },
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                delivered += 1
            else:
                log.warning(
                    "Telegram API returned HTTP %s: %s",
                    response.status_code, (response.text or "")[:200],
                )
        except Exception as exc:
            log.warning("Telegram broadcast failed: %s", str(exc)[:160])
    if delivered:
        log.info("Telegram broadcast delivered (%d message chunk(s))", delivered)
    return delivered > 0


def send_whatsapp_webhook(whatsapp_text: str) -> bool:
    """Optional headless WhatsApp delivery via WHATSAPP_WEBHOOK_URL."""
    webhook = (os.environ.get("WHATSAPP_WEBHOOK_URL") or "").strip()
    if not webhook:
        log.info("WhatsApp webhook not configured (WHATSAPP_WEBHOOK_URL unset) - digest file only")
        return False
    if requests is None:
        return False
    try:
        response = requests.post(
            webhook,
            json={"message": whatsapp_text, "text": whatsapp_text},
            timeout=REQUEST_TIMEOUT,
        )
        if 200 <= response.status_code < 300:
            log.info("WhatsApp webhook accepted the digest (HTTP %s)", response.status_code)
            return True
        log.warning(
            "WhatsApp webhook returned HTTP %s: %s",
            response.status_code, (response.text or "")[:200],
        )
    except Exception as exc:
        log.warning("WhatsApp webhook failed: %s", str(exc)[:160])
    return False


def broadcast_new_jobs(
    active: List[Dict[str, Any]],
    new_jobs: List[Dict[str, Any]],
    today: str,
    digest_path: Path,
    whatsapp_path: Path,
    send: bool = True,
) -> None:
    """Regenerate the digest files and broadcast new listings when possible."""
    digest = write_digests(active, new_jobs, today, digest_path, whatsapp_path)
    if not send:
        log.info(
            "Broadcast HELD: digest written, Telegram/WhatsApp not sent "
            "(--no-broadcast). Review daily_digest.json + whatsapp_digest.txt."
        )
        return
    if not new_jobs:
        log.info("No new listings this run - Telegram/WhatsApp broadcast skipped")
        return
    send_telegram_digest(digest["telegram_html"])
    send_whatsapp_webhook(digest["whatsapp_text"])


# ---------------------------------------------------------------------------
# sitemap.xml generation
# ---------------------------------------------------------------------------
def pretty_loc(url: str) -> str:
    """Extensionless form Cloudflare Pages serves with HTTP 200.

    ``/about.html`` redirects (308) to ``/about``, so sitemap entries must use
    the pretty path to stay canonical, indexable and redirect-free.
    """
    if not url.startswith(SITE_BASE_URL):
        return url
    path, sep, tail = url[len(SITE_BASE_URL):].partition("?")
    frag = ""
    if "#" in tail:
        tail, _, frag = tail.partition("#")
    if path == "/index.html":
        path = "/"
    elif path.endswith(".html"):
        path = path[:-5]
    rebuilt = SITE_BASE_URL + path
    if sep:
        rebuilt += "?" + tail
    if frag:
        rebuilt += "#" + frag
    return rebuilt


def write_sitemap(
    active_jobs: List[Dict[str, Any]],
    archive_jobs: List[Dict[str, Any]],
    path: Path,
) -> None:
    """Regenerate sitemap.xml for the registry.

    Includes the homepage, /dashboard, the archive view (/?view=archive), the
    category landing views (/?category=<slug>), the busiest state landing views
    (/?state=<State>), every active listing (/?job=<id>, priority 0.8,
    lastmod = date_added) and every archived listing (priority 0.5,
    lastmod = date_archived). All page URLs are emitted in the extensionless
    form the host serves with HTTP 200.
    """
    jobs = [
        job
        for job in filter_valid_jobs(active_jobs)
        if job.get("status") != "quarantined"
        and (job.get("entry_type") or "posting") != "unknown"
    ]
    archive = [
        record
        for record in filter_valid_jobs(archive_jobs)
        if record.get("status") != "quarantined"
    ]
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
                preserved[pretty_loc(loc)] = {
                    "lastmod": (node.findtext("{" + SITEMAP_NS + "}lastmod") or node.findtext("lastmod") or "").strip(),
                    "changefreq": (node.findtext("{" + SITEMAP_NS + "}changefreq") or node.findtext("changefreq") or "").strip(),
                    "priority": (node.findtext("{" + SITEMAP_NS + "}priority") or node.findtext("priority") or "").strip(),
                }
        except Exception as exc:
            log.warning("Could not parse existing sitemap (%s); generating fresh", exc)

    entries: Dict[str, Dict[str, str]] = {}

    home_url = SITE_BASE_URL + "/"
    dash_url = SITE_BASE_URL + "/dashboard"
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
        if "?van=" in loc:
            continue  # filtered spatial views canonicalise to spatial-data.html
        entries[loc] = {
            "lastmod": meta.get("lastmod") or today,
            "changefreq": meta.get("changefreq") or "monthly",
            "priority": meta.get("priority") or "0.6",
        }

    # Seed known static pages. Existing entries are preserved; newly added
    # institutional pages are picked up even when a sitemap already exists.
    for page_path, changefreq, priority in STATIC_SITEMAP_PAGES:
        loc = pretty_loc(SITE_BASE_URL + page_path)
        if loc not in entries:
            entries[loc] = {
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

    # Career-pathway hub pages (pre-rendered by scripts/build_seo_pages.py
    # on every pipeline run, so they always exist when this runs).
    for page_path in SEO_HUB_PAGES:
        entries[pretty_loc(SITE_BASE_URL + page_path)] = {
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9",
        }

    # Multilingual & regional portals (Hindi hub + state-wise regional hub).
    for page_path in MULTILINGUAL_PORTAL_PAGES:
        entries[pretty_loc(SITE_BASE_URL + page_path)] = {
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9",
        }

    # Global opportunities portal (strictly separated registry).
    for page_path in GLOBAL_PORTAL_PAGES:
        entries[pretty_loc(SITE_BASE_URL + page_path)] = {
            "lastmod": today,
            "changefreq": "weekly",
            "priority": "0.9",
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
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}loc").text = pretty_loc(loc)
        lastmod = meta["lastmod"]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod or ""):
            lastmod = today
        ET.SubElement(url_node, "{" + SITEMAP_NS + "}lastmod").text = lastmod
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
        "--digest-json",
        help="Path to daily_digest.json (default: public/daily_digest.json)",
    )
    parser.add_argument(
        "--digest-txt",
        help="Path to whatsapp_digest.txt (default: public/whatsapp_digest.txt)",
    )
    parser.add_argument(
        "--global-jobs",
        help="Path to global_jobs.json (default: public/global_jobs.json)",
    )
    parser.add_argument(
        "--global-archive",
        help="Path to global_archive.json (default: public/global_archive.json)",
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
    parser.add_argument(
        "--digest-only",
        action="store_true",
        help=(
            "Regenerate daily_digest.json + whatsapp_digest.txt from the current "
            "published records without scraping or sending anything."
        ),
    )
    parser.add_argument(
        "--no-broadcast",
        action="store_true",
        help=(
            "Generate daily_digest.json + whatsapp_digest.txt but do NOT send "
            "Telegram/WhatsApp messages (hold for review)."
        ),
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
    digest_json_path = (
        Path(args.digest_json) if args.digest_json else resolve_default(DEFAULT_DIGEST_JSON_PATH)
    )
    whatsapp_digest_path = (
        Path(args.digest_txt) if args.digest_txt else resolve_default(DEFAULT_WHATSAPP_DIGEST_PATH)
    )
    global_jobs_path = (
        Path(args.global_jobs) if args.global_jobs else resolve_default(DEFAULT_GLOBAL_JOBS_PATH)
    )
    global_archive_path = (
        Path(args.global_archive)
        if args.global_archive
        else resolve_default(DEFAULT_GLOBAL_ARCHIVE_PATH)
    )

    existing = [normalize_job_fields(job) for job in load_jobs(jobs_path)]
    archive = [normalize_job_fields(job) for job in load_jobs(archive_path)]
    log.info(
        "Loaded %d active listing(s) from %s and %d archived listing(s) from %s",
        len(existing), jobs_path, len(archive), archive_path,
    )

    today = date.today().isoformat()

    if args.sitemap_only:
        write_sitemap(existing, archive, sitemap_path)
        return 0

    if args.digest_only:
        write_digests(existing, [], today, digest_json_path, whatsapp_digest_path)
        return 0

    if args.sync_only:
        # Maintenance-only run: expire passed listings into the archive,
        # refresh the weekly telemetry and rewrite every published data file.
        # No scraping and no Gemini calls, so it works without an API key.
        active, archive, newly_archived = apply_job_lifecycle(existing, archive, today)
        stats = compute_stats(
            published_records(active), published_records(archive), today
        )
        write_jobs(active, jobs_path)
        write_archive(archive, archive_path)
        write_stats(stats, stats_path)
        write_sitemap(active, archive, sitemap_path)
        write_digests(active, [], today, digest_json_path, whatsapp_digest_path)
        # The strictly separated global registry is maintained in the same
        # run (seeds + lifecycle only; no scraping and no API key needed).
        run_global_stage(global_jobs_path, global_archive_path, today, api_key=None)
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

    # 1. Gather raw candidates from all sources. The per-source groups are
    # round-robin interleaved so a single noisy source cannot consume the
    # whole humanization budget (--max-new) on its own.
    log.info("Lookback window for this run: %d hour(s)", resolve_lookback_hours())
    board_candidates = scrape_board_candidates()
    targeted_candidates = fetch_targeted_green_jobs()
    reliefweb_candidates = fetch_reliefweb_jobs()
    academic_candidates = fetch_indian_academic_and_institute_jobs()
    portal_candidates = fetch_verified_indian_portals()
    freejobalert_candidates = fetch_freejobalert()
    official_candidates = fetch_official_pages()
    ats_candidates = fetch_ats_feeds(_employer_registry())
    candidates = interleave_candidates(
        [
            academic_candidates,
            freejobalert_candidates,
            official_candidates,
            ats_candidates,
            portal_candidates,
            reliefweb_candidates,
            targeted_candidates,
            board_candidates,
        ]
    )
    log.info(
        "Collected %d raw candidate(s) from all sources "
        "(institute-news=%d, freejobalert=%d, official=%d, ats=%d, portals=%d, "
        "reliefweb=%d, targeted=%d, boards=%d)",
        len(candidates),
        len(academic_candidates),
        len(freejobalert_candidates),
        len(official_candidates),
        len(ats_candidates),
        len(portal_candidates),
        len(reliefweb_candidates),
        len(targeted_candidates),
        len(board_candidates),
    )

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
    quarantined: List[Dict[str, Any]] = []
    source_leads = Counter(str(item.get("source") or "unknown") for item in candidates)
    source_stats = {
        name: {"leads": count, "passed": 0, "active": 0}
        for name, count in source_leads.items()
    }
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
            if record is not None:
                # Phase 3 gate: registry -> verified fetch -> landing page ->
                # content match -> field-in-source. Fail closed: unverified
                # candidates are quarantined, never published.
                record, reason = gate_candidate(
                    record,
                    _employer_registry(),
                    today,
                    resolve_news_url=resolve_google_news_link,
                )
            if record is None:
                log.info("[%d/%d] skipped %r - %s", index, len(fresh), label, reason)
            else:
                record_key = dedupe_key(record)
                if record_key in seen:
                    log.info(
                        "[%d/%d] skipped %r - duplicate of a listing already in the registry",
                        index, len(fresh), label,
                    )
                    continue
                seen.add(record_key)
                record["id"] = unique_id(record["id"], taken_ids)
                source_name = str(candidate.get("source") or "unknown")
                source_stats.setdefault(
                    source_name, {"leads": 0, "passed": 0, "active": 0}
                )
                source_stats[source_name]["passed"] += 1
                if record.get("status") == "quarantined":
                    quarantined.append(record)
                    log.warning(
                        "[%d/%d] quarantined %s - %s",
                        index, len(fresh), record["id"],
                        (record.get("quarantine") or {}).get("reason_code", reason),
                    )
                else:
                    accepted.append(record)
                    if record.get("status") == "active":
                        source_stats[source_name]["active"] += 1
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
    #    Quarantined records are kept in the data files for review but are
    #    never published, counted or broadcast.
    merged = accepted + quarantined + existing
    merged.sort(
        key=lambda job: (str(job.get("date_added") or ""), str(job.get("id") or "")),
        reverse=True,
    )

    if args.dry_run:
        log.info("DRY RUN: %d new listing(s) accepted; nothing written.", len(accepted))
        return 0

    active, archive, newly_archived = apply_job_lifecycle(merged, archive, today)
    # Telemetry counts only published records: quarantined rows and records
    # whose entry type is unknown (hidden by placement policy) are excluded.
    published = published_records(active)
    published_archive = published_records(archive)
    stats = compute_stats(published, published_archive, today)

    write_jobs(active, jobs_path)
    write_archive(archive, archive_path)
    write_stats(stats, stats_path)

    # 5. Regenerate the sitemap for Google Jobs indexing.
    write_sitemap(active, archive, sitemap_path)

    # 5b. Global opportunities registry - strictly separate files
    #     (global_jobs.json / global_archive.json), seed + fresh harvest.
    run_global_stage(global_jobs_path, global_archive_path, today, api_key=api_key)

    # 6. Per-source yield report (leads -> passed -> active).
    write_source_report(
        jobs_path.parent / "source_report.json",
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "policy_version": 2,
            "limits": SOURCE_LIMITS,
            "state_queries": len(STATE_QUERIES),
            "sources": dict(
                sorted(
                    source_stats.items(),
                    key=lambda item: (-item[1]["leads"], item[0]),
                )
            ),
            "totals": {
                "leads": sum(item["leads"] for item in source_stats.values()),
                "passed": sum(item["passed"] for item in source_stats.values()),
                "active": sum(item["active"] for item in source_stats.values()),
            },
        },
    )

    # 7. Refresh the daily WhatsApp bulletin + broadcast to Telegram when
    #    TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID (or a WhatsApp webhook) are set.
    broadcast_new_jobs(
        published,
        accepted,
        today,
        digest_json_path,
        whatsapp_digest_path,
        send=not args.no_broadcast,
    )

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
