#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Urban Forest Park - Mandate Dispatch (3-day email newsletter engine).

Reads public/jobs.json (+ public/archive.json for telemetry), filters the
mandates added in the last few days (default window: 4 days - a 72-hour
cadence plus slack), falls back to the most recent verified mandates when the
window is quiet, renders an executive HTML briefing into
``public/newsletter_latest.html`` (the deployable web edition), and then
delivers one personalised copy per subscriber when email credentials are
configured.

Delivery channels (first configured one wins):

    1. RESEND_API_KEY                     + NEWSLETTER_FROM_EMAIL
    2. BREVO_API_KEY                      + NEWSLETTER_FROM_EMAIL
    3. SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD
       (NEWSLETTER_FROM_EMAIL optional; defaults to SMTP_USER - works with
       a Gmail App Password, 100% free)

Subscriber sources (first one that yields addresses wins):

    1. NEWSLETTER_SUBSCRIBERS      env - JSON array, or comma/semicolon/
                                   newline separated list. Example:
                                   ["a@b.in", {"email": "c@d.in"}]
    2. NEWSLETTER_SUBSCRIBERS_CSV  env - URL of a published CSV (e.g. the
                                   Google Sheet filled by the Apps Script in
                                   google-apps-script/newsletter-subscribe.gs).
                                   A column titled "Email"/"email" is used.
    3. data/subscribers.json       repo file - [] or [{"email": ...}] or
                                   {"subscribers": [...]}.

By design the script NEVER fails CI when there is nothing to send or no
credentials are set: it writes the HTML edition, logs what was skipped, and
exits 0. Set NEWSLETTER_STRICT=1 (or pass --strict) to make a fully failed
delivery run (credentials present, zero delivered) a non-zero exit.

This script is read-only with respect to pipeline data - it never rewrites
jobs.json / archive.json.

Usage:
    py scripts/send_newsletter.py                 # generate + deliver if configured
    py scripts/send_newsletter.py --dry-run       # generate only
    py scripts/send_newsletter.py --to me@x.in    # test delivery to one address
    py scripts/send_newsletter.py --date 2026-10-19 --days 4
