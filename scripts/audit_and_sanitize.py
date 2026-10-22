#!/usr/bin/env python3
"""Run the SEO/link audits without letting a single bad job block the site.

The daily workflow must still commit the registry, send the Telegram brief and
deploy Cloudflare Pages when one record has a broken apply URL or a stale
static page. This wrapper:

* runs the existing audit scripts unchanged;
* identifies job-level offenders from their output;
* quarantines a small, bounded number of offending records;
* rebuilds the SEO surface and re-runs the audits;
* exits 0 for residual *audit* findings (they are printed loudly), but exits 1
  if the rebuild itself fails.

Structural/code-level errors are never "fixed" by mass-quarantining jobs. If
the error set is widespread, the wrapper leaves the registry alone and reports
the findings so a human can investigate.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
IST = ZoneInfo("Asia/Kolkata")

DATA_FILES = (
    PUBLIC / "jobs.json",
    PUBLIC / "global_jobs.json",
)

LINK_VIOLATION_RE = re.compile(
    r"^(?:jobs|global_jobs)\.json:([^:]+):\s*(.+)$"
)
SEO_JOB_ERROR_RE = re.compile(r"^\[G8\] ERROR /jobs/([^:]+):\s*(.+)$")


def _run(args: List[str]) -> Tuple[int, str]:
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _active_records() -> Dict[str, Tuple[Path, Dict[str, Any]]]:
    records: Dict[str, Tuple[Path, Dict[str, Any]]] = {}
    for path in DATA_FILES:
        payload = _load_json(path)
        if not isinstance(payload, list):
            continue
        for record in payload:
            if not isinstance(record, dict):
                continue
            job_id = str(record.get("id") or "").strip()
            if not job_id:
                continue
            if record.get("status") == "quarantined" or record.get("quarantine"):
                continue
            if record.get("status") == "archived":
                continue
            records[job_id] = (path, record)
    return records


def _quarantine(
    offenders: Dict[str, str],
    reason: str,
    max_records: int,
) -> int:
    """Quarantine a bounded set of active records, grouped by source file."""
    if not offenders:
        return 0
    if len(offenders) > max_records:
        print(
            f"AUTO-SANITIZE: {len(offenders)} job-level offenders exceeds the "
            f"cap of {max_records}; refusing to mass-quarantine. "
            "Treating this as a structural/code issue."
        )
        return 0

    by_file: Dict[Path, Dict[str, str]] = {}
    records = _active_records()
    for job_id, detail in offenders.items():
        entry = records.get(job_id)
        if not entry:
            continue
        path, _record = entry
        by_file.setdefault(path, {})[job_id] = detail

    changed = 0
    now = datetime.now(IST).isoformat(timespec="seconds")
    for path, ids in by_file.items():
        payload = _load_json(path)
        if not isinstance(payload, list):
            continue
        for record in payload:
            if not isinstance(record, dict):
                continue
            job_id = str(record.get("id") or "")
            if job_id not in ids:
                continue
            if record.get("status") == "quarantined" or record.get("quarantine"):
                continue
            record["status_before_quarantine"] = record.get("status", "active")
            record["status"] = "quarantined"
            record["quarantine"] = {
                "reason": reason,
                "detail": ids[job_id][:400],
                "date": now[:10],
                "source": "audit_and_sanitize.py",
            }
            changed += 1
            print(f"  quarantined {job_id}: {ids[job_id][:160]}")
        if changed:
            _write_json(path, payload)
    return changed


def _parse_link_offenders(output: str) -> Dict[str, str]:
    offenders: Dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("- "):
            line = line[2:].strip()
        match = LINK_VIOLATION_RE.match(line)
        if match:
            offenders[match.group(1)] = match.group(2)
    return offenders


def _parse_seo_job_offenders(output: str) -> Dict[str, str]:
    offenders: Dict[str, str] = {}
    for line in output.splitlines():
        match = SEO_JOB_ERROR_RE.match(line.strip())
        if match:
            offenders[match.group(1)] = match.group(2)
    return offenders


def _print_report(label: str, code: int, output: str) -> None:
    print(f"\n===== {label} (exit {code}) =====")
    print(output.rstrip() or "(no output)")
    print(f"===== end {label} =====\n")


def data_stage(max_records: int) -> int:
    code, output = _run([sys.executable, "scripts/link_guard.py"])
    _print_report("link guard (data)", code, output)
    link_offenders = _parse_link_offenders(output)

    code, output = _run([sys.executable, "scripts/seo_checklist_audit.py"])
    _print_report("SEO audit (data)", code, output)
    seo_offenders = _parse_seo_job_offenders(output)

    changed = _quarantine(link_offenders, "link_policy", max_records)
    changed += _quarantine(seo_offenders, "seo_job_page", max_records)

    if changed:
        print(f"AUTO-SANITIZE: quarantined {changed} record(s); rebuilding SEO pages.")
        build_code, build_output = _run([sys.executable, "scripts/build_seo_pages.py"])
        _print_report("SEO rebuild after sanitize", build_code, build_output)
        if build_code != 0:
            print("AUTO-SANITIZE: rebuild failed; this is a code/build stop condition.")
            return 1

        code, output = _run([sys.executable, "scripts/link_guard.py"])
        _print_report("link guard (post-sanitize)", code, output)
        code, output = _run([sys.executable, "scripts/seo_checklist_audit.py"])
        _print_report("SEO audit (post-sanitize)", code, output)

    # An audit finding is a warning, not a deployment blocker. The workflow
    # still surfaces it in the log and the failure-alert step catches genuine
    # pipeline crashes.
    print(
        "AUDIT STATUS: non-blocking. Residual audit findings (if any) are "
        "printed above for review; deployment will continue."
    )
    return 0


def dist_stage(dist: Path) -> int:
    code, output = _run(
        [sys.executable, "scripts/link_guard.py", "--dist", str(dist)]
    )
    _print_report("link guard (dist)", code, output)
    if code == 0:
        print("AUDIT STATUS: built-site link guard clean.")
        return 0
    print(
        "AUDIT STATUS: built-site guard reported violations. This is "
        "non-blocking per the daily workflow contract; the deploy continues "
        "and the findings above are the review queue."
    )
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("data", "dist"),
        default="data",
        help="Audit the source data or the built dist directory.",
    )
    parser.add_argument(
        "--dist",
        default="dist",
        help="Built-site directory for --stage dist (default: dist).",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=6,
        help="Maximum job records to quarantine per audit run (default: 6).",
    )
    args = parser.parse_args(argv)

    if args.stage == "dist":
        return dist_stage(Path(args.dist))
    return data_stage(max(1, args.max_records))


if __name__ == "__main__":
    sys.exit(main())
