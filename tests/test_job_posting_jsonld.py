"""Regression tests for JobPosting structured-data location fields.

Google rejects ``applicantLocationRequirements`` values that are not
``Country`` objects (for example ``AdministrativeArea``), which surfaced as
the Search Console issue "Invalid object type for field
'applicantLocationRequirements'" on worldwide-remote listings.
"""

import json
import re
from datetime import date

import build_seo_pages as bsp


def _job(**overrides):
    base = {
        "id": "sample-remote-role",
        "status": "active",
        "entry_type": "posting",
        "clean_title": "Climate Analyst",
        "organization": "Example Org",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "opportunity_kind": "Job / Career",
        "date_added": "2026-11-01",
        "valid_through": "2026-12-31",
        "apply_url": "https://example.org/jobs/1",
    }
    base.update(overrides)
    return base


def _jsonld(job):
    raw = bsp.job_posting_jsonld(job, date(2026, 11, 4))
    match = re.search(r"<script[^>]*>(.*)</script>", raw, re.S)
    assert match, raw
    return json.loads(match.group(1))


def test_worldwide_remote_omits_applicant_location_requirements():
    data = _jsonld(
        _job(city="Remote (Global)", state="Global / Remote", country="Global", **{"global": True})
    )
    assert data["jobLocationType"] == "TELECOMMUTE"
    assert "applicantLocationRequirements" not in data


def test_country_remote_uses_country_object():
    data = _jsonld(
        _job(city="Remote (India)", state="Remote", country="India")
    )
    assert data["jobLocationType"] == "TELECOMMUTE"
    requirement = data["applicantLocationRequirements"]
    assert requirement["@type"] == "Country"
    assert requirement["name"] == "India"


def test_on_site_job_has_postal_address():
    data = _jsonld(
        _job(city="New Delhi", state="Delhi", country="India")
    )
    assert "applicantLocationRequirements" not in data
    assert data["jobLocation"]["@type"] == "Place"
    assert data["jobLocation"]["address"]["addressCountry"] == "IN"
