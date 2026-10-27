#!/usr/bin/env python3
"""Submit the sitemap and active job pages to Google.

Google has no public API for the Search Console "Request indexing" button.
The supported automation is:

* Search Console API -> ``sitemaps.submit`` for the sitemap. This covers every
  hub and job URL in one request.
* Indexing API -> ``urlNotifications.publish`` for job pages. Google accepts
  this API only for pages with ``JobPosting`` or ``BroadcastEvent`` structured
  data, which is exactly what ``/jobs/<id>`` pages carry. Never send hub pages
  through it.

Both APIs use the same service account. Add the service account email as an
Owner of the Search Console property, then provide the JSON key through
``GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON`` (raw JSON) or
``GOOGLE_APPLICATION_CREDENTIALS`` (path).

Usage:
    py scripts/google_indexing.py --dry-run --all
    py scripts/google_indexing.py --sitemap
    py scripts/google_indexing.py --jobs --limit 200
    py scripts/google_indexing.py --all

Environment:
    GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON  raw service-account JSON
    GOOGLE_APPLICATION_CREDENTIALS        path to the JSON key
    GSC_PROPERTY                          default https://www.urbanforestpark.com/
    SITEMAP_URL                           default https://www.urbanforestpark.com/sitemap.xml
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:  # pragma: no cover - surfaced with a clear message
    service_account = None  # type: ignore[assignment]
    build = None  # type: ignore[assignment]
    HttpError = Exception  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = "https://www.urbanforestpark.com"
DEFAULT_PROPERTY = SITE + "/"
DEFAULT_SITEMAP = SITE + "/sitemap.xml"
DEFAULT_STATE = ROOT / "scripts" / "google_indexing_state.json"
SCOPES = [
    "https://www.googleapis.com/auth/indexing",
    "https://www.googleapis.com/auth/webmasters",
]
FINGERPRINT_FIELDS = (
    "id",
    "clean_title",
    "title",
    "organization",
    "city",
    "state",
    "country",
    "category",
    "position_type",
    "entry_type",
    "status",
    "deadline_or_window",
    "valid_through",
    "apply_url",
    "date_added",
)


def load_records(public: Path, filename: str) -> List[Dict[str, Any]]:
    path = public / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("jobs", [])
    return [entry for entry in data if isinstance(entry, dict)] if isinstance(data, list) else []


def record_fingerprint(record: Dict[str, Any]) -> str:
    payload = json.dumps(
        {key: record.get(key) for key in FINGERPRINT_FIELDS},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def collect_job_urls(public: Path = PUBLIC, site: str = SITE) -> Dict[str, str]:
    """Return ``{url: fingerprint}`` for every publishable active job posting.

    Portal/award/course records stay in the sitemap but are not sent to the
    Indexing API, which is reserved for JobPosting and BroadcastEvent pages.
    """
    current: Dict[str, str] = {}
    base = site.rstrip("/")
    for filename in ("jobs.json", "global_jobs.json"):
        for record in load_records(public, filename):
            if record.get("status") == "quarantined":
                continue
            if (record.get("entry_type") or "posting") != "posting":
                continue
            job_id = str(record.get("id") or "").strip()
            if not job_id:
                continue
            url = f"{base}/jobs/{quote(job_id, safe='-._~')}"
            current[url] = record_fingerprint(record)
    return current


def pending_urls(
    current: Dict[str, str], state_urls: Dict[str, str], force: bool = False
) -> List[str]:
    if force:
        return sorted(current)
    return sorted(
        url for url, fingerprint in current.items() if state_urls.get(url) != fingerprint
    )


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"urls": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"urls": {}}
    if not isinstance(data, dict) or not isinstance(data.get("urls"), dict):
        return {"urls": {}}
    return data


def save_state(path: Path, urls: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_run": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "urls": dict(sorted(urls.items())),
    }
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def get_credentials(args: argparse.Namespace) -> Optional[Any]:
    if service_account is None:
        print(
            "google-auth / google-api-python-client are not installed. "
            "Run: pip install -r scripts/requirements.txt"
        )
        return None
    raw = (os.environ.get("GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON") or "").strip()
    path = (args.credentials or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    try:
        if raw.startswith("{"):
            info = json.loads(raw)
            return service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES
            )
        if raw:
            path = raw
        if path:
            return service_account.Credentials.from_service_account_file(
                path, scopes=SCOPES
            )
    except Exception as exc:
        print("Could not load Google credentials:", str(exc)[:300])
        return None
    return None


def submit_sitemap(credentials: Any, property_url: str, sitemap_url: str) -> bool:
    """Submit the sitemap through the Search Console API."""
    last_error: Optional[Exception] = None
    for api, version in (("searchconsole", "v1"), ("webmasters", "v3")):
        try:
            service = build(api, version, credentials=credentials, cache_discovery=False)
            service.sitemaps().submit(
                siteUrl=property_url, feedpath=sitemap_url
            ).execute()
            print(f"Sitemap submitted: {sitemap_url} -> {property_url} ({api} {version})")
            return True
        except Exception as exc:  # try the alternate API name
            last_error = exc
    print("Sitemap submission failed:", str(last_error)[:500])
    print(
        "Check that the service-account email is an Owner of the Search Console "
        f"property {property_url!r}."
    )
    return False


def submit_jobs(credentials: Any, urls: List[str], limit: int) -> List[str]:
    """Publish URL_UPDATED notifications for job pages, respecting the quota."""
    if not urls:
        print("No new or changed job URLs to submit.")
        return []
    urls = urls[: max(1, limit)]
    service = build("indexing", "v3", credentials=credentials, cache_discovery=False)
    submitted: List[str] = []
    for index, url in enumerate(urls, 1):
        try:
            service.urlNotifications().publish(
                body={"url": url, "type": "URL_UPDATED"}
            ).execute()
            submitted.append(url)
            print(f"[{index}/{len(urls)}] OK {url}")
        except HttpError as exc:
            status = getattr(getattr(exc, "resp", None), "status", None)
            print(f"[{index}/{len(urls)}] FAIL {status} {url} {str(exc)[:220]}")
            if status == 429:
                print("Indexing API daily quota reached; stopping this run.")
                break
        except Exception as exc:
            print(f"[{index}/{len(urls)}] FAIL {url} {str(exc)[:220]}")
    return submitted


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Submit the sitemap and active job pages to Google"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sitemap", action="store_true", help="submit the sitemap only")
    group.add_argument("--jobs", action="store_true", help="submit job pages only")
    group.add_argument("--all", action="store_true", help="submit sitemap and job pages")
    parser.add_argument("--dry-run", action="store_true", help="print actions only")
    parser.add_argument("--force", action="store_true", help="ignore saved state")
    parser.add_argument("--limit", type=int, default=200, help="max job URLs (default 200)")
    parser.add_argument("--credentials", help="path to the service-account JSON key")
    parser.add_argument("--property", default=os.environ.get("GSC_PROPERTY") or DEFAULT_PROPERTY)
    parser.add_argument("--sitemap-url", default=os.environ.get("SITEMAP_URL") or DEFAULT_SITEMAP)
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--require-credentials", action="store_true")
    args = parser.parse_args(argv)

    if args.all or (not args.sitemap and not args.jobs):
        do_sitemap = do_jobs = True
    else:
        do_sitemap = args.sitemap
        do_jobs = args.jobs

    state_path = Path(args.state)
    if not state_path.is_absolute():
        state_path = ROOT / state_path

    current = collect_job_urls()
    state = load_state(state_path)
    pending = pending_urls(current, state.get("urls", {}), force=args.force)

    print(f"Active job URLs: {len(current)} | new/changed: {len(pending)}")
    print(f"State: {state_path}")
    if do_sitemap:
        print(f"Sitemap: {args.sitemap_url} -> property {args.property}")
    if do_jobs:
        print(f"Job URLs to submit: {min(len(pending), max(1, args.limit))}")

    if args.dry_run:
        shown = (
            pending[: min(len(pending), max(1, args.limit))] if do_jobs else []
        )
        for url in shown:
            print("  DRY", url)
        if do_jobs and len(pending) > len(shown):
            print(
                f"  ... and {len(pending) - len(shown)} more "
                f"(limit {max(1, args.limit)} per run)"
            )
        print("Dry run: no API calls made, state unchanged.")
        return 0

    credentials = get_credentials(args)
    if credentials is None:
        print(
            "No Google credentials configured. Set "
            "GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON (raw JSON) or "
            "GOOGLE_APPLICATION_CREDENTIALS (path)."
        )
        return 1 if args.require_credentials else 0

    sitemap_ok = True
    if do_sitemap:
        sitemap_ok = submit_sitemap(credentials, args.property, args.sitemap_url)

    submitted: List[str] = []
    if do_jobs:
        submitted = submit_jobs(credentials, pending, args.limit)
        # Keep fingerprints for URLs that are still active. A changed URL that
        # was not submitted (quota/limit) keeps its old fingerprint so the next
        # run retries it.
        next_urls = {
            url: fingerprint
            for url, fingerprint in state.get("urls", {}).items()
            if url in current
        }
        for url in submitted:
            next_urls[url] = current[url]
        save_state(state_path, next_urls)
        print(f"Submitted {len(submitted)} job URL(s); state updated.")

    if do_sitemap and not sitemap_ok:
        return 1
    if do_jobs and pending and not submitted:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
