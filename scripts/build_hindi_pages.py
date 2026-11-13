#!/usr/bin/env python3
"""Build Hindi (hi-IN) versions of the core hub pages.

The English site already covers the full cluster (hubs, exam guides, role
profiles, glossary, comparisons). This builder adds the entry points a
Hindi-speaking visitor needs first: the five pathway hubs plus a glossary
index. Each page declares hreflang so search engines can serve the right
language version.

Run after build_seo_pages.py:

    py scripts/build_hindi_pages.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
plain = beh.plain
cards = beh.cards
hero = beh.hero
section = beh.section
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local

JOBS = beh.active(beh.load(beh.JOBS_PATH))
GLOBAL = beh.active(beh.load(beh.GLOBAL_PATH))
POOL = JOBS + GLOBAL

HINDI_FONT = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap" rel="stylesheet">'
)


def hindi_shell(*, title: str, description: str, canonical: str, body: str, jsonld: str, en_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="hi-IN">
<head>
    {beh.bsp.GTM_SCRIPT}

    {beh.bsp.GA_SCRIPT}

    {beh.bsp.SWG_SCRIPT}

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    {beh.bsp.THEME_BOOTSTRAP}

    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{canonical}">
    <link rel="alternate" hreflang="hi-IN" href="{canonical}">
    <link rel="alternate" hreflang="en-IN" href="{en_url}">
    <link rel="alternate" hreflang="en" href="{SITE}/global-climate-sustainability-opportunities">
    <link rel="alternate" hreflang="x-default" href="{en_url}">

    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Urban Forest Park - हिंदी ग्रीन जॉब्स">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:locale" content="hi_IN">
    <meta name="twitter:card" content="summary_large_image">

    {jsonld}
    <meta name="theme-color" id="meta-theme-color" content="#F8FAFC">

    {beh.bsp.FAVICONS}

    {HINDI_FONT}

    <link rel="stylesheet" href="/styles/jobs.css?v=20261108e">
    <link rel="stylesheet" href="/styles/hub.css">
    <link rel="stylesheet" href="/styles/expansion.css">
</head>
<body style="font-family: 'Noto Sans Devanagari', 'Inter', sans-serif;">
    {beh.bsp.GTM_NOSCRIPT}
  <a class="skip-link" href="#main">Skip to content</a>

{beh.bsp.header_html('registry')}

  <main id="main">
{body}
  </main>

{beh.bsp.footer_html()}
</body>
</html>
"""


def match_government(job: Dict[str, Any]) -> bool:
    org = str(job.get("organization") or "").lower()
    category = str(job.get("category") or "").lower()
    if "forestry" in category or "wildlife" in category:
        return True
    return any(t in org for t in ("ministry", "moef", "csir", "icar", "forest survey", "wildlife institute", "pollution control", "forest department", "campa"))


def match_internship(job: Dict[str, Any]) -> bool:
    import re
    text = " ".join(str(job.get(k) or "") for k in ("category", "clean_title", "opportunity_kind", "position_type")).lower()
    return bool(re.search(r"\b(intern|internship|trainee|traineeship)\b", text))


def match_entry(job: Dict[str, Any]) -> bool:
    import re
    if plain(job.get("category")) not in {"Academic, JRF, SRF & PhD Positions", "Forestry, Wildlife & Afforestation", "ESG, Carbon Markets & Corporate Sustainability", "Research Associate & Project Staff (Contractual)", "GIS, Remote Sensing & Earth Observation", "Internships & Student Traineeships", "Climate Policy, Think-Tanks & Fellowships"}:
        return False
    title = plain(job.get("clean_title")).lower()
    if re.search(r"\b(course|workshop|webinar|conclave|summit|training programme|bootcamp)\b", title):
        return False
    text = " ".join(str(job.get(k) or "") for k in ("experience_level", "clean_title")).lower()
    return any(t in text for t in ("entry", "fresher", "graduate", "junior", "trainee", "assistant"))


