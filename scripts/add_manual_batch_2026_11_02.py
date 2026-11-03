"""Add the verified 2 November 2026 opportunity batch.

Sources: the LinkedIn posts shared by the site owner (destinations resolved
from lnkd.in short links) plus a discovery sweep of open fellowships,
workshops and research posts.

Rules applied (docs/LINK_POLICY.md v2):
- apply_url always comes from the source, never invented.
- 403 / bot-blocked official pages are kept as UNKNOWN_KEEP, not dropped.
- Deadlines already in the past are excluded.
- Aggregator pages are only used where the organiser exposes no single
  vacancy URL (FreeJobAlert is an allow-listed platform).

Run from the repository root:

    py scripts/add_manual_batch_2026_11_02.py

The script is idempotent: existing ids are left untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"
GLOBAL_PATH = ROOT / "public" / "global_jobs.json"

VERIFIED_AT = "2026-11-02"
DATE_ADDED = "2026-11-02"


def base_record(**overrides):
    record = {
        "clean_title": "",
        "organization": "",
        "city": "",
        "state": "",
        "country": "India",
        "region": "",
        "category": "",
        "position_type": "Full-Time Corporate / NGO",
        "opportunity_kind": "Job / Career",
        "experience_level": "1-3 Years",
        "employment_type": "FULL_TIME",
        "deadline_or_window": "Rolling / Open",
        "valid_through": "2026-12-31",
        "qualification_summary": "",
        "compensation_or_fellowship": "Not disclosed - see official notification",
        "role_summary": "",
        "key_responsibilities": [],
        "must_have_skills": [],
        "application_tip": "",
        "apply_url": "",
        "org_website": "",
        "org_domain": "",
        "source_portal": "Verified batch - 2026-11-02",
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
        id="csir-tkdl-project-associate-i-forestry-2026",
        clean_title="Project Associate-I - Forestry & Ecology (CSIR-TKDL)",
        organization="CSIR - Traditional Knowledge Digital Library (TKDL) Unit",
        city="New Delhi",
        state="Delhi",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Project Associate / Research Associate",
        experience_level="Entry Level / Fellowship",
        employment_type="CONTRACTOR",
        deadline_or_window="12 November 2026",
        valid_through="2026-11-12",
        qualification_summary=(
            "Master's degree in Forestry & Ecology, Environmental Sciences or related "
            "disciplines, as per the CSIR-TKDL notice."
        ),
        compensation_or_fellowship="Rs 25,000-31,000 per month + HRA",
        role_summary=(
            "CSIR-TKDL Unit, New Delhi invites candidates for two project-based "
            "Project Associate-I positions in Forestry & Ecology and Environmental "
            "Sciences. Selection is through a walk-in interview on 12 November 2026 "
            "at 9:30 AM at the CSIR-TKDL Unit, New Delhi."
        ),
        key_responsibilities=[
            "Support project work in forestry, ecology and environmental sciences",
            "Compile and verify technical and documentary records",
            "Assist with project reporting and documentation",
        ],
        must_have_skills=["Forestry", "Ecology", "Environmental Science", "Documentation"],
        application_tip=(
            "Attend the walk-in interview on 12 November 2026 at 9:30 AM at the "
            "CSIR-TKDL Unit, New Delhi with the prescribed application form and "
            "supporting documents."
        ),
        apply_url="https://www.freejobalert.com/articles/csir-tkdl-recruitment-2026-project-associate-i-pat-i-3077260",
        org_website="https://www.csir.res.in",
        org_domain="csir.res.in",
        source_portal="LinkedIn post (CSIR-NIScPR) + FreeJobAlert notice",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-notice-via-allowlisted-platform",
            "source": "https://www.freejobalert.com/articles/csir-tkdl-recruitment-2026-project-associate-i-pat-i-3077260",
            "http_status": 200,
        },
        reverify_after="2026-11-09",
    ),
    base_record(
        id="icar-nbsslup-young-professional-ii-rs-gis-2026",
        clean_title="Young Professional-II (Remote Sensing & GIS)",
        organization="ICAR - National Bureau of Soil Survey and Land Use Planning (NBSS&LUP)",
        city="Nagpur",
        state="Maharashtra",
        category="GIS, Remote Sensing & Earth Observation",
        position_type="Project Associate / Research Associate",
        experience_level="1-3 Years",
        employment_type="CONTRACTOR",
        deadline_or_window="16 November 2026",
        valid_through="2026-11-16",
        qualification_summary=(
            "Postgraduate degree in Remote Sensing & GIS, Geoinformatics, Geography "
            "or a related discipline, as per the ICAR-NBSS&LUP advertisement."
        ),
        compensation_or_fellowship="Rs 42,000 per month (fixed)",
        role_summary=(
            "ICAR-NBSS&LUP, Nagpur is engaging one Young Professional-II (RS & GIS) "
            "on a purely contractual basis. Selection is through a walk-in interview "
            "on 16 November 2026 at 11:00 AM."
        ),
        key_responsibilities=[
            "Carry out remote sensing and GIS analysis for soil survey projects",
            "Prepare spatial datasets, maps and technical outputs",
            "Support project reporting and data management",
        ],
        must_have_skills=["Remote Sensing", "GIS", "Spatial Analysis", "Mapping"],
        application_tip=(
            "Attend the walk-in interview on 16 November 2026 at 11:00 AM at "
            "ICAR-NBSS&LUP, Nagpur with the application form and original documents."
        ),
        apply_url="https://www.freejobalert.com/articles/icar-nbss-lup-young-professional-ii-rs-gis-recruitment-2026-3077207",
        org_website="https://icar-nbsslup.org.in",
        org_domain="icar-nbsslup.org.in",
        source_portal="LinkedIn post (GIS&RS Jobs) + FreeJobAlert notice",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-notice-via-allowlisted-platform",
            "source": "https://www.freejobalert.com/articles/icar-nbss-lup-young-professional-ii-rs-gis-recruitment-2026-3077207",
            "http_status": 200,
        },
        reverify_after="2026-11-13",
    ),
    base_record(
        id="biotrend-energy-research-analyst-2026",
        clean_title="Research Analyst - Bioenergy & Policy",
        organization="Bio Trend Energy Pvt. Ltd.",
        city="New Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Entry Level / Fellowship",
        employment_type="FULL_TIME",
        deadline_or_window="Rolling / Open",
        valid_through="2026-12-31",
        qualification_summary=(
            "Degree in a technical, energy, agricultural or environmental field "
            "(B.Sc., M.Sc., Biotechnology or similar); freshers welcome."
        ),
        compensation_or_fellowship="Not disclosed - see official notification",
        role_summary=(
            "Bio Trend Energy, Saket, New Delhi is hiring a Research Analyst to "
            "prepare reports, proposals and executive summaries, maintain research "
            "databases and track energy policy, schemes and market trends, working "
            "directly with the Director."
        ),
        key_responsibilities=[
            "Prepare reports, proposals, presentations and executive summaries",
            "Build and update research databases",
            "Track energy policies, schemes, technology and market trends",
            "Support strategic planning with the Director",
        ],
        must_have_skills=[
            "Desktop Research",
            "Statistical Analysis",
            "Report Writing",
            "Bioenergy",
            "Energy Policy",
        ],
        application_tip="Email your CV to hr@biotrendenergy.com.",
        apply_url="mailto:hr@biotrendenergy.com",
        org_website="",
        org_domain="biotrendenergy.com",
        source_portal="LinkedIn post (Bio Trend Energy)",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-email-in-post",
            "source": "mailto:hr@biotrendenergy.com",
        },
        reverify_after="2026-11-16",
    ),
    base_record(
        id="swadesh-metallics-environment-officer-2026",
        clean_title="Environment Officer",
        organization="Swadesh Metallics Pvt. Ltd.",
        city="Raipur (Kesda)",
        state="Chhattisgarh",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        employment_type="FULL_TIME",
        deadline_or_window="Rolling / Open",
        valid_through="2026-12-31",
        qualification_summary=(
            "Relevant qualification in Environmental Science or Environmental "
            "Engineering; experience in environmental management or the steel "
            "industry preferred."
        ),
        compensation_or_fellowship="Not disclosed - see official notification",
        role_summary=(
            "Swadesh Metallics, Raipur is hiring an Environment Officer for "
            "environmental compliance and statutory requirements, pollution control "
            "and monitoring, waste management, and environmental documentation and "
            "reporting. Immediate joiners preferred; Chhattisgarh candidates preferred."
        ),
        key_responsibilities=[
            "Maintain environmental compliance and statutory requirements",
            "Run pollution control and monitoring activities",
            "Manage waste streams and environmental documentation",
            "Prepare environmental reports and returns",
        ],
        must_have_skills=[
            "Environmental Compliance",
            "Pollution Monitoring",
            "Waste Management",
            "Environmental Reporting",
        ],
        application_tip="Send your CV to recruitment@swadeshmetallics.com.",
        apply_url="mailto:recruitment@swadeshmetallics.com",
        org_website="",
        org_domain="swadeshmetallics.com",
        source_portal="LinkedIn post (Swadesh Metallics)",
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-email-in-post",
            "source": "mailto:recruitment@swadeshmetallics.com",
        },
        reverify_after="2026-11-16",
    ),
]


GLOBAL_RECORDS = [
    base_record(
        id="icccad-cop31-climate-negotiation-diplomacy-2026",
        clean_title="Online Training Course on Climate Negotiation and Diplomacy: Tracking COP31",
        organization="International Centre for Climate Change and Development (ICCCAD), Independent University Bangladesh",
        city="Dhaka",
        state="",
        country="Bangladesh",
        region="Asia-Pacific",
        category="Workshops, Training & Capacity Building",
        position_type="Training / Short Course",
        opportunity_kind="Job / Career",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="9 November 2026",
        valid_through="2026-11-09",
        qualification_summary=(
            "Open to early- and mid-career professionals, government officials, "
            "researchers, academics, students, development practitioners and youth "
            "or civil society representatives, particularly from Least Developed Countries."
        ),
        compensation_or_fellowship="Participation fully waived",
        role_summary=(
            "Two-week online course (11-25 November 2026) on global climate "
            "governance, UNFCCC negotiations and COP31, covering climate finance, "
            "adaptation, loss and damage, clean energy and Article 6 carbon markets, "
            "with a negotiation simulation and mock COP. Certificate subject to 80% "
            "attendance and assessment. Organised under the CAP-RES project with "
            "support from the Embassy of Sweden in Dhaka."
        ),
        key_responsibilities=[
            "Follow COP31 negotiations and analyse draft negotiating texts",
            "Prepare position papers and briefing notes",
            "Take part in the negotiation simulation and mock COP",
        ],
        must_have_skills=[
            "Climate Policy",
            "UNFCCC",
            "Climate Finance",
            "Negotiation",
            "Policy Writing",
        ],
        application_tip=(
            "Apply through the official course form before 9 November 2026; "
            "enquiries to nazma.icccad@iub.edu.bd."
        ),
        apply_url="https://docs.google.com/forms/d/e/1FAIpQLSeH2_P8-gtP716qE5-Yr8YrCF-FP6t1jWBfdlZPjls0ivgDQA/viewform",
        org_website="https://iub.ac.bd/site/icccad",
        org_domain="iub.ac.bd",
        source_portal="LinkedIn post (ICCCAD / IUB)",
        entry_type="posting",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "shortener-resolved-and-fetched",
            "source": "https://lnkd.in/gDumPhpK -> Google Form; course page https://iub.ac.bd/site/icccad",
            "http_status": 200,
        },
        reverify_after="2026-11-06",
    ),
    base_record(
        id="ceps-climate-leadership-programme-2027",
        clean_title="CEPS Climate Leadership Programme 2027",
        organization="Centre for European Policy Studies (CEPS) x Heinrich-Boll-Stiftung European Union",
        city="Brussels",
        state="",
        country="Belgium",
        region="Europe",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="11 November 2026, 23:59 CET",
        valid_through="2026-11-11",
        qualification_summary=(
            "Open worldwide to young people already contributing to climate action "
            "through policy work, advocacy or entrepreneurship."
        ),
        compensation_or_fellowship="Travel, visa and accommodation covered",
        role_summary=(
            "Online masterclasses and skills training from December 2026 to February "
            "2027, followed by a week in Brussels (28 February-6 March 2027) including "
            "the CEPS Ideas Lab on 4-5 March 2027. Participants build understanding of "
            "EU climate governance and connect with policymakers, researchers and "
            "civil society."
        ),
        key_responsibilities=[
            "Complete the online masterclass and skills-training modules",
            "Attend the Brussels programme and CEPS Ideas Lab",
            "Engage with EU climate policymakers and practitioners",
        ],
        must_have_skills=["Climate Policy", "Advocacy", "EU Governance", "Communication"],
        application_tip="Apply through the CEPS call page before 11 November 2026, 23:59 CET.",
        apply_url="https://www.ceps.eu/ceps-news/call-for-applications-climate-leadership-programme",
        org_website="https://www.ceps.eu",
        org_domain="ceps.eu",
        source_portal="LinkedIn post (CEPS programme) + official CEPS call page",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-call-page-bot-blocked",
            "source": "https://www.ceps.eu/ceps-news/call-for-applications-climate-leadership-programme",
            "http_status": 403,
            "notes": "Official page returns 403 to automated clients (UNKNOWN_KEEP); call details confirmed via search index.",
        },
        reverify_after="2026-11-08",
    ),
    base_record(
        id="global-eba-fund-medium-grants-2026",
        clean_title="Global EbA Fund - Medium-Size Grants Call for Proposals",
        organization="IUCN x UN Environment Programme (Global EbA Fund, funded by IKI)",
        city="Global",
        state="",
        country="Global",
        region="Global",
        category="Grants & Research Funding",
        position_type="Grant / Funding",
        opportunity_kind="Grant / Funding",
        experience_level="Organisations / Consortia",
        employment_type="OTHER",
        deadline_or_window="16 November 2026",
        valid_through="2026-11-16",
        qualification_summary=(
            "Organisations and consortia scaling ecosystem-based adaptation, "
            "including applicants across Eastern Europe, Central Asia and beyond."
        ),
        compensation_or_fellowship="Grants of up to USD 500,000",
        role_summary=(
            "Call for proposals supporting initiatives that scale Ecosystem-based "
            "Adaptation and address systemic barriers through innovative finance, "
            "human development and security, and people-nature-climate-land synergies."
        ),
        key_responsibilities=[
            "Design an ecosystem-based adaptation project addressing systemic barriers",
            "Demonstrate pathways to scale EbA through finance or policy change",
            "Deliver measurable adaptation and resilience outcomes",
        ],
        must_have_skills=[
            "Ecosystem-based Adaptation",
            "Climate Adaptation",
            "Project Design",
            "Grant Proposal Writing",
        ],
        application_tip="Submit through the Global EbA Fund call page by 16 November 2026.",
        apply_url="https://globalebafund.org/medium-size-grants/",
        org_website="https://globalebafund.org",
        org_domain="globalebafund.org",
        source_portal="LinkedIn post (IUCN Eastern Europe and Central Asia)",
        entry_type="award_portal",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-page-fetched",
            "source": "https://globalebafund.org/medium-size-grants/",
            "http_status": 200,
        },
        reverify_after="2026-11-12",
    ),
    base_record(
        id="vanderbilt-meng-lab-phd-2027",
        clean_title="Fully Funded PhD - Vegetation Remote Sensing & Urban Ecology (Meng Lab)",
        organization="Vanderbilt University - Department of Earth and Environmental Sciences",
        city="Nashville",
        state="Tennessee",
        country="United States",
        region="North America",
        category="Academic, JRF, SRF & PhD Positions",
        position_type="PhD / Doctoral Fellowship",
        opportunity_kind="Scholarship",
        experience_level="Entry Level / Fellowship",
        employment_type="OTHER",
        deadline_or_window="1 January 2027",
        valid_through="2027-01-01",
        qualification_summary=(
            "Strong programming and quantitative skills with a background in remote "
            "sensing, urban ecology or related fields; ML modelling experience and "
            "strong written and spoken English expected."
        ),
        compensation_or_fellowship="Fully funded PhD position (Fall 2027)",
        role_summary=(
            "The Meng Lab recruits one fully funded PhD student (Fall 2027) in "
            "vegetation remote sensing, urban ecology and environmental change, "
            "integrating satellite observations, geospatial analysis and AI/ML to "
            "study urban warming, artificial light at night and air pollution."
        ),
        key_responsibilities=[
            "Integrate satellite observations with geospatial and AI/ML methods",
            "Study vegetation dynamics and environmental exposures",
            "Publish research and complete doctoral requirements",
        ],
        must_have_skills=[
            "Remote Sensing",
            "Programming",
            "Machine Learning",
            "Quantitative Analysis",
            "Urban Ecology",
        ],
        application_tip=(
            "Email a brief research-interest statement, CV and transcripts as a "
            "single PDF to lin.meng@vanderbilt.edu; deadline 1 January 2027."
        ),
        apply_url="https://sites.google.com/view/linmeng/join",
        org_website="https://sites.google.com/view/linmeng",
        org_domain="sites.google.com",
        source_portal="LinkedIn post (Lin Meng, Vanderbilt University)",
        entry_type="posting",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "shortener-resolved-lab-page-fetched",
            "source": "https://lnkd.in/eK7tBiFB -> https://sites.google.com/view/linmeng/join",
            "http_status": 200,
        },
        reverify_after="2026-12-01",
    ),
    base_record(
        id="mittal-family-climate-fellowship-2027",
        clean_title="Mittal Family Climate Fellowship (Academic Year 2027/28)",
        organization="Mittal South Asia Institute, Harvard University",
        city="Cambridge",
        state="Massachusetts",
        country="United States",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Researchers",
        employment_type="OTHER",
        deadline_or_window="8 December 2026",
        valid_through="2026-12-08",
        qualification_summary=(
            "Researchers working on climate-related questions relevant to South Asia; "
            "see the fellowship page for eligibility and reference requirements."
        ),
        compensation_or_fellowship="As per fellowship norms",
        role_summary=(
            "The Mittal Family Climate Fellowship at Harvard's Mittal South Asia "
            "Institute supports research on climate change in South Asia. "
            "Applications for Academic Year 2027/28 are open; the deadline is "
            "Tuesday, 8 December 2026."
        ),
        key_responsibilities=[
            "Conduct independent climate research on South Asia",
            "Engage with the Mittal South Asia Institute community",
            "Produce research outputs during the fellowship",
        ],
        must_have_skills=["Climate Research", "South Asia", "Research Writing"],
        application_tip="Apply through the Mittal South Asia Institute fellowship page by 8 December 2026.",
        apply_url="https://mittalsouthasiainstitute.harvard.edu/climate-fellowship",
        org_website="https://mittalsouthasiainstitute.harvard.edu",
        org_domain="harvard.edu",
        source_portal="Discovery sweep - Harvard Mittal South Asia Institute",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-page-bot-blocked",
            "source": "https://mittalsouthasiainstitute.harvard.edu/climate-fellowship",
            "http_status": 403,
            "notes": "Official page returns 403 to automated clients (UNKNOWN_KEEP); deadline confirmed via search index.",
        },
        reverify_after="2026-11-20",
    ),
    base_record(
        id="harvard-environmental-fellows-2027",
        clean_title="Harvard Environmental Fellows Program 2027",
        organization="Harvard University Center for the Environment",
        city="Cambridge",
        state="Massachusetts",
        country="United States",
        region="North America",
        category="Fellowships & Leadership Programs",
        position_type="Fellowship / Internship",
        opportunity_kind="Fellowship",
        experience_level="Researchers",
        employment_type="OTHER",
        deadline_or_window="1 December 2026",
        valid_through="2026-12-01",
        qualification_summary=(
            "Early-career researchers in environmental fields; see the program page "
            "for eligibility and appointment terms."
        ),
        compensation_or_fellowship="As per fellowship norms",
        role_summary=(
            "The Harvard Environmental Fellows Program supports early-career "
            "researchers working across environmental disciplines. The application "
            "window for 2027 is open and closes on 1 December 2026."
        ),
        key_responsibilities=[
            "Pursue independent environmental research at Harvard",
            "Collaborate with Harvard faculty and research groups",
        ],
        must_have_skills=["Environmental Research", "Research Writing"],
        application_tip="Apply through the Harvard Center for the Environment program page by 1 December 2026.",
        apply_url="https://www.environment.harvard.edu/environmental-fellows-program",
        org_website="https://www.environment.harvard.edu",
        org_domain="harvard.edu",
        source_portal="Discovery sweep - Harvard Center for the Environment",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-page-bot-blocked",
            "source": "https://www.environment.harvard.edu/environmental-fellows-program",
            "http_status": 403,
            "notes": "Official page returns 403 to automated clients (UNKNOWN_KEEP); deadline confirmed via search index.",
        },
        reverify_after="2026-11-20",
    ),
    base_record(
        id="unep-dhi-online-water-courses-2026",
        clean_title="UNEP-DHI Online Water & Climate Courses (2026 Editions)",
        organization="UNEP-DHI Centre on Water and Environment x CAP-NET",
        city="Online",
        state="",
        country="Global",
        region="Global",
        category="Workshops, Training & Capacity Building",
        position_type="Training / Short Course",
        opportunity_kind="Job / Career",
        experience_level="All levels",
        employment_type="OTHER",
        deadline_or_window="Rolling / Open",
        valid_through="2026-12-31",
        qualification_summary="Open to practitioners, policymakers and water professionals worldwide.",
        compensation_or_fellowship="Free, self-paced online courses",
        role_summary=(
            "Five free, self-paced online courses: IWRM for Climate Resilience, "
            "Sustainable Lake Management, Water Pollution Management, Integrated "
            "Drought Management (English and French) and Gender and IWRM. "
            "A certificate is issued on completing all modules."
        ),
        key_responsibilities=[
            "Complete the selected self-paced course modules",
            "Apply water and climate tools to national or basin contexts",
        ],
        must_have_skills=["Water Resources Management", "Climate Resilience", "IWRM"],
        application_tip="Enrol through the CAP-NET online courses catalogue; courses are free and self-paced.",
        apply_url="https://cap-net.org/the-network/online-courses/",
        org_website="https://unepdhi.org/training/",
        org_domain="cap-net.org",
        source_portal="Discovery sweep - UNEP-DHI training page",
        entry_type="careers_portal",
        **{"global": True},
        verification={
            "verified_at": VERIFIED_AT,
            "method": "official-catalogue-fetched",
            "source": "https://cap-net.org/the-network/online-courses/",
            "http_status": 200,
        },
        reverify_after="2026-11-20",
    ),
]


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


def main() -> None:
    jobs = load(JOBS_PATH)
    global_jobs = load(GLOBAL_PATH)

    print("India registry")
    added_india = add_new(jobs, INDIA_RECORDS, "India")

    print("Global registry")
    added_global = add_new(global_jobs, GLOBAL_RECORDS, "Global")

    save(JOBS_PATH, jobs)
    save(GLOBAL_PATH, global_jobs)

    print(f"\nDone: India +{added_india}; Global +{added_global}")
    print(f"India records: {len(jobs)}; global records: {len(global_jobs)}")


if __name__ == "__main__":
    main()
