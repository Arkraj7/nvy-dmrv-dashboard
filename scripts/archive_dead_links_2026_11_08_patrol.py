"""Link-patrol fixes (2026-11-08): archive dead apply links, fix moved ASPRS page.

- pravah-weather-data-scientist-data-assimilation-delhi-2026: Ashby 404
- jsac-research-associate-junior-project-assistant-2026: portal 404
- unb-mscf-black-spruce-stress-resilience-2026: portal 404
- sandisk-sustainability-data-energy-analyst-bengaluru-2026: SmartRecruiters removed
- asprs-geospatial-research-grant-2027: page moved; update apply_url, keep active

Data is never deleted: archived records keep every field plus
status/date_archived, per docs/LINK_POLICY.md.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-08"

MOVES = [
    (ROOT / "public/jobs.json", ROOT / "public/archive.json",
     "pravah-weather-data-scientist-data-assimilation-delhi-2026"),
    (ROOT / "public/jobs.json", ROOT / "public/archive.json",
     "jsac-research-associate-junior-project-assistant-2026"),
    (ROOT / "public/jobs.json", ROOT / "public/archive.json",
     "sandisk-sustainability-data-energy-analyst-bengaluru-2026"),
    (ROOT / "public/global_jobs.json", ROOT / "public/global_archive.json",
     "unb-mscf-black-spruce-stress-resilience-2026"),
]


def main():
    for src, dst, rid in MOVES:
        active = json.loads(src.read_text(encoding="utf-8"))
        archive = json.loads(dst.read_text(encoding="utf-8"))
        rec = next((r for r in active if r.get("id") == rid), None)
        if rec is None:
            print(f"SKIP (not active): {rid}")
            continue
        if any(r.get("id") == rid for r in archive):
            print(f"SKIP (already archived): {rid}")
            continue
        active.remove(rec)
        rec = dict(rec)
        rec["status"] = "archived"
        rec["date_archived"] = TODAY
        archive.append(rec)
        src.write_text(json.dumps(active, ensure_ascii=False, indent=2), encoding="utf-8")
        dst.write_text(json.dumps(archive, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"ARCHIVED {rid} -> {dst.name}")

    gpath = ROOT / "public/global_jobs.json"
    g = json.loads(gpath.read_text(encoding="utf-8"))
    for rec in g:
        if rec.get("id") == "asprs-geospatial-research-grant-2027":
            rec["apply_url"] = "https://www.asprs.org/Main/Education---Careers/ASPRS-Scholarships.aspx"
            print("UPDATED ASPRS apply_url")
    gpath.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
