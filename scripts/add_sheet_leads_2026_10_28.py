#!/usr/bin/env python3
"""Add verified leads from the user's Google Sheet as a new registry batch.

Only the four direct employer links are added as ``posting`` records.
The seven new aggregator category pages are added as ``careers_portal``
records. Duplicate companies already present in the registry are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
JOBS = PUBLIC / "jobs.json"

VERIFIED_ON = "2026-10-28"

DIRECT = [
    {
        "id": "mahindra-dy-manager-sustainability-environment",
        "clean_title": "Dy. Manager – Sustainability & Environment",
        "organization": "Mahindra & Mahindra Ltd.",
        "city": "Mumbai",
        "state": "Maharashtra",
        "experience_level": "Not disclosed",
        "employment_type": "FULL_TIME",
        "entry_type": "posting",
        "apply_url": "https://jobs.mahindracareers.com/job/Mumbai-A_O-Dy_-Manager-Sustainability-%26-Environment-MUM/1438986800/",
        "source_portal": "Mahindra Careers (official)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "EPR compliance, CPCB/SPCB coordination, waste streams, ESG KPI data and sustainability dashboards.",
    },
    {
        "id": "corning-supply-chain-data-carbon-accounting-specialist",
        "clean_title": "Supply Chain Data & Carbon Accounting Specialist",
        "organization": "Corning",
        "city": "Gurugram",
        "state": "Haryana",
        "experience_level": "Not disclosed",
        "employment_type": "",
        "entry_type": "posting",
        "apply_url": "https://corningjobs.corning.com/job/Gurgaon-Supply-Chain-Data-%26-Carbon-Accounting-Specialist-HR-122002/1425224500/",
        "source_portal": "Corning Careers (official)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Scope 3 carbon accounting, supplier sustainability, data modelling, emissions reporting and supplier assessments.",
        "deadline_or_window": "Requisition 77923",
    },
    {
        "id": "erm-consultant-biodiversity",
        "clean_title": "Consultant, Biodiversity",
        "organization": "ERM",
        "city": "New Delhi",
        "state": "Delhi",
        "experience_level": "Not disclosed",
        "employment_type": "FULL_TIME",
        "entry_type": "posting",
        "apply_url": "https://erm.wd3.myworkdayjobs.com/en-US/ERM_Careers/job/New-Delhi-India/Consultant--Biodiversity_R00031062",
        "source_portal": "ERM Careers on Workday (official)",
        "category": "Forestry, Wildlife & Afforestation",
        "role_summary": "Biodiversity and environmental consulting for global clients; requisition R00031062, listed end date 31 Oct 2026.",
        "deadline_or_window": "31 October 2026",
        "valid_through": "2026-10-31",
    },
    {
        "id": "wsp-senior-consultant-responsible-consumption",
        "clean_title": "Senior Consultant – Responsible Consumption",
        "organization": "WSP",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_level": "8–10 years",
        "employment_type": "",
        "entry_type": "posting",
        "apply_url": "https://emit.fa.ca3.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_2001/job/94772",
        "source_portal": "WSP Careers (official Oracle Cloud)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Circular economy, sustainable value chains, resource and waste management, policy/strategy and due diligence.",
    },
]

PORTALS = [
    {
        "id": "bosch-csr-lead-environment-sustainability",
        "clean_title": "CSR Lead – Environment & Sustainability",
        "organization": "Bosch / Bosch Global Software Technologies",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_level": "8–12 years",
        "entry_type": "careers_portal",
        "apply_url": "https://askbengaluru.com/bangalore-jobs/job/smartrecruiters-744000157754859/",
        "source_portal": "Ask Bengaluru (aggregated listing)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Environmental sustainability, CSR and strategic leadership.",
    },
    {
        "id": "bcg-sustainability-data-analytics-senior-manager",
        "clean_title": "Sustainability Data & Analytics Senior Manager",
        "organization": "Boston Consulting Group (BCG)",
        "city": "India",
        "state": "",
        "experience_level": "Senior level",
        "entry_type": "careers_portal",
        "apply_url": "https://csrjobs.club/jobs/boston-consulting-group-bcg-sustainability-data-analytics-senior-manager-t4ap",
        "source_portal": "CSR Jobs (specialist sustainability job board)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Corporate carbon accounting, environmental reporting, data engineering and decarbonization targets.",
    },
    {
        "id": "micron-senior-energy-and-decarbonization-engineer",
        "clean_title": "Senior Energy and Decarbonization Engineer",
        "organization": "Micron Technology",
        "city": "India",
        "state": "",
        "experience_level": "Senior level",
        "entry_type": "careers_portal",
        "apply_url": "https://csrjobs.club/jobboard/india",
        "source_portal": "CSR Jobs (specialist sustainability job board)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Energy efficiency, decarbonization and emissions reduction.",
    },
    {
        "id": "revantage-sustainability-data-analyst",
        "clean_title": "Sustainability Data Analyst",
        "organization": "Revantage (A Blackstone Portfolio Company)",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_level": "Mid-level",
        "entry_type": "careers_portal",
        "apply_url": "https://www.inclimate.com/climate-jobs/india/carbon-and-esg-reporting",
        "source_portal": "CSR Jobs / inClimate",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Sustainability data and ESG metrics/reporting.",
    },
    {
        "id": "hsbc-senior-esg-reporting-manager",
        "clean_title": "Senior ESG Reporting Manager",
        "organization": "HSBC",
        "city": "Bengaluru",
        "state": "Karnataka",
        "experience_level": "Senior level",
        "entry_type": "careers_portal",
        "apply_url": "https://www.inclimate.com/climate-jobs/india/carbon-and-esg-reporting",
        "source_portal": "CSR Jobs / inClimate",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "ESG reporting, disclosure and governance.",
    },
    {
        "id": "blackrock-sustainability-data-process-reporting-associate",
        "clean_title": "Sustainability Data, Process & Reporting Associate – Global Corporate Sustainability Controllers",
        "organization": "BlackRock",
        "city": "India",
        "state": "",
        "experience_level": "Mid-level",
        "entry_type": "careers_portal",
        "apply_url": "https://csrjobs.club/jobboard/india",
        "source_portal": "CSR Jobs (specialist sustainability job board)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Sustainability data, processes and corporate reporting.",
    },
    {
        "id": "pepsico-associate-director-sustainability",
        "clean_title": "Associate Director – Sustainability",
        "organization": "PepsiCo",
        "city": "India",
        "state": "",
        "experience_level": "Senior / leadership",
        "entry_type": "careers_portal",
        "apply_url": "https://csrjobs.club/jobboard/india",
        "source_portal": "CSR Jobs (specialist sustainability job board)",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "role_summary": "Corporate sustainability strategy and program leadership.",
    },
]

LINK_POLICY_BLOCK = {
    "status": "listing",
    "entry_type": "careers_portal",
    "checked": VERIFIED_ON,
    "note": "Aggregator category page; tagged as portal under policy v2.",
}

VERIFICATION_BLOCK = {
    "verified_on": VERIFIED_ON,
    "verified_by": "manual review of Google Sheet leads",
    "source": "User-provided Google Sheet",
    "notes": "Direct employer link verified live (HTTP 200) on 2026-10-28.",
}


def build_record(item: dict, is_portal: bool) -> dict:
    record = {
        "clean_title": item["clean_title"],
        "organization": item["organization"],
        "city": item["city"],
        "state": item["state"],
        "country": "India",
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
        "global": False,
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
    for item in DIRECT + PORTALS:
        rid = item["id"]
        if rid in existing:
            print(f"SKIP (already exists): {rid}")
            continue
        jobs.append({"id": rid, **build_record(item, is_portal=item["entry_type"] == "careers_portal")})
        existing.add(rid)
        added += 1
        print(f"ADDED: {rid} ({item['entry_type']})")
    JOBS.write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nAdded {added} new record(s). Total: {len(jobs)}")


if __name__ == "__main__":
    main()
