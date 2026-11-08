"""Add the 8 November 2026 LinkedIn batch (India + global).

Source: the owner's LinkedIn feed, LinkedIn Jobs keyword searches (past
week, India) and the owner's LinkedIn scholarship/grant posts, gathered
through the owner's browser on 8 November 2026.

Rules applied (docs/LINK_POLICY.md v2):
- apply_url is always taken from the source. LinkedIn is bot-blocked, so
  records are kept as UNKNOWN_KEEP and validated by URL pattern only.
- Only /jobs/view/<id> counts as a direct LinkedIn link; company and
  profile pages are published as entry_type "careers_portal".
- Shorteners (lnkd.in, b3th-energy.com, heyor.ca, ow.ly) were resolved in
  the browser before publishing.
- Facts come only from the listing/post headers. Undisclosed fields stay
  blank; no JD, qualification, skill or salary is invented.
- Posts whose deadline has already passed go to the archive registry.

Run from the repository root:
    py scripts/add_manual_batch_2026_11_08_linkedin.py
The script is idempotent: existing ids and apply_urls are left untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"
GLOBAL_PATH = ROOT / "public" / "global_jobs.json"
ARCHIVE_PATH = ROOT / "public" / "archive.json"
GLOBAL_ARCHIVE_PATH = ROOT / "public" / "global_archive.json"

VERIFIED_AT = "2026-11-08"
SOURCE_JOBS = "LinkedIn Jobs - India climate/forestry/environment search (owner-shared)"
SOURCE_FEED = "LinkedIn feed post (owner-shared)"


def base_record(**overrides):
    record = {
        "id": "",
        "clean_title": "",
        "organization": "",
        "city": "",
        "state": "",
        "country": "India",
        "region": "",
        "category": "",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "experience_level": "",
        "employment_type": "FULL_TIME",
        "deadline_or_window": "Rolling / Open",
        "valid_through": "2026-12-08",
        "qualification_summary": "",
        "compensation_or_fellowship": "Not disclosed - see official job description",
        "role_summary": "",
        "key_responsibilities": [],
        "must_have_skills": [],
        "application_tip": "See the official job page for full responsibilities and requirements.",
        "apply_url": "",
        "org_website": "",
        "org_domain": "",
        "source_portal": SOURCE_JOBS,
        "entry_type": "posting",
        "status": "active",
        "global": False,
        "evergreen": False,
        "date_added": VERIFIED_AT,
        "date_posted": VERIFIED_AT,
        "title_hi": "",
        "summary_hi": "",
        "academic_meta": {},
        "selection_process": "",
        "reverify_after": "2026-11-23",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-verified",
            "source": "LinkedIn listing (owner-shared)",
            "http_status": "UNKNOWN_KEEP",
        },
    }
    record.update(overrides)
    return record


def li(job_id: str) -> str:
    return f"https://www.linkedin.com/jobs/view/{job_id}"


def role(title: str, org: str, place: str, view: str = "LinkedIn") -> str:
    return (
        f"{title} role at {org}, {place}. Full responsibilities and "
        f"requirements are on the {view} page."
    )


def india_job(job_id, id_, title, org, city, state, category, exp,
              website="", position_type="Full-Time Corporate / NGO", extra=None):
    rec = base_record(
        id=id_,
        clean_title=title,
        organization=org,
        city=city,
        state=state,
        category=category,
        experience_level=exp,
        position_type=position_type,
        role_summary=role(title, org, city),
        apply_url=li(job_id),
        org_website=website,
        org_domain=website.replace("https://", "").replace("http://", "").split("/")[0] if website else "",
    )
    if extra:
        rec.update(extra)
    return rec


INDIA_RECORDS = [
    # --- LinkedIn feed: Berhampur University ecology project ---
    base_record(
        id="berhampur-university-research-associate-ecology-2026",
        clean_title="Research Associate (Ecology)",
        organization="Berhampur University",
        city="Berhampur",
        state="Odisha",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="Research / Academic (Contractual)",
        experience_level="1-3 Years",
        deadline_or_window="Rolling / Open",
        qualification_summary="Master's degree in Ecology, Environmental Science or a related field (as advertised).",
        compensation_or_fellowship="Rs. 47,000 per month (consolidated)",
        role_summary="Research associate on a three-year project assessing regional stochasticity and blackbuck population distribution in Odisha.",
        apply_url="mailto:bakp.evs@buodisha.edu.in",
        org_website="https://buodisha.edu.in",
        org_domain="buodisha.edu.in",
        source_portal=SOURCE_FEED,
        application_tip="Email your CV to the address in the notice.",
    ),
    base_record(
        id="berhampur-university-project-associate-ecology-2026",
        clean_title="Project Associate (Ecology)",
        organization="Berhampur University",
        city="Berhampur",
        state="Odisha",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Research / Academic (Contractual)",
        experience_level="1-3 Years",
        deadline_or_window="Rolling / Open",
        qualification_summary="Master's degree in Ecology, Environmental Science or a related field (as advertised).",
        compensation_or_fellowship="Rs. 30,000 per month (consolidated)",
        role_summary="Project associate on a three-year project assessing regional stochasticity and blackbuck population distribution in Odisha.",
        apply_url="mailto:bakp.evs@buodisha.edu.in",
        org_website="https://buodisha.edu.in",
        org_domain="buodisha.edu.in",
        source_portal=SOURCE_FEED,
        application_tip="Email your CV to the address in the notice.",
    ),
    base_record(
        id="berhampur-university-field-investigator-ecology-2026",
        clean_title="Field Investigator (Ecology)",
        organization="Berhampur University",
        city="Berhampur",
        state="Odisha",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Research / Academic (Contractual)",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="Rolling / Open",
        qualification_summary="Bachelor's degree in Ecology, Environmental Science or a related field (as advertised).",
        compensation_or_fellowship="Rs. 20,000 per month (consolidated)",
        role_summary="Field investigator on a three-year project assessing regional stochasticity and blackbuck population distribution in Odisha.",
        apply_url="mailto:bakp.evs@buodisha.edu.in",
        org_website="https://buodisha.edu.in",
        org_domain="buodisha.edu.in",
        source_portal=SOURCE_FEED,
        application_tip="Email your CV to the address in the notice.",
    ),
    # --- LinkedIn feed: NIH Roorkee young professionals ---
    base_record(
        id="nih-roorkee-young-professional-full-stack-2026",
        clean_title="Young Professional - Full Stack Development",
        organization="National Institute of Hydrology (NIH)",
        city="Roorkee",
        state="Uttarakhand",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Young Professional / Consultant (Contractual)",
        experience_level="Entry Level / Fellowship",
        employment_type="CONTRACTOR",
        deadline_or_window="Walk-in 13 November 2026",
        valid_through="2026-11-13",
        qualification_summary="Bachelor's in Computer Science / IT / Computer Applications (as advertised).",
        compensation_or_fellowship="Rs. 55,000 per month",
        role_summary="Full stack development and database management for the Bharat WIN portal and mobile apps at NIH Roorkee.",
        apply_url="https://www.nihroorkee.gov.in/job26102026.pdf",
        org_website="https://nihroorkee.gov.in",
        org_domain="nihroorkee.gov.in",
        source_portal=SOURCE_FEED,
        application_tip="Walk-in interview on 13 November 2026; see the official notice PDF.",
    ),
    base_record(
        id="nih-roorkee-young-professional-social-media-2026",
        clean_title="Young Professional - Social Media & Digital Content",
        organization="National Institute of Hydrology (NIH)",
        city="Roorkee",
        state="Uttarakhand",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Young Professional / Consultant (Contractual)",
        experience_level="Entry Level / Fellowship",
        employment_type="CONTRACTOR",
        deadline_or_window="Walk-in 13 November 2026",
        valid_through="2026-11-13",
        qualification_summary="Bachelor's in Mass Communication, Journalism, Digital Media or Graphic Design (as advertised).",
        compensation_or_fellowship="Rs. 55,000 per month",
        role_summary="Social media and digital content management for NIH Roorkee, including graphics, videos and presentations.",
        apply_url="https://www.nihroorkee.gov.in/job26102026.pdf",
        org_website="https://nihroorkee.gov.in",
        org_domain="nihroorkee.gov.in",
        source_portal=SOURCE_FEED,
        application_tip="Walk-in interview on 13 November 2026; see the official notice PDF.",
    ),
    # --- LinkedIn Jobs search, past week, India ---
    base_record(
        id="flora-carbon-nature-based-carbon-project-lead-kolkata-2026",
        clean_title="Nature-Based Carbon Project Lead (NBS)",
        organization="Flora Carbon AI",
        city="Kolkata",
        state="West Bengal",
        category="ESG, Carbon Markets & Corporate Sustainability",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary=role("Nature-based carbon project lead", "Flora Carbon AI", "Kolkata"),
        apply_url="https://floracarbon.ai/resources/careers/",
        org_website="https://floracarbon.ai",
        org_domain="floracarbon.ai",
        entry_type="careers_portal",
        application_tip="Apply through the Flora Carbon AI careers page.",
    ),
    india_job(
        "4486668339", "acg-capsules-manager-environment-sustainability-kandivali-2026",
        "Manager - Environment & Sustainability", "ACG Capsules", "Kandivali", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.acg-world.com",
    ),
    base_record(
        id="joblet-ai-scientific-computing-specialist-remote-2026",
        clean_title="Scientific Computing Specialist (Remote)",
        organization="Joblet-AI",
        city="Remote",
        state="Multiple States / Remote",
        category="GIS, Remote Sensing & Earth Observation",
        experience_level="1-3 Years",
        role_summary=role("Scientific computing specialist (remote)", "Joblet-AI", "India (remote)"),
        apply_url="https://www.linkedin.com/company/joblet-ai/jobs/",
        org_website="https://www.linkedin.com/company/joblet-ai",
        org_domain="linkedin.com",
        entry_type="careers_portal",
        application_tip="Browse the Joblet-AI jobs page for the live posting.",
    ),
    base_record(
        id="joblet-ai-stem-specialist-remote-2026",
        clean_title="STEM Specialist (Remote)",
        organization="Joblet-AI",
        city="Remote",
        state="Multiple States / Remote",
        category="GIS, Remote Sensing & Earth Observation",
        experience_level="Entry Level / Fellowship",
        role_summary=role("STEM specialist (remote)", "Joblet-AI", "India (remote)"),
        apply_url="https://www.linkedin.com/company/joblet-ai/jobs/",
        org_website="https://www.linkedin.com/company/joblet-ai",
        org_domain="linkedin.com",
        entry_type="careers_portal",
        application_tip="Browse the Joblet-AI jobs page for the live posting.",
    ),
    india_job(
        "4461978339", "burns-mcdonnell-gis-analyst-mumbai-2026",
        "GIS Analyst (Mumbai/Bengaluru) - ENS", "Burns & McDonnell India", "Mumbai", "Maharashtra",
        "GIS, Remote Sensing & Earth Observation", "1-3 Years",
        "https://www.burnsmcd.com",
    ),
    india_job(
        "4461996296", "wsp-india-system-analyst-mumbai-2026",
        "System Analyst - Power BI/Python/VBA/R", "WSP in India", "Mumbai", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4461994567", "wsp-india-system-analyst-noida-2026",
        "System Analyst - Power BI/Python/VBA/R", "WSP in India", "Noida", "Uttar Pradesh",
        "ESG, Carbon Markets & Corporate Sustainability", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4470314542", "wsp-india-associate-carbon-net-zero-mumbai-2026",
        "Associate - Carbon & Net Zero", "WSP in India", "Mumbai", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4480812620", "adani-natural-resources-assistant-manager-horticulture-2026",
        "Assistant Manager - Horticulture", "Adani Natural Resources", "Ahmedabad", "Gujarat",
        "Forestry, Wildlife & Afforestation", "1-3 Years",
        "https://www.adanienterprises.com",
    ),
    base_record(
        id="pragathi-labs-environmental-engineer-hyderabad-2026",
        clean_title="Environmental Engineer",
        organization="PRAGATHI LABS AND CONSULTANTS",
        city="Hyderabad",
        state="Telangana",
        category="ESG, Carbon Markets & Corporate Sustainability",
        experience_level="Entry Level / Fellowship",
        role_summary=role("Environmental engineer", "Pragathi Labs and Consultants", "Hyderabad"),
        apply_url="https://www.pragathilabs.com/",
        org_website="https://www.pragathilabs.com",
        org_domain="pragathilabs.com",
        entry_type="careers_portal",
        application_tip="Send your CV to info@pragathilabs.com as listed on the careers page.",
    ),
    india_job(
        "4460783220", "ey-senior-project-consultant-delhi-2026",
        "Senior Project Consultant - Business Consulting (GOV-CNS-BC-Transformation Delivery)",
        "EY", "New Delhi", "Delhi",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.ey.com/en_in",
    ),
    india_job(
        "4472284064", "adani-natural-resources-assistant-manager-environment-2026",
        "Assistant Manager - Environment", "Adani Natural Resources", "Ahmedabad", "Gujarat",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.adanienterprises.com",
    ),
    india_job(
        "4452371621", "wsp-india-senior-engineer-carbon-management-roads-mumbai-2026",
        "Senior Engineer - Carbon Management (Roads)", "WSP in India", "Mumbai", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4452372650", "wsp-india-senior-engineer-carbon-management-roads-noida-2026",
        "Senior Engineer - Carbon Management (Roads)", "WSP in India", "Noida", "Uttar Pradesh",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4470075951", "wsp-india-engineer-hydraulic-modelling-bengaluru-2026",
        "Engineer - Hydraulic Modelling", "WSP in India", "Bengaluru", "Karnataka",
        "GIS, Remote Sensing & Earth Observation", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4480516769", "avantor-analyst-sustainable-sourcing-coimbatore-2026",
        "Analyst - Sustainable Sourcing", "Avantor", "Coimbatore", "Tamil Nadu",
        "ESG, Carbon Markets & Corporate Sustainability", "Entry Level / Fellowship",
        "https://www.avantor.com",
    ),
    india_job(
        "4480516768", "avantor-analyst-sustainable-sourcing-pune-2026",
        "Analyst - Sustainable Sourcing", "Avantor", "Pune", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "Entry Level / Fellowship",
        "https://www.avantor.com",
    ),
    india_job(
        "4463368444", "aditya-birla-capital-team-member-esg-2026",
        "Team Member - ESG", "Aditya Birla Capital", "Mumbai", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "Entry Level / Fellowship",
        "https://www.adityabirlacapital.com",
    ),
    india_job(
        "4486584235", "novarch-landscape-architect-junior-new-delhi-2026",
        "Landscape Architect (Junior)", "NOVARCH CONSULTANTS", "New Delhi", "Delhi",
        "Forestry, Wildlife & Afforestation", "Entry Level / Fellowship",
    ),
    india_job(
        "4488486589", "aditya-birla-group-front-line-officer-etp-rishra-2026",
        "Front Line Officer - ETP Operations", "Aditya Birla Group", "Rishra", "West Bengal",
        "ESG, Carbon Markets & Corporate Sustainability", "Entry Level / Fellowship",
        "https://www.adityabirlacapital.com",
    ),
    india_job(
        "4470127804", "wri-india-intern-electric-mobility-bengaluru-2026",
        "Intern - Electric Mobility", "WRI India", "Bengaluru", "Karnataka",
        "Internships & Student Traineeships", "Entry Level / Fellowship",
        "https://wri-india.org",
        position_type="Internship",
        extra={"opportunity_kind": "Internship", "employment_type": "INTERN"},
    ),
    india_job(
        "4453102081", "engie-india-manager-om-bap-2026",
        "Manager - O&M", "ENGIE India", "Bap", "Rajasthan",
        "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
        "https://www.engie.com",
    ),
    india_job(
        "4470322096", "wsp-india-renewable-energy-systems-engineer-bengaluru-2026",
        "Renewable Energy Systems Engineer", "WSP in India", "Bengaluru", "Karnataka",
        "ESG, Carbon Markets & Corporate Sustainability", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
    india_job(
        "4470301959", "wsp-india-renewable-energy-systems-engineer-mumbai-2026",
        "Renewable Energy Systems Engineer", "WSP in India", "Mumbai", "Maharashtra",
        "ESG, Carbon Markets & Corporate Sustainability", "1-3 Years",
        "https://www.wsp.com/en-in",
    ),
]


def global_record(**overrides):
    rec = base_record(**overrides)
    rec["global"] = True
    rec.setdefault("date_posted", rec["date_added"])
    return rec


GLOBAL_RECORDS = [
    global_record(
        id="iasc-fellowship-programme-2027",
        clean_title="IASC Fellowship Programme 2027",
        organization="International Arctic Science Committee (IASC)",
        city="Remote",
        state="",
        country="International",
        region="Global",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="2027 programme (see notice)",
        qualification_summary="Early-career researchers working on Arctic science themes.",
        compensation_or_fellowship="Not disclosed - see official notice",
        role_summary="Ten fellowship places for early-career researchers in the IASC Fellowship Programme 2027.",
        apply_url="https://opportunitiesfeed.com/2026/10/28/fellowship-program-5/",
        org_website="https://iasc.info",
        org_domain="iasc.info",
        source_portal="LinkedIn post (IASC)",
        application_tip="See the fellowship notice for themes, eligibility and the application form.",
    ),
    global_record(
        id="care-climate-resilience-academy-2026",
        clean_title="CARE Climate & Resilience Academy",
        organization="CARE",
        city="Online",
        state="",
        country="International",
        region="Global",
        category="Workshops, Training & Capacity Building",
        position_type="Course",
        opportunity_kind="Course",
        experience_level="All Levels",
        deadline_or_window="Rolling / Open",
        qualification_summary="Open to humanitarian and development professionals.",
        compensation_or_fellowship="Free",
        role_summary="Free online courses on climate change, resilience and humanitarian-development practice.",
        apply_url="https://vacancybridge.com/online-courses/care-climate-resilience-academy/",
        org_website="https://www.care.org",
        org_domain="care.org",
        source_portal="LinkedIn post (CARE)",
        application_tip="Enrol through the course page.",
    ),
    global_record(
        id="song-masters-scholarships-papua-new-guinea-2026",
        clean_title="SONG Masters Scholarships",
        organization="EU-FCCB Programme / Expertise France",
        city="Port Moresby",
        state="",
        country="Papua New Guinea",
        region="Oceania",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="13 November 2026",
        valid_through="2026-11-13",
        qualification_summary="Postgraduate study in marine/freshwater/terrestrial ecology, climate change, sustainable forestry, agroforestry, environmental economics or ethnobiology.",
        compensation_or_fellowship="EUR 20,000 personal scholarship plus EUR 20,000 research grant",
        role_summary="Seventeen fully funded postgraduate scholarships (MPhil, MSc by research) at Papua New Guinea universities, starting 2027.",
        apply_url="mailto:songscholarships@gmail.com",
        org_website="https://www.expertisefrance.fr",
        org_domain="expertisefrance.fr",
        source_portal="LinkedIn post (EU-FCCB Programme)",
        application_tip="Apply by email following the scholarship notice.",
    ),
    global_record(
        id="asprs-geospatial-research-grant-2027",
        clean_title="ASPRS Geospatial Research Grant 2027",
        organization="American Society for Photogrammetry and Remote Sensing (ASPRS)",
        city="Remote",
        state="",
        country="United States",
        region="North America",
        category="Grants & Research Funding",
        position_type="Grant / Funding",
        opportunity_kind="Grant / Funding",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="Applications 1 December 2026; recommendations 22 December 2026",
        valid_through="2026-12-01",
        qualification_summary="Graduate students in geospatial sciences; preference for PhD students planning teaching careers.",
        compensation_or_fellowship="USD 25,000 one-year grant",
        role_summary="Research grant for graduate students in the geospatial sciences.",
        apply_url="https://www.asprs.org/Main/Education---Careers/ASPRS-Awards-and-Scholarships.aspx",
        org_website="https://www.asprs.org",
        org_domain="asprs.org",
        source_portal="LinkedIn post (ASPRS)",
        entry_type="careers_portal",
        application_tip="Apply through the ASPRS awards and scholarships page.",
    ),
    global_record(
        id="truman-picard-scholarship-2027",
        clean_title="Truman D. Picard Scholarship 2027",
        organization="Intertribal Timber Council",
        city="Remote",
        state="",
        country="United States",
        region="North America",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="November 2026",
        valid_through="2026-11-30",
        qualification_summary="Native American or Alaska Native students in natural resources, forestry or fire programmes.",
        compensation_or_fellowship="USD 4,000 (forestry/fire) or USD 3,000 (natural resources)",
        role_summary="Scholarship for Native American and Alaska Native students, with preference for forestry or fire majors.",
        apply_url="https://www.linkedin.com/company/intertribal-timber-council/jobs/",
        org_website="https://www.intertribaltimber.org",
        org_domain="intertribaltimber.org",
        source_portal="LinkedIn post (Intertribal Timber Council)",
        entry_type="careers_portal",
        application_tip="See the Intertribal Timber Council page for the application form.",
    ),
    global_record(
        id="obrien-foundation-fellowship-2026",
        clean_title="O'Brien Foundation Fellowship 2026",
        organization="O'Brien Foundation",
        city="Remote",
        state="",
        country="Canada",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship",
        opportunity_kind="Fellowship",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="1 December 2026",
        valid_through="2026-12-01",
        qualification_summary="Graduate students and researchers with New Brunswick connections pursuing advanced research-based study.",
        compensation_or_fellowship="CAD 5,000-15,000",
        role_summary="Fellowship for New Brunswick residents pursuing advanced research-based study at any institution worldwide.",
        apply_url="https://www.linkedin.com/company/unb-forestry-environmental-management/jobs/",
        org_website="https://www.obrienfoundation.ca",
        org_domain="obrienfoundation.ca",
        source_portal="LinkedIn post (UNB Forestry)",
        entry_type="careers_portal",
        application_tip="See the O'Brien Foundation notice for the application form.",
    ),
    global_record(
        id="ubc-master-international-forestry-tuition-scholarship-2026",
        clean_title="UBC Master of International Forestry Tuition Scholarship",
        organization="University of British Columbia",
        city="Vancouver",
        state="British Columbia",
        country="Canada",
        region="North America",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="Rolling / Open",
        qualification_summary="International students entering the Master of International Forestry programme.",
        compensation_or_fellowship="Tuition scholarship",
        role_summary="Tuition scholarship for the UBC Master of International Forestry programme.",
        apply_url="https://forestry.ubc.ca/future-students/graduate/professional-masters-degrees/master-of-international-forestry/tuition-funding/",
        org_website="https://forestry.ubc.ca",
        org_domain="forestry.ubc.ca",
        source_portal="LinkedIn post (UBC Forestry)",
        entry_type="award_portal",
        application_tip="See the UBC tuition-funding page for eligibility and how to apply.",
    ),
    global_record(
        id="gottstein-trust-skill-development-grants-2026",
        clean_title="Gottstein Trust Skill Development Grants, Fellowships & Scholarships",
        organization="Gottstein Trust",
        city="Remote",
        state="",
        country="Australia",
        region="Oceania",
        category="Grants & Research Funding",
        position_type="Grant / Funding",
        opportunity_kind="Grant / Funding",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="Rolling / Open",
        qualification_summary="Forestry, timber and forest-research professionals seeking skill development.",
        compensation_or_fellowship="Not disclosed - see official page",
        role_summary="Skill-development grants, fellowships and scholarships for forestry and timber professionals.",
        apply_url="https://gottsteintrust.org/grants-courses/",
        org_website="https://gottsteintrust.org",
        org_domain="gottsteintrust.org",
        source_portal="LinkedIn post (Gottstein Trust)",
        entry_type="careers_portal",
        application_tip="Browse the grants and courses page for the current round.",
    ),
    global_record(
        id="us-endowment-forestry-communities-rfp-2026",
        clean_title="U.S. Endowment for Forestry & Communities RFP",
        organization="U.S. Endowment for Forestry and Communities",
        city="Remote",
        state="",
        country="United States",
        region="North America",
        category="Grants & Research Funding",
        position_type="Grant / Funding",
        opportunity_kind="Grant / Funding",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="16 November 2026",
        valid_through="2026-11-16",
        qualification_summary="Organisations with strong regional relationships and experience in forestry, forest products or rural economic development.",
        compensation_or_fellowship="Up to USD 5 million anchor investment",
        role_summary="RFP for organisations supporting low-value, small-diameter and residual wood fibre initiatives.",
        apply_url="https://www.usendowment.org/u-s-endowment-opens-funding-opportunity-to-strengthen-regional-wood-fiber-markets/",
        org_website="https://www.usendowment.org",
        org_domain="usendowment.org",
        source_portal="LinkedIn post (U.S. Endowment)",
        application_tip="Read the RFP announcement for eligibility and submission details.",
    ),
    global_record(
        id="unb-mscf-black-spruce-stress-resilience-2026",
        clean_title="UNB MScF Opportunity - Black Spruce Stress Resilience",
        organization="University of New Brunswick",
        city="Fredericton",
        state="New Brunswick",
        country="Canada",
        region="North America",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Job / Career",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="30 November 2026",
        valid_through="2026-11-30",
        qualification_summary="Graduate student in plant science, remote sensing or geomatics.",
        compensation_or_fellowship="As per university norms",
        role_summary="High-throughput phenotyping of black spruce stress resilience, combining greenhouse data collection, remote sensing and geomatics.",
        apply_url="https://www.unb.ca/forestry/",
        org_website="https://www.unb.ca/forestry/",
        org_domain="unb.ca",
        source_portal="LinkedIn post (UNB Forestry)",
        entry_type="careers_portal",
        application_tip="Contact the UNB Faculty of Forestry with the subject line from the post.",
    ),
    global_record(
        id="cop31-delegate-accreditation-cose-2026",
        clean_title="COP31 Delegate Accreditation",
        organization="Circle of Sustainable Europe (CoSE)",
        city="Antalya",
        state="",
        country="Türkiye",
        region="Europe",
        category="Conferences, Summits & Events",
        position_type="Opportunity",
        opportunity_kind="Opportunity",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="9-20 November 2026",
        valid_through="2026-11-20",
        qualification_summary="Young people and sustainability advocates active in climate action.",
        compensation_or_fellowship="Observer access badges (three delegates selected)",
        role_summary="Observer accreditation for COP31 in Antalya, Türkiye.",
        apply_url="https://opportunitytracker.ug/opportunity/call-for-delegates-apply-for-the-cop31-climate-conference-accreditation-badge-to-attend-cop31-in-antalya-turkiye-2026/",
        org_website="https://www.cos-europe.org",
        org_domain="cos-europe.org",
        source_portal="LinkedIn post (CoSE)",
        application_tip="Follow the call for delegates and apply before the stated deadline.",
    ),
    global_record(
        id="msu-forest-carbon-short-courses-2026",
        clean_title="MSU Forest Carbon Short Courses",
        organization="Michigan State University",
        city="Online",
        state="",
        country="United States",
        region="North America",
        category="Workshops, Training & Capacity Building",
        position_type="Course",
        opportunity_kind="Course",
        experience_level="All Levels",
        deadline_or_window="Register by 10 November 2026",
        valid_through="2026-11-10",
        qualification_summary="Open to forestry professionals and students.",
        compensation_or_fellowship="Free with CFEs available; USD 175 for SAF members, USD 220 for non-members",
        role_summary="Two online courses: Forest Carbon Markets and Initiatives, and Physical Science of Forests, Climate Regulation and Carbon Storage.",
        apply_url="https://learn.eforester.org/MSU-offerings",
        org_website="https://www.canr.msu.edu/fccp",
        org_domain="canr.msu.edu",
        source_portal="LinkedIn post (MSU FCCP)",
        application_tip="Register through the MSU course listing.",
    ),
    global_record(
        id="fao-climate-natural-resources-jobs-2026",
        clean_title="FAO Climate & Natural Resources Positions",
        organization="Food and Agriculture Organization (FAO)",
        city="Multiple duty stations",
        state="",
        country="International",
        region="Global",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        opportunity_kind="Job / Career",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="Various deadlines, 4-26 November 2026",
        valid_through="2026-11-26",
        qualification_summary="Varies by position (GIS/MRV, climate capacity, GCF specialist).",
        compensation_or_fellowship="Not disclosed - see FAO vacancy",
        role_summary="Multiple FAO vacancies in climate and natural resources, including GIS/MRV, climate capacity and GCF specialist roles.",
        apply_url="https://jobs.fao.org/careersection/fao_external/jobdetail.ftl?job=2602183",
        org_website="https://www.fao.org",
        org_domain="fao.org",
        source_portal="LinkedIn post (FAO)",
        application_tip="Open the FAO vacancy and check the closing date before applying.",
    ),
    global_record(
        id="georgia-rise-usda-forest-service",
        clean_title="Georgia RISE - Forest Markets Programme",
        organization="USDA Forest Service / Georgia Tech",
        city="Georgia",
        state="Georgia",
        country="United States",
        region="North America",
        category="Forestry, Wildlife & Afforestation",
        position_type="Programme",
        opportunity_kind="Opportunity",
        experience_level="All Levels",
        deadline_or_window="Rolling / Open",
        qualification_summary="Private forest landowners interested in carbon, water and biodiversity markets.",
        compensation_or_fellowship="Not disclosed - see programme page",
        role_summary="Programme connecting private forest landowners with carbon, water and biodiversity market opportunities.",
        apply_url="https://www.linkedin.com/in/joan-scales-82a02514",
        org_website="https://www.fs.usda.gov",
        org_domain="fs.usda.gov",
        source_portal="LinkedIn post (Georgia RISE)",
        entry_type="careers_portal",
        application_tip="Contact the programme lead listed in the post.",
    ),
]


GLOBAL_ARCHIVE_RECORDS = [
    global_record(
        id="acla-water-youth-climate-webinar-2026",
        clean_title="Water & Youth Climate Webinar",
        organization="Africa Climate Leadership Academy (ACLA)",
        city="Online",
        state="",
        country="International",
        region="Global",
        category="Workshops, Training & Capacity Building",
        position_type="Webinar",
        opportunity_kind="Webinar",
        experience_level="All Levels",
        deadline_or_window="5 November 2026",
        valid_through="2026-11-05",
        qualification_summary="Young people, climate advocates and WASH practitioners.",
        compensation_or_fellowship="Free",
        role_summary="Webinar on El Nino effects on communities and how youth can respond.",
        apply_url="https://us02web.zoom.us/meeting/register/J8CKuyZST1Sr60ZNbLaNzw",
        org_website="https://www.linkedin.com/company/africa-climate-leadership-academy",
        org_domain="linkedin.com",
        source_portal="LinkedIn post (ACLA)",
    ),
    global_record(
        id="neapms-student-scholarships-2026",
        clean_title="NEAPMS Student Travel & Graduate Scholarships",
        organization="Northeast Aquatic Plant Management Society (NEAPMS)",
        city="Remote",
        state="",
        country="United States",
        region="North America",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="1 November 2026",
        valid_through="2026-11-01",
        qualification_summary="Students researching aquatic plants.",
        compensation_or_fellowship="USD 250 travel awards (four) and a USD 10,000 graduate scholarship",
        role_summary="Student travel awards and a graduate scholarship for aquatic plant research.",
        apply_url="https://www.neapms.org/graduate-scholarships",
        org_website="https://www.neapms.org",
        org_domain="neapms.org",
        source_portal="LinkedIn post (NEAPMS)",
    ),
    global_record(
        id="mastercard-foundation-scholars-cambridge-2027",
        clean_title="Mastercard Foundation Scholars Program (Cambridge) 2027",
        organization="University of Cambridge",
        city="Cambridge",
        state="",
        country="United Kingdom",
        region="Europe",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="19 October 2026",
        valid_through="2026-10-19",
        qualification_summary="Talented young Africans committed to climate resilience and sustainability.",
        compensation_or_fellowship="Fully funded master's degree",
        role_summary="Fully funded master's programme for young Africans, with a climate resilience and sustainability theme.",
        apply_url="https://www.linkedin.com/in/idris-ayab",
        org_website="https://www.cam.ac.uk",
        org_domain="cam.ac.uk",
        source_portal="LinkedIn post (Mastercard Foundation)",
        entry_type="careers_portal",
    ),
    global_record(
        id="ubc-chisholm-scholarship-forestry",
        clean_title="Hugh Robert Duncan Chisholm Scholarship in Forestry",
        organization="University of British Columbia",
        city="Vancouver",
        state="British Columbia",
        country="Canada",
        region="North America",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="September 2025",
        valid_through="2025-09-30",
        qualification_summary="Forestry students at UBC.",
        compensation_or_fellowship="Not disclosed - see scholarship guidelines",
        role_summary="Endowed scholarship for students in the UBC Faculty of Forestry.",
        apply_url="https://www.linkedin.com/in/choi-lam-wong-3a5681306",
        org_website="https://forestry.ubc.ca",
        org_domain="forestry.ubc.ca",
        source_portal="LinkedIn post (UBC Forestry)",
        entry_type="careers_portal",
    ),
    global_record(
        id="coillte-forestry-scholarship-ireland",
        clean_title="Coillte Forestry Scholarship",
        organization="Coillte",
        city="Dublin",
        state="",
        country="Ireland",
        region="Europe",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="Extended to 6 July 2026",
        valid_through="2026-07-06",
        qualification_summary="Leaving Certificate and mature students enrolling in forestry degrees at UCD or SETU.",
        compensation_or_fellowship="Up to EUR 20,000 per student",
        role_summary="Scholarship supporting careers in Ireland's forestry sector.",
        apply_url="https://ie.linkedin.com/company/coillte/jobs/",
        org_website="https://www.coillte.ie",
        org_domain="coillte.ie",
        source_portal="LinkedIn post (Coillte)",
        entry_type="careers_portal",
    ),
    global_record(
        id="labstart-2027-fellowship",
        clean_title="LabStart 2027 Fellowship",
        organization="LabStart / Breakthrough Energy Fellows",
        city="Remote",
        state="",
        country="United States",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship",
        opportunity_kind="Fellowship",
        experience_level="Mid-Senior (3-6 Years)",
        deadline_or_window="2 November 2026",
        valid_through="2026-11-02",
        qualification_summary="Entrepreneurs ready to commercialise breakthrough climate technologies.",
        compensation_or_fellowship="USD 6,000 (Discover phase) to USD 125,000 (Launch phase)",
        role_summary="Fellowship supporting entrepreneurs commercialising breakthrough climate technologies.",
        apply_url="https://apply.breakthroughenergy.org/",
        org_website="https://www.labstart.org",
        org_domain="labstart.org",
        source_portal="LinkedIn post (LabStart)",
        entry_type="careers_portal",
    ),
    global_record(
        id="domtar-award-indspire-2026",
        clean_title="Domtar Award (Indspire) 2026",
        organization="Domtar / Indspire",
        city="Remote",
        state="",
        country="Canada",
        region="North America",
        category="Scholarships & Doctoral Support",
        position_type="Scholarship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="1 November 2026",
        valid_through="2026-11-01",
        qualification_summary="Indigenous students in forestry-related, engineering, trade and apprenticeship programmes.",
        compensation_or_fellowship="As per Indspire guidelines",
        role_summary="Financial award for Indigenous students in forestry-related programmes.",
        apply_url="https://indspirefunding.ca/domtar/",
        org_website="https://indspire.ca",
        org_domain="indspire.ca",
        source_portal="LinkedIn post (Domtar)",
    ),
    global_record(
        id="regenerate-new-york-forestry-cost-share-grant-2026",
        clean_title="Regenerate New York Forestry Cost Share Grant (Round 5)",
        organization="New York State Department of Environmental Conservation",
        city="New York",
        state="New York",
        country="United States",
        region="North America",
        category="Grants & Research Funding",
        position_type="Grant / Funding",
        opportunity_kind="Grant / Funding",
        experience_level="All Levels",
        deadline_or_window="31 August 2026",
        valid_through="2026-08-31",
        qualification_summary="Private landowners, land trusts, non-profits, Tribes and forestry partners.",
        compensation_or_fellowship="Cost-share funding",
        role_summary="Funding to restore and establish healthy, resilient forests on private land.",
        apply_url="https://dec.ny.gov/nature/forests-trees/private-forest-management/regenerate-new-york-grant-program",
        org_website="https://dec.ny.gov",
        org_domain="dec.ny.gov",
        source_portal="LinkedIn post (NYS DEC)",
    ),
]


POSITION_MAP = {
    "Research / Academic (Contractual)": "Project Associate / Research Associate",
    "Internship": "Fellowship / Internship",
    "Fellowship": "Fellowship / Internship",
    "Scholarship": "Fellowship / Internship",
    "Grant / Funding": "Young Professional / Consultant (Contractual)",
    "Course": "Full-Time Corporate / NGO",
    "Webinar": "Full-Time Corporate / NGO",
    "Programme": "Full-Time Corporate / NGO",
    "Opportunity": "Fellowship / Internship",
}
KIND_MAP = {
    "Course": "Job / Career",
    "Webinar": "Job / Career",
    "Programme": "Job / Career",
    "Opportunity": "Job / Career",
}


def normalise_vocab(rec):
    """Keep position_type / opportunity_kind inside the site's vocabulary."""
    rec["position_type"] = POSITION_MAP.get(rec.get("position_type"), rec.get("position_type"))
    rec["opportunity_kind"] = KIND_MAP.get(rec.get("opportunity_kind"), rec.get("opportunity_kind"))
    return rec


