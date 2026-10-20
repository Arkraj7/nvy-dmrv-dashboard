#!/usr/bin/env python3
"""Ingestion gate for the daily jobs pipeline (Phase 3).

Every candidate must be verified at its source *before* anything is written to
the public data files. The gate is fail-closed:

    P3 blocklist -> registry -> fetch -> landing-page -> content match
    -> field-in-source -> publish (or quarantine, never delete)

The LLM may only restructure text that exists on the fetched apply page.
Titles, deadlines, compensation, qualifications and must-have skills must be
present verbatim (or fuzzy >= 0.9). Anything else is quarantined with
``FIELD_NOT_IN_SOURCE``.

Public helpers are intentionally pure/small so the pipeline and pytest share
exactly the same code path.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import certifi
import requests
from bs4 import BeautifulSoup

from link_policy import is_shortener, is_wrapper, strip_tracking as policy_strip_tracking
from verify_link import (
    DEAD_LINK,
    NOT_DIRECT_LINK,
    UNKNOWN_KEEP,
    UNRESOLVED_WRAPPER,
    load_employers_registry,
    verify_link,
)

log = logging.getLogger(__name__)

PAGE_TEXT_LIMIT = 20000
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 "
        "UrbanForestPark-LinkGate/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

TRACKING_PREFIXES = (
    "utm_", "fbclid", "gclid", "mc_cid", "mc_eid", "igshid",
    "ref", "referrer", "source", "campaign",
)
TRACKING_EXACT = {"ref", "referrer", "source", "campaign", "trk", "trackingid"}

FIELD_LABELS = {
    "clean_title": "title",
    "deadline_or_window": "deadline",
    "compensation_or_fellowship": "compensation",
    "qualification_summary": "qualifications",
    "must_have_skills": "must-have skills",
}

PLACEHOLDER_DEADLINES = {
    "", "rolling / open", "rolling", "open", "ongoing", "rolling/open",
    "open until filled", "as per notification",
}

CLOSED_PHRASES = (
    "applications are closed",
    "application closed",
    "applications closed",
    "position closed",
    "position has been closed",
    "vacancy closed",
    "no longer accepting applications",
    "no longer accepting application",
    "recruitment closed",
    "deadline has passed",
)


# ---------------------------------------------------------------------------
# Small text helpers
# ---------------------------------------------------------------------------
def _norm(text: Any) -> str:
    value = str(text or "").lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _slug(text: Any) -> str:
    return "-".join(_norm(text).split())


def strip_tracking(url: str) -> str:
    """Remove tracking parameters from a URL, keeping real query values."""
    raw = str(url or "").strip()
    if not raw:
        return raw
    parsed = urlparse(raw)
    if not parsed.query:
        return raw
    kept = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not (
            key.lower() in TRACKING_EXACT
            or key.lower().startswith(TRACKING_PREFIXES)
        )
    ]
    return urlunparse(parsed._replace(query=urlencode(kept, doseq=True)))


def normalize_deadline(value: Any) -> str:
    """Return ISO date when the deadline is parseable, else normalised text."""
    text = str(value or "").strip()
    if _norm(text) in PLACEHOLDER_DEADLINES:
        return ""
    iso = parse_deadline(text)
    if iso is not None:
        return iso.isoformat()
    return _norm(text)


def parse_deadline(value: Any) -> Optional[date]:
    """Best-effort parse of common deadline formats; None when not a date."""
    text = str(value or "").strip()
    if not text:
        return None
    if _norm(text) in PLACEHOLDER_DEADLINES:
        return None
    # ISO first (the pipeline usually stores YYYY-MM-DD)
    head = text[:10]
    try:
        return date.fromisoformat(head)
    except ValueError:
        pass
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y",
                "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text.strip(" ."), fmt).date()
        except ValueError:
            continue
    return None


def deadline_date(record: Dict[str, Any]) -> Optional[date]:
    """Deadline for a record, ignoring rolling/open placeholders."""
    return parse_deadline(record.get("deadline_or_window"))


def fuzzy_in_source(needle: Any, haystack: Any, threshold: float = 0.9) -> bool:
    """True when *needle* appears in *haystack* exactly or fuzzy >= threshold.

    Matching is case/punctuation insensitive. Fuzzy comparison slides a window
    the size of the needle across the haystack so short skills and long
    qualification sentences are both handled.
    """
    target = _norm(needle)
    if not target:
        return True
    source = _norm(haystack)
    if not source:
        return False
    if target in source:
        return True

    target_tokens = target.split()
    source_tokens = source.split()
    size = len(target_tokens)
    if size == 0 or len(source_tokens) < size:
        return False

    # Numbers matter: "INR 60,000" and "INR 99,000" are 0.9-similar strings
    # but different claims. Every digit group must occur in the source.
    digits = re.findall(r"\d+", target)
    if digits and not all(digit in source_tokens for digit in digits):
        return False

    first = target_tokens[0]
    anchors = [i for i, token in enumerate(source_tokens) if token == first]
    if not anchors:
        anchors = list(range(0, max(1, len(source_tokens) - size + 1), 2))

    best = 0.0
    for width in {max(1, size - 1), size, size + 1}:
        for start in anchors:
            if start + width > len(source_tokens):
                continue
            window = " ".join(source_tokens[start:start + width])
            ratio = SequenceMatcher(None, target, window).ratio()
            if ratio > best:
                best = ratio
                if best >= threshold:
                    return True
    return best >= threshold


# ---------------------------------------------------------------------------
# Employer registry matching
# ---------------------------------------------------------------------------
def _org_base(name: Any) -> str:
    value = str(name or "").lower().replace("&", " and ")
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _acronyms(name: Any) -> set:
    return {
        match.group(1).strip().lower().replace(".", "")
        for match in re.finditer(r"\(([A-Z][A-Za-z&.\-]{1,14})\)", str(name or ""))
        if match.group(1).strip().lower() not in {"india", "global"}
    }


def find_employer(
    organization: Any, registry: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Resolve an organisation name to a registry entry, or None.

    Match order: exact normalised name, acronym equality, then containment
    (shortest length difference wins). No fuzzy random matching: unmatched
    employers are quarantined for review instead of guessed.
    """
    if not isinstance(registry, dict):
        return None
    employers = registry.get("employers") or []
    name = str(organization or "").strip()
    if not name:
        return None

    base = _org_base(name)
    acronyms = _acronyms(name)

    exact: List[Dict[str, Any]] = []
    contained: List[Tuple[int, Dict[str, Any]]] = []
    for employer in employers:
        other_name = employer.get("name") or ""
        other_base = _org_base(other_name)
        if not other_base:
            continue
        if base and base == other_base:
            exact.append(employer)
            continue
        if acronyms and acronyms & _acronyms(other_name):
            exact.append(employer)
            continue
        if base and other_base and min(len(base), len(other_base)) >= 8:
            if base in other_base or other_base in base:
                contained.append((abs(len(base) - len(other_base)), employer))

    if exact:
        return exact[0]
    if contained:
        contained.sort(key=lambda pair: pair[0])
        return contained[0][1]
    return None


