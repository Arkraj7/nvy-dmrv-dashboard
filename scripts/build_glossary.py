#!/usr/bin/env python3
"""Build the ESG/climate glossary and a "new this week" digest.

Glossary
--------
Short, citable definitions of the terms that recur in green-job notices
(BRSR, ESG, GHG Protocol, carbon credit, net zero, SBTi, dMRV, Nagar Van,
CAMPA, JRF, SRF, EIA, EHS, circular economy, greenwashing). Each page cites
an official source and links to the jobs and guides that use the term, so it
earns informational search traffic without inventing anything.

New this week
-------------
A digest of listings added to the registry in the last seven days, grouped by
category. It is the page a returning visitor bookmarks and the one search
engines re-crawl most often.
"""

from __future__ import annotations

import re

from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import build_expansion_hubs as beh

PUBLIC = beh.PUBLIC
SITE = beh.SITE
TODAY = date.today()

esc = beh.esc
plain = beh.plain
cards = beh.cards
hero = beh.hero
section = beh.section
shell = beh.shell
def write_sub(dir_path, slug, html):
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / f"{slug}.html").write_text(html, encoding="utf-8")
add_sitemap = lambda path, cf, pr: beh.update_sitemap([path])


def bullet_list(items):
    return "        <ul class=\"check-list\">\n" + "\n".join(f"          <li>{item}</li>" for item in items) + "\n        </ul>"


def cards_block(jobs, empty_note):
    if not jobs:
        return f'        <p class="hub-empty">{esc(empty_note)}</p>'
    return '        <div class="hub-list">\n' + cards(jobs) + '\n        </div>'

INDIA = beh.active(beh.load(beh.JOBS_PATH))
GLOBAL = beh.active(beh.load(beh.GLOBAL_PATH))
POOL = INDIA + GLOBAL

GLOSSARY_DIR = PUBLIC / "glossary"


def match_any(*patterns: str) -> Callable[[Dict[str, Any]], bool]:
    compiled = [re.compile(p) for p in patterns]

    def matcher(job: Dict[str, Any]) -> bool:
        text = " ".join(
            str(job.get(k) or "")
            for k in ("clean_title", "category", "role_summary", "organization")
        ).lower()
        return any(r.search(text) for r in compiled)

    return matcher


