"""Repair the six pre-existing link-policy violations (27 Oct 2026).

Each record was published from a flyer with an organisation homepage as its
``apply_url``. Every entry below now points at the specific event/notice page,
and the one role that is no longer advertised is archived.

Idempotent: re-running only rewrites fields that still differ.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "public"
JOBS = PUBLIC / "jobs.json"
GLOBAL_JOBS = PUBLIC / "global_jobs.json"
ARCHIVE = PUBLIC / "archive.json"

TODAY = "2026-10-27"

# id -> fields to overwrite
FIXES = {
    "environmental-policy-and-climate-action-training-impri-impac": {
        "apply_url": (
            "https://www.impriindia.com/event/"
            "environmental-policy-and-climate-action/"
        ),
        "entry_type": "posting",
    },
    "ph-d-admission-2026-27-central-university-of-south-bihar": {
        "apply_url": (
            "https://www.cusb.ac.in/images/2026/admission_26/phd/phd_2026.pdf"
        ),
        "entry_type": "posting",
    },
    "junior-research-fellow-kscste-centre-for-water-resources-dev": {
        "apply_url": (
            "https://cwrdm.kerala.gov.in/"
            "walk-interview-post-junior-research-fellow"
        ),
        "org_website": "https://cwrdm.kerala.gov.in",
        "entry_type": "posting",
    },
    "the-big-sustainability-expo-2026-southern-sustainability-par": {
        "apply_url": "https://southernsustainability.co.uk/expo/",
        "org_website": "https://southernsustainability.co.uk",
        "org_domain": "southernsustainability.co.uk",
        "entry_type": "posting",
    },
    "9th-glf-investment-case-symposium-global-landscapes-forum-gl": {
        "apply_url": (
            "https://events.globallandscapesforum.org/"
            "9th-investment-case-symposium/"
        ),
        "entry_type": "posting",
    },
}

# The CPPR careers page (HTTP 200) advertises four openings and none of them is
# the Research Analyst (Project-Based) role, so the flyer record is no longer
# open and moves to the archive.
ARCHIVE_IDS = {
    "research-analyst-project-based-centre-for-public-policy-rese": {
        "apply_url": "https://www.cppr.in/careers",
        "date_archived": TODAY,
        "status": "archived",
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


def apply_fixes(records: list[dict], label: str) -> int:
    changed = 0
    for record in records:
        patch = FIXES.get(str(record.get("id", "")))
        if not patch:
            continue
        for key, value in patch.items():
            if record.get(key) != value:
                record[key] = value
                changed += 1
        print(f"  fixed {label}: {record['id']}")
    return changed


def main() -> int:
    jobs = load(JOBS)
    globals_ = load(GLOBAL_JOBS)
    archive = load(ARCHIVE)

    changed = apply_fixes(jobs, "jobs.json")
    changed += apply_fixes(globals_, "global_jobs.json")

    archived_ids = {str(record.get("id", "")) for record in archive}
    remaining = []
    moved = 0
    for record in jobs:
        patch = ARCHIVE_IDS.get(str(record.get("id", "")))
        if not patch:
            remaining.append(record)
            continue
        for key, value in patch.items():
            record[key] = value
        if record["id"] not in archived_ids:
            archive.append(record)
            archived_ids.add(record["id"])
        moved += 1
        print(f"  archived jobs.json: {record['id']}")

    if changed or moved:
        save(JOBS, remaining)
        save(GLOBAL_JOBS, globals_)
    if moved:
        save(ARCHIVE, archive)
    print(f"Done: {changed} field(s) updated, {moved} record(s) archived.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
