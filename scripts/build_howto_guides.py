#!/usr/bin/env python3
"""Build 'how to' guides for high-volume informational queries.

Each guide answers a question green-job seekers actually ask, using verified
facts and links to relevant jobs, exams and role profiles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
hero = beh.hero
section = beh.section
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local

GUIDES_DIR = PUBLIC / "guides"


def build_guide(slug: str, title: str, desc: str, kicker: str, h1: str, sub: str,
                steps: List[str], tips: List[str], faqs: List[tuple], related: List[tuple]) -> None:
    body = "\n".join([
        hero(kicker, h1, sub, [("Updated", TODAY.strftime("%d %b %Y"))]),
        "    <section class=\"hub-main\">\n      <div class=\"hub-main-inner\">\n        <h2>Step by step</h2>\n        <ol class=\"check-list\">\n" + "".join(f"          <li>{s}</li>\n" for s in steps) + "        </ol>\n      </div>\n    </section>",
        "    <section class=\"hub-main\">\n      <div class=\"hub-main-inner\">\n        <h2>Practical tips</h2>\n        <ul class=\"check-list\">\n" + "".join(f"          <li>{t}</li>\n" for t in tips) + "        </ul>\n      </div>\n    </section>",
        "    <section class=\"hub-main\">\n      <div class=\"hub-main-inner\">\n        <h2>Related pages</h2>\n        <ul class=\"check-list\">\n" + "".join(f'          <li><a href="{href}">{esc(label)}</a></li>\n' for href, label in related) + "        </ul>\n      </div>\n    </section>",
        beh.bsp.faq_section_html(faqs),
    ])
    jsonld = "\n".join([
        beh.bsp.organization_jsonld(),
        beh.bsp.website_jsonld(),
        beh.breadcrumb(title, f"{SITE}/guides/{slug}"),
        beh.faq_jsonld(faqs),
    ])
    write_sub(GUIDES_DIR, slug, shell(
        title=title, description=desc, canonical=f"{SITE}/guides/{slug}",
        body=body, jsonld=jsonld))


GUIDES = [
    {
        "slug": "how-to-apply-for-jrf",
        "title": "How to Apply for JRF in India: Step-by-Step Guide",
        "desc": "How to apply for a Junior Research Fellow (JRF) position in India: eligibility, NET/GATE, documents, interview and stipend.",
        "kicker": "How to guide",
        "h1": "How to Apply for a Junior Research Fellow (JRF) Position",
        "sub": "A step-by-step guide to applying for JRF positions in Indian research institutes, from eligibility to the interview.",
        "steps": [
            "<strong>Check eligibility.</strong> You need a master's degree in the project's discipline and a valid national eligibility test (CSIR-UGC NET, UGC-NET or GATE). Some institute advertisements accept a master's without NET.",
            "<strong>Find openings.</strong> Browse the <a href='/jrf-srf-project-associate-jobs'>JRF and project associate hub</a> and the <a href='/exams/csir-jrf'>CSIR JRF guide</a>. Institute websites and notice boards publish walk-in interviews year-round.",
            "<strong>Read the advertisement carefully.</strong> Note the essential qualification, percentage, age limit, contract duration and stipend. These vary by institute and project.",
            "<strong>Prepare documents.</strong> Degree certificates, mark sheets, NET/GATE scorecard, category certificate, PhD registration proof (for SRF), and a CV with your dissertation summary.",
            "<strong>Apply as instructed.</strong> Some institutes ask for email applications with a single PDF; others use an online form. Follow the advertisement exactly.",
            "<strong>Prepare for the interview.</strong> Expect questions on your dissertation, lab techniques, the project's subject area and why you want the role.",
            "<strong>Complete document verification.</strong> Carry originals and attested copies. The fellowship starts after verification and joining.",
        ],
        "tips": [
            "Apply to multiple institutes simultaneously. JRF positions are project-specific and competitive.",
            "A strong dissertation summary and lab skills matter more than grades in most interviews.",
            "PhD registration is usually required before upgrading from JRF to SRF. Plan this early.",
            "Fellowship amounts follow funding-agency norms and are printed in the advertisement. Do not expect negotiation.",
            "Keep a spreadsheet of applications with deadlines, contact persons and status.",
        ],
        "faqs": [
            ("Can I apply for JRF without NET?", "Some institute advertisements accept a master's without NET when project funding allows it. The notice states this explicitly."),
            ("How long does the JRF fellowship last?", "The initial JRF period is typically two years, extendable to SRF after PhD registration."),
            ("Is JRF experience counted as work experience?", "For academic and research applications, usually yes. For corporate roles, it depends on the employer."),
        ],
        "related": [("/roles/junior-research-fellow", "JRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide"), ("/exams/ugc-net-environmental-science", "UGC-NET guide"), ("/glossary/jrf", "JRF glossary entry")],
    },
    {
        "slug": "how-to-prepare-forest-guard-exam",
        "title": "How to Prepare for Forest Guard Exam in India",
        "desc": "How to prepare for the forest guard recruitment exam: written test, physical standards, syllabus, documents and timeline.",
        "kicker": "How to guide",
        "h1": "How to Prepare for the Forest Guard Exam",
        "sub": "A practical preparation guide for state forest guard recruitment: written test, physical standards, syllabus and documents.",
        "steps": [
            "<strong>Read the state notification.</strong> Forest guard recruitment is state-specific. Download the PDF from the state forest department website and note eligibility, age, physical standards and exam pattern.",
            "<strong>Check physical standards first.</strong> Height, chest and running tests eliminate more candidates than the written paper. Start running to the state's standard months before the test.",
            "<strong>Study the written syllabus.</strong> Common subjects: general awareness (state geography, forests, wildlife), basic arithmetic, reasoning and the state language.",
            "<strong>Prepare documents.</strong> School certificates, caste certificate, domicile certificate, physical fitness certificate and photographs.",
            "<strong>Practice previous papers.</strong> State forest departments and coaching institutes publish previous years' papers. Solve them under timed conditions.",
            "<strong>Prepare for the physical test.</strong> Run daily, build stamina and practice the specific test (running or walking to a fixed distance within a time limit).",
            "<strong>Attend document verification.</strong> Carry originals and attested copies. Missing documents disqualify even after clearing the written and physical tests.",
        ],
        "tips": [
            "Start physical preparation at least 3-4 months before the expected exam date.",
            "State forest department websites publish the notification; check them weekly during recruitment season.",
            "Forest guard is a field post. Expect outdoor work, irregular hours and postings in remote areas.",
            "Many states have separate physical standards for male and female candidates. Check the notification.",
            "Promotion to forester and ranger is possible through departmental exams after years of service.",
        ],
        "faqs": [
            ("Do I need a forestry degree?", "No. A school-leaving certificate is the usual minimum for forest guard. Forestry qualifications matter more for ranger posts."),
            ("Is the physical test very hard?", "It is demanding but achievable with preparation. Most states set a running or walking standard that requires steady practice."),
            ("Can women apply?", "Yes. Most states recruit women with separate physical standards and sometimes reserved posts."),
        ],
        "related": [("/exams/forest-guard", "Forest guard recruitment guide"), ("/roles/forest-guard", "Forest guard career profile"), ("/glossary/campa", "CAMPA glossary entry"), ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs")],
    },
    {
        "slug": "how-to-write-brsr-report",
        "title": "How to Prepare a BRSR Report: Step-by-Step Guide",
        "desc": "How to prepare a Business Responsibility and Sustainability Report (BRSR) for SEBI compliance: data collection, disclosure, and verification.",
        "kicker": "How to guide",
        "h1": "How to Prepare a BRSR Report",
        "sub": "A practical guide to preparing SEBI's Business Responsibility and Sustainability Report, from data collection to disclosure.",
        "steps": [
            "<strong>Understand the framework.</strong> BRSR has two sections: essential indicators (mandatory) and leadership indicators (voluntary). Download the format from SEBI's website.",
            "<strong>Identify data owners.</strong> Map each indicator to the department that holds the data: HR for employee metrics, facilities for energy and water, procurement for supply chain.",
            "<strong>Collect data for the full financial year.</strong> BRSR covers the entire fiscal year, not a snapshot. Set up data collection processes early.",
            "<strong>Calculate emissions.</strong> Use the GHG Protocol to compute Scope 1, 2 and 3 emissions. Document methodology and emission factors used.",
            "<strong>Draft the report.</strong> Follow the SEBI format exactly. Use clear language and avoid vague claims without data.",
            "<strong>Get internal review.</strong> Have legal, finance and sustainability teams review before submission.",
            "<strong>Consider assurance.</strong> SEBI is phasing in third-party assurance. Check the current circular for your company's phase.",
            "<strong>File with the annual report.</strong> BRSR is part of the annual report filed with stock exchanges.",
        ],
        "tips": [
            "Start data collection in Q1, not after year-end. Retroactive data collection is the most common failure.",
            "BRSR is mandatory for the top 1000 listed companies by market capitalisation. Smaller companies file voluntarily.",
            "The format changes periodically. Always use the latest SEBI circular.",
            "Assurance requirements are being phased in by company size. Check which phase applies to you.",
            "ESG analyst and sustainability reporting specialist roles are the main jobs created by BRSR.",
        ],
        "faqs": [
            ("Is BRSR mandatory for all companies?", "No. It applies to the top 1000 listed companies by market capitalisation, phased in from FY2022-23."),
            ("How long does BRSR preparation take?", "For a first-time filer, 3-6 months including data collection and review."),
            ("Can I outsource BRSR preparation?", "Yes. Consulting firms and ESG specialists offer BRSR services, but internal ownership is recommended."),
        ],
        "related": [("/glossary/brsr", "BRSR glossary entry"), ("/roles/sustainability-reporting", "Sustainability reporting profile"), ("/roles/esg-analyst", "ESG analyst profile"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
    {
        "slug": "how-to-enter-esg-career",
        "title": "How to Enter an ESG Career in India: Step-by-Step Guide",
        "desc": "How to start an ESG career in India: qualifications, skills, internships, certifications and entry-level roles.",
        "kicker": "How to guide",
        "h1": "How to Enter an ESG Career in India",
        "sub": "A practical guide for graduates and professionals who want to move into ESG and sustainability roles in India.",
        "steps": [
            "<strong>Understand what ESG roles involve.</strong> Read the <a href='/roles/esg-analyst'>ESG analyst profile</a> and the <a href='/glossary/esg'>ESG glossary entry</a>. ESG work ranges from data collection to strategy.",
            "<strong>Build foundational knowledge.</strong> Learn BRSR, GRI and the GHG Protocol. Free resources are available on SEBI's and WRI's websites.",
            "<strong>Get relevant experience.</strong> Internships at consulting firms, ESG rating agencies or corporate sustainability teams are the standard entry path.",
            "<strong>Build a portfolio.</strong> Create a mock BRSR section, a carbon inventory or a data dashboard. Show it in interviews.",
            "<strong>Apply for entry-level roles.</strong> Browse <a href='/esg-carbon-sustainability-jobs'>ESG and sustainability jobs</a> and <a href='/green-internships'>internships</a>. Entry-level titles include ESG analyst, sustainability associate and ESG data analyst.",
            "<strong>Consider certifications.</strong> GRI, SASB and BRSR training courses exist. They help but are not required for most entry-level roles.",
            "<strong>Network.</strong> LinkedIn, sustainability conferences and industry events are where ESG professionals connect.",
        ],
        "tips": [
            "ESG hiring in India is dominated by consulting firms and large listed companies. Target these.",
            "Data skills (Excel, Power BI, Python) are increasingly listed in ESG job descriptions.",
            "A master's in environment, economics or business helps but is not mandatory for analyst roles.",
            "ESG roles rarely publish pay. Ask about CTC breakup, variable component and assurance budget during interviews.",
            "The field is growing fast. Early movers with 2-3 years of experience are in high demand.",
        ],
        "faqs": [
            ("Do I need a science degree for ESG?", "No. Economics, business, law and social science backgrounds are common in ESG roles."),
            ("Is ESG a stable career?", "Yes. BRSR mandates and investor pressure are structural drivers, not trends."),
            ("How much do ESG analysts earn?", "The registry shows that most ESG listings do not publish pay. See the <a href='/roles/esg-analyst'>ESG analyst profile</a> for details."),
        ],
        "related": [("/roles/esg-analyst", "ESG analyst profile"), ("/glossary/esg", "ESG glossary entry"), ("/glossary/brsr", "BRSR glossary entry"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
]


def build_guides_index() -> None:
    guide_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/guides/{g['slug']}">{esc(g['title'])}</a></h3>
          <p class="hub-card-sum">{esc(g['desc'])}</p>
          <p class="hub-card-foot"><a href="/guides/{g['slug']}">Read guide &rarr;</a></p>
        </article>"""
        for g in GUIDES
    )
    body = "\n".join([
        hero("How-to guides", "Green Job Guides: How to Apply, Prepare & Enter", "Practical step-by-step guides for green-job seekers in India.", [("Guides", str(len(GUIDES))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Guides</h2>
        <p>Each guide is written from verified facts and links to relevant jobs, exams and role profiles.</p>
        <div class="hub-list">
{guide_cards}
        </div>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Are these guides free?", "Yes. All content on Urban Forest Park is free."),
            ("How often are they updated?", "Guides are reviewed when regulations or processes change."),
            ("Can I suggest a guide topic?", "Yes, through the report page or by email."),
        ]),
    ])
    write_sub(GUIDES_DIR, "index", shell(
        title="Green Job Guides: How to Apply, Prepare & Enter ESG Careers",
        description="Step-by-step guides for green-job seekers in India: how to apply for JRF, prepare for forest guard exam, write a BRSR report and enter ESG careers.",
        canonical=f"{SITE}/guides",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("Green Job Guides", f"{SITE}/guides")]),
    ))


def main() -> None:
    for g in GUIDES:
        build_guide(**{k: g[k] for k in ["slug", "title", "desc", "kicker", "h1", "sub", "steps", "tips", "faqs", "related"]})
    build_guides_index()
    beh.update_sitemap(["/guides"] + [f"/guides/{g['slug']}" for g in GUIDES])
    print(f"Wrote {len(GUIDES)} how-to guides + index")


if __name__ == "__main__":
    main()
