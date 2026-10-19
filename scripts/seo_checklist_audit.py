#!/usr/bin/env python
"""Seven-group SEO checklist auditor for the Urban Forest Park registry.

Groups
  1. URL hygiene      - one canonical host, no http://, no non-www variants
  2. Metadata         - titles, descriptions, single H1, keyword alignment
  3. Crawl controls   - robots.txt, sitemap canonicals, lastmod, exclusions
  4. Structured data  - parseable JSON-LD with the required graph per page
  5. International    - reciprocal hreflang cluster on the language pages
  6. Internal linking - no broken links/images, depth <= 2, no orphan pages
  7. Delivery         - headers, logo weight, favicons, confidential gate

Exits non-zero when any ERROR is recorded. Warnings do not fail the run.
"""

from __future__ import annotations

import io
import json
import re
import sys
from collections import deque
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = "https://www.urbanforestpark.com"
HOST = "www.urbanforestpark.com"

TITLE_MIN, TITLE_MAX = 55, 60
DESC_MIN, DESC_MAX = 155, 160

NOINDEX_FILES = {"404.html", "500.html", "unsubscribe.html", "newsletter_latest.html"}
LANGUAGE_PAGES = [
    "index.html",
    "hindi-environment-forestry-jobs.html",
    "bharat-regional-green-jobs.html",
    "global-climate-sustainability-opportunities.html",
]
HUB_FILES = [
    "jrf-srf-project-associate-jobs.html",
    "phd-fellowships-climate-sustainability.html",
    "forestry-wildlife-government-jobs.html",
    "gis-remote-sensing-climate-jobs.html",
    "esg-carbon-sustainability-jobs.html",
]
MATRIX_FILES = [
    "index.html",
    "404.html",
    "500.html",
    *HUB_FILES,
    "hindi-environment-forestry-jobs.html",
    "bharat-regional-green-jobs.html",
    "global-climate-sustainability-opportunities.html",
    "about.html",
]

TOP_STATE_HREFS = [
    ("Uttar Pradesh", "/?state=Uttar%20Pradesh"),
    ("Maharashtra", "/?state=Maharashtra"),
    ("Delhi NCR", "/?state=Delhi%20NCR"),
    ("Karnataka", "/?state=Karnataka"),
    ("Tamil Nadu", "/?state=Tamil%20Nadu"),
    ("Madhya Pradesh", "/?state=Madhya%20Pradesh"),
    ("Rajasthan", "/?state=Rajasthan"),
    ("Gujarat", "/?state=Gujarat"),
    ("Telangana", "/?state=Telangana"),
    ("Uttarakhand", "/?state=Uttarakhand"),
    ("West Bengal", "/?state=West%20Bengal"),
    ("Bihar", "/?state=Bihar"),
    ("Kerala", "/?state=Kerala"),
    ("Punjab", "/?state=Punjab"),
    ("Odisha", "/?state=Odisha"),
    ("Assam", "/?state=Assam"),
]

ERRORS: List[str] = []
WARNINGS: List[str] = []
INFO: List[str] = []


def error(group: str, message: str) -> None:
    ERRORS.append(f"[G{group}] ERROR {message}")


def warn(group: str, message: str) -> None:
    WARNINGS.append(f"[G{group}] WARN  {message}")


def info(message: str) -> None:
    INFO.append(message)


def read_text(path: Path) -> str:
    return io.open(path, encoding="utf-8", errors="replace").read()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

META_RE = re.compile(r"<meta\b[^>]*>", re.I)
LINK_RE = re.compile(r"<link\b[^>]*>", re.I)
H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
LD_RE = re.compile(
    r"<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>", re.I | re.S
)
TAG_STRIP = re.compile(r"<[^>]+>")


