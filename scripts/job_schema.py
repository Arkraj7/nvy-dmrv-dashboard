#!/usr/bin/env python3
"""Shared rules for when a record may emit Google ``JobPosting`` markup.

Google's JobPosting policy allows the markup only on a page that contains a
single job posting. The Urban Forest Park registry also carries conferences,
workshops, scholarships, grants, competitions, memberships and evergreen
careers portals. Those records keep their dossier page and ``Article`` /
``WebPage`` structured data, but must not emit ``JobPosting``.

Keep this module dependency-free so both the static page builder and the
Google Indexing API job can apply exactly the same rule.
"""
from __future__ import annotations

from typing import Any, Mapping

# Categories whose records are programmes, events, funding calls or portals
# rather than a single employment vacancy.
NON_JOB_CATEGORIES = frozenset(
    {
        "Workshops, Training & Capacity Building",
        "Conferences, Summits & Events",
        "Webinars & Online Courses",
        "Memberships & Community Programs",
        "Competitions, Hackathons & Awards",
        "Grants & Research Funding",
        "Scholarships & Doctoral Support",
        "Ambassador & Fellowship Programs",
    }
)

# Opportunity kinds that represent an employment relationship. Fellowships
# and internships are retained because many are paid, application-based
# positions. A missing kind defaults to "Job / Career" for legacy records.
JOB_KINDS = frozenset({"Job / Career", "Fellowship", "Internship"})
JOB_ENTRY_TYPES = frozenset({"posting"})

# Evergreen portals commonly use a far-future validThrough. They are listings,
# not a single vacancy, even when their entry_type was previously "posting".
EVERGREEN_YEAR_CUTOFF = 2030


def is_job_posting_eligible(record: Mapping[str, Any]) -> bool:
    """Return True only for a single, currently open job-like record."""
    if str(record.get("entry_type") or "").strip() not in JOB_ENTRY_TYPES:
        return False
    if str(record.get("status") or "active").strip() != "active":
        return False
    if record.get("date_archived"):
        return False
    kind = str(record.get("opportunity_kind") or "Job / Career").strip()
    if kind not in JOB_KINDS:
        return False
    if str(record.get("category") or "").strip() in NON_JOB_CATEGORIES:
        return False
    valid_through = str(record.get("valid_through") or "").strip()
    year = valid_through[:4]
    if year.isdigit() and int(year) >= EVERGREEN_YEAR_CUTOFF:
        return False
    return True
