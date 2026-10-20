#!/usr/bin/env python3
"""Editable direct-link policy shared by the verifier, gate, audit and guard.

The policy lives in ``public/link_policy.json`` so platforms can be added or
removed without touching code. This module only implements the mechanics:

* any employer domain is allowed;
* an allow-listed platform is accepted when the URL points at one specific
  job/notice page (pattern validation, no scraping for bot-blocked platforms);
* news wrappers and shorteners must resolve to a real destination;
* tracking parameters are stripped.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY_PATH = ROOT / "public" / "link_policy.json"

_CACHE: Optional[Dict[str, Any]] = None


def load_policy(path: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Load the editable policy, cached per process."""
    global _CACHE
    if _CACHE is not None and not force and path is None:
        return _CACHE
    target = Path(path) if path else DEFAULT_POLICY_PATH
    with open(target, encoding="utf-8") as handle:
        policy = json.load(handle)
    policy.setdefault("platforms", [])
    policy.setdefault("tracking_params", [])
    policy.setdefault("always_remove_hosts", [])
    policy.setdefault("shortener_hosts", [])
    policy.setdefault("not_direct_paths", [])
    policy.setdefault("not_direct_query_markers", [])
    policy.setdefault("closed_phrases", [])
    if path is None:
        _CACHE = policy
    return policy


def normalize_host(host: str) -> str:
    value = (host or "").lower().strip().rstrip(".")
    return value[4:] if value.startswith("www.") else value


def host_matches(host: str, domains: List[str]) -> bool:
    host = normalize_host(host)
    for domain in domains:
        domain = normalize_host(str(domain or ""))
        if not domain:
            continue
        if host == domain or host.endswith("." + domain):
            return True
    return False


def platform_for(host: str, policy: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    policy = policy or load_policy()
    host = normalize_host(host)
    for platform in policy.get("platforms", []):
        if host_matches(host, [str(h) for h in platform.get("hosts", [])]):
            return platform
    return None


def platform_label(host: str, policy: Optional[Dict[str, Any]] = None) -> str:
    platform = platform_for(host, policy)
    return str(platform.get("name") or "") if platform else ""


def is_wrapper(url: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    policy = policy or load_policy()
    host = (urlparse(str(url or "")).hostname or "")
    return bool(host) and host_matches(host, policy.get("always_remove_hosts", []))


def is_shortener(url: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    policy = policy or load_policy()
    host = (urlparse(str(url or "")).hostname or "")
    return bool(host) and host_matches(host, policy.get("shortener_hosts", []))


def strip_tracking(url: str, policy: Optional[Dict[str, Any]] = None) -> str:
    """Remove tracking parameters while preserving real query values (jk=)."""
    policy = policy or load_policy()
    raw = str(url or "").strip()
    if not raw:
        return raw
    parsed = urlparse(raw)
    if not parsed.query:
        return raw
    blocked = {str(item).lower() for item in policy.get("tracking_params", [])}
    kept = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if key.lower() not in blocked
        and not key.lower().startswith(("utm_", "pk_", "mtm_"))
    ]
    return urlunparse(parsed._replace(query=urlencode(kept, doseq=True)))


def _path_and_query(url: str) -> Tuple[str, str]:
    parsed = urlparse(str(url or ""))
    path = (parsed.path or "/").rstrip("/") or "/"
    return path, (parsed.query or "")


def matches_platform_pattern(url: str, platform: Dict[str, Any]) -> bool:
    target = str(url or "")
    parsed = urlparse(target)
    path = parsed.path or "/"
    query = parsed.query or ""
    path_and_query = path + (("?" + query) if query else "")
    for pattern in platform.get("direct_patterns", []):
        try:
            if re.search(str(pattern), path, flags=re.I):
                return True
            if query and re.search(str(pattern), path_and_query, flags=re.I):
                return True
        except re.error:
            if str(pattern).lower() in target.lower():
                return True
    return False


def is_generic_url(url: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    """True for home pages, search/listing/category roots, careers roots."""
    policy = policy or load_policy()
    path, query = _path_and_query(url)
    if re.search(
        r"(?:job|vacancy|position|post|advt|notice|requisition|req)[_-]?id=\d+",
        query,
        re.I,
    ):
        return False
    lowered = path.lower().rstrip("/") or "/"
    not_direct = {str(item).lower().rstrip("/") or "/" for item in policy.get("not_direct_paths", [])}
    if lowered in not_direct:
        return True
    for marker in policy.get("not_direct_query_markers", []):
        marker = str(marker).lower()
        if marker and marker in ("?" + query).lower():
            return True
    # A one-segment path is a section root when it reads like one
    # ("/careers", "/forest-jobs"); a hyphenated job slug stays specific.
    segments = [segment for segment in lowered.split("/") if segment]
    if not segments:
        return True
    if len(segments) == 1:
        segment = segments[0]
        section_words = {
            "careers", "career", "jobs", "job", "vacancies", "vacancy",
            "recruitment", "recruitments", "openings", "positions",
            "opportunities", "work-with-us", "join-us", "search",
            "scholarships", "fellowships", "grants", "awards", "programmes",
            "programs",
        }
        if segment in section_words:
            return True
        if re.search(r"-(jobs?|careers?|vacancies|recruitment|openings|positions)$", segment):
            return True
    return False


def looks_like_specific_job(url: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    """Heuristic for employer pages: specific path, not a section root."""
    if is_generic_url(url, policy):
        return False
    path, query = _path_and_query(url)
    if re.search(r"(?:^|[-_/])\d{3,}(?:$|[-_/])", path):
        return True
    segments = [segment for segment in path.lower().split("/") if segment]
    if len(segments) >= 2 and len(segments[-1]) >= 8:
        return True
    if query and re.search(r"(job|vacancy|position|post|id|advt|notice)[_-]?id?=", query, re.I):
        return True
    return bool(re.search(r"(job|vacancy|position|recruit|notice|advertisement|apply)", path, re.I))


def closed_phrase(text: str, policy: Optional[Dict[str, Any]] = None) -> bool:
    policy = policy or load_policy()
    lowered = re.sub(r"\s+", " ", str(text or "").lower())
    return any(str(phrase).lower() in lowered for phrase in policy.get("closed_phrases", []))
