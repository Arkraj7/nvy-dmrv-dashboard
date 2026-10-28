from job_schema import is_job_posting_eligible


def record(**overrides):
    base = {
        "id": "sample-role",
        "status": "active",
        "entry_type": "posting",
        "opportunity_kind": "Job / Career",
        "category": "ESG, Carbon Markets & Corporate Sustainability",
        "valid_through": "2026-11-30",
    }
    base.update(overrides)
    return base


def test_single_job_is_eligible():
    assert is_job_posting_eligible(record()) is True


def test_missing_kind_and_category_defaults_to_job():
    assert is_job_posting_eligible(record(opportunity_kind=None, category=None)) is True


def test_portal_is_not_eligible():
    assert is_job_posting_eligible(record(entry_type="careers_portal")) is False


def test_workshop_is_not_eligible():
    assert (
        is_job_posting_eligible(
            record(category="Workshops, Training & Capacity Building")
        )
        is False
    )


def test_scholarship_is_not_eligible():
    assert (
        is_job_posting_eligible(
            record(
                opportunity_kind="Scholarship",
                category="Scholarships & Doctoral Support",
            )
        )
        is False
    )


def test_ambassador_programme_is_not_eligible():
    assert (
        is_job_posting_eligible(record(category="Ambassador & Fellowship Programs"))
        is False
    )


def test_evergreen_portal_date_is_not_eligible():
    assert is_job_posting_eligible(record(valid_through="2036-10-16")) is False


def test_archived_record_is_not_eligible():
    assert is_job_posting_eligible(record(date_archived="2026-10-28")) is False
