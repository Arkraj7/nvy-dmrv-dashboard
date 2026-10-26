#!/usr/bin/env python3
"""Direct-link policy guard (policy v2).

Two modes:

  python scripts/link_guard.py                 # data guard (pre-build)
  python scripts/link_guard.py --dist dist     # built-site guard (post-build)

Data guard:
  * every public record has a real apply_url
  * no news wrapper or URL shortener is stored
  * postings point at a specific job page; section roots must be tagged
    ``careers_portal``
  * a verification or link_policy block is present

Built-site guard:
  * no quarantined slug appears in any HTML file or sitemap
  * no news-wrapper/shortener hrefs are rendered
  * job links point at dossier URLs
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from link_policy import (
    is_generic_url,
    is_shortener,
    is_wrapper,
    matches_platform_pattern,
    platform_for,
)
from verify_link import load_employers_registry

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE_HOSTS = {"urbanforestpark.com", "www.urbanforestpark.com"}

DATA_FILES = [
    PUBLIC / "jobs.json",
    PUBLIC / "global_jobs.json",
    PUBLIC / "archive.json",
    PUBLIC / "global_archive.json",
]


def load_records() -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in DATA_FILES:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FAIL read {path}: {exc}")
            continue
        for entry in data if isinstance(data, list) else []:
            if isinstance(entry, dict):
                rows.append((path, entry))
    return rows


def host_of(url: str) -> str:
    return (urlparse(str(url or "")).hostname or "").lower()


def is_direct(record: dict) -> bool:
    url = str(record.get("apply_url") or "")
    host = host_of(url)
    platform = platform_for(host)
    if platform:
        return bool(matches_platform_pattern(url, platform))
    return not is_generic_url(url)


def data_guard() -> list[str]:
    violations: list[str] = []
    for path, record in load_records():
        if record.get("status") == "quarantined":
            continue
        if record.get("status") == "archived":
            continue
        rid = record.get("id") or "(no id)"
        apply_url = str(record.get("apply_url") or "")
        if not apply_url.lower().startswith(("http", "mailto:")):
            violations.append(f"{path.name}:{rid}: missing apply_url")
            continue
        if is_wrapper(apply_url):
            violations.append(f"{path.name}:{rid}: news wrapper stored")
        if is_shortener(apply_url):
            violations.append(f"{path.name}:{rid}: URL shortener stored")
        entry_type = record.get("entry_type")
        if entry_type not in {"posting", "careers_portal", "award_portal", "unknown"}:
            violations.append(f"{path.name}:{rid}: invalid entry_type {entry_type!r}")
        if entry_type in {"posting", "award_portal"} and not is_direct(record):
            violations.append(
                f"{path.name}:{rid}: non-direct URL tagged as {entry_type}"
            )
        if not (record.get("verification") or record.get("link_policy")):
            violations.append(f"{path.name}:{rid}: missing verification/link_policy block")
    return violations


def dist_guard(dist: Path) -> list[str]:
    violations: list[str] = []
    if not dist.exists():
        return [f"dist directory not found: {dist}"]

    quarantined_ids = {
        str(record.get("id"))
        for _path, record in load_records()
        if record.get("status") == "quarantined" and record.get("id")
    }
    published_ids = {
        str(record.get("id"))
        for _path, record in load_records()
        if record.get("status") != "quarantined" and record.get("id")
    }

    for path in sorted(dist.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(dist)

        for qid in quarantined_ids:
            if qid and qid in text:
                violations.append(f"{rel}: quarantined slug present: {qid}")

        for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
            value = href.strip()
            if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                continue
            parsed = urlparse(value)
            if parsed.scheme not in ("http", "https"):
                # Relative link: check the internal dossier path below.
                path = parsed.path
            else:
                host = (parsed.hostname or "").lower()
                if not host:
                    continue
                if is_wrapper(value):
                    violations.append(f"{rel}: news-wrapper outbound link {value[:120]}")
                elif is_shortener(value):
                    violations.append(f"{rel}: shortener outbound link {value[:120]}")
                if host not in SITE_HOSTS:
                    # External URLs such as linkedin.com/jobs/view/... must not
                    # be mistaken for local /jobs/<id> dossier links.
                    continue
                path = parsed.path

            for job_id in re.findall(r"/jobs/([A-Za-z0-9._-]+)", path):
                job_id = job_id.removesuffix(".html").rstrip("/")
                if job_id in quarantined_ids:
                    violations.append(f"{rel}: link to quarantined dossier {job_id}")
                elif job_id not in published_ids:
                    violations.append(f"{rel}: link to unknown job page {job_id}")
                elif not (dist / "jobs" / f"{job_id}.html").exists():
                    violations.append(f"{rel}: static job page missing for {job_id}")

        for job_id in re.findall(r"\?job=([A-Za-z0-9._-]+)", text):
            if job_id in quarantined_ids:
                violations.append(f"{rel}: link to quarantined dossier {job_id}")

    sitemap = dist / "sitemap.xml"
    if sitemap.exists():
        sm = sitemap.read_text(encoding="utf-8", errors="ignore")
        for qid in quarantined_ids:
            if qid and qid in sm:
                violations.append(f"sitemap.xml: quarantined slug present: {qid}")
        for job_id in re.findall(r"\?job=([A-Za-z0-9._-]+)", sm):
            if job_id not in published_ids:
                violations.append(f"sitemap.xml: unknown job slug {job_id}")
        for job_id in re.findall(r"/jobs/([A-Za-z0-9._-]+)", sm):
            if job_id not in published_ids:
                violations.append(f"sitemap.xml: unknown job page {job_id}")
            elif not (dist / "jobs" / f"{job_id}.html").exists():
                violations.append(f"sitemap.xml: missing static page {job_id}")
    else:
        violations.append("dist/sitemap.xml missing")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Direct-link policy guard")
    parser.add_argument(
        "--dist",
        help="Built site directory to scan (e.g. dist). Omit for the data guard.",
    )
    args = parser.parse_args(argv)

    violations = dist_guard(Path(args.dist)) if args.dist else data_guard()
    if violations:
        print(f"LINK POLICY: {len(violations)} violation(s)")
        for item in violations:
            print("  - " + item)
        return 1
    mode = "dist" if args.dist else "data"
    print(f"LINK POLICY OK ({mode}): no violations")
    return 0


if __name__ == "__main__":
    sys.exit(main())
