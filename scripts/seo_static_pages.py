#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Institutional static-page surface for Urban Forest Park.

This module is imported lazily by :mod:`build_seo_pages`. It owns:

* the About / governance page,
* the institutional 404 and 500 pages,
* head-metadata normalisation for legacy static pages, and
* the compact site-directory links that keep every page within two clicks
  of the homepage.

All titles, descriptions and primary keywords come from
``scripts/seo_keyword_map.json`` so there is exactly one source of truth.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import build_seo_pages as bsp

GENERATED_PAGES = {
    "jrf-srf-project-associate-jobs.html",
    "phd-fellowships-climate-sustainability.html",
    "forestry-wildlife-government-jobs.html",
    "gis-remote-sensing-climate-jobs.html",
    "esg-carbon-sustainability-jobs.html",
    "hindi-environment-forestry-jobs.html",
    "bharat-regional-green-jobs.html",
    "global-climate-sustainability-opportunities.html",
}

# Pages that carry their own full matrix in the generated body.
NO_COMPACT_MATRIX = GENERATED_PAGES | {"index.html", "about.html", "404.html", "500.html"}

FULL_CLUSTER_PAGES = {
    "index.html": ("en-IN", bsp.SITE + "/"),
    "hindi-environment-forestry-jobs.html": ("hi-IN", bsp.SITE + "/hindi-environment-forestry-jobs.html"),
    "bharat-regional-green-jobs.html": ("en-IN", bsp.SITE + "/bharat-regional-green-jobs.html"),
    "global-climate-sustainability-opportunities.html": ("en", bsp.SITE + "/global-climate-sustainability-opportunities.html"),
}

SITE_MATRIX_START = "<!-- SITE_MATRIX_START -->"
SITE_MATRIX_END = "<!-- SITE_MATRIX_END -->"
LEGACY_MATRIX_START = "<!-- UFP_SITE_MATRIX_START -->"
LEGACY_MATRIX_END = "<!-- UFP_SITE_MATRIX_END -->"


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def _text(value: Any) -> str:
    return html.escape(str(value or ""), quote=False)


def _drop(text: str, pattern: str) -> str:
    return re.sub(pattern, "", text, flags=re.I | re.S)


def _head_block(file_name: str, meta: Dict[str, Any]) -> str:
    title = _text(meta.get("title"))
    desc = _text(meta.get("description"))
    canonical = _text(meta.get("canonical"))
    indexable = bool(meta.get("indexable"))
    robots = (
        "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
        if indexable
        else "noindex, follow"
    )
    if file_name in FULL_CLUSTER_PAGES:
        cluster = [
            ("en-IN", bsp.SITE + "/"),
            ("hi-IN", bsp.SITE + "/hindi-environment-forestry-jobs.html"),
            ("en", bsp.SITE + "/global-climate-sustainability-opportunities.html"),
            ("x-default", bsp.SITE + "/"),
        ]
    else:
        cluster = [("en-IN", canonical), ("x-default", canonical)]
    alternates = "\n".join(
        f'    <link rel="alternate" hreflang="{code}" href="{_esc(url)}" />'
        for code, url in cluster
    )
    locale = "hi_IN" if file_name == "hindi-environment-forestry-jobs.html" else "en_IN"
    image_alt = _esc(bsp.BRAND_ALT)
    slug_hint = file_name.removesuffix(".html").casefold()
    if any(
        hint in slug_hint
        for hint in (
            "jobs",
            "opportunities",
            "fellowships",
            "workshops",
            "conferences",
            "webinars",
            "programs",
            "memberships",
            "careers",
        )
    ):
        og_image = bsp.discover_image_for_hub(
            {"canonical": canonical, "title": title, "h1": ""}
        )
        og_width, og_height = bsp.DISCOVER_IMAGE_WIDTH, bsp.DISCOVER_IMAGE_HEIGHT
    else:
        og_image, og_width, og_height = bsp.LOGO_URL, 512, 512
    return f"""    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="robots" content="{robots}">
    <link rel="canonical" href="{canonical}">
{alternates}
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park">
    <meta property="og:locale" content="{locale}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{_esc(og_image)}">
    <meta property="og:image:width" content="{og_width}">
    <meta property="og:image:height" content="{og_height}">
    <meta property="og:image:alt" content="{image_alt}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{desc}">
    <meta name="twitter:image" content="{_esc(og_image)}">
    <meta name="theme-color" content="#F8FAFC">
{bsp.FAVICONS}"""


