#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Multilingual & regional portal builders for the Urban Forest Park registry.

Rendered by scripts/build_seo_pages.py after every pipeline run:

  * hindi-environment-forestry-jobs.html — Hindi SEO hub (lang="hi-IN",
    Devanagari title/description/h1, pre-rendered bilingual cards built from
    the title_hi / summary_hi fields, Hindi FAQPage + CollectionPage JSON-LD).
  * bharat-regional-green-jobs.html — pan-India regional hub with native-script
    section headings (हिंदी, मराठी, தமிழ், తెలుగు, ಕನ್ನಡ, বাংলা, ગુજરાતી),
    per-state active counts and crawlable state-filtered registry links.

This module reuses the shared constants and helpers of build_seo_pages.py; it
is imported lazily from that module's main() so the two never drift apart.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Tuple
from urllib.parse import quote

import build_seo_pages as bsp

SITE = bsp.SITE
LOGO_URL = bsp.LOGO_URL
esc = bsp.esc
plain = bsp.plain
trim = bsp.trim
ist_today = bsp.ist_today
long_date = bsp.long_date
jsonld_script = bsp.jsonld_script
state_label = bsp.state_label
position_type_of = bsp.position_type_of
recent_archive = bsp.recent_archive
faq_section_html = bsp.faq_section_html
faq_jsonld = bsp.faq_jsonld
footer_html = bsp.footer_html
header_html = bsp.header_html

HINDI_HUB_FILE = "hindi-environment-forestry-jobs.html"
REGIONAL_HUB_FILE = "bharat-regional-green-jobs.html"
HINDI_HUB_URL = SITE + "/" + HINDI_HUB_FILE
REGIONAL_HUB_URL = SITE + "/" + REGIONAL_HUB_FILE

# Devanagari + all major Indic scripts used by the regional portal.
FONTS_HI = """    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;600&family=Noto+Sans+Telugu:wght@400;600&family=Noto+Sans+Kannada:wght@400;600&family=Noto+Sans+Bengali:wght@400;600&family=Noto+Sans+Gujarati:wght@400;600&display=swap">"""

PATHWAY_LABELS_HI: Dict[str, str] = {
    "jrf-srf-project-associate-jobs.html": "JRF / SRF एवं प्रोजेक्ट एसोसिएट भर्तियाँ",
    "phd-fellowships-climate-sustainability.html": "PhD एवं पोस्टडॉक्टोरल फेलोशिप",
    "forestry-wildlife-government-jobs.html": "वानिकी, वन्यजीव एवं सरकारी भर्तियाँ",
    "gis-remote-sensing-climate-jobs.html": "GIS एवं रिमोट सेंसिंग भर्तियाँ",
    "esg-carbon-sustainability-jobs.html": "ESG एवं कार्बन बाज़ार भर्तियाँ",
}

