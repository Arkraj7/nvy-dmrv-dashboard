#!/usr/bin/env python3
"""Reclassify non-India records that landed in the India registry.

The 12 November LinkedIn batch filed a few overseas postings in
``public/jobs.json``. Every detail page is served at ``/jobs/<slug>`` whichever
registry holds the record, so moving them to ``public/global_jobs.json``
restores correct placement without changing a single public URL.

Nothing is dropped: each record is appended to the global registry with
``global: true`` and removed from the India registry.

Run from the repository root:
    py scripts/reclassify_non_india_2026_11_13.py [--apply]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT / "public" / "jobs.json"
GLOBAL = ROOT / "public" / "global_jobs.json"

INDIA_LABELS = {"", "india", "none"}
# Only the batch filed on this date landed overseas postings in the India
# registry by mistake; older global-labelled entries were placed there on
# purpose and must stay put.
BATCH_DATE = "2026-11-12"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    apply = "--apply" in sys.argv
    india = load(JOBS)
    glob = load(GLOBAL)
    glob_ids = {r.get("id") for r in glob}

    stay, move = [], []
    for rec in india:
        country = str(rec.get("country") or "").strip().lower()
        if country in INDIA_LABELS or str(rec.get("date_added")) != BATCH_DATE:
            stay.append(rec)
        else:
            move.append(rec)

    print(f"India registry: {len(india)} records, moving {len(move)} overseas record(s)")
    for rec in move:
        print(f"   -> global: {rec.get('id')} ({rec.get('country')})")
        rec["global"] = True

    moved = [r for r in move if r.get("id") not in glob_ids]
    skipped = [r for r in move if r.get("id") in glob_ids]

    if apply:
        JOBS.write_text(json.dumps(stay, indent=2, ensure_ascii=False), encoding="utf-8")
        GLOBAL.write_text(
            json.dumps(moved + glob, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"Applied: India {len(india)} -> {len(stay)}; "
            f"global {len(glob)} -> {len(glob) + len(moved)}"
        )
        if skipped:
            print(f"Skipped {len(skipped)} already present in the global registry")
    else:
        print("Dry run only; re-run with --apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
