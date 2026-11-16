#!/usr/bin/env python3
"""Reclassify small-team third-party aggregator records as careers_portal."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

SMALL_TEAM = [
    "greenjobsindia.in",
    "fundsforngos.org",
    "careersandopportunities.com",
    "biotecnika.org",
]


def main() -> int:
    for name in ("jobs.json", "global_jobs.json"):
        path = PUBLIC / name
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for rec in data:
            u = (rec.get("apply_url") or "").lower()
            if any(s in u for s in SMALL_TEAM) and rec.get("entry_type") == "posting":
                rec["entry_type"] = "careers_portal"
                changed += 1
        if changed:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"{name}: reclassified {changed} record(s) -> careers_portal")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