"""
from __future__ import annotations

import argparse
import csv
import html
import io
import json
import logging
import os
import re
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

SITE = "https://www.urbanforestpark.com"
DASHBOARD_URL = SITE + "/dashboard.html"
CALCULATOR_URL = SITE + "/green-calculator.html"
TELEGRAM_URL = "https://t.me/urbanforestpark"
WHATSAPP_URL = "https://chat.whatsapp.com/JJ0ItiNOfvEDCDIENscenw"
UNSUBSCRIBE_PAGE = SITE + "/unsubscribe.html"
CONTACT_EMAIL = "urbanforestpark@gmail.com"

# The audience is India-based and the workflow runs at 08:00 IST — dispatch
# dates are therefore computed in IST, not UTC.
IST = timezone(timedelta(hours=5, minutes=30))

DEFAULT_JOBS = REPO_ROOT / "public" / "jobs.json"
DEFAULT_ARCHIVE = REPO_ROOT / "public" / "archive.json"
DEFAULT_OUT = REPO_ROOT / "public" / "newsletter_latest.html"
SUBSCRIBERS_FILE = REPO_ROOT / "data" / "subscribers.json"

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

ACADEMIC_TYPES = {
    "JRF / SRF",
    "PhD / Doctoral Fellowship",
    "Project Associate / Research Associate",
    "Faculty / Academic",
    "Fellowship / Internship",
}
CORPORATE_CATEGORY = "ESG, Carbon Markets & Corporate Sustainability"

BRAND_DARK = "#0D1F17"
BRAND_ACCENT = "#065F46"
BRAND_EMERALD = "#10B981"
INK = "#0F172A"
INK_2 = "#334155"
INK_3 = "#64748B"
BORDER = "#E2E8F0"
BG = "#F8FAFC"
CARD = "#FFFFFF"

# ---------------------------------------------------------------------------
# Welcome email (sent once per new subscriber, on every cadence)
# ---------------------------------------------------------------------------
WELCOME_SUBJECT = (
    "Welcome to Urban Forest Park \u2014 India & Global Climate, Forestry, "
    "ESG & Research Career Dispatch"
)
WELCOME_PREVIEW = REPO_ROOT / "welcome_email_preview.html"
APP_INSTALL_URL = SITE + "/?source=welcome_email"
WELCOME_WHATSAPP_COLOR = "#128C7E"
WELCOME_TELEGRAM_COLOR = "#229ED9"

FREQUENCY_LABELS = {
    "3-day": "Every 3 Days",
    "3days": "Every 3 Days",
    "3_days": "Every 3 Days",
    "weekly": "Weekly Digest",
}

SECTOR_LABELS = {
    "all": "All mandates \u2014 academic, forestry, GIS, ESG, climate policy & water",
    "academic": "JRF / PhD / Academic and research mandates",
    "forestry-gis": "Forestry, Wildlife, GIS & Remote Sensing mandates",
    "corporate-esg": "Corporate ESG, carbon markets & sustainability mandates",
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def squash(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def clip(value: Any, limit: int) -> str:
    text = squash(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,;:.") + "\u2026"


def parse_iso_date(value: Any) -> Optional[date]:
    text = squash(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def load_jobs(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):  # tolerate {"jobs": [...]} wrappers
        data = data.get("jobs", [])
    # Quarantined records are never emailed. Broadcasts carry dossier URLs only.
    return [
        row
        for row in data
        if isinstance(row, dict) and row.get("status") != "quarantined"
    ]


def job_dossier_url(job_id: str) -> str:
    return f"{SITE}/?job={urllib.parse.quote(str(job_id))}"


def unsubscribe_url_for(email: str) -> str:
    return UNSUBSCRIBE_PAGE + "?email=" + urllib.parse.quote(email)


# --------------------------------------------------------------------------
# Recipients
# --------------------------------------------------------------------------
def _coerce_recipients(raw: Any) -> List[Dict[str, str]]:
    """Normalise any accepted container into [{"email": ...}] records."""
    out: List[Dict[str, str]] = []
    if raw is None:
        return out
    if isinstance(raw, str):
        # A single string: JSON array/object, or a separated list.
        text = raw.strip()
        if not text:
            return out
        if text[0] in "[{":
            try:
                return _coerce_recipients(json.loads(text))
            except json.JSONDecodeError:
                pass
        for chunk in re.split(r"[,;\n]+", text):
            email = chunk.strip().strip('"').lower()
            if email:
                out.append({"email": email})
        return out
    if isinstance(raw, dict):
        if "subscribers" in raw:
            return _coerce_recipients(raw["subscribers"])
        if "email" in raw:
            out.append({"email": str(raw["email"]).strip().lower()})
        return out
    if isinstance(raw, (list, tuple)):
        for item in raw:
            out.extend(_coerce_recipients(item))
    return out


def _dedupe_valid(records: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    result: List[Dict[str, str]] = []
    for record in records:
        email = record.get("email", "").strip().lower()
        if not email or not EMAIL_RE.match(email) or email in seen:
            continue
        seen.add(email)
        result.append({"email": email})
    return result


def fetch_csv_recipients(url: str) -> List[Dict[str, str]]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "ufp-newsletter/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001 - report and continue
        logging.warning("Could not fetch NEWSLETTER_SUBSCRIBERS_CSV (%s)", exc)
        return []

    rows = list(csv.reader(io.StringIO(body)))
    if not rows:
        return []

    email_column = 0
    header = [cell.strip().lower() for cell in rows[0]]
    start = 0
    for index, cell in enumerate(header):
        if cell in ("email", "email address", "e-mail", "address"):
            email_column = index
            start = 1
            break
    else:
        # No recognised header: sniff the column that looks like email data.
        first_data = rows[1] if len(rows) > 1 else rows[0]
        for index, cell in enumerate(first_data):
            if "@" in cell:
                email_column = index
                start = 1
                break

    out: List[Dict[str, str]] = []
    for row in rows[start:]:
        if len(row) > email_column and "@" in row[email_column]:
            out.append({"email": row[email_column].strip().lower()})
    return out


def _looks_like_test_email(email: str) -> bool:
    """True for obvious QA / placeholder addresses that should not be mailed."""
    return bool(
        re.search(
            r"(^qa[._-]|^test[-._@]|smoke|@example\.|@test\.|\.invalid$|@localhost)",
            email,
            flags=re.IGNORECASE,
        )
    )


def load_recipients(override: Optional[str] = None) -> Tuple[List[Dict[str, str]], str]:
    """Return (recipients, human-readable source label).

    Owner fallback: when no subscriber list is configured yet - or every
    configured address is a QA/placeholder entry - the site owner's own
    mailbox (NEWSLETTER_OWNER_EMAIL, else SMTP_USER, else
    NEWSLETTER_FROM_EMAIL) is substituted as the primary dispatch recipient,
    so the 3-day digest lands in the owner's inbox for verification and
    forwarding until real subscribers are collected.
    """
    if override:
        return _dedupe_valid(_coerce_recipients(override)), "--to override"

    recipients: List[Dict[str, str]] = []
    source = "none configured"

    env_json = os.environ.get("NEWSLETTER_SUBSCRIBERS", "").strip()
    if env_json:
        recipients = _dedupe_valid(_coerce_recipients(env_json))
        if recipients:
            source = "NEWSLETTER_SUBSCRIBERS"

    if not recipients:
        csv_url = os.environ.get("NEWSLETTER_SUBSCRIBERS_CSV", "").strip()
        if csv_url:
            recipients = _dedupe_valid(fetch_csv_recipients(csv_url))
            if recipients:
                source = "NEWSLETTER_SUBSCRIBERS_CSV"

    if not recipients and SUBSCRIBERS_FILE.exists():
        try:
            raw = json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logging.warning("Could not read %s (%s)", SUBSCRIBERS_FILE, exc)
            raw = []
        recipients = _dedupe_valid(_coerce_recipients(raw))
        if recipients:
            source = str(SUBSCRIBERS_FILE.relative_to(REPO_ROOT))

    usable = [record for record in recipients if not _looks_like_test_email(record["email"])]
    dropped = len(recipients) - len(usable)
    if dropped:
        logging.info("Excluded %d test/placeholder address(es) from delivery.", dropped)

    if not usable:
        owner = (
            os.environ.get("NEWSLETTER_OWNER_EMAIL", "").strip()
            or os.environ.get("SMTP_USER", "").strip()
            or os.environ.get("NEWSLETTER_FROM_EMAIL", "").strip()
        ).lower()
        if owner and EMAIL_RE.match(owner):
            note = (
                "owner copy via SMTP_USER (no subscriber list yet)"
                if source == "none configured"
                else f"owner copy via SMTP_USER ({source} held only test entries)"
            )
            logging.info(
                "No mailable subscribers - routing this dispatch to the owner mailbox (%s).", owner
            )
            return [{"email": owner}], note
        return [], source

    return usable, source


# --------------------------------------------------------------------------
# Selection + telemetry
# --------------------------------------------------------------------------
def select_cards(
    jobs: List[Dict[str, Any]], today: date, window_days: int, min_new: int, max_cards: int
) -> Tuple[List[Dict[str, Any]], bool, int]:
    """Return (cards, used_fallback, new_count_within_window)."""
    cutoff = today - timedelta(days=max(window_days - 1, 0))

    def dated(job: Dict[str, Any]) -> Optional[date]:
        return parse_iso_date(job.get("date_added"))

    fresh = [
        job for job in jobs
        if (dated(job) is not None and dated(job) >= cutoff)  # type: ignore[operator]
    ]
    fresh.sort(key=lambda job: (dated(job) or date.min, squash(job.get("clean_title"))), reverse=True)

    if len(fresh) >= min_new:
        return fresh[:max_cards], False, len(fresh)

    recent = sorted(
        jobs,
        key=lambda job: (dated(job) or date.min, squash(job.get("clean_title"))),
        reverse=True,
    )
    return recent[:max_cards], True, len(fresh)


def telemetry(jobs: List[Dict[str, Any]], today: date) -> Dict[str, int]:
    week_cutoff = today - timedelta(days=6)
    total = len(jobs)
    new_week = 0
    academic = 0
    corporate = 0
    for job in jobs:
        added = parse_iso_date(job.get("date_added"))
        if added is not None and added >= week_cutoff:
            new_week += 1
        position_type = squash(job.get("position_type"))
        category = squash(job.get("category"))
        if position_type in ACADEMIC_TYPES or category.startswith("Academic") or category.startswith("Research Associate"):
            academic += 1
        if category == CORPORATE_CATEGORY:
            corporate += 1
    return {"total": total, "new_week": new_week, "academic": academic, "corporate": corporate}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def _badge(text: str, tone: str = "accent") -> str:
    if tone == "accent":
        border, color, background = "#A7F3D0", BRAND_ACCENT, "#ECFDF5"
    else:
        border, color, background = BORDER, INK_3, BG
    return (
        f'<span style="display:inline-block;padding:3px 9px;border:1px solid {border};'
        f'border-radius:999px;background:{background};color:{color};font-size:11px;'
        f'font-weight:700;letter-spacing:.02em;">{esc(text)}</span>'
    )


def _stat_cell(label: str, value: str, width: str = "25%") -> str:
    return (
        f'<td width="{width}" style="padding:14px 12px;border:1px solid {BORDER};'
        f'border-radius:10px;background:{CARD};text-align:center;">'
        f'<div style="font-size:22px;font-weight:800;color:{INK};line-height:1.1;">{esc(value)}</div>'
        f'<div style="margin-top:4px;font-size:10.5px;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;color:{INK_3};">{esc(label)}</div>'
        "</td>"
    )


def _job_card(job: Dict[str, Any]) -> str:
    job_id = squash(job.get("id"))
    title = squash(job.get("clean_title")) or "Verified mandate"
    organization = squash(job.get("organization")) or "Institution not disclosed"
    state = squash(job.get("state")) or "India"
    city = squash(job.get("city"))
    location = state if (not city or city.lower() in state.lower()) else f"{state} \u00b7 {city}"
    position_type = squash(job.get("position_type"))
    qualification = clip(job.get("qualification_summary"), 170) or "See the official notification."
    compensation = squash(job.get("compensation_or_fellowship")) or "Not disclosed \u2014 see official portal"
    added = squash(job.get("date_added"))
    valid_through = squash(job.get("valid_through"))
    dossier = job_dossier_url(job_id) if job_id else SITE + "/"

    meta_bits = [esc(location)]
    if valid_through:
        meta_bits.append("Apply by " + esc(valid_through))

    return f"""<tr><td style="padding:0 0 14px 0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border:1px solid {BORDER};border-left:3px solid {BRAND_ACCENT};border-radius:10px;background:{CARD};">
  <tr><td style="padding:16px 18px 14px 18px;">
    <div style="font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{BRAND_ACCENT};">Verified mandate{f' &middot; added {esc(added)}' if added else ''}</div>
    <div style="margin-top:6px;font-size:16.5px;font-weight:700;line-height:1.35;color:{INK};">{esc(title)}</div>
    <div style="margin-top:4px;font-size:13px;line-height:1.5;color:{INK_2};"><strong>{esc(organization)}</strong> &middot; {' &middot; '.join(meta_bits)}</div>
    <div style="margin-top:10px;">{_badge(position_type or 'Verified position', 'accent')}&nbsp;{_badge(compensation, 'muted')}</div>
    <div style="margin-top:10px;font-size:12.5px;line-height:1.6;color:{INK_3};"><strong style="color:{INK_2};">Qualification:</strong> {esc(qualification)}</div>
    <div style="margin-top:14px;">
      <a href="{esc(dossier)}" style="display:inline-block;padding:10px 16px;background:{BRAND_ACCENT};color:#FFFFFF;border-radius:8px;font-size:12.5px;font-weight:700;text-decoration:none;">View Position Dossier &nearr;</a>
    </div>
  </td></tr>
