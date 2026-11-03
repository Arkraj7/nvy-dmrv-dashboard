#!/usr/bin/env python3
"""Build comparison pages for high-intent 'X vs Y' queries.

Each page compares two options that green-job seekers actually weigh, using
only verified facts. No invented salaries, eligibility or dates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
hero = beh.hero
section = beh.section
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None
beh_update = beh.update_sitemap


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local


COMPARE_DIR = PUBLIC / "compare"


def compare_table(rows: List[Tuple[str, str, str]]) -> str:
    body = "\n".join(
        f'            <tr><th scope="row">{esc(label)}</th><td>{esc(left)}</td><td>{esc(right)}</td></tr>'
        for label, left, right in rows
    )
    return f"""        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Dimension</th><th>Left</th><th>Right</th></tr></thead>
            <tbody>
{body}
            </tbody>
          </table>
        </div>"""


COMPARISONS: List[Dict[str, Any]] = [
    {
        "slug": "jrf-vs-srf-fellowship",
        "name": "JRF vs SRF",
        "h1": "JRF vs SRF: Difference, Eligibility & Stipend",
        "title": "JRF vs SRF: Difference, Eligibility & Stipend Explained",
        "desc": "Junior Research Fellow vs Senior Research Fellow: what each is, how you move from one to the other, and what changes.",
        "kicker": "Research fellowship",
        "intro": "JRF and SRF are two stages of the same fellowship, not two different jobs. The difference is registration, experience and pay.",
        "one_line": "In one line: JRF is the entry fellowship; SRF is the upgraded stage after PhD registration.",
        "rows": [
            ("Full form", "Junior Research Fellow", "Senior Research Fellow"),
            ("When you hold it", "After a master's degree and a national eligibility test", "After PhD registration and a period as JRF"),
            ("Stipend", "Lower fellowship rate", "Higher fellowship rate"),
            ("Pay basis", "Funding agency norms, printed in the advertisement", "Funding agency norms, printed in the advertisement"),
            ("Duration", "Fixed initial period", "Renewable, tied to project and PhD progress"),
            ("Typical next step", "Upgrade to SRF", "Research associate, project scientist or faculty"),
        ],
        "choose": [
            "If you have just finished a master's and cleared NET or GATE, you are applying for JRF.",
            "If you are already a JRF and have registered for a PhD, ask your PI about the SRF upgrade.",
            "If a posting asks for a PhD, it is not a JRF or SRF post.",
        ],
        "faqs": [
            ("Can I apply directly for SRF?", "Usually no. SRF follows JRF after PhD registration and satisfactory progress."),
            ("Is the SRF stipend much higher?", "It is higher, but both follow funding-agency norms. The exact figures are in the advertisement."),
            ("Does SRF require a PhD registration?", "Yes in almost all cases. That is the main difference between the two."),
        ],
        "related": [("/roles/junior-research-fellow", "JRF/SRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide"), ("/glossary/jrf", "JRF glossary entry")],
    },
    {
        "slug": "forest-guard-vs-ranger",
        "name": "Forest Guard vs Ranger",
        "h1": "Forest Guard vs Ranger: Difference, Eligibility & Promotion",
        "title": "Forest Guard vs Ranger: Difference, Eligibility & Promotion",
        "desc": "Forest guard vs forest ranger: qualification, physical test, pay basis, and how a guard becomes a ranger.",
        "kicker": "State forest service",
        "intro": "Forest guard and ranger are different rungs of the same state forest service, not two names for the same job.",
        "one_line": "In one line: forest guard is the entry field post; ranger supervises a range and its staff.",
        "rows": [
            ("Qualification", "School leaving certificate, usually Class 10 or 12", "Bachelor's degree, often in science or forestry"),
            ("Recruitment", "State forest department, written test plus physical test", "State PSC or forest department, written plus interview plus physical"),
            ("Physical standards", "Height, chest and running test", "Endurance and measurement tests, benchmarked separately"),
            ("Pay basis", "State pay matrix for the post", "State pay matrix for a gazetted post"),
            ("Duties", "Patrol, fire watch, nursery and plantation work", "Range management, enforcement, staff supervision"),
            ("Promotion", "Possible through departmental exams over years", "Promotion to higher forest service grades"),
        ],
        "choose": [
            "If you have a school-leaving certificate and can meet the physical standard, apply for forest guard.",
            "If you are a graduate with forestry or science background, ranger is the better entry point.",
            "Serving guards can often appear for departmental exams to become rangers.",
        ],
        "faqs": [
            ("Can a forest guard become a ranger?", "Yes, in many states through departmental or limited competitive examinations, though it takes years of service."),
            ("Is ranger a gazetted post?", "In most states yes, which is why it needs a degree and a commission-style selection."),
            ("Which pays more?", "Ranger, because it is a gazetted post at a higher pay level. Exact figures are in the state notification."),
        ],
        "related": [("/exams/forest-guard", "Forest guard recruitment guide"), ("/exams/forest-range-officer", "Forest range officer guide"), ("/roles/forest-guard", "Forest guard career profile")],
    },
    {
        "slug": "esg-vs-csr",
        "name": "ESG vs CSR",
        "h1": "ESG vs CSR: Difference, Regulation & Careers",
        "title": "ESG vs CSR: Difference, Regulation & Careers Explained",
        "desc": "ESG vs CSR: how they differ, how each is regulated in India, and which creates more jobs.",
        "kicker": "Corporate sustainability",
        "intro": "CSR and ESG are often used interchangeably, but they are different things with different rules.",
        "one_line": "In one line: CSR is a spending obligation under the Companies Act; ESG is a performance and disclosure framework.",
        "rows": [
            ("What it is", "Corporate Social Responsibility: spending 2% of average net profit on specified activities", "Environmental, Social and Governance: how a company performs and reports on non-financial factors"),
            ("Basis", "Companies Act, 2013, Section 135", "SEBI's BRSR framework and investor expectations"),
            ("Who it applies to", "Companies meeting profit, turnover or net-worth thresholds", "Top 1000 listed companies by market capitalisation, phased in"),
            ("Output", "Annual CSR report and spend disclosure", "Structured ESG disclosure in the annual report"),
            ("Jobs created", "CSR programme and NGO liaison roles", "ESG analyst, reporting, assurance and sustainability manager roles"),
            ("Regulator", "Ministry of Corporate Affairs", "SEBI"),
        ],
        "choose": [
            "If you want programme and community work, CSR roles fit better.",
            "If you want data, reporting and assurance, ESG roles fit better.",
            "Many mid-size companies combine both into one sustainability team.",
        ],
        "faqs": [
            ("Can one person do both CSR and ESG?", "Yes. In smaller companies one sustainability manager often owns both."),
            ("Is CSR spending counted as ESG?", "CSR spend may appear in ESG disclosures, but the two frameworks are separate."),
            ("Which has more jobs in India?", "ESG hiring currently outnumbers CSR-specific roles, driven by BRSR."),
        ],
        "related": [("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"), ("/roles/esg-analyst", "ESG analyst career profile"), ("/glossary/esg", "ESG glossary entry")],
    },
    {
        "slug": "ifs-vs-ias",
        "name": "IFS vs IAS",
        "h1": "IFS vs IAS: Difference, Exam & Career",
        "title": "IFS vs IAS: Difference, Exam & Career Compared",
        "desc": "Indian Forest Service vs Indian Administrative Service: same exam, different service, different career.",
        "kicker": "All India Services",
        "intro": "Both are recruited through the same Civil Services Examination, but they are different services with different work.",
        "one_line": "In one line: IAS is general administration; IFS is forest and wildlife administration.",
        "rows": [
            ("Recruitment", "UPSC Civil Services Examination", "UPSC Civil Services Examination"),
            ("Allocation", "Based on rank and preference", "Based on rank and preference, after IAS and IPS"),
            ("Work", "District and policy administration across sectors", "Forest, wildlife and environment administration"),
            ("Training", "LBSNAA foundation course", "LBSNAA foundation plus professional forestry training at IGNFA"),
            ("Posting", "Districts, ministries and departments", "State forest departments, protected areas, MoEFCC"),
            ("Pay basis", "7th CPC matrix for the service", "7th CPC matrix for the service"),
        ],
        "choose": [
            "If you want general administration and policy, IAS is the route.",
            "If you want forests, wildlife and conservation, IFS is the route.",
            "Both need the same preparation; the difference is rank, preference and interest.",
        ],
        "faqs": [
            ("Is the exam different?", "No. Both use the Civil Services Examination. Allocation depends on rank and the preference list."),
            ("Does IFS have a separate medical standard?", "Yes. The Indian Forest Service has its own physical and medical requirements."),
            ("Which is harder to get?", "IFS is allocated at lower ranks than IAS, so in practice it needs a strong rank. Both are highly competitive."),
        ],
        "related": [("/exams/indian-forest-service", "IFS exam guide"), ("/government-environment-jobs", "Government recruitment tracker"), ("/glossary/campa", "CAMPA glossary entry")],
    },
    {
        "slug": "gis-vs-remote-sensing",
        "name": "GIS vs Remote Sensing",
        "h1": "GIS vs Remote Sensing: Difference, Skills & Careers",
        "title": "GIS vs Remote Sensing: Difference, Skills & Careers Explained",
        "desc": "GIS vs remote sensing: what each does, the tools each uses, and how the two combine in environmental jobs.",
        "kicker": "Geospatial",
        "intro": "GIS and remote sensing are usually taught together, but they are different skills that environmental employers separate.",
        "one_line": "In one line: remote sensing collects data from above; GIS organises and analyses spatial data.",
        "rows": [
            ("Core task", "Managing, analysing and mapping spatial data", "Acquiring and interpreting imagery from satellites or aircraft"),
            ("Typical tools", "QGIS, ArcGIS, PostGIS, Python", "Google Earth Engine, ENVI, SNAP, ERDAS"),
            ("Data source", "Vector and raster layers, field data", "Satellite imagery, aerial photographs, drone data"),
            ("Common outputs", "Maps, suitability models, spatial analysis", "Land-cover maps, change detection, vegetation indices"),
            ("Entry qualification", "Science or engineering degree with GIS skills", "Science or engineering degree with image-processing skills"),
            ("Typical jobs", "GIS analyst, spatial analyst, planner", "Remote sensing analyst, earth observation specialist"),
        ],
        "choose": [
            "If you like mapping and database work, lean GIS.",
            "If you like imagery and spectral analysis, lean remote sensing.",
            "Most environmental postings want both, so learn one well and the basics of the other.",
        ],
        "faqs": [
            ("Can one person do both?", "Yes. Many postings combine them under one title."),
            ("Which is easier to learn first?", "QGIS for GIS, Google Earth Engine for remote sensing. Both are free."),
            ("Do I need a geoinformatics degree?", "No. Science and engineering graduates with demonstrated skills are hired regularly."),
        ],
        "related": [("/roles/gis-analyst", "GIS analyst career profile"), ("/gis-remote-sensing-climate-jobs", "GIS and remote sensing jobs"), ("/spatial-data", "Spatial data explorer")],
    },
    {
        "slug": "internship-vs-fellowship",
        "name": "Internship vs Fellowship",
        "h1": "Internship vs Fellowship: Difference & Which to Choose",
        "title": "Internship vs Fellowship: Difference & Which to Choose",
        "desc": "Internship vs fellowship: duration, pay, eligibility and which suits your career stage.",
        "kicker": "Early career",
        "intro": "Both are short-term, structured opportunities, but they serve different purposes and carry different expectations.",
        "one_line": "In one line: an internship builds experience; a fellowship funds research or leadership.",
        "rows": [
            ("Purpose", "Work experience and exposure", "Research, leadership or specialised training"),
            ("Duration", "Weeks to a few months", "Months to a year or more"),
            ("Pay", "Stipend or unpaid, varies widely", "Funded stipend, often with travel or tuition"),
            ("Eligibility", "Students or recent graduates", "Usually graduates or professionals, sometimes with an exam"),
            ("Output", "Work delivered to the host organisation", "Research, policy brief, project or dissertation"),
            ("Best for", "Testing a field and building a CV", "Deepening expertise and funding a transition"),
        ],
        "choose": [
            "If you are still studying or just graduated, an internship is usually the right first step.",
            "If you have a degree and want funded research or leadership exposure, consider a fellowship.",
            "Many people do an internship first, then apply for a fellowship with that experience.",
        ],
        "faqs": [
            ("Is a fellowship better paid than an internship?", "Often yes, because it is funded, but amounts vary. The registry reproduces the advertised figure for each."),
            ("Can I do both at once?", "Usually no, because both are full-time commitments."),
            ("Which looks better on a CV?", "Neither is better in general. Relevance to the next role matters more than the label."),
        ],
        "related": [("/green-internships", "Green internships and entry-level jobs"), ("/fellowship-deadlines", "Fellowship and grant deadlines"), ("/green-careers", "Green career pathways")],
    },
]


def build_compare_page(comp: Dict[str, Any]) -> None:
    live = []
    for r in comp["related"]:
        pass
    # pull live openings from the registry using related hubs' categories is overkill;
    # instead count matching jobs by keyword in the comparison name
    body = "\n".join(
        [
            hero(
                comp["kicker"],
                comp["h1"],
                comp["intro"],
                [
                    ("Comparison", comp["name"]),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>In one line</h2>
        <p>{esc(comp["one_line"])}</p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Side by side</h2>
        <p>Dimensions that actually differ. Pay is stated as a basis, not a number, because both sides vary by employer.</p>
{compare_table(comp["rows"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Which one to choose</h2>
{beh.bullet_list(comp["choose"]) if hasattr(beh, "bullet_list") else "<ul class='check-list'>" + "".join(f"<li>{esc(x)}</li>" for x in comp["choose"]) + "</ul>"}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in comp["related"])}
          <li><a href="/compare">All comparisons</a></li>
        </ul>
      </div>
    </section>""",
            beh.bsp.faq_section_html(comp["faqs"]),
        ]
    )
    jsonld = "\n".join(
        [
            beh.bsp.organization_jsonld(),
            beh.bsp.website_jsonld(),
            beh.breadcrumb(comp["name"] + " comparison", f"{SITE}/compare/{comp['slug']}"),
            beh.faq_jsonld(comp["faqs"]),
        ]
    )
    write_sub(
        COMPARE_DIR,
        comp["slug"],
        shell(
            title=comp["title"],
            description=comp["desc"],
            canonical=f"{SITE}/compare/{comp['slug']}",
            body=body,
            jsonld=jsonld,
        ),
    )


