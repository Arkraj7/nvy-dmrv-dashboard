#!/usr/bin/env python3
"""Build career transition guides, interview prep guides and resume templates.

All content is written from verified industry knowledge and the registry's
own data. No pay, deadline or eligibility figures are invented.
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


def build_page(slug: str, title: str, desc: str, kicker: str, h1: str, sub: str,
               sections: List[tuple], faqs: List[tuple], related: List[tuple]) -> None:
    sec_html = "\n".join(
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>{esc(s[0])}</h2>
        {s[1]}
      </div>
    </section>"""
        for s in sections
    )
    body = "\n".join([
        hero(kicker, h1, sub, [("Updated", TODAY.strftime("%d %b %Y"))]),
        sec_html,
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>Related pages</h2>
        <ul class="check-list">
          {''.join(f'<li><a href="{href}">{esc(label)}</a></li>' for href, label in related)}
        </ul>
      </div>
    </section>""",
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


# ---------------------------------------------------------------------------
# Career transition guides
# ---------------------------------------------------------------------------
TRANSITIONS = [
    {
        "slug": "it-to-sustainability-career",
        "title": "How to Transition from IT to Sustainability",
        "desc": "How software and IT professionals can move into sustainability, ESG and climate tech roles in India.",
        "kicker": "Career transition",
        "h1": "How to Transition from IT to Sustainability",
        "sub": "A practical guide for software and IT professionals who want to move into sustainability, ESG and climate tech roles.",
        "sections": [
            ("Why IT skills are in demand", "<p>Sustainability teams need data engineers, dashboard developers, automation specialists and ESG data platforms. IT professionals with domain knowledge are scarce and valued.</p>"),
            ("Skills that transfer", "<ul class=\"check-list\"><li><strong>Data engineering:</strong> ESG data pipelines, carbon accounting databases, supply chain traceability systems.</li><li><strong>Dashboard and BI:</strong> Power BI, Tableau, Grafana for sustainability KPIs.</li><li><strong>Automation:</strong> RPA for data collection, ESG reporting workflows.</li><li><strong>Cloud and IoT:</strong> sensor networks for emissions monitoring, remote sensing data processing.</li><li><strong>Software development:</strong> ESG reporting platforms, carbon calculators, sustainability apps.</li></ul>"),
            ("How to make the switch", "<ol class=\"check-list\"><li><strong>Learn the domain.</strong> Study BRSR, GRI, GHG Protocol and carbon accounting basics. Free resources on SEBI and WRI websites.</li><li><strong>Build a project.</strong> Create a carbon footprint dashboard, an ESG data pipeline or a sustainability report parser. Show it in interviews.</li><li><strong>Target the right roles.</strong> Look for 'ESG data analyst', 'sustainability technology', 'carbon accounting developer', 'climate tech' roles.</li><li><strong>Network.</strong> Attend sustainability conferences, join ESG communities on LinkedIn, connect with climate tech startups.</li><li><strong>Consider a certification.</strong> GRI, SASB or BRSR training courses add credibility but are not mandatory.</li></ol>"),
            ("Where to find roles", "<p>Browse <a href='/esg-carbon-sustainability-jobs'>ESG and sustainability jobs</a>, <a href='/roles/esg-analyst'>ESG analyst profile</a> and <a href='/roles/carbon-analyst'>carbon analyst profile</a>. IT professionals also fit well in <a href='/roles/gis-analyst'>GIS and remote sensing</a> roles.</p>"),
        ],
        "faqs": [
            ("Do I need a sustainability degree?", "No. IT professionals are hired for their technical skills. Domain knowledge can be learned on the job."),
            ("Will my salary drop?", "Entry-level ESG roles may pay less than senior IT roles. But the field is growing fast and experienced professionals are in high demand."),
            ("How long does the transition take?", "3-6 months of focused learning and project building is usually enough to start applying."),
        ],
        "related": [("/roles/esg-analyst", "ESG analyst profile"), ("/glossary/esg", "ESG glossary entry"), ("/glossary/brsr", "BRSR glossary entry"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
    {
        "slug": "engineering-to-esg-career",
        "title": "How to Transition from Engineering to ESG",
        "desc": "How engineers can move into ESG, sustainability and climate roles in India. Skills, pathways and entry points.",
        "kicker": "Career transition",
        "h1": "How to Transition from Engineering to ESG",
        "sub": "A practical guide for engineers who want to move into ESG, sustainability and climate roles in India.",
        "sections": [
            ("Why engineers are in demand", "<p>ESG and sustainability teams need people who understand industrial processes, emissions measurement, energy systems and environmental compliance. Engineers fit naturally into carbon accounting, EHS, environmental engineering and sustainability consulting roles.</p>"),
            ("Skills that transfer", "<ul class=\"check-list\"><li><strong>Environmental engineering:</strong> water/wastewater treatment, air pollution control, waste management.</li><li><strong>Mechanical/electrical:</strong> energy systems, HVAC, renewable energy, energy efficiency.</li><li><strong>Chemical engineering:</strong> process engineering, emissions control, chemical safety.</li><li><strong>Civil engineering:</strong> environmental impact assessment, construction sustainability, green building.</li><li><strong>Data skills:</strong> process data analysis, monitoring systems, automation.</li></ul>"),
            ("How to make the switch", "<ol class=\"check-list\"><li><strong>Identify your niche.</strong> Environmental engineering, EHS, energy, or carbon accounting. Match your degree to the closest ESG sub-field.</li><li><strong>Learn ESG frameworks.</strong> BRSR, GRI, GHG Protocol, TCFD. Free resources on SEBI and WRI websites.</li><li><strong>Get relevant experience.</strong> EHS roles, environmental consulting, or sustainability projects at your current company.</li><li><strong>Target the right roles.</strong> <a href='/roles/environmental-engineer'>Environmental engineer</a>, <a href='/roles/esg-analyst'>ESG analyst</a>, <a href='/roles/carbon-analyst'>carbon analyst</a>, <a href='/roles/sustainability-consultant'>sustainability consultant</a>.</li><li><strong>Consider certifications.</strong> NEBOSH, ISO 14001 lead auditor, GRI. These add credibility for compliance and consulting roles.</li></ol>"),
            ("Where to find roles", "<p>Browse <a href='/esg-carbon-sustainability-jobs'>ESG and sustainability jobs</a>, <a href='/roles/environmental-engineer'>environmental engineer profile</a> and <a href='/roles/carbon-analyst'>carbon analyst profile</a>.</p>"),
        ],
        "faqs": [
            ("Do I need a master's in environment?", "Not necessarily. A bachelor's in engineering plus relevant experience is sufficient for many EHS and environmental engineering roles."),
            ("Is ESG better paid than core engineering?", "It depends. Entry-level ESG roles may pay similar or slightly less. Senior ESG and consulting roles can pay significantly more."),
            ("How long does the transition take?", "If you are already in EHS or environmental engineering, the transition can be immediate. Otherwise, 3-6 months of focused learning."),
        ],
        "related": [("/roles/environmental-engineer", "Environmental engineer profile"), ("/roles/esg-analyst", "ESG analyst profile"), ("/roles/carbon-analyst", "Carbon analyst profile"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
    {
        "slug": "academia-to-industry-green-career",
        "title": "From Academia to Industry: Green Career Transition Guide",
        "desc": "How researchers and academics can transition to industry roles in sustainability, ESG and climate.",
        "kicker": "Career transition",
        "h1": "From Academia to Industry: Green Career Transition",
        "sub": "A practical guide for researchers and academics who want to move into industry roles in sustainability, ESG and climate.",
        "sections": [
            ("Why industry wants researchers", "<p>Industry sustainability teams need people who can analyse data, write reports, design studies and communicate findings. PhDs and postdocs have these skills in abundance.</p>"),
            ("Skills that transfer", "<ul class=\"check-list\"><li><strong>Research and analysis:</strong> literature review, data collection, statistical analysis, evidence synthesis.</li><li><strong>Technical writing:</strong> reports, policy briefs, technical documentation.</li><li><strong>Domain expertise:</strong> climate science, ecology, environmental engineering.</li><li><strong>Project management:</strong> grant management, research coordination, team supervision.</li><li><strong>Communication:</strong> presenting findings to non-expert audiences.</li></ul>"),
            ("How to make the switch", "<ol class=\"check-list\"><li><strong>Translate academic CV to industry resume.</strong> Replace publications with impact statements. Highlight transferable skills, not just research topics.</li><li><strong>Target the right roles.</strong> Research associate, sustainability analyst, ESG data analyst, climate policy analyst, carbon analyst.</li><li><strong>Build industry skills.</strong> Learn BRSR, GRI, Excel/Power BI, stakeholder communication. These are not taught in academia.</li><li><strong>Network outside academia.</strong> Attend industry conferences, join ESG communities, connect with alumni in industry.</li><li><strong>Consider a bridge role.</strong> Research associate or project associate at a think tank or NGO is a common stepping stone.</li></ol>"),
            ("Where to find roles", "<p>Browse <a href='/jrf-srf-project-associate-jobs'>JRF and project associate jobs</a>, <a href='/roles/climate-policy-analyst'>climate policy analyst profile</a> and <a href='/roles/carbon-analyst'>carbon analyst profile</a>.</p>"),
        ],
        "faqs": [
            ("Will industry value my PhD?", "Yes, but differently. Industry values research skills, not the topic. Frame your PhD as evidence of analytical ability."),
            ("Is the pay better in industry?", "Usually yes at mid and senior levels. Entry-level industry roles may pay similar to postdoc stipends."),
            ("How long does the transition take?", "2-4 months of active job searching, plus time to translate your CV and build industry skills."),
        ],
        "related": [("/roles/climate-policy-analyst", "Climate policy analyst profile"), ("/roles/carbon-analyst", "Carbon analyst profile"), ("/roles/junior-research-fellow", "JRF/SRF profile"), ("/jrf-srf-project-associate-jobs", "JRF and project associate jobs")],
    },
    {
        "slug": "nonprofit-to-corporate-green-career",
        "title": "From Non-Profit to Corporate: Green Career Transition",
        "desc": "How NGO and non-profit professionals can transition to corporate sustainability and ESG roles.",
        "kicker": "Career transition",
        "h1": "From Non-Profit to Corporate: Green Career Transition",
        "sub": "A practical guide for NGO and non-profit professionals who want to move into corporate sustainability and ESG roles.",
        "sections": [
            ("Why corporates want NGO experience", "<p>Corporate sustainability teams need people who understand community engagement, field implementation, stakeholder management and impact measurement. NGO professionals have these skills.</p>"),
            ("Skills that transfer", "<ul class=\"check-list\"><li><strong>Stakeholder engagement:</strong> community mobilisation, government liaison, partnership management.</li><li><strong>Project management:</strong> programme design, budget management, M&E, reporting to donors.</li><li><strong>Field experience:</strong> community-based conservation, livelihood programmes, awareness campaigns.</li><li><strong>Impact measurement:</strong> M&E frameworks, indicator design, data collection.</li><li><strong>Communication:</strong> report writing, presentation, advocacy.</li></ul>"),
            ("How to make the switch", "<ol class=\"check-list\"><li><strong>Learn corporate frameworks.</strong> BRSR, GRI, ESG reporting, carbon accounting. These are not taught in NGOs.</li><li><strong>Translate NGO experience.</strong> Replace 'community mobilisation' with 'stakeholder engagement'. Replace 'programme management' with 'project delivery'. Replace 'impact assessment' with 'M&E and reporting'.</li><li><strong>Target the right roles.</strong> Sustainability manager, ESG analyst, CSR manager, sustainability consultant, programme manager.</li><li><strong>Network in corporate sustainability.</strong> Attend industry events, connect with corporate sustainability professionals on LinkedIn.</li><li><strong>Consider a bridge role.</strong> CSR manager or sustainability associate at a mid-size company is a common stepping stone.</li></ol>"),
            ("Where to find roles", "<p>Browse <a href='/esg-carbon-sustainability-jobs'>ESG and sustainability jobs</a>, <a href='/roles/sustainability-manager'>sustainability manager profile</a> and <a href='/roles/csr-manager'>CSR manager profile</a>.</p>"),
        ],
        "faqs": [
            ("Will my NGO experience be valued?", "Yes, especially for stakeholder engagement, community programmes and impact measurement roles."),
            ("Is the pay better in corporate?", "Usually yes, especially at mid and senior levels. Entry-level corporate roles may pay similar to NGO roles."),
            ("How long does the transition take?", "2-4 months of active job searching with a translated CV and basic ESG framework knowledge."),
        ],
        "related": [("/roles/sustainability-manager", "Sustainability manager profile"), ("/roles/csr-manager", "CSR manager profile"), ("/roles/esg-analyst", "ESG analyst profile"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
]

# ---------------------------------------------------------------------------
# Interview prep guides
# ---------------------------------------------------------------------------
INTERVIEWS = [
    {
        "slug": "esg-interview-questions",
        "title": "ESG Interview Questions and How to Answer Them",
        "desc": "Common ESG interview questions in India: technical, behavioural and case study questions with answer frameworks.",
        "kicker": "Interview prep",
        "h1": "ESG Interview Questions and How to Answer Them",
        "sub": "A preparation guide for ESG and sustainability job interviews in India, covering technical, behavioural and case study questions.",
        "sections": [
            ("Technical questions", "<ul class=\"check-list\"><li><strong>What is BRSR and who must file it?</strong> SEBI's disclosure framework for the top 1000 listed companies. Covers environmental, social and governance indicators.</li><li><strong>Explain Scope 1, 2 and 3 emissions.</strong> Scope 1: direct. Scope 2: purchased energy. Scope 3: value chain. Most challenging is Scope 3.</li><li><strong>What is the GHG Protocol?</strong> The most widely used standard for measuring corporate emissions, developed by WRI and WBCSD.</li><li><strong>What is SBTi?</strong> Science Based Targets initiative — validates emission reduction targets against climate science.</li><li><strong>How would you calculate a company's carbon footprint?</strong> Identify emission sources, collect data, apply emission factors, sum by scope, document methodology.</li><li><strong>What is ESG vs CSR?</strong> CSR is a spending obligation under the Companies Act. ESG is a performance and disclosure framework.</li></ul>"),
            ("Behavioural questions", "<ul class=\"check-list\"><li><strong>Why do you want to work in ESG?</strong> Have a specific, genuine reason tied to your background.</li><li><strong>Tell me about a time you worked with data.</strong> ESG roles are data-heavy. Show analytical skills.</li><li><strong>How do you handle conflicting priorities?</strong> ESG teams balance multiple stakeholders. Show prioritisation skills.</li><li><strong>What is your understanding of BRSR?</strong> Know the structure, essential vs leadership indicators, and recent changes.</li></ul>"),
            ("Case study questions", "<ul class=\"check-list\"><li><strong>How would you reduce a company's Scope 3 emissions?</strong> Start with supplier engagement, data collection, target-setting, then action plans.</li><li><strong>A company has no ESG data. Where do you start?</strong> Gap assessment, materiality analysis, data owner mapping, then collection.</li><li><strong>How would you report ESG to the board?</strong> Focus on financial materiality, risks, opportunities and progress vs targets.</li></ul>"),
            ("How to prepare", "<ol class=\"check-list\"><li><strong>Study BRSR format.</strong> Download from SEBI website. Know the essential and leadership indicators.</li><li><strong>Learn GHG Protocol.</strong> Understand scopes, boundaries and emission factors.</li><li><strong>Build a portfolio.</strong> Create a mock BRSR section or carbon inventory. Show it in the interview.</li><li><strong>Research the company.</strong> Check their BRSR report, sustainability targets and ESG rating.</li><li><strong>Practice case studies.</strong> ESG interviews often include a data interpretation or strategy exercise.</li></ol>"),
        ],
        "faqs": [
            ("How technical are ESG interviews?", "It depends on the role. Analyst roles test data and framework knowledge. Manager roles test strategy and stakeholder skills."),
            ("Do I need certifications?", "Certifications help but are not required for most roles. Framework knowledge (BRSR, GRI, GHG Protocol) matters more."),
            ("What salary should I expect?", "The registry shows that most ESG listings do not publish pay. Ask about CTC breakup during the interview."),
        ],
        "related": [("/roles/esg-analyst", "ESG analyst profile"), ("/glossary/esg", "ESG glossary entry"), ("/glossary/brsr", "BRSR glossary entry"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
    {
        "slug": "gis-interview-questions",
        "title": "GIS Interview Questions and How to Answer Them",
        "desc": "Common GIS and remote sensing interview questions in India: technical, software and case study questions with answer frameworks.",
        "kicker": "Interview prep",
        "h1": "GIS Interview Questions and How to Answer Them",
        "sub": "A preparation guide for GIS and remote sensing job interviews in India.",
        "sections": [
            ("Technical questions", "<ul class=\"check-list\"><li><strong>What is the difference between vector and raster data?</strong> Vector: points, lines, polygons. Raster: grid of pixels. Each has different use cases.</li><li><strong>What is a coordinate system vs projection?</strong> Coordinate system defines location. Projection is how the 3D earth is flattened to 2D.</li><li><strong>What is NDVI?</strong> Normalized Difference Vegetation Index — measures vegetation health from satellite imagery.</li><li><strong>What is Google Earth Engine?</strong> A cloud platform for planetary-scale geospatial analysis. Used for land cover, deforestation monitoring, etc.</li><li><strong>What is the difference between supervised and unsupervised classification?</strong> Supervised uses training samples. Unsupervised groups pixels by similarity.</li></ul>"),
            ("Software questions", "<ul class=\"check-list\"><li><strong>QGIS vs ArcGIS?</strong> QGIS is free and open-source. ArcGIS is proprietary but industry standard. Know both.</li><li><strong>What Python libraries do you use for GIS?</strong> GeoPandas, Rasterio, Shapely, Folium, PyQGIS.</li><li><strong>How do you handle large raster datasets?</strong> Tiling, pyramids, cloud-optimized GeoTIFFs, chunked processing.</li><li><strong>What is PostGIS?</strong> Spatial database extension for PostgreSQL. Used for spatial queries and storage.</li></ul>"),
            ("Case study questions", "<ul class=\"check-list\"><li><strong>How would you map deforestation in a region?</strong> Satellite imagery (Landsat/Sentinel), NDVI change detection, classification, accuracy assessment.</li><li><strong>How would you create a suitability map?</strong> Multi-criteria analysis: identify factors, assign weights, overlay layers, reclassify.</li><li><strong>How would you validate your results?</strong> Ground truthing, accuracy assessment (confusion matrix), cross-validation.</li></ul>"),
            ("How to prepare", "<ol class=\"check-list\"><li><strong>Practice with real data.</strong> Download free satellite imagery and build a small project.</li><li><strong>Learn QGIS thoroughly.</strong> It is free and widely used in Indian institutes.</li><li><strong>Learn Google Earth Engine.</strong> Free, powerful, and increasingly listed in job postings.</li><li><strong>Build a portfolio.</strong> 2-3 maps with documented methodology. Show them in interviews.</li><li><strong>Know your projections.</strong> UTM, WGS84, and India-specific projections (Everest, WGS84).</li></ol>"),
        ],
        "faqs": [
            ("How technical are GIS interviews?", "Very technical. Expect live software tests, data manipulation exercises and conceptual questions."),
            ("Do I need a GIS degree?", "No. Science and engineering graduates with demonstrated GIS skills are hired regularly."),
            ("What salary should I expect?", "The registry shows advertised pay for some GIS roles. See the <a href='/roles/gis-analyst'>GIS analyst profile</a>."),
        ],
        "related": [("/roles/gis-analyst", "GIS analyst profile"), ("/glossary/dmrv", "dMRV glossary entry"), ("/gis-remote-sensing-climate-jobs", "GIS and remote sensing jobs"), ("/spatial-data", "Spatial data explorer")],
    },
    {
        "slug": "jrf-interview-prep",
        "title": "JRF Interview Preparation Guide",
        "desc": "How to prepare for a Junior Research Fellow (JRF) interview: what to expect, common questions and tips.",
        "kicker": "Interview prep",
        "h1": "JRF Interview Preparation Guide",
        "sub": "A preparation guide for Junior Research Fellow interviews in Indian research institutes.",
        "sections": [
            ("What to expect", "<p>JRF interviews are typically 15-30 minutes with a panel of 3-5 faculty members. They focus on your dissertation, subject knowledge and research aptitude. Some institutes also conduct a written screening test.</p>"),
            ("Common questions", "<ul class=\"check-list\"><li><strong>Tell us about your dissertation.</strong> Be prepared to explain your research question, methodology, findings and limitations in 3-5 minutes.</li><li><strong>What are your research interests?</strong> Align with the project's scope. Show genuine interest, not just need for a job.</li><li><strong>Explain a concept from your subject.</strong> Panel members test depth, not breadth. Know your subject well.</li><li><strong>What lab techniques are you familiar with?</strong> Be honest. List what you have actually done, not what you have read about.</li><li><strong>Why do you want this JRF?</strong> Connect your interests to the project. Show that you understand what the project does.</li><li><strong>What is your PhD plan?</strong> If you have one, share it. If not, say you are exploring and ask about the institute's PhD programme.</li></ul>"),
            ("How to prepare", "<ol class=\"check-list\"><li><strong>Revise your dissertation.</strong> Know every section, method and finding. Panel members will ask about limitations.</li><li><strong>Revise core subject concepts.</strong> Focus on fundamentals, not advanced topics. Depth over breadth.</li><li><strong>Read 2-3 recent papers.</strong> From the project's field. Show that you follow the literature.</li><li><strong>Prepare a 3-minute summary.</strong> Of your dissertation and research interests. Practice until it is natural.</li><li><strong>Know the institute.</strong> Read about the PI's research, the institute's work and the project's goals.</li><li><strong>Prepare questions to ask.</strong> About the project, PhD opportunities and the institute. Shows genuine interest.</li></ol>"),
            ("Documents to carry", "<ul class=\"check-list\"><li>Degree certificates and mark sheets (original + copies)</li><li>NET/GATE scorecard</li><li>CV (2-3 copies)</li><li>Dissertation summary (1 page)</li><li>Category certificate (if applicable)</li><li>PhD registration proof (for SRF positions)</li></ul>"),
        ],
        "faqs": [
            ("Is the JRF interview very technical?", "Yes. Panel members test subject depth and research aptitude. General knowledge is not tested."),
            ("How should I dress?", "Formal but comfortable. Research institutes are less formal than corporate offices."),
            ("Can I ask for time to think?", "Yes. It is better to pause and think than to give a wrong answer quickly."),
        ],
        "related": [("/roles/junior-research-fellow", "JRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide"), ("/exams/ugc-net-environmental-science", "UGC-NET guide"), ("/glossary/jrf", "JRF glossary entry")],
    },
    {
        "slug": "forest-guard-exam-prep",
        "title": "Forest Guard Exam Preparation Guide",
        "desc": "How to prepare for the forest guard recruitment exam: written test, physical standards, syllabus and documents.",
        "kicker": "Exam prep",
        "h1": "Forest Guard Exam Preparation Guide",
        "sub": "A comprehensive preparation guide for state forest guard recruitment exams.",
        "sections": [
            ("Written exam preparation", "<ul class=\"check-list\"><li><strong>General awareness:</strong> state geography, forests, wildlife, national parks, environmental schemes. This is the highest-weightage section.</li><li><strong>Arithmetic:</strong> basic operations, percentages, ratios, simple interest. School-level difficulty.</li><li><strong>Reasoning:</strong> analogies, series, coding-decoding, blood relations. Practice from previous papers.</li><li><strong>Language:</strong> state language paper. Focus on grammar, comprehension and vocabulary.</li><li><strong>Forestry basics:</strong> forest types, tree species, wildlife, conservation. State-specific topics.</li></ul>"),
            ("Physical test preparation", "<ul class=\"check-list\"><li><strong>Running:</strong> most states require 1600m-25km in a specified time. Start running 3-4 months before.</li><li><strong>Walking:</strong> some states have walking tests instead of running. Check the notification.</li><li><strong>Height and chest:</strong> measurements are taken. Know the standards for your category.</li><li><strong>Build stamina gradually.</strong> Do not overtrain. Consistency matters more than intensity.</li></ul>"),
            ("Documents checklist", "<ul class=\"check-list\"><li>School leaving certificate (Class 10/12)</li><li>Caste certificate (if applicable)</li><li>Domicile certificate</li><li>Physical fitness certificate from a government doctor</li><li>Passport-size photographs</li><li>Application form (as per state format)</li><li>Identity proof (Aadhaar, voter ID)</li></ul>"),
            ("Timeline", "<ol class=\"check-list\"><li><strong>3-4 months before:</strong> Start physical preparation. Begin studying general awareness and arithmetic.</li><li><strong>2 months before:</strong> Solve previous years' papers. Focus on weak areas.</li><li><strong>1 month before:</strong> Revise. Take mock tests. Check physical standards.</li><li><strong>1 week before:</strong> Rest. Verify documents. Check exam centre and reporting time.</li><li><strong>Exam day:</strong> Carry all documents. Arrive early. Stay calm.</li></ol>"),
        ],
        "faqs": [
            ("How many vacancies are there usually?", "It varies by state and year. Some states recruit hundreds; others recruit a few dozen. Check the notification."),
            ("Is coaching necessary?", "No. Self-study with previous papers and basic fitness preparation is sufficient for most candidates."),
            ("Can I apply in multiple states?", "Yes. Each state has its own recruitment. You can apply to any state where you meet the eligibility."),
        ],
        "related": [("/exams/forest-guard", "Forest guard recruitment guide"), ("/roles/forest-guard", "Forest guard career profile"), ("/glossary/campa", "CAMPA glossary entry"), ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs")],
    },
]

# ---------------------------------------------------------------------------
# Resume/CV templates
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        "slug": "esg-analyst-resume-template",
        "title": "ESG Analyst Resume Template & Format",
        "desc": "A resume template and format guide for ESG analyst roles in India. Sections, skills and tips.",
        "kicker": "Resume template",
        "h1": "ESG Analyst Resume Template",
        "sub": "A resume format and section guide for ESG analyst roles in India, with tips on what employers look for.",
        "sections": [
            ("Resume structure", "<ol class=\"check-list\"><li><strong>Header:</strong> Name, phone, email, LinkedIn, city. No photo needed.</li><li><strong>Summary:</strong> 2-3 lines: your background, key skills and what you are looking for. Example: 'ESG analyst with 2 years experience in BRSR reporting and carbon accounting. Skilled in data collection, GRI standards and stakeholder engagement.'</li><li><strong>Skills:</strong> List 8-12 skills. Group them: Frameworks (BRSR, GRI, GHG Protocol), Tools (Excel, Power BI, Python), Domain (carbon accounting, ESG data).</li><li><strong>Experience:</strong> Reverse chronological. For each role: company, title, dates, 3-4 bullet points with metrics.</li><li><strong>Education:</strong> Degree, institution, year. Include relevant coursework or thesis.</li><li><strong>Certifications:</strong> GRI, SASB, BRSR training, etc. (if any)</li><li><strong>Projects:</strong> 1-2 relevant projects with outcomes.</li></ol>"),
            ("What employers look for", "<ul class=\"check-list\"><li><strong>BRSR knowledge:</strong> Can you explain the essential and leadership indicators?</li><li><strong>Data skills:</strong> Excel, Power BI, Python. Show specific tools used.</li><li><strong>Framework knowledge:</strong> GRI, GHG Protocol, TCFD. Name the standards you know.</li><li><strong>Impact:</strong> Quantify your work. 'Collected ESG data from 50+ suppliers' is better than 'responsible for ESG data'.</li><li><strong>Communication:</strong> ESG analysts write reports. Show writing samples if possible.</li></ul>"),
            ("Common mistakes", "<ul class=\"check-list\"><li>Listing every skill you have ever touched. Keep it to 8-12 relevant skills.</li><li>No quantified achievements. Numbers make your resume credible.</li><li>Using a generic objective statement. Use a specific summary instead.</li><li>Not mentioning BRSR or GRI. These are the most common requirements in Indian ESG postings.</li><li>Too long. Keep it to 1-2 pages.</li></ul>"),
            ("Downloadable format", "<p>A clean, ATS-friendly resume template is available as a Word document. Format: single column, standard fonts, no graphics.</p><p><a class=\"btn btn-primary\" href=\"/assets/templates/esg-analyst-resume.docx\" download>Download ESG Analyst Resume Template (DOCX) &darr;</a></p>"),
        ],
        "faqs": [
            ("Should I include a photo?", "No. Indian recruiters do not expect photos on resumes. It can cause bias."),
            ("How long should my resume be?", "1 page for freshers, 2 pages for experienced professionals. Never more than 2 pages."),
            ("Should I list certifications I am pursuing?", "Yes, but mark them as 'in progress' or 'expected' with the expected completion date."),
        ],
        "related": [("/roles/esg-analyst", "ESG analyst profile"), ("/glossary/esg", "ESG glossary entry"), ("/glossary/brsr", "BRSR glossary entry"), ("/esg-carbon-sustainability-jobs", "ESG and sustainability jobs")],
    },
    {
        "slug": "jrf-cv-format",
        "title": "JRF CV Format & Template for Research Positions",
        "desc": "A CV format and template guide for Junior Research Fellow (JRF) applications in India. Sections, tips and common mistakes.",
        "kicker": "Resume template",
        "h1": "JRF CV Format & Template",
        "sub": "A CV format guide for Junior Research Fellow applications in Indian research institutes.",
        "sections": [
            ("CV structure", "<ol class=\"check-list\"><li><strong>Header:</strong> Name, phone, email, address. Include NET/GATE qualification and score.</li><li><strong>Research interests:</strong> 3-5 lines listing your research areas. Be specific.</li><li><strong>Education:</strong> Reverse chronological. Include thesis title, supervisor and grade.</li><li><strong>Research experience:</strong> Projects, internships, lab work. Include techniques used and outcomes.</li><li><strong>Publications:</strong> List any papers, posters or conference presentations.</li><li><strong>Skills:</strong> Lab techniques, software, programming, statistical tools.</li><li><strong>Awards & scholarships:</strong> NET/GATE, university medals, fellowships.</li><li><strong>References:</strong> 2-3 academic references with contact details.</li></ol>"),
            ("What panel members look for", "<ul class=\"check-list\"><li><strong>Dissertation depth:</strong> Can you explain your research clearly? Do you know the limitations?</li><li><strong>Technical skills:</strong> What lab techniques, software and methods have you actually used?</li><li><strong>Research aptitude:</strong> Do you read papers? Can you critique a study?</li><li><strong>Alignment:</strong> Does your background match the project's needs?</li><li><strong>Honesty:</strong> Do not claim skills you do not have. Panel members will test them.</li></ul>"),
            ("Common mistakes", "<ul class=\"check-list\"><li>Listing every course taken. Focus on relevant coursework and thesis.</li><li>No publications or conference presentations. Even a poster counts.</li><li>Claiming skills not demonstrated. Panel members will ask you to explain.</li><li>Not including NET/GATE score and rank. This is the first thing panel members check.</li><li>Too long. Keep it to 2-3 pages maximum.</li></ul>"),
            ("Downloadable format", "<p>A clean, ATS-friendly CV template is available as a Word document.</p><p><a class=\"btn btn-primary\" href=\"/assets/templates/jrf-cv-format.docx\" download>Download JRF CV Template (DOCX) &darr;</a></p>"),
        ],
        "faqs": [
            ("Should I include my PhD plan?", "Yes, if you have one. It shows research direction and commitment."),
            ("How many references should I list?", "2-3 academic references. Include at least one from your master's supervisor."),
            ("Should I include personal details?", "Include name, phone, email and address. Do not include age, religion or marital status."),
        ],
        "related": [("/roles/junior-research-fellow", "JRF salary and career profile"), ("/exams/csir-jrf", "CSIR JRF guide"), ("/exams/ugc-net-environmental-science", "UGC-NET guide"), ("/glossary/jrf", "JRF glossary entry")],
    },
    {
        "slug": "forest-guard-application-format",
        "title": "Forest Guard Application Format & Document Checklist",
        "desc": "Application format and document checklist for forest guard recruitment in India.",
        "kicker": "Application template",
        "h1": "Forest Guard Application Format",
        "sub": "Application format and document checklist for state forest guard recruitment.",
        "sections": [
            ("Application format", "<ol class=\"check-list\"><li><strong>Personal details:</strong> Name, father's name, date of birth, gender, category (SC/ST/OBC/General), domicile state.</li><li><strong>Educational qualification:</strong> Class 10/12 details — board, year, percentage, roll number.</li><li><strong>Physical details:</strong> Height, chest (if applicable), any physical disability.</li><li><strong>Experience:</strong> Any relevant field experience (optional but helpful).</li><li><strong>Declaration:</strong> Signed declaration that all information is correct.</li><li><strong>Photograph:</strong> Passport-size, as per state format.</li></ol>"),
            ("Document checklist", "<ul class=\"check-list\"><li>School leaving certificate (Class 10/12) — original + 2 copies</li><li>Caste certificate (if applicable) — original + 2 copies</li><li>Domicile certificate — original + 2 copies</li><li>Physical fitness certificate from government doctor</li><li>Passport-size photographs (4-6)</li><li>Application form (as per state format)</li><li>Identity proof (Aadhaar, voter ID) — original + copy</li><li>Category certificate for reservation (if applicable)</li></ul>"),
            ("Physical test preparation", "<ul class=\"check-list\"><li><strong>Running:</strong> 1600m-25km in specified time. Start 3-4 months before.</li><li><strong>Height and chest:</strong> Know the standards for your category and gender.</li><li><strong>Build stamina gradually.</strong> Consistency over intensity.</li><li><strong>Practice on similar terrain.</strong> Forest guard tests are often on uneven ground.</li></ul>"),
            ("Common mistakes", "<ul class=\"check-list\"><li>Missing documents at verification stage. Carry originals and copies.</li><li>Not meeting physical standards. Check height/chest requirements before applying.</li><li>Applying without reading the notification. Each state has different rules.</li><li>Missing the application deadline. State portals often close at midnight.</li></ul>"),
        ],
        "faqs": [
            ("Can I apply in multiple states?", "Yes. Each state has its own recruitment. You can apply to any state where you meet eligibility."),
            ("Is coaching necessary?", "No. Self-study with previous papers and physical preparation is sufficient."),
            ("What is the salary?", "Forest guard pay follows the state pay matrix. The notification states the current figure."),
        ],
        "related": [("/exams/forest-guard", "Forest guard recruitment guide"), ("/roles/forest-guard", "Forest guard career profile"), ("/glossary/campa", "CAMPA glossary entry"), ("/forestry-wildlife-government-jobs", "Forestry and wildlife jobs")],
    },
]


def build_index(items: List[Dict], title: str, desc: str, slug: str, kicker: str, h1: str, sub: str) -> None:
    cards = "\n".join(
        f"""        <article class="hub-card">
          <h3 class="hub-card-title"><a href="/guides/{item['slug']}">{esc(item['title'])}</a></h3>
          <p class="hub-card-sum">{esc(item['desc'])}</p>
          <p class="hub-card-foot"><a href="/guides/{item['slug']}">Read &rarr;</a></p>
        </article>"""
        for item in items
    )
    body = "\n".join([
        hero(kicker, h1, sub, [("Items", str(len(items))), ("Updated", TODAY.strftime("%d %b %Y"))]),
        f"""    <section class="hub-main">
      <div class="hub-main-inner">
        <h2>All items</h2>
        <div class="hub-list">
{cards}
        </div>
      </div>
    </section>""",
        beh.bsp.faq_section_html([
            ("Are these free?", "Yes. All content on Urban Forest Park is free."),
            ("How often are they updated?", "Reviewed when regulations or processes change."),
            ("Can I suggest a topic?", "Yes, through the report page or by email."),
        ]),
    ])
    write_sub(GUIDES_DIR, slug, shell(
        title=title, description=desc, canonical=f"{SITE}/guides/{slug}",
        body=body, jsonld="\n".join([beh.bsp.organization_jsonld(), beh.bsp.website_jsonld(), beh.breadcrumb(title, f"{SITE}/guides/{slug}")]),
    ))


def main() -> None:
    all_items = TRANSITIONS + INTERVIEWS + TEMPLATES
    for item in all_items:
        build_page(**{k: item[k] for k in ["slug", "title", "desc", "kicker", "h1", "sub", "sections", "faqs", "related"]})

    # Build index pages for each category
    build_index(TRANSITIONS, "Career Transition Guides", "How to switch into green careers from IT, engineering, academia and non-profit.", "career-transitions", "Career transitions", "Career Transition Guides", "How to move into green careers from other fields.")
    build_index(INTERVIEWS, "Interview Prep Guides", "Interview preparation for ESG, GIS, JRF and forest guard roles.", "interview-preparation", "Interview prep", "Interview Preparation Guides", "How to prepare for green job interviews.")
    build_index(TEMPLATES, "Resume & Application Templates", "Resume formats and application templates for green jobs in India.", "resume-templates", "Templates", "Resume & Application Templates", "Resume formats and application templates for green jobs.")

    beh.update_sitemap(["/guides"] + [f"/guides/{item['slug']}" for item in all_items] + ["/guides/career-transitions", "/guides/interview-preparation", "/guides/resume-templates"])
    print(f"Wrote {len(all_items)} guides + 3 index pages")


if __name__ == "__main__":
    main()
