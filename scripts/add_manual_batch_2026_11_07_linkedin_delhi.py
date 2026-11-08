"""Add the 7 November 2026 LinkedIn Delhi NCR ESG/climate batch.

Source: the LinkedIn Jobs search results shared by the site owner
(keyword search climate / environment / ESG / sustainability, Past week
filter, sorted by date; Greater Delhi Area). apply_url always comes from
the source (LinkedIn /jobs/view/<id> page). LinkedIn is bot-blocked, so
every record is kept as UNKNOWN_KEEP per docs/LINK_POLICY.md v2 -- URLs
are validated by pattern only, never fetched or scraped.

Facts come only from the listing headers above (title, employer, place,
posted age, salary where stated). No JD, qualification, skill, or
deadline is invented: undisclosed fields stay blank / "Not disclosed",
deadline_or_window is "Rolling / Open", and valid_through is
posted date + 30 days with a day-15 recheck.

Run from the repository root:
    py scripts/add_manual_batch_2026_11_07_linkedin_delhi.py
The script is idempotent: existing ids are left untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"
GLOBAL_PATH = ROOT / "public" / "global_jobs.json"

VERIFIED_AT = "2026-11-07"


def base_record(date_posted, valid_through, reverify_after, **overrides):
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
        "experience_level": "",
        "employment_type": "FULL_TIME",
        "deadline_or_window": "Rolling / Open",
        "valid_through": valid_through,
        "qualification_summary": "",
        "compensation_or_fellowship": "Not disclosed - see official job description",
        "role_summary": "",
        "key_responsibilities": [],
        "must_have_skills": [],
        "application_tip": "",
        "apply_url": "",
        "org_website": "",
        "org_domain": "",
        "source_portal": "LinkedIn Jobs - Delhi NCR ESG search (owner-shared)",
        "entry_type": "posting",
        "status": "active",
        "global": False,
        "evergreen": False,
        "date_added": date_posted,
        "date_posted": date_posted,
        "title_hi": "",
        "summary_hi": "",
        "academic_meta": {},
        "selection_process": "",
        "reverify_after": reverify_after,
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-verified",
            "source": "LinkedIn Jobs listing (owner-shared)",
            "http_status": "UNKNOWN_KEEP",
        },
        "id": "",
    }
    record.update(overrides)
    return record


INDIA_RECORDS = [
    base_record(
        date_posted="2026-11-06", valid_through="2026-12-06", reverify_after="2026-11-21",
        id="crisil-esg-sustainability-research-analyst-gurugram-2026",
        clean_title="Research / Senior Research Analyst - ESG & Sustainability",
        organization="Crisil",
        city="Gurugram",
        state="Haryana",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="ESG and sustainability research analyst role at Crisil, Gurugram. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486766816",
    ),
    base_record(
        date_posted="2026-11-07", valid_through="2026-12-07", reverify_after="2026-11-22",
        id="ey-consultant-business-consulting-transformation-delivery-delhi-2026",
        clean_title="Consultant - Business Consulting PI - GOV - CNS - BC - Transformation Delivery - New Delhi",
        organization="EY",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Business consulting transformation delivery consultant role at EY, New Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4459956508",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="smart-freight-centre-junior-partnerships-manager-delhi-2026",
        clean_title="Junior Partnerships Manager",
        organization="Smart Freight Centre",
        city="Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Junior partnerships manager role at Smart Freight Centre (Delhi, hybrid). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4484447918",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="erm-consultant-esg-reporting-disclosures-delhi-2026",
        clean_title="Consultant - ESG Reporting & Disclosures",
        organization="ERM",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="ESG reporting and disclosures consultant role at ERM, New Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4485030205",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="pwc-sustainability-associate-2-gurugram-2026",
        clean_title="US DAT - Sustainability-Associate 2",
        organization="PwC Acceleration Center India",
        city="Gurugram",
        state="Haryana",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Sustainability associate role at PwC Acceleration Center India, Gurugram. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4476459696",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="erm-senior-consultant-lifecycle-assessment-delhi-2026",
        clean_title="Senior Consultant - Lifecycle Assessment / LCA",
        organization="ERM",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Senior",
        role_summary="Senior consultant - lifecycle assessment (LCA) role at ERM, New Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4485065952",
    ),
    base_record(
        date_posted="2026-11-05", valid_through="2026-12-05", reverify_after="2026-11-20",
        id="climate-policy-initiative-communications-associate-delhi-2026",
        clean_title="Communications Associate - Content and Editing",
        organization="Climate Policy Initiative",
        city="Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Communications associate (content and editing) role at Climate Policy Initiative, Delhi (hybrid). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4474904312",
    ),
    base_record(
        date_posted="2026-11-05", valid_through="2026-12-05", reverify_after="2026-11-20",
        id="ey-associate-consultant-business-consulting-delhi-2026",
        clean_title="Associate Consultant - Business Consulting PI - GOV - CNS - BC - Transformation Delivery - New Delhi",
        organization="EY",
        city="Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Associate consultant - business consulting transformation delivery role at EY, Delhi (on-site). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4460200393",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="swaniti-global-associate-communications-delhi-2026",
        clean_title="Associate - Communications",
        organization="Swaniti Global",
        city="Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Associate - communications role at Swaniti Global, Delhi (on-site). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486354124",
    ),
    base_record(
        date_posted="2026-11-02", valid_through="2026-12-02", reverify_after="2026-11-17",
        id="gain-manager-climate-nutrition-delhi-2026",
        clean_title="Manager, Climate and Nutrition",
        organization="Global Alliance for Improved Nutrition (GAIN)",
        city="Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Senior",
        role_summary="Manager, climate and nutrition role at GAIN, Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486168114",
    ),
    base_record(
        date_posted="2026-11-05", valid_through="2026-12-05", reverify_after="2026-11-20",
        id="systemiq-program-lead-delhi-remote-2026",
        clean_title="Program Lead",
        organization="Systemiq Ltd.",
        city="New Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Program lead role at Systemiq Ltd. (New Delhi, remote). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4485093867",
    ),
    base_record(
        date_posted="2026-11-06", valid_through="2026-12-06", reverify_after="2026-11-21",
        id="wri-india-junior-program-associate-freight-delhi-2026",
        clean_title="Junior Program Associate - Freight",
        organization="WRI India",
        city="New Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Entry Level / Fellowship",
        role_summary="Junior program associate - freight role at WRI India, New Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486229296",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="icf-consultant-natural-gas-fuels-delhi-2026",
        clean_title="Consultant - Natural Gas & Fuels",
        organization="ICF",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Consultant - natural gas and fuels role at ICF, New Delhi. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4487009721",
    ),
    base_record(
        date_posted="2026-11-04", valid_through="2026-12-04", reverify_after="2026-11-19",
        id="tuv-sud-assistant-manager-operations-ess-gurugram-2026",
        clean_title="Asst. Manager / Manager - Operations (Environment, Social & Sustainability Services)",
        organization="TÜV SÜD",
        city="Gurugram",
        state="Haryana",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Assistant manager / manager - operations (environment, social and sustainability services) role at TÜV SÜD, Gurugram (on-site). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4476468177",
    ),
    base_record(
        date_posted="2026-11-05", valid_through="2026-12-05", reverify_after="2026-11-20",
        id="climate-policy-initiative-senior-associate-contract-operations-2026",
        clean_title="Senior Associate - Contract & Operations",
        organization="Climate Policy Initiative",
        city="Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Senior associate - contract and operations role at Climate Policy Initiative, Delhi (hybrid). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486597797",
    ),
    base_record(
        date_posted="2026-11-05", valid_through="2026-12-05", reverify_after="2026-11-20",
        id="weekday-applied-economics-policy-advisor-delhi-2026",
        clean_title="Applied Economics Policy Advisor",
        organization="Weekday (YC W21)",
        city="Delhi",
        state="Delhi",
        category="Climate Policy, Think-Tanks & Fellowships",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        compensation_or_fellowship="₹1.1M-1.4M INR/yr",
        role_summary="Applied economics policy advisor role at Weekday (YC W21), Delhi (on-site). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="Easy Apply on the LinkedIn job page. See the full job description for requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4485810244",
    ),
    base_record(
        date_posted="2026-11-06", valid_through="2026-12-06", reverify_after="2026-11-21",
        id="unv-sustainable-finance-specialist-iwm-delhi-remote-2026",
        clean_title="Sustainable Finance Specialist - Integrated Watershed Management",
        organization="United Nations Volunteers - Asia & the Pacific",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Young Professional / Consultant (Contractual)",
        opportunity_kind="Job / Career",
        experience_level="Mid-Senior (3-6 Years)",
        employment_type="CONTRACTOR",
        role_summary="Sustainable finance specialist - integrated watershed management assignment (New Delhi, remote) with the UN Volunteers - Asia & the Pacific. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486993355",
    ),
    base_record(
        date_posted="2026-11-07", valid_through="2026-12-07", reverify_after="2026-11-22",
        id="aecom-aquatic-ecologists-gurugram-2026",
        clean_title="Aquatic Ecologists - Freshwater, Marine & Hydro-ecology Specialists",
        organization="AECOM",
        city="Gurugram",
        state="Haryana",
        category="Forestry, Wildlife & Afforestation",
        position_type="Full-Time Corporate / NGO",
        experience_level="Mid-Senior (3-6 Years)",
        role_summary="Aquatic ecologists (freshwater, marine and hydro-ecology specialists) role at AECOM, Gurugram (hybrid). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4486316030",
    ),
    base_record(
        date_posted="2026-11-03", valid_through="2026-12-03", reverify_after="2026-11-18",
        id="bcg-sustainability-data-analytics-senior-manager-gurgaon-2026",
        clean_title="Sustainability Data & Analytics Senior Manager",
        organization="Boston Consulting Group (BCG)",
        city="Gurugram",
        state="Haryana",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="Senior",
        role_summary="Sustainability data and analytics senior manager role at Boston Consulting Group (BCG), Gurgaon. Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="See the LinkedIn job page for full responsibilities and requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4477534018",
    ),
    base_record(
        date_posted="2026-11-03", valid_through="2026-12-03", reverify_after="2026-11-18",
        id="aurassure-government-tender-bid-management-specialist-delhi-2026",
        clean_title="Govt. Tender & Bid Management Specialist (Delhi)",
        organization="Aurassure",
        city="New Delhi",
        state="Delhi",
        category="ESG, Carbon Markets & Corporate Sustainability",
        position_type="Full-Time Corporate / NGO",
        experience_level="1-3 Years",
        role_summary="Government tender and bid management specialist role at Aurassure (New Delhi, on-site). Full responsibilities and requirements are on the LinkedIn job page.",
        application_tip="Easy Apply on the LinkedIn job page. See the full job description for requirements.",
        apply_url="https://www.linkedin.com/jobs/view/4485742379",
    ),
]


def main():
    india = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    existing_ids = {r.get("id") for r in india}
    existing_urls = {str(r.get("apply_url", "")).rstrip("/") for r in india}

    added = 0
    new_records = []
    for rec in INDIA_RECORDS:
        if rec["id"] in existing_ids or str(rec["apply_url"]).rstrip("/") in existing_urls:
            print(f"SKIP (exists): {rec['id']}")
            continue
        new_records.append(rec)
        added += 1
        print(f"ADD: {rec['id']}")

    # Prepend newest-first so the static file order matches the live
    # sortByDateDesc rendering; existing records keep their order.
    new_records.sort(key=lambda r: (str(r.get("date_added") or ""), str(r.get("id") or "")), reverse=True)
    india = new_records + india

    JOBS_PATH.write_text(json.dumps(india, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nAdded {added}. Total India: {len(india)}")


if __name__ == "__main__":
    main()
