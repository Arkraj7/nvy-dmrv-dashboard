#!/usr/bin/env python3
"""Scan every active record's apply_url and classify it.

Rules from docs/LINK_POLICY.md:
- LinkedIn, Indeed, Naukri and lnkd.in are never fetched; they stay UNKNOWN_KEEP.
- 403/429/999, timeouts, TLS and DNS errors are UNKNOWN_KEEP (not dead).
- Only 404/410 or an explicit closed/expired page counts as dead.

Writes a JSON report; changes nothing.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path(r"C:\Users\arkra\NVY DMRV\nvy-dmrv-dashboard")
PUBLIC = ROOT / "public"
OUT = Path(r"C:\Users\arkra\AppData\Local\Temp\opencode\link_scan.json")

SKIP_HOSTS = (
    "linkedin.com",
    "lnkd.in",
    "indeed.",
    "naukri.com",
    "naukri.",
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

DEAD_STATUS = {404, 410}

CLOSED_PATTERNS = [
    r"job (?:has )?expired",
    r"this (?:job|position|vacancy|posting) (?:is )?no longer",
    r"(?:position|vacancy|role) (?:has been|is now) filled",
    r"applications? (?:are|is) (?:now )?closed",
    r"no longer accepting applications",
    r"deadline (?:has )?(?:passed|closed)",
    r"this posting is closed",
    r"vacancy (?:is )?closed",
    r"page not found",
    r"the page you (?:are|were) looking for",
    r"job not found",
]
CLOSED_RE = re.compile("|".join(f"(?:{p})" for p in CLOSED_PATTERNS), re.I)

CONTEXT_SSL = ssl.create_default_context()


def classify(rec):
    url = str(rec.get("apply_url") or "").strip()
    rid = rec.get("id")
    base = {"id": rid, "url": url, "date_added": rec.get("date_added"),
            "deadline": rec.get("deadline_or_window"), "entry_type": rec.get("entry_type"),
            "evergreen": rec.get("evergreen"), "title": rec.get("clean_title"),
            "org": rec.get("organization"), "country": rec.get("country")}

    if not url:
        return {**base, "status": "NO_URL", "code": None, "note": ""}

    if url.startswith("mailto:"):
        return {**base, "status": "MAILTO", "code": None, "note": ""}

    host = (urlsplit(url).hostname or "").lower()
    if any(h in host for h in SKIP_HOSTS):
        return {**base, "status": "UNKNOWN_KEEP", "code": None, "note": "policy: not fetched"}

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        resp = urllib.request.urlopen(req, timeout=25, context=CONTEXT_SSL)
        code = resp.status
        raw = resp.read(250000)
        try:
            text = raw.decode("utf-8", "ignore")
        except Exception:
            text = ""
        plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.I | re.S)
        plain = re.sub(r"<[^>]+>", " ", plain)
        plain = re.sub(r"\s+", " ", plain)
        m = CLOSED_RE.search(plain)
        if m:
            start = max(0, m.start() - 80)
            return {**base, "status": "CLOSED_TEXT", "code": code,
                    "note": plain[start:m.end() + 80][:200]}
        return {**base, "status": "LIVE", "code": code, "note": ""}
    except urllib.error.HTTPError as exc:
        code = exc.code
        if code in DEAD_STATUS:
            return {**base, "status": "DEAD", "code": code, "note": "http error"}
        return {**base, "status": "UNKNOWN_KEEP", "code": code, "note": "non-fatal http"}
    except Exception as exc:  # timeout, TLS, DNS
        return {**base, "status": "UNKNOWN_KEEP", "code": None, "note": type(exc).__name__}


def main():
    records = []
    for name in ("jobs.json", "global_jobs.json"):
        for rec in json.loads((PUBLIC / name).read_text(encoding="utf-8")):
            if rec.get("status") == "active":
                rec = dict(rec)
                rec["_file"] = name
                records.append(rec)

    print(f"scanning {len(records)} active records", flush=True)
    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(classify, rec): rec for rec in records}
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(records)}", flush=True)

    results.sort(key=lambda r: (r["status"], str(r.get("date_added")), r["id"] or ""))
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("status counts:", counts)
    print("report:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
