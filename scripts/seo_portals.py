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
HINDI_IMAGE_URL = bsp.DISCOVER_IMAGE_DIR + "/forestry.jpg"
REGIONAL_IMAGE_URL = bsp.DISCOVER_IMAGE_DIR + "/default.jpg"
GLOBAL_IMAGE_URL = bsp.DISCOVER_IMAGE_DIR + "/default.jpg"
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
footer_social_html = bsp.footer_social_html
header_html = bsp.header_html

HINDI_HUB_FILE = "hindi-environment-forestry-jobs.html"
REGIONAL_HUB_FILE = "bharat-regional-green-jobs.html"
HINDI_HUB_URL = SITE + "/" + HINDI_HUB_FILE
REGIONAL_HUB_URL = SITE + "/" + REGIONAL_HUB_FILE
HINDI_META = bsp.page_meta(HINDI_HUB_FILE)
REGIONAL_META = bsp.page_meta(REGIONAL_HUB_FILE)
GLOBAL_FAQ_HEADING = "Global Opportunities \u2014 Frequently Asked Questions"

# Devanagari + all major Indic scripts used by the regional portal.
FONTS_HI = """    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&family=Spectral:wght@500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;600&family=Noto+Sans+Telugu:wght@400;600&family=Noto+Sans+Kannada:wght@400;600&family=Noto+Sans+Bengali:wght@400;600&family=Noto+Sans+Gujarati:wght@400;600&display=swap">"""

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
        if qual and bsp.is_specific_qualification(qual)
        else ""
    )
    summary = plain(job.get("summary_hi")) or trim(job.get("role_summary"), 220)
    summary_html = f'<p class="hub-card-sum">{esc(summary)}</p>' if summary else ""
    link = f'/jobs/{esc(job.get("id"))}'

    return f"""        <article class="hub-card hi-card">
          <div class="hub-card-top">
            {bsp.BADGE_SEP.join(badges)}
          </div>
          <h3 class="hub-card-title"><a href="{link}" title="{esc(title)}">{esc(bsp.anchor_text(title))}</a></h3>
          {english_line}
          <p class="hub-card-org">{esc(org_line)}</p>
          {elig_html}
          {summary_html}
          <p class="hub-card-foot"><span>पूर्ण विवरण एवं आवेदन लिंक &rarr;</span></p>
        </article>"""


