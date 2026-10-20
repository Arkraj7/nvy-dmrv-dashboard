#!/usr/bin/env python3
"""Direct-link verification for Urban Forest Park.

Policy (v2, 20 Oct 2026) - see ``public/link_policy.json``:

* any employer domain is allowed;
* job platforms (LinkedIn, Indeed, Naukri, FreeJobAlert, Foundit, Shine,
  TimesJobs, Internshala, Apna and configured peers) are allowed when the URL
  points at one specific job/notice page;
* home pages, search/listing/category pages and careers roots are NOT_DIRECT
  and are placed in "Careers portals" instead of individual jobs;
* news wrappers and shorteners are resolved, or dropped when unresolvable;
* only dead links (404/410, confirmed soft-404, closed/expired text) are
  removed. UNKNOWN (bot block, timeout, TLS error) is never treated as dead.

SSRF protections and certificate verification stay enabled. ``verify=False``
is never used.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import certifi
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from link_policy import (
    closed_phrase,
    host_matches,
    is_generic_url,
    is_shortener,
    is_wrapper,
    load_policy,
    matches_platform_pattern,
    normalize_host,
    platform_for,
    platform_label,
    strip_tracking,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_REDIRECTS = 5
MAX_HTML_SIZE = 2 * 1024 * 1024
MAX_PDF_SIZE = 10 * 1024 * 1024
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20
TOTAL_TIMEOUT = 30
USER_AGENT = "UrbanForestPark-Verifier/2.0 (+https://www.urbanforestpark.com/contact)"

# Kept for backwards imports; policy v2 no longer blocks job boards.
BLOCKLISTED_HOSTS: Set[str] = set()

ATS_PATTERNS = (
    "myworkdayjobs.com", "boards.greenhouse.io", "jobs.lever.co",
    "jobs.smartrecruiters.com", "recruitee.com", "workable.com",
    "bamboohr.com", "icims.com", "taleo.net", "successfactors.com",
    "oraclecloud.com", "sapsf.com", "jobvite.com", "lever.co",
    "greenhouse.io", "smartrecruiters.com", "careers.ey.com",
)

GOV_ACADEMIC_PATTERNS = (
    ".gov.in", ".nic.in", ".ac.in", ".edu.in", ".res.in", ".org.in",
    ".ernet.in", ".gov", ".mil", ".edu",
)

# Reason codes (policy v2)
OK = "OK"
DEAD_LINK = "DEAD_LINK"
NOT_DIRECT_LINK = "NOT_DIRECT_LINK"
UNRESOLVED_WRAPPER = "UNRESOLVED_WRAPPER"
UNKNOWN_KEEP = "UNKNOWN_KEEP"


@dataclass
class VerificationResult:
    ok: bool
    final_url: str
    final_host: str
    http_status: int
    redirect_chain: List[str]
    verification_level: str   # page_verified | url_verified | domain_verified | unverified
    host_class: str           # platform | employer_primary | employer_ats | government_notice | unknown_host
    reason_code: str          # OK | DEAD_LINK | NOT_DIRECT_LINK | UNRESOLVED_WRAPPER | UNKNOWN_KEEP
    evidence_snippet: str
    content_hash: str
    verified_at: str
    entry_type: str           # posting | careers_portal | award_portal | unknown
    error_detail: str
    warnings: List[str] = field(default_factory=list)
    platform: str = ""
    direct: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "final_url": self.final_url,
            "final_host": self.final_host,
            "http_status": self.http_status,
            "redirect_chain": self.redirect_chain,
            "verification_level": self.verification_level,
            "host_class": self.host_class,
            "reason_code": self.reason_code,
            "evidence_snippet": self.evidence_snippet,
            "content_hash": self.content_hash,
            "verified_at": self.verified_at,
            "entry_type": self.entry_type,
            "error_detail": self.error_detail,
            "warnings": self.warnings,
            "platform": self.platform,
            "direct": self.direct,
        }


class LinkVerifier:
    """Classifies links against the editable direct-link policy."""

    def __init__(self, employers_registry: Optional[Dict[str, Any]] = None,
                 use_playwright: bool = False):
        self.employers = employers_registry or {"employers": []}
        self.use_playwright = use_playwright
        self.policy = load_policy()
        self._session = self._create_session()

    # ------------------------------------------------------------------
    # Session / SSRF
    # ------------------------------------------------------------------
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=1,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("HEAD", "GET", "OPTIONS"),
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": USER_AGENT})
        session.verify = certifi.where()  # certificate verification stays on
        return session

    def _is_private_ip(self, host: str):
        try:
            import socket
            ips = set()
            try:
                for res in socket.getaddrinfo(host, None, socket.AF_INET):
                    ips.add(res[4][0])
            except Exception:
                pass
            try:
                for res in socket.getaddrinfo(host, None, socket.AF_INET6):
                    ips.add(res[4][0])
            except Exception:
                pass
            if not ips:
                return False
            for ip_str in ips:
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    if ip_str in ("0.0.0.0", "::") or not ip_obj.is_global:
                        return "dns_filtered"
                except Exception:
                    continue
            for ip_str in ips:
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local):
                        return False
                except Exception:
                    continue
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Registry helpers (naming/domains only - never a publish gate)
    # ------------------------------------------------------------------
    def _find_employer(self, employer_id: str) -> Optional[Dict]:
        for emp in self.employers.get("employers", []):
            if emp.get("id") == employer_id:
                return emp
        return None

    def _find_employer_by_domain(self, host: str) -> Optional[Dict]:
        host = normalize_host(host)
        for emp in self.employers.get("employers", []):
            for domain in (emp.get("domains") or []) + (emp.get("ats_hosts") or []):
                if host_matches(host, [str(domain)]):
                    return emp
        return None

    def _is_ats_host(self, host: str) -> bool:
        host = normalize_host(host)
        return any(host == p or host.endswith("." + p) for p in ATS_PATTERNS)

    def _is_gov_academic(self, host: str) -> bool:
        host = normalize_host(host)
        return any(host.endswith(p) for p in GOV_ACADEMIC_PATTERNS)

    def _determine_host_class(self, host: str, employer: Optional[Dict]) -> str:
        if platform_for(host, self.policy):
            return "platform"
        if employer:
            for domain in (employer.get("domains") or []) + (employer.get("ats_hosts") or []):
                if host_matches(host, [str(domain)]):
                    return "employer_ats" if self._is_ats_host(host) else "employer_primary"
        if self._is_ats_host(host):
            return "employer_ats"
        if self._is_gov_academic(host):
            return "government_notice"
        return "unknown_host"

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------
    def _strip_tracking_params(self, url: str) -> str:
        return strip_tracking(url, self.policy)

    def _is_blocklisted(self, host: str) -> bool:
        # Compatibility shim: policy v2 has no host blocklist. Only wrappers
        # and shorteners are removed, and they are resolved first.
        return is_wrapper("https://" + (host or ""), self.policy) or is_shortener(
            "https://" + (host or ""), self.policy
        )

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------
    def _fetch_with_redirects(self, url: str) -> tuple:
        redirect_chain = [url]
        current_url = url
        for _hop in range(MAX_REDIRECTS):
            try:
                parsed = urlparse(current_url)
                hostname = parsed.hostname or ""
                if hostname and not hostname.startswith("/"):
                    ssrf_result = self._is_private_ip(hostname)
                    if ssrf_result is True:
                        return None, redirect_chain, "ssrf_guard|PrivateIPError|Blocked private IP"
                    if ssrf_result == "dns_filtered":
                        return None, redirect_chain, "dns|DNSFiltered|DNS filtered locally"
                resp = self._session.get(
                    current_url,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    allow_redirects=False,
                    stream=True,
                    headers={"Accept": "text/html,application/pdf,*/*"},
                )
                redirect_chain.append(resp.url)
                content_length = resp.headers.get("Content-Length")
                max_size = MAX_PDF_SIZE if "pdf" in resp.headers.get("Content-Type", "") else MAX_HTML_SIZE
                if content_length and int(content_length) > max_size:
                    resp.close()
                    return resp, redirect_chain, ""
                content = b""
                for chunk in resp.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > max_size:
                        break
                resp.close()
                resp._content_for_analysis = content
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("Location")
                    if location:
                        current_url = requests.compat.urljoin(current_url, location)
                        continue
                return resp, redirect_chain, ""
            except requests.exceptions.SSLError as exc:
                return None, redirect_chain, f"tls|SSLError|{exc}"
            except requests.exceptions.ConnectTimeout as exc:
                return None, redirect_chain, f"connect|ConnectTimeout|{exc}"
            except requests.exceptions.ReadTimeout as exc:
                return None, redirect_chain, f"read|ReadTimeout|{exc}"
            except requests.exceptions.Timeout as exc:
                return None, redirect_chain, f"timeout|Timeout|{exc}"
            except requests.exceptions.ConnectionError as exc:
                return None, redirect_chain, f"connect|ConnectionError|{exc}"
            except requests.exceptions.TooManyRedirects as exc:
                return None, redirect_chain, f"redirect|TooManyRedirects|{exc}"
            except requests.exceptions.RequestException as exc:
                return None, redirect_chain, f"request|{type(exc).__name__}|{exc}"
            except Exception as exc:
                return None, redirect_chain, f"unknown|{type(exc).__name__}|{exc}"
        return None, redirect_chain, "redirect|RedirectLoop|Max redirects exceeded"

    def _resolve_destination(self, url: str) -> Optional[str]:
        """Resolve a wrapper/shortener server-side, or return None."""
        if is_wrapper(url, self.policy):
            match = re.search(r"/articles/([A-Za-z0-9_\-]+)", url)
            try:
                if match:
                    from fetch_and_humanize import _resolve_google_news_via_batchexecute
                    resolved = _resolve_google_news_via_batchexecute(match.group(1), timeout=12)
                    if resolved:
                        return resolved
                from fetch_and_humanize import resolve_google_news_link
                resolved = resolve_google_news_link(url)
                if resolved and not is_wrapper(resolved, self.policy):
                    return resolved
            except Exception:
                return None
            return None
        response, chain, error = self._fetch_with_redirects(url)
        if error or response is None:
            return None
        final = chain[-1] if chain else url
        if response.status_code in (404, 410):
            return None
        return final

    def _extract_text_content(self, response, content_type: str) -> str:
        if not response or not hasattr(response, "_content_for_analysis"):
            return ""
        content = response._content_for_analysis
        if not content:
            return ""
        if "pdf" in content_type:
            try:
                import io
                import pdfplumber
                text = ""
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages[:5]:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text[:8000]
            except Exception:
                return ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)[:8000]
        except Exception:
            return content.decode("utf-8", errors="ignore")[:8000]

    def _compute_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()[:32]

    def _detect_entry_type(self, text: str, final_url: str, final_host: str) -> str:
        text_lower = (text or "").lower()
        url_lower = (final_url or "").lower()
        award_url_patterns = ["/award", "/prize", "/scholarship", "/fellowship", "/grant", "/competition", "/challenge", "/call-for"]
        award_phrases = ["scholarship", "fellowship", "prize", "award", "grant", "application deadline", "eligibility criteria", "selection criteria"]
        generic_url = ["/careers", "/jobs", "/vacancies", "/recruitment", "/openings", "/positions", "/opportunities", "/work-with-us"]
        generic_phrases = ["view all jobs", "view all positions", "all vacancies", "search jobs", "browse jobs", "current openings", "join our team", "career opportunities", "work with us", "explore careers"]
        specific_phrases = ["job description", "position summary", "key responsibilities", "qualifications", "requirements", "essential duties", "apply now", "apply for this position", "reference number", "requisition", "job id", "vacancy number"]

        generic_score = sum(1 for p in generic_url if p in url_lower and not re.search(rf"{re.escape(p)}/[a-z0-9-]+", url_lower))
        generic_score += sum(1 for p in generic_phrases if p in text_lower)
        award_score = sum(2 for p in award_url_patterns if p in url_lower)
        award_score += sum(1 for p in award_phrases if p in text_lower)
        specific_score = sum(2 for p in specific_phrases if p in text_lower)

        if award_score > max(generic_score, specific_score):
            return "award_portal"
        if generic_score > specific_score:
            return "careers_portal"
        if specific_score:
            return "posting"
        if is_generic_url(final_url, self.policy):
            return "careers_portal"
        return "posting" if not text else "posting"

    def _is_soft_404(self, text: str) -> bool:
        return closed_phrase(text, self.policy) or any(
            phrase in (text or "").lower()
            for phrase in ("page not found", "job not found", "error 404", "page doesn't exist")
        )

    def _result(self, **kwargs) -> VerificationResult:
        base = {
            "ok": False,
            "final_url": "",
            "final_host": "",
            "http_status": 0,
            "redirect_chain": [],
            "verification_level": "unverified",
            "host_class": "",
            "reason_code": OK,
            "evidence_snippet": "",
            "content_hash": "",
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "entry_type": "unknown",
            "error_detail": "",
            "warnings": [],
            "platform": "",
            "direct": False,
        }
        base.update(kwargs)
        return VerificationResult(**base)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def verify(self, apply_url: str, employer_id: str = "", job_title: str = "",
               org_name: str = "") -> VerificationResult:
        now = datetime.now(timezone.utc).isoformat()
        raw_url = str(apply_url or "").strip()
        if not raw_url.lower().startswith(("http://", "https://")):
            return self._result(
                final_url=raw_url, reason_code=DEAD_LINK,
                error_detail="invalid|InvalidURL|URL is not http(s)",
                warnings=["Invalid URL"],
            )
        clean_url = self._strip_tracking_params(raw_url)
        redirect_chain = [clean_url]
        employer = self._find_employer(employer_id) or self._find_employer_by_domain(
            urlparse(clean_url).hostname or ""
        )

        # 1. Resolve news wrappers and shorteners first.
        if is_wrapper(clean_url, self.policy) or is_shortener(clean_url, self.policy):
            resolved = self._resolve_destination(clean_url)
            if not resolved:
                return self._result(
                    final_url=clean_url,
                    final_host=urlparse(clean_url).hostname or "",
                    redirect_chain=redirect_chain,
                    reason_code=UNRESOLVED_WRAPPER,
                    error_detail="wrapper|Unresolved|Could not resolve wrapper or shortener",
                    warnings=["Unresolved wrapper/shortener"],
                )
            redirect_chain.append(resolved)
            clean_url = self._strip_tracking_params(resolved)

        host = urlparse(clean_url).hostname or ""
        platform = platform_for(host, self.policy)
        host_class = self._determine_host_class(host, employer)

        # 2. Platform URL-pattern validation. Never scrape bot-blocked sites.
        if platform:
            label = str(platform.get("name") or "")
            if not matches_platform_pattern(clean_url, platform):
                return self._result(
                    ok=True,
                    final_url=clean_url,
                    final_host=host,
                    http_status=0,
                    redirect_chain=redirect_chain,
                    verification_level="url_verified",
                    host_class="platform",
                    reason_code=NOT_DIRECT_LINK,
                    entry_type="careers_portal",
                    platform=label,
                    direct=False,
                    error_detail="pattern|NotDirect|URL is a search, listing or root page",
                    warnings=["Not a specific job page - placed in Careers portals"],
                )
            if platform.get("bot_blocked"):
                return self._result(
                    ok=True,
                    final_url=clean_url,
                    final_host=host,
                    http_status=0,
                    redirect_chain=redirect_chain,
                    verification_level="url_verified",
                    host_class="platform",
                    reason_code=UNKNOWN_KEEP,
                    entry_type="posting",
                    platform=label,
                    direct=True,
                    error_detail="platform|BotBlocked|Pattern-valid; content not fetched",
                    warnings=[f"{label} blocks automated content checks - kept"],
                )
            # Non-bot-blocked platforms get a light status/closed check.
            response, chain, error = self._fetch_with_redirects(clean_url)
            final_url = chain[-1] if chain else clean_url
            final_host = urlparse(final_url).hostname or host
            if error or response is None:
                return self._result(
                    ok=True, final_url=final_url, final_host=final_host,
                    redirect_chain=chain, verification_level="url_verified",
                    host_class="platform", reason_code=UNKNOWN_KEEP,
                    entry_type="posting", platform=label, direct=True,
                    error_detail=error, warnings=["Status check inconclusive - kept"],
                )
            status = response.status_code
            text = self._extract_text_content(response, response.headers.get("Content-Type", ""))
            if status in (404, 410) or self._is_soft_404(text):
                return self._result(
                    final_url=final_url, final_host=final_host,
                    http_status=status, redirect_chain=chain,
                    verification_level="unverified", host_class="platform",
                    reason_code=DEAD_LINK, entry_type="posting", platform=label,
                    content_hash=self._compute_hash(getattr(response, "_content_for_analysis", b"")),
                    evidence_snippet=text[:200],
                    error_detail=f"status|HTTP{status}|Dead or closed",
                    warnings=["Dead link"],
                )
            if status in (401, 403, 429, 999) or status >= 400:
                return self._result(
                    ok=True, final_url=final_url, final_host=final_host,
                    http_status=status, redirect_chain=chain,
                    verification_level="url_verified", host_class="platform",
                    reason_code=UNKNOWN_KEEP, entry_type="posting",
                    platform=label, direct=True,
                    error_detail=f"status|HTTP{status}|Bot block or server refusal",
                    warnings=["Inconclusive status - kept"],
                )
            return self._result(
                ok=True, final_url=final_url, final_host=final_host,
                http_status=status, redirect_chain=chain,
                verification_level="page_verified", host_class="platform",
                reason_code=OK, entry_type="posting", platform=label, direct=True,
                content_hash=self._compute_hash(getattr(response, "_content_for_analysis", b"")),
                evidence_snippet=text[:200],
            )

        # 3. Employer / unknown host: URL-pattern check first, then fetch.
        if is_generic_url(clean_url, self.policy):
            return self._result(
                ok=True, final_url=clean_url, final_host=host,
                http_status=0, redirect_chain=redirect_chain,
                verification_level="url_verified", host_class=host_class,
                reason_code=NOT_DIRECT_LINK, entry_type="careers_portal",
                direct=False,
                error_detail="pattern|NotDirect|Home, search or section page",
                warnings=["Not a specific job page - placed in Careers portals"],
            )

        response, chain, error = self._fetch_with_redirects(clean_url)
        final_url = chain[-1] if chain else clean_url
        final_host = urlparse(final_url).hostname or host
        host_class = self._determine_host_class(final_host, employer)

        if error or response is None:
            # UNKNOWN is not dead: keep visible.
            return self._result(
                ok=True, final_url=final_url, final_host=final_host,
                redirect_chain=chain, verification_level="domain_verified",
                host_class=host_class, reason_code=UNKNOWN_KEEP,
                entry_type="posting", direct=True,
                error_detail=error,
                warnings=["Fetch inconclusive (timeout/TLS/DNS/bot block) - kept"],
            )

        status = response.status_code
        content = getattr(response, "_content_for_analysis", b"")
        content_hash = self._compute_hash(content) if content else ""
        text = self._extract_text_content(response, response.headers.get("Content-Type", ""))

        if status in (404, 410):
            return self._result(
                final_url=final_url, final_host=final_host, http_status=status,
                redirect_chain=chain, host_class=host_class, reason_code=DEAD_LINK,
                entry_type="posting", content_hash=content_hash,
                error_detail=f"status|HTTP{status}|Not found", warnings=["Dead link"],
            )
        if status in (401, 403, 429, 999) or status >= 500:
            return self._result(
                ok=True, final_url=final_url, final_host=final_host,
                http_status=status, redirect_chain=chain,
                verification_level="domain_verified", host_class=host_class,
                reason_code=UNKNOWN_KEEP, entry_type="posting", direct=True,
                error_detail=f"status|HTTP{status}|Bot block or server error",
                warnings=["Inconclusive status - kept"],
            )
        if status >= 400:
            return self._result(
                ok=True, final_url=final_url, final_host=final_host,
                http_status=status, redirect_chain=chain,
                verification_level="domain_verified", host_class=host_class,
                reason_code=UNKNOWN_KEEP, entry_type="posting", direct=True,
                error_detail=f"status|HTTP{status}", warnings=["Inconclusive status - kept"],
            )

        if self._is_soft_404(text):
            return self._result(
                final_url=final_url, final_host=final_host, http_status=status,
                redirect_chain=chain, host_class=host_class, reason_code=DEAD_LINK,
                entry_type="posting", content_hash=content_hash,
                evidence_snippet=text[:200],
                error_detail="content|Closed|Page says the job is closed or expired",
                warnings=["Dead or closed page"],
            )

        entry_type = self._detect_entry_type(text, clean_url, final_host)
        if is_generic_url(clean_url, self.policy) or is_generic_url(final_url, self.policy):
            return self._result(
                ok=True, final_url=final_url, final_host=final_host,
                http_status=status, redirect_chain=chain,
                verification_level="page_verified", host_class=host_class,
                reason_code=NOT_DIRECT_LINK,
                entry_type="award_portal" if entry_type == "award_portal" else "careers_portal",
                content_hash=content_hash, direct=False,
                evidence_snippet=text[:200],
                error_detail="pattern|NotDirect|Home, search or section page",
                warnings=["Not a specific job page - placed in Careers portals"],
            )

        return self._result(
            ok=True, final_url=final_url, final_host=final_host,
            http_status=status, redirect_chain=chain,
            verification_level="page_verified", host_class=host_class,
            reason_code=OK, entry_type=entry_type if entry_type != "unknown" else "posting",
            content_hash=content_hash, direct=True,
            evidence_snippet=text[:200],
        )


def load_employers_registry(path: str = "public/employers.json") -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def verify_link(apply_url: str, employer_id: str = "", job_title: str = "",
                org_name: str = "", employers_registry: Optional[Dict] = None,
                use_playwright: bool = False) -> VerificationResult:
    if employers_registry is None:
        try:
            employers_registry = load_employers_registry()
        except Exception:
            employers_registry = {"employers": []}
    return LinkVerifier(employers_registry, use_playwright).verify(
        apply_url, employer_id, job_title, org_name
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python verify_link.py <apply_url> [employer_id] [job_title] [org_name]")
        sys.exit(1)
    result = verify_link(
        sys.argv[1],
        sys.argv[2] if len(sys.argv) > 2 else "",
        sys.argv[3] if len(sys.argv) > 3 else "",
        sys.argv[4] if len(sys.argv) > 4 else "",
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
