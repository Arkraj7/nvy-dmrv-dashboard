"""Unit tests for the Phase 3 ingestion gate.

These tests run fully offline: the verifier and page fetcher are injected.
"""
from __future__ import annotations

import copy

import pytest

from ingestion_gate import (
    dedupe_hash,
    find_employer,
    fuzzy_in_source,
    gate_candidate,
    missing_fields_in_source,
)
from verify_link import VerificationResult

REGISTRY = {
    "employers": [
        {
            "id": "acme-green-foundation",
            "name": "Acme Green Foundation",
            "domains": ["acmegreen.org"],
            "ats_hosts": [],
            "website": "https://acmegreen.org",
            "region": "india",
            "approved": True,
        }
    ]
}

PAGE_TEXT = (
    "Careers at Acme Green Foundation. Research Associate - Urban Forests. "
    "Apply before 15 November 2026. Compensation: INR 60,000 per month. "
    "Qualifications: Master's degree in Forestry or a related discipline. "
    "Skills: GIS, remote sensing, stakeholder engagement. "
    "Key responsibilities include field surveys and report writing. "
    "Apply now. Job ID: AGF-204."
)


def make_record(**overrides):
    record = {
        "id": "research-associate-urban-forests",
        "date_added": "2026-10-20",
        "clean_title": "Research Associate - Urban Forests",
        "organization": "Acme Green Foundation",
        "state": "Delhi",
        "city": "New Delhi",
        "category": "Forestry, Wildlife & Afforestation",
        "experience_level": "Mid-Senior (3-6 Years)",
        "position_type": "Project Associate / Research Associate",
        "opportunity_kind": "Job / Career",
        "deadline_or_window": "15 November 2026",
        "qualification_summary": "Master's degree in Forestry",
        "compensation_or_fellowship": "INR 60,000 per month",
        "role_summary": "Field research on urban forests.",
        "key_responsibilities": ["Field surveys", "Report writing", "Data analysis"],
        "must_have_skills": ["GIS", "remote sensing", "stakeholder engagement"],
        "application_tip": "Apply through the official careers page.",
        "apply_url": "https://acmegreen.org/careers/research-associate-urban-forests",
        "org_website": "",
        "org_domain": "",
        "source_portal": "",
        "_qualification_is_default": False,
        "_compensation_is_default": False,
        "_deadline_is_default": False,
    }
    record.update(overrides)
    return record


def ok_result(**overrides):
    data = dict(
        ok=True,
        final_url="https://acmegreen.org/careers/research-associate-urban-forests",
        final_host="acmegreen.org",
        http_status=200,
        redirect_chain=["https://acmegreen.org/careers/research-associate-urban-forests"],
        verification_level="page_verified",
        host_class="employer_primary",
        reason_code="OK",
        evidence_snippet="Research Associate - Urban Forests",
        content_hash="abc123",
        verified_at="2026-10-20T00:00:00Z",
        entry_type="posting",
        error_detail="",
    )
    data.update(overrides)
    return VerificationResult(**data)


def page(text=PAGE_TEXT, ok=True):
    return {"ok": ok, "text": text, "final_url": "", "status": 200, "error": ""}


def run_gate(record=None, result=None, page_result=None, registry=REGISTRY):
    return gate_candidate(
        copy.deepcopy(record or make_record()),
        registry,
        "2026-10-20",
        verifier=lambda *args, **kwargs: result or ok_result(),
        fetcher=lambda *args, **kwargs: page_result or page(),
    )


def test_verified_record_is_published_with_registry_identity():
    record, reason = run_gate(make_record())
    assert reason == ""
    assert record["status"] == "active"
    assert record["entry_type"] == "posting"
    assert record["employer_id"] == "acme-green-foundation"
    assert record["org_website"] == "https://acmegreen.org"
    assert record["org_domain"] == "acmegreen.org"
    assert record["verification"]["http_status"] == 200
    assert "_qualification_is_default" not in record


def test_invented_title_is_rejected_as_field_not_in_source():
    """A title that is not on the fetched page must never be published."""
    record, reason = run_gate(
        make_record(clean_title="Senior Director of Planetary Finance")
    )
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "FIELD_NOT_IN_SOURCE"
    assert "clean_title" in record["quarantine"]["fields"]
    assert "title" in reason