def attr(tag: str, name: str) -> Optional[str]:
    m = re.search(r"\b" + re.escape(name) + r"\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
    return m.group(2) if m else None


def unescape(value: str) -> str:
    named = {
        "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'",
        "mdash": "\u2014", "ndash": "\u2013", "rsquo": "\u2019", "lsquo": "\u2018",
        "ldquo": "\u201c", "rdquo": "\u201d", "hellip": "\u2026", "nbsp": " ",
        "times": "\u00d7", "deg": "\u00b0", "rupee": "\u20b9",
    }

    def named_repl(match: re.Match[str]) -> str:
        return named.get(match.group(1).lower(), match.group(0))

    value = re.sub(r"&([a-zA-Z]+);", named_repl, value)

    def numeric_repl(match: re.Match[str]) -> str:
        raw = match.group(1)
        try:
            code = int(raw[1:], 16) if raw[:1].lower() == "x" else int(raw)
        except ValueError:
            return match.group(0)
        return chr(code)

    return re.sub(r"&#(x?[0-9a-fA-F]+);", numeric_repl, value)


def visible(raw: str) -> str:
    return re.sub(r"\s+", " ", unescape(TAG_STRIP.sub(" ", raw))).strip()


def meta_content(text: str, *, name: Optional[str] = None, prop: Optional[str] = None) -> Optional[str]:
    key = "name" if name else "property"
    want = (name or prop or "").lower()
    for tag in META_RE.findall(text):
        got = (attr(tag, key) or "").lower()
        if got == want:
            return attr(tag, "content")
    return None


def link_hrefs(text: str, rel: str) -> List[str]:
    out: List[str] = []
    for tag in LINK_RE.findall(text):
        got = (attr(tag, "rel") or "").lower()
        if rel in got.split():
            out.append(attr(tag, "href") or "")
    return out


def html_pages() -> List[Path]:
    return sorted(PUBLIC.glob("*.html"))


def local_target(href: str, base: Path) -> Optional[Path]:
    """Map a site-relative href to a file on disk, or None when external.

    Extensionless URLs are resolved to the ``.html`` file the host serves for
    them, mirroring Cloudflare Pages' pretty-URL handling.
    """
    if not href:
        return None
    href = unescape(href).strip()
    if href.startswith(("mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")):
        return None
    parsed = urlparse(href)
    if parsed.scheme in ("http", "https"):
        if parsed.netloc not in (HOST, "urbanforestpark.com"):
            return None
        path = parsed.path
    elif parsed.scheme or href.startswith("//"):
        return None
    else:
        path = parsed.path
        if not path and not parsed.query and not parsed.fragment:
            return None
    path = path or "/"
    if path.endswith("/"):
        path += "index.html"
    target = PUBLIC / path.lstrip("/")
    if not target.exists() and not Path(path).suffix:
        pretty = PUBLIC / (path.lstrip("/") + ".html")
        if pretty.exists():
            return pretty
    return target


def load_json(path: Path) -> Optional[object]:
    try:
        return json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001 - report and continue
        return {"__error__": str(exc)}


def load_keyword_map() -> Dict[str, dict]:
    path = ROOT / "scripts" / "seo_keyword_map.json"
    data = json.loads(read_text(path))
    return {page["file"]: page for page in data["pages"]}


# --------------------------------------------------------------------------
# Group 1 - URL hygiene
# --------------------------------------------------------------------------

def group_1(pages: Dict[str, str], kmap: Dict[str, dict]) -> None:
    hosted = re.compile(r"https?://(?:www\.)?urbanforestpark\.com", re.I)
    for name, text in pages.items():
        if re.search(r"http://(?:www\.)?urbanforestpark\.com", text, re.I):
            error(1, f"{name}: contains an insecure http:// registry URL")

        canonical = meta_content(text, prop="og:url")
        link_canon = link_hrefs(text, "canonical")
        expected = kmap[name]["canonical"] if name in kmap else None
        if not link_canon:
            error(1, f"{name}: missing <link rel=\"canonical\">")
        elif len(link_canon) != 1:
            error(1, f"{name}: expected exactly one canonical, found {len(link_canon)}")
        elif link_canon[0] != expected:
            error(1, f"{name}: canonical {link_canon[0]!r} != keyword map {expected!r}")
        elif link_canon[0].endswith(".html"):
            error(1, f"{name}: canonical uses the redirecting .html form")

        if canonical and canonical != expected:
            error(1, f"{name}: og:url {canonical!r} != keyword map {expected!r}")

        for raw in re.findall(r"\"(?:url|@id|logo|image)\"\s*:\s*\"([^\"]+)\"", text):
            if raw.startswith("http://"):
                error(1, f"{name}: JSON-LD carries an insecure http:// URL: {raw}")
            if raw.startswith("https://urbanforestpark.com"):
                error(1, f"{name}: JSON-LD uses the non-www host: {raw}")

    sitemap = read_text(PUBLIC / "sitemap.xml")
    for loc in re.findall(r"<loc>([^<]+)</loc>", sitemap):
        if not loc.startswith(SITE):
            error(1, f"sitemap.xml: non-canonical location {loc}")

    robots = read_text(PUBLIC / "robots.txt")
    if f"Sitemap: {SITE}/sitemap.xml" not in robots:
        error(1, "robots.txt: sitemap declaration is missing or non-canonical")
    if re.search(r"http://", robots):
        error(1, "robots.txt: references an http:// URL")


# --------------------------------------------------------------------------
# Group 2 - Metadata, headings, images
# --------------------------------------------------------------------------

def group_2(pages: Dict[str, str], kmap: Dict[str, dict]) -> None:
    titles: Dict[str, str] = {}
    descs: Dict[str, str] = {}

    for name, text in pages.items():
        meta = kmap.get(name)
        if meta is None:
            warn(2, f"{name}: not present in the keyword map")
            continue

        title_match = re.search(r"<title\b[^>]*>(.*?)</title>", text, re.I | re.S)
        title = visible(title_match.group(1)) if title_match else ""
        desc = unescape(meta_content(text, name="description") or "").strip()

        if not title:
            error(2, f"{name}: missing <title>")
        else:
            if not (TITLE_MIN <= len(title) <= TITLE_MAX):
                error(2, f"{name}: title length {len(title)} outside {TITLE_MIN}-{TITLE_MAX}: {title!r}")
            if title != meta["title"]:
                error(2, f"{name}: title differs from keyword map")
            if title in titles:
                error(2, f"duplicate <title> shared by {titles[title]} and {name}: {title!r}")
            else:
                titles[title] = name

        if not desc:
            error(2, f"{name}: missing meta description")
        else:
            if not (DESC_MIN <= len(desc) <= DESC_MAX):
                error(2, f"{name}: description length {len(desc)} outside {DESC_MIN}-{DESC_MAX}")
            if desc != meta["description"]:
                error(2, f"{name}: description differs from keyword map")
            if desc in descs:
                error(2, f"duplicate meta description shared by {descs[desc]} and {name}")
            else:
                descs[desc] = name

        h1s = [visible(m.group(1)) for m in H1_RE.finditer(text)]
        if len(h1s) != 1:
            error(2, f"{name}: expected exactly one <h1>, found {len(h1s)}")
        elif h1s[0] != unescape(meta["h1"]).strip():
            error(2, f"{name}: H1 {h1s[0]!r} != keyword map {meta['h1']!r}")
        elif unescape(meta["primary_keyword"]).split(" & ")[0].lower() not in h1s[0].lower():
            warn(2, f"{name}: primary keyword not visible verbatim in the H1")

        levels = [int(m.group(1)) for m in HEADING_RE.finditer(text)]
        for prev, nxt in zip(levels, levels[1:]):
            if nxt > prev + 1:
                error(2, f"{name}: heading level jumps h{prev} -> h{nxt}")
                break

        for tag in IMG_RE.findall(text):
            src = attr(tag, "src") or "(no src)"
            alt = attr(tag, "alt")
            title_attr = attr(tag, "title")
            if alt is None or not visible(alt):
                error(2, f"{name}: image {src} has an empty or missing alt")
            if title_attr is None or not visible(title_attr):
                error(2, f"{name}: image {src} has an empty or missing title")
            for dim in ("width", "height"):
                val = attr(tag, dim)
                if not val or not val.strip().isdigit():
                    error(2, f"{name}: image {src} lacks an explicit {dim}")
            if not attr(tag, "loading"):
                error(2, f"{name}: image {src} lacks a loading attribute")
            if not attr(tag, "decoding"):
                error(2, f"{name}: image {src} lacks a decoding attribute")

    for title, name in titles.items():
        if not title:
            error(2, f"{name}: empty title after parsing")

    indexable = {n: m for n, m in kmap.items() if m.get("indexable")}
    for name, meta in indexable.items():
        text = pages.get(name, "")
        robots = (meta_content(text, name="robots") or "").lower()
        if "noindex" in robots:
            error(2, f"{name}: indexable page marked noindex")
    for name in NOINDEX_FILES:
        text = pages.get(name)
        if text is None:
            continue
        robots = (meta_content(text, name="robots") or "").lower()
        if "noindex" not in robots:
            error(2, f"{name}: error/utility page must carry noindex")


# --------------------------------------------------------------------------
# Group 3 - Crawl controls
# --------------------------------------------------------------------------

def group_3() -> None:
    robots = read_text(PUBLIC / "robots.txt")
    if "User-agent: *" not in robots:
        error(3, "robots.txt: missing the wildcard user-agent group")
    if "Allow: /" not in robots:
        error(3, "robots.txt: public pages are not allowed")
    if not re.search(r"Disallow: /admin-syndication", robots):
        error(3, "robots.txt: admin/syndication paths are not disallowed")
    if not re.search(r"Disallow: /syndication", robots):
        warn(3, "robots.txt: /syndication is not disallowed")

    sitemap = read_text(PUBLIC / "sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    if not locs:
        error(3, "sitemap.xml: no <loc> entries")
    if len(locs) != len(set(locs)):
        error(3, "sitemap.xml: duplicate <loc> entries")
    if any("?van=" in loc for loc in locs):
        error(3, "sitemap.xml: legacy ?van= URLs are still present")

    lastmods = re.findall(r"<lastmod>([^<]+)</lastmod>", sitemap)
    if lastmods and len(lastmods) < len(locs):
        error(3, "sitemap.xml: some <url> entries lack <lastmod>")
    for stamp in lastmods:
        try:
            datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
        except ValueError:
            error(3, f"sitemap.xml: invalid ISO lastmod {stamp!r}")

    for loc in locs:
        path = urlparse(loc).path
        rel = path.lstrip("/") or "index.html"
        if rel.endswith("/"):
            rel += "index.html"
        target = PUBLIC / rel
        if not target.exists() and "." not in path.rsplit("/", 1)[-1]:
            pretty = PUBLIC / (rel + ".html")
            if pretty.exists():
                target, rel = pretty, rel + ".html"
        if not target.exists():
            error(3, f"sitemap.xml: {loc} has no file on disk")
            continue
        if target.suffix == ".html":
            text = read_text(target)
            robots = (meta_content(text, name="robots") or "").lower()
            if "noindex" in robots:
                error(3, f"sitemap.xml: {rel} is noindex but still listed")
            canon = link_hrefs(text, "canonical")
            # Query-parameter routes (?job=, ?state=, ?category=, ?view=) are
            # expected to canonicalise to the clean page they resolve to.
            if canon and canon[0] != loc and canon[0] != loc.split("?", 1)[0]:
                error(3, f"sitemap.xml: {rel} canonical {canon[0]!r} != sitemap {loc!r}")
            if loc.endswith(".html"):
                error(3, f"sitemap.xml: redirecting .html URL listed: {loc}")

    for name in NOINDEX_FILES:
        rel = SITE + "/" + name
        if rel in locs:
            error(3, f"sitemap.xml: noindex page {name} is listed")

    if f"{SITE}/explore-dashboard" not in locs:
        error(3, "sitemap.xml: explore-dashboard is missing")
    if f"{SITE}/nagar-van-finder" not in locs:
        error(3, "sitemap.xml: nagar-van-finder is missing")


# --------------------------------------------------------------------------
# Group 4 - Structured data
# --------------------------------------------------------------------------

def schema_nodes(text: str) -> Tuple[List[dict], int]:
    nodes: List[dict] = []
    blocks = 0
    for raw in LD_RE.findall(text):
        blocks += 1
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON-LD ({exc})") from exc
        stack = [data]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                nodes.append(item)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
    return nodes, blocks


def types_in(nodes: List[dict]) -> Set[str]:
    found: Set[str] = set()
    for node in nodes:
        t = node.get("@type")
        if isinstance(t, str):
            found.add(t)
        elif isinstance(t, list):
            found.update(str(x) for x in t)
    return found


def group_4(pages: Dict[str, str]) -> None:
    required: Dict[str, Set[str]] = {
        "index.html": {"Organization", "WebSite", "ItemList"},
        "about.html": {"Organization", "AboutPage", "BreadcrumbList"},
        "404.html": {"BreadcrumbList"},
        "500.html": {"BreadcrumbList"},
    }
    for hub in HUB_FILES:
        required[hub] = {"BreadcrumbList", "FAQPage"}
    for form in ("hindi-environment-forestry-jobs.html", "bharat-regional-green-jobs.html",
                 "global-climate-sustainability-opportunities.html"):
        required[form] = {"BreadcrumbList", "FAQPage"}

    for name, text in pages.items():
        if not LD_RE.search(text):
            error(4, f"{name}: no JSON-LD block found")
            continue
        try:
            nodes, blocks = schema_nodes(text)
        except ValueError as exc:
            error(4, f"{name}: {exc}")
            continue
        info(f"{name}: {blocks} JSON-LD block(s), {len(nodes)} node(s)")
        found = types_in(nodes)
        for need in sorted(required.get(name, set())):
            if need not in found:
                error(4, f"{name}: missing {need} schema")

    jobs_js = read_text(PUBLIC / "js" / "jobs.js")
    for token in ("JobPosting", "BreadcrumbList", "WebPage", "canonical"):
        if token not in jobs_js:
            error(4, f"jobs.js: dynamic schema token {token!r} missing")

    org = None
    try:
        for node in schema_nodes(pages["index.html"])[0]:
            if node.get("@type") == "Organization":
                org = node
                break
    except (KeyError, ValueError):
        org = None
    if org is None:
        error(4, "index.html: Organization schema unavailable for inspection")
    else:
        for field in ("name", "url", "logo", "sameAs", "contactPoint"):
            if not org.get(field):
                warn(4, f"index.html: Organization.{field} is empty")


# --------------------------------------------------------------------------
# Group 5 - International targeting
# --------------------------------------------------------------------------

def group_5(pages: Dict[str, str]) -> None:
    """Every language page must publish the same reciprocal hreflang cluster."""
    canonical_cluster = {
        "en-IN": SITE + "/",
        "hi-IN": SITE + "/hindi-environment-forestry-jobs",
        "en": SITE + "/global-climate-sustainability-opportunities",
        "x-default": SITE + "/",
    }
    doc_lang = {
        "index.html": "en-IN",
        "hindi-environment-forestry-jobs.html": "hi-IN",
        "bharat-regional-green-jobs.html": "en-IN",
        "global-climate-sustainability-opportunities.html": "en",
    }
    for name in LANGUAGE_PAGES:
        text = pages.get(name)
        if text is None:
            error(5, f"{name}: missing")
            continue
        html_tag = re.search(r"<html\b[^>]*>", text, re.I)
        lang = attr(html_tag.group(0), "lang") if html_tag else None
        if lang != doc_lang[name]:
            error(5, f"{name}: <html lang> is {lang!r}, expected {doc_lang[name]!r}")

        cluster: Dict[str, str] = {}
        for tag in LINK_RE.findall(text):
            if "alternate" in (attr(tag, "rel") or "").lower():
                code = attr(tag, "hreflang")
                if code:
                    cluster[code] = unescape(attr(tag, "href") or "")
        if set(cluster) != set(canonical_cluster):
            error(5, f"{name}: hreflang set {sorted(cluster)} != {sorted(canonical_cluster)}")
        for code, url in canonical_cluster.items():
            if code in cluster and cluster[code] != url:
                error(5, f"{name}: hreflang={code} points at {cluster[code]!r}, expected {url!r}")


# --------------------------------------------------------------------------
# Group 6 - Internal linking and crawl reachability
# --------------------------------------------------------------------------

def group_6(pages: Dict[str, str], kmap: Dict[str, dict]) -> None:
    broken: List[str] = []
    html_links: List[str] = []
    graph: Dict[str, Set[str]] = {name: set() for name in pages}

    for name, text in pages.items():
        for href in re.findall(r"\bhref=[\"']([^\"']+)[\"']", text):
            raw = unescape(href)
            parsed = urlparse(raw)
            internal = parsed.netloc in ("", HOST, "urbanforestpark.com")
            if internal and parsed.path.endswith(".html") and not parsed.path.endswith("/index.html"):
                html_links.append(f"{name} -> {raw}")
            target = local_target(href, PUBLIC)
            if target is None:
                continue
            if not target.exists():
                broken.append(f"{name} -> {unescape(href)}")
                continue
            if target.suffix == ".html":
                graph[name].add(target.name)
            if unescape(href).startswith("/") and target.suffix != ".html":
                pass

    for tag in IMG_RE.findall("".join(pages.values())):
        src = attr(tag, "src") or ""
        if src.startswith("data:"):
            continue
        target = local_target(src, PUBLIC)
        if target is None:
            continue
        if not target.exists():
            broken.append(f"image {src}")

    for item in sorted(set(broken)):
        error(6, f"broken internal reference: {item}")

    html_links = sorted(set(html_links))
    if html_links:
        sample = "; ".join(html_links[:5])
        error(
            6,
            f"{len(html_links)} internal link(s) use the redirecting .html form: {sample}",
        )

    indexable = {n for n, m in kmap.items() if m.get("indexable")}
    depth = {name: 0 for name in graph if name == "index.html"}
    queue = deque(["index.html"])
    while queue:
        current = queue.popleft()
        for nxt in sorted(graph.get(current, ())):
            if nxt in depth:
                continue
            depth[nxt] = depth[current] + 1
            queue.append(nxt)

    for name in sorted(indexable):
        if name not in depth:
            error(6, f"{name}: indexable page is orphaned (unreachable from /)")
        elif depth[name] > 2:
            error(6, f"{name}: crawl depth {depth[name]} exceeds 2")
        else:
            info(f"{name}: crawl depth {depth[name]}")

    for name in MATRIX_FILES:
        text = pages.get(name)
        if text is None:
            continue
        if "National &amp; Global Career Pathways &amp; Research Hubs" not in text and \
                "National & Global Career Pathways & Research Hubs" not in text:
            error(6, f"{name}: site matrix section is missing")

    # India state gateways belong on India-facing surfaces only; the global hub
    # is an international landing page and must stay free of ?state= filtering.
    if 'href="/?state=' in pages.get("global-climate-sustainability-opportunities.html", ""):
        error(6, "global hub must not carry India state gateways")
    for name in ["index.html", *HUB_FILES,
                 "hindi-environment-forestry-jobs.html",
                 "bharat-regional-green-jobs.html"]:
        if not any(f'href="{href}"' in pages.get(name, "") for _, href in TOP_STATE_HREFS):
            warn(6, f"{name}: no contextual state gateway links found")

    hub_crumbs = re.compile(r"class=\"hub-crumbs\"", re.I)
    for name in HUB_FILES:
        text = pages.get(name, "")
        if not hub_crumbs.search(text):
            warn(6, f"{name}: visible breadcrumb navigation not found")
    if "breadcrumb" not in read_text(PUBLIC / "js" / "jobs.js").lower():
        error(6, "jobs.js: dossier breadcrumbs missing")


# --------------------------------------------------------------------------
# Group 7 - Delivery: headers, weight, favicons, confidential gate
# --------------------------------------------------------------------------

def group_7(pages: Dict[str, str]) -> None:
    headers = read_text(PUBLIC / "_headers")
    checks = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=",
    }
    for header, needle in checks.items():
        if header not in headers or needle not in headers:
            error(7, f"_headers: missing {header} policy")
    if "immutable" not in headers:
        error(7, "_headers: versioned assets are not immutable")
    if not re.search(r"Cache-Control: public, max-age=\d+", headers):
        error(7, "_headers: HTML/JSON cache lifetime is not declared")

    logo = PUBLIC / "assets" / "images" / "Logo_UFF.png"
    if not logo.exists():
        error(7, "Logo_UFF.png is missing")
    elif logo.stat().st_size > 70 * 1024:
        error(7, f"Logo_UFF.png is {logo.stat().st_size} bytes (limit 71680)")

    favicons = ["/favicon-16x16.png", "/favicon-32x32.png", "/favicon.ico",
                "/favicon.svg", "/apple-touch-icon.png"]
    for asset in favicons:
        if not (PUBLIC / asset.lstrip("/")).exists():
            error(7, f"missing favicon asset {asset}")

    for name, text in pages.items():
        head = text[: text.lower().find("</head>") + 7] if "</head>" in text.lower() else text
        for asset in favicons:
            if asset not in head:
                error(7, f"{name}: head does not link {asset}")

    for name, text in pages.items():
        if "meta-theme-color" in text:
            tag = re.search(r'<meta\b[^>]*name=["\']theme-color["\'][^>]*>', text, re.I)
            if not tag or "meta-theme-color" not in tag.group(0):
                error(7, f"{name}: night-mode script needs id=\"meta-theme-color\" on the theme-color meta")

    for name, text in pages.items():
        for tag in IMG_RE.findall(text):
            if "ufp-header-logo" not in (attr(tag, "class") or ""):
                continue
            if (attr(tag, "width"), attr(tag, "height")) != ("48", "48"):
                error(7, f"{name}: header logo must be 48x48, got {attr(tag, 'width')}x{attr(tag, 'height')}")
            if "fetchpriority" not in tag.lower():
                error(7, f"{name}: header logo lacks fetchpriority")
            if not attr(tag, "alt"):
                error(7, f"{name}: header logo lacks alt text")

    gate = read_text(ROOT / "scripts" / "fetch_and_humanize.py")
    if "BLOCKED_ORG_TERMS" not in gate or "has_blocked_organization" not in gate:
        error(7, "confidential-employer gate is missing from the registry pipeline")
    else:
        for term in ("confidential", "undisclosed", "unknown"):
            if term not in gate:
                error(7, f"confidential gate no longer blocks {term!r}")

    for data_file in ("jobs.json", "archive.json", "global_jobs.json", "global_archive.json"):
        path = PUBLIC / data_file
        if not path.exists():
            warn(7, f"{data_file}: not present, skipped the employer scan")
            continue
        payload = load_json(path)
        if isinstance(payload, dict) and "__error__" in payload:
            error(7, f"{data_file}: invalid JSON ({payload['__error__']})")
            continue
        records = payload if isinstance(payload, list) else payload.get("jobs", []) if isinstance(payload, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            org = str(record.get("organization", "")).casefold()
            for term in ("confidential", "undisclosed", "unknown"):
                if term in org:
                    error(7, f"{data_file}: published an anonymous employer {record.get('organization')!r}")
                    break


# --------------------------------------------------------------------------

def main() -> int:
    pages = {path.name: read_text(path) for path in html_pages()}
    if not pages:
        print("no HTML pages found under public/")
        return 2

    kmap = load_keyword_map()
    info(f"audited {len(pages)} HTML page(s) against {len(kmap)} keyword-map entries")

    group_1(pages, kmap)
    group_2(pages, kmap)
    group_3()
    group_4(pages)
    group_5(pages)
    group_6(pages, kmap)
    group_7(pages)

    print("=" * 78)
    print("SEO checklist audit - Urban Forest Park")
    print("=" * 78)
    for line in ERRORS:
        print(line)
    for line in WARNINGS:
        print(line)
    print("-" * 78)
    print(f"pages={len(pages)}  errors={len(ERRORS)}  warnings={len(WARNINGS)}")
    if "--verbose" in sys.argv:
        for line in INFO:
            print("  " + line)
    return 1 if ERRORS else 0


if __name__ == "__main__":
    sys.exit(main())
