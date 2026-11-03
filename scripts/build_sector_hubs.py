#!/usr/bin/env python3
"""Build hub pages for five new green sectors.

Sectors: renewable energy, electric mobility, waste & circular economy,
water & WASH, green building. Each hub has educational content (FAQs,
skills, pathways) so it is valuable even before listings accumulate, plus
auto-filtered openings from the registry.

Run after build_seo_pages.py:

    py scripts/build_sector_hubs.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = __import__("datetime").date.today()

esc = beh.esc
plain = beh.plain
cards = beh.cards
hero = beh.hero
section = beh.section
shell = beh.shell
write_sub = beh.write_sub if hasattr(beh, "write_sub") else None


def write_sub_local(dir_path: Path, slug: str, html: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")


write_sub = write_sub_local

JOBS = beh.active(beh.load(beh.JOBS_PATH))
GLOBAL = beh.active(beh.load(beh.GLOBAL_PATH))
POOL = JOBS + GLOBAL


def match_sector(keywords: List[str]) -> List[Dict[str, Any]]:
    result = []
    for job in POOL:
        text = " ".join(str(job.get(k) or "") for k in ("clean_title", "category", "role_summary", "must_have_skills")).lower()
        if any(kw in text for kw in keywords):
            result.append(job)
    result.sort(key=lambda j: str(j.get("valid_through") or "9999"))
    return result


SECTORS: List[Dict[str, Any]] = [
    {
        "slug": "renewable-energy-jobs",
        "name": "Renewable Energy Jobs",
        "h1": "Renewable Energy Jobs in India 2026",
        "title": "Renewable Energy Jobs in India 2026: Solar, Wind & Green Hydrogen",
        "desc": "Renewable energy jobs in India: solar, wind, green hydrogen and battery storage. Roles, skills, employers and how to enter.",
        "kicker": "Clean energy sector",
        "sub": "India has one of the world's largest renewable energy targets. Solar, wind, green hydrogen and battery storage are creating engineering, project management and policy roles at scale.",
        "keywords": ["renewable", "solar", "wind", "green hydrogen", "clean energy", "battery storage", "photovoltaic", "wind turbine"],
        "what": "Renewable energy is India's largest green employer. Roles span project development, engineering, operations and maintenance, policy and finance.",
        "entry": [
            "A bachelor's in electrical, mechanical or energy engineering is the standard entry for technical roles.",
            "Solar PV design, wind resource assessment and grid integration are the most listed technical skills.",
            "Site and field experience, even as an intern, is valued more than a second certificate.",
            "State renewable energy agencies, private developers and EPC contractors are the main employers.",
            "India's renewable target of 500 GW by 2030 means sustained hiring for the next decade.",
        ],
        "skills": ["Solar PV Design", "Wind Resource Assessment", "Grid Integration", "Project Management", "Electrical Engineering", "AutoCAD", "SCADA", "Energy Modelling"],
        "ladder": "Graduate Engineer Trainee -> Renewable Energy Engineer -> Senior Engineer -> Project Manager -> Head of Projects",
        "faqs": [
            ("Is renewable energy a good career in India?", "Yes. India has one of the world's largest renewable targets and the sector hires engineers, project managers and analysts at scale."),
            ("Do I need a master's degree?", "Not for most plant and design roles. Research and R&D posts often prefer one."),
            ("Are government jobs available?", "Yes. State renewable energy agencies and public sector units recruit engineers regularly."),
            ("What is the pay like?", "Entry-level engineers start at 4-8 LPA. Project managers and senior engineers earn 12-25 LPA. Pay varies by company size and location."),
        ],
        "related": [("/roles/renewable-energy-engineer", "Renewable energy engineer profile"), ("/exams", "Exam and eligibility guides"), ("/green-careers", "Green career pathways")],
    },
    {
        "slug": "electric-mobility-jobs",
        "name": "Electric Mobility & Clean Transport Jobs",
        "h1": "Electric Mobility & EV Jobs in India 2026",
        "title": "Electric Mobility & EV Jobs in India 2026: Manufacturing, Charging & Policy",
        "desc": "Electric mobility and EV jobs in India: manufacturing, charging infrastructure, battery technology, policy and fleet management.",
        "kicker": "Clean transport sector",
        "sub": "India's EV transition is creating jobs in manufacturing, charging infrastructure, battery technology and policy. The sector is growing at 40%+ annually.",
        "keywords": ["electric vehicle", "ev ", "e-mobility", "electric mobility", "charging", "battery", "electric car", "electric bus", "fleet"],
        "what": "Electric mobility is India's fastest-growing green sector. Roles span vehicle manufacturing, charging infrastructure, battery technology, policy and fleet operations.",
        "entry": [
            "A bachelor's in mechanical, electrical or automotive engineering is the standard entry for technical roles.",
            "Battery technology, power electronics and charging protocols are the most listed technical skills.",
            "EV startups and established OEMs (Tata, Mahindra, Ola, Ather) are the main employers.",
            "Policy and planning roles require knowledge of FAME scheme, state EV policies and charging standards.",
            "The sector hires across engineering, software, operations and policy functions.",
        ],
        "skills": ["Battery Technology", "Power Electronics", "EV Charging", "Automotive Engineering", "Embedded Systems", "CAN Bus", "MATLAB", "Python"],
        "ladder": "Graduate Engineer Trainee -> EV Engineer -> Senior Engineer -> Technical Lead -> Head of EV Technology",
        "faqs": [
            ("Is EV a good career in India?", "Yes. India's EV market is growing at 40%+ annually with strong government support through FAME and state EV policies."),
            ("Do I need an automotive degree?", "Not necessarily. Electrical and mechanical engineers are hired widely. Software engineers are in high demand for connected vehicle systems."),
            ("Are government jobs available in EV?", "Yes. State transport departments, BEE and NITI Aayog have EV policy and implementation roles."),
            ("What is FAME?", "Faster Adoption and Manufacturing of Electric Vehicles — India's subsidy scheme for EV adoption."),
        ],
        "related": [("/roles/renewable-energy-engineer", "Renewable energy engineer profile"), ("/green-careers", "Green career pathways"), ("/glossary/esg", "ESG glossary entry")],
    },
    {
        "slug": "waste-management-jobs",
        "name": "Waste Management & Circular Economy Jobs",
        "h1": "Waste Management & Circular Economy Jobs in India 2026",
        "title": "Waste Management Jobs in India 2026: EPR, Recycling & Circular Economy",
        "desc": "Waste management and circular economy jobs in India: EPR compliance, recycling, waste-to-energy, and sustainable materials.",
        "kicker": "Waste & circularity sector",
        "sub": "India's EPR rules for plastic, e-waste and batteries are creating compliance demand. Waste management, recycling and circular economy roles are growing.",
        "keywords": ["waste", "recycl", "circul", "epr", "solid waste", "waste-to-energy", "landfill", "composting"],
        "what": "Waste management and circular economy roles cover waste collection, processing, recycling, EPR compliance and waste-to-energy. India's EPR rules are driving hiring.",
        "entry": [
            "A degree in environmental engineering, chemistry or waste management is common.",
            "Knowledge of EPR rules, waste classification and treatment technologies is listed in most postings.",
            "Field experience at waste processing facilities is valued.",
            "NGOs, consultancies, waste management companies and government agencies are the main employers.",
            "EPR compliance roles are the fastest-growing segment in this sector.",
        ],
        "skills": ["Waste Management", "EPR Compliance", "Recycling", "Environmental Engineering", "Waste-to-Energy", "Life Cycle Assessment", "Circular Economy", "Hazardous Waste"],
        "ladder": "Waste Management Executive -> Specialist -> Manager -> Head of Sustainability",
        "faqs": [
            ("What is EPR?", "Extended Producer Responsibility makes producers responsible for end-of-life management of their products. India has EPR rules for plastic, e-waste and batteries."),
            ("Are waste jobs well paid?", "Entry-level roles are modestly paid; senior roles in waste-to-energy and consulting pay well."),
            ("Is this a government or private sector role?", "Both. State pollution boards and private waste companies hire."),
            ("Is circular economy the same as recycling?", "No. Recycling is the last resort. Circular economy includes designing out waste and keeping materials in use."),
        ],
        "related": [("/roles/waste-circular-economy", "Waste management career profile"), ("/glossary/circular-economy", "Circular economy glossary"), ("/exams/state-pollution-control-board", "State pollution board guide")],
    },
    {
        "slug": "water-wash-jobs",
        "name": "Water Resources & WASH Jobs",
        "h1": "Water & WASH Jobs in India 2026",
        "title": "Water & WASH Jobs in India 2026: Jal Jeevan, Treatment & Sanitation",
        "desc": "Water resources and WASH jobs in India: Jal Jeevan Mission, water treatment, sanitation, hydrology. Roles, skills and employers.",
        "kicker": "Water & sanitation sector",
        "sub": "Jal Jeevan Mission and urban water projects are creating demand for water engineers, hydrologists and WASH specialists across India.",
        "keywords": ["water", "wash", "hydro", "sanitation", "jal jeevan", "water treatment", "effluent", "sewage"],
        "what": "Water and WASH roles cover water supply, sanitation, treatment and resource management. Jal Jeevan Mission and urban water projects drive demand.",
        "entry": [
            "A degree in civil engineering, environmental engineering or water resources is standard.",
            "Knowledge of water treatment, hydrology and sanitation systems is listed in most postings.",
            "Field experience with water projects is valued.",
            "Government agencies, NGOs and consultancies are the main employers.",
            "Jal Jeevan Mission is creating thousands of water-related roles across rural India.",
        ],
        "skills": ["Water Treatment", "Hydrology", "Sanitation", "Environmental Engineering", "GIS", "Water Quality Monitoring", "Project Management", "WASH"],
        "ladder": "Water Engineer -> Specialist -> Manager -> Head of Water Programmes",
        "faqs": [
            ("What is WASH?", "Water, Sanitation and Hygiene — a sector covering safe water supply, sanitation and hygiene promotion."),
            ("Is Jal Jeevan Mission hiring?", "Yes, through state implementing agencies and partner organisations."),
            ("Do I need a civil engineering degree?", "For engineering posts, yes. Science graduates apply to monitoring and programme roles."),
            ("Are water jobs well paid?", "Government posts follow pay matrix rules. Private and NGO roles vary by organisation and location."),
        ],
        "related": [("/roles/water-wash-specialist", "Water and WASH specialist profile"), ("/exams/state-pollution-control-board", "State pollution board guide"), ("/green-careers", "Green career pathways")],
    },
    {
        "slug": "green-building-jobs",
        "name": "Green Building & Sustainable Construction Jobs",
        "h1": "Green Building Jobs in India 2026",
        "title": "Green Building Jobs in India 2026: LEED, GRIHA & Sustainable Construction",
        "desc": "Green building jobs in India: LEED, GRIHA, IGBC certification, energy efficiency, sustainable construction. Roles, skills and employers.",
        "kicker": "Built environment sector",
        "sub": "India is one of the top countries for LEED-certified space. Green building, energy efficiency and sustainable construction roles are growing in real estate and consulting.",
        "keywords": ["green building", "leed", "griha", "igbc", "built environment", "building energy", "energy efficiency", "sustainable construction", "architecture"],
        "what": "Green building specialists work on certification (LEED, GRIHA, IGBC), energy efficiency and sustainable construction. Real estate developers and consulting firms hire.",
        "entry": [
            "A degree in architecture, civil engineering or environmental engineering is standard.",
            "LEED or GRIHA accreditation is listed in most postings.",
            "Energy modelling and building simulation skills are valued.",
            "Consulting firms and real estate developers are the main employers.",
            "India is among the top countries for LEED-certified space, creating sustained demand.",
        ],
        "skills": ["LEED", "GRIHA", "IGBC", "Energy Modelling", "Building Simulation", "Sustainable Design", "Green Construction", "Energy Audit"],
        "ladder": "Green Building Analyst -> Specialist -> Manager -> Head of Sustainability",
        "faqs": [
            ("What is LEED?", "Leadership in Energy and Environmental Design — a global green building certification by USGBC."),
            ("What is GRIHA?", "Green Rating for Integrated Habitat Assessment — India's national green building rating system."),
            ("Is green building a growing field?", "Yes. India is among the top countries for LEED-certified space and IGBC membership is growing."),
            ("Do I need an architecture degree?", "For design roles, yes. For certification and energy audit roles, engineering backgrounds are accepted."),
        ],
        "related": [("/roles/green-building", "Green building specialist profile"), ("/glossary/esg", "ESG glossary entry"), ("/green-careers", "Green career pathways")],
    },
]


def build_sector_page(sector: Dict[str, Any]) -> None:
    live = match_sector(sector["keywords"])
    body = "\n".join([
        hero(sector["kicker"], sector["h1"], sector["sub"], [("Live openings", str(len(live))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>What the sector involves</h2>
        <p>{esc(sector["what"])}</p>
        <ul class="check-list">
          {''.join(f'<li>{esc(tip)}</li>' for tip in sector["entry"])}
        </ul>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Skills employers list</h2>
        <p class="skill-row">
          {''.join(f'<span class="badge badge-type">{esc(s)}</span>' for s in sector["skills"])}
        </p>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live openings ({len(live)})</h2>
        <p>Sorted by closing date. Each links to the full dossier and the official application page.</p>
        <div class="hub-list">
{cards(live[:12]) if live else '<p class="hub-empty">No live listing in this sector today. New roles are added daily as they are published.</p>'}
        </div>
      </div>
    </section>""",
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in sector["related"])}
          <li><a href="/green-careers">Green career pathways</a></li>
          <li><a href="/salary-guide">Salary guide</a></li>
        </ul>
      </div>
    </section>""",
        beh.bsp.faq_section_html(sector["faqs"]),
    ])
    jsonld = "\n".join([
        beh.bsp.organization_jsonld(),
        beh.bsp.website_jsonld(),
        beh.breadcrumb(sector["name"], f"{SITE}/{sector['slug']}"),
        beh.faq_jsonld(sector["faqs"]),
    ])
    write_sub(PUBLIC, sector["slug"], shell(
        title=sector["title"],
        description=sector["desc"],
        canonical=f"{SITE}/{sector['slug']}",
        body=body,
        jsonld=jsonld,
    ))


def build_sector_index() -> None:
    sector_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/{s['slug']}">{esc(s['name'])}</a></h3>
          <p class="hub-card-sum">{esc(s['desc'])}</p>
          <p class="hub-card-foot"><span>{len(match_sector(s['keywords']))} live opening(s)</span>
            <a href="/{s['slug']}">Browse &rarr;</a></p>
        </article>"""
        for s in SECTORS
    )
    body = "\n".join([
        hero("Sector hubs", "Green Job Sectors in India", "Browse green jobs by sector: renewable energy, electric mobility, waste management, water and WASH, and green building.", [("Sectors", str(len(SECTORS))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Choose a sector</h2>
        <p>Each hub lists live openings and explains how to enter the sector.</p>
        <div class="hub-list">
{sector_cards}
        </div>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Are these sectors growing?", "Yes. Renewable energy, electric mobility and waste management are among India's fastest-growing green sectors."),
            ("Do I need a specific degree?", "It depends on the sector. Engineering degrees are common for technical roles; science and policy backgrounds for research and advisory roles."),
            ("How do I find jobs in these sectors?", "Browse the sector hub for live openings, or use the search page to filter by skill and city."),
        ]),
    ])
    write_sub(PUBLIC, "green-sectors", shell(
        title="Green Job Sectors in India: Renewable Energy, EV, Waste, Water & Green Building",
        description="Browse green jobs by sector: renewable energy, electric mobility, waste management, water and WASH, and green building. Live openings and career guides.",
        canonical=f"{SITE}/green-sectors",
        body=body,
        jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb("Green Job Sectors", f"{SITE}/green-sectors")]),
    ))


def main() -> None:
    for sector in SECTORS:
        build_sector_page(sector)
    build_sector_index()

    paths = ["/green-sectors"] + [f"/{s['slug']}" for s in SECTORS]
    beh.update_sitemap(paths)
    print(f"Wrote {len(SECTORS)} sector hubs + index")


if __name__ == "__main__":
    main()
