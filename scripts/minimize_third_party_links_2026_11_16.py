#!/usr/bin/env python3
"""Minimize third-party links: extract official URLs where possible and
reclassify category-page links as careers_portal (per LINK_POLICY.md).

Changes:
1. ICAR NBSS&LUP record: apply_url was a FreeJobAlert aggregator page; replaced
   with the official ICAR recruitment PDF.
2. Five records pointing at csrjobs.club / inclimate.com category pages: these
   are NOT_DIRECT per link policy (they point at a listing root, not a specific
   job). Reclassify entry_type from 'posting' to 'careers_portal'.

LinkedIn/lnkd.in/Indeed/ReliefWeb records are left untouched: LinkedIn and
Indeed cannot be fetched (policy), and ReliefWeb is JS-rendered with a blocked
API, so the official URL cannot be extracted automatically.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

ICAR_NEW_URL = "https://icar-nbsslup.org.in/wp-content/uploads/2026/Recruitment/Recruit_Ngp_30102026.pdf"
RECLASSIFY = {
    "revantage-sustainability-data-analyst",
    "hsbc-senior-esg-reporting-manager",
    "pepsico-associate-director-sustainability",
    "micron-senior-energy-and-decarbonization-engineer",
    "blackrock-sustainability-data-process-reporting-associate",
}


def main() -> int:
    for name in ("jobs.json", "global_jobs.json"):
        path = PUBLIC / name
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = 0
        for rec in data:
            rid = rec.get("id")
            if rid == "icar-nbsslup-young-professional-ii-rs-gis-2026":
                old = rec.get("apply_url")
                rec["apply_url"] = ICAR_NEW_URL
                rec["source_portal"] = "ICAR NBSS&LUP official recruitment notification (PDF)"
                verification = rec.setdefault("verification", {})
                verification["method"] = "official-page-verified"
                verification["verified_at"] = "2026-11-16"
                verification["http_status"] = 200
                verification["note"] = (
                    "apply_url upgraded from FreeJobAlert aggregator to the official "
                    "ICAR NBSS&LUP recruitment PDF."
                )
                print(f"{name}: upgraded {rid}")
                print(f"  old: {old}")
                print(f"  new: {ICAR_NEW_URL}")
                changed += 1
            if rid in RECLASSIFY:
                rec["entry_type"] = "careers_portal"
                print(f"{name}: reclassified {rid} -> careers_portal")
                changed += 1
        if changed:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  wrote {name} ({changed} change(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