def header_html_hi() -> str:
    return """  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="#hindi-list" aria-label="Urban Forest Park - हिंदी करियर रजिस्ट्री">
        <img src="/assets/images/Logo_UFF.png" alt="Urban Forest Park — India Climate, Forestry, ESG &amp; Research Jobs Registry Logo" title="Urban Forest Park Official Emblem" class="ufp-header-logo" width="48" height="48" loading="eager" decoding="async" fetchpriority="high" />
        <span class="brand-word">Urban Forest Park</span>
        <span class="brand-sub">राष्ट्रीय जलवायु, वानिकी, ESG एवं भू-स्थानिक करियर रजिस्ट्री (भारत)</span>
      </a>
      <nav class="site-nav" id="site-nav" aria-label="मुख्य नेविगेशन">
        <a class="nav-link" href="#hindi-list">करियर रजिस्ट्री (हिंदी)</a>
        <a class="nav-link" href="/?view=archive&amp;lang=hi" rel="nofollow">संग्रहित भर्तियाँ</a>
        <a class="nav-link" href="/global-climate-sustainability-opportunities">वैश्विक अवसर</a>
        <a class="nav-link" href="/">EN Registry</a>
      </nav>
      <div class="header-actions">
        <a class="btn btn-outline nav-cta" href="#hindi-list">रजिस्ट्री ब्राउज़ करें</a>
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
          <li><a href="/jrf-srf-project-associate-jobs">JRF / SRF एवं प्रोजेक्ट एसोसिएट भर्तियाँ</a></li>
          <li><a href="/phd-fellowships-climate-sustainability">PhD एवं पोस्टडॉक्टोरल फेलोशिप</a></li>
          <li><a href="/forestry-wildlife-government-jobs">वानिकी एवं वन्यजीव सरकारी भर्तियाँ</a></li>
          <li><a href="/gis-remote-sensing-climate-jobs">GIS एवं रिमोट सेंसिंग भर्तियाँ</a></li>
          <li><a href="/esg-carbon-sustainability-jobs">ESG एवं कार्बन बाज़ार भर्तियाँ</a></li>
        </ul>
      </div>

      <div class="footer-col">
        <h3>क्षेत्रीय एवं बहुभाषी पोर्टल (भारत / हिंदी)</h3>
        <ul>
          <li><span class="footer-current">हिंदी करियर पोर्टल (यह पृष्ठ)</span></li>
          <li><a href="/bharat-regional-green-jobs">भारत क्षेत्रीय हरित भर्तियाँ</a></li>
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
          <li><a href="mailto:urbanforestpark@gmail.com">संपर्क करें</a></li>
          <li><button type="button" class="footer-link-btn" data-syndication-open>Syndication Desk</button></li>
        </ul>
      </div>
    </div>

{footer_social_html()}

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
    global_count: int = 0,
) -> str:
    badge_html = bsp.registry_refresh_badge_html(
        today, len(active_jobs), global_count
    )
    jobs = _sort_recent_first(active_jobs)
    cards = "\n".join(hindi_card_html(j) for j in jobs) or (
        '        <p class="hub-empty">इस समय कोई सक्रिय भर्ती उपलब्ध नहीं — नई भर्तियाँ प्रतिदिन जोड़ी जाती हैं। '
        '<a href="#hindi-list">लाइव रजिस्ट्री देखें</a>।</p>'
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

    h1 = bsp.plain(HINDI_META['h1'])
    title = bsp.plain(HINDI_META['title'])
    desc = bsp.plain(HINDI_META['description'])

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
    item_list = bsp.item_list_jsonld({"h1": h1}, jobs)
    organization = bsp.organization_jsonld()
    website = bsp.website_jsonld()
    breadcrumb = bsp.breadcrumb_jsonld(h1, HINDI_HUB_URL)

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
    <link rel="alternate" hreflang="en" href="{SITE}/global-climate-sustainability-opportunities.html">
    <link rel="alternate" hreflang="x-default" href="{SITE}/">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park — भारत करियर रजिस्ट्री">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{HINDI_HUB_URL}">
    <meta property="og:image" content="{HINDI_IMAGE_URL}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="675">
    <meta property="og:locale" content="hi_IN">
    <meta property="og:locale:alternate" content="en_IN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{HINDI_IMAGE_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{bsp.FAVICONS}

    <!-- Typography (Devanagari-aware) -->
{FONTS_HI}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{organization}
{website}
{collection}
{item_list}
{breadcrumb}
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
          <a href="/">All jobs</a><span aria-hidden="true">/</span><span>हिंदी करियर पोर्टल</span>
        </nav>
        <p class="eyebrow">हिंदी ग्रीन करियर पोर्टल</p>
        <h1>{esc(h1)}</h1>
        {badge_html}
        <p class="hub-hero-sub">
          वन विभागों, विश्वविद्यालयों एवं शोध संस्थानों (JRF / SRF / PhD / प्रोजेक्ट स्टाफ), सस्टेनेबिलिटी टीमों
          तथा जलवायु संगठनों की सक्रिय भर्तियों का निरंतर निगरानी किया जाने वाला सूचकांक।
          <strong>प्रत्येक सूची सीधे आधिकारिक आवेदन पोर्टल से जुड़ती है</strong> — कोई बिचौलिया नहीं, कोई शुल्क नहीं।
          बंद भर्तियाँ ऐतिहासिक संग्रह में संरक्षित रहती हैं।
        </p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="#hindi-list">लाइव रजिस्ट्री खोलें &rarr;</a>
          <a class="btn btn-outline" href="/?view=archive&amp;lang=hi" rel="nofollow">पुरानी भर्तियाँ</a>
          <a class="btn btn-outline" href="/bharat-regional-green-jobs">क्षेत्रीय पोर्टल (भारत)</a>
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
          <a class="btn btn-primary" href="#hindi-list">रजिस्ट्री में खोजें &rarr;</a>
        </section>

        <section class="hub-others" aria-labelledby="hub-others-title">
          <h2 id="hub-others-title">अन्य करियर पथ एवं पोर्टल</h2>
          <ul class="hub-other-grid">
            <li><a href="/bharat-regional-green-jobs"><span class="hub-other-name">भारत क्षेत्रीय हरित भर्तियाँ</span><span class="hub-other-cnt">सभी राज्य</span></a></li>
            <li><a href="/"><span class="hub-other-name">English Career Registry</span><span class="hub-other-cnt">EN</span></a></li>
{pathway_links}
          </ul>
        </section>
      </div>
    </section>
  </main>

{bsp.site_matrix_html('/' + HINDI_HUB_FILE)}

{footer_html_hi()}

  <script defer src="/js/consent.js"></script>
<script defer src="/js/back-to-top.js"></script>
<script defer src="/js/syndication-drawer.js?v=20261023-1"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Regional hub
# --------------------------------------------------------------------------
REGIONAL_FAQS: List[Tuple[str, str]] = [
    (
        "How are state-wise green jobs grouped on this portal?",
        "The regional portal groups active jobs into language and cultural regions used by India's "
        "environmental employers: the Hindi belt, Marathi-speaking Maharashtra, Tamil Nadu, Telugu states, "
        "Karnataka, West Bengal and Gujarat. Each state link opens the live registry pre-filtered to that "
        "state, with the same verified records and official application links as the main registry.",
    ),
    (
        "Do regional links open the live registry or a separate database?",
        "They open the single national registry with a state filter applied. The regional portal is a "
        "crawlable entry point, not a duplicate dataset, so deadlines, eligibility and application links "
        "always match the active registry.",
    ),
    (
        "Are the regional listings bilingual?",
        "Every verified job carries an English title and summary, and the main registry includes an "
        "EN | हिंदी switch. The Hindi portal and this regional portal provide additional language-native "
        "entry points for candidates who prefer to browse in Hindi or another Indian language.",
    ),
]


def build_regional_hub_page(
    active_jobs: List[Dict[str, Any]],
    today: date,
    global_count: int = 0,
) -> str:
    badge_html = bsp.registry_refresh_badge_html(
        today, len(active_jobs), global_count
    )
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
            f'            <li id="state-{bsp.state_slug(st)}"><a href="#state-{bsp.state_slug(st)}">{esc(st)} '
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
        <p class="region-total"><strong>{total}</strong> active environmental job(s) across {len(matched)} state(s) / region(s)</p>
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
                    "url": SITE + "/bharat-regional-green-jobs#state-" + bsp.state_slug(st),
                    "name": st,
                }
            )

    others = sorted(
        [(st, n) for st, n in counts.items() if st not in used],
        key=lambda kv: (-kv[1], kv[0]),
    )
    other_links = "\n".join(
        f'            <li id="state-{bsp.state_slug(st)}"><a href="#state-{bsp.state_slug(st)}">{esc(st)} '
        f'<span class="region-cnt">{n}</span></a></li>'
        for st, n in others
    ) or '            <li class="region-empty">&mdash;</li>'
    others_card = f"""      <article class="region-card region-card-other" lang="en">
        <h2>Other States &amp; Regions — अन्य राज्य एवं क्षेत्र</h2>
        <p class="region-total"><strong>{sum(n for _s, n in others)}</strong> active environmental job(s) in {len(others)} further state(s) / region(s)</p>
        <ul class="region-states">
{other_links}
        </ul>
        <p class="region-note">Bilingual listing metadata (EN / हिंदी) is available for every job — switch the registry to हिंदी with the EN | हिंदी toggle.</p>
      </article>"""

    cards_html = "\n\n".join(cards) + "\n\n" + others_card

    total_jobs = len(active_jobs)
    h1 = bsp.plain(REGIONAL_META['h1'])
    title = bsp.plain(REGIONAL_META['title'])
    desc = bsp.plain(REGIONAL_META['description'])

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
    organization = bsp.organization_jsonld()
    website = bsp.website_jsonld()
    breadcrumb = bsp.breadcrumb_jsonld(h1, REGIONAL_HUB_URL)
    faqs = faq_jsonld(REGIONAL_FAQS)
    faq_block = faq_section_html(REGIONAL_FAQS, heading="Bharat Regional Portal — Frequently Asked Questions")

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
    <link rel="alternate" hreflang="en-IN" href="{SITE}/">
    <link rel="alternate" hreflang="hi-IN" href="{HINDI_HUB_URL}">
    <link rel="alternate" hreflang="en" href="{SITE}/global-climate-sustainability-opportunities.html">
    <link rel="alternate" hreflang="x-default" href="{SITE}/">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park — India Career Registry">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{REGIONAL_HUB_URL}">
    <meta property="og:image" content="{REGIONAL_IMAGE_URL}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="675">
    <meta property="og:locale" content="en_IN">
    <meta property="og:locale:alternate" content="hi_IN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{REGIONAL_IMAGE_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{bsp.FAVICONS}

    <!-- Typography (Indic-script aware) -->
{FONTS_HI}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{organization}
{website}
{collection}
{item_list}
{breadcrumb}
{faqs}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#region-grid">Skip to regional listings</a>

{header_html('registry')}

  <main>
    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">All jobs</a><span aria-hidden="true">/</span><span>Bharat Regional Portal</span>
        </nav>
        <p class="eyebrow">Bharat Regional &amp; Multilingual Portal</p>
        <h1>{esc(h1)}</h1>
        {badge_html}
        <p class="hub-hero-sub">
          State-wise environment, forestry, wildlife, climate, ESG and geospatial jobs —
          हिंदी, मराठी, தமிழ், తెలుగు, ಕನ್ನಡ, বাংলা एवं ગુજરાતી क्षेत्रों हेतु क्षेत्रीय प्रवेश द्वार।
          Every listing links straight to a direct application page.
        </p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="/hindi-environment-forestry-jobs">हिंदी पोर्टल खोलें &rarr;</a>
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

{faq_block}

        <section class="hub-others" aria-labelledby="hub-others-title">
          <h2 id="hub-others-title">Explore career pathways</h2>
          <ul class="hub-other-grid">
            <li><a href="/hindi-environment-forestry-jobs"><span class="hub-other-name">हिंदी करियर पोर्टल</span><span class="hub-other-cnt">Hindi</span></a></li>
            <li><a href="/jrf-srf-project-associate-jobs"><span class="hub-other-name">JRF / SRF &amp; Project Associate Jobs</span><span class="hub-other-cnt">Academic</span></a></li>
            <li><a href="/phd-fellowships-climate-sustainability"><span class="hub-other-name">PhD &amp; Postdoctoral Fellowships</span><span class="hub-other-cnt">Doctoral</span></a></li>
            <li><a href="/forestry-wildlife-government-jobs"><span class="hub-other-name">Forestry, Wildlife &amp; Government Jobs</span><span class="hub-other-cnt">Government</span></a></li>
            <li><a href="/gis-remote-sensing-climate-jobs"><span class="hub-other-name">GIS &amp; Remote Sensing Jobs</span><span class="hub-other-cnt">Geospatial</span></a></li>
            <li><a href="/esg-carbon-sustainability-jobs"><span class="hub-other-name">ESG &amp; Carbon Market Jobs</span><span class="hub-other-cnt">Corporate</span></a></li>
          </ul>
        </section>
      </div>
    </section>
  </main>

{bsp.site_matrix_html('/' + REGIONAL_HUB_FILE)}

{footer_html(None)}

  <script defer src="/js/consent.js"></script>
<script defer src="/js/back-to-top.js"></script>
<script defer src="/js/syndication-drawer.js?v=20261023-1"></script>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Global hub (strictly separate from the India registry)
# --------------------------------------------------------------------------
GLOBAL_HUB_FILE = "global-climate-sustainability-opportunities.html"
GLOBAL_HUB_URL = SITE + "/" + GLOBAL_HUB_FILE
GLOBAL_META = bsp.page_meta(GLOBAL_HUB_FILE)

GLOBAL_REGION_ORDER: List[str] = [
    "Global / Remote",
    "Europe",
    "North America",
    "Asia-Pacific",
    "Africa & Middle East",
    "Latin America",
    "UN / Multilateral",
]

GLOBAL_KIND_ORDER: List[str] = [
    "Job / Career",
    "Fellowship",
    "Scholarship",
    "Grant / Funding",
    "Internship",
    "Competition / Award",
]

GLOBAL_FAQS: List[Tuple[str, str]] = [
    (
        "What are the Global Opportunities on Urban Forest Park?",
        "A curated international registry of climate, sustainability, forestry, energy, water, "
        "biodiversity and ESG opportunities published directly by official organisations \u2014 "
        "the UNFCCC, Green Climate Fund, UNDP, World Bank Group, IUCN, WRI, ESA, Future Earth, "
        "universities and major foundations. It covers jobs, fellowships, scholarships, grants, "
        "internships and competitions, and every entry links straight to the official application "
        "page \u2014 no fees.",
    ),
    (
        "How are India jobs and Global opportunities kept apart?",
        "The two registries are strictly separated and never mixed. The jurisdiction switcher "
        "(India Jobs / Global Opportunities) swaps the whole dataset: India jobs are "
        "state-filtered and include JRF, SRF, PhD and government vacancies, while Global "
        "opportunities replace the state dropdown with a region filter (Global / Remote, Europe, "
        "North America, Asia-Pacific, Africa & Middle East, Latin America, UN / Multilateral). "
        "The global hub is backed by global_jobs.json, a file that never contains India records.",
    ),
    (
        "Which regions do the global opportunities cover?",
        "Global / Remote, Europe, North America, Asia-Pacific, Africa & Middle East, Latin "
        "America and UN / Multilateral organisations. Remote and worldwide roles are grouped "
        "under Global / Remote, and UN bodies such as the UNFCCC, UNDP and Green Climate Fund are "
        "grouped under UN / Multilateral.",
    ),
    (
        "How do I receive new global opportunities as soon as they are published?",
        "Install the UrbanForestPark app from the registry page and enable instant job "
        "notifications \u2014 new verified listings reach your device automatically. You can also "
        "follow the daily broadcast on Telegram (@urbanforestpark) and the weekly roundup on "
        "the Urban Forest Park LinkedIn page.",
    ),
]


def global_location_label(job: Dict[str, Any]) -> str:
    city = plain(job.get("city"))
    country = plain(job.get("country"))
    region = plain(job.get("region"))
    if city and country and country not in ("Global", "Global / Remote"):
        return f"{city}, {country}"
    if country and country != "Global":
        return country
    if city:
        return f"{city} (Global)"
    return region or "Global / Remote"


def global_card_html(job: Dict[str, Any]) -> str:
    """Pre-rendered card for an international job or opportunity."""
    cat = plain(job.get("category")) or "Climate Policy, Think-Tanks & Fellowships"
    pt = position_type_of(job)
    kind = plain(job.get("opportunity_kind")) or "Job / Career"
    org = plain(job.get("organization")) or "International organisation"
    title = plain(job.get("clean_title")) or org
    location = global_location_label(job)
    deadline = plain(job.get("deadline_or_window")) or "Rolling / Open"
    badges = [
        f'<span class="badge {bsp.cat_class(cat)}">{esc(cat)}</span>',
        f'<span class="badge badge-type">{esc(pt)}</span>',
        f'<span class="badge badge-state">{bsp.PIN_SVG}{esc(location)}</span>',
    ]
    if kind != "Job / Career":
        badges.append(f'<span class="badge badge-exp">{esc(kind)}</span>')
    if deadline and deadline.lower() != "rolling / open":
        badges.append(f'<span class="badge badge-deadline">Deadline {esc(deadline)}</span>')

    skills = [
        plain(item) for item in (job.get("must_have_skills") or []) if plain(item)
    ][:3]
    quals = plain(job.get("qualification_summary"))
    comp = plain(job.get("compensation_or_fellowship"))
    elig_bits: List[str] = []
    if bsp.is_specific_qualification(quals):
        elig_bits.append(
            f"<span><strong>Eligibility:</strong> {esc(bsp.sentence(quals, 150))}</span>"
        )
    elif skills:
        elig_bits.append(f"<span><strong>Focus:</strong> {esc(', '.join(skills))}</span>")
    if bsp.is_specific_compensation(comp):
        elig_bits.append(
            f"<span><strong>Funding:</strong> {esc(bsp.sentence(comp, 120))}</span>"
        )
    elig_html = (
        '<p class="hub-card-elig">' + " ".join(elig_bits) + "</p>"
        if elig_bits
        else ""
    )
    summary = bsp.excerpt(job.get("role_summary"), 230)
    summary_html = f'<p class="hub-card-sum">{esc(summary)}</p>' if summary else ""
    apply_url = plain(job.get("apply_url"))
    # Anchor text must stay unique on a 50+ card hub. Generic "View details"
    # or "Official application" labels trip the duplicate-anchor audit.
    short_title = bsp.anchor_text(title, 40)
    official = (
        f'<a href="{esc(apply_url)}" target="_blank" rel="noopener noreferrer">'
        f'Official application: {esc(short_title)} <span aria-hidden="true">&nearr;</span></a>'
        if apply_url
        else ""
    )
    return f"""        <article class="hub-card global-card">
          <div class="hub-card-top">
            {bsp.BADGE_SEP.join(badges)}{bsp.CARD_STOP}
          </div>
          <h3 class="hub-card-title"><a href="{bsp.job_url(job)}" title="{esc(title)}">{esc(bsp.anchor_text(title))}</a>{bsp.CARD_STOP}</h3>
          <p class="hub-card-org">{esc(org)} <span class="global-card-loc">&middot; {esc(location)}</span></p>
          {elig_html}
          {summary_html}
          <p class="hub-card-foot"><a href="{bsp.job_url(job)}">View details: {esc(short_title)} <span aria-hidden="true">&rarr;</span></a>{(' ' + official) if official else ''}</p>
        </article>"""


def build_global_hub_page(
    global_active: List[Dict[str, Any]],
    today: date,
    india_count: int = 0,
    global_archive_count: int = 0,
) -> str:
    """Static hub for the strictly separated Global opportunities registry."""
    badge_html = bsp.registry_refresh_badge_html(
        today,
        india_count,
        sum(1 for job in global_active if not job.get("evergreen")),
    )
    region_counts: Dict[str, int] = {}
    kind_counts: Dict[str, int] = {}
    for job in global_active:
        region = plain(job.get("region")) or "Global / Remote"
        region_counts[region] = region_counts.get(region, 0) + 1
        kind = plain(job.get("opportunity_kind")) or "Job / Career"
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    item_entries: List[Dict[str, Any]] = []
    region_sections: List[str] = []
    ordered_regions = [r for r in GLOBAL_REGION_ORDER if region_counts.get(r)]
    for region in sorted(region_counts):
        if region not in ordered_regions:
            ordered_regions.append(region)

    for region in ordered_regions:
        matched = [
            j
            for j in global_active
            if (plain(j.get("region")) or "Global / Remote") == region
        ]
        matched.sort(
            key=lambda j: (
                str(j.get("date_added") or ""),
                str(j.get("id") or ""),
            ),
            reverse=True,
        )
        cards_html = "\n".join(global_card_html(job) for job in matched)
        if not cards_html:
            cards_html = (
                '        <p class="hub-empty">New verified opportunities for this region '
                'are being checked against official sources.</p>'
            )
        quick_links = "\n".join(
            f'            <li><a href="{bsp.job_url(job)}" title="{esc(plain(job.get("clean_title")))}">'
            f'Browse {esc(region)}: {esc(bsp.anchor_text(plain(job.get("clean_title")), 38))}</a></li>'
            for job in matched[:2]
        )
        region_sections.append(
            f"""      <section class="global-region region-card" id="gregion-{bsp.state_slug(region)}">
        <div class="global-region-head">
          <div>
            <h2>{esc(region)} <span class="region-cnt">{region_counts[region]}</span></h2>
            <p class="region-total"><strong>{region_counts[region]}</strong> verified global record(s) currently open, including career portals</p>
          </div>
          <a class="global-region-link" href="/?region=global&amp;gregion={quote(region)}" rel="nofollow">Open {esc(region)} roles &rarr;</a>
        </div>
        <ul class="region-states global-region-quick-links">
{quick_links}
        </ul>
        <div class="hub-list global-card-grid">
{cards_html}
        </div>
      </section>"""
        )
        for job in matched:
            item_entries.append(
                {
                    "@type": "ListItem",
                    "position": len(item_entries) + 1,
                    "url": SITE + "/jobs/" + quote(plain(job.get("id"))),
                    "name": plain(job.get("clean_title")),
                }
            )

    regions_html = "\n\n".join(region_sections) or (
        '      <section class="global-region"><h2>Global / Remote</h2>'
        '<p class="region-total">Listings are being verified \u2014 check back shortly.</p></section>'
    )
    kind_links = "\n".join(
        f'            <li><a href="/?region=global&amp;kind={quote(kind)}" rel="nofollow">'
        f'{esc(kind)} <span class="region-cnt">{kind_counts.get(kind, 0)}</span></a></li>'
        for kind in GLOBAL_KIND_ORDER
    )

    total_jobs = len(global_active)
    h1 = bsp.plain(GLOBAL_META['h1'])
    title = bsp.plain(GLOBAL_META['title'])
    desc = bsp.plain(GLOBAL_META['description'])

    collection = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": title,
            "description": desc,
            "url": GLOBAL_HUB_URL,
            "inLanguage": "en",
            "dateModified": today.isoformat(),
            "isPartOf": {
                "@type": "WebSite",
                "name": "Urban Forest Park \u2014 Green Jobs, Grants & Fellowships",
                "url": SITE + "/",
            },
            "about": {"@type": "Thing", "name": "Global climate and sustainability opportunities"},
        }
    )
    item_list = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Global climate and sustainability opportunities",
            "numberOfItems": len(item_entries),
            "itemListElement": item_entries,
        }
    )
    breadcrumb = jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Career Registry", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Global Opportunities", "item": GLOBAL_HUB_URL},
            ],
        }
    )
    faq_ld = faq_jsonld(GLOBAL_FAQS)
    organization = bsp.organization_jsonld()
    website = bsp.website_jsonld()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    {bsp.GA_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

{bsp.THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(desc)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{GLOBAL_HUB_URL}">
    <link rel="alternate" hreflang="en-IN" href="{SITE}/">
    <link rel="alternate" hreflang="hi-IN" href="{HINDI_HUB_URL}">
    <link rel="alternate" hreflang="en" href="{GLOBAL_HUB_URL}">
    <link rel="alternate" hreflang="x-default" href="{SITE}/">

    <!-- Open Graph / social -->
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park \u2014 Green Jobs, Grants &amp; Fellowships">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(desc)}">
    <meta property="og:url" content="{GLOBAL_HUB_URL}">
    <meta property="og:image" content="{GLOBAL_IMAGE_URL}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="675">
    <meta property="og:locale" content="en">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(desc)}">
    <meta name="twitter:image" content="{GLOBAL_IMAGE_URL}">
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    <!-- Favicons -->
{bsp.FAVICONS}

    {FONTS_HI}

    <!-- Registry styles (shared design system) + hub styles -->
    <link rel="stylesheet" href="/styles/jobs.css">
    <link rel="stylesheet" href="/styles/hub.css">

    <!-- Structured data -->
{organization}
{website}
{collection}
{item_list}
{breadcrumb}
{faq_ld}

    <script defer src="/js/hub.js"></script>
</head>

<body>
  <a class="skip-link" href="#global-grid">Skip to global listings</a>

{header_html('global')}

  <main>
    <section class="hub-hero">
      <div class="hub-hero-inner">
        <nav class="hub-crumbs" aria-label="Breadcrumb">
          <a href="/">All jobs</a><span aria-hidden="true">/</span><span>Global Opportunities</span>
        </nav>
        <p class="eyebrow">\U0001F30D Global Opportunities Registry \u2014 International</p>
        <h1>{esc(h1)}</h1>
        {badge_html}
        <p class="hub-hero-sub">
          A strictly separate registry of verified international opportunities \u2014 jobs, grants,
          scholarships, fellowships, internships and competitions from the UNFCCC, Green Climate
          Fund, UNDP, World Bank Group, IUCN, WRI, ESA, Future Earth and other official
          organisations. Every listing links straight to a direct application page.
        </p>
        <div class="hub-hero-actions">
          <a class="btn btn-primary" href="#global-grid">Browse global opportunities &rarr;</a>
          <a class="btn btn-outline" href="/">India Jobs</a>
        </div>
        <dl class="hub-stats">
          <div><dt>Global listings</dt><dd>{total_jobs}</dd></div>
          <div><dt>Regions</dt><dd>{len(ordered_regions)}</dd></div>
          <div><dt>Opportunity kinds</dt><dd>{len([k for k in GLOBAL_KIND_ORDER if kind_counts.get(k)])}</dd></div>
          <div><dt>Updated</dt><dd>{esc(long_date(today))}</dd></div>
        </dl>
      </div>
    </section>

    <section class="hub-main" id="global-grid">
      <div class="hub-main-inner">
        <div class="hub-main-head">
          <h2>Browse global opportunities by region</h2>
          <p>Every card links to its verified dossier and the organisation\u2019s official
          application page. Counts refresh with each pipeline run; closed roles move to the
          global archive ({global_archive_count} archived). India jobs remain in their own
          registry \u2014 the two datasets are never mixed.</p>
        </div>
        <div class="global-region-list">
{regions_html}
        </div>

        <section class="hub-others" aria-labelledby="global-kinds-title">
          <h2 id="global-kinds-title">Browse by opportunity kind</h2>
          <ul class="region-states region-states-wide">
{kind_links}
          </ul>
        </section>

        <section class="hub-others" aria-labelledby="global-others-title">
          <h2 id="global-others-title">Explore career pathways</h2>
          <ul class="hub-other-grid">
            <li><a href="#global-grid"><span class="hub-other-name">Global opportunities by region</span><span class="hub-other-cnt">International</span></a></li>
            <li><a href="/jrf-srf-project-associate-jobs"><span class="hub-other-name">JRF / SRF &amp; Project Associate Jobs</span><span class="hub-other-cnt">India</span></a></li>
            <li><a href="/phd-fellowships-climate-sustainability"><span class="hub-other-name">PhD &amp; Postdoctoral Fellowships</span><span class="hub-other-cnt">India</span></a></li>
            <li><a href="/forestry-wildlife-government-jobs"><span class="hub-other-name">Forestry, Wildlife &amp; Government Jobs</span><span class="hub-other-cnt">India</span></a></li>
            <li><a href="/gis-remote-sensing-climate-jobs"><span class="hub-other-name">GIS &amp; Remote Sensing Jobs</span><span class="hub-other-cnt">India</span></a></li>
            <li><a href="/esg-carbon-sustainability-jobs"><span class="hub-other-name">ESG &amp; Carbon Market Jobs</span><span class="hub-other-cnt">India</span></a></li>
            <li><a href="/hindi-environment-forestry-jobs"><span class="hub-other-name">हिंदी करियर पोर्टल</span><span class="hub-other-cnt">Hindi</span></a></li>
            <li><a href="/bharat-regional-green-jobs"><span class="hub-other-name">Bharat Regional Portal</span><span class="hub-other-cnt">India</span></a></li>
          </ul>
        </section>

{faq_section_html(GLOBAL_FAQS, GLOBAL_FAQ_HEADING)}
      </div>
    </section>
  </main>

{bsp.site_matrix_html('/' + GLOBAL_HUB_FILE, include_states=False)}

{footer_html(None)}

  <script defer src="/js/consent.js"></script>
<script defer src="/js/back-to-top.js"></script>
<script defer src="/js/syndication-drawer.js?v=20261023-1"></script>
</body>
</html>
"""