def _normalise_head(file_name: str, text: str, meta: Dict[str, Any]) -> str:
    """Replace only the SEO head fields, preserving scripts and custom meta."""
    head_match = re.search(r"<head\b[^>]*>(.*?)</head>", text, re.I | re.S)
    if not head_match:
        return text
    head = head_match.group(1)

    desc_id = ""
    m = re.search(r"<meta\b[^>]*name=[\"']description[\"'][^>]*>", head, re.I)
    if m and re.search(r"\bid=[\"']meta-desc[\"']", m.group(0), re.I):
        desc_id = ' id="meta-desc"'

    # The night-mode toggle in jobs.js/hub.js and the inline legal-page scripts
    # look up #meta-theme-color, so the id must survive head normalisation.
    theme_id = ""
    m = re.search(r"<meta\b[^>]*name=[\"']theme-color[\"'][^>]*>", head, re.I)
    if m:
        id_match = re.search(r"\bid=[\"']([^\"']+)[\"']", m.group(0), re.I)
        if id_match:
            theme_id = f' id="{id_match.group(1)}"'

    # Drop every field this normaliser owns, then append one canonical block.
    head = _drop(head, r"<title\b[^>]*>.*?</title>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']description[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']robots[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']theme-color[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']apple-mobile-web-app-title[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*property=[\"']og:[^\"']+[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']twitter:[^\"']+[\"'][^>]*>\s*")
    head = _drop(head, r"<link\b[^>]*rel=[\"'][^\"']*canonical[^\"']*[\"'][^>]*>\s*")
    head = _drop(head, r"<link\b[^>]*hreflang=[^>]*>\s*")
    head = _drop(head, r"<link\b[^>]*rel=[\"'][^\"']*(?:icon|manifest|apple-touch-icon|mask-icon)[^\"']*[\"'][^>]*>\s*")
    head = _drop(head, r"<meta\b[^>]*name=[\"']theme-color[\"'][^>]*>\s*")

    # Ensure charset/viewport survive on hand-written email/tool templates.
    if not re.search(r"<meta\b[^>]*charset=", head, re.I):
        head = '\n    <meta charset="UTF-8">' + head
    if not re.search(r"<meta\b[^>]*name=[\"']viewport[\"']", head, re.I):
        head = '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">' + head

    block = _head_block(file_name, meta)
    if desc_id:
        block = block.replace(
            '<meta name="description" content="',
            f'<meta name="description"{desc_id} content="',
            1,
        )
    if theme_id:
        block = block.replace(
            '<meta name="theme-color" content="',
            f'<meta name="theme-color"{theme_id} content="',
            1,
        )
    head = head.rstrip() + "\n" + block + "\n  "
    return text[: head_match.start(1)] + head + text[head_match.end(1) :]


def _normalise_lang(file_name: str, text: str) -> str:
    if file_name == "hindi-environment-forestry-jobs.html":
        lang = "hi-IN"
    elif file_name == "global-climate-sustainability-opportunities.html":
        lang = "en"
    else:
        lang = "en-IN"
    m = re.search(r"<html\b([^>]*)>", text, re.I)
    if not m:
        return text
    attrs = re.sub(r"\blang=[\"'][^\"']*[\"']", "", m.group(1), flags=re.I).strip()
    replacement = f"<html {attrs} lang=\"{lang}\">" if attrs else f"<html lang=\"{lang}\">"
    return text[: m.start()] + replacement + text[m.end() :]


def _insert_full_matrix(text: str, current_path: str) -> str:
    block = bsp.site_matrix_html(current_path)
    marked = re.compile(
        re.escape(SITE_MATRIX_START) + r".*?" + re.escape(SITE_MATRIX_END),
        re.I | re.S,
    )
    payload = f"{SITE_MATRIX_START}\n{block}\n{SITE_MATRIX_END}"
    if marked.search(text):
        return marked.sub(payload, text, count=1)
    m = re.search(r"\n?\s*<footer\b", text, re.I)
    if m:
        return text[: m.start()] + "\n" + payload + "\n" + text[m.start() :]
    return text.replace("</body>", payload + "\n</body>", 1)


