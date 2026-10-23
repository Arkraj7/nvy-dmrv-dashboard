#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verified international opportunity harvesters.

The global registry is intentionally separate from the India registry.  This
module only reads official organisation websites and ReliefWeb's public
Climate Change & Environment jobs feed.  It never reads LinkedIn, Indeed,
Naukri or any other aggregator.

Each source is best-effort: a 403/WAF challenge is logged and skipped rather
than allowed to break the daily pipeline.  The returned dictionaries are
deliberately close to the registry schema so ``fetch_and_humanize`` can turn
them into records without a Gemini call (and therefore without inventing any
facts).
"""
from __future__ import annotations

import html as html_module
import logging
import re
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlparse

log = logging.getLogger("ufp-global-sources")

try:  # optional in bare maintenance environments
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None  # type: ignore


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}
REQUEST_TIMEOUT = 30
MAX_DESCRIPTION = 7000

RELIEFWEB_THEME_JOBS_RSS = (
    "https://reliefweb.int/jobs/rss.xml?advanced-search=%28T4588%29"
)
RELIEFWEB_V1_JOBS_API = "https://api.reliefweb.int/v1/jobs?appname=urbanforestpark"
RELIEFWEB_V2_JOBS_API = "https://api.reliefweb.int/v2/jobs"
DEFAULT_RELIEFWEB_APPNAME = "urbanforestpark"

IUCN_OPEN_VACANCIES = "https://hrms.iucn.org/iresy/index.cfm?event=vac.showOpenList"
CIFOR_WORK_WITH_US = "https://www.cifor-icraf.org/about/work-with-us/"
LANDSCAPE_ALLIANCE_WORK_WITH_US = "https://www.landscapealliance.org/about/work-with-us/"
WRI_JOBS = "https://www.wri.org/careers/jobs"
GUND_PHD_COMPETITION = (
    "https://www.uvm.edu/gund/news/gund-institute-funded-phd-competition-now-open-0"
)
GUND_POSTDOCS = "https://www.uvm.edu/gund/postdoctoral-fellowships"
WWF_JOBS = "https://wwf.panda.org/jobs_wwf/"
WWF_DAYFORCE = "https://jobs.dayforcehcm.com/en-GB/wwfint/external/jobs"

RELEVANT_RE = re.compile(
    r"\b(climate|environment|environmental|forest|forestry|agroforest|landscape|"
    r"conservation|biodiversity|wildlife|ecosystem|ecology|ecological|water|"
    r"agricultur|food loss|food waste|restoration|sustainab|carbon|esg|energy|"
    r"nature|ocean|marine|resilience|adaptation|mitigation|gis|geospatial|"
    r"remote sensing|earth observation|critical mineral|green finance|"
    r"climate finance|soil|land health|reforestation|afforestation|"
    r"restore|red list|species|protected area|pollution|circular economy|renewable)\b",
    re.I,
)
EXCLUDED_TITLE_RE = re.compile(
    r"\b(accountant|accounting|auditor|payroll|procurement officer|driver|"
    r"cleaner|security guard|receptionist|administrative assistant|"
    r"executive assistant|human resources|hr officer|it support|"
    r"network engineer|software engineer|enterprise systems|global it|"
    r"legal counsel|general counsel|finance officer|finance assistant|"
    r"head of finance|financial planning|budget analyst|budget officer|"
    r"treasury|transport assistant|visual communication|visibility designer|"
    r"graphic designer|financier|financiero|financière|responsable du service|"
    r"asistencia de transporte|chofer|business service manager|"
    r"general call for applications|science roster|consultant roster)\b",
    re.I,
)
REMOTE_RE = re.compile(r"\b(remote|home[- ]based|home based|worldwide|global|anywhere)\b", re.I)

COUNTRY_ALIASES: Tuple[Tuple[str, str], ...] = (
    ("united states of america", "United States"),
    ("united states", "United States"),
    ("united kingdom of great britain and northern ireland", "United Kingdom"),
    ("united kingdom", "United Kingdom"),
    ("great britain", "United Kingdom"),
    ("republic of korea", "Republic of Korea"),
    ("south korea", "Republic of Korea"),
    ("côte d'ivoire", "Côte d'Ivoire"),
    ("cote d'ivoire", "Côte d'Ivoire"),
    ("democratic republic of the congo", "Democratic Republic of the Congo"),
    ("dr congo", "Democratic Republic of the Congo"),
    ("united republic of tanzania", "Tanzania"),
    ("syrian arab republic", "Syria"),
    ("syria", "Syria"),
    ("chad", "Chad"),
    ("viet nam", "Vietnam"),
    ("vietnam", "Vietnam"),
    ("costa rica", "Costa Rica"),
    ("south africa", "South Africa"),
    ("new zealand", "New Zealand"),
    ("papua new guinea", "Papua New Guinea"),
    ("saudi arabia", "Saudi Arabia"),
    ("united arab emirates", "United Arab Emirates"),
    ("sri lanka", "Sri Lanka"),
    ("bangladesh", "Bangladesh"),
    ("cambodia", "Cambodia"),
    ("myanmar", "Myanmar"),
    ("indonesia", "Indonesia"),
    ("malaysia", "Malaysia"),
    ("philippines", "Philippines"),
    ("thailand", "Thailand"),
    ("singapore", "Singapore"),
    ("australia", "Australia"),
    ("japan", "Japan"),
    ("china", "China"),
    ("nepal", "Nepal"),
    ("maldives", "Maldives"),
    ("india", "India"),
    ("kenya", "Kenya"),
    ("ethiopia", "Ethiopia"),
    ("nigeria", "Nigeria"),
    ("ghana", "Ghana"),
    ("uganda", "Uganda"),
    ("gabon", "Gabon"),
    ("micronesia", "Micronesia"),
    ("tanzania", "Tanzania"),
    ("rwanda", "Rwanda"),
    ("zambia", "Zambia"),
    ("zimbabwe", "Zimbabwe"),
    ("cameroon", "Cameroon"),
    ("senegal", "Senegal"),
    ("egypt", "Egypt"),
    ("jordan", "Jordan"),
    ("lebanon", "Lebanon"),
    ("iraq", "Iraq"),
    ("turkey", "Türkiye"),
    ("germany", "Germany"),
    ("switzerland", "Switzerland"),
    ("netherlands", "Netherlands"),
    ("belgium", "Belgium"),
    ("france", "France"),
    ("italy", "Italy"),
    ("spain", "Spain"),
    ("portugal", "Portugal"),
    ("ireland", "Ireland"),
    ("austria", "Austria"),
    ("sweden", "Sweden"),
    ("norway", "Norway"),
    ("denmark", "Denmark"),
    ("finland", "Finland"),
    ("poland", "Poland"),
    ("czech republic", "Czech Republic"),
    ("czechia", "Czech Republic"),
    ("greece", "Greece"),
    ("canada", "Canada"),
    ("mexico", "Mexico"),
    ("brazil", "Brazil"),
    ("peru", "Peru"),
    ("colombia", "Colombia"),
    ("ecuador", "Ecuador"),
    ("bolivia", "Bolivia"),
    ("chile", "Chile"),
    ("argentina", "Argentina"),
    ("paraguay", "Paraguay"),
    ("uruguay", "Uruguay"),
    ("fiji", "Fiji"),
    ("vanuatu", "Vanuatu"),
    ("solomon islands", "Solomon Islands"),
)
COUNTRY_LOOKUP = sorted(COUNTRY_ALIASES, key=lambda item: len(item[0]), reverse=True)

EUROPE_COUNTRIES = {
    "Germany", "Switzerland", "Netherlands", "Belgium", "France", "Italy",
    "Spain", "Portugal", "Ireland", "Austria", "Sweden", "Norway", "Denmark",
    "Finland", "Poland", "Czech Republic", "Greece", "United Kingdom",
}
NORTH_AMERICA_COUNTRIES = {"United States", "Canada", "Mexico"}
ASIA_PACIFIC_COUNTRIES = {
    "India", "Bangladesh", "Nepal", "Sri Lanka", "Maldives", "Indonesia",
    "Malaysia", "Philippines", "Thailand", "Vietnam", "Cambodia", "China",
    "Japan", "Republic of Korea", "Singapore", "Australia", "New Zealand",
    "Papua New Guinea", "Fiji", "Vanuatu", "Solomon Islands", "Myanmar",
    "Micronesia",
}
AFRICA_MIDDLE_EAST_COUNTRIES = {
    "Kenya", "Ethiopia", "Nigeria", "Ghana", "Uganda", "Tanzania", "Rwanda",
    "Zambia", "Zimbabwe", "Cameroon", "Senegal", "Egypt", "Jordan", "Lebanon",
    "Iraq", "Türkiye", "South Africa", "Côte d'Ivoire",
    "Democratic Republic of the Congo", "Saudi Arabia", "United Arab Emirates",
    "Syria", "Chad", "Gabon",
}
LATIN_AMERICA_COUNTRIES = {
    "Brazil", "Peru", "Colombia", "Ecuador", "Bolivia", "Chile", "Argentina",
    "Paraguay", "Uruguay", "Costa Rica",
}

SKILLS: Tuple[Tuple[str, str], ...] = (
    (r"\bgis\b|geographic information|spatial analysis|geospatial", "GIS / spatial analysis"),
    (r"remote sensing|earth observation|satellite", "Remote sensing / Earth observation"),
    (r"biodiversity|species|red list|conservation", "Biodiversity conservation"),
    (r"forest|agroforest|landscape|restoration|reforestation", "Forest and landscape restoration"),
    (r"climate finance|green finance|sustainable finance|investment", "Climate and sustainable finance"),
    (r"carbon market|mrv|carbon credit|emissions", "Carbon markets / MRV"),
    (r"esg|sustainability reporting|csr", "ESG and sustainability reporting"),
    (r"policy|governance|advocacy|negotiation", "Climate policy and governance"),
    (r"data analysis|statistics|modelling|modeling|python|r language", "Data analysis and modelling"),
    (r"monitoring and evaluation|mel\b|monitoring, evaluation", "Monitoring and evaluation"),
    (r"stakeholder|partnership|engagement|coordination", "Stakeholder engagement"),
    (r"project management|programme management|program management", "Project and programme management"),
    (r"field research|fieldwork|survey", "Field research"),
    (r"report writing|publication|knowledge product|communication", "Research writing and communication"),
    (r"soil|land health|agriculture|agroecology", "Soil health and sustainable agriculture"),
    (r"water|wash|sanitation|hydrology", "Water and WASH"),
    (r"energy|renewable|clean energy|energy transition", "Clean energy transition"),
    (r"marine|ocean|coastal|fisheries", "Marine and coastal conservation"),
    (r"grant|fundraising|resource mobilization", "Grants and resource mobilization"),
)

CATEGORY_RULES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(gis|remote sensing|geospatial|earth observation|satellite|cartograph)", re.I),
     "GIS, Remote Sensing & Earth Observation"),
    (re.compile(r"\b(phd|doctoral|postdoc|post-doc|post doctoral|fellowship|fellow)\b", re.I),
     "Fellowships & Leadership Programs"),
    (re.compile(r"\b(intern|internship|trainee|traineeship|est[\u00e1a]gio|estagi[\u00e1a]rio)\b", re.I),
     "Internships & Student Traineeships"),
    (re.compile(r"\b(forest|forestry|wildlife|conservation|biodiversity|ecosystem|ecology|"
                r"reforestation|afforestation|marine|ocean)\b", re.I),
     "Forestry, Wildlife & Afforestation"),
    (re.compile(r"\b(esg|carbon|sustainability|climate finance|green finance|sustainable finance|"
                r"corporate sustainability|net zero|decarbon)\b", re.I),
     "ESG, Carbon Markets & Corporate Sustainability"),
    (re.compile(r"\b(climate|environment|policy|governance|adaptation|mitigation|resilience)\b", re.I),
     "Climate Policy, Think-Tanks & Fellowships"),
    (re.compile(r"\b(research|scientist|analyst|associate|consultant|officer|manager|director|"
                r"coordinator|specialist|advisor|adviser|lead|head)\b", re.I),
     "Research Associate & Project Staff (Contractual)"),
)

POSITION_RULES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(jrf|junior research fellow|srf|senior research fellow)\b", re.I), "JRF / SRF"),
    (re.compile(r"\b(ph\.?\s?d|doctoral|doctorate|post-?doctoral|postdoc)\b", re.I),
     "PhD / Doctoral Fellowship"),
    (re.compile(r"\b(project associate|research associate|project assistant|research assistant|"
                r"project scientist|research scientist)\b", re.I),
     "Project Associate / Research Associate"),
    (re.compile(r"\b(young professional|consultant|advisor|adviser)\b", re.I),
     "Young Professional / Consultant (Contractual)"),
    (re.compile(r"\b(professor|faculty|lecturer|dean)\b", re.I), "Faculty / Academic"),
    (re.compile(r"\b(fellow|fellowship|intern|internship|trainee)\b", re.I),
     "Fellowship / Internship"),
    (re.compile(r"\b(part[- ]time|contract|consultancy|temporary)\b", re.I),
     "Part-Time / Contract"),
    (re.compile(r"\b(full[- ]time|permanent|staff)\b", re.I), "Full-Time Corporate / NGO"),
)

KIND_RULES: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b(grant|funding|rfp|request for proposals|call for proposals)\b", re.I),
     "Grant / Funding"),
    (re.compile(r"\b(scholarship|studentship|doctoral support|phd)\b", re.I), "Scholarship"),
    (re.compile(r"\b(fellowship|fellow|postdoc|post-doc|postdoctoral)\b", re.I), "Fellowship"),
    (re.compile(r"\b(intern|internship|trainee|traineeship|est[\u00e1a]gio|estagi[\u00e1a]rio)\b", re.I), "Internship"),
    (re.compile(r"\b(competition|award|prize|challenge|hackathon)\b", re.I), "Competition / Award"),
)

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _clean(value: Any) -> str:
    text = html_module.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _paragraph_text(node: Any) -> str:
    if node is None:
        return ""
    return _clean(node.get_text(" ", strip=True))


CHROME_MARKERS = (
    "main navigation",
    "skip to content",
    "footer menu",
    "click to see more",
    "back to work with us",
    "share this page",
    "learn more world resources",
)


def _looks_like_site_chrome(value: Any) -> bool:
    text = _clean(value).lower()
    if not text:
        return True
    if any(marker in text for marker in CHROME_MARKERS):
        return True
    navigation_hits = sum(
        1
        for label in (" research ", " data ", " initiatives ", " insights ", " donate ")
        if label in f" {text} "
    )
    return navigation_hits >= 3 and not re.search(r"[.!?]\s", text)


def classify_category(title: str, description: str = "") -> str:
    """Public wrapper used by the registry when repairing legacy records."""
    return _category(title, description)


def _get(url: str, *, params: Optional[Dict[str, Any]] = None,
         headers: Optional[Dict[str, str]] = None) -> Optional[Any]:
    if requests is None:
        log.warning("requests is not installed - cannot fetch %s", url)
        return None
    merged = dict(REQUEST_HEADERS)
    if headers:
        merged.update(headers)
    for attempt in range(1, 4):
        try:
            response = requests.get(
                url, params=params, headers=merged, timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200 and len(response.content) > 200:
                return response
            log.info(
                "Global source returned HTTP %s for %s (attempt %d/3)",
                response.status_code, url, attempt,
            )
        except Exception as exc:  # noqa: BLE001
            log.info("Global source fetch failed for %s (attempt %d/3): %s", url, attempt, exc)
        if attempt < 3:
            time.sleep(0.7 * attempt)
    return None


def _soup(response: Any) -> Any:
    if response is None or BeautifulSoup is None:
        return None
    try:
        raw = response.content or b""
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode(response.encoding or "utf-8", errors="replace")
        return BeautifulSoup(text, "html.parser")
    except Exception:  # noqa: BLE001
        return None


def _is_relevant(title: str, description: str = "") -> bool:
    text = f"{title} {description}"
    if not RELEVANT_RE.search(text):
        return False
    if EXCLUDED_TITLE_RE.search(title) and not RELEVANT_RE.search(title):
        return False
    return True


def _country(text: str) -> str:
    lowered = _clean(text).lower()
    if REMOTE_RE.search(lowered):
        return "Global"
    for alias, country in COUNTRY_LOOKUP:
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", lowered):
            return country
    return ""


def _city(text: str, country: str) -> str:
    text = _clean(text)
    if REMOTE_RE.search(text):
        return "Remote"
    if not text:
        return ""
    parts = [part.strip() for part in re.split(r"[,|/]", text) if part.strip()]
    if country:
        for part in parts:
            if part.lower() == country.lower():
                continue
            return part
    return parts[0] if parts else ""


def _region(country: str, organization: str = "", location: str = "") -> str:
    if country in EUROPE_COUNTRIES:
        return "Europe"
    if country in NORTH_AMERICA_COUNTRIES:
        return "North America"
    if country in ASIA_PACIFIC_COUNTRIES:
        return "Asia-Pacific"
    if country in AFRICA_MIDDLE_EAST_COUNTRIES:
        return "Africa & Middle East"
    if country in LATIN_AMERICA_COUNTRIES:
        return "Latin America"
    if re.search(r"\b(united nations|un |undp|unep|unfccc|university|iucn|wri|"
                 r"world bank|global fund|green climate fund|multilateral|"
                 r"international organization|international organisation)\b",
                 f"{organization} {location}", re.I):
        return "UN / Multilateral"
    return "Global / Remote"


def _category(title: str, description: str) -> str:
    text = f"{title} {description[:800]}"
    for pattern, category in CATEGORY_RULES:
        if pattern.search(text):
            return category
    return "Climate Policy, Think-Tanks & Fellowships"


def _position_type(title: str) -> str:
    for pattern, position_type in POSITION_RULES:
        if pattern.search(title):
            return position_type
    return "Full-Time Corporate / NGO"


def _opportunity_kind(title: str, description: str = "") -> str:
    text = f"{title} {description[:600]}"
    for pattern, kind in KIND_RULES:
        if pattern.search(text):
            return kind
    return "Job / Career"


def _parse_deadline(value: str) -> Optional[date]:
    text = _clean(value)
    if not text:
        return None
    iso = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", text)
    if iso:
        try:
            return date(int(iso.group(1)), int(iso.group(2)), int(iso.group(3)))
        except ValueError:
            pass
    match = re.search(
        r"\b(\d{1,2})\s+(Jan(?:uary)?\.?|Feb(?:ruary)?\.?|Mar(?:ch)?\.?|Apr(?:il)?\.?|"
        r"May\.?|Jun(?:e)?\.?|Jul(?:y)?\.?|Aug(?:ust)?\.?|Sep(?:t(?:ember)?)?\.?|"
        r"Oct(?:ober)?\.?|Nov(?:ember)?\.?|Dec(?:ember)?\.?)\s+(20\d{2})\b",
        text,
        re.I,
    )
    if match:
        month = MONTHS.get(match.group(2).lower()[:3])
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1)))
            except ValueError:
                pass
    match = re.search(
        r"\b(Jan(?:uary)?\.?|Feb(?:ruary)?\.?|Mar(?:ch)?\.?|Apr(?:il)?\.?|May\.?|"
        r"Jun(?:e)?\.?|Jul(?:y)?\.?|Aug(?:ust)?\.?|Sep(?:t(?:ember)?)?\.?|"
        r"Oct(?:ober)?\.?|Nov(?:ember)?\.?|Dec(?:ember)?\.?)\s+(\d{1,2}),?\s+(20\d{2})\b",
        text,
        re.I,
    )
    if match:
        month = MONTHS.get(match.group(1).lower()[:3])
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(2)))
            except ValueError:
                pass
    return None


def _deadline_label(value: str, fallback: str = "Rolling / Open") -> str:
    parsed = _parse_deadline(value)
    return parsed.strftime("%d %B %Y") if parsed else (fallback if not _clean(value) else _clean(value))


def _summary(description: str, title: str, organization: str) -> str:
    text = _clean(description)
    text = re.sub(
        r"^(menu|back to work with us|about|share this|page|apply|job details)\s+",
        "", text, flags=re.I,
    )
    sentences = re.split(r"(?<=[.!?])\s+", text)
    picked: List[str] = []
    for sentence in sentences:
        sentence = _clean(sentence)
        if len(sentence) < 55:
            continue
        if sentence.lower().startswith(("reference number", "job status", "job category",
                                        "duty station", "vacancy", "unit:", "location:",
                                        "closing date", "apply", "share this", "about us")):
            continue
        if title and _clean(sentence).lower() == _clean(title).lower():
            continue
        if not RELEVANT_RE.search(sentence) and len(picked) == 0:
            continue
        picked.append(sentence)
        if len(" ".join(picked)) >= 280:
            break
    if picked:
        return " ".join(picked)[:520].strip()
    return f"{title} at {organization}." if organization else title


def _qualification(description: str, title: str) -> str:
    text = _clean(description)
    for marker in ("qualifications", "requirements", "education", "profile",
                   "what you will need", "eligibility", "experience required"):
        match = re.search(re.escape(marker) + r"[:\s]+(.{80,420})", text, re.I)
        if match:
            snippet = match.group(1)
            snippet = re.split(
                r"\b(responsibilities|duties|what you will do|about the role|"
                r"how to apply|application process)\b",
                snippet, maxsplit=1, flags=re.I,
            )[0]
            snippet = _clean(snippet).strip(" .:;-")
            if len(snippet) >= 60:
                return snippet[:380]
    if re.search(r"\bphd|doctoral|postdoc\b", title, re.I):
        return "A relevant PhD or doctoral degree; candidates should show independent research and publications in the field."
    if re.search(r"\bintern|trainee\b", title, re.I):
        return "Students or recent graduates in a relevant discipline; see the official call for specific eligibility."
    return "A relevant university degree and demonstrated professional experience in the field; see the official vacancy notice for exact requirements."


def _compensation(description: str, kind: str) -> str:
    text = _clean(description)
    match = re.search(
        r"((?:USD|EUR|GBP|INR|CHF|AUD|CAD)\s?[\d,.]+(?:\s?(?:-|to)\s?(?:USD|EUR|GBP|INR|CHF|AUD|CAD)?\s?[\d,.]+)?"
        r"|(?:stipend|salary|remuneration|daily rate|monthly rate|contract fee)[^.]{0,120})",
        text,
        re.I,
    )
    if match:
        value = _clean(match.group(1))
        if len(value) > 12:
            return value[:180]
    if kind == "Grant / Funding":
        return "See official call for funding amount"
    return "Not disclosed - see official portal"


def _responsibilities(description: str, title: str) -> List[str]:
    text = _clean(description)
    start = -1
    for marker in ("responsibilities", "duties", "what you will do", "key accountabilities",
                   "the role", "tasks"):
        found = re.search(re.escape(marker), text, re.I)
        if found:
            start = found.end()
            break
    if start >= 0:
        block = text[start:start + 1400]
        candidates = re.split(r"(?<=[.;])\s+|\s*[•]\s*", block)
        items = []
        for item in candidates:
            item = _clean(item).strip(" .;:-")
            if 24 <= len(item) <= 220 and not item.lower().startswith(
                ("how to apply", "application", "closing date", "location", "unit")
            ):
                items.append(item)
            if len(items) >= 5:
                break
        if len(items) >= 3:
            return items[:5]
    role = _clean(title).lower()
    if "gis" in role or "remote sensing" in role:
        return [
            "Produce and validate spatial datasets and geospatial analysis.",
            "Support field teams with mapping, quality control and documentation.",
            "Prepare maps, technical notes and progress updates for partners.",
            "Coordinate data sharing and adhere to the programme's data standards.",
        ]
    if "finance" in role or "investment" in role:
        return [
            "Appraise proposals and prepare investment or financial analysis.",
            "Monitor portfolio performance, risks and reporting requirements.",
            "Engage delivery partners and national counterparts.",
            "Prepare decision notes for committees and senior management.",
        ]
    return [
        "Deliver the role's core research and programme outputs.",
        "Coordinate with internal teams, partners and external stakeholders.",
        "Prepare high-quality written analysis, reports and briefings.",
        "Support monitoring, reporting and delivery against agreed deadlines.",
    ]


def _skills(description: str, title: str) -> List[str]:
    text = f"{title} {description}"
    found: List[str] = []
    for pattern, label in SKILLS:
        if re.search(pattern, text, re.I) and label not in found:
            found.append(label)
    if len(found) < 5:
        for fallback in (
            "Research and analysis", "Project management", "Stakeholder engagement",
            "Report writing", "Monitoring and evaluation",
        ):
            if fallback not in found:
                found.append(fallback)
            if len(found) >= 5:
                break
    return found[:7]


def _candidate(
    *,
    source: str,
    source_portal: str,
    title: str,
    organization: str,
    location: str,
    description: str,
    apply_url: str,
    org_website: str,
    posted: str = "",
    deadline: str = "",
) -> Dict[str, Any]:
    title = _clean(title)
    organization = _clean(organization)
    description = _clean(description)[:MAX_DESCRIPTION]
    # Several employer career pages serve a JavaScript shell whose visible text
    # is menus and footer links. Never let that chrome drive the category,
    # skills or summary: classify and summarize from the verified title instead.
    if _looks_like_site_chrome(description):
        description = ""
    location = _clean(location) or "Global / Remote"
    country = _country(location)
    if not country:
        country = _country(title)
    if not country and REMOTE_RE.search(f"{title} {description}"):
        country = "Global"
    if not country and location and "," not in location:
        # ReliefWeb and a few official boards give only a country name. Keep
        # it rather than flattening every such role to "Global".
        country = location
    if not country:
        country = "Global"
    city = _city(location, country)
    category = _category(title, description)
    position_type = _position_type(title)
    kind = _opportunity_kind(title, description)
    deadline_label = _deadline_label(deadline)
    parsed_deadline = _parse_deadline(deadline)
    if parsed_deadline and parsed_deadline < date.today():
        return {}
    return {
        "source": source,
        "source_portal": source_portal,
        "title": title,
        "organization": organization,
        "location_raw": location,
        "city": city,
        "state": "",
        "country": country,
        "region": _region(country, organization, location),
        "description": description,
        "role_summary": _summary(description, title, organization),
        "qualification_summary": _qualification(description, title),
        "compensation_or_fellowship": _compensation(description, kind),
        "key_responsibilities": _responsibilities(description, title),
        "must_have_skills": _skills(description, title),
        "category": category,
        "position_type": position_type,
        "opportunity_kind": kind,
        "deadline_or_window": deadline_label,
        "date_posted": _clean(posted),
        "apply_url": apply_url,
        "org_website": org_website,
        "application_tip": (
            "Apply through the official application link and tailor your CV to the "
            "specific competencies and deadline stated in the notice."
        ),
    }


# ---------------------------------------------------------------------------
# ReliefWeb
# ---------------------------------------------------------------------------
def _reliefweb_v2_candidates() -> List[Dict[str, Any]]:
    """Try ReliefWeb v2 with the requested appname, returning [] on 403."""
    if requests is None:
        return []
    payload = {
        "limit": 40,
        "profile": "full",
        "filter": {
            "field": "theme",
            "value": "climate change and environment",
        },
        "sort": ["date.created:desc"],
    }
    try:
        response = requests.post(
            RELIEFWEB_V2_JOBS_API,
            params={"appname": DEFAULT_RELIEFWEB_APPNAME},
            json=payload,
            headers={"Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            log.info(
                "ReliefWeb v2 unavailable (HTTP %s); using the public climate jobs RSS feed",
                response.status_code,
            )
            return []
        items = response.json().get("data", [])
    except Exception as exc:  # noqa: BLE001
        log.info("ReliefWeb v2 request failed (%s); using RSS", exc)
        return []
    results: List[Dict[str, Any]] = []
    for item in items:
        fields = item.get("fields") or {}
        title = _clean(fields.get("title"))
        body = _clean(fields.get("body"))
        if not title or not _is_relevant(title, body):
            continue
        countries = [
            _clean(country.get("name"))
            for country in (fields.get("country") or [])
            if country.get("name")
        ]
        source = fields.get("source") or []
        organization = _clean(source[0].get("name")) if source else "ReliefWeb"
        deadline = _clean(fields.get("date") or {}).get("closing") or ""
        candidate = _candidate(
            source="ReliefWeb",
            source_portal="ReliefWeb",
            title=title,
            organization=organization,
            location=", ".join(countries) or "Global / Remote",
            description=body,
            apply_url=_clean(fields.get("url")),
            org_website="https://reliefweb.int",
            posted=_clean((fields.get("date") or {}).get("created") or ""),
            deadline=deadline,
        )
        if candidate:
            results.append(candidate)
    return results


def fetch_reliefweb_global_candidates() -> List[Dict[str, Any]]:
    """ReliefWeb climate/environment jobs, v2 first and public RSS fallback.

    The legacy v1 endpoint is documented here because the requested URL used
    it, but ReliefWeb decommissioned v1 (HTTP 410) in 2026.  v2 is attempted
    with the ``urbanforestpark`` appname; while that approval is pending, the
    public Climate Change & Environment RSS feed is the authoritative fallback.
    """
    log.info("ReliefWeb: v1 endpoint is decommissioned; trying v2 then public RSS")
    v2 = _reliefweb_v2_candidates()
    if v2:
        log.info("ReliefWeb v2 returned %d global candidate(s)", len(v2))
        return v2
    if feedparser is None:
        log.warning("feedparser is not installed - skipping ReliefWeb RSS")
        return []
    response = _get(
        RELIEFWEB_THEME_JOBS_RSS,
        headers={
            "Accept": "application/rss+xml",
            "User-Agent": "python-requests/2.31.0",
        },
    )
    if response is None:
        return []
    parsed = feedparser.parse(response.content)
    results: List[Dict[str, Any]] = []
    for entry in parsed.entries:
        title = _clean(entry.get("title"))
        summary = _clean(entry.get("summary"))
        if not title or not _is_relevant(title, summary):
            continue
        country = ""
        match = re.search(r"Country:\s*([^\n]+?)(?:\s+Organization:|\s+Closing date:|$)",
                          summary, re.I)
        if match:
            country = _clean(match.group(1))
        organization = ""
        match = re.search(r"Organization:\s*([^\n]+?)(?:\s+Closing date:|$)", summary, re.I)
        if match:
            organization = _clean(match.group(1))
        deadline = ""
        match = re.search(r"Closing date:\s*([^\n]+?)(?:\s+[A-Z][a-z]+:|$)", summary, re.I)
        if match:
            deadline = _clean(match.group(1))
        body = re.sub(r"^(Country|Organization|Closing date):.*?(?=\s[A-Z])", " ",
                      summary, flags=re.I)
        candidate = _candidate(
            source="ReliefWeb",
            source_portal="ReliefWeb",
            title=title,
            organization=organization or "ReliefWeb-listed organisation",
            location=country or "Global / Remote",
            description=body or summary,
            apply_url=_clean(entry.get("link")),
            org_website="https://reliefweb.int",
            posted=_clean(entry.get("published") or ""),
            deadline=deadline,
        )
        if candidate:
            results.append(candidate)
    log.info("ReliefWeb RSS returned %d climate/environment candidate(s)", len(results))
    return results


# ---------------------------------------------------------------------------
# IUCN HRMS
# ---------------------------------------------------------------------------
def fetch_iucn_candidates() -> List[Dict[str, Any]]:
    response = _get(IUCN_OPEN_VACANCIES)
    soup = _soup(response)
    if soup is None:
        return []
    results: List[Dict[str, Any]] = []
    for row in soup.find_all("tr"):
        link = row.find("a", href=re.compile(r"vacId=\d+", re.I))
        if link is None:
            continue
        title = _paragraph_text(link)
        if not title or EXCLUDED_TITLE_RE.search(title):
            continue
        cells = row.find_all("td")
        location = _paragraph_text(cells[2]) if len(cells) > 2 else ""
        deadline = _paragraph_text(cells[3]) if len(cells) > 3 else ""
        href = urljoin("https://hrms.iucn.org", link.get("href", ""))
        detail = _get(href)
        detail_soup = _soup(detail)
        description = ""
        if detail_soup is not None:
            body = detail_soup.find("main") or detail_soup
            description = _paragraph_text(body)
        if not description:
            description = _paragraph_text(row)
        # The IUCN HRMS detail page uses its H1 for the site header, not the
        # vacancy title, so keep the authoritative title from the open-list row.
        if not _is_relevant(title, description):
            log.info("IUCN skipped non-green role: %s", title)
            continue
        candidate = _candidate(
            source="IUCN",
            source_portal="Official Organization Website",
            title=title,
            organization="International Union for Conservation of Nature (IUCN)",
            location=location,
            description=description,
            apply_url=href,
            org_website="https://www.iucn.org",
            deadline=deadline,
        )
        if candidate:
            results.append(candidate)
    log.info("IUCN returned %d relevant vacancy(ies)", len(results))
    return results


# ---------------------------------------------------------------------------
# WRI
# ---------------------------------------------------------------------------
def fetch_wri_candidates() -> List[Dict[str, Any]]:
    response = _get(WRI_JOBS)
    soup = _soup(response)
    if soup is None:
        return []
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=re.compile(r"^/careers/jobs/[^/?#]+", re.I)):
        title = _paragraph_text(link)
        href = urljoin("https://www.wri.org", link.get("href", ""))
        if not title or href in seen or EXCLUDED_TITLE_RE.search(title):
            continue
        seen.add(href)
        detail = _get(href)
        detail_soup = _soup(detail)
        description = ""
        location = ""
        deadline = ""
        if detail_soup is not None:
            body = detail_soup.find("main") or detail_soup
            description = _paragraph_text(body)
            text = _clean(description)
            match = re.search(
                r"Apply\s+(.+?)\s+Application Deadline\s+([A-Z][a-z]+\.?\s+\d{1,2},\s+20\d{2})",
                text, re.I,
            )
            if match:
                location = _clean(match.group(1))
                deadline = _clean(match.group(2))
            if not description:
                description = _paragraph_text(detail_soup)
        if not _is_relevant(title, description):
            log.info("WRI skipped non-green role: %s", title)
            continue
        candidate = _candidate(
            source="WRI",
            source_portal="Official Organization Website",
            title=title,
            organization="World Resources Institute (WRI)",
            location=location or "Global / Remote",
            description=description,
            apply_url=href,
            org_website="https://www.wri.org",
            deadline=deadline,
        )
        if candidate:
            results.append(candidate)
    log.info("WRI returned %d relevant vacancy(ies)", len(results))
    return results


# ---------------------------------------------------------------------------
# CIFOR-ICRAF / Landscape Alliance
# ---------------------------------------------------------------------------
def fetch_cifor_candidates() -> List[Dict[str, Any]]:
    response = _get(CIFOR_WORK_WITH_US)
    if response is None:
        log.info("CIFOR-ICRAF work-with-us page unavailable; trying Landscape Alliance")
        response = _get(LANDSCAPE_ALLIANCE_WORK_WITH_US)
    soup = _soup(response)
    if soup is None:
        return []
    results: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for link in soup.find_all("a", href=re.compile(r"/career/[0-9]", re.I)):
        href = urljoin("https://www.landscapealliance.org", link.get("href", ""))
        text = _paragraph_text(link)
        if not text or href in seen or EXCLUDED_TITLE_RE.search(text):
            continue
        seen.add(href)
        # Link text: title, location, team, contract type, closing date.
        # The list card is compact; the detail page's h1 is the clean title.
        title = text.split(" Closes ", 1)[0].strip()
        deadline = ""
        match = re.search(r"Closes\s+([0-9]{1,2}\s+[A-Z][a-z]+\s+20\d{2})", text, re.I)
        if match:
            deadline = match.group(1)
        location = ""
        for country_alias, country in COUNTRY_LOOKUP:
            if re.search(rf"\b{re.escape(country_alias)}\b", text, re.I):
                location = country
                break
        detail = _get(href)
        detail_soup = _soup(detail)
        description = ""
        if detail_soup is not None:
            heading = detail_soup.find("h1")
            if heading is not None and _paragraph_text(heading):
                title = _paragraph_text(heading)
            body = detail_soup.find("main") or detail_soup
            description = _paragraph_text(body)
            if not location:
                match = re.search(r"Duty station:\s*([^\n]+?)(?:\s+Download|\s+Reference|$)",
                                  description, re.I)
                if match:
                    location = _clean(match.group(1))
            if not deadline:
                match = re.search(r"(?:Closes|Closing date)[:\s]+([0-9]{1,2}\s+[A-Z][a-z]+\s+20\d{2})",
                                  description, re.I)
                if match:
                    deadline = match.group(1)
        if not location:
            location = "Global / Remote"
        if not _is_relevant(title, description):
            log.info("CIFOR-ICRAF skipped non-green role: %s", title)
            continue
        candidate = _candidate(
            source="CIFOR-ICRAF / Landscape Alliance",
            source_portal="Official Organization Website",
            title=title,
            organization="CIFOR-ICRAF (Landscape Alliance)",
            location=location,
            description=description,
            apply_url=href,
            org_website="https://www.landscapealliance.org",
            deadline=deadline,
        )
        if candidate:
            results.append(candidate)
    log.info("CIFOR-ICRAF returned %d relevant vacancy(ies)", len(results))
    return results


# ---------------------------------------------------------------------------
# Gund Institute
# ---------------------------------------------------------------------------
def fetch_gund_candidates() -> List[Dict[str, Any]]:
    response = _get(GUND_PHD_COMPETITION)
    soup = _soup(response)
    if soup is None:
        return []
    text = _paragraph_text(soup.find("main") or soup)
    deadline = ""
    match = re.search(r"Applications? (?:are )?due\s+([A-Z][a-z]+\.?\s+\d{1,2},\s+20\d{2})", text, re.I)
    if match:
        deadline = match.group(1)
    candidate = _candidate(
        source="Gund Institute",
        source_portal="Official Organization Website",
        title="Gund Institute Funded PhD Competition - Climate & Sustainability Research",
        organization="Gund Institute for Environment, University of Vermont",
        location="Burlington, Vermont, United States",
        description=text,
        apply_url=GUND_PHD_COMPETITION,
        org_website="https://www.uvm.edu/gund",
        deadline=deadline,
    )
    results = [candidate] if candidate else []
    # The postdoctoral programme page is a standing call, but it is not a
    # current vacancy on its own.  Keep it only when it explicitly names a
    # deadline in the page copy.
    postdoc = _get(GUND_POSTDOCS)
    postdoc_soup = _soup(postdoc)
    if postdoc_soup is not None:
        postdoc_text = _paragraph_text(postdoc_soup.find("main") or postdoc_soup)
        postdoc_deadline = ""
        match = re.search(
            r"(?:applications? (?:are )?due|deadline)[:\s]+([A-Z][a-z]+\.?\s+\d{1,2},\s+20\d{2})",
            postdoc_text, re.I,
        )
        if match:
            postdoc_deadline = match.group(1)
    log.info("Gund Institute returned %d active candidate(s)", len(results))
    return results


# ---------------------------------------------------------------------------
# WWF International (best effort)
# ---------------------------------------------------------------------------
def fetch_wwf_candidates() -> List[Dict[str, Any]]:
    """WWF International uses a JS-only Dayforce board.

    The public jobs landing page is Cloudflare-protected and the Dayforce
    board renders vacancies client-side, so we deliberately do not fabricate
    replacements.  A parseable Dayforce JSON payload is used when it becomes
    available; otherwise the source is skipped gracefully.
    """
    response = _get(WWF_JOBS)
    if response is None:
        return []
    soup = _soup(response)
    if soup is None:
        return []
    results: List[Dict[str, Any]] = []
    for link in soup.find_all("a", href=True):
        text = _paragraph_text(link)
        href = urljoin("https://wwf.panda.org", link.get("href", ""))
        if not text or not _is_relevant(text):
            continue
        if not re.search(r"job|vacanc|career|position", href + " " + text, re.I):
            continue
        candidate = _candidate(
            source="WWF International",
            source_portal="Official Organization Website",
            title=text,
            organization="WWF International",
            location="Global / Remote",
            description=text,
            apply_url=href,
            org_website="https://wwf.panda.org",
        )
        if candidate:
            results.append(candidate)
    log.info("WWF International returned %d parseable candidate(s)", len(results))
    return results


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def fetch_official_global_candidates() -> List[Dict[str, Any]]:
    """Return de-duplicated candidates from every official source.

    Source failures are isolated so one WAF challenge cannot stop the others.
    The ReliefWeb RSS feed is intentionally last: it is broad and its entries
    overlap with employer postings, so official pages win on duplicate URLs.
    """
    harvesters = (
        ("IUCN", fetch_iucn_candidates),
        ("WRI", fetch_wri_candidates),
        ("CIFOR-ICRAF", fetch_cifor_candidates),
        ("Gund Institute", fetch_gund_candidates),
        ("WWF International", fetch_wwf_candidates),
        ("ReliefWeb", fetch_reliefweb_global_candidates),
    )
    all_candidates: List[Dict[str, Any]] = []
    for label, harvester in harvesters:
        try:
            found = harvester()
        except Exception as exc:  # noqa: BLE001
            log.warning("%s global harvester failed: %s | %s", label, type(exc).__name__, exc)
            continue
        log.info("%s global harvester yielded %d candidate(s)", label, len(found))
        all_candidates.extend(found)

    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for candidate in all_candidates:
        key = (candidate.get("apply_url") or "").strip().lower()
        title_key = (
            re.sub(r"[^a-z0-9]+", " ", (candidate.get("title") or "").lower()).strip(),
            re.sub(r"[^a-z0-9]+", " ", (candidate.get("organization") or "").lower()).strip(),
            re.sub(r"[^a-z0-9]+", " ", (candidate.get("country") or "").lower()).strip(),
        )
        identity = "|".join(title_key) or key
        if not identity or identity in seen:
            continue
        seen.add(identity)
        unique.append(candidate)
    log.info("Official global harvest: %d unique candidate(s)", len(unique))
    return unique