def match_funding(job: Dict[str, Any]) -> bool:
    kind = plain(job.get("opportunity_kind"))
    category = plain(job.get("category"))
    return (kind in {"Fellowship", "Scholarship", "Grant / Funding", "Competition / Award"}
            or category in {"Fellowships & Leadership Programs", "Scholarships & Doctoral Support", "Grants & Research Funding", "Workshops, Training & Capacity Building", "Competitions, Hackathons & Awards", "Ambassador & Fellowship Programs", "Conferences, Summits & Events", "Visiting Fellowships & Short-Term Research"})


# ---------------------------------------------------------------------------
# 1. Government tracker (Hindi)
# ---------------------------------------------------------------------------
def build_gov_hi() -> None:
    live = sorted([j for j in JOBS if match_government(j)], key=lambda j: str(j.get("valid_through") or "9999"))
    body = "\n".join([
        hero("सरकारी और सार्वजनिक क्षेत्र", "सरकारी पर्यावरण, वन और वन्यजीव भर्ती", "भारत में पर्यावरण वैज्ञानिकों, वन अधिकारियों और वन्यजीव शोधकर्ताओं को भर्ती करने वाले सार्वजनिक निकायों का ट्रैकर, आधिकारिक पोर्टल के साथ।", [("निकाय", "9"), ("लाइव ओपनिंग", str(len(live))), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>भर्ती ट्रैकर</h2>
        <p>हर पंक्ति आधिकारिक पोर्टल की ओर इशारा करती है, क्योंकि अधिसूचना तिथियाँ हर चक्र में बदलती हैं।</p>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>भर्ती निकाय</th><th>क्या भर्ती करते हैं</th><th>चक्र</th><th>आधिकारिक पोर्टल</th></tr></thead>
          <tbody>
            <tr><td><strong>UPSC - भारतीय वन सेवा (IFS)</strong></td><td>सिविल सेवा परीक्षा के माध्यम से IFS चयन</td><td>वार्षिक UPSC चक्र</td><td><a href="https://upsc.gov.in" target="_blank" rel="noopener noreferrer">upsc.gov.in &nearr;</a></td></tr>
            <tr><td><strong>MoEFCC</strong></td><td>युवा पेशेवर, परियोजना स्टाफ, प्रतिनियुक्ति पद</td><td>अधिसूचना-आधारित</td><td><a href="https://moef.gov.in/recruitment/update" target="_blank" rel="noopener noreferrer">moef.gov.in &nearr;</a></td></tr>
            <tr><td><strong>CSIR</strong></td><td>परियोजना सहयोगी, JRF/SRF, शोध सहयोगी</td><td>संस्थान-वार वॉक-इन और विज्ञापित पद</td><td><a href="https://www.csir.res.in" target="_blank" rel="noopener noreferrer">csir.res.in &nearr;</a></td></tr>
            <tr><td><strong>ICAR</strong></td><td>JRF/SRF, युवा पेशेवर, परियोजना स्टाफ</td><td>संस्थान-वार रिक्तियाँ</td><td><a href="https://icar.org.in/en/archive-vacancies" target="_blank" rel="noopener noreferrer">icar.org.in &nearr;</a></td></tr>
            <tr><td><strong>Forest Survey of India (FSI)</strong></td><td>तकनीकी, परियोजना और मानचित्रण पद</td><td>अधिसूचना-आधारित</td><td><a href="https://fsi.nic.in" target="_blank" rel="noopener noreferrer">fsi.nic.in &nearr;</a></td></tr>
            <tr><td><strong>Wildlife Institute of India (WII)</strong></td><td>शोध पद, JRF/परियोजना स्टाफ, PG डिप्लोमा</td><td>रोलिंग रिक्तियाँ + वार्षिक प्रवेश</td><td><a href="https://wii.gov.in" target="_blank" rel="noopener noreferrer">wii.gov.in &nearr;</a></td></tr>
            <tr><td><strong>CPCB</strong></td><td>वैज्ञानिक, इंजीनियर, तकनीकी पद</td><td>अधिसूचना-आधारित</td><td><a href="https://cpcb.nic.in" target="_blank" rel="noopener noreferrer">cpcb.nic.in &nearr;</a></td></tr>
            <tr><td><strong>मध्य प्रदेश वन विभाग</strong></td><td>वन रक्षक, रेंजर, फील्ड भर्ती</td><td>राज्य-विशिष्ट</td><td><a href="https://www.mpforest.gov.in" target="_blank" rel="noopener noreferrer">mpforest.gov.in &nearr;</a></td></tr>
            <tr><td><strong>ओडिशा वन विभाग</strong></td><td>वन रक्षक, फॉरेस्टर, फील्ड भर्ती</td><td>राज्य-विशिष्ट</td><td><a href="https://forest.odisha.gov.in" target="_blank" rel="noopener noreferrer">forest.odisha.gov.in &nearr;</a></td></tr>
          </tbody>
        </table></div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>इस मार्ग में लाइव ओपनिंग ({len(live)})</h2>
        <p>रजिस्ट्री से खींचा गया, बंद होने की तारीख के अनुसार क्रमबद्ध।</p>
        <div class="hub-list">
{cards(live[:12]) if live else '<p class="hub-empty">अभी इस मार्ग में कोई ओपनिंग नहीं। नई भर्तियाँ रोज़ जोड़ी जाती हैं।</p>'}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/exams">परीक्षा और पात्रता गाइड</a></li>
          <li><a href="/glossary">शब्दावली (Glossary)</a></li>
          <li><a href="/green-careers">ग्रीन करियर मार्ग</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("सरकारी पर्यावरण भर्ती", f"{SITE}/hindi-government-jobs")])
    write_sub(PUBLIC, "hindi-government-jobs", hindi_shell(title="सरकारी पर्यावरण, वन और वन्यजीव भर्ती 2026", description="भारतीय वन सेवा, MoEFCC, CSIR, ICAR, FSI, WII, CPCB और राज्य वन विभाग भर्ती का ट्रैकर, आधिकारिक पोर्टल के साथ।", canonical=f"{SITE}/hindi-government-jobs", body=body, jsonld=jsonld, en_url=f"{SITE}/government-environment-jobs"))


# ---------------------------------------------------------------------------
# 2. Internships (Hindi)
# ---------------------------------------------------------------------------
def build_internships_hi() -> None:
    interns = sorted([j for j in JOBS if match_internship(j)], key=lambda j: str(j.get("valid_through") or "9999"))
    entry = sorted([j for j in JOBS if match_entry(j) and j not in interns], key=lambda j: str(j.get("valid_through") or "9999"))
    body = "\n".join([
        hero("छात्र और शुरुआती करियर", "ग्रीन इंटर्नशिप और एंट्री-लेवल पर्यावरण नौकरियाँ", "पर्यावरण, वन, GIS, ESG और जलवायु क्षेत्र में सत्यापित इंटर्नशिप, ट्रेनीशिप और पहली नौकरी के अवसर, आधिकारिक आवेदन लिंक के साथ।", [("इंटर्नशिप", str(len(interns))), ("एंट्री-लेवल", str(len(entry))), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>इंटर्नशिप और ट्रेनीशिप ({len(interns)})</h2>
        <p>पोर्टफोलियो बनाने वाले अल्पकालिक अवसर। जहाँ आयोजक तिथि प्रकाशित करता है, वहाँ डेडलाइन दिखाई गई है।</p>
        <div class="hub-list">
{cards(interns) if interns else '<p class="hub-empty">अभी कोई इंटर्नशिप नहीं। नई भर्तियाँ रोज़ जोड़ी जाती हैं।</p>'}
        </div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>एंट्री-लेवल और जूनियर भूमिकाएँ ({len(entry)})</h2>
        <p>सहायक, सहयोगी और फ्रेशर-अनुकूल पद।</p>
        <div class="hub-list">
{cards(entry[:20]) if entry else '<p class="hub-empty">अभी कोई एंट्री-लेवल भूमिका नहीं।</p>'}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>पतले CV के साथ आवेदन कैसे करें</h2>
        <ul class="check-list">
          <li><strong>एक पेज, एक दिशा।</strong> पाठ्यक्रम, फील्ड वर्क, टूल्स और एक ठोस आउटपुट पर ध्यान दें।</li>
          <li><strong>टूल्स का नाम लें।</strong> QGIS, R, Python, Google Earth Engine, Excel — जो आप वास्तव में उपयोग कर सकते हैं।</li>
          <li><strong>एक डिलीवरेबल दिखाएँ।</strong> एक नक्शा, रिपोर्ट, डेटासेट या फील्ड नोट दिलचस्पी के दावे से बेहतर है।</li>
          <li><strong>अधिसूचना से मिलाएँ।</strong> आधिकारिक विज्ञापन की योग्यता और अनुभव शब्दावली को दोहराएँ।</li>
          <li><strong>मोड जाँचें।</strong> वॉक-इन के लिए दस्तावेज़ और रिपोर्टिंग समय चाहिए; ईमेल आवेदन के लिए एक PDF।</li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/green-internships">English: Green Internships</a></li>
          <li><a href="/green-careers">ग्रीन करियर मार्ग</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("ग्रीन इंटर्नशिप", f"{SITE}/hindi-green-internships")])
    write_sub(PUBLIC, "hindi-green-internships", hindi_shell(title="ग्रीन इंटर्नशिप और एंट्री-लेवल पर्यावरण नौकरियाँ 2026", description="भारत में पर्यावरण, वन, GIS, ESG और जलवायु क्षेत्र में सत्यापित इंटर्नशिप और एंट्री-लेवल नौकरियाँ।", canonical=f"{SITE}/hindi-green-internships", body=body, jsonld=jsonld, en_url=f"{SITE}/green-internships"))


# ---------------------------------------------------------------------------
# 3. Fellowship deadlines (Hindi)
# ---------------------------------------------------------------------------
def build_fellowship_hi() -> None:
    pool = JOBS + GLOBAL
    funding = [j for j in pool if match_funding(j)]
    dated = sorted([(beh.parse_date(j.get("valid_through")), j) for j in funding if beh.parse_date(j.get("valid_through")) and beh.parse_date(j.get("valid_through")) >= TODAY], key=lambda x: x[0])
    rolling = [j for j in funding if not beh.parse_date(j.get("valid_through"))]
    rows = "\n".join(f"          <tr><td><time datetime='{p.isoformat()}'>{p.strftime('%d %b %Y')}</time></td><td><a href='{beh.bsp.job_url(j)}' title='{esc(plain(j.get('clean_title')))}'><strong>{esc(beh.bsp.anchor_text(plain(j.get('clean_title'))))}</strong></a><br><span class='muted'>{esc(plain(j.get('organization')))}</span></td><td>{esc(plain(j.get('category')))}</td><td>{esc(plain(j.get('city')) or plain(j.get('country')))}</td></tr>" for p, j in dated[:40])
    body = "\n".join([
        hero("फंडिंग और प्रशिक्षण कैलेंडर", "फेलोशिप, छात्रवृत्ति और अनुदान डेडलाइन", "जलवायु, पर्यावरण और सस्टेनेबिलिटी में फेलोशिप, छात्रवृत्ति, अनुदान, प्रतियोगिता और प्रशिक्षण की एक डेडलाइन कैलेंडर, अगले बंद होने वाले के अनुसार क्रमबद्ध।", [("डेटेड डेडलाइन", str(len(dated))), ("रोलिंग/ओपन", str(len(rolling))), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>अगले बंद होने वाले</h2>
        <p>बंद होने की तारीख के अनुसार क्रमबद्ध। दो हफ्ते के अंदर वाले चिह्नित हैं।</p>
        <div class="table-wrap"><table class="data-table">
          <thead><tr><th>डेडलाइन</th><th>अवसर</th><th>प्रकार</th><th>स्थान</th></tr></thead>
          <tbody>{rows or '<tr><td colspan="4">अभी कोई डेटेड डेडलाइन नहीं।</td></tr>'}</tbody>
        </table></div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>रोलिंग और ओपन कॉल ({len(rolling)})</h2>
        <p>कोई निश्चित बंद तारीख नहीं — जल्दी आवेदन करें।</p>
        <div class="hub-list">
{cards(rolling[:20]) if rolling else '<p class="hub-empty">अभी कोई रोलिंग कॉल नहीं।</p>'}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/fellowship-deadlines">English: Fellowship Deadlines</a></li>
          <li><a href="/green-careers">ग्रीन करियर मार्ग</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("फेलोशिप डेडलाइन", f"{SITE}/hindi-fellowship-deadlines")])
    write_sub(PUBLIC, "hindi-fellowship-deadlines", hindi_shell(title="फेलोशिप, छात्रवृत्ति और अनुदान डेडलाइन 2026-27", description="जलवायु और पर्यावरण फेलोशिप, छात्रवृत्ति, अनुदान और प्रशिक्षण डेडलाइन एक कैलेंडर में।", canonical=f"{SITE}/hindi-fellowship-deadlines", body=body, jsonld=jsonld, en_url=f"{SITE}/fellowship-deadlines"))


# ---------------------------------------------------------------------------
# 4. dMRV (Hindi)
# ---------------------------------------------------------------------------
def build_dmrv_hi() -> None:
    tools = [
        ("Nagar Van dMRV डैशबोर्ड", "/dashboard", "शहरी वन प्लॉट के लिए निगरानी दृश्य: कैनोपी, कार्बन, जैवविविधता और शीतलन संकेतक एक जगह।"),
        ("लाइव साइट इनसाइट्स", "/explore-dashboard", "Nagar Van साइटों के लिए थीमैटिक मानचित्र, मौसम संदर्भ और क्षेत्रीय प्रोफाइल।"),
        ("Urban Forest Green Calculator", "/green-calculator", "किसी साइट के लिए कार्बन सीक्वेस्ट्रेशन, जैवविविधता, शीतलन, वायु गुणवत्ता और स्टॉर्मवॉटर लाभ का अनुमान।"),
        ("Nagar Van Finder", "/nagar-van-finder", "राज्य के अनुसार Nagar Van साइटें खोजें।"),
        ("स्पेशियल डेटा एक्सप्लोरर", "/spatial-data", "30 चुनिंदा साइटों के लिए पर्यावरण प्रभाव प्रोफाइल।"),
        ("पब्लिक सर्वे", "/public-survey", "शहरी वन साइटों की स्थिति और उपयोग पर सामुदायिक फीडबैक।"),
    ]
    tool_cards = "\n".join(f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="{href}">{esc(name)}</a></h3>
          <p class="hub-card-sum">{esc(copy)}</p>
          <p class="hub-card-foot"><a href="{href}">टूल खोलें &rarr;</a></p>
        </article>""" for name, href, copy in tools)
    body = "\n".join([
        hero("संस्थागत टूल्स", "Nagar Van dMRV, Green Calculator और शहरी वन डेटा", "शहरी वनों के लिए डिजिटल मॉनिटरिंग, रिपोर्टिंग और वेरिफिकेशन टूलिंग — जो टीमें Nagar Van साइटें लगाती, फंड करती और निरीक्षण करती हैं।", [("टूल्स", str(len(tools))), ("चुनिंदा साइटें", "30"), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>टूलकिट</h2>
        <p>हर टूल शहरी वन चक्र में एक अलग सवाल का जवाब देता है: साइट कहाँ है, यह क्या देता है, और यह कैसे बदल रहा है।</p>
        <div class="hub-list">
{tool_cards}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>dMRV का अर्थ यहाँ</h2>
        <ul class="check-list">
          <li><strong>Monitor:</strong> एक बार की वृक्षारोपण गिनती के बजाय समय के साथ साइट की स्थिति और लाभ संकेतक ट्रैक करें।</li>
          <li><strong>Report:</strong> फील्ड और स्पेशियल इनपुट को एक सुसंगत प्रोफाइल में बदलें जिसे फंडर और रिव्यूअर के साथ साझा किया जा सके।</li>
          <li><strong>Verify:</strong> विधि को दृश्यमान रखें — इनपुट, अनुमान और गणना — ताकि तीसरा पक्ष संख्याओं की जाँच कर सके।</li>
          <li><strong>Compare:</strong> अगला रखरखाव और निवेश कहाँ जाए, यह तय करने के लिए साइटों में एक ही संकेतक उपयोग करें।</li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/dashboard">लाइव dMRV डैशबोर्ड</a></li>
          <li><a href="/green-calculator">Green Calculator</a></li>
          <li><a href="/nagar-van-finder">Nagar Van Finder</a></li>
          <li><a href="/dmrv">English: dMRV overview</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("Nagar Van dMRV और शहरी वन डेटा", f"{SITE}/hindi-dmrv")])
    write_sub(PUBLIC, "hindi-dmrv", hindi_shell(title="Nagar Van dMRV, Green Calculator और शहरी वन डेटा", description="Nagar Van शहरी वनों के लिए डिजिटल मॉनिटरिंग, रिपोर्टिंग और वेरिफिकेशन टूल्स।", canonical=f"{SITE}/hindi-dmrv", body=body, jsonld=jsonld, en_url=f"{SITE}/dmrv"))


# ---------------------------------------------------------------------------
# 5. Green careers (Hindi)
# ---------------------------------------------------------------------------
def build_careers_hi() -> None:
    paths = [
        ("शोध और अकादमिक", "/jrf-srf-project-associate-jobs", "JRF/SRF और परियोजना सहयोगी भूमिकाएँ मानक प्रवेश बिंदु हैं।", lambda j: "JRF" in plain(j.get("category")) or "Academic" in plain(j.get("category"))),
        ("वन और वन्यजीव", "/forestry-wildlife-government-jobs", "फील्ड और सरकारी मार्ग: वन रक्षक, रेंजर, वन्यजीव जीवविज्ञान।", lambda j: "Forestry" in plain(j.get("category")) or "Wildlife" in plain(j.get("category"))),
        ("ESG, कार्बन और सस्टेनेबिलिटी", "/esg-carbon-sustainability-jobs", "कॉर्पोरेट और कंसल्टिंग मार्ग: BRSR और ESG रिपोर्टिंग, कार्बन अकाउंटिंग।", lambda j: "ESG" in plain(j.get("category"))),
        ("GIS और रिमोट सेंसिंग", "/gis-remote-sensing-climate-jobs", "स्पेशियल एनालिस्ट से अर्थ-ऑब्जर्वेशन विशेषज्ञ तक।", lambda j: "GIS" in plain(j.get("category"))),
        ("जलवायु नीति और थिंक टैंक", "/sustainability-jobs-india", "थिंक टैंक, बहुपक्षीय और जलवायु वित्त में शोध और नीति भूमिकाएँ।", lambda j: "Climate Policy" in plain(j.get("category"))),
        ("इंटर्नशिप और एंट्री लेवल", "/green-internships", "पोर्टफोलियो बनाने वाले अल्पकालिक और पहली नौकरी के अवसर।", lambda j: match_internship(j) or match_entry(j)),
    ]
    active_jobs = JOBS
    cards_html = "\n".join(f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="{href}">{esc(name)}</a></h3>
          <p class="hub-card-sum">{esc(copy)}</p>
          <p class="hub-card-foot"><span>{sum(1 for j in active_jobs if m(j))} खुले हैं</span> <a href="{href}">देखें &rarr;</a></p>
        </article>""" for name, href, copy, m in paths)
    body = "\n".join([
        hero("करियर इंटेलिजेंस", "भारत में ग्रीन करियर: मार्ग, भूमिकाएँ और वेतन", "ग्रीन अर्थव्यवस्था वास्तव में कैसे भर्ती करती है — प्रवेश बिंदु, संक्रमण और वेतन बैंड।", [("मार्ग", str(len(paths))), ("सक्रिय भूमिकाएँ", str(len(active_jobs))), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>एक मार्ग चुनें</h2>
        <p>हर मार्ग का अपना प्रवेश क्रेडेंशियल, भर्ती चक्र और शिखर है।</p>
        <div class="hub-list">
{cards_html}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>मार्ग कैसे जुड़ते हैं</h2>
        <ul class="check-list">
          <li><strong>शोध मार्ग:</strong> JRF/SRF &rarr; PhD पंजीकरण &rarr; शोध सहयोगी &rarr; वैज्ञानिक या फैकल्टी।</li>
          <li><strong>कॉर्पोरेट मार्ग:</strong> एनालिस्ट या इंटर्न &rarr; ESG/कार्बन सहयोगी &rarr; मैनेजर &rarr; सस्टेनेबिलिटी हेड।</li>
          <li><strong>जियोस्पेशियल मार्ग:</strong> GIS एग्जीक्यूटिव &rarr; एनालिस्ट &rarr; रिमोट-सेंसिंग विशेषज्ञ &rarr; अर्थ-ऑब्जर्वेशन लीड।</li>
          <li><strong>सार्वजनिक मार्ग:</strong> वन रक्षक या फील्ड सहायक &rarr; रेंजर/RFO &rarr; राज्य वन सेवा &rarr; IFS।</li>
        </ul>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>वेतन और प्रगति</h2>
        <p><a href="/salary-guide">वेतन गाइड</a> भूमिका, शहर और अनुभव के अनुसार बैंड एकत्र करता है। सरकारी पद वेतन-मैट्रिक्स नियमों का पालन करते हैं।</p>
        <p><a class="btn btn-primary" href="/salary-guide">वेतन गाइड खोलें &rarr;</a></p>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/green-careers">English: Green Careers</a></li>
          <li><a href="/exams">परीक्षा और पात्रता गाइड</a></li>
          <li><a href="/glossary">शब्दावली</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("ग्रीन करियर", f"{SITE}/hindi-green-careers")])
    write_sub(PUBLIC, "hindi-green-careers", hindi_shell(title="भारत में ग्रीन करियर 2026: मार्ग, भूमिकाएँ और वेतन", description="भारत में ग्रीन करियर मार्ग — शोध, वन, ESG, GIS, जलवायु नीति और इंटर्नशिप।", canonical=f"{SITE}/hindi-green-careers", body=body, jsonld=jsonld, en_url=f"{SITE}/green-careers"))


# ---------------------------------------------------------------------------
# 6. Glossary index (Hindi)
# ---------------------------------------------------------------------------
def build_glossary_hi() -> None:
    terms = [
        ("BRSR", "Business Responsibility and Sustainability Reporting", "SEBI का रिपोर्टिंग फ्रेमवर्क।", "/glossary/brsr"),
        ("ESG", "Environmental, Social, Governance", "पर्यावरण, सामाजिक और शासन कारक।", "/glossary/esg"),
        ("GHG Protocol", "Greenhouse Gas Protocol", "ग्रीनहाउस गैस उत्सर्जन मापने का मानक।", "/glossary/ghg-protocol"),
        ("Carbon credit", "कार्बन क्रेडिट", "एक टन CO2e कमी का प्रमाणपत्र।", "/glossary/carbon-credit"),
        ("Net zero", "नेट ज़ीरो", "उत्सर्जन को शून्य तक कम करना।", "/glossary/net-zero"),
        ("SBTi", "Science Based Targets initiative", "विज्ञान-आधारित उत्सर्जन लक्ष्य।", "/glossary/sbti"),
        ("dMRV", "Digital Monitoring, Reporting, Verification", "डिजिटल निगरानी और वेरिफिकेशन।", "/glossary/dmrv"),
        ("Nagar Van", "नगर वन", "शहरी वन योजना।", "/glossary/nagar-van"),
        ("CAMPA", "Compensatory Afforestation Fund", "प्रतिपूरक वनीकरण निधि।", "/glossary/campa"),
        ("JRF", "Junior Research Fellow", "जूनियर रिसर्च फेलो।", "/glossary/jrf"),
        ("SRF", "Senior Research Fellow", "सीनियर रिसर्च फेलो।", "/glossary/srf"),
        ("EIA", "Environmental Impact Assessment", "पर्यावरण प्रभाव आकलन।", "/glossary/eia"),
        ("EHS", "Environment, Health, Safety", "पर्यावरण, स्वास्थ्य, सुरक्षा।", "/glossary/ehs"),
        ("Circular economy", "सर्कुलर इकॉनमी", "अपशिष्ट रहित अर्थव्यवस्था।", "/glossary/circular-economy"),
        ("Greenwashing", "ग्रीनवॉशिंग", "भ्रामक पर्यावरणीय दावे।", "/glossary/greenwashing"),
    ]
    term_cards = "\n".join(f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="{url}">{esc(term)} <span class="muted">({esc(full)})</span></a></h3>
          <p class="hub-card-sum">{esc(desc)}</p>
          <p class="hub-card-foot"><a href="{url}">English में पढ़ें &rarr;</a></p>
        </article>""" for term, full, desc, url in terms)
    body = "\n".join([
        hero("शब्दावली", "ग्रीन जॉब्स और जलवायु शब्दावली", "पर्यावरण नौकरी अधिसूचनाओं में बार-बार आने वाले शब्दों की सरल हिंदी में व्याख्या, आधिकारिक स्रोत के साथ।", [("शब्द", str(len(terms))), ("अपडेट", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>शब्द</h2>
        <p>परिभाषाएँ संक्षिप्त हैं और आधिकारिक स्रोत की ओर इशारा करती हैं। जहाँ कानूनी परिभाषा है, वही मान्य है।</p>
        <div class="hub-list">
{term_cards}
        </div>
      </div>
    </section>""",
        """    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>संबंधित पृष्ठ</h2>
        <ul class="check-list">
          <li><a href="/hindi-environment-forestry-jobs">हिंदी पर्यावरण और वन नौकरी पोर्टल</a></li>
          <li><a href="/glossary">English: Full Glossary</a></li>
          <li><a href="/green-careers">ग्रीन करियर मार्ग</a></li>
        </ul>
      </div>
    </section>""",
    ])
    jsonld = "\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("ग्रीन जॉब्स शब्दावली", f"{SITE}/hindi-glossary")])
    write_sub(PUBLIC, "hindi-glossary", hindi_shell(title="ग्रीन जॉब्स और जलवायु शब्दावली", description="ESG, BRSR, GHG Protocol, कार्बन क्रेडिट, नेट ज़ीरो, SBTi, dMRV, नगर वन, CAMPA, JRF, SRF, EIA, EHS और सर्कुलर इकॉनमी की हिंदी व्याख्या।", canonical=f"{SITE}/hindi-glossary", body=body, jsonld=jsonld, en_url=f"{SITE}/glossary"))


def main() -> None:
    build_gov_hi()
    build_internships_hi()
    build_fellowship_hi()
    build_dmrv_hi()
    build_careers_hi()
    build_glossary_hi()
    beh.update_sitemap(["/hindi-government-jobs", "/hindi-green-internships", "/hindi-fellowship-deadlines", "/hindi-dmrv", "/hindi-green-careers", "/hindi-glossary"])
    print("Wrote 6 Hindi hub pages")


if __name__ == "__main__":
    main()
