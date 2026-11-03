#!/usr/bin/env python3
"""Generate a downloadable salary dataset (CSV) from the verified job registry.

The CSV is served at /data/green-jobs-salary.csv and linked from the salary
guide. It contains only fields already published on the site: role, employer,
city, state, category, position type, experience level, compensation as
advertised, deadline, and the registry dossier URL. No data is invented.

Run after the registry is updated:

    py scripts/build_salary_csv.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
SITE = "https://www.urbanforestpark.com"


def load_jobs():
    out = []
    for name in ("jobs.json", "global_jobs.json"):
        path = PUBLIC / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for j in data:
                    j = dict(j)
                    j["_registry"] = "india" if name == "jobs.json" else "global"
                    out.append(j)
        except Exception:
            pass
    return out


def main():
    jobs = load_jobs()
    active = [j for j in jobs if str(j.get("status") or "active") == "active"]

    out_dir = PUBLIC / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "green-jobs-salary.csv"

    fields = [
        "id", "registry", "clean_title", "organization", "city", "state", "country",
        "category", "position_type", "experience_level", "employment_type",
        "compensation_or_fellowship", "deadline_or_window", "valid_through",
        "qualification_summary", "date_added", "dossier_url", "apply_url",
    ]

    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for j in active:
            writer.writerow({
                "id": j.get("id", ""),
                "registry": j.get("_registry", ""),
                "clean_title": j.get("clean_title", ""),
                "organization": j.get("organization", ""),
                "city": j.get("city", ""),
                "state": j.get("state", ""),
                "country": j.get("country", ""),
                "category": j.get("category", ""),
                "position_type": j.get("position_type", ""),
                "experience_level": j.get("experience_level", ""),
                "employment_type": j.get("employment_type", ""),
                "compensation_or_fellowship": j.get("compensation_or_fellowship", ""),
                "deadline_or_window": j.get("deadline_or_window", ""),
                "valid_through": j.get("valid_through", ""),
                "qualification_summary": j.get("qualification_summary", ""),
                "date_added": j.get("date_added", ""),
                "dossier_url": f"{SITE}/jobs/{j.get('id', '')}",
                "apply_url": j.get("apply_url", ""),
            })

    print(f"Wrote {len(active)} rows to {out_path}")


if __name__ == "__main__":
    main()
