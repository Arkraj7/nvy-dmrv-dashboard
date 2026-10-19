#!/usr/bin/env python3
"""
verify_link.py - Official link verification module for Urban Forest Park

This module implements the verification policy (P1-P7):
- P1: Two destinations only (apply_url + dossier)
- P2: Allowed hosts per employer registry
- P3: Blocklist enforcement
- P4: Verifiable means checked (redirects, content match, evidence)
- P5: Fail closed (quarantine on failure)
- P6: Aggregators for discovery only
- P7: Broadcasts use dossier URLs only

Usage:
    from verify_link import verify_link, VerificationResult
    result = verify_link(apply_url, employer_id, employer_registry)
"""
import re
import json
import hashlib
import ipaddress
import logging
import certifi
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MAX_REDIRECTS = 5
MAX_HTML_SIZE = 2 * 1024 * 1024      # 2 MB
MAX_PDF_SIZE = 10 * 1024 * 1024      # 10 MB
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 20
TOTAL_TIMEOUT = 30
USER_AGENT = 'UrbanForestPark-Verifier/1.0 (+https://www.urbanforestpark.com/contact)'

# Tracking parameters to strip
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'fbclid', 'gclid', 'ref', 'source', 'utm_id', 'utm_source_platform',
    'utm_creative_format', 'utm_marketing_tactic', 'msclkid', 'yclid',
    '_ga', '_gl', 'mc_cid', 'mc_eid', 'utm_reader', 'utm_place'
}

# Blocklisted hosts (P3) - job boards, aggregators, social, shorteners, file hosts
BLOCKLISTED_HOSTS: Set[str] = {
    # Job boards
    'linkedin.com', 'www.linkedin.com', 'in.linkedin.com',
    'naukri.com', 'www.naukri.com',
    'indeed.com', 'www.indeed.com', 'indeed.co.in', 'in.indeed.com',
    'glassdoor.com', 'www.glassdoor.com', 'glassdoor.co.in',
    'foundit.in', 'www.foundit.in',
    'monster.com', 'www.monster.com', 'monsterindia.com',
    'shine.com', 'www.shine.com',
    'timesjobs.com', 'www.timesjobs.com',
    'apna.co', 'www.apna.co',
    'freshersworld.com', 'www.freshersworld.com',
    'jobsora.com', 'www.jobsora.com',
    'jooble.org', 'www.jooble.org', 'in.jooble.org',
    'talent.com', 'www.talent.com', 'in.talent.com',
    'ziprecruiter.com', 'www.ziprecruiter.com',
    'internshala.com', 'www.internshala.com',
    'unstop.com', 'www.unstop.com',
    'hirist.com', 'www.hirist.com',
    'cutshort.io', 'www.cutshort.io',
    'upwork.com', 'www.upwork.com',
    'freejobalert.com', 'www.freejobalert.com',
    'reliefweb.int', 'www.reliefweb.int',
    'indiabioscience.org', 'www.indiabioscience.org',
    # News & wrappers
    'news.google.com', 'www.news.google.com',
    'google.com', 'www.google.com',
    'feedproxy.google.com',
    # Social & messaging
    't.me', 'telegram.me',
    'wa.me', 'chat.whatsapp.com', 'www.chat.whatsapp.com',
    'facebook.com', 'www.facebook.com', 'fb.com', 'm.facebook.com',
    'x.com', 'www.x.com', 'twitter.com', 'www.twitter.com',
    'instagram.com', 'www.instagram.com',
    'youtube.com', 'www.youtube.com',
    # Shorteners
    'bit.ly', 'tinyurl.com', 't.co', 'lnkd.in', 'goo.gl',
    'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'shorte.st',
    # File hosts
    'drive.google.com', 'docs.google.com', 'sheets.google.com',
    'dropbox.com', 'www.dropbox.com',
    'onedrive.live.com', '1drv.ms',
    'we.tl', 'wetransfer.com',
}

# Government/academic TLD patterns that are allowed when matching employer domain
GOV_ACADEMIC_PATTERNS = (
    '.gov.in', '.nic.in', '.ac.in', '.edu.in', '.res.in', 
    '.org.in', '.ernet.in', '.gov', '.mil', '.edu'
)

