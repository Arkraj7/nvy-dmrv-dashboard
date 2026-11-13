#!/usr/bin/env python3
"""Archive the records confirmed dead, unverifiable or duplicated on 13 Nov 2026.

Evidence for every record is recorded in ``archive_reason`` and the
``verification`` note. Nothing is deleted; archived pages render no apply link.

  dead_page         the employer's own page says the post is filled/closed
  unverified listing the cited page does not advertise the vacancy at all
                    (careers root / index page), so it cannot be shown as open
  duplicate listing  the same vacancy already exists under another record

Run from the repository root:
    py scripts/archive_stale_and_dupes_2026_11_13.py [--apply]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
TODAY = "2026-11-13"

FILES = {
    "jobs.json": "archive.json",
    "global_jobs.json": "global_archive.json",
}

# id -> (reason, evidence note, replacement deadline text)
TARGETS = {
    # --- employer page says the vacancy is closed -------------------------
    "mahindra-dy-manager-sustainability-environment": (
        "dead_page",
        "Employer page states 'Sorry, this position has been filled.'",
        "Closed - position filled",
    ),
    "nrdc-india-renewable-energy-specialists-2026": (
        "dead_page",
        "NRDC India job page states 'No Longer Accepting Applications'.",
        "Closed - no longer accepting applications",
    ),
    "gmr-associate-manager-environment-sustainability-nagpur-2026": (
        "dead_page",
        "GMR careers page states 'Sorry, this position has been filled.'",
        "Closed - position filled",
    ),
    "cactus-editor-environmental-science-remote-2026": (
        "dead_page",
        "Cactus Global job page no longer exists (posting removed).",
        "Closed - posting removed",
    ),
    # --- cited page does not advertise the vacancy ------------------------
    "jrf-air-quality-atmospheric-chemistry-iit-delhi": (
        "unverified listing",
        "The cited IIT Delhi jobs index lists only post-doctoral and faculty "
        "notices; it contains no JRF or air-quality vacancy, so this record "
        "cannot be confirmed as open.",
        "Not verifiable at source",
    ),
    "jrf-tiger-ecology-landscape-connectivity-wii-dehradun": (
        "unverified listing",
        "The cited WII recruitment page lists no research-fellow vacancy; the "
        "only tiger items are the AITE 2026 technical-assistant and NTCA "
        "consultant adverts, so this record cannot be confirmed as open.",
        "Not verifiable at source",
    ),
    "research-associate-biodiversity-ecological-genomics-ncbs": (
        "unverified listing",
        "Apply URL is the NCBS careers root, not a notice for this post; no "
        "deadline was recorded and the record passed the 30-day re-check limit "
        "(added 2026-10-13).",
        "Not verifiable at source",
    ),
    "phd-climate-dynamics-earth-system-modelling-iisc-bengaluru": (
        "unverified listing",
        "Apply URL is the IISc careers root, not a notice for this post; no "
        "deadline was recorded and the record passed the 30-day re-check limit "
        "(added 2026-10-12).",
        "Not verifiable at source",
    ),
    "doctoral-fellowship-climate-policy-sustainable-development-teri": (
        "unverified listing",
        "Apply URL is the TERI careers root, not a notice for this fellowship; "
        "no deadline was recorded and the record passed the 30-day re-check "
        "limit (added 2026-10-11).",
        "Not verifiable at source",
    ),
    # --- same vacancy already carried by another record -------------------
    "bcg-sustainability-data-analytics-senior-manager": (
        "duplicate listing",
        "Same BCG vacancy already published as "
        "bcg-sustainability-data-analytics-senior-manager-gurgaon-2026.",
        "See the duplicate notice",
    ),
    "national-forest-foundation-reforestation-senior-specialist-remote-2026": (
        "duplicate listing",
        "Same NFF vacancy already published as "
        "national-forest-foundation-reforestation-senior-specialist-2026.",
        "See the duplicate notice",
    ),
    "social-change-school-ncf-project-coordinator-2026": (
        "duplicate listing",
        "Same NCF vacancy already published as "
        "ncf-project-coordinator-el-nino-2026 (same source link and deadline).",
        "See the duplicate notice",
    ),
}

KEEPERS = {
    "bcg-sustainability-data-analytics-senior-manager":
        "bcg-sustainability-data-analytics-senior-manager-gurgaon-2026",
    "national-forest-foundation-reforestation-senior-specialist-remote-2026":
        "national-forest-foundation-reforestation-senior-specialist-2026",
    "social-change-school-ncf-project-coordinator-2026":
        "ncf-project-coordinator-el-nino-2026",
}


def main() -> int:
    apply = "--apply" in sys.argv
    moved_total = 0

    for active_name, archive_name in FILES.items():
        active_path = PUBLIC / active_name
        archive_path = PUBLIC / archive_name
        active = json.loads(active_path.read_text(encoding="utf-8"))
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
        archive_ids = {r.get("id") for r in archive}

        keep, moved = [], []
        for rec in active:
            meta = TARGETS.get(rec.get("id"))
            if not meta:
                keep.append(rec)
                continue
            reason, note, deadline_text = meta
            rec["status"] = "archived"
            rec["date_archived"] = TODAY
            rec["archive_reason"] = reason
            rec["deadline_or_window"] = deadline_text
            rec["reverify_after"] = ""
            if rec["id"] in KEEPERS:
                rec["duplicate_of"] = KEEPERS[rec["id"]]
            verification = rec.setdefault("verification", {})
            verification["method"] = "manual-review"
            verification["verified_at"] = TODAY
            verification["archived_reason"] = note
            moved.append(rec)
            print(f"{active_name}: archive {rec['id']} ({reason})")

        new_archive = moved + [r for r in archive if r.get("id") not in {m['id'] for m in moved}]
        moved_total += len(moved)
        print(f"  {active_name} {len(active)} -> {len(keep)}; "
              f"{archive_name} {len(archive)} -> {len(new_archive)}; "
              f"ids already archived: {len(archive_ids)}")

        if apply:
            active_path.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
            archive_path.write_text(json.dumps(new_archive, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"total archived: {moved_total}")
    if not apply:
        print("Dry run only; re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
