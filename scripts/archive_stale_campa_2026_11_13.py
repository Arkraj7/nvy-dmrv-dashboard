#!/usr/bin/env python3
"""Archive the two stale National CAMPA / NAEB circulars (13 Nov 2026).

Both PDFs are still linked from the official "Work with Us" page, so the
URL check passed, but the circulars themselves are old:

  * 695f604a4cff2.pdf - 08 Young Professionals, National Authority CAMPA
    PDF modified 2026-01-08; the advertised last date was 28 January 2026.
  * 6a01a2c1a2e27.pdf - 02 Research Associates, NAEB, MoEF&CC
    PDF modified 2026-05-08.

Government sites leave closed circulars online, so the page listing alone is
not evidence that a post is open. Both records move to the archive with the
circular date recorded; nothing is deleted.

Run from the repository root:
    py scripts/archive_stale_campaigna_2026_11_13.py [--apply]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "public" / "jobs.json"
ARCHIVE = ROOT / "public" / "archive.json"

TODAY = "2026-11-13"

STALE = {
    "national-campa-young-professionals-2026": (
        "2026-01-08",
        "Circular dated 2026-01-08; advertised last date 28 January 2026. "
        "Still linked from the official Work with Us page, but the vacancy is closed.",
    ),
    "naeb-moefcc-research-associates-2026": (
        "2026-05-08",
        "Circular dated 2026-05-08. Still linked from the official Work with Us page, "
        "but the application window has long closed.",
    ),
}


def main() -> int:
    apply = "--apply" in sys.argv
    jobs = json.loads(JOBS.read_text(encoding="utf-8"))
    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    archive_ids = {r.get("id") for r in archive}

    keep, moved = [], []
    for rec in jobs:
        meta = STALE.get(rec.get("id"))
        if not meta:
            keep.append(rec)
            continue
        circular_date, reason = meta
        rec["status"] = "archived"
        rec["date_archived"] = TODAY
        rec["archive_reason"] = "deadline passed"
        rec["deadline_or_window"] = f"Closed (circular dated {circular_date})"
        rec["valid_through"] = circular_date
        rec["reverify_after"] = ""
        rec.setdefault("verification", {})
        rec["verification"]["method"] = "official-page-verified"
        rec["verification"]["note"] = reason
        moved.append(rec)
        print(f"archive {rec['id']} (circular {circular_date})")

    new_archive = moved + [r for r in archive if r.get("id") not in STALE]

    print(f"jobs {len(jobs)} -> {len(keep)}; archive {len(archive)} -> {len(new_archive)}")

    if apply:
        JOBS.write_text(json.dumps(keep, indent=2, ensure_ascii=False), encoding="utf-8")
        ARCHIVE.write_text(json.dumps(new_archive, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Applied.")
    else:
        print("Dry run only; re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
