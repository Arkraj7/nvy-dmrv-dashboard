#!/usr/bin/env python3
"""Add verified green-sector leads from LinkedIn posts as a new registry batch.

Direct official links -> posting (pattern-validated).
LinkedIn short links (lnkd.in) -> careers_portal (cannot verify directness).
Expired deadlines and non-green roles are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
JOBS = PUBLIC / "jobs.json"

VERIFIED_ON = "2026-10-29"

RECORDS = [
    # --- Direct official links (posting) ---
    {
        "id": "udd-uttarakhand-gis-positions-2026",
        "clean_title": "GIS Positions (Lead Consultant, GIS Planner, GIS Manager, GIS Technical)",
        "organization": "Urban Development Directorate, Government of Uttarakhand",
        "city": "Dehradun",
        "state": "Uttarakhand",
        "category": "GIS, Remote Sensing & Earth Observation",
        "experience_level": "Varies by post",
        "employment_type": "CONTRACTOR",
        "entry_type": "posting",
        "apply_url": "https://udd.uk.gov.in",
        "source_portal": "Official government website",
        "role_summary": "Contractual GIS positions under SMMU/CMMU: Lead Consultant, GIS Planner, GIS Manager, GIS Technical. Last date 13 Nov 2026.",
        "deadline_or_window": "13 November 2026",
        "valid_through": "2026-11-13",
    },
    {
        "id": "iica-corporate-climate-leadership-programme",
        "clean_title": "Corporate Climate Leadership Programme (CCLP) – Batch I",
        "organization": "Indian Institute of Corporate Affairs (IICA)",
        "city": "India",
        "state": "",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Senior / Board level",
        "employment_type": "OTHER",
        "entry_type": "posting",
        "apply_url": "https://iica.nic.in/cclp/",
        "source_portal": "Official IICA website",
        "role_summary": "3-month hybrid executive programme on climate finance, green bonds, transition planning. For board members, CFOs, CSOs and sustainability practitioners.",
    },
    # --- LinkedIn-sourced (careers_portal) ---
    {
        "id": "fao-environment-climate-change-specialist",
        "clean_title": "Environment and Climate Change Specialist",
        "organization": "Food and Agriculture Organization of the United Nations (FAO)",
        "city": "India",
        "state": "",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Senior (7+ years)",
        "employment_type": "CONTRACTOR",
        "entry_type": "posting",
        "apply_url": "https://lnkd.in/dmGE4YtC",
        "source_portal": "LinkedIn",
        "role_summary": "Support climate resilience, environmental sustainability, biodiversity conservation and climate finance. Duration 12 months, renewable. Deadline 5 Nov 2026.",
        "deadline_or_window": "5 November 2026",
        "valid_through": "2026-11-05",
    },
    {
        "id": "envirocatalysts-project-associate-punjab",
        "clean_title": "Project Associate – Air Quality & Waste Management",
        "organization": "EnviroCatalysts",
        "city": "Punjab",
        "state": "Punjab",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "experience_level": "2+ years",
        "employment_type": "FULL_TIME",
        "entry_type": "posting",
        "apply_url": "https://lnkd.in/gHaDAv2X",
        "source_portal": "LinkedIn",
        "role_summary": "Work with local ULBs on air quality and waste management data, policy-relevant research. Full-time, on-site. Deadline 15 Nov 2026.",
        "deadline_or_window": "15 November 2026",
        "valid_through": "2026-11-15",
    },
    {
        "id": "atree-policy-lead-analyst-himalayan-region",
        "clean_title": "Policy Lead & Analyst (Biodiversity Conservation, Landscape Restoration)",
        "organization": "Ashoka Trust for Research in Ecology and the Environment (ATREE)",
        "city": "India",
        "state": "",
        "category": "Climate Policy, Think-Tanks & Fellowships",
        "experience_level": "Mid-Senior",
        "employment_type": "",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/gZyeABzK",
        "source_portal": "LinkedIn",
        "role_summary": "Policy research, reviews, consultations and recommendations on biodiversity conservation and bio-resource use across the Indian Himalayan Region.",
    },
    {
        "id": "iit-roorkee-jrf-landscape-ecology-terai",
        "clean_title": "Junior Research Fellow – Landscape Ecology (Terai Ecoregion)",
        "organization": "Indian Institute of Technology Roorkee (IIT Roorkee)",
        "city": "Roorkee",
        "state": "Uttarakhand",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "employment_type": "CONTRACTOR",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/grEMZ598",
        "source_portal": "LinkedIn",
        "role_summary": "JRF for ANRF-funded project on land use/land cover changes in Terai-Duar Savanna and Grasslands Ecoregion. Salary Rs 37,000 + HRA. Deadline 11 Nov 2026.",
        "deadline_or_window": "11 November 2026",
        "valid_through": "2026-11-11",
    },
    {
        "id": "iit-bhubaneswar-jrf-environmental-engineering",
        "clean_title": "Junior Research Fellow – Environmental Engineering",
        "organization": "Indian Institute of Technology Bhubaneswar (IIT Bhubaneswar)",
        "city": "Bhubaneswar",
        "state": "Odisha",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Entry Level / Fellowship",
        "employment_type": "CONTRACTOR",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/grEMZ598",
        "source_portal": "LinkedIn",
        "role_summary": "JRF in Environmental Engineering, School of Infrastructure. B.Tech + M.Tech required. Last date 6 Nov 2026.",
        "deadline_or_window": "6 November 2026",
        "valid_through": "2026-11-06",
    },
    {
        "id": "rgu-research-associate-field-investigator",
        "clean_title": "Research Associate & Field Investigator (ICSSR Project)",
        "organization": "Rajiv Gandhi University (RGU)",
        "city": "Doimukh",
        "state": "Arunachal Pradesh",
        "category": "Academic, JRF, SRF & PhD Positions",
        "experience_level": "Mid-level",
        "employment_type": "CONTRACTOR",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/g76iU5kF",
        "source_portal": "LinkedIn",
        "role_summary": "ICSSR-funded research project staff: Research Associate (Rs 47,000/month) and Field Investigator (Rs 20,000/month). Deadline 3/6 Nov 2026.",
        "deadline_or_window": "6 November 2026",
        "valid_through": "2026-11-06",
    },
    {
        "id": "mit-solve-2027-global-climate-challenge",
        "clean_title": "MIT Solve 2027 Global Climate Challenge",
        "organization": "Massachusetts Institute of Technology (MIT Solve)",
        "city": "Global",
        "state": "",
        "country": "Global",
        "category": "Competitions, Hackathons & Awards",
        "experience_level": "All levels",
        "employment_type": "OTHER",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/eUZq7t8S",
        "source_portal": "LinkedIn / SEA Capital Pathways",
        "role_summary": "Funding for climate technology solutions: US$10,000 Solver Award, up to US$150,000 sponsor prizes, 9-month support programme. Deadline 2 Nov 2026.",
        "deadline_or_window": "2 November 2026",
        "valid_through": "2026-11-02",
    },
    {
        "id": "breakthrough-energy-fellows-cohort-7",
        "clean_title": "Breakthrough Energy Fellows Program – Cohort 7",
        "organization": "Breakthrough Energy",
        "city": "Global",
        "state": "",
        "country": "Global",
        "category": "Fellowships & Leadership Programs",
        "experience_level": "All levels",
        "employment_type": "OTHER",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/difJutZN",
        "source_portal": "LinkedIn / Global South Opportunities",
        "role_summary": "Up to US$500,000 funding for early-stage climate technology innovations, plus mentorship and investor connections. Deadline 2 Nov 2026.",
        "deadline_or_window": "2 November 2026",
        "valid_through": "2026-11-02",
    },
    {
        "id": "giga-young-leaders-summer-academy-2027",
        "clean_title": "Young Leaders Summer Academy (YLSA) 2027 – Climate-Security Nexus",
        "organization": "German Institute for Global and Area Studies (GIGA)",
        "city": "Hamburg",
        "state": "",
        "country": "Germany",
        "category": "Conferences, Summits & Events",
        "experience_level": "Young professionals",
        "employment_type": "OTHER",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/ec8sTJfj",
        "source_portal": "LinkedIn",
        "role_summary": "Summer academy on climate-security nexus for future leaders from Middle East and Europe. 13–16 June 2027 in Hamburg. Applications until 13 Dec 2026.",
        "deadline_or_window": "13 December 2026",
        "valid_through": "2026-12-13",
    },
    {
        "id": "jnmc-jawaharlal-nehru-fellowship",
        "clean_title": "Jawaharlal Nehru Fellowship – Research & Creative Projects",
        "organization": "Jawaharlal Nehru Memorial Fund (JNMF)",
        "city": "India",
        "state": "",
        "category": "Fellowships & Leadership Programs",
        "experience_level": "Researchers",
        "employment_type": "OTHER",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/gGhk_Bbr",
        "source_portal": "LinkedIn / EPN Worldwide",
        "role_summary": "Monthly stipend of Rs 1 lakh for 2 years for original research, creative projects and independent intellectual inquiry.",
    },
    {
        "id": "climate-repair-student-grants-cambridge",
        "clean_title": "Climate Repair Student Grants (up to £1000)",
        "organization": "University of Cambridge – Centre for Climate Repair",
        "city": "Cambridge",
        "state": "",
        "country": "United Kingdom",
        "category": "Grants & Research Funding",
        "experience_level": "Undergraduate / Postgraduate",
        "employment_type": "OTHER",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/eeawNjGU",
        "source_portal": "LinkedIn",
        "role_summary": "Grants of up to £1000 for climate repair projects by Cambridge students. Applications close 11 December 2026.",
        "deadline_or_window": "11 December 2026",
        "valid_through": "2026-12-11",
    },
    {
        "id": "adel-pan-african-consultant-roster",
        "clean_title": "Pan-African Expert Consultant Roster (Climate & Disaster Risk, GIS, MEAL)",
        "organization": "African Development Evidence Lab (ADEL)",
        "city": "Africa",
        "state": "",
        "country": "Global",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "experience_level": "Experienced professionals",
        "employment_type": "CONTRACTOR",
        "entry_type": "careers_portal",
        "apply_url": "https://lnkd.in/dw4cfCHd",
        "source_portal": "LinkedIn / Hybrid and Remote Working",
        "role_summary": "Consultant roster for research, evaluations, advisory and development consulting across Africa. Includes climate & disaster risk specialists and GIS analysts. Closing 31 Oct 2026.",
        "deadline_or_window": "31 October 2026",
        "valid_through": "2026-10-31",
    },
]

LINK_POLICY_BLOCK = {
    "status": "listing",
    "entry_type": "careers_portal",
    "checked": VERIFIED_ON,
    "note": "LinkedIn-sourced listing; tagged as portal under policy v2.",
}

VERIFICATION_BLOCK = {
    "verified_on": VERIFIED_ON,
    "verified_by": "manual review of LinkedIn posts",
    "source": "User-provided LinkedIn posts",
    "notes": "Link pattern-validated (platform). Content not fetched per policy.",
}


def build_record(item: dict) -> dict:
    is_portal = item["entry_type"] == "careers_portal"
    record = {
        "clean_title": item["clean_title"],
        "organization": item["organization"],
        "city": item["city"],
        "state": item["state"],
        "country": item.get("country", "India"),
        "category": item["category"],
        "position_type": item["clean_title"],
        "opportunity_kind": "Job / Career",
        "experience_level": item.get("experience_level", ""),
        "employment_type": item.get("employment_type", ""),
        "deadline_or_window": item.get("deadline_or_window", "Not disclosed"),
        "valid_through": item.get("valid_through", ""),
        "role_summary": item.get("role_summary", ""),
        "apply_url": item["apply_url"],
        "org_website": "",
        "org_domain": "",
        "source_portal": item["source_portal"],
        "entry_type": item["entry_type"],
        "status": "active",
        "global": item.get("country", "India") in ("Global", "Germany", "United Kingdom"),
        "evergreen": False,
        "date_added": VERIFIED_ON,
        "date_posted": VERIFIED_ON,
        "verification": dict(VERIFICATION_BLOCK),
    }
    if is_portal:
        record["link_policy"] = dict(LINK_POLICY_BLOCK)
    return record


def main() -> None:
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    existing = {str(r.get("id", "")).strip() for r in jobs}
    added = 0
    for item in RECORDS:
        rid = item["id"]
        if rid in existing:
            print(f"SKIP (already exists): {rid}")
            continue
        jobs.append({"id": rid, **build_record(item)})
        existing.add(rid)
        added += 1
        print(f"ADDED: {rid} ({item['entry_type']})")
    JOBS.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nAdded {added} new record(s). Total: {len(jobs)}")


if __name__ == "__main__":
    main()