def _insert_compact_matrix(text: str, current_path: str) -> str:
    block = bsp.compact_site_matrix_html(current_path)
    marked = re.compile(
        re.escape(LEGACY_MATRIX_START) + r".*?" + re.escape(LEGACY_MATRIX_END),
        re.I | re.S,
    )
    payload = f"{LEGACY_MATRIX_START}\n{block}\n{LEGACY_MATRIX_END}"
    if marked.search(text):
        return marked.sub(payload, text, count=1)
    m = re.search(r"\n?\s*<footer\b", text, re.I)
    if m:
        return text[: m.start()] + "\n" + payload + "\n" + text[m.start() :]
    return text.replace("</body>", payload + "\n</body>", 1)




# ---------------------------------------------------------------------------
# Body-level normalisation for legacy static pages
# ---------------------------------------------------------------------------
_PROTECTED_RE = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>)", re.I | re.S)
_HEADING_RE = re.compile(r"<h([1-6])\b([^>]*)>(.*?)</h\1>", re.I | re.S)
_IMG_RE = re.compile(r"<img\b[^>]*>", re.I)


def _insert_heading_banner(text: str, h1: str) -> str:
    body = re.search(r"<body\b[^>]*>", text, re.I)
    if not body:
        return text
    banner = (
        '\n<header class="seo-page-banner" style="padding:18px 20px;background:#F8FAFC;'
        'border-bottom:1px solid #E2E8F0;"><h1 style="max-width:1240px;margin:0 auto;'
        'font:600 clamp(21px,3vw,28px)/1.25 Georgia,serif;color:#0F172A;">'
        + _text(h1)
        + "</h1></header>\n"
    )
    return text[: body.end()] + banner + text[body.end() :]


def _normalise_headings(text: str, meta: Dict[str, Any]) -> str:
    segments = _PROTECTED_RE.split(text)
    h1_count = sum(len(re.findall(r"<h1\b", seg, re.I)) for i, seg in enumerate(segments) if i % 2 == 0)
    if h1_count == 0:
        text = _insert_heading_banner(text, str(meta.get("h1") or meta.get("title") or "Urban Forest Park"))
        segments = _PROTECTED_RE.split(text)

    state = {"prev": 0, "seen": 0}

    def repl(match: re.Match[str]) -> str:
        level = int(match.group(1))
        attrs = match.group(2)
        content = match.group(3)
        if state["seen"] == 0:
            if level != 1:
                level = 1
            state["seen"] = 1
        else:
            if level == 1:
                level = 2
            level = min(level, state["prev"] + 1)
            level = max(level, 2)
        state["prev"] = level
        return f"<h{level}{attrs}>{content}</h{level}>"

    out: List[str] = []
    for index, segment in enumerate(segments):
        if index % 2:
            out.append(segment)
        else:
            out.append(_HEADING_RE.sub(repl, segment))
    return "".join(out)


def _img_attr(attrs: str, name: str) -> Optional[str]:
    m = re.search(r"\b" + re.escape(name) + r"\s*=\s*([\"'])(.*?)\1", attrs, re.I | re.S)
    return m.group(2) if m else None