TERMS: List[Dict[str, Any]] = [
    {
        "slug": "brsr",
        "term": "BRSR",
        "full": "Business Responsibility and Sustainability Reporting",
        "h1": "What is BRSR? Business Responsibility and Sustainability Reporting",
        "title": "What is BRSR? Business Responsibility & Sustainability Reporting Explained",
        "desc": "BRSR is SEBI's reporting framework for listed Indian companies. What it covers, who must file it, and why it drives ESG hiring.",
        "kicker": "Reporting framework",
        "definition": (
            "BRSR is the disclosure framework introduced by SEBI for listed Indian companies. It "
            "replaced the earlier Business Responsibility Report (BRR) and asks companies to report "
            "environmental, social and governance information in a structured, comparable format."
        ),
        "why": [
            "It is mandatory for the top 1000 listed companies by market capitalisation, phased in from FY2022-23.",
            "It covers energy, water, waste, emissions, employee welfare, diversity and community impact.",
            "Because the data must be collected, verified and disclosed, it created a large share of India's ESG analyst and sustainability manager demand.",
        ],
        "source_label": "Securities and Exchange Board of India (SEBI)",
        "source_url": "https://www.sebi.gov.in",
        "match": match_any(r"\besg\b", r"\bbrsr\b", r"sustainability"),
        "related": [("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"), ("/roles/esg-analyst", "ESG analyst salary and career profile")],
        "faqs": [
            ("Is BRSR mandatory for all companies?", "No. It applies to the top 1000 listed companies by market capitalisation. Smaller listed companies file voluntarily or under lighter requirements."),
            ("Is BRSR the same as GRI?", "No. GRI is a global standard; BRSR is SEBI's India-specific framework. Companies often report both because investors ask for GRI."),
            ("Does BRSR require third-party assurance?", "Assurance requirements are being phased in. Check the latest SEBI circular rather than an old summary."),
        ],
    },
    {
        "slug": "esg",
        "term": "ESG",
        "full": "Environmental, Social and Governance",
        "h1": "What is ESG? Environmental, Social and Governance Explained",
        "title": "What is ESG? Environmental, Social & Governance Explained",
        "desc": "ESG explained in plain terms: what the three letters stand for, how investors and regulators use them, and where the jobs are.",
        "kicker": "Concept",
        "definition": (
            "ESG stands for Environmental, Social and Governance. It is a way of evaluating a company "
            "beyond its financial statements, covering how it affects the environment, treats people "
            "and is run."
        ),
        "why": [
            "Environmental covers emissions, energy, water, waste and biodiversity.",
            "Social covers workers, communities, customers and human rights.",
            "Governance covers board structure, ethics, disclosure and risk management.",
            "In India, ESG hiring is driven by SEBI's BRSR requirements, investor pressure and export-market expectations.",
        ],
        "source_label": "Global Reporting Initiative (GRI) and SEBI",
        "source_url": "https://www.sebi.gov.in",
        "match": match_any(r"\besg\b", r"sustainability"),
        "related": [("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"), ("/roles/esg-analyst", "ESG analyst career profile")],
        "faqs": [
            ("Is ESG the same as CSR?", "No. CSR is a spending obligation under the Companies Act. ESG is a broader performance and disclosure framework."),
            ("Is ESG regulated in India?", "Partly. SEBI mandates BRSR disclosure for large listed companies and regulates ESG funds and ratings."),
            ("Do ESG roles need a science degree?", "No. Many postings accept economics, business, law and social-science backgrounds."),
        ],
    },
    {
        "slug": "ghg-protocol",
        "term": "GHG Protocol",
        "full": "Greenhouse Gas Protocol",
        "h1": "What is the GHG Protocol? Scope 1, 2 and 3 Explained",
        "title": "What is the GHG Protocol? Scope 1, 2 & 3 Explained",
        "desc": "The GHG Protocol is the standard for measuring corporate greenhouse-gas emissions. Scope 1, 2 and 3 explained.",
        "kicker": "Measurement standard",
        "definition": (
            "The Greenhouse Gas Protocol is the most widely used standard for measuring and managing "
            "greenhouse-gas emissions. It was developed by the World Resources Institute and the "
            "World Business Council for Sustainable Development."
        ),
        "why": [
            "Scope 1 covers direct emissions from sources a company owns or controls.",
            "Scope 2 covers indirect emissions from purchased electricity, heat and steam.",
            "Scope 3 covers all other indirect emissions, including supply chains and product use.",
            "Carbon accounting, ESG reporting and target-setting roles all start from a GHG inventory, so the protocol is the core skill.",
        ],
        "source_label": "World Resources Institute (WRI)",
        "source_url": "https://ghgprotocol.org",
        "match": match_any(r"carbon", r"ghg", r"decarbon"),
        "related": [("/roles/carbon-analyst", "Carbon analyst career profile"), ("/esg-carbon-sustainability-jobs", "ESG and carbon jobs")],
        "faqs": [
            ("Which scope is hardest to measure?", "Scope 3, because it sits in supply chains and product use outside the company's direct control."),
            ("Is the GHG Protocol mandatory?", "Not by itself. Regulators and investors require emission reporting, and the protocol is the common method used to produce it."),
            ("Do I need to memorise emission factors?", "No. Practitioners use databases and tools. The skill is knowing the boundaries and categories."),
        ],
    },
    {
        "slug": "carbon-credit",
        "term": "Carbon credit",
        "full": "Carbon credit / carbon market",
        "h1": "What is a Carbon Credit? Carbon Markets Explained",
        "title": "What is a Carbon Credit? Carbon Markets Explained",
        "desc": "A carbon credit represents one tonne of CO2e reduced or removed. How carbon markets work and what it means for jobs.",
        "kicker": "Market mechanism",
        "definition": (
            "A carbon credit is a tradable certificate representing one tonne of carbon dioxide "
            "equivalent that has been reduced, avoided or removed from the atmosphere. Carbon markets "
            "let emitters buy credits to offset emissions they cannot yet eliminate."
        ),
        "why": [
            "Voluntary carbon markets trade credits from projects such as forestry, renewables and cookstoves.",
            "Compliance markets are created by regulation, such as the EU Emissions Trading System.",
            "India is developing its own carbon credit trading scheme, which is creating demand for MRV and carbon accounting skills.",
            "Jobs in this area include carbon analysts, project developers, verifiers and registry staff.",
        ],
        "source_label": "UNFCCC and the World Bank carbon pricing dashboard",
        "source_url": "https://unfccc.int",
        "match": match_any(r"carbon", r"climate"),
        "related": [("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs"), ("/roles/carbon-analyst", "Carbon analyst career profile")],
        "faqs": [
            ("Is a carbon credit the same as a carbon offset?", "In practice the terms are used interchangeably, though 'offset' describes the use and 'credit' the unit."),
            ("Are carbon credits controversial?", "Yes. Quality, additionality and double counting are debated. Good projects publish their methodology and verification."),
            ("Can individuals buy carbon credits?", "Yes, through voluntary market retailers, though the impact depends on the project quality."),
        ],
    },
    {
        "slug": "net-zero",
        "term": "Net zero",
        "full": "Net-zero emissions",
        "h1": "What is Net Zero? Definition and Climate Targets Explained",
        "title": "What is Net Zero? Definition & Climate Targets Explained",
        "desc": "Net zero means cutting emissions to as close to zero as possible, with residual emissions balanced by removals. Explained.",
        "kicker": "Climate target",
        "definition": (
            "Net zero means reducing greenhouse-gas emissions to as close to zero as possible, with any "
            "remaining emissions balanced by removals from the atmosphere. It is a target for a company, "
            "city or country, not a single action."
        ),
        "why": [
            "The IPCC links net zero to limiting warming to 1.5 degrees Celsius.",
            "India has announced a net-zero target of 2070.",
            "Companies set net-zero targets through frameworks such as SBTi.",
            "Net-zero work creates jobs in carbon accounting, target-setting, energy transition and reporting.",
        ],
        "source_label": "Intergovernmental Panel on Climate Change (IPCC)",
        "source_url": "https://www.ipcc.ch",
        "match": match_any(r"climate", r"carbon", r"net zero"),
        "related": [("/roles/carbon-analyst", "Carbon analyst career profile"), ("/esg-carbon-sustainability-jobs", "ESG and carbon jobs")],
        "faqs": [
            ("Is net zero the same as carbon neutral?", "They are close. Carbon neutral usually balances annual emissions with offsets. Net zero implies deep cuts first, with removals only for residual emissions."),
            ("Can a company be net zero without cutting emissions?", "No. Offsetting without reduction is not net zero under credible frameworks."),
            ("What is a net-zero target year?", "The year by which a company or country aims to reach net zero, stated in its climate commitment."),
        ],
    },
    {
        "slug": "sbti",
        "term": "SBTi",
        "full": "Science Based Targets initiative",
        "h1": "What is SBTi? Science Based Targets Initiative Explained",
        "title": "What is SBTi? Science Based Targets Initiative Explained",
        "desc": "SBTi helps companies set emission-reduction targets aligned with climate science. What it is and why it matters for ESG jobs.",
        "kicker": "Target-setting framework",
        "definition": (
            "The Science Based Targets initiative is a partnership that helps companies set "
            "greenhouse-gas emission-reduction targets in line with the goals of the Paris Agreement. "
            "Targets are reviewed and validated against a published methodology."
        ),
        "why": [
            "Targets are validated, not self-declared, which is why companies hire people to prepare and defend them.",
            "The initiative covers corporate targets, financial institutions and, separately, a net-zero standard.",
            "SBTi appears regularly in Indian ESG job descriptions as a required framework.",
            "Work includes baseline inventories, target modelling, submission and progress reporting.",
        ],
        "source_label": "Science Based Targets initiative",
        "source_url": "https://sciencebasedtargets.org",
        "match": match_any(r"\besg\b", r"carbon", r"sustainability"),
        "related": [("/roles/esg-analyst", "ESG analyst career profile"), ("/esg-carbon-sustainability-jobs", "ESG and carbon jobs")],
        "faqs": [
            ("Is SBTi mandatory?", "No. It is voluntary, but many large companies and investors treat validated targets as a credibility signal."),
            ("Does SBTi cover Scope 3?", "Yes, where Scope 3 is a significant share of total emissions, a Scope 3 target is required for validation."),
            ("How long does validation take?", "It varies by company size and target type. The initiative publishes current timelines on its website."),
        ],
    },
    {
        "slug": "dmrv",
        "term": "dMRV",
        "full": "Digital Monitoring, Reporting and Verification",
        "h1": "What is dMRV? Digital Monitoring, Reporting and Verification Explained",
        "title": "What is dMRV? Digital Monitoring, Reporting & Verification Explained",
        "desc": "dMRV uses digital tools to monitor, report and verify project outcomes such as carbon and forest benefits. Explained.",
        "kicker": "Digital MRV",
        "definition": (
            "dMRV stands for digital Monitoring, Reporting and Verification. It means using digital "
            "tools such as remote sensing, sensors and mobile applications to track the outcomes of a "
            "project, for example carbon sequestration or forest cover, in a way a third party can check."
        ),
        "why": [
            "It reduces the cost and delay of manual field verification.",
            "It makes project data auditable because inputs, assumptions and calculations stay visible.",
            "It is increasingly required by carbon standards and funders for forest and nature projects.",
            "Urban Forest Park's Nagar Van dashboard and green calculator are examples of dMRV-style tools.",
        ],
        "source_label": "UNFCCC and voluntary carbon standard bodies",
        "source_url": "https://unfccc.int",
        "match": match_any(r"gis", r"remote sensing", r"forest", r"carbon"),
        "related": [("/dmrv", "Nagar Van dMRV tools"), ("/green-calculator", "Urban Forest Green Calculator"), ("/spatial-data", "Spatial data explorer")],
        "faqs": [
            ("Is dMRV the same as MRV?", "MRV is the broader process. dMRV specifically uses digital and remote-sensing methods to do it."),
            ("Does dMRV replace field visits?", "No. It complements them. Field measurement remains the reference for many indicators."),
            ("Who uses dMRV?", "Project developers, verifiers, funders and regulators, plus researchers and students studying urban forests."),
        ],
    },
    {
        "slug": "nagar-van",
        "term": "Nagar Van",
        "full": "Nagar Van Yojana (urban forest)",
        "h1": "What is a Nagar Van? Urban Forests in India Explained",
        "title": "What is a Nagar Van? Urban Forests in India Explained",
        "desc": "Nagar Van Yojana is India's urban forest scheme. What it is, who runs it, and how to find a site near you.",
        "kicker": "Urban forest scheme",
        "definition": (
            "Nagar Van, meaning 'city forest', is a scheme of the Ministry of Environment, Forest and "
            "Climate Change to create and manage urban forests in cities. The aim is to improve air "
            "quality, biodiversity, cooling and public access to green space."
        ),
        "why": [
            "The scheme sets a target of around 400 Nagar Vans across Indian cities.",
            "Sites are developed on forest or other available land within or near cities.",
            "Urban Forest Park tracks these sites through its dMRV dashboard, finder and green calculator.",
            "The work creates roles in urban forestry, GIS, carbon monitoring and community engagement.",
        ],
        "source_label": "Ministry of Environment, Forest and Climate Change (MoEFCC)",
        "source_url": "https://moef.gov.in",
        "match": match_any(r"forest", r"urban", r"nagar"),
        "related": [("/nagar-van-finder", "Nagar Van Finder"), ("/dashboard", "Nagar Van dMRV Dashboard"), ("/green-calculator", "Urban Forest Green Calculator")],
        "faqs": [
            ("Who funds a Nagar Van?", "Funding comes through MoEFCC and the National Compensatory Afforestation Fund, with state forest departments implementing."),
            ("Can a citizen propose a site?", "Urban Forest Park accepts site suggestions through its public survey, which are reviewed before appearing."),
            ("Is a Nagar Van the same as a city park?", "Not exactly. It is a forested ecosystem with native species, not a landscaped garden."),
        ],
    },
    {
        "slug": "campa",
        "term": "CAMPA",
        "full": "Compensatory Afforestation Fund Management and Planning Authority",
        "h1": "What is CAMPA? Compensatory Afforestation Fund Explained",
        "title": "What is CAMPA? Compensatory Afforestation Fund Explained",
        "desc": "CAMPA manages funds for compensatory afforestation when forest land is diverted for non-forest use. Explained.",
        "kicker": "Forest fund",
        "definition": (
            "CAMPA stands for the Compensatory Afforestation Fund Management and Planning Authority. "
            "It manages money collected when forest land is diverted for non-forest purposes such as "
            "roads or mining, and that money funds compensatory afforestation and related works."
        ),
        "why": [
            "The Compensatory Afforestation Fund Act was passed in 2016.",
            "Funds are collected from user agencies and disbursed to states for afforestation and wildlife management.",
            "CAMPA-funded projects create forestry, GIS, monitoring and project staff roles.",
            "It is one of the larger funding streams behind Indian afforestation work.",
        ],
        "source_label": "Ministry of Environment, Forest and Climate Change (MoEFCC)",
        "source_url": "https://moef.gov.in",
        "match": match_any(r"forest", r"campa", r"afforestation"),
        "related": [("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs"), ("/roles/forest-guard", "Forest guard career profile")],
        "faqs": [
            ("Who pays into CAMPA?", "User agencies that divert forest land pay the compensatory levy."),
            ("Is CAMPA money only for planting trees?", "No. It also funds wildlife management, forest protection and capacity building."),
            ("Are CAMPA projects government jobs?", "Most are contract or project posts funded by CAMPA money through state forest departments."),
        ],
    },
    {
        "slug": "jrf",
        "term": "JRF",
        "full": "Junior Research Fellow",
        "h1": "What is a JRF? Junior Research Fellow Explained",
        "title": "What is a JRF? Junior Research Fellow Explained",
        "desc": "JRF explained: what a Junior Research Fellow does, eligibility through NET or GATE, stipend basis and progression to SRF.",
        "kicker": "Research fellowship",
        "definition": (
            "A Junior Research Fellow is a funded research position attached to a project or a PhD "
            "programme. The fellow does research, fieldwork and analysis under a principal investigator "
            "and receives a monthly fellowship rather than a salary."
        ),
        "why": [
            "Eligibility usually requires a master's degree plus a national eligibility test such as CSIR-UGC NET, UGC-NET or GATE.",
            "Fellowship amounts follow the funding agency's norms and are printed in each advertisement.",
            "After PhD registration the fellow is usually upgraded to Senior Research Fellow.",
            "JRF experience counts as research experience for later academic and scientist posts.",
        ],
        "source_label": "CSIR, UGC and DST funding norms",
        "source_url": "https://csir.res.in",
        "match": match_any(r"\bjrf\b", r"junior research fellow"),
        "related": [("/roles/junior-research-fellow", "JRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide"), ("/exams/ugc-net-environmental-science", "UGC-NET guide")],
        "faqs": [
            ("Is JRF a job?", "It is a fellowship, not employment. It carries a stipend and usually requires PhD registration to continue."),
            ("Can I take a JRF without a PhD seat?", "Yes for the initial period. Most institutes require registration before upgrading to SRF."),
            ("Is the JRF stipend taxable?", "Fellowships are generally treated differently from salary. Confirm with the institute and a tax adviser."),
        ],
    },
    {
        "slug": "srf",
        "term": "SRF",
        "full": "Senior Research Fellow",
        "h1": "What is an SRF? Senior Research Fellow Explained",
        "title": "What is an SRF? Senior Research Fellow Explained",
        "desc": "SRF explained: the upgrade from JRF, eligibility, stipend and progression to research associate or scientist.",
        "kicker": "Research fellowship",
        "definition": (
            "A Senior Research Fellow is the next rung after Junior Research Fellow. The upgrade usually "
            "requires PhD registration and a minimum period as JRF, and it carries a higher fellowship."
        ),
        "why": [
            "SRF is not a separate exam; it follows from JRF performance and registration.",
            "The fellowship amount is higher than JRF and is printed in the advertisement.",
            "SRF positions are common in CSIR, ICAR and university projects.",
            "After SRF, the usual next steps are research associate, project scientist or faculty.",
        ],
        "source_label": "CSIR, UGC and DST funding norms",
        "source_url": "https://csir.res.in",
        "match": match_any(r"\bsrf\b", r"senior research fellow"),
        "related": [("/roles/junior-research-fellow", "JRF/SRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide")],
        "faqs": [
            ("How long can I hold an SRF?", "It is limited by the project duration and the funding agency's maximum fellowship period."),
            ("Is SRF permanent?", "No. It is a fellowship tied to a project or PhD, renewed periodically."),
            ("Can I move from SRF to a permanent post?", "Yes, through open recruitment for scientist or faculty positions."),
        ],
    },
    {
        "slug": "eia",
        "term": "EIA",
        "full": "Environmental Impact Assessment",
        "h1": "What is EIA? Environmental Impact Assessment Explained",
        "title": "What is EIA? Environmental Impact Assessment Explained",
        "desc": "EIA is the process of evaluating environmental effects of a proposed project before approval. India's EIA Notification 2006 explained.",
        "kicker": "Regulatory process",
        "definition": (
            "Environmental Impact Assessment is the process of identifying and evaluating the likely "
            "environmental effects of a proposed project before a decision is made to approve it. In "
            "India it is governed by the EIA Notification, 2006, under the Environment (Protection) Act."
        ),
        "why": [
            "Projects above thresholds require prior environmental clearance.",
            "The process includes screening, scoping, impact analysis, mitigation and public hearing.",
            "EIA work creates roles for environmental engineers, consultants and compliance officers.",
            "Clearance records are published, which makes them a useful source for job seekers tracking projects.",
        ],
        "source_label": "Ministry of Environment, Forest and Climate Change (MoEFCC)",
        "source_url": "https://moef.gov.in",
        "match": match_any(r"environmental engineer", r"compliance", r"eia", r"impact assessment"),
        "related": [("/roles/environmental-engineer", "Environmental engineer career profile"), ("/exams/cpcb-scientist-engineer", "CPCB recruitment guide")],
        "faqs": [
            ("Is an EIA public?", "The draft EIA report and the public hearing are published for Category A and B1 projects."),
            ("Who prepares an EIA?", "Accredited consultants prepare it; the regulator grants clearance."),
            ("Does every project need an EIA?", "No. Projects below the thresholds or on the exempt list do not."),
        ],
    },
    {
        "slug": "ehs",
        "term": "EHS",
        "full": "Environment, Health and Safety",
        "h1": "What is EHS? Environment, Health and Safety Explained",
        "title": "What is EHS? Environment, Health & Safety Explained",
        "desc": "EHS covers environmental compliance, worker safety and occupational health in industry. What the role involves.",
        "kicker": "Industry function",
        "definition": (
            "EHS stands for Environment, Health and Safety. It is the combined function in an "
            "organisation responsible for environmental compliance, worker safety and occupational health."
        ),
        "why": [
            "EHS roles sit at the intersection of pollution control, safety management and compliance.",
            "They are common in manufacturing, energy, infrastructure and chemicals.",
            "Entry usually requires an engineering degree plus knowledge of environmental law and safety standards.",
            "EHS officers often move into sustainability and ESG roles later in their careers.",
        ],
        "source_label": "Factories Act and Environment (Protection) Act, India",
        "source_url": "https://moef.gov.in",
        "match": match_any(r"\behs\b", r"\bhse\b", r"safety", r"compliance", r"environmental engineer"),
        "related": [("/roles/environmental-engineer", "Environmental engineer career profile"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
        "faqs": [
            ("Is EHS the same as ESG?", "No. EHS is operational compliance and safety. ESG is broader reporting and governance. They overlap in practice."),
            ("Do EHS roles need a safety certification?", "Some employers ask for NEBOSH or IOSH, but many hire on engineering degree and plant experience."),
            ("Is EHS work field-based?", "Largely yes. It involves site inspections, audits and training rather than desk reporting."),
        ],
    },
    {
        "slug": "circular-economy",
        "term": "Circular economy",
        "full": "Circular economy",
        "h1": "What is the Circular Economy? Explained",
        "title": "What is the Circular Economy? Explained",
        "desc": "Circular economy explained: designing out waste, keeping materials in use, and what it means for green jobs.",
        "kicker": "Economic model",
        "definition": (
            "A circular economy is an economic system aimed at eliminating waste and keeping materials "
            "in use for as long as possible through reuse, repair, refurbishment and recycling."
        ),
        "why": [
            "It contrasts with the linear take-make-dispose model.",
            "In India it appears in waste management, extended producer responsibility and recycling policy.",
            "Jobs include waste management engineers, recycling analysts and circularity consultants.",
            "Extended producer responsibility rules are pushing companies to hire for circularity.",
        ],
        "source_label": "Ellen MacArthur Foundation and MoEFCC",
        "source_url": "https://moef.gov.in",
        "match": match_any(r"circul", r"waste", r"recycl"),
        "related": [("/esg-carbon-sustainability-jobs", "ESG, carbon and sustainability jobs")],
        "faqs": [
            ("Is circular economy only about recycling?", "No. Recycling is the last resort. Designing products to last and be repaired comes first."),
            ("Is it regulated in India?", "Partly. Extended producer responsibility rules for plastic, e-waste and batteries create compliance obligations."),
            ("Does it create jobs?", "Yes, in collection, sorting, processing and product design, though many are informal today."),
        ],
    },
    {
        "slug": "greenwashing",
        "term": "Greenwashing",
        "full": "Greenwashing",
        "h1": "What is Greenwashing? How to Spot It",
        "title": "What is Greenwashing? How to Spot It",
        "desc": "Greenwashing is misleading claims about environmental benefits. How to spot it and why it matters for ESG careers.",
        "kicker": "Risk",
        "definition": (
            "Greenwashing is the practice of making misleading or unsubstantiated claims about the "
            "environmental benefits of a product, service or organisation. It ranges from vague language "
            "to selective disclosure of favourable data."
        ),
        "why": [
            "It erodes trust in genuine sustainability work and in ESG reporting.",
            "Regulators in several jurisdictions are tightening rules against it, including in India through advertising and securities regulators.",
            "ESG analysts and assurance professionals are hired partly to prevent it.",
            "Job seekers should verify claims against published data and third-party assurance.",
        ],
        "source_label": "UNEP and consumer protection regulators",
        "source_url": "https://www.unep.org",
        "match": match_any(r"\besg\b", r"sustainability", r"green"),
        "related": [("/roles/esg-analyst", "ESG analyst career profile"), ("/green-careers", "Green career pathways")],
        "faqs": [
            ("Is greenwashing illegal in India?", "Misleading advertising is actionable under consumer protection law, and SEBI regulates ESG disclosures for listed companies."),
            ("How do I check a company's green claims?", "Look for published data, defined metrics, third-party assurance and consistency across years."),
            ("Does greenwashing affect hiring?", "Yes. Companies under scrutiny hire assurance and verification staff, which increases demand for rigorous ESG analysts."),
        ],
    },
]


def build_term_page(term: Dict[str, Any]) -> None:
    live = [job for job in POOL if term["match"](job)]
    live.sort(key=lambda job: str(job.get("valid_through") or "9999"))

    related_links = "".join(
        f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in term["related"]
    )
    related_links += '<li><a href="/glossary">Full glossary</a></li>'

    body = "\n".join(
        [
            hero(
                term["kicker"],
                term["h1"],
                term["definition"],
                [
                    ("Live openings", str(len(live))),
                    ("Official source", term["source_label"].split(" (")[0][:28]),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Why it matters</h2>
        <p>This is where the term shows up in practice and in hiring.</p>
{bullet_list(term["why"])}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Official source</h2>
        <p>The definition and rules above come from the body that owns the term. This site does not paraphrase a regulation into a simpler claim than the source supports.</p>
        <p><a href="{term["source_url"]}" target="_blank" rel="noopener noreferrer">{esc(term["source_label"])} &nearr;</a></p>
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Live openings that use this term ({len(live)})</h2>
        <p>Sorted by closing date. Each links to the full dossier and the official application page.</p>
{cards_block(live[:9], "No live listing is tagged with this term today. New roles are added daily.")}
      </div>
    </section>""",
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {related_links}
        </ul>
      </div>
    </section>""",
            beh.bsp.faq_section_html(term["faqs"]),
        ]
    )
    jsonld = "\n".join(
        [
            beh.bsp.organization_jsonld(),
            beh.bsp.website_jsonld(),
            beh.breadcrumb(term["term"] + " explained", f"{SITE}/glossary/{term['slug']}"),
            beh.faq_jsonld(term["faqs"]),
        ]
    )
    write_sub(
        GLOSSARY_DIR,
        term["slug"],
        shell(
            title=term["title"],
            description=term["desc"],
            canonical=f"{SITE}/glossary/{term['slug']}",
            body=body,
            jsonld=jsonld,
        ),
    )


def build_glossary_index() -> None:
    term_cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/glossary/{t['slug']}">{esc(t['term'])}</a> <span class="muted">({esc(t['full'])})</span></h3>
          <p class="hub-card-sum">{esc(t['definition'])}</p>
          <p class="hub-card-foot"><span>{len([j for j in POOL if t['match'](j)])} live listing(s)</span>
            <a href="/glossary/{t['slug']}">Read &rarr;</a></p>
        </article>"""
        for t in TERMS
    )
    body = "\n".join(
        [
            hero(
                "Glossary",
                "Green Jobs & Climate Glossary",
                "Plain-language definitions of the terms that recur in Indian green-job notices, each with an official source and the live openings that use it.",
                [
                    ("Terms", str(len(TERMS))),
                    ("Live openings", str(sum(len([j for j in POOL if t["match"](j)]) for t in TERMS))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Terms</h2>
        <p>Definitions are kept short and point at the official source. Where a term has a legal definition, that definition wins.</p>
        <div class="hub-list">
{term_cards}
        </div>
      </div>
    </section>""",
            section(
                "How to use this glossary",
                "Read the definition, then check the live openings.",
                """        <ul class="check-list">
          <li><strong>Match the term to the notice.</strong> If an advertisement uses BRSR, GHG Protocol or EIA, the relevant guide tells you what the employer is actually asking for.</li>
          <li><strong>Check the source.</strong> Every page links to the body that owns the term. Regulations change; the source is authoritative.</li>
          <li><strong>Follow the jobs.</strong> Each term page lists the live openings tagged with it.</li>
        </ul>""",
            ),
            beh.bsp.faq_section_html(
                [
                    ("Is this glossary neutral?", "Yes. It defines terms and links to sources. It does not rank employers or recommend products."),
                    ("How often is it updated?", "It is rebuilt with the site, and live-opening counts refresh from the registry on every build."),
                    ("Can I suggest a term?", "Yes, through the report page or by email to the registry."),
                ]
            ),
        ]
    )
    write_sub(
        GLOSSARY_DIR,
        "index",
        shell(
            title="Green Jobs & Climate Glossary: ESG, BRSR, GHG, dMRV & More",
            description="Plain-language definitions of ESG, BRSR, GHG Protocol, carbon credit, net zero, SBTi, dMRV, Nagar Van, CAMPA, JRF, SRF, EIA, EHS and circular economy, with official sources.",
            canonical=f"{SITE}/glossary",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("Green Jobs & Climate Glossary", f"{SITE}/glossary"),
                ]
            ),
        ),
    )


