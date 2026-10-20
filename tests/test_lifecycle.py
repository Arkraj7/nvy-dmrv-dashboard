"""Lifecycle tests: quarantine safety, deadline expiry, day-15 recheck."""
from __future__ import annotations

from fetch_and_humanize import apply_job_lifecycle


def test_quarantined_records_are_never_reactivated_or_archived():
    jobs = [
        {
            "id": "bad-job",
            "date_added": "2020-01-01",
            "status": "quarantined",
            "status_before_quarantine": "active",
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, archive, newly = apply_job_lifecycle(jobs, [], "2026-10-20")
    assert archive == []
    assert newly == 0
    assert active[0]["status"] == "quarantined"
    assert active[0]["status_before_quarantine"] == "active"


def test_quarantine_in_archive_file_is_preserved():
    archive = [
        {
            "id": "bad-old",
            "date_added": "2025-01-01",
            "status": "quarantined",
            "status_before_quarantine": "archived",
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, archive_out, _ = apply_job_lifecycle([], archive, "2026-10-20")
    assert active == []
    assert archive_out[0]["status"] == "quarantined"


def test_no_deadline_gets_30_day_cap_and_day_15_recheck():
    jobs = [
        {
            "id": "rolling-job",
            "date_added": "2026-10-20",
            "deadline_or_window": "Rolling / Open",
            "status": "active",
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, _, _ = apply_job_lifecycle(jobs, [], "2026-10-20")
    assert active[0]["valid_through"] == "2026-11-19"
    assert active[0]["reverify_after"] == "2026-11-04"


def test_stated_deadline_sets_valid_through():
    jobs = [
        {
            "id": "deadline-job",
            "date_added": "2026-10-20",
            "deadline_or_window": "2026-11-15",
            "status": "active",
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, _, _ = apply_job_lifecycle(jobs, [], "2026-10-20")
    assert active[0]["valid_through"] == "2026-11-15"
    assert "reverify_after" not in active[0]


def test_passed_deadline_archives_the_record():
    jobs = [
        {
            "id": "expired-job",
            "date_added": "2026-09-01",
            "deadline_or_window": "2026-09-30",
            "status": "active",
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, archive, newly = apply_job_lifecycle(jobs, [], "2026-10-20")
    assert active == []
    assert newly == 1
    assert archive[0]["status"] == "archived"


def test_quarantined_evergreen_record_is_not_reactivated():
    """Evergreen seeds must never override a quarantine block."""
    from fetch_and_humanize import apply_global_lifecycle

    jobs = [
        {
            "id": "quarantined-evergreen",
            "date_added": "2026-01-01",
            "evergreen": True,
            "status": "quarantined",
            "status_before_quarantine": "active",
            "quarantine": {"reason_code": "NEEDS_MANUAL_CHECK"},
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, archive, _ = apply_global_lifecycle(jobs, [], "2026-10-20")
    assert archive == []
    assert active[0]["status"] == "quarantined"
    assert active[0]["quarantine"]["reason_code"] == "NEEDS_MANUAL_CHECK"


def test_stale_quarantine_block_wins_over_active_status():
    """Defence in depth: a status flip cannot leak a recorded quarantine."""
    jobs = [
        {
            "id": "stale-flag",
            "date_added": "2026-10-01",
            "status": "active",
            "quarantine": {"reason_code": "GENERIC_LANDING_PAGE"},
            "apply_url": "https://example.org/job",
            "organization": "Acme",
        }
    ]
    active, _, _ = apply_job_lifecycle(jobs, [], "2026-10-20")
    assert active[0]["status"] == "quarantined"
