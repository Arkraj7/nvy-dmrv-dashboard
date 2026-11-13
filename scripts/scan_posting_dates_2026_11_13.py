#!/usr/bin/env python3
"""Second pass: pull a structured posting date from every fetchable apply page.

Only evidence the page itself states is used:
- JSON-LD "datePosted" / "validThrough"
- an explicit "Posted <date>" / "Date: <date>" / "Posted N days ago" line

Records whose page is bot-blocked or policy-skipped are left untouched.
Writes a JSON report; changes nothing.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

SCAN = Path(r"C:\Users\arkra\AppData\Local\Temp\opencode\link_scan.json")
OUT = Path(r"C:\Users\arkra\AppData\Local\Temp\opencode\posting_dates.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

MONTHS = {m.lower(): i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}
MON = "|".join(MONTHS)

DATE_DMY = re.compile(rf"(\d{{1,2}})\s*({MON})[a-z]*\.?,?\s*(\d{{4}})", re.I)
DATE_MDY = re.compile(rf"({MON})[a-z]*\.?\s+(\d{{1,2}}),?\s+(\d{{4}})", re.I)
JSON_DATE = re.compile(r'"(?:datePosted|datePublished)"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})')
REL_AGO = re.compile(r"(\d+)\s*(day|week|month)s?\s+ago", re.I)


def parse_dates(text):
    found = []
    for m in DATE_DMY.finditer(text):
        try:
            found.append(date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))))
        except (KeyError, ValueError):
            pass
    for m in DATE_MDY.finditer(text):
        try:
            found.append(date(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2))))
        except (KeyError, ValueError):
            pass
    return found


def probe(rec):
    url = rec["url"]
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        resp = urllib.request.urlopen(req, timeout=25)
        body = resp.read(400000).decode("utf-8", "ignore")
    except Exception as exc:
        return {"id": rec["id"], "posted": None, "source": f"err:{type(exc).__name__}"}

    m = JSON_DATE.search(body)
    if m:
        return {"id": rec["id"], "posted": m.group(1), "source": "json-ld"}

    plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.I | re.S)
    plain = re.sub(r"<[^>]+>", "\n", plain)
    for line in plain.split("\n"):
        if re.search(r"\b(?:posted|date added|publish(?:ed)? date|date)\b", line, re.I):
            dates = parse_dates(line)
            if dates:
                return {"id": rec["id"], "posted": min(dates).isoformat(), "source": "visible"}

    rel = REL_AGO.search(plain)
    if rel:
        return {"id": rec["id"], "posted": None, "ago": rel.group(0), "source": "relative"}
    return {"id": rec["id"], "posted": None, "source": "none"}


def main():
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    targets = [r for r in scan if r["status"] in ("LIVE", "CLOSED_TEXT")]
    print(f"probing {len(targets)} reachable pages", flush=True)

    out = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(probe, r) for r in targets]
        for i, fut in enumerate(as_completed(futures), 1):
            out.append(fut.result())
            if i % 40 == 0:
                print(f"  {i}/{len(targets)}", flush=True)

    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    dated = [r for r in out if r["posted"]]
    print(f"pages with a stated posting date: {len(dated)}/{len(targets)}")
    print("report:", OUT)


if __name__ == "__main__":
    raise SystemExit(main())
