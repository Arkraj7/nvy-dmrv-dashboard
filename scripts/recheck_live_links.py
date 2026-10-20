#!/usr/bin/env python3
"""Nightly re-verification of every live (non-quarantined) listing.

Policy:
  * dead page (HTTP 404 / SOFT_404 "closed") -> archive immediately
  * any other failure -> consecutive-failure counter; quarantine on the 3rd
  * success -> reset the counter
  * records without a stated deadline carry ``reverify_after`` (day 15)
  * one summary line per run, printed to stdout
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ingestion_gate import quarantine_record
from verify_link import load_employers_registry, verify_link

ROOT = Path(__file__).resolve().parent.parent
FAIL_THRESHOLD = 3
DEAD_REASONS = {"HTTP_404", "SOFT_404", "HTTP_410"}


def load_json(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data if isinstance(row, dict)] if isinstance(data, list) else []


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_state(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def archive_dead(record: Dict[str, Any], today: str) -> None:
    record["status"] = "archived"
    record["date_archived"] = today
    record["archive_reason"] = "dead_page"


def employer_for(record: Dict[str, Any], registry: Dict[str, Any]) -> str:
    employer_id = str(record.get("employer_id") or "")
    if employer_id:
        return employer_id
    from ingestion_gate import find_employer

    employer = find_employer(record.get("organization"), registry)
    return str(employer.get("id") or "") if employer else ""


def recheck_file(
    path: Path,
    archive_path: Path,
    state: Dict[str, Dict[str, Any]],
    registry: Dict[str, Any],
    today: str,
) -> Dict[str, int]:
    records = load_json(path)
    archive = load_json(archive_path)
    stats = {"checked": 0, "pass": 0, "archived": 0, "quarantined": 0, "failing": 0}
    archived_now: List[Dict[str, Any]] = []
    keep: List[Dict[str, Any]] = []

    for record in records:
        rid = str(record.get("id") or "")
        if not rid or record.get("status") in {"quarantined", "archived"}:
            keep.append(record)
            continue
        employer_id = employer_for(record, registry)
        if not employer_id:
            # Registry is the source of truth; unmatched rows wait for review.
            keep.append(record)
            stats["failing"] += 1
            continue
        result = verify_link(
            record.get("apply_url", ""),
            employer_id,
            record.get("clean_title", ""),
            record.get("organization", ""),
            employers_registry=registry,
        )
        stats["checked"] += 1
        entry = state.setdefault(rid, {"consecutive_failures": 0})
        entry["last_checked"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry["last_reason"] = result.reason_code

        if result.ok and result.verification_level == "page_verified":
            entry["consecutive_failures"] = 0
            record["verification"] = {
                "verified_at": result.verified_at,
                "final_url": result.final_url,
                "final_host": result.final_host,
                "http_status": result.http_status,
                "content_hash": result.content_hash,
                "entry_type": result.entry_type,
                "host_class": result.host_class,
                "verifier": "verify_link",
            }
            record["entry_type"] = result.entry_type
            keep.append(record)
            stats["pass"] += 1
            continue

        entry["consecutive_failures"] = int(entry.get("consecutive_failures") or 0) + 1
        record["last_link_check"] = {
            "checked_at": entry["last_checked"],
            "reason_code": result.reason_code,
            "http_status": result.http_status,
            "consecutive_failures": entry["consecutive_failures"],
        }
        if result.reason_code in DEAD_REASONS:
            archive_dead(record, today)
            archived_now.append(record)
            stats["archived"] += 1
        elif entry["consecutive_failures"] >= FAIL_THRESHOLD:
            quarantine_record(
                record,
                result.reason_code,
                f"failed {entry['consecutive_failures']} consecutive nightly checks",
                result=result,
                today=today,
                source="nightly_recheck",
            )
            keep.append(record)
            stats["quarantined"] += 1
        else:
            keep.append(record)
            stats["failing"] += 1

    write_json(path, keep)
    if archived_now:
        existing = {str(row.get("id")): row for row in archive}
        for record in archived_now:
            existing[str(record.get("id"))] = record
        write_json(archive_path, list(existing.values()))
    return stats


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nightly link recheck")
    parser.add_argument("--jobs", default=str(ROOT / "public" / "jobs.json"))
    parser.add_argument("--archive", default=str(ROOT / "public" / "archive.json"))
    parser.add_argument("--global-jobs", default=str(ROOT / "public" / "global_jobs.json"))
    parser.add_argument(
        "--global-archive", default=str(ROOT / "public" / "global_archive.json")
    )
    parser.add_argument(
        "--state", default=str(ROOT / "scripts" / "link_recheck_state.json")
    )
    args = parser.parse_args(argv)

    today = date.today().isoformat()
    registry = load_employers_registry(str(ROOT / "public" / "employers.json"))
    state_path = Path(args.state)
    state = load_state(state_path)

    india = recheck_file(
        Path(args.jobs), Path(args.archive), state, registry, today
    )
    glob = recheck_file(
        Path(args.global_jobs), Path(args.global_archive), state, registry, today
    )
    write_json(state_path, state)

    totals = {
        key: india.get(key, 0) + glob.get(key, 0)
        for key in ("checked", "pass", "archived", "quarantined", "failing")
    }
    print(
        "link-recheck {date} checked={checked} pass={pass} archived={archived} "
        "quarantined={quarantined} failing={failing}".format(date=today, **totals)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
