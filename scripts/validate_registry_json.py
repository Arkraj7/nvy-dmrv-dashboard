#!/usr/bin/env python3
"""Validate the published registry JSON before CI commits it.

The daily workflow rebases, pops a stash and commits whichever registry files
happen to be in the worktree. When that stash pop conflicts, Git leaves
``<<<<<<<`` markers in the JSON and the commit goes through, which publishes a
file the front end cannot parse. This guard fails the step instead.

It also rejects duplicate ids, which a careless merge produces.

Run from the repository root:
    py scripts/validate_registry_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FILES = (
    "public/jobs.json",
    "public/global_jobs.json",
    "public/archive.json",
    "public/global_archive.json",
    "public/stats.json",
    "public/source_report.json",
)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    problems: list[str] = []

    for name in FILES:
        path = root / name
        if not path.exists():
            continue
        raw = path.read_text(encoding="utf-8")
        if "<<<<<<<" in raw or ">>>>>>>" in raw:
            problems.append(f"{name}: merge-conflict markers")
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            problems.append(f"{name}: {exc}")
            continue
        if isinstance(data, list):
            ids = [rec.get("id") for rec in data if isinstance(rec, dict)]
            dups = sorted({i for i in ids if i and ids.count(i) > 1})
            if dups:
                problems.append(f"{name}: duplicate ids {', '.join(dups[:5])}")

    if problems:
        for problem in problems:
            print(f"::error::registry JSON invalid - {problem}")
        return 1

    print("registry JSON OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
