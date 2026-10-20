"""Attach entry_type + verification metadata to PASS records (2026-10-20).

Quarantine metadata already lives in each FAIL record's ``quarantine`` block.
PASS records need the same provenance so the dossier can show
"Verified at source on <date>" and the feed can place them in the right
section (posting -> Jobs, careers_portal -> Careers portals,
award_portal -> Fellowships & programmes, unknown -> hidden).
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

FILES = [
    "public/jobs.json",
    "public/archive.json",
    "public/global_jobs.json",
    "public/global_archive.json",
]

rows = {
    row["slug"]: row
    for row in csv.DictReader(open("audit_report.csv", encoding="utf-8"))
    if row["verdict"] == "PASS"
}

verified_at = "2026-10-20T00:00:00Z"
updated = 0
seen = set()

for path in FILES:
    file_path = Path(path)
    if not file_path.exists():
        continue
    data = json.loads(file_path.read_text(encoding="utf-8"))
    changed = False
    for record in data:
        row = rows.get(record.get("id"))
        if not row:
            continue
        record["entry_type"] = row["entry_type"]
        record["employer_id"] = row["employer_id"]
        record["verification"] = {
            "verified_at": verified_at,
            "final_url": row["final_url"],
            "final_host": row["final_host"],
            "http_status": int(row["http_status"] or 0),
            "content_hash": row["content_hash"],
            "entry_type": row["entry_type"],
            "host_class": row["host_class"],
            "verifier": "verify_link",
        }
        updated += 1
        seen.add(record["id"])
        changed = True
    if changed:
        file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

print(f"PASS records enriched: {updated} / {len(rows)}")
print("Missing:", sorted(set(rows) - seen))
for row in rows.values():
    print(f"  {row['slug']:65s} {row['entry_type']:14s} {row['final_host']}")
