#!/usr/bin/env python3
"""Extra public sources for the daily pipeline (policy v2).

All adapters use public pages/APIs that permit automated access. Nothing logs
in, bypasses a paywall or scrapes a site that forbids automation. Every
adapter is best-effort: a blocked or changed upstream simply yields zero leads
and the run continues.

Sources:
  * FreeJobAlert public search results (specific notice pages);
  * official recruitment / notice pages (ICFRE, FSI, WII, IIFM, MoEFCC,
    CPCB, ICAR, CSIR, IITs, IISc, NIO);
  * Greenhouse / Lever / SmartRecruiters public job APIs for employers that
    already exist in public/employers.json.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import quote_plus, urljoin, urlparse

import certifi
import requests
from bs4 import BeautifulSoup

log = logging.getLogger("ufp-jobs.sources")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}
TIMEOUT = 25

GREEN_TERMS = (
    "forest", "forestry", "wildlife", "biodiversity", "ecology", "climate",
    "sustainab", "environment", "carbon", "esg", "brsr", "gis", "remote sensing",
    "geospatial", "watershed", "water resource", "agroforest", "renewable",
    "solar", "circular economy", "waste management", "pollution", "air quality",
    "jrf", "srf", "project associate", "research associate", "project assistant",
    "research fellow", "young professional", "conservation", "urban forest",
    "urban planning", "ehs", "eia",
)

# 15 states/regions that previously had few or no listings.
STATES = [
    "Uttar Pradesh", "Madhya Pradesh", "Rajasthan", "Himachal Pradesh",
    "Uttarakhand", "Jharkhand", "Chhattisgarh", "Andhra Pradesh", "Goa",
    "Assam", "Meghalaya", "Nagaland", "Tripura", "Manipur", "Arunachal Pradesh",
]

STATE_QUERIES = [
    f"forestry forest guard wildlife environment sustainability GIS jobs {state}"
    for state in STATES
]

FREEFOBALERT_QUERIES = [
    "forest guard", "forest officer", "forester", "wildlife", "environment",
    "sustainability", "climate change", "ESG", "carbon", "GIS remote sensing",
    "JRF SRF", "project associate environment", "pollution control board",
    "water resources", "renewable energy",
]

OFFICIAL_PAGES: List[Tuple[str, str]] = [
    # Forestry, ecology and statutory science institutes
    ("Indian Council of Forestry Research and Education (ICFRE)", "https://icfre.gov.in/recruitments"),
    ("Forest Research Institute (FRI), Dehradun", "https://fri.icfre.gov.in/recruitment"),
    ("Institute of Forest Genetics and Tree Breeding (IFGTB)", "https://ifgtb.icfre.gov.in/"),
    ("Institute of Wood Science and Technology (IWST)", "https://iwst.icfre.gov.in/"),
    ("Tropical Forest Research Institute (TFRI)", "https://tfri.icfre.gov.in/"),
    ("Arid Forest Research Institute (AFRI)", "https://afri.icfre.gov.in/"),
    ("Rain Forest Research Institute (RFRI)", "https://rfri.icfre.gov.in/"),
    ("Himalayan Forest Research Institute (HFRI)", "https://hfri.icfre.gov.in/"),
    ("Institute of Forest Biodiversity (IFB), Hyderabad", "https://ifb.icfre.gov.in/"),
    ("Forest Survey of India (FSI)", "https://fsi.nic.in/recruitment"),
    ("Wildlife Institute of India (WII)", "https://wii.gov.in/recruitment"),
    ("Indian Institute of Forest Management (IIFM)", "https://iifm.ac.in/careers"),
    ("Botanical Survey of India (BSI)", "https://bsi.gov.in/"),
    ("Zoological Survey of India (ZSI)", "https://zsi.gov.in/"),
    ("GBPIHED / NIHE Almora", "https://gbpihed.gov.in/recruitment"),
    ("SACON Coimbatore", "https://sacon.in/careers/"),
    ("National Centre for Sustainable Coastal Management (NCSCM)", "https://www.ncscm.res.in/careers"),
    ("Ministry of Environment, Forest and Climate Change (MoEFCC)", "https://moef.gov.in/recruitment"),
    ("Central Pollution Control Board (CPCB)", "https://cpcb.nic.in/recruitment/"),
    # Geospatial, earth, atmospheric and marine sciences
    ("Indian Institute of Remote Sensing (IIRS)", "https://www.iirs.gov.in/recruitment"),
    ("National Remote Sensing Centre (NRSC)", "https://www.nrsc.gov.in/recruitment"),
    ("Space Applications Centre (SAC), ISRO", "https://www.sac.gov.in/"),
    ("Indian Institute of Tropical Meteorology (IITM)", "https://www.tropmet.res.in/careers"),
    ("National Centre for Polar and Ocean Research (NCPOR)", "https://www.ncpore.res.in/"),
    ("National Institute of Ocean Technology (NIOT)", "https://www.niot.res.in/careers"),
    ("Indian National Centre for Ocean Information Services (INCOIS)", "https://incois.gov.in/recruitment"),
    ("National Institute of Oceanography (NIO)", "https://www.nio.res.in/careers"),
    # Agricultural and environmental research councils
    ("Indian Council of Agricultural Research (ICAR)", "https://icar.org.in/recruitment"),
    ("ICAR-IARI New Delhi", "https://iari.res.in/recruitment"),
    ("ICAR-CAZRI Jodhpur", "https://cazri.res.in/recruitment"),
    ("ICAR-CRIDA Hyderabad", "https://crida.in/recruitment"),
    ("ICAR-NBPGR New Delhi", "https://nbpgr.icar.gov.in/"),
    ("ICAR-CSSRI Karnal", "https://cssri.res.in/"),
    ("ICAR-IIWM Bhubaneswar", "https://iiwm.res.in/"),
    ("ICAR-NAARM Hyderabad", "https://naarm.org.in/careers"),
    ("CSIR", "https://www.csir.res.in/careers"),
    ("CSIR-NEERI Nagpur", "https://neeri.res.in/careers"),
    ("CSIR-NBRI Lucknow", "https://nbri.res.in/recruitment"),
    ("CSIR-CIMAP Lucknow", "https://cimap.res.in/"),
    ("CSIR-4PI Bengaluru", "https://4pi.res.in/"),
    # Premier universities and sponsored research portals
    ("IIT Delhi", "https://home.iitd.ac.in/jobs.php"),
    ("IIT Bombay", "https://www.iitb.ac.in/en/career"),
    ("IIT Kharagpur", "https://www.iitkgp.ac.in/recruitment"),
    ("IIT Roorkee", "https://www.iitr.ac.in/recruitment"),
    ("IIT Madras", "https://www.iitm.ac.in/careers"),
    ("IIT Guwahati", "https://www.iitg.ac.in/recruitment"),
    ("IIT Kanpur", "https://www.iitk.ac.in/dord/recruitment"),
    ("Indian Institute of Science (IISc)", "https://iisc.ac.in/careers/"),
    ("IISER Pune", "https://www.iiserpune.ac.in/careers"),
    ("Jawaharlal Nehru University (JNU)", "https://www.jnu.ac.in/careers"),
    ("Banaras Hindu University (BHU)", "https://bhu.ac.in/recruitment"),
    ("Tata Institute of Social Sciences (TISS)", "https://tiss.edu/careers"),
    ("TERI School of Advanced Studies (TERI SAS)", "https://terisas.ac.in/careers"),
    ("Department of Science and Technology (DST)", "https://dst.gov.in/careers"),
    ("Anusandhan National Research Foundation (ANRF)", "https://anrf.gov.in/"),
    ("Science and Engineering Research Board (SERB)", "https://serb.gov.in/"),
    ("Department of Biotechnology (DBT)", "https://dbtindia.gov.in/careers"),
]

SOURCE_LIMITS = {
    "jobspy_results_per_query": {"old": 15, "new": 50},
    "max_new_per_run": {"old": 12, "new": 60},
    "global_max_new_per_run": {"old": 4, "new": 12},
    "google_news_results_per_query": {"old": 25, "new": 50},
    "reliefweb_limit": {"old": 60, "new": 100},
    "freejobalert_per_query": {"old": 0, "new": 8},
    "official_pages": {"old": 0, "new": len(OFFICIAL_PAGES)},
}


JUNK_TERMS = (
    "admit card", "answer key", "result", "syllabus", "previous papers",
    "cut off", "exam date", "hall ticket", "merit list", "question paper",
)


def _relevant(title: str) -> bool:
    lowered = (title or "").lower()
    if any(term in lowered for term in JUNK_TERMS):
        return False
    return any(term in lowered for term in GREEN_TERMS)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = certifi.where()
    return session


def fetch_freejobalert(per_query: int = 8) -> List[Dict[str, Any]]:
    """FreeJobAlert public search results, specific notice pages only."""
    out: List[Dict[str, Any]] = []
    seen = set()
    session = _session()
    try:
        for query in FREEFOBALERT_QUERIES:
            url = "https://www.freejobalert.com/search-jobs/?q=" + quote_plus(query)
            try:
                response = session.get(url, timeout=TIMEOUT)
                if response.status_code != 200:
                    log.info("FreeJobAlert %r -> HTTP %s", query, response.status_code)
                    continue
            except Exception as exc:
                log.info("FreeJobAlert %r failed: %s", query, type(exc).__name__)
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            kept = 0
            for anchor in soup.select("a[href*='/articles/']"):
                href = urljoin(url, anchor.get("href") or "")
                title = _clean(anchor.get_text(" ", strip=True))
                if not title or len(title) < 15 or href in seen:
                    continue
                if not _relevant(title):
                    continue
                seen.add(href)
                out.append(
                    {
                        "source": "freejobalert",
                        "title": title[:180],
                        "organization": "See notification (FreeJobAlert)",
                        "location_raw": "India",
                        "description": "",
                        "apply_url": href,
                        "date_posted": date.today().isoformat(),
                        "matched_query": query,
                    }
                )
                kept += 1
                if kept >= per_query:
                    break
    finally:
        session.close()
    return out


def _extract_official_page(org: str, page_url: str, html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, Any]] = []
    seen = set()
    for anchor in soup.select("a[href]"):
        href = urljoin(page_url, anchor.get("href") or "")
        title = _clean(anchor.get_text(" ", strip=True))
        if not title or len(title) < 12 or len(title) > 200:
            continue
        if not href.lower().startswith("http"):
            continue
        if href.rstrip("/") == page_url.rstrip("/") or href in seen:
            continue
        path = urlparse(href).path
        if path in ("", "/") or not _relevant(title):
            continue
        seen.add(href)
        out.append(
            {
                "source": "official-page",
                "title": title,
                "organization": org,
                "location_raw": "India",
                "description": "",
                "apply_url": href,
                "date_posted": date.today().isoformat(),
                "matched_query": org,
            }
        )
        if len(out) >= 15:
            break
    return out


def _root_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return url
    return f"{parsed.scheme}://{parsed.netloc}/"


def fetch_official_pages() -> List[Dict[str, Any]]:
    """Harvest specific notice links from official recruitment pages.

    Institute sites frequently move their recruitment page without leaving a
    redirect (a stale /recruitment path returns 404 while the homepage still
    links the current notice board). A homepage fallback keeps those sources
    useful instead of silently losing an entire institute.
    """
    out: List[Dict[str, Any]] = []
    session = _session()
    try:
        for org, url in OFFICIAL_PAGES:
            try:
                response = session.get(url, timeout=TIMEOUT)
                page_url = url
                if response.status_code in (403, 404):
                    root = _root_url(url)
                    if root != url:
                        fallback = session.get(root, timeout=TIMEOUT)
                        if fallback.status_code == 200:
                            log.info(
                                "Official page %s -> HTTP %s; using homepage fallback %s",
                                url, response.status_code, root,
                            )
                            response = fallback
                            page_url = root
                if response.status_code != 200:
                    log.info("Official page %s -> HTTP %s", url, response.status_code)
                    continue
                out.extend(_extract_official_page(org, page_url, response.text))
            except Exception as exc:
                log.info("Official page %s failed: %s", url, type(exc).__name__)
    finally:
        session.close()
    return out


def fetch_ats_feeds(registry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Public ATS APIs for employers already in the registry.

    The current registry contains no Greenhouse/Lever/SmartRecruiters boards,
    so this returns [] until such a domain is added. The adapter is kept so
    new registry entries work without code changes.
    """
    out: List[Dict[str, Any]] = []
    session = _session()
    try:
        for employer in registry.get("employers", []):
            hosts = [
                str(value).lower()
                for value in (employer.get("domains") or [])
                + (employer.get("ats_hosts") or [])
            ]
            token = ""
            kind = ""
            for host in hosts:
                if "greenhouse.io" in host:
                    kind = "greenhouse"
                    token = host.split(".")[0]
                elif "lever.co" in host:
                    kind = "lever"
                    token = host.split(".")[0]
                elif "smartrecruiters.com" in host:
                    kind = "smartrecruiters"
                    token = host.split(".")[0]
            if not kind or not token:
                continue
            try:
                if kind == "greenhouse":
                    api = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
                    payload = session.get(api, timeout=TIMEOUT).json()
                    for job in payload.get("jobs", []):
                        out.append(
                            {
                                "source": "greenhouse",
                                "title": _clean(job.get("title")),
                                "organization": employer.get("name") or token,
                                "location_raw": _clean(
                                    (job.get("location") or {}).get("name") or "India"
                                ),
                                "description": BeautifulSoup(
                                    job.get("content") or "", "html.parser"
                                ).get_text(" ", strip=True)[:4000],
                                "apply_url": job.get("absolute_url") or "",
                                "date_posted": date.today().isoformat(),
                                "matched_query": "greenhouse",
                            }
                        )
                elif kind == "lever":
                    api = f"https://api.lever.co/v0/postings/{token}?mode=json"
                    payload = session.get(api, timeout=TIMEOUT).json()
                    for job in payload if isinstance(payload, list) else []:
                        out.append(
                            {
                                "source": "lever",
                                "title": _clean(job.get("text")),
                                "organization": employer.get("name") or token,
                                "location_raw": _clean(
                                    (job.get("categories") or {}).get("location") or "India"
                                ),
                                "description": _clean(job.get("descriptionPlain"))[:4000],
                                "apply_url": job.get("hostedUrl") or "",
                                "date_posted": date.today().isoformat(),
                                "matched_query": "lever",
                            }
                        )
                elif kind == "smartrecruiters":
                    api = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
                    payload = session.get(api, timeout=TIMEOUT).json()
                    for job in payload.get("content", []):
                        out.append(
                            {
                                "source": "smartrecruiters",
                                "title": _clean(job.get("name")),
                                "organization": employer.get("name") or token,
                                "location_raw": _clean(
                                    (job.get("location") or {}).get("city") or "India"
                                ),
                                "description": "",
                                "apply_url": (
                                    f"https://jobs.smartrecruiters.com/{token}/{job.get('id')}"
                                ),
                                "date_posted": date.today().isoformat(),
                                "matched_query": "smartrecruiters",
                            }
                        )
            except Exception as exc:
                log.info("ATS %s/%s failed: %s", kind, token, type(exc).__name__)
    finally:
        session.close()
    return out


def write_source_report(path: Path, report: Dict[str, Any]) -> None:
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