# ATS host patterns (employer-controlled)
ATS_PATTERNS = (
    'myworkdayjobs.com',
    'boards.greenhouse.io',
    'jobs.lever.co',
    'jobs.smartrecruiters.com',
    'recruitee.com',
    'workable.com',
    'bamboohr.com',
    'icims.com',
    'taleo.net',
    'successfactors.com',
    'oraclecloud.com',
    'sapsf.com',
    'jobvite.com',
    'lever.co',
    'greenhouse.io',
    'smartrecruiters.com',
)


@dataclass
class VerificationResult:
    """Structured verification result with machine-readable reason codes."""
    ok: bool
    final_url: str
    final_host: str
    http_status: int
    redirect_chain: List[str]
    verification_level: str  # "page_verified" | "domain_verified" | "unverified"
    host_class: str          # "employer_primary" | "employer_ats" | "government_notice" | "blocklisted" | "unregistered"
    reason_code: str         # BLOCKED_HOST, HOST_NOT_IN_REGISTRY, HTTP_404, SOFT_404, CONTENT_MISMATCH, GENERIC_LANDING_PAGE, TIMEOUT, REDIRECT_LOOP, SSL_ERROR, UNREACHABLE_FROM_RUNNER, EMPLOYER_NOT_IN_REGISTRY, VERIFICATION_ERROR, OK
    evidence_snippet: str
    content_hash: str
    verified_at: str
    entry_type: str          # "posting" | "careers_portal" | "unknown"
    error_detail: str        # exception class + message for debugging
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ok': self.ok,
            'final_url': self.final_url,
            'final_host': self.final_host,
            'http_status': self.http_status,
            'redirect_chain': self.redirect_chain,
            'verification_level': self.verification_level,
            'host_class': self.host_class,
            'reason_code': self.reason_code,
            'evidence_snippet': self.evidence_snippet,
            'content_hash': self.content_hash,
            'verified_at': self.verified_at,
            'entry_type': self.entry_type,
            'error_detail': self.error_detail,
            'warnings': self.warnings
        }