</table>
</td></tr>"""


def dispatch_heading(new_count: int, cards_count: int, used_fallback: bool) -> str:
    """Human heading for the masthead and subject line (cards may be a subset)."""
    if used_fallback:
        return "Registry briefing"
    if new_count > cards_count:
        return f"{cards_count} of {new_count} new verified mandates"
    return f"{new_count} new verified mandate{'s' if new_count != 1 else ''}"


def render_email(
    cards: List[Dict[str, Any]],
    stats: Dict[str, int],
    used_fallback: bool,
    new_count: int,
    generated_on: date,
    unsubscribe_url: str,
) -> Tuple[str, str]:
    """Return (html, plain_text)."""
    date_line = generated_on.strftime("%d %B %Y")
    heading_count = dispatch_heading(new_count, len(cards), used_fallback)

    if used_fallback:
        intro = (
            "No new verified mandates were recorded in this brief window. As a service to "
            "subscribers, the most recent verified positions on the registry are summarised below."
        )
    else:
        intro = (
            "The following verified mandates were added to the national registry in this "
            "dispatch cycle, sourced from official institutional notifications and application "
            "portals across India."
        )

    cards_html = "\n".join(_job_card(job) for job in cards) if cards else (
        f'<tr><td style="padding:18px;border:1px solid {BORDER};border-radius:10px;'
        f'background:{CARD};font-size:13px;color:{INK_3};">The registry is between cycles — '
        "the next verified mandates will appear here.</td></tr>"
    )

    preheader = clip(intro, 120)

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Urban Forest Park — Mandate Dispatch</title>
</head>
<body style="margin:0;padding:0;background:{BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{esc(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};">
<tr><td align="center" style="padding:26px 12px;">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;max-width:100%;">

  <!-- Masthead -->
  <tr><td style="padding:24px 26px;background:{BRAND_DARK};border-radius:12px 12px 0 0;">
    <div style="font-size:16px;font-weight:800;letter-spacing:.16em;color:#FFFFFF;">URBAN FOREST PARK</div>
    <div style="margin-top:6px;font-size:12.5px;line-height:1.5;color:#9FB6AB;">India Climate, Forestry, Academic &amp; ESG Career Dispatch</div>
    <div style="margin-top:12px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#10B981;">Mandate Dispatch &middot; {esc(date_line)} &middot; {esc(heading_count)}</div>
  </td></tr>

  <!-- Body -->
  <tr><td style="padding:22px 26px 8px 26px;background:{BG};border:1px solid {BORDER};border-top:0;">
    <p style="margin:0 0 16px 0;font-size:13.5px;line-height:1.65;color:{INK_2};">{esc(intro)}</p>

    <!-- Telemetry -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:separate;border-spacing:8px 0;margin:0 -8px 18px -8px;">
      <tr>
        {_stat_cell('Total Active Mandates', str(stats['total']))}
        {_stat_cell('New This Week', str(stats['new_week']))}
        {_stat_cell('Academic / JRF', str(stats['academic']))}
        {_stat_cell('Corporate ESG', str(stats['corporate']))}
      </tr>
    </table>

    <!-- Cards -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
{cards_html}
    </table>

    <p style="margin:8px 0 18px 0;font-size:12.5px;line-height:1.65;color:{INK_3};">
      Every dossier links to the official application portal of the publishing institution.
      Always verify deadlines, stipends and eligibility in the authoritative notification before applying.
      Urban Forest Park is an informational registry — it charges no fees and does not process applications.
    </p>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:20px 26px;background:{BRAND_DARK};border-radius:0 0 12px 12px;">
    <div style="font-size:12px;line-height:1.7;color:#9FB6AB;">
      <a href="{esc(SITE)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Career Registry</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(DASHBOARD_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Nagar Van dMRV Dashboard</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(CALCULATOR_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Green Calculator</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(TELEGRAM_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Telegram</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(WHATSAPP_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">WhatsApp</a>
    </div>
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(232,240,236,.14);font-size:11px;line-height:1.7;color:#7E9A8C;">
      You are receiving this dispatch because you subscribed at urbanforestpark.com.
      <a href="{esc(unsubscribe_url)}" style="color:#10B981;font-weight:700;text-decoration:none;">Unsubscribe</a> or manage your
      <a href="{esc(UNSUBSCRIBE_PAGE)}" style="color:#10B981;text-decoration:none;">dispatch preferences</a>.
      Opt-out requests are honoured within 7 working days.
    </div>
    <div style="margin-top:12px;font-size:11px;line-height:1.7;color:#5F7A6C;">
      Urban Forest Park &middot; National Climate, Forestry, ESG &amp; Geospatial Career Registry (India)
      &middot; Grievance Officer: {esc(CONTACT_EMAIL)}
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

    text_lines = [
        "URBAN FOREST PARK",
        "India Climate, Forestry, Academic & ESG Career Dispatch",
        f"Mandate Dispatch - {date_line} - {heading_count}",
        "",
        intro,
        "",
        f"Total active mandates: {stats['total']} | New this week: {stats['new_week']} | "
        f"Academic/JRF: {stats['academic']} | Corporate ESG: {stats['corporate']}",
        "",
    ]
    for job in cards:
        text_lines.extend(
            [
                f"- {squash(job.get('clean_title'))} | {squash(job.get('organization'))} | {squash(job.get('state'))}",
                f"  {squash(job.get('position_type'))} | {squash(job.get('compensation_or_fellowship'))}",
                f"  Dossier: {job_dossier_url(squash(job.get('id')))}",
                "",
            ]
        )
    text_lines.extend(
        [
            "Career Registry: " + SITE,
            "dMRV Dashboard: " + DASHBOARD_URL,
            "Green Calculator: " + CALCULATOR_URL,
            "",
            "Unsubscribe: " + unsubscribe_url,
            "Urban Forest Park - Grievance Officer: " + CONTACT_EMAIL,
        ]
    )
    return html_doc, "\n".join(text_lines)


# --------------------------------------------------------------------------
# Welcome email - one formal onboarding message per new subscriber
# --------------------------------------------------------------------------
def frequency_label(frequency: Any) -> str:
    return FREQUENCY_LABELS.get(squash(frequency).lower(), "Every 3 Days")


def sector_label(sector: Any) -> str:
    return SECTOR_LABELS.get(squash(sector).lower(), SECTOR_LABELS["all"])


def featured_jobs(jobs: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    """The three most recently verified active mandates, newest first."""
    ranked = sorted(
        jobs,
        key=lambda job: (parse_iso_date(job.get("date_added")) or date.min, squash(job.get("clean_title"))),
        reverse=True,
    )
    return ranked[:limit]


def _email_button(url: str, label: str, color: str, outline: bool = False) -> str:
    if outline:
        style = (
            f"display:inline-block;margin:0 8px 8px 0;padding:10px 16px;background:{CARD};"
            f"color:{BRAND_ACCENT};border:1px solid {BRAND_ACCENT};border-radius:8px;"
            "font-size:12.5px;font-weight:700;text-decoration:none;"
        )
    else:
        style = (
            f"display:inline-block;margin:0 8px 8px 0;padding:10px 16px;background:{color};"
            "color:#FFFFFF;border-radius:8px;font-size:12.5px;font-weight:700;text-decoration:none;"
        )
    return f'<a href="{esc(url)}" style="{style}">{esc(label)}</a>'


def _welcome_section(title: str, rows_html: str) -> str:
    return (
        f'<tr><td style="padding:18px 0 0 0;">'
        f'<div style="font-size:14px;font-weight:800;letter-spacing:.01em;color:{INK};'
        f'padding-bottom:10px;border-bottom:1px solid {BORDER};">{esc(title)}</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">'
        f"{rows_html}</table></td></tr>"
    )


def _welcome_li(title: str, body: str) -> str:
    return (
        f'<tr><td style="padding:0 0 10px 0;font-size:13px;line-height:1.65;color:{INK_2};">'
        f'<strong style="color:{INK};">{esc(title)}</strong> \u2014 {body}</td></tr>'
    )


def build_welcome_email_html(
    subscriber_email: str,
    frequency: Any = "3-day",
    sector: Any = "all",
    jobs: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, str]:
    """Formal welcome email for a new subscriber. Returns (html, plain_text)."""
    cadence = frequency_label(frequency)
    sector_text = sector_label(sector)
    address = squash(subscriber_email)
    if jobs is None:
        try:
            jobs = load_jobs(DEFAULT_JOBS) if DEFAULT_JOBS.exists() else []
        except (OSError, json.JSONDecodeError):
            jobs = []

    picks = featured_jobs(jobs, 3)
    cards_html = "\n".join(_job_card(job) for job in picks) if picks else (
        f'<tr><td style="padding:16px 18px;border:1px solid {BORDER};border-radius:10px;'
        f'background:{CARD};font-size:13px;color:{INK_3};">The live registry is between harvest '
        f'cycles \u2014 open <a href="{esc(SITE)}" style="color:{BRAND_ACCENT};font-weight:700;'
        'text-decoration:none;">urbanforestpark.com</a> for the current verified mandates.</td></tr>'
    )

    tracked = (
        _welcome_li(
            "Academic & research mandates",
            "JRF, SRF, Project Associate I/II, Research Associate, PhD fellowships and Young "
            "Professional roles published by WII, ICFRE, IIFM, IIRS, ICAR, IITs and IISc.",
        )
        + _welcome_li(
            "Corporate ESG, carbon & sustainability roles",
            "ESG analysts, BRSR reporting, carbon market and dMRV specialists, and CSR managers "
            "at India's leading corporates and consultancies.",
        )
        + _welcome_li(
            "Forestry, GIS & climate policy",
            "Think-tank positions (CEEW, WRI India, TERI, ATREE, UNDP), GIS / remote sensing "
            "roles, plus fellowships, grants, scholarships, internships and competitions.",
        )
        + _welcome_li(
            "Separate India & Global portals",
            "Every dossier carries the official application link. Use the "
            "<strong>\U0001F1EE\U0001F1F3 India Registry</strong> and "
            "<strong>\U0001F30D Global Opportunities</strong> switcher on the homepage to change "
            "jurisdiction in one click.",
        )
    )

    guide = (
        _welcome_li(
            "Right-side instant search",
            "Search every active mandate and past archived position \u2014 archived records are "
            "ideal for benchmarking stipends, required skills and eligibility.",
        )
        + _welcome_li(
            "One-click filters",
            "Narrow by Indian state, global region, career track, opportunity type or experience "
            "tier to reach an exact shortlist instantly.",
        )
        + _welcome_li(
            "Nagar Van dMRV Dashboard & Green Calculator",
            "Run urban-forestry and heat-island impact analysis, and estimate carbon and "
            "plantation benefits for your own project.",
        )
    )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome to Urban Forest Park</title>
</head>
<body style="margin:0;padding:0;background:{BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">Welcome aboard - your {esc(cadence)} dispatch of verified India &amp; Global climate, forestry, ESG and research mandates starts now.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};">
<tr><td align="center" style="padding:26px 12px;">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;max-width:100%;">

  <!-- Masthead -->
  <tr><td style="padding:24px 26px;background:{BRAND_DARK};border-radius:12px 12px 0 0;">
    <div style="font-size:16px;font-weight:800;letter-spacing:.16em;color:#FFFFFF;">URBAN FOREST PARK</div>
    <div style="margin-top:6px;font-size:12.5px;line-height:1.5;color:#9FB6AB;">India Climate, Forestry, Academic &amp; ESG Career Registry</div>
    <div style="margin-top:12px;font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#10B981;">Welcome aboard &middot; {esc(cadence)}</div>
  </td></tr>

  <!-- Greeting -->
  <tr><td style="padding:22px 26px 8px 26px;background:{BG};border:1px solid {BORDER};border-top:0;">
    <p style="margin:0 0 12px 0;font-size:15px;line-height:1.65;color:{INK};"><strong>Welcome to Urban Forest Park \u2014 <a href="{esc(SITE)}" style="color:{BRAND_ACCENT};font-weight:700;text-decoration:none;">urbanforestpark.com</a></strong></p>
    <p style="margin:0 0 12px 0;font-size:13.5px;line-height:1.7;color:{INK_2};">
      This mailbox{(' (' + esc(address) + ')') if address else ''} is now registered on the official
      registry dispatch. Your confirmed preference: <strong>{esc(cadence)}</strong> &middot;
      <strong>{esc(sector_text)}</strong>. Every briefing is compiled from official institutional
      notifications and application portals \u2014 verified before it is sent, with direct links to
      the authoritative source.
    </p>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:4px 0 2px 0;">
      <tr>
        <td width="50%" style="padding:0 6px 0 0;">
          <div style="padding:12px 14px;border:1px solid {BORDER};border-radius:10px;background:{CARD};">
            <div style="font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK_3};">Dispatch cadence</div>
            <div style="margin-top:4px;font-size:15px;font-weight:800;color:{INK};">{esc(cadence)}</div>
          </div>
        </td>
        <td width="50%" style="padding:0 0 0 6px;">
          <div style="padding:12px 14px;border:1px solid {BORDER};border-radius:10px;background:{CARD};">
            <div style="font-size:10.5px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:{INK_3};">Sector preference</div>
            <div style="margin-top:4px;font-size:13.5px;font-weight:700;line-height:1.4;color:{INK};">{esc(sector_text)}</div>
          </div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- What we track & verify -->
  <tr><td style="padding:0 26px;background:{BG};border-left:1px solid {BORDER};border-right:1px solid {BORDER};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      {_welcome_section('What We Track & Verify for You', tracked)}
    </table>
  </td></tr>

  <!-- Quick guide -->
  <tr><td style="padding:0 26px 14px 26px;background:{BG};border-left:1px solid {BORDER};border-right:1px solid {BORDER};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      {_welcome_section('How to Use Urban Forest Park Effectively', guide)}
    </table>
  </td></tr>

  <!-- Featured opportunities -->
  <tr><td style="padding:0 26px 8px 26px;background:{BG};border-left:1px solid {BORDER};border-right:1px solid {BORDER};">
    <div style="font-size:14px;font-weight:800;color:{INK};padding-bottom:10px;border-bottom:1px solid {BORDER};">Top 3 Featured Active Opportunities Right Now</div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px;">
{cards_html}
    </table>
  </td></tr>

  <!-- Channels -->
  <tr><td style="padding:0 26px 22px 26px;background:{BG};border-left:1px solid {BORDER};border-right:1px solid {BORDER};">
    <div style="padding:16px 18px;border:1px solid {BORDER};border-radius:10px;background:{CARD};">
      <div style="font-size:13.5px;font-weight:800;color:{INK};">Instant alerts &amp; the Urban Forest Park web app</div>
      <p style="margin:8px 0 12px 0;font-size:12.5px;line-height:1.65;color:{INK_2};">
        Job alerts are broadcast every morning at 7 AM IST across the community network. Join the
        channels below, or install the official web app for one-tap access and offline dossiers.
      </p>
      <div>
        {_email_button(WHATSAPP_URL, 'Join the WhatsApp Job Group', WELCOME_WHATSAPP_COLOR)}
        {_email_button(TELEGRAM_URL, 'Join the Telegram Channel', WELCOME_TELEGRAM_COLOR)}
        {_email_button(APP_INSTALL_URL, 'Install the Urban Forest Park Web App', BRAND_ACCENT)}
      </div>
    </div>
    <p style="margin:14px 0 0 0;font-size:12px;line-height:1.65;color:{INK_3};">
      Urban Forest Park is an informational registry \u2014 it charges no fees, processes no
      applications, and every dossier links straight to the official application portal.
    </p>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:20px 26px;background:{BRAND_DARK};border-radius:0 0 12px 12px;">
    <div style="font-size:12px;line-height:1.7;color:#9FB6AB;">
      <a href="{esc(SITE)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Career Registry</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(DASHBOARD_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Nagar Van dMRV Dashboard</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(CALCULATOR_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Green Calculator</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(TELEGRAM_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">Telegram</a>
      &nbsp;&middot;&nbsp;
      <a href="{esc(WHATSAPP_URL)}" style="color:#E8F0EC;font-weight:600;text-decoration:none;">WhatsApp</a>
    </div>
    <div style="margin-top:14px;padding-top:14px;border-top:1px solid rgba(232,240,236,.14);font-size:11px;line-height:1.7;color:#7E9A8C;">
      You are receiving this welcome message because this mailbox subscribed at urbanforestpark.com.
      <a href="{esc(unsubscribe_url_for(address))}" style="color:#10B981;font-weight:700;text-decoration:none;">Unsubscribe</a> or manage your
      <a href="{esc(UNSUBSCRIBE_PAGE)}" style="color:#10B981;text-decoration:none;">dispatch preferences</a>.
      Opt-out requests are honoured within 7 working days.
    </div>
    <div style="margin-top:12px;font-size:11px;line-height:1.7;color:#5F7A6C;">
      Urban Forest Park &middot; National Climate, Forestry, ESG &amp; Geospatial Career Registry (India)
      &middot; Grievance Officer: {esc(CONTACT_EMAIL)}
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""

    text_lines = [
        "URBAN FOREST PARK",
        "Welcome - India & Global Climate, Forestry, ESG & Research Career Dispatch",
        "",
        f"Hello{(' (' + address + ')') if address else ''},",
        "",
        f"Your confirmed dispatch preference: {cadence} | {sector_text}.",
        "Every briefing is compiled from official institutional notifications and application portals.",
        "",
        "WHAT WE TRACK & VERIFY FOR YOU",
        "- Academic & research mandates: JRF, SRF, Project Associate I/II, Research Associate, PhD fellowships and Young Professional roles (WII, ICFRE, IIFM, IIRS, ICAR, IITs, IISc).",
        "- Corporate ESG, carbon & sustainability roles: ESG analysts, BRSR reporting, carbon market / dMRV specialists, CSR managers.",
        "- Forestry, GIS & climate policy: think-tank positions (CEEW, WRI India, TERI, ATREE, UNDP), GIS / remote sensing roles, fellowships, grants, scholarships, internships and competitions.",
        "- Separate India & Global portals: switch between the India Registry and Global Opportunities on the homepage.",
        "",
        "HOW TO USE URBAN FOREST PARK EFFECTIVELY",
        "- Right-side instant search: query every active mandate and past archived position (ideal for benchmarking stipends and skills).",
        "- One-click filters: Indian state, global region, career track, opportunity type, experience tier.",
        "- Nagar Van dMRV Dashboard & Green Calculator: urban forestry and heat-island impact analysis.",
        "",
        "TOP 3 FEATURED ACTIVE OPPORTUNITIES RIGHT NOW",
    ]
    for job in picks:
        text_lines.extend(
            [
                f"- {squash(job.get('clean_title'))} | {squash(job.get('organization'))} | {squash(job.get('state'))}",
                f"  {squash(job.get('position_type'))} | {squash(job.get('compensation_or_fellowship'))}",
                f"  View Position Dossier: {job_dossier_url(squash(job.get('id')))}",
                "",
            ]
        )
    text_lines.extend(
        [
            "INSTANT ALERTS & WEB APP",
            "WhatsApp Job Group: " + WHATSAPP_URL,
            "Telegram Channel: " + TELEGRAM_URL,
            "Install the Urban Forest Park web app: " + APP_INSTALL_URL,
            "",
            "Urban Forest Park is an informational registry - no fees, no application processing.",
            "Unsubscribe: " + unsubscribe_url_for(address),
            "Urban Forest Park - Grievance Officer: " + CONTACT_EMAIL,
        ]
    )
    return html_doc, "\n".join(text_lines)


def deliver_welcome(
    channel: str,
    config: Dict[str, str],
    recipient: str,
    frequency: Any,
    sector: Any,
    jobs: Optional[List[Dict[str, Any]]] = None,
) -> None:
    html_body, text_body = build_welcome_email_html(recipient, frequency, sector, jobs)
    list_unsub = f"<mailto:{CONTACT_EMAIL}?subject=unsubscribe>, <{unsubscribe_url_for(recipient)}>"
    DELIVERERS[channel](config, recipient, WELCOME_SUBJECT, html_body, text_body, list_unsub)


def _raw_subscriber_records(raw: Any) -> List[Dict[str, Any]]:
    """Normalise the subscribers file (list | wrapper | bare addresses)."""
    if isinstance(raw, dict):
        raw = raw.get("subscribers", [])
    if not isinstance(raw, list):
        return []
    records: List[Dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            records.append(dict(item))
        elif isinstance(item, str) and item.strip():
            records.append({"email": item.strip()})
    return records


def load_subscriber_records() -> List[Dict[str, Any]]:
    if not SUBSCRIBERS_FILE.exists():
        return []
    try:
        raw = json.loads(SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logging.warning("Could not read %s (%s)", SUBSCRIBERS_FILE, exc)
        return []
    return _raw_subscriber_records(raw)


def save_subscriber_records(records: List[Dict[str, Any]]) -> None:
    SUBSCRIBERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = SUBSCRIBERS_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp_path.replace(SUBSCRIBERS_FILE)


def process_welcome_backlog(
    channel: str,
    config: Dict[str, str],
    jobs: Optional[List[Dict[str, Any]]] = None,
    pace: float = 0.4,
) -> int:
    """Send the welcome email to every recorded subscriber that lacks one.

    This is the safety net behind the instant `/api/subscribe` trigger: any
    subscriber saved without ``welcome_sent: true`` receives the onboarding
    email on the next dispatch run, and the marker is written back so each
    address is welcomed exactly once. Never raises: the dispatch run must
    stay green even if a single welcome delivery fails.
    """
    records = load_subscriber_records()
    pending = [
        record for record in records
        if EMAIL_RE.match(squash(record.get("email")))
        and record.get("welcome_sent") is not True
        and not _looks_like_test_email(squash(record.get("email")))
    ]
    if not records:
        logging.info("Welcome backlog: no subscribers recorded yet - nothing to send.")
        return 0
    if not pending:
        logging.info("Welcome backlog: all %d recorded subscriber(s) already welcomed.", len(records))
        return 0

    logging.info("Welcome backlog: %d subscriber(s) pending a welcome email.", len(pending))
    sent = 0
    for record in pending:
        address = squash(record.get("email")).lower()
        try:
            deliver_welcome(channel, config, address, record.get("frequency"), record.get("sector"), jobs)
            record["email"] = address
            record["welcome_sent"] = True
            record["welcome_sent_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            sent += 1
            logging.info("Welcome email delivered -> %s", address)
        except Exception as exc:  # noqa: BLE001 - continue the batch
            logging.warning("Welcome email FAILED -> %s (%s)", address, clip(exc, 160))
        if pace > 0:
            time.sleep(pace)

    if sent:
        try:
            save_subscriber_records(records)
            logging.info("Welcome backlog: %d welcome email(s) sent; subscriber file updated.", sent)
        except OSError as exc:
            logging.warning("Welcome backlog: could not update %s (%s)", SUBSCRIBERS_FILE, clip(exc, 160))
    return sent


# --------------------------------------------------------------------------
# Delivery
# --------------------------------------------------------------------------
def http_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 45) -> Tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json", **headers}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:  # noqa: F821 - imported below
        return exc.code, exc.read().decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        return 0, str(exc)


def detect_channel() -> Tuple[Optional[str], Dict[str, str]]:
    from_name = os.environ.get("NEWSLETTER_FROM_NAME", "Urban Forest Park Registry").strip() \
        or "Urban Forest Park Registry"
    from_email = os.environ.get("NEWSLETTER_FROM_EMAIL", "").strip()

    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    if resend_key and from_email:
        return "resend", {"key": resend_key, "from_name": from_name, "from_email": from_email}

    brevo_key = os.environ.get("BREVO_API_KEY", "").strip()
    if brevo_key and from_email:
        return "brevo", {"key": brevo_key, "from_name": from_name, "from_email": from_email}

    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_user = os.environ.get("SMTP_USER", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    if smtp_host and smtp_user and smtp_password:
        return "smtp", {
            "host": smtp_host,
            "port": os.environ.get("SMTP_PORT", "587").strip() or "587",
            "user": smtp_user,
            "password": smtp_password,
            "from_name": from_name,
            "from_email": from_email or smtp_user,
        }
    return None, {}


def deliver_smtp(config: Dict[str, str], recipient: str, subject: str, html_body: str, text_body: str, list_unsub: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{config['from_name']} <{config['from_email']}>"
    message["To"] = recipient
    message["List-Unsubscribe"] = list_unsub
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    port = int(config["port"])
    if port == 465:
        server = smtplib.SMTP_SSL(config["host"], port, timeout=45, context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(config["host"], port, timeout=45)
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
    try:
        server.login(config["user"], config["password"])
        server.send_message(message)
    finally:
        try:
            server.quit()
        except Exception:  # noqa: BLE001 - best-effort close
            pass


def deliver_resend(config: Dict[str, str], recipient: str, subject: str, html_body: str, text_body: str, list_unsub: str) -> None:
    status, body = http_json(
        "https://api.resend.com/emails",
        {
            "from": f"{config['from_name']} <{config['from_email']}>",
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "headers": {"List-Unsubscribe": list_unsub},
        },
        {"Authorization": "Bearer " + config["key"]},
    )
    if status < 200 or status >= 300:
        raise RuntimeError(f"Resend HTTP {status}: {clip(body, 180)}")


def deliver_brevo(config: Dict[str, str], recipient: str, subject: str, html_body: str, text_body: str, list_unsub: str) -> None:
    status, body = http_json(
        "https://api.brevo.com/v3/smtp/email",
        {
            "sender": {"name": config["from_name"], "email": config["from_email"]},
            "to": [{"email": recipient}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": text_body,
            "headers": {"List-Unsubscribe": list_unsub},
        },
        {"api-key": config["key"]},
    )
    if status < 200 or status >= 300:
        raise RuntimeError(f"Brevo HTTP {status}: {clip(body, 180)}")


DELIVERERS = {"smtp": deliver_smtp, "resend": deliver_resend, "brevo": deliver_brevo}


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate (and optionally deliver) the Urban Forest Park Mandate Dispatch."
    )
    parser.add_argument("--jobs", type=Path, default=DEFAULT_JOBS, help="Path to jobs.json")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE, help="Path to archive.json (telemetry context)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output HTML path")
    parser.add_argument("--days", type=int, default=4, help="Freshness window in days (default 4 = 3-day cadence + slack)")
    parser.add_argument("--min-new", type=int, default=3, help="Fall back to recent mandates when fewer than this are fresh")
    parser.add_argument("--max-cards", type=int, default=10, help="Maximum job cards in the dispatch")
    parser.add_argument("--date", default="", help="Override 'today' (YYYY-MM-DD) - for testing")
    parser.add_argument("--to", default="", help="Send only to these address(es), comma separated - test mode")
    parser.add_argument(
        "--welcome",
        default="",
        metavar="EMAIL",
        help="Send the one-time Welcome email to this address now, then exit",
    )
    parser.add_argument(
        "--test-welcome",
        action="store_true",
        help="Send a test Welcome email to SMTP_USER / NEWSLETTER_OWNER_EMAIL and always write welcome_email_preview.html",
    )
    parser.add_argument(
        "--frequency",
        default="3-day",
        choices=["3-day", "weekly"],
        help="Dispatch cadence stamped into the Welcome email (default 3-day)",
    )
    parser.add_argument(
        "--sector",
        default="all",
        choices=["all", "academic", "forestry-gis", "corporate-esg"],
        help="Sector preference stamped into the Welcome email (default all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Generate the HTML edition only; do not send")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when delivery was attempted and nothing was delivered")
    parser.add_argument("--pace", type=float, default=0.4, help="Seconds to pause between deliveries (default 0.4)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging")
    return parser


def run_welcome_command(args: argparse.Namespace) -> int:
    """--welcome / --test-welcome: build and deliver the onboarding email."""
    jobs: Optional[List[Dict[str, Any]]] = None
    if args.jobs.exists():
        jobs = load_jobs(args.jobs)

    if args.test_welcome:
        recipient = (
            (args.to or "").split(",")[0].strip()
            or os.environ.get("NEWSLETTER_OWNER_EMAIL", "").strip()
            or os.environ.get("SMTP_USER", "").strip()
            or os.environ.get("NEWSLETTER_FROM_EMAIL", "").strip()
        )
        if not recipient or not EMAIL_RE.match(recipient):
            recipient = CONTACT_EMAIL
            logging.info(
                "No SMTP_USER / NEWSLETTER_OWNER_EMAIL configured - using %s for the preview.",
                CONTACT_EMAIL,
            )
        mode = "test"
    else:
        recipient = args.welcome.strip()
        mode = "single"

    if not recipient or not EMAIL_RE.match(recipient):
        logging.error(
            "No valid recipient for the welcome email (pass --welcome <email>, --to, or set SMTP_USER)."
        )
        return 1

    html_body, _text_body = build_welcome_email_html(recipient, args.frequency, args.sector, jobs)
    try:
        WELCOME_PREVIEW.write_text(html_body, encoding="utf-8")
        logging.info(
            "Welcome email preview written to %s (%d bytes).",
            WELCOME_PREVIEW, len(html_body.encode("utf-8")),
        )
    except OSError as exc:
        logging.warning("Could not write the welcome preview (%s).", clip(exc, 160))

    channel, config = detect_channel()
    if channel is None:
        logging.info(
            "No email credentials configured (RESEND_API_KEY / BREVO_API_KEY / SMTP_*) - "
            "preview saved only; nothing was sent."
        )
        return 0

    try:
        deliver_welcome(channel, config, recipient, args.frequency, args.sector, jobs)
    except Exception as exc:  # noqa: BLE001 - surface the failure for this explicit request
        logging.error("Welcome email delivery failed via %s: %s", channel.upper(), clip(exc, 240))
        return 1
    logging.info("Welcome email (%s mode) delivered via %s -> %s", mode, channel.upper(), recipient)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.welcome or args.test_welcome:
        return run_welcome_command(args)

    today = parse_iso_date(args.date) or datetime.now(IST).date()

    if not args.jobs.exists():
        logging.error("jobs.json not found at %s - nothing to dispatch.", args.jobs)
        return 1
    jobs = load_jobs(args.jobs)
    logging.info("Registry snapshot: %d active mandates read.", len(jobs))

    cards, used_fallback, new_count = select_cards(
        jobs, today, args.days, args.min_new, args.max_cards
    )
    stats = telemetry(jobs, today)
    logging.info(
        "Dispatch selection: %d card(s) | %d fresh in the last %d day window%s | telemetry: %s",
        len(cards), new_count, args.days, " (RECENT-MANDATE FALLBACK)" if used_fallback else "", stats,
    )

    unsubscribe_placeholder = "__UFP_UNSUBSCRIBE__"
    html_body, text_body = render_email(
        cards, stats, used_fallback, new_count, today, unsubscribe_placeholder
    )

    # Web edition (generic unsubscribe target — this file is published).
    web_html = html_body.replace(unsubscribe_placeholder, UNSUBSCRIBE_PAGE)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(web_html, encoding="utf-8")
    logging.info("Web edition written to %s (%d bytes).", args.out, len(web_html.encode("utf-8")))

    if args.dry_run:
        logging.info("--dry-run requested: skipping delivery.")
        return 0

    channel, config = detect_channel()

    # Welcome-email safety net: any subscriber recorded without a welcome
    # email yet receives the onboarding message on this run (exactly once).
    if channel is not None and not args.to:
        try:
            process_welcome_backlog(channel, config, jobs, pace=args.pace)
        except Exception as exc:  # noqa: BLE001 - never fail the dispatch run
            logging.warning("Welcome backlog pass skipped: %s", clip(exc, 160))

    recipients, source = load_recipients(args.to or None)
    logging.info("Subscriber source: %s (%d valid unique recipient(s)).", source, len(recipients))
    if not recipients:
        logging.info(
            "No subscribers configured - skipping delivery (set NEWSLETTER_SUBSCRIBERS, "
            "NEWSLETTER_SUBSCRIBERS_CSV, or populate data/subscribers.json)."
        )
        return 0

    if channel is None:
        logging.info(
            "No email credentials configured (RESEND_API_KEY / BREVO_API_KEY / SMTP_*) - "
            "skipping delivery. The web edition is saved and CI will pass."
        )
        return 0

    heading = dispatch_heading(new_count, len(cards), used_fallback)
    subject = f"Urban Forest Park \u2014 Mandate Dispatch \u00b7 {today.strftime('%d %b %Y')} \u00b7 {heading}"
    deliver = DELIVERERS[channel]
    logging.info("Delivering via %s to %d subscriber(s).", channel.upper(), len(recipients))

    delivered = 0
    failures: List[str] = []
    for index, recipient in enumerate(recipients, start=1):
        email = recipient["email"]
        unsub_url = unsubscribe_url_for(email)
        list_unsub = f"<mailto:{CONTACT_EMAIL}?subject=unsubscribe>, <{unsub_url}>"
        personalised_html = html_body.replace(unsubscribe_placeholder, unsub_url)
        try:
            deliver(config, email, subject, personalised_html, text_body, list_unsub)
            delivered += 1
            logging.info("[%d/%d] delivered -> %s", index, len(recipients), email)
        except Exception as exc:  # noqa: BLE001 - continue the batch
            failures.append(f"{email}: {exc}")
            logging.warning("[%d/%d] FAILED -> %s (%s)", index, len(recipients), email, clip(exc, 160))
        if args.pace > 0 and index < len(recipients):
            time.sleep(args.pace)

    logging.info(
        "Dispatch summary: %d/%d delivered | %d failed | channel=%s | cards=%d | file=%s",
        delivered, len(recipients), len(failures), channel, len(cards), args.out,
    )
    if failures:
        logging.warning("Delivery failures: %s", " | ".join(failures[:5]))

    strict = args.strict or os.environ.get("NEWSLETTER_STRICT", "").strip().lower() in {"1", "true", "yes"}
    if strict and delivered == 0:
        logging.error("Strict mode: zero deliveries - failing the run.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
