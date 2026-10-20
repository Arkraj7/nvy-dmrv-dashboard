#!/usr/bin/env python3
"""Build public/quarantine_report.json from the live quarantine queue.

The report is the reviewer's worklist: quarantined records grouped by employer
with reason codes and fix hints. It is regenerated from the data files (never
the other way round), so records added by the ingestion gate or the nightly
recheck show up immediately.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ingestion_gate import find_employer, load_registry

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
FILES = ["jobs.json", "archive.json", "global_jobs.json", "global_archive.json"]

FIX_HINTS = {
    "HOST_NOT_IN_REGISTRY": (
        "Lead came from a host that is not an approved employer domain. Resolve "
        "to the employer's own page; never store the aggregator URL."
    ),
    "BLOCKED_HOST": (
        "Replace with the employer's own posting/careers URL from the registry "
        "(job-board links may only be used for discovery)."
    ),
    "GENERIC_LANDING_PAGE": (
        "Replace the portal URL with the specific posting URL (job title must "
        "appear on the page)."
    ),
    "CONTENT_MISMATCH": (
        "Replace with the page that carries this exact posting, or add the "
        "correct domain/ATS host to the registry."
    ),
    "SOFT_404": 'Page says "404 / not found" though HTTP=200 - find the current posting URL.',
    "NEEDS_MANUAL_CHECK": (
        "Manual review: TLS/403/DNS-filtered host. Open in a browser inside "
        "India, capture the true posting URL, then re-run verify_link."
    ),
    "HTTP_404": "Dead link - find the current posting URL or drop the record.",
    "MissingSchema": "Fetch broke on a relative redirect - retry/replace URL.",
    "EMPLOYER_NOT_IN_REGISTRY": (
        "Add the employer (with a verified own domain) to public/employers.json, "
        "or drop the lead."
    ),
    "FIELD_NOT_IN_SOURCE": (
        "The LLM claimed a title/deadline/compensation/qualification/skill that "
        "is not on the fetched page. Re-fetch the page and restructure only "
        "what it says."
    ),
    "PAGE_TEXT_UNAVAILABLE": "The verified page returned no readable text - re-fetch or replace the URL.",
    "POSITION_CLOSED": "The page says applications are closed - archive or replace the record.",
    "TIMEOUT": "Source timed out - retry; quarantine persists after 3 nightly failures.",
    "UNREACHABLE_FROM_RUNNER": "Runner could not reach the host - retry from another network.",
    "SSL_ERROR": "TLS certificate problem - verify the official host; do not bypass verification.",
    "REDIRECT_LOOP": "Redirect loop - replace with the final canonical posting URL.",
}


def load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []


def main() -> int:
    registry = load_registry(str(PUBLIC / "employers.json"))
    records: List[Dict[str, Any]] = []
    total = 0
    for file_name in FILES:
        for record in load(PUBLIC / file_name):
            total += 1
            if record.get("status") == "quarantined":
                records.append({**record, "_file": f"public/{file_name}"})

    by_reason: Counter = Counter()
    groups: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "reason_codes": Counter(), "records": []}
    )
    for record in records:
        quarantine = record.get("quarantine") or {}
        reason = str(quarantine.get("reason_code") or "VERIFICATION_ERROR")
        by_reason[reason] += 1
        employer = str(record.get("organization") or "Unknown employer").strip()
        group = groups[employer]
        group["count"] += 1
        group["reason_codes"][reason] += 1
        group["records"].append(
            {
                "slug": record.get("id"),
                "file": record["_file"],
                "reason_code": reason,
                "final_host": quarantine.get("final_host") or "",
                "apply_url": record.get("apply_url") or "",
                "entry_type": quarantine.get("entry_type")
                or record.get("entry_type")
                or "unknown",
                "date_added": record.get("date_added") or "",
            }
        )

    employer_rows = []
    for employer, group in groups.items():
        registry_hit = find_employer(employer, registry)
        employer_rows.append(
            {
                "employer": employer,
                "employer_id": (registry_hit or {}).get("id", ""),
                "count": group["count"],
                "reason_codes": dict(group["reason_codes"]),
                "records": sorted(group["records"], key=lambda row: str(row["slug"])),
            }
        )
    employer_rows.sort(key=lambda row: (-row["count"], row["employer"].lower()))

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "live quarantine queue (status=quarantined)",
        "policy": "docs/LINK_POLICY.md",
        "tag": "pre-gate-2026-10-20",
        "totals": {
            "records": total,
            "quarantined": len(records),
            "public": total - len(records),
        },
        "by_reason": dict(by_reason.most_common()),
        "fix_hints": FIX_HINTS,
        "by_employer": employer_rows,
    }
    (PUBLIC / "quarantine_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"quarantine report: {len(records)} quarantined / {total} records, "
        f"{len(employer_rows)} employer group(s), {len(by_reason)} reason code(s)"
    )
    for reason, count in by_reason.most_common():
        print(f"  {count:3d}  {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