def _set_img_attr(tag: str, name: str, value: str) -> str:
    pattern = re.compile(r"(\b" + re.escape(name) + r"\s*=\s*)([\"']).*?\2", re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(lambda m: m.group(1) + '"' + value + '"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{value}">'


def _normalise_images(text: str) -> str:
    segments = _PROTECTED_RE.split(text)
    out: List[str] = []
    for index, segment in enumerate(segments):
        if index % 2:
            out.append(segment)
            continue

        def repl(match: re.Match[str]) -> str:
            tag = match.group(0)
            attrs = tag
            src = _img_attr(attrs, "src") or ""
            cls = _img_attr(attrs, "class") or ""
            alt = _img_attr(attrs, "alt") or ""
            title = _img_attr(attrs, "title") or ""
            if "Logo_UFF" in src:
                if "ufp-header-logo" in cls:
                    alt = getattr(bsp, "BRAND_ALT_HTML", bsp.BRAND_ALT)
                    title = bsp.BRAND_TITLE
                    width, height = "48", "48"
                else:
                    alt = alt or "Urban Forest Park app emblem"
                    title = title or "Urban Forest Park app emblem"
                    width, height = ("34", "34") if "uaw-logo" in cls else ("48", "48")
            elif "Nagar_Van_Logo" in src:
                alt = alt or "Nagar Van Yojana dMRV emblem"
                title = title or "Nagar Van Yojana Digital Monitoring, Reporting and Verification Emblem"
                width, height = "2000", "2000"
            elif "arkraj-biswas-portrait" in src:
                alt = alt or "Portrait of Arkraj Biswas, founder and editorial lead of Urban Forest Park"
                title = title or "Arkraj Biswas, Founder and Editorial Lead"
                width, height = "586", "626"
            elif "favicon" in src:
                alt = alt or "Urban Forest Park emblem"
                title = title or "Urban Forest Park emblem"
                width, height = "96", "96"
            else:
                alt = alt or "Urban Forest Park institutional image"
                title = title or alt
                width, height = "96", "96"
            if not alt:
                alt = "Urban Forest Park institutional image"
            if not title:
                title = alt
            tag = _set_img_attr(tag, "alt", alt)
            tag = _set_img_attr(tag, "title", title)
            if not _img_attr(tag, "width"):
                tag = _set_img_attr(tag, "width", width)
            if not _img_attr(tag, "height"):
                tag = _set_img_attr(tag, "height", height)
            if not _img_attr(tag, "loading"):
                tag = _set_img_attr(tag, "loading", "lazy")
            if not _img_attr(tag, "decoding"):
                tag = _set_img_attr(tag, "decoding", "async")
            if "ufp-header-logo" in cls and not _img_attr(tag, "fetchpriority"):
                tag = _set_img_attr(tag, "fetchpriority", "high")
            return tag

        out.append(_IMG_RE.sub(repl, segment))
    return "".join(out)


FEED_JSONLD_RE = re.compile(
    r'<script type="application/ld\+json" id="feed-jobs-jsonld">.*?</script>',
    re.S,
)


def _ensure_index_item_list(text: str, public: Path) -> str:
    """Expose a static ItemList of the live jobs on the homepage.

    Regenerated on every SEO build (not append-only): quarantined records and
    records whose entry type is unknown must never appear in JSON-LD. jobs.js
    checks for the same ``feed-jobs-jsonld`` id, so the runtime feed schema
    never duplicates this crawlable snapshot.
    """
    jobs_path = public / "jobs.json"
    if not jobs_path.exists():
        return text
    try:
        jobs = json.loads(jobs_path.read_text(encoding="utf-8"))
    except Exception:
        return text
    if not isinstance(jobs, list):
        return text
    publishable = [
        job
        for job in jobs
        if isinstance(job, dict)
        and job.get("status") != "quarantined"
        and str(job.get("entry_type") or "posting") != "unknown"
    ]
    entries = []
    for index, job in enumerate(publishable[:20], start=1):
        entries.append(
            {
                "@type": "ListItem",
                "position": index,
                "name": str(job.get("clean_title") or "")
                + " \u2014 "
                + str(job.get("organization") or ""),
                "url": bsp.SITE + "/jobs/" + str(job.get("id") or ""),
            }
        )
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Active environmental, forestry, JRF and ESG jobs in India \u2014 Climate, Forestry, ESG & GIS",
        "numberOfItems": len(entries),
        "itemListElement": entries,
    }
    script = bsp.jsonld_script(payload).replace(
        '<script type="application/ld+json">',
        '<script type="application/ld+json" id="feed-jobs-jsonld">',
        1,
    )
    if FEED_JSONLD_RE.search(text):
        return FEED_JSONLD_RE.sub(lambda _match: script, text, count=1)
    return text.replace("</head>", script + "\n</head>", 1)


def normalise_static_pages(public: Path) -> None:
    """Apply the keyword map and crawlable directory to legacy pages."""
    for file_name, meta in bsp.KEYWORD_MAP.items():
        if file_name in GENERATED_PAGES:
            continue
        path = public / file_name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        text = _normalise_lang(file_name, text)
        text = _normalise_head(file_name, text, meta)
        current_path = "/" if file_name == "index.html" else "/" + file_name
        if file_name == "index.html":
            text = _insert_full_matrix(text, current_path)
            text = _ensure_index_item_list(text, public)
        elif file_name not in NO_COMPACT_MATRIX:
            text = _insert_compact_matrix(text, current_path)
        text = _normalise_headings(text, meta)
        text = _normalise_images(text)
        # Every indexable/institutional page should expose the same publisher
        # and site identity, even when the page predates the schema rollout.
        if '"@type": "Organization"' not in text:
            text = text.replace("</head>", bsp.organization_jsonld() + "\n</head>", 1)
        if '"@type": "WebSite"' not in text:
            text = text.replace("</head>", bsp.website_jsonld() + "\n</head>", 1)
        path.write_text(text, encoding="utf-8")


def write_keyword_map(public: Path) -> None:
    public.mkdir(parents=True, exist_ok=True)
    payload = bsp.KEYWORD_MAP_PATH.read_text(encoding="utf-8")
    (public / "seo_keyword_map.json").write_text(payload, encoding="utf-8")


def _page_shell(
    file_name: str,
    meta: Dict[str, Any],
    body: str,
    jsonld_blocks: Iterable[str],
    *,
    body_class: str = "",
) -> str:
    body_attr = f' class="{body_class}"' if body_class else ""
    ld = "\n".join(jsonld_blocks)
    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_text(meta['title'])}</title>
    <meta name="description" content="{_text(meta['description'])}">
    <meta name="robots" content="{'index, follow' if meta.get('indexable') else 'noindex, follow'}">
    <link rel="canonical" href="{_esc(meta['canonical'])}">
    <link rel="alternate" hreflang="en-IN" href="{_esc(meta['canonical'])}" />
    <link rel="alternate" hreflang="x-default" href="{_esc(meta['canonical'])}" />
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park">
    <meta property="og:locale" content="en_IN">
    <meta property="og:title" content="{_text(meta['title'])}">
    <meta property="og:description" content="{_text(meta['description'])}">
    <meta property="og:url" content="{_esc(meta['canonical'])}">
    <meta property="og:image" content="{_esc(bsp.LOGO_URL)}">
    <meta property="og:image:width" content="512">
    <meta property="og:image:height" content="512">
    <meta property="og:image:alt" content="{_esc(bsp.BRAND_ALT)}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{_text(meta['title'])}">
    <meta name="twitter:description" content="{_text(meta['description'])}">
    <meta name="twitter:image" content="{_esc(bsp.LOGO_URL)}">
    <meta name="theme-color" content="#F8FAFC">
{bsp.FAVICONS}
{bsp.FONTS}
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">
{ld}
</head>
<body{body_attr}>
  <a class="skip-link" href="#main-content">Skip to main content</a>
{bsp.header_html('registry')}
{body}
  <script defer src="/js/consent.js"></script>
  <script defer src="/js/back-to-top.js"></script>
  <script defer src="/js/syndication-drawer.js?v=20261023-1"></script>
