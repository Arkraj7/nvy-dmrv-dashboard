#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Urban Forest Park - Weekly LinkedIn Top-10 opportunities roundup.

Builds a paste-ready LinkedIn post every Monday at 09:00 IST (cron
``'30 3 * * 1'`` in .github/workflows/weekly_linkedin.yml):

  * selects 8-10 highest-impact opportunities from the past 7 days,
    balancing the India registry across jobs / JRF / fellowships /
    scholarships / grants / internships (with graceful widening to 14 days
    and then most-recent when the window is quiet),
  * adds the top 2-3 Global highlights, each labelled ``[INDIA]`` or
    ``[GLOBAL]`` so the two strictly separated registries stay distinct,
  * writes ``public/linkedin_weekly_post.txt`` (copied verbatim from the
    internal Syndication Desk drawer - /admin-syndication) and
    ``public/linkedin_weekly.json`` (hook, items, metadata),
  * emails the post to SMTP_USER with the exact subject
    ``Ready to Post: Your Weekly LinkedIn Top 10 Opportunities Roundup``,
  * optionally publishes it directly through the LinkedIn REST API
    (POST https://api.linkedin.com/rest/posts) when LINKEDIN_ACCESS_TOKEN
    and LINKEDIN_AUTHOR_URN are configured.

CI discipline: the script never fails the workflow. Missing SMTP
credentials, missing LinkedIn secrets, absent data files or rate limits are
all logged and skipped (exit 0).

Usage:
    py scripts/weekly_linkedin_post.py                 # build + email + publish
    py scripts/weekly_linkedin_post.py --dry-run       # build only
    py scripts/weekly_linkedin_post.py --date 2026-10-19 --days 7
    py scripts/weekly_linkedin_post.py --to me@x.com   # test email recipient
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import smtplib
import ssl
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("weekly_linkedin")

IST = timezone(timedelta(hours=5, minutes=30))
SITE = "https://www.urbanforestpark.com"
JOB_URL = SITE + "/jobs/{id}"
GLOBAL_HUB = SITE + "/global-climate-sustainability-opportunities.html"

EMAIL_SUBJECT = "Ready to Post: Your Weekly LinkedIn Top 10 Opportunities Roundup"

HASHTAGS = (
    "#ClimateJobs #Forestry #ESG #Sustainability #JRF #Fellowships "
    "#GreenJobsIndia #GIS #UrbanForestPark"
)

CTA = (
    "Apply directly through the official portals \u2014 every listing links straight to the "
    "source (no fees).\n"
    "Full registry \u00b7 daily alerts \u00b7 Global opportunities hub: " + SITE + "/\n"
    "Telegram: https://t.me/urbanforestpark"
)

KIND_ORDER = [
    "Job / Career",
    "Fellowship",
    "Scholarship",
    "Grant / Funding",
    "Internship",
    "Competition / Award",
]

POSITION_TYPE_BY_CATEGORY: Dict[str, str] = {
    "Academic, JRF, SRF & PhD Positions": "JRF / SRF",
    "Research Associate & Project Staff (Contractual)": "Project Associate / Research Associate",
    "Grants & Research Funding": "Young Professional / Consultant (Contractual)",
    "Scholarships & Doctoral Support": "PhD / Doctoral Fellowship",
    "Fellowships & Leadership Programs": "Fellowship / Internship",
    "Internships & Student Traineeships": "Fellowship / Internship",
    "Competitions, Hackathons & Awards": "Fellowship / Internship",
}

POSITION_TYPE_PATTERNS: List[Tuple[str, str]] = [
    ("jrf", "JRF / SRF"),
    ("junior research fellow", "JRF / SRF"),
    ("senior research fellow", "JRF / SRF"),
    ("research associate", "Project Associate / Research Associate"),
    ("project associate", "Project Associate / Research Associate"),
    ("phd", "PhD / Doctoral Fellowship"),
    ("doctoral", "PhD / Doctoral Fellowship"),
    ("postdoc", "PhD / Doctoral Fellowship"),
    ("post-doc", "PhD / Doctoral Fellowship"),
    ("faculty", "Faculty / Academic"),
    ("professor", "Faculty / Academic"),
    ("fellow", "Fellowship / Internship"),
    ("fellowship", "Fellowship / Internship"),
    ("intern", "Fellowship / Internship"),
    ("trainee", "Fellowship / Internship"),
    ("young professional", "Young Professional / Consultant (Contractual)"),
    ("consultant", "Young Professional / Consultant (Contractual)"),
]

PRESTIGE_KEYWORDS: List[str] = [
    "indian institute", "iit ", "iisc", "iim ", "icar", "icfre", "wildlife institute",
    "ministry", "government", "state forest", "csir", "dst", "serb", "anrf", "niti",
    "university", "institute of", "centre for", "center for", "tifr", "jnu", "du ",
    "unfccc", "undp", "unep", "iucn", "world bank", "green climate fund", "gef",
    "wri", "ceew", "teri", "atree", "future earth", "esa", "wwf", "unesco", "fao",
    "chevening", "erasmus", "earthshot", "zayed",
]

KIND_SCORE = {
    "Job / Career": 6.0,
    "Fellowship": 7.0,
    "Scholarship": 8.0,
    "Grant / Funding": 8.0,
    "Internship": 5.0,
    "Competition / Award": 6.0,
}

DEADLINE_FORMATS = (
    "%Y-%m-%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d/%m/%Y",
    "%d-%m-%Y",
)


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def ist_today() -> date:
    return datetime.now(IST).date()


def load_json(path: Path) -> Any:
    if not path.exists():
        log.warning("%s not found", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("Could not read %s: %s", path, exc)
        return None


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def parse_date(value: Any) -> Optional[date]:
    text = clean(value)
    if not text:
        return None
    text = text[:10] if len(text) >= 10 and text[4] == "-" else text
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_deadline(value: Any) -> Optional[date]:
    text = clean(value)
    if not text:
        return None
    # "20 November 2026" / "November 20, 2026" / "2026-11-20" etc.
    for token in (text, text.split("(")[0].strip().rstrip(".")):
        for fmt in DEADLINE_FORMATS:
            try:
                return datetime.strptime(token, fmt).date()
            except ValueError:
                continue
    return None


def position_type_of(job: Dict[str, Any]) -> str:
    explicit = clean(job.get("position_type"))
    if explicit:
        return explicit
    text = (clean(job.get("clean_title")) + " " + clean(job.get("category"))).lower()
    for needle, label in POSITION_TYPE_PATTERNS:
        if needle in text:
            return label
    category = clean(job.get("category"))
    return POSITION_TYPE_BY_CATEGORY.get(category, "Full-Time Corporate / NGO")


def kind_of(job: Dict[str, Any]) -> str:
    kind = clean(job.get("opportunity_kind"))
    return kind if kind in KIND_ORDER else "Job / Career"


def location_of(job: Dict[str, Any]) -> str:
    if clean(job.get("region")):
        return clean(job.get("city")) or clean(job.get("country")) or clean(job.get("region"))
    city = clean(job.get("city"))
    state = clean(job.get("state"))
    if city and state:
        return f"{city}, {state}"
    return city or state or "India"


def impact_score(job: Dict[str, Any], today: date) -> float:
    score = 0.0
    added = parse_date(job.get("date_added"))
    if added:
        age = (today - added).days
        if age <= 2:
            score += 30.0
        elif age <= 4:
            score += 22.0
        elif age <= 7:
            score += 14.0
        elif age <= 14:
            score += 8.0
        else:
            score += 3.0
    score += KIND_SCORE.get(kind_of(job), 5.0)

    haystack = (
        clean(job.get("organization")) + " " + clean(job.get("clean_title"))
    ).lower()
    hits = 0
    for keyword in PRESTIGE_KEYWORDS:
        if keyword in haystack:
            hits += 1
            if hits >= 3:
                break
    score += hits * 4.0

    deadline_raw = clean(job.get("deadline_or_window"))
    if deadline_raw:
        if "rolling" in deadline_raw.lower() or "open" in deadline_raw.lower():
            score += 2.0
        deadline = parse_deadline(deadline_raw)
        if deadline:
            days_left = (deadline - today).days
            if 0 <= days_left <= 7:
                score += 8.0
            elif 0 <= days_left <= 21:
                score += 6.0
            elif days_left < 0 and kind_of(job) == "Job / Career":
                score -= 4.0

    if clean(job.get("compensation_or_fellowship")):
        score += 2.0
    return score


def pool_for_window(
    jobs: List[Dict[str, Any]], today: date, days: int
) -> Tuple[List[Dict[str, Any]], str]:
    cutoff = today - timedelta(days=days)
    window: List[Dict[str, Any]] = []
    for job in jobs:
        added = parse_date(job.get("date_added"))
        if added and added >= cutoff:
            window.append(job)
    if window:
        return window, f"last {days} day(s)"
    return list(jobs), "most recent verified listings (quiet window)"


def select_roundup(
    india_pool: List[Dict[str, Any]],
    global_pool: List[Dict[str, Any]],
    today: date,
    min_items: int = 8,
    max_items: int = 10,
    global_max: int = 3,
) -> List[Dict[str, Any]]:
    def scored(pool: List[Dict[str, Any]], registry: str) -> List[Dict[str, Any]]:
        rows = []
        for job in pool:
            rows.append(
                {
                    "job": job,
                    "registry": registry,
                    "score": impact_score(job, today),
                }
            )
        rows.sort(key=lambda row: row["score"], reverse=True)
        return rows

    india_rows = scored(india_pool, "india")
    global_rows = scored(global_pool, "global")

    picked: List[Dict[str, Any]] = []
    used: set = set()

    def job_key(row: Dict[str, Any]) -> str:
        return row["registry"] + ":" + clean(row["job"].get("id"))

    # 1. Balance the India side: one strong pick per opportunity kind first.
    for kind in KIND_ORDER:
        for row in india_rows:
            if job_key(row) in used:
                continue
            if kind_of(row["job"]) == kind:
                picked.append(row)
                used.add(job_key(row))
                break
        if len(picked) >= max_items - global_max:
            break

    # 2. Global highlights (top 2-3, spread across kinds when possible).
    global_selected = 0
    for kind in KIND_ORDER:
        if global_selected >= global_max:
            break
        for row in global_rows:
            if job_key(row) in used or kind_of(row["job"]) != kind:
                continue
            picked.append(row)
            used.add(job_key(row))
            global_selected += 1
            break
    for row in global_rows:
        if global_selected >= global_max:
            break
        if job_key(row) in used:
            continue
        picked.append(row)
        used.add(job_key(row))
        global_selected += 1

    # 3. Fill with the strongest India picks.
    for row in india_rows:
        if len(picked) >= max_items:
            break
        if job_key(row) in used:
            continue
        picked.append(row)
        used.add(job_key(row))

    # 4. Anything still missing comes from the global pool.
    for row in global_rows:
        if len(picked) >= max_items:
            break
        if job_key(row) in used:
            continue
        picked.append(row)
        used.add(job_key(row))

    picked.sort(key=lambda row: row["score"], reverse=True)
    if len(picked) > max_items:
        picked = picked[:max_items]
    if len(picked) < min_items:
        log.warning(
            "Only %d eligible opportunit(y/ies) available for the roundup (minimum %d).",
            len(picked),
            min_items,
        )
    return picked


def line_for_item(position: int, row: Dict[str, Any]) -> Tuple[str, str]:
    job = row["job"]
    label = "INDIA" if row["registry"] == "india" else "GLOBAL"
    title = clean(job.get("clean_title")) or "Untitled opportunity"
    org = clean(job.get("organization")) or "Organisation"
    location = location_of(job)
    ptype = position_type_of(job)
    url = JOB_URL.format(id=clean(job.get("id")))
    return (
        f"{position}. [{label}] {title} \u2014 {org} ({location} | {ptype})",
        url,
    )


def build_post_text(rows: List[Dict[str, Any]], today: date) -> str:
    india_count = sum(1 for row in rows if row["registry"] == "india")
    global_count = len(rows) - india_count
    hook = (
        "\U0001F331 Top " + str(len(rows)) + " green opportunities this week \u2014 "
        "climate, forestry, ESG, geospatial & sustainability (" +
        f"{india_count} India" + (f" + {global_count} Global" if global_count else "") +
        "), verified with direct application links:\n"
        "\U0001F1EE\U0001F1F3 India Jobs \u00b7 \U0001F30D Global Opportunities"
    )

    lines: List[str] = [hook, ""]
    for position, row in enumerate(rows, start=1):
        headline, url = line_for_item(position, row)
        lines.append(headline)
        lines.append(url)
        lines.append("")
    lines.append(CTA)
    lines.append("")
    lines.append(HASHTAGS)
    return "\n".join(lines).strip() + "\n"


def build_email_html(post_text: str, today: date) -> str:
    escaped = (
        post_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{EMAIL_SUBJECT}</title></head>
<body style="margin:0;padding:24px;background:#F1F5F9;font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;">
  <div style="max-width:680px;margin:0 auto;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;overflow:hidden;">
    <div style="padding:20px 24px;background:#0D1F17;color:#E8F0EC;">
      <div style="font-size:13px;letter-spacing:.14em;font-weight:800;">URBAN FOREST PARK</div>
      <div style="font-size:12px;opacity:.8;margin-top:4px;">Weekly LinkedIn Top 10 Roundup &middot; {today.isoformat()} (IST)</div>
    </div>
    <div style="padding:22px 24px;color:#0F172A;">
      <p style="margin:0 0 12px;font-size:14px;line-height:1.6;">
        Hello \u2014 this week&rsquo;s roundup is ready to publish. Click <strong>Copy</strong> below
        (or use the <em>&ldquo;Copy Weekly LinkedIn Roundup (Top 10)&rdquo;</em> button in the registry
        footer), then paste it straight into a LinkedIn post.
      </p>
      <pre style="white-space:pre-wrap;word-break:break-word;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;line-height:1.55;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:16px;margin:0;">{escaped}</pre>
      <p style="margin:14px 0 0;font-size:12.5px;line-height:1.6;color:#475569;">
        Direct publishing is attempted automatically when LINKEDIN_ACCESS_TOKEN and
        LINKEDIN_AUTHOR_URN are configured; otherwise post it manually from the text above.
        Global hub: <a href="{GLOBAL_HUB}">{GLOBAL_HUB}</a>
      </p>
    </div>
  </div>
</body>
</html>"""


def send_email(post_text: str, today: date, recipient_override: str = "") -> Optional[str]:
    host = os.environ.get("SMTP_HOST", "").strip()
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    port = int(os.environ.get("SMTP_PORT", "587").strip() or "587")
    if not (host and user and password):
        log.info("Email dispatch skipped: SMTP_HOST / SMTP_USER / SMTP_PASSWORD not configured.")
        return None

    recipient = (
        recipient_override.strip()
        or os.environ.get("WEEKLY_ROUNDUP_TO", "").strip()
        or user
    )
    from_name = os.environ.get("NEWSLETTER_FROM_NAME", "Urban Forest Park").strip() or "Urban Forest Park"
    from_email = os.environ.get("NEWSLETTER_FROM_EMAIL", "").strip() or user

    message = EmailMessage()
    message["Subject"] = EMAIL_SUBJECT
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = recipient
    message.set_content(
        "Your weekly LinkedIn Top 10 opportunities roundup is ready to publish.\n\n"
        + post_text
        + "\n\n-- Urban Forest Park | " + SITE + "/\n"
    )
    message.add_alternative(build_email_html(post_text, today), subtype="html")

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=45, context=ssl.create_default_context())
        else:
            server = smtplib.SMTP(host, port, timeout=45)
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        try:
            server.login(user, password)
            server.send_message(message)
        finally:
            try:
                server.quit()
            except Exception:  # noqa: BLE001 - best-effort close
                pass
    except Exception as exc:  # noqa: BLE001 - never fail CI on mail trouble
        log.warning("Email dispatch failed (non-fatal): %s", exc)
        return None

    log.info("Emailed the roundup to %s with subject %r", recipient, EMAIL_SUBJECT)
    return recipient


def publish_to_linkedin(post_text: str) -> bool:
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    author = os.environ.get("LINKEDIN_AUTHOR_URN", "").strip()
    if not token or not author:
        log.info(
            "LinkedIn direct publishing skipped: LINKEDIN_ACCESS_TOKEN / "
            "LINKEDIN_AUTHOR_URN not configured (manual posting path preserved)."
        )
        return False

    commentary = post_text.strip()
    if len(commentary) > 2900:
        commentary = commentary[:2897].rstrip() + "\u2026"

    payload = {
        "author": author,
        "commentary": commentary,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    request = urllib.request.Request(
        "https://api.linkedin.com/rest/posts",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "LinkedIn-Version": "202601",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            log.info("Published to LinkedIn (HTTP %s).", response.status)
            return True
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        log.warning("LinkedIn publish failed (non-fatal): HTTP %s %s", exc.code, detail)
    except Exception as exc:  # noqa: BLE001 - never fail CI on social trouble
        log.warning("LinkedIn publish failed (non-fatal): %s", exc)
    return False


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Weekly LinkedIn Top-10 roundup builder")
    parser.add_argument("--public", default="public", help="Registry data directory (default: public)")
    parser.add_argument("--date", default="", help="Override 'today' (YYYY-MM-DD, IST) for testing")
    parser.add_argument("--days", type=int, default=7, help="Recency window in days (default: 7)")
    parser.add_argument("--max-items", type=int, default=10, help="Maximum items in the post (default: 10)")
    parser.add_argument("--min-items", type=int, default=8, help="Minimum items expected (default: 8)")
    parser.add_argument("--to", default="", help="Override the email recipient (default: SMTP_USER)")
    parser.add_argument("--dry-run", action="store_true", help="Build the files only; skip email + publishing")
    parser.add_argument("--no-publish", action="store_true", help="Skip the LinkedIn REST publish step")
    args = parser.parse_args(argv)

    today = (
        datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else ist_today()
    )
    public = Path(args.public).resolve()

    india = load_json(public / "jobs.json") or []
    global_jobs = load_json(public / "global_jobs.json") or []
    india = [
        j for j in india
        if isinstance(j, dict) and clean(j.get("id"))
        and j.get("status") != "quarantined"
    ]
    global_jobs = [
        j for j in global_jobs
        if isinstance(j, dict) and clean(j.get("id"))
        and j.get("status") != "quarantined"
    ]

    india_pool, india_window = pool_for_window(india, today, args.days)
    global_pool, global_window = pool_for_window(global_jobs, today, args.days)
    log.info(
        "Roundup pools: %d India (%s), %d Global (%s)",
        len(india_pool),
        india_window,
        len(global_pool),
        global_window,
    )

    rows = select_roundup(
        india_pool,
        global_pool,
        today,
        min_items=args.min_items,
        max_items=args.max_items,
    )
    if not rows:
        log.warning("No opportunities available - writing an empty-but-valid roundup.")

    post_text = build_post_text(rows, today)

    txt_path = public / "linkedin_weekly_post.txt"
    txt_path.write_text(post_text, encoding="utf-8")
    log.info("Wrote %s (%d item(s))", txt_path.name, len(rows))

    meta = {
        "generated_at": datetime.now(IST).isoformat(timespec="seconds"),
        "week_of": today.isoformat(),
        "window_days": args.days,
        "india_window": india_window,
        "global_window": global_window,
        "subject": EMAIL_SUBJECT,
        "hook": post_text.split("\n", 1)[0] if post_text else "",
        "cta": CTA,
        "hashtags": HASHTAGS,
        "counts": {
            "total": len(rows),
            "india": sum(1 for row in rows if row["registry"] == "india"),
            "global": sum(1 for row in rows if row["registry"] == "global"),
        },
        "items": [
            {
                "position": position,
                "registry": row["registry"],
                "id": clean(row["job"].get("id")),
                "title": clean(row["job"].get("clean_title")),
                "organization": clean(row["job"].get("organization")),
                "location": location_of(row["job"]),
                "position_type": position_type_of(row["job"]),
                "opportunity_kind": kind_of(row["job"]),
                "score": round(row["score"], 2),
                "url": JOB_URL.format(id=clean(row["job"].get("id"))),
            }
            for position, row in enumerate(rows, start=1)
        ],
        "post_text": post_text,
    }
    json_path = public / "linkedin_weekly.json"
    json_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info("Wrote %s", json_path.name)

    if args.dry_run:
        log.info("Dry run: email + LinkedIn publishing skipped.")
        return 0

    send_email(post_text, today, args.to)
    if not args.no_publish:
        publish_to_linkedin(post_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