def registry_identity(employer: Dict[str, Any]) -> Tuple[str, str]:
    """Return (org_website, org_domain) from a registry entry."""
    domains = [str(d).strip().lower() for d in (employer.get("domains") or []) if d]
    domain = domains[0] if domains else ""
    website = str(employer.get("website") or "").strip()
    if not website and domain:
        website = "https://" + domain
    return website, domain


# ---------------------------------------------------------------------------
# Page text
# ---------------------------------------------------------------------------
def fetch_page_text(
    url: str, session: Optional[requests.Session] = None, timeout: int = 25
) -> Dict[str, Any]:
    """Fetch a verified page and return visible text (capped, internal only)."""
    result = {"ok": False, "final_url": url, "status": 0, "text": "", "error": ""}
    if not str(url or "").lower().startswith("http"):
        result["error"] = "invalid url"
        return result
    owned = session is None
    http = session or requests.Session()
    http.verify = certifi.where()
    http.headers.update(HTTP_HEADERS)
    try:
        response = http.get(url, timeout=timeout, allow_redirects=True, stream=True)
        result["status"] = response.status_code
        result["final_url"] = response.url
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result
        content_type = (response.headers.get("content-type") or "").lower()
        chunks: List[bytes] = []
        total = 0
        for chunk in response.iter_content(65536):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total >= 2_000_000:
                break
        body = b"".join(chunks)
        if "pdf" in content_type:
            try:
                import io

                import pdfplumber

                with pdfplumber.open(io.BytesIO(body)) as pdf:
                    text = "\n".join(
                        (page.extract_text() or "") for page in pdf.pages[:5]
                    )
            except Exception as exc:  # pragma: no cover - optional dependency
                text = ""
                result["error"] = f"pdf: {type(exc).__name__}"
        else:
            soup = BeautifulSoup(body, "html.parser")
            for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
                tag.decompose()
            text = soup.get_text(" ", strip=True)
        result["text"] = re.sub(r"\s+", " ", text).strip()[:PAGE_TEXT_LIMIT]
        result["ok"] = bool(result["text"])
        return result
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
        return result
    finally:
        if owned:
            http.close()


