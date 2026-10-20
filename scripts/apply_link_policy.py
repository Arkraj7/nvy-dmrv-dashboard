#!/usr/bin/env python3
"""Re-apply the editable direct-link policy to every stored record.

Policy v2 (20 Oct 2026) replaces the official-source-only rule:

* any employer domain and allow-listed platform are public;
* DEAD_LINK records are archived (never deleted);
* NOT_DIRECT_LINK records become "Careers portals";
* everything else is restored to active.

Usage:
    py scripts/apply_link_policy.py            # dry run, prints a summary
    py scripts/apply_link_policy.py --apply    # rewrite the data files
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

from link_policy import strip_tracking
from verify_link import DEAD_LINK, NOT_DIRECT_LINK, LinkVerifier, load_employers_registry

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
FILES = [
    PUBLIC / "jobs.json",
    PUBLIC / "global_jobs.json",
    PUBLIC / "archive.json",
    PUBLIC / "global_archive.json",
]


def load(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("jobs", [])
    return [row for row in data if isinstance(row, dict)]


def save(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def is_quarantined(record: Dict[str, Any]) -> bool:
    return record.get("status") == "quarantined" or bool(record.get("quarantine"))


def classify(record: Dict[str, Any], verifier: LinkVerifier) -> Tuple[str, Any]:
    url = strip_tracking(str(record.get("apply_url") or ""))
    result = verifier.verify(
        url,
        str(record.get("employer_id") or ""),
        str(record.get("clean_title") or ""),
        str(record.get("organization") or ""),
    )
    return result.reason_code, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="write changes")
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    registry = load_employers_registry(str(PUBLIC / "employers.json"))
    verifier = LinkVerifier(registry)
    today = date.today().isoformat()

    buckets: Dict[Path, List[Dict[str, Any]]] = {path: load(path) for path in FILES}
    targets: List[Tuple[Path, int, Dict[str, Any]]] = []
    for path, rows in buckets.items():
        for index, record in enumerate(rows):
            if is_quarantined(record):
                targets.append((path, index, record))

    print(f"Re-checking {len(targets)} quarantined record(s) with policy v2...")

    def work(item):
        path, index, record = item
        try:
            reason, result = classify(record, verifier)
        except Exception as exc:  # fail open: UNKNOWN is never dead
            return path, index, "UNKNOWN_KEEP", None, f"{type(exc).__name__}: {exc}"
        return path, index, reason, result, ""

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for done, item in enumerate(pool.map(work, targets), start=1):
            results.append(item)
            if done % 10 == 0 or done == len(targets):
                print(f"  checked {done}/{len(targets)}")

    counts: Counter = Counter()
    moved: Counter = Counter()
    for path, index, reason, result, error in results:
        record = buckets[path][index]
        counts[reason] += 1
        previous = (record.get("quarantine") or {}).get("reason_code") or record.get("status")
        is_archive_file = path.name.endswith("archive.json")

        record.pop("quarantine", None)
        record.pop("status_before_quarantine", None)
        record["link_policy"] = {
            "policy_version": 2,
            "restored_at": today,
            "previous_reason_code": previous,
            "reason_code": reason,
            "checked_at": getattr(result, "verified_at", "") if result else "",
            "platform": getattr(result, "platform", "") if result else "",
        }

        if reason == DEAD_LINK:
            record["status"] = "archived"
            record.setdefault("date_archived", today)
            moved["archived_dead"] += 1
            continue

        if is_archive_file:
            # Already past its window: keep it archived (no outbound link),
            # but no longer quarantined.
            record["status"] = "archived"
            record.setdefault("date_archived", today)
            moved["stayed_archived"] += 1
            continue

        if reason == NOT_DIRECT_LINK:
            record["status"] = "active"
            entry = getattr(result, "entry_type", "") if result else ""
            record["entry_type"] = entry if entry in {"careers_portal", "award_portal"} else "careers_portal"
            moved["careers_portal"] += 1
        else:
            record["status"] = "active"
            entry = getattr(result, "entry_type", "") if result else ""
            if entry in {"posting", "award_portal", "careers_portal"}:
                record["entry_type"] = entry
            else:
                record["entry_type"] = "posting"
            moved["restored_active"] += 1

    print("\nReason codes:")
    for reason, count in counts.most_common():
        print(f"  {reason}: {count}")
    print("Outcome:")
    for key, count in moved.most_common():
        print(f"  {key}: {count}")

    if not args.apply:
        print("\nDry run only. Re-run with --apply to write.")
        return 0

    # Move dead records out of the active files into the matching archive.
    for path in (PUBLIC / "jobs.json", PUBLIC / "global_jobs.json"):
        rows = buckets[path]
        keep = [row for row in rows if row.get("status") != "archived"]
        dead = [row for row in rows if row.get("status") == "archived"]
        if dead:
            archive_path = (
                PUBLIC / "global_archive.json"
                if path.name == "global_jobs.json"
                else PUBLIC / "archive.json"
            )
            archive_rows = buckets[archive_path]
            existing = {str(row.get("id")) for row in archive_rows}
            for row in dead:
                if str(row.get("id")) not in existing:
                    archive_rows.append(row)
            buckets[path] = keep

    for path, rows in buckets.items():
        save(path, rows)
        print(f"Wrote {len(rows)} record(s) to {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
