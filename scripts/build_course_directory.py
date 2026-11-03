#!/usr/bin/env python3
"""Build a course and certification directory for green jobs.

Lists the certifications and courses that recur in green-job notices (GRI,
BRSR, LEED, GHG Protocol, etc.) with what each covers, who runs it, and
which roles ask for it. Affiliate links are placeholders.
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

COURSES_DIR = PUBLIC / "courses"


COURSES = [
    {
        "name": "GRI Standards",
        "provider": "Global Reporting Initiative",
        "url": "https://www.globalreporting.org",
        "what": "The most widely used sustainability reporting standard globally. Covers economic, environmental and social impacts.",
        "who_asks": "ESG analyst, sustainability reporting specialist, CSR manager",
        "roles": ["/roles/esg-analyst", "/roles/sustainability-reporting"],
        "level": "Beginner to advanced",
        "cost": "Free (standards) / paid (certification)",
        "duration": "Self-paced",
    },
    {
        "name": "BRSR (Business Responsibility and Sustainability Reporting)",
        "provider": "SEBI / NSE Academy",
        "url": "https://www.sebi.gov.in",
        "what": "India's mandatory ESG disclosure framework for the top 1000 listed companies. Covers 90+ indicators across environmental, social and governance.",
        "who_asks": "ESG analyst, sustainability reporting specialist, CSR manager, sustainability consultant",
        "roles": ["/roles/esg-analyst", "/roles/sustainability-reporting", "/roles/csr-manager"],
        "level": "Intermediate",
        "cost": "Free (framework) / paid (training)",
        "duration": "Self-paced",
    },
    {
        "name": "GHG Protocol",
        "provider": "World Resources Institute (WRI)",
        "url": "https://ghgprotocol.org",
        "what": "The standard for measuring and managing greenhouse gas emissions. Covers Scope 1, 2 and 3. Foundation of carbon accounting.",
        "who_asks": "Carbon analyst, ESG analyst, sustainability consultant",
        "roles": ["/roles/carbon-analyst", "/roles/esg-analyst"],
        "level": "Beginner to intermediate",
        "cost": "Free",
        "duration": "Self-paced",
    },
    {
        "name": "LEED (Leadership in Energy and Environmental Design)",
        "provider": "US Green Building Council (USGBC)",
        "url": "https://www.usgbc.org/leed",
        "what": "Global green building certification. Covers sustainable site development, water efficiency, energy, materials and indoor environment.",
        "who_asks": "Green building specialist, sustainability consultant, environmental engineer",
        "roles": ["/roles/green-building", "/roles/environmental-engineer"],
        "level": "Intermediate",
        "cost": "Paid (exam + study materials)",
        "duration": "3-6 months",
    },
    {
        "name": "GRIHA",
        "provider": "GRIHA Council (TERI)",
        "url": "https://www.grihaindia.org",
        "what": "India's national green building rating system. Covers site planning, water, energy, waste and indoor environment.",
        "who_asks": "Green building specialist, sustainability consultant",
        "roles": ["/roles/green-building"],
        "level": "Intermediate",
        "cost": "Paid",
        "duration": "3-6 months",
    },
    {
        "name": "IGBC (Indian Green Building Council)",
        "provider": "CII - IGBC",
        "url": "https://igbc.in",
        "what": "India's green building rating system by CII. Covers new construction, existing buildings, interiors and landscapes.",
        "who_asks": "Green building specialist, sustainability consultant",
        "roles": ["/roles/green-building"],
        "level": "Intermediate",
        "cost": "Paid",
        "duration": "3-6 months",
    },
    {
        "name": "SBTi (Science Based Targets initiative)",
        "provider": "SBTi (CDP, WRI, WWF, UN Global Compact)",
        "url": "https://sciencebasedtargets.org",
        "what": "Framework for setting emission reduction targets aligned with climate science. Covers target setting, validation and progress tracking.",
        "who_asks": "Carbon analyst, ESG analyst, sustainability manager",
        "roles": ["/roles/carbon-analyst", "/roles/esg-analyst", "/roles/sustainability-manager"],
        "level": "Intermediate",
        "cost": "Free (methodology) / Paid (validation)",
        "duration": "Self-paced",
    },
    {
        "name": "ISO 14001 (Environmental Management Systems)",
        "provider": "International Organization for Standardization",
        "url": "https://www.iso.org/standard/60857.html",
        "what": "International standard for environmental management systems. Covers planning, implementation, monitoring and improvement.",
        "who_asks": "Environmental engineer, EHS specialist, sustainability manager",
        "roles": ["/roles/environmental-engineer", "/roles/sustainability-manager"],
        "level": "Intermediate",
        "cost": "Paid (exam + training)",
        "duration": "1-3 months",
    },
    {
        "name": "NEBOSH (National Examination Board in Occupational Safety and Health)",
        "provider": "NEBOSH",
        "url": "https://www.nebosh.org.uk",
        "what": "International qualification in occupational health and safety. Covers risk assessment, hazard control and safety management.",
        "who_asks": "EHS specialist, environmental engineer",
        "roles": ["/roles/environmental-engineer"],
        "level": "Intermediate",
        "cost": "Paid",
        "duration": "1-3 months",
    },
    {
        "name": "GRI Professional Certification",
        "provider": "Global Reporting Initiative",
        "url": "https://www.globalreporting.org/professional-development",
        "what": "Professional certification in GRI sustainability reporting. Covers reporting principles, disclosures and assurance.",
        "who_asks": "ESG analyst, sustainability reporting specialist",
        "roles": ["/roles/esg-analyst", "/roles/sustainability-reporting"],
        "level": "Intermediate",
        "cost": "Paid",
        "duration": "1-2 months",
    },
    {
        "name": "SASB (Sustainability Accounting Standards Board)",
        "provider": "SASB (now part of IFRS Foundation)",
        "url": "https://www.sasb.org",
        "what": "Industry-specific sustainability accounting standards. Used by investors for ESG analysis.",
        "who_asks": "ESG analyst, sustainability consultant, climate finance analyst",
        "roles": ["/roles/esg-analyst", "/roles/sustainability-consultant"],
        "level": "Intermediate",
        "cost": "Free (standards) / Paid (certification)",
        "duration": "Self-paced",
    },
    {
        "name": "TCFD (Task Force on Climate-related Financial Disclosures)",
        "provider": "Financial Stability Board",
        "url": "https://www.fsb-tcfd.org",
        "what": "Framework for climate-related financial risk disclosure. Covers governance, strategy, risk management and metrics.",
        "who_asks": "Climate risk analyst, ESG analyst, sustainability manager",
        "roles": ["/roles/climate-risk-analyst", "/roles/esg-analyst"],
        "level": "Intermediate",
        "cost": "Free",
        "duration": "Self-paced",
    },
    {
        "name": "TNFD (Taskforce on Nature-related Financial Disclosures)",
        "provider": "TNFD",
        "url": "https://tnfd.global",
        "what": "Framework for nature-related financial risk disclosure. Emerging standard, similar to TCFD but for biodiversity.",
        "who_asks": "Biodiversity analyst, ESG analyst, sustainability consultant",
        "roles": ["/roles/biodiversity-analyst", "/roles/esg-analyst"],
        "level": "Intermediate",
        "cost": "Free",
        "duration": "Self-paced",
    },
    {
        "name": "GHG Protocol Corporate Standard",
        "provider": "WRI / WBCSD",
        "url": "https://ghgprotocol.org/corporate-standard",
        "what": "The corporate accounting and reporting standard for greenhouse gas emissions. Foundation of carbon accounting.",
        "who_asks": "Carbon analyst, ESG analyst, sustainability reporting specialist",
        "roles": ["/roles/carbon-analyst", "/roles/esg-analyst", "/roles/sustainability-reporting"],
        "level": "Beginner to intermediate",
        "cost": "Free",
        "duration": "Self-paced",
    },
    {
        "name": "ISO 14064 (Greenhouse Gas Verification)",
        "provider": "International Organization for Standardization",
        "url": "https://www.iso.org/standard/66453.html",
        "what": "International standard for greenhouse gas quantification and verification. Used by carbon auditors and verifiers.",
        "who_asks": "Carbon analyst, carbon market analyst, environmental engineer",
        "roles": ["/roles/carbon-analyst", "/roles/carbon-market-analyst"],
        "level": "Advanced",
        "cost": "Paid",
        "duration": "1-3 months",
    },
]


def build_course_page(course: Dict[str, Any]) -> None:
    body = "\n".join([
        hero("Certification", course["name"], course["what"], [("Provider", course["provider"]), ("Level", course["level"]), ("Cost", course["cost"])]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Details</h2>
        <div class="table-wrap">
          <table class="data-table">
            <tbody>
              <tr><th scope="row">Provider</th><td>{esc(course["provider"])}</td></tr>
              <tr><th scope="row">What it covers</th><td>{esc(course["what"])}</td></tr>
              <tr><th scope="row">Who asks for it</th><td>{esc(course["who_asks"])}</td></tr>
              <tr><th scope="row">Level</th><td>{esc(course["level"])}</td></tr>
              <tr><th scope="row">Cost</th><td>{esc(course["cost"])}</td></tr>
              <tr><th scope="row">Duration</th><td>{esc(course["duration"])}</td></tr>
            </tbody>
          </table>
        </div>
        <p><a href="{course['url']}" target="_blank" rel="noopener noreferrer">Official website &nearr;</a></p>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related role profiles</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{r}">{r.split("/")[-1].replace("-", " ").title()}</a></li>' for r in course["roles"])}
        </ul>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            (f"Is {course['name']} worth it?", "It depends on your target role. Check the 'who asks for it' section above. If your target employers list it, it is worth the investment."),
            ("Can I learn this for free?", "Most frameworks publish their standards for free. Certification exams and training courses are usually paid."),
            ("How long does it take?", f"Typically {course['duration']}. Self-paced options are available for most."),
        ]),
    ])
    jsonld = "\n".join([
        beh.bsp.organization_jsonld(),
        beh.bsp.website_jsonld(),
        beh.breadcrumb(course["name"], f"{SITE}/courses/{course['name'].lower().replace(' ', '-').replace('(', '').replace(')', '')}"),
    ])
    slug = course["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and")
    write_sub(COURSES_DIR, slug, shell(
        title=f"{course['name']} Certification: What It Is and Who Asks For It",
        description=f"{course['name']} by {course['provider']}: what it covers, who asks for it, cost and duration.",
        canonical=f"{SITE}/courses/{slug}",
        body=body,
        jsonld=jsonld,
    ))


def build_courses_index() -> None:
    course_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/courses/{c['name'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('&', 'and')}">{esc(c['name'])}</a></h3>
          <p class="hub-card-sum">{esc(c['what'])}</p>
          <p class="hub-card-foot"><span>{esc(c['provider'])}</span> <a href="/courses/{c['name'].lower().replace(' ', '-').replace('(', '').replace(')', '').replace('&', 'and')}">Details &rarr;</a></p>
        </article>"""
        for c in COURSES
    )
    body = "\n".join([
        hero("Certifications & courses", "Green Job Certifications & Courses", "Certifications and courses that recur in green-job notices, with what each covers and who asks for it.", [("Certifications", str(len(COURSES))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Certifications</h2>
        <p>Each page links to the official provider and to the role profiles that list it as a requirement.</p>
        <div class="hub-list">
{course_cards}
        </div>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Are these certifications mandatory?", "No. Most are voluntary. Employers list them as 'preferred' or 'desirable' rather than essential."),
            ("Which should I get first?", "Start with free frameworks (GHG Protocol, BRSR format, GRI standards). Paid certifications add value once you have a target role."),
            ("Do certifications guarantee a job?", "No. They signal commitment and knowledge. Practical experience and a portfolio matter more."),
        ]),
    ])
    write_sub(COURSES_DIR, "index", shell(
        title="Green Job Certifications & Courses: GRI, BRSR, LEED, GHG Protocol & More",
        description="Certifications and courses for green jobs in India: GRI, BRSR, LEED, GRIHA, GHG Protocol, SBTi, TCFD, TNFD, ISO 14001 and more.",
        canonical=f"{SITE}/courses",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("Green Job Certifications", f"{SITE}/courses")]),
    ))


def main() -> None:
    for course in COURSES:
        build_course_page(course)
    build_courses_index()
    slugs = [c["name"].lower().replace(" ", "-").replace("(", "").replace(")", "").replace("&", "and") for c in COURSES]
    beh.update_sitemap(["/courses"] + [f"/courses/{s}" for s in slugs])
    print(f"Wrote {len(COURSES)} course pages + index")


if __name__ == "__main__":
    main()