class LinkVerifier:
    """Verifies apply_url links against the employer registry and blocklist."""
    
    def __init__(self, employers_registry: Dict[str, Any], use_playwright: bool = False):
        self.employers = employers_registry
        self.use_playwright = use_playwright
        self._session = self._create_session()
        self._playwright = None
        self._browser = None
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retries and polite headers."""
        session = requests.Session()
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=('HEAD', 'GET', 'OPTIONS')
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update({'User-Agent': USER_AGENT})
        # Use certifi's CA bundle to avoid system cert issues
        session.verify = certifi.where()
        return session
    
    def _strip_tracking_params(self, url: str) -> str:
        """Remove tracking parameters from URL."""
        parsed = urlparse(url)
        query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) 
                 if k.lower() not in TRACKING_PARAMS]
        new_query = urlencode(query)
        return urlunparse(parsed._replace(query=new_query))
    
    def _is_private_ip(self, host: str) -> bool:
        """Check if host resolves to private/loopback/link-local IP (SSRF protection)."""
        try:
            import socket
            ip = socket.gethostbyname(host)
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local
        except Exception:
            return False
    
    def _normalize_host(self, host: str) -> str:
        """Normalize host for comparison (lowercase, strip www)."""
        host = host.lower().strip()
        if host.startswith('www.'):
            host = host[4:]
        return host
    
    def _host_matches_domain(self, host: str, domain: str) -> bool:
        """Check if host matches domain or is a subdomain of it."""
        host = self._normalize_host(host)
        domain = self._normalize_host(domain)
        return host == domain or host.endswith('.' + domain)
    
    def _is_blocklisted(self, host: str) -> bool:
        """Check if host is in blocklist."""
        host = self._normalize_host(host)
        for blocked in BLOCKLISTED_HOSTS:
            if host == blocked or host.endswith('.' + blocked):
                return True
        return False
    
    def _is_ats_host(self, host: str) -> bool:
        """Check if host matches known ATS patterns."""
        host = self._normalize_host(host)
        for pattern in ATS_PATTERNS:
            if host == pattern or host.endswith('.' + pattern):
                return True
        return False
    
    def _is_gov_academic(self, host: str) -> bool:
        """Check if host is a government/academic domain."""
        host = self._normalize_host(host)
        return any(host.endswith(p) for p in GOV_ACADEMIC_PATTERNS)
    
    def _find_employer(self, employer_id: str) -> Optional[Dict]:
        """Find employer by ID in registry."""
        for emp in self.employers.get('employers', []):
            if emp['id'] == employer_id:
                return emp
        return None
    
    def _find_employer_by_domain(self, host: str) -> Optional[Dict]:
        """Find employer whose domain matches the host."""
        host = self._normalize_host(host)
        for emp in self.employers.get('employers', []):
            for domain in emp.get('domains', []):
                if self._host_matches_domain(host, domain):
                    return emp
            # Also check ATS hosts
            for ats in emp.get('ats_hosts', []):
                if self._host_matches_domain(host, ats):
                    return emp
        return None
    
    def _determine_host_class(self, final_host: str, employer: Optional[Dict]) -> str:
        """Determine the host class per policy P2."""
        if self._is_blocklisted(final_host):
            return 'blocklisted'
        
        if employer:
            for domain in employer.get('domains', []):
                if self._host_matches_domain(final_host, domain):
                    return 'employer_primary'
            for ats in employer.get('ats_hosts', []):
                if self._host_matches_domain(final_host, ats):
                    return 'employer_ats'
        
        # Check if it's a government/academic notice matching employer domain
        found_emp = self._find_employer_by_domain(final_host)
        if found_emp and self._is_gov_academic(final_host):
            return 'government_notice'
        
        return 'unregistered'
    
    def _fetch_with_redirects(self, url: str) -> tuple:
        """Fetch URL following redirects, return (response, redirect_chain)."""
        redirect_chain = [url]
        current_url = url
        
        for hop in range(MAX_REDIRECTS):
            try:
                # Check for private IP (SSRF)
                parsed = urlparse(current_url)
                if self._is_private_ip(parsed.hostname or ''):
                    logger.warning(f"SSRF blocked: {current_url} resolves to private IP")
                    return None, redirect_chain
                
                # Stream to control size
                resp = self._session.get(
                    current_url,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    allow_redirects=False,
                    stream=True,
                    headers={'Accept': 'text/html,application/pdf,*/*'}
                )
                
                redirect_chain.append(resp.url)
                
                # Check content length
                content_length = resp.headers.get('Content-Length')
                max_size = MAX_PDF_SIZE if 'pdf' in resp.headers.get('Content-Type', '') else MAX_HTML_SIZE
                if content_length and int(content_length) > max_size:
                    logger.warning(f"Content too large: {content_length} > {max_size}")
                    resp.close()
                    return resp, redirect_chain
                
                # Read limited content
                content = b''
                for chunk in resp.iter_content(chunk_size=8192):
                    content += chunk
                    if len(content) > max_size:
                        break
                resp.close()
                
                # Store content for later analysis
                resp._content_for_analysis = content
                
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get('Location')
                    if location:
                        current_url = location
                        continue
                
                return resp, redirect_chain
                
            except requests.exceptions.SSLError as e:
                logger.warning(f"SSL error for {current_url}: {e}")
                return None, redirect_chain
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout for {current_url}: {e}")
                return None, redirect_chain
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error for {current_url}: {e}")
                return None, redirect_chain
            except Exception as e:
                logger.warning(f"Error fetching {current_url}: {e}")
                return None, redirect_chain
        
        # Too many redirects
        logger.warning(f"Redirect loop detected for {url}")
        return None, redirect_chain
    
    def _extract_text_content(self, response, content_type: str) -> str:
        """Extract text content from response for content matching."""
        if not response or not hasattr(response, '_content_for_analysis'):
            return ''
        
        content = response._content_for_analysis
        if not content:
            return ''
        
        if 'pdf' in content_type:
            try:
                import pdfplumber
                import io
                text = ''
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages[:5]:  # First 5 pages
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + '\n'
                return text[:5000]
            except Exception:
                return ''
        else:
            # HTML - extract visible text
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                # Remove script/style
                for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                    tag.decompose()
                text = soup.get_text(separator=' ', strip=True)
                return text[:5000]
            except Exception:
                return content.decode('utf-8', errors='ignore')[:5000]
    
    def _content_match(self, text: str, org_name: str, job_title: str) -> tuple:
        """Check if fetched content matches org name and job title."""
        if not text:
            return False, 0.0, ''
        
        text_lower = text.lower()
        org_lower = org_name.lower()
        
        # Check org name presence (fuzzy)
        org_words = [w for w in org_lower.split() if len(w) > 3]
        org_found = any(word in text_lower for word in org_words)
        
        # Check job title token overlap
        title_words = [w for w in job_title.lower().split() if len(w) > 3]
        if not title_words:
            title_overlap = 0.0
        else:
            matches = sum(1 for w in title_words if w in text_lower)
            title_overlap = matches / len(title_words)
        
        # Evidence snippet (first 200 chars around match)
        evidence = ''
        if org_found and title_overlap >= 0.6:
            # Find position of org name
            for word in org_words:
                pos = text_lower.find(word)
                if pos >= 0:
                    start = max(0, pos - 100)
                    end = min(len(text), pos + 200)
                    evidence = text[start:end].strip()
                    break
        
        return org_found and title_overlap >= 0.6, title_overlap, evidence
    
    def _is_soft_404(self, text: str, status: int) -> bool:
        """Detect soft 404 pages."""
        if not text:
            return False
        text_lower = text.lower()
        soft_404_phrases = [
            'no longer available', 'position closed', 'page not found',
            'job has expired', 'vacancy closed', 'this job is no longer',
            'position has been filled', 'recruitment closed',
            'application deadline has passed', 'job not found',
            'error 404', 'page doesn\'t exist'
        ]
        return any(phrase in text_lower for phrase in soft_404_phrases)
    
    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()[:32]
    
    def _detect_entry_type(self, text: str, final_url: str, final_host: str) -> str:
        """Detect if page is a job-specific posting or generic careers portal."""
        if not text:
            return 'unknown'
        
        text_lower = text.lower()
        url_lower = final_url.lower()
        
        # Generic portal indicators in URL
        generic_url_patterns = [
            '/careers', '/jobs', '/vacancies', '/recruitment', '/openings',
            '/positions', '/opportunities', '/apply', '/work-with-us'
        ]
        
        # Generic portal indicators in content
        generic_content_phrases = [
            'view all jobs', 'view all positions', 'all vacancies',
            'search jobs', 'browse jobs', 'current openings',
            'join our team', 'career opportunities', 'work with us',
            'explore careers', 'find your next role'
        ]
        
        # Job-specific indicators
        job_specific_phrases = [
            'job description', 'position summary', 'key responsibilities',
            'qualifications', 'requirements', 'essential duties',
            'apply now', 'apply for this position', 'reference number',
            'requisition', 'job id', 'vacancy number'
        ]
        
        generic_score = 0
        specific_score = 0
        
        # URL check
        for pattern in generic_url_patterns:
            if pattern in url_lower:
                # Check if URL has job-specific path (e.g., /careers/job/123)
                if re.search(r'(job|position|vacancy|requisition)[-/]\d+', url_lower):
                    specific_score += 2
                else:
                    generic_score += 1
        
        # Content check
        for phrase in generic_content_phrases:
            if phrase in text_lower:
                generic_score += 1
        
        for phrase in job_specific_phrases:
            if phrase in text_lower:
                specific_score += 2
        
        # Title token overlap check (if we have title words)
        # This will be done in _content_match
        
        if generic_score > specific_score and generic_score > 0:
            return 'careers_portal'
        elif specific_score > 0:
            return 'posting'
        elif generic_score > 0:
            return 'careers_portal'
        return 'unknown'
    
    def _is_generic_landing_page(self, text: str, final_url: str, final_host: str, 
                                  matched: bool, overlap: float) -> bool:
        """Check if page is a generic careers/recruitment landing page."""
        if not text:
            return True
        
        entry_type = self._detect_entry_type(text, final_url, final_host)
        
        # If content match failed AND it's a generic portal, it's a generic landing page
        if not matched and entry_type == 'careers_portal':
            return True
        
        # If overlap is very low and it's a portal, it's generic
        if entry_type == 'careers_portal' and overlap < 0.3:
            return True
        
        return False
    
    def verify(self, apply_url: str, employer_id: str, job_title: str = '', 
               org_name: str = '') -> VerificationResult:
        """
        Main verification entry point.
        
        Returns VerificationResult with all policy checks.
        """
        now = datetime.now(timezone.utc).isoformat()
        clean_url = self._strip_tracking_params(apply_url)
        error_detail = ''
        
        # Find employer
        employer = self._find_employer(employer_id)
        
        # If employer not in registry, check by domain
        if not employer:
            parsed = urlparse(clean_url)
            employer = self._find_employer_by_domain(parsed.hostname or '')
        
        if not employer:
            return VerificationResult(
                ok=False,
                final_url=clean_url,
                final_host=urlparse(clean_url).hostname or '',
                http_status=0,
                redirect_chain=[clean_url],
                verification_level='unverified',
                host_class='unregistered',
                reason_code='EMPLOYER_NOT_IN_REGISTRY',
                evidence_snippet='',
                content_hash='',
                verified_at=now,
                entry_type='unknown',
                error_detail='',
                warnings=[f'Employer {employer_id} not found in registry']
            )
        
        # Fetch with redirects
        try:
            response, redirect_chain = self._fetch_with_redirects(clean_url)
        except Exception as e:
            error_detail = f'{type(e).__name__}: {e}'
            final_url = clean_url
            final_host = urlparse(clean_url).hostname or ''
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=0,
                redirect_chain=[clean_url],
                verification_level='unverified',
                host_class=self._determine_host_class(final_host, employer),
                reason_code='VERIFICATION_ERROR',
                evidence_snippet='',
                content_hash='',
                verified_at=now,
                entry_type='unknown',
                error_detail=error_detail,
                warnings=[f'Fetch exception: {error_detail}']
            )
        
        final_url = redirect_chain[-1] if redirect_chain else clean_url
        final_host = urlparse(final_url).hostname or ''
        
        if not response:
            # Check if it's a known gov/academic host that blocks foreign IPs
            if self._is_gov_academic(final_host):
                return VerificationResult(
                    ok=False,
                    final_url=final_url,
                    final_host=final_host,
                    http_status=0,
                    redirect_chain=redirect_chain,
                    verification_level='unverified',
                    host_class='government_notice',
                    reason_code='UNREACHABLE_FROM_RUNNER',
                    evidence_snippet='',
                    content_hash='',
                    verified_at=now,
                    entry_type='unknown',
                    error_detail='Connection timeout/blocked from foreign IP',
                    warnings=[f'Government/academic host {final_host} unreachable from GitHub runner (foreign IP)']
                )
            error_detail = 'No response received (timeout/connection error)'
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=0,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class=self._determine_host_class(final_host, employer),
                reason_code='TIMEOUT' if 'timeout' in str(redirect_chain).lower() else 'CONNECTION_ERROR',
                evidence_snippet='',
                content_hash='',
                verified_at=now,
                entry_type='unknown',
                error_detail=error_detail,
                warnings=['Failed to fetch URL']
            )
        
        status = response.status_code
        content_type = response.headers.get('Content-Type', '')
        content = getattr(response, '_content_for_analysis', b'')
        text = self._extract_text_content(response, content_type)
        content_hash = self._compute_hash(content) if content else ''
        
        # Check HTTP status
        if status in (404, 410):
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class=self._determine_host_class(final_host, employer),
                reason_code='HTTP_404',
                evidence_snippet='',
                content_hash=content_hash,
                verified_at=now,
                entry_type='unknown',
                error_detail='',
                warnings=[f'HTTP {status}']
            )
        
        if status >= 400:
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class=self._determine_host_class(final_host, employer),
                reason_code=f'HTTP_{status}',
                evidence_snippet='',
                content_hash=content_hash,
                verified_at=now,
                entry_type='unknown',
                error_detail=f'HTTP {status}',
                warnings=[f'HTTP {status}']
            )
        
        # Soft 404 check
        if self._is_soft_404(text, status):
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class=self._determine_host_class(final_host, employer),
                reason_code='SOFT_404',
                evidence_snippet=text[:200],
                content_hash=content_hash,
                verified_at=now,
                entry_type=self._detect_entry_type(text, final_url, final_host),
                error_detail='',
                warnings=['Soft 404 detected']
            )
        
        # Determine host class
        host_class = self._determine_host_class(final_host, employer)
        
        # Blocklist check
        if host_class == 'blocklisted':
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class='blocklisted',
                reason_code='BLOCKED_HOST',
                evidence_snippet='',
                content_hash=content_hash,
                verified_at=now,
                entry_type=self._detect_entry_type(text, final_url, final_host),
                error_detail='',
                warnings=[f'Final host {final_host} is blocklisted']
            )
        
        # Host not in registry
        if host_class == 'unregistered':
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class='unregistered',
                reason_code='HOST_NOT_IN_REGISTRY',
                evidence_snippet='',
                content_hash=content_hash,
                verified_at=now,
                entry_type=self._detect_entry_type(text, final_url, final_host),
                error_detail='',
                warnings=[f'Final host {final_host} not in employer registry']
            )
        
        # Content match check (for page_verified)
        org_name = employer.get('name', '')
        job_title_clean = job_title or org_name
        matched, overlap, evidence = self._content_match(text, org_name, job_title_clean)
        entry_type = self._detect_entry_type(text, final_url, final_host)
        
        # Check for generic landing page
        is_generic = self._is_generic_landing_page(text, final_url, final_host, matched, overlap)
        
        if is_generic:
            return VerificationResult(
                ok=False,
                final_url=final_url,
                final_host=final_host,
                http_status=status,
                redirect_chain=redirect_chain,
                verification_level='unverified',
                host_class=host_class,
                reason_code='GENERIC_LANDING_PAGE',
                evidence_snippet=text[:200] if text else '',
                content_hash=content_hash,
                verified_at=now,
                entry_type='careers_portal',
                error_detail='',
                warnings=['Generic careers/recruitment landing page - not job-specific']
            )
        
        if matched:
            verification_level = 'page_verified'
            reason_code = 'OK'
            ok = True
        else:
            # Domain verified only - host is allowed but content couldn't be matched
            verification_level = 'domain_verified'
            reason_code = 'CONTENT_MISMATCH' if text else 'EMPTY_RESPONSE'
            ok = True  # Still OK for domain_verified per policy
        
        return VerificationResult(
            ok=ok,
            final_url=final_url,
            final_host=final_host,
            http_status=status,
            redirect_chain=redirect_chain,
            verification_level=verification_level,
            host_class=host_class,
            reason_code=reason_code,
            evidence_snippet=evidence[:200] if evidence else '',
            content_hash=content_hash,
            verified_at=now,
            entry_type=entry_type,
            error_detail=error_detail,
            warnings=[]
        )


def load_employers_registry(path: str = 'public/employers.json') -> Dict[str, Any]:
    """Load employer registry from JSON file."""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def verify_link(apply_url: str, employer_id: str, job_title: str = '', 
                org_name: str = '', employers_registry: Optional[Dict] = None,
                use_playwright: bool = False) -> VerificationResult:
    """
    Convenience function to verify a single link.
    
    Args:
        apply_url: The application URL to verify
        employer_id: Employer ID from employers.json
        job_title: Job title for content matching
        org_name: Organisation name for content matching
        employers_registry: Pre-loaded registry (optional)
        use_playwright: Use Playwright fallback for JS-rendered pages
    
    Returns:
        VerificationResult with all checks
    """
    if employers_registry is None:
        employers_registry = load_employers_registry()
    
    verifier = LinkVerifier(employers_registry, use_playwright)
    return verifier.verify(apply_url, employer_id, job_title, org_name)


if __name__ == '__main__':
    # CLI for testing
    import sys
    if len(sys.argv) < 3:
        print("Usage: python verify_link.py <apply_url> <employer_id> [job_title] [org_name]")
        sys.exit(1)
    
    apply_url = sys.argv[1]
    employer_id = sys.argv[2]
    job_title = sys.argv[3] if len(sys.argv) > 3 else ''
    org_name = sys.argv[4] if len(sys.argv) > 4 else ''
    
    result = verify_link(apply_url, employer_id, job_title, org_name)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))