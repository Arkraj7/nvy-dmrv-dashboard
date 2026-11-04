"""Add the Axiom GIS Trainee (Navi Mumbai) walk-in opportunity.

Source: user-shared LinkedIn/WhatsApp posting (100+ GIS Trainee positions).
apply_url is the employer email supplied in the posting.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS_PATH = ROOT / "public" / "jobs.json"

VERIFIED_AT = "2026-11-04"
DATE_ADDED = "2026-11-04"


def main():
    jobs = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    existing = {r.get("id") for r in jobs}

    record = {
        "id": "axiom-gis-trainee-navi-mumbai-2026",
        "date_added": DATE_ADDED,
        "date_posted": DATE_ADDED,
        "clean_title": "GIS Trainee",
        "title_hi": "",
        "organization": "Axiom Group",
        "state": "Maharashtra",
        "city": "Navi Mumbai (Mahape, Ghansoli)",
        "category": "GIS, Remote Sensing & Earth Observation",
        "experience_level": "Entry Level / Fellowship",
        "position_type": "Fellowship / Internship",
        "opportunity_kind": "Internship",
        "employment_type": "CONTRACTOR",
        "deadline_or_window": "Walk-in 3-7 November 2026",
        "region": "India",
        "country": "India",
        "qualification_summary": "Third-year B.A. (TYBA) students and graduates; interns and freshers welcome. Basic familiarity with GIS concepts is an advantage; training is provided on the job.",
        "compensation_or_fellowship": "Stipend Rs. 12,000-15,000 per month for the 6-month engagement",
        "role_summary": "Axiom is hiring 100+ GIS Trainees for a 6-month, day-shift engagement in Navi Mumbai. Walk-in interviews run 3-7 November 2026 at Rupa Solitaire, Mahape, Ghansoli. An entry point into GIS, mapping and geospatial technology for students and freshers, with on-the-job training and a monthly stipend.",
        "key_responsibilities": [
            "GIS digitisation, mapping and attribute data entry",
            "Geospatial data cleaning, QA and basic analysis",
            "Support to mapping and survey projects under senior GIS staff",
            "Working with QGIS/ArcGIS for map production and updates",
            "Maintaining spatial databases and project records",
        ],
        "must_have_skills": ["GIS basics", "Mapping", "QGIS or ArcGIS", "MS Excel", "Attention to detail", "Willingness to learn"],
        "application_tip": "Walk in between 3-7 November 2026 at Rupa Solitaire, Mahape, Ghansoli, Navi Mumbai, carrying an updated resume and ID proof. Alternatively email your resume to Recruitment@axiomgroup.in or call 8655659575. Arrive early; walk-ins are on a first-come basis.",
        "apply_url": "mailto:Recruitment@axiomgroup.in",
        "org_website": "",
        "org_domain": "",
        "source_portal": "LinkedIn/WhatsApp post (user-shared)",
        "entry_type": "posting",
        "status": "active",
        "global": False,
        "evergreen": False,
        "valid_through": "2026-11-07",
        "title_hi": "",
        "summary_hi": "",
        "academic_meta": {},
        "selection_process": "Walk-in interview",
        "reverify_after": "2026-11-07",
        "verification": {
            "verified_at": VERIFIED_AT,
            "method": "manual-batch-verified",
            "source": "User-shared posting",
            "http_status": "UNKNOWN_KEEP",
        },
    }

    if record["id"] in existing:
        print(f"SKIP (exists): {record['id']}")
        return

    jobs.append(record)
    JOBS_PATH.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ADD: {record['id']}  (total India: {len(jobs)})")


if __name__ == "__main__":
    main()