def test_invented_skill_is_rejected():
    record, reason = run_gate(make_record(must_have_skills=["GIS", "quantum computing"]))
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "FIELD_NOT_IN_SOURCE"


def test_default_placeholders_are_not_required_on_page():
    record, reason = run_gate(
        make_record(
            qualification_summary="Bachelor's / Master's degree in the relevant discipline or equivalent experience",
            compensation_or_fellowship="Not disclosed - see official portal",
            deadline_or_window="Rolling / Open",
            _qualification_is_default=True,
            _compensation_is_default=True,
            _deadline_is_default=True,
        )
    )
    assert record["status"] == "active", record.get("quarantine")
    assert reason == ""


def test_unregistered_employer_is_quarantined():
    record, reason = run_gate(make_record(organization="Mystery Employer Ltd"))
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "EMPLOYER_NOT_IN_REGISTRY"
    assert record["apply_url"]  # data is kept for review


def test_blocklisted_job_board_lead_is_dropped_not_stored():
    record, reason = run_gate(
        make_record(apply_url="https://www.linkedin.com/jobs/view/123456")
    )
    assert record is None
    assert "aggregator" in reason


def test_landing_page_failure_is_quarantined():
    record, reason = run_gate(
        result=ok_result(ok=False, verification_level="unverified",
                         reason_code="GENERIC_LANDING_PAGE",
                         error_detail="landing|GenericLanding|no title match")
    )
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "GENERIC_LANDING_PAGE"


def test_empty_page_text_is_quarantined():
    record, reason = run_gate(page_result=page(text="", ok=False))
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "PAGE_TEXT_UNAVAILABLE"


def test_closed_page_is_quarantined():
    record, reason = run_gate(
        page_result=page(text=PAGE_TEXT + " Applications are closed.")
    )
    assert record["status"] == "quarantined"
    assert record["quarantine"]["reason_code"] == "POSITION_CLOSED"


def test_tracking_parameters_are_stripped_from_stored_url():
    record, reason = run_gate(
        make_record(
            apply_url=(
                "https://acmegreen.org/careers/research-associate-urban-forests"
                "?utm_source=linkedin&utm_campaign=x&ref=abc"
            )
        )
    )
    assert record["status"] == "active"
    assert "utm_" not in record["apply_url"]
    assert "ref=" not in record["apply_url"]


def test_dedupe_hash_ignores_tracking_and_uses_location_deadline():
    base = make_record()
    same = make_record(
        apply_url="https://acmegreen.org/careers/x?utm_source=newsletter"
    )
    other_deadline = make_record(deadline_or_window="30 November 2026")
    other_city = make_record(city="Mumbai")
    assert dedupe_hash(base, "acme-green-foundation") == dedupe_hash(
        same, "acme-green-foundation"
    )
    assert dedupe_hash(base, "acme-green-foundation") != dedupe_hash(
        other_deadline, "acme-green-foundation"
    )
    assert dedupe_hash(base, "acme-green-foundation") != dedupe_hash(
        other_city, "acme-green-foundation"
    )


def test_fuzzy_title_matching_tolerates_punctuation_but_not_invention():
    assert fuzzy_in_source(
        "Research Associate - Urban Forests",
        "We are hiring a Research Associate – Urban Forests in Delhi.",
    )
    assert not fuzzy_in_source(
        "Senior Director of Planetary Finance", PAGE_TEXT
    )


def test_employer_lookup_is_conservative():
    registry = {
        "employers": [
            {"id": "iit-delhi", "name": "Indian Institute of Technology Delhi"},
            {"id": "iit-bombay", "name": "Indian Institute of Technology Bombay"},
        ]
    }
    assert find_employer("IIT Delhi", registry) is None
    found = find_employer("Indian Institute of Technology Delhi (IIT Delhi)", registry)
    assert found and found["id"] == "iit-delhi"


def test_missing_fields_reports_each_claim():
    record = make_record(
        compensation_or_fellowship="INR 99,000 per month",
        qualification_summary="Ph.D. in Astrophysics",
    )
    missing = missing_fields_in_source(record, PAGE_TEXT)
    assert "compensation_or_fellowship" in missing
    assert "qualification_summary" in missing