HINDI_FAQS: List[Tuple[str, str]] = [
    (
        "भारत में पर्यावरण एवं वानिकी भर्तियाँ कहाँ प्रकाशित होती हैं?",
        "राज्य वन विभाग, पर्यावरण, वन एवं जलवायु परिवर्तन मंत्रालय (MoEFCC), ICFRE संस्थान, "
        "भारतीय वन्यजीव संस्थान (WII), विश्वविद्यालय, IIT, IISc एवं अन्य शोध संस्थान अपने "
        "आधिकारिक पोर्टलों पर भर्तियाँ प्रकाशित करते हैं। यह रजिस्ट्री इन स्रोतों को प्रतिदिन "
        "स्कैन करके सत्यापित भर्तियाँ एक ही स्थान पर उपलब्ध कराती है।",
    ),
    (
        "JRF / SRF एवं PhD फेलोशिप हेतु पात्रता क्या है?",
        "JRF हेतु सामान्यतः संबंधित विषय में M.Sc. / M.Tech. तथा UGC-NET या GATE योग्यता "
        "आवश्यक होती है; SRF हेतु इसके साथ लगभग दो वर्ष का शोध अनुभव। प्रत्येक विज्ञापन की "
        "सटीक शर्तें आधिकारिक सूचना में दी जाती हैं — लिंक सीधे नियोक्ता के पोर्टल पर जाता है।",
    ),
    (
        "रजिस्ट्री कितनी बार अपडेट होती है और अलर्ट कैसे मिलते हैं?",
        "स्वचालित पाइपलाइन प्रतिदिन प्रातः 07:00 बजे (IST) नई भर्तियों को सत्यापित करके "
        "प्रकाशित करती है और Telegram / WhatsApp चैनलों पर तुरंत प्रसारित करती है। ईमेल "
        "डाइजेस्ट प्रत्येक 72 घंटे में भेजा जाता है — कोई शुल्क नहीं, कभी भी अनसब्सक्राइब "
        "किया जा सकता है।",
    ),
    (
        "क्या बंद (पुरानी) भर्तियाँ भी देखी जा सकती हैं?",
        "हाँ — आवेदन अवधि समाप्त होने पर भर्तियाँ ऐतिहासिक संग्रह (Historical Archive) में "
        "सुरक्षित रहती हैं, जिससे वेतन, पात्रता एवं संस्थागत संदर्भ की जानकारी शोधार्थियों "
        "तथा संस्थानों के लिए उपलब्ध रहती है।",
    ),
    (
        "क्या वेबसाइट पूर्णतः हिंदी में उपलब्ध है?",
        "मुख्य रजिस्ट्री में EN | हिंदी स्विच उपलब्ध है और इस हिंदी पोर्टल पर प्रत्येक भर्ती "
        "का शीर्षक एवं सारांश देवनागरी में दिया जाता है। JRF, SRF, GIS, ESG, PhD जैसे "
        "तकनीकी संक्षेप आधिकारिक विज्ञापनों से मेल हेतु अंग्रेज़ी में ही रखे गए हैं।",
    ),
]

LANGUAGE_REGIONS: List[Dict[str, Any]] = [
    {
        "key": "hi",
        "heading": "हिंदी क्षेत्र — उत्तर प्रदेश, मध्य प्रदेश, उत्तराखंड, दिल्ली NCR, राजस्थान एवं बिहार",
        "states": ["Uttar Pradesh", "Madhya Pradesh", "Uttarakhand", "Delhi", "Rajasthan", "Bihar"],
        "note": "इन राज्यों की प्रत्येक सत्यापित भर्ती हिंदी शीर्षक एवं सारांश के साथ हिंदी पोर्टल पर भी उपलब्ध है।",
        "hub": "/" + HINDI_HUB_FILE,
        "hub_label": "पूरा हिंदी करियर पोर्टल देखें",
    },
    {
        "key": "mr",
        "heading": "मराठी क्षेत्र — महाराष्ट्र",
        "states": ["Maharashtra"],
        "note": "महाराष्ट्रातील पर्यावरण, वन्यजीव, हवामान व ESG नोकऱ्या — दररोज सत्यापित व अद्ययावत.",
    },
    {
        "key": "ta",
        "heading": "தமிழ் மண்டலம் — தமிழ்நாடு",
        "states": ["Tamil Nadu"],
        "note": "தமிழ்நாட்டில் சுற்றுச்சூழல், வனவிலங்கு, காலநிலை மற்றும் ESG பணியிடங்கள் — தினமும் புதுப்பிக்கப்படுகிறது.",
    },
    {
        "key": "te",
        "heading": "తెలుగు ప్రాంతం — తెలంగాణ & ఆంధ్రప్రదేశ్",
        "states": ["Telangana", "Andhra Pradesh"],
        "note": "తెలంగాణ మరియు ఆంధ్రప్రదేశ్‌లో పర్యావరణ, అటవీ, వాతావరణ ఉద్యోగాలు — ప్రతిరోజూ నవీకరించబడతాయి.",
    },
    {
        "key": "kn",
        "heading": "ಕನ್ನಡ ಪ್ರದೇಶ — ಕರ್ನಾಟಕ",
        "states": ["Karnataka"],
        "note": "ಕರ್ನಾಟಕದಲ್ಲಿ ಪರಿಸರ, ಅರಣ್ಯ, ಹವಾಮಾನ ಮತ್ತು ESG ಉದ್ಯೋಗಗಳು — ಪ್ರತಿದಿನ ಪರಿಶೀಲಿಸಲಾಗುತ್ತದೆ.",
    },
    {
        "key": "bn",
        "heading": "বাংলা অঞ্চল — পশ্চিমবঙ্গ",
        "states": ["West Bengal"],
        "note": "পশ্চিমবঙ্গে পরিবেশ, বন্যপ্রাণী, জলবায়ু ও ESG চাকরি — প্রতিদিন যাচাই করা হয়।",
    },
    {
        "key": "gu",
        "heading": "ગુજરાતી ક્ષેત્ર — ગુજરાત",
        "states": ["Gujarat"],
        "note": "ગુજરાતમાં પર્યાવરણ, વન્યજીવન, આબોહવા અને ESG નોકરીઓ — દરરોજ ચકાસાય છે.",
    },
]


