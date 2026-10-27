"""Add the verified 27 October 2026 LinkedIn opportunity batch.

The batch is intentionally limited to records whose public application link
(or email address) could be verified.  Records that only exposed a link
shortener, a QR code, a phone number, or an expired official notice are not
added here.

Run from the repository root:

    py scripts/add_manual_batch_2026_10_27.py

The script is idempotent: existing ids are left untouched unless they appear
in UPDATES, which repairs two older records with blocked or non-official
application links.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"
GLOBAL_PATH = ROOT / "public" / "global_jobs.json"

VERIFIED_AT = "2026-10-27"
DATE_ADDED = "2026-10-27"


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
        "valid_through": "2026-11-26",
        "qualification_summary": "",
        "compensation_or_fellowship": "Not disclosed - see official notification",
        "role_summary": "",
        "key_responsibilities": [],
        "must_have_skills": [],
        "application_tip": "",
        "apply_url": "",
        "org_website": "",
        "org_domain": "",
        "source_portal": "LinkedIn batch - verified 2026-10-27",
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
        id="celestial-earth-gis-analyst-2026",
        clean_title="GIS Analyst",
        organization="Celestial Earth",
        city="Gurugram",
        state="Haryana",
        category="GIS, Remote Sensing & Earth Observation",
        experience_level="1-3 Years",
        qualification_summary=(
            "Degree in GIS, remote sensing, geography, environmental science, or a related "
            "field; working knowledge of ArcGIS/QGIS and spatial data workflows."
        ),
        role_summary=(
            "Celestial Earth is hiring a GIS Analyst to support environmental and geospatial "
            "projects. The role covers spatial data preparation, mapping, remote-sensing "
            "analysis, and project deliverables for climate and sustainability clients."
        ),
        key_responsibilities=[
            "Prepare and clean spatial datasets",
            "Create maps and geospatial visualisations",
            "Support remote-sensing and environmental analysis",
            "Document methods and project outputs",
        ],
        must_have_skills=["GIS", "ArcGIS or QGIS", "Remote Sensing", "Spatial Analysis", "Data Management"],
        application_tip=(
            "Email your CV and portfolio to dipti.a@thecelestialearth.org with the subject "
            "line 'GIS Analyst'."
        ),
        apply_url="mailto:dipti.a@thecelestialearth.org",
        org_website="https://www.thecelestialearth.org/",
        org_domain="thecelestialearth.org",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:dipti.a@thecelestialearth.org",
        },
    ),
    base_record(
        id="enkay-enviro-junior-social-expert-2026",
        clean_title="Junior Social Expert",
        organization="Enkay Enviro Services Pvt. Ltd.",
        city="Jaipur",
        state="Rajasthan",
        category="ESG, Carbon Markets & Corporate Sustainability",
        experience_level="Entry Level / Fellowship",
        qualification_summary=(
            "Degree in social sciences, sociology, development studies, environmental science, "
            "or a related field; 0-2 years of experience in social impact assessment, "
            "stakeholder engagement, or EIA/social safeguards."
        ),
        role_summary=(
            "Enkay Enviro Services is hiring a Junior Social Expert for environmental and "
            "social assessment work. The role supports social impact studies, stakeholder "
            "consultations, field surveys, and safeguard documentation for infrastructure and "
            "development projects."
        ),
        key_responsibilities=[
            "Conduct social impact assessments and baseline surveys",
            "Support stakeholder consultations and community engagement",
            "Prepare social safeguard and EIA documentation",
            "Analyse field data and contribute to reports",
        ],
        must_have_skills=["Social Impact Assessment", "Stakeholder Engagement", "Field Research", "Report Writing"],
        application_tip=(
            "Email your CV to socio@enkayenviro.com with the subject line 'Junior Social Expert'."
        ),
        apply_url="mailto:socio@enkayenviro.com",
        org_website="https://enkayenviro.com",
        org_domain="enkayenviro.com",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:socio@enkayenviro.com",
        },
    ),
    base_record(
        id="iisc-urban-flood-forecasting-4-positions-2026",
        clean_title="Urban Flood Forecasting & Climate Resilience - 4 Project Positions",
        organization="Indian Institute of Science (IISc), Bengaluru",
        city="Bengaluru",
        state="Karnataka",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Project Associate / Research Associate",
        experience_level="1-3 Years",
        employment_type="CONTRACTOR",
        deadline_or_window="8 November 2026",
        valid_through="2026-11-08",
        qualification_summary=(
            "B.Tech/M.Tech/M.Sc/PhD in civil engineering, water resources, environmental "
            "engineering, hydrology, GIS/remote sensing, data science, or a related field."
        ),
        compensation_or_fellowship="As per IISc project norms",
        role_summary=(
            "IISc Bengaluru is recruiting four project positions for an urban flood "
            "forecasting and climate resilience project. The roles cover flood modelling, "
            "hydrological analysis, geospatial data, field support, and project deliverables."
        ),
        key_responsibilities=[
            "Develop and run urban flood and hydrological models",
            "Process rainfall, drainage, and geospatial datasets",
            "Support field data collection and validation",
            "Prepare project reports and visualisations",
        ],
        must_have_skills=["Hydrology", "Flood Modelling", "GIS", "Data Analysis", "Python or R"],
        application_tip=(
            "Email your CV and relevant project experience to rajarshidb@iisc.ac.in by "
            "8 November 2026."
        ),
        apply_url="mailto:rajarshidb@iisc.ac.in",
        org_website="https://www.iisc.ac.in",
        org_domain="iisc.ac.in",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-07",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:rajarshidb@iisc.ac.in",
        },
    ),
    base_record(
        id="churchgate-partners-research-analyst-sustainability-2026",
        clean_title="Research Analyst - Sustainability",
        organization="Churchgate Partners",
        city="Mumbai",
        state="Maharashtra",
        category="ESG, Carbon Markets & Corporate Sustainability",
        deadline_or_window="30 October 2026",
        valid_through="2026-10-30",
        qualification_summary=(
            "Degree in environmental science, sustainability, economics, finance, or a "
            "related field; 1-3 years of research or ESG advisory experience."
        ),
        role_summary=(
            "Churchgate Partners is hiring a Research Analyst for its sustainability practice. "
            "The role involves ESG research, sustainability reporting, data analysis, and "
            "support for client engagements."
        ),
        key_responsibilities=[
            "Research ESG and sustainability trends",
            "Analyse corporate disclosures and sustainability data",
            "Support client reports and presentations",
            "Track regulatory and market developments",
        ],
        must_have_skills=["ESG Research", "Sustainability Reporting", "Data Analysis", "Report Writing"],
        application_tip=(
            "Email your CV to talent@churchgatepartners.com by 30 October 2026 with the "
            "subject line 'Research Analyst - Sustainability'."
        ),
        apply_url="mailto:talent@churchgatepartners.com",
        org_website="https://www.churchgatepartners.com",
        org_domain="churchgatepartners.com",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-10-29",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:talent@churchgatepartners.com",
        },
    ),
    base_record(
        id="teri-transport-modelling-emissions-accounting-ra-2026",
        clean_title="Research Associate - Transport Modelling & Emissions Accounting",
        organization="The Energy and Resources Institute (TERI)",
        city="New Delhi",
        state="Delhi",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Project Associate / Research Associate",
        experience_level="1-3 Years",
        employment_type="CONTRACTOR",
        deadline_or_window="8 November 2026",
        valid_through="2026-11-08",
        qualification_summary=(
            "Master's degree in transport planning, environmental science, economics, "
            "engineering, or a related field; experience with transport modelling and "
            "emissions accounting."
        ),
        compensation_or_fellowship="As per TERI norms",
        role_summary=(
            "TERI is hiring a Research Associate for transport modelling and emissions "
            "accounting. The role supports low-carbon transport research, scenario analysis, "
            "and policy-relevant emissions estimates."
        ),
        key_responsibilities=[
            "Develop transport and emissions models",
            "Analyse transport data and policy scenarios",
            "Prepare research reports and presentations",
            "Support project delivery and stakeholder engagement",
        ],
        must_have_skills=["Transport Modelling", "Emissions Accounting", "Data Analysis", "Policy Research"],
        application_tip=(
            "Email your CV to tripti.patra@teri.res.in by 8 November 2026 with the subject "
            "line 'Research Associate - Transport Modelling'."
        ),
        apply_url="mailto:tripti.patra@teri.res.in",
        org_website="https://www.teriin.org",
        org_domain="teriin.org",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-07",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:tripti.patra@teri.res.in",
        },
    ),
    base_record(
        id="reeds-program-manager-finance-research-assistant-2026",
        clean_title="Program Manager / Executive - Finance / Research Assistant and Other Roles (5 Positions)",
        organization="Rural Economic and Educational Development Society (REEDS)",
        city="Hyderabad",
        state="Telangana",
        category="Climate Policy, Think-Tanks & Fellowships",
        deadline_or_window="15 November 2026",
        valid_through="2026-11-15",
        qualification_summary=(
            "Relevant degree and experience in programme management, finance/accounts, "
            "research, or rural development; five positions across multiple functions."
        ),
        role_summary=(
            "REEDS is hiring for five positions across programme management, finance, "
            "research, and project implementation. Confirmed roles include Program Manager, "
            "Executive - Finance, and Research Assistant, with additional project roles."
        ),
        key_responsibilities=[
            "Manage rural development programmes and field teams",
            "Support finance, accounts, and compliance functions",
            "Conduct research, data collection, and documentation",
            "Coordinate with communities, partners, and project stakeholders",
        ],
        must_have_skills=["Programme Management", "Finance or Accounts", "Research", "Rural Development"],
        application_tip=(
            "Email your CV to info@reeds.in by 15 November 2026, mentioning the position "
            "you are applying for."
        ),
        apply_url="mailto:info@reeds.in",
        org_website="https://reeds.in",
        org_domain="reeds.in",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-14",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:info@reeds.in",
        },
    ),
    base_record(
        id="ag-horizon-water-resources-multiple-positions-2026",
        clean_title="Water Resource Engineer / Business Consultant / Disaster Management Expert / Office Coordinator (Multiple Positions)",
        organization="AG Horizon Pvt. Ltd.",
        city="Guwahati / Gurugram",
        state="Assam / Haryana",
        category="GIS, Remote Sensing & Earth Observation",
        qualification_summary=(
            "Engineering, environmental science, GIS, management, or related background "
            "depending on the role; experience in water resources, disaster management, "
            "business consulting, or office coordination."
        ),
        role_summary=(
            "AG Horizon is recruiting for multiple water resources, consulting, disaster "
            "management, and office coordination roles across its Guwahati and Gurugram "
            "offices. Current openings are listed on the official recruitment page."
        ),
        key_responsibilities=[
            "Support water resources and irrigation projects",
            "Conduct GIS and spatial analysis",
            "Contribute to disaster management and climate resilience work",
            "Provide business consulting or office coordination support",
        ],
        must_have_skills=["Water Resources", "GIS", "Disaster Management", "Project Coordination"],
        application_tip=(
            "Apply through the official AG Horizon recruitment form; current openings include "
            "Guwahati and Gurugram roles."
        ),
        apply_url="https://aggrp.in/recruitment/",
        org_website="https://aggrp.in/",
        org_domain="aggrp.in",
        entry_type="careers_portal",
        source_portal="LinkedIn batch - official recruitment page verified",
        reverify_after="2026-11-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://aggrp.in/recruitment/",
            "http_status": 200,
        },
    ),
    base_record(
        id="iora-biodiversity-data-intern-2026",
        clean_title="Biodiversity Data Intern",
        organization="Iora Ecological Solutions",
        city="New Delhi",
        state="Delhi",
        category="Internships & Student Traineeships",
        position_type="Fellowship / Internship",
        opportunity_kind="Internship",
        experience_level="Entry Level / Fellowship",
        employment_type="INTERN",
        qualification_summary=(
            "Students or recent graduates in ecology, environmental science, biodiversity, "
            "GIS, or related fields; interest in biodiversity data and field research."
        ),
        role_summary=(
            "Iora Ecological Solutions is offering a biodiversity data internship. The intern "
            "will support biodiversity data collection, cleaning, GIS mapping, literature "
            "review, and field research for conservation projects."
        ),
        key_responsibilities=[
            "Compile and clean biodiversity datasets",
            "Support GIS mapping and spatial analysis",
            "Conduct literature reviews and species research",
            "Assist with field surveys and project documentation",
        ],
        must_have_skills=["Biodiversity", "Data Management", "GIS", "Literature Review"],
        application_tip=(
            "Email your CV and a brief statement of interest to "
            "internships@ioraecological.com."
        ),
        apply_url="mailto:internships@ioraecological.com",
        org_website="https://ioraecological.com",
        org_domain="ioraecological.com",
        source_portal="LinkedIn batch - official email verified",
        reverify_after="2026-11-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-email",
            "source": "mailto:internships@ioraecological.com",
        },
    ),
    base_record(
        id="iit-madras-teaching-program-coordinator-2026",
        clean_title="Teaching Program Coordinator",
        organization="Indian Institute of Technology Madras (IIT Madras)",
        city="Chennai",
        state="Tamil Nadu",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="Faculty / Academic",
        experience_level="Mid-Senior (3-6 Years)",
        employment_type="CONTRACTOR",
        deadline_or_window="29 October 2026",
        valid_through="2026-10-29",
        qualification_summary=(
            "Postgraduate degree with experience in academic programme coordination, "
            "teaching administration, or student support."
        ),
        compensation_or_fellowship="As per IIT Madras norms",
        role_summary=(
            "IIT Madras is hiring a Teaching Program Coordinator through its IC&SR "
            "recruitment portal (Advert 209/2026). The role coordinates teaching programmes, "
            "schedules, student support, and academic documentation."
        ),
        key_responsibilities=[
            "Coordinate teaching programmes and course schedules",
            "Support faculty and students on programme delivery",
            "Maintain academic records and documentation",
            "Organise meetings, reviews, and programme activities",
        ],
        must_have_skills=["Academic Coordination", "Programme Management", "Communication", "Documentation"],
        application_tip=(
            "Official advert 209/2026; last date 29 October 2026. Apply through the IC&SR "
            "recruitment portal."
        ),
        apply_url="https://icandsr.iitm.ac.in/careers/current_openings.php?page=4",
        org_website="https://www.iitm.ac.in",
        org_domain="iitm.ac.in",
        entry_type="careers_portal",
        source_portal="LinkedIn batch - official recruitment portal verified",
        reverify_after="2026-10-28",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://icandsr.iitm.ac.in/careers/current_openings.php?page=4",
            "http_status": 200,
        },
    ),
    base_record(
        id="jsac-research-associate-junior-project-assistant-2026",
        clean_title="Research Associate / Junior Project Assistant",
        organization="Jharkhand Space Applications Centre (JSAC)",
        city="Ranchi",
        state="Jharkhand",
        category="GIS, Remote Sensing & Earth Observation",
        position_type="Project Associate / Research Associate",
        experience_level="1-3 Years",
        employment_type="CONTRACTOR",
        deadline_or_window="18 November 2026",
        valid_through="2026-11-18",
        qualification_summary=(
            "M.Sc./M.Tech in remote sensing, GIS, geoinformatics, environmental science, or a "
            "related field; experience with satellite data processing and spatial analysis."
        ),
        compensation_or_fellowship="As per JSAC norms",
        role_summary=(
            "JSAC is recruiting Research Associates and Junior Project Assistants for remote "
            "sensing and geospatial applications. The roles support satellite data processing, "
            "GIS analysis, and project mapping."
        ),
        key_responsibilities=[
            "Process satellite imagery and geospatial data",
            "Carry out GIS analysis and map production",
            "Support remote-sensing applications and field validation",
            "Prepare project reports and datasets",
        ],
        must_have_skills=["Remote Sensing", "GIS", "Satellite Data Processing", "Spatial Analysis"],
        application_tip=(
            "Apply through the JSAC recruitment portal; online applications close "
            "18 November 2026."
        ),
        apply_url="https://jsac.jharkhand.gov.in/recruitment/",
        org_website="https://jsac.jharkhand.gov.in",
        org_domain="jsac.jharkhand.gov.in",
        entry_type="careers_portal",
        source_portal="LinkedIn batch - official recruitment portal verified",
        reverify_after="2026-11-17",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://jsac.jharkhand.gov.in/recruitment/",
            "http_status": 200,
        },
    ),
    base_record(
        id="pxd-heat-forecast-program-manager-research-associate-2026",
        clean_title="Program Manager / Research Associate - Heat Forecast",
        organization="Precision Development (PxD)",
        city="New Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="10 November 2026",
        valid_through="2026-11-10",
        qualification_summary=(
            "Relevant degree and experience in programme management, economics, climate "
            "adaptation, or research; existing authorization to work in India."
        ),
        role_summary=(
            "PxD is hiring a Program Manager and a Research Associate/Sr Research Associate "
            "for its Heat Forecast work. The roles combine programme management, applied "
            "research, data analysis, and stakeholder engagement on extreme heat."
        ),
        key_responsibilities=[
            "Manage heat forecast programme delivery",
            "Conduct applied research and data analysis",
            "Engage with government and community stakeholders",
            "Support scale-up of heat resilience interventions",
        ],
        must_have_skills=["Programme Management", "Climate Adaptation", "Data Analysis", "Stakeholder Engagement"],
        application_tip=(
            "PxD's careers page lists both Program Manager and Research Associate/Sr Research "
            "Associate (Heat Forecast); New Delhi preferred. Apply by 10 November 2026."
        ),
        apply_url="https://precisiondev.org/about-us/careers/",
        org_website="https://precisiondev.org",
        org_domain="precisiondev.org",
        entry_type="careers_portal",
        source_portal="LinkedIn batch - official careers page verified",
        reverify_after="2026-11-09",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://precisiondev.org/about-us/careers/",
            "http_status": 200,
        },
    ),
]

GLOBAL_RECORDS = [
    base_record(
        id="cornell-forest-restoration-ecology-phd-2027",
        clean_title="PhD in Forest Restoration Ecology",
        organization="Cornell University - Forest Restoration Ecology Lab",
        city="Ithaca",
        state="New York",
        country="United States",
        region="North America",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="1 December 2026",
        valid_through="2026-12-01",
        qualification_summary=(
            "Bachelor's or master's degree in ecology, environmental science, forestry, "
            "geography, or a related field; strong quantitative and field research interest."
        ),
        compensation_or_fellowship="Fully funded for five years (stipend, tuition, and benefits)",
        role_summary=(
            "The Forest Restoration Ecology Lab at Cornell University is recruiting PhD "
            "students to study how forests can be restored, managed, and adapted. Projects "
            "span field measurements, experiments, spatial analysis, and ecological and "
            "economic approaches in New York and Panama."
        ),
        key_responsibilities=[
            "Design and conduct field and landscape research",
            "Analyse ecological and spatial data",
            "Publish research and present findings",
            "Collaborate with lab and partner researchers",
        ],
        must_have_skills=["Ecology", "Field Research", "Spatial Analysis", "Quantitative Methods"],
        application_tip=(
            "Review the lab's opportunities page and apply through Cornell's graduate "
            "admissions process. Contact kas595@cornell.edu with questions; deadline "
            "1 December 2026."
        ),
        apply_url="https://www.katherinesinacore.com/opportunities",
        org_website="https://www.katherinesinacore.com",
        org_domain="katherinesinacore.com",
        source_portal="LinkedIn batch - official lab page verified",
        entry_type="careers_portal",
        global_=True,
        reverify_after="2026-11-30",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.katherinesinacore.com/opportunities",
            "http_status": 200,
        },
    ),
    base_record(
        id="unu-ehs-joint-msc-geography-environmental-risks-2027",
        clean_title="Joint MSc in Geography of Environmental Risks and Human Security",
        organization="United Nations University - Institute for Environment and Human Security (UNU-EHS)",
        city="Bonn",
        state="",
        country="Germany",
        region="Europe",
        category="Scholarships & Doctoral Support",
        position_type="Fellowship / Internship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="31 October 2026",
        valid_through="2026-10-31",
        qualification_summary=(
            "Bachelor's degree in geography, environmental science, social science, or a "
            "related field; English proficiency."
        ),
        compensation_or_fellowship="DAAD EPOS scholarship available for eligible candidates",
        role_summary=(
            "UNU-EHS and the University of Bonn offer a Joint MSc in Geography of "
            "Environmental Risks and Human Security. The programme combines environmental "
            "risk, vulnerability, and human-security research with a master's thesis."
        ),
        key_responsibilities=[
            "Complete advanced coursework in environmental risks",
            "Conduct independent research and a master's thesis",
            "Participate in interdisciplinary seminars and field work",
            "Engage with UNU-EHS research teams",
        ],
        must_have_skills=["Environmental Risk", "Geography", "Research Methods", "English"],
        application_tip=(
            "Applications close 31 October 2026 for the October 2027 intake. Apply through "
            "the UNU-EHS online form and review DAAD EPOS eligibility."
        ),
        apply_url="https://unu.edu/ehs/learning/msc-geography-environmental-risks-and-human-security",
        org_website="https://unu.edu",
        org_domain="unu.edu",
        source_portal="LinkedIn batch - official programme page verified",
        global_=True,
        reverify_after="2026-10-30",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://unu.edu/ehs/learning/msc-geography-environmental-risks-and-human-security",
            "http_status": 200,
        },
    ),
    base_record(
        id="geus-greenland-ice-sheet-hydrology-phd-2027",
        clean_title="PhD in Hydrology and Dynamics of the Greenland Ice Sheet",
        organization="Geological Survey of Denmark and Greenland (GEUS)",
        city="Copenhagen",
        state="",
        country="Denmark",
        region="Europe",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="1 November 2026",
        valid_through="2026-11-01",
        qualification_summary=(
            "Master's degree in hydrology, geophysics, earth sciences, environmental "
            "engineering, or a related field; quantitative and programming skills."
        ),
        compensation_or_fellowship="Salary and employment terms according to the Danish collective agreement",
        role_summary=(
            "GEUS is recruiting a PhD researcher to study the hydrology and dynamics of the "
            "Greenland Ice Sheet. The project combines glaciology, hydrology, and numerical "
            "modelling to understand ice-sheet response to climate change."
        ),
        key_responsibilities=[
            "Analyse glaciological and hydrological data",
            "Develop and run numerical models",
            "Conduct fieldwork where required",
            "Publish research and present at conferences",
        ],
        must_have_skills=["Hydrology", "Glaciology", "Numerical Modelling", "Data Analysis"],
        application_tip=(
            "Apply through the Jobnet posting; deadline 1 November 2026."
        ),
        apply_url="https://jobnet.dk/find-job/a50753a3-48bb-4a5a-8c31-a04968ef86ce",
        org_website="https://www.geus.dk",
        org_domain="geus.dk",
        source_portal="LinkedIn batch - official Jobnet posting verified",
        global_=True,
        reverify_after="2026-10-31",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://jobnet.dk/find-job/a50753a3-48bb-4a5a-8c31-a04968ef86ce",
            "http_status": 200,
        },
    ),
    base_record(
        id="harvard-environmental-fellows-2027",
        clean_title="Environmental Fellows Program 2027",
        organization="Harvard University Center for the Environment",
        city="Cambridge",
        state="Massachusetts",
        country="United States",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="1 December 2026",
        valid_through="2026-12-01",
        qualification_summary=(
            "Recent PhD recipients in environmental fields; interdisciplinary research "
            "proposal and strong academic record."
        ),
        compensation_or_fellowship="Stipend and benefits for a two-year fellowship",
        role_summary=(
            "The Harvard Environmental Fellows Program supports recent PhD recipients "
            "pursuing interdisciplinary environmental research. Fellows join Harvard's "
            "environmental community and work with faculty across the university."
        ),
        key_responsibilities=[
            "Develop an independent interdisciplinary research programme",
            "Collaborate with Harvard faculty and researchers",
            "Communicate research to academic and policy audiences",
            "Participate in the environmental fellows community",
        ],
        must_have_skills=["Environmental Research", "Interdisciplinary Collaboration", "Research Design"],
        application_tip=(
            "Applications close 1 December 2026; review the official program page for "
            "eligibility and application instructions."
        ),
        apply_url="https://www.environment.harvard.edu/environmental-fellows-program",
        org_website="https://www.environment.harvard.edu",
        org_domain="harvard.edu",
        source_portal="LinkedIn batch - official program page verified",
        global_=True,
        reverify_after="2026-11-30",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.environment.harvard.edu/environmental-fellows-program",
            "http_status": 403,
            "bot_blocked": True,
            "note": "Official page returns 403 to automated clients; link is valid in a browser.",
        },
    ),
    base_record(
        id="uea-climate-information-to-climate-action-phd-2027",
        clean_title="PhD - From Climate Information to Climate Action (ARIES)",
        organization="University of East Anglia (UEA)",
        city="Norwich",
        state="",
        country="United Kingdom",
        region="Europe",
        category="Scholarships & Doctoral Support",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="16 December 2026",
        valid_through="2026-12-16",
        qualification_summary=(
            "At least a UK 2:1 honours degree (or equivalent) in environmental science, "
            "geography, climate policy, or a related field; qualitative and quantitative "
            "research skills."
        ),
        compensation_or_fellowship=(
            "Fully funded ARIES studentship: fees, maintenance stipend (£21,805 p.a. for "
            "2026/27), and research training support grant"
        ),
        role_summary=(
            "UEA is recruiting a PhD researcher to examine how climate information shapes "
            "local adaptation decision-making in English local authorities. The project uses "
            "documentary analysis and interviews and collaborates with the UK Met Office."
        ),
        key_responsibilities=[
            "Analyse local authority adaptation strategies and risk registers",
            "Conduct semi-structured interviews with adaptation staff",
            "Apply qualitative coding and thematic analysis",
            "Engage with Met Office climate services and policy stakeholders",
        ],
        must_have_skills=["Climate Adaptation", "Qualitative Research", "Policy Analysis", "Interviewing"],
        application_tip=(
            "Apply through the UEA postgraduate research portal by 16 December 2026. The "
            "project starts 1 October 2027."
        ),
        apply_url=(
            "https://www.uea.ac.uk/course/phd-doctorate/phd-from-climate-information-to-climate-action-"
            "evaluating-how-climate-information-use-shapes-local-adaptation-decision-making-in-english-"
            "local-authorities-and-opportunities-for-improvement-jenkinsueaaries27"
        ),
        org_website="https://www.uea.ac.uk",
        org_domain="uea.ac.uk",
        source_portal="LinkedIn batch - official course page verified",
        global_=True,
        reverify_after="2026-12-15",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": (
                "https://www.uea.ac.uk/course/phd-doctorate/phd-from-climate-information-to-climate-"
                "action-evaluating-how-climate-information-use-shapes-local-adaptation-decision-making-"
                "in-english-local-authorities-and-opportunities-for-improvement-jenkinsueaaries27"
            ),
            "http_status": 200,
        },
    ),
    base_record(
        id="cambridge-interfaith-leverhulme-ecf-2027",
        clean_title="Leverhulme Early Career Fellowship - Peace, Conflict and Religion",
        organization="Cambridge Interfaith Programme, University of Cambridge",
        city="Cambridge",
        state="",
        country="United Kingdom",
        region="Europe",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="30 November 2026",
        valid_through="2026-11-30",
        qualification_summary=(
            "PhD submitted for viva no earlier than 18 February 2023 (or thesis submitted "
            "before 18 February 2027); strong research proposal in peace, conflict, and "
            "religion."
        ),
        compensation_or_fellowship=(
            "Leverhulme Early Career Fellowship (three years), with Faculty of Divinity "
            "match-funding for the successful candidate"
        ),
        role_summary=(
            "The Cambridge Interfaith Programme invites early-career researchers to develop "
            "an independent project on peace, conflict, and religion. Successful candidates "
            "are supported in applying for a three-year Leverhulme Early Career Fellowship."
        ),
        key_responsibilities=[
            "Develop an independent research project",
            "Contribute to CIP's research culture and seminars",
            "Publish research and engage in knowledge exchange",
            "Work with a faculty mentor at the Faculty of Divinity",
        ],
        must_have_skills=["Research Design", "Peace and Conflict Studies", "Religion and Society", "Academic Writing"],
        application_tip=(
            "Submit CV, publications list, research statement, proposal, and two references "
            "to pjh42@cam.ac.uk by 30 November 2026."
        ),
        apply_url="https://www.interfaith.cam.ac.uk/news/funding-opportunity-peace-conflict-and-religion",
        org_website="https://www.interfaith.cam.ac.uk",
        org_domain="cam.ac.uk",
        source_portal="LinkedIn batch - official programme page verified",
        global_=True,
        reverify_after="2026-11-29",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.interfaith.cam.ac.uk/news/funding-opportunity-peace-conflict-and-religion",
            "http_status": 200,
        },
    ),
    base_record(
        id="carboun-institute-head-of-research-2026",
        clean_title="Head of Research",
        organization="Carboun Institute",
        city="Remote",
        state="",
        country="Global",
        region="Africa & Middle East",
        category="Climate Policy, Think-Tanks & Fellowships",
        experience_level="Senior",
        deadline_or_window="Rolling / Open",
        valid_through="2026-12-31",
        qualification_summary=(
            "Advanced degree in energy, climate, economics, engineering, or public policy; "
            "substantial research leadership experience in energy transition and industrial "
            "decarbonization."
        ),
        role_summary=(
            "Carboun Institute is hiring a Head of Research to lead its work on energy "
            "transition and green industry in the MENA region. The role combines applied "
            "research, project oversight, policy advice, and team leadership."
        ),
        key_responsibilities=[
            "Lead applied research on energy transition and industrial decarbonization",
            "Oversee research projects and ensure methodological rigour",
            "Translate findings into policy recommendations",
            "Build partnerships with academia, industry, and policy institutions",
        ],
        must_have_skills=["Energy Transition", "Industrial Decarbonization", "Policy Research", "Research Leadership"],
        application_tip=(
            "Applications are reviewed on a rolling basis until the position is filled. "
            "Apply through the official Carboun careers page."
        ),
        apply_url="https://www.carboun.com/careers/head-of-research",
        org_website="https://www.carboun.com",
        org_domain="carboun.com",
        source_portal="LinkedIn batch - official careers page verified",
        global_=True,
        reverify_after="2026-11-30",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.carboun.com/careers/head-of-research",
            "http_status": 200,
        },
    ),
    base_record(
        id="un-ypp-2026",
        clean_title="UN Young Professionals Programme 2026",
        organization="United Nations",
        city="Various",
        state="",
        country="Global",
        region="UN / Multilateral",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="30 November 2026",
        valid_through="2026-11-30",
        qualification_summary=(
            "Bachelor's degree or higher in a relevant field; nationality of a participating "
            "UN member state; age and language requirements as per the YPP call."
        ),
        compensation_or_fellowship="UN professional salary and benefits",
        role_summary=(
            "The UN Young Professionals Programme is a competitive recruitment programme for "
            "entry-level professionals from participating member states. The 2026 cycle "
            "includes development and sustainability-related examination areas."
        ),
        key_responsibilities=[
            "Prepare for the YPP written examination",
            "Demonstrate analytical and policy competencies",
            "Meet eligibility and nationality requirements",
            "Complete the online application before the deadline",
        ],
        must_have_skills=["Analytical Writing", "Policy Analysis", "International Development", "English or French"],
        application_tip=(
            "Check the official UN YPP page for the 2026 participating countries, exam "
            "subjects, and application window; deadline 30 November 2026."
        ),
        apply_url="https://careers.un.org/ypp/home",
        org_website="https://careers.un.org",
        org_domain="un.org",
        entry_type="careers_portal",
        source_portal="LinkedIn batch - official UN YPP page verified",
        global_=True,
        reverify_after="2026-11-29",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://careers.un.org/ypp/home",
            "http_status": 200,
        },
    ),
    base_record(
        id="university-barcelona-phd-energy-climate-economics-2027",
        clean_title="PhD in Economics - Energy, Climate and Environmental Economics",
        organization="University of Barcelona School of Economics",
        city="Barcelona",
        state="",
        country="Spain",
        region="Europe",
        category="Scholarships & Doctoral Support",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="11 December 2026",
        valid_through="2026-12-11",
        qualification_summary=(
            "Master's degree in economics, environmental economics, energy economics, or a "
            "related field; strong quantitative skills."
        ),
        compensation_or_fellowship="Three-year full-time PhD fellowship (funding details on the official call)",
        role_summary=(
            "The University of Barcelona School of Economics invites expressions of interest "
            "for its PhD in Economics, including research in energy, climate, and "
            "environmental economics. The programme offers a three-year full-time PhD "
            "fellowship starting in September 2027."
        ),
        key_responsibilities=[
            "Develop an independent research agenda in environmental economics",
            "Complete PhD coursework and a doctoral thesis",
            "Present research at seminars and conferences",
            "Collaborate with the Chair of Energy Sustainability and IEB researchers",
        ],
        must_have_skills=["Economics", "Econometrics", "Environmental Economics", "Research Writing"],
        application_tip=(
            "Expressions of interest open 19 October to 11 December 2026 for the 2027-28 "
            "intake. Apply through the UB School of Economics page."
        ),
        apply_url="https://www.ub.edu/school-economics/apply-now-phd/",
        org_website="https://www.ub.edu/school-economics/",
        org_domain="ub.edu",
        source_portal="LinkedIn batch - official school page verified",
        global_=True,
        reverify_after="2026-12-10",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-page",
            "source": "https://www.ub.edu/school-economics/apply-now-phd/",
            "http_status": 200,
        },
    ),
]

# Repair two earlier records that stored a link shortener or an aggregator link.
UPDATES = {
    "phd-students-kotak-school-of-sustainability-iit-kanpur": {
        "clean_title": "PhD Programme - Kotak School of Sustainability, IIT Kanpur",
        "apply_url": "https://www.iitk.ac.in/doaa/pgadmission.htm",
        "entry_type": "careers_portal",
        "deadline_or_window": "3 November 2026",
        "valid_through": "2026-11-03",
        "reverify_after": "2026-11-02",
        "org_website": "https://iitk.ac.in/kss/",
        "org_domain": "iitk.ac.in",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://www.iitk.ac.in/doaa/pgadmission.htm",
            "http_status": 200,
        },
    },
    "project-associate-assistant-wii": {
        "clean_title": "Project Associate, Project Assistant and Other Project Posts (19 Posts)",
        "country": "India",
        "employment_type": "CONTRACTOR",
        "apply_url": "https://wii.gov.in/recruitments",
        "entry_type": "careers_portal",
        "deadline_or_window": "1 November 2026",
        "valid_through": "2026-11-01",
        "reverify_after": "2026-10-31",
        "org_website": "https://wii.gov.in",
        "org_domain": "wii.gov.in",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-official-portal",
            "source": "https://wii.gov.in/recruitments",
            "http_status": 200,
        },
    },
    "cornell-forest-restoration-ecology-phd-2027": {
        "entry_type": "careers_portal",
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
    # The base_record helper accepts global_ to avoid the Python keyword; normalise it.
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
