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
    {
        "name": "QGIS for Environmental and Geospatial Jobs",
        "provider": "QGIS Project / OSGeo (free, open-source)",
        "url": "https://qgis.org",
        "what": "Hands-on QGIS training for maps, spatial data, land-use mapping and field-data analysis. The free software most GIS trainee and mapping-associate roles expect candidates to know.",
        "who_asks": "GIS trainee, mapping associate, GIS analyst, project associate",
        "roles": ["/roles/gis-analyst", "/roles/project-associate", "/roles/junior-research-fellow"],
        "level": "Beginner to intermediate",
        "cost": "Free (QGIS + official documentation and community tutorials)",
        "duration": "6-10 weeks self-paced",
        "audience": "Freshers, geography / environment / civil graduates, and research scholars who need to produce publishable maps without an ArcGIS licence.",
        "curriculum": [
            "Map theory: projections, coordinate systems, scales and symbology for Indian maps",
            "Digitisation and georeferencing of Survey of India toposheets and satellite imagery",
            "Vector editing, topology and attribute-table data cleaning",
            "LULC, land-use and building-footprint mapping workflows (the exact tasks GeoNxt and Axiom trainees do)",
            "Raster analysis: NDVI, clipping, reclassification and terrain analysis",
            "QGIS plugins, layouts and exporting maps that look professional in reports",
            "Portfolio project: a land-use map of your district with a one-page report",
        ],
        "outcomes": [
            "Produce a complete LULC or building-footprint map from raw data",
            "Georeference and digitise paper maps and satellite imagery",
            "Build a print-ready map layout with symbols and a clear legend",
            "Show a real GIS portfolio in interviews instead of only a certificate",
        ],
    },
    {
        "name": "ArcGIS Pro for GIS Analysts",
        "provider": "Esri",
        "url": "https://www.esri.com/en-us/arcgis/products/arcgis-pro/overview",
        "what": "Esri's desktop GIS platform used by government departments, urban-planning boards and large consultancies. Covers map production, spatial analysis and geodatabase workflows employers list in senior GIS notices.",
        "who_asks": "GIS analyst, GIS planner, GIS manager, urban planner",
        "roles": ["/roles/gis-analyst", "/roles/project-associate"],
        "level": "Intermediate",
        "cost": "Paid (ArcGIS licence / Esri Academy)",
        "duration": "8-12 weeks self-paced",
        "audience": "Candidates targeting state GIS cells (like NIT Calicut CoEUPD and Uttarakhand GIS roles), PRSC/ISRO project posts, and consultancy jobs that list ArcGIS Pro explicitly.",
        "curriculum": [
            "ArcGIS Pro interface, projects and data management",
            "Editing, georeferencing and geodatabase design",
            "Spatial analysis with overlay, buffer and suitability tools",
            "Raster and 3D analysis for urban and environmental planning",
            "Cartography, labelling and professional layouts",
            "ArcGIS Online sharing and working with field data",
            "Case study: a city land-use suitability map end to end",
        ],
        "outcomes": [
            "Work confidently in ArcGIS Pro based offices and GIS cells",
            "Design a geodatabase and run overlay/suitability analysis",
            "Produce publication-quality maps with professional symbology",
            "Read ArcGIS-heavy job descriptions without guessing",
        ],
    },
    {
        "name": "Google Earth Engine for Earth Observation",
        "provider": "Google",
        "url": "https://earthengine.google.com",
        "what": "Cloud-based Earth-observation platform for analysing Sentinel, Landsat and MODIS imagery at scale. The toolkit behind most modern climate, vegetation-change and urban-heat research roles.",
        "who_asks": "Research associate, project associate, climate analyst, GIS analyst",
        "roles": ["/roles/gis-analyst", "/roles/junior-research-fellow", "/roles/project-associate", "/roles/climate-risk-analyst"],
        "level": "Intermediate",
        "cost": "Free (research and education use)",
        "duration": "8-12 weeks self-paced",
        "audience": "Postgraduates and JRF/Project Associate candidates wanting to move beyond desktop mapping into data-driven climate and land-change research.",
        "curriculum": [
            "JavaScript API and Code Editor basics for Earth Engine",
            "Loading Sentinel-2 and Landsat collections and cloud masking",
            "NDVI, SAVI and vegetation-change time series",
            "Supervised classification for land-use and land-cover mapping",
            "Urban heat island analysis with land-surface temperature",
            "Exporting charts, maps and statistics for research papers",
            "Project: a 10-year vegetation-trend study of your home district",
        ],
        "outcomes": [
            "Analyse satellite imagery for any district in minutes",
            "Build a defensible forest-change or heat-island study",
            "Write the methods section of a research paper with real data",
            "Stand out in JRF/Project Associate interviews with a live demo",
        ],
    },
    {
        "name": "Remote Sensing Fundamentals and Image Classification",
        "provider": "Indian Institute of Remote Sensing (IIRS), ISRO / open learning",
        "url": "https://www.iirs.gov.in",
        "what": "Core remote-sensing theory and practice: sensor physics, image interpretation, and supervised/unsupervised classification. The foundation every PRSC, NRSC and university GIS post quietly assumes.",
        "who_asks": "JRF, project associate, remote sensing assistant, research associate",
        "roles": ["/roles/junior-research-fellow", "/roles/project-associate", "/roles/gis-analyst"],
        "level": "Beginner to intermediate",
        "cost": "Free (IIRS outreach / open courses) to paid (certificate courses)",
        "duration": "10-14 weeks self-paced",
        "audience": "M.Sc. Remote Sensing, Geography, Earth Science and Environmental Science students preparing for JRF, PRSC and project-associate screening tests.",
        "curriculum": [
            "Electromagnetic spectrum, sensors and the Sentinel/Landsat/IRIS family",
            "Image geometry and radiometric corrections",
            "Visual image interpretation of terrain, water, vegetation and settlements",
            "Spectral signatures and indices (NDVI, NDWI, NDBI)",
            "Supervised classification: training data, algorithms and accuracy assessment",
            "Change detection for deforestation, urban growth and water bodies",
            "Mock screening: a 30-question practice test with explanations",
        ],
        "outcomes": [
            "Explain how sensors see the Earth in a JRF interview",
            "Classify a satellite image and report accuracy honestly",
            "Detect land-use change between two dates with a clear map",
            "Answer the theory questions that screen GIS/RS notices",
        ],
    },
    {
        "name": "Drone and Aerial Mapping for Geospatial Surveys",
        "provider": "DJI Academy / ISRO-registered training centres",
        "url": "https://www.dji.com/academy",
        "what": "Drone surveying, photogrammetry and orthomosaic mapping for land records, mining, forestry and infrastructure surveys. A fast-growing niche in government and consultancy GIS teams.",
        "who_asks": "GIS analyst, survey associate, drone operator, project associate",
        "roles": ["/roles/gis-analyst", "/roles/project-associate", "/roles/environmental-engineer"],
        "level": "Intermediate",
        "cost": "Paid (course + DGCA RPTO training where required)",
        "duration": "4-8 weeks",
        "audience": "Field-oriented candidates who want to combine drone flying with GIS processing, and current GIS trainees moving into survey roles.",
        "curriculum": [
            "Drone regulations in India (DGCA rules, RPTO and permissions)",
            "Flight planning: overlap, GSD and ground control points",
            "Photogrammetry software: orthomosaics, DSM/DTM and 3D models",
            "Volume estimation for mines, quarries and stockpiles",
            "Crop-health and NDVI mapping from drone imagery",
            "Integrating drone outputs into QGIS/ArcGIS workflows",
            "Field safety, batteries and data backup discipline",
        ],
        "outcomes": [
            "Plan and fly a legal, repeatable survey mission",
            "Produce an orthomosaic and digital surface model",
            "Estimate volumes and crop health from drone data",
            "Add a high-demand drone skill to a GIS CV",
        ],
    },
    {
        "name": "GNSS and GPS Surveying for Field Mapping",
        "provider": "Survey of India / CSIR training programmes",
        "url": "https://www.surveyofindia.gov.in",
        "what": "GPS/GNSS field surveying: coordinate systems, DGPS/RTK workflows and field-data collection that research and infrastructure projects depend on for accurate ground truth.",
        "who_asks": "Field investigator, project associate, GIS analyst, survey associate",
        "roles": ["/roles/gis-analyst", "/roles/project-associate", "/roles/biodiversity-analyst"],
        "level": "Beginner to intermediate",
        "cost": "Free concepts / paid instrument training",
        "duration": "4-6 weeks",
        "audience": "Candidates joining field-based JRF and project positions where GPS ground-truthing is a daily task, not just screen work.",
        "curriculum": [
            "Coordinate systems made practical: WGS84, UTM and datum shifts",
            "Handheld GPS vs DGPS vs RTK — accuracy, cost and when each fits",
            "Collecting clean field data: points, tracks and attributes",
            "Ground control points for satellite and drone imagery",
            "Converting field data into GIS-ready layers",
            "Quality checks: PDOP, fix types and error budgets",
            "Field protocol: a one-day ground-truthing checklist you can reuse",
        ],
        "outcomes": [
            "Collect survey-grade field data with confidence",
            "Validate satellite and drone maps with real ground points",
            "Convert GPS logs into clean GIS layers without losing accuracy",
            "Work independently in field teams for JRF and project posts",
        ],
    },
]