def _sort_recent_first(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    fn = getattr(bsp, "sort_recent_first", None)
    if fn:
        return fn(jobs)
    return sorted(jobs, key=lambda j: str(j.get("date_added") or ""), reverse=True)


def region_matches(region: Dict[str, Any], state_name: str) -> bool:
    s = plain(state_name).lower()
    if not s:
        return False
    for alias in region["states"]:
        a = plain(alias).lower()
        if s == a or a in s or s in a:
            return True
    return False


# --------------------------------------------------------------------------
# Hindi hub
# --------------------------------------------------------------------------
def hindi_card_html(job: Dict[str, Any]) -> str:
    title_hi = plain(job.get("title_hi"))
    eng_title = plain(job.get("clean_title"))
    title = title_hi or eng_title or plain(job.get("organization")) or "भर्ती विवरण"
    org = plain(job.get("organization")) or "संस्थान"
    city = plain(job.get("city"))
    org_line = org + (f" · {city}" if city and city.lower() != org.lower() else "")

    badges = [
        f'<span class="badge badge-type">{esc(position_type_of(job))}</span>',
        f'<span class="badge badge-state">{bsp.PIN_SVG}{esc(state_label(job))}</span>',
    ]
    english_line = (
        f'<p class="hi-card-en">{esc(eng_title)}</p>'
        if title_hi and eng_title and title_hi != eng_title
        else ""
    )
    qual = plain(job.get("qualification_summary"))
    elig_html = (
        f'<p class="hub-card-elig"><strong>योग्यता:</strong> {esc(trim(qual, 200))}</p>'
        if qual
        else ""
    )
    summary = plain(job.get("summary_hi")) or trim(job.get("role_summary"), 220)
    summary_html = f'<p class="hub-card-sum">{esc(summary)}</p>' if summary else ""
    link = f'/?job={esc(job.get("id"))}&amp;lang=hi'

    return f"""        <article class="hub-card hi-card">
          <div class="hub-card-top">
            {''.join(badges)}
          </div>
          <h3 class="hub-card-title"><a href="{link}">{esc(title)}</a></h3>
          {english_line}
          <p class="hub-card-org">{esc(org_line)}</p>
          {elig_html}
          {summary_html}
          <p class="hub-card-foot"><a href="{link}">पूर्ण विवरण एवं आवेदन लिंक &rarr;</a></p>
        </article>"""


def header_html_hi() -> str:
    return """  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="/?lang=hi" aria-label="Urban Forest Park - हिंदी करियर रजिस्ट्री">
        <span class="brand-word">Urban Forest Park</span>
        <span class="brand-sub">राष्ट्रीय जलवायु, वानिकी, ESG एवं भू-स्थानिक करियर रजिस्ट्री (भारत)</span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="मुख्य नेविगेशन">
        <a class="nav-link" href="/?lang=hi">करियर रजिस्ट्री (हिंदी)</a>
        <a class="nav-link" href="/?view=archive&amp;lang=hi">संग्रहित भर्तियाँ</a>
        <a class="nav-link" href="/dashboard.html">dMRV डैशबोर्ड <span class="live-tool-badge">Live Tool</span></a>
        <a class="nav-link" href="/">EN Registry</a>
      </nav>
      <div class="header-actions">
        <a class="btn btn-outline nav-cta" href="/?lang=hi#filter-bar">रजिस्ट्री ब्राउज़ करें</a>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false" aria-label="रात्रि मोड पर स्विच करें">
          <svg class="theme-icon icon-sun" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.4"/><path d="M12 2.5v2.4M12 19.1v2.4M2.5 12h2.4M19.1 12h2.4M5.3 5.3l1.7 1.7M17 17l1.7 1.7M18.7 5.3 17 7M7 17l-1.7 1.7"/></svg>
          <svg class="theme-icon icon-moon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.4 14.2A8.5 8.5 0 1 1 9.8 3.6a7 7 0 0 0 10.6 10.6z"/></svg>
          <span class="theme-label" id="theme-label">रात्रि</span>
        </button>
        <button class="nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="नेविगेशन मेनू">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
        </button>
      </div>
    </div>
  </header>"""


def footer_html_hi() -> str:
    return f"""  <footer class="site-footer">
    <div class="footer-grid">
      <div class="footer-col">
        <h3>Urban Forest Park</h3>
        <p>
          राष्ट्रीय जलवायु, वानिकी, ESG एवं भू-स्थानिक करियर रजिस्ट्री (भारत)। हम आधिकारिक पोर्टलों,
          विश्वविद्यालयों एवं शोध संस्थानों की निगरानी करके सत्यापित भर्तियाँ सीधे स्रोत से जोड़ते हैं।
        </p>
        <p style="margin-top:10px;">
          साथ ही: <a href="/dashboard.html">नगर वन dMRV डैशबोर्ड एवं ग्रीन कैलकुलेटर</a>।
        </p>
      </div>

      <div class="footer-col">
        <h3>करियर पथ</h3>
        <ul>
          <li><a href="/jrf-srf-project-associate-jobs.html">JRF / SRF एवं प्रोजेक्ट एसोसिएट भर्तियाँ</a></li>
          <li><a href="/phd-fellowships-climate-sustainability.html">PhD एवं पोस्टडॉक्टोरल फेलोशिप</a></li>
          <li><a href="/forestry-wildlife-government-jobs.html">वानिकी एवं वन्यजीव सरकारी भर्तियाँ</a></li>
          <li><a href="/gis-remote-sensing-climate-jobs.html">GIS एवं रिमोट सेंसिंग भर्तियाँ</a></li>
          <li><a href="/esg-carbon-sustainability-jobs.html">ESG एवं कार्बन बाज़ार भर्तियाँ</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>क्षेत्रीय एवं बहुभाषी पोर्टल (भारत / हिंदी)</h3>
        <ul>
          <li><span class="footer-current">हिंदी करियर पोर्टल (यह पृष्ठ)</span></li>
          <li><a href="/bharat-regional-green-jobs.html">भारत क्षेत्रीय हरित भर्तियाँ</a></li>
          <li><a href="/">English Career Registry</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>संपर्क एवं कानूनी</h3>
        <ul>
          <li><a href="/about.html">परिचय</a></li>
          <li><a href="/privacy.html">गोपनीयता नीति</a></li>
          <li><a href="/terms.html">उपयोग की शर्तें</a></li>
          <li><a href="/unsubscribe.html">डिस्पैच प्राथमिकताएँ</a></li>
          <li><a href="mailto:arkraj.biswas6@gmail.com">संपर्क करें</a></li>
        </ul>
      </div>
    </div>

    <div class="footer-bottom">
      &copy; {ist_today().year} Urban Forest Park<span class="dot">&bull;</span>राष्ट्रीय जलवायु, वानिकी, ESG एवं भू-स्थानिक करियर रजिस्ट्री (भारत)
      <span class="dot">&bull;</span>सभी सूचियाँ आधिकारिक आवेदन पोर्टल से जुड़ी हैं — आवेदन से पूर्व विवरण सत्यापित करें।
    </div>
  </footer>"""


def build_hindi_hub_page(
    active_jobs: List[Dict[str, Any]],
    archived_jobs: List[Dict[str, Any]],
    hub_counts: Dict[str, int],
    today: date,
) -> str:
    jobs = _sort_recent_first(active_jobs)
    cards = "\n".join(hindi_card_html(j) for j in jobs) or (
        '        <p class="hub-empty">इस समय कोई सक्रिय भर्ती उपलब्ध नहीं — नई भर्तियाँ प्रतिदिन जोड़ी जाती हैं। '
        '<a href="/?lang=hi">लाइव रजिस्ट्री देखें</a>।</p>'
    )
    archived = recent_archive(archived_jobs, today, bsp.RECENT_ARCHIVE_DAYS)[: bsp.HUB_ARCHIVE_LIMIT]
    archive_block = ""
    if archived:
        arch_cards = "\n".join(hindi_card_html(j) for j in archived)
        archive_block = f"""      <section class="hub-archive" aria-labelledby="hub-archive-title">
        <h2 id="hub-archive-title">हाल ही में बंद भर्तियाँ ({len(archived)})</h2>
        <p class="hub-archive-sub">संदर्भ हेतु संरक्षित — वेतन, पात्रता एवं संस्थागत इतिहास की जानकारी।</p>
        <div class="hub-list">
{arch_cards}
        </div>
      </section>"""

    states = sorted({state_label(j) for j in jobs})
    states_note = (
        f"{len(states)} राज्य / क्षेत्र"
        if len(states) > 1
        else (states[0] if states else "संपूर्ण भारत")
    )

    pathway_links = "\n".join(
        f'            <li><a href="/{h["file"]}"><span class="hub-other-name">'
        f'{esc(PATHWAY_LABELS_HI.get(h["file"], h["h1"]))}</span>'
        f'<span class="hub-other-cnt">{hub_counts.get(h["file"], 0)} सक्रिय</span></a></li>'
        for h in bsp.HUBS
    )

    title = (
        "पर्यावरण एवं वानिकी भर्तियाँ 2026 — JRF, ESG, GIS, PhD एवं जलवायु करियर "
        "| Urban Forest Park"
    )
    desc = (
        "भारत में पर्यावरण, वानिकी, वन्यजीव, जलवायु परिवर्तन, ESG, कार्बन बाज़ार एवं भू-स्थानिक (GIS) क्षेत्र की "
        "सत्यापित भर्तियाँ — JRF / SRF, PhD एवं पोस्टडॉक्टोरल फेलोशिप, रिसर्च एवं प्रोजेक्ट पद तथा कॉर्पोरेट "
        "सस्टेनेबिलिटी भूमिकाएँ। प्रत्येक सूची सीधे आधिकारिक आवेदन पोर्टल से जुड़ती है।"
    )

    collection = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "description": desc,
            "url": HINDI_HUB_URL,
            "inLanguage": "hi-IN",
            "dateModified": today.isoformat(),
            "isPartOf": {
                "@type": "WebSite",
                "name": "Urban Forest Park — National Climate, Forestry, ESG & Geospatial Career Registry (India)",
                "url": SITE + "/",
            },
            "about": {"@type": "Thing", "name": "पर्यावरण एवं वानिकी भर्तियाँ — भारत"},
        }
    )
    faqs = faq_jsonld(HINDI_FAQS)
    faq_block = faq_section_html(HINDI_FAQS, heading="अक्सर पूछे जाने वाले प्रश्न")

    return f"""<!DOCTYPE html>
<html lang="hi-IN">
<head>
    {bsp.GA_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{bsp.THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{HINDI_HUB_URL}">
    <link rel="alternate" hreflang="en-IN" href="{SITE}/">
    <link rel="alternate" hreflang="hi-IN" href="{HINDI_HUB_URL}">
    <link rel="alternate" hreflang="x-default" href="{SITE}/">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park — भारत करियर रजिस्ट्री">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{HINDI_HUB_URL}">
    <meta property="og:image" content="{LOGO_URL}">
    <meta property="og:locale" content="hi_IN">
    <meta property="og:locale:alternate" content="en_IN">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{LOGO_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{bsp.FAVICONS}

    <!-- Typography (Devanagari-aware) -->
{FONTS_HI}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{collection}
{faqs}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#hindi-list">भर्ती सूची पर जाएँ</a>

{header_html_hi()}

  <main>
    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="ब्रेडक्रम्ब">
          <a href="/">Career Registry</a><span aria-hidden="true">/</span><span>हिंदी करियर पोर्टल</span>
        </nav>
        <p class="eyebrow">हिंदी ग्रीन करियर पोर्टल</p>
        <h1>भारत में पर्यावरण एवं वानिकी भर्तियाँ — JRF, ESG, GIS एवं जलवायु करियर</h1>
        <p class="hub-hero-sub">
          वन विभागों, विश्वविद्यालयों एवं शोध संस्थानों (JRF / SRF / PhD / प्रोजेक्ट स्टाफ), सस्टेनेबिलिटी टीमों
          तथा जलवायु संगठनों की सक्रिय भर्तियों का निरंतर निगरानी किया जाने वाला सूचकांक।
          <strong>प्रत्येक सूची सीधे आधिकारिक आवेदन पोर्टल से जुड़ती है</strong> — कोई बिचौलिया नहीं, कोई शुल्क नहीं।
          बंद भर्तियाँ ऐतिहासिक संग्रह में संरक्षित रहती हैं।
        </p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="/?lang=hi">लाइव रजिस्ट्री खोलें &rarr;</a>
          <a class="btn btn-outline" href="/?view=archive&amp;lang=hi">संग्रहित भर्तियाँ</a>
          <a class="btn btn-outline" href="/bharat-regional-green-jobs.html">क्षेत्रीय पोर्टल (भारत)</a>
        </div>
        <dl class="hub-stats">
          <div><dt>सक्रिय भर्तियाँ</dt><dd>{len(jobs)}</dd></div>
          <div><dt>कवरेज</dt><dd>{esc(states_note)}</dd></div>
          <div><dt>अद्यतन</dt><dd>{esc(long_date(today))}</dd></div>
        </dl>
        <p class="hub-lang-note">तकनीकी एवं अंतरराष्ट्रीय संक्षेप (JRF, SRF, GIS, ESG, PhD, dMRV) आधिकारिक विज्ञापनों से मेल हेतु अंग्रेज़ी में रखे गए हैं।</p>
      </div>
    </section>

    <section class="hub-main" id="hindi-list">
      <div class="hub-main-inner">
        <div class="hub-main-head">
          <h2>नवीनतम सत्यापित भर्तियाँ ({len(jobs)})</h2>
          <p>प्रत्येक भर्ती का शीर्षक एवं सारांश देवनागरी में — मूल अंग्रेज़ी शीर्षक के साथ। डोज़ियर खोलने पर आवेदन लिंक, योग्यता एवं संस्थागत विवरण उपलब्ध हैं।</p>
        </div>
        <div class="hub-list">
{cards}
        </div>

{archive_block}

{faq_block}

        <section class="hub-cta" aria-label="लाइव रजिस्ट्री">
          <div>
            <h2>रोज़ाना नई भर्तियाँ — प्रत्येक सुबह 07:00 बजे IST</h2>
            <p>Telegram एवं WhatsApp पर तुरंत अलर्ट, तथा प्रत्येक 72 घंटे में ईमेल डाइजेस्ट। कोई शुल्क नहीं।</p>
          </div>
          <a class="btn btn-primary" href="/?lang=hi">रजिस्ट्री में खोजें &rarr;</a>
        </section>

        <section class="hub-others" aria-labelledby="hub-others-title">
          <h2 id="hub-others-title">अन्य करियर पथ एवं पोर्टल</h2>
          <ul class="hub-other-grid">
            <li><a href="/bharat-regional-green-jobs.html"><span class="hub-other-name">भारत क्षेत्रीय हरित भर्तियाँ</span><span class="hub-other-cnt">सभी राज्य</span></a></li>
            <li><a href="/"><span class="hub-other-name">English Career Registry</span><span class="hub-other-cnt">EN</span></a></li>
{pathway_links}
          </ul>
        </section>
      </div>
    </section>
  </main>

{footer_html_hi()}

  <script defer src="/js/consent.js"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Regional hub
# --------------------------------------------------------------------------
def build_regional_hub_page(active_jobs: List[Dict[str, Any]], today: date) -> str:
    counts: Dict[str, int] = {}
    for job in active_jobs:
        st = state_label(job)
        counts[st] = counts.get(st, 0) + 1

    used = set()
    cards: List[str] = []
    item_entries: List[Dict[str, Any]] = []
    for region in LANGUAGE_REGIONS:
        matched = sorted(
            [(st, n) for st, n in counts.items() if st not in used and region_matches(region, st)],
            key=lambda kv: (-kv[1], kv[0]),
        )
        for st, _n in matched:
            used.add(st)
        total = sum(n for _st, n in matched)
        state_links = "\n".join(
            f'            <li><a href="/?state={quote(st)}">{esc(st)} '
            f'<span class="region-cnt">{n}</span></a></li>'
            for st, n in matched
        ) or (
            '            <li class="region-empty">इस क्षेत्र हेतु नई भर्तियाँ शीघ्र जुड़ेंगी / '
            'listings coming soon</li>'
        )
        hub_line = (
            f'        <p class="region-hub"><a href="{region["hub"]}">'
            f'{esc(region["hub_label"])} &rarr;</a></p>'
            if region.get("hub")
            else ""
        )
        cards.append(
            f"""      <article class="region-card" lang="{region['key']}" id="region-{region['key']}">
        <h2>{esc(region['heading'])}</h2>
        <p class="region-total"><strong>{total}</strong> active green mandate(s) across {len(matched)} state(s) / region(s)</p>
        <ul class="region-states">
{state_links}
        </ul>
{hub_line}
        <p class="region-note">{esc(region['note'])}</p>
      </article>"""
        )
        for st, _n in matched[:8]:
            item_entries.append(
                {
                    "@type": "ListItem",
                    "position": len(item_entries) + 1,
                    "url": SITE + "/?state=" + quote(st),
                    "name": st,
                }
            )

    others = sorted(
        [(st, n) for st, n in counts.items() if st not in used],
        key=lambda kv: (-kv[1], kv[0]),
    )
    other_links = "\n".join(
        f'            <li><a href="/?state={quote(st)}">{esc(st)} '
        f'<span class="region-cnt">{n}</span></a></li>'
        for st, n in others
    ) or '            <li class="region-empty">&mdash;</li>'
    others_card = f"""      <article class="region-card region-card-other" lang="en">
        <h2>Other States &amp; Regions — अन्य राज्य एवं क्षेत्र</h2>
        <p class="region-total"><strong>{sum(n for _s, n in others)}</strong> active green mandate(s) in {len(others)} further state(s) / region(s)</p>
        <ul class="region-states">
{other_links}
        </ul>
        <p class="region-note">Bilingual listing metadata (EN / हिंदी) is available for every mandate — switch the registry to हिंदी with the EN | हिंदी toggle.</p>
      </article>"""

    cards_html = "\n\n".join(cards) + "\n\n" + others_card

    total_jobs = len(active_jobs)
    title = (
        "Bharat Regional & State-Wise Green Jobs — भारत क्षेत्रीय पर्यावरण एवं वानिकी भर्तियाँ "
        "| Urban Forest Park"
    )
    desc = (
        "State-wise green job portal for India — environment, forestry, wildlife, climate, ESG and "
        "geospatial vacancies across the Hindi, Marathi, Tamil, Telugu, Kannada, Bengali and Gujarati "
        "regions. हर राज्य की सत्यापित भर्तियाँ — सीधे आधिकारिक आवेदन पोर्टल से जुड़ी।"
    )

    collection = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "description": desc,
            "url": REGIONAL_HUB_URL,
            "inLanguage": "en-IN",
            "dateModified": today.isoformat(),
            "isPartOf": {
                "@type": "WebSite",
                "name": "Urban Forest Park — National Climate, Forestry, ESG & Geospatial Career Registry (India)",
                "url": SITE + "/",
            },
            "about": {"@type": "Thing", "name": "State-wise green jobs in India"},
        }
    )
    item_list = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "State-wise green job listings in India",
            "numberOfItems": len(item_entries),
            "itemListElement": item_entries,
        }
    )

    return f"""<!DOCTYPE html>
