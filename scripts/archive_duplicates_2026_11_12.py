"""Archive duplicate listings found during the 12 November 2026 audit.

- sustainable-finance-specialist-unep-india: the same UN Volunteer assignment
  is carried by unv-sustainable-finance-specialist-iwm-delhi-remote-2026, and
  this older copy's own "Apply by 23 Oct 2026" window has closed.
- mittal-family-climate-fellowship-academic-year-2027-28-harva: duplicate of
  mittal-family-climate-fellowship-2027 on the same institute page (the two
  records differ only by a trailing slash), which produced duplicate titles
  and anchors.

Records are archived, never deleted (docs/LINK_POLICY.md).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-12"

MOVES = [
    (
        ROOT / "public/jobs.json",
        ROOT / "public/archive.json",
        "sustainable-finance-specialist-unep-india",
    ),
    (
        ROOT / "public/global_jobs.json",
        ROOT / "public/global_archive.json",
        "mittal-family-climate-fellowship-academic-year-2027-28-harva",
    ),
    (
        ROOT / "public/jobs.json",
        ROOT / "public/archive.json",
        "earths-care-awards-14th-2026",
    ),
]


def main() -> None:
    for src, dst, rid in MOVES:
        active = json.loads(src.read_text(encoding="utf-8"))
        archive = json.loads(dst.read_text(encoding="utf-8"))
        rec = next((r for r in active if r.get("id") == rid), None)
        if rec is None:
            print(f"SKIP (not active): {rid}")
            continue
        if any(r.get("id") == rid for r in archive):
            print(f"SKIP (already archived): {rid}")
            continue
        active.remove(rec)
        rec = dict(rec)
        rec["status"] = "archived"
        rec["date_archived"] = TODAY
        rec["archive_reason"] = "duplicate listing"
        archive.append(rec)
        src.write_text(json.dumps(active, ensure_ascii=False, indent=2), encoding="utf-8")
        dst.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"ARCHIVED {rid} -> {dst.name}")


if __name__ == "__main__":
    main()
