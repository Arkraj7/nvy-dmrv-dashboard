#!/usr/bin/env python3
"""Registry refresh for 13 November 2026.

Three jobs:

1. Add two official Government of India vacancies that were missing from the
   registry and are published on the National CAMPA "Work with Us" page
   (page last reviewed 2026-11-12):
     - National Authority CAMPA - 08 Young Professionals, New Delhi
     - NAEB, MoEF&CC          - 02 Research Associates, New Delhi
   Both circulars are scanned PDFs, so only the facts visible in the published
   circular titles are recorded: post name, number of posts, office and the
   official circular link. Pay, eligibility and deadlines are left to the
   circular itself rather than guessed.

2. Move active records whose advertised deadline has already passed into the
   matching archive file (status "archived" + date_archived), matching
   ``cleanup_2026_10_31.archive_expired``. Records advertised as
   "Rolling / Open" are still open at source, so their validity horizon is
   simply refreshed to the new reverify date instead of being archived.

3. Nothing is ever deleted: archived records keep their file entry.

Run from the repository root:
    py scripts/update_registry_2026_11_13.py [--apply]

Without ``--apply`` the script only prints what it would change.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from add_manual_batch_2026_11_08_linkedin import (  # noqa: E402
    GLOBAL_ARCHIVE_PATH,
    GLOBAL_PATH,
    JOBS_PATH,
    base_record,
    merge_active,
    merge_archive,
)

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = ROOT / "public" / "archive.json"

VERIFIED_AT = "2026-11-13"
SOURCE_GOV = "National CAMPA / MoEF&CC official vacancy page (Work with Us)"

CAMPA_CIRCULAR = (
    "https://nationalcampa.nic.in/dashboard/job_circularsPDF/695f604a4cff2.pdf"
)
NAEB_CIRCULAR = (
    "https://nationalcampa.nic.in/dashboard/job_circularsPDF/6a01a2c1a2e27.pdf"
)


def gov_record(**kw):
    rec = base_record(
        source_portal=SOURCE_GOV,
        entry_type="posting",
        country="India",
        valid_through="2026-12-13",
        reverify_after="2026-11-27",
        **kw,
    )
    rec["verification"] = {
        "verified_at": VERIFIED_AT,
        "method": "official-page-verified",
        "source": "National CAMPA Work with Us page (last reviewed 2026-11-12)",
        "http_status": 200,
    }
    rec["date_added"] = VERIFIED_AT
    rec["date_posted"] = VERIFIED_AT
    return rec


NEW_INDIA = [
    gov_record(
        id="national-campa-young-professionals-2026",
        clean_title="Young Professional - National Authority CAMPA (08 posts)",
        organization="National Authority CAMPA, MoEFCC",
        city="New Delhi",
        state="Delhi",
        category="Forestry, Wildlife & Afforestation",
        position_type="Young Professional / Consultant (Contractual)",
        opportunity_kind="Job / Career",
        experience_level="Entry Level / Fellowship",
        employment_type="CONTRACTOR",
        deadline_or_window="See official circular",
        qualification_summary="As per the official vacancy circular; see the linked PDF.",
        compensation_or_fellowship="Not disclosed in the published circular title - see official circular",
        role_summary=(
            "Eight Young Professional positions in the National Authority CAMPA office, "
            "New Delhi, supporting compensatory afforestation appraisal, monitoring and "
            "evaluation work. Post name, number of posts and office are as published in the "
            "official circular; pay, eligibility and the last date are stated in the circular."
        ),
        key_responsibilities=[],
        must_have_skills=[],
        application_tip=(
            "Download the official circular from the National CAMPA Work with Us page and "
            "follow the application method it prescribes."
        ),
        apply_url=CAMPA_CIRCULAR,
        org_website="https://nationalcampa.nic.in",
        org_domain="nationalcampa.nic.in",
        evergreen=False,
    ),
    gov_record(
        id="naeb-moefcc-research-associates-2026",
        clean_title="Research Associate - NAEB, MoEF&CC (02 posts)",
        organization="National Afforestation and Eco-Development Board (NAEB), MoEF&CC",
        city="New Delhi",
        state="Delhi",
        category="Research Associate & Project Staff (Contractual)",
        position_type="Project Associate / Research Associate",
        opportunity_kind="Job / Career",
        experience_level="1-3 Years",
        employment_type="CONTRACTOR",
        deadline_or_window="See official circular",
        qualification_summary="As per the official vacancy circular; see the linked PDF.",
        compensation_or_fellowship="Not disclosed in the published circular title - see official circular",
        role_summary=(
            "Two Research Associate positions in the National Afforestation and "
            "Eco-Development Board, MoEF&CC, New Delhi. Post name, number of posts and "
            "office are as published in the official circular; eligibility, pay and the "
            "last date are stated in the circular."
        ),
        key_responsibilities=[],
        must_have_skills=[],
        application_tip=(
            "Download the official circular from the National CAMPA Work with Us page and "
            "follow the application method it prescribes."
        ),
        apply_url=NAEB_CIRCULAR,
        org_website="https://nationalcampa.nic.in",
        org_domain="nationalcampa.nic.in",
        evergreen=False,
    ),
]

ROLLING_PAT = re.compile(r"rolling|open until filled|ongoing", re.I)
DATE_PAT = re.compile(
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{4})",
    re.I,
)
MONTHS = {
    name.lower(): number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}


def deadline_date(text: str):
    """Return the explicit deadline date in the text, else None."""
    t = str(text or "")
    m = DATE_PAT.search(t)
    if not m:
        return None
    try:
        return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    except (KeyError, ValueError):
        return None


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def refresh_registry(active_path: Path, archive_path: Path, label: str, today: date):
    active = load(active_path)
    archive = load(archive_path)
    archive_by_id = {str(r.get("id")): r for r in archive}

    kept, archived, refreshed = [], [], []
    for job in active:
        if job.get("status") != "active":
            kept.append(job)
            continue
        window = str(job.get("deadline_or_window") or "")
        if ROLLING_PAT.search(window):
            # Still open at source; extend the validity horizon instead.
            job["valid_through"] = (today + timedelta(days=30)).isoformat()
            job["reverify_after"] = (today + timedelta(days=14)).isoformat()
            refreshed.append(job.get("id"))
            kept.append(job)
            continue
        dl = deadline_date(window)
        if dl and dl < today:
            job["status"] = "archived"
            job.setdefault("date_archived", today.isoformat())
            job["archive_reason"] = "deadline passed"
            if job.get("id") in archive_by_id:
                archive_by_id[job["id"]].setdefault("date_archived", today.isoformat())
            else:
                archive_by_id[job["id"]] = job
            archived.append((job.get("id"), window))
            continue
        kept.append(job)

    archive_out = sorted(
        archive_by_id.values(),
        key=lambda r: (str(r.get("date_archived") or ""), str(r.get("id") or "")),
        reverse=True,
    )
    print(f"[{label}] active {len(active)} -> {len(kept)}; archive {len(archive)} -> {len(archive_out)}")
    for rid, window in archived:
        print(f"   archived {rid} (deadline {window})")
    for rid in refreshed:
        print(f"   refreshed rolling record {rid}")
    return kept, archive_out


def main() -> int:
    apply = "--apply" in sys.argv
    today = date(2026, 11, 13)

    if apply:
        merge_active(JOBS_PATH, NEW_INDIA, False)

    india_active = load(JOBS_PATH)
    print(f"India active after merge: {len(india_active)}")
    for rec in NEW_INDIA:
        print(f"   added {rec['id']}")

    kept, arch = refresh_registry(JOBS_PATH, ARCHIVE_PATH, "India", today)
    gkept, garch = refresh_registry(GLOBAL_PATH, GLOBAL_ARCHIVE_PATH, "Global", today)

    if apply:
        save(JOBS_PATH, kept)
        save(ARCHIVE_PATH, arch)
        save(GLOBAL_PATH, gkept)
        save(GLOBAL_ARCHIVE_PATH, garch)
        print("Applied.")
    else:
        print("Dry run only; re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
