#!/usr/bin/env python3
"""One-off registry cleanup for the 2026-10-31 SEO critical fixes.

1. Move every active record whose ``valid_through`` is before 2026-10-31 into
   the matching archive file with ``status: "archived"`` and a
   ``date_archived`` stamp (matching ``fetch_and_humanize.archive_expired``).
2. Remove the duplicate FAO India record
   ``fao-environment-climate-change-specialist``. Its URL is 301'd in
   ``build_seo_pages.REMOVED_JOB_REDIRECTS`` to the richer
   ``fao-environment-climate-change-specialist-2026`` record.

Usage: py scripts/cleanup_2026_10_31.py [--apply]
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC = REPO_ROOT / "public"
TODAY = date(2026, 10, 31)
DUPLICATE_FAO_ID = "fao-environment-climate-change-specialist"


def load(name: str):
    return json.loads((PUBLIC / name).read_text(encoding="utf-8"))


def save(name: str, data) -> None:
    (PUBLIC / name).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def archive_expired(active, archive, label):
    archive_by_id = {}
    for record in archive:
        rid = str(record.get("id") or "").strip()
        if rid:
            archive_by_id.setdefault(rid, record)

    kept, moved, dropped_dupes = [], [], []
    for job in active:
        rid = str(job.get("id") or "").strip()
        if not rid:
            continue
        if rid == DUPLICATE_FAO_ID and label == "India":
            dropped_dupes.append(rid)
            continue
        valid_through = str(job.get("valid_through") or "").strip()
        try:
            expired = bool(valid_through) and date.fromisoformat(valid_through) < TODAY
        except ValueError:
            expired = False
        if expired:
            job["status"] = "archived"
            job.setdefault("date_archived", TODAY.isoformat())
            existing = archive_by_id.get(rid)
            if existing is None:
                archive_by_id[rid] = job
                moved.append((rid, valid_through))
            else:
                existing.setdefault("date_archived", job.get("date_archived"))
                moved.append((rid, valid_through + " (already archived)"))
        else:
            kept.append(job)

    for record in archive_by_id.values():
        if record.get("status") != "quarantined" and not record.get("quarantine"):
            record["status"] = "archived"
            record.setdefault("date_archived", TODAY.isoformat())

    archive_out = sorted(
        archive_by_id.values(),
        key=lambda r: (str(r.get("date_archived") or ""), str(r.get("id") or "")),
        reverse=True,
    )
    return kept, archive_out, moved, dropped_dupes


def main() -> int:
    apply = "--apply" in sys.argv

    for active_name, archive_name, label in [
        ("jobs.json", "archive.json", "India"),
        ("global_jobs.json", "global_archive.json", "Global"),
    ]:
        active = load(active_name)
        archive = load(archive_name)
        kept, archive_out, moved, dropped = archive_expired(active, archive, label)
        print(f"[{label}] active {len(active)} -> {len(kept)}; archive {len(archive)} -> {len(archive_out)}")
        for rid, vt in moved:
            print(f"   archived {rid} (valid_through {vt})")
        for rid in dropped:
            print(f"   removed duplicate {rid}")
        if apply:
            save(active_name, kept)
            save(archive_name, archive_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