def build_course_page(course: Dict[str, Any]) -> None:
    extra = ""
    if course.get("curriculum"):
        items = "".join(f"<li>{esc(x)}</li>" for x in course["curriculum"])
        extra += f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>What you will learn</h2>
        <p>{esc(course.get("audience", ""))}</p>
        <ul class="check-list">{items}</ul>
      </div>
    </section>"""
    if course.get("outcomes"):
        items = "".join(f"<li>{esc(x)}</li>" for x in course["outcomes"])
        extra += f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>What you will be able to do</h2>
        <ul class="check-list">{items}</ul>
      </div>
    </section>"""
    faqs = [
        (f"Is {course['name']} worth it?", "It depends on your target role. Check the 'who asks for it' section above. If your target employers list it, it is worth the investment."),
        ("Can I learn this for free?", "Most frameworks publish their standards for free. Certification exams and training courses are usually paid."),
        ("How long does it take?", f"Typically {course['duration']}. Self-paced options are available for most."),
    ]
    if course.get("curriculum"):
        faqs.append(("Do I need a certificate, or is a portfolio better?", "For GIS and remote-sensing roles, a small portfolio (a completed map or study with a one-page report) usually matters more than a certificate. Complete the portfolio project in the curriculum and link it in your CV."))
        faqs.append(("Which software do I need?", "Start with the free tools named in the curriculum. Paid software is worth buying only when a target employer requires it."))
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
        extra,
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related role profiles</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{r}">{r.split("/")[-1].replace("-", " ").title()}</a></li>' for r in course["roles"])}
        </ul>
      </div>
    </section>""",
        beh.bsp.faq_section_html(faqs),
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
        title="Green Job Certifications & GIS Courses: QGIS, ArcGIS, GEE, GRI, BRSR & More",
        description="Certifications and courses for green jobs in India: QGIS, ArcGIS Pro, Google Earth Engine, remote sensing, drones, GNSS, GRI, BRSR, LEED, GHG Protocol and more.",
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
