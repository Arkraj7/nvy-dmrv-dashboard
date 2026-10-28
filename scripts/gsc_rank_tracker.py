#!/usr/bin/env python3
"""Weekly Google Search Console rank tracker.

Exports query-level performance data (clicks, impressions, CTR, position)
for the Urban Forest Park property and writes a timestamped CSV + a
human-readable summary. Designed to run in GitHub Actions or locally.

Setup
-----
1. Enable the Google Search Console API in your GCP project.
2. Create a service account and download the JSON key.
3. Add the service-account email as an Owner in Search Console.
4. Set environment variables:
     GSC_PROPERTY  = https://www.urbanforestpark.com/   (or sc-domain:urbanforestpark.com)
     GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON = <full JSON key contents>
   (or GOOGLE_APPLICATION_CREDENTIALS = /path/to/key.json)

Usage
-----
    py scripts/gsc_rank_tracker.py --days 28 --output data/gsc_ranks.csv
    py scripts/gsc_rank_tracker.py --days 7 --top 50 --json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover
    service_account = None
    build = None


SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def load_credentials():
    if service_account is None:
        raise RuntimeError("google-api-python-client not installed. Run: pip install google-api-python-client google-auth")
    raw = os.environ.get("GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON")
    if raw:
        info = json.loads(raw)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if path and Path(path).exists():
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    raise RuntimeError(
        "No credentials found. Set GOOGLE_INDEXING_SERVICE_ACCOUNT_JSON or "
        "GOOGLE_APPLICATION_CREDENTIALS."
    )


def fetch_search_analytics(property_url: str, days: int, row_limit: int = 500) -> list[dict]:
    creds = load_credentials()
    service = build("searchconsole", "v1", credentials=creds)
    end = date.today() - timedelta(days=3)  # GSC data lags ~3 days
    start = end - timedelta(days=days - 1)
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": ["query", "page"],
        "rowLimit": row_limit,
        "dataState": "final",
    }
    response = service.searchanalytics().query(siteUrl=property_url, body=body).execute()
    rows = response.get("rows", [])
    out = []
    for r in rows:
        keys = r.get("keys", [])
        out.append({
            "query": keys[0] if len(keys) > 0 else "",
            "page": keys[1] if len(keys) > 1 else "",
            "clicks": r.get("clicks", 0),
            "impressions": r.get("impressions", 0),
            "ctr": round(r.get("ctr", 0) * 100, 2),
            "position": round(r.get("position", 0), 1),
        })
    return out, start.isoformat(), end.isoformat()


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "page", "clicks", "impressions", "ctr", "position"])
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict], top: int = 20) -> None:
    print(f"\n{'Query':<45} {'Page':<50} {'Clicks':>6} {'Impr':>7} {'CTR':>6} {'Pos':>6}")
    print("-" * 125)
    for r in sorted(rows, key=lambda x: -x["impressions"])[:top]:
        q = r["query"][:44]
        pg = r["page"].replace("https://www.urbanforestpark.com", "")[:49]
        print(f"{q:<45} {pg:<50} {r['clicks']:>6} {r['impressions']:>7} {r['ctr']:>5}% {r['position']:>6}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export GSC query performance data")
    parser.add_argument("--days", type=int, default=28, help="Lookback window (default 28)")
    parser.add_argument("--top", type=int, default=20, help="Top N queries to print (default 20)")
    parser.add_argument("--row-limit", type=int, default=500, help="Max rows from API (default 500)")
    parser.add_argument("--output", type=str, default="", help="CSV output path")
    parser.add_argument("--json", action="store_true", help="Also write JSON summary")
    args = parser.parse_args()

    property_url = os.environ.get("GSC_PROPERTY", "https://www.urbanforestpark.com/")
    print(f"Property: {property_url}")
    print(f"Fetching last {args.days} days of search analytics...")

    rows, start, end = fetch_search_analytics(property_url, args.days, args.row_limit)
    print(f"Date range: {start} to {end}")
    print(f"Total rows: {len(rows)}")

    if not rows:
        print("No data returned. The property may have no indexed pages yet or the service account lacks access.")
        return 0

    print_summary(rows, args.top)

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = DATA_DIR / f"gsc_ranks_{date.today().isoformat()}.csv"
    write_csv(rows, out_path)
    print(f"\nCSV written: {out_path}")

    if args.json:
        json_path = out_path.with_suffix(".json")
        json_path.write_text(json.dumps({"start": start, "end": end, "rows": rows}, indent=2), encoding="utf-8")
        print(f"JSON written: {json_path}")

    # Quick insights
    total_clicks = sum(r["clicks"] for r in rows)
    total_impr = sum(r["impressions"] for r in rows)
    avg_pos = sum(r["position"] * r["impressions"] for r in rows) / max(total_impr, 1)
    print(f"\n--- Quick insights ---")
    print(f"Total clicks: {total_clicks:,}")
    print(f"Total impressions: {total_impr:,}")
    print(f"Weighted avg position: {avg_pos:.1f}")
    print(f"Queries with > 100 impressions: {sum(1 for r in rows if r['impressions'] > 100)}")
    print(f"Queries in top 10: {sum(1 for r in rows if r['position'] <= 10)}")
    print(f"Queries in top 20: {sum(1 for r in rows if r['position'] <= 20)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
EOF
echo "written"