</body>
</html>
"""


def build_about_page(today: date) -> str:
    meta = bsp.page_meta("about.html")
    date_text = bsp.long_date(today)
    about_ld = bsp.jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": bsp.SITE + "/about.html#webpage",
            "url": bsp.SITE + "/about.html",
            "name": meta["title"],
            "description": meta["description"],
            "isPartOf": {"@id": bsp.SITE + "/#website"},
            "about": {"@id": bsp.SITE + "/#organization"},
            "mainEntity": {"@id": bsp.SITE + "/#organization"},
            "breadcrumb": {"@id": bsp.SITE + "/about.html#breadcrumb"},
            "inLanguage": "en-IN",
            "dateModified": today.isoformat(),
            "citation": (
                "Urban Forest Park. (2026). National Climate, Forestry, ESG & "
                "Geospatial Career Registry (India). https://www.urbanforestpark.com/"
            ),
        }
    )
    person_ld = bsp.jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "Person",
            "@id": bsp.SITE + "/about.html#arkraj-biswas",
            "name": "Arkraj Biswas",
            "jobTitle": "Founder & Editorial Lead",
            "worksFor": {"@id": bsp.SITE + "/#organization"},
            "image": bsp.SITE + "/assets/images/arkraj-biswas-portrait.jpg",
            "description": (
                "Environmental and sustainable development professional leading the "
                "editorial verification and institutional governance of Urban Forest Park."
            ),
            "alumniOf": [
                {"@type": "CollegeOrUniversity", "name": "Banaras Hindu University"},
                {"@type": "CollegeOrUniversity", "name": "University of Agricultural Sciences, Dharwad"},
            ],
            "knowsAbout": [
                "Environmental science",
                "Sustainable development",
                "Urban forestry",
                "Geospatial dMRV",
                "Environmental law and policy",
                "Climate careers",
            ],
        }
    )
    breadcrumb_ld = bsp.breadcrumb_jsonld("About & Editorial Governance", bsp.SITE + "/about.html")
    body = f"""  <main id="main-content" class="about-main">
    <section class="hub-hero about-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">Career Registry</a><span aria-hidden="true">/</span><span>About &amp; Governance</span>
        </nav>
        <p class="eyebrow">Institutional Governance</p>
        <h1>About Urban Forest Park &mdash; Institutional Governance &amp; Editorial Verification</h1>
        <p class="hub-hero-sub">
          Urban Forest Park is an independent public-interest registry for climate, forestry,
          ESG, geospatial and academic careers in India, and the home of the Nagar Van dMRV
          Dashboard and Green Calculator. We publish vacancies only after source, deadline and
          application-link checks, and we never accept payment for inclusion.
        </p>
        <dl class="hub-stats about-meta">
          <div><dt>Editorial lead</dt><dd>Arkraj Biswas</dd></div>
          <div><dt>Last reviewed</dt><dd>{_text(date_text)}</dd></div>
          <div><dt>Contact</dt><dd><a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a></dd></div>
        </dl>
      </div>
    </section>

    <section class="hub-main">
      <div class="hub-main-inner about-copy">
        <h2>Our mission</h2>
        <p>
          India's climate transition depends on people being able to find credible, timely
          opportunities in forestry, conservation, environmental science, sustainability,
          geospatial analysis and academic research. Urban Forest Park exists to make that
          search transparent. Every active and archived job is presented with its
          organisation, state, position type, deadline and a direct link to the official
          application page &mdash; no application fees and no sponsored
          ranking.
        </p>

        <h2 id="verification">Editorial &amp; research verification methodology</h2>
        <p>
          Our workflow combines automated source monitoring with human review. The standard
          below applies to every registry record, including historical archive entries and
          international opportunities.
        </p>
        <ol class="about-steps">
          <li>
            <h3>1. Source discovery</h3>
            <p>We monitor official government portals, university and institute recruitment pages, public-sector notices, verified feeds and institutional announcements. A record is never created from an unattributed social-media post or a third-party job aggregator alone.</p>
          </li>
          <li>
            <h3>2. Normalisation &amp; duplicate control</h3>
            <p>Title, organisation, location, position type, deadline, compensation and application URL are normalised into a consistent schema. Duplicate notices, expired windows and records without a resolvable official application link are rejected.</p>
          </li>
          <li>
            <h3>3. Human editorial review</h3>
            <p>The editorial lead checks the source page, confirms the application destination and reviews the summary for accuracy and tone. Confidential, undisclosed and unknown employers are blocked from publication by policy. Listings that cannot be verified are held back rather than published speculatively.</p>
          </li>
          <li>
            <h3>4. Publication, monitoring &amp; correction</h3>
            <p>Active jobs are refreshed daily. Expired jobs move to the public archive rather than disappearing. Corrections can be submitted through the <a href="/report.html">issue-reporting form</a>; we aim to acknowledge substantive corrections within two business days.</p>
          </li>
        </ol>

        <h2>Domain expertise behind the registry</h2>
        <div class="about-grid">
          <article class="about-card">
            <h3>Environmental &amp; earth sciences</h3>
            <p>Editorial review is grounded in environmental and sustainable development training, with attention to ecology, climate policy and evidence quality.</p>
          </article>
          <article class="about-card">
            <h3>Geospatial dMRV &amp; remote sensing</h3>
            <p>The Nagar Van dashboard and Green Calculator translate satellite, field and survey data into readable urban-forest indicators, with clear source notes and limitations.</p>
          </article>
          <article class="about-card">
            <h3>Urban forestry &amp; heat-island mitigation</h3>
            <p>We prioritise jobs and research that connect plantation, maintenance and community outcomes to measurable cooling, carbon and biodiversity benefits.</p>
          </article>
          <article class="about-card">
            <h3>Environmental law &amp; public policy</h3>
            <p>Policy and legal context is reviewed against Indian environmental governance, including Nagar Van Yojana, CAMPA and national climate commitments.</p>
          </article>
        </div>

        <h2>Founder &amp; editorial lead</h2>
        <div class="about-person">
          <img src="/assets/images/arkraj-biswas-portrait.jpg"
               alt="Portrait of Arkraj Biswas, founder and editorial lead of Urban Forest Park"
               title="Arkraj Biswas, Founder and Editorial Lead"
               width="586" height="626" loading="lazy" decoding="async">
          <div>
            <h3>Arkraj Biswas</h3>
            <p class="about-role">Director &ndash; Sustainability, EcoServe Development Foundation; Embark India Development Fellow at National CAMPA (MoEF&amp;CC).</p>
            <h3>Academic &amp; professional background</h3>
            <p>
              Arkraj holds a Master of Science in Environmental &amp; Sustainable Development
              (Earth &amp; Atmospheric Sciences) from Banaras Hindu University and a Bachelor
              of Science in Agricultural Sciences from UAS Dharwad. He is pursuing a Post
              Graduate Diploma in Environmental Law and Policy from WWF-India and National Law
              University, Delhi.
            </p>
            <h3>Vision for a Viksit Bharat</h3>
            <p>
              India's Nationally Determined Contributions require decentralised, data-driven
              action. Nagar Vans and Nagar Vatikas can create carbon sinks, reduce the urban
              heat-island effect and strengthen community resilience. This platform is built
              so that a park visitor, a researcher and a policymaker can all use the same
              transparent evidence base.
            </p>
          </div>
        </div>

        <h2>Institutional contact &amp; corrections</h2>
        <p>
          For editorial corrections, data-source questions, accessibility feedback or
          partnership enquiries, write to
          <a href="mailto:urbanforestpark@gmail.com">urbanforestpark@gmail.com</a> or use the
          <a href="/report.html">public issue tracker</a>. We publish a correction when a
          material factual error is confirmed. Legal and privacy enquiries are handled under
          the <a href="/privacy.html">Privacy Policy</a> and <a href="/terms.html">Terms of Use</a>.
        </p>
        <p>
          Community channels: <a href="https://t.me/urbanforestpark" rel="noopener">Telegram</a>
          and the <a href="https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw" rel="noopener">WhatsApp group</a>.
        </p>

        <h2>Open-access research utilities</h2>
        <ul class="about-links">
          <li><a href="/dashboard.html">Nagar Van dMRV Dashboard</a> &mdash; ecological, climate and site-level indicators.</li>
          <li><a href="/explore-dashboard.html">Live site-insights dashboard</a> &mdash; thematic maps and regional profiles.</li>
          <li><a href="/green-calculator.html">Urban Forest Green Calculator</a> &mdash; carbon, biodiversity, cooling and water benefits.</li>
          <li><a href="/nagar-van-finder.html">Nagar Van Finder</a> &mdash; locate urban forest sites near you.</li>
          <li><a href="/spatial-data.html">Spatial Data Explorer</a> &mdash; environmental impact profiles for 30 featured sites.</li>
        </ul>

        <h2 id="cite">Cite or link to this registry</h2>
        <p>
          Researchers, journalists, universities and community organisations may cite the
          registry with attribution. Please link to the canonical homepage rather than copying
          individual listings, so readers always see the current deadline and official link.
        </p>
        <div class="citation-box">
          <p class="citation-label">Suggested citation</p>
          <pre id="citation-text">Urban Forest Park. (2026). National Climate, Forestry, ESG &amp; Geospatial Career Registry (India). https://www.urbanforestpark.com/</pre>
          <button type="button" class="btn btn-outline" data-copy-citation data-copy-target="citation-text">Copy citation</button>
        </div>
        <details class="citation-embed">
          <summary>Embeddable HTML link</summary>
          <pre>&lt;a href="https://www.urbanforestpark.com/"&gt;Urban Forest Park &amp;mdash; National Climate, Forestry, ESG &amp;amp; Geospatial Career Registry (India)&lt;/a&gt;</pre>
        </details>

        <h2>Governance disclosures</h2>
        <h3>Funding &amp; independence</h3>
        <p>Listing is free. No employer, consultancy or institution pays for inclusion, ranking or editorial coverage. Hosting and maintenance costs are met independently of listing fees.</p>
        <h3>Data sources &amp; limitations</h3>
        <p>Registry records are derived from official recruitment pages and public notices. The dMRV dashboard additionally uses government records, field surveys and satellite-derived indicators. We link to primary sources, but users should verify critical eligibility, dates and compensation before applying.</p>
        <h3>Update cadence</h3>
        <p>The active registry, archive, pathway hubs and sitemap are refreshed by the daily publishing pipeline. The homepage and hub pages display the latest editorial review date.</p>

        <section class="hub-cta" aria-labelledby="about-cta-title">
          <div>
            <h2 id="about-cta-title">Explore the registry</h2>
            <p>Start with the national India registry or the strictly separate Global Opportunities portal.</p>
          </div>
          <a class="btn btn-primary" href="/">Open the India registry &rarr;</a>
        </section>
      </div>
    </section>
  </main>