# ---------------------------------------------------------------------------
# New this week digest
# ---------------------------------------------------------------------------
def build_weekly_digest() -> None:
    cutoff = TODAY - timedelta(days=7)
    monthly_cutoff = TODAY - timedelta(days=30)

    weekly: List[Dict[str, Any]] = []
    monthly: List[Dict[str, Any]] = []
    for job in POOL:
        added = beh.parse_date(job.get("date_added"))
        if not added:
            continue
        if added >= cutoff:
            weekly.append(job)
        elif added >= monthly_cutoff:
            monthly.append(job)

    weekly.sort(key=lambda j: str(j.get("date_added") or ""), reverse=True)
    monthly.sort(key=lambda j: str(j.get("date_added") or ""), reverse=True)

    by_category: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
    for job in weekly:
        by_category[plain(job.get("category")) or "Other"].append(job)

    category_blocks = "\n".join(
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>{esc(category)} ({len(jobs)})</h2>
        <div class="hub-list">
{cards(jobs)}
        </div>
      </div>
    </section>"""
        for category, jobs in sorted(by_category.items(), key=lambda x: -len(x[1]))
    )
    if not category_blocks:
        category_blocks = """    <section class="hub-main">
      <div class="hub-main-inner">
        <p class="hub-empty">No new listing was added in the last seven days. The registry is refreshed daily; check back soon or browse the full registry.</p>
      </div>
    </section>"""

    monthly_html = ""
    if monthly:
        monthly_html = f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Added in the last 30 days ({len(monthly)})</h2>
        <p>Older additions, still open. Sorted by date added.</p>
        <div class="hub-list">
{cards(monthly[:18])}
        </div>
      </div>
    </section>"""

    body = "\n".join(
        [
            hero(
                "Fresh listings",
                "New Green Jobs This Week",
                "Listings added to the registry in the last seven days, grouped by category. Every link goes to the official application page.",
                [
                    ("New this week", str(len(weekly))),
                    ("New this month", str(len(monthly))),
                    ("Updated", TODAY.strftime("%d %b %Y")),
                ],
            ),
            category_blocks,
            monthly_html,
            section(
                "How to use this page",
                "It is a feed, not a filter.",
                """        <ul class="check-list">
          <li><strong>Check daily.</strong> New roles are added as they are verified, so the list changes through the week.</li>
          <li><strong>Apply through the official page.</strong> Each card links to the employer's or portal's application page.</li>
          <li><strong>Use alerts for your category.</strong> The weekly digest lists everything; alerts narrow it to your role and city.</li>
        </ul>""",
            ),
            beh.bsp.faq_section_html(
                [
                    ("How often is this page updated?", "It is regenerated on every build from the registry's date_added field."),
                    ("Why is a listing missing?", "It may have been added earlier, or it may still be in verification. Only verified listings appear."),
                    ("Can I get this as a feed?", "Yes. The registry publishes feed.xml and jrf-feed.xml for RSS readers."),
                ]
            ),
        ]
    )
    write_sub(
        PUBLIC,
        "green-jobs-this-week",
        shell(
            title="New Green Jobs This Week in India & Worldwide",
            description=f"{len(weekly)} new verified green jobs added in the last seven days, grouped by category, with official application links.",
            canonical=f"{SITE}/green-jobs-this-week",
            body=body,
            jsonld="\n".join(
                [
                    beh.bsp.organization_jsonld(),
                    beh.bsp.website_jsonld(),
                    beh.breadcrumb("New Green Jobs This Week", f"{SITE}/green-jobs-this-week"),
                ]
            ),
        ),
    )


def main() -> None:
    for term in TERMS:
        build_term_page(term)
    build_glossary_index()
    build_weekly_digest()

    for term in TERMS:
        add_sitemap(f"/glossary/{term['slug']}", "monthly", "0.7")
    add_sitemap("/glossary", "weekly", "0.8")
    add_sitemap("/green-jobs-this-week", "daily", "0.9")

    print(f"Wrote {len(TERMS)} glossary terms + index and the weekly digest")


if __name__ == "__main__":
    main()