# ---------------------------------------------------------------------------
# Field-in-source checks
# ---------------------------------------------------------------------------
def missing_fields_in_source(
    record: Dict[str, Any], page_text: str
) -> List[str]:
    """Return record fields whose values are not present on the page."""
    missing: List[str] = []

    title = record.get("clean_title")
    if not fuzzy_in_source(title, page_text):
        missing.append("clean_title")

    if not record.get("_deadline_is_default"):
        if not fuzzy_in_source(record.get("deadline_or_window"), page_text):
            missing.append("deadline_or_window")

    if not record.get("_compensation_is_default"):
        if not fuzzy_in_source(record.get("compensation_or_fellowship"), page_text):
            missing.append("compensation_or_fellowship")

    if not record.get("_qualification_is_default"):
        if not fuzzy_in_source(record.get("qualification_summary"), page_text):
            missing.append("qualification_summary")

    for skill in record.get("must_have_skills") or []:
        if not fuzzy_in_source(skill, page_text):
            missing.append("must_have_skills")
            break

    return missing


def page_says_closed(page_text: str) -> bool:
    lowered = _norm(page_text)
    return any(_norm(phrase) in lowered for phrase in CLOSED_PHRASES)


# ---------------------------------------------------------------------------
# Dedupe hash
# ---------------------------------------------------------------------------
def dedupe_hash(record: Dict[str, Any], employer_id: str = "") -> str:
    """Stable dedupe hash: employer_id + title + location + deadline.

    Tracking parameters are never part of the hash (no URL is used at all),
    so the same vacancy reached through different wrappers collapses.
    """
    employer = employer_id or record.get("employer_id") or record.get("organization")
    city = str(record.get("city") or "")
    state = str(record.get("state") or "")
    deadline = normalize_deadline(
        record.get("deadline_or_window") or record.get("valid_through") or ""
    )
    raw = "|".join(
        [
            _slug(employer),
            _slug(record.get("clean_title") or record.get("title") or ""),
            _slug((city + " " + state).strip()),
            deadline,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------
def quarantine_record(
    record: Dict[str, Any],
    reason_code: str,
    detail: str = "",
    result: Any = None,
    today: Optional[str] = None,
    source: str = "ingestion_gate",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Mark a record as quarantined in place (data is never removed)."""
    previous = record.get("status_before_quarantine")
    if not previous:
        previous = record.get("status") or "active"
    record["status"] = "quarantined"
    record["status_before_quarantine"] = previous
    quarantine: Dict[str, Any] = {
        "reason_code": reason_code or "VERIFICATION_ERROR",
        "final_url": "",
        "final_host": "",
        "http_status": 0,
        "entry_type": record.get("entry_type") or "unknown",
        "host_class": "",
        "error_detail": (detail or "")[:300],
        "verified_at": (
            getattr(result, "verified_at", "")
            or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        "audit": source,
    }
    if result is not None:
        quarantine.update(
            {
                "final_url": getattr(result, "final_url", "") or "",
                "final_host": getattr(result, "final_host", "") or "",
                "http_status": int(getattr(result, "http_status", 0) or 0),
                "entry_type": getattr(result, "entry_type", "") or quarantine["entry_type"],
                "host_class": getattr(result, "host_class", "") or "",
            }
        )
    if today:
        quarantine["run_date"] = today
    if extra:
        quarantine.update(extra)
    record["quarantine"] = quarantine
    return record


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------
def _is_wrapper_or_shortener(url: str) -> bool:
    return is_wrapper(url) or is_shortener(url)


def _source_portal(host: str, employer: Dict[str, Any]) -> str:
    host = (host or "").lower().removeprefix("www.")
    for ats in employer.get("ats_hosts") or []:
        ats = str(ats).lower()
        if host == ats or host.endswith("." + ats):
            return "Employer ATS"
    for domain in employer.get("domains") or []:
        domain = str(domain).lower()
        if host == domain or host.endswith("." + domain):
            return "Official Organisation Website"
    return "Official Organisation Website"


def gate_candidate(
    record: Dict[str, Any],
    registry: Dict[str, Any],
    today: str,
    resolve_news_url: Optional[Callable[[str], Optional[str]]] = None,
    verifier: Callable[..., Any] = verify_link,
    fetcher: Callable[..., Dict[str, Any]] = fetch_page_text,
) -> Tuple[Optional[Dict[str, Any]], str]:
    """Run the direct-link gate. Returns ``(record, reason)``.

    * published: ``status == "active"`` (or ``"archived"`` when dead)
    * ``None``: unresolvable wrapper/lead dropped before storage
    * UNKNOWN results are kept (fail-open); only dead links are archived.
    """
    apply_url = strip_tracking(str(record.get("apply_url") or "").strip())
    if not apply_url.lower().startswith("http"):
        return None, "apply URL missing or invalid"
    record["apply_url"] = apply_url

    # 1. News wrappers / shorteners: resolve first, drop only if unresolved.
    if _is_wrapper_or_shortener(apply_url):
        resolved = resolve_news_url(apply_url) if resolve_news_url else None
        if not resolved:
            return None, "wrapper/shortener could not be resolved"
        apply_url = strip_tracking(resolved)
        record["apply_url"] = apply_url

    # 2. Registry match is optional: it supplies naming/domains only.
    employer = find_employer(record.get("organization"), registry)

    # 3. Direct-link policy check (fail-open on UNKNOWN).
    result = verifier(
        apply_url,
        employer.get("id", "") if employer else "",
        record.get("clean_title", ""),
        record.get("organization", ""),
        employers_registry=registry,
    )
    reason = getattr(result, "reason_code", "") or UNKNOWN_KEEP
    if reason == UNRESOLVED_WRAPPER:
        return None, "wrapper/shortener could not be resolved"
    if reason == DEAD_LINK:
        record["status"] = "archived"
        record["date_archived"] = today
        record["apply_url"] = apply_url
        record.pop("quarantine", None)
        record.pop("status_before_quarantine", None)
        record["link_policy"] = {
            "policy_version": 2,
            "reason_code": DEAD_LINK,
            "checked_at": getattr(result, "verified_at", ""),
            "final_url": getattr(result, "final_url", "") or apply_url,
        }
        return record, DEAD_LINK

    # 4. If the page was actually fetched, confirm it is open and blank any
    #    field the model supplied that is not present in the source text.
    page_text = ""
    if getattr(result, "verification_level", "") == "page_verified":
        page = fetcher(getattr(result, "final_url", "") or apply_url)
        page_text = page.get("text") or ""
        if page_text and page_says_closed(page_text):
            record["status"] = "archived"
            record["date_archived"] = today
            record.pop("quarantine", None)
            record.pop("status_before_quarantine", None)
            record["link_policy"] = {
                "policy_version": 2,
                "reason_code": DEAD_LINK,
                "checked_at": getattr(result, "verified_at", ""),
                "final_url": getattr(result, "final_url", "") or apply_url,
            }
            return record, DEAD_LINK
        if page_text:
            missing = missing_fields_in_source(record, page_text)
            for field in missing:
                if field == "must_have_skills":
                    record["must_have_skills"] = []
                else:
                    record[field] = ""

    # 5. Publish. Identity comes from the registry when matched, never the LLM.
    website, domain = registry_identity(employer) if employer else ("", "")
    record["apply_url"] = strip_tracking(getattr(result, "final_url", "") or apply_url)
    if website:
        record["org_website"] = website
    if domain:
        record["org_domain"] = domain
    label = getattr(result, "platform", "") or ""
    record["source_portal"] = label or _source_portal(
        getattr(result, "final_host", ""), employer or {}
    )
    entry_type = getattr(result, "entry_type", "posting") or "posting"
    if reason == NOT_DIRECT_LINK:
        entry_type = entry_type if entry_type in {"careers_portal", "award_portal"} else "careers_portal"
    elif entry_type == "unknown":
        entry_type = "posting"
    record["entry_type"] = entry_type
    if employer:
        record["employer_id"] = employer.get("id", "")
    record["status"] = "active"
    record.pop("quarantine", None)
    record.pop("status_before_quarantine", None)
    record["verification"] = {
        "verified_at": getattr(result, "verified_at", ""),
        "final_url": record["apply_url"],
        "final_host": getattr(result, "final_host", ""),
        "http_status": int(getattr(result, "http_status", 0) or 0),
        "content_hash": getattr(result, "content_hash", ""),
        "evidence_snippet": (getattr(result, "evidence_snippet", "") or "")[:200],
        "entry_type": record["entry_type"],
        "host_class": getattr(result, "host_class", ""),
        "reason_code": reason,
        "platform": label,
        "verifier": "verify_link_v2",
    }
    record["link_policy"] = {
        "policy_version": 2,
        "reason_code": reason,
        "checked_at": getattr(result, "verified_at", ""),
    }
    for key in ("_qualification_is_default", "_compensation_is_default",
                "_deadline_is_default"):
        record.pop(key, None)
    return record, ""


def load_registry(path: str = "public/employers.json") -> Dict[str, Any]:
    return load_employers_registry(path)
