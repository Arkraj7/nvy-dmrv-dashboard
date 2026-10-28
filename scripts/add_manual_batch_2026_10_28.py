"""Add the verified 28 October 2026 LinkedIn opportunity batch.

Only records whose official page (or official application form / email) was
reachable on 2026-10-28 are included.  Posts that exposed only an aggregator
or a link shortener without an official destination, and calls whose deadline
had already passed, are intentionally omitted.

Run from the repository root:

    py scripts/add_manual_batch_2026_10_28.py

The script is idempotent: existing ids are left untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"
GLOBAL_PATH = ROOT / "public" / "global_jobs.json"

VERIFIED_AT = "2026-10-28"
DATE_ADDED = "2026-10-28"


def base_record(**overrides):
    record = {
        "clean_title": "",
        "organization": "",
        "city": "",
        "state": "",
        "country": "India",
        "category": "",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "experience_level": "1-3 Years",
        "employment_type": "FULL_TIME",
        "deadline_or_window": "Rolling / Open",
        "valid_through": "2026-11-27",
        "qualification_summary": "",
        "compensation_or_fellowship": "Not disclosed - see official notification",
        "role_summary": "",
        "key_responsibilities": [],
        "must_have_skills": [],
        "application_tip": "",
        "apply_url": "",
        "org_website": "",
        "org_domain": "",
        "source_portal": "LinkedIn batch - verified 2026-10-28",
        "entry_type": "posting",
        "status": "active",
        "global": False,
        "evergreen": False,
        "date_added": DATE_ADDED,
        "date_posted": DATE_ADDED,
        "title_hi": "",
        "summary_hi": "",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-verified",
        },
        "id": "",
    }
    record.update(overrides)
    return record


INDIA_RECORDS = [
    base_record(
        id="sgs-assistant-manager-techno-commercial-esg-2026",
        clean_title="Assistant Manager - Techno-Commercial / Pre-Sales (ESG and Sustainability)",
        organization="SGS India",
        city="Chennai",
        state="Tamil Nadu",
        category="ESG, Carbon Markets & Corporate Sustainability",
        experience_level="Mid-Senior (3-6 Years)",
        qualification_summary=(
            "3-6 years in ESG, sustainability, or environmental consulting, with a technical "
            "understanding of ESG frameworks, BRSR, GHG/carbon footprint, net zero, ESG "
            "assessments, and sustainability reporting."
        ),
        role_summary=(
            "SGS India is hiring a technical ESG and sustainability professional for a "
            "techno-commercial / pre-sales role. The position translates client ESG requirements "
            "into technical solutions and supports proposals, client discussions, and business "
            "development across ESG advisory, BRSR, carbon footprint, net zero, and training."
        ),
        key_responsibilities=[
            "Understand client ESG and sustainability requirements and propose technical solutions",
            "Support pre-sales through client discussions, presentations, and technical proposals",
            "Work with sales and technical teams on techno-commercial proposals",
            "Support business development and conversion of ESG opportunities",
            "Engage ESG, CSR, EHS, compliance, and procurement stakeholders",
        ],
        must_have_skills=[
            "ESG Advisory",
            "BRSR",
            "GHG Accounting",
            "Sustainability Reporting",
            "Pre-Sales",
            "Client Communication",
        ],
        application_tip=(
            "Email your CV to sayeeda.pathan@sgs.com with the subject line "
            "'Assistant Manager - Techno-Commercial / Pre-Sales (ESG and Sustainability)'."
        ),
        apply_url="mailto:sayeeda.pathan@sgs.com",
        org_website="https://www.sgs.com",
        org_domain="sgs.com",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-11",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:sayeeda.pathan@sgs.com",
        },
    ),
    base_record(
        id="climate-educators-network-project-coordinator-2026",
        clean_title="Project Coordinator - Climate Action Forums",
        organization="Climate Educators Network (CEN)",
        city="Bengaluru (Kodathi)",
        state="Karnataka",
        category="Climate Policy, Think-Tanks & Fellowships",
        experience_level="1-3 Years",
        qualification_summary=(
            "1-2 years in programme coordination, education, sustainability, or social impact; "
            "fluent spoken Kannada is mandatory; working knowledge of climate change and school "
            "education systems."
        ),
        role_summary=(
            "Climate Educators Network is hiring a Project Coordinator to lead Climate Action "
            "Forums across five partner schools in Kodathi, Bengaluru. The role coordinates "
            "school climate projects, teacher and student support, audits, campaigns, "
            "documentation, and event logistics, with regular travel to school sites."
        ),
        key_responsibilities=[
            "Coordinate activities across five partner schools in Kodathi",
            "Support teachers and students on climate projects, audits, and campaigns",
            "Document impact stories, case studies, and social media content",
            "Track progress, manage timelines, and handle event logistics",
            "Travel regularly to partner school sites",
        ],
        must_have_skills=[
            "Programme Coordination",
            "Climate Education",
            "Kannada",
            "Documentation",
            "Event Logistics",
            "Stakeholder Engagement",
        ],
        application_tip=(
            "Email your resume to info@thecen.in. For queries, contact midhili@asar.co.in or "
            "sunayana.ganguly@thecen.in."
        ),
        apply_url="mailto:info@thecen.in",
        org_website="https://thecen.in",
        org_domain="thecen.in",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-11",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:info@thecen.in",
        },
    ),
    base_record(
        id="ccdc-gis-specialist-charm-india-2026",
        clean_title="Project Research Scientist III (Non-Medical) - GIS Specialist",
        organization="Centre for Chronic Disease Control (CCDC)",
        city="New Delhi",
        state="Delhi",
        category="GIS, Remote Sensing & Earth Observation",
        position_type="Project Associate / Research Associate",
        experience_level="Mid-Senior (3-6 Years)",
        employment_type="CONTRACTOR",
        deadline_or_window="10 November 2026",
        valid_through="2026-11-10",
        qualification_summary=(
            "Postgraduate degree in GIS, geoinformatics, remote sensing, geography, "
            "environmental science, geomatics, computer science, data science, statistics, or a "
            "related discipline with five years of post-qualification experience, or a PhD with "
            "two years; at least five relevant projects."
        ),
        compensation_or_fellowship="As per ICMR pay structure",
        role_summary=(
            "CCDC is recruiting a GIS Specialist for CHARM-India, a climate and health "
            "adaptation project. The role leads spatial data integration, climate-health "
            "vulnerability mapping, the Climate-Health Vulnerability Index (CHVI), and "
            "geospatial dashboards for hospital climate resilience planning."
        ),
        key_responsibilities=[
            "Integrate geospatial, environmental, climatic, demographic, and health datasets",
            "Conduct advanced spatial analysis and climate-health vulnerability modelling",
            "Design, validate, and update the Climate-Health Vulnerability Index",
            "Build GIS dashboards and spatial decision-support systems",
            "Produce maps, analytical reports, and technical inputs for publications",
        ],
        must_have_skills=[
            "GIS",
            "Remote Sensing",
            "ArcGIS or QGIS",
            "Python or R",
            "PostGIS",
            "Spatial Analysis",
            "Climate and Health",
        ],
        application_tip=(
            "Apply through the official CCDC application form linked on the job page by "
            "10 November 2026."
        ),
        apply_url="https://ccdcindia.org/career/project-research-scientist-iii-non-medical-2/",
        org_website="https://ccdcindia.org",
        org_domain="ccdcindia.org",
        source_portal="LinkedIn batch - official job page verified",
        reverify_after="2026-11-09",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://ccdcindia.org/career/project-research-scientist-iii-non-medical-2/",
            "http_status": 200,
        },
    ),
    base_record(
        id="iica-advanced-programme-csr-esg-sustainability-2026",
        clean_title="Advanced Programme on CSR, ESG and Sustainability (Practical Track)",
        organization="Indian Institute of Corporate Affairs (IICA), Ministry of Corporate Affairs",
        city="Online",
        state="",
        category="Workshops, Training & Capacity Building",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="31 October 2026",
        valid_through="2026-10-31",
        qualification_summary=(
            "Open to CSR, ESG, and sustainability learners and career aspirants, including "
            "participants of the SWAYAM CSR, ESG and Sustainability programme."
        ),
        compensation_or_fellowship="Programme fee Rs 35,000 (no GST for the first 60 learners)",
        role_summary=(
            "IICA, an autonomous organisation under the Ministry of Corporate Affairs, offers "
            "an Advanced Programme on CSR, ESG and Sustainability with faculty-led sessions, "
            "exam preparation, real-world assignments, and a capstone project. The cohort starts "
            "1 November 2026 and enrolment closes 31 October 2026."
        ),
        key_responsibilities=[
            "Complete faculty-led sessions on CSR, ESG, and sustainability",
            "Work through case studies and practical assignments",
            "Prepare for the SWAYAM CSR, ESG and Sustainability examination",
            "Complete a capstone project",
        ],
        must_have_skills=[
            "CSR",
            "ESG",
            "Sustainability Reporting",
            "BRSR",
            "Corporate Governance",
        ],
        application_tip=(
            "Register on the IICA CSR portal; enrolment closes 31 October 2026 and the "
            "programme starts 1 November 2026."
        ),
        apply_url="https://iicacsr.edmingle.com/course/CSRESGandSustainabilityAdvancedCourse-115355",
        org_website="https://iica.nic.in",
        org_domain="iica.nic.in",
        source_portal="LinkedIn batch - official programme page verified",
        reverify_after="2026-10-30",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://iicacsr.edmingle.com/",
            "http_status": 200,
        },
    ),
    base_record(
        id="prithu-gis-executive-2026",
        clean_title="GIS Executive",
        organization="Prithu (Varaha)",
        city="Remote",
        state="",
        category="GIS, Remote Sensing & Earth Observation",
        qualification_summary=(
            "Hands-on experience with QGIS or ArcGIS, spatial data workflows, and a strong eye "
            "for accuracy; interest in climate and carbon projects."
        ),
        role_summary=(
            "Prithu is hiring a remote GIS Executive to support real-world climate and carbon "
            "projects across India. The role involves spatial data preparation, mapping, "
            "quality checks, and geospatial deliverables."
        ),
        key_responsibilities=[
            "Prepare and maintain spatial datasets for carbon and climate projects",
            "Create maps and geospatial visualisations in QGIS or ArcGIS",
            "Perform quality checks and accuracy reviews",
            "Support project teams with spatial analysis",
        ],
        must_have_skills=["GIS", "QGIS", "ArcGIS", "Spatial Data", "Mapping", "Attention to Detail"],
        application_tip="Email your CV to hr@prithu.earth.",
        apply_url="mailto:hr@prithu.earth",
        org_website="https://prithu.earth",
        org_domain="prithu.earth",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-11",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:hr@prithu.earth",
        },
    ),
    base_record(
        id="iit-mandi-c3dar-phd-jan-2027",
        clean_title="PhD / M.Tech (Research) Admissions - Centre for Climate Change and Disaster Management",
        organization="IIT Mandi - Centre for Climate Change and Disaster Management (C3DAR)",
        city="Mandi",
        state="Himachal Pradesh",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="9 November 2026",
        valid_through="2026-11-09",
        qualification_summary=(
            "Master's or bachelor's degree in engineering, technology, sciences, or allied "
            "subjects with the prescribed CGPA/CPI, plus GATE/NET or an equivalent national "
            "examination unless exempt."
        ),
        compensation_or_fellowship="Institute fellowship for regular full-time scholars; sponsored and self-sponsored modes available",
        role_summary=(
            "C3DAR at IIT Mandi invites applications for PhD, M.Tech (Research), and dual-degree "
            "programmes for the January-July 2027 semester. Research areas include climate "
            "change, hydrology, water resources, environmental engineering, cryospheric "
            "studies, forest fire dynamics, and disaster management."
        ),
        key_responsibilities=[
            "Develop and run independent research in climate change or disaster management",
            "Complete coursework and a doctoral or research thesis",
            "Publish research and present at seminars",
            "Engage with C3DAR faculty and interdisciplinary projects",
        ],
        must_have_skills=[
            "Climate Change",
            "Hydrology",
            "Environmental Engineering",
            "Disaster Management",
            "Research Methods",
        ],
        application_tip=(
            "Apply through the IIT Mandi Samarth admissions portal; the C3DAR call closes "
            "9 November 2026."
        ),
        apply_url="https://iitmandi.ac.in/pdf/admissions/c3dar_2026_27.pdf",
        org_website="https://c3dar.iitmandi.ac.in/",
        org_domain="iitmandi.ac.in",
        source_portal="LinkedIn batch - official admission notice verified",
        reverify_after="2026-11-08",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-pdf",
            "source": "https://iitmandi.ac.in/pdf/admissions/c3dar_2026_27.pdf",
            "http_status": 200,
        },
    ),
    base_record(
        id="iit-mandi-scene-phd-jan-2027",
        clean_title="PhD / M.Tech (Research) Admissions - School of Civil and Environmental Engineering",
        organization="IIT Mandi - School of Civil and Environmental Engineering (SCENE)",
        city="Mandi",
        state="Himachal Pradesh",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="3 November 2026",
        valid_through="2026-11-03",
        qualification_summary=(
            "B.Tech/B.E. or M.Tech/M.E./M.S. in civil, environmental, water resources, "
            "geotechnical, structural, or related engineering disciplines, with the prescribed "
            "academic thresholds and GATE/NET where required."
        ),
        compensation_or_fellowship="Institute fellowship for regular full-time scholars; sponsored and self-sponsored modes available",
        role_summary=(
            "SCENE at IIT Mandi invites applications for PhD, M.Tech (Research), and dual-degree "
            "programmes for the January 2027 semester. Specialisations include water resources, "
            "environmental engineering, geotechnical, structural, and earthquake engineering."
        ),
        key_responsibilities=[
            "Conduct independent research in civil and environmental engineering",
            "Complete coursework and a research thesis",
            "Publish research and present at seminars",
            "Collaborate with SCENE faculty and project teams",
        ],
        must_have_skills=[
            "Civil Engineering",
            "Environmental Engineering",
            "Water Resources",
            "Research Methods",
        ],
        application_tip=(
            "Apply through the IIT Mandi Samarth admissions portal; the SCENE call closes "
            "3 November 2026."
        ),
        apply_url="https://iitmandi.ac.in/pdf/admissions/SCENE_Advt_2026.pdf",
        org_website="https://www.iitmandi.ac.in/schools/SCENE",
        org_domain="iitmandi.ac.in",
        source_portal="LinkedIn batch - official admission notice verified",
        reverify_after="2026-11-02",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-pdf",
            "source": "https://iitmandi.ac.in/pdf/admissions/SCENE_Advt_2026.pdf",
            "http_status": 200,
        },
    ),
    base_record(
        id="isb-bipp-human-dimensions-climate-change-2026",
        clean_title="Executive Programme - Understanding Human Dimensions of Climate Change",
        organization="Indian School of Business (ISB) - Bharti Institute of Public Policy",
        city="Hyderabad",
        state="Telangana",
        category="Workshops, Training & Capacity Building",
        experience_level="Senior",
        employment_type="OTHER",
        deadline_or_window="Programme runs 16-20 November 2026",
        valid_through="2026-11-16",
        qualification_summary=(
            "Senior government officers across ministries and states, plus a limited number of "
            "self- or organisation-sponsored private sector leaders."
        ),
        compensation_or_fellowship="DoPT-sponsored seats for government officers; fee structure shared on expression of interest",
        role_summary=(
            "The Bharti Institute of Public Policy at ISB Hyderabad hosts a five-day executive "
            "programme on the human dimensions of climate change: impacts, adaptation, and "
            "mitigation. Sessions cover climate science, behaviour, vulnerability, public policy, "
            "the circular bioeconomy, and resilience, led by Prof. Ashwini Chhatre."
        ),
        key_responsibilities=[
            "Attend the five-day in-person programme at ISB Hyderabad",
            "Examine climate impacts, vulnerability, and adaptation policy",
            "Explore circular bioeconomy and sustainable development solutions",
            "Build strategic resilience and peer networks with public administrators",
        ],
        must_have_skills=[
            "Climate Policy",
            "Adaptation",
            "Public Policy",
            "Sustainability Strategy",
            "Circular Bioeconomy",
        ],
        application_tip=(
            "Express interest through the official BIPP form; the cohort runs 16-20 November "
            "2026 at ISB Hyderabad."
        ),
        apply_url="https://form.jotform.com/BIPP_ISB/understanding-human-dimensions-of-c",
        org_website="https://www.isb.edu",
        org_domain="isb.edu",
        source_portal="LinkedIn batch - official programme form verified",
        reverify_after="2026-11-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-form",
            "source": "https://form.jotform.com/BIPP_ISB/understanding-human-dimensions-of-c",
            "http_status": 200,
        },
    ),
]

GLOBAL_RECORDS = [
    base_record(
        id="ukudla-masters-scholarship-cohort-3-2027",
        clean_title="Master's Scholarships in Sustainable Food Systems and Applied Data Science (Cohort 3)",
        organization="African German Centre for Sustainable and Resilient Food Systems (UKUDLA)",
        city="University of Mpumalanga / University of the Western Cape",
        state="",
        country="South Africa",
        region="Africa & Middle East",
        category="Scholarships & Doctoral Support",
        position_type="Fellowship / Internship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="7 November 2026",
        valid_through="2026-11-07",
        qualification_summary=(
            "African candidates with a four-year university degree equivalent to BSc Hons "
            "(NQF level 8) and at least a 68% average, a quantitative background in data "
            "science, computer science, bioinformatics, statistics, mathematics, or agricultural "
            "sciences, basic Python/R and machine learning skills, and eligibility to study in "
            "South Africa."
        ),
        compensation_or_fellowship=(
            "DAAD-funded: EUR 650 monthly stipend + EUR 30 rent subsidy, tuition support up to "
            "EUR 3,000 per year, medical aid contribution up to EUR 20 per month, for up to 24 months"
        ),
        role_summary=(
            "UKUDLA invites applications for fully funded master's scholarships at the "
            "University of Mpumalanga and the University of the Western Cape. Research areas "
            "include data science for food systems, the water-energy-food nexus, farming systems, "
            "agricultural economics, genomics, machine learning, and geospatial analysis."
        ),
        key_responsibilities=[
            "Complete a full-time master's programme at UMP or UWC from February 2027",
            "Conduct research in sustainable food systems and applied data science",
            "Participate in the UKUDLA Graduate Centre, summer schools, and short courses",
            "Produce a master's thesis and contribute to UKUDLA research",
        ],
        must_have_skills=[
            "Data Science",
            "Python or R",
            "Machine Learning",
            "Food Systems",
            "Geospatial Analysis",
            "Statistics",
        ],
        application_tip=(
            "Apply through the official UKUDLA call page by 7 November 2026; queries to "
            "ukudlagradcentre@uwc.ac.za."
        ),
        apply_url="https://ukudla-coe.ac.za/2026/10/12/call-for-masters-scholarship-applications/",
        org_website="https://ukudla-coe.ac.za",
        org_domain="ukudla-coe.ac.za",
        source_portal="LinkedIn batch - official call page verified",
        global_=True,
        reverify_after="2026-11-06",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://ukudla-coe.ac.za/2026/10/12/call-for-masters-scholarship-applications/",
            "http_status": 200,
        },
    ),
    base_record(
        id="leiden-phd-biodiversity-inclusive-agriculture-2027",
        clean_title="PhD - Key Performance Indicators for Biodiversity-Inclusive Agriculture",
        organization="Leiden University - Institute of Environmental Sciences (CML)",
        city="Leiden",
        state="",
        country="Netherlands",
        region="Europe",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="23 November 2026",
        valid_through="2026-11-23",
        qualification_summary=(
            "Master's degree in ecology, environmental science, agricultural science, "
            "sustainability assessment, or a related field; quantitative and interdisciplinary "
            "research skills."
        ),
        compensation_or_fellowship="Salary scale P: EUR 3,204-EUR 4,051 gross per month, plus Leiden University benefits",
        role_summary=(
            "Leiden University's Institute of Environmental Sciences (CML) is recruiting a PhD "
            "researcher to develop key performance indicators for biodiversity-inclusive "
            "agriculture. The project connects biodiversity measurement, farming systems, and "
            "sustainability assessment."
        ),
        key_responsibilities=[
            "Develop and test biodiversity indicators for agricultural systems",
            "Analyse ecological and farm-level data",
            "Publish research and present at conferences",
            "Collaborate with CML researchers and project partners",
        ],
        must_have_skills=[
            "Biodiversity",
            "Agriculture",
            "Quantitative Analysis",
            "Environmental Science",
            "Research Writing",
        ],
        application_tip=(
            "Apply through the Leiden University vacancy page by 23 November 2026."
        ),
        apply_url="https://careers.universiteitleiden.nl/job/PhD-student-on-Key-Performance-Indicators-for-biodiversity-inclusive-agriculture/16985-en_US",
        org_website="https://www.universiteitleiden.nl/en/science/environmental-sciences",
        org_domain="universiteitleiden.nl",
        source_portal="LinkedIn batch - official vacancy verified",
        global_=True,
        reverify_after="2026-11-22",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://careers.universiteitleiden.nl/job/PhD-student-on-Key-Performance-Indicators-for-biodiversity-inclusive-agriculture/16985-en_US",
            "http_status": 200,
        },
    ),
    base_record(
        id="leiden-phd-spatial-demographic-change-2027",
        clean_title="PhD Researcher - Environmental Impacts of Spatial Demographic Change",
        organization="Leiden University - Institute of Environmental Sciences (CML)",
        city="Leiden",
        state="",
        country="Netherlands",
        region="Europe",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="11 January 2027",
        valid_through="2027-01-11",
        qualification_summary=(
            "Master's degree in environmental science, geography, demography, economics, "
            "data science, or a related field; strong quantitative and modelling skills."
        ),
        compensation_or_fellowship="Salary scale P: EUR 3,204-EUR 4,051 gross per month, plus Leiden University benefits",
        role_summary=(
            "Leiden University's CML is recruiting a PhD researcher to study how population "
            "change, urban development, and demographic trends affect energy demand, resource "
            "consumption, and greenhouse gas emissions across Europe. The position starts with a "
            "one-year contract, extendable for up to three additional years."
        ),
        key_responsibilities=[
            "Model links between demographic change and environmental pressures",
            "Analyse European energy, resource, and emissions data",
            "Publish research and present at international conferences",
            "Collaborate with CML and external research partners",
        ],
        must_have_skills=[
            "Environmental Modelling",
            "Demography",
            "Data Analysis",
            "Energy and Emissions",
            "Research Writing",
        ],
        application_tip=(
            "Apply through the Leiden University vacancy page by 11 January 2027."
        ),
        apply_url="https://careers.universiteitleiden.nl/job/Leiden-PhD-Researcher-Environmental-Impacts-of-Spatial-Demographic-Change/16964-en_US",
        org_website="https://www.universiteitleiden.nl/en/science/environmental-sciences",
        org_domain="universiteitleiden.nl",
        source_portal="LinkedIn batch - official vacancy verified",
        global_=True,
        reverify_after="2027-01-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://careers.universiteitleiden.nl/job/Leiden-PhD-Researcher-Environmental-Impacts-of-Spatial-Demographic-Change/16964-en_US",
            "http_status": 200,
        },
    ),
    base_record(
        id="leiden-phd-pfas-free-membranes-2027",
        clean_title="PhD Position - PFAS-Free Membranes for Use in Electrolysers",
        organization="Leiden University - Leiden Institute of Chemistry",
        city="Leiden",
        state="",
        country="Netherlands",
        region="Europe",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="20 November 2026",
        valid_through="2026-11-20",
        qualification_summary=(
            "Master's degree in chemistry, materials science, chemical engineering, or a related "
            "field; experience with membranes, polymers, or electrochemistry is an advantage."
        ),
        compensation_or_fellowship="Salary scale P: EUR 3,204-EUR 4,051 gross per month, plus Leiden University benefits",
        role_summary=(
            "Leiden University is recruiting a PhD researcher to develop PFAS-free membranes for "
            "electrolysers, supporting the scale-up of green hydrogen and cleaner industrial "
            "chemistry. The project combines materials synthesis, membrane characterisation, and "
            "electrochemical testing."
        ),
        key_responsibilities=[
            "Synthesise and characterise PFAS-free membrane materials",
            "Test membranes in electrolyser conditions",
            "Analyse performance, durability, and degradation",
            "Publish research and collaborate with project partners",
        ],
        must_have_skills=[
            "Materials Chemistry",
            "Membranes",
            "Electrochemistry",
            "Polymer Science",
            "Experimental Research",
        ],
        application_tip=(
            "Apply through the Leiden University vacancy page by 20 November 2026."
        ),
        apply_url="https://careers.universiteitleiden.nl/job/PhD-position-PFAS-free-membranes-for-use-in-electrolysers/16951-en_US",
        org_website="https://www.universiteitleiden.nl/en/science/chemistry",
        org_domain="universiteitleiden.nl",
        source_portal="LinkedIn batch - official vacancy verified",
        global_=True,
        reverify_after="2026-11-19",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://careers.universiteitleiden.nl/job/PhD-position-PFAS-free-membranes-for-use-in-electrolysers/16951-en_US",
            "http_status": 200,
        },
    ),
    base_record(
        id="leiden-phd-entangled-seaweed-2027",
        clean_title="PhD Candidate - 'Entangled with Seaweed' (South Africa Case Studies)",
        organization="Leiden University - Institute of Cultural Anthropology and Development Sociology",
        city="Leiden",
        state="",
        country="Netherlands",
        region="Europe",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="7 November 2026",
        valid_through="2026-11-07",
        qualification_summary=(
            "Master's degree in anthropology, geography, environmental studies, science and "
            "technology studies, or a related social science; qualitative research experience "
            "and willingness to conduct fieldwork in South Africa."
        ),
        compensation_or_fellowship="Salary scale P: EUR 3,204-EUR 4,051 gross per month, plus Leiden University benefits",
        role_summary=(
            "Leiden University is recruiting a PhD candidate for the 'Entangled with Seaweed' "
            "project, using South African case studies to examine human-seaweed relations, "
            "coastal livelihoods, and more-than-human entanglements in environmental governance."
        ),
        key_responsibilities=[
            "Conduct ethnographic fieldwork in South African coastal communities",
            "Analyse human-environment and more-than-human relations",
            "Publish research and present at academic events",
            "Contribute to the interdisciplinary project team",
        ],
        must_have_skills=[
            "Qualitative Research",
            "Ethnography",
            "Environmental Anthropology",
            "Fieldwork",
            "Academic Writing",
        ],
        application_tip=(
            "Apply through the Leiden University vacancy page by 7 November 2026."
        ),
        apply_url="https://careers.universiteitleiden.nl/job/PhD-Candidate-in-the-research-project-%27Entangled-with-Seaweed%27%2C-case-studies-in-South-Africa/16936-en_US",
        org_website="https://www.universiteitleiden.nl/en/social-behavioural-sciences/cultural-anthropology-and-development-sociology",
        org_domain="universiteitleiden.nl",
        source_portal="LinkedIn batch - official vacancy verified",
        global_=True,
        reverify_after="2026-11-06",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://careers.universiteitleiden.nl/job/PhD-Candidate-in-the-research-project-%27Entangled-with-Seaweed%27%2C-case-studies-in-South-Africa/16936-en_US",
            "http_status": 200,
        },
    ),
    base_record(
        id="aureo-early-career-workshop-2027",
        clean_title="AURÖ Early-Career Workshop in Environmental and Resource Economics",
        organization="RPTU University Kaiserslautern-Landau - AURÖ",
        city="Kaiserslautern",
        state="",
        country="Germany",
        region="Europe",
        category="Conferences, Summits & Events",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="8 January 2027",
        valid_through="2027-01-08",
        qualification_summary=(
            "PhD students and postdocs in environmental and resource economics; work in progress, "
            "rough drafts, and preliminary results are welcome."
        ),
        compensation_or_fellowship="No fee stated; participants cover their own travel and accommodation",
        role_summary=(
            "The AURÖ Early-Career Workshop brings PhD students and postdocs in environmental "
            "and resource economics to RPTU Kaiserslautern-Landau from 22-24 February 2027. "
            "Participants present research, receive feedback, and network with early-career "
            "researchers; keynotes by Lara Bartels and Johannes Gessner."
        ),
        key_responsibilities=[
            "Submit a research paper or work in progress by 8 January 2027",
            "Present research at the workshop",
            "Discuss and give feedback on other participants' work",
            "Attend keynotes and networking sessions",
        ],
        must_have_skills=[
            "Environmental Economics",
            "Resource Economics",
            "Research Presentation",
            "Academic Writing",
        ],
        application_tip=(
            "Submit your title and abstract through the RPTU survey form by 8 January 2027."
        ),
        apply_url="https://survey.rptu.de/index.php/363274?newtest=Y&lang=en",
        org_website="https://rptu.de",
        org_domain="rptu.de",
        source_portal="LinkedIn batch - official submission form verified",
        global_=True,
        reverify_after="2026-12-15",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-form",
            "source": "https://survey.rptu.de/index.php/363274?newtest=Y&lang=en",
            "http_status": 200,
        },
    ),
    base_record(
        id="clivar-emerging-ideas-climate-dynamics-webinar-2027",
        clean_title="Emerging Ideas in Climate Dynamics - Six-Part Webinar Series",
        organization="CLIVAR Climate Dynamics Panel (WCRP)",
        city="Online",
        state="",
        country="Global",
        region="Global / Remote",
        category="Workshops, Training & Capacity Building",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="Series runs 16 February - 23 March 2027",
        valid_through="2027-03-23",
        qualification_summary=(
            "Open to climate researchers, students, and practitioners interested in climate "
            "dynamics; registration is free."
        ),
        compensation_or_fellowship="Free online webinar series",
        role_summary=(
            "The CLIVAR Climate Dynamics Panel hosts a six-part webinar series on emerging ideas "
            "in climate dynamics from 16 February to 23 March 2027. Topics include foundational "
            "climate dynamics, convective constraints on extreme temperatures, land humidity, "
            "cloud feedbacks, tropical circulations, and jets and blocking."
        ),
        key_responsibilities=[
            "Register for the webinar series",
            "Attend the one-hour introductory session and five topical webinars",
            "Engage with speakers from leading climate research institutions",
        ],
        must_have_skills=[
            "Climate Dynamics",
            "Climate Science",
            "Atmospheric Science",
        ],
        application_tip=(
            "Register through the official CLIVAR event page; the series runs 16 February - "
            "23 March 2027."
        ),
        apply_url="https://www.clivar.org/events/emerging-ideas-climate-dynamics-webinar-series-hosted-clivar-climate-dynamics-panel",
        org_website="https://www.clivar.org",
        org_domain="clivar.org",
        source_portal="LinkedIn batch - official event page verified",
        global_=True,
        reverify_after="2027-01-15",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.clivar.org/events/emerging-ideas-climate-dynamics-webinar-series-hosted-clivar-climate-dynamics-panel",
            "http_status": 200,
        },
    ),
    base_record(
        id="afs-sir-cyril-taylor-young-african-leaders-2027",
        clean_title="Sir Cyril Taylor Young African Leaders Program 2027",
        organization="AFS Youth Assembly - Sir Cyril Taylor Charitable Foundation",
        city="Sub-Saharan Africa",
        state="",
        country="Global",
        region="Africa & Middle East",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="19 November 2026",
        valid_through="2026-11-19",
        qualification_summary=(
            "Young changemakers aged 18-35 from Sub-Saharan Africa with a demonstrated interest "
            "in sustainable development and at least intermediate English."
        ),
        compensation_or_fellowship=(
            "Fully funded 12-month fellowship with seed funding, capacity building, and covered "
            "travel and accommodation for the AFS Youth Assembly in Geneva in August 2027"
        ),
        role_summary=(
            "AFS Youth Assembly invites applications for the third edition of the Sir Cyril "
            "Taylor Young African Leaders Program. Ten young leaders receive a 12-month "
            "fellowship with seed funding, leadership development, intercultural learning, and "
            "support to implement social impact projects aligned with the SDGs."
        ),
        key_responsibilities=[
            "Develop and implement a community social impact project",
            "Participate in leadership workshops and capacity-building sessions",
            "Attend the AFS Youth Assembly in Geneva in August 2027",
            "Engage with the global Sir Cyril Taylor alumni network",
        ],
        must_have_skills=[
            "Community Leadership",
            "Sustainable Development",
            "Project Management",
            "English",
        ],
        application_tip=(
            "Apply through the AFS Youth Assembly page by 19 November 2026, 23:59 UTC."
        ),
        apply_url="https://www.youthassembly.org/2026/10/16/young-african-leaders-scholarships/",
        org_website="https://www.youthassembly.org",
        org_domain="youthassembly.org",
        source_portal="LinkedIn batch - official programme page verified",
        global_=True,
        reverify_after="2026-11-18",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.youthassembly.org/2026/10/16/young-african-leaders-scholarships/",
            "http_status": 200,
        },
    ),
    base_record(
        id="awesome-foundation-conservation-climate-grant-2026",
        clean_title="Conservation and Climate Microgrants",
        organization="The Awesome Foundation - Conservation and Climate Chapter",
        city="Global",
        state="",
        country="Global",
        region="Global / Remote",
        category="Grants & Research Funding",
        position_type="Young Professional / Consultant (Contractual)",
        opportunity_kind="Grant / Funding",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        entry_type="careers_portal",
        deadline_or_window="27 November 2026",
        valid_through="2026-11-27",
        qualification_summary=(
            "Individuals or small teams anywhere in the world with a concrete conservation or "
            "climate project that can reach a tipping point with a USD 1,000 grant."
        ),
        compensation_or_fellowship="USD 1,000 microgrant",
        role_summary=(
            "The Awesome Foundation's Conservation and Climate chapter awards monthly USD 1,000 "
            "microgrants to promising nature conservation and climate projects. The chapter looks "
            "for ideas where a small grant is the difference between a project happening or not."
        ),
        key_responsibilities=[
            "Submit a short project application in English",
            "Explain how USD 1,000 would create a tipping point for the project",
            "Provide a short video if shortlisted",
            "Use the grant to launch or accelerate the project",
        ],
        must_have_skills=[
            "Conservation",
            "Climate Action",
            "Project Design",
            "Community Impact",
        ],
        application_tip=(
            "Apply through the Conservation and Climate chapter page before the 27 November 2026 "
            "deadline."
        ),
        apply_url="https://www.awesomefoundation.org/en/chapters/conservationandclimate",
        org_website="https://www.awesomefoundation.org",
        org_domain="awesomefoundation.org",
        source_portal="LinkedIn batch - official chapter page verified",
        global_=True,
        reverify_after="2026-11-26",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://www.awesomefoundation.org/en/chapters/conservationandclimate",
            "http_status": 200,
        },
    ),
    base_record(
        id="stanford-global-sustainability-challenge-2027",
        clean_title="Global Sustainability Challenge 2026-27",
        organization="Stanford University - Global Sustainability Challenge",
        city="Stanford",
        state="California",
        country="United States",
        region="North America",
        category="Competitions, Hackathons & Awards",
        position_type="Fellowship / Internship",
        opportunity_kind="Competition / Award",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="Phase 1 (Ignite) closes November 2026",
        valid_through="2026-11-30",
        qualification_summary=(
            "University student teams from around the world designing and prototyping "
            "sustainability solutions."
        ),
        compensation_or_fellowship="Competition prizes and global finale participation; see official challenge details",
        role_summary=(
            "The Stanford-led Global Sustainability Challenge is an annual competition in which "
            "university student teams design, build, and showcase real-world sustainability "
            "solutions. The 2026-27 season runs from September 2026 to the global finale at "
            "Zhejiang University in May 2027."
        ),
        key_responsibilities=[
            "Form a university student team and register for the challenge",
            "Complete the Phase 1 Ignite deliverables",
            "Build and test a sustainability solution in Phase 2",
            "Present at a regional final and the global finale",
        ],
        must_have_skills=[
            "Sustainability",
            "Innovation",
            "Teamwork",
            "Prototyping",
            "Project Development",
        ],
        application_tip=(
            "Register a student team on the official challenge site; Phase 1 runs "
            "September-November 2026."
        ),
        apply_url="https://www.globalsustainabilitychallenge.org/challenge-details",
        org_website="https://www.globalsustainabilitychallenge.org",
        org_domain="globalsustainabilitychallenge.org",
        source_portal="LinkedIn batch - official challenge page verified",
        global_=True,
        reverify_after="2026-11-15",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.globalsustainabilitychallenge.org/",
            "http_status": 200,
        },
    ),
]


UPDATES = {
    "iica-advanced-programme-csr-esg-sustainability-2026": {
        "apply_url": "https://iicacsr.edmingle.com/course/CSRESGandSustainabilityAdvancedCourse-115355",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://iicacsr.edmingle.com/course/CSRESGandSustainabilityAdvancedCourse-115355",
            "http_status": 200,
        },
    },
    "stanford-global-sustainability-challenge-2027": {
        "apply_url": "https://www.globalsustainabilitychallenge.org/challenge-details",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.globalsustainabilitychallenge.org/challenge-details",
            "http_status": 200,
        },
    },
}


def load(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise SystemExit(f"{path} is not a JSON list")
    return data


def save(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def add_new(records: list[dict], additions: list[dict], label: str) -> int:
    existing = {str(record.get("id", "")) for record in records}
    added = 0
    for record in additions:
        if record["id"] in existing:
            print(f"  skip existing {label}: {record['id']}")
            continue
        records.append(record)
        existing.add(record["id"])
        added += 1
        print(f"  add {label}: {record['id']}")
    return added


def apply_updates(records: list[dict], updates: dict[str, dict], label: str) -> int:
    changed = 0
    for record in records:
        patch = updates.get(str(record.get("id", "")))
        if not patch:
            continue
        before = {key: record.get(key) for key in patch}
        if before == patch:
            print(f"  unchanged {label}: {record['id']}")
            continue
        record.update(patch)
        changed += 1
        print(f"  update {label}: {record['id']}")
    return changed


def main() -> None:
    jobs = load(JOBS_PATH)
    global_jobs = load(GLOBAL_PATH)

    print("India registry")
    added_india = add_new(jobs, INDIA_RECORDS, "India")
    updated_india = apply_updates(jobs, UPDATES, "India")

    print("Global registry")
    for record in GLOBAL_RECORDS:
        record["global"] = record.pop("global_", True)
    added_global = add_new(global_jobs, GLOBAL_RECORDS, "Global")
    updated_global = apply_updates(global_jobs, UPDATES, "Global")

    save(JOBS_PATH, jobs)
    save(GLOBAL_PATH, global_jobs)

    print(
        f"\nDone: India +{added_india} / updated {updated_india}; "
        f"Global +{added_global} / updated {updated_global}"
    )
    print(f"India records: {len(jobs)}; global records: {len(global_jobs)}")


if __name__ == "__main__":
    main()
