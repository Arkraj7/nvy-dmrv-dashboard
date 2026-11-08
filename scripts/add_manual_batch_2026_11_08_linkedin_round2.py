"""Add the second 8 November 2026 LinkedIn batch (India + global).

Source: the owner's LinkedIn feed, LinkedIn post searches and LinkedIn
Jobs keyword searches (past week, India), gathered through the owner's
browser on 8 November 2026.

Rules applied (docs/LINK_POLICY.md v2): apply_url comes from the source;
LinkedIn records stay UNKNOWN_KEEP; shortlinks (lnkd.in) were resolved in
the browser; no JD, qualification, skill or salary is invented.

Skipped from this round (no direct apply link in the post, or already on
the site): VIT Project Associate-II (VIT SRF already listed), IIT Roorkee
TRST01 internship, Hazaribagh East SRF/JRF (~1 month old, walk-in only),
University of Guelph funded Master's (no apply link in post), Olive
Recruitment Environmental Analyst Kochi (same role already listed).

Run from the repository root:
    py scripts/add_manual_batch_2026_11_08_linkedin_round2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_manual_batch_2026_11_08_linkedin import (  # noqa: E402
    JOBS_PATH,
    GLOBAL_PATH,
    SOURCE_FEED,
    base_record,
    global_record,
    india_job,
    li,
    merge_active,
    role,
)

INDIA_RECORDS = [
    # --- LinkedIn feed/search posts: fellowships ---
    base_record(
        id="edf-climate-corps-india-fellowship-2027",
        clean_title="Ashoka - EDF Climate Corps Fellowship 2027",
        organization="Ashoka University / Environmental Defense Fund",
        city="Multiple locations across India",
        state="Multiple States / Remote",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="1-3 Years",
        deadline_or_window="Phase II (early-career): 4 December 2026 - 3 January 2027",
        valid_through="2027-01-03",
        qualification_summary="Postgraduate students or early-career professionals (graduated not before 1 July 2022) with at least 2 years of relevant work experience.",
        compensation_or_fellowship="Rs. 50,000 per month stipend plus up to Rs. 30,000 one-time relocation allowance",
        role_summary="Fellowship pairing climate professionals with host organisations in India for a 3- or 6-month full-time project between April and September 2027.",
        apply_url="https://business.edf.org/insights/program-details-india-fellowship/",
        org_website="https://business.edf.org",
        org_domain="business.edf.org",
        source_portal=SOURCE_FEED,
        application_tip="Apply through the EDF India Fellowship programme page; Phase II opens 4 December 2026.",
    ),
    base_record(
        id="climalearn-climate-career-fellowship-cohort-4",
        clean_title="Climate Career Fellowship - Cohort 4 (Circular Economy Edition)",
        organization="ClimaLearn",
        city="India",
        state="Multiple States / Remote",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="Rolling / Open",
        qualification_summary="India-based professionals with 0-4 years of work experience interested in renewable energy, circular economy, ESG or the built environment.",
        compensation_or_fellowship="Not disclosed - see application form",
        role_summary="Cohort-based fellowship with expert sessions, a peer network and 3 months of 1:1 mentorship with an industry professional.",
        apply_url="https://forms.gle/sC5ztbpqDbBEy2je9",
        org_website="https://www.linkedin.com/company/climalearn",
        org_domain="linkedin.com",
        source_portal=SOURCE_FEED,
        application_tip="Express interest through the ClimaLearn application form.",
    ),
    # --- LinkedIn Jobs search, past week, India ---
    india_job("4486069019", "nsrcel-program-associate-climate-coe-bengaluru-2026",
              "Program Associate - Climate CoE", "NSRCEL", "Bengaluru", "Karnataka",
              "Climate Policy, Think-Tanks & Fellowships", "1-3 Years"),
    india_job("4486031992", "nsrcel-program-manager-bengaluru-2026",
              "Program Manager / Senior Program Manager", "NSRCEL", "Bengaluru", "Karnataka",
              "Climate Policy, Think-Tanks & Fellowships", "Mid-Senior (3-6 Years)"),
    india_job("4486827389", "iforest-programme-associate-odisha-2026",
              "Programme Associate", "International Forum for Environment, Sustainability & Technology (iFOREST)",
              "Odisha", "Odisha",
              "Climate Policy, Think-Tanks & Fellowships", "1-3 Years"),
    india_job("4488182232", "uplers-project-associate-air-environment-sustainability-mumbai-2026",
              "Project Associate (Air Environment & Sustainability)", "Uplers", "Mumbai", "Maharashtra",
              "Research Associate & Project Staff (Contractual)", "1-3 Years",
              position_type="Project Associate / Research Associate"),
    india_job("4488147574", "uplers-project-associate-air-water-wastewater-mumbai-2026",
              "Project Associate (Air / Water / Wastewater)", "Uplers", "Mumbai", "Maharashtra",
              "Research Associate & Project Staff (Contractual)", "1-3 Years",
              position_type="Project Associate / Research Associate"),
    india_job("4485019708", "erm-biodiversity-consultant-new-delhi-2026",
              "Biodiversity Consultant", "ERM", "New Delhi", "Delhi",
              "Forestry, Wildlife & Afforestation", "Mid-Senior (3-6 Years)"),
    india_job("4485035077", "erm-biodiversity-consultant-bengaluru-2026",
              "Biodiversity Consultant", "ERM", "Bengaluru", "Karnataka",
              "Forestry, Wildlife & Afforestation", "Mid-Senior (3-6 Years)"),
    india_job("4462771036", "buro-happold-senior-nature-biodiversity-consultant-bengaluru-2026",
              "Senior Nature & Biodiversity Consultant", "Buro Happold", "Bengaluru", "Karnataka",
              "Forestry, Wildlife & Afforestation", "Senior"),
    india_job("4485888906", "wsp-india-assistant-consultant-ecology-mumbai-2026",
              "Assistant Consultant - Ecology", "WSP in India", "Mumbai", "Maharashtra",
              "Forestry, Wildlife & Afforestation", "Entry Level / Fellowship",
              "https://www.wsp.com/en-in"),
    india_job("4486934904", "wsp-india-assistant-consultant-ecology-noida-2026",
              "Assistant Consultant - Ecology", "WSP in India", "Noida", "Uttar Pradesh",
              "Forestry, Wildlife & Afforestation", "Entry Level / Fellowship",
              "https://www.wsp.com/en-in"),
    india_job("4486597570", "wsp-india-senior-consultant-carbon-net-zero-mumbai-2026",
              "Senior Consultant - Carbon and Net Zero", "WSP in India", "Mumbai", "Maharashtra",
              "ESG, Carbon Markets & Corporate Sustainability", "Senior",
              "https://www.wsp.com/en-in"),
    india_job("4480354335", "adani-natural-resources-deputy-manager-esg-mundra-2026",
              "Deputy Manager - ESG", "Adani Natural Resources", "Mundra", "Gujarat",
              "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
              "https://www.adanienterprises.com"),
    india_job("4485822058", "skf-sustainability-manager-pune-2026",
              "Sustainability Manager", "SKF Group", "Pune", "Maharashtra",
              "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
              "https://www.skf.com"),
    india_job("4486060490", "bridgenext-gis-developer-pune-2026",
              "GIS Developer", "Bridgenext", "Pune", "Maharashtra",
              "GIS, Remote Sensing & Earth Observation", "1-3 Years"),
    india_job("4480119236", "verisk-gis-analyst-hyderabad-2026",
              "GIS Analyst I", "Verisk", "Hyderabad", "Telangana",
              "GIS, Remote Sensing & Earth Observation", "Entry Level / Fellowship",
              "https://www.verisk.com"),
    india_job("4486363708", "cognizant-geospatial-sr-analyst-bengaluru-2026",
              "GeoSpatial Sr. Analyst MAP", "Cognizant", "Bengaluru", "Karnataka",
              "GIS, Remote Sensing & Earth Observation", "Mid-Senior (3-6 Years)",
              "https://www.cognizant.com"),
    india_job("4488498742", "siterecon-jr-gis-cartographers-noida-2026",
              "Jr. GIS Cartographers / Cartographers (Immediate Joiners)", "SiteRecon", "Noida", "Uttar Pradesh",
              "GIS, Remote Sensing & Earth Observation", "Entry Level / Fellowship"),
    india_job("4486914606", "citi-physical-climate-risk-model-developer-mumbai-2026",
              "Physical Climate Risk Model Developer, Vice President", "Citi", "Mumbai", "Maharashtra",
              "ESG, Carbon Markets & Corporate Sustainability", "Senior",
              "https://www.citi.com"),
    india_job("4486493850", "alignerr-wildlife-habitat-conservation-scientist-mumbai-2026",
              "Wildlife and Habitat Conservation Scientist", "Alignerr", "Mumbai", "Maharashtra",
              "Forestry, Wildlife & Afforestation", "Mid-Senior (3-6 Years)"),
    india_job("4487598588", "alignerr-wildlife-habitat-conservation-scientist-delhi-2026",
              "Wildlife and Habitat Conservation Scientist", "Alignerr", "New Delhi", "Delhi",
              "Forestry, Wildlife & Afforestation", "Mid-Senior (3-6 Years)"),
    india_job("4486824429", "cascade-climate-india-partnerships-operations-consultant-delhi-2026",
              "India Partnerships & Operations Consultant (Part-Time)", "Cascade Climate", "New Delhi", "Delhi",
              "Climate Policy, Think-Tanks & Fellowships", "Mid-Senior (3-6 Years)",
              position_type="Young Professional / Consultant (Contractual)",
              extra={"employment_type": "CONTRACTOR"}),
    india_job("4485075408", "wri-india-intern-sustainable-agriculture-delhi-2026",
              "Intern - Sustainable Agriculture", "WRI India", "New Delhi", "Delhi",
              "Internships & Student Traineeships", "Entry Level / Fellowship",
              "https://wri-india.org", position_type="Internship",
              extra={"opportunity_kind": "Internship", "employment_type": "INTERN"}),
    india_job("4474256638", "rwdi-senior-air-quality-scientist-trivandrum-2026",
              "Senior Air Quality Scientist / Engineer", "RWDI", "Thiruvananthapuram", "Kerala",
              "ESG, Carbon Markets & Corporate Sustainability", "Senior",
              "https://www.rwdi.com"),
    india_job("4485876819", "enzene-esg-expert-chakan-2026",
              "ESG Expert - ESG & Sustainability", "Enzene Biosciences Ltd", "Chakan", "Maharashtra",
              "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)"),
    india_job("4484658168", "exemplar-lead-sustainability-bengaluru-2026",
              "Lead Sustainability", "Exemplar Luxury Group India", "Bengaluru", "Karnataka",
              "ESG, Carbon Markets & Corporate Sustainability", "Senior"),
    india_job("4486365862", "kritter-senior-geospatial-data-scientist-bengaluru-2026",
              "Senior Geospatial Data Scientist", "Kritter Software Technology", "Bengaluru", "Karnataka",
              "GIS, Remote Sensing & Earth Observation", "Mid-Senior (3-6 Years)"),
    india_job("4483668348", "globalfoundries-corporate-ehs-sustainability-environmental-engineer-bengaluru-2026",
              "Corporate EHS & Sustainability Environmental Engineer", "GlobalFoundries", "Bengaluru", "Karnataka",
              "ESG, Carbon Markets & Corporate Sustainability", "Mid-Senior (3-6 Years)",
              "https://gf.com"),
    india_job("4477589175", "burns-mcdonnell-water-resources-engineer-mumbai-2026",
              "Water Resources Engineer - Hydraulics & Hydrology (Water)", "Burns & McDonnell India",
              "Mumbai", "Maharashtra",
              "GIS, Remote Sensing & Earth Observation", "1-3 Years",
              "https://www.burnsmcd.com"),
    india_job("4460249351", "wsp-india-senior-engineer-water-resources-mumbai-2026",
              "Senior Engineer - Water Resources", "WSP in India", "Mumbai", "Maharashtra",
              "GIS, Remote Sensing & Earth Observation", "Mid-Senior (3-6 Years)",
              "https://www.wsp.com/en-in"),
    india_job("4460238512", "wsp-india-senior-engineer-water-resources-noida-2026",
              "Senior Engineer - Water Resources", "WSP in India", "Noida", "Uttar Pradesh",
              "GIS, Remote Sensing & Earth Observation", "Mid-Senior (3-6 Years)",
              "https://www.wsp.com/en-in"),
]

GLOBAL_RECORDS = [
    global_record(
        id="mcw-young-leaders-fellowship-2027",
        clean_title="MCW Young Leaders Fellowship Program 2027",
        organization="MCW Global",
        city="New York / Burlington",
        state="New York / Vermont",
        country="United States",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        deadline_or_window="3 December 2026",
        valid_through="2026-12-03",
        qualification_summary="Young people aged 18-26 from any country, interested in community projects in education, health and economic security.",
        compensation_or_fellowship="Fully funded (international economy flights and programme costs covered)",
        role_summary="Year-long fellowship with a virtual community needs assessment, an in-person vision planning and project development programme in July 2027, and virtual project implementation with alumni mentorship.",
        apply_url="https://mcwglobal.org/young-leaders-fellowship-2027/",
        org_website="https://mcwglobal.org",
        org_domain="mcwglobal.org",
        source_portal="LinkedIn post (MCW Global)",
        application_tip="Apply through the MCW Young Leaders Fellowship page before 3 December 2026.",
    ),
]


def main():
    merge_active(JOBS_PATH, INDIA_RECORDS, False)
    merge_active(GLOBAL_PATH, GLOBAL_RECORDS, True)


if __name__ == "__main__":
    main()
