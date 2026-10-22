#!/usr/bin/env python3
"""Verify that the live site received today's pipeline + broadcast state.

The daily workflow calls this after ``wrangler pages deploy``. A green deploy
step is not enough: a bot commit can succeed while the CDN keeps serving an old
stats.json, or the Telegram step can fail before the rotation marker is written.
This probe makes those failures loud.

Usage:
    python scripts/verify_live_update.py
    python scripts/verify_live_update.py --url https://www.urbanforestpark.com/stats.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
IST = ZoneInfo("Asia/Kolkata")
DEFAULT_URL = "https://www.urbanforestpark.com/stats.json"


def ist_today() -> str:
    return datetime.now(IST).date().isoformat()


def fetch_json(url: str, timeout: int = 20) -> Dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "urbanforestpark-daily-verifier/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8", errors="replace")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("stats.json is not a JSON object")
    return parsed


def check(payload: Dict[str, Any], today: str, require_broadcast: bool) -> list[str]:
    problems: list[str] = []
    pipeline_date = str(payload.get("last_pipeline_run_date_ist") or "")
    updated = str(payload.get("last_updated_ist") or payload.get("last_updated") or "")
    broadcast = str(payload.get("last_telegram_broadcast_date") or "")
    recent = payload.get("recent_telegram_job_ids") or []

    if pipeline_date != today:
        problems.append(
            f"last_pipeline_run_date_ist={pipeline_date!r}, expected {today!r}"
        )
    if not updated.startswith(today):
        problems.append(f"last_updated_ist={updated!r}, expected a {today} timestamp")
    if require_broadcast:
        if broadcast != today:
            problems.append(
                f"last_telegram_broadcast_date={broadcast!r}, expected {today!r}"
            )
        if not isinstance(recent, list) or len(recent) < 10:
            problems.append(
                f"recent_telegram_job_ids has {len(recent) if isinstance(recent, list) else 0} "
                "entries; expected at least 10"
            )
    if int(payload.get("active_open_jobs") or 0) <= 0:
        problems.append("active_open_jobs is zero")
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--date", default=ist_today())
    parser.add_argument("--attempts", type=int, default=6)
    parser.add_argument("--sleep", type=float, default=20.0)
    parser.add_argument(
        "--require-broadcast",
        action="store_true",
        default=True,
        help="Require today's Telegram marker and at least 10 rotation ids.",
    )
    parser.add_argument(
        "--allow-missing-broadcast",
        dest="require_broadcast",
        action="store_false",
        help="Only verify the pipeline date, not the Telegram state.",
    )
    args = parser.parse_args(argv)

    last_error = ""
    for attempt in range(1, max(1, args.attempts) + 1):
        separator = "&" if "?" in args.url else "?"
        probe = f"{args.url}{separator}verify={int(time.time())}"
        try:
            payload = fetch_json(probe)
            problems = check(payload, args.date, args.require_broadcast)
            if not problems:
                print(
                    "LIVE VERIFY OK: "
                    f"pipeline={payload.get('last_pipeline_run_date_ist')} "
                    f"broadcast={payload.get('last_telegram_broadcast_date')} "
                    f"recent_ids={len(payload.get('recent_telegram_job_ids') or [])} "
                    f"active={payload.get('active_open_jobs')}"
                )
                return 0
            last_error = "; ".join(problems)
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        print(
            f"LIVE VERIFY attempt {attempt}/{args.attempts} not ready: {last_error}",
            flush=True,
        )
        if attempt < args.attempts:
            time.sleep(max(0.0, args.sleep))

    print(f"LIVE VERIFY FAILED after {args.attempts} attempt(s): {last_error}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
