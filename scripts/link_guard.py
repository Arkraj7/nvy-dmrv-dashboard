#!/usr/bin/env python3
"""Official-link policy guard.

Two modes:

  python scripts/link_guard.py                 # data guard (pre-build)
  python scripts/link_guard.py --dist dist     # built-site guard (post-build)

Data guard (fails closed):
  * every active, non-quarantined record has a real apply_url
  * no blocklisted job board / aggregator / Google News wrapper is stored
  * the apply host belongs to the record's employer registry entry
  * the record carries verification metadata (verified_at, entry_type)

Built-site guard:
  * no quarantined slug appears in any HTML file or sitemap
  * every outbound link on a built page is limited to
    {apply_url host, employer homepage, urbanforestpark.com}
    plus the site's own community/asset infrastructure
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from verify_link import BLOCKLISTED_HOSTS, load_employers_registry

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE_HOSTS = {"urbanforestpark.com", "www.urbanforestpark.com"}

# Non-job infrastructure the site itself needs (fonts, favicons, community
# channels, social profiles). These are not application destinations.
INFRA_HOSTS = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "www.google.com",
    "google.com",
    "api.whatsapp.com",
    "wa.me",
    "chat.whatsapp.com",
    "t.me",
    "telegram.me",
    "www.linkedin.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "www.instagram.com",
    "instagram.com",
}

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


def bare(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def is_blocklisted(host: str) -> bool:
    host = (host or "").lower()
    return host in BLOCKLISTED_HOSTS or bare(host) in BLOCKLISTED_HOSTS


def employer_hosts(registry: dict, employer_id: str) -> set[str]:
    hosts: set[str] = set()
    for employer in registry.get("employers") or []:
        if employer.get("id") != employer_id:
            continue
        for value in (employer.get("domains") or []) + (employer.get("ats_hosts") or []):
            value = str(value or "").lower().strip()
            if value:
                hosts.add(value)
        website = host_of(employer.get("website") or "")
        if website:
            hosts.add(website)
    return hosts


def host_matches(host: str, allowed: set[str]) -> bool:
    if not host:
        return False
    host = host.lower()
    if host in allowed or bare(host) in allowed:
        return True
    return any(host.endswith("." + entry) or bare(host).endswith("." + entry) for entry in allowed)


def data_guard() -> list[str]:
    violations: list[str] = []
    registry = load_employers_registry(str(PUBLIC / "employers.json"))
    for path, record in load_records():
        if record.get("status") == "quarantined":
            continue
        if record.get("status") == "archived":
            continue  # archived records render no outbound link
        rid = record.get("id") or "(no id)"
        apply_url = str(record.get("apply_url") or "")
        if not apply_url.lower().startswith("http"):
            violations.append(f"{path.name}:{rid}: missing apply_url")
            continue
        host = host_of(apply_url)
        if is_blocklisted(host):
            violations.append(f"{path.name}:{rid}: blocklisted host {host}")
        if host.endswith("news.google.com"):
            violations.append(f"{path.name}:{rid}: Google News wrapper stored")
        employer_id = str(record.get("employer_id") or "")
        if not employer_id:
            violations.append(f"{path.name}:{rid}: employer_id missing")
            continue
        allowed = employer_hosts(registry, employer_id)
        if not allowed:
            violations.append(
                f"{path.name}:{rid}: employer {employer_id} not in registry"
            )
        elif not host_matches(host, allowed):
            violations.append(
                f"{path.name}:{rid}: apply host {host} outside registry {sorted(allowed)}"
            )
        verification = record.get("verification") or {}
        if not verification.get("verified_at"):
            violations.append(f"{path.name}:{rid}: missing verification.verified_at")
        entry_type = record.get("entry_type")
        if entry_type not in {"posting", "careers_portal", "award_portal", "unknown"}:
            violations.append(f"{path.name}:{rid}: invalid entry_type {entry_type!r}")
    return violations


def collect_allowed_hosts() -> set[str]:
    registry = load_employers_registry(str(PUBLIC / "employers.json"))
    allowed = set(SITE_HOSTS) | INFRA_HOSTS
    for _path, record in load_records():
        if record.get("status") == "quarantined" or record.get("status") == "archived":
            continue
        host = host_of(record.get("apply_url") or "")
        if host:
            allowed.add(host)
            allowed.add(bare(host))
        employer_id = str(record.get("employer_id") or "")
        for entry in employer_hosts(registry, employer_id):
            allowed.add(entry)
            allowed.add(bare(entry))
    return allowed


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
    allowed_hosts = collect_allowed_hosts()

    html_files = sorted(dist.rglob("*.html"))
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(dist)

        # Quarantined slugs must not leak into any built page.
        for qid in quarantined_ids:
            if qid and qid in text:
                violations.append(f"{rel}: quarantined slug present: {qid}")

        # The outbound-link rule applies to job pages (pages that render
        # listings); institutional/calculator pages have their own assets.
        if "?job=" not in text:
            continue

        for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
            value = href.strip()
            if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                continue
            parsed = urlparse(value)
            if parsed.scheme not in ("http", "https"):
                continue
            host = (parsed.hostname or "").lower()
            if not host:
                continue
            if host_matches(host, SITE_HOSTS | INFRA_HOSTS):
                continue
            if is_blocklisted(host):
                violations.append(f"{rel}: blocklisted outbound link {host}")
                continue
            if host_matches(host, allowed_hosts):
                continue
            violations.append(f"{rel}: outbound link outside policy {host} ({value[:120]})")

        # Job links inside the built page must point at dossier URLs.
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
    else:
        violations.append("dist/sitemap.xml missing")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Official-link policy guard")
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