{bsp.site_matrix_html('/about.html')}

{bsp.footer_html('about.html')}
  <script>
    (function () {{
      document.querySelectorAll('[data-copy-citation]').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          var target = document.getElementById(btn.getAttribute('data-copy-target') || 'citation-text');
          if (!target) return;
          var value = target.textContent || '';
          function done() {{ btn.textContent = 'Copied'; setTimeout(function () {{ btn.textContent = 'Copy citation'; }}, 1600); }}
          if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(value).then(done).catch(function () {{
              var r = document.createRange(); r.selectNodeContents(target);
              var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
              try {{ document.execCommand('copy'); done(); }} catch (e) {{}}
            }});
          }} else {{
            var r = document.createRange(); r.selectNodeContents(target);
            var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
            try {{ document.execCommand('copy'); done(); }} catch (e) {{}}
          }}
        }});
      }});
    }})();
  </script>
"""
    return _page_shell(
        "about.html",
        meta,
        body,
        [bsp.organization_jsonld(), bsp.website_jsonld(), about_ld, person_ld, breadcrumb_ld],
    )


def build_error_page(file_name: str, today: date) -> str:
    meta = bsp.page_meta(file_name)
    code = "404" if file_name == "404.html" else "500"
    heading = meta["h1"]
    if code == "404":
        intro = (
            "The page you requested has moved, expired or never existed. The registry is "
            "still open: start with the India career registry, the Global Opportunities "
            "portal or one of the dedicated pathway hubs below."
        )
    else:
        intro = (
            "A temporary server error stopped this page from loading. Your data has not been "
            "changed. Return to the registry, or contact the editorial team if the problem "
            "continues."
        )
    web_page_ld = bsp.jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": meta["title"],
            "description": meta["description"],
            "url": meta["canonical"],
            "isPartOf": {"@id": bsp.SITE + "/#website"},
            "about": {"@id": bsp.SITE + "/#organization"},
            "inLanguage": "en-IN",
        }
    )
    breadcrumb_ld = bsp.breadcrumb_jsonld(heading, meta["canonical"])
    hub_links = "\n".join(
        f'            <li><a href="/{hub["file"]}"><span class="hub-other-name">{_text(hub["h1"])}</span><span class="hub-other-cnt">Pathway</span></a></li>'
        for hub in bsp.HUBS
    )
    body = f"""  <main id="main-content" class="hub-main error-main">
    <section class="hub-hero error-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">Career Registry</a><span aria-hidden="true">/</span><span>{code} error</span>
        </nav>
        <p class="eyebrow">Error {code}</p>
        <h1>{_text(heading)}</h1>
        <p class="hub-hero-sub">{_text(intro)}</p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="/">India career registry &rarr;</a>
          <a class="btn btn-outline" href="/global-climate-sustainability-opportunities.html">Global opportunities</a>
        </div>
      </div>
    </section>

    <section class="hub-main">
      <div class="hub-main-inner">
        <section class="hub-others" aria-labelledby="error-hubs-title">
          <h2 id="error-hubs-title">Career pathway hubs</h2>
          <ul class="hub-other-grid">
{hub_links}
            <li><a href="/hindi-environment-forestry-jobs.html"><span class="hub-other-name">हिंदी पर्यावरण एवं वानिकी करियर पोर्टल</span><span class="hub-other-cnt">Hindi</span></a></li>
            <li><a href="/bharat-regional-green-jobs.html"><span class="hub-other-name">Bharat Regional &amp; State-Wise Green Jobs</span><span class="hub-other-cnt">Regional</span></a></li>
          </ul>
        </section>

        <section class="hub-cta" aria-labelledby="error-tools-title">
          <div>
            <h2 id="error-tools-title">Institutional tools &amp; governance</h2>
            <p>Use the dMRV dashboard, Green Calculator, Nagar Van Finder, public issue tracker or About page to continue.</p>
          </div>
          <a class="btn btn-outline" href="/about.html">About &amp; verification</a>
        </section>
      </div>
    </section>
  </main>

{bsp.site_matrix_html('/' + file_name)}

{bsp.footer_html(file_name)}
"""
    return _page_shell(
        file_name,
        meta,
        body,
        [
            bsp.organization_jsonld(),
            bsp.website_jsonld(),
            web_page_ld,
            breadcrumb_ld,
        ],
    )


def write_institutional_pages(public: Path, today: date) -> None:
    (public / "about.html").write_text(build_about_page(today), encoding="utf-8")
    (public / "404.html").write_text(build_error_page("404.html", today), encoding="utf-8")
    (public / "500.html").write_text(build_error_page("500.html", today), encoding="utf-8")