def merge_active(path, records, global_flag):
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = {r.get("id") for r in data}
    urls = {str(r.get("apply_url", "")).rstrip("/") for r in data}
    added = []
    for rec in records:
        if rec["id"] in ids or str(rec["apply_url"]).rstrip("/") in urls:
            print(f"SKIP (exists): {rec['id']}")
            continue
        normalise_vocab(rec)
        rec["global"] = global_flag
        added.append(rec)
        ids.add(rec["id"])
        urls.add(str(rec["apply_url"]).rstrip("/"))
        print(f"ADD: {rec['id']}")
    added.sort(key=lambda r: (str(r.get("date_added") or ""), str(r.get("id") or "")), reverse=True)
    path.write_text(json.dumps(added + data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{path.name}: +{len(added)} -> {len(data) + len(added)}")


def merge_archive(path, records):
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = {r.get("id") for r in data}
    added = []
    for rec in records:
        if rec["id"] in ids:
            print(f"SKIP (archived): {rec['id']}")
            continue
        rec = dict(rec)
        normalise_vocab(rec)
        rec["status"] = "archived"
        rec["date_archived"] = VERIFIED_AT
        rec["global"] = True
        added.append(rec)
        ids.add(rec["id"])
        print(f"ARCHIVE: {rec['id']}")
    data.extend(added)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{path.name}: +{len(added)} -> {len(data)}")


def main():
    merge_active(JOBS_PATH, INDIA_RECORDS, False)
    merge_active(GLOBAL_PATH, GLOBAL_RECORDS, True)
    merge_archive(GLOBAL_ARCHIVE_PATH, GLOBAL_ARCHIVE_RECORDS)


if __name__ == "__main__":
    main()