<html lang="en-IN">
<head>
    {bsp.GA_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{bsp.THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{REGIONAL_HUB_URL}">
    <link rel="alternate" hreflang="en-IN" href="{REGIONAL_HUB_URL}">
    <link rel="alternate" hreflang="hi-IN" href="{HINDI_HUB_URL}">
    <link rel="alternate" hreflang="x-default" href="{REGIONAL_HUB_URL}">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park — India Career Registry">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{REGIONAL_HUB_URL}">
    <meta property="og:image" content="{LOGO_URL}">
    <meta property="og:locale" content="en_IN">
    <meta property="og:locale:alternate" content="hi_IN">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{LOGO_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{bsp.FAVICONS}

    <!-- Typography (Indic-script aware) -->
{FONTS_HI}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{collection}
{item_list}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#region-grid">Skip to regional listings</a>

{header_html('registry')}

  <main>
    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">Career Registry</a><span aria-hidden="true">/</span><span>Bharat Regional Portal</span>
        </nav>
        <p class="eyebrow">Bharat Regional &amp; Multilingual Portal</p>
        <h1>Bharat Regional &amp; State-Wise Green Jobs — भारत क्षेत्रीय हरित भर्तियाँ</h1>
        <p class="hub-hero-sub">
          State-wise environment, forestry, wildlife, climate, ESG and geospatial mandates —
          हिंदी, मराठी, தமிழ், తెలుగు, ಕನ್ನಡ, বাংলা एवं ગુજરાતી क्षेत्रों हेतु क्षेत्रीय प्रवेश द्वार।
          Every listing links straight to the official application portal.
        </p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="/hindi-environment-forestry-jobs.html">हिंदी पोर्टल खोलें &rarr;</a>
          <a class="btn btn-outline" href="/">Open the live registry</a>
        </div>
        <dl class="hub-stats">
          <div><dt>Active listings</dt><dd>{total_jobs}</dd></div>
          <div><dt>States / regions</dt><dd>{len(counts)}</dd></div>
          <div><dt>Updated</dt><dd>{esc(long_date(today))}</dd></div>
        </dl>
      </div>
    </section>

    <section class="hub-main" id="region-grid">
      <div class="hub-main-inner">
        <div class="hub-main-head">
          <h2>Choose your state or language region / अपना राज्य अथवा क्षेत्र चुनें</h2>
          <p>Regional gateways group the registry by the languages India's green economy hires in. Counts refresh with every daily pipeline run (07:00 IST); each state link opens the live registry pre-filtered to that state.</p>
        </div>
        <div class="region-grid">
{cards_html}
        </div>

        <section class="hub-others" aria-labelledby="hub-others-title">
          <h2 id="hub-others-title">Explore career pathways</h2>
          <ul class="hub-other-grid">
            <li><a href="/hindi-environment-forestry-jobs.html"><span class="hub-other-name">हिंदी करियर पोर्टल</span><span class="hub-other-cnt">Hindi</span></a></li>
            <li><a href="/jrf-srf-project-associate-jobs.html"><span class="hub-other-name">JRF / SRF &amp; Project Associate Jobs</span><span class="hub-other-cnt">Academic</span></a></li>
            <li><a href="/phd-fellowships-climate-sustainability.html"><span class="hub-other-name">PhD &amp; Postdoctoral Fellowships</span><span class="hub-other-cnt">Doctoral</span></a></li>
            <li><a href="/forestry-wildlife-government-jobs.html"><span class="hub-other-name">Forestry, Wildlife &amp; Government Jobs</span><span class="hub-other-cnt">Government</span></a></li>
            <li><a href="/gis-remote-sensing-climate-jobs.html"><span class="hub-other-name">GIS &amp; Remote Sensing Jobs</span><span class="hub-other-cnt">Geospatial</span></a></li>
            <li><a href="/esg-carbon-sustainability-jobs.html"><span class="hub-other-name">ESG &amp; Carbon Market Jobs</span><span class="hub-other-cnt">Corporate</span></a></li>
          </ul>
        </section>
      </div>
    </section>
  </main>

{footer_html(None)}

  <script defer src="/js/consent.js"></script>
</body>
</html>
"""
