#!/usr/bin/env python3
"""Apply the 28 October 2026 health-check link and record fixes.

Idempotent:

* retag five workshop/event listing URLs from ``posting`` to ``careers_portal``
  (the policy's only non-direct link type);
* replace the three confirmed dead links with verified live destinations;
* archive the concluded TERI WSDS 2026 record instead of leaving a dead apply
  link on an active page.

Run from the repository root:

    py scripts/fix_health_check_2026_10_28.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

RETAG_IDS = {
    "state-workshop--powering-uttar-pradesh-s-clean-energy-future",
    "marine-marshals-programme-2026-centre-for-science-and-enviro",
    "conflict-and-commons-community-centred-land-governance-for",
    "climate-fresk-workshop-climate-fresk-various-hosts",
    "climate-fresk-facilitator-training-climate-fresk",
}

LINK_REPLACEMENTS = {
    "future-earth-global-opportunities": "https://futureearth.org/about/careers/",
    "mopga-2027-visiting-fellowship-make-our-planet-great-again-c": (
        "https://campusfrance.smapply.io/prog/mopga_2027/"
    ),
}

TERI_ID = "world-sustainable-development-summit-wsds-2026-teri-the-ener"
TERI_ARCHIVE = {
    "status": "archived",
    "date_archived": "2026-10-28",
    "archive_reason": (
        "Official WSDS 2026 page returned 404; the event has concluded. "
        "Preserved for reference only."
    ),
}

LINK_POLICY_BLOCK = {
    "status": "listing",
    "entry_type": "careers_portal",
    "checked": "2026-10-28",
    "note": (
        "Official workshop/event listing page. No single-vacancy URL is "
        "exposed, so the record is tagged as a portal under policy v2."
    ),
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


def main() -> None:
    jobs_path = PUBLIC / "jobs.json"
    global_path = PUBLIC / "global_jobs.json"
    archive_path = PUBLIC / "archive.json"

    jobs = load(jobs_path)
    global_jobs = load(global_path)
    archive = load(archive_path)

    retagged = 0
    for record in jobs:
        if str(record.get("id")) not in RETAG_IDS:
            continue
        if record.get("entry_type") != "careers_portal":
            record["entry_type"] = "careers_portal"
            retagged += 1
        record.setdefault("link_policy", dict(LINK_POLICY_BLOCK))

    replaced = 0
    for record in jobs + global_jobs:
        new_url = LINK_REPLACEMENTS.get(str(record.get("id")))
        if new_url and record.get("apply_url") != new_url:
            record["apply_url"] = new_url
            replaced += 1

    archived = False
    teri = next((record for record in jobs if str(record.get("id")) == TERI_ID), None)
    if teri is not None:
        jobs = [record for record in jobs if str(record.get("id")) != TERI_ID]
        teri.update(TERI_ARCHIVE)
        if not any(str(record.get("id")) == TERI_ID for record in archive):
            archive.append(teri)
        archived = True
    else:
        for record in archive:
            if str(record.get("id")) == TERI_ID:
                changed = {
                    key: value
                    for key, value in TERI_ARCHIVE.items()
                    if record.get(key) != value
                }
                record.update(TERI_ARCHIVE)
                archived = bool(changed)

    save(jobs_path, jobs)
    save(global_path, global_jobs)
    save(archive_path, archive)

    print(f"Retagged as careers_portal: {retagged}")
    print(f"Replaced apply URLs: {replaced}")
    print(f"Archived/updated TERI WSDS record: {archived}")


if __name__ == "__main__":
    main()