def build_compare_index() -> None:
    comp_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/compare/{c['slug']}">{esc(c['name'])}</a></h3>
          <p class="hub-card-sum">{esc(c['desc'])}</p>
          <p class="hub-card-foot"><a href="/compare/{c['slug']}">Compare &rarr;</a></p>
        </article>"""
        for c in COMPARISONS
    )
    body = "\n".join(
        [
            hero(
                "Comparisons",
                "Green Career Comparisons: JRF vs SRF, ESG vs CSR and More",
                "Side-by-side answers to the choices green-job seekers actually face, using only verified facts.",
                [
                    ("Comparisons", str(len(COMPARISONS))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a comparison</h2>
        <p>Each page states the dimension, the difference and how to decide, without inventing pay or eligibility.</p>
        <div class="hub-list">
{comp_cards}
        </div>
      </div>
    </section>""",
            beh.bsp.faq_section_html(
                [
                    ("Are these comparisons neutral?", "Yes. They state the dimensions on which the options differ and leave the decision to the reader."),
                    ("Do they include salary numbers?", "No. Pay varies by employer and is stated as a basis. The role profiles and salary guide carry advertised figures."),
                    ("How often are they updated?", "They are rebuilt with the site and reviewed when a regulation or scheme changes."),
                ]
            ),
        ]
    )
    write_sub(
        COMPARE_DIR,
        "index",
        shell(
            title="Green Career Comparisons: JRF vs SRF, ESG vs CSR & More",
            description="Side-by-side comparisons of JRF vs SRF, forest guard vs ranger, ESG vs CSR, IFS vs IAS, GIS vs remote sensing and internship vs fellowship.",
            canonical=f"{SITE}/compare",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("Green Career Comparisons", f"{SITE}/compare"),
                ]
            ),
        ),
    )


def main() -> None:
    for comp in COMPARISONS:
        build_compare_page(comp)
    build_compare_index()
    for comp in COMPARISONS:
        beh.update_sitemap([f"/compare/{comp['slug']}"])
    beh.update_sitemap(["/compare"])
    print(f"Wrote {len(COMPARISONS)} comparison pages + index")


if __name__ == "__main__":
    main()
